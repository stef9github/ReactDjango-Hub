"""
Local filesystem storage backend.
"""

import os
import aiofiles
import aiofiles.os
from pathlib import Path
from typing import BinaryIO, Dict, Optional, AsyncIterator, Any, List
from datetime import datetime
import logging

from .base import (
    StorageBackend, StorageError, FileNotFoundError, 
    StorageQuotaExceededError, FileInfo
)

logger = logging.getLogger(__name__)


class LocalFileStorage(StorageBackend):
    """Local filesystem storage implementation."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        self.base_path = Path(self.config.get("base_path", "/app/storage"))
        self.create_directories = self.config.get("create_directories", True)
        self.quota_bytes = self.config.get("quota_bytes", None)  # None = no quota
        
        # Ensure base directory exists
        if self.create_directories:
            self.base_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"LocalFileStorage initialized with base_path: {self.base_path}")
    
    def _get_full_path(self, path: str) -> Path:
        """Get full filesystem path from storage path."""
        return self.base_path / path.lstrip('/')
    
    async def _check_quota(self, file_size: int) -> None:
        """Check if adding file would exceed quota."""
        if not self.quota_bytes:
            return
        
        try:
            stats = await self.get_storage_stats()
            current_usage = stats.get("used_bytes", 0)
            
            if current_usage + file_size > self.quota_bytes:
                raise StorageQuotaExceededError(
                    f"Adding file would exceed quota. "
                    f"Current: {current_usage}, Adding: {file_size}, Limit: {self.quota_bytes}"
                )
        except Exception as e:
            if isinstance(e, StorageQuotaExceededError):
                raise
            logger.warning(f"Could not check storage quota: {e}")
    
    async def store(
        self, 
        file_data: BinaryIO, 
        path: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileInfo:
        """Store file data in local filesystem."""
        try:
            full_path = self._get_full_path(path)
            
            # Validate file
            validation_info = self.validate_file(file_data, path)
            
            # Check quota
            await self._check_quota(validation_info["size"])
            
            # Create directory if it doesn't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            async with aiofiles.open(full_path, 'wb') as f:
                file_data.seek(0)
                while chunk := file_data.read(8192):
                    await f.write(chunk)
            
            # Store metadata if provided
            if metadata:
                await self._store_metadata(path, metadata)
            
            # Get file stats
            stat = await aiofiles.os.stat(full_path)
            
            return FileInfo(
                path=path,
                size=validation_info["size"],
                content_type=validation_info["content_type"],
                hash=validation_info["hash"],
                metadata=metadata or {},
                created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat()
            )
            
        except Exception as e:
            logger.error(f"Failed to store file at {path}: {e}")
            if isinstance(e, (StorageError, StorageQuotaExceededError)):
                raise
            raise StorageError(f"Storage operation failed: {e}")
    
    async def retrieve(self, path: str) -> AsyncIterator[bytes]:
        """Retrieve file data from local filesystem."""
        full_path = self._get_full_path(path)
        
        if not await aiofiles.os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            async with aiofiles.open(full_path, 'rb') as f:
                while chunk := await f.read(8192):
                    yield chunk
        except Exception as e:
            logger.error(f"Failed to retrieve file {path}: {e}")
            raise StorageError(f"File retrieval failed: {e}")
    
    async def delete(self, path: str) -> bool:
        """Delete file from local filesystem."""
        full_path = self._get_full_path(path)
        
        if not await aiofiles.os.path.exists(full_path):
            return False
        
        try:
            await aiofiles.os.remove(full_path)
            
            # Also delete metadata file if it exists
            await self._delete_metadata(path)
            
            # Clean up empty directories
            await self._cleanup_empty_directories(full_path.parent)
            
            logger.info(f"Deleted file: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            raise StorageError(f"File deletion failed: {e}")
    
    async def exists(self, path: str) -> bool:
        """Check if file exists in local filesystem."""
        full_path = self._get_full_path(path)
        return await aiofiles.os.path.exists(full_path)
    
    async def get_info(self, path: str) -> Optional[FileInfo]:
        """Get file information from local filesystem."""
        full_path = self._get_full_path(path)
        
        if not await aiofiles.os.path.exists(full_path):
            return None
        
        try:
            stat = await aiofiles.os.stat(full_path)
            
            # Try to detect content type from file
            content_type = "application/octet-stream"
            try:
                import magic
                content_type = magic.from_file(str(full_path), mime=True)
            except Exception:
                pass
            
            # Calculate file hash
            import hashlib
            hasher = hashlib.sha256()
            async with aiofiles.open(full_path, 'rb') as f:
                while chunk := await f.read(8192):
                    hasher.update(chunk)
            file_hash = hasher.hexdigest()
            
            # Load metadata if exists
            metadata = await self._load_metadata(path)
            
            return FileInfo(
                path=path,
                size=stat.st_size,
                content_type=content_type,
                hash=file_hash,
                metadata=metadata,
                created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat()
            )
            
        except Exception as e:
            logger.error(f"Failed to get file info for {path}: {e}")
            return None
    
    async def list_files(self, prefix: str = "", limit: int = 1000) -> List[FileInfo]:
        """List files in local filesystem with optional prefix filter."""
        files = []
        search_path = self.base_path
        
        if prefix:
            search_path = self._get_full_path(prefix)
        
        try:
            if not await aiofiles.os.path.exists(search_path):
                return files
            
            count = 0
            for root, dirs, filenames in os.walk(search_path):
                if count >= limit:
                    break
                
                root_path = Path(root)
                
                for filename in filenames:
                    if count >= limit:
                        break
                    
                    # Skip metadata files
                    if filename.endswith('.metadata'):
                        continue
                    
                    file_path = root_path / filename
                    relative_path = file_path.relative_to(self.base_path)
                    
                    file_info = await self.get_info(str(relative_path))
                    if file_info:
                        files.append(file_info)
                        count += 1
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files with prefix {prefix}: {e}")
            return files
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics."""
        try:
            total_size = 0
            file_count = 0
            
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    # Skip metadata files in counting
                    if file.endswith('.metadata'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        total_size += stat.st_size
                        file_count += 1
                    except OSError:
                        continue
            
            # Get filesystem stats
            statvfs = os.statvfs(self.base_path)
            total_space = statvfs.f_frsize * statvfs.f_blocks
            free_space = statvfs.f_frsize * statvfs.f_available
            
            return {
                "backend_type": "local_filesystem",
                "base_path": str(self.base_path),
                "used_bytes": total_size,
                "file_count": file_count,
                "total_space_bytes": total_space,
                "free_space_bytes": free_space,
                "quota_bytes": self.quota_bytes,
                "quota_used_percent": (total_size / self.quota_bytes * 100) if self.quota_bytes else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                "backend_type": "local_filesystem",
                "base_path": str(self.base_path),
                "error": str(e)
            }
    
    async def _store_metadata(self, path: str, metadata: Dict[str, Any]) -> None:
        """Store metadata alongside file."""
        if not metadata:
            return
        
        metadata_path = self._get_full_path(f"{path}.metadata")
        
        try:
            import json
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(metadata, indent=2))
                
        except Exception as e:
            logger.warning(f"Failed to store metadata for {path}: {e}")
    
    async def _load_metadata(self, path: str) -> Dict[str, Any]:
        """Load metadata for a file."""
        metadata_path = self._get_full_path(f"{path}.metadata")
        
        if not await aiofiles.os.path.exists(metadata_path):
            return {}
        
        try:
            import json
            async with aiofiles.open(metadata_path, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            logger.warning(f"Failed to load metadata for {path}: {e}")
            return {}
    
    async def _delete_metadata(self, path: str) -> None:
        """Delete metadata file if it exists."""
        metadata_path = self._get_full_path(f"{path}.metadata")
        
        if await aiofiles.os.path.exists(metadata_path):
            try:
                await aiofiles.os.remove(metadata_path)
            except Exception as e:
                logger.warning(f"Failed to delete metadata for {path}: {e}")
    
    async def _cleanup_empty_directories(self, directory: Path) -> None:
        """Recursively remove empty directories."""
        try:
            # Don't delete the base storage directory
            if directory <= self.base_path:
                return
            
            if directory.exists() and directory.is_dir():
                try:
                    directory.rmdir()  # Only works if empty
                    # Recursively clean parent directories
                    await self._cleanup_empty_directories(directory.parent)
                except OSError:
                    # Directory not empty, that's fine
                    pass
        except Exception as e:
            logger.debug(f"Error cleaning up directory {directory}: {e}")
    
    async def get_direct_url(self, path: str, expires_in: int = 3600) -> Optional[str]:
        """
        Get a direct URL for file access (not applicable for local storage).
        Returns None as local storage doesn't support direct URLs.
        """
        return None
    
    async def create_backup(self, path: str, backup_path: str) -> FileInfo:
        """Create a backup copy of a file."""
        return await self.copy_file(path, backup_path)