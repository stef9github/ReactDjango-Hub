"""
Base storage interface for document storage backends.
"""

from abc import ABC, abstractmethod
from typing import BinaryIO, Dict, Optional, AsyncIterator, Any
from pathlib import Path
import hashlib
import magic
import os


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class FileNotFoundError(StorageError):
    """File not found in storage."""
    pass


class StorageQuotaExceededError(StorageError):
    """Storage quota exceeded."""
    pass


class FileValidationError(StorageError):
    """File validation failed."""
    pass


class FileInfo:
    """File information container."""
    
    def __init__(
        self,
        path: str,
        size: int,
        content_type: str,
        hash: str,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[str] = None,
        modified_at: Optional[str] = None
    ):
        self.path = path
        self.size = size
        self.content_type = content_type
        self.hash = hash
        self.metadata = metadata or {}
        self.created_at = created_at
        self.modified_at = modified_at


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.max_file_size = self.config.get("max_file_size", 100 * 1024 * 1024)  # 100MB
        self.allowed_content_types = self.config.get("allowed_content_types", set())
        self.blocked_extensions = self.config.get("blocked_extensions", {
            '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js'
        })
    
    @abstractmethod
    async def store(
        self, 
        file_data: BinaryIO, 
        path: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> FileInfo:
        """
        Store file data at the specified path.
        
        Args:
            file_data: Binary file data
            path: Storage path for the file
            metadata: Optional metadata to store with the file
            
        Returns:
            FileInfo object with storage details
            
        Raises:
            StorageError: If storage operation fails
        """
        pass
    
    @abstractmethod
    async def retrieve(self, path: str) -> AsyncIterator[bytes]:
        """
        Retrieve file data from storage.
        
        Args:
            path: Storage path of the file
            
        Yields:
            Chunks of file data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            StorageError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def delete(self, path: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            path: Storage path of the file
            
        Returns:
            True if file was deleted, False if it didn't exist
            
        Raises:
            StorageError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def exists(self, path: str) -> bool:
        """
        Check if file exists in storage.
        
        Args:
            path: Storage path to check
            
        Returns:
            True if file exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_info(self, path: str) -> Optional[FileInfo]:
        """
        Get file information.
        
        Args:
            path: Storage path of the file
            
        Returns:
            FileInfo object or None if file doesn't exist
        """
        pass
    
    @abstractmethod
    async def list_files(self, prefix: str = "", limit: int = 1000) -> List[FileInfo]:
        """
        List files with optional prefix filter.
        
        Args:
            prefix: Path prefix to filter by
            limit: Maximum number of files to return
            
        Returns:
            List of FileInfo objects
        """
        pass
    
    @abstractmethod
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage usage statistics
        """
        pass
    
    def validate_file(self, file_data: BinaryIO, filename: str) -> Dict[str, Any]:
        """
        Validate file before storage.
        
        Args:
            file_data: Binary file data
            filename: Original filename
            
        Returns:
            Dictionary with validation results
            
        Raises:
            FileValidationError: If validation fails
        """
        # Check file size
        file_data.seek(0, 2)  # Seek to end
        file_size = file_data.tell()
        file_data.seek(0)  # Reset to beginning
        
        if file_size > self.max_file_size:
            raise FileValidationError(
                f"File size {file_size} exceeds maximum allowed size {self.max_file_size}"
            )
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext in self.blocked_extensions:
            raise FileValidationError(f"File extension {file_ext} is not allowed")
        
        # Detect content type
        file_data.seek(0)
        content_type = magic.from_buffer(file_data.read(2048), mime=True)
        file_data.seek(0)
        
        # Validate content type if restrictions are set
        if self.allowed_content_types and content_type not in self.allowed_content_types:
            raise FileValidationError(f"Content type {content_type} is not allowed")
        
        # Calculate file hash
        file_data.seek(0)
        hasher = hashlib.sha256()
        while chunk := file_data.read(8192):
            hasher.update(chunk)
        file_hash = hasher.hexdigest()
        file_data.seek(0)
        
        return {
            "size": file_size,
            "content_type": content_type,
            "hash": file_hash,
            "extension": file_ext
        }
    
    def generate_storage_path(
        self, 
        filename: str, 
        organization_id: str, 
        user_id: str = None
    ) -> str:
        """
        Generate a storage path for a file.
        
        Args:
            filename: Original filename
            organization_id: Organization identifier
            user_id: Optional user identifier
            
        Returns:
            Generated storage path
        """
        from datetime import datetime
        import uuid
        
        # Create date-based directory structure
        now = datetime.utcnow()
        date_path = f"{now.year}/{now.month:02d}/{now.day:02d}"
        
        # Generate unique filename to avoid conflicts
        file_ext = Path(filename).suffix.lower()
        unique_name = f"{uuid.uuid4()}{file_ext}"
        
        # Construct full path
        if user_id:
            return f"{organization_id}/{user_id}/{date_path}/{unique_name}"
        else:
            return f"{organization_id}/{date_path}/{unique_name}"
    
    async def copy_file(self, source_path: str, destination_path: str) -> FileInfo:
        """
        Copy file within storage backend.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            
        Returns:
            FileInfo for the copied file
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            StorageError: If copy operation fails
        """
        if not await self.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Read source file
        source_data = b""
        async for chunk in self.retrieve(source_path):
            source_data += chunk
        
        # Store at destination
        from io import BytesIO
        return await self.store(BytesIO(source_data), destination_path)
    
    async def move_file(self, source_path: str, destination_path: str) -> FileInfo:
        """
        Move file within storage backend.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            
        Returns:
            FileInfo for the moved file
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            StorageError: If move operation fails
        """
        # Copy file to new location
        file_info = await self.copy_file(source_path, destination_path)
        
        # Delete original file
        await self.delete(source_path)
        
        return file_info