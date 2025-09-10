#!/usr/bin/env python3
"""
Simple standalone test for workflow models without pytest infrastructure
This provides a quick way to verify our core model functionality
"""
import uuid
from datetime import datetime, timedelta

# Import models directly
from models.workflow_definition import WorkflowDefinition
from models.workflow_instance import WorkflowInstance
from models.workflow_history import WorkflowHistory


def test_workflow_definition():
    """Test WorkflowDefinition model functionality"""
    print("Testing WorkflowDefinition...")
    
    definition = WorkflowDefinition(
        name="Test Workflow",
        description="A test workflow",
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
    assert definition.initial_state == "draft"
    assert len(definition.states) == 3
    assert len(definition.transitions) == 3
    
    # Test state list
    state_list = definition.state_list
    assert state_list == ["draft", "review", "approved"]
    
    # Test state config
    draft_config = definition.get_state_config("draft")
    assert draft_config["label"] == "Draft"
    
    # Test transitions
    draft_transitions = definition.get_valid_transitions("draft")
    assert len(draft_transitions) == 1
    assert draft_transitions[0]["action"] == "submit"
    
    # Test validation
    assert definition.validate_transition("draft", "review", "submit") is True
    assert definition.validate_transition("draft", "approved", "submit") is False
    
    print("✓ WorkflowDefinition tests passed")


def test_workflow_instance():
    """Test WorkflowInstance model functionality"""
    print("Testing WorkflowInstance...")
    
    instance = WorkflowInstance(
        definition_id=uuid.uuid4(),
        entity_id="test-entity-123",
        entity_type="purchase_request",
        title="Test Purchase Request",
        current_state="draft",
        status="active",  # Explicitly set status
        context_data={"amount": 1000, "department": "IT"},
        assigned_to="user-123",
        organization_id="org-456",
        started_at=datetime.utcnow() - timedelta(hours=2)
    )
    
    # Test basic properties
    assert instance.entity_id == "test-entity-123"
    assert instance.entity_type == "purchase_request"
    assert instance.current_state == "draft"
    assert instance.context_data["amount"] == 1000
    
    # Test computed properties
    assert instance.is_active is True
    assert instance.is_completed is False
    
    # Test duration
    duration = instance.duration
    assert duration.total_seconds() > 7000  # More than 2 hours
    
    # Test context operations
    assert instance.get_context_value("amount") == 1000
    assert instance.get_context_value("nonexistent", "default") == "default"
    
    instance.set_context_value("priority", "high")
    assert instance.get_context_value("priority") == "high"
    
    # Test overdue detection
    assert instance.is_overdue is False  # No due date
    
    instance.due_date = datetime.utcnow() - timedelta(hours=1)
    assert instance.is_overdue is True  # Past due date
    
    print("✓ WorkflowInstance tests passed")


def test_workflow_history():
    """Test WorkflowHistory model functionality"""
    print("Testing WorkflowHistory...")
    
    instance_id = uuid.uuid4()
    
    # Test basic creation
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
    assert history.is_successful is True
    
    # Test create_entry method
    history2 = WorkflowHistory.create_entry(
        instance_id=instance_id,
        from_state="review",
        to_state="approved",
        action="approve",
        triggered_by="user-456",
        comment="Approved by manager",
        action_metadata={"approval_code": "MGR001"},
        context_snapshot={"amount": 2000},
        was_successful="true"
    )
    
    assert history2.action_metadata["approval_code"] == "MGR001"
    assert history2.context_snapshot["amount"] == 2000
    assert history2.is_successful is True
    
    # Test failed entry
    failed_history = WorkflowHistory(
        instance_id=instance_id,
        from_state="review",
        to_state="approved",
        action="approve",
        triggered_by="user-123",
        was_successful="false",
        error_message="Insufficient permissions"
    )
    
    assert failed_history.is_successful is False
    assert failed_history.error_message == "Insufficient permissions"
    
    print("✓ WorkflowHistory tests passed")


def test_model_integration():
    """Test integration between models"""
    print("Testing model integration...")
    
    definition_id = uuid.uuid4()
    instance_id = uuid.uuid4()
    
    # Create definition
    definition = WorkflowDefinition(
        id=definition_id,
        name="Integration Test",
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
    
    # Create instance
    instance = WorkflowInstance(
        id=instance_id,
        definition_id=definition_id,
        entity_id="integration-test",
        current_state=definition.initial_state,
        organization_id="org-123"
    )
    
    # Mock definition relationship for testing
    instance.definition = definition
    
    # Test consistency
    assert instance.definition_id == definition.id
    assert instance.current_state == definition.initial_state
    assert instance.current_state in definition.state_list
    
    # Test transition capabilities
    available_actions = instance.get_available_actions()
    assert "proceed" in available_actions
    
    assert instance.can_transition_to("middle", "proceed") is True
    assert instance.can_transition_to("end", "proceed") is False
    
    # Create history
    history = WorkflowHistory.create_entry(
        instance_id=instance_id,
        from_state="start",
        to_state="middle",
        action="proceed",
        triggered_by="user-123",
        was_successful="true"
    )
    
    assert history.instance_id == instance.id
    
    print("✓ Model integration tests passed")


def main():
    """Run all tests"""
    print("Running Workflow Model Tests")
    print("=" * 40)
    
    try:
        test_workflow_definition()
        test_workflow_instance()
        test_workflow_history()
        test_model_integration()
        
        print("\n" + "=" * 40)
        print("All tests passed successfully! ✓")
        print("\nCore model functionality verified:")
        print("- WorkflowDefinition: state management, transitions, validation")
        print("- WorkflowInstance: lifecycle, context, progress tracking")
        print("- WorkflowHistory: audit trail, success/failure tracking")
        print("- Model integration: relationships and consistency")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())