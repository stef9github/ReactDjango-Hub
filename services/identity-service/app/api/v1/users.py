"""User Management API endpoints"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_user_service, get_event_publisher, get_current_user,
    require_permission
)
from app.schemas.user import (
    CreateUserProfileRequest, UserProfileResponse,
    UpdateUserPreferencesRequest, UserPreferencesResponse,
    UserDashboardResponse, UserActivitySummaryResponse
)
from app.services.user_service import UserManagementService
from app.utils.messaging import EventPublisher

router = APIRouter(prefix="/users", tags=["User Management"])


@router.post("/profile", response_model=UserProfileResponse)
async def create_user_profile(
    request: CreateUserProfileRequest,
    user_service: UserManagementService = Depends(get_user_service),
    event_publisher: EventPublisher = Depends(get_event_publisher)
):
    """Create complete user with enhanced profile"""
    try:
        user_data = await user_service.create_complete_user(
            email=request.email,
            password=request.password,
            profile_data={
                "first_name": request.first_name,
                "last_name": request.last_name,
                "phone_number": request.phone_number,
                "job_title": request.job_title,
                "department": request.department,
                "bio": request.bio,
                "skills": request.skills,
                "interests": request.interests
            },
            tenant_id=request.tenant_id
        )
        
        # Publish user creation event
        await event_publisher.publish_event("user.profile_created", {
            "user_id": user_data["user_id"],
            "email": request.email,
            "tenant_id": request.tenant_id
        })
        
        return UserProfileResponse(**user_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{user_id}/dashboard", response_model=UserDashboardResponse)
async def get_user_dashboard(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserManagementService = Depends(get_user_service)
):
    """Get user dashboard with comprehensive data"""
    # Users can only access their own dashboard unless they have admin permissions
    if (user_id != current_user["user_id"] and 
        "admin" not in current_user.get("roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        dashboard_data = await user_service.get_user_dashboard_data(user_id)
        return UserDashboardResponse(**dashboard_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.patch("/{user_id}/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    user_id: str,
    request: UpdateUserPreferencesRequest,
    current_user: dict = Depends(get_current_user),
    user_service: UserManagementService = Depends(get_user_service),
    event_publisher: EventPublisher = Depends(get_event_publisher)
):
    """Update user preferences and settings"""
    # Users can only update their own preferences
    if user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        preferences = await user_service.update_user_preferences(
            user_id=user_id,
            preferences_data={
                "theme": request.theme,
                "language": request.language,
                "timezone": request.timezone,
                "notification_preferences": request.notification_preferences,
                "privacy_settings": request.privacy_settings
            }
        )
        
        # Publish preferences update event
        await event_publisher.publish_event("user.preferences_updated", {
            "user_id": user_id,
            "preferences": preferences
        })
        
        return UserPreferencesResponse(**preferences)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{user_id}/activity", response_model=UserActivitySummaryResponse)
async def get_user_activity(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    user_service: UserManagementService = Depends(get_user_service)
):
    """Get user activity summary and recent activities"""
    # Users can only access their own activity unless they have admin permissions
    if (user_id != current_user["user_id"] and 
        "admin" not in current_user.get("roles", [])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        activity_data = await user_service.get_user_activity_summary(user_id)
        return UserActivitySummaryResponse(**activity_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )