"""
Unit tests for database models
"""
import pytest
import uuid
from datetime import datetime

from models import (
    WorkflowDefinition, 
    WorkflowInstance, 
    WorkflowHistory, 
    AIInsight
)

class TestWorkflowDefinition:
    """Test WorkflowDefinition model"""
    
    def test_create_workflow_definition(self, test_session):
        """Test creating a workflow definition"""
        definition = WorkflowDefinition(
            name="Test Workflow",
            description="A test workflow",
            category="approval",
            version="1.0.0",
            organization_id="org-123",
            initial_state="draft",
            states=[
                {"name": "draft", "is_initial": True},
                {"name": "approved", "is_final": True}
            ],
            transitions=[
                {"from": "draft", "to": "approved", "action": "approve"}
            ],
            is_active=True,
            created_by="test-user"
        )
        
        test_session.add(definition)
        test_session.commit()
        
        assert definition.id is not None
        assert definition.name == "Test Workflow"
        assert definition.is_active is True
        assert definition.usage_count == 0
    
    def test_state_list_property(self, sample_workflow_definition):
        """Test state_list property"""
        states = sample_workflow_definition.state_list
        expected_states = ["draft", "pending_review", "approved", "rejected"]
        assert states == expected_states
    
    def test_get_state_config(self, sample_workflow_definition):
        """Test getting state configuration"""
        draft_config = sample_workflow_definition.get_state_config("draft")
        assert draft_config["name"] == "draft"
        assert draft_config["is_initial"] is True
        
        invalid_config = sample_workflow_definition.get_state_config("nonexistent")
        assert invalid_config is None
    
    def test_get_valid_transitions(self, sample_workflow_definition):
        """Test getting valid transitions from a state"""
        transitions = sample_workflow_definition.get_valid_transitions("draft")
        assert len(transitions) == 1
        assert transitions[0]["to"] == "pending_review"
        assert transitions[0]["action"] == "submit_for_review"
        
        # Test state with multiple transitions
        review_transitions = sample_workflow_definition.get_valid_transitions("pending_review")
        assert len(review_transitions) == 2
        actions = [t["action"] for t in review_transitions]
        assert "approve" in actions
        assert "reject" in actions
    
    def test_validate_transition(self, sample_workflow_definition):
        """Test transition validation"""
        # Valid transition
        assert sample_workflow_definition.validate_transition("draft", "pending_review", "submit_for_review")
        
        # Invalid transition (wrong target state)
        assert not sample_workflow_definition.validate_transition("draft", "approved", "submit_for_review")
        
        # Invalid transition (wrong action)
        assert not sample_workflow_definition.validate_transition("draft", "pending_review", "approve")

class TestWorkflowInstance:
    """Test WorkflowInstance model"""
    
    def test_create_workflow_instance(self, test_session, sample_workflow_definition):
        """Test creating a workflow instance"""
        instance = WorkflowInstance(
            definition_id=sample_workflow_definition.id,
            entity_id="test-123",
            entity_type="request",
            title="Test Request",
            current_state="draft",
            organization_id="org-123",
            context_data={"key": "value"},
            status="active",
            created_by="test-user"
        )
        
        test_session.add(instance)
        test_session.commit()
        
        assert instance.id is not None
        assert instance.entity_id == "test-123"
        assert instance.current_state == "draft"
        assert instance.is_active is True
        assert instance.is_completed is False
    
    def test_properties(self, sample_workflow_instance):
        """Test instance properties"""
        assert sample_workflow_instance.is_active is True
        assert sample_workflow_instance.is_completed is False
        assert sample_workflow_instance.is_overdue is False  # No due date set
        
        # Test duration
        duration = sample_workflow_instance.duration
        assert duration.total_seconds() >= 0
    
    def test_context_methods(self, sample_workflow_instance):
        """Test context data methods"""
        # Get existing value
        amount = sample_workflow_instance.get_context_value("amount")
        assert amount == 500
        
        # Get default for missing value
        missing = sample_workflow_instance.get_context_value("missing_key", "default")
        assert missing == "default"
        
        # Set new value
        sample_workflow_instance.set_context_value("new_key", "new_value")
        assert sample_workflow_instance.context_data["new_key"] == "new_value"
    
    def test_get_available_actions(self, test_session, sample_workflow_instance):
        """Test getting available actions"""
        actions = sample_workflow_instance.get_available_actions()
        assert "submit_for_review" in actions
    
    def test_can_transition_to(self, test_session, sample_workflow_instance):
        """Test transition validation"""
        # Valid transition
        assert sample_workflow_instance.can_transition_to("pending_review", "submit_for_review")
        
        # Invalid transition
        assert not sample_workflow_instance.can_transition_to("approved", "submit_for_review")
    
    def test_update_progress(self, test_session, sample_workflow_instance):
        """Test progress calculation"""
        sample_workflow_instance.update_progress()
        # Should be 0% for first state
        assert sample_workflow_instance.progress_percentage == "0"
        
        # Move to second state
        sample_workflow_instance.current_state = "pending_review"
        sample_workflow_instance.update_progress()
        # Should be 33% for second of 4 states
        assert int(sample_workflow_instance.progress_percentage) > 0

class TestWorkflowHistory:
    """Test WorkflowHistory model"""
    
    def test_create_history_entry(self, test_session, sample_workflow_instance):
        """Test creating a history entry"""
        history = WorkflowHistory.create_entry(
            instance_id=sample_workflow_instance.id,
            from_state="draft",
            to_state="pending_review",
            action="submit_for_review",
            triggered_by="test-user",
            comment="Submitted for review",
            action_metadata={"key": "value"}
        )
        
        test_session.add(history)
        test_session.commit()
        
        assert history.id is not None
        assert history.from_state == "draft"
        assert history.to_state == "pending_review"
        assert history.is_successful is True
        assert not history.is_initial_state
    
    def test_initial_state_entry(self, test_session, sample_workflow_instance):
        """Test initial state history entry"""
        history = WorkflowHistory.create_entry(
            instance_id=sample_workflow_instance.id,
            to_state="draft",
            action="create"
        )
        
        assert history.is_initial_state is True
    
    def test_duration_methods(self, test_session, sample_workflow_instance):
        """Test duration calculation methods"""
        history = WorkflowHistory.create_entry(
            instance_id=sample_workflow_instance.id,
            to_state="draft",
            action="create",
            duration_ms="1500"  # 1.5 seconds
        )
        
        assert history.duration_seconds == 1.5
    
    def test_metadata_methods(self, test_session, sample_workflow_instance):
        """Test metadata access methods"""
        history = WorkflowHistory.create_entry(
            instance_id=sample_workflow_instance.id,
            to_state="draft",
            action="create",
            action_metadata={"test_key": "test_value"},
            context_snapshot={"context_key": "context_value"}
        )
        
        assert history.get_metadata_value("test_key") == "test_value"
        assert history.get_metadata_value("missing", "default") == "default"
        
        assert history.get_context_value("context_key") == "context_value"

class TestAIInsight:
    """Test AIInsight model"""
    
    def test_create_ai_insight(self, test_session, sample_workflow_instance):
        """Test creating an AI insight"""
        insight = AIInsight.create_insight(
            instance_id=sample_workflow_instance.id,
            insight_type="suggestion",
            content="This request should be approved quickly",
            source="openai",
            confidence_score=0.95,
            organization_id="org-123"
        )
        
        test_session.add(insight)
        test_session.commit()
        
        assert insight.id is not None
        assert insight.insight_type == "suggestion"
        assert insight.confidence_score == 0.95
        assert insight.is_high_confidence is True
    
    def test_properties(self, test_session, sample_workflow_instance):
        """Test insight properties"""
        insight = AIInsight.create_insight(
            instance_id=sample_workflow_instance.id,
            insight_type="analysis",
            content="Analysis content",
            source="anthropic",
            confidence_score=0.7,
            processing_time_ms="2500",
            organization_id="org-123"
        )
        
        assert insight.is_high_confidence is False  # 0.7 < 0.8
        assert insight.processing_time_seconds == 2.5
    
    def test_structured_data_methods(self, test_session, sample_workflow_instance):
        """Test structured data methods"""
        insight = AIInsight.create_insight(
            instance_id=sample_workflow_instance.id,
            insight_type="analysis",
            content="Test content",
            source="openai",
            structured_data={"risk_score": 0.3, "category": "low_risk"},
            organization_id="org-123"
        )
        
        assert insight.get_structured_value("risk_score") == 0.3
        assert insight.get_structured_value("missing", "default") == "default"
    
    def test_tags_methods(self, test_session, sample_workflow_instance):
        """Test tag management methods"""
        insight = AIInsight.create_insight(
            instance_id=sample_workflow_instance.id,
            insight_type="suggestion",
            content="Test content",
            source="openai",
            tags=["urgent", "financial"],
            organization_id="org-123"
        )
        
        assert insight.has_tag("urgent") is True
        assert insight.has_tag("missing") is False
        
        insight.add_tag("new_tag")
        assert insight.has_tag("new_tag") is True
        assert len(insight.tags) == 3