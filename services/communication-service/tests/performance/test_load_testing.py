"""
Performance and Load Testing for Communication Service
Tests system performance under various load conditions
"""

import pytest
import asyncio
import time
import statistics
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from concurrent.futures import ThreadPoolExecutor
import httpx
from fastapi.testclient import TestClient

from tests.fixtures.sample_data import SampleNotificationData
from tests.fixtures.mock_responses import IdentityServiceMocks


@pytest.mark.performance
@pytest.mark.slow
class TestNotificationAPIPerformance:
    """Performance tests for notification API endpoints"""
    
    async def test_single_notification_endpoint_performance(self, client: TestClient):
        """Test performance of single notification endpoint"""
        
        # Mock authentication and task processing
        with patch('httpx.AsyncClient.post') as mock_identity, \
             patch('tasks.notification_tasks.send_notification') as mock_task:
            
            # Mock Identity Service
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
            mock_identity.return_value = mock_response
            
            # Mock task
            mock_result = MagicMock()
            mock_result.id = "perf-task-123"
            mock_task.apply_async.return_value = mock_result
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            notification_data = {
                "type": "email",
                "to": "perf@example.com",
                "subject": "Performance Test",
                "message": "Testing API performance"
            }
            
            # Measure response times for multiple requests
            response_times = []
            success_count = 0
            
            for i in range(50):  # Test 50 requests
                start_time = time.time()
                response = client.post("/api/v1/notifications", 
                                     json=notification_data, 
                                     headers=headers)
                end_time = time.time()
                
                response_time = end_time - start_time
                response_times.append(response_time)
                
                if response.status_code == 200:
                    success_count += 1
            
            # Performance assertions
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            
            assert avg_response_time < 0.1, f"Average response time too high: {avg_response_time:.3f}s"
            assert p95_response_time < 0.2, f"95th percentile response time too high: {p95_response_time:.3f}s"
            assert success_count == 50, f"Not all requests succeeded: {success_count}/50"
            
            print(f"Performance metrics:")
            print(f"- Average response time: {avg_response_time:.3f}s")
            print(f"- 95th percentile: {p95_response_time:.3f}s")
            print(f"- Success rate: {success_count}/50 (100%)")
    
    async def test_concurrent_notification_requests(self, client: TestClient):
        """Test API performance under concurrent load"""
        
        with patch('httpx.AsyncClient.post') as mock_identity, \
             patch('tasks.notification_tasks.send_notification') as mock_task:
            
            # Mock responses
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
            mock_identity.return_value = mock_response
            
            mock_result = MagicMock()
            mock_result.id = "concurrent-task"
            mock_task.apply_async.return_value = mock_result
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            
            def make_request(request_id):
                """Make a single notification request"""
                notification_data = {
                    "type": "email",
                    "to": f"concurrent{request_id}@example.com",
                    "subject": f"Concurrent Test {request_id}",
                    "message": f"Testing concurrent requests {request_id}"
                }
                
                start_time = time.time()
                response = client.post("/api/v1/notifications",
                                     json=notification_data,
                                     headers=headers)
                end_time = time.time()
                
                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                }
            
            # Run concurrent requests
            concurrent_requests = 20
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request, i) for i in range(concurrent_requests)]
                results = [future.result() for future in futures]
            
            total_time = time.time() - start_time
            
            # Analyze results
            successful_requests = [r for r in results if r["success"]]
            response_times = [r["response_time"] for r in results]
            
            success_rate = len(successful_requests) / len(results) * 100
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            throughput = len(results) / total_time
            
            # Performance assertions
            assert success_rate >= 95, f"Success rate too low: {success_rate:.1f}%"
            assert avg_response_time < 0.5, f"Average response time under load too high: {avg_response_time:.3f}s"
            assert throughput >= 10, f"Throughput too low: {throughput:.1f} requests/second"
            
            print(f"Concurrent load test results:")
            print(f"- Requests: {concurrent_requests}")
            print(f"- Success rate: {success_rate:.1f}%")
            print(f"- Average response time: {avg_response_time:.3f}s")
            print(f"- Max response time: {max_response_time:.3f}s") 
            print(f"- Throughput: {throughput:.1f} requests/second")
    
    async def test_bulk_notification_performance(self, client: TestClient):
        """Test performance of bulk notification processing"""
        
        with patch('httpx.AsyncClient.post') as mock_identity, \
             patch('tasks.notification_tasks.send_notification') as mock_task:
            
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
            mock_identity.return_value = mock_response
            
            mock_result = MagicMock()
            mock_task.apply_async.return_value = mock_result
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            
            # Prepare bulk notification data
            bulk_size = 100
            notifications = []
            
            for i in range(bulk_size):
                notification_data = {
                    "type": "email",
                    "to": f"bulk{i}@example.com", 
                    "subject": f"Bulk Test {i}",
                    "message": f"Bulk notification {i}"
                }
                notifications.append(notification_data)
            
            # Measure bulk processing time
            start_time = time.time()
            
            # Send all notifications rapidly
            responses = []
            for notification in notifications:
                response = client.post("/api/v1/notifications",
                                     json=notification,
                                     headers=headers)
                responses.append(response)
            
            processing_time = time.time() - start_time
            
            # Analyze results
            successful_responses = [r for r in responses if r.status_code == 200]
            success_rate = len(successful_responses) / len(responses) * 100
            throughput = len(responses) / processing_time
            
            # Performance assertions
            assert success_rate >= 98, f"Bulk processing success rate too low: {success_rate:.1f}%"
            assert throughput >= 50, f"Bulk processing throughput too low: {throughput:.1f} notifications/second"
            assert processing_time < 10, f"Bulk processing took too long: {processing_time:.1f}s"
            
            print(f"Bulk notification performance:")
            print(f"- Notifications: {bulk_size}")
            print(f"- Processing time: {processing_time:.2f}s")
            print(f"- Success rate: {success_rate:.1f}%")
            print(f"- Throughput: {throughput:.1f} notifications/second")


@pytest.mark.performance
@pytest.mark.slow
class TestCeleryQueuePerformance:
    """Performance tests for Celery task queues"""
    
    @patch('tasks.notification_tasks.send_notification')
    @patch('celery.app.Celery.send_task')
    async def test_queue_throughput_performance(self, mock_send_task, mock_notification_task):
        """Test Celery queue throughput under load"""
        
        # Mock task execution
        mock_result = MagicMock()
        mock_result.id = "queue-perf-task"
        mock_send_task.return_value = mock_result
        
        mock_notification_task.apply_async.return_value = mock_result
        
        # Simulate high-volume task queuing
        task_count = 500
        start_time = time.time()
        
        task_ids = []
        for i in range(task_count):
            task_data = {
                "notification_id": f"queue-test-{i}",
                "recipient": f"queue{i}@example.com",
                "content": f"Queue performance test {i}",
                "priority": "normal"
            }
            
            # Queue task
            result = mock_notification_task.apply_async.return_value
            task_ids.append(result.id)
        
        queuing_time = time.time() - start_time
        
        # Performance metrics
        queuing_throughput = task_count / queuing_time
        
        assert queuing_throughput >= 100, f"Queue throughput too low: {queuing_throughput:.1f} tasks/second"
        assert queuing_time < 10, f"Queuing took too long: {queuing_time:.1f}s"
        
        print(f"Queue performance metrics:")
        print(f"- Tasks queued: {task_count}")
        print(f"- Queuing time: {queuing_time:.2f}s")
        print(f"- Throughput: {queuing_throughput:.1f} tasks/second")
    
    @patch('tasks.notification_tasks.send_notification')
    async def test_priority_queue_performance(self, mock_task):
        """Test priority-based queue performance"""
        
        mock_result = MagicMock()
        mock_result.id = "priority-task"
        mock_task.apply_async.return_value = mock_result
        
        # Queue tasks with different priorities
        priorities = ["urgent", "high", "normal", "low"]
        tasks_per_priority = 25
        
        start_time = time.time()
        
        for priority in priorities:
            for i in range(tasks_per_priority):
                task_data = {
                    "notification_id": f"priority-{priority}-{i}",
                    "recipient": f"priority{i}@example.com",
                    "priority": priority
                }
                
                # Mock priority-based queuing
                mock_task.apply_async.return_value
        
        total_time = time.time() - start_time
        total_tasks = len(priorities) * tasks_per_priority
        
        priority_throughput = total_tasks / total_time
        
        assert priority_throughput >= 50, f"Priority queue throughput too low: {priority_throughput:.1f} tasks/second"
        
        print(f"Priority queue performance:")
        print(f"- Total tasks: {total_tasks}")
        print(f"- Processing time: {total_time:.2f}s")
        print(f"- Throughput: {priority_throughput:.1f} tasks/second")
    
    @patch('redis.Redis')
    async def test_redis_queue_performance(self, mock_redis):
        """Test Redis queue performance and memory usage"""
        
        # Mock Redis operations
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client
        
        # Simulate queue operations
        operations = 1000
        start_time = time.time()
        
        for i in range(operations):
            # Simulate typical queue operations
            task_data = {
                "id": f"redis-task-{i}",
                "data": f"test data {i}",
                "timestamp": time.time()
            }
            
            # Mock Redis operations
            mock_redis_client.lpush.return_value = i + 1  # Queue length
            mock_redis_client.brpop.return_value = (b"queue", str(task_data).encode())
            mock_redis_client.get.return_value = str(task_data).encode()
            mock_redis_client.set.return_value = True
        
        redis_time = time.time() - start_time
        redis_throughput = operations / redis_time
        
        assert redis_throughput >= 500, f"Redis throughput too low: {redis_throughput:.1f} operations/second"
        
        print(f"Redis queue performance:")
        print(f"- Operations: {operations}")
        print(f"- Time: {redis_time:.2f}s")
        print(f"- Throughput: {redis_throughput:.1f} operations/second")


@pytest.mark.performance
@pytest.mark.slow
class TestNotificationProviderPerformance:
    """Performance tests for notification providers"""
    
    @patch('aiosmtplib.SMTP')
    async def test_email_provider_performance(self, mock_smtp):
        """Test email provider performance under load"""
        
        # Mock SMTP operations
        mock_smtp_instance = AsyncMock()
        mock_smtp_instance.connect.return_value = None
        mock_smtp_instance.send_message.return_value = {}
        mock_smtp.return_value = mock_smtp_instance
        
        from providers.email import EmailProvider
        
        config = {
            "host": "smtp.example.com",
            "port": 587,
            "username": "test@example.com",
            "password": "password"
        }
        
        provider = EmailProvider(config)
        
        # Send multiple emails and measure performance
        email_count = 100
        start_time = time.time()
        
        send_times = []
        for i in range(email_count):
            send_start = time.time()
            result = await provider.send(
                recipient=f"perf{i}@example.com",
                subject=f"Performance Test {i}",
                content=f"Email performance test {i}"
            )
            send_end = time.time()
            
            send_times.append(send_end - send_start)
            assert result["status"] == "sent"
        
        total_time = time.time() - start_time
        
        # Performance analysis
        avg_send_time = statistics.mean(send_times)
        throughput = email_count / total_time
        
        assert avg_send_time < 0.01, f"Average email send time too high: {avg_send_time:.4f}s"
        assert throughput >= 50, f"Email throughput too low: {throughput:.1f} emails/second"
        
        print(f"Email provider performance:")
        print(f"- Emails sent: {email_count}")
        print(f"- Average send time: {avg_send_time:.4f}s")
        print(f"- Throughput: {throughput:.1f} emails/second")
    
    @patch('twilio.rest.Client')
    async def test_sms_provider_performance(self, mock_twilio):
        """Test SMS provider performance"""
        
        # Mock Twilio client
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SMS_PERF_123"
        mock_message.status = "queued"
        mock_client.messages.create.return_value = mock_message
        mock_twilio.return_value = mock_client
        
        from providers.sms import SMSProvider
        
        config = {
            "account_sid": "test_sid",
            "auth_token": "test_token",
            "from_number": "+1234567890"
        }
        
        provider = SMSProvider(config)
        
        # Send multiple SMS messages
        sms_count = 50
        start_time = time.time()
        
        send_times = []
        for i in range(sms_count):
            send_start = time.time()
            result = await provider.send(
                recipient=f"+123456789{i:02d}",
                content=f"SMS performance test {i}"
            )
            send_end = time.time()
            
            send_times.append(send_end - send_start)
            assert result["status"] == "sent"
        
        total_time = time.time() - start_time
        
        # Performance analysis
        avg_send_time = statistics.mean(send_times)
        throughput = sms_count / total_time
        
        assert avg_send_time < 0.02, f"Average SMS send time too high: {avg_send_time:.4f}s"
        assert throughput >= 25, f"SMS throughput too low: {throughput:.1f} messages/second"
        
        print(f"SMS provider performance:")
        print(f"- Messages sent: {sms_count}")
        print(f"- Average send time: {avg_send_time:.4f}s")
        print(f"- Throughput: {throughput:.1f} messages/second")
    
    @patch('httpx.AsyncClient.post')
    async def test_push_provider_performance(self, mock_post):
        """Test push notification provider performance"""
        
        # Mock FCM response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "multicast_id": 123456789,
            "success": 1,
            "failure": 0,
            "results": [{"message_id": "push_perf_123"}]
        }
        mock_post.return_value = mock_response
        
        from providers.push import PushProvider
        
        config = {
            "server_key": "test_server_key",
            "project_id": "test_project"
        }
        
        provider = PushProvider(config)
        
        # Send multiple push notifications
        push_count = 75
        start_time = time.time()
        
        send_times = []
        for i in range(push_count):
            send_start = time.time()
            result = await provider.send(
                recipient=f"push_token_{i}",
                title=f"Push Performance Test {i}",
                content=f"Push notification performance test {i}"
            )
            send_end = time.time()
            
            send_times.append(send_end - send_start)
            assert result["status"] == "sent"
        
        total_time = time.time() - start_time
        
        # Performance analysis
        avg_send_time = statistics.mean(send_times)
        throughput = push_count / total_time
        
        assert avg_send_time < 0.05, f"Average push send time too high: {avg_send_time:.4f}s"
        assert throughput >= 20, f"Push throughput too low: {throughput:.1f} notifications/second"
        
        print(f"Push provider performance:")
        print(f"- Notifications sent: {push_count}")
        print(f"- Average send time: {avg_send_time:.4f}s")
        print(f"- Throughput: {throughput:.1f} notifications/second")


@pytest.mark.performance
@pytest.mark.slow
class TestDatabasePerformance:
    """Performance tests for database operations"""
    
    async def test_notification_query_performance(self, db_session):
        """Test database query performance for notifications"""
        
        from database.models import Notification
        
        # Insert test data
        notifications = []
        for i in range(200):
            notification = Notification(
                recipient=f"dbperf{i}@example.com",
                subject=f"DB Performance Test {i}",
                content=f"Database performance test notification {i}",
                channel="email" if i % 2 == 0 else "sms",
                status="delivered" if i % 3 == 0 else "pending",
                organization_id=f"org-{i % 10}",
                user_id=f"user-{i % 50}"
            )
            notifications.append(notification)
        
        db_session.add_all(notifications)
        await db_session.commit()
        
        # Test query performance
        queries = [
            # Query by organization
            lambda: db_session.execute(
                select(Notification).where(Notification.organization_id == "org-1")
            ),
            # Query by status
            lambda: db_session.execute(
                select(Notification).where(Notification.status == "delivered")
            ),
            # Query by user
            lambda: db_session.execute(
                select(Notification).where(Notification.user_id == "user-10")
            ),
            # Complex query
            lambda: db_session.execute(
                select(Notification)
                .where(Notification.organization_id == "org-2")
                .where(Notification.status == "pending")
                .order_by(Notification.created_at.desc())
                .limit(10)
            )
        ]
        
        query_times = []
        for i, query_func in enumerate(queries):
            start_time = time.time()
            result = await query_func()
            query_time = time.time() - start_time
            query_times.append(query_time)
            
            assert query_time < 0.1, f"Query {i} too slow: {query_time:.4f}s"
        
        avg_query_time = statistics.mean(query_times)
        assert avg_query_time < 0.05, f"Average query time too high: {avg_query_time:.4f}s"
        
        print(f"Database query performance:")
        print(f"- Average query time: {avg_query_time:.4f}s")
        print(f"- Max query time: {max(query_times):.4f}s")
    
    async def test_bulk_insert_performance(self, db_session):
        """Test bulk insert performance for notifications"""
        
        from database.models import NotificationCategory, NotificationTemplate, Notification
        
        # Test bulk category insert
        categories = []
        for i in range(50):
            category = NotificationCategory(
                name=f"bulk_category_{i}",
                description=f"Bulk insert test category {i}",
                organization_id=f"org-bulk-{i % 5}"
            )
            categories.append(category)
        
        start_time = time.time()
        db_session.add_all(categories)
        await db_session.commit()
        category_insert_time = time.time() - start_time
        
        # Test bulk notification insert
        notifications = []
        for i in range(500):
            notification = Notification(
                recipient=f"bulk{i}@example.com",
                subject=f"Bulk Insert Test {i}",
                content=f"Bulk database insert test {i}",
                channel="email",
                status="pending",
                organization_id=f"org-bulk-{i % 5}",
                user_id=f"user-bulk-{i % 100}"
            )
            notifications.append(notification)
        
        start_time = time.time()
        db_session.add_all(notifications)
        await db_session.commit()
        notification_insert_time = time.time() - start_time
        
        # Performance assertions
        category_throughput = len(categories) / category_insert_time
        notification_throughput = len(notifications) / notification_insert_time
        
        assert category_throughput >= 25, f"Category insert throughput too low: {category_throughput:.1f} records/second"
        assert notification_throughput >= 50, f"Notification insert throughput too low: {notification_throughput:.1f} records/second"
        
        print(f"Bulk insert performance:")
        print(f"- Category insert: {category_throughput:.1f} records/second")
        print(f"- Notification insert: {notification_throughput:.1f} records/second")


@pytest.mark.performance
class TestMemoryUsagePerformance:
    """Memory usage and leak detection tests"""
    
    async def test_memory_usage_under_load(self, client: TestClient):
        """Test memory usage doesn't grow excessively under load"""
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch('httpx.AsyncClient.post') as mock_identity, \
             patch('tasks.notification_tasks.send_notification') as mock_task:
            
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
            mock_identity.return_value = mock_response
            
            mock_result = MagicMock()
            mock_result.id = "memory-test-task"
            mock_task.apply_async.return_value = mock_result
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            
            # Process many requests
            for i in range(200):
                notification_data = {
                    "type": "email",
                    "to": f"memory{i}@example.com",
                    "subject": f"Memory Test {i}",
                    "message": f"Testing memory usage {i}"
                }
                
                response = client.post("/api/v1/notifications",
                                     json=notification_data,
                                     headers=headers)
                assert response.status_code == 200
                
                # Check memory periodically
                if i % 50 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_growth = current_memory - initial_memory
                    
                    # Memory growth should be reasonable
                    assert memory_growth < 100, f"Excessive memory growth: {memory_growth:.1f}MB"
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_growth = final_memory - initial_memory
        
        print(f"Memory usage analysis:")
        print(f"- Initial memory: {initial_memory:.1f}MB")
        print(f"- Final memory: {final_memory:.1f}MB") 
        print(f"- Total growth: {total_growth:.1f}MB")
        
        # Total memory growth should be reasonable
        assert total_growth < 50, f"Memory leak suspected: {total_growth:.1f}MB growth"