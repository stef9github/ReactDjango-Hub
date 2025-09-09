"""
Integration tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json


@pytest.mark.integration
class TestHealthEndpoint:
    """Integration tests for health endpoint"""
    
    def test_health_endpoint_success(self, client: TestClient):
        """Test health endpoint returns successful response"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "workflow-intelligence-service" in data["service"]
        assert "status" in data
        assert "version" in data
        assert data["version"] == "1.0.0"

    def test_health_endpoint_includes_metrics(self, client: TestClient):
        """Test health endpoint includes system metrics"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "uptime_seconds" in data["metrics"]
        assert "memory_usage_mb" in data["metrics"]
        assert isinstance(data["metrics"]["uptime_seconds"], int)
        assert isinstance(data["metrics"]["memory_usage_mb"], float)

    def test_health_endpoint_includes_dependencies(self, client: TestClient):
        """Test health endpoint includes dependency status"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "dependencies" in data
        # Should include database, redis, identity-service, ai-services
        dependencies = data["dependencies"]
        expected_deps = ["database", "redis", "identity-service", "ai-services"]
        
        for dep in expected_deps:
            assert dep in dependencies


@pytest.mark.integration
@pytest.mark.auth
class TestWorkflowEndpoints:
    """Integration tests for workflow management endpoints"""
    
    def test_create_workflow_without_auth(self, client: TestClient):
        """Test workflow creation requires authentication"""
        workflow_data = {
            "definition_id": "test-definition-123",
            "entity_id": "test-entity-123",
            "context": {"priority": "high"}
        }
        
        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code == 403  # No authentication provided

    @patch('httpx.AsyncClient.post')
    def test_create_workflow_with_auth_success(self, mock_post, client: TestClient, mock_user_data, sample_workflow_definition):
        """Test successful workflow creation with authentication"""
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        workflow_data = {
            "definition_id": str(sample_workflow_definition.id),
            "entity_id": "test-document-123",
            "context": {"priority": "high", "department": "IT"}
        }
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.post("/api/v1/workflows", json=workflow_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_id"] is not None
        assert data["definition_id"] == str(sample_workflow_definition.id)
        assert data["entity_id"] == "test-document-123"
        assert data["current_state"] == sample_workflow_definition.initial_state
        assert data["status"] == "active"
        assert "available_actions" in data
        assert data["created_by"] == mock_user_data["user_id"]

    @patch('httpx.AsyncClient.post')
    def test_create_workflow_invalid_definition(self, mock_post, client: TestClient, mock_user_data):
        """Test workflow creation with invalid definition ID"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        workflow_data = {
            "definition_id": "nonexistent-definition-id",
            "entity_id": "test-entity-123",
            "context": {}
        }
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.post("/api/v1/workflows", json=workflow_data, headers=headers)
        
        assert response.status_code == 400
        assert "not found or inactive" in response.json()["detail"]

    def test_get_workflow_status_without_auth(self, client: TestClient):
        """Test workflow status retrieval requires authentication"""
        response = client.get("/api/v1/workflows/test-workflow-123/status")
        assert response.status_code == 403

    @patch('httpx.AsyncClient.post')
    def test_get_workflow_status_success(self, mock_post, client: TestClient, mock_user_data, sample_workflow_instance):
        """Test successful workflow status retrieval"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get(f"/api/v1/workflows/{sample_workflow_instance.id}/status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["instance_id"] == str(sample_workflow_instance.id)
        assert data["current_state"] == sample_workflow_instance.current_state
        assert data["status"] == sample_workflow_instance.status
        assert "available_actions" in data
        assert "recent_history" in data

    @patch('httpx.AsyncClient.post')
    def test_get_workflow_status_nonexistent(self, mock_post, client: TestClient, mock_user_data):
        """Test workflow status for non-existent workflow"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/workflows/nonexistent-id/status", headers=headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('httpx.AsyncClient.post')
    def test_get_workflow_status_access_denied(self, mock_post, client: TestClient):
        """Test workflow status access denied for unauthorized user"""
        # Mock user from different organization
        unauthorized_user = {
            "user_id": "other-user-123",
            "organization_id": "other-org-456",
            "roles": ["user"]
        }
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = unauthorized_user
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/workflows/some-workflow-id/status", headers=headers)
        
        assert response.status_code == 404  # Workflow not found due to access restrictions

    def test_advance_workflow_without_auth(self, client: TestClient):
        """Test workflow advancement requires authentication"""
        transition_data = {
            "action": "submit_for_review",
            "data": {"comment": "Ready for review"}
        }
        
        response = client.patch("/api/v1/workflows/test-123/next", json=transition_data)
        assert response.status_code == 403

    @patch('httpx.AsyncClient.post')
    def test_advance_workflow_success(self, mock_post, client: TestClient, mock_user_data, sample_workflow_instance):
        """Test successful workflow advancement"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        transition_data = {
            "action": "submit_for_review",
            "data": {"comment": "Ready for review", "priority": "high"}
        }
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        
        with patch('workflow_engine.DynamicWorkflowStateMachine') as mock_state_machine_class:
            # Mock the state machine and transition
            mock_state_machine = AsyncMock()
            mock_state_machine_class.return_value = mock_state_machine
            
            # Mock the transition method
            mock_transition = AsyncMock()
            setattr(mock_state_machine, "submit_for_review", mock_transition)
            
            response = client.patch(
                f"/api/v1/workflows/{sample_workflow_instance.id}/next",
                json=transition_data,
                headers=headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["workflow_id"] == str(sample_workflow_instance.id)
        assert data["action"] == "submit_for_review"
        assert "current_state" in data
        assert "updated_by" in data

    @patch('httpx.AsyncClient.post')
    def test_advance_workflow_invalid_action(self, mock_post, client: TestClient, mock_user_data, sample_workflow_instance):
        """Test workflow advancement with invalid action"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        transition_data = {
            "action": "invalid_action",
            "data": {}
        }
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.patch(
            f"/api/v1/workflows/{sample_workflow_instance.id}/next",
            json=transition_data,
            headers=headers
        )
        
        assert response.status_code == 400
        assert "not available" in response.json()["detail"]

    def test_get_user_workflows_without_auth(self, client: TestClient):
        """Test user workflows endpoint requires authentication"""
        response = client.get("/api/v1/workflows/user/test-user-123")
        assert response.status_code == 403

    @patch('httpx.AsyncClient.post')
    def test_get_user_workflows_success(self, mock_post, client: TestClient, mock_user_data, sample_workflow_instance):
        """Test successful user workflows retrieval"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get(f"/api/v1/workflows/user/{mock_user_data['user_id']}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert "pagination" in data
        assert isinstance(data["workflows"], list)

    @patch('httpx.AsyncClient.post')
    def test_get_user_workflows_access_denied(self, mock_post, client: TestClient, mock_user_data):
        """Test user workflows access denied for other user"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/workflows/user/other-user-id", headers=headers)
        
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    @patch('httpx.AsyncClient.post')
    def test_get_user_workflows_with_filters(self, mock_post, client: TestClient, mock_user_data):
        """Test user workflows with query filters"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get(
            f"/api/v1/workflows/user/{mock_user_data['user_id']}?status=active&limit=5&offset=0",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "filters" in data
        assert data["filters"]["status"] == "active"
        assert data["pagination"]["limit"] == 5


@pytest.mark.integration
@pytest.mark.auth
class TestAIEndpoints:
    """Integration tests for AI assistance endpoints"""
    
    def test_ai_summarize_without_auth(self, client: TestClient):
        """Test AI summarization requires authentication"""
        ai_data = {
            "text": "This is test text to summarize",
            "task_type": "summarize",
            "context": {}
        }
        
        response = client.post("/api/v1/ai/summarize", json=ai_data)
        assert response.status_code == 403

    @patch('httpx.AsyncClient.post')
    def test_ai_summarize_success(self, mock_post, client: TestClient, mock_user_data):
        """Test successful AI summarization"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        ai_data = {
            "text": "This is a long document that needs to be summarized for workflow purposes.",
            "task_type": "summarize",
            "context": {"priority": "high"}
        }
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.post("/api/v1/ai/summarize", json=ai_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["original_length"] == len(ai_data["text"])
        assert "summary" in data
        assert "confidence" in data
        assert data["requested_by"] == mock_user_data["user_id"]

    @patch('httpx.AsyncClient.post')
    def test_ai_suggest_success(self, mock_post, client: TestClient, mock_user_data):
        """Test successful AI suggestions"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        ai_data = {
            "text": "Purchase request for office supplies",
            "task_type": "suggest",
            "context": {"department": "IT", "budget": 1000}
        }
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.post("/api/v1/ai/suggest", json=ai_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert "confidence" in data
        assert data["requested_by"] == mock_user_data["user_id"]

    @patch('httpx.AsyncClient.post')
    def test_ai_analyze_success(self, mock_post, client: TestClient, mock_user_data):
        """Test successful AI analysis"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        ai_data = {
            "text": "Contract review for new vendor agreement",
            "task_type": "analyze",
            "context": {"contract_type": "vendor", "value": 50000}
        }
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.post("/api/v1/ai/analyze", json=ai_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert "insights" in data
        assert data["requested_by"] == mock_user_data["user_id"]


@pytest.mark.integration
@pytest.mark.auth
class TestWorkflowDefinitionEndpoints:
    """Integration tests for workflow definition endpoints"""
    
    def test_list_definitions_without_auth(self, client: TestClient):
        """Test listing workflow definitions requires authentication"""
        response = client.get("/api/v1/definitions")
        assert response.status_code == 403

    @patch('httpx.AsyncClient.post')
    def test_list_definitions_success(self, mock_post, client: TestClient, mock_user_data):
        """Test successful workflow definitions listing"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/definitions", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "definitions" in data
        assert isinstance(data["definitions"], list)
        assert data["requested_by"] == mock_user_data["user_id"]

    def test_create_definition_without_auth(self, client: TestClient):
        """Test creating workflow definition requires authentication"""
        definition_data = {
            "name": "Test Definition",
            "states": ["start", "end"],
            "transitions": []
        }
        
        response = client.post("/api/v1/definitions", json=definition_data)
        assert response.status_code == 403

    @patch('httpx.AsyncClient.post')
    def test_create_definition_without_admin_role(self, mock_post, client: TestClient, mock_user_data):
        """Test creating workflow definition requires admin role"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data  # Regular user without admin role
        mock_post.return_value = mock_response
        
        definition_data = {
            "name": "Test Definition",
            "states": ["start", "end"],
            "transitions": []
        }
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.post("/api/v1/definitions", json=definition_data, headers=headers)
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    @patch('httpx.AsyncClient.post')
    def test_create_definition_with_admin_role(self, mock_post, client: TestClient, admin_user_data):
        """Test creating workflow definition with admin role"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = admin_user_data
        mock_post.return_value = mock_response
        
        definition_data = {
            "name": "Test Admin Definition",
            "description": "Test definition created by admin",
            "states": ["start", "middle", "end"],
            "transitions": [
                {"from": "start", "to": "middle", "action": "proceed"},
                {"from": "middle", "to": "end", "action": "complete"}
            ]
        }
        
        headers = {"Authorization": "Bearer admin.jwt.token"}
        response = client.post("/api/v1/definitions", json=definition_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["created_by"] == admin_user_data["user_id"]


@pytest.mark.integration
@pytest.mark.auth
class TestWorkflowStatsEndpoints:
    """Integration tests for workflow statistics endpoints"""
    
    def test_workflow_stats_without_auth(self, client: TestClient):
        """Test workflow stats require authentication"""
        response = client.get("/api/v1/workflows/stats")
        assert response.status_code == 403

    @patch('httpx.AsyncClient.post')
    def test_workflow_stats_success(self, mock_post, client: TestClient, mock_user_data):
        """Test successful workflow statistics retrieval"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/workflows/stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "active_workflows" in data
        assert "completed_today" in data
        assert "overdue_workflows" in data
        assert "average_completion_time" in data

    def test_sla_check_without_auth(self, client: TestClient):
        """Test SLA compliance check requires authentication"""
        response = client.get("/api/v1/workflows/sla-check")
        assert response.status_code == 403

    @patch('httpx.AsyncClient.post')
    def test_sla_check_success(self, mock_post, client: TestClient, mock_user_data):
        """Test successful SLA compliance check"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/workflows/sla-check", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "requested_by" in data
        assert data["requested_by"] == mock_user_data["user_id"]


@pytest.mark.integration
class TestAPIErrorHandling:
    """Integration tests for API error handling"""
    
    def test_invalid_json_request(self, client: TestClient):
        """Test handling of invalid JSON in request body"""
        headers = {"Content-Type": "application/json"}
        # Send invalid JSON
        response = client.post("/api/v1/workflows", data="invalid-json", headers=headers)
        
        assert response.status_code == 422  # Unprocessable Entity

    def test_missing_required_fields(self, client: TestClient):
        """Test validation of required fields"""
        # Missing required fields
        incomplete_data = {"entity_id": "test-123"}  # Missing definition_id
        
        response = client.post("/api/v1/workflows", json=incomplete_data)
        assert response.status_code in [403, 422]  # Auth error or validation error

    def test_invalid_uuid_format(self, client: TestClient):
        """Test handling of invalid UUID format in URL parameters"""
        response = client.get("/api/v1/workflows/invalid-uuid-format/status")
        assert response.status_code == 403  # Auth error comes first

    @patch('httpx.AsyncClient.post')
    def test_internal_server_error_handling(self, mock_post, client: TestClient, mock_user_data):
        """Test handling of internal server errors"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        # Create a workflow with invalid data that might cause internal errors
        headers = {"Authorization": "Bearer valid.jwt.token"}
        
        # This should trigger an internal error due to invalid definition ID
        workflow_data = {
            "definition_id": "nonexistent-definition",
            "entity_id": "test-123",
            "context": {}
        }
        
        response = client.post("/api/v1/workflows", json=workflow_data, headers=headers)
        
        # Should handle error gracefully
        assert response.status_code in [400, 500]
        assert "detail" in response.json()


@pytest.mark.integration
class TestAPIPerformance:
    """Integration tests for API performance"""
    
    @pytest.mark.slow
    def test_health_endpoint_performance(self, client: TestClient):
        """Test health endpoint response time"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second

    @pytest.mark.slow
    @patch('httpx.AsyncClient.post')
    def test_concurrent_requests(self, mock_post, client: TestClient, mock_user_data):
        """Test handling of concurrent requests"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        
        # Make multiple concurrent requests
        import concurrent.futures
        
        def make_request():
            return client.get("/api/v1/definitions", headers=headers)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200


@pytest.mark.integration
class TestAPIDocumentation:
    """Integration tests for API documentation endpoints"""
    
    def test_openapi_schema_endpoint(self, client: TestClient):
        """Test OpenAPI schema is accessible"""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    def test_docs_endpoint(self, client: TestClient):
        """Test Swagger UI documentation endpoint"""
        response = client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint(self, client: TestClient):
        """Test ReDoc documentation endpoint"""
        response = client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]