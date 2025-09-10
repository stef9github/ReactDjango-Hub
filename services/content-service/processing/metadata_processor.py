"""
Metadata processing service for handling document metadata extraction
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import uuid4
import time

from ..extractors.factory import metadata_factory
from ..repositories.document_repository import DocumentRepository
from ..repositories.audit_repository import AuditRepository
from database.connection import get_db_session
from .queue_manager import ProcessingTask

logger = logging.getLogger(__name__)


class MetadataProcessor:
    """Processes metadata extraction tasks"""
    
    def __init__(self):
        self.name = "MetadataProcessor"
        self.version = "1.0.0"
        self.supported_task_types = ["metadata_extraction", "ocr", "content_analysis"]
    
    async def can_process(self, task: ProcessingTask) -> bool:
        """Check if this processor can handle the task"""
        return task.task_type in self.supported_task_types
    
    async def process_task(self, task: ProcessingTask) -> Dict[str, Any]:
        """Process a metadata extraction task"""
        start_time = time.time()
        
        try:
            logger.info(f"Processing metadata extraction task {task.id} for document {task.document_id}")
            
            # Validate task parameters
            if not task.file_path:
                raise ValueError("File path is required for metadata extraction")
            
            if not task.mime_type:
                raise ValueError("MIME type is required for metadata extraction")
            
            file_path = Path(task.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Extract metadata using factory
            extracted_metadata = await metadata_factory.extract_metadata(file_path, task.mime_type)
            
            # Update document in database
            await self._update_document_metadata(task, extracted_metadata)
            
            # Create audit log
            await self._log_processing_audit(task, extracted_metadata, success=True)
            
            # Calculate processing duration
            processing_duration = int((time.time() - start_time) * 1000)
            
            # Prepare result
            result = {
                "status": "success",
                "metadata_extracted": True,
                "processing_duration_ms": processing_duration,
                "extractor_used": extracted_metadata.extractor_version,
                "text_extracted": extracted_metadata.has_text_content(),
                "metadata_summary": extracted_metadata.get_summary(),
                "suggested_categories": extracted_metadata.suggested_categories,
                "suggested_tags": extracted_metadata.suggested_tags,
                "confidence_scores": {
                    "text_extraction": extracted_metadata.text_extraction_confidence,
                    "ocr_confidence": extracted_metadata.ocr_confidence
                }
            }
            
            # Add specific results based on task type
            if task.task_type == "ocr":
                result["ocr_text"] = extracted_metadata.text_content
                result["ocr_confidence"] = extracted_metadata.ocr_confidence
            elif task.task_type == "content_analysis":
                result["content_analysis"] = {
                    "word_count": extracted_metadata.word_count,
                    "character_count": extracted_metadata.character_count,
                    "language": extracted_metadata.language,
                    "keywords": extracted_metadata.keywords,
                    "tables_detected": extracted_metadata.tables_detected,
                    "images_detected": extracted_metadata.images_detected,
                    "links_detected": extracted_metadata.links_detected
                }
            
            logger.info(f"Successfully processed metadata extraction for document {task.document_id}")
            return result
            
        except Exception as e:
            error_msg = f"Metadata processing failed: {str(e)}"
            logger.error(f"Task {task.id} failed: {error_msg}")
            
            # Log processing failure
            try:
                await self._log_processing_audit(task, None, success=False, error_message=error_msg)
            except Exception as audit_error:
                logger.error(f"Failed to log processing audit: {audit_error}")
            
            raise
    
    async def _update_document_metadata(self, task: ProcessingTask, metadata):
        """Update document with extracted metadata"""
        try:
            async with get_db_session() as db:
                doc_repo = DocumentRepository(db)
                
                # Get current document
                document = await doc_repo.get_by_id(task.document_id)
                if not document:
                    raise ValueError(f"Document {task.document_id} not found")
                
                # Prepare metadata update
                metadata_dict = metadata.to_dict()
                
                # Update document fields
                update_data = {
                    "processing_status": "completed",
                    "metadata": metadata_dict,
                    "extracted_text": metadata.text_content if metadata.has_text_content() else None,
                    "word_count": metadata.word_count,
                    "character_count": metadata.character_count,
                    "language": metadata.language,
                    "ocr_completed": bool(metadata.ocr_confidence),
                    "text_extraction_confidence": metadata.text_extraction_confidence
                }
                
                # Update document type based on content analysis
                if metadata.suggested_categories:
                    update_data["document_type"] = metadata.suggested_categories[0]
                
                # Update tags if suggestions available
                if metadata.suggested_tags:
                    existing_tags = document.metadata.get("tags", []) if document.metadata else []
                    combined_tags = list(set(existing_tags + metadata.suggested_tags[:10]))  # Limit tags
                    
                    # Update metadata with combined tags
                    current_metadata = document.metadata or {}
                    current_metadata["tags"] = combined_tags
                    current_metadata.update({
                        "suggested_categories": metadata.suggested_categories,
                        "extraction_metadata": metadata_dict,
                        "last_processed": time.time()
                    })
                    update_data["metadata"] = current_metadata
                
                # Update the document
                updated_document = await doc_repo.update_by_id(task.document_id, **update_data)
                
                if not updated_document:
                    raise ValueError("Failed to update document")
                
                logger.info(f"Updated document {task.document_id} with extracted metadata")
                
        except Exception as e:
            logger.error(f"Failed to update document metadata: {e}")
            raise
    
    async def _log_processing_audit(self, task: ProcessingTask, metadata, success: bool, error_message: str = None):
        """Log processing audit trail"""
        try:
            async with get_db_session() as db:
                audit_repo = AuditRepository(db)
                
                action = "metadata_extracted" if success else "metadata_extraction_failed"
                
                details = {
                    "task_id": task.id,
                    "task_type": task.task_type,
                    "file_path": task.file_path,
                    "mime_type": task.mime_type,
                    "attempts": task.attempts,
                    "processing_duration_ms": getattr(metadata, 'extraction_duration_ms', None) if metadata else None
                }
                
                if success and metadata:
                    details.update({
                        "extractor_version": metadata.extractor_version,
                        "text_extracted": metadata.has_text_content(),
                        "metadata_summary": metadata.get_summary(),
                        "suggested_categories": metadata.suggested_categories[:3],
                        "confidence_scores": {
                            "text_extraction": metadata.text_extraction_confidence,
                            "ocr_confidence": metadata.ocr_confidence
                        }
                    })
                else:
                    details["error_message"] = error_message
                
                await audit_repo.log_action(
                    action=action,
                    user_id=task.user_id,
                    organization_id=task.organization_id,
                    document_id=task.document_id,
                    details=details
                )
                
                logger.debug(f"Logged processing audit for task {task.id}")
                
        except Exception as e:
            logger.error(f"Failed to log processing audit: {e}")
            # Don't raise - audit logging failure shouldn't fail the main process
    
    async def validate_task_parameters(self, task: ProcessingTask) -> Dict[str, Any]:
        """Validate task parameters and return validation results"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required parameters
        if not task.file_path:
            validation_result["errors"].append("File path is required")
            validation_result["valid"] = False
        
        if not task.mime_type:
            validation_result["errors"].append("MIME type is required")
            validation_result["valid"] = False
        
        if not task.document_id:
            validation_result["errors"].append("Document ID is required")
            validation_result["valid"] = False
        
        # Check file existence
        if task.file_path:
            file_path = Path(task.file_path)
            if not file_path.exists():
                validation_result["errors"].append(f"File not found: {file_path}")
                validation_result["valid"] = False
            else:
                # Check file size
                try:
                    file_size = file_path.stat().st_size
                    if file_size == 0:
                        validation_result["warnings"].append("File is empty")
                    elif file_size > 100 * 1024 * 1024:  # 100MB
                        validation_result["warnings"].append("Large file may take longer to process")
                except Exception as e:
                    validation_result["warnings"].append(f"Could not check file size: {e}")
        
        # Check if extractor is available for MIME type
        if task.mime_type:
            try:
                supported_types = metadata_factory.get_supported_mime_types()
                if task.mime_type not in supported_types:
                    validation_result["warnings"].append(f"No specific extractor for MIME type: {task.mime_type}")
            except Exception as e:
                validation_result["warnings"].append(f"Could not check extractor availability: {e}")
        
        return validation_result
    
    async def estimate_processing_time(self, task: ProcessingTask) -> int:
        """Estimate processing time in seconds based on file type and size"""
        if not task.file_path:
            return 60  # Default estimate
        
        try:
            file_path = Path(task.file_path)
            if not file_path.exists():
                return 60
            
            file_size = file_path.stat().st_size
            mime_type = task.mime_type
            
            # Base time estimates by file type (seconds per MB)
            time_estimates = {
                'application/pdf': 5,
                'image/': 15,  # OCR is slower
                'text/': 1,
                'application/msword': 3,
                'application/vnd.openxmlformats-officedocument': 3,
                'default': 5
            }
            
            # Find matching estimate
            seconds_per_mb = time_estimates.get('default')
            for pattern, estimate in time_estimates.items():
                if pattern != 'default' and mime_type.startswith(pattern):
                    seconds_per_mb = estimate
                    break
            
            # Calculate estimate
            size_mb = file_size / (1024 * 1024)
            estimated_time = max(10, int(size_mb * seconds_per_mb))  # Minimum 10 seconds
            
            # Add extra time for OCR tasks
            if task.task_type == "ocr":
                estimated_time *= 2
            
            return min(estimated_time, 1800)  # Cap at 30 minutes
            
        except Exception:
            return 120  # Default 2 minutes if estimation fails
    
    def get_processor_info(self) -> Dict[str, Any]:
        """Get information about this processor"""
        return {
            "name": self.name,
            "version": self.version,
            "supported_task_types": self.supported_task_types,
            "extractor_info": metadata_factory.get_extractor_info()
        }


# Global processor instance
metadata_processor = MetadataProcessor()