"""
Collaboration-related schemas for request/response validation.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class CreateCommentRequest(BaseModel):
    """Request schema for creating a comment."""
    content: str = Field(..., description="Comment content", min_length=1, max_length=5000)
    parent_comment_id: Optional[UUID] = Field(None, description="Parent comment ID for replies")
    page_number: Optional[int] = Field(None, description="Page number for PDF annotations", ge=1)
    position_data: Optional[Dict[str, Any]] = Field(None, description="Position/selection data for annotations")


class CommentResponse(BaseModel):
    """Response schema for comments."""
    id: UUID
    document_id: UUID
    author_id: UUID
    content: str
    parent_comment_id: Optional[UUID]
    page_number: Optional[int]
    position_data: Optional[Dict[str, Any]]
    status: str
    is_resolved: bool
    resolved_by: Optional[UUID]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    replies: List["CommentResponse"] = []
    
    class Config:
        from_attributes = True


class UpdateCommentRequest(BaseModel):
    """Request schema for updating a comment."""
    content: str = Field(..., description="Updated comment content", min_length=1, max_length=5000)


class ResolveCommentRequest(BaseModel):
    """Request schema for resolving a comment."""
    resolved: bool = Field(..., description="Whether to resolve or unresolve the comment")


class DocumentCommentsResponse(BaseModel):
    """Response schema for document comments."""
    document_id: UUID
    total_comments: int
    unresolved_comments: int
    comments: List[CommentResponse]
    page: int
    limit: int
    has_more: bool


class ActivityResponse(BaseModel):
    """Response schema for activities."""
    id: UUID
    document_id: UUID
    user_id: UUID
    activity_type: str
    activity_description: str
    target_user_id: Optional[UUID]
    metadata: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentActivitiesResponse(BaseModel):
    """Response schema for document activities."""
    document_id: UUID
    total_activities: int
    activities: List[ActivityResponse]
    page: int
    limit: int
    has_more: bool


class ShareNotificationResponse(BaseModel):
    """Response schema for share notifications."""
    id: UUID
    document_id: UUID
    shared_by: UUID
    shared_with_type: str
    shared_with_id: str
    share_message: Optional[str]
    access_level: str
    shared_at: datetime
    expires_at: Optional[datetime]
    notification_status: str
    notification_read_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserSharedDocumentsResponse(BaseModel):
    """Response schema for documents shared with a user."""
    total_shares: int
    unread_shares: int
    shares: List[ShareNotificationResponse]
    page: int
    limit: int
    has_more: bool


class CreateWorkspaceRequest(BaseModel):
    """Request schema for creating a workspace."""
    name: str = Field(..., description="Workspace name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Workspace description", max_length=1000)
    is_public: bool = Field(False, description="Whether workspace is public within organization")
    settings: Optional[Dict[str, Any]] = Field(None, description="Workspace settings")


class UpdateWorkspaceRequest(BaseModel):
    """Request schema for updating a workspace."""
    name: Optional[str] = Field(None, description="Updated workspace name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Updated workspace description", max_length=1000)
    is_public: Optional[bool] = Field(None, description="Whether workspace is public")
    settings: Optional[Dict[str, Any]] = Field(None, description="Updated workspace settings")


class WorkspaceResponse(BaseModel):
    """Response schema for workspaces."""
    id: UUID
    name: str
    description: Optional[str]
    organization_id: UUID
    created_by: UUID
    is_public: bool
    status: str
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any]
    
    class Config:
        from_attributes = True


class WorkspaceListResponse(BaseModel):
    """Response schema for workspace lists."""
    total_workspaces: int
    workspaces: List[WorkspaceResponse]
    page: int
    limit: int
    has_more: bool


class CollaborationStatsResponse(BaseModel):
    """Response schema for collaboration statistics."""
    document_id: UUID
    total_shares: int
    active_shares: int
    total_comments: int
    unresolved_comments: int
    total_activities: int
    recent_activity_count: int
    last_activity_at: Optional[datetime]
    
    # Share breakdown
    shares_by_type: Dict[str, int]  # {"user": 5, "role": 3}
    shares_by_access_level: Dict[str, int]  # {"read": 6, "write": 2}
    
    # Comment breakdown
    comments_by_status: Dict[str, int]  # {"active": 10, "resolved": 5}
    comments_by_page: Optional[Dict[str, int]]  # Page-wise comment distribution
    
    # Activity breakdown
    activities_by_type: Dict[str, int]  # Activity type distribution


class DocumentCollaborationSummary(BaseModel):
    """Complete collaboration summary for a document."""
    document_id: UUID
    document_name: str
    created_by: UUID
    
    # Permissions summary
    total_permissions: int
    direct_shares: int
    role_shares: int
    
    # Comments summary
    total_comments: int
    unresolved_comments: int
    comment_threads: int
    
    # Activity summary
    total_activities: int
    unique_collaborators: int
    last_activity_at: Optional[datetime]
    
    # Recent activity
    recent_activities: List[ActivityResponse]
    recent_comments: List[CommentResponse]
    
    # Statistics
    stats: CollaborationStatsResponse


class NotificationPreferencesRequest(BaseModel):
    """Request schema for notification preferences."""
    email_notifications: bool = Field(True, description="Enable email notifications")
    share_notifications: bool = Field(True, description="Notify when documents are shared with me")
    comment_notifications: bool = Field(True, description="Notify when someone comments on my documents")
    mention_notifications: bool = Field(True, description="Notify when I'm mentioned in comments")
    activity_digest: bool = Field(True, description="Enable daily/weekly activity digest")
    digest_frequency: str = Field("daily", description="Digest frequency: daily, weekly, none")
    
    @validator('digest_frequency')
    def validate_digest_frequency(cls, v):
        valid_frequencies = {'daily', 'weekly', 'none'}
        if v not in valid_frequencies:
            raise ValueError(f"digest_frequency must be one of {valid_frequencies}")
        return v


class NotificationPreferencesResponse(BaseModel):
    """Response schema for notification preferences."""
    user_id: UUID
    email_notifications: bool
    share_notifications: bool
    comment_notifications: bool
    mention_notifications: bool
    activity_digest: bool
    digest_frequency: str
    updated_at: datetime


class BulkCommentActionRequest(BaseModel):
    """Request schema for bulk comment operations."""
    comment_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    action: str = Field(..., description="Action: resolve, unresolve, delete")
    
    @validator('action')
    def validate_action(cls, v):
        valid_actions = {'resolve', 'unresolve', 'delete'}
        if v not in valid_actions:
            raise ValueError(f"action must be one of {valid_actions}")
        return v


class BulkCommentActionResponse(BaseModel):
    """Response schema for bulk comment operations."""
    success: bool
    processed_count: int
    failed_count: int
    errors: List[str]
    results: List[Dict[str, Any]]


class CollaborationInsightsResponse(BaseModel):
    """Response schema for collaboration insights."""
    organization_id: UUID
    time_period: str  # "last_7_days", "last_30_days", etc.
    
    # Overall statistics
    total_documents_with_collaboration: int
    total_shares: int
    total_comments: int
    total_activities: int
    active_collaborators: int
    
    # Trends
    share_trend: Dict[str, int]  # Date -> count
    comment_trend: Dict[str, int]  # Date -> count
    activity_trend: Dict[str, int]  # Date -> count
    
    # Top collaborators
    top_sharers: List[Dict[str, Any]]  # user_id, share_count, name?
    top_commenters: List[Dict[str, Any]]  # user_id, comment_count, name?
    most_active_users: List[Dict[str, Any]]  # user_id, activity_count, name?
    
    # Document insights
    most_shared_documents: List[Dict[str, Any]]  # document_id, share_count, name
    most_commented_documents: List[Dict[str, Any]]  # document_id, comment_count, name
    most_collaborative_documents: List[Dict[str, Any]]  # document_id, collaboration_score, name


# Update CommentResponse to handle forward reference
CommentResponse.model_rebuild()