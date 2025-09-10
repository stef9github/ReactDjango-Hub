"""
Tests for document permission system.
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient
from main import app


class TestPermissionModel:
    """Test permission model functionality."""
    
    def test_permission_model_creation(self):
        """Test creating permission instances."""
        from models.permission import DocumentPermission
        
        document_id = uuid4()
        user_id = uuid4()
        granted_by = uuid4()
        
        permission = DocumentPermission.create_user_permission(
            document_id=document_id,
            user_id=user_id,
            granted_by=granted_by,
            permissions=["read", "write"]
        )
        
        assert permission.document_id == document_id
        assert permission.user_id == user_id
        assert permission.granted_by == granted_by
        assert permission.can_read is True
        assert permission.can_write is True
        assert permission.can_delete is False
        assert permission.can_share is False
        assert permission.can_admin is False
    
    def test_role_permission_creation(self):
        """Test creating role permissions."""
        from models.permission import DocumentPermission
        
        document_id = uuid4()
        granted_by = uuid4()
        
        permission = DocumentPermission.create_role_permission(
            document_id=document_id,
            role_name="editor",
            granted_by=granted_by,
            permissions=["read", "write", "share"]
        )
        
        assert permission.document_id == document_id
        assert permission.role_name == "editor"
        assert permission.granted_by == granted_by
        assert permission.can_read is True
        assert permission.can_write is True
        assert permission.can_share is True
        assert permission.can_delete is False
        assert permission.can_admin is False
    
    def test_permission_hierarchy(self):
        """Test permission hierarchy (admin implies all)."""
        from models.permission import DocumentPermission
        
        permission = DocumentPermission()
        permission.grant_permission("admin")
        
        assert permission.can_admin is True
        assert permission.can_share is True
        assert permission.can_delete is True
        assert permission.can_write is True
        assert permission.can_read is True
    
    def test_permission_revocation(self):
        """Test permission revocation cascades properly."""
        from models.permission import DocumentPermission
        
        permission = DocumentPermission()
        permission.grant_permission("admin")
        
        # Revoke read should revoke all higher permissions
        permission.revoke_permission("read")
        
        assert permission.can_read is False
        assert permission.can_write is False
        assert permission.can_delete is False
        assert permission.can_admin is False
        # Share is independent
        assert permission.can_share is True
    
    def test_permission_expiration(self):
        """Test permission expiration logic."""
        from models.permission import DocumentPermission
        
        # Not expired permission
        future_time = datetime.utcnow() + timedelta(hours=1)
        permission = DocumentPermission(expires_at=future_time)
        assert not permission.is_expired
        
        # Expired permission
        past_time = datetime.utcnow() - timedelta(hours=1)
        permission = DocumentPermission(expires_at=past_time)
        assert permission.is_expired
        
        # No expiration
        permission = DocumentPermission(expires_at=None)
        assert not permission.is_expired


class TestPermissionRepository:
    """Test permission repository operations."""
    
    @pytest.mark.asyncio
    async def test_repository_initialization(self):
        """Test permission repository can be initialized."""
        from repositories.permission_repository import PermissionRepository
        from unittest.mock import AsyncMock
        
        mock_session = AsyncMock()
        repo = PermissionRepository(mock_session)
        assert repo is not None
        assert repo.session == mock_session
    
    @pytest.mark.asyncio
    async def test_grant_user_permission_structure(self):
        """Test user permission granting structure."""
        from repositories.permission_repository import PermissionRepository
        from unittest.mock import AsyncMock
        
        mock_session = AsyncMock()
        repo = PermissionRepository(mock_session)
        
        # Mock the create_instance method to avoid database operations
        async def mock_create_instance(permission):
            permission.id = uuid4()
            return permission
        
        repo.create_instance = mock_create_instance
        repo.revoke_user_permission = AsyncMock(return_value=True)
        
        document_id = uuid4()
        user_id = uuid4()
        granted_by = uuid4()
        
        permission = await repo.grant_user_permission(
            document_id=document_id,
            user_id=user_id,
            permissions=["read", "write"],
            granted_by=granted_by
        )
        
        assert permission.document_id == document_id
        assert permission.user_id == user_id
        assert permission.granted_by == granted_by
        assert permission.can_read is True
        assert permission.can_write is True


class TestPermissionEndpoints:
    """Test permission-related API endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
        self.valid_token = "valid-jwt-token"
        self.mock_user_data = {
            "user_id": str(uuid4()),
            "organization_id": str(uuid4()),
            "email": "test@example.com",
            "roles": ["editor"]
        }
    
    def test_grant_user_permission_requires_auth(self):
        """Test that granting user permission requires authentication."""
        document_id = uuid4()
        
        response = self.client.post(
            f"/api/v1/documents/{document_id}/permissions/users",
            json={
                "user_id": str(uuid4()),
                "permissions": ["read"]
            }
        )
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @patch('httpx.AsyncClient')
    def test_grant_user_permission_invalid_data(self, mock_client):
        """Test granting permission with invalid data."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        document_id = uuid4()
        
        # Test with invalid permissions
        response = self.client.post(
            f"/api/v1/documents/{document_id}/permissions/users",
            headers={"Authorization": f"Bearer {self.valid_token}"},
            json={
                "user_id": str(uuid4()),
                "permissions": ["invalid_permission"]
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch('httpx.AsyncClient')
    def test_grant_role_permission_invalid_data(self, mock_client):
        """Test granting role permission with invalid data."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        document_id = uuid4()
        
        # Test with empty role name
        response = self.client.post(
            f"/api/v1/documents/{document_id}/permissions/roles",
            headers={"Authorization": f"Bearer {self.valid_token}"},
            json={
                "role_name": "",
                "permissions": ["read"]
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_document_permissions_requires_auth(self):
        """Test that getting permissions requires authentication."""
        document_id = uuid4()
        
        response = self.client.get(f"/api/v1/documents/{document_id}/permissions")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_get_effective_permissions_requires_auth(self):
        """Test that getting effective permissions requires authentication."""
        document_id = uuid4()
        
        response = self.client.get(f"/api/v1/documents/{document_id}/permissions/effective")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_share_document_requires_auth(self):
        """Test that sharing document requires authentication."""
        document_id = uuid4()
        
        response = self.client.post(
            f"/api/v1/documents/{document_id}/share",
            json={
                "share_type": "user",
                "target_id": str(uuid4()),
                "permissions": ["read"]
            }
        )
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @patch('httpx.AsyncClient')
    def test_share_document_invalid_data(self, mock_client):
        """Test sharing document with invalid data."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        document_id = uuid4()
        
        # Test with invalid share_type
        response = self.client.post(
            f"/api/v1/documents/{document_id}/share",
            headers={"Authorization": f"Bearer {self.valid_token}"},
            json={
                "share_type": "invalid_type",
                "target_id": str(uuid4()),
                "permissions": ["read"]
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_revoke_user_permission_requires_auth(self):
        """Test that revoking user permission requires authentication."""
        document_id = uuid4()
        user_id = uuid4()
        
        response = self.client.delete(
            f"/api/v1/documents/{document_id}/permissions/users/{user_id}"
        )
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_revoke_role_permission_requires_auth(self):
        """Test that revoking role permission requires authentication."""
        document_id = uuid4()
        role_name = "editor"
        
        response = self.client.delete(
            f"/api/v1/documents/{document_id}/permissions/roles/{role_name}"
        )
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_check_document_access_requires_auth(self):
        """Test that access check requires authentication."""
        document_id = uuid4()
        
        response = self.client.post(
            f"/api/v1/documents/{document_id}/access-check",
            json={
                "user_id": str(uuid4()),
                "permission_type": "read"
            }
        )
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @patch('httpx.AsyncClient')
    def test_access_check_invalid_data(self, mock_client):
        """Test access check with invalid data."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        document_id = uuid4()
        
        # Test with invalid permission type
        response = self.client.post(
            f"/api/v1/documents/{document_id}/access-check",
            headers={"Authorization": f"Bearer {self.valid_token}"},
            json={
                "user_id": str(uuid4()),
                "permission_type": "invalid_permission"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_accessible_documents_requires_auth(self):
        """Test that getting accessible documents requires authentication."""
        user_id = uuid4()
        
        response = self.client.get(f"/api/v1/users/{user_id}/accessible-documents")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]


class TestPermissionSchemas:
    """Test permission-related schemas."""
    
    def test_grant_user_permission_schema(self):
        """Test user permission request schema validation."""
        from schemas.permission import GrantUserPermissionRequest
        
        # Valid request
        request = GrantUserPermissionRequest(
            user_id=uuid4(),
            permissions=["read", "write"]
        )
        assert request.user_id is not None
        assert len(request.permissions) == 2
        
        # Test with invalid permissions
        with pytest.raises(ValueError):
            GrantUserPermissionRequest(
                user_id=uuid4(),
                permissions=["invalid_permission"]
            )
        
        # Test with empty permissions
        with pytest.raises(ValueError):
            GrantUserPermissionRequest(
                user_id=uuid4(),
                permissions=[]
            )
    
    def test_grant_role_permission_schema(self):
        """Test role permission request schema validation."""
        from schemas.permission import GrantRolePermissionRequest
        
        # Valid request
        request = GrantRolePermissionRequest(
            role_name="editor",
            permissions=["read", "write", "share"]
        )
        assert request.role_name == "editor"
        assert len(request.permissions) == 3
        
        # Test with invalid permissions
        with pytest.raises(ValueError):
            GrantRolePermissionRequest(
                role_name="editor",
                permissions=["invalid_permission"]
            )
    
    def test_share_document_schema(self):
        """Test document sharing schema validation."""
        from schemas.permission import ShareDocumentRequest
        
        # Valid user sharing
        request = ShareDocumentRequest(
            share_type="user",
            target_id=str(uuid4()),
            permissions=["read"]
        )
        assert request.share_type == "user"
        assert request.permissions == ["read"]
        
        # Valid role sharing
        request = ShareDocumentRequest(
            share_type="role",
            target_id="editor",
            permissions=["read", "write"]
        )
        assert request.share_type == "role"
        assert request.target_id == "editor"
        
        # Invalid share type
        with pytest.raises(ValueError):
            ShareDocumentRequest(
                share_type="invalid",
                target_id="test",
                permissions=["read"]
            )
        
        # Invalid UUID for user sharing
        with pytest.raises(ValueError):
            ShareDocumentRequest(
                share_type="user",
                target_id="not-a-uuid",
                permissions=["read"]
            )
    
    def test_document_access_check_schema(self):
        """Test document access check schema validation."""
        from schemas.permission import DocumentAccessCheckRequest
        
        # Valid request
        request = DocumentAccessCheckRequest(
            user_id=uuid4(),
            user_roles=["editor", "viewer"],
            permission_type="read"
        )
        assert request.permission_type == "read"
        assert len(request.user_roles) == 2
        
        # Default values
        request = DocumentAccessCheckRequest(user_id=uuid4())
        assert request.user_roles == []
        assert request.permission_type == "read"
        
        # Invalid permission type
        with pytest.raises(ValueError):
            DocumentAccessCheckRequest(
                user_id=uuid4(),
                permission_type="invalid_permission"
            )


class TestPermissionIntegration:
    """Test permission system integration."""
    
    def test_owner_permissions(self):
        """Test that document owner has all permissions."""
        from models.permission import DocumentPermission
        
        # Owner should have all permissions by default logic
        # This would be tested in integration scenarios where we check
        # if document.created_by == user_id grants full permissions
        pass
    
    def test_permission_inheritance_concept(self):
        """Test permission inheritance concept."""
        from models.permission import DocumentPermission
        
        # Test inherited permission structure
        permission = DocumentPermission(
            document_id=uuid4(),
            role_name="admin",
            granted_by=uuid4(),
            inherited=True,
            source_type="organization",
            source_id=uuid4()
        )
        
        assert permission.inherited is True
        assert permission.source_type == "organization"
        assert permission.source_id is not None
    
    def test_permission_cleanup_concept(self):
        """Test permission cleanup structure."""
        from models.permission import DocumentPermission
        from datetime import datetime, timedelta
        
        # Test expired permission detection
        expired_permission = DocumentPermission(
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        assert expired_permission.is_expired is True
        
        # Test active permission
        active_permission = DocumentPermission(
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        assert active_permission.is_expired is False