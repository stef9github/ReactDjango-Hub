"""
Unit tests for Identity Service business logic
Tests authentication, user management, MFA, and organization services
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import AuthService, TokenService
from app.services.user_service import UserManagementService
from app.services.mfa_service import MFAService
from app.services.email_service import EmailService
from app.models.enhanced_models import User, Organization, MFAMethod, UserSession
from app.core.security import hash_password, verify_password


@pytest.mark.unit
@pytest.mark.asyncio
class TestAuthService:
    """Unit tests for AuthService"""
    
    @pytest.fixture
    def auth_service(self, test_session: AsyncSession):
        """Create AuthService instance"""
        return AuthService(test_session)
    
    async def test_authenticate_user_success(self, auth_service: AuthService, test_session: AsyncSession):
        """Test successful user authentication"""
        # Create test user with known password
        password = "testpassword123"
        hashed = hash_password(password)
        
        user = User(
            email="auth@example.com",
            name="Auth User",
            password_hash=hashed,
            is_active=True,
            is_verified=True,
            organization_id=uuid.uuid4()
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        
        # Test authentication
        result = await auth_service.authenticate_user(
            email="auth@example.com",
            password=password,
            remember_me=False,
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        
        assert result is not None
        assert "user_id" in result
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["user_id"] == str(user.id)
    
    async def test_authenticate_user_invalid_email(self, auth_service: AuthService):
        """Test authentication with invalid email"""
        result = await auth_service.authenticate_user(
            email="nonexistent@example.com",
            password="password123",
            remember_me=False,
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        
        assert result is None
    
    async def test_authenticate_user_invalid_password(self, auth_service: AuthService, test_session: AsyncSession):
        """Test authentication with invalid password"""
        password = "correctpassword123"
        hashed = hash_password(password)
        
        user = User(
            email="wrongpass@example.com",
            name="Wrong Pass User",
            password_hash=hashed,
            is_active=True,
            is_verified=True,
            organization_id=uuid.uuid4()
        )
        test_session.add(user)
        await test_session.commit()
        
        # Test with wrong password
        result = await auth_service.authenticate_user(
            email="wrongpass@example.com",
            password="wrongpassword123",
            remember_me=False,
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        
        assert result is None
    
    async def test_authenticate_inactive_user(self, auth_service: AuthService, test_session: AsyncSession):
        """Test authentication with inactive user"""
        password = "testpassword123"
        hashed = hash_password(password)
        
        user = User(
            email="inactive@example.com",
            name="Inactive User",
            password_hash=hashed,
            is_active=False,  # Inactive user
            is_verified=True,
            organization_id=uuid.uuid4()
        )
        test_session.add(user)
        await test_session.commit()
        
        result = await auth_service.authenticate_user(
            email="inactive@example.com",
            password=password,
            remember_me=False,
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        
        assert result is None
    
    async def test_authenticate_unverified_user(self, auth_service: AuthService, test_session: AsyncSession):
        """Test authentication with unverified user"""
        password = "testpassword123"
        hashed = hash_password(password)
        
        user = User(
            email="unverified@example.com",
            name="Unverified User",
            password_hash=hashed,
            is_active=True,
            is_verified=False,  # Unverified user
            organization_id=uuid.uuid4()
        )
        test_session.add(user)
        await test_session.commit()
        
        result = await auth_service.authenticate_user(
            email="unverified@example.com",
            password=password,
            remember_me=False,
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        
        # Should still authenticate but may require verification
        assert result is None or "requires_verification" in result
    
    @patch('app.services.auth_service.EventPublisher')
    async def test_authenticate_user_publishes_event(self, mock_publisher, auth_service: AuthService, test_session: AsyncSession):
        """Test that authentication publishes login event"""
        mock_publisher_instance = AsyncMock()
        mock_publisher.return_value = mock_publisher_instance
        
        password = "testpassword123"
        hashed = hash_password(password)
        
        user = User(
            email="event@example.com",
            name="Event User",
            password_hash=hashed,
            is_active=True,
            is_verified=True,
            organization_id=uuid.uuid4()
        )
        test_session.add(user)
        await test_session.commit()
        
        await auth_service.authenticate_user(
            email="event@example.com",
            password=password,
            remember_me=False,
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        
        # Verify event was published
        mock_publisher_instance.publish_event.assert_called_once()
        call_args = mock_publisher_instance.publish_event.call_args
        assert call_args[0][0] == "user.login"
        assert "user_id" in call_args[0][1]


@pytest.mark.unit
@pytest.mark.asyncio
class TestTokenService:
    """Unit tests for TokenService"""
    
    @pytest.fixture
    def token_service(self):
        """Create TokenService instance"""
        return TokenService()
    
    def test_create_access_token(self, token_service: TokenService, mock_user_data):
        """Test access token creation"""
        token = token_service.create_access_token(mock_user_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        decoded = token_service.decode_token(token)
        assert decoded["user_id"] == mock_user_data["user_id"]
        assert decoded["email"] == mock_user_data["email"]
    
    def test_create_refresh_token(self, token_service: TokenService, mock_user_data):
        """Test refresh token creation"""
        token = token_service.create_refresh_token(mock_user_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Refresh token should have longer expiry
        decoded = token_service.decode_token(token)
        assert decoded["user_id"] == mock_user_data["user_id"]
        assert decoded["type"] == "refresh"
    
    def test_decode_valid_token(self, token_service: TokenService, mock_user_data):
        """Test decoding valid token"""
        token = token_service.create_access_token(mock_user_data)
        decoded = token_service.decode_token(token)
        
        assert decoded is not None
        assert decoded["user_id"] == mock_user_data["user_id"]
        assert decoded["email"] == mock_user_data["email"]
        assert "exp" in decoded
    
    def test_decode_invalid_token(self, token_service: TokenService):
        """Test decoding invalid token"""
        invalid_token = "invalid.token.here"
        
        decoded = token_service.decode_token(invalid_token)
        assert decoded is None
    
    def test_decode_expired_token(self, token_service: TokenService, expired_jwt_token):
        """Test decoding expired token"""
        decoded = token_service.decode_token(expired_jwt_token)
        assert decoded is None
    
    def test_token_expiry_times(self, token_service: TokenService, mock_user_data):
        """Test that tokens have correct expiry times"""
        access_token = token_service.create_access_token(mock_user_data)
        refresh_token = token_service.create_refresh_token(mock_user_data)
        
        access_decoded = token_service.decode_token(access_token)
        refresh_decoded = token_service.decode_token(refresh_token)
        
        # Refresh token should expire later than access token
        assert refresh_decoded["exp"] > access_decoded["exp"]
    
    def test_refresh_token_validation(self, token_service: TokenService, mock_user_data):
        """Test refresh token specific validation"""
        refresh_token = token_service.create_refresh_token(mock_user_data)
        
        # Should validate successfully
        is_valid = token_service.validate_refresh_token(refresh_token)
        assert is_valid is True
        
        # Access token should not validate as refresh token
        access_token = token_service.create_access_token(mock_user_data)
        is_valid = token_service.validate_refresh_token(access_token)
        assert is_valid is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserManagementService:
    """Unit tests for UserManagementService"""
    
    @pytest.fixture
    def user_service(self, test_session: AsyncSession):
        """Create UserManagementService instance"""
        return UserManagementService(test_session)
    
    async def test_create_user_success(self, user_service: UserManagementService):
        """Test successful user creation"""
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "name": "New User",
            "phone": "+1234567890"
        }
        
        created_user = await user_service.create_user(user_data)
        
        assert created_user is not None
        assert created_user.email == user_data["email"]
        assert created_user.name == user_data["name"]
        assert created_user.is_active is True
        assert created_user.is_verified is False  # Should require verification
        assert created_user.password_hash != user_data["password"]  # Should be hashed
    
    async def test_create_user_duplicate_email(self, user_service: UserManagementService, test_user):
        """Test creating user with duplicate email fails"""
        user_data = {
            "email": test_user.email,  # Same email as existing user
            "password": "SecurePassword123!",
            "name": "Duplicate User"
        }
        
        with pytest.raises(ValueError, match="Email already registered"):
            await user_service.create_user(user_data)
    
    async def test_get_user_by_id(self, user_service: UserManagementService, test_user):
        """Test retrieving user by ID"""
        found_user = await user_service.get_user_by_id(str(test_user.id))
        
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.email == test_user.email
    
    async def test_get_user_by_id_not_found(self, user_service: UserManagementService):
        """Test retrieving non-existent user returns None"""
        non_existent_id = str(uuid.uuid4())
        
        found_user = await user_service.get_user_by_id(non_existent_id)
        assert found_user is None
    
    async def test_get_user_by_email(self, user_service: UserManagementService, test_user):
        """Test retrieving user by email"""
        found_user = await user_service.get_user_by_email(test_user.email)
        
        assert found_user is not None
        assert found_user.id == test_user.id
        assert found_user.email == test_user.email
    
    async def test_update_user_profile(self, user_service: UserManagementService, test_user):
        """Test updating user profile"""
        update_data = {
            "name": "Updated Name",
            "phone": "+0987654321"
        }
        
        updated_user = await user_service.update_user_profile(str(test_user.id), update_data)
        
        assert updated_user is not None
        assert updated_user.name == "Updated Name"
        # Phone would be in user profile, not user table
    
    async def test_deactivate_user(self, user_service: UserManagementService, test_user):
        """Test deactivating user"""
        result = await user_service.deactivate_user(str(test_user.id))
        
        assert result is True
        
        # Verify user is deactivated
        updated_user = await user_service.get_user_by_id(str(test_user.id))
        assert updated_user.is_active is False
    
    async def test_get_user_dashboard_data(self, user_service: UserManagementService, test_user):
        """Test getting comprehensive user dashboard data"""
        dashboard_data = await user_service.get_user_dashboard_data(str(test_user.id))
        
        assert dashboard_data is not None
        assert "user" in dashboard_data
        assert "activity_summary" in dashboard_data
        assert "session_count" in dashboard_data
        assert "mfa_methods" in dashboard_data
        assert dashboard_data["user"]["id"] == str(test_user.id)
    
    @patch('app.services.user_service.EventPublisher')
    async def test_create_user_publishes_event(self, mock_publisher, user_service: UserManagementService):
        """Test that user creation publishes event"""
        mock_publisher_instance = AsyncMock()
        mock_publisher.return_value = mock_publisher_instance
        
        user_data = {
            "email": "eventuser@example.com",
            "password": "SecurePassword123!",
            "name": "Event User"
        }
        
        await user_service.create_user(user_data)
        
        # Verify event was published
        mock_publisher_instance.publish_event.assert_called_once()
        call_args = mock_publisher_instance.publish_event.call_args
        assert call_args[0][0] == "user.created"


@pytest.mark.unit
@pytest.mark.asyncio
class TestMFAService:
    """Unit tests for MFAService"""
    
    @pytest.fixture
    def mfa_service(self, test_session: AsyncSession):
        """Create MFAService instance"""
        return MFAService(test_session)
    
    async def test_setup_totp_method(self, mfa_service: MFAService, test_user):
        """Test setting up TOTP MFA method"""
        result = await mfa_service.setup_mfa_method(
            user_id=str(test_user.id),
            method_type="totp",
            metadata={"app_name": "Test App"}
        )
        
        assert result is not None
        assert "secret" in result
        assert "qr_code" in result
        assert "backup_codes" in result
        assert result["method_type"] == "totp"
    
    async def test_setup_email_method(self, mfa_service: MFAService, test_user):
        """Test setting up email MFA method"""
        result = await mfa_service.setup_mfa_method(
            user_id=str(test_user.id),
            method_type="email"
        )
        
        assert result is not None
        assert result["method_type"] == "email"
        assert "method_id" in result
    
    async def test_setup_sms_method(self, mfa_service: MFAService, test_user):
        """Test setting up SMS MFA method"""
        result = await mfa_service.setup_mfa_method(
            user_id=str(test_user.id),
            method_type="sms",
            metadata={"phone": "+1234567890"}
        )
        
        assert result is not None
        assert result["method_type"] == "sms"
        assert "method_id" in result
    
    async def test_list_user_methods(self, mfa_service: MFAService, test_user, test_mfa_method):
        """Test listing user's MFA methods"""
        methods = await mfa_service.get_user_mfa_methods(str(test_user.id))
        
        assert methods is not None
        assert len(methods) >= 1
        
        method = methods[0]
        assert "id" in method
        assert "method_type" in method
        assert "is_enabled" in method
        assert "created_at" in method
    
    async def test_create_challenge_totp(self, mfa_service: MFAService, test_user, test_mfa_method):
        """Test creating TOTP challenge"""
        if test_mfa_method.method_type != "totp":
            test_mfa_method.method_type = "totp"
        
        challenge = await mfa_service.create_mfa_challenge(
            user_id=str(test_user.id),
            method_id=str(test_mfa_method.id)
        )
        
        assert challenge is not None
        assert "challenge_id" in challenge
        assert "expires_at" in challenge
        assert challenge["method_type"] == "totp"
    
    @patch('app.services.mfa_service.EmailService')
    async def test_create_challenge_email(self, mock_email, mfa_service: MFAService, test_user, test_mfa_method):
        """Test creating email MFA challenge"""
        mock_email_instance = AsyncMock()
        mock_email.return_value = mock_email_instance
        mock_email_instance.send_mfa_code.return_value = True
        
        test_mfa_method.method_type = "email"
        
        challenge = await mfa_service.create_mfa_challenge(
            user_id=str(test_user.id),
            method_id=str(test_mfa_method.id)
        )
        
        assert challenge is not None
        assert challenge["method_type"] == "email"
        
        # Verify email was sent
        mock_email_instance.send_mfa_code.assert_called_once()
    
    async def test_verify_totp_code_success(self, mfa_service: MFAService, test_user, test_mfa_method, valid_totp_code):
        """Test successful TOTP verification"""
        test_mfa_method.method_type = "totp"
        test_mfa_method.secret = "JBSWY3DPEHPK3PXP"  # Known test secret
        
        with patch('pyotp.TOTP.verify', return_value=True):
            result = await mfa_service.verify_mfa_challenge(
                user_id=str(test_user.id),
                method_id=str(test_mfa_method.id),
                challenge_code=valid_totp_code
            )
        
        assert result is True
    
    async def test_verify_totp_code_failure(self, mfa_service: MFAService, test_user, test_mfa_method):
        """Test failed TOTP verification"""
        test_mfa_method.method_type = "totp"
        
        with patch('pyotp.TOTP.verify', return_value=False):
            result = await mfa_service.verify_mfa_challenge(
                user_id=str(test_user.id),
                method_id=str(test_mfa_method.id),
                challenge_code="000000"  # Invalid code
            )
        
        assert result is False
    
    async def test_remove_mfa_method(self, mfa_service: MFAService, test_user, test_mfa_method):
        """Test removing MFA method"""
        result = await mfa_service.remove_mfa_method(
            user_id=str(test_user.id),
            method_id=str(test_mfa_method.id)
        )
        
        assert result is True
        
        # Verify method is removed
        methods = await mfa_service.get_user_mfa_methods(str(test_user.id))
        method_ids = [m["id"] for m in methods]
        assert str(test_mfa_method.id) not in method_ids
    
    async def test_generate_backup_codes(self, mfa_service: MFAService, test_user):
        """Test generating backup codes"""
        backup_codes = await mfa_service.generate_backup_codes(str(test_user.id))
        
        assert backup_codes is not None
        assert len(backup_codes) == 8  # Standard number of backup codes
        
        for code in backup_codes:
            assert isinstance(code, str)
            assert len(code) >= 8  # Minimum code length
    
    async def test_verify_backup_code(self, mfa_service: MFAService, test_user):
        """Test verifying backup code"""
        # First generate backup codes
        backup_codes = await mfa_service.generate_backup_codes(str(test_user.id))
        test_code = backup_codes[0]
        
        # Verify the code
        result = await mfa_service.verify_backup_code(str(test_user.id), test_code)
        assert result is True
        
        # Code should only work once
        result = await mfa_service.verify_backup_code(str(test_user.id), test_code)
        assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestEmailService:
    """Unit tests for EmailService"""
    
    @pytest.fixture
    def email_service(self):
        """Create EmailService instance"""
        return EmailService()
    
    @patch('smtplib.SMTP')
    async def test_send_verification_email(self, mock_smtp, email_service: EmailService):
        """Test sending verification email"""
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        
        result = await email_service.send_verification_email(
            email="test@example.com",
            name="Test User",
            verification_token="token123"
        )
        
        assert result is True
        mock_smtp_instance.send_message.assert_called_once()
    
    @patch('smtplib.SMTP')
    async def test_send_password_reset_email(self, mock_smtp, email_service: EmailService):
        """Test sending password reset email"""
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        
        result = await email_service.send_password_reset_email(
            email="test@example.com",
            name="Test User",
            reset_token="reset123"
        )
        
        assert result is True
        mock_smtp_instance.send_message.assert_called_once()
    
    @patch('smtplib.SMTP')
    async def test_send_mfa_code_email(self, mock_smtp, email_service: EmailService):
        """Test sending MFA code via email"""
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value = mock_smtp_instance
        
        result = await email_service.send_mfa_code(
            email="test@example.com",
            name="Test User",
            mfa_code="123456"
        )
        
        assert result is True
        mock_smtp_instance.send_message.assert_called_once()
    
    async def test_email_template_rendering(self, email_service: EmailService):
        """Test email template rendering"""
        template_data = {
            "name": "Test User",
            "verification_link": "https://example.com/verify/token123"
        }
        
        rendered = email_service.render_template("verification", template_data)
        
        assert rendered is not None
        assert "Test User" in rendered
        assert "https://example.com/verify/token123" in rendered
    
    @patch('smtplib.SMTP', side_effect=Exception("SMTP Error"))
    async def test_email_sending_failure(self, mock_smtp, email_service: EmailService):
        """Test email sending failure handling"""
        result = await email_service.send_verification_email(
            email="test@example.com",
            name="Test User",
            verification_token="token123"
        )
        
        assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestServiceIntegration:
    """Test service integration and dependencies"""
    
    @pytest.fixture
    def auth_service(self, test_session: AsyncSession):
        return AuthService(test_session)
    
    @pytest.fixture
    def user_service(self, test_session: AsyncSession):
        return UserManagementService(test_session)
    
    @pytest.fixture
    def mfa_service(self, test_session: AsyncSession):
        return MFAService(test_session)
    
    async def test_user_creation_flow(self, user_service: UserManagementService, auth_service: AuthService):
        """Test complete user creation and authentication flow"""
        # Create user
        user_data = {
            "email": "flow@example.com",
            "password": "FlowPassword123!",
            "name": "Flow User"
        }
        
        created_user = await user_service.create_user(user_data)
        assert created_user is not None
        
        # Activate and verify user (would normally be done via email verification)
        created_user.is_verified = True
        
        # Authenticate user
        auth_result = await auth_service.authenticate_user(
            email=user_data["email"],
            password=user_data["password"],
            remember_me=False,
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        
        assert auth_result is not None
        assert "access_token" in auth_result
        assert auth_result["user_id"] == str(created_user.id)
    
    async def test_mfa_setup_and_authentication_flow(self, user_service: UserManagementService, mfa_service: MFAService, test_user):
        """Test MFA setup and verification flow"""
        # Setup TOTP MFA
        mfa_setup = await mfa_service.setup_mfa_method(
            user_id=str(test_user.id),
            method_type="totp"
        )
        
        assert mfa_setup is not None
        method_id = mfa_setup["method_id"]
        
        # Create MFA challenge
        challenge = await mfa_service.create_mfa_challenge(
            user_id=str(test_user.id),
            method_id=method_id
        )
        
        assert challenge is not None
        
        # Verify challenge (with mocked TOTP)
        with patch('pyotp.TOTP.verify', return_value=True):
            verification = await mfa_service.verify_mfa_challenge(
                user_id=str(test_user.id),
                method_id=method_id,
                challenge_code="123456"
            )
        
        assert verification is True
    
    async def test_password_reset_flow(self, user_service: UserManagementService, auth_service: AuthService, test_user):
        """Test password reset flow"""
        original_password = "OriginalPassword123!"
        new_password = "NewPassword123!"
        
        # Set original password
        test_user.password_hash = hash_password(original_password)
        
        # Initiate password reset
        reset_token = await auth_service.initiate_password_reset(test_user.email)
        assert reset_token is not None
        
        # Reset password
        result = await auth_service.reset_password(reset_token, new_password)
        assert result is True
        
        # Verify old password no longer works
        auth_result = await auth_service.authenticate_user(
            email=test_user.email,
            password=original_password,
            remember_me=False,
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        assert auth_result is None
        
        # Verify new password works
        auth_result = await auth_service.authenticate_user(
            email=test_user.email,
            password=new_password,
            remember_me=False,
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        assert auth_result is not None


@pytest.mark.unit
class TestServiceErrorHandling:
    """Test service error handling and edge cases"""
    
    @pytest.fixture
    def mock_session(self):
        """Mock database session that raises errors"""
        session = AsyncMock()
        session.commit.side_effect = Exception("Database error")
        return session
    
    async def test_auth_service_database_error(self, mock_session):
        """Test auth service handles database errors"""
        auth_service = AuthService(mock_session)
        
        # Should handle database errors gracefully
        result = await auth_service.authenticate_user(
            email="test@example.com",
            password="password",
            remember_me=False,
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        
        assert result is None  # Should return None on error
    
    async def test_user_service_database_error(self, mock_session):
        """Test user service handles database errors"""
        user_service = UserManagementService(mock_session)
        
        user_data = {
            "email": "error@example.com",
            "password": "ErrorPassword123!",
            "name": "Error User"
        }
        
        # Should handle database errors gracefully
        with pytest.raises(Exception):  # Or whatever error handling is implemented
            await user_service.create_user(user_data)
    
    async def test_mfa_service_invalid_method_type(self, test_session: AsyncSession, test_user):
        """Test MFA service handles invalid method types"""
        mfa_service = MFAService(test_session)
        
        with pytest.raises(ValueError, match="Unsupported MFA method"):
            await mfa_service.setup_mfa_method(
                user_id=str(test_user.id),
                method_type="invalid_type"
            )
    
    async def test_service_with_none_inputs(self, test_session: AsyncSession):
        """Test services handle None inputs gracefully"""
        auth_service = AuthService(test_session)
        
        # Should handle None email
        result = await auth_service.authenticate_user(
            email=None,
            password="password",
            remember_me=False,
            ip_address="127.0.0.1",
            user_agent="Test Browser"
        )
        
        assert result is None
    
    async def test_service_with_empty_inputs(self, test_session: AsyncSession):
        """Test services handle empty inputs gracefully"""
        user_service = UserManagementService(test_session)
        
        # Should handle empty user data
        with pytest.raises((ValueError, TypeError)):
            await user_service.create_user({})


@pytest.mark.unit
class TestServicePerformance:
    """Test service performance characteristics"""
    
    @pytest.mark.benchmark
    def test_password_hashing_performance(self, benchmark):
        """Test password hashing performance"""
        def hash_password_test():
            return hash_password("TestPassword123!")
        
        result = benchmark(hash_password_test)
        assert result is not None
    
    @pytest.mark.benchmark
    def test_token_creation_performance(self, benchmark, mock_user_data):
        """Test JWT token creation performance"""
        token_service = TokenService()
        
        def create_token_test():
            return token_service.create_access_token(mock_user_data)
        
        result = benchmark(create_token_test)
        assert result is not None
    
    @pytest.mark.benchmark
    def test_token_verification_performance(self, benchmark, mock_user_data):
        """Test JWT token verification performance"""
        token_service = TokenService()
        token = token_service.create_access_token(mock_user_data)
        
        def verify_token_test():
            return token_service.decode_token(token)
        
        result = benchmark(verify_token_test)
        assert result is not None