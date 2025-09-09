"""
MFA Policy Service
Manages system-wide and per-user 2FA requirements and policies
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from .enhanced_models import User, Organization


class MFARequirement(str, Enum):
    """MFA requirement levels"""
    DISABLED = "disabled"          # 2FA not allowed
    OPTIONAL = "optional"          # 2FA available but not required
    RECOMMENDED = "recommended"    # 2FA suggested but not enforced
    REQUIRED = "required"          # 2FA mandatory for login
    REQUIRED_ADMIN = "required_admin"  # 2FA required for admin users only


class MFAEnforcementScope(str, Enum):
    """Where MFA enforcement applies"""
    LOGIN = "login"                # Required at login
    SENSITIVE_ACTIONS = "sensitive_actions"  # Required for sensitive operations
    API_ACCESS = "api_access"      # Required for API access
    ADMIN_ACTIONS = "admin_actions"  # Required for admin operations


@dataclass
class MFAPolicy:
    """MFA policy configuration"""
    requirement_level: MFARequirement
    enforcement_scopes: List[MFAEnforcementScope]
    allowed_methods: List[str]  # ['email', 'sms', 'totp', 'backup_codes']
    grace_period_days: Optional[int] = None  # Days before enforcement
    exceptions: List[str] = None  # User IDs or roles that are exempt


class MFAPolicyService:
    """Service for managing MFA policies and requirements"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_system_mfa_policy(self) -> MFAPolicy:
        """Get system-wide MFA policy"""
        
        # Get from system settings (you could store this in database or config)
        system_setting = await self._get_system_setting("mfa_policy")
        
        if system_setting:
            return MFAPolicy(
                requirement_level=MFARequirement(system_setting.get("requirement_level", "optional")),
                enforcement_scopes=[MFAEnforcementScope(scope) for scope in system_setting.get("enforcement_scopes", ["login"])],
                allowed_methods=system_setting.get("allowed_methods", ["email", "sms", "totp"]),
                grace_period_days=system_setting.get("grace_period_days"),
                exceptions=system_setting.get("exceptions", [])
            )
        
        # Default policy if none configured
        return MFAPolicy(
            requirement_level=MFARequirement.OPTIONAL,
            enforcement_scopes=[MFAEnforcementScope.LOGIN],
            allowed_methods=["email", "sms", "totp", "backup_codes"],
            grace_period_days=30,
            exceptions=[]
        )
    
    async def get_organization_mfa_policy(self, org_id: str) -> Optional[MFAPolicy]:
        """Get organization-specific MFA policy"""
        
        result = await self.db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        org = result.scalar_one_or_none()
        
        if not org or not org.settings.get("mfa_policy"):
            return None
        
        policy_data = org.settings["mfa_policy"]
        return MFAPolicy(
            requirement_level=MFARequirement(policy_data.get("requirement_level", "optional")),
            enforcement_scopes=[MFAEnforcementScope(scope) for scope in policy_data.get("enforcement_scopes", ["login"])],
            allowed_methods=policy_data.get("allowed_methods", ["email", "sms", "totp"]),
            grace_period_days=policy_data.get("grace_period_days"),
            exceptions=policy_data.get("exceptions", [])
        )
    
    async def get_user_mfa_policy(self, user_id: str) -> Optional[MFAPolicy]:
        """Get user-specific MFA override policy"""
        
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.preferences.get("mfa_policy"):
            return None
        
        policy_data = user.preferences["mfa_policy"]
        return MFAPolicy(
            requirement_level=MFARequirement(policy_data.get("requirement_level")),
            enforcement_scopes=[MFAEnforcementScope(scope) for scope in policy_data.get("enforcement_scopes", [])],
            allowed_methods=policy_data.get("allowed_methods", []),
            grace_period_days=policy_data.get("grace_period_days"),
            exceptions=[]  # User overrides don't have exceptions
        )
    
    async def get_effective_mfa_policy(self, user_id: str) -> MFAPolicy:
        """
        Get the effective MFA policy for a user considering all levels:
        1. User-specific override (highest priority)
        2. Organization policy 
        3. System-wide policy (fallback)
        """
        
        user = await self.db.execute(
            select(User).options(selectinload(User.organization)).where(User.id == user_id)
        )
        user = user.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        # Start with system policy
        effective_policy = await self.get_system_mfa_policy()
        
        # Override with organization policy if exists
        if user.organization_id:
            org_policy = await self.get_organization_mfa_policy(user.organization_id)
            if org_policy:
                effective_policy = self._merge_policies(effective_policy, org_policy)
        
        # Override with user policy if exists
        user_policy = await self.get_user_mfa_policy(user_id)
        if user_policy:
            effective_policy = self._merge_policies(effective_policy, user_policy)
        
        # Apply role-based overrides
        effective_policy = await self._apply_role_based_overrides(user, effective_policy)
        
        return effective_policy
    
    async def is_mfa_required_for_user(self, user_id: str, scope: MFAEnforcementScope = MFAEnforcementScope.LOGIN) -> bool:
        """Check if MFA is required for a specific user and scope"""
        
        policy = await self.get_effective_mfa_policy(user_id)
        
        # Check if user is in exceptions list
        if str(user_id) in policy.exceptions:
            return False
        
        # Check requirement level
        if policy.requirement_level == MFARequirement.DISABLED:
            return False
        elif policy.requirement_level == MFARequirement.REQUIRED:
            return scope in policy.enforcement_scopes
        elif policy.requirement_level == MFARequirement.REQUIRED_ADMIN:
            # Check if user has admin role
            is_admin = await self._user_has_admin_role(user_id)
            return is_admin and scope in policy.enforcement_scopes
        
        return False
    
    async def is_mfa_recommended_for_user(self, user_id: str) -> bool:
        """Check if MFA is recommended (but not required) for user"""
        
        policy = await self.get_effective_mfa_policy(user_id)
        return policy.requirement_level == MFARequirement.RECOMMENDED
    
    async def get_allowed_mfa_methods_for_user(self, user_id: str) -> List[str]:
        """Get allowed MFA methods for a specific user"""
        
        policy = await self.get_effective_mfa_policy(user_id)
        return policy.allowed_methods
    
    async def is_user_in_grace_period(self, user_id: str) -> bool:
        """Check if user is still in grace period for MFA enforcement"""
        
        policy = await self.get_effective_mfa_policy(user_id)
        
        if not policy.grace_period_days:
            return False
        
        # Get user creation or policy activation date
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return False
        
        # Calculate grace period end
        grace_period_start = user.created_at
        
        # Check if there's a policy activation date that's more recent
        policy_activated_at = user.preferences.get("mfa_policy_activated_at")
        if policy_activated_at:
            policy_date = datetime.fromisoformat(policy_activated_at)
            if policy_date > grace_period_start:
                grace_period_start = policy_date
        
        grace_period_end = grace_period_start + timedelta(days=policy.grace_period_days)
        return datetime.utcnow() < grace_period_end
    
    async def set_system_mfa_policy(self, policy: MFAPolicy) -> bool:
        """Set system-wide MFA policy"""
        
        policy_data = {
            "requirement_level": policy.requirement_level.value,
            "enforcement_scopes": [scope.value for scope in policy.enforcement_scopes],
            "allowed_methods": policy.allowed_methods,
            "grace_period_days": policy.grace_period_days,
            "exceptions": policy.exceptions or []
        }
        
        await self._set_system_setting("mfa_policy", policy_data)
        
        # Log policy change
        await self._log_policy_change("system", "mfa_policy_updated", policy_data)
        
        return True
    
    async def set_organization_mfa_policy(self, org_id: str, policy: MFAPolicy) -> bool:
        """Set organization-specific MFA policy"""
        
        policy_data = {
            "requirement_level": policy.requirement_level.value,
            "enforcement_scopes": [scope.value for scope in policy.enforcement_scopes],
            "allowed_methods": policy.allowed_methods,
            "grace_period_days": policy.grace_period_days,
            "exceptions": policy.exceptions or []
        }
        
        # Update organization settings
        await self.db.execute(
            update(Organization)
            .where(Organization.id == org_id)
            .values(
                settings=Organization.settings.op("||")({"mfa_policy": policy_data}),
                updated_at=datetime.utcnow()
            )
        )
        
        # Log policy change
        await self._log_policy_change("organization", "mfa_policy_updated", 
                                      {**policy_data, "org_id": org_id})
        
        await self.db.commit()
        return True
    
    async def set_user_mfa_override(self, user_id: str, policy: MFAPolicy) -> bool:
        """Set user-specific MFA policy override"""
        
        policy_data = {
            "requirement_level": policy.requirement_level.value,
            "enforcement_scopes": [scope.value for scope in policy.enforcement_scopes],
            "allowed_methods": policy.allowed_methods,
            "grace_period_days": policy.grace_period_days,
            "activated_at": datetime.utcnow().isoformat()
        }
        
        # Update user preferences
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                preferences=User.preferences.op("||")({"mfa_policy": policy_data}),
                updated_at=datetime.utcnow()
            )
        )
        
        # Log policy change
        await self._log_policy_change("user", "mfa_policy_updated", 
                                      {**policy_data, "user_id": user_id})
        
        await self.db.commit()
        return True
    
    async def remove_user_mfa_override(self, user_id: str) -> bool:
        """Remove user-specific MFA policy override"""
        
        # Get current preferences
        user_result = await self.db.execute(
            select(User.preferences).where(User.id == user_id)
        )
        current_prefs = user_result.scalar_one_or_none() or {}
        
        # Remove MFA policy
        if "mfa_policy" in current_prefs:
            del current_prefs["mfa_policy"]
            
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    preferences=current_prefs,
                    updated_at=datetime.utcnow()
                )
            )
            
            await self._log_policy_change("user", "mfa_policy_removed", {"user_id": user_id})
            await self.db.commit()
        
        return True
    
    def _merge_policies(self, base_policy: MFAPolicy, override_policy: MFAPolicy) -> MFAPolicy:
        """Merge two policies, with override taking precedence"""
        
        return MFAPolicy(
            requirement_level=override_policy.requirement_level,
            enforcement_scopes=override_policy.enforcement_scopes or base_policy.enforcement_scopes,
            allowed_methods=override_policy.allowed_methods or base_policy.allowed_methods,
            grace_period_days=override_policy.grace_period_days if override_policy.grace_period_days is not None else base_policy.grace_period_days,
            exceptions=base_policy.exceptions  # Exceptions only apply at system/org level
        )
    
    async def _apply_role_based_overrides(self, user: User, policy: MFAPolicy) -> MFAPolicy:
        """Apply role-based policy overrides"""
        
        # Check if user has admin/privileged roles
        is_admin = await self._user_has_admin_role(user.id)
        
        if is_admin and policy.requirement_level == MFARequirement.REQUIRED_ADMIN:
            # Convert to required for admin users
            policy.requirement_level = MFARequirement.REQUIRED
        
        return policy
    
    async def _user_has_admin_role(self, user_id: str) -> bool:
        """Check if user has admin or privileged role"""
        from .models import UserRole, Role
        
        result = await self.db.execute(
            select(Role.code)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id == user_id,
                Role.is_active == True,
                UserRole.valid_from <= datetime.utcnow()
            )
            .where(
                (UserRole.valid_until.is_(None)) | 
                (UserRole.valid_until >= datetime.utcnow())
            )
        )
        role_codes = [row[0] for row in result.fetchall()]
        
        # Check for admin/privileged roles
        admin_roles = ['admin', 'superuser', 'system_admin', 'org_admin']
        return any(role in admin_roles for role in role_codes)
    
    async def _get_system_setting(self, key: str) -> Optional[Dict]:
        """Get system setting (implement based on your settings storage)"""
        # This could be stored in database, Redis, config file, etc.
        # For now, return None (will use defaults)
        return None
    
    async def _set_system_setting(self, key: str, value: Dict) -> None:
        """Set system setting (implement based on your settings storage)"""
        # Implementation depends on your settings storage strategy
        pass
    
    async def _log_policy_change(self, level: str, action: str, details: Dict) -> None:
        """Log MFA policy changes"""
        from .enhanced_models import UserActivityLog
        
        log_entry = UserActivityLog(
            user_id=None,  # System-level change
            action=action,
            resource="mfa_policy",
            metadata={
                "level": level,
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            },
            success=True
        )
        self.db.add(log_entry)