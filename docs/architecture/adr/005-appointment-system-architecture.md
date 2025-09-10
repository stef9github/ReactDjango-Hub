# ADR-005: Appointment System Architecture with Communication Service Integration

## Status
Proposed (Updated with Communication Service Integration)

## Date
2025-01-10 (Updated 2025-01-10)

## Context

The ReactDjango Hub platform needs to implement a comprehensive appointment system with APIs. The platform currently operates with a microservices architecture:

- **Identity Service** (Port 8001): FastAPI-based service handling authentication, users, organizations, MFA, and RBAC
- **Backend Service** (Port 8000): Django-based service for core business logic, data models, and APIs
- **Communication Service** (Port 8003): FastAPI-based service for multi-channel notifications, messaging, and templates
- **Frontend** (Port 3000/5173): React-based user interface
- **Planned Services**: Content (Port 8002) and Workflow Intelligence (Port 8004) services

We need to determine the optimal architectural approach for implementing appointment functionality that will:
- Support scheduling, management, and tracking of appointments
- Integrate with existing user and organization data
- **Provide comprehensive notification capabilities through the Communication Service**
- **Support multi-channel messaging (email, SMS, in-app notifications)**
- **Enable automated reminders and follow-ups**
- Provide APIs for various client applications
- Scale independently if needed
- Maintain clear domain boundaries

## Decision

**Implement the appointment system within the Django Backend Service (Port 8000)** rather than creating a new microservice.

### Implementation Strategy

1. **Create a dedicated Django app** within the backend service:
   ```
   backend/apps/appointments/
   ├── models.py       # Appointment, TimeSlot, Availability models
   ├── api.py          # Django Ninja API endpoints
   ├── services.py     # Business logic layer
   ├── tasks.py        # Async tasks (reminders, notifications)
   └── tests/          # Comprehensive test suite
   ```

2. **Integration Points**:
   - **Identity Service**: Authenticate requests and fetch user/organization data
   - **Communication Service**: Comprehensive notification and messaging integration
   - **Workflow Service** (when ready): Automate appointment workflows

3. **API Design**:
   ```python
   # Django Ninja API structure
   /api/appointments/
   ├── POST   /appointments/              # Create appointment
   ├── GET    /appointments/              # List appointments
   ├── GET    /appointments/{id}/         # Get appointment details
   ├── PATCH  /appointments/{id}/         # Update appointment
   ├── DELETE /appointments/{id}/         # Cancel appointment
   ├── POST   /appointments/{id}/confirm/ # Confirm appointment
   ├── GET    /availability/              # Get available time slots
   ├── POST   /availability/              # Set availability rules
   └── GET    /appointments/calendar/     # Calendar view data
   ```

## Consequences

### Positive

1. **Faster Time to Market**
   - Leverages existing Django infrastructure and patterns
   - No need to set up new service boilerplate
   - Reuses existing database connections and configurations

2. **Simplified Data Management**
   - Direct access to business models (Client, BusinessRecord)
   - Easier transaction management within single database
   - Simpler data consistency without distributed transactions

3. **Reduced Operational Complexity**
   - One less service to deploy, monitor, and maintain
   - No additional inter-service communication overhead
   - Simplified debugging and troubleshooting

4. **Natural Domain Alignment**
   - Appointments are core business logic, fitting Django's purpose
   - Strong coupling with business entities is acceptable
   - Future migration path exists if needed

5. **Resource Efficiency**
   - No additional infrastructure resources required
   - Shared connection pools and caching layers
   - Lower overall system footprint

### Negative

1. **Reduced Service Isolation**
   - Appointment failures could impact other backend functionality
   - Shared resource contention possible under high load
   - Less granular scaling options

2. **Increased Backend Complexity**
   - Backend service becomes larger and more complex
   - Longer build and deployment times
   - More difficult to onboard new developers

3. **Limited Technology Flexibility**
   - Bound to Django/Python technology stack
   - Cannot optimize technology choice for appointment-specific needs
   - Harder to adopt specialized scheduling libraries

### Risks

1. **Scaling Challenges**
   - If appointments grow disproportionately, may need extraction
   - Risk Level: **Medium**
   - Mitigation: Design with clear boundaries for future extraction

2. **Performance Impact**
   - Heavy appointment operations could affect other backend APIs
   - Risk Level: **Low-Medium**
   - Mitigation: Implement caching, async processing, database optimization

3. **Team Coordination**
   - Multiple teams working on same codebase
   - Risk Level: **Low**
   - Mitigation: Clear code ownership, strong testing practices

## Alternatives Considered

### Alternative 1: New Appointment Microservice

**Pros:**
- Complete service isolation and independent scaling
- Technology flexibility (could use Node.js for real-time features)
- Clear domain boundaries from the start
- Independent deployment and versioning

**Cons:**
- Significant additional complexity for MVP
- Distributed transaction challenges
- Additional infrastructure and monitoring requirements
- Longer development timeline
- Over-engineering for current scale requirements

**Why Rejected:** The complexity overhead outweighs benefits at current scale. Microservices are beneficial when you have clear needs for independent scaling, team autonomy, or technology diversity - none of which apply strongly here yet.

### Alternative 2: Add to Identity Service

**Pros:**
- User data readily available
- Could leverage existing authentication flows

**Cons:**
- Violates single responsibility principle
- Identity service should remain focused on authentication/authorization
- Would create inappropriate coupling between domains
- Makes identity service too complex

**Why Rejected:** Appointments are business logic, not identity management. This would blur service boundaries and create long-term architectural debt.

## Implementation Plan (Updated with Communication Service Integration)

### Phase 1: Core Implementation & Communication Setup (Week 1-2)
1. Create appointment Django app structure
2. Implement data models with migrations including notification preferences
3. Build core CRUD APIs with Django Ninja
4. Integrate authentication with Identity Service
5. **Set up Communication Service client and connection**
6. **Implement basic notification workflows (create, confirm, cancel)**
7. Add comprehensive test coverage including notification mocking

### Phase 2: Advanced Features & Messaging (Week 3-4)
1. Implement availability and scheduling logic
2. Add recurring appointment support
3. Build calendar integration APIs
4. Implement conflict detection and resolution
5. **Implement comprehensive reminder system via Communication Service**
6. **Set up message templates for all notification types**
7. **Implement multi-channel notification preferences**
8. **Add SMS and push notification support**

### Phase 3: Reliability & Integration (Week 5)
1. **Implement reliability patterns (circuit breaker, retry logic)**
2. **Set up notification fallback mechanisms**
3. **Implement notification queue for failed messages**
4. Frontend integration with React components
5. Integration testing with Identity and Communication Services
6. Performance testing including notification throughput
7. Documentation and API specifications

### Phase 4: Advanced Communication Features (Week 6)
1. **Implement follow-up notification workflows**
2. **Add no-show detection and alerting**
3. **Implement notification analytics and tracking**
4. **Set up notification preference management UI**
5. **Add bulk notification capabilities for group appointments**
6. **Implement notification digest for frequent users**
7. **Add real-time notification status tracking**

## Communication Service Integration Architecture

### Overview
The appointment system will leverage the Communication Service (Port 8003) for all notification and messaging capabilities, creating a robust event-driven notification workflow that ensures users are properly informed about their appointments across multiple channels.

### Integration Architecture

```python
# backend/apps/appointments/communication.py

from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import httpx
from django.conf import settings

class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PUSH = "push"

class NotificationType(Enum):
    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_CONFIRMED = "appointment_confirmed"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    APPOINTMENT_RESCHEDULED = "appointment_rescheduled"
    APPOINTMENT_REMINDER = "appointment_reminder"
    APPOINTMENT_FOLLOW_UP = "appointment_follow_up"
    NO_SHOW_ALERT = "no_show_alert"

@dataclass
class NotificationRequest:
    type: NotificationType
    channels: List[NotificationChannel]
    recipient_ids: List[str]
    template_id: str
    template_data: Dict[str, Any]
    scheduling: Dict[str, Any] = None
    priority: str = "normal"

class CommunicationServiceClient:
    """Client for integrating with Communication Service"""
    
    def __init__(self):
        self.base_url = settings.COMMUNICATION_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_notification(self, request: NotificationRequest) -> Dict:
        """Send notification through Communication Service"""
        endpoint = f"{self.base_url}/api/communication/notifications/send"
        
        payload = {
            "type": request.type.value,
            "channels": [c.value for c in request.channels],
            "recipients": request.recipient_ids,
            "template_id": request.template_id,
            "template_data": request.template_data,
            "priority": request.priority
        }
        
        if request.scheduling:
            payload["scheduling"] = request.scheduling
        
        response = await self.client.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def schedule_reminder(
        self, 
        appointment_id: str,
        reminder_times: List[int],  # Minutes before appointment
        channels: List[NotificationChannel]
    ) -> Dict:
        """Schedule appointment reminders"""
        endpoint = f"{self.base_url}/api/communication/reminders/schedule"
        
        payload = {
            "entity_type": "appointment",
            "entity_id": appointment_id,
            "reminder_times": reminder_times,
            "channels": [c.value for c in channels],
            "template_id": "appointment_reminder_v1"
        }
        
        response = await self.client.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def cancel_scheduled_notifications(self, appointment_id: str) -> Dict:
        """Cancel all scheduled notifications for an appointment"""
        endpoint = f"{self.base_url}/api/communication/notifications/cancel"
        
        params = {
            "entity_type": "appointment",
            "entity_id": appointment_id
        }
        
        response = await self.client.delete(endpoint, params=params)
        response.raise_for_status()
        return response.json()
```

### Event-Driven Notification Workflows

```python
# backend/apps/appointments/notification_workflows.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from celery import shared_task
from .models import Appointment
from .communication import CommunicationServiceClient, NotificationRequest, NotificationType, NotificationChannel

class AppointmentNotificationManager:
    """Manages all appointment-related notifications"""
    
    def __init__(self):
        self.comm_client = CommunicationServiceClient()
    
    async def handle_appointment_created(self, appointment: Appointment):
        """Send notifications when appointment is created"""
        
        # 1. Send confirmation to organizer
        await self._send_organizer_confirmation(appointment)
        
        # 2. Send invitations to participants
        await self._send_participant_invitations(appointment)
        
        # 3. Schedule reminders based on preferences
        await self._schedule_reminders(appointment)
        
        # 4. If SMS enabled, send SMS confirmations
        if appointment.sms_notifications_enabled:
            await self._send_sms_confirmations(appointment)
    
    async def handle_appointment_updated(self, appointment: Appointment, changes: Dict):
        """Handle notifications for appointment updates"""
        
        # Cancel existing scheduled notifications
        await self.comm_client.cancel_scheduled_notifications(appointment.id)
        
        # Determine notification type based on changes
        if 'start_time' in changes or 'end_time' in changes:
            notification_type = NotificationType.APPOINTMENT_RESCHEDULED
            template_id = "appointment_reschedule_v1"
        else:
            notification_type = NotificationType.APPOINTMENT_UPDATED
            template_id = "appointment_update_v1"
        
        # Send update notifications
        await self._send_update_notifications(
            appointment, 
            notification_type, 
            template_id,
            changes
        )
        
        # Reschedule reminders
        await self._schedule_reminders(appointment)
    
    async def handle_appointment_cancelled(self, appointment: Appointment):
        """Send cancellation notifications"""
        
        # Cancel all scheduled notifications
        await self.comm_client.cancel_scheduled_notifications(appointment.id)
        
        # Send cancellation notices
        notification = NotificationRequest(
            type=NotificationType.APPOINTMENT_CANCELLED,
            channels=self._get_preferred_channels(appointment),
            recipient_ids=appointment.get_all_participant_ids(),
            template_id="appointment_cancellation_v1",
            template_data={
                "appointment_title": appointment.title,
                "original_time": appointment.start_time.isoformat(),
                "cancellation_reason": appointment.cancellation_reason,
                "organizer_name": appointment.organizer_name
            },
            priority="high"
        )
        
        await self.comm_client.send_notification(notification)
    
    async def _schedule_reminders(self, appointment: Appointment):
        """Schedule automated reminders"""
        
        reminder_settings = appointment.reminder_settings or {
            "email": [1440, 60],  # 24 hours and 1 hour before
            "sms": [60],  # 1 hour before
            "in_app": [1440, 60, 15]  # 24 hours, 1 hour, and 15 minutes
        }
        
        for channel, times in reminder_settings.items():
            if times:
                await self.comm_client.schedule_reminder(
                    appointment_id=str(appointment.id),
                    reminder_times=times,
                    channels=[NotificationChannel(channel)]
                )
    
    def _get_preferred_channels(self, appointment: Appointment) -> List[NotificationChannel]:
        """Determine notification channels based on user preferences"""
        channels = [NotificationChannel.IN_APP]  # Always include in-app
        
        if appointment.email_notifications_enabled:
            channels.append(NotificationChannel.EMAIL)
        
        if appointment.sms_notifications_enabled:
            channels.append(NotificationChannel.SMS)
        
        if appointment.push_notifications_enabled:
            channels.append(NotificationChannel.PUSH)
        
        return channels

# Celery tasks for async notification processing
@shared_task
def send_appointment_notifications(appointment_id: str, event_type: str):
    """Async task to send appointment notifications"""
    from .models import Appointment
    import asyncio
    
    appointment = Appointment.objects.get(id=appointment_id)
    manager = AppointmentNotificationManager()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        if event_type == "created":
            loop.run_until_complete(manager.handle_appointment_created(appointment))
        elif event_type == "updated":
            loop.run_until_complete(manager.handle_appointment_updated(appointment, {}))
        elif event_type == "cancelled":
            loop.run_until_complete(manager.handle_appointment_cancelled(appointment))
    finally:
        loop.close()
```

### Message Templates and Personalization

```python
# backend/apps/appointments/templates.py

class AppointmentTemplateManager:
    """Manages message templates for appointments"""
    
    @staticmethod
    def register_templates_with_communication_service():
        """Register all appointment templates with Communication Service"""
        
        templates = [
            {
                "id": "appointment_confirmation_v1",
                "name": "Appointment Confirmation",
                "channels": ["email", "sms", "in_app"],
                "variables": [
                    "recipient_name", "appointment_title", "appointment_date",
                    "appointment_time", "location", "meeting_url", "organizer_name",
                    "appointment_id", "confirmation_link"
                ],
                "email_template": {
                    "subject": "Appointment Confirmed: {{appointment_title}}",
                    "html_body": """
                        <h2>Your appointment has been confirmed</h2>
                        <p>Hi {{recipient_name}},</p>
                        <p>Your appointment "{{appointment_title}}" has been confirmed.</p>
                        <div style="border: 1px solid #ddd; padding: 15px; margin: 20px 0;">
                            <strong>Date:</strong> {{appointment_date}}<br>
                            <strong>Time:</strong> {{appointment_time}}<br>
                            <strong>Location:</strong> {{location}}<br>
                            {{#if meeting_url}}
                            <strong>Virtual Meeting:</strong> <a href="{{meeting_url}}">Join Meeting</a><br>
                            {{/if}}
                            <strong>Organizer:</strong> {{organizer_name}}
                        </div>
                        <p><a href="{{confirmation_link}}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Appointment Details</a></p>
                    """,
                    "text_body": """
                        Your appointment has been confirmed
                        
                        Hi {{recipient_name}},
                        
                        Your appointment "{{appointment_title}}" has been confirmed.
                        
                        Date: {{appointment_date}}
                        Time: {{appointment_time}}
                        Location: {{location}}
                        Organizer: {{organizer_name}}
                        
                        View details: {{confirmation_link}}
                    """
                },
                "sms_template": {
                    "body": "Appointment confirmed: {{appointment_title}} on {{appointment_date}} at {{appointment_time}}. Location: {{location}}. Details: {{confirmation_link}}"
                },
                "in_app_template": {
                    "title": "Appointment Confirmed",
                    "body": "Your appointment '{{appointment_title}}' is confirmed for {{appointment_date}} at {{appointment_time}}",
                    "action_url": "/appointments/{{appointment_id}}"
                }
            },
            {
                "id": "appointment_reminder_v1",
                "name": "Appointment Reminder",
                "channels": ["email", "sms", "in_app", "push"],
                "variables": [
                    "recipient_name", "appointment_title", "time_until",
                    "appointment_time", "location", "meeting_url", "preparation_notes"
                ],
                "schedule_relative": True,  # Can be scheduled relative to appointment time
                # ... template content ...
            },
            {
                "id": "appointment_cancellation_v1",
                "name": "Appointment Cancellation",
                "channels": ["email", "sms", "in_app", "push"],
                "priority": "high",
                # ... template content ...
            },
            {
                "id": "appointment_reschedule_v1",
                "name": "Appointment Rescheduled",
                "channels": ["email", "sms", "in_app"],
                "priority": "high",
                # ... template content ...
            },
            {
                "id": "appointment_follow_up_v1",
                "name": "Post-Appointment Follow-up",
                "channels": ["email", "in_app"],
                "schedule_relative": True,
                # ... template content ...
            }
        ]
        
        # Register templates with Communication Service
        for template in templates:
            register_template_with_service(template)
```

### Reliability Patterns

```python
# backend/apps/appointments/reliability.py

from typing import Optional, Dict, Any
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class ResilientCommunicationClient:
    """Communication client with reliability patterns"""
    
    def __init__(self):
        self.primary_client = CommunicationServiceClient()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=httpx.HTTPError
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(httpx.HTTPError)
    )
    async def send_notification_with_retry(self, request: NotificationRequest) -> Dict:
        """Send notification with automatic retry logic"""
        
        # Check circuit breaker state
        if self.circuit_breaker.is_open():
            logger.warning("Circuit breaker is open, using fallback")
            return await self._fallback_notification(request)
        
        try:
            # Attempt primary notification
            result = await self.primary_client.send_notification(request)
            self.circuit_breaker.record_success()
            return result
            
        except httpx.HTTPError as e:
            self.circuit_breaker.record_failure()
            logger.error(f"Notification failed: {e}")
            
            # If this is the last retry, use fallback
            if self.circuit_breaker.is_open():
                return await self._fallback_notification(request)
            raise
    
    async def _fallback_notification(self, request: NotificationRequest) -> Dict:
        """Fallback notification strategy"""
        
        # 1. Try to queue for later processing
        if await self._queue_for_retry(request):
            return {"status": "queued", "message": "Notification queued for retry"}
        
        # 2. If critical, try alternative channel
        if request.priority == "high":
            return await self._send_via_alternative_channel(request)
        
        # 3. Log for manual processing
        await self._log_failed_notification(request)
        return {"status": "failed", "message": "Notification logged for manual processing"}
    
    async def _queue_for_retry(self, request: NotificationRequest) -> bool:
        """Queue notification for retry when service recovers"""
        try:
            from .tasks import retry_failed_notification
            retry_failed_notification.apply_async(
                args=[request.__dict__],
                countdown=300  # Retry in 5 minutes
            )
            return True
        except Exception as e:
            logger.error(f"Failed to queue notification: {e}")
            return False
    
    async def _send_via_alternative_channel(self, request: NotificationRequest) -> Dict:
        """Try to send via alternative channel if primary fails"""
        
        # If email fails, try SMS
        if NotificationChannel.EMAIL in request.channels and NotificationChannel.SMS not in request.channels:
            request.channels = [NotificationChannel.SMS]
            return await self.send_notification_with_retry(request)
        
        # If SMS fails, ensure in-app notification is created
        if NotificationChannel.SMS in request.channels:
            return await self._create_in_app_notification(request)
        
        return {"status": "failed", "message": "No alternative channel available"}

class CircuitBreaker:
    """Circuit breaker pattern for service resilience"""
    
    def __init__(self, failure_threshold: int, recovery_timeout: int, expected_exception: type):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def is_open(self) -> bool:
        if self.state == "open":
            # Check if recovery timeout has passed
            if self._should_attempt_reset():
                self.state = "half-open"
                return False
            return True
        return False
    
    def record_success(self):
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = asyncio.get_event_loop().time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and
            asyncio.get_event_loop().time() - self.last_failure_time >= self.recovery_timeout
        )

# Notification queue processor
@shared_task(bind=True, max_retries=5)
def retry_failed_notification(self, notification_data: Dict):
    """Process failed notifications from queue"""
    try:
        client = CommunicationServiceClient()
        request = NotificationRequest(**notification_data)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(client.send_notification(request))
            logger.info(f"Successfully sent queued notification: {result}")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Failed to send queued notification: {e}")
        raise self.retry(countdown=60 * (2 ** self.request.retries))
```

## Service Communication Patterns

### Synchronous vs Asynchronous Communication

```python
# backend/apps/appointments/service_integration.py

class ServiceIntegrationStrategy:
    """Defines communication patterns between services"""
    
    def __init__(self):
        self.sync_client = httpx.AsyncClient(timeout=5.0)  # Short timeout for sync calls
        self.async_client = CommunicationServiceClient()
        self.event_bus = EventBus()
    
    async def handle_appointment_creation(self, appointment: Appointment):
        """Orchestrate service communications for appointment creation"""
        
        # 1. SYNCHRONOUS: Validate user exists (critical path)
        try:
            user_data = await self._validate_users_sync(appointment.participant_ids)
        except httpx.TimeoutError:
            raise ServiceUnavailableError("Identity service timeout")
        
        # 2. ASYNCHRONOUS: Send notifications (non-critical path)
        await self._send_notifications_async(appointment)
        
        # 3. EVENT-DRIVEN: Publish appointment created event
        await self.event_bus.publish(
            "appointment.created",
            {
                "appointment_id": str(appointment.id),
                "organizer_id": appointment.organizer_id,
                "participant_ids": appointment.participant_ids,
                "start_time": appointment.start_time.isoformat()
            }
        )
    
    async def _validate_users_sync(self, user_ids: List[str]) -> List[Dict]:
        """Synchronous call to Identity Service - blocks on response"""
        response = await self.sync_client.post(
            f"{settings.IDENTITY_SERVICE_URL}/api/identity/users/validate",
            json={"user_ids": user_ids}
        )
        response.raise_for_status()
        return response.json()
    
    async def _send_notifications_async(self, appointment: Appointment):
        """Asynchronous notification - fire and forget with queue"""
        from .tasks import send_appointment_notifications
        
        # Queue for async processing
        send_appointment_notifications.delay(
            appointment_id=str(appointment.id),
            event_type="created"
        )
```

### Event-Driven Architecture

```python
# backend/apps/appointments/events.py

from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime
import json
import redis.asyncio as redis

@dataclass
class AppointmentEvent:
    """Base class for appointment events"""
    event_type: str
    appointment_id: str
    timestamp: datetime
    metadata: Dict[str, Any]

class EventBus:
    """Event bus for publishing appointment events to other services"""
    
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        self.subscribers = {
            "communication": ["appointment.*"],
            "workflow": ["appointment.created", "appointment.completed"],
            "analytics": ["appointment.*"]
        }
    
    async def publish(self, event_type: str, data: Dict[str, Any]):
        """Publish event to interested services"""
        
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "appointment-service",
            "data": data
        }
        
        # Publish to Redis pub/sub
        await self.redis_client.publish(
            f"events:{event_type}",
            json.dumps(event)
        )
        
        # Also store in event stream for replay capability
        await self.redis_client.xadd(
            "appointment-events",
            {"event": json.dumps(event)}
        )

class EventSubscriber:
    """Subscribe to events from Communication Service"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.handlers = {
            "notification.delivered": self.handle_notification_delivered,
            "notification.failed": self.handle_notification_failed,
            "notification.bounced": self.handle_notification_bounced
        }
    
    async def start_listening(self):
        """Start listening for communication events"""
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe("events:notification.*")
        
        async for message in pubsub.listen():
            if message["type"] == "message":
                await self.process_message(message)
    
    async def process_message(self, message):
        """Process incoming event message"""
        event = json.loads(message["data"])
        event_type = event["type"]
        
        if event_type in self.handlers:
            await self.handlers[event_type](event["data"])
    
    async def handle_notification_delivered(self, data: Dict):
        """Update appointment when notification is delivered"""
        if data.get("entity_type") == "appointment":
            appointment = await Appointment.objects.aget(id=data["entity_id"])
            appointment.notification_status["delivered"].append({
                "channel": data["channel"],
                "timestamp": data["timestamp"],
                "recipient": data["recipient"]
            })
            await appointment.asave()
    
    async def handle_notification_failed(self, data: Dict):
        """Handle failed notification - maybe retry or alert"""
        if data.get("entity_type") == "appointment":
            logger.error(f"Notification failed for appointment {data['entity_id']}")
            # Trigger alternative notification method
            await self.trigger_fallback_notification(data["entity_id"])
```

### API Gateway Integration

```python
# backend/apps/appointments/gateway.py

class KongGatewayIntegration:
    """Integration patterns for Kong API Gateway"""
    
    @staticmethod
    def get_service_routes():
        """Define routes for Kong API Gateway configuration"""
        return {
            "appointment-service": {
                "routes": [
                    {
                        "path": "/api/appointments",
                        "methods": ["GET", "POST", "PUT", "DELETE"],
                        "strip_path": False,
                        "plugins": [
                            {
                                "name": "jwt",
                                "config": {
                                    "claims_to_verify": ["exp", "nbf"],
                                    "key_claim_name": "iss"
                                }
                            },
                            {
                                "name": "rate-limiting",
                                "config": {
                                    "minute": 100,
                                    "hour": 1000
                                }
                            },
                            {
                                "name": "correlation-id",
                                "config": {
                                    "header_name": "X-Correlation-ID",
                                    "generator": "uuid"
                                }
                            }
                        ]
                    }
                ],
                "upstream": {
                    "targets": [
                        {"target": "backend:8000", "weight": 100}
                    ],
                    "healthchecks": {
                        "active": {
                            "path": "/health/appointments",
                            "interval": 30
                        }
                    }
                }
            }
        }
    
    @staticmethod
    def get_cross_service_headers():
        """Headers to propagate across service calls"""
        return [
            "X-Correlation-ID",
            "X-Request-ID", 
            "X-User-ID",
            "X-Organization-ID",
            "X-Trace-ID",
            "Authorization"
        ]
```

### Service Mesh Configuration

```yaml
# infrastructure/service-mesh/appointment-communication.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: appointment-to-communication
spec:
  hosts:
  - communication-service
  http:
  - match:
    - headers:
        x-source-service:
          exact: appointment-service
    route:
    - destination:
        host: communication-service
        port:
          number: 8003
    timeout: 30s
    retries:
      attempts: 3
      perTryTimeout: 10s
      retryOn: 5xx,reset,connect-failure,refused-stream

---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: communication-service-circuit-breaker
spec:
  host: communication-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 100
        http2MaxRequests: 100
        maxRequestsPerConnection: 2
    outlierDetection:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
      minHealthPercent: 30
```

### Migration Strategy (Future)

If appointment functionality needs to be extracted into a microservice:

1. **Data Migration**
   - Export appointment data to new database
   - Implement dual-write during transition
   - Verify data consistency

2. **API Migration**
   - Implement facade pattern in Django backend
   - Gradually redirect traffic to new service
   - Maintain backward compatibility

3. **Feature Parity**
   - Ensure all features work in new service
   - Migrate background jobs and scheduled tasks
   - Update monitoring and alerting

## Technical Implementation Details

### Data Model Design

```python
# backend/apps/appointments/models.py

class Appointment(BaseModel):
    """Core appointment model"""
    # Relationships
    organizer_id = models.UUIDField()  # From Identity Service
    participant_ids = models.JSONField()  # List of user IDs
    client = models.ForeignKey('business.Client', null=True)
    
    # Scheduling
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    timezone = models.CharField(max_length=50)
    
    # Details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=500, blank=True)
    meeting_url = models.URLField(blank=True)
    
    # Status
    status = models.CharField(choices=AppointmentStatus.choices)
    confirmation_status = models.JSONField()  # Per-participant status
    
    # Metadata
    recurring_pattern = models.JSONField(null=True)
    reminder_settings = models.JSONField()
    custom_fields = models.JSONField(default=dict)

class TimeSlot(BaseModel):
    """Available time slots for scheduling"""
    user_id = models.UUIDField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_available = models.BooleanField(default=True)
    appointment = models.ForeignKey(Appointment, null=True)

class AvailabilityRule(BaseModel):
    """Recurring availability patterns"""
    user_id = models.UUIDField()
    day_of_week = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField()
    effective_until = models.DateField(null=True)
```

### Service Layer Architecture

```python
# backend/apps/appointments/services.py

class AppointmentService:
    """Business logic for appointment operations"""
    
    def __init__(self, identity_client: IdentityClient):
        self.identity_client = identity_client
    
    async def create_appointment(
        self,
        organizer_id: str,
        participant_ids: List[str],
        start_time: datetime,
        end_time: datetime,
        **details
    ) -> Appointment:
        # Validate users exist in Identity Service
        await self._validate_users(organizer_id, participant_ids)
        
        # Check availability
        if not await self._check_availability(participant_ids, start_time, end_time):
            raise ConflictError("Time slot not available")
        
        # Create appointment
        appointment = await Appointment.objects.create(...)
        
        # Send notifications (async)
        await self._send_notifications(appointment)
        
        return appointment
    
    async def get_availability(
        self,
        user_id: str,
        date_range: DateRange
    ) -> List[TimeSlot]:
        # Get user's availability rules
        # Generate time slots
        # Filter out booked slots
        # Return available slots
        pass
```

### API Integration Pattern

```python
# backend/apps/appointments/api.py

from ninja import Router
from django.views.decorators.cache import cache_page

router = Router(tags=["appointments"])

@router.post("/appointments/")
async def create_appointment(request, data: AppointmentCreateSchema):
    """Create a new appointment"""
    # Extract JWT token
    token = request.headers.get("Authorization")
    
    # Validate with Identity Service
    user = await identity_client.validate_token(token)
    
    # Create appointment
    service = AppointmentService(identity_client)
    appointment = await service.create_appointment(
        organizer_id=user.id,
        **data.dict()
    )
    
    return AppointmentResponse.from_orm(appointment)

@router.get("/availability/")
@cache_page(60 * 5)  # Cache for 5 minutes
async def get_availability(
    request,
    user_id: str,
    start_date: date,
    end_date: date
):
    """Get available time slots for a user"""
    service = AppointmentService(identity_client)
    slots = await service.get_availability(
        user_id=user_id,
        date_range=DateRange(start_date, end_date)
    )
    return [SlotResponse.from_orm(slot) for slot in slots]
```

## Monitoring and Success Metrics

### Key Performance Indicators
- API response time < 200ms for 95th percentile
- Appointment creation success rate > 99%
- Zero data inconsistencies between services
- System availability > 99.9%

### Monitoring Strategy
- Track API endpoint performance with Datadog/New Relic
- Monitor database query performance
- Alert on failed appointment creations
- Track user engagement with appointment features

## Conclusion

Implementing the appointment system within the Django Backend Service, with comprehensive integration to the Communication Service, provides an optimal architecture that balances:

1. **Development Efficiency**: Leveraging Django's robust framework while maintaining microservices communication patterns
2. **User Experience**: Multi-channel notifications ensure users never miss appointments
3. **Reliability**: Circuit breakers, retry logic, and fallback mechanisms ensure notification delivery
4. **Scalability**: Event-driven architecture allows independent scaling of notification processing
5. **Maintainability**: Clear service boundaries with well-defined integration points

The comprehensive communication integration ensures:
- **Automated Reminders**: Scheduled notifications across email, SMS, and in-app channels
- **Real-time Updates**: Event-driven architecture for immediate notification of changes
- **Personalization**: Template-based messaging with user preference management
- **Reliability**: Multiple fallback mechanisms to ensure critical notifications are delivered
- **Analytics**: Full tracking of notification delivery and engagement

This architecture positions the appointment system as a robust, user-centric feature that leverages the strengths of both the Django Backend Service for business logic and the Communication Service for sophisticated messaging capabilities. The design maintains clear boundaries for future extraction if needed while delivering a comprehensive solution today.

## References

- Martin Fowler: "MonolithFirst" - https://martinfowler.com/bliki/MonolithFirst.html
- Sam Newman: "Building Microservices" - Chapter on Service Boundaries
- Django Ninja Documentation: https://django-ninja.rest-framework.com/
- ReactDjango Hub Architecture Documentation: /docs/architecture/saas-hub-architecture-spec.md

## Review and Approval

- **Author**: Technical Lead Agent (ag-techlead)
- **Updated By**: Technical Lead Agent (ag-techlead) - Added Communication Service Integration
- **Reviewers**: Backend Team, Infrastructure Team, Frontend Team, Communication Service Team
- **Approval Date**: Pending
- **Implementation Start**: Upon approval
- **Last Updated**: 2025-01-10 - Comprehensive Communication Service Integration Added