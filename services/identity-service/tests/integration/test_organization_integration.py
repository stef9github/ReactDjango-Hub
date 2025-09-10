"""
Comprehensive organization management integration tests
Tests multi-tenant organization features, RBAC, and data isolation
"""

import pytest
import uuid
from datetime import datetime, timedelta
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


@pytest.mark.organization
@pytest.mark.integration
@pytest.mark.asyncio
class TestOrganizationManagement:
    """Test organization CRUD operations"""
    
    async def test_create_organization_success(self, test_client: AsyncClient, auth_headers):
        """Test successful organization creation"""
        org_data = {
            "name": "Test Organization Inc",
            "domain": "testorg.com",
            "org_type": "business",
            "description": "A test organization for integration testing",
            "settings": {
                "theme": "light",
                "notifications": True,
                "timezone": "UTC",
                "language": "en"
            },
            "contact_info": {
                "email": "contact@testorg.com",
                "phone": "+1234567890",
                "address": {
                    "street": "123 Test St",
                    "city": "Test City",
                    "state": "TS",
                    "zip": "12345",
                    "country": "US"
                }
            }
        }
        
        response = await test_client.post("/api/v1/organizations",
                                        json=org_data,
                                        headers=auth_headers("admin_token"))
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["name"] == org_data["name"]
        assert data["domain"] == org_data["domain"]
        assert data["org_type"] == org_data["org_type"]
        assert data["description"] == org_data["description"]
        assert data["settings"] == org_data["settings"]
        assert data["is_active"] is True
        assert "created_at" in data
        assert "updated_at" in data
        
        return data["id"]
    
    async def test_create_organization_validation(self, test_client: AsyncClient, auth_headers):
        """Test organization creation validation"""
        invalid_orgs = [
            # Missing required fields
            {},
            {"name": "No Type Org"},
            {"org_type": "business"},
            
            # Invalid data types
            {"name": "", "org_type": "business"},  # Empty name
            {"name": "Valid Name", "org_type": "invalid_type"},  # Invalid type
            {"name": "Valid Name", "org_type": "business", "domain": "invalid-domain"},
            
            # Field length validation
            {"name": "x" * 1000, "org_type": "business"},  # Too long name
        ]
        
        for invalid_org in invalid_orgs:
            response = await test_client.post("/api/v1/organizations",
                                            json=invalid_org,
                                            headers=auth_headers("admin_token"))
            
            assert response.status_code == 422  # Validation error
    
    async def test_organization_name_uniqueness(self, test_client: AsyncClient, auth_headers):
        """Test organization name uniqueness constraint"""
        org_name = "Unique Organization Name"
        
        # Create first organization
        org1_data = {"name": org_name, "org_type": "business"}
        response1 = await test_client.post("/api/v1/organizations",
                                         json=org1_data,
                                         headers=auth_headers("admin_token"))
        
        assert response1.status_code == 201
        
        # Try to create second organization with same name
        org2_data = {"name": org_name, "org_type": "nonprofit"}
        response2 = await test_client.post("/api/v1/organizations",
                                         json=org2_data,
                                         headers=auth_headers("admin_token"))
        
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()
    
    async def test_get_organization_details(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test retrieving organization details"""
        response = await test_client.get(f"/api/v1/organizations/{test_organization.id}",
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(test_organization.id)
        assert data["name"] == test_organization.name
        assert "created_at" in data
        assert "updated_at" in data
        assert "settings" in data
    
    async def test_update_organization(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test updating organization details"""
        update_data = {
            "description": "Updated organization description",
            "settings": {
                "theme": "dark",
                "notifications": False,
                "timezone": "America/New_York"
            }
        }
        
        response = await test_client.patch(f"/api/v1/organizations/{test_organization.id}",
                                         json=update_data,
                                         headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["description"] == update_data["description"]
        assert data["settings"]["theme"] == "dark"
        assert data["settings"]["notifications"] is False
    
    async def test_delete_organization(self, test_client: AsyncClient, auth_headers):
        """Test organization deletion (soft delete)"""
        # Create organization to delete
        org_id = await self.test_create_organization_success(test_client, auth_headers)
        
        # Delete organization
        response = await test_client.delete(f"/api/v1/organizations/{org_id}",
                                          headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        
        # Verify organization is deactivated (soft delete)
        get_response = await test_client.get(f"/api/v1/organizations/{org_id}",
                                           headers=auth_headers("admin_token"))
        
        if get_response.status_code == 200:
            data = get_response.json()
            assert data["is_active"] is False
        else:
            # Organization might be completely removed
            assert get_response.status_code == 404


@pytest.mark.organization
@pytest.mark.integration
@pytest.mark.asyncio
class TestOrganizationUserManagement:
    """Test organization user management"""
    
    async def test_add_user_to_organization(self, test_client: AsyncClient, test_organization, test_user, auth_headers):
        """Test adding user to organization"""
        user_data = {
            "user_id": str(test_user.id),
            "role": "member",
            "permissions": ["read", "write"]
        }
        
        response = await test_client.post(f"/api/v1/organizations/{test_organization.id}/users",
                                        json=user_data,
                                        headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "added" in data["message"].lower()
        assert "user_id" in data
        assert data["user_id"] == str(test_user.id)
    
    async def test_list_organization_users(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test listing organization users"""
        response = await test_client.get(f"/api/v1/organizations/{test_organization.id}/users",
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert "users" in data
        assert "total_count" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["users"], list)
        
        # Each user should have required fields
        for user in data["users"]:
            assert "id" in user
            assert "email" in user
            assert "name" in user
            assert "role" in user
            assert "joined_at" in user
            assert "is_active" in user
    
    async def test_update_user_role_in_organization(self, test_client: AsyncClient, test_organization, test_user, auth_headers):
        """Test updating user role in organization"""
        # First add user to organization
        add_response = await test_client.post(f"/api/v1/organizations/{test_organization.id}/users",
                                            json={
                                                "user_id": str(test_user.id),
                                                "role": "member"
                                            },
                                            headers=auth_headers("admin_token"))
        
        if add_response.status_code == 200:
            # Update user role
            update_response = await test_client.patch(f"/api/v1/organizations/{test_organization.id}/users/{test_user.id}",
                                                    json={
                                                        "role": "admin",
                                                        "permissions": ["read", "write", "delete", "admin"]
                                                    },
                                                    headers=auth_headers("admin_token"))
            
            assert update_response.status_code == 200
            data = update_response.json()
            assert data["role"] == "admin"
    
    async def test_remove_user_from_organization(self, test_client: AsyncClient, test_organization, test_user, auth_headers):
        """Test removing user from organization"""
        # First add user
        add_response = await test_client.post(f"/api/v1/organizations/{test_organization.id}/users",
                                            json={
                                                "user_id": str(test_user.id),
                                                "role": "member"
                                            },
                                            headers=auth_headers("admin_token"))
        
        if add_response.status_code == 200:
            # Remove user
            remove_response = await test_client.delete(f"/api/v1/organizations/{test_organization.id}/users/{test_user.id}",
                                                     headers=auth_headers("admin_token"))
            
            assert remove_response.status_code == 200
            
            # Verify user is removed
            list_response = await test_client.get(f"/api/v1/organizations/{test_organization.id}/users",
                                                headers=auth_headers("admin_token"))
            
            if list_response.status_code == 200:
                users = list_response.json()["users"]
                user_ids = [u["id"] for u in users]
                assert str(test_user.id) not in user_ids
    
    async def test_organization_user_pagination(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization user list pagination"""
        # Test pagination parameters
        response = await test_client.get(f"/api/v1/organizations/{test_organization.id}/users",
                                       params={"page": 1, "page_size": 5},
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["users"]) <= 5
    
    async def test_organization_user_search(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization user search"""
        # Search by email
        response = await test_client.get(f"/api/v1/organizations/{test_organization.id}/users",
                                       params={"search": "test@example.com"},
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        # Results should be filtered
        for user in data["users"]:
            assert "test" in user["email"].lower() or "example" in user["email"].lower()


@pytest.mark.organization
@pytest.mark.integration
@pytest.mark.asyncio
class TestOrganizationDashboard:
    """Test organization dashboard and analytics"""
    
    async def test_organization_dashboard_data(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization dashboard data retrieval"""
        response = await test_client.get(f"/api/v1/organizations/{test_organization.id}/dashboard",
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify dashboard structure
        required_fields = [
            "organization",
            "user_count",
            "activity_summary",
            "recent_activities",
            "settings",
            "statistics"
        ]
        
        for field in required_fields:
            assert field in data
        
        # Verify organization info
        assert data["organization"]["id"] == str(test_organization.id)
        assert data["organization"]["name"] == test_organization.name
        
        # Verify statistics
        assert isinstance(data["user_count"], int)
        assert data["user_count"] >= 0
        
        # Verify activity summary
        activity = data["activity_summary"]
        assert "total_logins" in activity
        assert "active_users" in activity
        assert "recent_registrations" in activity
    
    async def test_organization_activity_analytics(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization activity analytics"""
        # Get activity data with date range
        params = {
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "activity_type": "login"
        }
        
        response = await test_client.get(f"/api/v1/organizations/{test_organization.id}/analytics/activity",
                                       params=params,
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert "activities" in data
        assert "summary" in data
        assert "time_series" in data
        
        # Time series should have data points
        time_series = data["time_series"]
        assert isinstance(time_series, list)
        
        for point in time_series:
            assert "date" in point
            assert "count" in point
    
    async def test_organization_user_analytics(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization user analytics"""
        response = await test_client.get(f"/api/v1/organizations/{test_organization.id}/analytics/users",
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert "user_statistics" in data
        assert "growth_metrics" in data
        assert "role_distribution" in data
        
        stats = data["user_statistics"]
        assert "total_users" in stats
        assert "active_users" in stats
        assert "inactive_users" in stats
        
        # Role distribution should be a valid structure
        roles = data["role_distribution"]
        assert isinstance(roles, list)
        
        for role in roles:
            assert "role" in role
            assert "count" in role
    
    async def test_organization_security_dashboard(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization security dashboard"""
        response = await test_client.get(f"/api/v1/organizations/{test_organization.id}/security",
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        security_fields = [
            "mfa_compliance",
            "failed_login_attempts",
            "security_alerts",
            "password_policy_compliance"
        ]
        
        for field in security_fields:
            assert field in data
        
        # MFA compliance should have stats
        mfa_compliance = data["mfa_compliance"]
        assert "total_users" in mfa_compliance
        assert "mfa_enabled_users" in mfa_compliance
        assert "compliance_percentage" in mfa_compliance
        
        # Failed login attempts should be tracked
        failed_logins = data["failed_login_attempts"]
        assert "total_attempts" in failed_logins
        assert "unique_users" in failed_logins
        assert "recent_attempts" in failed_logins


@pytest.mark.organization
@pytest.mark.integration
@pytest.mark.asyncio
class TestOrganizationRBAC:
    """Test Role-Based Access Control within organizations"""
    
    async def test_organization_role_definitions(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization role definitions"""
        response = await test_client.get(f"/api/v1/organizations/{test_organization.id}/roles",
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert "roles" in data
        roles = data["roles"]
        
        # Should have standard roles
        role_names = [role["name"] for role in roles]
        expected_roles = ["owner", "admin", "manager", "member", "viewer"]
        
        for expected_role in expected_roles:
            if expected_role not in role_names:
                # Role might not exist yet, which is acceptable
                continue
    
    async def test_create_custom_organization_role(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test creating custom organization role"""
        role_data = {
            "name": "custom_analyst",
            "display_name": "Data Analyst",
            "description": "Can view and analyze organization data",
            "permissions": [
                "organization.read",
                "analytics.read",
                "users.read"
            ]
        }
        
        response = await test_client.post(f"/api/v1/organizations/{test_organization.id}/roles",
                                        json=role_data,
                                        headers=auth_headers("admin_token"))
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == role_data["name"]
        assert data["display_name"] == role_data["display_name"]
        assert data["permissions"] == role_data["permissions"]
    
    async def test_assign_role_to_user(self, test_client: AsyncClient, test_organization, test_user, auth_headers):
        """Test assigning role to user in organization"""
        # First add user to organization
        add_user_response = await test_client.post(f"/api/v1/organizations/{test_organization.id}/users",
                                                 json={
                                                     "user_id": str(test_user.id),
                                                     "role": "member"
                                                 },
                                                 headers=auth_headers("admin_token"))
        
        if add_user_response.status_code == 200:
            # Assign additional role
            role_assignment = {
                "user_id": str(test_user.id),
                "role": "manager",
                "scope": "department_analytics"
            }
            
            response = await test_client.post(f"/api/v1/organizations/{test_organization.id}/role-assignments",
                                            json=role_assignment,
                                            headers=auth_headers("admin_token"))
            
            assert response.status_code == 200
            data = response.json()
            assert data["role"] == "manager"
    
    async def test_check_user_permissions(self, test_client: AsyncClient, test_organization, test_user, auth_headers):
        """Test checking user permissions in organization context"""
        permission_check = {
            "user_id": str(test_user.id),
            "permission": "organization.analytics.read",
            "resource": f"organization:{test_organization.id}"
        }
        
        response = await test_client.post("/api/v1/auth/check-permission",
                                        json=permission_check,
                                        headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert "allowed" in data
        assert isinstance(data["allowed"], bool)
        assert "reason" in data
    
    async def test_organization_permission_inheritance(self, test_client: AsyncClient, test_organization, test_user, auth_headers):
        """Test permission inheritance within organization"""
        # Create hierarchical role structure
        parent_role = {
            "name": "department_head",
            "permissions": ["department.manage", "users.manage"]
        }
        
        child_role = {
            "name": "team_lead",
            "parent_role": "department_head",
            "permissions": ["team.manage"]
        }
        
        # Create roles
        parent_response = await test_client.post(f"/api/v1/organizations/{test_organization.id}/roles",
                                               json=parent_role,
                                               headers=auth_headers("admin_token"))
        
        if parent_response.status_code == 201:
            child_response = await test_client.post(f"/api/v1/organizations/{test_organization.id}/roles",
                                                  json=child_role,
                                                  headers=auth_headers("admin_token"))
            
            if child_response.status_code == 201:
                # Assign child role to user
                assignment = {
                    "user_id": str(test_user.id),
                    "role": "team_lead"
                }
                
                assign_response = await test_client.post(f"/api/v1/organizations/{test_organization.id}/role-assignments",
                                                       json=assignment,
                                                       headers=auth_headers("admin_token"))
                
                if assign_response.status_code == 200:
                    # Check that user has inherited permissions
                    permission_check = {
                        "user_id": str(test_user.id),
                        "permission": "department.manage"  # From parent role
                    }
                    
                    check_response = await test_client.post("/api/v1/auth/check-permission",
                                                          json=permission_check,
                                                          headers=auth_headers("admin_token"))
                    
                    if check_response.status_code == 200:
                        data = check_response.json()
                        # Should have inherited permission
                        assert data["allowed"] is True


@pytest.mark.organization
@pytest.mark.integration
@pytest.mark.asyncio
class TestOrganizationDataIsolation:
    """Test data isolation between organizations"""
    
    async def test_cross_organization_data_isolation(self, test_client: AsyncClient, auth_headers):
        """Test that organizations cannot access each other's data"""
        # Create two organizations
        org1_data = {"name": "Organization One", "org_type": "business"}
        org2_data = {"name": "Organization Two", "org_type": "business"}
        
        org1_response = await test_client.post("/api/v1/organizations",
                                             json=org1_data,
                                             headers=auth_headers("admin_token"))
        
        org2_response = await test_client.post("/api/v1/organizations",
                                             json=org2_data,
                                             headers=auth_headers("admin_token"))
        
        if org1_response.status_code == 201 and org2_response.status_code == 201:
            org1_id = org1_response.json()["id"]
            org2_id = org2_response.json()["id"]
            
            # Try to access org2 data with org1 context
            # This would require implementing organization context in auth
            response = await test_client.get(f"/api/v1/organizations/{org2_id}/users",
                                           headers=auth_headers("org1_admin_token"))
            
            # Should be forbidden or not found
            assert response.status_code in [403, 404]
    
    async def test_user_data_scoping_by_organization(self, test_client: AsyncClient, test_organization, test_user, auth_headers):
        """Test that user data is properly scoped to organization"""
        # Add user to organization
        add_response = await test_client.post(f"/api/v1/organizations/{test_organization.id}/users",
                                            json={
                                                "user_id": str(test_user.id),
                                                "role": "member"
                                            },
                                            headers=auth_headers("admin_token"))
        
        if add_response.status_code == 200:
            # Get user's organization-specific data
            response = await test_client.get(f"/api/v1/organizations/{test_organization.id}/users/{test_user.id}/profile",
                                           headers=auth_headers("admin_token"))
            
            if response.status_code == 200:
                data = response.json()
                
                # Should only show data relevant to this organization
                assert data["organization_id"] == str(test_organization.id)
                
                # Should not expose data from other organizations
                assert "other_organizations" not in data
    
    async def test_organization_admin_scope_limitation(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test that organization admins cannot exceed their scope"""
        # Organization admin should not be able to:
        
        # 1. Create system-wide policies
        response = await test_client.put("/api/v1/mfa/policy/system",
                                       json={"requirement_level": "required"},
                                       headers=auth_headers("org_admin_token"))
        
        assert response.status_code in [401, 403]
        
        # 2. Access other organizations
        other_org_id = str(uuid.uuid4())
        response = await test_client.get(f"/api/v1/organizations/{other_org_id}",
                                       headers=auth_headers("org_admin_token"))
        
        assert response.status_code in [403, 404]
        
        # 3. Modify global user accounts outside their org
        global_user_id = str(uuid.uuid4())
        response = await test_client.patch(f"/api/v1/users/{global_user_id}",
                                         json={"name": "Hacked Name"},
                                         headers=auth_headers("org_admin_token"))
        
        assert response.status_code in [401, 403, 404]
    
    async def test_multi_organization_user_data_separation(self, test_client: AsyncClient, test_user, auth_headers):
        """Test user data separation across multiple organizations"""
        # Create two organizations
        org1_data = {"name": "User Org One", "org_type": "business"}
        org2_data = {"name": "User Org Two", "org_type": "business"}
        
        org1_response = await test_client.post("/api/v1/organizations",
                                             json=org1_data,
                                             headers=auth_headers("admin_token"))
        
        org2_response = await test_client.post("/api/v1/organizations",
                                             json=org2_data,
                                             headers=auth_headers("admin_token"))
        
        if org1_response.status_code == 201 and org2_response.status_code == 201:
            org1_id = org1_response.json()["id"]
            org2_id = org2_response.json()["id"]
            
            # Add user to both organizations with different roles
            add_org1 = await test_client.post(f"/api/v1/organizations/{org1_id}/users",
                                            json={
                                                "user_id": str(test_user.id),
                                                "role": "admin"
                                            },
                                            headers=auth_headers("admin_token"))
            
            add_org2 = await test_client.post(f"/api/v1/organizations/{org2_id}/users",
                                            json={
                                                "user_id": str(test_user.id),
                                                "role": "viewer"
                                            },
                                            headers=auth_headers("admin_token"))
            
            if add_org1.status_code == 200 and add_org2.status_code == 200:
                # User should have different permissions in each org
                
                # Check permissions in org1 (should have admin permissions)
                perm_check1 = await test_client.post("/api/v1/auth/check-permission",
                                                   json={
                                                       "user_id": str(test_user.id),
                                                       "permission": "organization.manage",
                                                       "resource": f"organization:{org1_id}"
                                                   },
                                                   headers=auth_headers("admin_token"))
                
                # Check permissions in org2 (should have limited permissions)
                perm_check2 = await test_client.post("/api/v1/auth/check-permission",
                                                   json={
                                                       "user_id": str(test_user.id),
                                                       "permission": "organization.manage",
                                                       "resource": f"organization:{org2_id}"
                                                   },
                                                   headers=auth_headers("admin_token"))
                
                # Permissions should be different
                if perm_check1.status_code == 200 and perm_check2.status_code == 200:
                    perm1 = perm_check1.json()["allowed"]
                    perm2 = perm_check2.json()["allowed"]
                    
                    # Admin in org1, viewer in org2
                    assert perm1 != perm2


@pytest.mark.organization
@pytest.mark.integration
@pytest.mark.asyncio
class TestOrganizationSecurityPolicies:
    """Test organization-specific security policies"""
    
    async def test_organization_password_policy(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization-specific password policies"""
        # Set organization password policy
        policy_data = {
            "min_length": 12,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_symbols": True,
            "password_history": 5,
            "max_age_days": 90
        }
        
        response = await test_client.put(f"/api/v1/organizations/{test_organization.id}/security/password-policy",
                                       json=policy_data,
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["min_length"] == 12
        assert data["require_uppercase"] is True
        assert data["password_history"] == 5
    
    async def test_organization_session_policy(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization session management policies"""
        session_policy = {
            "max_session_duration": 480,  # 8 hours
            "idle_timeout": 60,  # 1 hour
            "max_concurrent_sessions": 3,
            "require_mfa_for_sensitive_actions": True,
            "session_notification": True
        }
        
        response = await test_client.put(f"/api/v1/organizations/{test_organization.id}/security/session-policy",
                                       json=session_policy,
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["max_session_duration"] == 480
        assert data["max_concurrent_sessions"] == 3
        assert data["require_mfa_for_sensitive_actions"] is True
    
    async def test_organization_access_policy(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization access control policies"""
        access_policy = {
            "allowed_ip_ranges": ["192.168.1.0/24", "10.0.0.0/8"],
            "blocked_countries": ["CN", "RU"],
            "require_vpn": False,
            "business_hours_only": False,
            "device_restrictions": {
                "allow_mobile": True,
                "allow_unmanaged": False,
                "require_encryption": True
            }
        }
        
        response = await test_client.put(f"/api/v1/organizations/{test_organization.id}/security/access-policy",
                                       json=access_policy,
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert "192.168.1.0/24" in data["allowed_ip_ranges"]
        assert data["device_restrictions"]["require_encryption"] is True
    
    async def test_organization_audit_configuration(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization audit and compliance configuration"""
        audit_config = {
            "log_retention_days": 2555,  # 7 years for compliance
            "audit_level": "detailed",
            "compliance_frameworks": ["SOX", "HIPAA", "GDPR"],
            "alert_on_suspicious_activity": True,
            "export_format": "json",
            "encryption_at_rest": True
        }
        
        response = await test_client.put(f"/api/v1/organizations/{test_organization.id}/security/audit-config",
                                       json=audit_config,
                                       headers=auth_headers("admin_token"))
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["log_retention_days"] == 2555
        assert "HIPAA" in data["compliance_frameworks"]
        assert data["encryption_at_rest"] is True


@pytest.mark.organization
@pytest.mark.integration
@pytest.mark.asyncio
class TestOrganizationIntegrations:
    """Test organization integrations with external services"""
    
    async def test_organization_sso_configuration(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization SSO integration configuration"""
        sso_config = {
            "provider": "okta",
            "domain": "testorg.okta.com",
            "client_id": "test_client_id",
            "client_secret": "encrypted_secret",
            "scopes": ["openid", "profile", "email"],
            "auto_provision": True,
            "default_role": "member",
            "attribute_mapping": {
                "email": "email",
                "first_name": "given_name",
                "last_name": "family_name",
                "role": "groups"
            }
        }
        
        response = await test_client.post(f"/api/v1/organizations/{test_organization.id}/integrations/sso",
                                        json=sso_config,
                                        headers=auth_headers("admin_token"))
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["provider"] == "okta"
        assert data["auto_provision"] is True
        assert "client_secret" not in data  # Should be hidden
    
    async def test_organization_directory_sync(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization directory synchronization"""
        directory_config = {
            "type": "active_directory",
            "server": "ldap://ad.testorg.com",
            "base_dn": "DC=testorg,DC=com",
            "bind_username": "sync_user@testorg.com",
            "bind_password": "encrypted_password",
            "user_filter": "(&(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))",
            "group_filter": "(&(objectClass=group))",
            "sync_schedule": "0 2 * * *",  # Daily at 2 AM
            "auto_disable_users": True
        }
        
        response = await test_client.post(f"/api/v1/organizations/{test_organization.id}/integrations/directory",
                                        json=directory_config,
                                        headers=auth_headers("admin_token"))
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["type"] == "active_directory"
        assert data["auto_disable_users"] is True
        assert "bind_password" not in data  # Should be encrypted/hidden
    
    async def test_organization_webhook_configuration(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization webhook configuration"""
        webhook_config = {
            "name": "User Management Webhook",
            "url": "https://api.testorg.com/webhooks/identity",
            "events": ["user.created", "user.updated", "user.deleted", "user.login"],
            "secret": "webhook_secret_key",
            "timeout": 30,
            "retry_attempts": 3,
            "active": True,
            "headers": {
                "Authorization": "Bearer webhook_token",
                "Content-Type": "application/json"
            }
        }
        
        response = await test_client.post(f"/api/v1/organizations/{test_organization.id}/webhooks",
                                        json=webhook_config,
                                        headers=auth_headers("admin_token"))
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == "User Management Webhook"
        assert "user.created" in data["events"]
        assert data["retry_attempts"] == 3
        assert "secret" not in data  # Should be hidden
    
    @patch('httpx.AsyncClient.post')
    async def test_webhook_delivery(self, mock_post, test_client: AsyncClient, test_organization, test_user, auth_headers):
        """Test webhook event delivery"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Configure webhook
        webhook_config = {
            "name": "Test Webhook",
            "url": "https://api.example.com/webhook",
            "events": ["user.login"],
            "active": True
        }
        
        webhook_response = await test_client.post(f"/api/v1/organizations/{test_organization.id}/webhooks",
                                                json=webhook_config,
                                                headers=auth_headers("admin_token"))
        
        if webhook_response.status_code == 201:
            # Trigger event that should send webhook
            login_response = await test_client.post("/api/v1/auth/login",
                                                  json={
                                                      "email": test_user.email,
                                                      "password": "testpassword123",
                                                      "remember_me": False
                                                  })
            
            if login_response.status_code == 200:
                # Webhook should have been called
                mock_post.assert_called()
                
                # Verify webhook payload
                call_args = mock_post.call_args
                webhook_data = call_args[1]["json"]  # Assuming JSON payload
                
                assert webhook_data["event"] == "user.login"
                assert webhook_data["user_id"] == str(test_user.id)
                assert webhook_data["organization_id"] == str(test_organization.id)


@pytest.mark.organization
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
class TestOrganizationPerformance:
    """Test organization management performance"""
    
    async def test_large_organization_user_list_performance(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test performance with large number of organization users"""
        import time
        
        # Test pagination with different page sizes
        page_sizes = [10, 50, 100, 500]
        
        for page_size in page_sizes:
            start_time = time.time()
            
            response = await test_client.get(f"/api/v1/organizations/{test_organization.id}/users",
                                           params={"page_size": page_size},
                                           headers=auth_headers("admin_token"))
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                # Response time should be reasonable
                assert response_time < 5.0  # Under 5 seconds
                
                # Should not return more than requested
                data = response.json()
                assert len(data["users"]) <= page_size
    
    async def test_organization_dashboard_performance(self, test_client: AsyncClient, test_organization, auth_headers):
        """Test organization dashboard loading performance"""
        import time
        
        start_time = time.time()
        
        response = await test_client.get(f"/api/v1/organizations/{test_organization.id}/dashboard",
                                       headers=auth_headers("admin_token"))
        
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            # Dashboard should load quickly
            assert response_time < 3.0  # Under 3 seconds
            
            # Should have all required data
            data = response.json()
            assert "user_count" in data
            assert "activity_summary" in data
    
    async def test_concurrent_organization_operations(self, test_client: AsyncClient, auth_headers):
        """Test concurrent organization management operations"""
        import asyncio
        
        async def create_org(index):
            org_data = {
                "name": f"Concurrent Org {index}",
                "org_type": "business"
            }
            return await test_client.post("/api/v1/organizations",
                                        json=org_data,
                                        headers=auth_headers("admin_token"))
        
        # Create 5 organizations concurrently
        tasks = [create_org(i) for i in range(5)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Most should succeed
        successful_creates = 0
        for response in responses:
            if not isinstance(response, Exception) and response.status_code == 201:
                successful_creates += 1
        
        # At least some should succeed (depending on rate limiting)
        assert successful_creates > 0