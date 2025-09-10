"""
File streaming functionality tests for content service.
"""

import pytest
import asyncio
import io
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from fastapi.testclient import TestClient
from fastapi.responses import StreamingResponse

import aiofiles


@pytest.mark.unit
class TestFileStreamingEndpoints:
    """Test file streaming endpoints."""
    
    @patch('httpx.AsyncClient')
    def test_stream_document_success(self, mock_client, client, valid_token, mock_user_data):
        """Test successful document streaming."""
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        document_id = "12345678-1234-5678-9012-123456789012"
        
        # Mock file content
        with patch('aiofiles.open', mock_open(read_data=b'PDF file content here')):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.stat') as mock_stat:
                    mock_stat.return_value.st_size = 1024
                    
                    response = client.get(
                        f"/api/v1/documents/{document_id}/stream",
                        headers={"Authorization": f"Bearer {valid_token}"}
                    )
        
        assert response.status_code == 200
        assert "application/octet-stream" in response.headers.get("content-type", "")
    
    @patch('httpx.AsyncClient')
    def test_stream_document_with_range_header(self, mock_client, client, valid_token, mock_user_data):
        """Test document streaming with range header for partial content."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        document_id = "12345678-1234-5678-9012-123456789012"
        
        with patch('aiofiles.open', mock_open(read_data=b'0123456789' * 100)):  # 1000 bytes
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.stat') as mock_stat:
                    mock_stat.return_value.st_size = 1000
                    
                    response = client.get(
                        f"/api/v1/documents/{document_id}/stream",
                        headers={
                            "Authorization": f"Bearer {valid_token}",
                            "Range": "bytes=0-499"  # Request first 500 bytes
                        }
                    )
        
        # Should return partial content
        assert response.status_code == 206 or response.status_code == 200  # Depends on implementation
        assert len(response.content) <= 500
    
    def test_stream_document_requires_auth(self, client):
        """Test that streaming requires authentication."""
        document_id = "12345678-1234-5678-9012-123456789012"
        
        response = client.get(f"/api/v1/documents/{document_id}/stream")
        
        assert response.status_code == 401
    
    @patch('httpx.AsyncClient')
    def test_stream_document_not_found(self, mock_client, client, valid_token, mock_user_data):
        """Test streaming non-existent document."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        document_id = "nonexistent-document-id"
        
        with patch('pathlib.Path.exists', return_value=False):
            response = client.get(
                f"/api/v1/documents/{document_id}/stream",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
        
        assert response.status_code == 404
    
    @patch('httpx.AsyncClient')
    def test_preview_document_success(self, mock_client, client, valid_token, mock_user_data):
        """Test successful document preview."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        document_id = "12345678-1234-5678-9012-123456789012"
        
        with patch('aiofiles.open', mock_open(read_data=b'%PDF-1.4\nPDF content')):
            with patch('pathlib.Path.exists', return_value=True):
                response = client.get(
                    f"/api/v1/documents/{document_id}/preview",
                    headers={"Authorization": f"Bearer {valid_token}"}
                )
        
        assert response.status_code == 200
        # Preview should include proper headers for browser display
        content_disposition = response.headers.get("content-disposition", "")
        assert "inline" in content_disposition or "attachment" in content_disposition


@pytest.mark.unit
class TestStreamingResponseGeneration:
    """Test streaming response generation utilities."""
    
    @pytest.mark.asyncio
    async def test_file_chunk_generator(self, sample_text_file):
        """Test file chunk generator for streaming."""
        async def file_chunk_generator(file_path: Path, chunk_size: int = 8192):
            """Generate file chunks for streaming."""
            async with aiofiles.open(file_path, 'rb') as file:
                while chunk := await file.read(chunk_size):
                    yield chunk
        
        chunks = []
        async for chunk in file_chunk_generator(sample_text_file, chunk_size=10):
            chunks.append(chunk)
        
        # Verify all chunks are read
        full_content = b''.join(chunks)
        expected_content = sample_text_file.read_bytes()
        assert full_content == expected_content
    
    @pytest.mark.asyncio
    async def test_range_file_generator(self, sample_text_file):
        """Test file range generator for partial content requests."""
        async def range_file_generator(file_path: Path, start: int, end: int, chunk_size: int = 8192):
            """Generate file chunks for a specific byte range."""
            async with aiofiles.open(file_path, 'rb') as file:
                await file.seek(start)
                remaining = end - start + 1
                
                while remaining > 0:
                    to_read = min(chunk_size, remaining)
                    chunk = await file.read(to_read)
                    if not chunk:
                        break
                    yield chunk
                    remaining -= len(chunk)
        
        # Read bytes 5-15 from the file
        chunks = []
        async for chunk in range_file_generator(sample_text_file, 5, 15):
            chunks.append(chunk)
        
        partial_content = b''.join(chunks)
        full_content = sample_text_file.read_bytes()
        expected_partial = full_content[5:16]  # end is inclusive
        
        assert partial_content == expected_partial
    
    def test_streaming_response_creation(self, sample_text_file):
        """Test creating streaming response."""
        def create_streaming_response(file_path: Path, content_type: str = "application/octet-stream"):
            """Create a StreamingResponse for file download."""
            async def file_generator():
                async with aiofiles.open(file_path, 'rb') as file:
                    while chunk := await file.read(8192):
                        yield chunk
            
            file_size = file_path.stat().st_size
            headers = {
                "content-length": str(file_size),
                "content-type": content_type,
                "content-disposition": f"inline; filename={file_path.name}"
            }
            
            return StreamingResponse(
                file_generator(),
                media_type=content_type,
                headers=headers
            )
        
        response = create_streaming_response(sample_text_file, "text/plain")
        
        assert response.media_type == "text/plain"
        assert "content-length" in response.headers
        assert "inline" in response.headers["content-disposition"]


@pytest.mark.integration
class TestFileStreamingIntegration:
    """Integration tests for file streaming."""
    
    @pytest.mark.asyncio
    async def test_large_file_streaming(self, large_file):
        """Test streaming large files efficiently."""
        chunk_size = 8192
        total_size = large_file.stat().st_size
        bytes_read = 0
        
        async with aiofiles.open(large_file, 'rb') as file:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                bytes_read += len(chunk)
                
                # Simulate processing chunk (e.g., sending over network)
                await asyncio.sleep(0)  # Yield control
        
        assert bytes_read == total_size
    
    @pytest.mark.asyncio
    async def test_concurrent_file_access(self, sample_text_file):
        """Test concurrent file access for streaming."""
        async def read_file_portion(start: int, size: int):
            """Read a portion of the file."""
            async with aiofiles.open(sample_text_file, 'rb') as file:
                await file.seek(start)
                return await file.read(size)
        
        # Simulate multiple concurrent readers
        file_size = sample_text_file.stat().st_size
        chunk_size = file_size // 3
        
        tasks = [
            read_file_portion(0, chunk_size),
            read_file_portion(chunk_size, chunk_size),
            read_file_portion(chunk_size * 2, file_size - (chunk_size * 2))
        ]
        
        chunks = await asyncio.gather(*tasks)
        
        # Verify all chunks combine to original file
        combined = b''.join(chunks)
        original = sample_text_file.read_bytes()
        assert combined == original
    
    @pytest.mark.asyncio
    async def test_streaming_with_error_handling(self, temp_directory):
        """Test streaming with file system errors."""
        non_existent_file = temp_directory / "non_existent.txt"
        
        # Test file not found
        try:
            async with aiofiles.open(non_existent_file, 'rb') as file:
                await file.read(1024)
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass
        
        # Test permission denied (simulate)
        restricted_file = temp_directory / "restricted.txt"
        restricted_file.write_text("content")
        
        # Mock permission error
        with patch('aiofiles.open', side_effect=PermissionError("Access denied")):
            try:
                async with aiofiles.open(restricted_file, 'rb') as file:
                    await file.read(1024)
                assert False, "Should have raised PermissionError"
            except PermissionError:
                pass
    
    def test_content_type_detection(self, sample_pdf_file, sample_image_file):
        """Test content type detection for streaming."""
        def detect_content_type(file_path: Path) -> str:
            """Detect content type from file extension."""
            suffix_map = {
                '.pdf': 'application/pdf',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.txt': 'text/plain',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }
            return suffix_map.get(file_path.suffix.lower(), 'application/octet-stream')
        
        assert detect_content_type(sample_pdf_file) == 'application/pdf'
        assert detect_content_type(sample_image_file) == 'image/jpeg'
    
    @pytest.mark.asyncio
    async def test_streaming_with_progress_tracking(self, large_file):
        """Test streaming with progress tracking."""
        total_size = large_file.stat().st_size
        bytes_streamed = 0
        progress_updates = []
        
        async def stream_with_progress(file_path: Path, chunk_size: int = 8192):
            """Stream file with progress tracking."""
            nonlocal bytes_streamed
            
            async with aiofiles.open(file_path, 'rb') as file:
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    
                    bytes_streamed += len(chunk)
                    progress = (bytes_streamed / total_size) * 100
                    progress_updates.append(progress)
                    
                    yield chunk
        
        chunks = []
        async for chunk in stream_with_progress(large_file):
            chunks.append(chunk)
        
        # Verify streaming completed
        assert bytes_streamed == total_size
        assert len(progress_updates) > 0
        assert progress_updates[-1] == 100.0  # Should reach 100%
        
        # Verify data integrity
        streamed_data = b''.join(chunks)
        original_data = large_file.read_bytes()
        assert streamed_data == original_data


@pytest.mark.performance
class TestStreamingPerformance:
    """Performance tests for file streaming."""
    
    @pytest.mark.asyncio
    async def test_optimal_chunk_size(self, large_file, performance_timer):
        """Test different chunk sizes for optimal performance."""
        chunk_sizes = [1024, 4096, 8192, 16384, 32768]
        results = {}
        
        for chunk_size in chunk_sizes:
            performance_timer.start()
            
            bytes_read = 0
            async with aiofiles.open(large_file, 'rb') as file:
                while chunk := await file.read(chunk_size):
                    bytes_read += len(chunk)
            
            performance_timer.stop()
            results[chunk_size] = {
                'time': performance_timer.elapsed,
                'bytes': bytes_read
            }
        
        # Verify all chunk sizes read the same amount
        expected_size = large_file.stat().st_size
        for chunk_size, result in results.items():
            assert result['bytes'] == expected_size
        
        # Find optimal chunk size (fastest)
        optimal_chunk_size = min(results.keys(), key=lambda k: results[k]['time'])
        print(f"Optimal chunk size: {optimal_chunk_size} bytes")
    
    @pytest.mark.asyncio
    async def test_memory_usage_streaming(self, large_file):
        """Test memory usage during streaming."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Stream large file
        async with aiofiles.open(large_file, 'rb') as file:
            while chunk := await file.read(8192):
                # Simulate minimal processing
                _ = len(chunk)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal for streaming
        # (not loading entire file into memory)
        file_size = large_file.stat().st_size
        assert memory_increase < file_size / 10  # Less than 10% of file size
    
    @pytest.mark.asyncio
    async def test_concurrent_streaming_performance(self, sample_text_file, performance_timer):
        """Test performance of concurrent file streaming."""
        concurrent_readers = 5
        
        async def stream_file():
            """Stream entire file."""
            bytes_read = 0
            async with aiofiles.open(sample_text_file, 'rb') as file:
                while chunk := await file.read(8192):
                    bytes_read += len(chunk)
            return bytes_read
        
        performance_timer.start()
        
        # Run concurrent streaming
        tasks = [stream_file() for _ in range(concurrent_readers)]
        results = await asyncio.gather(*tasks)
        
        performance_timer.stop()
        
        # Verify all readers read the complete file
        expected_size = sample_text_file.stat().st_size
        for bytes_read in results:
            assert bytes_read == expected_size
        
        # Performance should scale reasonably with concurrency
        print(f"Concurrent streaming time: {performance_timer.elapsed:.3f}s")


@pytest.mark.security
class TestStreamingSecurity:
    """Security tests for file streaming."""
    
    @patch('httpx.AsyncClient')
    def test_path_traversal_protection(self, mock_client, client, valid_token, mock_user_data):
        """Test protection against path traversal attacks."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Try to access file outside allowed directory
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\windows\\system32\\config\\sam"
        ]
        
        for malicious_path in malicious_paths:
            response = client.get(
                f"/api/v1/documents/{malicious_path}/stream",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            
            # Should reject malicious paths
            assert response.status_code in [400, 403, 404]
    
    @patch('httpx.AsyncClient')
    def test_file_size_limits(self, mock_client, client, valid_token, mock_user_data):
        """Test file size limits for streaming."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        document_id = "12345678-1234-5678-9012-123456789012"
        
        # Mock extremely large file
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.stat') as mock_stat:
                # Mock 10GB file
                mock_stat.return_value.st_size = 10 * 1024 * 1024 * 1024
                
                response = client.get(
                    f"/api/v1/documents/{document_id}/stream",
                    headers={"Authorization": f"Bearer {valid_token}"}
                )
        
        # Should handle large files appropriately
        # (either reject or stream efficiently)
        assert response.status_code in [200, 206, 413, 429]  # Various acceptable responses
    
    def test_content_type_validation(self):
        """Test content type validation for streaming."""
        def validate_content_type(content_type: str) -> bool:
            """Validate content type for security."""
            allowed_types = [
                'application/pdf',
                'image/jpeg',
                'image/png',
                'text/plain',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
            return content_type in allowed_types
        
        # Test allowed types
        assert validate_content_type('application/pdf') is True
        assert validate_content_type('image/jpeg') is True
        
        # Test disallowed types
        assert validate_content_type('application/x-executable') is False
        assert validate_content_type('text/html') is False
        assert validate_content_type('application/javascript') is False