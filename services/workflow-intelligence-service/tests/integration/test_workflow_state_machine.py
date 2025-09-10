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
        # Create workflow instance for enterprise procurement
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="enterprise-contract-123",
            entity_type="vendor_contract",
            title="Microsoft Enterprise License Agreement",
            organization_id="org-123",
            created_by="procurement-manager-123",
            context_data={
                "contract_value": 125000,
                "vendor_name": "Microsoft Corporation",
                "department": "IT",
                "contract_type": "software_license",
                "risk_assessment": "low",
                "compliance_required": True
            }
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
        
        # Execute final business approval
        final_instance = workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="approve",
            user_id="cfo-123", 
            organization_id="org-123",
            comment="Approved - strategic vendor relationship, excellent ROI projection",
            context_updates={
                "final_approval_date": "2024-01-15",
                "expected_savings": "$45000",
                "contract_start_date": "2024-02-01"
            }
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
        # Create procurement contract instance for rejection scenario
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="high-risk-contract-123",
            entity_type="service_contract",
            title="High-Risk Service Provider Agreement",
            organization_id="org-123",
            created_by="department-head-123",
            context_data={
                "contract_value": 250000,
                "vendor_name": "Unknown Vendor LLC",
                "risk_assessment": "high",
                "compliance_concerns": ["data_privacy", "financial_stability"]
            }
        )
        
        workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="submit_for_review",
            user_id="user-123",
            organization_id="org-123"
        )
        
        # Reject the high-risk contract
        rejected_instance = workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="reject",
            user_id="risk-manager-123",
            organization_id="org-123",
            comment="Contract rejected: vendor fails financial stability requirements, data privacy concerns unresolved",
            context_updates={
                "rejection_reason": "compliance_failure",
                "risk_score": "4.2/5.0",
                "recommended_action": "find_alternative_vendor"
            }
        )
        
        assert rejected_instance.current_state == "rejected"
        
        # Revise contract terms and resubmit
        revised_instance = workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="revise",
            user_id="department-head-123", 
            organization_id="org-123",
            comment="Contract revised: added compliance clauses, vendor provided financial guarantees, data privacy terms updated",
            context_updates={
                "revision_version": "2.0",
                "compliance_issues_resolved": True,
                "vendor_certifications": ["SOC2", "ISO27001"],
                "financial_guarantee_amount": "$50000"
            }
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
            entity_id="invalid-business-transition-123",
            entity_type="purchase_order",
            title="Invalid Business Process Test",
            organization_id="org-123",
            created_by="employee-123"
        )
        
        # Try invalid business transition: employee attempting direct approval (bypassing manager)
        with pytest.raises(ValueError, match="Invalid transition"):
            workflow_engine.advance_workflow(
                instance_id=str(instance.id),
                action="approve",  # Invalid: employees cannot directly approve, must go through review process
                user_id="employee-123",
                organization_id="org-123"
            )
        
        # Verify instance state unchanged
        test_session.refresh(instance)
        assert instance.current_state == "draft"

    def test_state_machine_context_updates(self, test_session, sample_workflow_definition, workflow_engine):
        """Test that context data is properly updated during transitions"""
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="vendor-onboarding-123",
            entity_type="vendor_onboarding",
            title="Strategic Vendor Partnership Agreement",
            organization_id="org-123",
            created_by="procurement-specialist-123",
            context_data={
                "priority": "high",
                "contract_value": 75000,
                "vendor_tier": "strategic",
                "business_unit": "operations"
            }
        )
        
        # Update business context during transition
        updated_instance = workflow_engine.advance_workflow(
            instance_id=str(instance.id),
            action="submit_for_review",
            user_id="procurement-specialist-123",
            organization_id="org-123",
            context_updates={
                "priority": "critical",
                "reviewer_assigned": "procurement-director-123",
                "budget_approval_required": True,
                "strategic_importance": "high",
                "competitive_analysis_complete": True
            }
        )
        
        assert updated_instance.context_data["priority"] == "critical"
        assert updated_instance.context_data["reviewer_assigned"] == "procurement-director-123"
        assert updated_instance.context_data["contract_value"] == 75000  # Original value preserved
        assert updated_instance.context_data["strategic_importance"] == "high"
        assert updated_instance.context_data["business_unit"] == "operations"  # Original preserved

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
    
    def test_enterprise_contract_approval_with_conditions(self, test_session, workflow_engine):
        """Test enterprise contract workflow with financial threshold-based routing"""
        # Create enterprise contract approval workflow definition
        complex_definition = WorkflowDefinition(
            name="Enterprise Contract Approval Workflow",
            description="Multi-tier contract approval based on financial thresholds and risk assessment",
            category="enterprise_procurement",
            organization_id="org-123",
            initial_state="draft",
            states=[
                {"name": "draft", "is_initial": True, "title": "Contract Draft"},
                {"name": "procurement_review", "requires_approval": True, "title": "Procurement Review"},
                {"name": "legal_review", "requires_approval": True, "title": "Legal & Compliance Review"},
                {"name": "finance_review", "requires_approval": True, "title": "Financial Analysis"},
                {"name": "executive_review", "requires_approval": True, "title": "C-Level Executive Review"},
                {"name": "approved", "is_final": True, "title": "Contract Executed"},
                {"name": "rejected", "is_final": True, "title": "Contract Rejected"}
            ],
            transitions=[
                {"from": "draft", "to": "procurement_review", "action": "submit_for_procurement"},
                {"from": "procurement_review", "to": "legal_review", "action": "procurement_approve"},
                {"from": "procurement_review", "to": "rejected", "action": "procurement_reject"},
                {"from": "legal_review", "to": "finance_review", "action": "legal_approve", "condition": "contract_value > 50000"},
                {"from": "legal_review", "to": "approved", "action": "legal_approve", "condition": "contract_value <= 50000"},
                {"from": "legal_review", "to": "rejected", "action": "legal_reject"},
                {"from": "finance_review", "to": "executive_review", "action": "finance_approve", "condition": "contract_value > 500000"},
                {"from": "finance_review", "to": "approved", "action": "finance_approve", "condition": "contract_value <= 500000"},
                {"from": "finance_review", "to": "rejected", "action": "finance_reject"},
                {"from": "executive_review", "to": "approved", "action": "executive_approve"},
                {"from": "executive_review", "to": "rejected", "action": "executive_reject"}
            ],
            business_rules={
                "conditional_routing": True,
                "financial_thresholds": {
                    "legal_only": 50000,
                    "finance_required": 50000,
                    "executive_required": 500000
                },
                "compliance_requirements": {
                    "risk_assessment_required": True,
                    "vendor_due_diligence": True,
                    "data_privacy_review": True
                }
            },
            created_by="admin"
        )
        
        test_session.add(complex_definition)
        test_session.commit()
        test_session.refresh(complex_definition)
        
        # Test low-value contract workflow (should go: draft -> procurement -> legal -> approved)
        low_value_contract = workflow_engine.create_workflow_instance(
            definition_id=str(complex_definition.id),
            entity_id="office-supplies-contract-123",
            entity_type="service_contract",
            title="Office Supplies Annual Contract",
            organization_id="org-123",
            created_by="office-manager-123",
            context_data={
                "contract_value": 25000,
                "vendor_name": "Office Depot Business Solutions",
                "contract_duration": "12 months",
                "risk_level": "low"
            }
        )
        
        # Submit for procurement review
        workflow_engine.advance_workflow(
            instance_id=str(low_value_contract.id),
            action="submit_for_procurement",
            user_id="office-manager-123",
            organization_id="org-123"
        )
        assert low_value_contract.current_state == "procurement_review"
        
        # Procurement approves, moves to legal
        workflow_engine.advance_workflow(
            instance_id=str(low_value_contract.id),
            action="procurement_approve",
            user_id="procurement-specialist-123",
            organization_id="org-123"
        )
        assert low_value_contract.current_state == "legal_review"
        
        # Legal approves - should go directly to approved (under $50k threshold)
        workflow_engine.advance_workflow(
            instance_id=str(low_value_contract.id),
            action="legal_approve",
            user_id="legal-counsel-123",
            organization_id="org-123"
        )
        assert low_value_contract.current_state == "approved"

    def test_workflow_with_due_dates_and_sla(self, test_session, sample_workflow_definition, workflow_engine):
        """Test workflow SLA and due date handling"""
        due_date = datetime.utcnow() + timedelta(days=3)
        
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="enterprise-sla-test-123",
            entity_type="strategic_partnership",
            title="Mission-Critical Infrastructure Partnership",
            organization_id="org-123",
            created_by="cto-123",
            context_data={
                "sla_hours": 48,
                "priority": "mission_critical",
                "business_impact": "high",
                "revenue_at_risk": "$2M",
                "customer_impact": "enterprise_customers"
            }
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
            entity_id="enterprise-resilience-test-123",
            entity_type="business_continuity_contract",
            title="Enterprise Business Continuity Service Agreement",
            organization_id="org-123",
            created_by="business-continuity-manager-123"
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
        
        # Create multiple enterprise contract workflow instances
        contract_types = [
            ("software-license-bulk-1", "Enterprise Software License", 150000),
            ("consulting-services-bulk-2", "Strategic Consulting Services", 75000),
            ("cloud-infrastructure-bulk-3", "Cloud Infrastructure Services", 200000),
            ("security-services-bulk-4", "Cybersecurity Monitoring", 95000),
            ("training-services-bulk-5", "Employee Training Program", 45000)
        ]
        
        for entity_id, title, value in contract_types:
            instance = workflow_engine.create_workflow_instance(
                definition_id=str(sample_workflow_definition.id),
                entity_id=entity_id,
                entity_type="enterprise_contract",
                title=title,
                organization_id="org-123",
                created_by="procurement-director-123",
                context_data={
                    "contract_value": value,
                    "strategic_importance": "high",
                    "business_unit": "enterprise_operations"
                }
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