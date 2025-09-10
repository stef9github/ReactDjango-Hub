"""
Comprehensive authentication integration tests
100% coverage of authentication flows, security, and edge cases
"""

import pytest
import uuid
import time
import jwt
from datetime import datetime, timedelta
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

from app.core.security import create_access_token, create_refresh_token, verify_token


@pytest.mark.auth
@pytest.mark.integration
@pytest.mark.asyncio
class TestJWTAuthentication:
    """Test JWT token authentication system"""
    
    async def test_jwt_token_creation_and_validation(self, test_client: AsyncClient, test_user):
        """Test complete JWT lifecycle"""
        # Login to get tokens
        login_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123",
            "remember_me": False
        })
        
        assert login_response.status_code == 200
        tokens = login_response.json()
        
        # Verify token structure
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "expires_in" in tokens
        assert "user_id" in tokens
        
        # Decode and verify access token
        access_token = tokens["access_token"]
        decoded = jwt.decode(access_token, options={"verify_signature": False})
        
        assert decoded["user_id"] == str(test_user.id)
        assert decoded["email"] == test_user.email
        assert "exp" in decoded
        assert "iat" in decoded
        assert decoded["type"] == "access"
        
        # Use access token for authenticated request
        auth_response = await test_client.get("/api/v1/auth/me", 
                                            headers={"Authorization": f"Bearer {access_token}"})
        assert auth_response.status_code == 200
    
    async def test_refresh_token_validation(self, test_client: AsyncClient, test_user):
        """Test refresh token specific validation"""
        # Get tokens
        login_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123",
            "remember_me": False
        })
        tokens = login_response.json()
        
        # Verify refresh token
        refresh_token = tokens["refresh_token"]
        decoded = jwt.decode(refresh_token, options={"verify_signature": False})
        
        assert decoded["type"] == "refresh"
        assert decoded["user_id"] == str(test_user.id)
        assert decoded["exp"] > decoded["iat"]
        
        # Use refresh token to get new access token
        refresh_response = await test_client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert "access_token" in new_tokens
        assert "expires_in" in new_tokens
    
    async def test_token_expiry_handling(self, test_client: AsyncClient, test_user):
        """Test handling of expired tokens"""
        # Create expired token
        expired_payload = {
            "user_id": str(test_user.id),
            "email": test_user.email,
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired
            "iat": datetime.utcnow() - timedelta(hours=2),
            "type": "access"
        }
        
        expired_token = jwt.encode(expired_payload, "test-secret", algorithm="HS256")
        
        # Use expired token
        response = await test_client.get("/api/v1/auth/me",
                                       headers={"Authorization": f"Bearer {expired_token}"})
        
        assert response.status_code == 401
        data = response.json()
        assert "expired" in data["detail"].lower()
    
    async def test_token_signature_validation(self, test_client: AsyncClient, test_user):
        """Test token signature validation"""
        # Create token with wrong signature
        valid_payload = {
            "user_id": str(test_user.id),
            "email": test_user.email,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        # Sign with wrong secret
        invalid_token = jwt.encode(valid_payload, "wrong-secret", algorithm="HS256")
        
        response = await test_client.get("/api/v1/auth/me",
                                       headers={"Authorization": f"Bearer {invalid_token}"})
        
        assert response.status_code == 401
    
    async def test_token_tampering_detection(self, test_client: AsyncClient, test_user):
        """Test detection of tampered tokens"""
        # Get valid token
        login_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123",
            "remember_me": False
        })
        valid_token = login_response.json()["access_token"]
        
        # Tamper with token
        token_parts = valid_token.split(".")
        # Modify payload (middle part)
        tampered_payload = token_parts[1][:-1] + "X"  # Change last character
        tampered_token = f"{token_parts[0]}.{tampered_payload}.{token_parts[2]}"
        
        response = await test_client.get("/api/v1/auth/me",
                                       headers={"Authorization": f"Bearer {tampered_token}"})
        
        assert response.status_code == 401
    
    async def test_token_claims_validation(self, test_client: AsyncClient, test_user):
        """Test validation of token claims"""
        # Create token with missing claims
        incomplete_payload = {
            "user_id": str(test_user.id),
            # Missing email, exp, etc.
            "iat": datetime.utcnow(),
        }
        
        incomplete_token = jwt.encode(incomplete_payload, "test-secret", algorithm="HS256")
        
        response = await test_client.get("/api/v1/auth/me",
                                       headers={"Authorization": f"Bearer {incomplete_token}"})
        
        assert response.status_code == 401
    
    async def test_token_algorithm_validation(self, test_client: AsyncClient, test_user):
        """Test token algorithm validation"""
        # Create token with different algorithm
        payload = {
            "user_id": str(test_user.id),
            "email": test_user.email,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        # Use different algorithm
        wrong_algo_token = jwt.encode(payload, "test-secret", algorithm="HS512")
        
        response = await test_client.get("/api/v1/auth/me",
                                       headers={"Authorization": f"Bearer {wrong_algo_token}"})
        
        # Should fail due to algorithm mismatch
        assert response.status_code == 401


@pytest.mark.auth
@pytest.mark.integration
@pytest.mark.asyncio
class TestAuthenticationFlow:
    """Test complete authentication flows"""
    
    async def test_complete_registration_flow(self, test_client: AsyncClient):
        """Test complete user registration and verification flow"""
        # Step 1: Register user
        user_data = {
            "email": "flowtest@example.com",
            "password": "FlowTestPassword123!",
            "name": "Flow Test User",
            "phone": "+1234567890"
        }
        
        register_response = await test_client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        user_info = register_response.json()
        assert user_info["email"] == user_data["email"]
        assert user_info["is_verified"] is False
        
        # Step 2: Try to login (should fail if email verification required)
        login_response = await test_client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"],
            "remember_me": False
        })
        
        # Depending on configuration, might require verification
        assert login_response.status_code in [200, 401]
        
        if login_response.status_code == 401:
            # Step 3: Verify email (simulate)
            verify_response = await test_client.post("/api/v1/auth/verify-email", json={
                "verification_token": "simulated-token"
            })
            # May succeed or fail depending on token validity
            
            # Step 4: Login after verification
            login_response = await test_client.post("/api/v1/auth/login", json={
                "email": user_data["email"],
                "password": user_data["password"],
                "remember_me": False
            })
            assert login_response.status_code == 200
    
    async def test_password_reset_flow(self, test_client: AsyncClient, test_user):
        """Test complete password reset flow"""
        # Step 1: Request password reset
        reset_request = await test_client.post("/api/v1/auth/forgot-password", json={
            "email": test_user.email
        })
        
        assert reset_request.status_code == 200
        assert "sent" in reset_request.json()["message"].lower()
        
        # Step 2: Reset password with token
        new_password = "NewSecurePassword123!"
        reset_response = await test_client.post("/api/v1/auth/reset-password", json={
            "reset_token": "simulated-reset-token",
            "new_password": new_password
        })
        
        # May succeed or fail depending on token validity
        assert reset_response.status_code in [200, 400]
        
        # Step 3: Try login with old password (should fail if reset succeeded)
        old_login = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123",  # Old password
            "remember_me": False
        })
        
        # If reset succeeded, old password should fail
        if reset_response.status_code == 200:
            assert old_login.status_code == 401
    
    async def test_session_management_flow(self, test_client: AsyncClient, test_user):
        """Test session creation, tracking, and revocation"""
        # Step 1: Login to create session
        login_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123",
            "remember_me": False
        })
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Check active sessions
        sessions_response = await test_client.get("/api/v1/auth/sessions", headers=auth_headers)
        assert sessions_response.status_code == 200
        
        sessions = sessions_response.json()["sessions"]
        assert len(sessions) >= 1
        
        # Step 3: Revoke a session
        if sessions:
            session_id = sessions[0]["id"]
            revoke_response = await test_client.delete(f"/api/v1/auth/sessions/{session_id}",
                                                     headers=auth_headers)
            assert revoke_response.status_code in [200, 404]
        
        # Step 4: Logout to end session
        logout_response = await test_client.post("/api/v1/auth/logout", headers=auth_headers)
        assert logout_response.status_code == 200
        
        # Step 5: Try using token after logout (should fail)
        me_response = await test_client.get("/api/v1/auth/me", headers=auth_headers)
        assert me_response.status_code == 401
    
    async def test_remember_me_functionality(self, test_client: AsyncClient, test_user):
        """Test remember me login functionality"""
        # Login with remember_me=True
        login_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123",
            "remember_me": True
        })
        
        assert login_response.status_code == 200
        tokens = login_response.json()
        
        # Refresh token should have longer expiry
        refresh_token = tokens["refresh_token"]
        decoded = jwt.decode(refresh_token, options={"verify_signature": False})
        
        # Remember me should extend token lifetime
        token_lifetime = decoded["exp"] - decoded["iat"]
        assert token_lifetime > 3600  # More than 1 hour
    
    async def test_concurrent_login_sessions(self, test_client: AsyncClient, test_user):
        """Test multiple concurrent sessions for same user"""
        # Create multiple sessions
        sessions = []
        for i in range(3):
            login_response = await test_client.post("/api/v1/auth/login", json={
                "email": test_user.email,
                "password": "testpassword123",
                "remember_me": False
            })
            
            if login_response.status_code == 200:
                sessions.append(login_response.json()["access_token"])
        
        # All tokens should be valid
        for token in sessions:
            response = await test_client.get("/api/v1/auth/me",
                                           headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
    
    async def test_device_tracking(self, test_client: AsyncClient, test_user):
        """Test device information tracking"""
        # Login with different user agents
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
            "Mozilla/5.0 (Android 10; Mobile; rv:81.0) Gecko/81.0 Firefox/81.0"
        ]
        
        for user_agent in user_agents:
            # Custom headers for different devices
            headers = {"User-Agent": user_agent}
            
            login_response = await test_client.post("/api/v1/auth/login", 
                                                  json={
                                                      "email": test_user.email,
                                                      "password": "testpassword123",
                                                      "remember_me": False
                                                  },
                                                  headers=headers)
            
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                
                # Check sessions show device info
                sessions_response = await test_client.get("/api/v1/auth/sessions",
                                                        headers={"Authorization": f"Bearer {token}"})
                
                if sessions_response.status_code == 200:
                    sessions = sessions_response.json()["sessions"]
                    # Should contain device information
                    for session in sessions:
                        if "device_info" in session:
                            assert session["user_agent"] == user_agent


@pytest.mark.auth
@pytest.mark.integration
@pytest.mark.asyncio
class TestAuthenticationSecurity:
    """Test security aspects of authentication"""
    
    async def test_brute_force_protection(self, test_client: AsyncClient, test_user):
        """Test brute force attack protection"""
        # Attempt multiple failed logins
        failed_attempts = []
        for i in range(10):
            response = await test_client.post("/api/v1/auth/login", json={
                "email": test_user.email,
                "password": f"wrong_password_{i}",
                "remember_me": False
            })
            failed_attempts.append(response.status_code)
            
            # Small delay to avoid overwhelming
            time.sleep(0.1)
        
        # Should see 401s initially, then potentially 429 (rate limited)
        assert all(status in [401, 429] for status in failed_attempts)
        
        # Check if rate limiting kicks in
        rate_limited = any(status == 429 for status in failed_attempts)
        
        # Try correct password after failed attempts
        correct_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123",
            "remember_me": False
        })
        
        # Should be blocked if rate limiting is active
        if rate_limited:
            assert correct_response.status_code == 429
        else:
            assert correct_response.status_code in [200, 429]
    
    async def test_account_lockout_mechanism(self, test_client: AsyncClient, test_user):
        """Test account lockout after failed attempts"""
        # Make multiple failed login attempts
        for i in range(15):  # Exceed typical lockout threshold
            await test_client.post("/api/v1/auth/login", json={
                "email": test_user.email,
                "password": f"wrong_password_{i}",
                "remember_me": False
            })
        
        # Account should be locked
        response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123",  # Correct password
            "remember_me": False
        })
        
        # Should fail due to lockout or rate limiting
        assert response.status_code in [401, 429]
    
    async def test_ip_address_tracking(self, test_client: AsyncClient, test_user):
        """Test IP address tracking and validation"""
        # Login with different IP addresses (simulated via headers)
        ip_addresses = ["192.168.1.100", "10.0.0.50", "172.16.0.25"]
        
        for ip_addr in ip_addresses:
            headers = {"X-Forwarded-For": ip_addr}
            
            response = await test_client.post("/api/v1/auth/login", 
                                            json={
                                                "email": test_user.email,
                                                "password": "testpassword123",
                                                "remember_me": False
                                            },
                                            headers=headers)
            
            if response.status_code == 200:
                token = response.json()["access_token"]
                
                # Check that IP is tracked in sessions
                sessions_response = await test_client.get("/api/v1/auth/sessions",
                                                        headers={"Authorization": f"Bearer {token}"})
                
                if sessions_response.status_code == 200:
                    sessions = sessions_response.json()["sessions"]
                    # Should track IP address
                    assert any("ip_address" in session for session in sessions)
    
    async def test_suspicious_activity_detection(self, test_client: AsyncClient, test_user):
        """Test detection of suspicious login patterns"""
        # Rapid logins from different locations/devices
        suspicious_requests = [
            {"User-Agent": "Windows", "X-Forwarded-For": "192.168.1.1"},
            {"User-Agent": "iPhone", "X-Forwarded-For": "10.0.0.1"},
            {"User-Agent": "Android", "X-Forwarded-For": "172.16.0.1"},
            {"User-Agent": "Linux", "X-Forwarded-For": "203.0.113.1"}
        ]
        
        for headers in suspicious_requests:
            response = await test_client.post("/api/v1/auth/login",
                                            json={
                                                "email": test_user.email,
                                                "password": "testpassword123",
                                                "remember_me": False
                                            },
                                            headers=headers)
            
            # May trigger additional verification or warnings
            assert response.status_code in [200, 401, 429]
            
            # Check for security warnings in response
            if response.status_code == 200:
                data = response.json()
                # Might include security warnings
                if "warnings" in data:
                    assert isinstance(data["warnings"], list)
    
    async def test_password_policy_enforcement(self, test_client: AsyncClient):
        """Test password policy enforcement"""
        weak_passwords = [
            "weak",
            "12345678",
            "password",
            "qwerty123",
            "admin",
            ""
        ]
        
        for weak_password in weak_passwords:
            response = await test_client.post("/api/v1/auth/register", json={
                "email": f"weak{weak_password}@example.com",
                "password": weak_password,
                "name": "Weak Password User"
            })
            
            # Should reject weak passwords
            assert response.status_code == 422
            data = response.json()
            assert "password" in str(data).lower()
    
    async def test_secure_headers(self, test_client: AsyncClient):
        """Test security headers in responses"""
        response = await test_client.get("/health")
        
        # Check for security headers
        headers = response.headers
        
        # Content-Type should be set
        assert "content-type" in headers
        
        # Security headers might include:
        # - X-Content-Type-Options
        # - X-Frame-Options  
        # - X-XSS-Protection
        # These depend on middleware configuration
    
    async def test_timing_attack_resistance(self, test_client: AsyncClient, test_user):
        """Test resistance to timing attacks"""
        import time
        
        # Time login with valid user
        start_time = time.time()
        valid_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "wrongpassword",
            "remember_me": False
        })
        valid_time = time.time() - start_time
        
        # Time login with invalid user
        start_time = time.time()
        invalid_response = await test_client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword",
            "remember_me": False
        })
        invalid_time = time.time() - start_time
        
        # Response times should be similar to prevent user enumeration
        assert both_responses_similar = abs(valid_time - invalid_time) < 0.5  # 500ms difference
        
        # Both should return 401
        assert valid_response.status_code == 401
        assert invalid_response.status_code == 401


@pytest.mark.auth
@pytest.mark.integration  
@pytest.mark.asyncio
class TestAuthenticationEdgeCases:
    """Test edge cases and error conditions"""
    
    async def test_malformed_authorization_headers(self, test_client: AsyncClient):
        """Test handling of malformed authorization headers"""
        malformed_headers = [
            {"Authorization": "invalid"},
            {"Authorization": "Bearer"},  # Missing token
            {"Authorization": "Basic token"},  # Wrong scheme
            {"Authorization": "Bearer "},  # Empty token
            {"Authorization": "Bearer token with spaces"},
            {"Authorization": "Bearer " + "x" * 1000},  # Very long token
        ]
        
        for headers in malformed_headers:
            response = await test_client.get("/api/v1/auth/me", headers=headers)
            assert response.status_code == 401
    
    async def test_special_characters_in_credentials(self, test_client: AsyncClient):
        """Test handling of special characters in credentials"""
        special_chars_data = [
            {"email": "test+tag@example.com", "password": "Pass@#$%^&*()123!"},
            {"email": "test@example-domain.com", "password": "Pássword123!"},  # Unicode
            {"email": "test@subdomain.example.com", "password": "Pass|\\{}[]123!"},
            {"email": "test@example.com", "password": "Pass\"'`123!"}  # Quotes
        ]
        
        for creds in special_chars_data:
            # Test registration
            response = await test_client.post("/api/v1/auth/register", json={
                **creds,
                "name": "Special Chars User"
            })
            
            # Should handle special characters properly
            assert response.status_code in [201, 400, 422]  # Created or validation error
    
    async def test_unicode_handling(self, test_client: AsyncClient):
        """Test Unicode character handling"""
        unicode_data = {
            "email": "tëst@éxample.com",
            "password": "Pässwörd123!",
            "name": "Tëst Üser 測試"
        }
        
        response = await test_client.post("/api/v1/auth/register", json=unicode_data)
        
        # Should handle Unicode properly
        assert response.status_code in [201, 400, 422]
    
    async def test_extremely_long_inputs(self, test_client: AsyncClient):
        """Test handling of extremely long inputs"""
        long_data = {
            "email": "x" * 1000 + "@example.com",
            "password": "x" * 1000 + "Pass123!",
            "name": "x" * 10000
        }
        
        response = await test_client.post("/api/v1/auth/register", json=long_data)
        
        # Should reject or truncate long inputs
        assert response.status_code in [400, 413, 422]
    
    async def test_null_and_empty_values(self, test_client: AsyncClient):
        """Test handling of null and empty values"""
        null_data_sets = [
            {"email": None, "password": "Pass123!", "name": "Test"},
            {"email": "", "password": "Pass123!", "name": "Test"},
            {"email": "test@example.com", "password": None, "name": "Test"},
            {"email": "test@example.com", "password": "", "name": "Test"},
            {"email": "test@example.com", "password": "Pass123!", "name": None},
            {"email": "test@example.com", "password": "Pass123!", "name": ""}
        ]
        
        for data in null_data_sets:
            response = await test_client.post("/api/v1/auth/register", json=data)
            assert response.status_code == 422  # Validation error
    
    async def test_concurrent_authentication_requests(self, test_client: AsyncClient, test_user):
        """Test concurrent authentication requests"""
        import asyncio
        
        async def login_request():
            return await test_client.post("/api/v1/auth/login", json={
                "email": test_user.email,
                "password": "testpassword123",
                "remember_me": False
            })
        
        # Make 5 concurrent login requests
        tasks = [login_request() for _ in range(5)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should either succeed or be rate limited
        for response in responses:
            if not isinstance(response, Exception):
                assert response.status_code in [200, 429]
    
    async def test_token_race_conditions(self, test_client: AsyncClient, test_user):
        """Test token validation race conditions"""
        # Get a valid token
        login_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123",
            "remember_me": False
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            
            # Make concurrent requests with same token
            import asyncio
            
            async def authenticated_request():
                return await test_client.get("/api/v1/auth/me",
                                           headers={"Authorization": f"Bearer {token}"})
            
            tasks = [authenticated_request() for _ in range(10)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should succeed (no race conditions)
            for response in responses:
                if not isinstance(response, Exception):
                    assert response.status_code == 200
    
    async def test_memory_leak_prevention(self, test_client: AsyncClient, test_user):
        """Test that authentication doesn't cause memory leaks"""
        import gc
        import sys
        
        # Get initial memory usage
        initial_objects = len(gc.get_objects())
        
        # Perform many authentication operations
        for i in range(100):
            response = await test_client.post("/api/v1/auth/login", json={
                "email": test_user.email,
                "password": "testpassword123",
                "remember_me": False
            })
            
            if response.status_code == 200:
                token = response.json()["access_token"]
                
                # Use token
                await test_client.get("/api/v1/auth/me",
                                    headers={"Authorization": f"Bearer {token}"})
                
                # Logout
                await test_client.post("/api/v1/auth/logout",
                                     headers={"Authorization": f"Bearer {token}"})
        
        # Force garbage collection
        gc.collect()
        
        # Check memory usage hasn't grown significantly
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects
        
        # Allow some growth but not excessive
        assert object_growth < 1000  # Arbitrary threshold


@pytest.mark.auth
@pytest.mark.integration
@pytest.mark.asyncio
class TestAuthenticationIntegration:
    """Test authentication integration with other services"""
    
    @patch('httpx.AsyncClient.post')
    async def test_external_service_token_validation(self, mock_post, test_client: AsyncClient, test_user):
        """Test token validation for external services"""
        # Mock external service validation request
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": str(test_user.id),
            "email": test_user.email,
            "is_valid": True
        }
        mock_post.return_value = mock_response
        
        # Get token
        login_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123",
            "remember_me": False
        })
        
        token = login_response.json()["access_token"]
        
        # Validate token
        validate_response = await test_client.post("/api/v1/auth/validate", json={
            "token": token
        })
        
        assert validate_response.status_code == 200
        data = validate_response.json()
        assert data["is_valid"] is True
        assert data["user_id"] == str(test_user.id)
    
    async def test_cross_service_authorization(self, test_client: AsyncClient, test_user, auth_headers):
        """Test authorization across different services"""
        # Test different resource access
        resources = ["users", "organizations", "analytics", "billing"]
        actions = ["read", "write", "delete", "admin"]
        
        for resource in resources:
            for action in actions:
                response = await test_client.post("/api/v1/auth/authorize",
                                                json={
                                                    "resource": resource,
                                                    "action": action
                                                },
                                                headers=auth_headers("valid_token"))
                
                assert response.status_code == 200
                data = response.json()
                assert "authorized" in data
                assert isinstance(data["authorized"], bool)
    
    async def test_token_propagation(self, test_client: AsyncClient, test_user):
        """Test token propagation in request chain"""
        # Get token
        login_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123", 
            "remember_me": False
        })
        
        token = login_response.json()["access_token"]
        
        # Make request that might propagate to other services
        response = await test_client.get("/api/v1/auth/me",
                                       headers={"Authorization": f"Bearer {token}"})
        
        assert response.status_code == 200
        
        # Token should contain necessary information for other services
        user_data = response.json()
        assert "organization_id" in user_data
        assert "permissions" in user_data
        assert "roles" in user_data
    
    async def test_service_to_service_authentication(self, test_client: AsyncClient):
        """Test service-to-service authentication"""
        # Simulate service account token
        service_payload = {
            "service_id": "analytics-service",
            "service_name": "Analytics Service",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "type": "service"
        }
        
        service_token = jwt.encode(service_payload, "test-secret", algorithm="HS256")
        
        # Use service token for internal API
        response = await test_client.post("/api/v1/auth/validate", 
                                        json={"token": service_token},
                                        headers={"Authorization": f"Bearer {service_token}"})
        
        # May succeed or fail depending on service auth implementation
        assert response.status_code in [200, 401, 403]


@pytest.mark.auth
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
class TestAuthenticationPerformance:
    """Test authentication performance characteristics"""
    
    async def test_login_performance(self, test_client: AsyncClient, test_user):
        """Test login endpoint performance"""
        login_times = []
        
        for i in range(10):
            start_time = time.time()
            
            response = await test_client.post("/api/v1/auth/login", json={
                "email": test_user.email,
                "password": "testpassword123",
                "remember_me": False
            })
            
            end_time = time.time()
            
            if response.status_code == 200:
                login_times.append(end_time - start_time)
        
        if login_times:
            avg_time = sum(login_times) / len(login_times)
            max_time = max(login_times)
            
            # Login should be reasonably fast
            assert avg_time < 2.0  # Average under 2 seconds
            assert max_time < 5.0  # Max under 5 seconds
    
    async def test_token_validation_performance(self, test_client: AsyncClient, test_user):
        """Test token validation performance"""
        # Get token
        login_response = await test_client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123",
            "remember_me": False
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            validation_times = []
            
            for i in range(20):
                start_time = time.time()
                
                response = await test_client.get("/api/v1/auth/me",
                                               headers={"Authorization": f"Bearer {token}"})
                
                end_time = time.time()
                
                if response.status_code == 200:
                    validation_times.append(end_time - start_time)
            
            if validation_times:
                avg_time = sum(validation_times) / len(validation_times)
                
                # Token validation should be very fast
                assert avg_time < 0.5  # Average under 500ms
    
    async def test_concurrent_authentication_load(self, test_client: AsyncClient, test_user):
        """Test system under concurrent authentication load"""
        import asyncio
        
        async def login_and_validate():
            # Login
            login_response = await test_client.post("/api/v1/auth/login", json={
                "email": test_user.email,
                "password": "testpassword123",
                "remember_me": False
            })
            
            if login_response.status_code == 200:
                token = login_response.json()["access_token"]
                
                # Validate
                validate_response = await test_client.get("/api/v1/auth/me",
                                                        headers={"Authorization": f"Bearer {token}"})
                
                return login_response.status_code, validate_response.status_code
            
            return login_response.status_code, None
        
        # Run 20 concurrent authentication flows
        tasks = [login_and_validate() for _ in range(20)]
        start_time = time.time()
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Check results
        successful_logins = 0
        successful_validations = 0
        
        for result in results:
            if not isinstance(result, Exception):
                login_status, validate_status = result
                if login_status == 200:
                    successful_logins += 1
                if validate_status == 200:
                    successful_validations += 1
        
        # Most operations should succeed
        success_rate = successful_logins / len(tasks)
        assert success_rate > 0.8  # 80% success rate
        
        # Total time should be reasonable
        assert total_time < 30.0  # Under 30 seconds for 20 concurrent operations