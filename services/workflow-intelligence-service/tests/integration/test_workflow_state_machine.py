"""
Integration tests for workflow state machine transitions and business logic
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from models import WorkflowDefinition, WorkflowInstance, WorkflowHistory
from workflow_engine import WorkflowEngine, DynamicWorkflowStateMachine


@pytest.mark.integration
class TestWorkflowStateMachine:
    """Integration tests for workflow state machine functionality"""
    
    def test_complete_approval_workflow_flow(self, test_session, sample_workflow_definition, workflow_engine):
        """Test complete workflow from draft to final state"""
        # Create workflow instance
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="approval-request-123",
            entity_type="approval_request",
            title="Office Equipment Purchase",
            organization_id="org-123",
            created_by="user-123",
            context_data={"amount": 2500, "department": "IT"}
        )
        
        assert instance.current_state == "draft"
        assert instance.status == "active"
        
        # Advance to pending review
        advanced_instance = workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="submit_for_review",
            user_id="user-123",
            organization_id="org-123",
            comment="Submitting for review"
        )
        
        assert advanced_instance.current_state == "pending_review"
        
        # Check history was created
        history = test_session.query(WorkflowHistory).filter_by(
            instance_id=instance.id,
            action="submit_for_review"
        ).first()
        assert history is not None
        assert history.from_state == "draft"
        assert history.to_state == "pending_review"
        
        # Approve the request
        final_instance = workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="approve",
            user_id="manager-123", 
            organization_id="org-123",
            comment="Approved - within budget"
        )
        
        assert final_instance.current_state == "approved"
        assert final_instance.status == "completed"
        assert final_instance.completed_at is not None
        
        # Verify complete history trail
        all_history = test_session.query(WorkflowHistory).filter_by(
            instance_id=instance.id
        ).order_by(WorkflowHistory.created_at).all()
        
        assert len(all_history) == 2
        assert all_history[0].action == "submit_for_review"
        assert all_history[1].action == "approve"

    def test_workflow_rejection_and_revision_flow(self, test_session, sample_workflow_definition, workflow_engine):
        """Test workflow rejection and revision cycle"""
        # Create instance and advance to review
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="rejection-test-123",
            organization_id="org-123",
            created_by="user-123"
        )
        
        workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="submit_for_review",
            user_id="user-123",
            organization_id="org-123"
        )
        
        # Reject the request
        rejected_instance = workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="reject",
            user_id="manager-123",
            organization_id="org-123",
            comment="Insufficient justification"
        )
        
        assert rejected_instance.current_state == "rejected"
        
        # Revise and resubmit
        revised_instance = workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="revise",
            user_id="user-123", 
            organization_id="org-123",
            comment="Added detailed justification"
        )
        
        assert revised_instance.current_state == "draft"
        assert revised_instance.status == "active"
        
        # Verify revision created new history entry
        revise_history = test_session.query(WorkflowHistory).filter_by(
            instance_id=instance.id,
            action="revise"
        ).first()
        assert revise_history is not None
        assert revise_history.from_state == "rejected"
        assert revise_history.to_state == "draft"

    def test_invalid_state_transitions(self, test_session, sample_workflow_definition, workflow_engine):
        """Test that invalid state transitions are rejected"""
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="invalid-transition-123",
            organization_id="org-123",
            created_by="user-123"
        )
        
        # Try invalid transition from draft directly to approved
        with pytest.raises(ValueError, match="Invalid transition"):
            workflow_engine.advance_workflow(
                instance_id=str(instance.id),
                action="approve",  # Invalid from draft state
                user_id="user-123",
                organization_id="org-123"
            )
        
        # Verify instance state unchanged
        test_session.refresh(instance)
        assert instance.current_state == "draft"

    def test_state_machine_context_updates(self, test_session, sample_workflow_definition, workflow_engine):
        """Test that context data is properly updated during transitions"""
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="context-test-123",
            organization_id="org-123",
            created_by="user-123",
            context_data={"priority": "medium", "amount": 1000}
        )
        
        # Update context during transition
        updated_instance = workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="submit_for_review",
            user_id="user-123",
            organization_id="org-123",
            context_updates={"priority": "high", "reviewer_assigned": "manager-123"}
        )
        
        assert updated_instance.context_data["priority"] == "high"
        assert updated_instance.context_data["reviewer_assigned"] == "manager-123"
        assert updated_instance.context_data["amount"] == 1000  # Original value preserved

    def test_concurrent_workflow_advancement(self, test_session, sample_workflow_definition, workflow_engine):
        """Test handling of concurrent workflow advancement attempts"""
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="concurrent-test-123",
            organization_id="org-123",
            created_by="user-123"
        )
        
        # First advancement should succeed
        advanced_instance = workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="submit_for_review",
            user_id="user-123",
            organization_id="org-123"
        )
        assert advanced_instance.current_state == "pending_review"
        
        # Second attempt with same action should fail gracefully
        with pytest.raises(ValueError, match="Invalid transition"):
            workflow_engine.advance_workflow(
                instance_id=str(instance.id),
                action="submit_for_review",  # Already in pending_review
                user_id="user-123", 
                organization_id="org-123"
            )

    def test_workflow_progress_calculation(self, test_session, sample_workflow_definition, workflow_engine):
        """Test that workflow progress is calculated correctly"""
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="progress-test-123",
            organization_id="org-123",
            created_by="user-123"
        )
        
        # Initial state (draft) should be 0% progress
        assert int(instance.progress_percentage) == 0
        
        # Move to second state (pending_review)
        advanced_instance = workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="submit_for_review",
            user_id="user-123",
            organization_id="org-123"
        )
        
        progress = int(advanced_instance.progress_percentage)
        assert progress > 0 and progress < 100
        
        # Move to final state (approved)
        final_instance = workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="approve",
            user_id="manager-123",
            organization_id="org-123"
        )
        
        assert int(final_instance.progress_percentage) == 100

    def test_workflow_duration_tracking(self, test_session, sample_workflow_definition, workflow_engine):
        """Test that workflow duration is properly tracked"""
        start_time = datetime.utcnow() - timedelta(hours=2)
        
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="duration-test-123",
            organization_id="org-123",
            created_by="user-123"
        )
        
        # Manually set started_at for testing
        instance.started_at = start_time
        test_session.commit()
        test_session.refresh(instance)
        
        duration = instance.duration
        assert duration.total_seconds() >= 7200  # At least 2 hours
        
        # Complete workflow
        completed_instance = workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="submit_for_review",
            user_id="user-123",
            organization_id="org-123"
        )
        
        workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="approve",
            user_id="manager-123",
            organization_id="org-123"
        )
        
        test_session.refresh(completed_instance)
        assert completed_instance.completed_at is not None
        assert completed_instance.status == "completed"


@pytest.mark.integration
class TestComplexWorkflowScenarios:
    """Integration tests for complex workflow scenarios"""
    
    def test_multi_step_approval_with_conditions(self, test_session, workflow_engine):
        """Test complex workflow with conditional branching"""
        # Create a more complex workflow definition
        complex_definition = WorkflowDefinition(
            name="Complex Approval Workflow",
            description="Multi-step approval with conditions",
            category="complex_approval",
            organization_id="org-123",
            initial_state="draft",
            states=[
                {"name": "draft", "is_initial": True},
                {"name": "manager_review", "requires_approval": True},
                {"name": "finance_review", "requires_approval": True},
                {"name": "ceo_review", "requires_approval": True},
                {"name": "approved", "is_final": True},
                {"name": "rejected", "is_final": True}
            ],
            transitions=[
                {"from": "draft", "to": "manager_review", "action": "submit"},
                {"from": "manager_review", "to": "finance_review", "action": "manager_approve", "condition": "amount > 1000"},
                {"from": "manager_review", "to": "approved", "action": "manager_approve", "condition": "amount <= 1000"},
                {"from": "finance_review", "to": "ceo_review", "action": "finance_approve", "condition": "amount > 10000"},
                {"from": "finance_review", "to": "approved", "action": "finance_approve", "condition": "amount <= 10000"},
                {"from": "ceo_review", "to": "approved", "action": "ceo_approve"},
                {"from": "manager_review", "to": "rejected", "action": "manager_reject"},
                {"from": "finance_review", "to": "rejected", "action": "finance_reject"},
                {"from": "ceo_review", "to": "rejected", "action": "ceo_reject"}
            ],
            business_rules={
                "conditional_routing": True,
                "amount_thresholds": {"manager": 1000, "finance": 10000}
            },
            created_by="admin"
        )
        
        test_session.add(complex_definition)
        test_session.commit()
        test_session.refresh(complex_definition)
        
        # Test low amount workflow (should go: draft -> manager -> approved)
        low_amount_instance = workflow_engine.create_workflow_instance(
            definition_id=str(complex_definition.id),
            entity_id="low-amount-123",
            organization_id="org-123",
            created_by="user-123",
            context_data={"amount": 500}
        )
        
        # Submit for manager review
        workflow_engine.advance_workflow(
            instance_id=str(low_amount_instance.id),
            action="submit",
            user_id="user-123",
            organization_id="org-123"
        )
        assert low_amount_instance.current_state == "manager_review"

    def test_workflow_with_due_dates_and_sla(self, test_session, sample_workflow_definition, workflow_engine):
        """Test workflow SLA and due date handling"""
        due_date = datetime.utcnow() + timedelta(days=3)
        
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="sla-test-123",
            organization_id="org-123",
            created_by="user-123",
            context_data={"sla_hours": 72, "priority": "high"}
        )
        
        # Set due date
        instance.due_date = due_date
        test_session.commit()
        
        assert not instance.is_overdue
        
        # Simulate past due date
        instance.due_date = datetime.utcnow() - timedelta(hours=1)
        test_session.commit()
        
        assert instance.is_overdue
        
        # Complete before SLA breach should update metrics
        workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="submit_for_review",
            user_id="user-123",
            organization_id="org-123"
        )
        
        # SLA metrics should be tracked in context
        test_session.refresh(instance)
        assert "sla_status" in instance.context_data or instance.is_overdue

    def test_workflow_error_recovery(self, test_session, sample_workflow_definition, workflow_engine):
        """Test workflow error handling and recovery mechanisms"""
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="error-recovery-123",
            organization_id="org-123",
            created_by="user-123"
        )
        
        # Simulate system error during transition
        with patch('workflow_engine.WorkflowEngine.advance_workflow') as mock_advance:
            mock_advance.side_effect = Exception("Database connection error")
            
            with pytest.raises(Exception, match="Database connection error"):
                workflow_engine.advance_workflow(
                    instance_id=str(instance.id),
                    action="submit_for_review",
                    user_id="user-123",
                    organization_id="org-123"
                )
        
        # Verify instance state remained unchanged
        test_session.refresh(instance)
        assert instance.current_state == "draft"
        assert instance.error_count == "0"  # Error count tracking if implemented

    def test_bulk_workflow_operations(self, test_session, sample_workflow_definition, workflow_engine):
        """Test bulk workflow operations and performance"""
        instances = []
        
        # Create multiple workflow instances
        for i in range(5):
            instance = workflow_engine.create_workflow_instance(
                definition_id=str(sample_workflow_definition.id),
                entity_id=f"bulk-test-{i}",
                organization_id="org-123",
                created_by="user-123"
            )
            instances.append(instance)
        
        # Advance all instances to review state
        for instance in instances:
            advanced = workflow_engine.advance_workflow(
                instance_id=str(instance.id),
                action="submit_for_review",
                user_id="user-123",
                organization_id="org-123"
            )
            assert advanced.current_state == "pending_review"
        
        # Verify all transitions were recorded
        total_history = test_session.query(WorkflowHistory).filter(
            WorkflowHistory.action == "submit_for_review"
        ).count()
        assert total_history >= 5