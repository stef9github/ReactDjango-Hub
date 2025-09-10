"""
Permission-related schemas for request/response validation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class PermissionFlags(BaseModel):
    """Permission flags schema."""
    read: bool = False
    write: bool = False
    delete: bool = False
    share: bool = False
    admin: bool = False


class GrantUserPermissionRequest(BaseModel):
    """Request schema for granting user permissions."""
    user_id: UUID = Field(..., description="ID of the user to grant permissions to")
    permissions: List[str] = Field(..., description="List of permissions to grant (read, write, delete, share, admin)")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration time for permissions")
    
    @validator('permissions')
    def validate_permissions(cls, v):
        valid_permissions = {'read', 'write', 'delete', 'share', 'admin'}
        invalid_perms = set(v) - valid_permissions
        if invalid_perms:
            raise ValueError(f"Invalid permissions: {invalid_perms}. Valid options: {valid_permissions}")
        if not v:
            raise ValueError("At least one permission must be specified")
        return v


class GrantRolePermissionRequest(BaseModel):
    """Request schema for granting role permissions."""
    role_name: str = Field(..., description="Name of the role to grant permissions to", min_length=1, max_length=50)
    permissions: List[str] = Field(..., description="List of permissions to grant (read, write, delete, share, admin)")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration time for permissions")
    
    @validator('permissions')
    def validate_permissions(cls, v):
        valid_permissions = {'read', 'write', 'delete', 'share', 'admin'}
        invalid_perms = set(v) - valid_permissions
        if invalid_perms:
            raise ValueError(f"Invalid permissions: {invalid_perms}. Valid options: {valid_permissions}")
        if not v:
            raise ValueError("At least one permission must be specified")
        return v


class UserPermissionResponse(BaseModel):
    """Response schema for user permissions."""
    id: UUID
    user_id: UUID
    permissions: PermissionFlags
    granted_by: UUID
    granted_at: datetime
    expires_at: Optional[datetime]
    is_expired: bool
    inherited: bool = False
    source_type: Optional[str] = None


class RolePermissionResponse(BaseModel):
    """Response schema for role permissions."""
    id: UUID
    role_name: str
    permissions: PermissionFlags
    granted_by: UUID
    granted_at: datetime
    expires_at: Optional[datetime]
    is_expired: bool
    inherited: bool = False
    source_type: Optional[str] = None


class DocumentPermissionSummary(BaseModel):
    """Complete permission summary for a document."""
    document_id: UUID
    total_permissions: int
    user_permissions: List[UserPermissionResponse]
    role_permissions: List[RolePermissionResponse]


class EffectivePermissionsResponse(BaseModel):
    """User's effective permissions for a document."""
    user_id: UUID
    document_id: UUID
    permissions: PermissionFlags
    sources: List[str] = Field(..., description="Sources of permissions (direct, role:admin, role:editor, etc.)")


class ShareDocumentRequest(BaseModel):
    """Request schema for sharing a document."""
    share_type: str = Field(..., description="Type of sharing: 'user' or 'role'")
    target_id: str = Field(..., description="User ID (UUID) or role name depending on share_type")
    permissions: List[str] = Field(default=['read'], description="Permissions to grant")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration time")
    message: Optional[str] = Field(None, description="Optional message for the recipient", max_length=500)
    
    @validator('share_type')
    def validate_share_type(cls, v):
        if v not in ['user', 'role']:
            raise ValueError("share_type must be 'user' or 'role'")
        return v
    
    @validator('permissions')
    def validate_permissions(cls, v):
        valid_permissions = {'read', 'write', 'delete', 'share', 'admin'}
        invalid_perms = set(v) - valid_permissions
        if invalid_perms:
            raise ValueError(f"Invalid permissions: {invalid_perms}. Valid options: {valid_permissions}")
        if not v:
            v = ['read']  # Default to read permission
        return v
    
    @validator('target_id')
    def validate_target_id(cls, v, values):
        share_type = values.get('share_type')
        if share_type == 'user':
            # Validate UUID format
            try:
                UUID(v)
            except ValueError:
                raise ValueError("target_id must be a valid UUID for user sharing")
        elif share_type == 'role':
            # Validate role name format
            if not v or len(v.strip()) < 1 or len(v) > 50:
                raise ValueError("target_id must be a valid role name (1-50 characters)")
        return v


class ShareDocumentResponse(BaseModel):
    """Response schema for sharing a document."""
    success: bool
    message: str
    permission_id: UUID
    shared_with: str
    permissions_granted: List[str]
    expires_at: Optional[datetime]


class RevokePermissionRequest(BaseModel):
    """Request schema for revoking permissions."""
    target_type: str = Field(..., description="Type of target: 'user' or 'role'")
    target_id: str = Field(..., description="User ID or role name")
    
    @validator('target_type')
    def validate_target_type(cls, v):
        if v not in ['user', 'role']:
            raise ValueError("target_type must be 'user' or 'role'")
        return v


class UserAccessibleDocumentsResponse(BaseModel):
    """Response schema for documents accessible to a user."""
    total_count: int
    documents: List[Dict[str, Any]]  # Will contain simplified document info
    page: int
    limit: int
    has_more: bool


class PermissionAuditEntry(BaseModel):
    """Audit entry for permission changes."""
    id: UUID
    action: str  # granted, revoked, modified, expired
    document_id: UUID
    target_type: str  # user, role
    target_id: str
    permissions_before: Optional[PermissionFlags]
    permissions_after: Optional[PermissionFlags]
    changed_by: UUID
    changed_at: datetime
    details: Optional[Dict[str, Any]]


class PermissionAuditResponse(BaseModel):
    """Response schema for permission audit trail."""
    document_id: UUID
    total_entries: int
    entries: List[PermissionAuditEntry]
    page: int
    limit: int


class BulkPermissionRequest(BaseModel):
    """Request schema for bulk permission operations."""
    document_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    operation: str = Field(..., description="Operation: 'grant' or 'revoke'")
    target_type: str = Field(..., description="Target type: 'user' or 'role'")
    target_id: str = Field(..., description="User ID or role name")
    permissions: List[str] = Field(default=['read'], description="Permissions to grant/revoke")
    
    @validator('operation')
    def validate_operation(cls, v):
        if v not in ['grant', 'revoke']:
            raise ValueError("operation must be 'grant' or 'revoke'")
        return v
    
    @validator('target_type')
    def validate_target_type(cls, v):
        if v not in ['user', 'role']:
            raise ValueError("target_type must be 'user' or 'role'")
        return v


class BulkPermissionResponse(BaseModel):
    """Response schema for bulk permission operations."""
    success: bool
    processed_count: int
    failed_count: int
    errors: List[str]
    results: List[Dict[str, Any]]


class PermissionCleanupResponse(BaseModel):
    """Response schema for permission cleanup operations."""
    expired_permissions_removed: int
    invalid_permissions_removed: int
    total_cleanup_actions: int
    cleanup_timestamp: datetime


class DocumentAccessCheckRequest(BaseModel):
    """Request schema for checking document access."""
    user_id: UUID
    user_roles: List[str] = Field(default=[])
    permission_type: str = Field(default='read', description="Permission type to check")
    
    @validator('permission_type')
    def validate_permission_type(cls, v):
        valid_permissions = {'read', 'write', 'delete', 'share', 'admin'}
        if v not in valid_permissions:
            raise ValueError(f"Invalid permission type. Valid options: {valid_permissions}")
        return v


class DocumentAccessCheckResponse(BaseModel):
    """Response schema for document access check."""
    user_id: UUID
    document_id: UUID
    has_access: bool
    permission_type: str
    access_source: Optional[str] = Field(None, description="Source of access (direct, role:admin, owner, etc.)")
    effective_permissions: PermissionFlags