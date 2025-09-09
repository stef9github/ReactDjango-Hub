"""
Performance tests for Workflow Intelligence Service
"""
import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


@pytest.mark.performance
@pytest.mark.slow
class TestWorkflowPerformance:
    """Performance tests for workflow operations"""
    
    @patch('httpx.AsyncClient.post')
    def test_workflow_creation_performance(self, mock_post, client: TestClient, mock_user_data):
        """Test workflow creation performance under load"""
        # Mock identity service
        identity_mock_response = AsyncMock()
        identity_mock_response.status_code = 200
        identity_mock_response.json.return_value = mock_user_data
        mock_post.return_value = identity_mock_response
        
        headers = {"Authorization": "Bearer valid_token"}
        workflow_data = {
            "definition_id": "perf-test-def",
            "entity_id": "perf-test-entity",
            "title": "Performance Test Workflow",
            "context_data": {"test": "performance"}
        }
        
        # Test single request performance
        start_time = time.time()
        response = client.post("/api/v1/workflows", json=workflow_data, headers=headers)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5  # Should complete within 500ms
        
    def test_bulk_workflow_creation_performance(self, client: TestClient, mock_user_data):
        """Test bulk workflow creation performance"""
        with patch('httpx.AsyncClient.post') as mock_post:
            identity_mock_response = AsyncMock()
            identity_mock_response.status_code = 200
            identity_mock_response.json.return_value = mock_user_data
            mock_post.return_value = identity_mock_response
            
            headers = {"Authorization": "Bearer valid_token"}
            
            # Create multiple workflows concurrently
            def create_workflow(index):
                workflow_data = {
                    "definition_id": f"bulk-test-def-{index}",
                    "entity_id": f"bulk-test-entity-{index}",
                    "title": f"Bulk Test Workflow {index}",
                    "context_data": {"test": "bulk_performance", "index": index}
                }
                start_time = time.time()
                response = client.post("/api/v1/workflows", json=workflow_data, headers=headers)
                response_time = time.time() - start_time
                return response.status_code, response_time
            
            # Test with 10 concurrent requests
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(create_workflow, i) for i in range(10)]
                results = [future.result() for future in futures]
            total_time = time.time() - start_time
            
            # Verify all requests succeeded
            for status_code, response_time in results:
                assert status_code == 200
                assert response_time < 1.0  # Individual request within 1 second
            
            # Total time for 10 concurrent requests should be reasonable
            assert total_time < 3.0  # All requests within 3 seconds
    
    @patch('httpx.AsyncClient.post')
    def test_workflow_state_transition_performance(self, mock_post, client: TestClient, mock_user_data):
        """Test workflow state transition performance"""
        # Mock identity service
        identity_mock_response = AsyncMock()
        identity_mock_response.status_code = 200
        identity_mock_response.json.return_value = mock_user_data
        mock_post.return_value = identity_mock_response
        
        headers = {"Authorization": "Bearer valid_token"}
        
        # Create workflow first
        workflow_data = {
            "definition_id": "state-perf-test",
            "entity_id": "state-perf-entity",
            "title": "State Performance Test"
        }
        create_response = client.post("/api/v1/workflows", json=workflow_data, headers=headers)
        assert create_response.status_code == 200
        workflow_id = create_response.json()["id"]
        
        # Test state transition performance
        advance_data = {
            "action": "submit_for_review",
            "comment": "Performance test state transition"
        }
        
        start_time = time.time()
        response = client.post(f"/api/v1/workflows/{workflow_id}/advance", 
                              json=advance_data, headers=headers)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.3  # State transition within 300ms
    
    @patch('httpx.AsyncClient.post')
    def test_workflow_query_performance(self, mock_post, client: TestClient, mock_user_data):
        """Test workflow query performance"""
        # Mock identity service
        identity_mock_response = AsyncMock()
        identity_mock_response.status_code = 200
        identity_mock_response.json.return_value = mock_user_data
        mock_post.return_value = identity_mock_response
        
        headers = {"Authorization": "Bearer valid_token"}
        
        # Test various query endpoints performance
        test_endpoints = [
            "/api/v1/workflows/stats",
            "/api/v1/workflow-definitions",
            "/health/detailed"
        ]
        
        for endpoint in test_endpoints:
            start_time = time.time()
            response = client.get(endpoint, headers=headers)
            response_time = time.time() - start_time
            
            assert response.status_code in [200, 401]  # 401 for unprotected endpoints is OK
            assert response_time < 0.5  # Query within 500ms


@pytest.mark.performance
@pytest.mark.slow
class TestAIServicePerformance:
    """Performance tests for AI service integration"""
    
    @patch('httpx.AsyncClient.post')
    def test_ai_summarization_performance(self, mock_post, client: TestClient, mock_user_data):
        """Test AI summarization performance"""
        # Mock both identity and AI services
        def mock_post_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            if 'identity-service' in str(url):
                identity_response = AsyncMock()
                identity_response.status_code = 200
                identity_response.json.return_value = mock_user_data
                return identity_response
            else:
                # Mock AI service with realistic delay
                ai_response = AsyncMock()
                ai_response.status_code = 200
                ai_response.json.return_value = {
                    "summary": "Performance test summary",
                    "confidence": 0.95,
                    "processing_time_ms": 1500
                }
                return ai_response
        
        mock_post.side_effect = mock_post_side_effect
        
        headers = {"Authorization": "Bearer valid_token"}
        summarize_data = {
            "text": "This is a performance test document. " * 100,  # Longer text
            "max_length": 50
        }
        
        start_time = time.time()
        response = client.post("/api/v1/ai/summarize", json=summarize_data, headers=headers)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 5.0  # AI processing within 5 seconds
    
    @patch('httpx.AsyncClient.post') 
    def test_ai_analysis_concurrent_performance(self, mock_post, client: TestClient, mock_user_data):
        """Test AI analysis under concurrent load"""
        def mock_post_side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            if 'identity-service' in str(url):
                identity_response = AsyncMock()
                identity_response.status_code = 200
                identity_response.json.return_value = mock_user_data
                return identity_response
            else:
                ai_response = AsyncMock()
                ai_response.status_code = 200
                ai_response.json.return_value = {
                    "analysis": {"sentiment": "neutral", "topics": ["test"]},
                    "confidence": 0.85
                }
                return ai_response
        
        mock_post.side_effect = mock_post_side_effect
        
        headers = {"Authorization": "Bearer valid_token"}
        
        def analyze_text(index):
            analyze_data = {
                "text": f"Performance analysis test document {index}",
                "analysis_type": "basic"
            }
            start_time = time.time()
            response = client.post("/api/v1/ai/analyze", json=analyze_data, headers=headers)
            response_time = time.time() - start_time
            return response.status_code, response_time
        
        # Test 5 concurrent AI analysis requests
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(analyze_text, i) for i in range(5)]
            results = [future.result() for future in futures]
        total_time = time.time() - start_time
        
        # Verify all requests succeeded
        for status_code, response_time in results:
            assert status_code == 200
            assert response_time < 6.0  # Individual AI request within 6 seconds
        
        # Total time should be reasonable for concurrent processing
        assert total_time < 10.0  # All AI requests within 10 seconds


@pytest.mark.performance
@pytest.mark.slow
class TestDatabasePerformance:
    """Performance tests for database operations"""
    
    def test_workflow_history_query_performance(self, client: TestClient, mock_user_data, test_session):
        """Test workflow history query performance with large datasets"""
        from models import WorkflowDefinition, WorkflowInstance, WorkflowHistory
        
        # Create test workflow
        definition = WorkflowDefinition(
            name="Performance Test Workflow",
            category="performance",
            initial_state="start",
            organization_id="perf-org",
            states=[{"name": "start"}, {"name": "end"}],
            transitions=[{"from": "start", "to": "end", "action": "complete"}]
        )
        test_session.add(definition)
        test_session.commit()
        
        instance = WorkflowInstance(
            definition_id=definition.id,
            entity_id="perf-entity",
            current_state="start",
            organization_id="perf-org",
            created_by="perf-user"
        )
        test_session.add(instance)
        test_session.commit()
        
        # Create many history entries
        history_entries = []
        for i in range(100):
            history = WorkflowHistory(
                instance_id=instance.id,
                to_state="end" if i % 2 else "start",
                action=f"action_{i}",
                triggered_by=f"user_{i % 10}"
            )
            history_entries.append(history)
        
        test_session.add_all(history_entries)
        test_session.commit()
        
        # Test query performance
        with patch('httpx.AsyncClient.post') as mock_post:
            identity_mock_response = AsyncMock()
            identity_mock_response.status_code = 200
            identity_mock_response.json.return_value = mock_user_data
            mock_post.return_value = identity_mock_response
            
            headers = {"Authorization": "Bearer valid_token"}
            
            start_time = time.time()
            response = client.get(f"/api/v1/workflows/{instance.id}/history", headers=headers)
            query_time = time.time() - start_time
            
            assert response.status_code == 200
            assert len(response.json()) == 100
            assert query_time < 1.0  # Query 100 history entries within 1 second
    
    def test_workflow_statistics_performance(self, client: TestClient, mock_user_data, test_session):
        """Test workflow statistics calculation performance"""
        from models import WorkflowDefinition, WorkflowInstance
        
        # Create multiple workflows for statistics
        definitions = []
        instances = []
        
        for i in range(50):
            definition = WorkflowDefinition(
                name=f"Stats Test Workflow {i}",
                category="stats_test",
                initial_state="start",
                organization_id="stats-org",
                states=[{"name": "start"}, {"name": "end"}],
                transitions=[]
            )
            definitions.append(definition)
        
        test_session.add_all(definitions)
        test_session.commit()
        
        for i, definition in enumerate(definitions):
            for j in range(5):  # 5 instances per definition
                instance = WorkflowInstance(
                    definition_id=definition.id,
                    entity_id=f"stats-entity-{i}-{j}",
                    current_state="start" if j % 2 else "end",
                    status="active" if j % 2 else "completed",
                    organization_id="stats-org",
                    created_by=f"stats-user-{j}"
                )
                instances.append(instance)
        
        test_session.add_all(instances)
        test_session.commit()
        
        # Test statistics query performance
        with patch('httpx.AsyncClient.post') as mock_post:
            identity_mock_response = AsyncMock()
            identity_mock_response.status_code = 200
            identity_mock_response.json.return_value = mock_user_data
            mock_post.return_value = identity_mock_response
            
            headers = {"Authorization": "Bearer valid_token"}
            
            start_time = time.time()
            response = client.get("/api/v1/workflows/stats", headers=headers)
            stats_time = time.time() - start_time
            
            assert response.status_code == 200
            stats = response.json()
            assert "total_workflows" in stats
            assert stats["total_workflows"] >= 250  # 50 definitions * 5 instances
            assert stats_time < 2.0  # Statistics calculation within 2 seconds


@pytest.mark.performance
@pytest.mark.slow
class TestMemoryPerformance:
    """Memory usage and leak tests"""
    
    def test_memory_usage_during_bulk_operations(self, client: TestClient, mock_user_data):
        """Test memory usage during bulk workflow operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch('httpx.AsyncClient.post') as mock_post:
            identity_mock_response = AsyncMock()
            identity_mock_response.status_code = 200
            identity_mock_response.json.return_value = mock_user_data
            mock_post.return_value = identity_mock_response
            
            headers = {"Authorization": "Bearer valid_token"}
            
            # Perform many workflow operations
            for i in range(100):
                workflow_data = {
                    "definition_id": f"memory-test-{i}",
                    "entity_id": f"memory-entity-{i}",
                    "title": f"Memory Test Workflow {i}",
                    "context_data": {"large_data": "x" * 1000}  # 1KB per workflow
                }
                response = client.post("/api/v1/workflows", json=workflow_data, headers=headers)
                assert response.status_code == 200
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB for 100 workflows)
        assert memory_increase < 50, f"Memory increased by {memory_increase}MB, which may indicate a leak"


@pytest.mark.benchmark
class TestBenchmarks:
    """Benchmark tests using pytest-benchmark"""
    
    def test_workflow_creation_benchmark(self, benchmark, client: TestClient, mock_user_data):
        """Benchmark workflow creation performance"""
        with patch('httpx.AsyncClient.post') as mock_post:
            identity_mock_response = AsyncMock()
            identity_mock_response.status_code = 200
            identity_mock_response.json.return_value = mock_user_data
            mock_post.return_value = identity_mock_response
            
            headers = {"Authorization": "Bearer valid_token"}
            workflow_data = {
                "definition_id": "benchmark-def",
                "entity_id": "benchmark-entity",
                "title": "Benchmark Workflow"
            }
            
            def create_workflow():
                response = client.post("/api/v1/workflows", json=workflow_data, headers=headers)
                assert response.status_code == 200
                return response
            
            # Benchmark the operation
            result = benchmark(create_workflow)
            assert result.status_code == 200
    
    def test_workflow_query_benchmark(self, benchmark, client: TestClient, mock_user_data):
        """Benchmark workflow query performance"""
        with patch('httpx.AsyncClient.post') as mock_post:
            identity_mock_response = AsyncMock()
            identity_mock_response.status_code = 200
            identity_mock_response.json.return_value = mock_user_data
            mock_post.return_value = identity_mock_response
            
            headers = {"Authorization": "Bearer valid_token"}
            
            def query_workflows():
                response = client.get("/api/v1/workflows/stats", headers=headers)
                assert response.status_code == 200
                return response
            
            # Benchmark the operation
            result = benchmark(query_workflows)
            assert result.status_code == 200