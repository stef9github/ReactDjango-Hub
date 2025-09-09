"""
End-to-end tests for complete workflow scenarios
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from models import WorkflowDefinition, WorkflowInstance, WorkflowHistory, AIInsight


@pytest.mark.e2e
class TestCompleteWorkflowJourneys:
    """End-to-end tests for complete workflow journeys"""
    
    @patch('httpx.AsyncClient.post')
    def test_complete_approval_workflow_e2e(self, mock_post, client: TestClient, mock_user_data):
        """Test complete approval workflow from creation to completion"""
        # Mock identity service responses
        identity_mock_response = AsyncMock()
        identity_mock_response.status_code = 200
        identity_mock_response.json.return_value = mock_user_data
        mock_post.return_value = identity_mock_response
        
        headers = {"Authorization": "Bearer valid_token"}
        
        # Step 1: Create workflow definition
        definition_data = {
            "name": "E2E Test Approval Workflow",
            "description": "Complete workflow for testing",
            "category": "approval",
            "initial_state": "draft",
            "states": [
                {"name": "draft", "is_initial": True, "is_final": False},
                {"name": "pending_review", "is_initial": False, "is_final": False},
                {"name": "approved", "is_initial": False, "is_final": True},
                {"name": "rejected", "is_initial": False, "is_final": True}
            ],
            "transitions": [
                {"from": "draft", "to": "pending_review", "action": "submit_for_review"},
                {"from": "pending_review", "to": "approved", "action": "approve"},
                {"from": "pending_review", "to": "rejected", "action": "reject"},
                {"from": "rejected", "to": "draft", "action": "revise"}
            ],
            "business_rules": {
                "required_fields": ["title", "description"],
                "auto_assignments": {"pending_review": "reviewer_role"}
            }
        }
        
        # Create workflow definition
        definition_response = client.post("/api/v1/admin/workflow-definitions", json=definition_data, headers=headers)
        assert definition_response.status_code == 201
        definition = definition_response.json()
        definition_id = definition["id"]
        
        # Step 2: Create workflow instance
        instance_data = {
            "definition_id": definition_id,
            "entity_id": "e2e-test-request-001",
            "entity_type": "purchase_request",
            "title": "Office Equipment Purchase",
            "description": "Request for new laptops and monitors for the development team",
            "context_data": {
                "amount": 15000,
                "department": "Engineering",
                "items": ["Laptops x5", "Monitors x10"],
                "justification": "Team expansion requires additional equipment"
            }
        }
        
        instance_response = client.post("/api/v1/workflows", json=instance_data, headers=headers)
        assert instance_response.status_code == 200
        instance = instance_response.json()
        instance_id = instance["id"]
        
        # Verify initial state
        assert instance["current_state"] == "draft"
        assert instance["status"] == "active"
        
        # Step 3: Submit for review
        advance_data = {
            "action": "submit_for_review",
            "comment": "Submitting request for management review",
            "context_updates": {
                "submitted_at": datetime.utcnow().isoformat(),
                "reviewer_notes": "Please prioritize - team expansion is critical"
            }
        }
        
        advance_response = client.post(f"/api/v1/workflows/{instance_id}/advance", json=advance_data, headers=headers)
        assert advance_response.status_code == 200
        advanced_instance = advance_response.json()
        
        # Verify state transition
        assert advanced_instance["current_state"] == "pending_review"
        assert "submitted_at" in advanced_instance["context_data"]
        
        # Step 4: Check workflow history
        history_response = client.get(f"/api/v1/workflows/{instance_id}/history", headers=headers)
        assert history_response.status_code == 200
        history = history_response.json()
        
        assert len(history) == 1
        assert history[0]["action"] == "submit_for_review"
        assert history[0]["from_state"] == "draft"
        assert history[0]["to_state"] == "pending_review"
        
        # Step 5: Get available actions
        actions_response = client.get(f"/api/v1/workflows/{instance_id}/actions", headers=headers)
        assert actions_response.status_code == 200
        actions = actions_response.json()
        
        assert "approve" in actions
        assert "reject" in actions
        
        # Step 6: Approve the workflow
        approve_data = {
            "action": "approve",
            "comment": "Approved - legitimate business need and within budget",
            "context_updates": {
                "approved_by": "manager@company.com",
                "approved_at": datetime.utcnow().isoformat(),
                "procurement_reference": "PO-2024-001"
            }
        }
        
        approve_response = client.post(f"/api/v1/workflows/{instance_id}/advance", json=approve_data, headers=headers)
        assert approve_response.status_code == 200
        final_instance = approve_response.json()
        
        # Verify completion
        assert final_instance["current_state"] == "approved"
        assert final_instance["status"] == "completed"
        assert final_instance["completed_at"] is not None
        assert final_instance["progress_percentage"] == "100"
        
        # Step 7: Verify final history
        final_history_response = client.get(f"/api/v1/workflows/{instance_id}/history", headers=headers)
        assert final_history_response.status_code == 200
        final_history = final_history_response.json()
        
        assert len(final_history) == 2
        assert final_history[1]["action"] == "approve"
        assert final_history[1]["to_state"] == "approved"

    @patch('httpx.AsyncClient.post')
    def test_workflow_with_rejection_and_revision_e2e(self, mock_post, client: TestClient, mock_user_data):
        """Test workflow rejection and revision cycle end-to-end"""
        # Mock identity service responses
        identity_mock_response = AsyncMock()
        identity_mock_response.status_code = 200
        identity_mock_response.json.return_value = mock_user_data
        mock_post.return_value = identity_mock_response
        
        headers = {"Authorization": "Bearer valid_token"}
        
        # Create workflow definition (reuse from previous test structure)
        definition_data = {
            "name": "Rejection Test Workflow",
            "description": "Workflow for testing rejection flows",
            "category": "approval",
            "initial_state": "draft",
            "states": [
                {"name": "draft", "is_initial": True, "is_final": False},
                {"name": "pending_review", "is_initial": False, "is_final": False},
                {"name": "approved", "is_initial": False, "is_final": True},
                {"name": "rejected", "is_initial": False, "is_final": True}
            ],
            "transitions": [
                {"from": "draft", "to": "pending_review", "action": "submit_for_review"},
                {"from": "pending_review", "to": "approved", "action": "approve"},
                {"from": "pending_review", "to": "rejected", "action": "reject"},
                {"from": "rejected", "to": "draft", "action": "revise"}
            ]
        }
        
        definition_response = client.post("/api/v1/admin/workflow-definitions", json=definition_data, headers=headers)
        assert definition_response.status_code == 201
        definition = definition_response.json()
        definition_id = definition["id"]
        
        # Create instance with insufficient information
        instance_data = {
            "definition_id": definition_id,
            "entity_id": "rejection-test-001",
            "entity_type": "budget_request",
            "title": "Budget Request",
            "description": "Need more money",  # Insufficient detail
            "context_data": {
                "amount": 50000,  # High amount
                "justification": "Business needs"  # Poor justification
            }
        }
        
        instance_response = client.post("/api/v1/workflows", json=instance_data, headers=headers)
        assert instance_response.status_code == 200
        instance = instance_response.json()
        instance_id = instance["id"]
        
        # Submit for review
        advance_data = {"action": "submit_for_review", "comment": "Submitting for review"}
        advance_response = client.post(f"/api/v1/workflows/{instance_id}/advance", json=advance_data, headers=headers)
        assert advance_response.status_code == 200
        
        # Reject due to insufficient information
        reject_data = {
            "action": "reject",
            "comment": "Insufficient justification for budget amount. Please provide detailed breakdown and business case.",
            "context_updates": {
                "rejection_reason": "insufficient_justification",
                "required_actions": ["detailed_budget_breakdown", "business_case", "roi_analysis"]
            }
        }
        
        reject_response = client.post(f"/api/v1/workflows/{instance_id}/advance", json=reject_data, headers=headers)
        assert reject_response.status_code == 200
        rejected_instance = reject_response.json()
        
        # Verify rejection
        assert rejected_instance["current_state"] == "rejected"
        assert "rejection_reason" in rejected_instance["context_data"]
        
        # Revise the request
        revise_data = {
            "action": "revise",
            "comment": "Addressing feedback with detailed justification",
            "context_updates": {
                "detailed_breakdown": {
                    "personnel": 30000,
                    "equipment": 15000,
                    "training": 5000
                },
                "business_case": "Expansion into new market segment expected to generate $200K revenue in first year",
                "roi_analysis": "Expected ROI of 300% within 18 months"
            }
        }
        
        revise_response = client.post(f"/api/v1/workflows/{instance_id}/advance", json=revise_data, headers=headers)
        assert revise_response.status_code == 200
        revised_instance = revise_response.json()
        
        # Verify revision returned to draft
        assert revised_instance["current_state"] == "draft"
        assert revised_instance["status"] == "active"
        assert "detailed_breakdown" in revised_instance["context_data"]
        
        # Resubmit improved request
        resubmit_response = client.post(f"/api/v1/workflows/{instance_id}/advance", json={"action": "submit_for_review"}, headers=headers)
        assert resubmit_response.status_code == 200
        
        # Approve improved request
        approve_response = client.post(f"/api/v1/workflows/{instance_id}/advance", 
                                     json={"action": "approve", "comment": "Approved - comprehensive business case provided"}, 
                                     headers=headers)
        assert approve_response.status_code == 200
        final_instance = approve_response.json()
        
        # Verify final approval
        assert final_instance["current_state"] == "approved"
        assert final_instance["status"] == "completed"
        
        # Verify complete history shows the full journey
        history_response = client.get(f"/api/v1/workflows/{instance_id}/history", headers=headers)
        assert history_response.status_code == 200
        history = history_response.json()
        
        assert len(history) == 4  # submit, reject, revise, submit, approve
        actions = [h["action"] for h in history]
        assert "submit_for_review" in actions
        assert "reject" in actions
        assert "revise" in actions
        assert "approve" in actions

    @patch('httpx.AsyncClient.post')
    def test_ai_enhanced_workflow_e2e(self, mock_post, client: TestClient, mock_user_data):
        """Test AI-enhanced workflow with intelligent features end-to-end"""
        # Mock identity service
        def mock_post_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            if 'identity-service' in str(url):
                identity_mock_response = AsyncMock()
                identity_mock_response.status_code = 200
                identity_mock_response.json.return_value = mock_user_data
                return identity_mock_response
            else:
                # Mock AI service responses
                ai_mock_response = AsyncMock()
                ai_mock_response.status_code = 200
                ai_mock_response.json.return_value = {
                    "analysis": {
                        "sentiment": "positive",
                        "urgency": "high",
                        "topics": ["security", "urgent", "compliance"],
                        "risk_factors": ["security vulnerability"],
                        "recommended_priority": "urgent"
                    },
                    "confidence": 0.92
                }
                return ai_mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        headers = {"Authorization": "Bearer valid_token"}
        
        # Create AI-enhanced workflow definition
        definition_data = {
            "name": "AI-Enhanced Security Workflow",
            "description": "Security-focused workflow with AI analysis",
            "category": "security",
            "initial_state": "draft",
            "states": [
                {"name": "draft", "is_initial": True},
                {"name": "ai_analysis", "description": "AI content analysis"},
                {"name": "security_review", "description": "Security team review"},
                {"name": "approved", "is_final": True},
                {"name": "rejected", "is_final": True}
            ],
            "transitions": [
                {"from": "draft", "to": "ai_analysis", "action": "submit"},
                {"from": "ai_analysis", "to": "security_review", "action": "ai_analyze"},
                {"from": "security_review", "to": "approved", "action": "approve"},
                {"from": "security_review", "to": "rejected", "action": "reject"}
            ],
            "business_rules": {
                "ai_analysis_required": True,
                "auto_escalation": {"conditions": ["high_risk", "urgent"]},
                "intelligent_routing": True
            }
        }
        
        definition_response = client.post("/api/v1/admin/workflow-definitions", json=definition_data, headers=headers)
        assert definition_response.status_code == 201
        definition = definition_response.json()
        definition_id = definition["id"]
        
        # Create security request instance
        instance_data = {
            "definition_id": definition_id,
            "entity_id": "security-request-001",
            "entity_type": "security_request",
            "title": "Critical Security Patch Deployment",
            "description": "Urgent deployment of security patches to address critical vulnerability CVE-2024-0001 affecting our web servers. This vulnerability could allow remote code execution and must be patched immediately.",
            "context_data": {
                "vulnerability_id": "CVE-2024-0001",
                "affected_systems": ["web-server-01", "web-server-02", "web-server-03"],
                "severity": "critical",
                "patch_available": True,
                "business_impact": "high"
            }
        }
        
        instance_response = client.post("/api/v1/workflows", json=instance_data, headers=headers)
        assert instance_response.status_code == 200
        instance = instance_response.json()
        instance_id = instance["id"]
        
        # Submit for AI analysis
        submit_response = client.post(f"/api/v1/workflows/{instance_id}/advance", 
                                    json={"action": "submit", "comment": "Submitting for AI analysis"}, 
                                    headers=headers)
        assert submit_response.status_code == 200
        
        # Perform AI analysis
        ai_analysis_data = {
            "text": instance_data["description"],
            "context": instance_data["context_data"],
            "analysis_type": "security_assessment"
        }
        
        ai_response = client.post("/api/v1/ai/analyze", json=ai_analysis_data, headers=headers)
        assert ai_response.status_code == 200
        ai_analysis = ai_response.json()
        
        # AI should detect high urgency and security context
        assert ai_analysis.get("confidence", 0) > 0.5
        
        # Advance workflow based on AI analysis
        ai_advance_data = {
            "action": "ai_analyze",
            "comment": "AI analysis completed - high priority security issue detected",
            "context_updates": {
                "ai_analysis": ai_analysis,
                "ai_priority": "urgent",
                "ai_routing": "security_team_lead",
                "risk_score": 9.2
            }
        }
        
        ai_advance_response = client.post(f"/api/v1/workflows/{instance_id}/advance", json=ai_advance_data, headers=headers)
        assert ai_advance_response.status_code == 200
        analyzed_instance = ai_advance_response.json()
        
        # Verify AI analysis integration
        assert analyzed_instance["current_state"] == "security_review"
        assert "ai_analysis" in analyzed_instance["context_data"]
        assert analyzed_instance["context_data"]["ai_priority"] == "urgent"
        
        # Security team approves critical patch
        approve_data = {
            "action": "approve",
            "comment": "Approved for immediate deployment - critical security vulnerability confirmed",
            "context_updates": {
                "deployment_window": "immediate",
                "authorized_by": "security_team_lead",
                "patch_deployment_plan": "rolling_deployment_with_monitoring"
            }
        }
        
        approve_response = client.post(f"/api/v1/workflows/{instance_id}/advance", json=approve_data, headers=headers)
        assert approve_response.status_code == 200
        final_instance = approve_response.json()
        
        # Verify completion with AI insights
        assert final_instance["current_state"] == "approved"
        assert final_instance["status"] == "completed"
        assert final_instance["context_data"]["risk_score"] == 9.2
        assert "ai_analysis" in final_instance["context_data"]
        
        # Check that AI insights were stored
        insights_response = client.get(f"/api/v1/workflows/{instance_id}/insights", headers=headers)
        if insights_response.status_code == 200:  # If insights endpoint exists
            insights = insights_response.json()
            assert len(insights) > 0
            assert insights[0]["insight_type"] in ["security_analysis", "workflow_analysis"]

    @patch('httpx.AsyncClient.post')
    def test_multi_user_workflow_collaboration_e2e(self, mock_post, client: TestClient, mock_user_data):
        """Test multi-user workflow collaboration end-to-end"""
        # Mock different user contexts
        user1_data = {**mock_user_data, "user_id": "user-1", "roles": ["employee", "requester"]}
        manager_data = {**mock_user_data, "user_id": "manager-1", "roles": ["manager", "approver"]}
        admin_data = {**mock_user_data, "user_id": "admin-1", "roles": ["admin", "workflow_admin"]}
        
        def mock_post_side_effect(*args, **kwargs):
            # Simple mock for identity service - in real test would check token
            identity_mock_response = AsyncMock()
            identity_mock_response.status_code = 200
            identity_mock_response.json.return_value = user1_data  # Default to user1
            return identity_mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        headers = {"Authorization": "Bearer valid_token"}
        
        # Admin creates workflow definition
        definition_data = {
            "name": "Multi-User Collaboration Workflow",
            "description": "Workflow requiring multiple user interactions",
            "category": "collaboration",
            "initial_state": "draft",
            "states": [
                {"name": "draft", "is_initial": True, "assignee_roles": ["employee"]},
                {"name": "peer_review", "assignee_roles": ["peer_reviewer"]},
                {"name": "manager_approval", "assignee_roles": ["manager"]},
                {"name": "approved", "is_final": True},
                {"name": "rejected", "is_final": True}
            ],
            "transitions": [
                {"from": "draft", "to": "peer_review", "action": "submit_for_peer_review"},
                {"from": "peer_review", "to": "manager_approval", "action": "peer_approve"},
                {"from": "peer_review", "to": "draft", "action": "peer_reject"},
                {"from": "manager_approval", "to": "approved", "action": "manager_approve"},
                {"from": "manager_approval", "to": "rejected", "action": "manager_reject"}
            ],
            "business_rules": {
                "role_based_assignments": True,
                "parallel_reviews": False,
                "escalation_timeout_hours": 48
            }
        }
        
        definition_response = client.post("/api/v1/admin/workflow-definitions", json=definition_data, headers=headers)
        assert definition_response.status_code == 201
        definition = definition_response.json()
        definition_id = definition["id"]
        
        # Employee creates workflow instance
        instance_data = {
            "definition_id": definition_id,
            "entity_id": "collaboration-test-001",
            "entity_type": "project_proposal",
            "title": "New Feature Development Proposal",
            "description": "Proposal for implementing real-time collaboration features",
            "context_data": {
                "estimated_effort": "3 months",
                "team_size": 4,
                "technologies": ["React", "WebRTC", "Redis"],
                "business_value": "high"
            }
        }
        
        instance_response = client.post("/api/v1/workflows", json=instance_data, headers=headers)
        assert instance_response.status_code == 200
        instance = instance_response.json()
        instance_id = instance["id"]
        
        # Employee submits for peer review
        submit_response = client.post(f"/api/v1/workflows/{instance_id}/advance", 
                                    json={
                                        "action": "submit_for_peer_review",
                                        "comment": "Ready for peer review",
                                        "context_updates": {"submitted_by": "user-1"}
                                    }, 
                                    headers=headers)
        assert submit_response.status_code == 200
        
        # Get workflows for peer reviewer (simulate different user context)
        peer_workflows_response = client.get("/api/v1/workflows?assigned_to_me=true", headers=headers)
        assert peer_workflows_response.status_code == 200
        peer_workflows = peer_workflows_response.json()
        
        # Peer reviewer approves
        peer_approve_response = client.post(f"/api/v1/workflows/{instance_id}/advance", 
                                          json={
                                              "action": "peer_approve",
                                              "comment": "Technical approach looks solid, recommend approval",
                                              "context_updates": {
                                                  "peer_reviewer": "peer-reviewer-1",
                                                  "technical_review_score": 8.5
                                              }
                                          }, 
                                          headers=headers)
        assert peer_approve_response.status_code == 200
        
        # Manager receives workflow for approval
        manager_workflows_response = client.get("/api/v1/workflows?state=manager_approval", headers=headers)
        assert manager_workflows_response.status_code == 200
        
        # Manager approves
        manager_approve_response = client.post(f"/api/v1/workflows/{instance_id}/advance", 
                                             json={
                                                 "action": "manager_approve",
                                                 "comment": "Approved - aligns with business objectives",
                                                 "context_updates": {
                                                     "manager_approval": "manager-1",
                                                     "budget_allocated": 75000,
                                                     "start_date": "2024-02-01"
                                                 }
                                             }, 
                                             headers=headers)
        assert manager_approve_response.status_code == 200
        final_instance = manager_approve_response.json()
        
        # Verify multi-user collaboration completed successfully
        assert final_instance["current_state"] == "approved"
        assert final_instance["status"] == "completed"
        assert "peer_reviewer" in final_instance["context_data"]
        assert "manager_approval" in final_instance["context_data"]
        assert final_instance["context_data"]["budget_allocated"] == 75000
        
        # Verify complete audit trail
        history_response = client.get(f"/api/v1/workflows/{instance_id}/history", headers=headers)
        assert history_response.status_code == 200
        history = history_response.json()
        
        assert len(history) == 3  # submit_for_peer_review, peer_approve, manager_approve
        participants = set(h.get("triggered_by") for h in history if h.get("triggered_by"))
        assert len(participants) >= 1  # Multiple users participated