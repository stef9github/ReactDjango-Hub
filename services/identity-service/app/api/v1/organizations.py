"""Organization Management API endpoints"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status

from app.api.deps import (
    get_user_service, get_event_publisher, get_current_user,
    require_permission, require_role
)
from app.schemas.organization import (
    CreateOrganizationRequest, OrganizationResponse,
    OrganizationDashboardResponse, AddUserToOrganizationRequest,
    OrganizationUserResponse
)
from app.services.user_service import UserManagementService
from app.utils.messaging import EventPublisher

router = APIRouter(prefix="/organizations", tags=["Organization Management"])


@router.post("", response_model=OrganizationResponse)
async def create_organization(
    request: CreateOrganizationRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserManagementService = Depends(get_user_service),
    event_publisher: EventPublisher = Depends(get_event_publisher)
):
    """Create new organization with multi-tenant support"""
    try:
        # Use organization service from user_service module
        org_data = await user_service.create_organization(
            name=request.name,
            description=request.description,
            organization_type=request.organization_type,
            industry=request.industry,
            size=request.size,
            website=request.website,
            address=request.address,
            settings=request.settings,
            created_by=current_user["user_id"]
        )
        
        # Publish organization creation event
        await event_publisher.publish_event("organization.created", {
            "organization_id": org_data["organization_id"],
            "name": request.name,
            "created_by": current_user["user_id"],
            "tenant_id": current_user.get("tenant_id")
        })
        
        return OrganizationResponse(**org_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{org_id}/dashboard", response_model=OrganizationDashboardResponse)
async def get_organization_dashboard(
    org_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserManagementService = Depends(get_user_service)
):
    """Get organization dashboard with analytics"""
    try:
        # Check if user has access to this organization
        user_orgs = await user_service.get_user_organizations(current_user["user_id"])
        if not any(org["organization_id"] == org_id for org in user_orgs):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        dashboard_data = await user_service.get_organization_dashboard_data(org_id)
        return OrganizationDashboardResponse(**dashboard_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )


@router.post("/{org_id}/users", response_model=OrganizationUserResponse)
async def add_user_to_organization(
    org_id: str,
    request: AddUserToOrganizationRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserManagementService = Depends(get_user_service),
    event_publisher: EventPublisher = Depends(get_event_publisher)
):
    """Add user to organization with role assignment"""
    try:
        # Check if current user has admin/owner permissions for this organization
        user_org_role = await user_service.get_user_organization_role(
            current_user["user_id"], org_id
        )
        if user_org_role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to add users"
            )
        
        user_org_data = await user_service.add_user_to_organization(
            user_id=request.user_id,
            organization_id=org_id,
            role=request.role,
            added_by=current_user["user_id"]
        )
        
        # Publish user addition event
        await event_publisher.publish_event("organization.user_added", {
            "organization_id": org_id,
            "user_id": request.user_id,
            "role": request.role,
            "added_by": current_user["user_id"]
        })
        
        return OrganizationUserResponse(**user_org_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{org_id}/users", response_model=List[OrganizationUserResponse])
async def list_organization_users(
    org_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserManagementService = Depends(get_user_service)
):
    """List all users in organization"""
    try:
        # Check if user has access to this organization
        user_orgs = await user_service.get_user_organizations(current_user["user_id"])
        if not any(org["organization_id"] == org_id for org in user_orgs):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this organization"
            )
        
        org_users = await user_service.get_organization_users(org_id)
        return [OrganizationUserResponse(**user) for user in org_users]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )