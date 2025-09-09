"""
Enhanced User Management Service
Extends auth service with user profile and organization management
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models.enhanced_models import (
    User, Organization, UserProfile, UserActivityLog, 
    UserPreference, UserStatus, OrganizationType
)


@dataclass
class UserProfileData:
    """User profile creation/update data"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    bio: Optional[str] = None
    skills: List[str] = None
    interests: List[str] = None


@dataclass
class OrganizationData:
    """Organization creation/update data"""
    name: str
    slug: str
    description: Optional[str] = None
    website_url: Optional[str] = None
    contact_email: Optional[str] = None
    organization_type: OrganizationType = OrganizationType.INDIVIDUAL
    industry: Optional[str] = None


class UserManagementService:
    """Enhanced user management beyond basic authentication"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_complete_user(
        self, 
        email: str, 
        password_hash: str,
        profile_data: UserProfileData,
        organization_id: Optional[str] = None
    ) -> User:
        """Create user with complete profile information"""
        
        # Create base user
        user = User(
            email=email,
            password_hash=password_hash,
            first_name=profile_data.first_name,
            last_name=profile_data.last_name,
            phone_number=profile_data.phone_number,
            organization_id=organization_id,
            status=UserStatus.PENDING_VERIFICATION
        )
        
        self.db.add(user)
        await self.db.flush()  # Get user.id
        
        # Create extended profile
        if any([profile_data.job_title, profile_data.department, 
               profile_data.skills, profile_data.interests]):
            user_profile = UserProfile(
                user_id=user.id,
                job_title=profile_data.job_title,
                department=profile_data.department,
                skills=profile_data.skills or [],
                interests=profile_data.interests or []
            )
            self.db.add(user_profile)
        
        # Log user creation
        await self._log_activity(
            user.id, "user.created", 
            metadata={"email": email, "has_profile": True}
        )
        
        await self.db.commit()
        return user
    
    async def get_user_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user dashboard information"""
        
        # Get user with all related data
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.organization))
            .where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Get user profile
        profile_result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()
        
        # Get recent activity
        activity_result = await self.db.execute(
            select(UserActivityLog)
            .where(UserActivityLog.user_id == user_id)
            .order_by(UserActivityLog.created_at.desc())
            .limit(10)
        )
        recent_activity = activity_result.scalars().all()
        
        # Get active sessions count
        from .models import Session
        sessions_result = await self.db.execute(
            select(Session)
            .where(
                Session.user_id == user_id,
                Session.is_active == True,
                Session.expires_at > datetime.utcnow()
            )
        )
        active_sessions = len(sessions_result.scalars().all())
        
        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}".strip(),
                "status": user.status,
                "avatar_url": user.avatar_url,
                "last_login": user.last_login_at.isoformat() if user.last_login_at else None
            },
            "organization": {
                "id": str(user.organization.id) if user.organization else None,
                "name": user.organization.name if user.organization else None,
                "role": "member"  # Could be enhanced with role information
            } if user.organization else None,
            "profile": {
                "job_title": profile.job_title if profile else None,
                "department": profile.department if profile else None,
                "skills": profile.skills if profile else [],
                "onboarding_completed": profile.onboarding_completed if profile else False
            },
            "activity": {
                "recent_actions": [
                    {
                        "action": activity.action,
                        "timestamp": activity.created_at.isoformat(),
                        "success": activity.success
                    }
                    for activity in recent_activity
                ],
                "active_sessions": active_sessions
            },
            "preferences": {
                "language": user.language_code,
                "timezone": user.timezone,
                "theme": user.theme_preference
            }
        }
    
    async def update_user_preferences(
        self, 
        user_id: str, 
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user preferences and settings"""
        
        # Update direct user preferences
        user_updates = {}
        if "language_code" in preferences:
            user_updates["language_code"] = preferences["language_code"]
        if "timezone" in preferences:
            user_updates["timezone"] = preferences["timezone"]
        if "theme_preference" in preferences:
            user_updates["theme_preference"] = preferences["theme_preference"]
        
        if user_updates:
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(**user_updates, updated_at=datetime.utcnow())
            )
        
        # Update detailed preferences
        for category, settings in preferences.items():
            if category in ["language_code", "timezone", "theme_preference"]:
                continue  # Already handled above
            
            if isinstance(settings, dict):
                for key, value in settings.items():
                    await self._upsert_preference(user_id, category, key, value)
        
        await self._log_activity(
            user_id, "user.preferences_updated",
            metadata={"categories": list(preferences.keys())}
        )
        
        await self.db.commit()
        return True
    
    async def get_user_activity_summary(
        self, 
        user_id: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user activity summary for specified period"""
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(UserActivityLog)
            .where(
                UserActivityLog.user_id == user_id,
                UserActivityLog.created_at >= since_date
            )
            .order_by(UserActivityLog.created_at.desc())
        )
        activities = result.scalars().all()
        
        # Aggregate activity data
        activity_by_day = {}
        activity_by_type = {}
        success_rate = {"total": 0, "successful": 0}
        
        for activity in activities:
            day = activity.created_at.date().isoformat()
            activity_by_day[day] = activity_by_day.get(day, 0) + 1
            
            activity_by_type[activity.action] = activity_by_type.get(activity.action, 0) + 1
            
            success_rate["total"] += 1
            if activity.success:
                success_rate["successful"] += 1
        
        return {
            "period_days": days,
            "total_activities": len(activities),
            "activities_by_day": activity_by_day,
            "activities_by_type": activity_by_type,
            "success_rate": (
                success_rate["successful"] / success_rate["total"] 
                if success_rate["total"] > 0 else 0
            ),
            "recent_activities": [
                {
                    "action": activity.action,
                    "timestamp": activity.created_at.isoformat(),
                    "success": activity.success,
                    "ip_address": activity.ip_address
                }
                for activity in activities[:10]
            ]
        }
    
    async def _upsert_preference(
        self, 
        user_id: str, 
        category: str, 
        key: str, 
        value: Any
    ):
        """Insert or update a user preference"""
        
        # Try to update existing preference
        result = await self.db.execute(
            update(UserPreference)
            .where(
                UserPreference.user_id == user_id,
                UserPreference.category == category,
                UserPreference.key == key
            )
            .values(value=value, updated_at=datetime.utcnow())
            .returning(UserPreference.id)
        )
        
        # If no existing preference, create new one
        if not result.scalar_one_or_none():
            preference = UserPreference(
                user_id=user_id,
                category=category,
                key=key,
                value=value
            )
            self.db.add(preference)
    
    async def _log_activity(
        self, 
        user_id: str, 
        action: str,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict] = None,
        success: bool = True
    ):
        """Log user activity"""
        
        activity = UserActivityLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            ip_address=ip_address,
            metadata=metadata or {},
            success=success
        )
        self.db.add(activity)


class OrganizationManagementService:
    """Organization/tenant management service"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_organization(
        self, 
        org_data: OrganizationData,
        creator_user_id: Optional[str] = None
    ) -> Organization:
        """Create new organization/tenant"""
        
        # Check if slug is unique
        existing = await self.db.execute(
            select(Organization).where(Organization.slug == org_data.slug)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Organization slug '{org_data.slug}' already exists")
        
        # Create organization
        organization = Organization(
            name=org_data.name,
            slug=org_data.slug,
            description=org_data.description,
            website_url=org_data.website_url,
            contact_email=org_data.contact_email,
            organization_type=org_data.organization_type,
            industry=org_data.industry
        )
        
        self.db.add(organization)
        await self.db.flush()
        
        # If creator specified, update their organization
        if creator_user_id:
            await self.db.execute(
                update(User)
                .where(User.id == creator_user_id)
                .values(organization_id=organization.id)
            )
        
        await self.db.commit()
        return organization
    
    async def get_organization_dashboard(self, org_id: str) -> Dict[str, Any]:
        """Get organization dashboard data"""
        
        # Get organization with users
        result = await self.db.execute(
            select(Organization)
            .options(selectinload(Organization.users))
            .where(Organization.id == org_id)
        )
        organization = result.scalar_one_or_none()
        
        if not organization:
            return None
        
        # Count active users
        active_users = len([u for u in organization.users if u.is_active])
        
        return {
            "organization": {
                "id": str(organization.id),
                "name": organization.name,
                "slug": organization.slug,
                "type": organization.organization_type,
                "industry": organization.industry,
                "created_at": organization.created_at.isoformat()
            },
            "stats": {
                "total_users": len(organization.users),
                "active_users": active_users,
                "subscription_tier": organization.subscription_tier
            },
            "recent_users": [
                {
                    "id": str(user.id),
                    "name": f"{user.first_name} {user.last_name}".strip(),
                    "email": user.email,
                    "status": user.status,
                    "joined_at": user.created_at.isoformat()
                }
                for user in sorted(
                    organization.users, 
                    key=lambda u: u.created_at, 
                    reverse=True
                )[:10]
            ]
        }