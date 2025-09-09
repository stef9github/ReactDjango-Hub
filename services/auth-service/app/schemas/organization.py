"""Organization management schemas for request/response validation"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr


class CreateOrganizationRequest(BaseModel):
    name: str
    description: Optional[str] = None
    organization_type: str = "company"
    industry: Optional[str] = None
    size: Optional[str] = None
    website: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None


class OrganizationResponse(BaseModel):
    organization_id: str
    name: str
    description: Optional[str]
    organization_type: str
    industry: Optional[str]
    size: Optional[str]
    website: Optional[str]
    address: Optional[Dict[str, Any]]
    settings: Dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: str


class OrganizationDashboardResponse(BaseModel):
    organization: OrganizationResponse
    member_count: int
    recent_activities: List[Dict[str, Any]]
    usage_stats: Dict[str, Any]
    subscription_info: Optional[Dict[str, Any]]


class AddUserToOrganizationRequest(BaseModel):
    user_id: str
    role: str = "member"


class OrganizationUserResponse(BaseModel):
    user_id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    display_name: Optional[str]
    role: str
    status: str
    joined_at: datetime
    last_active: Optional[datetime]