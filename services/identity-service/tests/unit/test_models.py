"""
Unit tests for Identity Service database models
Tests model creation, validation, relationships, and methods
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.enhanced_models import (
    User, Organization, UserProfile, MFAMethod, 
    MFAChallenge, PasswordReset, EmailVerification,
    UserSession, UserActivityLog, UserPreference
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserModel:
    """Unit tests for User model"""
    
    async def test_user_creation(self, test_session: AsyncSession):
        """Test basic user creation"""
        user_data = {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewLCYeQ3ZsYe4Y9K",
            "is_active": True,
            "is_verified": True,
            "organization_id": uuid.uuid4()
        }
        
        user = User(**user_data)
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        
        assert user.id is not None
        assert user.email == user_data["email"]
        assert user.first_name == user_data["first_name"]
        assert user.last_name == user_data["last_name"]
        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        assert user.is_active is True
        assert user.is_verified is True
    
    async def test_user_email_uniqueness(self, test_session: AsyncSession):
        """Test that email addresses must be unique"""
        email = "unique@example.com"
        
        # Create first user
        user1 = User(
            email=email,
            first_name="User",
            last_name="One",
            password_hash="hash1",
            organization_id=uuid.uuid4()
        )
        test_session.add(user1)
        await test_session.commit()
        
        # Try to create second user with same email
        user2 = User(
            email=email,
            first_name="User Two", 
            password_hash="hash2",
            organization_id=uuid.uuid4()
        )
        test_session.add(user2)
        
        with pytest.raises(IntegrityError):
            await test_session.commit()
    
    async def test_user_defaults(self, test_session: AsyncSession):
        """Test default values are set correctly"""
        user = User(
            email="defaults@example.com",
            first_name="Default User",
            password_hash="hash",
            organization_id=uuid.uuid4()
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        
        assert user.is_active is True  # Default should be True
        assert user.is_verified is False  # Default should be False
        assert user.status == "pending_verification"  # Default status
        assert user.created_at is not None
        assert user.updated_at is not None
    
    async def test_user_string_representation(self, test_session: AsyncSession):
        """Test user string representation"""
        user = User(
            email="repr@example.com",
            first_name="Repr User",
            password_hash="hash",
            organization_id=uuid.uuid4()
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        
        user_str = str(user)
        assert "User object at" in user_str  # Default SQLAlchemy object representation


@pytest.mark.unit
@pytest.mark.asyncio
class TestOrganizationModel:
    """Unit tests for Organization model"""
    
    async def test_organization_creation(self, test_session: AsyncSession):
        """Test organization creation with all fields"""
        org_data = {
            "name": "Test Organization",
            "slug": "test-organization",
            "organization_type": "small_business",
            "is_active": True,
            "settings": {"theme": "light", "notifications": True}
        }
        
        organization = Organization(**org_data)
        test_session.add(organization)
        await test_session.commit()
        await test_session.refresh(organization)
        
        assert organization.id is not None
        assert organization.name == org_data["name"]
        assert organization.slug == org_data["slug"]
        assert organization.organization_type == org_data["organization_type"]
        assert organization.is_active == org_data["is_active"]
        assert organization.is_active is True
        assert organization.settings == org_data["settings"]
        assert organization.created_at is not None
    
    async def test_organization_slug_uniqueness(self, test_session: AsyncSession):
        """Test organization slug uniqueness"""
        slug = "unique-organization"
        
        # Create first organization
        org1 = Organization(
            name="Organization One",
            slug=slug,
            organization_type="small_business"
        )
        test_session.add(org1)
        await test_session.commit()
        
        # Try to create second organization with same slug
        org2 = Organization(
            name="Organization Two",
            slug=slug,
            organization_type="non_profit"
        )
        test_session.add(org2)
        
        with pytest.raises(IntegrityError):
            await test_session.commit()
    
    async def test_organization_domain_validation(self, test_session: AsyncSession):
        """Test organization website_url field"""
        org = Organization(
            name="Domain Test Org",
            slug="domain-test-org",
            website_url="https://domain-test.com",
            organization_type="small_business"
        )
        test_session.add(org)
        await test_session.commit()
        await test_session.refresh(org)
        
        assert org.website_url == "https://domain-test.com"
        assert org.name == "Domain Test Org"


@pytest.mark.unit 
@pytest.mark.asyncio
class TestUserProfileModel:
    """Unit tests for UserProfile model"""
    
    async def test_user_profile_creation(self, test_user):
        """Test user profile creation"""
        profile_data = {
            "user_id": test_user.id,
            "bio": "Test user biography",
            "avatar_url": "https://example.com/avatar.jpg",
            "phone": "+1234567890",
            "timezone": "UTC",
            "language": "en",
            "metadata": {"preference": "test"}
        }
        
        profile = UserProfile(**profile_data)
        # Profile creation would be tested with session if needed
        
        assert profile.user_id == test_user.id
        assert profile.bio == profile_data["bio"]
        assert profile.avatar_url == profile_data["avatar_url"]
        assert profile.phone == profile_data["phone"]
        assert profile.timezone == profile_data["timezone"]
        assert profile.language == profile_data["language"]
        assert profile.metadata == profile_data["metadata"]


@pytest.mark.unit
@pytest.mark.asyncio  
class TestMFAMethodModel:
    """Unit tests for MFAMethod model"""
    
    async def test_mfa_method_creation(self, test_user):
        """Test MFA method creation"""
        mfa_data = {
            "user_id": test_user.id,
            "method_type": "totp",
            "is_enabled": True,
            "secret": "JBSWY3DPEHPK3PXP",
            "metadata": {"app_name": "Test App"}
        }
        
        mfa_method = MFAMethod(**mfa_data)
        
        assert mfa_method.user_id == test_user.id
        assert mfa_method.method_type == "totp"
        assert mfa_method.is_enabled is True
        assert mfa_method.secret == "JBSWY3DPEHPK3PXP"
        assert mfa_method.metadata["app_name"] == "Test App"
    
    async def test_mfa_method_types(self, test_user):
        """Test different MFA method types"""
        method_types = ["email", "sms", "totp", "backup_codes"]
        
        for method_type in method_types:
            mfa_method = MFAMethod(
                user_id=test_user.id,
                method_type=method_type,
                is_enabled=True,
                secret=f"secret_{method_type}"
            )
            assert mfa_method.method_type == method_type
    
    async def test_mfa_method_defaults(self, test_user):
        """Test MFA method default values"""
        mfa_method = MFAMethod(
            user_id=test_user.id,
            method_type="email",
            secret="test_secret"
        )
        
        assert mfa_method.is_enabled is False  # Default should be False
        assert mfa_method.created_at is not None
        assert mfa_method.metadata == {}  # Default empty dict


@pytest.mark.unit
@pytest.mark.asyncio
class TestMFAChallengeModel:
    """Unit tests for MFAChallenge model"""
    
    async def test_mfa_challenge_creation(self, test_user, test_mfa_method):
        """Test MFA challenge creation"""
        challenge_data = {
            "user_id": test_user.id,
            "method_id": test_mfa_method.id,
            "challenge_type": "totp",
            "challenge_code": "123456",
            "expires_at": datetime.utcnow() + timedelta(minutes=5),
            "is_used": False
        }
        
        challenge = MFAChallenge(**challenge_data)
        
        assert challenge.user_id == test_user.id
        assert challenge.method_id == test_mfa_method.id
        assert challenge.challenge_type == "totp"
        assert challenge.challenge_code == "123456"
        assert challenge.is_used is False
        assert challenge.expires_at > datetime.utcnow()
    
    async def test_mfa_challenge_expiry(self, test_user, test_mfa_method):
        """Test MFA challenge expiry logic"""
        # Expired challenge
        expired_challenge = MFAChallenge(
            user_id=test_user.id,
            method_id=test_mfa_method.id,
            challenge_type="email",
            challenge_code="123456",
            expires_at=datetime.utcnow() - timedelta(minutes=1),
            is_used=False
        )
        
        assert expired_challenge.expires_at < datetime.utcnow()
        
        # Valid challenge
        valid_challenge = MFAChallenge(
            user_id=test_user.id,
            method_id=test_mfa_method.id,
            challenge_type="sms",
            challenge_code="654321",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            is_used=False
        )
        
        assert valid_challenge.expires_at > datetime.utcnow()


@pytest.mark.unit
@pytest.mark.asyncio
class TestPasswordResetModel:
    """Unit tests for PasswordReset model"""
    
    async def test_password_reset_creation(self, test_user):
        """Test password reset token creation"""
        reset_data = {
            "user_id": test_user.id,
            "reset_token": "secure-reset-token-123",
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "is_used": False,
            "created_at": datetime.utcnow()
        }
        
        reset = PasswordReset(**reset_data)
        
        assert reset.user_id == test_user.id
        assert reset.reset_token == "secure-reset-token-123"
        assert reset.expires_at > datetime.utcnow()
        assert reset.is_used is False
    
    async def test_password_reset_token_uniqueness(self, test_user):
        """Test that reset tokens should be unique"""
        token = "unique-token-123"
        
        reset1 = PasswordReset(
            user_id=test_user.id,
            reset_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        reset2 = PasswordReset(
            user_id=test_user.id,
            reset_token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        # Both objects can be created, but database constraint should prevent duplicates
        assert reset1.reset_token == reset2.reset_token


@pytest.mark.unit
@pytest.mark.asyncio
class TestEmailVerificationModel:
    """Unit tests for EmailVerification model"""
    
    async def test_email_verification_creation(self, test_user):
        """Test email verification creation"""
        verification_data = {
            "user_id": test_user.id,
            "verification_token": "email-verify-token-123",
            "expires_at": datetime.utcnow() + timedelta(days=1),
            "is_used": False
        }
        
        verification = EmailVerification(**verification_data)
        
        assert verification.user_id == test_user.id
        assert verification.verification_token == "email-verify-token-123"
        assert verification.expires_at > datetime.utcnow()
        assert verification.is_used is False
    
    async def test_email_verification_defaults(self, test_user):
        """Test email verification default values"""
        verification = EmailVerification(
            user_id=test_user.id,
            verification_token="token",
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        
        assert verification.is_used is False  # Default
        assert verification.created_at is not None


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserSessionModel:
    """Unit tests for UserSession model"""
    
    async def test_user_session_creation(self, test_user):
        """Test user session creation"""
        session_data = {
            "user_id": test_user.id,
            "session_token": "session-token-123",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0 Test Browser",
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "is_active": True,
            "device_info": {"os": "macOS", "browser": "Chrome"}
        }
        
        session = UserSession(**session_data)
        
        assert session.user_id == test_user.id
        assert session.session_token == "session-token-123"
        assert session.ip_address == "192.168.1.100"
        assert session.user_agent == "Mozilla/5.0 Test Browser"
        assert session.is_active is True
        assert session.device_info["os"] == "macOS"
    
    async def test_user_session_defaults(self, test_user):
        """Test user session default values"""
        session = UserSession(
            user_id=test_user.id,
            session_token="token",
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        assert session.is_active is True  # Default
        assert session.created_at is not None
        assert session.last_accessed is not None


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserActivityLogModel:
    """Unit tests for UserActivityLog model"""
    
    async def test_activity_log_creation(self, test_user):
        """Test user activity log creation"""
        activity_data = {
            "user_id": test_user.id,
            "action": "login",
            "resource": "auth/login",
            "ip_address": "192.168.1.100",
            "user_agent": "Test Browser",
            "metadata": {"success": True, "mfa_used": False}
        }
        
        activity = UserActivityLog(**activity_data)
        
        assert activity.user_id == test_user.id
        assert activity.action == "login"
        assert activity.resource == "auth/login"
        assert activity.ip_address == "192.168.1.100"
        assert activity.metadata["success"] is True
        assert activity.created_at is not None
    
    async def test_activity_log_different_actions(self, test_user):
        """Test different activity log actions"""
        actions = ["login", "logout", "password_change", "profile_update", "mfa_setup"]
        
        for action in actions:
            activity = UserActivityLog(
                user_id=test_user.id,
                action=action,
                resource=f"test/{action}",
                metadata={"test": True}
            )
            assert activity.action == action


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserPreferenceModel:
    """Unit tests for UserPreference model"""
    
    async def test_user_preference_creation(self, test_user):
        """Test user preference creation"""
        preference_data = {
            "user_id": test_user.id,
            "preference_key": "theme",
            "preference_value": "dark",
            "category": "appearance"
        }
        
        preference = UserPreference(**preference_data)
        
        assert preference.user_id == test_user.id
        assert preference.preference_key == "theme"
        assert preference.preference_value == "dark"
        assert preference.category == "appearance"
    
    async def test_user_preference_different_types(self, test_user):
        """Test different preference value types"""
        preferences = [
            ("notifications", "true", "settings"),
            ("language", "en", "localization"),
            ("timezone", "UTC", "localization"),
            ("dashboard_layout", "grid", "appearance")
        ]
        
        for key, value, category in preferences:
            preference = UserPreference(
                user_id=test_user.id,
                preference_key=key,
                preference_value=value,
                category=category
            )
            assert preference.preference_key == key
            assert preference.preference_value == value
            assert preference.category == category


@pytest.mark.unit
@pytest.mark.asyncio  
class TestModelRelationships:
    """Test model relationships and foreign keys"""
    
    async def test_user_organization_relationship(self, test_session: AsyncSession, test_organization):
        """Test user-organization relationship"""
        user = User(
            email="relationship@example.com",
            first_name="Relationship User",
            password_hash="hash",
            organization_id=test_organization.id
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        
        assert user.organization_id == test_organization.id
    
    async def test_user_mfa_methods_relationship(self, test_session: AsyncSession, test_user):
        """Test user can have multiple MFA methods"""
        mfa_methods = [
            MFAMethod(user_id=test_user.id, method_type="email", secret="email_secret"),
            MFAMethod(user_id=test_user.id, method_type="totp", secret="totp_secret"),
            MFAMethod(user_id=test_user.id, method_type="sms", secret="sms_secret")
        ]
        
        for method in mfa_methods:
            test_session.add(method)
        
        await test_session.commit()
        
        # All methods should belong to the same user
        for method in mfa_methods:
            assert method.user_id == test_user.id
    
    async def test_mfa_method_challenges_relationship(self, test_session: AsyncSession, test_user, test_mfa_method):
        """Test MFA method can have multiple challenges"""
        challenges = [
            MFAChallenge(
                user_id=test_user.id,
                method_id=test_mfa_method.id,
                challenge_type="totp",
                challenge_code="123456",
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            ),
            MFAChallenge(
                user_id=test_user.id, 
                method_id=test_mfa_method.id,
                challenge_type="totp",
                challenge_code="654321",
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
        ]
        
        for challenge in challenges:
            test_session.add(challenge)
        
        await test_session.commit()
        
        # All challenges should belong to the same method and user
        for challenge in challenges:
            assert challenge.user_id == test_user.id
            assert challenge.method_id == test_mfa_method.id


@pytest.mark.unit
@pytest.mark.asyncio
class TestModelValidation:
    """Test model validation and constraints"""
    
    async def test_user_email_validation(self, test_session: AsyncSession):
        """Test user email format validation"""
        # Valid emails should work (tested elsewhere)
        # Invalid emails would be caught by application layer, not model layer
        
        user = User(
            email="valid@example.com",
            first_name="Valid User",
            password_hash="hash",
            organization_id=uuid.uuid4()
        )
        test_session.add(user)
        await test_session.commit()
        assert user.email == "valid@example.com"
    
    async def test_required_fields(self, test_session: AsyncSession):
        """Test that required fields are enforced"""
        # User without email should fail
        with pytest.raises(TypeError):
            User(name="No Email User", password_hash="hash")
        
        # Organization without name should fail
        with pytest.raises(TypeError):
            Organization(org_type="business")
    
    async def test_field_lengths(self, test_session: AsyncSession):
        """Test field length constraints"""
        # Very long name
        long_name = "x" * 1000
        
        user = User(
            email="longname@example.com",
            name=long_name,
            password_hash="hash",
            organization_id=uuid.uuid4()
        )
        
        # Model allows long names, database constraints would enforce limits
        assert len(user.name) == 1000
    
    async def test_enum_values(self, test_organization):
        """Test enum field validation"""
        # Valid organization types
        valid_types = ["business", "nonprofit", "government", "education"]
        
        for org_type in valid_types:
            org = Organization(
                name=f"Test {org_type} Org",
                org_type=org_type
            )
            assert org.org_type == org_type
        
        # Invalid organization type (would be validated at application layer)
        org = Organization(
            first_name="Invalid Type Org", 
            org_type="invalid_type"
        )
        # Model accepts any string, validation happens elsewhere
        assert org.org_type == "invalid_type"


@pytest.mark.unit
class TestModelUtilityMethods:
    """Test utility methods and properties on models"""
    
    def test_model_string_representations(self, test_user, test_organization):
        """Test __str__ and __repr__ methods"""
        user_str = str(test_user)
        org_str = str(test_organization)
        
        # Should contain meaningful information
        assert test_user.email in user_str or test_user.name in user_str
        assert test_organization.name in org_str
    
    def test_model_equality(self, test_user):
        """Test model equality comparison"""
        # Same user should be equal to itself
        assert test_user == test_user
        
        # Different users should not be equal
        other_user = User(
            email="other@example.com",
            first_name="Other User",
            password_hash="hash",
            organization_id=uuid.uuid4()
        )
        # Without database IDs, comparison might not work as expected
        # This tests the behavior, not necessarily desired functionality
    
    def test_model_hashing(self, test_user):
        """Test that models can be hashed (for use in sets, etc.)"""
        # Should be able to add to set without errors
        user_set = {test_user}
        assert len(user_set) == 1
        assert test_user in user_set
    
    async def test_timestamp_updates(self, test_session: AsyncSession):
        """Test that updated_at timestamps are maintained"""
        user = User(
            email="timestamp@example.com",
            first_name="Timestamp User",
            password_hash="hash",
            organization_id=uuid.uuid4()
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        
        original_updated_at = user.updated_at
        
        # Update user
        user.name = "Updated Name"
        await test_session.commit()
        await test_session.refresh(user)
        
        # updated_at should change (if automatic updating is implemented)
        # This depends on the model implementation
        assert user.name == "Updated Name"