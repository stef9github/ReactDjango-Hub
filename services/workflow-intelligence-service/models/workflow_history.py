"""
Workflow History model - audit trail for workflow state changes
"""
from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin

class WorkflowHistory(Base, UUIDMixin, TimestampMixin):
    """
    Workflow History model
    
    Maintains an immutable audit trail of all state changes and actions
    taken during workflow execution. Critical for compliance, debugging,
    and workflow analytics.
    """
    __tablename__ = "workflow_history"
    
    # Instance reference
    instance_id = Column(UUID(as_uuid=True), ForeignKey("workflow_instances.id"), nullable=False, index=True)
    
    # State transition info
    from_state = Column(String(100), nullable=True)  # Null for initial state
    to_state = Column(String(100), nullable=False)
    action = Column(String(100), nullable=True)  # Action that triggered the transition
    
    # User and system tracking
    triggered_by = Column(String(255), nullable=True)  # User ID who triggered the action
    trigger_type = Column(String(50), nullable=False, default="manual")  # manual, automatic, scheduled, api
    
    # Action details
    comment = Column(Text, nullable=True)  # User comment or system message
    action_metadata = Column(JSON, nullable=True)  # Additional context data
    
    # System information
    system_info = Column(JSON, nullable=True)  # Request info, IP, user agent, etc.
    duration_ms = Column(String(20), nullable=True)  # How long the action took
    
    # Error tracking
    was_successful = Column(String(5), nullable=False, default="true")  # "true" or "false" as string
    error_message = Column(Text, nullable=True)
    
    # Business context
    context_snapshot = Column(JSON, nullable=True)  # Snapshot of context at time of action
    validation_results = Column(JSON, nullable=True)  # Results of business rule validation
    
    # Relationships
    instance = relationship("WorkflowInstance", back_populates="history")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_workflow_history_instance_created', 'instance_id', 'created_at'),
        Index('ix_workflow_history_trigger_type', 'trigger_type', 'created_at'),
        Index('ix_workflow_history_triggered_by', 'triggered_by', 'created_at'),
    )
    
    def __repr__(self):
        return f"<WorkflowHistory(instance_id={self.instance_id}, {self.from_state}->{self.to_state})>"
    
    @property
    def is_successful(self):
        """Check if the action was successful"""
        return self.was_successful == "true"
    
    @property
    def is_initial_state(self):
        """Check if this is the initial state entry"""
        return self.from_state is None
    
    @property 
    def duration_seconds(self):
        """Get duration in seconds"""
        if not self.duration_ms:
            return None
        try:
            return float(self.duration_ms) / 1000.0
        except (ValueError, TypeError):
            return None
    
    def get_metadata_value(self, key: str, default=None):
        """Get a value from action metadata"""
        if not self.action_metadata:
            return default
        return self.action_metadata.get(key, default)
    
    def get_context_value(self, key: str, default=None):
        """Get a value from context snapshot"""
        if not self.context_snapshot:
            return default
        return self.context_snapshot.get(key, default)
    
    @classmethod
    def create_entry(cls, instance_id, to_state, from_state=None, action=None, 
                     triggered_by=None, comment=None, action_metadata=None, **kwargs):
        """Helper method to create a history entry"""
        return cls(
            instance_id=instance_id,
            from_state=from_state,
            to_state=to_state,
            action=action,
            triggered_by=triggered_by,
            comment=comment,
            action_metadata=action_metadata,
            **kwargs
        )