"""User management schemas for request/response validation"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr


class CreateUserProfileRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    bio: Optional[str] = None
    skills: List[str] = []
    interests: List[str] = []
    tenant_id: Optional[str] = None


class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    display_name: Optional[str]
    phone_number: Optional[str]
    job_title: Optional[str]
    department: Optional[str]
    bio: Optional[str]
    skills: List[str]
    interests: List[str]
    status: str
    created_at: datetime
    updated_at: datetime
    tenant_id: Optional[str]


class UpdateUserPreferencesRequest(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    privacy_settings: Optional[Dict[str, Any]] = None


class UserPreferencesResponse(BaseModel):
    user_id: str
    theme: str
    language: str
    timezone: str
    notification_preferences: Dict[str, Any]
    privacy_settings: Dict[str, Any]
    updated_at: datetime


class UserDashboardResponse(BaseModel):
    user: UserProfileResponse
    activity_summary: Dict[str, Any]
    recent_activities: List[Dict[str, Any]]
    preferences: UserPreferencesResponse


class UserActivitySummaryResponse(BaseModel):
    user_id: str
    total_activities: int
    activities_today: int
    activities_this_week: int
    activities_this_month: int
    recent_activities: List[Dict[str, Any]]


class EnhancedUserResponse(BaseModel):
    user_id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    display_name: Optional[str]
    phone_number: Optional[str]
    job_title: Optional[str]
    department: Optional[str]
    bio: Optional[str]
    skills: List[str]
    interests: List[str]
    status: str
    roles: List[str]
    permissions: List[str]
    organizations: List[Dict[str, Any]]
    preferences: Dict[str, Any]
    is_verified: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    tenant_id: Optional[str]


class UserSessionResponse(BaseModel):
    session_id: str
    user_id: str
    device_info: Dict[str, Any]
    ip_address: str
    location: Optional[str]
    created_at: datetime
    last_active: datetime
    is_current: bool