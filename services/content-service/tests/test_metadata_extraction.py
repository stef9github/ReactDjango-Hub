"""
Metadata extraction and processing tests for Content Service
Tests the complete metadata extraction pipeline and background processing
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app


class TestMetadataExtraction:
    """Test metadata extraction functionality"""

    def test_process_document_requires_auth(self, client):
        """Test that process endpoint requires authentication"""
        document_id = "12345678-1234-5678-9012-123456789012"
        
        response = client.post(f"/api/v1/documents/{document_id}/process")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_process_document_not_found(self, mock_client, client, valid_token, mock_user_data):
        """Test processing when document doesn't exist"""
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        document_id = "nonexistent-document-id"
        
        response = client.post(
            f"/api/v1/documents/{document_id}/process",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_process_document_invalid_type(self, mock_client, client, valid_token, mock_user_data):
        """Test processing with invalid processing type"""
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        document_id = "12345678-1234-5678-9012-123456789012"
        
        response = client.post(
            f"/api/v1/documents/{document_id}/process",
            headers={"Authorization": f"Bearer {valid_token}"},
            params={"processing_type": "invalid_type"}
        )
        
        assert response.status_code == 400
        assert "Invalid processing type" in response.json()["detail"]

    def test_processing_status_requires_auth(self, client):
        """Test that processing status endpoint requires authentication"""
        document_id = "12345678-1234-5678-9012-123456789012"
        
        response = client.get(f"/api/v1/documents/{document_id}/processing-status")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_queue_stats_requires_auth(self, client):
        """Test that queue statistics endpoint requires authentication"""
        response = client.get("/api/v1/processing/queue-stats")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]


class TestMetadataExtractors:
    """Test individual metadata extractors"""
    
    @pytest.mark.asyncio
    async def test_pdf_extractor_availability(self):
        """Test PDF extractor can be imported and initialized"""
        try:
            from extractors.pdf_extractor import PDFExtractor
            
            extractor = PDFExtractor()
            assert extractor is not None
            assert "application/pdf" in extractor.get_supported_mime_types()
            
            # Test can_extract method
            test_path = Path("test.pdf")
            result = await extractor.can_extract(test_path, "application/pdf")
            assert isinstance(result, bool)
            
        except ImportError as e:
            pytest.skip(f"PDF extractor dependencies not available: {e}")

    @pytest.mark.asyncio
    async def test_image_extractor_availability(self):
        """Test image extractor can be imported and initialized"""
        try:
            from extractors.image_extractor import ImageExtractor
            
            extractor = ImageExtractor()
            assert extractor is not None
            
            supported_types = extractor.get_supported_mime_types()
            assert "image/jpeg" in supported_types
            assert "image/png" in supported_types
            
        except ImportError as e:
            pytest.skip(f"Image extractor dependencies not available: {e}")

    @pytest.mark.asyncio
    async def test_text_extractor_availability(self):
        """Test text extractor can be imported and initialized"""
        from extractors.text_extractor import TextExtractor
        
        extractor = TextExtractor()
        assert extractor is not None
        
        supported_types = extractor.get_supported_mime_types()
        assert "text/plain" in supported_types
        assert "text/html" in supported_types

    @pytest.mark.asyncio
    async def test_office_extractor_availability(self):
        """Test office extractor can be imported and initialized"""
        try:
            from extractors.office_extractor import OfficeExtractor
            
            extractor = OfficeExtractor()
            assert extractor is not None
            
            supported_types = extractor.get_supported_mime_types()
            assert "application/msword" in supported_types
            assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in supported_types
            
        except ImportError as e:
            pytest.skip(f"Office extractor dependencies not available: {e}")

    @pytest.mark.asyncio
    async def test_metadata_factory(self):
        """Test metadata extractor factory"""
        from extractors.factory import MetadataExtractorFactory, metadata_factory
        
        # Test factory initialization
        assert metadata_factory is not None
        assert isinstance(metadata_factory, MetadataExtractorFactory)
        
        # Test supported MIME types
        supported_types = metadata_factory.get_supported_mime_types()
        assert len(supported_types) > 0
        assert "text/plain" in supported_types
        
        # Test extractor info
        info = metadata_factory.get_extractor_info()
        assert "total_extractors" in info
        assert info["total_extractors"] > 0
        assert "extractors" in info


class TestProcessingQueue:
    """Test processing queue system"""

    @pytest.mark.asyncio
    async def test_queue_manager_initialization(self):
        """Test processing queue manager initialization"""
        try:
            from processing.queue_manager import ProcessingQueueManager
            
            queue_manager = ProcessingQueueManager("redis://localhost:6379/1")
            assert queue_manager is not None
            
            # Test without Redis connection (should not fail initialization)
            assert queue_manager.redis_client is None
            
        except ImportError as e:
            pytest.skip(f"Redis dependencies not available: {e}")

    @pytest.mark.asyncio
    async def test_processing_task_creation(self):
        """Test processing task creation and serialization"""
        from processing.queue_manager import ProcessingTask
        
        task = ProcessingTask(
            id="test-task-123",
            document_id="doc-123",
            organization_id="org-123",
            user_id="user-123",
            task_type="metadata_extraction",
            file_path="/test/path.pdf",
            mime_type="application/pdf"
        )
        
        assert task.id == "test-task-123"
        assert task.document_id == "doc-123"
        assert task.task_type == "metadata_extraction"
        assert task.status == "pending"
        assert task.attempts == 0
        
        # Test serialization
        task_dict = task.to_dict()
        assert isinstance(task_dict, dict)
        assert task_dict["id"] == "test-task-123"
        
        # Test deserialization
        reconstructed_task = ProcessingTask.from_dict(task_dict)
        assert reconstructed_task.id == task.id
        assert reconstructed_task.document_id == task.document_id

    @pytest.mark.asyncio
    async def test_metadata_processor(self):
        """Test metadata processor functionality"""
        from processing.metadata_processor import MetadataProcessor, metadata_processor
        
        processor = MetadataProcessor()
        assert processor is not None
        assert processor.name == "MetadataProcessor"
        assert len(processor.supported_task_types) > 0
        assert "metadata_extraction" in processor.supported_task_types
        
        # Test processor info
        info = processor.get_processor_info()
        assert "name" in info
        assert "version" in info
        assert "supported_task_types" in info

    @pytest.mark.asyncio
    async def test_background_worker_initialization(self):
        """Test background worker initialization"""
        try:
            from processing.background_worker import BackgroundWorker
            from processing.queue_manager import ProcessingQueueManager
            
            queue_manager = ProcessingQueueManager("redis://localhost:6379/1")
            worker = BackgroundWorker(queue_manager, worker_id="test-worker")
            
            assert worker is not None
            assert worker.worker_id == "test-worker"
            assert not worker.is_running
            assert worker.max_concurrent_tasks == 3  # default
            
            # Test worker stats
            stats = worker.get_worker_stats()
            assert "worker_id" in stats
            assert "is_running" in stats
            assert stats["worker_id"] == "test-worker"
            
        except ImportError as e:
            pytest.skip(f"Worker dependencies not available: {e}")


class TestTextExtraction:
    """Test text extraction from various file formats"""

    @pytest.mark.asyncio
    async def test_text_file_extraction(self):
        """Test text extraction from plain text files"""
        from extractors.text_extractor import TextExtractor
        
        extractor = TextExtractor()
        
        # Create temporary text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            test_content = "This is a test document.\nIt has multiple lines.\nAnd some keywords like important, document, test."
            f.write(test_content)
            f.flush()
            
            try:
                file_path = Path(f.name)
                
                # Test extraction
                metadata = await extractor.extract_metadata(file_path, "text/plain")
                
                assert metadata is not None
                assert metadata.text_content == test_content
                assert metadata.word_count > 0
                assert metadata.character_count > 0
                assert len(metadata.keywords) > 0
                assert "text" in metadata.suggested_categories
                
            finally:
                Path(f.name).unlink(missing_ok=True)

    @pytest.mark.asyncio  
    async def test_html_file_extraction(self):
        """Test text extraction from HTML files"""
        from extractors.text_extractor import TextExtractor
        
        extractor = TextExtractor()
        
        # Create temporary HTML file
        html_content = """
        <html>
        <head><title>Test Document</title></head>
        <body>
            <h1>Main Heading</h1>
            <p>This is a paragraph with <strong>important</strong> content.</p>
            <p>Another paragraph with keywords like <em>extraction</em> and metadata.</p>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            f.flush()
            
            try:
                file_path = Path(f.name)
                
                # Test extraction
                metadata = await extractor.extract_metadata(file_path, "text/html")
                
                assert metadata is not None
                assert metadata.text_content is not None
                assert len(metadata.text_content) > 0
                assert "Main Heading" in metadata.text_content
                assert metadata.word_count > 0
                assert "web" in metadata.suggested_categories or "markup" in metadata.suggested_categories
                
            finally:
                Path(f.name).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_csv_file_extraction(self):
        """Test metadata extraction from CSV files"""
        from extractors.text_extractor import TextExtractor
        
        extractor = TextExtractor()
        
        # Create temporary CSV file
        csv_content = """Name,Age,City,Country
John Doe,30,New York,USA
Jane Smith,25,London,UK
Bob Johnson,35,Toronto,Canada
Alice Brown,28,Sydney,Australia"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            
            try:
                file_path = Path(f.name)
                
                # Test extraction
                metadata = await extractor.extract_metadata(file_path, "text/csv")
                
                assert metadata is not None
                assert metadata.text_content == csv_content
                assert metadata.word_count > 0
                assert "data" in metadata.suggested_categories
                assert "csv" in metadata.suggested_tags
                assert metadata.tables_detected >= 1
                
            finally:
                Path(f.name).unlink(missing_ok=True)


class TestExtractorErrorHandling:
    """Test error handling in extractors"""

    @pytest.mark.asyncio
    async def test_missing_file_handling(self):
        """Test handling of missing files"""
        from extractors.factory import metadata_factory
        
        missing_file = Path("/nonexistent/file.pdf")
        
        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            await metadata_factory.extract_metadata(missing_file, "application/pdf")

    @pytest.mark.asyncio
    async def test_invalid_mime_type_handling(self):
        """Test handling of invalid MIME types"""
        from extractors.factory import metadata_factory
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            f.flush()
            
            try:
                file_path = Path(f.name)
                
                # Test with unsupported MIME type
                metadata = await metadata_factory.extract_metadata(file_path, "application/unknown")
                
                # Should return metadata with warnings
                assert metadata is not None
                assert len(metadata.warnings) > 0
                assert "No extractor available" in metadata.warnings[0]
                
            finally:
                Path(f.name).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_corrupted_file_handling(self):
        """Test handling of corrupted files"""
        from extractors.text_extractor import TextExtractor
        
        extractor = TextExtractor()
        
        # Create file with invalid encoding
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            # Write invalid UTF-8 sequence
            f.write(b'\xff\xfe\x00\x00invalid utf-8 content\xff\xff')
            f.flush()
            
            try:
                file_path = Path(f.name)
                
                # Should handle gracefully
                metadata = await extractor.extract_metadata(file_path, "text/plain")
                
                # Should return metadata even if extraction partially failed
                assert metadata is not None
                # May have content or errors, but shouldn't crash
                
            finally:
                Path(f.name).unlink(missing_ok=True)


class TestPerformanceAndScaling:
    """Test performance characteristics of metadata extraction"""

    @pytest.mark.asyncio
    async def test_concurrent_extraction(self):
        """Test concurrent metadata extraction"""
        from extractors.text_extractor import TextExtractor
        
        extractor = TextExtractor()
        
        # Create multiple temporary files
        files_to_process = []
        
        try:
            for i in range(3):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(f"Test document {i} with content and keywords like test, document, content.")
                    files_to_process.append(Path(f.name))
            
            # Process files concurrently
            tasks = [
                extractor.extract_metadata(file_path, "text/plain")
                for file_path in files_to_process
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All should succeed
            assert len(results) == 3
            for result in results:
                assert result is not None
                assert result.text_content is not None
                assert result.word_count > 0
                
        finally:
            for file_path in files_to_process:
                file_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_large_file_handling(self):
        """Test handling of larger files"""
        from extractors.text_extractor import TextExtractor
        
        extractor = TextExtractor()
        
        # Create larger text file (not too large for testing)
        large_content = "This is a test line with various words and content.\n" * 1000  # ~50KB
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(large_content)
            f.flush()
            
            try:
                file_path = Path(f.name)
                
                # Should handle larger files
                metadata = await extractor.extract_metadata(file_path, "text/plain")
                
                assert metadata is not None
                assert metadata.text_content is not None
                assert metadata.word_count > 5000  # Should have many words
                assert metadata.extraction_duration_ms is not None
                assert metadata.extraction_duration_ms > 0
                
            finally:
                Path(f.name).unlink(missing_ok=True)