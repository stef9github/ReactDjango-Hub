"""
Locust Load Testing Configuration for Communication Service
Run with: locust -f tests/performance/locustfile.py --host=http://localhost:8002
"""

import json
import random
from datetime import datetime
from locust import HttpUser, task, between


class NotificationUser(HttpUser):
    """Simulated user for notification load testing"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Setup user session"""
        # Mock JWT token for testing
        self.headers = {
            "Authorization": "Bearer mock.jwt.token.for.load.testing",
            "Content-Type": "application/json"
        }
        
        # User data for varied testing
        self.user_id = f"load_test_user_{random.randint(1, 1000)}"
        self.organization_id = f"org_{random.randint(1, 10)}"
    
    @task(10)  # Weight: high frequency
    def send_email_notification(self):
        """Send email notification - most common operation"""
        notification_data = {
            "type": "email",
            "to": f"loadtest{random.randint(1, 10000)}@example.com",
            "subject": f"Load Test Email - {datetime.now().isoformat()}",
            "message": "This is a load testing email notification to verify system performance under stress.",
            "priority": random.choice(["urgent", "high", "normal", "low"]),
            "data": {
                "test_type": "load_test",
                "user_id": self.user_id,
                "organization_id": self.organization_id,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        with self.client.post("/api/v1/notifications",
                              json=notification_data,
                              headers=self.headers,
                              catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Email notification failed: {response.status_code}")
    
    @task(5)  # Weight: medium frequency
    def send_sms_notification(self):
        """Send SMS notification"""
        notification_data = {
            "type": "sms",
            "to": f"+1{random.randint(2000000000, 9999999999)}",
            "message": f"Load test SMS {random.randint(1000, 9999)}. System performance verification in progress.",
            "priority": random.choice(["urgent", "high", "normal"]),
            "data": {
                "test_type": "load_test_sms",
                "user_id": self.user_id
            }
        }
        
        with self.client.post("/api/v1/notifications",
                              json=notification_data,
                              headers=self.headers,
                              catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"SMS notification failed: {response.status_code}")
    
    @task(3)  # Weight: lower frequency
    def send_push_notification(self):
        """Send push notification"""
        notification_data = {
            "type": "push",
            "to": f"push_token_{random.randint(100000, 999999)}",
            "title": "Load Test Push Notification",
            "message": "Testing push notification system performance",
            "data": {
                "test_type": "load_test_push",
                "deep_link": f"/test/{random.randint(1, 100)}",
                "user_id": self.user_id
            }
        }
        
        with self.client.post("/api/v1/notifications",
                              json=notification_data,
                              headers=self.headers,
                              catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Push notification failed: {response.status_code}")
    
    @task(4)  # Weight: medium frequency
    def get_unread_notifications(self):
        """Get unread notifications"""
        with self.client.get("/api/v1/notifications/unread",
                             headers=self.headers,
                             catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get unread notifications failed: {response.status_code}")
    
    @task(2)  # Weight: low frequency
    def mark_notifications_read(self):
        """Mark notifications as read"""
        request_data = {
            "notification_ids": [
                f"notif_{random.randint(1, 1000)}_{i}" 
                for i in range(random.randint(1, 5))
            ]
        }
        
        with self.client.post("/api/v1/notifications/mark-read",
                              json=request_data,
                              headers=self.headers,
                              catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Mark read failed: {response.status_code}")
    
    @task(1)  # Weight: very low frequency
    def get_notification_status(self):
        """Check notification status"""
        notification_id = f"status_test_{random.randint(1, 100)}"
        
        with self.client.get(f"/api/v1/notifications/{notification_id}/status",
                             headers=self.headers,
                             catch_response=True) as response:
            if response.status_code in [200, 404]:  # 404 is acceptable for random IDs
                response.success()
            else:
                response.failure(f"Status check failed: {response.status_code}")
    
    @task(1)  # Weight: very low frequency  
    def health_check(self):
        """Health check endpoint"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")


class AdminUser(HttpUser):
    """Simulated admin user for administrative operations"""
    
    wait_time = between(5, 10)  # Admins operate less frequently
    weight = 1  # Lower weight (fewer admin users)
    
    def on_start(self):
        """Setup admin session"""
        self.headers = {
            "Authorization": "Bearer admin.jwt.token.for.load.testing",
            "Content-Type": "application/json"
        }
    
    @task(5)
    def create_notification_template(self):
        """Create notification template"""
        template_data = {
            "name": f"Load Test Template {random.randint(1, 1000)}",
            "subject": "Load Test Template - {{ user_name }}",
            "content": "Hello {{ user_name }}, this is a load test template notification for {{ organization_name }}.",
            "channel": random.choice(["email", "sms", "push"]),
            "variables": ["user_name", "organization_name"],
            "metadata": {
                "created_by": "load_test",
                "test_type": "template_creation"
            }
        }
        
        with self.client.post("/api/v1/templates",
                              json=template_data,
                              headers=self.headers,
                              catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Template creation failed: {response.status_code}")
    
    @task(3)
    def get_templates_list(self):
        """Get templates list"""
        params = {
            "page": random.randint(1, 5),
            "page_size": 20,
            "channel": random.choice(["email", "sms", "push", ""])
        }
        
        with self.client.get("/api/v1/templates",
                             params=params,
                             headers=self.headers,
                             catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get templates failed: {response.status_code}")
    
    @task(2)
    def get_queue_status(self):
        """Get queue status (admin only)"""
        with self.client.get("/api/v1/queue/status",
                             headers=self.headers,
                             catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Queue status failed: {response.status_code}")
    
    @task(1)
    def get_analytics(self):
        """Get notification analytics (admin only)"""
        params = {
            "start_date": "2024-01-01",
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "channel": random.choice(["email", "sms", "push", "all"])
        }
        
        with self.client.get("/api/v1/analytics/notifications",
                             params=params,
                             headers=self.headers,
                             catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Analytics failed: {response.status_code}")


class HighVolumeUser(HttpUser):
    """High-volume user for stress testing"""
    
    wait_time = between(0.1, 0.5)  # Very frequent requests
    weight = 2  # More frequent than admin, less than regular user
    
    def on_start(self):
        """Setup high-volume session"""
        self.headers = {
            "Authorization": "Bearer highvolume.jwt.token.for.load.testing",
            "Content-Type": "application/json"
        }
        self.batch_size = random.randint(5, 20)
    
    @task(15)
    def batch_email_notifications(self):
        """Send batch of email notifications"""
        for i in range(self.batch_size):
            notification_data = {
                "type": "email",
                "to": f"batch{i}@loadtest.com",
                "subject": f"Batch Email {i}",
                "message": f"High volume batch notification {i}",
                "priority": "normal"
            }
            
            with self.client.post("/api/v1/notifications",
                                  json=notification_data,
                                  headers=self.headers,
                                  catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"Batch email {i} failed: {response.status_code}")
                    break  # Stop batch on first failure
        else:
            # All requests in batch succeeded
            response.success()
    
    @task(5)
    def rapid_status_checks(self):
        """Rapid notification status checks"""
        for i in range(5):
            notification_id = f"rapid_status_{random.randint(1, 100)}"
            
            with self.client.get(f"/api/v1/notifications/{notification_id}/status",
                                 headers=self.headers,
                                 catch_response=True) as response:
                if response.status_code not in [200, 404]:
                    response.failure(f"Rapid status check {i} failed: {response.status_code}")
                    break
        else:
            response.success()


# Custom load testing scenarios
class LoadTestScenarios:
    """Custom load testing scenarios for specific testing needs"""
    
    @staticmethod
    def spike_test():
        """Spike test configuration - sudden load increase"""
        # Use with: locust -f locustfile.py --users 200 --spawn-rate 50
        pass
    
    @staticmethod
    def stress_test():
        """Stress test configuration - sustained high load"""
        # Use with: locust -f locustfile.py --users 500 --spawn-rate 10
        pass
    
    @staticmethod
    def volume_test():
        """Volume test configuration - large data processing"""
        # Use with: locust -f locustfile.py --users 100 --spawn-rate 5 -t 30m
        pass


# Configuration for different test scenarios
if __name__ == "__main__":
    print("Communication Service Load Testing Configuration")
    print("Available test scenarios:")
    print("1. Regular load test: locust -f locustfile.py --users 50 --spawn-rate 5")
    print("2. Spike test: locust -f locustfile.py --users 200 --spawn-rate 50")
    print("3. Stress test: locust -f locustfile.py --users 500 --spawn-rate 10") 
    print("4. Volume test: locust -f locustfile.py --users 100 --spawn-rate 5 -t 30m")
    print("\nMake sure the Communication Service is running on port 8002")