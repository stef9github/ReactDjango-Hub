"""
AI Insight model - stores AI-generated insights and suggestions
"""
from sqlalchemy import Column, String, Text, JSON, Float, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin, OrganizationMixin

class AIInsight(Base, UUIDMixin, TimestampMixin, OrganizationMixin):
    """
    AI Insight model
    
    Stores AI-generated insights, suggestions, and analysis results
    associated with workflow instances. Used for smart recommendations,
    automated decision support, and workflow optimization.
    """
    __tablename__ = "ai_insights"
    
    # Instance reference
    instance_id = Column(UUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False, index=True)
    
    # Insight classification
    insight_type = Column(String(50), nullable=False, index=True)  # summary, suggestion, analysis, prediction
    category = Column(String(100), nullable=True, index=True)  # risk, optimization, compliance, etc.
    source = Column(String(50), nullable=False)  # openai, anthropic, custom_model
    
    # Content
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)  # Main insight content
    raw_response = Column(Text, nullable=True)  # Raw AI response for debugging
    
    # Confidence and quality metrics
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    quality_score = Column(Float, nullable=True)  # 0.0 to 1.0
    relevance_score = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Processing metadata
    model_version = Column(String(100), nullable=True)  # e.g., "gpt-4", "claude-3"
    processing_time_ms = Column(String(20), nullable=True)
    token_usage = Column(JSON, nullable=True)  # Token consumption details
    
    # Business impact
    priority = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    action_required = Column(Boolean, default=False, nullable=False)
    estimated_impact = Column(String(20), nullable=True)  # time_savings, cost_reduction, etc.
    
    # User interaction
    is_acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by = Column(String(255), nullable=True)  # User ID
    acknowledged_at = Column(String(50), nullable=True)  # Timestamp as string
    user_rating = Column(String(5), nullable=True)  # 1-5 rating from user
    user_feedback = Column(Text, nullable=True)
    
    # Status and lifecycle
    status = Column(String(50), nullable=False, default="active")  # active, dismissed, archived, applied
    is_actionable = Column(Boolean, default=True, nullable=False)
    expires_at = Column(String(50), nullable=True)  # Timestamp when insight becomes stale
    
    # Structured data
    structured_data = Column(JSON, nullable=True)  # Machine-readable insight data
    tags = Column(JSON, nullable=True)  # List of tags for categorization
    
    # Context
    context_snapshot = Column(JSON, nullable=True)  # Workflow context when insight was generated
    input_data = Column(JSON, nullable=True)  # Data used to generate the insight
    
    # Relationships
    instance = relationship("WorkflowInstance", back_populates="ai_insights")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_ai_insights_instance_type', 'instance_id', 'insight_type'),
        Index('ix_ai_insights_org_category', 'organization_id', 'category'),
        Index('ix_ai_insights_status_priority', 'status', 'priority'),
        Index('ix_ai_insights_created_score', 'created_at', 'confidence_score'),
    )
    
    def __repr__(self):
        return f"<AIInsight(id={self.id}, type='{self.insight_type}', confidence={self.confidence_score})>"
    
    @property
    def is_high_confidence(self):
        """Check if insight has high confidence (>0.8)"""
        return self.confidence_score is not None and self.confidence_score > 0.8
    
    @property
    def is_expired(self):
        """Check if insight has expired"""
        if not self.expires_at:
            return False
        try:
            from datetime import datetime
            expire_time = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
            return datetime.utcnow() > expire_time
        except (ValueError, AttributeError):
            return False
    
    @property
    def processing_time_seconds(self):
        """Get processing time in seconds"""
        if not self.processing_time_ms:
            return None
        try:
            return float(self.processing_time_ms) / 1000.0
        except (ValueError, TypeError):
            return None
    
    def get_structured_value(self, key: str, default=None):
        """Get a value from structured data"""
        if not self.structured_data:
            return default
        return self.structured_data.get(key, default)
    
    def add_tag(self, tag: str):
        """Add a tag to the insight"""
        if not self.tags:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)
    
    def has_tag(self, tag: str):
        """Check if insight has a specific tag"""
        return self.tags and tag in self.tags
    
    @classmethod
    def create_insight(cls, instance_id, insight_type, content, source="openai", 
                      confidence_score=None, **kwargs):
        """Helper method to create an AI insight"""
        return cls(
            instance_id=instance_id,
            insight_type=insight_type,
            content=content,
            source=source,
            confidence_score=confidence_score,
            **kwargs
        )