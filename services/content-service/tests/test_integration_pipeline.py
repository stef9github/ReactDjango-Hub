"""
Integration tests for the complete file processing pipeline.
"""

import pytest
import uuid
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from models import Document
from repositories import DocumentRepository, AuditRepository
from processing.queue_manager import ProcessingQueueManager, ProcessingTask
from processing.metadata_processor import MetadataProcessor
from extractors.factory import MetadataExtractorFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestFileProcessingPipeline:
    """Integration tests for complete file processing pipeline."""
    
    async def test_complete_upload_processing_pipeline(
        self, 
        db_session, 
        mock_user_data, 
        sample_text_file, 
        mock_redis,
        mock_file_storage
    ):
        """Test complete pipeline from upload to processed document."""
        # Setup repositories
        doc_repo = DocumentRepository(db_session)
        audit_repo = AuditRepository(db_session)
        
        # Mock file operations
        with patch('aiofiles.open'), \
             patch('magic.from_buffer', return_value="text/plain"), \
             patch('hashlib.sha256') as mock_hash:
            
            mock_hash.return_value.hexdigest.return_value = "test_file_hash"
            
            # 1. Create document (simulating upload)
            document = await doc_repo.create_document(
                filename="test_document.txt",
                original_filename="test_document.txt",
                content_type="text/plain",
                file_size=1024,
                file_hash="test_file_hash",
                storage_path="/storage/test_document.txt",
                created_by=uuid.UUID(mock_user_data["user_id"]),
                organization_id=uuid.UUID(mock_user_data["organization_id"])
            )
            
            assert document.processing_status == "pending"
            
            # 2. Log upload audit
            upload_audit = await audit_repo.log_action(
                action="upload",
                user_id=uuid.UUID(mock_user_data["user_id"]),
                organization_id=uuid.UUID(mock_user_data["organization_id"]),
                document_id=document.id,
                details={"filename": "test_document.txt", "file_size": 1024}
            )
            
            assert upload_audit.action == "upload"
            
            # 3. Process document (simulating background processing)
            with patch('extractors.factory.metadata_factory') as mock_factory:
                mock_metadata = MagicMock()
                mock_metadata.text_content = "Sample document content"
                mock_metadata.word_count = 10
                mock_metadata.language = "en"
                mock_metadata.keywords = ["sample", "document", "test"]
                mock_metadata.extraction_duration_ms = 150
                mock_factory.extract_metadata.return_value = mock_metadata
                
                # Update processing status
                processed_document = await doc_repo.update_processing_status(
                    document_id=document.id,
                    processing_status="completed",
                    ocr_completed=True,
                    extracted_text="Sample document content"
                )
                
                assert processed_document.processing_status == "completed"
                assert processed_document.extracted_text == "Sample document content"
            
            # 4. Verify complete pipeline
            final_document = await doc_repo.get_by_id(document.id)
            assert final_document.status == "active"
            assert final_document.processing_status == "completed"
            assert final_document.extracted_text is not None
    
    async def test_pdf_processing_pipeline(
        self, 
        db_session, 
        mock_user_data, 
        sample_pdf_file,
        mock_redis
    ):
        """Test PDF document processing pipeline."""
        doc_repo = DocumentRepository(db_session)
        
        with patch('magic.from_buffer', return_value="application/pdf"):
            # Create PDF document
            document = await doc_repo.create_document(
                filename="document.pdf",
                original_filename="document.pdf",
                content_type="application/pdf",
                file_size=sample_pdf_file.stat().st_size,
                file_hash="pdf_hash_123",
                storage_path=str(sample_pdf_file),
                created_by=uuid.UUID(mock_user_data["user_id"]),
                organization_id=uuid.UUID(mock_user_data["organization_id"])
            )
            
            # Mock PDF extraction
            with patch('extractors.pdf_extractor.PDFExtractor') as mock_extractor:
                mock_instance = mock_extractor.return_value
                mock_instance.can_extract.return_value = True
                
                mock_metadata = MagicMock()
                mock_metadata.text_content = "Extracted PDF text content"
                mock_metadata.page_count = 5
                mock_metadata.author = "Test Author"
                mock_metadata.title = "Test Document"
                mock_instance.extract_metadata.return_value = mock_metadata
                
                # Process PDF
                processed_doc = await doc_repo.update_processing_status(
                    document_id=document.id,
                    processing_status="completed",
                    ocr_completed=True,
                    extracted_text="Extracted PDF text content"
                )
                
                assert processed_doc.extracted_text == "Extracted PDF text content"
    
    async def test_image_ocr_processing_pipeline(
        self, 
        db_session, 
        mock_user_data, 
        sample_image_file
    ):
        """Test image OCR processing pipeline."""
        doc_repo = DocumentRepository(db_session)
        
        with patch('magic.from_buffer', return_value="image/jpeg"):
            # Create image document
            document = await doc_repo.create_document(
                filename="scan.jpg",
                original_filename="scan.jpg",
                content_type="image/jpeg",
                file_size=sample_image_file.stat().st_size,
                file_hash="image_hash_456",
                storage_path=str(sample_image_file),
                created_by=uuid.UUID(mock_user_data["user_id"]),
                organization_id=uuid.UUID(mock_user_data["organization_id"])
            )
            
            # Mock OCR extraction
            with patch('extractors.image_extractor.ImageExtractor') as mock_extractor:
                mock_instance = mock_extractor.return_value
                mock_instance.can_extract.return_value = True
                
                mock_metadata = MagicMock()
                mock_metadata.text_content = "OCR extracted text from image"
                mock_metadata.ocr_confidence = 0.95
                mock_metadata.image_dimensions = {"width": 1920, "height": 1080}
                mock_instance.extract_metadata.return_value = mock_metadata
                
                # Process with OCR
                processed_doc = await doc_repo.update_processing_status(
                    document_id=document.id,
                    processing_status="completed",
                    ocr_completed=True,
                    extracted_text="OCR extracted text from image"
                )
                
                assert processed_doc.ocr_completed is True
                assert processed_doc.extracted_text == "OCR extracted text from image"
    
    async def test_queue_processing_integration(
        self, 
        db_session, 
        mock_user_data, 
        mock_redis
    ):
        """Test integration with processing queue system."""
        # Mock queue manager
        with patch('processing.queue_manager.ProcessingQueueManager') as mock_queue_class:
            queue_manager = mock_queue_class.return_value
            queue_manager.connect = AsyncMock()
            queue_manager.disconnect = AsyncMock()
            queue_manager.add_task = AsyncMock(return_value=True)
            queue_manager.get_queue_stats = AsyncMock(return_value={
                "queue_high_length": 0,
                "queue_normal_length": 1,
                "queue_low_length": 0,
                "processing_count": 0
            })
            
            # Create processing task
            task = ProcessingTask(
                id="test-task-123",
                document_id=str(uuid.uuid4()),
                organization_id=mock_user_data["organization_id"],
                user_id=mock_user_data["user_id"],
                task_type="metadata_extraction",
                file_path="/storage/test.pdf",
                mime_type="application/pdf"
            )
            
            # Test task serialization
            task_dict = task.to_dict()
            assert task_dict["id"] == "test-task-123"
            assert task_dict["task_type"] == "metadata_extraction"
            
            # Test task deserialization
            reconstructed_task = ProcessingTask.from_dict(task_dict)
            assert reconstructed_task.id == task.id
            assert reconstructed_task.task_type == task.task_type
            
            # Test queue operations
            await queue_manager.connect()
            success = await queue_manager.add_task(task, priority="normal")
            stats = await queue_manager.get_queue_stats()
            await queue_manager.disconnect()
            
            assert success is True
            assert stats["queue_normal_length"] == 1
    
    async def test_error_handling_pipeline(
        self, 
        db_session, 
        mock_user_data,
        simulate_file_system_error
    ):
        """Test error handling throughout the pipeline."""
        doc_repo = DocumentRepository(db_session)
        audit_repo = AuditRepository(db_session)
        
        # Create document
        document = await doc_repo.create_document(
            filename="error_test.pdf",
            original_filename="error_test.pdf",
            content_type="application/pdf",
            file_size=1024,
            file_hash="error_hash",
            storage_path="/nonexistent/path.pdf",
            created_by=uuid.UUID(mock_user_data["user_id"]),
            organization_id=uuid.UUID(mock_user_data["organization_id"])
        )
        
        # Simulate processing error
        with patch('extractors.factory.metadata_factory') as mock_factory:
            mock_factory.extract_metadata.side_effect = simulate_file_system_error("not_found")
            
            # Update to failed status
            failed_document = await doc_repo.update_processing_status(
                document_id=document.id,
                processing_status="failed"
            )
            
            assert failed_document.processing_status == "failed"
            
            # Log error
            error_audit = await audit_repo.log_action(
                action="processing_error",
                user_id=uuid.UUID(mock_user_data["user_id"]),
                organization_id=uuid.UUID(mock_user_data["organization_id"]),
                document_id=document.id,
                details={
                    "error_type": "file_not_found",
                    "error_message": "File not found",
                    "processing_stage": "metadata_extraction"
                }
            )
            
            assert error_audit.action == "processing_error"
    
    async def test_concurrent_processing_pipeline(
        self, 
        db_session, 
        mock_user_data,
        test_data_factory
    ):
        """Test concurrent document processing."""
        doc_repo = DocumentRepository(db_session)
        
        # Create multiple documents
        documents = []
        for i in range(5):
            doc_data = test_data_factory.create_document_data(
                filename=f"doc_{i}.txt",
                file_hash=f"hash_{i}"
            )
            
            document = await doc_repo.create_document(
                **doc_data,
                created_by=uuid.UUID(mock_user_data["user_id"]),
                organization_id=uuid.UUID(mock_user_data["organization_id"])
            )
            documents.append(document)
        
        # Process documents concurrently
        async def process_document(doc):
            """Process a single document."""
            with patch('extractors.factory.metadata_factory') as mock_factory:
                mock_metadata = MagicMock()
                mock_metadata.text_content = f"Content for {doc.filename}"
                mock_factory.extract_metadata.return_value = mock_metadata
                
                return await doc_repo.update_processing_status(
                    document_id=doc.id,
                    processing_status="completed",
                    extracted_text=f"Content for {doc.filename}"
                )
        
        # Process all documents concurrently
        processed_docs = await asyncio.gather(*[
            process_document(doc) for doc in documents
        ])
        
        # Verify all were processed
        assert len(processed_docs) == 5
        for proc_doc in processed_docs:
            assert proc_doc.processing_status == "completed"
            assert proc_doc.extracted_text is not None
    
    async def test_metadata_extraction_factory_integration(self, sample_text_file):
        """Test metadata extraction factory integration."""
        # Test factory initialization
        from extractors.factory import MetadataExtractorFactory, metadata_factory
        
        assert metadata_factory is not None
        assert isinstance(metadata_factory, MetadataExtractorFactory)
        
        # Test supported MIME types
        supported_types = metadata_factory.get_supported_mime_types()
        assert "text/plain" in supported_types
        
        # Test extractor info
        info = metadata_factory.get_extractor_info()
        assert "total_extractors" in info
        assert info["total_extractors"] > 0
        
        # Test extraction with real file
        with patch('extractors.factory.metadata_factory.extract_metadata') as mock_extract:
            mock_metadata = MagicMock()
            mock_metadata.text_content = "Sample text content"
            mock_metadata.word_count = 5
            mock_extract.return_value = mock_metadata
            
            result = await metadata_factory.extract_metadata(sample_text_file, "text/plain")
            
            assert result.text_content == "Sample text content"
            assert result.word_count == 5
    
    async def test_background_worker_integration(self, mock_redis):
        """Test background worker integration."""
        with patch('processing.background_worker.BackgroundWorker') as mock_worker_class:
            with patch('processing.queue_manager.ProcessingQueueManager') as mock_queue_class:
                # Mock queue manager
                queue_manager = mock_queue_class.return_value
                queue_manager.connect = AsyncMock()
                queue_manager.get_next_task = AsyncMock(return_value=None)
                
                # Mock worker
                worker = mock_worker_class.return_value
                worker.worker_id = "test-worker-1"
                worker.is_running = False
                worker.max_concurrent_tasks = 3
                worker.get_worker_stats = MagicMock(return_value={
                    "worker_id": "test-worker-1",
                    "is_running": False,
                    "tasks_processed": 0,
                    "tasks_failed": 0,
                    "uptime_seconds": 0
                })
                
                # Test worker initialization
                assert worker.worker_id == "test-worker-1"
                assert worker.max_concurrent_tasks == 3
                
                # Test worker stats
                stats = worker.get_worker_stats()
                assert stats["worker_id"] == "test-worker-1"
                assert "tasks_processed" in stats
    
    async def test_complete_security_audit_pipeline(
        self, 
        db_session, 
        mock_user_data, 
        dangerous_filename_file
    ):
        """Test complete security audit pipeline."""
        doc_repo = DocumentRepository(db_session)
        audit_repo = AuditRepository(db_session)
        
        safe_path, dangerous_name = dangerous_filename_file
        
        # Simulate security validation
        def validate_filename(filename: str) -> bool:
            """Validate filename for security."""
            dangerous_patterns = ["../", "..\\", "/etc/", "C:\\"]
            return not any(pattern in filename for pattern in dangerous_patterns)
        
        # Test dangerous filename detection
        is_safe = validate_filename(dangerous_name)
        assert is_safe is False
        
        # Log security violation
        if not is_safe:
            security_audit = await audit_repo.log_action(
                action="security_violation",
                user_id=uuid.UUID(mock_user_data["user_id"]),
                organization_id=uuid.UUID(mock_user_data["organization_id"]),
                document_id=None,
                details={
                    "violation_type": "dangerous_filename",
                    "attempted_filename": dangerous_name,
                    "user_ip": "192.168.1.100",
                    "action_taken": "upload_rejected"
                }
            )
            
            assert security_audit.action == "security_violation"
            assert "dangerous_filename" in security_audit.details["violation_type"]


@pytest.mark.performance
@pytest.mark.asyncio
class TestPipelinePerformance:
    """Performance tests for the processing pipeline."""
    
    async def test_pipeline_throughput(
        self, 
        db_session, 
        mock_user_data, 
        performance_timer,
        test_data_factory
    ):
        """Test pipeline throughput under load."""
        doc_repo = DocumentRepository(db_session)
        
        # Create batch of documents
        document_count = 20
        
        performance_timer.start()
        
        # Create documents
        create_tasks = []
        for i in range(document_count):
            doc_data = test_data_factory.create_document_data(
                filename=f"perf_test_{i}.txt",
                file_hash=f"perf_hash_{i}"
            )
            
            task = doc_repo.create_document(
                **doc_data,
                created_by=uuid.UUID(mock_user_data["user_id"]),
                organization_id=uuid.UUID(mock_user_data["organization_id"])
            )
            create_tasks.append(task)
        
        documents = await asyncio.gather(*create_tasks)
        
        # Process documents
        with patch('extractors.factory.metadata_factory') as mock_factory:
            mock_metadata = MagicMock()
            mock_metadata.text_content = "Performance test content"
            mock_factory.extract_metadata.return_value = mock_metadata
            
            process_tasks = []
            for doc in documents:
                task = doc_repo.update_processing_status(
                    document_id=doc.id,
                    processing_status="completed",
                    extracted_text="Performance test content"
                )
                process_tasks.append(task)
            
            processed_docs = await asyncio.gather(*process_tasks)
        
        performance_timer.stop()
        
        # Verify performance
        total_time = performance_timer.elapsed
        throughput = document_count / total_time
        
        print(f"Processed {document_count} documents in {total_time:.2f}s")
        print(f"Throughput: {throughput:.2f} documents/second")
        
        # Performance benchmark
        assert throughput > 5  # Should process at least 5 documents per second
        assert len(processed_docs) == document_count
    
    async def test_memory_usage_pipeline(
        self, 
        db_session, 
        mock_user_data,
        large_file
    ):
        """Test memory usage in processing pipeline."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        doc_repo = DocumentRepository(db_session)
        
        # Create document with large file
        document = await doc_repo.create_document(
            filename="large_file.txt",
            original_filename="large_file.txt",
            content_type="text/plain",
            file_size=large_file.stat().st_size,
            file_hash="large_file_hash",
            storage_path=str(large_file),
            created_by=uuid.UUID(mock_user_data["user_id"]),
            organization_id=uuid.UUID(mock_user_data["organization_id"])
        )
        
        # Simulate processing large file
        with patch('extractors.factory.metadata_factory') as mock_factory:
            # Mock streaming extraction to avoid loading entire file
            mock_metadata = MagicMock()
            mock_metadata.text_content = "Large file content preview..."
            mock_metadata.file_size = large_file.stat().st_size
            mock_factory.extract_metadata.return_value = mock_metadata
            
            processed_doc = await doc_repo.update_processing_status(
                document_id=document.id,
                processing_status="completed",
                extracted_text="Large file content preview..."
            )
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory usage should be reasonable
        file_size = large_file.stat().st_size
        assert memory_increase < file_size / 5  # Less than 20% of file size
        
        print(f"Memory increase: {memory_increase / 1024 / 1024:.2f} MB")
        print(f"File size: {file_size / 1024 / 1024:.2f} MB")


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndScenarios:
    """End-to-end integration test scenarios."""
    
    async def test_document_lifecycle_scenario(
        self, 
        db_session, 
        mock_user_data, 
        admin_user_data,
        sample_pdf_file
    ):
        """Test complete document lifecycle scenario."""
        doc_repo = DocumentRepository(db_session)
        audit_repo = AuditRepository(db_session)
        
        user_id = uuid.UUID(mock_user_data["user_id"])
        admin_id = uuid.UUID(admin_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        
        # 1. Upload document
        document = await doc_repo.create_document(
            filename="project_report.pdf",
            original_filename="project_report.pdf",
            content_type="application/pdf",
            file_size=sample_pdf_file.stat().st_size,
            file_hash="report_hash_789",
            storage_path=str(sample_pdf_file),
            created_by=user_id,
            organization_id=org_id
        )
        
        await audit_repo.log_action("upload", user_id, org_id, document.id, 
                                   {"filename": "project_report.pdf"})
        
        # 2. Process document
        with patch('extractors.pdf_extractor.PDFExtractor'):
            processed_doc = await doc_repo.update_processing_status(
                document_id=document.id,
                processing_status="completed",
                extracted_text="Project report content..."
            )
        
        # 3. Access document
        accessed_doc = await doc_repo.get_by_id(document.id)
        await audit_repo.log_action("access", user_id, org_id, document.id,
                                   {"access_type": "view"})
        
        # 4. Share document (simulated)
        await audit_repo.log_action("share", user_id, org_id, document.id,
                                   {"target_user": str(admin_id), "permissions": ["read"]})
        
        # 5. Download document
        await audit_repo.log_action("download", admin_id, org_id, document.id,
                                   {"download_type": "full"})
        
        # 6. Delete document
        deleted_doc = await doc_repo.mark_as_deleted(document.id)
        await audit_repo.log_action("delete", admin_id, org_id, document.id,
                                   {"deletion_type": "soft_delete"})
        
        # Verify complete lifecycle
        assert processed_doc.processing_status == "completed"
        assert accessed_doc.id == document.id
        assert deleted_doc.status == "deleted"
        
        # Verify audit trail
        audit_trail = await audit_repo.get_document_audit_trail(document.id, limit=10)
        audit_actions = [audit.action for audit in audit_trail]
        
        expected_actions = ["upload", "access", "share", "download", "delete"]
        for action in expected_actions:
            assert action in audit_actions