# Backend Agent: Event Scheduler Integration Guide

## Overview

This guide provides the Backend Agent (ag-backend) with comprehensive documentation on integrating with the Event Scheduler Service for time-based event management in the Django backend.

## Architecture Context

The Event Scheduler Service (Port 8005) provides centralized time-based event scheduling with sophisticated timezone management. As the Backend Agent, you'll primarily interact with this service for:

- Scheduling appointment-related events
- Managing business rule triggers
- Handling recurring tasks
- Processing scheduled events

## Service Integration Points

### 1. Client Configuration

```python
# backend/config/settings.py

EVENT_SCHEDULER_URL = env('EVENT_SCHEDULER_URL', default='http://localhost:8005')
EVENT_SCHEDULER_TIMEOUT = 30  # seconds
EVENT_SCHEDULER_API_KEY = env('EVENT_SCHEDULER_API_KEY', default='')

# Celery configuration for event processing
CELERY_TASK_ROUTES = {
    'backend.process_event': {'queue': 'backend-events'},
}
```

### 2. Event Scheduler Client

```python
# backend/core/clients/event_scheduler.py

import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class EventSchedulerClient:
    """Client for interacting with Event Scheduler Service"""
    
    def __init__(self):
        self.base_url = settings.EVENT_SCHEDULER_URL
        self.timeout = settings.EVENT_SCHEDULER_TIMEOUT
        self.headers = {
            'X-Service-Name': 'backend',
            'X-API-Key': settings.EVENT_SCHEDULER_API_KEY
        }
    
    async def schedule_event(
        self,
        event_type: str,
        entity_id: str,
        scheduled_time: datetime,
        resource_timezone: str,
        user_timezone: str,
        payload: Dict[str, Any],
        recurrence: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Schedule a new event
        
        Args:
            event_type: Type of event (e.g., 'APPOINTMENT_REMINDER')
            entity_id: Related entity ID
            scheduled_time: When to execute the event
            resource_timezone: IANA timezone of the resource
            user_timezone: IANA timezone of the user
            payload: Event-specific data
            recurrence: Optional recurrence pattern
            
        Returns:
            Event ID
        """
        event_data = {
            "type": event_type,
            "service_id": "backend",
            "entity_id": entity_id,
            "scheduled_time": scheduled_time.isoformat(),
            "timezone_context": {
                "resource_timezone": resource_timezone,
                "user_timezone": user_timezone,
                "execution_timezone": resource_timezone
            },
            "payload": payload
        }
        
        if recurrence:
            event_data["recurrence"] = recurrence
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/events/schedule",
                json=event_data,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Scheduled event {result['event_id']} for {scheduled_time}")
            return result['event_id']
    
    async def cancel_event(self, event_id: str) -> bool:
        """Cancel a scheduled event"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/events/{event_id}",
                headers=self.headers,
                timeout=self.timeout
            )
            if response.status_code == 200:
                logger.info(f"Cancelled event {event_id}")
                return True
            return False
    
    async def get_upcoming_events(
        self,
        entity_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        timezone: str = "UTC"
    ) -> List[Dict[str, Any]]:
        """Get upcoming scheduled events"""
        params = {
            "service_id": "backend",
            "timezone": timezone
        }
        if entity_id:
            params["entity_id"] = entity_id
        if start_time:
            params["start_time"] = start_time.isoformat()
        if end_time:
            params["end_time"] = end_time.isoformat()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/events/upcoming",
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
```

## Implementation Patterns

### 1. Appointment Event Scheduling

```python
# backend/apps/appointments/services/event_service.py

from datetime import datetime, timedelta
from typing import Optional
from backend.core.clients.event_scheduler import EventSchedulerClient
from ..models import Appointment

class AppointmentEventService:
    """Service for managing appointment-related events"""
    
    def __init__(self):
        self.scheduler = EventSchedulerClient()
    
    async def schedule_appointment_events(
        self,
        appointment: Appointment,
        user_timezone: str = "America/New_York",
        resource_timezone: str = "America/New_York"
    ):
        """Schedule all events for a new appointment"""
        
        # Schedule reminders
        reminder_configs = [
            (timedelta(days=1), "24_hour_reminder"),
            (timedelta(hours=2), "2_hour_reminder"),
            (timedelta(minutes=15), "15_minute_reminder")
        ]
        
        for delta, reminder_type in reminder_configs:
            reminder_time = appointment.start_time - delta
            
            await self.scheduler.schedule_event(
                event_type="APPOINTMENT_REMINDER",
                entity_id=str(appointment.id),
                scheduled_time=reminder_time,
                resource_timezone=resource_timezone,
                user_timezone=user_timezone,
                payload={
                    "appointment_id": str(appointment.id),
                    "reminder_type": reminder_type,
                    "participant_ids": appointment.participant_ids,
                    "title": appointment.title,
                    "start_time": appointment.start_time.isoformat()
                }
            )
        
        # Schedule follow-up
        follow_up_time = appointment.end_time + timedelta(hours=1)
        
        await self.scheduler.schedule_event(
            event_type="APPOINTMENT_FOLLOW_UP",
            entity_id=str(appointment.id),
            scheduled_time=follow_up_time,
            resource_timezone=resource_timezone,
            user_timezone=user_timezone,
            payload={
                "appointment_id": str(appointment.id),
                "follow_up_type": "satisfaction_survey"
            }
        )
    
    async def cancel_appointment_events(self, appointment_id: str):
        """Cancel all events for an appointment"""
        events = await self.scheduler.get_upcoming_events(
            entity_id=appointment_id
        )
        
        for event in events:
            await self.scheduler.cancel_event(event['id'])
```

### 2. Business Rule Scheduling

```python
# backend/apps/business_rules/services/rule_scheduler.py

from datetime import datetime, time
from backend.core.clients.event_scheduler import EventSchedulerClient

class BusinessRuleScheduler:
    """Schedule and manage business rule executions"""
    
    def __init__(self):
        self.scheduler = EventSchedulerClient()
    
    async def schedule_daily_rule(
        self,
        rule_id: str,
        execution_time: time,
        timezone: str = "UTC",
        context: Dict[str, Any] = None
    ):
        """Schedule a daily business rule execution"""
        
        # Calculate next execution time
        now = datetime.now()
        next_run = datetime.combine(now.date(), execution_time)
        if next_run < now:
            next_run += timedelta(days=1)
        
        await self.scheduler.schedule_event(
            event_type="BUSINESS_RULE",
            entity_id=rule_id,
            scheduled_time=next_run,
            resource_timezone=timezone,
            user_timezone=timezone,
            payload={
                "rule_id": rule_id,
                "context": context or {}
            },
            recurrence={
                "frequency": "DAILY",
                "interval": 1,
                "timezone": timezone
            }
        )
    
    async def schedule_monthly_report(
        self,
        report_id: str,
        day_of_month: int,
        execution_time: time,
        timezone: str = "UTC"
    ):
        """Schedule monthly report generation"""
        
        await self.scheduler.schedule_event(
            event_type="REPORT_GENERATION",
            entity_id=report_id,
            scheduled_time=self._calculate_next_monthly_run(
                day_of_month, execution_time
            ),
            resource_timezone=timezone,
            user_timezone=timezone,
            payload={
                "report_id": report_id,
                "report_type": "monthly"
            },
            recurrence={
                "frequency": "MONTHLY",
                "by_month_day": [day_of_month],
                "timezone": timezone
            }
        )
```

### 3. Event Processing Handler

```python
# backend/apps/core/tasks.py

from celery import shared_task
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

@shared_task(name="backend.process_event")
def process_scheduled_event(event_data: Dict[str, Any]):
    """
    Process events from the Event Scheduler Service
    
    This task is called by the scheduler when an event is due.
    The task name must match what's configured in the scheduler.
    """
    
    event_type = event_data.get("type")
    payload = event_data.get("payload", {})
    
    try:
        if event_type == "BUSINESS_RULE":
            from apps.business_rules.services import execute_rule
            result = execute_rule(
                rule_id=payload["rule_id"],
                context=payload.get("context", {})
            )
            
        elif event_type == "REPORT_GENERATION":
            from apps.reports.services import generate_report
            result = generate_report(
                report_id=payload["report_id"],
                report_type=payload.get("report_type")
            )
            
        elif event_type == "DATA_CLEANUP":
            from apps.maintenance.services import cleanup_old_data
            result = cleanup_old_data(
                days_to_keep=payload.get("days_to_keep", 90)
            )
            
        else:
            logger.warning(f"Unknown event type: {event_type}")
            return {"status": "skipped", "reason": "Unknown event type"}
        
        logger.info(f"Successfully processed {event_type} event")
        return {"status": "success", "result": result}
        
    except Exception as e:
        logger.error(f"Failed to process event {event_data.get('id')}: {e}")
        raise  # Let Celery handle retry
```

## Django Model Integration

### 1. Timezone-Aware Models

```python
# backend/apps/appointments/models.py

from django.db import models
from django.contrib.postgres.fields import JSONField
import zoneinfo

class TimezoneAwareAppointment(models.Model):
    """Appointment model with timezone support"""
    
    # Time fields stored in UTC
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    # Timezone information
    resource_timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="IANA timezone where resource is located"
    )
    user_timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text="IANA timezone where user is located"
    )
    
    # Event tracking
    scheduled_event_ids = JSONField(
        default=list,
        help_text="IDs of scheduled events in Event Scheduler"
    )
    
    def get_local_start_time(self, timezone: str = None):
        """Get start time in specified timezone"""
        tz_str = timezone or self.user_timezone
        tz = zoneinfo.ZoneInfo(tz_str)
        return self.start_time.astimezone(tz)
    
    def get_resource_start_time(self):
        """Get start time in resource timezone"""
        tz = zoneinfo.ZoneInfo(self.resource_timezone)
        return self.start_time.astimezone(tz)
    
    async def schedule_events(self):
        """Schedule all events for this appointment"""
        from .services.event_service import AppointmentEventService
        
        service = AppointmentEventService()
        await service.schedule_appointment_events(
            appointment=self,
            user_timezone=self.user_timezone,
            resource_timezone=self.resource_timezone
        )
    
    async def cancel_events(self):
        """Cancel all scheduled events"""
        from backend.core.clients.event_scheduler import EventSchedulerClient
        
        client = EventSchedulerClient()
        for event_id in self.scheduled_event_ids:
            await client.cancel_event(event_id)
        
        self.scheduled_event_ids = []
        self.save()
```

### 2. Django Admin Integration

```python
# backend/apps/appointments/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import TimezoneAwareAppointment

@admin.register(TimezoneAwareAppointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'get_local_time', 'resource_timezone', 
        'user_timezone', 'event_count'
    ]
    
    def get_local_time(self, obj):
        """Display time in user's timezone"""
        local_time = obj.get_local_start_time()
        return format_html(
            '<span title="UTC: {}">{}</span>',
            obj.start_time.isoformat(),
            local_time.strftime('%Y-%m-%d %H:%M %Z')
        )
    get_local_time.short_description = 'Start Time (User TZ)'
    
    def event_count(self, obj):
        """Show number of scheduled events"""
        count = len(obj.scheduled_event_ids)
        return format_html(
            '<span style="color: {};">{} events</span>',
            'green' if count > 0 else 'red',
            count
        )
    event_count.short_description = 'Scheduled Events'
    
    actions = ['reschedule_events', 'cancel_events']
    
    def reschedule_events(self, request, queryset):
        """Admin action to reschedule events"""
        import asyncio
        
        async def reschedule():
            for appointment in queryset:
                await appointment.cancel_events()
                await appointment.schedule_events()
        
        asyncio.run(reschedule())
        self.message_user(request, f"Rescheduled events for {queryset.count()} appointments")
    
    def cancel_events(self, request, queryset):
        """Admin action to cancel events"""
        import asyncio
        
        async def cancel():
            for appointment in queryset:
                await appointment.cancel_events()
        
        asyncio.run(cancel())
        self.message_user(request, f"Cancelled events for {queryset.count()} appointments")
```

## Testing Patterns

### 1. Mocking Event Scheduler

```python
# backend/apps/appointments/tests/test_event_scheduling.py

from unittest.mock import AsyncMock, patch
from django.test import TestCase
from datetime import datetime, timedelta
import zoneinfo

class AppointmentEventTests(TestCase):
    
    @patch('backend.core.clients.event_scheduler.EventSchedulerClient')
    async def test_appointment_schedules_events(self, mock_client_class):
        """Test that creating appointment schedules correct events"""
        
        # Setup mock
        mock_client = AsyncMock()
        mock_client.schedule_event.return_value = "event_123"
        mock_client_class.return_value = mock_client
        
        # Create appointment
        appointment = await Appointment.objects.acreate(
            title="Test Meeting",
            start_time=datetime.now() + timedelta(days=1),
            end_time=datetime.now() + timedelta(days=1, hours=1),
            resource_timezone="America/New_York",
            user_timezone="Europe/London"
        )
        
        # Schedule events
        await appointment.schedule_events()
        
        # Verify calls
        assert mock_client.schedule_event.call_count == 4  # 3 reminders + 1 follow-up
        
        # Check reminder was scheduled with correct timezone
        first_call = mock_client.schedule_event.call_args_list[0]
        assert first_call.kwargs['resource_timezone'] == "America/New_York"
        assert first_call.kwargs['user_timezone'] == "Europe/London"
```

### 2. Integration Testing

```python
# backend/apps/appointments/tests/test_integration.py

import httpx
from django.test import TransactionTestCase
from datetime import datetime, timedelta

class EventSchedulerIntegrationTest(TransactionTestCase):
    """Integration tests with real Event Scheduler Service"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Check if scheduler service is available
        try:
            response = httpx.get("http://localhost:8005/health")
            cls.scheduler_available = response.status_code == 200
        except:
            cls.scheduler_available = False
    
    def test_end_to_end_event_scheduling(self):
        """Test complete event scheduling flow"""
        
        if not self.scheduler_available:
            self.skipTest("Event Scheduler Service not available")
        
        # Create appointment with events
        appointment = Appointment.objects.create(
            title="Integration Test",
            start_time=datetime.now() + timedelta(hours=2),
            end_time=datetime.now() + timedelta(hours=3),
            resource_timezone="UTC",
            user_timezone="UTC"
        )
        
        # Schedule events (synchronously for testing)
        from asgiref.sync import async_to_sync
        async_to_sync(appointment.schedule_events)()
        
        # Verify events were scheduled
        client = EventSchedulerClient()
        events = async_to_sync(client.get_upcoming_events)(
            entity_id=str(appointment.id)
        )
        
        self.assertEqual(len(events), 4)  # 3 reminders + 1 follow-up
```

## Common Pitfalls and Solutions

### 1. Timezone Confusion

**Problem**: Mixing naive and aware datetimes
```python
# WRONG
appointment.start_time = datetime.now()  # Naive datetime
```

**Solution**: Always use timezone-aware datetimes
```python
# CORRECT
from django.utils import timezone
appointment.start_time = timezone.now()  # Aware datetime in UTC
```

### 2. Event Duplication

**Problem**: Scheduling events multiple times
```python
# WRONG - Creates duplicate events
await appointment.schedule_events()
await appointment.schedule_events()  # Duplicates!
```

**Solution**: Cancel existing events before rescheduling
```python
# CORRECT
await appointment.cancel_events()
await appointment.schedule_events()
```

### 3. Synchronous Blocking

**Problem**: Blocking Django thread with async calls
```python
# WRONG - Blocks thread
import asyncio
asyncio.run(schedule_event())  # Blocks!
```

**Solution**: Use Celery for async operations
```python
# CORRECT
from .tasks import schedule_appointment_events
schedule_appointment_events.delay(appointment_id)
```

## Monitoring and Debugging

### 1. Logging Configuration

```python
# backend/config/settings.py

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'event_scheduler': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/event_scheduler.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'backend.core.clients.event_scheduler': {
            'handlers': ['event_scheduler'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 2. Management Commands

```python
# backend/apps/core/management/commands/check_events.py

from django.core.management.base import BaseCommand
from backend.core.clients.event_scheduler import EventSchedulerClient
from asgiref.sync import async_to_sync

class Command(BaseCommand):
    help = 'Check upcoming scheduled events'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--entity-id',
            help='Filter by entity ID',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to look ahead',
        )
    
    def handle(self, *args, **options):
        client = EventSchedulerClient()
        
        end_time = datetime.now() + timedelta(days=options['days'])
        
        events = async_to_sync(client.get_upcoming_events)(
            entity_id=options.get('entity_id'),
            end_time=end_time
        )
        
        self.stdout.write(f"Found {len(events)} upcoming events")
        
        for event in events:
            self.stdout.write(
                f"  - {event['id']}: {event['type']} at {event['scheduled_time']}"
            )
```

## Performance Considerations

1. **Batch Operations**: Schedule multiple events in a single request when possible
2. **Caching**: Cache timezone conversions for frequently used timezones
3. **Async Processing**: Use Celery for non-blocking event scheduling
4. **Connection Pooling**: Reuse HTTP connections to Event Scheduler Service

## Security Notes

1. **API Key**: Always use service-specific API keys for authentication
2. **Payload Encryption**: Encrypt sensitive data in event payloads
3. **Rate Limiting**: Implement rate limiting to prevent event bombing
4. **Audit Logging**: Log all event scheduling operations for compliance

## Next Steps

1. Review the Event Scheduler Service API documentation
2. Implement event scheduling for your appointment models
3. Add Celery task handlers for your event types
4. Test timezone handling with various timezone combinations
5. Monitor event execution in production

## Related Documentation

- [ADR-006: Time-Based Event System Architecture](/Users/stephanerichard/Documents/CODING/ReactDjango-Hub/docs/architecture/adr/006-time-based-event-system-architecture.md)
- [Event Scheduler Service API](/docs/services/event-scheduler/api.md)
- [Celery Configuration Guide](/docs/backend/celery-setup.md)