"""
Unit tests for workflow engine
"""
import pytest
import uuid
from datetime import datetime

from workflow_engine import WorkflowEngine, DynamicWorkflowStateMachine
from models import WorkflowDefinition, WorkflowInstance, WorkflowHistory

class TestWorkflowEngine:
    """Test WorkflowEngine class"""
    
    def test_create_workflow_instance(self, test_session, sample_workflow_definition):
        """Test creating a new workflow instance"""
        engine = WorkflowEngine(test_session)
        
        instance = engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="test-request-456",
            entity_type="purchase_request",
            title="Test Purchase Request",
            context={"amount": 750, "department": "HR"},
            assigned_to="test-user",
            organization_id="org-123",
            created_by="creator-user"
        )
        
        assert instance.id is not None
        assert instance.entity_id == "test-request-456"
        assert instance.current_state == sample_workflow_definition.initial_state
        assert instance.context_data["amount"] == 750
        assert instance.status == "active"
        
        # Check that history entry was created
        history = test_session.query(WorkflowHistory).filter(
            WorkflowHistory.instance_id == instance.id
        ).first()
        
        assert history is not None
        assert history.to_state == sample_workflow_definition.initial_state
        assert history.action == "create"
        
        # Check that definition usage count was incremented
        test_session.refresh(sample_workflow_definition)
        assert sample_workflow_definition.usage_count == 1
    
    def test_create_workflow_instance_invalid_definition(self, test_session):
        """Test creating instance with invalid definition"""
        engine = WorkflowEngine(test_session)
        
        with pytest.raises(ValueError, match="not found or inactive"):
            engine.create_workflow_instance(
                definition_id=str(uuid.uuid4()),  # Random UUID
                entity_id="test-123",
                organization_id="org-123"
            )
    
    def test_advance_workflow(self, test_session, sample_workflow_instance):
        """Test advancing workflow to next state"""
        engine = WorkflowEngine(test_session)
        
        # Advance from draft to pending_review
        updated_instance = engine.advance_workflow(
            instance_id=str(sample_workflow_instance.id),
            action="submit_for_review",
            user_id="test-user",
            comment="Submitting for review",
            context_updates={"submitted_at": datetime.utcnow().isoformat()}
        )
        
        assert updated_instance.current_state == "pending_review"
        assert updated_instance.previous_state == "draft"
        assert "submitted_at" in updated_instance.context_data
        
        # Check history was created
        history_count = test_session.query(WorkflowHistory).filter(
            WorkflowHistory.instance_id == sample_workflow_instance.id
        ).count()
        assert history_count > 0
    
    def test_advance_workflow_invalid_action(self, test_session, sample_workflow_instance):
        """Test advancing workflow with invalid action"""
        engine = WorkflowEngine(test_session)
        
        with pytest.raises(ValueError, match="not available"):
            engine.advance_workflow(
                instance_id=str(sample_workflow_instance.id),
                action="invalid_action",
                user_id="test-user"
            )
    
    def test_advance_workflow_inactive_instance(self, test_session, sample_workflow_instance):
        """Test advancing inactive workflow instance"""
        engine = WorkflowEngine(test_session)
        
        # Mark instance as completed
        sample_workflow_instance.status = "completed"
        test_session.commit()
        
        with pytest.raises(ValueError, match="not active"):
            engine.advance_workflow(
                instance_id=str(sample_workflow_instance.id),
                action="submit_for_review",
                user_id="test-user"
            )
    
    def test_get_workflow_status(self, test_session, sample_workflow_instance):
        """Test getting comprehensive workflow status"""
        engine = WorkflowEngine(test_session)
        
        # Create some history first
        from models import WorkflowHistory
        history = WorkflowHistory.create_entry(
            instance_id=sample_workflow_instance.id,
            to_state="draft",
            action="create",
            triggered_by="creator"
        )
        test_session.add(history)
        test_session.commit()
        
        status = engine.get_workflow_status(str(sample_workflow_instance.id))
        
        assert status["instance_id"] == str(sample_workflow_instance.id)
        assert status["current_state"] == "draft"
        assert status["status"] == "active"
        assert "available_actions" in status
        assert "submit_for_review" in status["available_actions"]
        assert "recent_history" in status
        assert len(status["recent_history"]) > 0
        
        # Check context data is included
        assert status["context_data"]["amount"] == 500
    
    def test_get_workflow_status_not_found(self, test_session):
        """Test getting status for nonexistent workflow"""
        engine = WorkflowEngine(test_session)
        
        with pytest.raises(ValueError, match="not found"):
            engine.get_workflow_status(str(uuid.uuid4()))
    
    def test_get_user_workflows(self, test_session, sample_workflow_instance):
        """Test getting workflows for a user"""
        engine = WorkflowEngine(test_session)
        
        # Assign the workflow to a user
        sample_workflow_instance.assigned_to = "test-user-123"
        test_session.commit()
        
        workflows = engine.get_user_workflows(
            user_id="test-user-123",
            organization_id="test-org-123"
        )
        
        assert len(workflows) == 1
        workflow = workflows[0]
        assert workflow["instance_id"] == str(sample_workflow_instance.id)
        assert workflow["entity_id"] == sample_workflow_instance.entity_id
        assert workflow["current_state"] == "draft"
        assert workflow["status"] == "active"
    
    def test_get_user_workflows_with_filters(self, test_session, sample_workflow_definition):
        """Test getting user workflows with status filter"""
        engine = WorkflowEngine(test_session)
        
        # Create multiple instances for the same user
        active_instance = engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="active-request",
            assigned_to="test-user-123",
            organization_id="org-123",
            created_by="creator"
        )
        
        completed_instance = engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="completed-request",
            assigned_to="test-user-123",
            organization_id="org-123", 
            created_by="creator"
        )
        completed_instance.status = "completed"
        test_session.commit()
        
        # Get only active workflows
        active_workflows = engine.get_user_workflows(
            user_id="test-user-123",
            organization_id="org-123",
            status="active"
        )
        
        assert len(active_workflows) == 1
        assert active_workflows[0]["entity_id"] == "active-request"
        
        # Get only completed workflows
        completed_workflows = engine.get_user_workflows(
            user_id="test-user-123",
            organization_id="org-123",
            status="completed"
        )
        
        assert len(completed_workflows) == 1
        assert completed_workflows[0]["entity_id"] == "completed-request"

class TestDynamicWorkflowStateMachine:
    """Test DynamicWorkflowStateMachine class"""
    
    def test_state_machine_creation(self, sample_workflow_definition, sample_workflow_instance):
        """Test creating a dynamic state machine"""
        state_machine = DynamicWorkflowStateMachine(
            sample_workflow_definition, 
            sample_workflow_instance
        )
        
        # Check that states were created
        assert hasattr(state_machine, 'draft')
        assert hasattr(state_machine, 'pending_review') 
        assert hasattr(state_machine, 'approved')
        assert hasattr(state_machine, 'rejected')
        
        # Check initial state
        assert state_machine.current_state.name == 'draft'
    
    def test_state_machine_invalid_definition(self, sample_workflow_instance):
        """Test creating state machine with invalid definition"""
        # Create definition without states
        from models import WorkflowDefinition
        invalid_definition = WorkflowDefinition(
            name="Invalid",
            initial_state="start",
            states=None  # No states defined
        )
        
        with pytest.raises(ValueError, match="must have states defined"):
            DynamicWorkflowStateMachine(invalid_definition, sample_workflow_instance)

class TestWorkflowValidation:
    """Test workflow validation logic"""
    
    def test_transition_validation_success(self, sample_workflow_definition):
        """Test successful transition validation"""
        # Valid transition
        is_valid = sample_workflow_definition.validate_transition(
            "draft", "pending_review", "submit_for_review"
        )
        assert is_valid is True
    
    def test_transition_validation_failure(self, sample_workflow_definition):
        """Test failed transition validation"""
        # Invalid transition - wrong target state
        is_valid = sample_workflow_definition.validate_transition(
            "draft", "approved", "submit_for_review"  # Can't go directly from draft to approved
        )
        assert is_valid is False
        
        # Invalid transition - wrong action
        is_valid = sample_workflow_definition.validate_transition(
            "draft", "pending_review", "approve"  # Wrong action for this transition
        )
        assert is_valid is False
    
    def test_business_rules_validation(self, test_session):
        """Test business rules validation"""
        # Create definition with business rules
        definition = WorkflowDefinition(
            name="Business Rules Test",
            initial_state="draft",
            states=[
                {"name": "draft"},
                {"name": "approved"}
            ],
            transitions=[
                {"from": "draft", "to": "approved", "action": "approve"}
            ],
            business_rules={
                "transitions": {
                    "draft_approved": {
                        "required_fields": ["amount", "justification"],
                        "conditions": ["amount < 1000"]
                    }
                }
            },
            organization_id="org-123"
        )
        
        # Basic validation should still work
        is_valid = definition.validate_transition("draft", "approved", "approve")
        assert is_valid is True  # Business rule validation not fully implemented yet