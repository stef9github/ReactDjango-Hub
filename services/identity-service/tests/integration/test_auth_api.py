"""
Integration tests for Authentication API endpoints
Tests the complete API flows including database interactions
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.auth
class TestAuthAPI:
    """Test authentication API endpoints with full integration"""
    
    @pytest.mark.asyncio
    async def test_register_login_flow(self, test_client: AsyncClient):
        """Test complete register -> login flow"""
        
        # Register new user
        register_data = {
            "email": "integration@example.com",
            "password": "testpassword123",
            "first_name": "Integration",
            "last_name": "Test"
        }
        
        response = await test_client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 200
        
        register_result = response.json()
        assert register_result["email"] == "integration@example.com"
        assert "access_token" in register_result
        assert "user_id" in register_result
        
        # Login with registered user
        login_data = {
            "email": "integration@example.com",
            "password": "testpassword123"
        }
        
        response = await test_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        login_result = response.json()
        assert login_result["email"] == "integration@example.com"
        assert "access_token" in login_result
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, test_client: AsyncClient):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = await test_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_token_validation(self, test_client: AsyncClient, test_user):
        """Test token validation endpoint"""
        
        # First login to get token
        login_data = {
            "email": "testuser@example.com",
            "password": "testpassword123"
        }
        
        response = await test_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        login_result = response.json()
        access_token = login_result["access_token"]
        
        # Validate token
        validate_data = {"token": access_token}
        response = await test_client.post("/api/v1/auth/validate", json=validate_data)
        assert response.status_code == 200
        
        validation_result = response.json()
        assert validation_result["valid"] is True
        assert validation_result["user_id"] is not None
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_with_token(self, test_client: AsyncClient, test_user):
        """Test accessing protected endpoint with valid token"""
        
        # Login to get token
        login_data = {
            "email": "testuser@example.com",
            "password": "testpassword123"
        }
        
        response = await test_client.post("/api/v1/auth/login", json=login_data)
        login_result = response.json()
        access_token = login_result["access_token"]
        
        # Access protected endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await test_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["email"] == "testuser@example.com"
    
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, test_client: AsyncClient):
        """Test accessing protected endpoint without token"""
        response = await test_client.get("/api/v1/auth/me")
        assert response.status_code == 403  # or 401 depending on your setup
    
    @pytest.mark.asyncio
    async def test_logout(self, test_client: AsyncClient, test_user):
        """Test logout functionality"""
        
        # Login first
        login_data = {
            "email": "testuser@example.com",
            "password": "testpassword123"
        }
        
        response = await test_client.post("/api/v1/auth/login", json=login_data)
        login_result = response.json()
        access_token = login_result["access_token"]
        refresh_token = login_result.get("refresh_token")
        
        # Logout
        headers = {"Authorization": f"Bearer {access_token}"}
        logout_data = {"refresh_token": refresh_token} if refresh_token else {}
        
        response = await test_client.post("/api/v1/auth/logout", 
                                        json=logout_data, headers=headers)
        assert response.status_code == 200


@pytest.mark.integration
class TestUserManagementAPI:
    """Test user management API endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_user_profile(self, test_client: AsyncClient):
        """Test creating user profile via API"""
        profile_data = {
            "email": "profile@example.com",
            "password": "testpassword123",
            "first_name": "Profile",
            "last_name": "User",
            "job_title": "Software Engineer",
            "department": "Engineering",
            "skills": ["Python", "FastAPI", "PostgreSQL"]
        }
        
        response = await test_client.post("/api/v1/users/profile", json=profile_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["email"] == "profile@example.com"
        assert result["first_name"] == "Profile"
        assert result["job_title"] == "Software Engineer"
        assert result["skills"] == ["Python", "FastAPI", "PostgreSQL"]
    
    @pytest.mark.asyncio
    async def test_get_user_dashboard(self, test_client: AsyncClient, test_user):
        """Test getting user dashboard data"""
        
        # Login to get token
        login_data = {
            "email": "testuser@example.com",
            "password": "testpassword123"
        }
        
        response = await test_client.post("/api/v1/auth/login", json=login_data)
        login_result = response.json()
        access_token = login_result["access_token"]
        user_id = login_result["user_id"]
        
        # Get dashboard
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await test_client.get(f"/api/v1/users/{user_id}/dashboard", 
                                       headers=headers)
        assert response.status_code == 200
        
        dashboard = response.json()
        assert "user" in dashboard
        assert "activity_summary" in dashboard


@pytest.mark.integration
class TestHealthEndpoints:
    """Test health and monitoring endpoints"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, test_client: AsyncClient):
        """Test health check endpoint"""
        response = await test_client.get("/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["service"] == "auth-service"
        assert "status" in health_data
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, test_client: AsyncClient):
        """Test metrics endpoint"""
        response = await test_client.get("/metrics")
        assert response.status_code == 200
        
        # Prometheus metrics should be in text format
        assert response.headers["content-type"].startswith("text/plain")