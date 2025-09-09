"""
Integration tests for JWT authentication with endpoints
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock

class TestEndpointAuthentication:
    """Test that all protected endpoints require authentication"""
    
    def test_health_endpoint_no_auth_required(self, client):
        """Test that health endpoint is accessible without authentication"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "service" in data
        assert "workflow-intelligence-service" in data["service"]
    
    def test_workflow_creation_requires_auth(self, client):
        """Test that workflow creation requires authentication"""
        workflow_data = {
            "definition_id": "approval-workflow",
            "entity_id": "test-123",
            "context": {}
        }
        
        response = client.post("/api/v1/workflows", json=workflow_data)
        assert response.status_code == 403  # FastAPI returns 403 for missing auth
    
    def test_workflow_status_requires_auth(self, client):
        """Test that workflow status endpoint requires authentication"""
        response = client.get("/api/v1/workflows/test-123/status")
        assert response.status_code == 403
    
    def test_workflow_advance_requires_auth(self, client):
        """Test that workflow advance endpoint requires authentication"""
        transition_data = {"action": "approve", "data": {}}
        
        response = client.patch("/api/v1/workflows/test-123/next", json=transition_data)
        assert response.status_code == 403
    
    def test_user_workflows_requires_auth(self, client):
        """Test that user workflows endpoint requires authentication"""
        response = client.get("/api/v1/workflows/user/test-user")
        assert response.status_code == 403
    
    def test_ai_summarize_requires_auth(self, client):
        """Test that AI summarization requires authentication"""
        ai_data = {
            "text": "This is test text to summarize",
            "task_type": "summarize",
            "context": {}
        }
        
        response = client.post("/api/v1/ai/summarize", json=ai_data)
        assert response.status_code == 403
    
    def test_ai_suggest_requires_auth(self, client):
        """Test that AI suggestions require authentication"""
        ai_data = {
            "text": "Test text for suggestions",
            "task_type": "suggest", 
            "context": {}
        }
        
        response = client.post("/api/v1/ai/suggest", json=ai_data)
        assert response.status_code == 403
    
    def test_ai_analyze_requires_auth(self, client):
        """Test that AI analysis requires authentication"""
        ai_data = {
            "text": "Test text for analysis",
            "task_type": "analyze",
            "context": {}
        }
        
        response = client.post("/api/v1/ai/analyze", json=ai_data)
        assert response.status_code == 403
    
    def test_definitions_list_requires_auth(self, client):
        """Test that workflow definitions listing requires authentication"""
        response = client.get("/api/v1/definitions")
        assert response.status_code == 403
    
    def test_definitions_create_requires_auth(self, client):
        """Test that workflow definition creation requires authentication"""
        definition_data = {
            "name": "Test Definition",
            "states": ["start", "end"],
            "transitions": []
        }
        
        response = client.post("/api/v1/definitions", json=definition_data)
        assert response.status_code == 403
    
    def test_workflow_stats_requires_auth(self, client):
        """Test that workflow statistics require authentication"""
        response = client.get("/api/v1/workflows/stats")
        assert response.status_code == 403
    
    def test_sla_check_requires_auth(self, client):
        """Test that SLA compliance check requires authentication"""
        response = client.get("/api/v1/workflows/sla-check")
        assert response.status_code == 403

class TestAuthenticatedEndpointAccess:
    """Test endpoints with valid authentication"""
    
    def test_workflow_creation_with_auth(self, client, mock_auth_headers):
        """Test workflow creation with valid authentication"""
        workflow_data = {
            "definition_id": "approval-workflow", 
            "entity_id": "test-123",
            "context": {}
        }
        
        with patch("main.validate_jwt_token") as mock_validate:
            mock_validate.return_value = {
                "user_id": "user-123",
                "email": "test@example.com",
                "organization_id": "org-123",
                "roles": ["user", "workflow_user"]
            }
            
            response = client.post(
                "/api/v1/workflows", 
                json=workflow_data,
                headers=mock_auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["created_by"] == "user-123"
            assert data["organization"] == "org-123"
    
    def test_workflow_status_with_auth(self, client, mock_auth_headers):
        """Test workflow status with valid authentication"""
        with patch("main.validate_jwt_token") as mock_validate:
            mock_validate.return_value = {
                "user_id": "user-123",
                "organization_id": "org-123",
                "roles": ["user"]
            }
            
            response = client.get(
                "/api/v1/workflows/test-123/status",
                headers=mock_auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["requested_by"] == "user-123"
    
    def test_ai_endpoints_with_auth(self, client, mock_auth_headers):
        """Test AI endpoints with valid authentication"""
        with patch("main.validate_jwt_token") as mock_validate:
            mock_validate.return_value = {
                "user_id": "user-123",
                "organization_id": "org-123",
                "roles": ["user"]
            }
            
            ai_data = {
                "text": "Test text",
                "task_type": "summarize",
                "context": {}
            }
            
            # Test summarization
            response = client.post(
                "/api/v1/ai/summarize",
                json=ai_data,
                headers=mock_auth_headers
            )
            assert response.status_code == 200
            assert response.json()["requested_by"] == "user-123"
            
            # Test suggestions
            response = client.post(
                "/api/v1/ai/suggest",
                json=ai_data,
                headers=mock_auth_headers
            )
            assert response.status_code == 200
            assert response.json()["requested_by"] == "user-123"
            
            # Test analysis
            response = client.post(
                "/api/v1/ai/analyze", 
                json=ai_data,
                headers=mock_auth_headers
            )
            assert response.status_code == 200
            assert response.json()["requested_by"] == "user-123"

class TestAuthorizationChecks:
    """Test authorization rules for different user roles"""
    
    def test_user_workflows_access_control(self, client, mock_auth_headers):
        """Test that users can only access their own workflows"""
        with patch("main.validate_jwt_token") as mock_validate:
            mock_validate.return_value = {
                "user_id": "user-123",
                "organization_id": "org-123",
                "roles": ["user"]
            }
            
            # User trying to access their own workflows - should succeed
            response = client.get(
                "/api/v1/workflows/user/user-123",
                headers=mock_auth_headers
            )
            assert response.status_code == 200
            
            # User trying to access another user's workflows - should fail
            response = client.get(
                "/api/v1/workflows/user/other-user",
                headers=mock_auth_headers
            )
            assert response.status_code == 403
            assert "Access denied" in response.json()["detail"]
    
    def test_admin_can_access_all_workflows(self, client, mock_auth_headers):
        """Test that admin users can access any user's workflows"""
        with patch("main.validate_jwt_token") as mock_validate:
            mock_validate.return_value = {
                "user_id": "admin-123",
                "organization_id": "org-123",
                "roles": ["admin", "user"]
            }
            
            # Admin accessing another user's workflows - should succeed
            response = client.get(
                "/api/v1/workflows/user/other-user",
                headers=mock_auth_headers
            )
            assert response.status_code == 200
    
    def test_workflow_definition_creation_requires_admin(self, client, mock_auth_headers):
        """Test that workflow definition creation requires admin role"""
        definition_data = {
            "name": "Test Definition",
            "states": ["start", "end"],
            "transitions": []
        }
        
        # Regular user should be denied
        with patch("main.validate_jwt_token") as mock_validate:
            mock_validate.return_value = {
                "user_id": "user-123",
                "organization_id": "org-123", 
                "roles": ["user"]
            }
            
            response = client.post(
                "/api/v1/definitions",
                json=definition_data,
                headers=mock_auth_headers
            )
            assert response.status_code == 403
            assert "Insufficient permissions" in response.json()["detail"]
        
        # Admin user should be allowed
        with patch("main.validate_jwt_token") as mock_validate:
            mock_validate.return_value = {
                "user_id": "admin-123",
                "organization_id": "org-123",
                "roles": ["admin", "user"]
            }
            
            response = client.post(
                "/api/v1/definitions",
                json=definition_data,
                headers=mock_auth_headers
            )
            assert response.status_code == 200
            assert response.json()["created_by"] == "admin-123"

class TestAuthenticationErrorHandling:
    """Test various authentication error scenarios"""
    
    def test_malformed_authorization_header(self, client):
        """Test handling of malformed Authorization header"""
        # Missing 'Bearer' prefix
        response = client.post(
            "/api/v1/workflows",
            json={"definition_id": "test", "entity_id": "test"},
            headers={"Authorization": "invalid-token-format"}
        )
        assert response.status_code in [401, 403, 422]  # FastAPI may return different codes
    
    def test_empty_authorization_header(self, client):
        """Test handling of empty Authorization header"""
        response = client.post(
            "/api/v1/workflows",
            json={"definition_id": "test", "entity_id": "test"},
            headers={"Authorization": ""}
        )
        assert response.status_code in [401, 403, 422]
    
    def test_missing_authorization_header(self, client):
        """Test handling of completely missing Authorization header"""
        response = client.post(
            "/api/v1/workflows",
            json={"definition_id": "test", "entity_id": "test"}
        )
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403 for missing header