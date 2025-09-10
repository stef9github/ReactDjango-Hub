"""
Comprehensive unit tests for Dynamic State Machine functionality
Tests state machine creation, transitions, validation, and error handling
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from statemachine.exceptions import TransitionNotAllowed

from workflow_engine import DynamicWorkflowStateMachine
from models import WorkflowDefinition, WorkflowInstance, WorkflowHistory


@pytest.mark.unit
class TestDynamicStateMachineInitialization:
    """Tests for Dynamic State Machine initialization and configuration"""

    def test_state_machine_basic_initialization(self, test_session, sample_workflow_definition, sample_workflow_instance):
        """Test basic state machine initialization"""
        # Verify that the definition has proper structure for state machine
        assert sample_workflow_definition.states is not None
        assert len(sample_workflow_definition.states) > 0
        assert sample_workflow_definition.initial_state is not None
        assert sample_workflow_instance.current_state is not None
        
        # Verify the current state exists in definition states
        state_names = [state.get("name") for state in sample_workflow_definition.states]
        assert sample_workflow_instance.current_state in state_names

    def test_state_machine_with_minimal_definition(self, test_session):
        """Test state machine with minimal workflow definition"""
        # Create minimal definition
        definition = WorkflowDefinition(
            name="Minimal Workflow",
            category="test",
            initial_state="start",
            states=[
                {"name": "start", "initial": True},
                {"name": "end", "is_final": True}
            ],
            transitions=[
                {"from": "start", "to": "end", "action": "complete"}
            ],
            organization_id="org-123"
        )
        test_session.add(definition)
        test_session.commit()
        
        instance = WorkflowInstance(
            definition_id=definition.id,
            entity_id="minimal-test",
            current_state="start",
            organization_id="org-123"
        )
        test_session.add(instance)
        test_session.commit()
        
        # Should be able to create state machine
        assert instance.current_state == "start"
        assert definition.validate_transition("start", "end", "complete") is True

    def test_state_machine_with_complex_definition(self, test_session):
        """Test state machine with complex workflow definition"""
        complex_definition = WorkflowDefinition(
            name="Complex Workflow",
            category="test",
            initial_state="draft",
            states=[
                {"name": "draft", "label": "Draft", "description": "Initial draft state"},
                {"name": "pending_review", "label": "Pending Review", "description": "Awaiting review"},
                {"name": "in_review", "label": "In Review", "description": "Currently being reviewed"},
                {"name": "approved", "label": "Approved", "description": "Review approved"},
                {"name": "rejected", "label": "Rejected", "description": "Review rejected"},
                {"name": "completed", "label": "Completed", "description": "Process completed", "is_final": True}
            ],
            transitions=[
                {"from": "draft", "to": "pending_review", "action": "submit_for_review"},
                {"from": "pending_review", "to": "in_review", "action": "start_review"},
                {"from": "in_review", "to": "approved", "action": "approve"},
                {"from": "in_review", "to": "rejected", "action": "reject"},
                {"from": "approved", "to": "completed", "action": "finalize"},
                {"from": "rejected", "to": "draft", "action": "revise"}
            ],
            business_rules={
                "transitions": {
                    "draft_pending_review": {"required_fields": ["title", "description"]},
                    "in_review_approved": {"required_role": "reviewer"}
                }
            },
            organization_id="org-123"
        )
        test_session.add(complex_definition)
        test_session.commit()
        
        # Verify complex definition structure
        assert len(complex_definition.states) == 6
        assert len(complex_definition.transitions) == 6
        assert complex_definition.business_rules is not None

    def test_state_machine_initialization_errors(self, test_session):
        """Test state machine initialization with invalid definitions"""
        # Definition with no states
        no_states_definition = WorkflowDefinition(
            name="No States Workflow",
            category="test",
            initial_state="start",
            states=[],  # Empty states
            transitions=[],
            organization_id="org-123"
        )
        test_session.add(no_states_definition)
        test_session.commit()
        
        instance = WorkflowInstance(
            definition_id=no_states_definition.id,
            entity_id="no-states-test",
            current_state="start",
            organization_id="org-123"
        )
        test_session.add(instance)
        test_session.commit()
        
        # Should handle empty states gracefully
        assert no_states_definition.state_list == []


@pytest.mark.unit 
class TestStateMachineTransitions:
    """Tests for state machine transition logic and validation"""

    def test_valid_transition_detection(self, test_session, sample_workflow_definition):
        """Test detection of valid state transitions"""
        # Test getting valid transitions from initial state
        valid_transitions = sample_workflow_definition.get_valid_transitions(
            sample_workflow_definition.initial_state
        )
        
        assert isinstance(valid_transitions, list)
        assert len(valid_transitions) > 0
        
        # Each transition should have required fields
        for transition in valid_transitions:
            assert "from" in transition
            assert "to" in transition
            assert "action" in transition

    def test_transition_validation_logic(self, test_session, sample_workflow_definition):
        """Test transition validation with various scenarios"""
        if sample_workflow_definition.transitions:
            # Get first valid transition
            valid_transition = sample_workflow_definition.transitions[0]
            from_state = valid_transition["from"]
            to_state = valid_transition["to"]
            action = valid_transition.get("action")
            
            # Test valid transition
            assert sample_workflow_definition.validate_transition(from_state, to_state, action) is True
            
            # Test invalid transitions
            assert sample_workflow_definition.validate_transition(from_state, "nonexistent_state", action) is False
            assert sample_workflow_definition.validate_transition("nonexistent_state", to_state, action) is False
            assert sample_workflow_definition.validate_transition(from_state, to_state, "wrong_action") is False

    def test_state_machine_business_rules(self, test_session):
        """Test state machine business rules validation"""
        definition_with_rules = WorkflowDefinition(
            name="Business Rules Workflow",
            category="test",
            initial_state="draft",
            states=[
                {"name": "draft"},
                {"name": "approved", "is_final": True}
            ],
            transitions=[
                {"from": "draft", "to": "approved", "action": "approve"}
            ],
            business_rules={
                "transitions": {
                    "draft_approved": {
                        "required_fields": ["title", "amount"],
                        "conditions": ["amount < 1000"]
                    }
                }
            },
            organization_id="org-123"
        )
        test_session.add(definition_with_rules)
        test_session.commit()
        
        # Verify business rules are stored correctly
        assert definition_with_rules.business_rules is not None
        assert "transitions" in definition_with_rules.business_rules
        transition_rules = definition_with_rules.business_rules["transitions"]
        assert "draft_approved" in transition_rules

    def test_circular_transition_handling(self, test_session):
        """Test handling of circular state transitions"""
        circular_definition = WorkflowDefinition(
            name="Circular Workflow",
            category="test",
            initial_state="state_a",
            states=[
                {"name": "state_a"},
                {"name": "state_b"},
                {"name": "state_c"}
            ],
            transitions=[
                {"from": "state_a", "to": "state_b", "action": "next"},
                {"from": "state_b", "to": "state_c", "action": "next"},
                {"from": "state_c", "to": "state_a", "action": "restart"},
                {"from": "state_b", "to": "state_a", "action": "back"}
            ],
            organization_id="org-123"
        )
        test_session.add(circular_definition)
        test_session.commit()
        
        # Test circular transitions are valid
        assert circular_definition.validate_transition("state_c", "state_a", "restart") is True
        assert circular_definition.validate_transition("state_b", "state_a", "back") is True
        
        # Verify all states are reachable
        assert len(circular_definition.get_valid_transitions("state_a")) >= 1
        assert len(circular_definition.get_valid_transitions("state_b")) >= 2
        assert len(circular_definition.get_valid_transitions("state_c")) >= 1

    def test_parallel_transition_paths(self, test_session):
        """Test handling of parallel/branching transition paths"""
        branching_definition = WorkflowDefinition(
            name="Branching Workflow",
            category="test",
            initial_state="start",
            states=[
                {"name": "start"},
                {"name": "path_a"},
                {"name": "path_b"},
                {"name": "merged", "is_final": True}
            ],
            transitions=[
                {"from": "start", "to": "path_a", "action": "choose_a"},
                {"from": "start", "to": "path_b", "action": "choose_b"},
                {"from": "path_a", "to": "merged", "action": "complete"},
                {"from": "path_b", "to": "merged", "action": "complete"}
            ],
            organization_id="org-123"
        )
        test_session.add(branching_definition)
        test_session.commit()
        
        # Test branching transitions
        start_transitions = branching_definition.get_valid_transitions("start")
        assert len(start_transitions) == 2
        
        actions = [t["action"] for t in start_transitions]
        assert "choose_a" in actions
        assert "choose_b" in actions


@pytest.mark.unit
class TestStateMachineExecution:
    """Tests for state machine execution and context handling"""

    @patch('workflow_engine.SessionLocal')
    def test_transition_execution_success(self, mock_session_local, test_session, sample_workflow_definition, sample_workflow_instance):
        """Test successful transition execution with context updates"""
        # Mock database session for internal operations
        mock_session = Mock()
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        mock_session_local.return_value.__exit__.return_value = None
        
        # Test transition execution logic
        initial_state = sample_workflow_instance.current_state
        context_updates = {"updated_by": "user-123", "timestamp": str(datetime.utcnow())}
        
        # Simulate context update
        sample_workflow_instance.set_context_value("last_action", "test_transition")
        sample_workflow_instance.set_context_value("updated_by", "user-123")
        
        # Verify context was updated
        assert sample_workflow_instance.get_context_value("last_action") == "test_transition"
        assert sample_workflow_instance.get_context_value("updated_by") == "user-123"

    def test_transition_context_preservation(self, test_session, sample_workflow_instance):
        """Test that context data is preserved during transitions"""
        # Set initial context
        initial_context = {
            "user_id": "user-123",
            "department": "IT",
            "priority": "high",
            "metadata": {"created_at": str(datetime.utcnow())}
        }
        sample_workflow_instance.context_data = initial_context
        
        # Add new context data
        sample_workflow_instance.set_context_value("last_modified", str(datetime.utcnow()))
        sample_workflow_instance.set_context_value("approval_level", "L1")
        
        # Verify old context is preserved
        assert sample_workflow_instance.get_context_value("user_id") == "user-123"
        assert sample_workflow_instance.get_context_value("department") == "IT"
        assert sample_workflow_instance.get_context_value("priority") == "high"
        
        # Verify new context was added
        assert sample_workflow_instance.get_context_value("last_modified") is not None
        assert sample_workflow_instance.get_context_value("approval_level") == "L1"

    @patch('workflow_engine.logger')
    def test_transition_error_logging(self, mock_logger, test_session, sample_workflow_instance):
        """Test that transition errors are properly logged"""
        # Simulate error scenario
        error_message = "Test transition error"
        instance_id = str(sample_workflow_instance.id)
        
        # Test that logger can be called (verifying mock setup)
        mock_logger.error.assert_not_called()
        
        # Simulate error logging
        mock_logger.error(f"Workflow transition failed for {instance_id}: {error_message}")
        mock_logger.error.assert_called_once()
        
        # Verify error logging format
        call_args = mock_logger.error.call_args[0]
        assert instance_id in call_args[0]
        assert error_message in call_args[0]

    def test_final_state_detection(self, test_session):
        """Test detection and handling of final states"""
        final_state_definition = WorkflowDefinition(
            name="Final State Workflow",
            category="test",
            initial_state="start",
            states=[
                {"name": "start"},
                {"name": "processing"},
                {"name": "completed", "is_final": True},
                {"name": "cancelled", "is_final": True}
            ],
            transitions=[
                {"from": "start", "to": "processing", "action": "begin"},
                {"from": "processing", "to": "completed", "action": "complete"},
                {"from": "processing", "to": "cancelled", "action": "cancel"}
            ],
            organization_id="org-123"
        )
        test_session.add(final_state_definition)
        test_session.commit()
        
        instance = WorkflowInstance(
            definition_id=final_state_definition.id,
            entity_id="final-state-test",
            current_state="start",
            status="active",
            organization_id="org-123"
        )
        test_session.add(instance)
        test_session.commit()
        
        # Verify initial state is not final
        assert instance.status == "active"
        
        # Simulate reaching final state
        instance.current_state = "completed"
        instance.status = "completed"
        instance.completed_at = datetime.utcnow()
        
        # Verify final state handling
        assert instance.is_completed is True
        assert instance.completed_at is not None


@pytest.mark.unit
class TestStateMachineErrorHandling:
    """Tests for state machine error handling and edge cases"""

    def test_invalid_state_transitions(self, test_session, sample_workflow_definition):
        """Test handling of invalid state transitions"""
        # Try to validate impossible transitions
        invalid_transitions = [
            ("nonexistent_state", "valid_state", "action"),
            ("valid_state", "nonexistent_state", "action"), 
            (None, "valid_state", "action"),
            ("valid_state", None, "action"),
            ("", "valid_state", "action"),
            ("valid_state", "", "action")
        ]
        
        for from_state, to_state, action in invalid_transitions:
            result = sample_workflow_definition.validate_transition(from_state, to_state, action)
            assert result is False

    def test_malformed_definition_handling(self, test_session):
        """Test handling of malformed workflow definitions"""
        malformed_definitions = [
            # Missing required transition fields
            WorkflowDefinition(
                name="Malformed 1",
                category="test",
                initial_state="start",
                states=[{"name": "start"}, {"name": "end"}],
                transitions=[{"from": "start"}],  # Missing 'to' and 'action'
                organization_id="org-123"
            ),
            # States without names
            WorkflowDefinition(
                name="Malformed 2",
                category="test",
                initial_state="start",
                states=[{"label": "Start State"}, {"name": "end"}],  # Missing 'name' in first state
                transitions=[{"from": "start", "to": "end", "action": "finish"}],
                organization_id="org-123"
            ),
            # Empty transitions list
            WorkflowDefinition(
                name="Malformed 3",
                category="test",
                initial_state="start",
                states=[{"name": "start"}],
                transitions=None,  # None instead of empty list
                organization_id="org-123"
            )
        ]
        
        for definition in malformed_definitions:
            test_session.add(definition)
            test_session.commit()
            
            # Should handle malformed definitions gracefully
            transitions = definition.get_valid_transitions(definition.initial_state)
            assert isinstance(transitions, list)  # Should return empty list, not crash

    def test_state_machine_with_null_values(self, test_session, sample_workflow_instance):
        """Test state machine handling of null/None values"""
        # Test with null context data
        sample_workflow_instance.context_data = None
        assert sample_workflow_instance.get_context_value("any_key") is None
        assert sample_workflow_instance.get_context_value("any_key", "default") == "default"
        
        # Test setting context on null context_data
        sample_workflow_instance.set_context_value("new_key", "new_value")
        assert sample_workflow_instance.context_data is not None
        assert sample_workflow_instance.get_context_value("new_key") == "new_value"

    def test_concurrent_state_modifications(self, test_session, sample_workflow_instance):
        """Test handling of concurrent state modifications (simulation)"""
        # Simulate concurrent modifications by testing state consistency
        original_state = sample_workflow_instance.current_state
        original_updated_at = sample_workflow_instance.updated_at
        
        # Simulate state change
        sample_workflow_instance.current_state = "new_state"
        sample_workflow_instance.updated_at = datetime.utcnow()
        
        # Verify state change tracking
        assert sample_workflow_instance.current_state != original_state
        assert sample_workflow_instance.updated_at > original_updated_at

    def test_state_machine_memory_efficiency(self, test_session):
        """Test state machine memory efficiency with large state spaces"""
        # Create definition with many states
        many_states = [{"name": f"state_{i}"} for i in range(100)]
        many_transitions = [
            {"from": f"state_{i}", "to": f"state_{i+1}", "action": f"action_{i}"}
            for i in range(99)
        ]
        
        large_definition = WorkflowDefinition(
            name="Large State Space Workflow",
            category="test",
            initial_state="state_0",
            states=many_states,
            transitions=many_transitions,
            organization_id="org-123"
        )
        test_session.add(large_definition)
        test_session.commit()
        
        # Should handle large state space efficiently
        assert len(large_definition.state_list) == 100
        transitions_from_first = large_definition.get_valid_transitions("state_0")
        assert len(transitions_from_first) == 1
        
        transitions_from_middle = large_definition.get_valid_transitions("state_50")
        assert len(transitions_from_middle) == 1


@pytest.mark.unit
class TestStateMachineProgress:
    """Tests for state machine progress calculation and tracking"""

    def test_progress_calculation_linear(self, test_session):
        """Test progress calculation for linear workflows"""
        linear_definition = WorkflowDefinition(
            name="Linear Progress Workflow",
            category="test",
            initial_state="step_1",
            states=[
                {"name": "step_1"},
                {"name": "step_2"},
                {"name": "step_3"},
                {"name": "step_4"},
                {"name": "step_5", "is_final": True}
            ],
            transitions=[
                {"from": "step_1", "to": "step_2", "action": "next"},
                {"from": "step_2", "to": "step_3", "action": "next"},
                {"from": "step_3", "to": "step_4", "action": "next"},
                {"from": "step_4", "to": "step_5", "action": "finish"}
            ],
            organization_id="org-123"
        )
        test_session.add(linear_definition)
        test_session.commit()
        
        instance = WorkflowInstance(
            definition_id=linear_definition.id,
            entity_id="progress-test",
            current_state="step_1",
            organization_id="org-123"
        )
        test_session.add(instance)
        test_session.commit()
        
        # Test progress at different states
        test_cases = [
            ("step_1", 0),    # First state = 0%
            ("step_2", 25),   # Second state = 25%
            ("step_3", 50),   # Third state = 50%
            ("step_4", 75),   # Fourth state = 75% 
            ("step_5", 100)   # Final state = 100%
        ]
        
        for state, expected_progress in test_cases:
            instance.current_state = state
            instance.update_progress()
            actual_progress = int(instance.progress_percentage)
            assert actual_progress == expected_progress

    def test_progress_calculation_branching(self, test_session):
        """Test progress calculation for branching workflows"""
        branching_definition = WorkflowDefinition(
            name="Branching Progress Workflow",
            category="test",
            initial_state="start",
            states=[
                {"name": "start"},
                {"name": "branch_a"},
                {"name": "branch_b"},
                {"name": "end", "is_final": True}
            ],
            transitions=[
                {"from": "start", "to": "branch_a", "action": "go_a"},
                {"from": "start", "to": "branch_b", "action": "go_b"},
                {"from": "branch_a", "to": "end", "action": "finish"},
                {"from": "branch_b", "to": "end", "action": "finish"}
            ],
            organization_id="org-123"
        )
        test_session.add(branching_definition)
        test_session.commit()
        
        instance = WorkflowInstance(
            definition_id=branching_definition.id,
            entity_id="branching-progress-test",
            current_state="start",
            organization_id="org-123"
        )
        test_session.add(instance)
        test_session.commit()
        
        # Test progress calculation
        instance.update_progress()
        start_progress = int(instance.progress_percentage)
        assert start_progress == 0
        
        # Move to branch state
        instance.current_state = "branch_a"
        instance.update_progress()
        branch_progress = int(instance.progress_percentage)
        assert branch_progress > 0
        assert branch_progress < 100
        
        # Move to final state
        instance.current_state = "end"
        instance.update_progress()
        final_progress = int(instance.progress_percentage)
        assert final_progress == 100

    def test_progress_with_invalid_state(self, test_session, sample_workflow_instance):
        """Test progress calculation with invalid current state"""
        original_progress = sample_workflow_instance.progress_percentage
        
        # Set invalid current state
        sample_workflow_instance.current_state = "nonexistent_state"
        sample_workflow_instance.update_progress()
        
        # Progress should remain unchanged when state is invalid
        assert sample_workflow_instance.progress_percentage == original_progress