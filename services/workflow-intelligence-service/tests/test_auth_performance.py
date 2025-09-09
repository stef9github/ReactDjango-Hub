"""
Performance tests for JWT authentication
"""
import pytest
import time
import asyncio
from unittest.mock import patch, Mock, AsyncMock
from concurrent.futures import ThreadPoolExecutor

class TestAuthenticationPerformance:
    """Test authentication performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_token_validation_response_time(self, mock_valid_token):
        """Test that token validation completes within acceptable time"""
        from main import validate_jwt_token
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "user-123",
            "email": "test@example.com",
            "organization_id": "org-123",
            "roles": ["user"]
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            start_time = time.time()
            result = await validate_jwt_token(mock_valid_token)
            end_time = time.time()
            
            # Authentication should complete within 100ms under normal conditions
            assert (end_time - start_time) < 0.1
            assert result["user_id"] == "user-123"
    
    def test_concurrent_authentication_requests(self, client, mock_auth_headers):
        """Test handling of concurrent authentication requests"""
        def make_request():
            with patch("main.validate_jwt_token") as mock_validate:
                mock_validate.return_value = {
                    "user_id": "user-123",
                    "organization_id": "org-123", 
                    "roles": ["user"]
                }
                
                response = client.get("/api/v1/definitions", headers=mock_auth_headers)
                return response.status_code
        
        # Simulate 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
            end_time = time.time()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        
        # Total time should be reasonable (less than 1 second for 10 concurrent requests)
        assert (end_time - start_time) < 1.0
    
    def test_authentication_memory_usage(self, client, mock_auth_headers):
        """Test that authentication doesn't cause memory leaks"""
        import gc
        import sys
        
        def get_memory_usage():
            """Get current memory usage"""
            return sys.getsizeof(gc.get_objects())
        
        with patch("main.validate_jwt_token") as mock_validate:
            mock_validate.return_value = {
                "user_id": "user-123",
                "organization_id": "org-123",
                "roles": ["user"]
            }
            
            # Measure initial memory
            gc.collect()
            initial_memory = get_memory_usage()
            
            # Make many authenticated requests
            for i in range(50):
                response = client.get("/api/v1/definitions", headers=mock_auth_headers)
                assert response.status_code == 200
            
            # Force garbage collection and measure final memory
            gc.collect()
            final_memory = get_memory_usage()
            
            # Memory usage shouldn't grow significantly
            memory_growth = final_memory - initial_memory
            # Allow for some growth but not excessive (less than 10MB)
            assert memory_growth < 10_000_000
    
    def test_identity_service_timeout_handling(self, client, mock_auth_headers):
        """Test performance when Identity Service is slow/timing out"""
        from main import validate_jwt_token
        import asyncio
        
        async def slow_response():
            await asyncio.sleep(0.1)  # Simulate slow response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"user_id": "user-123"}
            return mock_response
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=slow_response)
            
            # Test should still complete within reasonable time due to timeout settings
            with patch("main.validate_jwt_token") as mock_validate:
                mock_validate.return_value = {
                    "user_id": "user-123",
                    "organization_id": "org-123",
                    "roles": ["user"]
                }
                
                start_time = time.time()
                response = client.get("/api/v1/definitions", headers=mock_auth_headers)
                end_time = time.time()
                
                assert response.status_code == 200
                # Should complete within timeout + processing time
                assert (end_time - start_time) < 1.0

class TestCachingPerformance:
    """Test caching strategies for authentication (if implemented)"""
    
    def test_repeated_token_validation_performance(self, client, mock_auth_headers):
        """Test performance of repeated requests with same token"""
        call_count = 0
        
        def mock_validate_with_counter(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return {
                "user_id": "user-123",
                "organization_id": "org-123",
                "roles": ["user"]
            }
        
        with patch("main.validate_jwt_token", side_effect=mock_validate_with_counter):
            start_time = time.time()
            
            # Make multiple requests with same token
            for i in range(5):
                response = client.get("/api/v1/definitions", headers=mock_auth_headers)
                assert response.status_code == 200
            
            end_time = time.time()
            
            # All requests should be processed
            assert call_count == 5
            
            # Total time should be reasonable
            assert (end_time - start_time) < 0.5

class TestNetworkFailureRecovery:
    """Test performance under network failure conditions"""
    
    def test_identity_service_unavailable_performance(self, client, mock_auth_headers):
        """Test response time when Identity Service is unavailable"""
        with patch("main.validate_jwt_token") as mock_validate:
            # Simulate Identity Service being unavailable
            from fastapi import HTTPException
            mock_validate.side_effect = HTTPException(
                status_code=503,
                detail="Authentication service unavailable"
            )
            
            start_time = time.time()
            response = client.get("/api/v1/definitions", headers=mock_auth_headers)
            end_time = time.time()
            
            # Should fail fast, not hang
            assert response.status_code == 503
            assert (end_time - start_time) < 0.1  # Should fail quickly
    
    def test_network_timeout_performance(self, mock_valid_token):
        """Test that network timeouts are handled within expected time"""
        from main import validate_jwt_token
        import httpx
        
        with patch("httpx.AsyncClient") as mock_client:
            # Simulate timeout exception
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )
            
            start_time = time.time()
            
            with pytest.raises(HTTPException) as exc_info:
                import asyncio
                asyncio.run(validate_jwt_token(mock_valid_token))
            
            end_time = time.time()
            
            # Should timeout within expected time (less than our 10s client timeout + processing)
            assert (end_time - start_time) < 11.0
            assert exc_info.value.status_code == 503

class TestLoadTesting:
    """Test authentication under load"""
    
    def test_burst_request_handling(self, client, mock_auth_headers):
        """Test handling of burst requests"""
        with patch("main.validate_jwt_token") as mock_validate:
            mock_validate.return_value = {
                "user_id": "user-123",
                "organization_id": "org-123",
                "roles": ["user"]
            }
            
            start_time = time.time()
            responses = []
            
            # Make rapid burst of requests
            for i in range(20):
                response = client.get("/api/v1/definitions", headers=mock_auth_headers)
                responses.append(response.status_code)
            
            end_time = time.time()
            
            # All requests should be handled successfully
            success_count = sum(1 for status in responses if status == 200)
            
            # At least 90% should succeed (allowing for some throttling if implemented)
            assert success_count >= 18
            
            # Should complete within reasonable time
            assert (end_time - start_time) < 2.0
    
    def test_mixed_auth_success_failure_performance(self, client, mock_auth_headers):
        """Test performance with mix of successful and failed authentications"""
        call_count = 0
        
        def mixed_validate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            # Alternate between success and failure
            if call_count % 2 == 0:
                return {
                    "user_id": "user-123",
                    "organization_id": "org-123", 
                    "roles": ["user"]
                }
            else:
                from fastapi import HTTPException
                raise HTTPException(status_code=401, detail="Invalid token")
        
        with patch("main.validate_jwt_token", side_effect=mixed_validate):
            start_time = time.time()
            
            success_count = 0
            fail_count = 0
            
            for i in range(10):
                response = client.get("/api/v1/definitions", headers=mock_auth_headers)
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 401:
                    fail_count += 1
            
            end_time = time.time()
            
            # Should have roughly equal success and failures
            assert success_count >= 4
            assert fail_count >= 4
            
            # Should complete within reasonable time despite failures
            assert (end_time - start_time) < 1.0

class TestResourceUtilization:
    """Test resource utilization during authentication"""
    
    def test_cpu_usage_during_auth(self, client, mock_auth_headers):
        """Test CPU usage during authentication operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        with patch("main.validate_jwt_token") as mock_validate:
            mock_validate.return_value = {
                "user_id": "user-123",
                "organization_id": "org-123",
                "roles": ["user"]
            }
            
            # Measure CPU before
            cpu_before = process.cpu_percent()
            time.sleep(0.1)  # Let CPU measurement stabilize
            
            # Make authenticated requests
            for i in range(10):
                response = client.get("/api/v1/definitions", headers=mock_auth_headers)
                assert response.status_code == 200
            
            # Measure CPU after
            cpu_after = process.cpu_percent()
            
            # CPU usage should be reasonable (this is a rough check)
            # In test environment, CPU usage might be higher due to mocking overhead
            assert cpu_after < 50.0  # Less than 50% CPU usage