"""
Workflow Definition model - stores reusable workflow templates
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, JSON
from sqlalchemy.orm import relationship
from .base import Base, UUIDMixin, TimestampMixin, UserTrackingMixin, OrganizationMixin

class WorkflowDefinition(Base, UUIDMixin, TimestampMixin, UserTrackingMixin, OrganizationMixin):
    """
    Workflow Definition model
    
    Stores reusable workflow templates that can be instantiated multiple times.
    Each definition contains the state machine configuration, business rules,
    and metadata for a specific type of business process.
    """
    __tablename__ = "workflow_definitions"
    
    # Basic definition info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)  # e.g., "approval", "onboarding", "project"
    version = Column(String(50), nullable=False, default="1.0.0")
    
    # State machine configuration
    initial_state = Column(String(100), nullable=False)
    states = Column(JSON, nullable=False)  # List of all possible states
    transitions = Column(JSON, nullable=False)  # State transition rules
    
    # Business rules and configuration
    business_rules = Column(JSON, nullable=True)  # Custom validation rules
    auto_transitions = Column(JSON, nullable=True)  # Automatic state changes
    sla_config = Column(JSON, nullable=True)  # SLA and timeout configuration
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)  # System template vs custom
    usage_count = Column(Integer, default=0, nullable=False)  # Number of instances created
    
    # Relationships
    instances = relationship("WorkflowInstance", back_populates="definition", lazy="dynamic")
    
    def __repr__(self):
        return f"<WorkflowDefinition(id={self.id}, name='{self.name}', version='{self.version}')>"
    
    @property
    def state_list(self):
        """Get list of state names"""
        return [state.get('name') for state in (self.states or [])]
    
    def get_state_config(self, state_name: str):
        """Get configuration for a specific state"""
        for state in (self.states or []):
            if state.get('name') == state_name:
                return state
        return None
    
    def get_valid_transitions(self, from_state: str):
        """Get valid transitions from a given state"""
        transitions = []
        for transition in (self.transitions or []):
            if transition.get('from') == from_state:
                transitions.append(transition)
        return transitions
    
    def validate_transition(self, from_state: str, to_state: str, action: str = None):
        """Validate if a state transition is allowed"""
        valid_transitions = self.get_valid_transitions(from_state)
        
        for transition in valid_transitions:
            if transition.get('to') == to_state:
                # If action is specified, check if it matches
                if action and transition.get('action') != action:
                    continue
                return True
        
        return False