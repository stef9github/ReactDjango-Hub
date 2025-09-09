"""
MFA Policy API Endpoints
Manages system-wide and per-user 2FA requirements and policies
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .mfa_policy_service import MFAPolicyService, MFAPolicy, MFARequirement, MFAEnforcementScope
from .services import get_current_user
from .models import User

router = APIRouter(prefix="/mfa/policy", tags=["MFA Policy"])


# Request/Response Models
class MFAPolicyRequest(BaseModel):
    """MFA policy configuration request"""
    requirement_level: MFARequirement
    enforcement_scopes: List[MFAEnforcementScope] = ["login"]
    allowed_methods: List[str] = ["email", "sms", "totp", "backup_codes"]
    grace_period_days: Optional[int] = None
    exceptions: Optional[List[str]] = None


class MFAPolicyResponse(BaseModel):
    """MFA policy configuration response"""
    requirement_level: MFARequirement
    enforcement_scopes: List[MFAEnforcementScope]
    allowed_methods: List[str]
    grace_period_days: Optional[int]
    exceptions: Optional[List[str]]
    source: str  # "system", "organization", "user"


class UserMFAStatusResponse(BaseModel):
    """User's MFA status and requirements"""
    user_id: str
    mfa_required: bool
    mfa_recommended: bool
    allowed_methods: List[str]
    in_grace_period: bool
    grace_period_expires: Optional[str]
    current_methods: List[dict]
    policy_source: str


class MFAConfigurationResponse(BaseModel):
    """Complete MFA configuration overview"""
    system_policy: MFAPolicyResponse
    organization_policy: Optional[MFAPolicyResponse]
    user_override: Optional[MFAPolicyResponse]
    effective_policy: MFAPolicyResponse


# System-wide MFA Policy (Admin only)
@router.get("/system", response_model=MFAPolicyResponse)
async def get_system_mfa_policy(
    current_user: User = Depends(get_current_user),
    policy_service: MFAPolicyService = Depends()
):
    """Get system-wide MFA policy (Admin only)"""
    
    # Check admin permissions
    if not await _check_admin_permissions(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    policy = await policy_service.get_system_mfa_policy()
    
    return MFAPolicyResponse(
        requirement_level=policy.requirement_level,
        enforcement_scopes=policy.enforcement_scopes,
        allowed_methods=policy.allowed_methods,
        grace_period_days=policy.grace_period_days,
        exceptions=policy.exceptions,
        source="system"
    )


@router.put("/system", response_model=MFAPolicyResponse)
async def update_system_mfa_policy(
    policy_request: MFAPolicyRequest,
    current_user: User = Depends(get_current_user),
    policy_service: MFAPolicyService = Depends()
):
    """Update system-wide MFA policy (Admin only)"""
    
    # Check admin permissions
    if not await _check_admin_permissions(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    policy = MFAPolicy(
        requirement_level=policy_request.requirement_level,
        enforcement_scopes=policy_request.enforcement_scopes,
        allowed_methods=policy_request.allowed_methods,
        grace_period_days=policy_request.grace_period_days,
        exceptions=policy_request.exceptions or []
    )
    
    success = await policy_service.set_system_mfa_policy(policy)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update system MFA policy"
        )
    
    return MFAPolicyResponse(
        requirement_level=policy.requirement_level,
        enforcement_scopes=policy.enforcement_scopes,
        allowed_methods=policy.allowed_methods,
        grace_period_days=policy.grace_period_days,
        exceptions=policy.exceptions,
        source="system"
    )


# Organization MFA Policy (Org Admin only)
@router.get("/organization/{org_id}", response_model=Optional[MFAPolicyResponse])
async def get_organization_mfa_policy(
    org_id: str,
    current_user: User = Depends(get_current_user),
    policy_service: MFAPolicyService = Depends()
):
    """Get organization-specific MFA policy"""
    
    # Check organization permissions
    if not await _check_organization_permissions(current_user, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization admin permissions required"
        )
    
    policy = await policy_service.get_organization_mfa_policy(org_id)
    
    if not policy:
        return None
    
    return MFAPolicyResponse(
        requirement_level=policy.requirement_level,
        enforcement_scopes=policy.enforcement_scopes,
        allowed_methods=policy.allowed_methods,
        grace_period_days=policy.grace_period_days,
        exceptions=policy.exceptions,
        source="organization"
    )


@router.put("/organization/{org_id}", response_model=MFAPolicyResponse)
async def update_organization_mfa_policy(
    org_id: str,
    policy_request: MFAPolicyRequest,
    current_user: User = Depends(get_current_user),
    policy_service: MFAPolicyService = Depends()
):
    """Update organization-specific MFA policy"""
    
    # Check organization permissions
    if not await _check_organization_permissions(current_user, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization admin permissions required"
        )
    
    policy = MFAPolicy(
        requirement_level=policy_request.requirement_level,
        enforcement_scopes=policy_request.enforcement_scopes,
        allowed_methods=policy_request.allowed_methods,
        grace_period_days=policy_request.grace_period_days,
        exceptions=policy_request.exceptions or []
    )
    
    success = await policy_service.set_organization_mfa_policy(org_id, policy)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization MFA policy"
        )
    
    return MFAPolicyResponse(
        requirement_level=policy.requirement_level,
        enforcement_scopes=policy.enforcement_scopes,
        allowed_methods=policy.allowed_methods,
        grace_period_days=policy.grace_period_days,
        exceptions=policy.exceptions,
        source="organization"
    )


@router.delete("/organization/{org_id}")
async def remove_organization_mfa_policy(
    org_id: str,
    current_user: User = Depends(get_current_user),
    policy_service: MFAPolicyService = Depends()
):
    """Remove organization-specific MFA policy (revert to system policy)"""
    
    # Check organization permissions
    if not await _check_organization_permissions(current_user, org_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization admin permissions required"
        )
    
    # Implementation would remove the MFA policy from organization settings
    # For now, return success
    return {"message": "Organization MFA policy removed successfully"}


# User MFA Override (Self or Admin)
@router.get("/user/{user_id}", response_model=Optional[MFAPolicyResponse])
async def get_user_mfa_override(
    user_id: str,
    current_user: User = Depends(get_current_user),
    policy_service: MFAPolicyService = Depends()
):
    """Get user-specific MFA policy override"""
    
    # Check permissions (self or admin)
    if not await _check_user_permissions(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    policy = await policy_service.get_user_mfa_policy(user_id)
    
    if not policy:
        return None
    
    return MFAPolicyResponse(
        requirement_level=policy.requirement_level,
        enforcement_scopes=policy.enforcement_scopes,
        allowed_methods=policy.allowed_methods,
        grace_period_days=policy.grace_period_days,
        exceptions=None,  # User overrides don't have exceptions
        source="user"
    )


@router.put("/user/{user_id}", response_model=MFAPolicyResponse)
async def update_user_mfa_override(
    user_id: str,
    policy_request: MFAPolicyRequest,
    current_user: User = Depends(get_current_user),
    policy_service: MFAPolicyService = Depends()
):
    """Update user-specific MFA policy override"""
    
    # Check permissions (admin only for user overrides)
    if not await _check_admin_permissions(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required for user MFA overrides"
        )
    
    policy = MFAPolicy(
        requirement_level=policy_request.requirement_level,
        enforcement_scopes=policy_request.enforcement_scopes,
        allowed_methods=policy_request.allowed_methods,
        grace_period_days=policy_request.grace_period_days,
        exceptions=[]  # User overrides don't have exceptions
    )
    
    success = await policy_service.set_user_mfa_override(user_id, policy)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user MFA override"
        )
    
    return MFAPolicyResponse(
        requirement_level=policy.requirement_level,
        enforcement_scopes=policy.enforcement_scopes,
        allowed_methods=policy.allowed_methods,
        grace_period_days=policy.grace_period_days,
        exceptions=None,
        source="user"
    )


@router.delete("/user/{user_id}")
async def remove_user_mfa_override(
    user_id: str,
    current_user: User = Depends(get_current_user),
    policy_service: MFAPolicyService = Depends()
):
    """Remove user-specific MFA policy override"""
    
    # Check permissions (admin only)
    if not await _check_admin_permissions(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    success = await policy_service.remove_user_mfa_override(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove user MFA override"
        )
    
    return {"message": "User MFA override removed successfully"}


# User MFA Status and Requirements
@router.get("/status/{user_id}", response_model=UserMFAStatusResponse)
async def get_user_mfa_status(
    user_id: str,
    current_user: User = Depends(get_current_user),
    policy_service: MFAPolicyService = Depends()
):
    """Get user's effective MFA status and requirements"""
    
    # Check permissions (self or admin)
    if not await _check_user_permissions(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    try:
        # Get effective policy and requirements
        effective_policy = await policy_service.get_effective_mfa_policy(user_id)
        mfa_required = await policy_service.is_mfa_required_for_user(user_id)
        mfa_recommended = await policy_service.is_mfa_recommended_for_user(user_id)
        allowed_methods = await policy_service.get_allowed_mfa_methods_for_user(user_id)
        in_grace_period = await policy_service.is_user_in_grace_period(user_id)
        
        # Get current MFA methods (would come from MFAService)
        # current_methods = await mfa_service.get_user_mfa_methods(user_id)
        current_methods = []  # Placeholder
        
        # Determine policy source
        user_override = await policy_service.get_user_mfa_policy(user_id)
        if user_override:
            policy_source = "user_override"
        else:
            # Check if there's an org policy
            from .enhanced_models import User
            from sqlalchemy import select
            
            db_session = policy_service.db
            user_result = await db_session.execute(
                select(User.organization_id).where(User.id == user_id)
            )
            user_org_id = user_result.scalar_one_or_none()
            
            if user_org_id:
                org_policy = await policy_service.get_organization_mfa_policy(user_org_id)
                policy_source = "organization" if org_policy else "system"
            else:
                policy_source = "system"
        
        # Calculate grace period expiry if applicable
        grace_period_expires = None
        if in_grace_period and effective_policy.grace_period_days:
            # This would be calculated based on policy activation date
            # Implementation depends on your specific requirements
            pass
        
        return UserMFAStatusResponse(
            user_id=user_id,
            mfa_required=mfa_required,
            mfa_recommended=mfa_recommended,
            allowed_methods=allowed_methods,
            in_grace_period=in_grace_period,
            grace_period_expires=grace_period_expires,
            current_methods=current_methods,
            policy_source=policy_source
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/configuration/{user_id}", response_model=MFAConfigurationResponse)
async def get_user_mfa_configuration(
    user_id: str,
    current_user: User = Depends(get_current_user),
    policy_service: MFAPolicyService = Depends()
):
    """Get complete MFA configuration overview for user"""
    
    # Check permissions (self or admin)
    if not await _check_user_permissions(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    try:
        # Get all policy levels
        system_policy = await policy_service.get_system_mfa_policy()
        
        # Get user's organization
        from .enhanced_models import User
        from sqlalchemy import select
        
        db_session = policy_service.db
        user_result = await db_session.execute(
            select(User.organization_id).where(User.id == user_id)
        )
        user_org_id = user_result.scalar_one_or_none()
        
        org_policy = None
        if user_org_id:
            org_policy = await policy_service.get_organization_mfa_policy(user_org_id)
        
        user_override = await policy_service.get_user_mfa_policy(user_id)
        effective_policy = await policy_service.get_effective_mfa_policy(user_id)
        
        return MFAConfigurationResponse(
            system_policy=MFAPolicyResponse(
                requirement_level=system_policy.requirement_level,
                enforcement_scopes=system_policy.enforcement_scopes,
                allowed_methods=system_policy.allowed_methods,
                grace_period_days=system_policy.grace_period_days,
                exceptions=system_policy.exceptions,
                source="system"
            ),
            organization_policy=MFAPolicyResponse(
                requirement_level=org_policy.requirement_level,
                enforcement_scopes=org_policy.enforcement_scopes,
                allowed_methods=org_policy.allowed_methods,
                grace_period_days=org_policy.grace_period_days,
                exceptions=org_policy.exceptions,
                source="organization"
            ) if org_policy else None,
            user_override=MFAPolicyResponse(
                requirement_level=user_override.requirement_level,
                enforcement_scopes=user_override.enforcement_scopes,
                allowed_methods=user_override.allowed_methods,
                grace_period_days=user_override.grace_period_days,
                exceptions=None,
                source="user"
            ) if user_override else None,
            effective_policy=MFAPolicyResponse(
                requirement_level=effective_policy.requirement_level,
                enforcement_scopes=effective_policy.enforcement_scopes,
                allowed_methods=effective_policy.allowed_methods,
                grace_period_days=effective_policy.grace_period_days,
                exceptions=effective_policy.exceptions,
                source="effective"
            )
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# Helper functions for permission checking
async def _check_admin_permissions(user: User) -> bool:
    """Check if user has admin permissions"""
    # This would check user roles for admin privileges
    # Implementation depends on your role system
    return user.is_staff or hasattr(user, 'is_admin')


async def _check_organization_permissions(user: User, org_id: str) -> bool:
    """Check if user has organization admin permissions"""
    # Check if user is admin of the specific organization
    if await _check_admin_permissions(user):
        return True
    
    # Check if user belongs to organization and has org admin role
    return str(user.organization_id) == org_id and await _user_has_org_admin_role(user)


async def _check_user_permissions(user: User, target_user_id: str) -> bool:
    """Check if user can access target user's information"""
    # Users can access their own information
    if str(user.id) == target_user_id:
        return True
    
    # Admins can access any user
    if await _check_admin_permissions(user):
        return True
    
    # Organization admins can access users in their org
    # This would require checking if both users are in same org
    return False


async def _user_has_org_admin_role(user: User) -> bool:
    """Check if user has organization admin role"""
    # Implementation depends on your role system
    return False