# ADR-006-REVISED: Progressive Time-Based Event System Using Django + Celery

## Status
Proposed (Revised based on Technical Review)

## Date
2025-01-10

## Context

The ReactDjango Hub platform requires a time-based event system for scheduling and triggering events at specific times. Key requirements include:

1. **Core Functionality**:
   - Schedule events to fire at specific times
   - Support for appointment reminders and follow-ups
   - Workflow automation triggers
   - Business rule execution

2. **Timezone Management**:
   - Handle events across different timezones
   - Support DST transitions correctly
   - Manage resource vs user timezone contexts

3. **Reliability**:
   - Ensure events fire on time
   - Provide retry mechanisms for failures
   - Maintain audit trail of all events

4. **Current Architecture**:
   - Identity Service (Port 8001): Authentication and users
   - Backend Service (Port 8000): Django-based business logic
   - Limited operational team capacity
   - Django + PostgreSQL + Redis already in use

## Decision

**Implement a progressive event scheduling system starting with Django + Celery Beat**, with clear evolution paths based on actual usage patterns and requirements.

### Progressive Architecture Strategy

```
Phase 1: Django + Celery Beat (MVP)
    ↓ (If >10K events/hour)
Phase 2: Enhanced with Redis Caching
    ↓ (If >100K events/hour)
Phase 3: Evaluate Managed Service or Microservice
```

## Implementation Strategy

### Phase 1: MVP Implementation (Weeks 1-2)

#### Core Architecture

```python
# backend/apps/scheduling/models.py

from django.db import models
from django.contrib.postgres.fields import JSONField
import zoneinfo
from datetime import datetime

class ScheduledEvent(models.Model):
    """Simple event model using Django ORM"""
    
    EVENT_TYPES = [
        ('appointment_reminder', 'Appointment Reminder'),
        ('appointment_followup', 'Appointment Follow-up'),
        ('workflow_trigger', 'Workflow Trigger'),
        ('business_rule', 'Business Rule'),
        ('notification', 'Notification'),
    ]
    
    EVENT_STATUS = [
        ('scheduled', 'Scheduled'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Core fields
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    scheduled_time = models.DateTimeField(db_index=True)
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Related entity
    entity_type = models.CharField(max_length=50)  # 'appointment', 'workflow', etc.
    entity_id = models.CharField(max_length=255, db_index=True)
    
    # Execution details
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=EVENT_STATUS, default='scheduled')
    attempts = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Celery task tracking
    task_id = models.CharField(max_length=255, blank=True, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['scheduled_time', 'status']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]
        ordering = ['scheduled_time']
    
    def schedule(self):
        """Schedule this event with Celery"""
        from .tasks import process_scheduled_event
        
        # Convert to target timezone for execution
        tz = zoneinfo.ZoneInfo(self.timezone)
        local_time = self.scheduled_time.astimezone(tz)
        
        # Schedule with Celery
        result = process_scheduled_event.apply_async(
            args=[self.id],
            eta=local_time
        )
        
        self.task_id = result.id
        self.save(update_fields=['task_id'])
        
        return result.id
    
    def cancel(self):
        """Cancel this scheduled event"""
        from celery.result import AsyncResult
        
        if self.task_id and self.status == 'scheduled':
            # Revoke Celery task
            AsyncResult(self.task_id).revoke()
            
            self.status = 'cancelled'
            self.save(update_fields=['status'])
            return True
        
        return False
```

#### Celery Tasks Implementation

```python
# backend/apps/scheduling/tasks.py

from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, soft_time_limit=300)
def process_scheduled_event(self, event_id):
    """
    Process a scheduled event with automatic retry on failure
    """
    from .models import ScheduledEvent
    from .handlers import EVENT_HANDLERS
    
    try:
        with transaction.atomic():
            event = ScheduledEvent.objects.select_for_update().get(id=event_id)
            
            # Check if already processed or cancelled
            if event.status in ['completed', 'cancelled']:
                return {'status': 'skipped', 'reason': event.status}
            
            # Update status
            event.status = 'processing'
            event.attempts += 1
            event.save(update_fields=['status', 'attempts'])
        
        # Get appropriate handler
        handler = EVENT_HANDLERS.get(event.event_type)
        if not handler:
            raise ValueError(f"No handler for event type: {event.event_type}")
        
        # Process the event
        result = handler(event)
        
        # Mark as completed
        event.status = 'completed'
        event.completed_at = timezone.now()
        event.save(update_fields=['status', 'completed_at'])
        
        logger.info(f"Successfully processed event {event_id} of type {event.event_type}")
        return result
        
    except Exception as exc:
        logger.error(f"Error processing event {event_id}: {exc}")
        
        # Update event with error
        event.error_message = str(exc)
        event.save(update_fields=['error_message'])
        
        # Retry with exponential backoff
        if self.request.retries < event.max_retries:
            countdown = 2 ** self.request.retries * 60  # 1, 2, 4 minutes
            raise self.retry(exc=exc, countdown=countdown)
        else:
            # Max retries exceeded
            event.status = 'failed'
            event.save(update_fields=['status'])
            
            # Send failure notification
            notify_event_failure.delay(event_id)
            
            raise

@shared_task
def notify_event_failure(event_id):
    """Notify about failed events"""
    from .models import ScheduledEvent
    from apps.notifications.services import NotificationService
    
    event = ScheduledEvent.objects.get(id=event_id)
    
    NotificationService.send_admin_alert(
        subject=f"Event Processing Failed: {event.event_type}",
        message=f"Event {event_id} failed after {event.attempts} attempts. Error: {event.error_message}",
        severity='high'
    )

@shared_task
def cleanup_old_events():
    """Clean up old completed/failed events"""
    from datetime import timedelta
    from .models import ScheduledEvent
    
    cutoff = timezone.now() - timedelta(days=30)
    
    count = ScheduledEvent.objects.filter(
        status__in=['completed', 'cancelled'],
        completed_at__lt=cutoff
    ).delete()[0]
    
    logger.info(f"Cleaned up {count} old events")
    return count
```

#### Event Handlers

```python
# backend/apps/scheduling/handlers.py

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def handle_appointment_reminder(event: 'ScheduledEvent') -> Dict[str, Any]:
    """Handle appointment reminder events"""
    from apps.appointments.models import Appointment
    from apps.notifications.services import NotificationService
    
    appointment = Appointment.objects.get(id=event.entity_id)
    
    # Send reminder through notification service
    NotificationService.send_appointment_reminder(
        appointment=appointment,
        channels=event.payload.get('channels', ['email']),
        template_data=event.payload.get('template_data', {})
    )
    
    # Update appointment
    appointment.last_reminder_sent = timezone.now()
    appointment.save(update_fields=['last_reminder_sent'])
    
    return {
        'status': 'sent',
        'appointment_id': appointment.id,
        'channels': event.payload.get('channels')
    }

def handle_workflow_trigger(event: 'ScheduledEvent') -> Dict[str, Any]:
    """Trigger workflow automation"""
    from apps.workflows.services import WorkflowService
    
    workflow_id = event.payload.get('workflow_id')
    context = event.payload.get('context', {})
    
    result = WorkflowService.execute_workflow(
        workflow_id=workflow_id,
        context=context,
        triggered_by=f"scheduled_event_{event.id}"
    )
    
    return {
        'status': 'triggered',
        'workflow_id': workflow_id,
        'execution_id': result.execution_id
    }

def handle_business_rule(event: 'ScheduledEvent') -> Dict[str, Any]:
    """Execute business rules"""
    from apps.rules.engine import RuleEngine
    
    rule_id = event.payload.get('rule_id')
    context = event.payload.get('context', {})
    
    result = RuleEngine.execute_rule(rule_id, context)
    
    return {
        'status': 'executed',
        'rule_id': rule_id,
        'actions_taken': result.actions
    }

# Registry of event handlers
EVENT_HANDLERS = {
    'appointment_reminder': handle_appointment_reminder,
    'appointment_followup': handle_appointment_reminder,  # Reuse same handler
    'workflow_trigger': handle_workflow_trigger,
    'business_rule': handle_business_rule,
    'notification': lambda e: handle_notification(e),
}
```

#### Service Layer for Easy Use

```python
# backend/apps/scheduling/services.py

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import zoneinfo
from django.db import transaction

class EventSchedulingService:
    """High-level service for scheduling events"""
    
    @classmethod
    def schedule_appointment_reminders(
        cls,
        appointment: 'Appointment',
        user_timezone: str = 'UTC'
    ) -> List[str]:
        """Schedule standard reminders for an appointment"""
        from .models import ScheduledEvent
        
        event_ids = []
        
        # Standard reminder times
        reminder_deltas = [
            (timedelta(days=1), 'day_before'),
            (timedelta(hours=2), 'two_hours_before'),
            (timedelta(minutes=15), 'fifteen_minutes_before'),
        ]
        
        with transaction.atomic():
            for delta, reminder_type in reminder_deltas:
                reminder_time = appointment.start_time - delta
                
                # Skip if in the past
                if reminder_time <= timezone.now():
                    continue
                
                event = ScheduledEvent.objects.create(
                    event_type='appointment_reminder',
                    scheduled_time=reminder_time,
                    timezone=user_timezone,
                    entity_type='appointment',
                    entity_id=str(appointment.id),
                    payload={
                        'reminder_type': reminder_type,
                        'channels': ['email', 'sms'],
                        'template_data': {
                            'appointment_title': appointment.title,
                            'start_time': appointment.start_time.isoformat(),
                            'location': appointment.location,
                        }
                    },
                    created_by=appointment.user
                )
                
                # Schedule with Celery
                task_id = event.schedule()
                event_ids.append(event.id)
        
        return event_ids
    
    @classmethod
    def schedule_recurring_event(
        cls,
        event_type: str,
        start_time: datetime,
        recurrence_rule: str,  # RRULE format
        timezone_str: str,
        payload: Dict[str, Any],
        count: int = 10
    ) -> List[str]:
        """Schedule recurring events using dateutil.rrule"""
        from dateutil import rrule
        from .models import ScheduledEvent
        
        # Parse recurrence rule
        rule = rrule.rrulestr(recurrence_rule, dtstart=start_time)
        
        # Generate occurrences
        occurrences = list(rule[:count])
        
        event_ids = []
        for occurrence in occurrences:
            event = ScheduledEvent.objects.create(
                event_type=event_type,
                scheduled_time=occurrence,
                timezone=timezone_str,
                entity_type='recurring',
                entity_id=f"recurring_{start_time.timestamp()}",
                payload=payload
            )
            event.schedule()
            event_ids.append(event.id)
        
        return event_ids
    
    @classmethod
    def cancel_entity_events(
        cls,
        entity_type: str,
        entity_id: str
    ) -> int:
        """Cancel all scheduled events for an entity"""
        from .models import ScheduledEvent
        
        events = ScheduledEvent.objects.filter(
            entity_type=entity_type,
            entity_id=entity_id,
            status='scheduled'
        )
        
        count = 0
        for event in events:
            if event.cancel():
                count += 1
        
        return count
    
    @classmethod
    def get_upcoming_events(
        cls,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        days_ahead: int = 7
    ) -> List['ScheduledEvent']:
        """Get upcoming scheduled events"""
        from .models import ScheduledEvent
        
        queryset = ScheduledEvent.objects.filter(
            status='scheduled',
            scheduled_time__lte=timezone.now() + timedelta(days=days_ahead)
        )
        
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)
        
        return list(queryset.order_by('scheduled_time'))
```

#### Django Admin Interface

```python
# backend/apps/scheduling/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import ScheduledEvent

@admin.register(ScheduledEvent)
class ScheduledEventAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'event_type', 'scheduled_time', 'timezone',
        'status_badge', 'entity_info', 'attempts', 'created_by'
    ]
    list_filter = ['event_type', 'status', 'timezone', 'created_at']
    search_fields = ['entity_id', 'entity_type', 'error_message']
    readonly_fields = ['task_id', 'created_at', 'completed_at']
    
    actions = ['cancel_events', 'retry_failed_events']
    
    def status_badge(self, obj):
        colors = {
            'scheduled': 'blue',
            'processing': 'orange',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def entity_info(self, obj):
        return f"{obj.entity_type}:{obj.entity_id}"
    entity_info.short_description = 'Entity'
    
    def cancel_events(self, request, queryset):
        count = 0
        for event in queryset.filter(status='scheduled'):
            if event.cancel():
                count += 1
        self.message_user(request, f"Cancelled {count} events")
    cancel_events.short_description = "Cancel selected events"
    
    def retry_failed_events(self, request, queryset):
        from .tasks import process_scheduled_event
        
        count = 0
        for event in queryset.filter(status='failed'):
            event.status = 'scheduled'
            event.attempts = 0
            event.error_message = ''
            event.save()
            
            process_scheduled_event.delay(event.id)
            count += 1
        
        self.message_user(request, f"Retrying {count} failed events")
    retry_failed_events.short_description = "Retry failed events"
```

### Phase 2: Enhanced Features (When Needed)

#### Add Redis Caching for High-Volume

```python
# backend/apps/scheduling/cache.py

import redis
from django.conf import settings
import json
from datetime import datetime

class EventCache:
    """Redis caching for high-volume event processing"""
    
    def __init__(self):
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
        self.ttl = 3600  # 1 hour cache
    
    def add_upcoming_event(self, event: 'ScheduledEvent'):
        """Add event to Redis sorted set for quick retrieval"""
        score = event.scheduled_time.timestamp()
        value = json.dumps({
            'id': event.id,
            'type': event.event_type,
            'entity': f"{event.entity_type}:{event.entity_id}"
        })
        
        self.redis.zadd('upcoming_events', {value: score})
        self.redis.expire('upcoming_events', self.ttl)
    
    def get_due_events(self, window_minutes: int = 5) -> List[int]:
        """Get events due in the next window"""
        now = datetime.now().timestamp()
        future = now + (window_minutes * 60)
        
        results = self.redis.zrangebyscore('upcoming_events', now, future)
        
        event_ids = []
        for result in results:
            data = json.loads(result)
            event_ids.append(data['id'])
        
        return event_ids
```

#### Monitoring and Metrics

```python
# backend/apps/scheduling/monitoring.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.scheduling.models import ScheduledEvent

class EventMetrics:
    """Collect metrics for monitoring"""
    
    @classmethod
    def get_metrics(cls) -> dict:
        now = timezone.now()
        day_ago = now - timedelta(days=1)
        
        return {
            'scheduled_count': ScheduledEvent.objects.filter(
                status='scheduled'
            ).count(),
            
            'completed_24h': ScheduledEvent.objects.filter(
                status='completed',
                completed_at__gte=day_ago
            ).count(),
            
            'failed_24h': ScheduledEvent.objects.filter(
                status='failed',
                completed_at__gte=day_ago
            ).count(),
            
            'processing_time_avg': ScheduledEvent.objects.filter(
                status='completed',
                completed_at__gte=day_ago
            ).aggregate(
                avg_time=Avg(F('completed_at') - F('scheduled_time'))
            )['avg_time'],
            
            'retry_rate': cls._calculate_retry_rate(),
        }
    
    @classmethod
    def _calculate_retry_rate(cls) -> float:
        total = ScheduledEvent.objects.filter(
            status__in=['completed', 'failed']
        ).count()
        
        if total == 0:
            return 0.0
        
        retried = ScheduledEvent.objects.filter(
            status__in=['completed', 'failed'],
            attempts__gt=1
        ).count()
        
        return (retried / total) * 100
```

### Phase 3: Evolution Triggers

Define clear metrics for when to evolve the architecture:

```python
# backend/apps/scheduling/evolution_metrics.py

class ArchitectureEvolutionMetrics:
    """
    Monitor metrics to determine when to evolve architecture
    """
    
    THRESHOLDS = {
        'events_per_hour': 10000,  # Consider Redis caching
        'events_per_day': 100000,  # Consider managed service
        'failure_rate': 5.0,  # Percentage requiring investigation
        'avg_delay': 60,  # Seconds of scheduling delay
    }
    
    @classmethod
    def check_evolution_needed(cls) -> dict:
        from .monitoring import EventMetrics
        
        metrics = EventMetrics.get_metrics()
        
        recommendations = []
        
        # Check event volume
        events_per_hour = metrics['completed_24h'] / 24
        if events_per_hour > cls.THRESHOLDS['events_per_hour']:
            recommendations.append({
                'issue': 'High event volume',
                'current': events_per_hour,
                'threshold': cls.THRESHOLDS['events_per_hour'],
                'recommendation': 'Consider adding Redis caching layer'
            })
        
        # Check failure rate
        total = metrics['completed_24h'] + metrics['failed_24h']
        if total > 0:
            failure_rate = (metrics['failed_24h'] / total) * 100
            if failure_rate > cls.THRESHOLDS['failure_rate']:
                recommendations.append({
                    'issue': 'High failure rate',
                    'current': failure_rate,
                    'threshold': cls.THRESHOLDS['failure_rate'],
                    'recommendation': 'Investigate failure causes, consider circuit breakers'
                })
        
        return {
            'evolution_needed': len(recommendations) > 0,
            'recommendations': recommendations,
            'metrics': metrics
        }
```

## Consequences

### Positive

1. **Immediate Value Delivery**
   - Working solution in 1-2 weeks vs 4-5 weeks
   - Uses existing team knowledge and tools
   - No new operational overhead

2. **Progressive Complexity**
   - Start simple, evolve based on real needs
   - Clear metrics for when to evolve
   - Avoid premature optimization

3. **Operational Simplicity**
   - No new services to deploy and monitor
   - Uses Django Admin for management
   - Existing logging and monitoring tools work

4. **Cost Effective**
   - No new infrastructure costs
   - Minimal development time
   - Low maintenance overhead

### Negative

1. **Initial Scalability Limits**
   - Single database bottleneck (mitigated by PostgreSQL scaling)
   - Limited to ~10K events/hour initially
   - May need refactoring if massive scale required

2. **Less Sophisticated**
   - No built-in event replay (can be added)
   - Simpler timezone handling (adequate for most cases)
   - Less granular monitoring initially

### Risks and Mitigations

| Risk | Level | Mitigation |
|------|-------|------------|
| PostgreSQL bottleneck | Low | Index optimization, partitioning if needed |
| Celery worker failures | Low | Multiple workers, automatic restart |
| Timezone edge cases | Low | Comprehensive testing, use zoneinfo |
| Event storms | Medium | Rate limiting, circuit breakers in Phase 2 |

## Migration Path to Advanced Architecture

If metrics indicate need for evolution:

### Option 1: Managed Service Migration
```python
# Easy migration to AWS EventBridge
class EventBridgeAdapter:
    def schedule_event(self, event: ScheduledEvent):
        # Translate to EventBridge format
        return eventbridge.put_events(
            Entries=[{
                'Source': 'reactdjango.hub',
                'DetailType': event.event_type,
                'Detail': json.dumps(event.payload),
                'Time': event.scheduled_time
            }]
        )
```

### Option 2: Microservice Extraction
- Database already has all event data
- Service interfaces already defined
- Can run both in parallel during migration

## Conclusion

This revised architecture provides:

1. **Immediate solution** using existing tools
2. **Clear evolution path** based on metrics
3. **Lower risk** and operational overhead
4. **Faster time to market**

The progressive approach ensures we solve today's problems today, while maintaining flexibility for tomorrow's challenges.

## References

- Django Celery Beat: https://django-celery-beat.readthedocs.io/
- Celery Best Practices: https://docs.celeryq.dev/en/stable/userguide/
- PostgreSQL Performance: https://www.postgresql.org/docs/current/performance-tips.html
- AWS EventBridge (future): https://aws.amazon.com/eventbridge/

## Review and Approval

- **Author**: Technical Lead Agent (Revised)
- **Date**: 2025-01-10
- **Status**: Proposed (Revised)
- **Implementation Start**: Immediate upon approval
- **First Review**: After 2 weeks of production use