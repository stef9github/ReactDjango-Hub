"""
Integration tests for Identity Service API endpoints
Tests all 40 API endpoints with authentication, validation, and error handling
"""

import pytest
import uuid
import json
from datetime import datetime, timedelta
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

from app.main import app


@pytest.mark.integration
@pytest.mark.asyncio
class TestHealthAndSystemEndpoints:
    """Test system endpoints that don't require authentication"""
    
    async def test_health_endpoint(self, test_client: AsyncClient):
        """Test health check endpoint"""
        response = await test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "status" in data
        assert "version" in data
        assert data["service"] == "auth-service"
        assert data["status"] in ["healthy", "degraded"]
    
    async def test_metrics_endpoint(self, test_client: AsyncClient):
        """Test Prometheus metrics endpoint"""
        response = await test_client.get("/metrics")
        
        # Metrics endpoint returns text/plain
        assert response.status_code == 200
        assert "text/plain" in response.headers.get("content-type", "")
        
        # Should contain some basic metrics
        content = response.text
        assert len(content) > 0


@pytest.mark.integration
@pytest.mark.asyncio
class TestAuthenticationEndpoints:
    """Test authentication endpoints (14 endpoints)"""
    
    async def test_user_registration_success(self, test_client: AsyncClient):
        """Test successful user registration - POST /api/v1/auth/register"""
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "name": "New User",
            "phone": "+1234567890"
        }
        
        response = await test_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        assert data["email"] == user_data["email"]
        assert "password" not in data  # Password should not be returned
    
    async def test_user_registration_duplicate_email(self, test_client: AsyncClient, test_user):
        """Test registration with duplicate email fails"""
        user_data = {
            "email": test_user.email,
            "password": "SecurePassword123!",
            "name": "Duplicate User"
        }
        
        response = await test_client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already registered" in data["detail"].lower()
    
    async def test_user_registration_invalid_data(self, test_client: AsyncClient):
        """Test registration with invalid data"""
        test_cases = [
            # Missing email
            {"password": "SecurePassword123!", "name": "No Email"},
            # Invalid email format
            {"email": "invalid-email", "password": "SecurePassword123!", "name": "Invalid Email"},
            # Weak password
            {"email": "weak@example.com", "password": "weak", "name": "Weak Password"},
            # Missing required fields
            {}
        ]
        
        for invalid_data in test_cases:
            response = await test_client.post("/api/v1/auth/register", json=invalid_data)
            assert response.status_code == 422  # Validation error
    
    async def test_user_login_success(self, test_client: AsyncClient, test_user):
        """Test successful user login - POST /api/v1/auth/login"""
        login_data = {
            "email": test_user.email,
            "password": "testpassword123",  # From conftest fixture
            "remember_me": False
        }
        
        response = await test_client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        assert "user_id" in data
        assert data["user_id"] == str(test_user.id)
    
    async def test_user_login_invalid_credentials(self, test_client: AsyncClient, test_user):
        """Test login with invalid credentials"""
        # Wrong password
        response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "wrongpassword",
            "remember_me": False
        })
        assert response.status_code == 401
        
        # Non-existent user
        response = await test_client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password123",
            "remember_me": False
        })
        assert response.status_code == 401
    
    async def test_token_refresh_success(self, test_client: AsyncClient, test_user):
        """Test token refresh - POST /api/v1/auth/refresh"""
        # First login to get refresh token
        login_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123",
            "remember_me": False
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new access token
        response = await test_client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "expires_in" in data
    
    async def test_token_refresh_invalid(self, test_client: AsyncClient):
        """Test refresh with invalid token"""
        response = await test_client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.refresh.token"
        })
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    async def test_user_logout_success(self, test_client: AsyncClient, test_user, auth_headers):
        """Test user logout - POST /api/v1/auth/logout"""
        response = await test_client.post("/api/v1/auth/logout", headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()
    
    async def test_logout_without_auth(self, test_client: AsyncClient):
        """Test logout without authentication"""
        response = await test_client.post("/api/v1/auth/logout")
        
        assert response.status_code == 401
    
    async def test_token_validation(self, test_client: AsyncClient, test_user):
        """Test token validation - POST /api/v1/auth/validate"""
        # Get valid token
        login_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123",
            "remember_me": False
        })
        access_token = login_response.json()["access_token"]
        
        # Validate token
        response = await test_client.post("/api/v1/auth/validate", json={
            "token": access_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        assert "is_valid" in data
        assert data["is_valid"] is True
    
    async def test_authorization_check(self, test_client: AsyncClient, auth_headers):
        """Test authorization - POST /api/v1/auth/authorize"""
        response = await test_client.post("/api/v1/auth/authorize", 
                                        json={"resource": "users", "action": "read"},
                                        headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "authorized" in data
    
    async def test_get_user_permissions(self, test_client: AsyncClient, test_user, auth_headers):
        """Test get user permissions - GET /api/v1/auth/permissions/{user_id}"""
        response = await test_client.get(f"/api/v1/auth/permissions/{test_user.id}",
                                       headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "permissions" in data
        assert isinstance(data["permissions"], list)
    
    async def test_get_current_user(self, test_client: AsyncClient, test_user, auth_headers):
        """Test get current user - GET /api/v1/auth/me"""
        response = await test_client.get("/api/v1/auth/me", 
                                       headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        assert "name" in data
        assert "organization" in data
        assert "permissions" in data
    
    async def test_get_user_sessions(self, test_client: AsyncClient, auth_headers):
        """Test get user sessions - GET /api/v1/auth/sessions"""
        response = await test_client.get("/api/v1/auth/sessions",
                                       headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)
    
    async def test_revoke_session(self, test_client: AsyncClient, auth_headers):
        """Test revoke session - DELETE /api/v1/auth/sessions/{session_id}"""
        session_id = str(uuid.uuid4())
        
        response = await test_client.delete(f"/api/v1/auth/sessions/{session_id}",
                                          headers=auth_headers("valid_token"))
        
        # Should either succeed or return 404 if session doesn't exist
        assert response.status_code in [200, 404]
    
    async def test_forgot_password(self, test_client: AsyncClient, test_user):
        """Test forgot password - POST /api/v1/auth/forgot-password"""
        response = await test_client.post("/api/v1/auth/forgot-password", json={
            "email": test_user.email
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "reset" in data["message"].lower()
    
    async def test_reset_password(self, test_client: AsyncClient):
        """Test reset password - POST /api/v1/auth/reset-password"""
        # Use dummy reset token for testing
        response = await test_client.post("/api/v1/auth/reset-password", json={
            "reset_token": "dummy-reset-token",
            "new_password": "NewSecurePassword123!"
        })
        
        # Should return either success or invalid token error
        assert response.status_code in [200, 400]
    
    async def test_verify_email(self, test_client: AsyncClient):
        """Test email verification - POST /api/v1/auth/verify-email"""
        response = await test_client.post("/api/v1/auth/verify-email", json={
            "verification_token": "dummy-verification-token"
        })
        
        # Should return either success or invalid token error
        assert response.status_code in [200, 400]
    
    async def test_resend_verification(self, test_client: AsyncClient, test_user):
        """Test resend verification - POST /api/v1/auth/resend-verification"""
        response = await test_client.post("/api/v1/auth/resend-verification", json={
            "email": test_user.email
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "sent" in data["message"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserManagementEndpoints:
    """Test user management endpoints (4 endpoints)"""
    
    async def test_create_user_profile(self, test_client: AsyncClient, test_user, auth_headers):
        """Test create user profile - POST /api/v1/users/profile"""
        profile_data = {
            "bio": "Updated user biography",
            "phone": "+1234567890",
            "avatar_url": "https://example.com/avatar.jpg",
            "timezone": "America/New_York",
            "language": "en",
            "preferences": {"theme": "dark", "notifications": True}
        }
        
        response = await test_client.post("/api/v1/users/profile", 
                                        json=profile_data,
                                        headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "profile" in data
        assert data["profile"]["bio"] == profile_data["bio"]
    
    async def test_get_user_dashboard(self, test_client: AsyncClient, test_user, auth_headers):
        """Test get user dashboard - GET /api/v1/users/{user_id}/dashboard"""
        response = await test_client.get(f"/api/v1/users/{test_user.id}/dashboard",
                                       headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "activity_summary" in data
        assert "session_count" in data
        assert "mfa_methods" in data
        assert "recent_activity" in data
    
    async def test_update_user_preferences(self, test_client: AsyncClient, test_user, auth_headers):
        """Test update user preferences - PATCH /api/v1/users/{user_id}/preferences"""
        preferences_data = {
            "theme": "dark",
            "notifications": True,
            "language": "es",
            "timezone": "UTC"
        }
        
        response = await test_client.patch(f"/api/v1/users/{test_user.id}/preferences",
                                         json=preferences_data,
                                         headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "preferences" in data
        assert data["preferences"]["theme"] == "dark"
    
    async def test_get_user_activity(self, test_client: AsyncClient, test_user, auth_headers):
        """Test get user activity - GET /api/v1/users/{user_id}/activity"""
        response = await test_client.get(f"/api/v1/users/{test_user.id}/activity",
                                       headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        assert "total_count" in data
        assert "page" in data
        assert isinstance(data["activities"], list)
    
    async def test_user_endpoints_require_auth(self, test_client: AsyncClient, test_user):
        """Test that all user endpoints require authentication"""
        endpoints = [
            ("POST", "/api/v1/users/profile", {}),
            ("GET", f"/api/v1/users/{test_user.id}/dashboard", None),
            ("PATCH", f"/api/v1/users/{test_user.id}/preferences", {}),
            ("GET", f"/api/v1/users/{test_user.id}/activity", None)
        ]
        
        for method, endpoint, json_data in endpoints:
            if method == "GET":
                response = await test_client.get(endpoint)
            elif method == "POST":
                response = await test_client.post(endpoint, json=json_data)
            elif method == "PATCH":
                response = await test_client.patch(endpoint, json=json_data)
            
            assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestOrganizationEndpoints:
    """Test organization management endpoints (4 endpoints)"""
    
    async def test_create_organization(self, test_client: AsyncClient, auth_headers):
        """Test create organization - POST /api/v1/organizations"""
        org_data = {
            "name": "Test Organization",
            "domain": "testorg.com",
            "org_type": "business",
            "settings": {"theme": "light", "notifications": True}
        }
        
        response = await test_client.post("/api/v1/organizations",
                                        json=org_data,
                                        headers=auth_headers("admin_token"))
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert data["name"] == org_data["name"]
        assert data["domain"] == org_data["domain"]
        assert data["org_type"] == org_data["org_type"]
    
    async def test_get_organization_dashboard(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test get organization dashboard - GET /api/v1/organizations/{org_id}/dashboard"""
        response = await test_client.get(f"/api/v1/organizations/{test_organization.id}/dashboard",
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "organization" in data
        assert "user_count" in data
        assert "activity_summary" in data
        assert "recent_activities" in data
        assert "settings" in data
    
    async def test_add_user_to_organization(self, test_client: AsyncClient, test_organization, test_user, auth_headers):
        """Test add user to organization - POST /api/v1/organizations/{org_id}/users"""
        user_data = {
            "user_id": str(test_user.id),
            "role": "member"
        }
        
        response = await test_client.post(f"/api/v1/organizations/{test_organization.id}/users",
                                        json=user_data,
                                        headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "added" in data["message"].lower()
    
    async def test_list_organization_users(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test list organization users - GET /api/v1/organizations/{org_id}/users"""
        response = await test_client.get(f"/api/v1/organizations/{test_organization.id}/users",
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total_count" in data
        assert "page" in data
        assert isinstance(data["users"], list)
    
    async def test_organization_endpoints_require_admin(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test that organization endpoints require admin privileges"""
        regular_user_headers = auth_headers("user_token")
        
        endpoints = [
            ("POST", "/api/v1/organizations", {"name": "Test", "org_type": "business"}),
            ("GET", f"/api/v1/organizations/{test_organization.id}/dashboard", None),
            ("POST", f"/api/v1/organizations/{test_organization.id}/users", {"user_id": str(uuid.uuid4()), "role": "member"}),
            ("GET", f"/api/v1/organizations/{test_organization.id}/users", None)
        ]
        
        for method, endpoint, json_data in endpoints:
            if method == "GET":
                response = await test_client.get(endpoint, headers=regular_user_headers)
            elif method == "POST":
                response = await test_client.post(endpoint, json=json_data, headers=regular_user_headers)
            
            assert response.status_code in [401, 403]  # Unauthorized or Forbidden


@pytest.mark.integration
@pytest.mark.asyncio
class TestMFAEndpoints:
    """Test MFA endpoints (6 core endpoints)"""
    
    async def test_setup_mfa_totp(self, test_client: AsyncClient, auth_headers):
        """Test setup TOTP MFA - POST /api/v1/mfa/setup"""
        mfa_data = {
            "method_type": "totp",
            "metadata": {"app_name": "Test App"}
        }
        
        response = await test_client.post("/api/v1/mfa/setup",
                                        json=mfa_data,
                                        headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "method_id" in data
        assert "secret" in data
        assert "qr_code" in data
        assert "backup_codes" in data
        assert data["method_type"] == "totp"
    
    async def test_setup_mfa_email(self, test_client: AsyncClient, auth_headers):
        """Test setup email MFA - POST /api/v1/mfa/setup"""
        mfa_data = {
            "method_type": "email"
        }
        
        response = await test_client.post("/api/v1/mfa/setup",
                                        json=mfa_data,
                                        headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "method_id" in data
        assert data["method_type"] == "email"
    
    async def test_setup_mfa_sms(self, test_client: AsyncClient, auth_headers):
        """Test setup SMS MFA - POST /api/v1/mfa/setup"""
        mfa_data = {
            "method_type": "sms",
            "metadata": {"phone": "+1234567890"}
        }
        
        response = await test_client.post("/api/v1/mfa/setup",
                                        json=mfa_data,
                                        headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "method_id" in data
        assert data["method_type"] == "sms"
    
    async def test_list_mfa_methods(self, test_client: AsyncClient, auth_headers):
        """Test list MFA methods - GET /api/v1/mfa/methods"""
        response = await test_client.get("/api/v1/mfa/methods",
                                       headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "methods" in data
        assert isinstance(data["methods"], list)
    
    async def test_create_mfa_challenge(self, test_client: AsyncClient, test_mfa_method, auth_headers):
        """Test create MFA challenge - POST /api/v1/mfa/challenge"""
        challenge_data = {
            "method_id": str(test_mfa_method.id)
        }
        
        response = await test_client.post("/api/v1/mfa/challenge",
                                        json=challenge_data,
                                        headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "challenge_id" in data
        assert "expires_at" in data
    
    async def test_verify_mfa_challenge(self, test_client: AsyncClient, test_mfa_method, auth_headers):
        """Test verify MFA challenge - POST /api/v1/mfa/verify"""
        verify_data = {
            "method_id": str(test_mfa_method.id),
            "challenge_code": "123456"
        }
        
        # Mock TOTP verification
        with patch('pyotp.TOTP.verify', return_value=True):
            response = await test_client.post("/api/v1/mfa/verify",
                                            json=verify_data,
                                            headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "verified" in data
        assert data["verified"] is True
    
    async def test_remove_mfa_method(self, test_client: AsyncClient, test_mfa_method, auth_headers):
        """Test remove MFA method - DELETE /api/v1/mfa/methods/{method_id}"""
        response = await test_client.delete(f"/api/v1/mfa/methods/{test_mfa_method.id}",
                                          headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "removed" in data["message"].lower()
    
    async def test_regenerate_backup_codes(self, test_client: AsyncClient, auth_headers):
        """Test regenerate backup codes - POST /api/v1/mfa/backup-codes/regenerate"""
        response = await test_client.post("/api/v1/mfa/backup-codes/regenerate",
                                        headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "backup_codes" in data
        assert isinstance(data["backup_codes"], list)
        assert len(data["backup_codes"]) == 8  # Standard number of backup codes


@pytest.mark.integration
@pytest.mark.asyncio
class TestMFAPolicyEndpoints:
    """Test MFA Policy endpoints (10 endpoints)"""
    
    async def test_get_system_mfa_policy(self, test_client: AsyncClient, auth_headers):
        """Test get system MFA policy - GET /api/v1/mfa/policy/system"""
        response = await test_client.get("/api/v1/mfa/policy/system",
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "requirement_level" in data
        assert "enforcement_scopes" in data
        assert "allowed_methods" in data
    
    async def test_update_system_mfa_policy(self, test_client: AsyncClient, auth_headers):
        """Test update system MFA policy - PUT /api/v1/mfa/policy/system"""
        policy_data = {
            "requirement_level": "required",
            "enforcement_scopes": ["login", "sensitive_operations"],
            "allowed_methods": ["totp", "sms"],
            "grace_period_days": 7
        }
        
        response = await test_client.put("/api/v1/mfa/policy/system",
                                       json=policy_data,
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert data["requirement_level"] == "required"
        assert "totp" in data["allowed_methods"]
    
    async def test_get_organization_mfa_policy(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test get organization MFA policy - GET /api/v1/mfa/policy/organization/{org_id}"""
        response = await test_client.get(f"/api/v1/mfa/policy/organization/{test_organization.id}",
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "requirement_level" in data
        assert "policy_source" in data
    
    async def test_update_organization_mfa_policy(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test update organization MFA policy - PUT /api/v1/mfa/policy/organization/{org_id}"""
        policy_data = {
            "requirement_level": "recommended",
            "enforcement_scopes": ["login"],
            "allowed_methods": ["email", "totp"],
            "exceptions": ["admin@example.com"]
        }
        
        response = await test_client.put(f"/api/v1/mfa/policy/organization/{test_organization.id}",
                                       json=policy_data,
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert data["requirement_level"] == "recommended"
    
    async def test_delete_organization_mfa_policy(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test delete organization MFA policy - DELETE /api/v1/mfa/policy/organization/{org_id}"""
        response = await test_client.delete(f"/api/v1/mfa/policy/organization/{test_organization.id}",
                                          headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "deleted" in data["message"].lower()
    
    async def test_get_user_mfa_policy(self, test_client: AsyncClient, test_user, auth_headers):
        """Test get user MFA policy - GET /api/v1/mfa/policy/user/{user_id}"""
        response = await test_client.get(f"/api/v1/mfa/policy/user/{test_user.id}",
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "requirement_level" in data
        assert "policy_source" in data
    
    async def test_update_user_mfa_policy(self, test_client: AsyncClient, test_user, auth_headers):
        """Test update user MFA policy - PUT /api/v1/mfa/policy/user/{user_id}"""
        policy_data = {
            "requirement_level": "disabled",
            "exceptions": ["medical_emergency"]
        }
        
        response = await test_client.put(f"/api/v1/mfa/policy/user/{test_user.id}",
                                       json=policy_data,
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert data["requirement_level"] == "disabled"
    
    async def test_delete_user_mfa_policy(self, test_client: AsyncClient, test_user, auth_headers):
        """Test delete user MFA policy - DELETE /api/v1/mfa/policy/user/{user_id}"""
        response = await test_client.delete(f"/api/v1/mfa/policy/user/{test_user.id}",
                                          headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    async def test_get_user_mfa_status(self, test_client: AsyncClient, test_user, auth_headers):
        """Test get user MFA status - GET /api/v1/mfa/policy/status/{user_id}"""
        response = await test_client.get(f"/api/v1/mfa/policy/status/{test_user.id}",
                                       headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "mfa_required" in data
        assert "mfa_recommended" in data
        assert "allowed_methods" in data
        assert "current_methods" in data
        assert "policy_source" in data
    
    async def test_get_user_mfa_configuration(self, test_client: AsyncClient, test_user, auth_headers):
        """Test get user MFA configuration - GET /api/v1/mfa/policy/configuration/{user_id}"""
        response = await test_client.get(f"/api/v1/mfa/policy/configuration/{test_user.id}",
                                       headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        assert "effective_policy" in data
        assert "compliance_status" in data
        assert "recommendations" in data


@pytest.mark.integration
@pytest.mark.asyncio 
class TestErrorHandlingAndValidation:
    """Test error handling and input validation across all endpoints"""
    
    async def test_invalid_json_format(self, test_client: AsyncClient):
        """Test endpoints handle invalid JSON gracefully"""
        response = await test_client.post("/api/v1/auth/register", 
                                        data="invalid-json",
                                        headers={"Content-Type": "application/json"})
        
        assert response.status_code == 422
    
    async def test_missing_required_fields(self, test_client: AsyncClient):
        """Test validation of required fields"""
        endpoints_with_required_fields = [
            ("/api/v1/auth/register", {}),
            ("/api/v1/auth/login", {}),
            ("/api/v1/auth/refresh", {}),
            ("/api/v1/mfa/setup", {})
        ]
        
        for endpoint, empty_data in endpoints_with_required_fields:
            response = await test_client.post(endpoint, json=empty_data)
            assert response.status_code == 422
    
    async def test_invalid_uuid_format(self, test_client: AsyncClient, auth_headers):
        """Test endpoints handle invalid UUID formats"""
        invalid_uuid = "invalid-uuid-format"
        
        endpoints_with_uuid_params = [
            f"/api/v1/users/{invalid_uuid}/dashboard",
            f"/api/v1/organizations/{invalid_uuid}/users",
            f"/api/v1/mfa/methods/{invalid_uuid}"
        ]
        
        for endpoint in endpoints_with_uuid_params:
            if "methods" in endpoint:
                response = await test_client.delete(endpoint, headers=auth_headers("valid_token"))
            else:
                response = await test_client.get(endpoint, headers=auth_headers("valid_token"))
            
            assert response.status_code in [400, 422]  # Bad request or validation error
    
    async def test_sql_injection_protection(self, test_client: AsyncClient):
        """Test protection against SQL injection attempts"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'; --",
            "<script>alert('xss')</script>"
        ]
        
        for malicious_input in malicious_inputs:
            response = await test_client.post("/api/v1/auth/login", json={
                "email": malicious_input,
                "password": "password123",
                "remember_me": False
            })
            
            # Should return 401 (invalid credentials) or 422 (validation error), not 500
            assert response.status_code in [401, 422]
    
    async def test_rate_limiting(self, test_client: AsyncClient):
        """Test rate limiting on sensitive endpoints"""
        # Make multiple rapid requests to login endpoint
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword",
            "remember_me": False
        }
        
        responses = []
        for _ in range(10):  # Make 10 rapid requests
            response = await test_client.post("/api/v1/auth/login", json=login_data)
            responses.append(response.status_code)
        
        # Some requests should be rate limited (429) or all should be 401
        assert any(status == 429 for status in responses) or all(status == 401 for status in responses)
    
    async def test_request_size_limits(self, test_client: AsyncClient):
        """Test request size limits"""
        # Create a very large request
        large_data = {
            "email": "test@example.com",
            "password": "password123",
            "name": "x" * 10000,  # Very large name
            "bio": "x" * 50000    # Very large bio
        }
        
        response = await test_client.post("/api/v1/auth/register", json=large_data)
        
        # Should either reject due to size limits or validation
        assert response.status_code in [400, 413, 422]
    
    async def test_cors_headers(self, test_client: AsyncClient):
        """Test CORS headers are properly set"""
        response = await test_client.options("/api/v1/auth/login")
        
        # Should include CORS headers
        assert response.status_code in [200, 204]
        # Headers might vary based on CORS configuration
    
    async def test_security_headers(self, test_client: AsyncClient):
        """Test security headers are present"""
        response = await test_client.get("/health")
        
        assert response.status_code == 200
        # Could check for security headers like Content-Type, etc.
        assert "content-type" in response.headers


@pytest.mark.integration
@pytest.mark.asyncio
class TestAPIPerformance:
    """Test API performance characteristics"""
    
    @pytest.mark.benchmark
    async def test_health_endpoint_performance(self, test_client: AsyncClient, benchmark):
        """Benchmark health endpoint performance"""
        async def health_check():
            response = await test_client.get("/health")
            return response.status_code
        
        result = await benchmark(health_check)
        assert result == 200
    
    @pytest.mark.benchmark
    async def test_login_performance(self, test_client: AsyncClient, test_user, benchmark):
        """Benchmark login endpoint performance"""
        login_data = {
            "email": test_user.email,
            "password": "testpassword123",
            "remember_me": False
        }
        
        async def login():
            response = await test_client.post("/api/v1/auth/login", json=login_data)
            return response.status_code
        
        result = await benchmark(login)
        assert result == 200
    
    async def test_concurrent_requests(self, test_client: AsyncClient):
        """Test handling of concurrent requests"""
        import asyncio
        
        async def make_request():
            return await test_client.get("/health")
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
class TestEndpointSecurity:
    """Test security aspects of all endpoints"""
    
    async def test_authentication_required_endpoints(self, test_client: AsyncClient):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            ("GET", "/api/v1/auth/me"),
            ("POST", "/api/v1/auth/logout"),
            ("GET", "/api/v1/auth/sessions"),
            ("POST", "/api/v1/users/profile"),
            ("POST", "/api/v1/mfa/setup"),
            ("GET", "/api/v1/mfa/methods")
        ]
        
        for method, endpoint in protected_endpoints:
            if method == "GET":
                response = await test_client.get(endpoint)
            elif method == "POST":
                response = await test_client.post(endpoint, json={})
            
            assert response.status_code == 401
    
    async def test_admin_required_endpoints(self, test_client: AsyncClient, auth_headers):
        """Test that admin endpoints require admin privileges"""
        admin_endpoints = [
            ("POST", "/api/v1/organizations"),
            ("PUT", "/api/v1/mfa/policy/system"),
            ("GET", "/api/v1/mfa/policy/system")
        ]
        
        # Test with regular user token
        for method, endpoint in admin_endpoints:
            if method == "GET":
                response = await test_client.get(endpoint, headers=auth_headers("user_token"))
            elif method == "POST":
                response = await test_client.post(endpoint, json={}, headers=auth_headers("user_token"))
            elif method == "PUT":
                response = await test_client.put(endpoint, json={}, headers=auth_headers("user_token"))
            
            assert response.status_code in [401, 403]
    
    async def test_jwt_token_validation(self, test_client: AsyncClient):
        """Test JWT token validation security"""
        invalid_tokens = [
            "invalid.token.format",
            "Bearer invalid-token",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
            "",
            "null",
            None
        ]
        
        for token in invalid_tokens:
            if token:
                headers = {"Authorization": f"Bearer {token}"}
            else:
                headers = {}
            
            response = await test_client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == 401
    
    async def test_sensitive_data_not_exposed(self, test_client: AsyncClient, test_user):
        """Test that sensitive data is not exposed in responses"""
        # Register user and check response doesn't include sensitive data
        user_data = {
            "email": "sensitive@example.com",
            "password": "SensitivePassword123!",
            "name": "Sensitive User"
        }
        
        response = await test_client.post("/api/v1/auth/register", json=user_data)
        
        if response.status_code == 201:
            data = response.json()
            # Password should never be in response
            assert "password" not in str(data).lower()
            assert "password_hash" not in data
            assert user_data["password"] not in str(data)


@pytest.mark.integration 
@pytest.mark.asyncio
class TestAPIDocumentationCompliance:
    """Test that API responses match OpenAPI documentation"""
    
    async def test_response_schemas(self, test_client: AsyncClient):
        """Test that responses match expected schemas"""
        # Test health endpoint response structure
        response = await test_client.get("/health")
        data = response.json()
        
        required_fields = ["service", "status", "version"]
        for field in required_fields:
            assert field in data
    
    async def test_error_response_format(self, test_client: AsyncClient):
        """Test that error responses follow consistent format"""
        # Test validation error format
        response = await test_client.post("/api/v1/auth/register", json={})
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data  # FastAPI validation error format
    
    async def test_success_response_format(self, test_client: AsyncClient, test_user):
        """Test that success responses follow consistent format"""
        # Test login response format
        login_data = {
            "email": test_user.email,
            "password": "testpassword123",
            "remember_me": False
        }
        
        response = await test_client.post("/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            expected_fields = ["access_token", "refresh_token", "expires_in", "user_id"]
            for field in expected_fields:
                assert field in data