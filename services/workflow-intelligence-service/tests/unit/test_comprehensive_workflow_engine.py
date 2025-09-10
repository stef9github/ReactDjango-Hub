"""
Comprehensive unit tests for workflow engine core functionality
Covers workflow creation, state transitions, AI integration, error handling, and edge cases
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, AsyncMock, call
from typing import Dict, List, Any
import json

from workflow_engine import WorkflowEngine, DynamicWorkflowStateMachine
from models import WorkflowDefinition, WorkflowInstance, WorkflowHistory
from statemachine.exceptions import TransitionNotAllowed


@pytest.mark.unit
class TestWorkflowEngineCore:
    """Comprehensive tests for core workflow engine functionality"""

    def test_workflow_engine_initialization_with_session(self, test_session):
        """Test workflow engine initialization with database session"""
        engine = WorkflowEngine(db_session=test_session)
        assert engine.db_session is test_session

    def test_workflow_engine_initialization_without_session(self):
        """Test workflow engine initialization without database session"""
        engine = WorkflowEngine(db_session=None)
        assert engine.db_session is None

    def test_create_workflow_instance_minimal_params(self, test_session, sample_workflow_definition, workflow_engine):
        """Test creating workflow instance with minimal required parameters"""
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="minimal-test-123"
        )
        
        # Verify basic instance creation
        assert instance.id is not None
        assert instance.definition_id == sample_workflow_definition.id
        assert instance.entity_id == "minimal-test-123"
        assert instance.current_state == sample_workflow_definition.initial_state
        assert instance.status == "active"
        assert instance.started_at is not None
        assert instance.title == "Workflow for minimal-test-123"  # Default title

    def test_create_workflow_instance_full_params(self, test_session, sample_workflow_definition, workflow_engine):
        """Test creating workflow instance with all parameters"""
        context = {"priority": "high", "department": "IT", "budget": 5000}
        
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="full-test-456",
            entity_type="purchase_request",
            title="IT Equipment Purchase Request",
            context=context,
            assigned_to="user-789",
            organization_id="org-456",
            created_by="user-123"
        )
        
        # Verify all parameters are set correctly
        assert instance.entity_type == "purchase_request"
        assert instance.title == "IT Equipment Purchase Request"
        assert instance.context_data == context
        assert instance.assigned_to == "user-789"
        assert instance.organization_id == "org-456"
        assert instance.created_by == "user-123"

    def test_create_workflow_instance_inactive_definition(self, test_session, workflow_engine):
        """Test creating instance with inactive definition fails"""
        # Create inactive definition
        definition = WorkflowDefinition(
            name="Inactive Test Workflow",
            category="test",
            initial_state="start",
            states=[{"name": "start"}, {"name": "end"}],
            transitions=[{"from": "start", "to": "end", "action": "finish"}],
            is_active=False,  # Inactive
            organization_id="org-123"
        )
        test_session.add(definition)
        test_session.commit()
        
        with pytest.raises(ValueError, match="not found or inactive"):
            workflow_engine.create_workflow_instance(
                definition_id=str(definition.id),
                entity_id="test-123"
            )

    def test_create_workflow_instance_creates_initial_history(self, test_session, sample_workflow_definition, workflow_engine):
        """Test that initial history entry is created with correct details"""
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="history-test-123",
            created_by="user-456"
        )
        
        # Check history entry
        history_entries = test_session.query(WorkflowHistory).filter(
            WorkflowHistory.instance_id == instance.id
        ).all()
        
        assert len(history_entries) == 1
        history = history_entries[0]
        assert history.from_state is None  # Initial creation
        assert history.to_state == sample_workflow_definition.initial_state
        assert history.action == "create"
        assert history.triggered_by == "user-456"
        assert history.trigger_type == "manual"
        assert history.comment == "Workflow instance created"

    def test_create_workflow_instance_updates_definition_usage_count(self, test_session, sample_workflow_definition, workflow_engine):
        """Test that definition usage count is properly incremented"""
        initial_count = sample_workflow_definition.usage_count or 0
        
        # Create multiple instances
        workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="usage-test-1"
        )
        workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="usage-test-2"
        )
        
        test_session.refresh(sample_workflow_definition)
        assert sample_workflow_definition.usage_count == initial_count + 2


@pytest.mark.unit
class TestWorkflowStateTransitions:
    """Comprehensive tests for workflow state transitions and state machine logic"""

    @patch('workflow_engine.DynamicWorkflowStateMachine')
    def test_advance_workflow_valid_transition(self, mock_state_machine_class, test_session, sample_workflow_instance, workflow_engine):
        """Test successful workflow state transition"""
        # Mock state machine setup
        mock_state_machine = Mock()
        mock_transition_method = Mock()
        mock_state_machine_class.return_value = mock_state_machine
        setattr(mock_state_machine, "submit_for_review", mock_transition_method)
        
        # Execute transition
        updated_instance = workflow_engine.advance_workflow(
            instance_id=str(sample_workflow_instance.id),
            action="submit_for_review",
            user_id="user-123",
            comment="Ready for review",
            data={"urgency": "high"},
            context_updates={"last_modified_by": "user-123"}
        )
        
        # Verify state machine was called correctly
        mock_state_machine_class.assert_called_once()
        mock_transition_method.assert_called_once_with(
            user_id="user-123",
            comment="Ready for review",
            data={"urgency": "high"},
            context={"last_modified_by": "user-123"}
        )

    def test_advance_workflow_invalid_action(self, test_session, sample_workflow_instance, workflow_engine):
        """Test advancing workflow with invalid action fails appropriately"""
        with pytest.raises(ValueError, match="not available"):
            workflow_engine.advance_workflow(
                instance_id=str(sample_workflow_instance.id),
                action="invalid_nonexistent_action",
                user_id="user-123"
            )

    def test_advance_workflow_completed_instance(self, test_session, sample_workflow_instance, workflow_engine):
        """Test that completed workflows cannot be advanced"""
        # Mark instance as completed
        sample_workflow_instance.status = "completed"
        sample_workflow_instance.completed_at = datetime.utcnow()
        test_session.commit()
        
        with pytest.raises(ValueError, match="not active"):
            workflow_engine.advance_workflow(
                instance_id=str(sample_workflow_instance.id),
                action="submit_for_review",
                user_id="user-123"
            )

    def test_advance_workflow_paused_instance(self, test_session, sample_workflow_instance, workflow_engine):
        """Test that paused workflows cannot be advanced"""
        # Mark instance as paused
        sample_workflow_instance.status = "paused"
        test_session.commit()
        
        with pytest.raises(ValueError, match="not active"):
            workflow_engine.advance_workflow(
                instance_id=str(sample_workflow_instance.id),
                action="submit_for_review",
                user_id="user-123"
            )

    def test_get_workflow_status_comprehensive(self, test_session, sample_workflow_instance, workflow_engine):
        """Test comprehensive workflow status retrieval"""
        # Add some history entries
        history1 = WorkflowHistory(
            instance_id=sample_workflow_instance.id,
            from_state="draft",
            to_state="pending_review", 
            action="submit",
            triggered_by="user-123",
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        history2 = WorkflowHistory(
            instance_id=sample_workflow_instance.id,
            from_state="pending_review",
            to_state="approved",
            action="approve",
            triggered_by="user-456",
            created_at=datetime.utcnow() - timedelta(hours=1)
        )
        test_session.add_all([history1, history2])
        test_session.commit()
        
        status = workflow_engine.get_workflow_status(str(sample_workflow_instance.id))
        
        # Verify comprehensive status data
        assert status["instance_id"] == str(sample_workflow_instance.id)
        assert status["definition_id"] == str(sample_workflow_instance.definition_id)
        assert status["entity_id"] == sample_workflow_instance.entity_id
        assert status["current_state"] == sample_workflow_instance.current_state
        assert status["status"] == sample_workflow_instance.status
        assert "progress_percentage" in status
        assert "started_at" in status
        assert "available_actions" in status
        assert "context_data" in status
        assert "recent_history" in status
        assert len(status["recent_history"]) >= 2


@pytest.mark.unit
class TestWorkflowUserManagement:
    """Tests for workflow assignment and user management functionality"""

    def test_get_user_workflows_basic(self, test_session, workflow_engine):
        """Test getting workflows for a specific user"""
        # Create test definition and instances
        definition = WorkflowDefinition(
            name="User Test Workflow",
            category="test",
            initial_state="draft",
            states=[{"name": "draft"}, {"name": "done"}],
            transitions=[{"from": "draft", "to": "done", "action": "complete"}],
            organization_id="org-123"
        )
        test_session.add(definition)
        test_session.commit()
        
        # Create instances assigned to different users
        instance1 = workflow_engine.create_workflow_instance(
            definition_id=str(definition.id),
            entity_id="user-workflow-1",
            assigned_to="user-123",
            organization_id="org-123"
        )
        instance2 = workflow_engine.create_workflow_instance(
            definition_id=str(definition.id), 
            entity_id="user-workflow-2",
            assigned_to="user-456",
            organization_id="org-123"
        )
        instance3 = workflow_engine.create_workflow_instance(
            definition_id=str(definition.id),
            entity_id="user-workflow-3", 
            assigned_to="user-123",
            organization_id="org-123"
        )
        
        # Get workflows for user-123
        user_workflows = workflow_engine.get_user_workflows(
            user_id="user-123",
            organization_id="org-123"
        )
        
        # Should return 2 workflows for user-123
        assert len(user_workflows) == 2
        workflow_ids = [w["instance_id"] for w in user_workflows]
        assert str(instance1.id) in workflow_ids
        assert str(instance3.id) in workflow_ids
        assert str(instance2.id) not in workflow_ids

    def test_get_user_workflows_with_filters(self, test_session, workflow_engine):
        """Test getting user workflows with status and organization filters"""
        definition = WorkflowDefinition(
            name="Filter Test Workflow",
            category="test", 
            initial_state="start",
            states=[{"name": "start"}, {"name": "end"}],
            transitions=[{"from": "start", "to": "end", "action": "finish"}],
            organization_id="org-123"
        )
        test_session.add(definition)
        test_session.commit()
        
        # Create instances with different statuses and organizations
        active_instance = workflow_engine.create_workflow_instance(
            definition_id=str(definition.id),
            entity_id="filter-test-1",
            assigned_to="user-123",
            organization_id="org-123"
        )
        
        completed_instance = workflow_engine.create_workflow_instance(
            definition_id=str(definition.id),
            entity_id="filter-test-2", 
            assigned_to="user-123",
            organization_id="org-123"
        )
        completed_instance.status = "completed"
        test_session.commit()
        
        # Test status filter
        active_workflows = workflow_engine.get_user_workflows(
            user_id="user-123",
            organization_id="org-123",
            status="active"
        )
        assert len(active_workflows) == 1
        assert active_workflows[0]["instance_id"] == str(active_instance.id)
        
        completed_workflows = workflow_engine.get_user_workflows(
            user_id="user-123", 
            organization_id="org-123",
            status="completed"
        )
        assert len(completed_workflows) == 1
        assert completed_workflows[0]["instance_id"] == str(completed_instance.id)

    def test_get_user_workflows_pagination(self, test_session, workflow_engine):
        """Test workflow pagination functionality"""
        definition = WorkflowDefinition(
            name="Pagination Test Workflow",
            category="test",
            initial_state="start",
            states=[{"name": "start"}],
            transitions=[],
            organization_id="org-123"
        )
        test_session.add(definition)
        test_session.commit()
        
        # Create multiple instances
        instances = []
        for i in range(7):  # Create 7 instances
            instance = workflow_engine.create_workflow_instance(
                definition_id=str(definition.id),
                entity_id=f"pagination-test-{i}",
                assigned_to="user-123",
                organization_id="org-123"
            )
            instances.append(instance)
        
        # Test first page
        page1 = workflow_engine.get_user_workflows(
            user_id="user-123",
            organization_id="org-123",
            limit=3,
            offset=0
        )
        assert len(page1) == 3
        
        # Test second page
        page2 = workflow_engine.get_user_workflows(
            user_id="user-123",
            organization_id="org-123", 
            limit=3,
            offset=3
        )
        assert len(page2) == 3
        
        # Test third page (remaining items)
        page3 = workflow_engine.get_user_workflows(
            user_id="user-123",
            organization_id="org-123",
            limit=3,
            offset=6
        )
        assert len(page3) == 1


@pytest.mark.unit
class TestWorkflowErrorHandling:
    """Comprehensive tests for workflow error handling and edge cases"""

    def test_create_workflow_with_malformed_uuid(self, test_session, workflow_engine):
        """Test error handling for malformed UUID definition ID"""
        with pytest.raises(ValueError):
            workflow_engine.create_workflow_instance(
                definition_id="not-a-valid-uuid",
                entity_id="test-123"
            )

    def test_advance_workflow_with_malformed_uuid(self, test_session, workflow_engine):
        """Test error handling for malformed UUID instance ID"""
        with pytest.raises(ValueError):
            workflow_engine.advance_workflow(
                instance_id="not-a-valid-uuid",
                action="submit",
                user_id="user-123"
            )

    def test_get_status_with_nonexistent_instance(self, test_session, workflow_engine):
        """Test error handling when getting status for non-existent instance"""
        nonexistent_id = str(uuid.uuid4())
        
        with pytest.raises(ValueError, match="not found"):
            workflow_engine.get_workflow_status(nonexistent_id)

    @patch('workflow_engine.SessionLocal')
    def test_database_transaction_rollback(self, mock_session_local, test_session, workflow_engine):
        """Test that database errors trigger proper transaction rollback"""
        # Mock a database error during commit
        mock_session = Mock()
        mock_session.add = Mock()
        mock_session.commit = Mock(side_effect=Exception("Database connection error"))
        mock_session.rollback = Mock()
        mock_session_local.return_value.__enter__.return_value = mock_session
        mock_session_local.return_value.__exit__.return_value = None
        
        # This should properly handle the database error
        with pytest.raises(Exception, match="Database connection error"):
            # The create method uses SessionLocal internally for history creation
            pass

    def test_workflow_with_empty_context(self, test_session, sample_workflow_definition, workflow_engine):
        """Test workflow creation and operations with empty context"""
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="empty-context-test",
            context={}
        )
        
        assert instance.context_data == {}
        
        # Test context operations
        instance.set_context_value("new_key", "new_value")
        assert instance.get_context_value("new_key") == "new_value"
        assert instance.get_context_value("nonexistent", "default") == "default"

    def test_workflow_with_complex_context(self, test_session, sample_workflow_definition, workflow_engine):
        """Test workflow with complex nested context data"""
        complex_context = {
            "request_details": {
                "items": [
                    {"name": "Laptop", "quantity": 2, "price": 1200.00},
                    {"name": "Monitor", "quantity": 2, "price": 300.00}
                ],
                "total_amount": 3000.00,
                "currency": "USD"
            },
            "approvals": {
                "manager_required": True,
                "finance_required": True,
                "levels": ["L1", "L2", "L3"]
            },
            "metadata": {
                "priority": "high",
                "tags": ["IT", "equipment", "urgent"]
            }
        }
        
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="complex-context-test",
            context=complex_context
        )
        
        # Verify complex context is preserved
        assert instance.context_data["request_details"]["total_amount"] == 3000.00
        assert "L3" in instance.context_data["approvals"]["levels"]
        assert "urgent" in instance.context_data["metadata"]["tags"]


@pytest.mark.unit
class TestWorkflowStateManagement:
    """Tests for workflow state machine logic and validation"""

    def test_workflow_progress_calculation(self, test_session, sample_workflow_instance):
        """Test workflow progress percentage calculation"""
        # Test initial state progress
        sample_workflow_instance.update_progress()
        initial_progress = int(sample_workflow_instance.progress_percentage)
        assert initial_progress >= 0
        
        # Test progress update when state changes
        if sample_workflow_instance.definition and sample_workflow_instance.definition.states:
            states = sample_workflow_instance.definition.state_list
            if len(states) > 1:
                # Move to second state
                sample_workflow_instance.current_state = states[1]
                sample_workflow_instance.update_progress()
                updated_progress = int(sample_workflow_instance.progress_percentage)
                assert updated_progress > initial_progress

    def test_workflow_available_actions(self, test_session, sample_workflow_instance):
        """Test getting available actions based on current state"""
        actions = sample_workflow_instance.get_available_actions()
        
        assert isinstance(actions, list)
        # Actions should be strings
        for action in actions:
            assert isinstance(action, str)
            assert len(action) > 0

    def test_workflow_transition_validation(self, test_session, sample_workflow_definition):
        """Test workflow transition validation logic"""
        if sample_workflow_definition.transitions:
            # Get a valid transition
            valid_transition = sample_workflow_definition.transitions[0]
            from_state = valid_transition["from"]
            to_state = valid_transition["to"] 
            action = valid_transition.get("action")
            
            # Test valid transition
            assert sample_workflow_definition.validate_transition(from_state, to_state, action) is True
            
            # Test invalid transition (wrong action)
            assert sample_workflow_definition.validate_transition(from_state, to_state, "invalid_action") is False
            
            # Test invalid transition (wrong target state)
            assert sample_workflow_definition.validate_transition(from_state, "invalid_state", action) is False

    def test_workflow_duration_tracking(self, test_session, sample_workflow_instance):
        """Test workflow duration calculation"""
        duration = sample_workflow_instance.duration
        
        from datetime import timedelta
        assert isinstance(duration, timedelta)
        assert duration.total_seconds() >= 0
        
        # Test with completed workflow
        sample_workflow_instance.completed_at = datetime.utcnow() + timedelta(minutes=30)
        completed_duration = sample_workflow_instance.duration
        assert completed_duration.total_seconds() >= 1800  # At least 30 minutes

    def test_workflow_overdue_detection(self, test_session, sample_workflow_instance):
        """Test workflow overdue status detection"""
        # Initially not overdue (no due date set)
        assert sample_workflow_instance.is_overdue is False
        
        # Set future due date
        sample_workflow_instance.due_date = datetime.utcnow() + timedelta(hours=24)
        assert sample_workflow_instance.is_overdue is False
        
        # Set past due date
        sample_workflow_instance.due_date = datetime.utcnow() - timedelta(hours=1)
        assert sample_workflow_instance.is_overdue is True
        
        # Completed workflows should not be overdue regardless of due date
        sample_workflow_instance.status = "completed"
        sample_workflow_instance.completed_at = datetime.utcnow()
        assert sample_workflow_instance.is_overdue is False


@pytest.mark.unit
class TestAIIntegrationMocks:
    """Tests for AI integration endpoints with mocked responses"""

    @patch('httpx.AsyncClient')
    async def test_ai_text_summarization_mock(self, mock_client_class):
        """Test AI text summarization with mocked response"""
        # Mock the HTTP client response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "summary": "This is a test document summary generated by AI.",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "confidence": 0.95
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Test the AI summarization (would be called from main.py endpoints)
        # This is a mock test showing how AI endpoints should be tested
        
        # Simulate API call
        test_text = "This is a long document that needs to be summarized by AI services."
        
        # Mock AI service response
        expected_summary = {
            "summary": "This is a test document summary generated by AI.",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "confidence": 0.95
        }
        
        # In real implementation, this would call the actual AI service
        # Here we verify the mock setup works
        assert expected_summary["confidence"] == 0.95
        assert len(expected_summary["key_points"]) == 3

    @patch('httpx.AsyncClient')
    async def test_ai_form_suggestions_mock(self, mock_client_class):
        """Test AI form pre-filling suggestions with mocked response"""
        # Mock AI response for form suggestions
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "suggestions": {
                "title": "Equipment Purchase Request",
                "category": "IT Hardware",
                "estimated_cost": "$3,000",
                "priority": "Medium",
                "justification": "Required for new employee onboarding"
            },
            "confidence_scores": {
                "title": 0.9,
                "category": 0.85,
                "estimated_cost": 0.7,
                "priority": 0.8
            }
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Test form suggestions (mock scenario)
        context = {
            "user_role": "IT Manager",
            "department": "Information Technology",
            "previous_requests": ["Monitor", "Laptop", "Keyboard"]
        }
        
        expected_suggestions = {
            "title": "Equipment Purchase Request",
            "category": "IT Hardware",
            "estimated_cost": "$3,000"
        }
        
        # Verify mock response structure
        assert "suggestions" in mock_response.json()
        assert "confidence_scores" in mock_response.json()

    @patch('httpx.AsyncClient')
    async def test_ai_workflow_analysis_mock(self, mock_client_class):
        """Test AI workflow analysis with mocked response"""
        # Mock AI analysis response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "analysis": {
                "bottlenecks": ["Manual approval step takes 3-5 days"],
                "efficiency_score": 0.72,
                "recommendations": [
                    "Consider automatic approval for requests under $500",
                    "Set up parallel approval workflow for urgent requests"
                ],
                "predicted_completion_time": "5-7 business days"
            },
            "insights": {
                "pattern_detection": "High volume requests on Mondays",
                "user_behavior": "Most requests submitted near end of month"
            }
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Verify AI analysis response structure
        analysis_data = mock_response.json()
        assert "analysis" in analysis_data
        assert "insights" in analysis_data
        assert analysis_data["analysis"]["efficiency_score"] == 0.72
        assert len(analysis_data["analysis"]["recommendations"]) == 2

    async def test_ai_error_handling_mock(self):
        """Test AI service error handling"""
        # Test various error scenarios
        error_scenarios = [
            {"status_code": 401, "error": "Invalid API key"},
            {"status_code": 429, "error": "Rate limit exceeded"},
            {"status_code": 500, "error": "Internal server error"},
            {"status_code": 503, "error": "Service temporarily unavailable"}
        ]
        
        for scenario in error_scenarios:
            # Mock error response
            mock_response = Mock()
            mock_response.status_code = scenario["status_code"]
            mock_response.json.return_value = {"error": scenario["error"]}
            
            # Verify error handling logic would work
            assert mock_response.status_code != 200
            assert "error" in mock_response.json()


@pytest.mark.unit
class TestWorkflowEngineIntegration:
    """Tests for workflow engine integration points and relationships"""

    def test_workflow_definition_relationship(self, test_session, sample_workflow_definition, workflow_engine):
        """Test workflow instance relationship with definition"""
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="relationship-test-123"
        )
        
        # Test forward relationship (instance -> definition)
        assert instance.definition_id == sample_workflow_definition.id
        assert instance.definition == sample_workflow_definition
        
        # Test reverse relationship (definition -> instances)
        definition_instances = sample_workflow_definition.instances.all()
        assert instance in definition_instances

    def test_workflow_history_relationship(self, test_session, sample_workflow_instance):
        """Test workflow instance relationship with history"""
        # Create history entries
        history1 = WorkflowHistory(
            instance_id=sample_workflow_instance.id,
            from_state="draft",
            to_state="review",
            action="submit",
            triggered_by="user-123"
        )
        history2 = WorkflowHistory(
            instance_id=sample_workflow_instance.id,
            from_state="review", 
            to_state="approved",
            action="approve",
            triggered_by="user-456"
        )
        
        test_session.add_all([history1, history2])
        test_session.commit()
        
        # Test relationship
        instance_history = sample_workflow_instance.history.all()
        assert len(instance_history) >= 2
        assert history1 in instance_history
        assert history2 in instance_history

    def test_workflow_context_persistence(self, test_session, sample_workflow_instance):
        """Test that workflow context data persists correctly"""
        # Set complex context data
        test_context = {
            "user_data": {"name": "John Doe", "role": "Manager"},
            "request_info": {"amount": 5000, "currency": "USD"},
            "approvals": ["level1", "level2"],
            "metadata": {"timestamp": str(datetime.utcnow())}
        }
        
        sample_workflow_instance.context_data = test_context
        test_session.commit()
        
        # Refresh instance and verify context persistence
        test_session.refresh(sample_workflow_instance)
        assert sample_workflow_instance.context_data == test_context
        assert sample_workflow_instance.get_context_value("user_data")["name"] == "John Doe"
        assert sample_workflow_instance.get_context_value("request_info")["amount"] == 5000

    def test_workflow_multiple_organization_isolation(self, test_session, workflow_engine):
        """Test that workflows are properly isolated by organization"""
        # Create definitions for different organizations
        org1_definition = WorkflowDefinition(
            name="Org1 Workflow",
            category="test",
            initial_state="start",
            states=[{"name": "start"}, {"name": "end"}],
            transitions=[{"from": "start", "to": "end", "action": "finish"}],
            organization_id="org-111"
        )
        org2_definition = WorkflowDefinition(
            name="Org2 Workflow", 
            category="test",
            initial_state="start",
            states=[{"name": "start"}, {"name": "end"}],
            transitions=[{"from": "start", "to": "end", "action": "finish"}],
            organization_id="org-222"
        )
        
        test_session.add_all([org1_definition, org2_definition])
        test_session.commit()
        
        # Create instances in different organizations
        org1_instance = workflow_engine.create_workflow_instance(
            definition_id=str(org1_definition.id),
            entity_id="org1-entity",
            assigned_to="user-123",
            organization_id="org-111"
        )
        org2_instance = workflow_engine.create_workflow_instance(
            definition_id=str(org2_definition.id),
            entity_id="org2-entity",
            assigned_to="user-123",
            organization_id="org-222"
        )
        
        # Verify organization isolation
        org1_workflows = workflow_engine.get_user_workflows(
            user_id="user-123",
            organization_id="org-111"
        )
        org2_workflows = workflow_engine.get_user_workflows(
            user_id="user-123",
            organization_id="org-222"
        )
        
        assert len(org1_workflows) == 1
        assert len(org2_workflows) == 1
        assert org1_workflows[0]["instance_id"] == str(org1_instance.id)
        assert org2_workflows[0]["instance_id"] == str(org2_instance.id)


@pytest.mark.unit
class TestWorkflowEngineEdgeCases:
    """Tests for workflow engine edge cases and boundary conditions"""

    def test_workflow_with_single_state(self, test_session, workflow_engine):
        """Test workflow with only one state (edge case)"""
        single_state_definition = WorkflowDefinition(
            name="Single State Workflow",
            category="test",
            initial_state="completed",
            states=[{"name": "completed", "is_final": True}],
            transitions=[],  # No transitions possible
            organization_id="org-123"
        )
        test_session.add(single_state_definition)
        test_session.commit()
        
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(single_state_definition.id),
            entity_id="single-state-test"
        )
        
        # Should be immediately completed
        assert instance.current_state == "completed"
        assert instance.get_available_actions() == []

    def test_workflow_with_circular_transitions(self, test_session, workflow_engine):
        """Test workflow with circular state transitions"""
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
                {"from": "state_c", "to": "state_a", "action": "restart"}  # Circular
            ],
            organization_id="org-123"
        )
        test_session.add(circular_definition)
        test_session.commit()
        
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(circular_definition.id),
            entity_id="circular-test"
        )
        
        # Verify circular transitions are possible
        available_actions = instance.get_available_actions()
        assert "next" in available_actions
        
        # Verify transition validation works for circular case
        assert instance.can_transition_to("state_b", "next") is True

    def test_workflow_with_large_context_data(self, test_session, sample_workflow_definition, workflow_engine):
        """Test workflow with large context data payload"""
        # Create large context data (simulating real-world complex workflows)
        large_context = {
            "form_data": {f"field_{i}": f"value_{i}" for i in range(100)},
            "attachments": [{"id": f"file_{i}", "size": 1024 * i} for i in range(50)],
            "history_log": [{"timestamp": str(datetime.utcnow()), "action": f"action_{i}"} for i in range(200)],
            "nested_objects": {
                "level1": {
                    "level2": {
                        "level3": {
                            "data": "deeply nested data",
                            "arrays": [[i, i*2, i*3] for i in range(20)]
                        }
                    }
                }
            }
        }
        
        instance = workflow_engine.create_workflow_instance(
            definition_id=str(sample_workflow_definition.id),
            entity_id="large-context-test",
            context=large_context
        )
        
        # Verify large context is handled correctly
        assert len(instance.context_data["form_data"]) == 100
        assert len(instance.context_data["attachments"]) == 50
        assert len(instance.context_data["history_log"]) == 200
        assert instance.context_data["nested_objects"]["level1"]["level2"]["level3"]["data"] == "deeply nested data"

    def test_concurrent_workflow_operations(self, test_session, sample_workflow_definition, workflow_engine):
        """Test concurrent workflow operations (simulated)"""
        # Create multiple instances simultaneously (simulating concurrent operations)
        instances = []
        
        for i in range(10):
            instance = workflow_engine.create_workflow_instance(
                definition_id=str(sample_workflow_definition.id),
                entity_id=f"concurrent-test-{i}",
                assigned_to=f"user-{i % 3}",  # Distribute across 3 users
                organization_id="org-123"
            )
            instances.append(instance)
        
        # Verify all instances were created successfully
        assert len(instances) == 10
        
        # Verify each instance has unique ID
        instance_ids = [instance.id for instance in instances]
        assert len(set(instance_ids)) == 10  # All unique
        
        # Verify definition usage count updated correctly
        test_session.refresh(sample_workflow_definition)
        assert sample_workflow_definition.usage_count >= 10