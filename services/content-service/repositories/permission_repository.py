"""
Permission repository for document access control operations.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from models.permission import DocumentPermission
from models.document import Document


class PermissionRepository(BaseRepository[DocumentPermission]):
    """Repository for document permission operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentPermission)
    
    async def grant_user_permission(
        self,
        document_id: UUID,
        user_id: UUID,
        permissions: List[str],
        granted_by: UUID,
        expires_at: Optional[datetime] = None
    ) -> DocumentPermission:
        """Grant permissions to a user for a document."""
        # Remove existing permissions for this user/document combination
        await self.revoke_user_permission(document_id, user_id)
        
        # Create new permission
        permission = DocumentPermission.create_user_permission(
            document_id=document_id,
            user_id=user_id,
            granted_by=granted_by,
            permissions=permissions,
            expires_at=expires_at
        )
        
        return await self.create_instance(permission)
    
    async def grant_role_permission(
        self,
        document_id: UUID,
        role_name: str,
        permissions: List[str],
        granted_by: UUID,
        expires_at: Optional[datetime] = None
    ) -> DocumentPermission:
        """Grant permissions to a role for a document."""
        # Remove existing permissions for this role/document combination
        await self.revoke_role_permission(document_id, role_name)
        
        # Create new permission
        permission = DocumentPermission.create_role_permission(
            document_id=document_id,
            role_name=role_name,
            granted_by=granted_by,
            permissions=permissions,
            expires_at=expires_at
        )
        
        return await self.create_instance(permission)
    
    async def get_user_permissions(
        self,
        document_id: UUID,
        user_id: UUID
    ) -> Optional[DocumentPermission]:
        """Get direct user permissions for a document."""
        stmt = select(DocumentPermission).where(
            and_(
                DocumentPermission.document_id == document_id,
                DocumentPermission.user_id == user_id
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_role_permissions(
        self,
        document_id: UUID,
        role_name: str
    ) -> Optional[DocumentPermission]:
        """Get role permissions for a document."""
        stmt = select(DocumentPermission).where(
            and_(
                DocumentPermission.document_id == document_id,
                DocumentPermission.role_name == role_name
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_document_permissions(
        self,
        document_id: UUID,
        include_expired: bool = False
    ) -> List[DocumentPermission]:
        """Get all permissions for a document."""
        conditions = [DocumentPermission.document_id == document_id]
        
        if not include_expired:
            conditions.append(
                or_(
                    DocumentPermission.expires_at.is_(None),
                    DocumentPermission.expires_at > func.now()
                )
            )
        
        stmt = select(DocumentPermission).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def check_user_permission(
        self,
        document_id: UUID,
        user_id: UUID,
        user_roles: List[str],
        permission_type: str
    ) -> bool:
        """Check if a user has a specific permission for a document."""
        # First check direct user permissions
        user_permission = await self.get_user_permissions(document_id, user_id)
        if user_permission and not user_permission.is_expired:
            if user_permission.has_permission(permission_type):
                return True
        
        # Then check role-based permissions
        for role in user_roles:
            role_permission = await self.get_role_permissions(document_id, role)
            if role_permission and not role_permission.is_expired:
                if role_permission.has_permission(permission_type):
                    return True
        
        return False
    
    async def get_user_effective_permissions(
        self,
        document_id: UUID,
        user_id: UUID,
        user_roles: List[str]
    ) -> Dict[str, bool]:
        """Get effective permissions for a user (combining direct and role permissions)."""
        effective_permissions = {
            "read": False,
            "write": False,
            "delete": False,
            "share": False,
            "admin": False
        }
        
        # Check direct user permissions
        user_permission = await self.get_user_permissions(document_id, user_id)
        if user_permission and not user_permission.is_expired:
            for perm in effective_permissions:
                if user_permission.has_permission(perm):
                    effective_permissions[perm] = True
        
        # Check role permissions (combine with existing)
        for role in user_roles:
            role_permission = await self.get_role_permissions(document_id, role)
            if role_permission and not role_permission.is_expired:
                for perm in effective_permissions:
                    if role_permission.has_permission(perm):
                        effective_permissions[perm] = True
        
        return effective_permissions
    
    async def revoke_user_permission(
        self,
        document_id: UUID,
        user_id: UUID
    ) -> bool:
        """Revoke user permissions for a document."""
        permission = await self.get_user_permissions(document_id, user_id)
        if permission:
            await self.delete_by_id(permission.id)
            return True
        return False
    
    async def revoke_role_permission(
        self,
        document_id: UUID,
        role_name: str
    ) -> bool:
        """Revoke role permissions for a document."""
        permission = await self.get_role_permissions(document_id, role_name)
        if permission:
            await self.delete_by_id(permission.id)
            return True
        return False
    
    async def get_user_accessible_documents(
        self,
        user_id: UUID,
        user_roles: List[str],
        organization_id: UUID,
        permission_type: str = "read",
        limit: int = 50,
        offset: int = 0
    ) -> List[Document]:
        """Get documents accessible to a user based on permissions."""
        # Build conditions for user and role permissions
        user_condition = and_(
            DocumentPermission.user_id == user_id,
            DocumentPermission.can_read == True
        )
        
        role_conditions = []
        for role in user_roles:
            role_conditions.append(
                and_(
                    DocumentPermission.role_name == role,
                    DocumentPermission.can_read == True
                )
            )
        
        permission_condition = user_condition
        if role_conditions:
            permission_condition = or_(user_condition, *role_conditions)
        
        # Add expiration check
        permission_condition = and_(
            permission_condition,
            or_(
                DocumentPermission.expires_at.is_(None),
                DocumentPermission.expires_at > func.now()
            )
        )
        
        stmt = (
            select(Document)
            .join(DocumentPermission, Document.id == DocumentPermission.document_id)
            .where(
                and_(
                    Document.organization_id == organization_id,
                    Document.status == "active",
                    permission_condition
                )
            )
            .distinct()
            .offset(offset)
            .limit(limit)
            .order_by(Document.created_at.desc())
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_documents_shared_with_user(
        self,
        user_id: UUID,
        user_roles: List[str],
        organization_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Document]:
        """Get documents that have been specifically shared with a user."""
        # Only include documents where user is not the creator
        user_condition = and_(
            DocumentPermission.user_id == user_id,
            DocumentPermission.can_read == True,
            Document.created_by != user_id
        )
        
        role_conditions = []
        for role in user_roles:
            role_conditions.append(
                and_(
                    DocumentPermission.role_name == role,
                    DocumentPermission.can_read == True,
                    Document.created_by != user_id
                )
            )
        
        permission_condition = user_condition
        if role_conditions:
            permission_condition = or_(user_condition, *role_conditions)
        
        # Add expiration check
        permission_condition = and_(
            permission_condition,
            or_(
                DocumentPermission.expires_at.is_(None),
                DocumentPermission.expires_at > func.now()
            )
        )
        
        stmt = (
            select(Document)
            .join(DocumentPermission, Document.id == DocumentPermission.document_id)
            .where(
                and_(
                    Document.organization_id == organization_id,
                    Document.status == "active",
                    permission_condition
                )
            )
            .distinct()
            .offset(offset)
            .limit(limit)
            .order_by(DocumentPermission.granted_at.desc())
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_permission_summary(
        self,
        document_id: UUID
    ) -> Dict[str, Any]:
        """Get a summary of permissions for a document."""
        permissions = await self.get_all_document_permissions(document_id)
        
        user_permissions = []
        role_permissions = []
        
        for perm in permissions:
            perm_data = {
                "id": str(perm.id),
                "granted_by": str(perm.granted_by),
                "granted_at": perm.granted_at.isoformat(),
                "expires_at": perm.expires_at.isoformat() if perm.expires_at else None,
                "permissions": {
                    "read": perm.can_read,
                    "write": perm.can_write,
                    "delete": perm.can_delete,
                    "share": perm.can_share,
                    "admin": perm.can_admin
                },
                "is_expired": perm.is_expired
            }
            
            if perm.user_id:
                perm_data["user_id"] = str(perm.user_id)
                user_permissions.append(perm_data)
            else:
                perm_data["role_name"] = perm.role_name
                role_permissions.append(perm_data)
        
        return {
            "document_id": str(document_id),
            "total_permissions": len(permissions),
            "user_permissions": user_permissions,
            "role_permissions": role_permissions
        }
    
    async def clean_expired_permissions(self) -> int:
        """Remove expired permissions and return count removed."""
        stmt = select(DocumentPermission).where(
            and_(
                DocumentPermission.expires_at.is_not(None),
                DocumentPermission.expires_at <= func.now()
            )
        )
        result = await self.session.execute(stmt)
        expired_permissions = list(result.scalars().all())
        
        count = len(expired_permissions)
        for perm in expired_permissions:
            await self.session.delete(perm)
        
        await self.session.flush()
        return count
    
    async def create_instance(self, permission: DocumentPermission) -> DocumentPermission:
        """Helper method to create a permission instance."""
        self.session.add(permission)
        await self.session.flush()
        await self.session.refresh(permission)
        return permission