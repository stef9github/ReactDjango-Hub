"""
Tests for health check endpoint and functionality
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from main import app

class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_endpoint_success(self):
        """Test successful health check"""
        with patch('main.get_uptime') as mock_uptime, \
             patch('main.get_memory_usage') as mock_memory, \
             patch('main.get_active_connections') as mock_connections, \
             patch('main.redis.from_url') as mock_redis, \
             patch('main.httpx.AsyncClient') as mock_httpx:
            
            # Mock helper functions
            mock_uptime.return_value = 3600
            mock_memory.return_value = 128.5
            mock_connections.return_value = 10
            
            # Mock Redis health check
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock(return_value=True)
            mock_redis_client.close = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            # Mock Identity Service health check
            mock_http_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_http_client.get.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_http_client
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["service"] == "communication-service"
            assert data["status"] == "healthy"
            assert data["version"] == "1.0.0"
            assert data["port"] == 8003
            
            # Check dependencies
            assert "dependencies" in data
            assert data["dependencies"]["redis"] == "healthy"
            assert data["dependencies"]["identity-service"] == "healthy"
            
            # Check metrics
            assert "metrics" in data
            assert data["metrics"]["uptime_seconds"] == 3600
            assert data["metrics"]["memory_usage_mb"] == 128.5
            assert data["metrics"]["active_connections"] == 10
    
    def test_health_endpoint_degraded_redis(self):
        """Test health check with Redis failure"""
        with patch('main.get_uptime') as mock_uptime, \
             patch('main.get_memory_usage') as mock_memory, \
             patch('main.get_active_connections') as mock_connections, \
             patch('main.redis.from_url') as mock_redis, \
             patch('main.httpx.AsyncClient') as mock_httpx:
            
            mock_uptime.return_value = 3600
            mock_memory.return_value = 128.5
            mock_connections.return_value = 10
            
            # Mock Redis failure
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock(side_effect=Exception("Redis connection failed"))
            mock_redis_client.close = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            # Mock Identity Service success
            mock_http_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_http_client.get.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_http_client
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "degraded"
            assert data["dependencies"]["redis"] == "unhealthy"
            assert data["dependencies"]["identity-service"] == "healthy"
    
    def test_health_endpoint_degraded_identity_service(self):
        """Test health check with Identity Service failure"""
        with patch('main.get_uptime') as mock_uptime, \
             patch('main.get_memory_usage') as mock_memory, \
             patch('main.get_active_connections') as mock_connections, \
             patch('main.redis.from_url') as mock_redis, \
             patch('main.httpx.AsyncClient') as mock_httpx:
            
            mock_uptime.return_value = 3600
            mock_memory.return_value = 128.5
            mock_connections.return_value = 10
            
            # Mock Redis success
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock(return_value=True)
            mock_redis_client.close = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            # Mock Identity Service failure
            mock_http_client = AsyncMock()
            mock_http_client.get.side_effect = Exception("Service unavailable")
            mock_httpx.return_value.__aenter__.return_value = mock_http_client
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "degraded"
            assert data["dependencies"]["redis"] == "healthy"
            assert data["dependencies"]["identity-service"] == "unhealthy"
    
    def test_health_endpoint_all_degraded(self):
        """Test health check with all dependencies failing"""
        with patch('main.get_uptime') as mock_uptime, \
             patch('main.get_memory_usage') as mock_memory, \
             patch('main.get_active_connections') as mock_connections, \
             patch('main.redis.from_url') as mock_redis, \
             patch('main.httpx.AsyncClient') as mock_httpx:
            
            mock_uptime.return_value = 3600
            mock_memory.return_value = 128.5
            mock_connections.return_value = 10
            
            # Mock Redis failure
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock(side_effect=Exception("Redis failed"))
            mock_redis_client.close = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            # Mock Identity Service failure
            mock_http_client = AsyncMock()
            mock_http_client.get.side_effect = Exception("Service failed")
            mock_httpx.return_value.__aenter__.return_value = mock_http_client
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "degraded"
            assert data["dependencies"]["redis"] == "unhealthy"
            assert data["dependencies"]["identity-service"] == "unhealthy"
            assert data["dependencies"]["celery-workers"] == "not-implemented"

class TestHealthHelperFunctions:
    """Test health check helper functions"""
    
    def test_get_uptime(self):
        """Test uptime calculation"""
        import time
        from main import start_time, get_uptime
        
        # Mock start_time to be 100 seconds ago
        with patch('main.start_time', time.time() - 100):
            uptime = get_uptime()
            
            # Should be approximately 100 seconds (allow small variance)
            assert 95 <= uptime <= 105
    
    def test_get_memory_usage(self):
        """Test memory usage retrieval"""
        with patch('main.psutil.Process') as mock_process_class:
            mock_process = MagicMock()
            mock_memory_info = MagicMock()
            mock_memory_info.rss = 134217728  # 128 MB in bytes
            mock_process.memory_info.return_value = mock_memory_info
            mock_process_class.return_value = mock_process
            
            from main import get_memory_usage
            memory_mb = get_memory_usage()
            
            assert memory_mb == 128.0  # Should be 128.0 MB
    
    def test_get_active_connections(self):
        """Test active connections count"""
        from main import get_active_connections
        
        # Currently returns 0 as placeholder
        connections = get_active_connections()
        assert connections == 0

class TestHealthIntegration:
    """Integration tests for health functionality"""
    
    def test_health_with_real_app_structure(self):
        """Test health endpoint with actual app structure"""
        client = TestClient(app)
        
        # This test will use the actual main.py health endpoint
        # but mock external dependencies
        with patch('main.redis.from_url') as mock_redis, \
             patch('main.httpx.AsyncClient') as mock_httpx:
            
            # Mock successful Redis
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock(return_value=True)
            mock_redis_client.close = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            # Mock successful Identity Service
            mock_http_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_http_client.get.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_http_client
            
            response = client.get("/health")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            
            data = response.json()
            
            # Verify required fields exist
            required_fields = ["service", "status", "version", "port", "dependencies", "metrics"]
            for field in required_fields:
                assert field in data
            
            # Verify dependencies structure
            assert isinstance(data["dependencies"], dict)
            dependency_keys = ["redis", "identity-service", "celery-workers"]
            for key in dependency_keys:
                assert key in data["dependencies"]
            
            # Verify metrics structure
            assert isinstance(data["metrics"], dict)
            metric_keys = ["uptime_seconds", "active_connections", "memory_usage_mb"]
            for key in metric_keys:
                assert key in data["metrics"]
                assert isinstance(data["metrics"][key], (int, float))

class TestHealthResponseFormat:
    """Test health response format compliance"""
    
    def test_health_response_schema(self):
        """Test that health response matches expected schema"""
        with patch('main.redis.from_url') as mock_redis, \
             patch('main.httpx.AsyncClient') as mock_httpx:
            
            # Mock all dependencies as healthy
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock(return_value=True)
            mock_redis_client.close = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            mock_http_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_http_client.get.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_http_client
            
            client = TestClient(app)
            response = client.get("/health")
            data = response.json()
            
            # Verify top-level schema
            assert isinstance(data["service"], str)
            assert data["status"] in ["healthy", "degraded", "unhealthy"]
            assert isinstance(data["version"], str)
            assert isinstance(data["port"], int)
            assert isinstance(data["dependencies"], dict)
            assert isinstance(data["metrics"], dict)
            
            # Verify dependencies values
            for dep_name, dep_status in data["dependencies"].items():
                assert dep_status in ["healthy", "unhealthy", "not-implemented"]
            
            # Verify metrics values
            assert isinstance(data["metrics"]["uptime_seconds"], int)
            assert isinstance(data["metrics"]["active_connections"], int)
            assert isinstance(data["metrics"]["memory_usage_mb"], (int, float))
            
            # Verify numeric ranges make sense
            assert data["metrics"]["uptime_seconds"] >= 0
            assert data["metrics"]["active_connections"] >= 0
            assert data["metrics"]["memory_usage_mb"] > 0