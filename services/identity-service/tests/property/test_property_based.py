"""
Property-based tests for Identity Service
Uses Hypothesis to generate test data and verify system properties
"""

import pytest
import re
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, assume, example, settings
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, invariant
from httpx import AsyncClient

from app.core.security import SecurityUtils
from app.models.enhanced_models import User, Organization, UserStatus, OrganizationType


# Custom strategies for domain-specific data
@st.composite
def valid_email(draw):
    """Generate valid email addresses"""
    local = draw(st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        min_size=1, max_size=20
    ).filter(lambda x: not x.startswith('.') and not x.endswith('.')))
    
    domain = draw(st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")) + '-',
        min_size=1, max_size=15
    ).filter(lambda x: not x.startswith('-') and not x.endswith('-')))
    
    tld = draw(st.sampled_from(['com', 'org', 'net', 'edu', 'gov']))
    
    return f"{local}@{domain}.{tld}"


@st.composite  
def valid_password(draw):
    """Generate valid passwords meeting security requirements"""
    # At least 8 chars, with uppercase, lowercase, number, special char
    base = draw(st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pc", "Pd", "Ps", "Pe")),
        min_size=8, max_size=50
    ))
    
    # Ensure at least one of each required character type
    if not any(c.isupper() for c in base):
        base += 'A'
    if not any(c.islower() for c in base):
        base += 'a'  
    if not any(c.isdigit() for c in base):
        base += '1'
    if not any(c in '!@#$%^&*()_+-=' for c in base):
        base += '!'
        
    return base


@st.composite
def valid_organization_slug(draw):
    """Generate valid organization slugs"""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Nd")) + '-',
        min_size=1, max_size=50
    ).filter(lambda x: not x.startswith('-') and not x.endswith('-') and '--' not in x))


@st.composite
def user_data(draw):
    """Generate valid user data"""
    return {
        "email": draw(valid_email()),
        "first_name": draw(st.text(min_size=1, max_size=100).filter(str.strip)),
        "last_name": draw(st.text(min_size=1, max_size=100).filter(str.strip)),
        "password": draw(valid_password()),
    }


@st.composite
def organization_data(draw):
    """Generate valid organization data"""
    return {
        "name": draw(st.text(min_size=1, max_size=200).filter(str.strip)),
        "slug": draw(valid_organization_slug()),
        "organization_type": draw(st.sampled_from([e.value for e in OrganizationType])),
        "description": draw(st.one_of(st.none(), st.text(max_size=500))),
        "website_url": draw(st.one_of(st.none(), st.just("https://example.com"))),
    }


@pytest.mark.property
@pytest.mark.asyncio  
class TestUserProperties:
    """Property-based tests for User model behavior"""
    
    @given(user_data())
    @example({
        "email": "test@example.com", 
        "first_name": "Test",
        "last_name": "User",
        "password": "SecurePass123!"
    })
    async def test_user_creation_properties(self, test_session, data):
        """Test that user creation maintains invariants"""
        # Create user
        user = User(
            email=data["email"],
            first_name=data["first_name"], 
            last_name=data["last_name"],
            password_hash=SecurityUtils.hash_password(data["password"])
        )
        
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        
        # Invariants that should always hold
        assert user.id is not None
        assert user.email == data["email"]
        assert user.first_name == data["first_name"]
        assert user.last_name == data["last_name"]
        assert user.is_active is True  # Default
        assert user.is_verified is False  # Default
        assert user.status == UserStatus.PENDING_VERIFICATION  # Default
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.created_at <= user.updated_at
        assert isinstance(user.created_at, datetime)
    
    @given(st.text(), st.text())
    async def test_password_hashing_properties(self, password1, password2):
        """Test password hashing properties"""
        assume(password1 != password2)
        assume(len(password1) > 0 and len(password2) > 0)
        
        hash1 = SecurityUtils.hash_password(password1)
        hash2 = SecurityUtils.hash_password(password2)
        
        # Different passwords should produce different hashes
        assert hash1 != hash2
        
        # Same password should verify correctly
        assert SecurityUtils.verify_password(password1, hash1)
        assert SecurityUtils.verify_password(password2, hash2)
        
        # Wrong password should not verify
        assert not SecurityUtils.verify_password(password1, hash2)
        assert not SecurityUtils.verify_password(password2, hash1)
    
    @given(valid_email())
    @settings(max_examples=50)
    async def test_email_validation_properties(self, email):
        """Test email validation properties"""
        # All emails generated by our strategy should be valid
        assert '@' in email
        assert email.count('@') == 1
        assert not email.startswith('@')
        assert not email.endswith('@')
        
        local, domain = email.split('@')
        assert len(local) > 0
        assert len(domain) > 0
        assert '.' in domain


@pytest.mark.property
@pytest.mark.asyncio
class TestOrganizationProperties:
    """Property-based tests for Organization model behavior"""
    
    @given(organization_data())
    @example({
        "name": "Test Org",
        "slug": "test-org", 
        "organization_type": "small_business",
        "description": "Test organization",
        "website_url": "https://test.com"
    })
    async def test_organization_creation_properties(self, test_session, data):
        """Test organization creation invariants"""
        org = Organization(
            name=data["name"],
            slug=data["slug"],
            organization_type=data["organization_type"],
            description=data["description"],
            website_url=data["website_url"]
        )
        
        test_session.add(org)
        await test_session.commit()
        await test_session.refresh(org)
        
        # Invariants
        assert org.id is not None
        assert org.name == data["name"]
        assert org.slug == data["slug"]
        assert org.organization_type == data["organization_type"]
        assert org.created_at is not None
        assert org.updated_at is not None
        assert org.created_at <= org.updated_at
    
    @given(valid_organization_slug())
    @settings(max_examples=30)
    async def test_slug_format_properties(self, slug):
        """Test that all generated slugs follow proper format"""
        # Slug format invariants
        assert not slug.startswith('-')
        assert not slug.endswith('-')
        assert '--' not in slug  # No consecutive dashes
        assert all(c.islower() or c.isdigit() or c == '-' for c in slug)
        assert len(slug) > 0


@pytest.mark.property
@pytest.mark.asyncio
class TestAPIProperties:
    """Property-based tests for API endpoints"""
    
    @given(user_data())
    @settings(max_examples=10)  # Limit for async/HTTP tests
    async def test_user_registration_properties(self, test_client: AsyncClient, data):
        """Test user registration endpoint properties"""
        response = await test_client.post("/api/v1/auth/register", json=data)
        
        if response.status_code == 201:
            # Successful registration properties
            response_data = response.json()
            assert "user" in response_data
            assert "access_token" in response_data
            assert response_data["user"]["email"] == data["email"]
            assert response_data["user"]["first_name"] == data["first_name"]
            assert response_data["user"]["last_name"] == data["last_name"]
            assert "id" in response_data["user"]
            assert "password" not in response_data["user"]  # Never expose password
        else:
            # Error response properties  
            assert response.status_code >= 400
            assert "detail" in response.json()
    
    @given(st.text(), st.text())
    @settings(max_examples=10)
    async def test_invalid_login_properties(self, test_client: AsyncClient, email, password):
        """Test login with invalid credentials"""
        assume(len(email) > 0 and len(password) > 0)
        assume('@' in email)  # Basic email format
        
        response = await test_client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        
        # Invalid credentials should always return 401 or 422
        assert response.status_code in [401, 422]
        if response.status_code == 401:
            assert "invalid" in response.json()["detail"].lower()


class UserManagementStateMachine(RuleBasedStateMachine):
    """Stateful property-based testing for user management"""
    
    def __init__(self):
        super().__init__()
        self.users = {}
        self.organizations = {}
    
    users = Bundle('users')
    organizations = Bundle('organizations')
    
    @rule(target=users, data=user_data())
    def create_user(self, data):
        """Create a user and verify it maintains invariants"""
        user_id = f"user_{len(self.users)}"
        
        # Simulate user creation
        user_info = {
            "id": user_id,
            "email": data["email"],
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "is_active": True,
            "is_verified": False,
            "created_at": datetime.utcnow()
        }
        
        self.users[user_id] = user_info
        return user_id
    
    @rule(target=organizations, data=organization_data())
    def create_organization(self, data):
        """Create an organization"""
        org_id = f"org_{len(self.organizations)}"
        
        org_info = {
            "id": org_id,
            "name": data["name"],
            "slug": data["slug"],
            "organization_type": data["organization_type"],
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        
        self.organizations[org_id] = org_info
        return org_id
    
    @rule(user_id=users)
    def activate_user(self, user_id):
        """Activate a user"""
        if user_id in self.users:
            self.users[user_id]["is_active"] = True
            self.users[user_id]["is_verified"] = True
    
    @rule(user_id=users)  
    def deactivate_user(self, user_id):
        """Deactivate a user"""
        if user_id in self.users:
            self.users[user_id]["is_active"] = False
    
    @invariant()
    def users_have_valid_emails(self):
        """All users should have valid email addresses"""
        for user in self.users.values():
            email = user["email"]
            assert '@' in email
            assert email.count('@') == 1
    
    @invariant()
    def organizations_have_unique_slugs(self):
        """All organizations should have unique slugs"""
        slugs = [org["slug"] for org in self.organizations.values()]
        assert len(slugs) == len(set(slugs)), "Organization slugs must be unique"
    
    @invariant()
    def active_users_are_verified(self):
        """Business rule: Active users should generally be verified"""
        # This is a soft invariant - we might have exceptions
        active_unverified = [
            user for user in self.users.values() 
            if user["is_active"] and not user["is_verified"]
        ]
        # Allow some active unverified users but not too many
        assert len(active_unverified) <= len(self.users) * 0.3


# Property-based test execution
@pytest.mark.property
@pytest.mark.slow
def test_user_management_state_machine():
    """Run the stateful property-based test"""
    UserManagementStateMachine.TestCase.settings = settings(
        max_examples=50,
        stateful_step_count=20
    )
    UserManagementStateMachine.TestCase().runTest()


@pytest.mark.property  
@pytest.mark.asyncio
class TestSecurityProperties:
    """Property-based security tests"""
    
    @given(st.text(min_size=1))
    @settings(max_examples=20)
    async def test_jwt_token_properties(self, payload):
        """Test JWT token generation and validation properties"""
        from app.services.auth_service import TokenService
        
        # Generate token
        token_data = {"sub": payload, "exp": datetime.utcnow() + timedelta(hours=1)}
        token = TokenService.create_access_token(token_data)
        
        # Token should be a string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Token should have JWT format (header.payload.signature)
        parts = token.split('.')
        assert len(parts) == 3
        
        # Should be able to decode the token
        decoded = TokenService.verify_token(token)
        assert decoded["sub"] == payload
    
    @given(st.integers(min_value=1, max_value=10))
    async def test_rate_limiting_properties(self, attempt_count):
        """Test rate limiting behavior properties"""
        from app.services.auth_service import RateLimiter
        
        limiter = RateLimiter()
        client_id = "test_client"
        
        # First few attempts should be allowed
        for i in range(min(attempt_count, 5)):
            assert limiter.is_allowed(client_id, "login")
        
        # After many attempts, should be rate limited
        for i in range(20):  # Exceed rate limit
            limiter.is_allowed(client_id, "login")
        
        # Should now be rate limited
        assert not limiter.is_allowed(client_id, "login")


# Configure Hypothesis settings for property tests
@pytest.mark.property
class HypothesisConfig:
    """Configuration for Hypothesis-based tests"""
    
    @staticmethod
    def configure_settings():
        """Configure Hypothesis settings for different test types"""
        # Fast tests for CI
        settings.register_profile("ci", max_examples=10, deadline=1000)
        
        # Thorough tests for development  
        settings.register_profile("dev", max_examples=100, deadline=5000)
        
        # Load profile based on environment
        import os
        profile = os.getenv("HYPOTHESIS_PROFILE", "ci")
        settings.load_profile(profile)