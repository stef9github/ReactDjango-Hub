"""
Unit tests for workflow models - focuses on model functionality without full app dependencies
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Import models directly without app dependencies
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.workflow_definition import WorkflowDefinition
from models.workflow_instance import WorkflowInstance
from models.workflow_history import WorkflowHistory


@pytest.mark.unit
class TestWorkflowDefinitionModel:
    """Unit tests for WorkflowDefinition model"""

    def test_workflow_definition_creation(self):
        """Test creating a workflow definition"""
        definition = WorkflowDefinition(
            name="Test Workflow",
            description="A test workflow for unit testing",
            category="test",
            version="1.0.0",
            initial_state="draft",
            states=[
                {"name": "draft", "label": "Draft"},
                {"name": "review", "label": "Under Review"},
                {"name": "approved", "label": "Approved", "is_final": True}
            ],
            transitions=[
                {"from": "draft", "to": "review", "action": "submit"},
                {"from": "review", "to": "approved", "action": "approve"},
                {"from": "review", "to": "draft", "action": "reject"}
            ],
            organization_id="org-123"
        )
        
        # Test basic properties
        assert definition.name == "Test Workflow"
        assert definition.category == "test"
        assert definition.initial_state == "draft"
        assert len(definition.states) == 3
        assert len(definition.transitions) == 3

    def test_workflow_definition_state_list(self):
        """Test getting state list from definition"""
        definition = WorkflowDefinition(
            name="State List Test",
            category="test",
            initial_state="start",
            states=[
                {"name": "start"},
                {"name": "middle"},
                {"name": "end"}
            ],
            transitions=[],
            organization_id="org-123"
        )
        
        state_list = definition.state_list
        assert state_list == ["start", "middle", "end"]

    def test_workflow_definition_get_state_config(self):
        """Test getting specific state configuration"""
        definition = WorkflowDefinition(
            name="State Config Test",
            category="test",
            initial_state="draft",
            states=[
                {"name": "draft", "label": "Draft", "color": "blue"},
                {"name": "review", "label": "Under Review", "color": "yellow"},
                {"name": "approved", "label": "Approved", "color": "green", "is_final": True}
            ],
            transitions=[],
            organization_id="org-123"
        )
        
        # Test getting existing state
        draft_config = definition.get_state_config("draft")
        assert draft_config["label"] == "Draft"
        assert draft_config["color"] == "blue"
        
        # Test getting non-existent state
        nonexistent = definition.get_state_config("nonexistent")
        assert nonexistent is None

    def test_workflow_definition_get_valid_transitions(self):
        """Test getting valid transitions from a state"""
        definition = WorkflowDefinition(
            name="Transitions Test",
            category="test",
            initial_state="draft",
            states=[
                {"name": "draft"},
                {"name": "review"},
                {"name": "approved"}
            ],
            transitions=[
                {"from": "draft", "to": "review", "action": "submit"},
                {"from": "draft", "to": "approved", "action": "auto_approve"},
                {"from": "review", "to": "approved", "action": "approve"},
                {"from": "review", "to": "draft", "action": "reject"}
            ],
            organization_id="org-123"
        )
        
        # Test transitions from draft
        draft_transitions = definition.get_valid_transitions("draft")
        assert len(draft_transitions) == 2
        actions = [t["action"] for t in draft_transitions]
        assert "submit" in actions
        assert "auto_approve" in actions
        
        # Test transitions from review
        review_transitions = definition.get_valid_transitions("review")
        assert len(review_transitions) == 2
        
        # Test transitions from state with no outgoing transitions
        no_transitions = definition.get_valid_transitions("approved")
        assert len(no_transitions) == 0

    def test_workflow_definition_validate_transition(self):
        """Test transition validation"""
        definition = WorkflowDefinition(
            name="Validation Test",
            category="test",
            initial_state="draft",
            states=[
                {"name": "draft"},
                {"name": "review"},
                {"name": "approved"}
            ],
            transitions=[
                {"from": "draft", "to": "review", "action": "submit"},
                {"from": "review", "to": "approved", "action": "approve"},
                {"from": "review", "to": "draft", "action": "reject"}
            ],
            organization_id="org-123"
        )
        
        # Test valid transitions
        assert definition.validate_transition("draft", "review", "submit") is True
        assert definition.validate_transition("review", "approved", "approve") is True
        assert definition.validate_transition("review", "draft", "reject") is True
        
        # Test invalid transitions
        assert definition.validate_transition("draft", "approved", "submit") is False  # Wrong target
        assert definition.validate_transition("draft", "review", "wrong_action") is False  # Wrong action
        assert definition.validate_transition("approved", "draft", "submit") is False  # No such transition
        
        # Test transition without action specified
        assert definition.validate_transition("draft", "review") is True  # Should match any action to that state


@pytest.mark.unit
class TestWorkflowInstanceModel:
    """Unit tests for WorkflowInstance model"""

    def test_workflow_instance_creation(self):
        """Test creating a workflow instance"""
        instance = WorkflowInstance(
            definition_id=uuid.uuid4(),
            entity_id="test-entity-123",
            entity_type="purchase_request",
            title="Test Purchase Request",
            current_state="draft",
            context_data={"amount": 1000, "department": "IT"},
            assigned_to="user-123",
            organization_id="org-456"
        )
        
        assert instance.entity_id == "test-entity-123"
        assert instance.entity_type == "purchase_request"
        assert instance.title == "Test Purchase Request"
        assert instance.current_state == "draft"
        assert instance.context_data["amount"] == 1000
        assert instance.assigned_to == "user-123"

    def test_workflow_instance_properties(self):
        """Test workflow instance computed properties"""
        instance = WorkflowInstance(
            definition_id=uuid.uuid4(),
            entity_id="properties-test",
            current_state="active",
            status="active",
            started_at=datetime.utcnow() - timedelta(hours=2),
            organization_id="org-123"
        )
        
        # Test is_active property
        assert instance.is_active is True
        
        # Test is_completed property (should be False)
        assert instance.is_completed is False
        
        # Test duration property
        duration = instance.duration
        assert duration.total_seconds() > 7000  # More than 2 hours in seconds

    def test_workflow_instance_completion(self):
        """Test workflow instance completion"""
        instance = WorkflowInstance(
            definition_id=uuid.uuid4(),
            entity_id="completion-test",
            current_state="completed",
            status="completed",
            started_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=datetime.utcnow(),
            organization_id="org-123"
        )
        
        assert instance.is_active is False
        assert instance.is_completed is True
        
        # Test duration with completed workflow
        duration = instance.duration
        assert duration.total_seconds() > 3500  # Approximately 1 hour

    def test_workflow_instance_overdue_detection(self):
        """Test overdue detection"""
        # Instance without due date (not overdue)
        instance_no_due = WorkflowInstance(
            definition_id=uuid.uuid4(),
            entity_id="no-due-test",
            current_state="active",
            status="active",
            organization_id="org-123"
        )
        assert instance_no_due.is_overdue is False
        
        # Instance with future due date (not overdue)
        instance_future_due = WorkflowInstance(
            definition_id=uuid.uuid4(),
            entity_id="future-due-test",
            current_state="active",
            status="active",
            due_date=datetime.utcnow() + timedelta(days=1),
            organization_id="org-123"
        )
        assert instance_future_due.is_overdue is False
        
        # Instance with past due date (overdue)
        instance_overdue = WorkflowInstance(
            definition_id=uuid.uuid4(),
            entity_id="overdue-test",
            current_state="active", 
            status="active",
            due_date=datetime.utcnow() - timedelta(hours=1),
            organization_id="org-123"
        )
        assert instance_overdue.is_overdue is True
        
        # Completed instance with past due date (not overdue)
        instance_completed_past_due = WorkflowInstance(
            definition_id=uuid.uuid4(),
            entity_id="completed-past-due-test",
            current_state="completed",
            status="completed",
            completed_at=datetime.utcnow(),
            due_date=datetime.utcnow() - timedelta(hours=1),
            organization_id="org-123"
        )
        assert instance_completed_past_due.is_overdue is False

    def test_workflow_instance_context_operations(self):
        """Test context data operations"""
        instance = WorkflowInstance(
            definition_id=uuid.uuid4(),
            entity_id="context-test",
            current_state="draft",
            organization_id="org-123"
        )
        
        # Test with no initial context
        assert instance.get_context_value("nonexistent") is None
        assert instance.get_context_value("nonexistent", "default") == "default"
        
        # Test setting context values
        instance.set_context_value("priority", "high")
        instance.set_context_value("amount", 5000)
        
        # Test getting context values
        assert instance.get_context_value("priority") == "high"
        assert instance.get_context_value("amount") == 5000
        
        # Test context_data structure
        assert instance.context_data["priority"] == "high"
        assert instance.context_data["amount"] == 5000

    def test_workflow_instance_progress_update(self):
        """Test progress percentage update"""
        # Create mock definition for progress calculation
        mock_definition = Mock()
        mock_definition.state_list = ["draft", "review", "approved", "completed"]
        
        instance = WorkflowInstance(
            definition_id=uuid.uuid4(),
            entity_id="progress-test",
            current_state="draft",
            organization_id="org-123"
        )
        instance.definition = mock_definition
        
        # Test progress at different states
        test_cases = [
            ("draft", 0),      # First state
            ("review", 33),    # Second state (1/3 * 100)
            ("approved", 66),  # Third state (2/3 * 100)
            ("completed", 100) # Final state
        ]
        
        for state, expected_progress in test_cases:
            instance.current_state = state
            instance.update_progress()
            actual_progress = int(instance.progress_percentage)
            assert actual_progress == expected_progress


@pytest.mark.unit
class TestWorkflowHistoryModel:
    """Unit tests for WorkflowHistory model"""

    def test_workflow_history_creation(self):
        """Test creating workflow history entry"""
        instance_id = uuid.uuid4()
        
        history = WorkflowHistory(
            instance_id=instance_id,
            from_state="draft",
            to_state="review",
            action="submit",
            triggered_by="user-123",
            trigger_type="manual",
            comment="Ready for review",
            was_successful="true"
        )
        
        assert history.instance_id == instance_id
        assert history.from_state == "draft"
        assert history.to_state == "review"
        assert history.action == "submit"
        assert history.triggered_by == "user-123"
        assert history.comment == "Ready for review"

    def test_workflow_history_create_entry_method(self):
        """Test WorkflowHistory.create_entry class method"""
        instance_id = uuid.uuid4()
        
        # Test with all parameters
        history = WorkflowHistory.create_entry(
            instance_id=instance_id,
            from_state="review",
            to_state="approved",
            action="approve",
            triggered_by="user-456",
            trigger_type="manual",
            comment="Approved by manager",
            action_metadata={"approval_code": "MGR001"},
            context_snapshot={"amount": 2000, "priority": "high"},
            duration_ms="500",
            was_successful="true"
        )
        
        assert history.instance_id == instance_id
        assert history.from_state == "review"
        assert history.to_state == "approved"
        assert history.action == "approve"
        assert history.triggered_by == "user-456"
        assert history.comment == "Approved by manager"
        assert history.action_metadata["approval_code"] == "MGR001"
        assert history.context_snapshot["amount"] == 2000

    def test_workflow_history_success_detection(self):
        """Test history entry success detection"""
        # Successful entry
        success_history = WorkflowHistory(
            instance_id=uuid.uuid4(),
            to_state="completed",
            action="complete",
            triggered_by="user-123",
            was_successful="true"
        )
        assert success_history.is_successful is True
        
        # Failed entry
        failed_history = WorkflowHistory(
            instance_id=uuid.uuid4(),
            from_state="review",
            to_state="approved",
            action="approve",
            triggered_by="user-123",
            was_successful="false",
            error_message="Insufficient permissions"
        )
        assert failed_history.is_successful is False
        assert failed_history.error_message == "Insufficient permissions"

    def test_workflow_history_minimal_entry(self):
        """Test creating history with minimal required fields"""
        minimal_history = WorkflowHistory(
            instance_id=uuid.uuid4(),
            to_state="started",
            action="initialize",
            triggered_by="system"
        )
        
        assert minimal_history.to_state == "started"
        assert minimal_history.action == "initialize"
        assert minimal_history.triggered_by == "system"
        assert minimal_history.from_state is None  # Should be allowed for initial entry


@pytest.mark.unit
class TestWorkflowModelIntegration:
    """Integration tests between workflow models"""

    def test_definition_instance_relationship_simulation(self):
        """Test simulated relationship between definition and instance"""
        definition_id = uuid.uuid4()
        
        # Create definition
        definition = WorkflowDefinition(
            id=definition_id,
            name="Integration Test Workflow",
            category="test",
            initial_state="start",
            states=[
                {"name": "start"},
                {"name": "middle"},
                {"name": "end", "is_final": True}
            ],
            transitions=[
                {"from": "start", "to": "middle", "action": "proceed"},
                {"from": "middle", "to": "end", "action": "finish"}
            ],
            organization_id="org-123"
        )
        
        # Create instance using the definition
        instance = WorkflowInstance(
            definition_id=definition_id,
            entity_id="integration-test",
            current_state=definition.initial_state,
            organization_id="org-123"
        )
        
        # Verify relationship
        assert instance.definition_id == definition.id
        assert instance.current_state == definition.initial_state

    def test_instance_history_relationship_simulation(self):
        """Test simulated relationship between instance and history"""
        instance_id = uuid.uuid4()
        
        # Create instance
        instance = WorkflowInstance(
            id=instance_id,
            definition_id=uuid.uuid4(),
            entity_id="history-integration-test",
            current_state="draft",
            organization_id="org-123"
        )
        
        # Create history entries for the instance
        history_entries = [
            WorkflowHistory(
                instance_id=instance_id,
                to_state="draft",
                action="create",
                triggered_by="user-123"
            ),
            WorkflowHistory(
                instance_id=instance_id,
                from_state="draft",
                to_state="review",
                action="submit",
                triggered_by="user-123"
            ),
            WorkflowHistory(
                instance_id=instance_id,
                from_state="review", 
                to_state="approved",
                action="approve",
                triggered_by="user-456"
            )
        ]
        
        # Verify all history entries relate to the instance
        for history in history_entries:
            assert history.instance_id == instance.id

    def test_workflow_state_consistency(self):
        """Test consistency between definition states and instance state"""
        definition = WorkflowDefinition(
            name="Consistency Test",
            category="test",
            initial_state="pending",
            states=[
                {"name": "pending"},
                {"name": "processing"},
                {"name": "completed"}
            ],
            transitions=[
                {"from": "pending", "to": "processing", "action": "start"},
                {"from": "processing", "to": "completed", "action": "finish"}
            ],
            organization_id="org-123"
        )
        
        instance = WorkflowInstance(
            definition_id=uuid.uuid4(),
            entity_id="consistency-test",
            current_state="pending",  # Should match definition's initial_state
            organization_id="org-123"
        )
        
        # Verify state consistency
        assert instance.current_state in definition.state_list
        assert instance.current_state == definition.initial_state

    def test_workflow_transition_validation_with_models(self):
        """Test transition validation using actual model methods"""
        definition = WorkflowDefinition(
            name="Validation Integration Test",
            category="test", 
            initial_state="created",
            states=[
                {"name": "created"},
                {"name": "in_progress"},
                {"name": "completed"}
            ],
            transitions=[
                {"from": "created", "to": "in_progress", "action": "start_work"},
                {"from": "in_progress", "to": "completed", "action": "complete_work"}
            ],
            organization_id="org-123"
        )
        
        instance = WorkflowInstance(
            definition_id=uuid.uuid4(),
            entity_id="validation-integration-test",
            current_state="created",
            organization_id="org-123"
        )
        
        # Mock the definition relationship
        instance.definition = definition
        
        # Test transition validation through instance
        assert instance.can_transition_to("in_progress", "start_work") is True
        assert instance.can_transition_to("completed", "complete_work") is False  # Not from current state
        assert instance.can_transition_to("in_progress", "wrong_action") is False
        
        # Test available actions
        available_actions = instance.get_available_actions()
        assert "start_work" in available_actions
        assert len(available_actions) == 1  # Only one action from "created" state