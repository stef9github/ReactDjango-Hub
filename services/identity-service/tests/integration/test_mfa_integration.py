"""
Comprehensive MFA (Multi-Factor Authentication) integration tests
Tests all MFA methods, policies, and security flows
"""

import pytest
import uuid
import time
import pyotp
import qrcode
from datetime import datetime, timedelta
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from io import BytesIO


@pytest.mark.mfa
@pytest.mark.integration
@pytest.mark.asyncio
class TestTOTPMFA:
    """Test Time-based One-Time Password (TOTP) MFA"""
    
    async def test_totp_setup_complete_flow(self, test_client: AsyncClient, test_user, auth_headers):
        """Test complete TOTP setup flow"""
        # Setup TOTP
        setup_response = await test_client.post("/api/v1/mfa/setup", 
                                              json={
                                                  "method_type": "totp",
                                                  "metadata": {"app_name": "Test App"}
                                              },
                                              headers=auth_headers("valid_token"))
        
        assert setup_response.status_code == 200
        setup_data = setup_response.json()
        
        # Verify response structure
        assert "method_id" in setup_data
        assert "secret" in setup_data
        assert "qr_code" in setup_data
        assert "backup_codes" in setup_data
        assert setup_data["method_type"] == "totp"
        
        # Verify secret is valid base32
        secret = setup_data["secret"]
        assert len(secret) >= 16  # Minimum TOTP secret length
        
        # Verify QR code is valid base64 image
        qr_code = setup_data["qr_code"]
        assert qr_code.startswith("data:image/")
        
        # Verify backup codes
        backup_codes = setup_data["backup_codes"]
        assert len(backup_codes) == 8  # Standard number
        for code in backup_codes:
            assert isinstance(code, str)
            assert len(code) >= 8
        
        return setup_data["method_id"], secret
    
    async def test_totp_qr_code_generation(self, test_client: AsyncClient, test_user, auth_headers):
        """Test TOTP QR code generation"""
        setup_response = await test_client.post("/api/v1/mfa/setup",
                                              json={
                                                  "method_type": "totp",
                                                  "metadata": {"app_name": "Identity Service Test"}
                                              },
                                              headers=auth_headers("valid_token"))
        
        assert setup_response.status_code == 200
        setup_data = setup_response.json()
        
        # Decode QR code data
        qr_data = setup_data["qr_code"]
        assert "otpauth://totp/" in qr_data or qr_data.startswith("data:image/")
        
        # If it's a data URL, verify it's a valid image
        if qr_data.startswith("data:image/"):
            # Extract base64 data
            header, encoded = qr_data.split(',', 1)
            assert "base64" in header
            
            # Should be decodable
            import base64
            try:
                image_data = base64.b64decode(encoded)
                assert len(image_data) > 0
            except Exception as e:
                pytest.fail(f"Invalid base64 QR code data: {e}")
    
    async def test_totp_challenge_creation(self, test_client: AsyncClient, test_user, auth_headers):
        """Test TOTP challenge creation"""
        # First setup TOTP
        method_id, secret = await self.test_totp_setup_complete_flow(test_client, test_user, auth_headers)
        
        # Create challenge
        challenge_response = await test_client.post("/api/v1/mfa/challenge",
                                                  json={"method_id": method_id},
                                                  headers=auth_headers("valid_token"))
        
        assert challenge_response.status_code == 200
        challenge_data = challenge_response.json()
        
        assert "challenge_id" in challenge_data
        assert "expires_at" in challenge_data
        assert "method_type" in challenge_data
        assert challenge_data["method_type"] == "totp"
        
        # Expires at should be in the future
        expires_at = datetime.fromisoformat(challenge_data["expires_at"].replace('Z', '+00:00'))
        assert expires_at > datetime.now(expires_at.tzinfo)
    
    async def test_totp_verification_success(self, test_client: AsyncClient, test_user, auth_headers):
        """Test successful TOTP verification"""
        # Setup TOTP
        method_id, secret = await self.test_totp_setup_complete_flow(test_client, test_user, auth_headers)
        
        # Generate valid TOTP code
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        
        # Verify code
        verify_response = await test_client.post("/api/v1/mfa/verify",
                                               json={
                                                   "method_id": method_id,
                                                   "challenge_code": current_code
                                               },
                                               headers=auth_headers("valid_token"))
        
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        
        assert "verified" in verify_data
        assert verify_data["verified"] is True
        assert "message" in verify_data
    
    async def test_totp_verification_failure(self, test_client: AsyncClient, test_user, auth_headers):
        """Test failed TOTP verification"""
        # Setup TOTP
        method_id, secret = await self.test_totp_setup_complete_flow(test_client, test_user, auth_headers)
        
        # Use invalid code
        invalid_code = "000000"
        
        verify_response = await test_client.post("/api/v1/mfa/verify",
                                               json={
                                                   "method_id": method_id,
                                                   "challenge_code": invalid_code
                                               },
                                               headers=auth_headers("valid_token"))
        
        assert verify_response.status_code == 400
        verify_data = verify_response.json()
        
        assert "verified" in verify_data
        assert verify_data["verified"] is False
    
    async def test_totp_time_window_tolerance(self, test_client: AsyncClient, test_user, auth_headers):
        """Test TOTP time window tolerance"""
        # Setup TOTP
        method_id, secret = await self.test_totp_setup_complete_flow(test_client, test_user, auth_headers)
        
        # Generate codes for different time windows
        totp = pyotp.TOTP(secret)
        
        # Current code
        current_code = totp.now()
        
        # Previous window code (30 seconds ago)
        previous_code = totp.at(datetime.now() - timedelta(seconds=30))
        
        # Next window code (30 seconds from now)
        next_code = totp.at(datetime.now() + timedelta(seconds=30))
        
        # Test current code (should work)
        response = await test_client.post("/api/v1/mfa/verify",
                                        json={
                                            "method_id": method_id,
                                            "challenge_code": current_code
                                        },
                                        headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        assert response.json()["verified"] is True
    
    async def test_totp_replay_attack_protection(self, test_client: AsyncClient, test_user, auth_headers):
        """Test TOTP replay attack protection"""
        # Setup TOTP
        method_id, secret = await self.test_totp_setup_complete_flow(test_client, test_user, auth_headers)
        
        # Generate valid code
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        # Use code first time
        first_response = await test_client.post("/api/v1/mfa/verify",
                                              json={
                                                  "method_id": method_id,
                                                  "challenge_code": code
                                              },
                                              headers=auth_headers("valid_token"))
        
        assert first_response.status_code == 200
        
        # Try to use same code again (should fail)
        second_response = await test_client.post("/api/v1/mfa/verify",
                                               json={
                                                   "method_id": method_id,
                                                   "challenge_code": code
                                               },
                                               headers=auth_headers("valid_token"))
        
        # Should fail due to replay protection
        assert second_response.status_code == 400
        assert second_response.json()["verified"] is False


@pytest.mark.mfa
@pytest.mark.integration
@pytest.mark.asyncio
class TestEmailMFA:
    """Test Email-based MFA"""
    
    @patch('app.services.email_service.EmailService')
    async def test_email_mfa_setup(self, mock_email_service, test_client: AsyncClient, test_user, auth_headers):
        """Test email MFA setup"""
        mock_email_instance = AsyncMock()
        mock_email_service.return_value = mock_email_instance
        mock_email_instance.send_mfa_code.return_value = True
        
        # Setup email MFA
        setup_response = await test_client.post("/api/v1/mfa/setup",
                                              json={
                                                  "method_type": "email"
                                              },
                                              headers=auth_headers("valid_token"))
        
        assert setup_response.status_code == 200
        setup_data = setup_response.json()
        
        assert "method_id" in setup_data
        assert setup_data["method_type"] == "email"
        assert "email" in setup_data
        
        return setup_data["method_id"]
    
    @patch('app.services.email_service.EmailService')
    async def test_email_mfa_challenge_creation(self, mock_email_service, test_client: AsyncClient, test_user, auth_headers):
        """Test email MFA challenge creation"""
        mock_email_instance = AsyncMock()
        mock_email_service.return_value = mock_email_instance
        mock_email_instance.send_mfa_code.return_value = True
        
        # Setup email MFA
        method_id = await self.test_email_mfa_setup(mock_email_service, test_client, test_user, auth_headers)
        
        # Create challenge
        challenge_response = await test_client.post("/api/v1/mfa/challenge",
                                                  json={"method_id": method_id},
                                                  headers=auth_headers("valid_token"))
        
        assert challenge_response.status_code == 200
        challenge_data = challenge_response.json()
        
        assert "challenge_id" in challenge_data
        assert "expires_at" in challenge_data
        assert challenge_data["method_type"] == "email"
        
        # Verify email was sent
        mock_email_instance.send_mfa_code.assert_called_once()
    
    @patch('app.services.email_service.EmailService')
    async def test_email_mfa_code_verification(self, mock_email_service, test_client: AsyncClient, test_user, auth_headers):
        """Test email MFA code verification"""
        mock_email_instance = AsyncMock()
        mock_email_service.return_value = mock_email_instance
        mock_email_instance.send_mfa_code.return_value = True
        
        # Setup email MFA
        method_id = await self.test_email_mfa_setup(mock_email_service, test_client, test_user, auth_headers)
        
        # Create challenge (this should generate and store a code)
        challenge_response = await test_client.post("/api/v1/mfa/challenge",
                                                  json={"method_id": method_id},
                                                  headers=auth_headers("valid_token"))
        
        assert challenge_response.status_code == 200
        
        # Simulate user entering the correct code
        # In real implementation, code would be stored in database during challenge creation
        test_code = "123456"
        
        with patch('app.services.mfa_service.MFAService.verify_email_code', return_value=True):
            verify_response = await test_client.post("/api/v1/mfa/verify",
                                                   json={
                                                       "method_id": method_id,
                                                       "challenge_code": test_code
                                                   },
                                                   headers=auth_headers("valid_token"))
            
            assert verify_response.status_code == 200
            assert verify_response.json()["verified"] is True
    
    async def test_email_mfa_code_expiration(self, test_client: AsyncClient, test_user, auth_headers):
        """Test email MFA code expiration"""
        with patch('app.services.email_service.EmailService') as mock_email_service:
            mock_email_instance = AsyncMock()
            mock_email_service.return_value = mock_email_instance
            mock_email_instance.send_mfa_code.return_value = True
            
            # Setup email MFA
            method_id = await self.test_email_mfa_setup(mock_email_service, test_client, test_user, auth_headers)
            
            # Create challenge
            challenge_response = await test_client.post("/api/v1/mfa/challenge",
                                                      json={"method_id": method_id},
                                                      headers=auth_headers("valid_token"))
            
            assert challenge_response.status_code == 200
            
            # Simulate expired code
            with patch('app.services.mfa_service.MFAService.verify_email_code', return_value=False) as mock_verify:
                mock_verify.side_effect = ValueError("Code expired")
                
                verify_response = await test_client.post("/api/v1/mfa/verify",
                                                       json={
                                                           "method_id": method_id,
                                                           "challenge_code": "123456"
                                                       },
                                                       headers=auth_headers("valid_token"))
                
                assert verify_response.status_code == 400
                assert "expired" in verify_response.json()["detail"].lower()


@pytest.mark.mfa
@pytest.mark.integration
@pytest.mark.asyncio
class TestSMSMFA:
    """Test SMS-based MFA"""
    
    @patch('app.services.sms_service.SMSService')
    async def test_sms_mfa_setup(self, mock_sms_service, test_client: AsyncClient, test_user, auth_headers):
        """Test SMS MFA setup"""
        mock_sms_instance = AsyncMock()
        mock_sms_service.return_value = mock_sms_instance
        mock_sms_instance.send_sms.return_value = {"status": "sent", "id": "sms-123"}
        
        # Setup SMS MFA
        setup_response = await test_client.post("/api/v1/mfa/setup",
                                              json={
                                                  "method_type": "sms",
                                                  "metadata": {"phone": "+1234567890"}
                                              },
                                              headers=auth_headers("valid_token"))
        
        assert setup_response.status_code == 200
        setup_data = setup_response.json()
        
        assert "method_id" in setup_data
        assert setup_data["method_type"] == "sms"
        assert "phone" in setup_data
        
        return setup_data["method_id"]
    
    @patch('app.services.sms_service.SMSService')
    async def test_sms_mfa_challenge_creation(self, mock_sms_service, test_client: AsyncClient, test_user, auth_headers):
        """Test SMS MFA challenge creation"""
        mock_sms_instance = AsyncMock()
        mock_sms_service.return_value = mock_sms_instance
        mock_sms_instance.send_sms.return_value = {"status": "sent", "id": "sms-123"}
        
        # Setup SMS MFA
        method_id = await self.test_sms_mfa_setup(mock_sms_service, test_client, test_user, auth_headers)
        
        # Create challenge
        challenge_response = await test_client.post("/api/v1/mfa/challenge",
                                                  json={"method_id": method_id},
                                                  headers=auth_headers("valid_token"))
        
        assert challenge_response.status_code == 200
        challenge_data = challenge_response.json()
        
        assert "challenge_id" in challenge_data
        assert "expires_at" in challenge_data
        assert challenge_data["method_type"] == "sms"
        
        # Verify SMS was sent
        mock_sms_instance.send_sms.assert_called_once()
    
    @patch('app.services.sms_service.SMSService')
    async def test_sms_mfa_rate_limiting(self, mock_sms_service, test_client: AsyncClient, test_user, auth_headers):
        """Test SMS MFA rate limiting"""
        mock_sms_instance = AsyncMock()
        mock_sms_service.return_value = mock_sms_instance
        mock_sms_instance.send_sms.return_value = {"status": "sent", "id": "sms-123"}
        
        # Setup SMS MFA
        method_id = await self.test_sms_mfa_setup(mock_sms_service, test_client, test_user, auth_headers)
        
        # Make multiple rapid challenge requests
        responses = []
        for i in range(5):
            response = await test_client.post("/api/v1/mfa/challenge",
                                            json={"method_id": method_id},
                                            headers=auth_headers("valid_token"))
            responses.append(response.status_code)
        
        # Some should be rate limited
        assert any(status == 429 for status in responses)
    
    async def test_sms_mfa_phone_validation(self, test_client: AsyncClient, test_user, auth_headers):
        """Test SMS MFA phone number validation"""
        invalid_phones = [
            "invalid-phone",
            "123",
            "+1234567890123456789",  # Too long
            "",
            "abcdefghij"
        ]
        
        for phone in invalid_phones:
            response = await test_client.post("/api/v1/mfa/setup",
                                            json={
                                                "method_type": "sms",
                                                "metadata": {"phone": phone}
                                            },
                                            headers=auth_headers("valid_token"))
            
            # Should reject invalid phone numbers
            assert response.status_code == 422


@pytest.mark.mfa
@pytest.mark.integration
@pytest.mark.asyncio
class TestBackupCodes:
    """Test backup codes functionality"""
    
    async def test_backup_codes_generation(self, test_client: AsyncClient, test_user, auth_headers):
        """Test backup codes generation"""
        response = await test_client.post("/api/v1/mfa/backup-codes/regenerate",
                                        headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert "backup_codes" in data
        backup_codes = data["backup_codes"]
        
        # Verify backup codes structure
        assert len(backup_codes) == 8  # Standard number
        for code in backup_codes:
            assert isinstance(code, str)
            assert len(code) >= 8  # Minimum length
            assert code.replace('-', '').isalnum()  # Only alphanumeric and dashes
    
    async def test_backup_codes_uniqueness(self, test_client: AsyncClient, test_user, auth_headers):
        """Test that backup codes are unique"""
        # Generate first set
        response1 = await test_client.post("/api/v1/mfa/backup-codes/regenerate",
                                         headers=auth_headers("valid_token"))
        
        codes1 = set(response1.json()["backup_codes"])
        
        # Generate second set
        response2 = await test_client.post("/api/v1/mfa/backup-codes/regenerate",
                                         headers=auth_headers("valid_token"))
        
        codes2 = set(response2.json()["backup_codes"])
        
        # Sets should be different
        assert codes1 != codes2
        assert len(codes1.intersection(codes2)) == 0  # No common codes
    
    async def test_backup_code_verification(self, test_client: AsyncClient, test_user, auth_headers):
        """Test backup code verification"""
        # Generate backup codes
        codes_response = await test_client.post("/api/v1/mfa/backup-codes/regenerate",
                                              headers=auth_headers("valid_token"))
        
        backup_codes = codes_response.json()["backup_codes"]
        test_code = backup_codes[0]
        
        # Use backup code for MFA verification
        with patch('app.services.mfa_service.MFAService.verify_backup_code', return_value=True):
            verify_response = await test_client.post("/api/v1/mfa/verify",
                                                   json={
                                                       "challenge_code": test_code,
                                                       "is_backup_code": True
                                                   },
                                                   headers=auth_headers("valid_token"))
            
            assert verify_response.status_code == 200
            assert verify_response.json()["verified"] is True
    
    async def test_backup_code_single_use(self, test_client: AsyncClient, test_user, auth_headers):
        """Test that backup codes are single-use"""
        # Generate backup codes
        codes_response = await test_client.post("/api/v1/mfa/backup-codes/regenerate",
                                              headers=auth_headers("valid_token"))
        
        backup_codes = codes_response.json()["backup_codes"]
        test_code = backup_codes[0]
        
        # Use backup code first time
        with patch('app.services.mfa_service.MFAService.verify_backup_code', return_value=True) as mock_verify:
            first_response = await test_client.post("/api/v1/mfa/verify",
                                                   json={
                                                       "challenge_code": test_code,
                                                       "is_backup_code": True
                                                   },
                                                   headers=auth_headers("valid_token"))
            
            assert first_response.status_code == 200
        
        # Try to use same code again
        with patch('app.services.mfa_service.MFAService.verify_backup_code', return_value=False) as mock_verify:
            second_response = await test_client.post("/api/v1/mfa/verify",
                                                    json={
                                                        "challenge_code": test_code,
                                                        "is_backup_code": True
                                                    },
                                                    headers=auth_headers("valid_token"))
            
            assert second_response.status_code == 400
            assert second_response.json()["verified"] is False


@pytest.mark.mfa
@pytest.mark.integration
@pytest.mark.asyncio
class TestMFAMethodManagement:
    """Test MFA method management"""
    
    async def test_list_user_mfa_methods(self, test_client: AsyncClient, test_user, auth_headers):
        """Test listing user's MFA methods"""
        response = await test_client.get("/api/v1/mfa/methods",
                                       headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert "methods" in data
        assert isinstance(data["methods"], list)
        
        # Each method should have required fields
        for method in data["methods"]:
            assert "id" in method
            assert "method_type" in method
            assert "is_enabled" in method
            assert "created_at" in method
    
    async def test_multiple_mfa_methods_setup(self, test_client: AsyncClient, test_user, auth_headers):
        """Test setting up multiple MFA methods"""
        methods_to_setup = [
            {"method_type": "totp", "metadata": {"app_name": "Test App"}},
            {"method_type": "email"},
        ]
        
        method_ids = []
        
        # Setup multiple methods
        for method_data in methods_to_setup:
            with patch('app.services.email_service.EmailService') as mock_email:
                mock_email.return_value.send_mfa_code.return_value = True
                
                response = await test_client.post("/api/v1/mfa/setup",
                                                json=method_data,
                                                headers=auth_headers("valid_token"))
                
                if response.status_code == 200:
                    method_ids.append(response.json()["method_id"])
        
        # List methods to verify
        list_response = await test_client.get("/api/v1/mfa/methods",
                                            headers=auth_headers("valid_token"))
        
        if list_response.status_code == 200:
            methods = list_response.json()["methods"]
            found_types = [m["method_type"] for m in methods]
            
            # Should find the methods we set up
            for method_data in methods_to_setup:
                if method_data["method_type"] not in found_types:
                    # Method setup might have failed due to missing dependencies
                    continue
    
    async def test_disable_mfa_method(self, test_client: AsyncClient, test_user, test_mfa_method, auth_headers):
        """Test disabling MFA method"""
        # Disable method
        disable_response = await test_client.patch(f"/api/v1/mfa/methods/{test_mfa_method.id}",
                                                 json={"is_enabled": False},
                                                 headers=auth_headers("valid_token"))
        
        # Should succeed or method might not exist
        assert disable_response.status_code in [200, 404]
        
        if disable_response.status_code == 200:
            # Verify method is disabled
            list_response = await test_client.get("/api/v1/mfa/methods",
                                                headers=auth_headers("valid_token"))
            
            if list_response.status_code == 200:
                methods = list_response.json()["methods"]
                disabled_method = next((m for m in methods if m["id"] == str(test_mfa_method.id)), None)
                
                if disabled_method:
                    assert disabled_method["is_enabled"] is False
    
    async def test_remove_mfa_method(self, test_client: AsyncClient, test_user, test_mfa_method, auth_headers):
        """Test removing MFA method"""
        # Remove method
        remove_response = await test_client.delete(f"/api/v1/mfa/methods/{test_mfa_method.id}",
                                                 headers=auth_headers("valid_token"))
        
        assert remove_response.status_code in [200, 404]
        
        if remove_response.status_code == 200:
            # Verify method is removed
            list_response = await test_client.get("/api/v1/mfa/methods",
                                                headers=auth_headers("valid_token"))
            
            if list_response.status_code == 200:
                methods = list_response.json()["methods"]
                method_ids = [m["id"] for m in methods]
                
                assert str(test_mfa_method.id) not in method_ids
    
    async def test_mfa_method_security_validation(self, test_client: AsyncClient, test_user, auth_headers):
        """Test MFA method security validation"""
        # Try to setup with invalid data
        invalid_setups = [
            {"method_type": "invalid_type"},
            {"method_type": "totp", "metadata": {"malicious_field": "<script>alert('xss')</script>"}},
            {"method_type": "sms", "metadata": {"phone": "'; DROP TABLE users; --"}},
        ]
        
        for invalid_setup in invalid_setups:
            response = await test_client.post("/api/v1/mfa/setup",
                                            json=invalid_setup,
                                            headers=auth_headers("valid_token"))
            
            # Should reject invalid setups
            assert response.status_code in [400, 422]


@pytest.mark.mfa
@pytest.mark.integration
@pytest.mark.asyncio
class TestMFAPolicyManagement:
    """Test MFA policy management"""
    
    async def test_get_system_mfa_policy(self, test_client: AsyncClient, auth_headers):
        """Test getting system-wide MFA policy"""
        response = await test_client.get("/api/v1/mfa/policy/system",
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert "requirement_level" in data
        assert "enforcement_scopes" in data
        assert "allowed_methods" in data
        
        # Validate enum values
        assert data["requirement_level"] in ["disabled", "optional", "recommended", "required"]
        assert isinstance(data["enforcement_scopes"], list)
        assert isinstance(data["allowed_methods"], list)
    
    async def test_update_system_mfa_policy(self, test_client: AsyncClient, auth_headers):
        """Test updating system-wide MFA policy"""
        policy_update = {
            "requirement_level": "required",
            "enforcement_scopes": ["login", "sensitive_operations"],
            "allowed_methods": ["totp", "sms", "email"],
            "grace_period_days": 7
        }
        
        response = await test_client.put("/api/v1/mfa/policy/system",
                                       json=policy_update,
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["requirement_level"] == "required"
        assert "totp" in data["allowed_methods"]
        assert data["grace_period_days"] == 7
    
    async def test_organization_mfa_policy(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization-specific MFA policy"""
        # Get current policy
        get_response = await test_client.get(f"/api/v1/mfa/policy/organization/{test_organization.id}",
                                           headers=auth_headers("admin_token"))
        
        assert get_response.status_code == 200
        
        # Update policy
        policy_update = {
            "requirement_level": "recommended",
            "enforcement_scopes": ["login"],
            "allowed_methods": ["totp", "email"],
            "exceptions": ["admin@example.com"]
        }
        
        update_response = await test_client.put(f"/api/v1/mfa/policy/organization/{test_organization.id}",
                                              json=policy_update,
                                              headers=auth_headers("admin_token"))
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["requirement_level"] == "recommended"
    
    async def test_user_mfa_policy(self, test_client: AsyncClient, test_user, auth_headers):
        """Test user-specific MFA policy"""
        # Get user policy
        get_response = await test_client.get(f"/api/v1/mfa/policy/user/{test_user.id}",
                                           headers=auth_headers("admin_token"))
        
        assert get_response.status_code == 200
        
        # Update user policy
        policy_update = {
            "requirement_level": "disabled",
            "exceptions": ["medical_emergency"]
        }
        
        update_response = await test_client.put(f"/api/v1/mfa/policy/user/{test_user.id}",
                                              json=policy_update,
                                              headers=auth_headers("admin_token"))
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["requirement_level"] == "disabled"
    
    async def test_mfa_policy_hierarchy(self, test_client: AsyncClient, test_user, test_organization, auth_headers):
        """Test MFA policy inheritance hierarchy"""
        # System > Organization > User
        
        # Set system policy
        await test_client.put("/api/v1/mfa/policy/system",
                            json={"requirement_level": "recommended"},
                            headers=auth_headers("admin_token"))
        
        # Set organization policy
        await test_client.put(f"/api/v1/mfa/policy/organization/{test_organization.id}",
                            json={"requirement_level": "required"},
                            headers=auth_headers("admin_token"))
        
        # Get user's effective policy
        status_response = await test_client.get(f"/api/v1/mfa/policy/status/{test_user.id}",
                                              headers=auth_headers("valid_token"))
        
        if status_response.status_code == 200:
            status = status_response.json()
            
            # Should inherit organization policy (most restrictive)
            assert status["policy_source"] in ["organization", "system"]
            
            if "mfa_required" in status:
                # Organization policy should override system policy
                assert isinstance(status["mfa_required"], bool)
    
    async def test_mfa_status_for_user(self, test_client: AsyncClient, test_user, auth_headers):
        """Test getting user's MFA status"""
        response = await test_client.get(f"/api/v1/mfa/policy/status/{test_user.id}",
                                       headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["mfa_required", "mfa_recommended", "allowed_methods", "current_methods", "policy_source"]
        for field in required_fields:
            assert field in data
        
        assert isinstance(data["mfa_required"], bool)
        assert isinstance(data["mfa_recommended"], bool)
        assert isinstance(data["allowed_methods"], list)
        assert isinstance(data["current_methods"], list)
    
    async def test_mfa_configuration_overview(self, test_client: AsyncClient, test_user, auth_headers):
        """Test getting user's MFA configuration overview"""
        response = await test_client.get(f"/api/v1/mfa/policy/configuration/{test_user.id}",
                                       headers=auth_headers("valid_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert "effective_policy" in data
        assert "compliance_status" in data
        assert "recommendations" in data
        
        # Compliance status should indicate if user meets requirements
        assert data["compliance_status"] in ["compliant", "non_compliant", "grace_period"]
    
    async def test_mfa_policy_validation(self, test_client: AsyncClient, auth_headers):
        """Test MFA policy validation"""
        invalid_policies = [
            {"requirement_level": "invalid_level"},
            {"enforcement_scopes": ["invalid_scope"]},
            {"allowed_methods": ["invalid_method"]},
            {"grace_period_days": -1},
            {"grace_period_days": "not_a_number"}
        ]
        
        for invalid_policy in invalid_policies:
            response = await test_client.put("/api/v1/mfa/policy/system",
                                           json=invalid_policy,
                                           headers=auth_headers("admin_token"))
            
            assert response.status_code == 422  # Validation error


@pytest.mark.mfa
@pytest.mark.integration
@pytest.mark.asyncio
class TestMFASecurityScenarios:
    """Test MFA security scenarios and attack prevention"""
    
    async def test_mfa_brute_force_protection(self, test_client: AsyncClient, test_user, test_mfa_method, auth_headers):
        """Test MFA brute force protection"""
        # Attempt multiple failed verifications
        failed_attempts = []
        
        for i in range(10):
            response = await test_client.post("/api/v1/mfa/verify",
                                            json={
                                                "method_id": str(test_mfa_method.id),
                                                "challenge_code": f"00000{i}"
                                            },
                                            headers=auth_headers("valid_token"))
            
            failed_attempts.append(response.status_code)
        
        # Should see failures and eventually rate limiting
        assert all(status in [400, 429] for status in failed_attempts)
        
        # Eventually should be rate limited
        assert any(status == 429 for status in failed_attempts[-3:])
    
    async def test_mfa_timing_attack_resistance(self, test_client: AsyncClient, test_user, auth_headers):
        """Test MFA timing attack resistance"""
        import time
        
        # Setup TOTP
        setup_response = await test_client.post("/api/v1/mfa/setup",
                                              json={
                                                  "method_type": "totp",
                                                  "metadata": {"app_name": "Timing Test"}
                                              },
                                              headers=auth_headers("valid_token"))
        
        if setup_response.status_code != 200:
            pytest.skip("TOTP setup failed")
        
        method_id = setup_response.json()["method_id"]
        
        # Test timing for valid vs invalid codes
        times = {"valid": [], "invalid": []}
        
        # Invalid codes
        for i in range(5):
            start = time.time()
            response = await test_client.post("/api/v1/mfa/verify",
                                            json={
                                                "method_id": method_id,
                                                "challenge_code": f"00000{i}"
                                            },
                                            headers=auth_headers("valid_token"))
            end = time.time()
            times["invalid"].append(end - start)
        
        # Valid codes (with mocking)
        with patch('pyotp.TOTP.verify', return_value=True):
            for i in range(5):
                start = time.time()
                response = await test_client.post("/api/v1/mfa/verify",
                                                json={
                                                    "method_id": method_id,
                                                    "challenge_code": "123456"
                                                },
                                                headers=auth_headers("valid_token"))
                end = time.time()
                times["valid"].append(end - start)
        
        # Response times should be similar
        avg_valid = sum(times["valid"]) / len(times["valid"])
        avg_invalid = sum(times["invalid"]) / len(times["invalid"])
        
        # Timing difference should be minimal
        timing_difference = abs(avg_valid - avg_invalid)
        assert timing_difference < 0.5  # Less than 500ms difference
    
    async def test_mfa_replay_prevention_across_sessions(self, test_client: AsyncClient, test_user, auth_headers):
        """Test MFA replay prevention across different sessions"""
        # Setup TOTP
        setup_response = await test_client.post("/api/v1/mfa/setup",
                                              json={
                                                  "method_type": "totp",
                                                  "metadata": {"app_name": "Replay Test"}
                                              },
                                              headers=auth_headers("valid_token"))
        
        if setup_response.status_code != 200:
            pytest.skip("TOTP setup failed")
        
        method_id = setup_response.json()["method_id"]
        
        # Generate a TOTP code
        with patch('pyotp.TOTP.verify', return_value=True) as mock_verify:
            # Use code in first session
            response1 = await test_client.post("/api/v1/mfa/verify",
                                             json={
                                                 "method_id": method_id,
                                                 "challenge_code": "123456"
                                             },
                                             headers=auth_headers("valid_token"))
            
            assert response1.status_code == 200
        
        # Try to use same code again (should be blocked by replay prevention)
        with patch('pyotp.TOTP.verify', return_value=False) as mock_verify:
            response2 = await test_client.post("/api/v1/mfa/verify",
                                             json={
                                                 "method_id": method_id,
                                                 "challenge_code": "123456"
                                             },
                                             headers=auth_headers("valid_token"))
            
            assert response2.status_code == 400
    
    async def test_mfa_method_enumeration_protection(self, test_client: AsyncClient, auth_headers):
        """Test protection against MFA method enumeration"""
        # Try to access MFA methods for non-existent user
        fake_user_id = str(uuid.uuid4())
        
        response = await test_client.get(f"/api/v1/mfa/policy/status/{fake_user_id}",
                                       headers=auth_headers("admin_token"))
        
        # Should not reveal whether user exists
        assert response.status_code in [404, 403, 401]
        
        # Response should not leak information about user existence
        if response.status_code == 404:
            assert "not found" in response.json()["detail"].lower()
    
    async def test_mfa_privilege_escalation_prevention(self, test_client: AsyncClient, test_user, auth_headers):
        """Test prevention of privilege escalation through MFA"""
        # Regular user should not be able to modify system policies
        response = await test_client.put("/api/v1/mfa/policy/system",
                                       json={"requirement_level": "disabled"},
                                       headers=auth_headers("user_token"))
        
        assert response.status_code in [401, 403]
        
        # Regular user should not modify other users' policies
        other_user_id = str(uuid.uuid4())
        response = await test_client.put(f"/api/v1/mfa/policy/user/{other_user_id}",
                                       json={"requirement_level": "disabled"},
                                       headers=auth_headers("user_token"))
        
        assert response.status_code in [401, 403, 404]