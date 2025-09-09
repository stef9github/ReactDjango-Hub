"""
Workflow Instance model - stores active workflow executions
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, JSON, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin, UserTrackingMixin, OrganizationMixin

class WorkflowInstance(Base, UUIDMixin, TimestampMixin, UserTrackingMixin, OrganizationMixin):
    """
    Workflow Instance model
    
    Represents an active execution of a workflow definition.
    Each instance tracks the current state, context data, and execution history
    for a specific business process execution.
    """
    __tablename__ = "workflow_instances"
    
    # Definition reference
    definition_id = Column(UUID(as_uuid=True), ForeignKey("workflow_definitions.id"), nullable=False, index=True)
    
    # Instance identification
    entity_id = Column(String(255), nullable=False, index=True)  # e.g., "request-123", "employee-456"
    entity_type = Column(String(100), nullable=True, index=True)  # e.g., "purchase_request", "employee"
    title = Column(String(255), nullable=True)  # Human-readable title
    description = Column(Text, nullable=True)
    
    # Current state
    current_state = Column(String(100), nullable=False, index=True)
    previous_state = Column(String(100), nullable=True)
    
    # Execution tracking
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Status and priority
    status = Column(String(50), nullable=False, default="active", index=True)  # active, completed, failed, paused
    priority = Column(String(20), nullable=False, default="medium", index=True)  # low, medium, high, urgent
    
    # Assignment and ownership
    assigned_to = Column(String(255), nullable=True, index=True)  # User ID from identity service
    assigned_group = Column(String(255), nullable=True, index=True)  # Group/role from identity service
    
    # Context and metadata
    context_data = Column(JSON, nullable=True)  # Business context and variables
    execution_metadata = Column(JSON, nullable=True)  # Runtime execution data
    
    # Progress tracking
    progress_percentage = Column(String(5), nullable=False, default="0")  # 0-100
    estimated_completion = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_count = Column(String(10), nullable=False, default="0")
    last_error = Column(Text, nullable=True)
    
    # Relationships
    definition = relationship("WorkflowDefinition", back_populates="instances")
    history = relationship("WorkflowHistory", back_populates="instance", lazy="dynamic", order_by="WorkflowHistory.created_at.desc()")
    ai_insights = relationship("AIInsight", back_populates="instance", lazy="dynamic")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_workflow_instances_org_status', 'organization_id', 'status'),
        Index('ix_workflow_instances_org_state', 'organization_id', 'current_state'),
        Index('ix_workflow_instances_assigned_status', 'assigned_to', 'status'),
        Index('ix_workflow_instances_due_date_status', 'due_date', 'status'),
    )
    
    def __repr__(self):
        return f"<WorkflowInstance(id={self.id}, entity_id='{self.entity_id}', state='{self.current_state}')>"
    
    @property
    def is_active(self):
        """Check if workflow instance is currently active"""
        return self.status == "active"
    
    @property
    def is_completed(self):
        """Check if workflow instance is completed"""
        return self.status == "completed" and self.completed_at is not None
    
    @property
    def is_overdue(self):
        """Check if workflow instance is overdue"""
        if not self.due_date or self.is_completed:
            return False
        return datetime.utcnow() > self.due_date
    
    @property
    def duration(self):
        """Get workflow execution duration"""
        end_time = self.completed_at or datetime.utcnow()
        return end_time - self.started_at
    
    def get_context_value(self, key: str, default=None):
        """Get a value from context data"""
        if not self.context_data:
            return default
        return self.context_data.get(key, default)
    
    def set_context_value(self, key: str, value):
        """Set a value in context data"""
        if not self.context_data:
            self.context_data = {}
        self.context_data[key] = value
    
    def get_available_actions(self):
        """Get available actions based on current state and definition"""
        if not self.definition:
            return []
        
        transitions = self.definition.get_valid_transitions(self.current_state)
        return [transition.get('action') for transition in transitions if transition.get('action')]
    
    def can_transition_to(self, target_state: str, action: str = None):
        """Check if instance can transition to target state"""
        if not self.definition:
            return False
        
        return self.definition.validate_transition(
            self.current_state, 
            target_state, 
            action
        )
    
    def update_progress(self):
        """Calculate and update progress percentage based on state"""
        if not self.definition or not self.definition.states:
            return
        
        states = self.definition.state_list
        if not states:
            return
        
        try:
            current_index = states.index(self.current_state)
            progress = int((current_index / (len(states) - 1)) * 100)
            self.progress_percentage = str(min(100, max(0, progress)))
        except ValueError:
            # Current state not in definition states
            pass