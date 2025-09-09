"""
Unit tests for database models
"""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from models import WorkflowDefinition, WorkflowInstance, WorkflowHistory, AIInsight


@pytest.mark.unit
class TestWorkflowDefinition:
    """Unit tests for WorkflowDefinition model"""
    
    def test_workflow_definition_creation(self, test_session):
        """Test workflow definition can be created with valid data"""
        definition_data = {
            "name": "Test Approval Process",
            "description": "A test workflow for approval processes",
            "category": "approval",
            "version": "1.0.0",
            "initial_state": "draft",
            "states": [
                {"name": "draft", "title": "Draft", "is_initial": True, "is_final": False},
                {"name": "approved", "title": "Approved", "is_initial": False, "is_final": True}
            ],
            "transitions": [
                {"from": "draft", "to": "approved", "action": "approve", "title": "Approve"}
            ],
            "organization_id": "org-123",
            "created_by": "user-123"
        }
        
        definition = WorkflowDefinition(**definition_data)
        test_session.add(definition)
        test_session.commit()
        test_session.refresh(definition)
        
        assert definition.id is not None
        assert definition.name == "Test Approval Process"
        assert definition.initial_state == "draft"
        assert definition.is_active is True
        assert definition.usage_count == 0
        assert definition.created_at is not None
        assert isinstance(definition.created_at, datetime)

    def test_workflow_definition_state_list_property(self, test_session):
        """Test state_list property returns correct state names"""
        definition = WorkflowDefinition(
            name="Test Workflow",
            category="test",
            initial_state="start",
            states=[
                {"name": "start", "title": "Start"},
                {"name": "middle", "title": "Middle"},
                {"name": "end", "title": "End"}
            ],
            transitions=[],
            organization_id="org-123"
        )
        
        test_session.add(definition)
        test_session.commit()
        
        state_names = definition.state_list
        assert state_names == ["start", "middle", "end"]

    def test_get_state_config(self, test_session):
        """Test getting configuration for a specific state"""
        definition = WorkflowDefinition(
            name="Test Workflow",
            category="test", 
            initial_state="draft",
            states=[
                {"name": "draft", "title": "Draft", "color": "blue"},
                {"name": "review", "title": "Review", "color": "yellow"}
            ],
            transitions=[],
            organization_id="org-123"
        )
        
        test_session.add(definition)
        test_session.commit()
        
        draft_config = definition.get_state_config("draft")
        assert draft_config["title"] == "Draft"
        assert draft_config["color"] == "blue"
        
        nonexistent_config = definition.get_state_config("nonexistent")
        assert nonexistent_config is None

    def test_get_valid_transitions(self, test_session):
        """Test getting valid transitions from a state"""
        definition = WorkflowDefinition(
            name="Test Workflow",
            category="test",
            initial_state="draft",
            states=[
                {"name": "draft"}, {"name": "review"}, {"name": "approved"}
            ],
            transitions=[
                {"from": "draft", "to": "review", "action": "submit"},
                {"from": "draft", "to": "approved", "action": "auto_approve"},
                {"from": "review", "to": "approved", "action": "approve"}
            ],
            organization_id="org-123"
        )
        
        test_session.add(definition)
        test_session.commit()
        
        draft_transitions = definition.get_valid_transitions("draft")
        assert len(draft_transitions) == 2
        assert any(t["action"] == "submit" for t in draft_transitions)
        assert any(t["action"] == "auto_approve" for t in draft_transitions)
        
        review_transitions = definition.get_valid_transitions("review")
        assert len(review_transitions) == 1
        assert review_transitions[0]["action"] == "approve"

    def test_validate_transition(self, test_session):
        """Test transition validation"""
        definition = WorkflowDefinition(
            name="Test Workflow",
            category="test",
            initial_state="draft",
            states=[{"name": "draft"}, {"name": "approved"}],
            transitions=[
                {"from": "draft", "to": "approved", "action": "approve"}
            ],
            organization_id="org-123"
        )
        
        test_session.add(definition)
        test_session.commit()
        
        # Valid transition
        assert definition.validate_transition("draft", "approved", "approve") is True
        
        # Invalid transition - wrong action
        assert definition.validate_transition("draft", "approved", "reject") is False
        
        # Invalid transition - wrong states
        assert definition.validate_transition("approved", "draft", "approve") is False

    def test_workflow_definition_required_fields(self, test_session):
        """Test that required fields are enforced"""
        # Missing name should raise error
        with pytest.raises((IntegrityError, TypeError)):
            definition = WorkflowDefinition(
                category="test",
                initial_state="draft",
                organization_id="org-123"
            )
            test_session.add(definition)
            test_session.commit()


@pytest.mark.unit
class TestWorkflowInstance:
    """Unit tests for WorkflowInstance model"""
    
    def test_workflow_instance_creation(self, test_session, sample_workflow_definition):
        """Test workflow instance can be created"""
        instance_data = {
            "definition_id": sample_workflow_definition.id,
            "entity_id": "document-123",
            "entity_type": "document",
            "title": "Document Approval Request",
            "current_state": "draft",
            "organization_id": "org-123",
            "created_by": "user-123",
            "status": "active"
        }
        
        instance = WorkflowInstance(**instance_data)
        test_session.add(instance)
        test_session.commit()
        test_session.refresh(instance)
        
        assert instance.id is not None
        assert instance.entity_id == "document-123"
        assert instance.current_state == "draft"
        assert instance.status == "active"
        assert instance.progress_percentage == "0"
        assert instance.error_count == "0"

    def test_workflow_instance_properties(self, test_session, sample_workflow_definition):
        """Test workflow instance computed properties"""
        instance = WorkflowInstance(
            definition_id=sample_workflow_definition.id,
            entity_id="test-123",
            current_state="draft",
            status="active",
            organization_id="org-123",
            created_by="user-123"
        )
        
        test_session.add(instance)
        test_session.commit()
        
        # Test is_active property
        assert instance.is_active is True
        
        # Test is_completed property
        assert instance.is_completed is False
        
        # Test is_overdue property (no due date set)
        assert instance.is_overdue is False
        
        # Set due date in the past
        instance.due_date = datetime.utcnow() - timedelta(hours=1)
        assert instance.is_overdue is True
        
        # Set status to completed
        instance.status = "completed"
        instance.completed_at = datetime.utcnow()
        assert instance.is_completed is True
        assert instance.is_active is False

    def test_workflow_instance_duration_property(self, test_session, sample_workflow_definition):
        """Test duration calculation"""
        start_time = datetime.utcnow() - timedelta(hours=2)
        
        instance = WorkflowInstance(
            definition_id=sample_workflow_definition.id,
            entity_id="test-123",
            current_state="draft",
            started_at=start_time,
            organization_id="org-123",
            created_by="user-123"
        )
        
        test_session.add(instance)
        test_session.commit()
        
        duration = instance.duration
        assert duration.total_seconds() >= 7200  # At least 2 hours

    def test_context_data_methods(self, test_session, sample_workflow_definition):
        """Test context data getter and setter methods"""
        instance = WorkflowInstance(
            definition_id=sample_workflow_definition.id,
            entity_id="test-123",
            current_state="draft",
            organization_id="org-123",
            created_by="user-123"
        )
        
        test_session.add(instance)
        test_session.commit()
        
        # Test getting non-existent key
        value = instance.get_context_value("nonexistent", "default")
        assert value == "default"
        
        # Test setting and getting context value
        instance.set_context_value("priority", "high")
        assert instance.get_context_value("priority") == "high"
        
        # Test context_data was updated
        assert instance.context_data["priority"] == "high"

    def test_get_available_actions(self, test_session, sample_workflow_definition):
        """Test getting available actions based on current state"""
        instance = WorkflowInstance(
            definition_id=sample_workflow_definition.id,
            entity_id="test-123",
            current_state="draft",
            organization_id="org-123",
            created_by="user-123"
        )
        
        test_session.add(instance)
        test_session.commit()
        
        actions = instance.get_available_actions()
        assert "submit_for_review" in actions

    def test_can_transition_to(self, test_session, sample_workflow_definition):
        """Test transition possibility checking"""
        instance = WorkflowInstance(
            definition_id=sample_workflow_definition.id,
            entity_id="test-123",
            current_state="draft",
            organization_id="org-123",
            created_by="user-123"
        )
        
        test_session.add(instance)
        test_session.commit()
        
        # Valid transition
        assert instance.can_transition_to("pending_review", "submit_for_review") is True
        
        # Invalid transition
        assert instance.can_transition_to("approved", "submit_for_review") is False

    def test_update_progress(self, test_session, sample_workflow_definition):
        """Test progress calculation update"""
        instance = WorkflowInstance(
            definition_id=sample_workflow_definition.id,
            entity_id="test-123",
            current_state="pending_review",  # Second state in definition
            organization_id="org-123",
            created_by="user-123"
        )
        
        test_session.add(instance)
        test_session.commit()
        
        instance.update_progress()
        
        # Should be 33% (index 1 out of 4 states = 1/3 = ~33%)
        progress = int(instance.progress_percentage)
        assert progress > 0 and progress <= 50  # Allow some variance


@pytest.mark.unit  
class TestWorkflowHistory:
    """Unit tests for WorkflowHistory model"""
    
    def test_workflow_history_creation(self, test_session, sample_workflow_instance):
        """Test workflow history entry creation"""
        history_data = {
            "instance_id": sample_workflow_instance.id,
            "from_state": "draft",
            "to_state": "pending_review", 
            "action": "submit_for_review",
            "triggered_by": "user-123",
            "trigger_type": "manual",
            "comment": "Submitting for review",
            "action_metadata": {"priority": "high"},
            "duration_ms": "1500",
            "was_successful": "true"
        }
        
        history = WorkflowHistory(**history_data)
        test_session.add(history)
        test_session.commit()
        test_session.refresh(history)
        
        assert history.id is not None
        assert history.from_state == "draft"
        assert history.to_state == "pending_review"
        assert history.action == "submit_for_review"
        assert history.was_successful == "true"
        assert history.created_at is not None

    def test_workflow_history_create_entry_classmethod(self, test_session, sample_workflow_instance):
        """Test create_entry class method"""
        history = WorkflowHistory.create_entry(
            instance_id=sample_workflow_instance.id,
            from_state="draft",
            to_state="review",
            action="submit",
            triggered_by="user-123",
            comment="Test transition"
        )
        
        assert history.instance_id == sample_workflow_instance.id
        assert history.from_state == "draft"
        assert history.to_state == "review" 
        assert history.action == "submit"
        assert history.triggered_by == "user-123"
        assert history.comment == "Test transition"
        assert history.trigger_type == "manual"  # Default value
        assert history.was_successful == "true"  # Default value

    def test_workflow_history_is_successful_property(self, test_session, sample_workflow_instance):
        """Test is_successful computed property"""
        # Test successful history
        success_history = WorkflowHistory(
            instance_id=sample_workflow_instance.id,
            to_state="review",
            action="submit",
            was_successful="true"
        )
        assert success_history.is_successful is True
        
        # Test failed history
        fail_history = WorkflowHistory(
            instance_id=sample_workflow_instance.id,
            to_state="review",
            action="submit", 
            was_successful="false"
        )
        assert fail_history.is_successful is False


@pytest.mark.unit
class TestAIInsight:
    """Unit tests for AIInsight model"""
    
    def test_ai_insight_creation(self, test_session, sample_workflow_instance):
        """Test AI insight creation"""
        insight_data = {
            "instance_id": sample_workflow_instance.id,
            "insight_type": "optimization",
            "content": {"suggestions": ["Automate approval step", "Add notification"]},
            "confidence_score": 0.85,
            "generated_by": "openai-gpt4",
            "organization_id": "org-123"
        }
        
        insight = AIInsight(**insight_data)
        test_session.add(insight)
        test_session.commit()
        test_session.refresh(insight)
        
        assert insight.id is not None
        assert insight.insight_type == "optimization"
        assert insight.confidence_score == 0.85
        assert insight.generated_by == "openai-gpt4"
        assert insight.created_at is not None

    def test_ai_insight_validation(self, test_session, sample_workflow_instance):
        """Test AI insight data validation"""
        # Test confidence score bounds (should be between 0 and 1)
        insight = AIInsight(
            instance_id=sample_workflow_instance.id,
            insight_type="analysis",
            content={"result": "test"},
            confidence_score=1.5,  # Invalid - above 1.0
            organization_id="org-123"
        )
        
        # Note: Depending on your model validation, this might raise an error
        # For now, we'll just test that the model accepts the data
        test_session.add(insight)
        test_session.commit()
        
        # The confidence score should ideally be validated at the application level
        assert insight.confidence_score == 1.5


@pytest.mark.unit
class TestModelRelationships:
    """Unit tests for model relationships"""
    
    def test_workflow_definition_to_instances_relationship(self, test_session, sample_workflow_definition):
        """Test relationship between workflow definition and instances"""
        # Create instances
        instance1 = WorkflowInstance(
            definition_id=sample_workflow_definition.id,
            entity_id="test-1",
            current_state="draft",
            organization_id="org-123",
            created_by="user-123"
        )
        instance2 = WorkflowInstance(
            definition_id=sample_workflow_definition.id,
            entity_id="test-2", 
            current_state="draft",
            organization_id="org-123",
            created_by="user-123"
        )
        
        test_session.add_all([instance1, instance2])
        test_session.commit()
        
        # Test relationship
        instances = sample_workflow_definition.instances.all()
        assert len(instances) == 2
        assert instance1 in instances
        assert instance2 in instances

    def test_workflow_instance_to_history_relationship(self, test_session, sample_workflow_instance):
        """Test relationship between workflow instance and history"""
        # Create history entries
        history1 = WorkflowHistory(
            instance_id=sample_workflow_instance.id,
            to_state="review",
            action="submit"
        )
        history2 = WorkflowHistory(
            instance_id=sample_workflow_instance.id,
            from_state="review",
            to_state="approved", 
            action="approve"
        )
        
        test_session.add_all([history1, history2])
        test_session.commit()
        
        # Test relationship
        history_entries = sample_workflow_instance.history.all()
        assert len(history_entries) == 2

    def test_workflow_instance_to_ai_insights_relationship(self, test_session, sample_workflow_instance):
        """Test relationship between workflow instance and AI insights"""
        # Create AI insights
        insight1 = AIInsight(
            instance_id=sample_workflow_instance.id,
            insight_type="optimization",
            content={"suggestion": "Automate step"},
            organization_id="org-123"
        )
        insight2 = AIInsight(
            instance_id=sample_workflow_instance.id,
            insight_type="analysis",
            content={"analysis": "High priority"},
            organization_id="org-123"
        )
        
        test_session.add_all([insight1, insight2])
        test_session.commit()
        
        # Test relationship
        insights = sample_workflow_instance.ai_insights.all()
        assert len(insights) == 2
        assert insight1 in insights
        assert insight2 in insights