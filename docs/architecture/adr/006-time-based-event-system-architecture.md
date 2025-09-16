# ADR-006: Time-Based Event System with Complex Timezone Management

## Status
Proposed

## Date
September 10, 2025

## Context

The ReactDjango Hub platform requires a sophisticated time-based event system that goes beyond simple appointment scheduling. The system needs to handle:

1. **Time-based Event Triggers**: Events that fire at specific times, which may or may not be related to appointment bookings
2. **Complex Timezone Scenarios**:
   - Resource location (where the service/resource is physically located)
   - User location (where the person booking is located)
   - Different timezones between multiple participants
   - Daylight Saving Time (DST) transitions
3. **Event Types**:
   - Appointment-related events (reminders, follow-ups)
   - Scheduled workflows and automations
   - Time-based business rules
   - Recurring events with complex patterns
4. **Reliability Requirements**:
   - Events must fire exactly once at the correct time
   - Must handle system failures and restarts gracefully
   - Must handle timezone changes and DST transitions correctly

### Current Architecture Context

- **Identity Service** (Port 8001): User management and authentication
- **Backend Service** (Port 8000): Django-based business logic
- **Communication Service** (Port 8003): Notifications and messaging
- **Workflow Intelligence Service** (Port 8004): Process automation and AI

## Decision

**Implement a hybrid architecture combining a dedicated Event Scheduler Service with distributed event processing across existing services.**

### Architecture Components

1. **Event Scheduler Service** (New - Port 8005)
   - Centralized time-based event scheduling and triggering
   - Timezone-aware event management
   - Reliable event delivery with at-least-once semantics

2. **Distributed Event Processors**
   - Each service processes its own domain events
   - Event handlers registered with the scheduler
   - Service-specific business logic execution

3. **Shared Event Store**
   - PostgreSQL with TimescaleDB extension for time-series data
   - Redis for real-time event queuing
   - Event sourcing for audit and replay capabilities

## Implementation Strategy

### 1. Event Scheduler Service Architecture

```python
# services/event-scheduler-service/models.py

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from enum import Enum
import zoneinfo

class EventType(str, Enum):
    APPOINTMENT_REMINDER = "appointment_reminder"
    WORKFLOW_TRIGGER = "workflow_trigger"
    NOTIFICATION_SCHEDULE = "notification_schedule"
    BUSINESS_RULE = "business_rule"
    CUSTOM = "custom"

class RecurrencePattern(BaseModel):
    """RRULE-based recurrence pattern"""
    frequency: str  # DAILY, WEEKLY, MONTHLY, YEARLY
    interval: int = 1
    count: Optional[int] = None
    until: Optional[datetime] = None
    by_day: Optional[List[str]] = None
    by_month_day: Optional[List[int]] = None
    by_month: Optional[List[int]] = None
    timezone: str  # IANA timezone identifier

class TimezoneContext(BaseModel):
    """Timezone context for an event"""
    resource_timezone: str  # Where the resource is located
    user_timezone: str      # Where the user is located
    execution_timezone: str # Which timezone to use for execution
    
    def get_execution_time(self, scheduled_time: datetime) -> datetime:
        """Convert scheduled time to execution timezone"""
        tz = zoneinfo.ZoneInfo(self.execution_timezone)
        if scheduled_time.tzinfo is None:
            # Assume UTC if no timezone
            scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)
        return scheduled_time.astimezone(tz)

class ScheduledEvent(BaseModel):
    """Core event model"""
    id: str
    type: EventType
    service_id: str  # Which service handles this event
    entity_id: str   # Related entity (appointment_id, workflow_id, etc.)
    
    # Scheduling
    scheduled_time: datetime
    timezone_context: TimezoneContext
    recurrence: Optional[RecurrencePattern] = None
    
    # Execution
    payload: Dict[str, Any]
    max_retries: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: int = 300
    
    # State
    status: str  # scheduled, pending, processing, completed, failed
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    next_attempt: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Audit
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
```

### 2. Timezone Management Strategy

```python
# services/event-scheduler-service/timezone_manager.py

from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import zoneinfo
from dateutil import rrule
import pytz

class TimezoneManager:
    """Sophisticated timezone handling for events"""
    
    def __init__(self):
        self.supported_timezones = list(zoneinfo.available_timezones())
    
    def calculate_event_times(
        self,
        base_time: datetime,
        resource_tz: str,
        participant_timezones: List[str]
    ) -> Dict[str, datetime]:
        """
        Calculate event time in all relevant timezones
        
        Args:
            base_time: The scheduled time in resource timezone
            resource_tz: IANA timezone of the resource
            participant_timezones: List of participant timezones
            
        Returns:
            Dictionary mapping timezone to local time
        """
        resource_zone = zoneinfo.ZoneInfo(resource_tz)
        
        # Ensure base_time has timezone info
        if base_time.tzinfo is None:
            base_time = base_time.replace(tzinfo=resource_zone)
        elif base_time.tzinfo != resource_zone:
            base_time = base_time.astimezone(resource_zone)
        
        times = {"resource": base_time}
        
        for tz_str in participant_timezones:
            participant_zone = zoneinfo.ZoneInfo(tz_str)
            local_time = base_time.astimezone(participant_zone)
            times[tz_str] = local_time
        
        return times
    
    def handle_dst_transition(
        self,
        scheduled_time: datetime,
        timezone_str: str
    ) -> Tuple[datetime, bool]:
        """
        Handle DST transitions for scheduled events
        
        Args:
            scheduled_time: The scheduled time
            timezone_str: IANA timezone identifier
            
        Returns:
            Tuple of (adjusted_time, is_ambiguous)
        """
        tz = zoneinfo.ZoneInfo(timezone_str)
        
        try:
            # Check if time is ambiguous (occurs twice during fall-back)
            localized = scheduled_time.replace(tzinfo=tz)
            
            # Check for DST transition
            utc_offset_before = (scheduled_time - timedelta(hours=1)).replace(tzinfo=tz).utcoffset()
            utc_offset_after = (scheduled_time + timedelta(hours=1)).replace(tzinfo=tz).utcoffset()
            
            if utc_offset_before != utc_offset_after:
                # DST transition detected
                return localized, True
            
            return localized, False
            
        except zoneinfo.ZoneInfoNotFoundError:
            raise ValueError(f"Unknown timezone: {timezone_str}")
    
    def get_next_occurrence(
        self,
        recurrence: RecurrencePattern,
        after: datetime
    ) -> Optional[datetime]:
        """
        Calculate next occurrence of a recurring event
        
        Args:
            recurrence: Recurrence pattern
            after: Calculate next occurrence after this time
            
        Returns:
            Next occurrence datetime or None if no more occurrences
        """
        tz = zoneinfo.ZoneInfo(recurrence.timezone)
        
        # Convert recurrence pattern to rrule
        freq_map = {
            'DAILY': rrule.DAILY,
            'WEEKLY': rrule.WEEKLY,
            'MONTHLY': rrule.MONTHLY,
            'YEARLY': rrule.YEARLY
        }
        
        kwargs = {
            'freq': freq_map[recurrence.frequency],
            'interval': recurrence.interval,
            'dtstart': after.replace(tzinfo=tz)
        }
        
        if recurrence.count:
            kwargs['count'] = recurrence.count
        if recurrence.until:
            kwargs['until'] = recurrence.until.replace(tzinfo=tz)
        if recurrence.by_day:
            kwargs['byweekday'] = recurrence.by_day
        if recurrence.by_month_day:
            kwargs['bymonthday'] = recurrence.by_month_day
        if recurrence.by_month:
            kwargs['bymonth'] = recurrence.by_month
        
        rule = rrule.rrule(**kwargs)
        
        # Get next occurrence
        next_occurrences = list(rule[:2])  # Get next 2 to skip current
        if len(next_occurrences) > 1:
            return next_occurrences[1]
        elif len(next_occurrences) == 1 and next_occurrences[0] > after:
            return next_occurrences[0]
        
        return None
    
    def validate_timezone_compatibility(
        self,
        resource_tz: str,
        user_tz: str
    ) -> Dict[str, Any]:
        """
        Check timezone compatibility and provide warnings
        
        Returns:
            Dictionary with compatibility info and warnings
        """
        resource_zone = zoneinfo.ZoneInfo(resource_tz)
        user_zone = zoneinfo.ZoneInfo(user_tz)
        
        now = datetime.now(tz=resource_zone)
        
        # Calculate offset difference
        resource_offset = now.utcoffset().total_seconds() / 3600
        user_offset = now.astimezone(user_zone).utcoffset().total_seconds() / 3600
        offset_diff = abs(resource_offset - user_offset)
        
        warnings = []
        
        # Check for large timezone differences
        if offset_diff > 12:
            warnings.append(f"Large timezone difference ({offset_diff} hours) may cause confusion")
        
        # Check for DST mismatches
        resource_dst = bool(now.dst())
        user_dst = bool(now.astimezone(user_zone).dst())
        
        if resource_dst != user_dst:
            warnings.append("Resources and user are in different DST states")
        
        return {
            "resource_timezone": resource_tz,
            "user_timezone": user_tz,
            "offset_difference_hours": offset_diff,
            "resource_dst_active": resource_dst,
            "user_dst_active": user_dst,
            "warnings": warnings,
            "compatible": len(warnings) == 0
        }
```

### 3. Event Scheduler Engine

```python
# services/event-scheduler-service/scheduler_engine.py

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from celery import Celery
import logging

logger = logging.getLogger(__name__)

class EventSchedulerEngine:
    """Core scheduling engine with reliable event triggering"""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        celery_app: Celery,
        timezone_manager: TimezoneManager
    ):
        self.redis = redis_client
        self.celery = celery_app
        self.tz_manager = timezone_manager
        self.running = False
        self.scheduler_task = None
        
    async def start(self):
        """Start the scheduler engine"""
        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Event scheduler engine started")
        
    async def stop(self):
        """Stop the scheduler engine gracefully"""
        self.running = False
        if self.scheduler_task:
            await self.scheduler_task
        logger.info("Event scheduler engine stopped")
        
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                # Get events due in the next minute
                now = datetime.utcnow()
                window_end = now + timedelta(minutes=1)
                
                events = await self._get_due_events(now, window_end)
                
                for event in events:
                    asyncio.create_task(self._process_event(event))
                
                # Sleep until next check
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def _get_due_events(
        self,
        start: datetime,
        end: datetime
    ) -> List[ScheduledEvent]:
        """
        Get events due for execution in the time window
        
        Uses Redis sorted set for efficient time-based queries
        """
        # Use Redis ZRANGEBYSCORE for efficient time-based retrieval
        event_ids = await self.redis.zrangebyscore(
            "scheduled_events",
            start.timestamp(),
            end.timestamp()
        )
        
        events = []
        for event_id in event_ids:
            event_data = await self.redis.hget("events", event_id)
            if event_data:
                event = ScheduledEvent.parse_raw(event_data)
                
                # Apply timezone conversion
                exec_time = event.timezone_context.get_execution_time(
                    event.scheduled_time
                )
                
                if start <= exec_time <= end:
                    events.append(event)
        
        return events
    
    async def _process_event(self, event: ScheduledEvent):
        """Process a single event"""
        try:
            # Mark as processing
            event.status = "processing"
            event.attempts += 1
            event.last_attempt = datetime.utcnow()
            await self._update_event(event)
            
            # Send to appropriate service via Celery
            task_name = f"{event.service_id}.process_event"
            result = self.celery.send_task(
                task_name,
                args=[event.dict()],
                queue=event.service_id,
                time_limit=event.timeout_seconds,
                soft_time_limit=event.timeout_seconds - 10
            )
            
            # Wait for result with timeout
            try:
                await asyncio.wait_for(
                    self._wait_for_celery_result(result),
                    timeout=event.timeout_seconds
                )
                
                # Mark as completed
                event.status = "completed"
                event.completed_at = datetime.utcnow()
                
                # Schedule next occurrence if recurring
                if event.recurrence:
                    await self._schedule_next_occurrence(event)
                    
            except asyncio.TimeoutError:
                raise TimeoutError(f"Event processing timed out after {event.timeout_seconds}s")
            
        except Exception as e:
            logger.error(f"Failed to process event {event.id}: {e}")
            event.error_message = str(e)
            
            # Retry logic
            if event.attempts < event.max_retries:
                event.status = "scheduled"
                event.next_attempt = datetime.utcnow() + timedelta(
                    seconds=event.retry_delay_seconds * event.attempts
                )
                await self._reschedule_event(event)
            else:
                event.status = "failed"
                await self._handle_failed_event(event)
        
        finally:
            await self._update_event(event)
    
    async def _schedule_next_occurrence(self, event: ScheduledEvent):
        """Schedule the next occurrence of a recurring event"""
        next_time = self.tz_manager.get_next_occurrence(
            event.recurrence,
            event.scheduled_time
        )
        
        if next_time:
            # Create new event for next occurrence
            next_event = event.copy()
            next_event.id = f"{event.id}_next_{next_time.timestamp()}"
            next_event.scheduled_time = next_time
            next_event.status = "scheduled"
            next_event.attempts = 0
            next_event.last_attempt = None
            next_event.error_message = None
            
            await self.schedule_event(next_event)
    
    async def schedule_event(self, event: ScheduledEvent) -> str:
        """
        Schedule a new event
        
        Returns:
            Event ID
        """
        # Validate timezone
        validation = self.tz_manager.validate_timezone_compatibility(
            event.timezone_context.resource_timezone,
            event.timezone_context.user_timezone
        )
        
        if validation["warnings"]:
            logger.warning(f"Timezone warnings for event {event.id}: {validation['warnings']}")
        
        # Store event
        await self.redis.hset(
            "events",
            event.id,
            event.json()
        )
        
        # Add to scheduled set
        exec_time = event.timezone_context.get_execution_time(event.scheduled_time)
        await self.redis.zadd(
            "scheduled_events",
            {event.id: exec_time.timestamp()}
        )
        
        logger.info(f"Scheduled event {event.id} for {exec_time}")
        return event.id
    
    async def cancel_event(self, event_id: str) -> bool:
        """Cancel a scheduled event"""
        # Remove from scheduled set
        removed = await self.redis.zrem("scheduled_events", event_id)
        
        if removed:
            # Update status
            event_data = await self.redis.hget("events", event_id)
            if event_data:
                event = ScheduledEvent.parse_raw(event_data)
                event.status = "cancelled"
                await self._update_event(event)
                logger.info(f"Cancelled event {event_id}")
                return True
        
        return False
    
    async def _update_event(self, event: ScheduledEvent):
        """Update event in storage"""
        event.updated_at = datetime.utcnow()
        await self.redis.hset(
            "events",
            event.id,
            event.json()
        )
    
    async def _reschedule_event(self, event: ScheduledEvent):
        """Reschedule event for retry"""
        await self.redis.zadd(
            "scheduled_events",
            {event.id: event.next_attempt.timestamp()}
        )
        logger.info(f"Rescheduled event {event.id} for retry at {event.next_attempt}")
    
    async def _handle_failed_event(self, event: ScheduledEvent):
        """Handle permanently failed event"""
        # Send failure notification
        await self._send_failure_notification(event)
        
        # Store in failed events for manual review
        await self.redis.hset(
            "failed_events",
            event.id,
            event.json()
        )
        
        # Remove from scheduled set
        await self.redis.zrem("scheduled_events", event.id)
        
        logger.error(f"Event {event.id} permanently failed after {event.attempts} attempts")
    
    async def _send_failure_notification(self, event: ScheduledEvent):
        """Send notification about failed event"""
        # Send to Communication Service
        notification_event = ScheduledEvent(
            id=f"notification_{event.id}_failed",
            type=EventType.NOTIFICATION_SCHEDULE,
            service_id="communication",
            entity_id=event.id,
            scheduled_time=datetime.utcnow(),
            timezone_context=TimezoneContext(
                resource_timezone="UTC",
                user_timezone="UTC",
                execution_timezone="UTC"
            ),
            payload={
                "template": "event_processing_failed",
                "data": {
                    "event_id": event.id,
                    "event_type": event.type,
                    "error": event.error_message,
                    "attempts": event.attempts
                }
            }
        )
        
        await self.schedule_event(notification_event)
```

### 4. Service Integration Patterns

```python
# backend/apps/appointments/event_integration.py

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from django.conf import settings

class AppointmentEventScheduler:
    """Integration with Event Scheduler Service for appointments"""
    
    def __init__(self):
        self.scheduler_url = settings.EVENT_SCHEDULER_URL
        self.service_id = "backend"
        
    async def schedule_appointment_events(
        self,
        appointment: 'Appointment',
        user_timezone: str,
        resource_timezone: str
    ):
        """Schedule all events for an appointment"""
        
        # Schedule reminder events
        await self._schedule_reminders(appointment, user_timezone, resource_timezone)
        
        # Schedule follow-up events
        await self._schedule_follow_ups(appointment, user_timezone, resource_timezone)
        
        # Schedule workflow triggers
        await self._schedule_workflow_triggers(appointment, user_timezone, resource_timezone)
    
    async def _schedule_reminders(
        self,
        appointment: 'Appointment',
        user_tz: str,
        resource_tz: str
    ):
        """Schedule reminder events"""
        
        reminder_times = [
            timedelta(days=1),   # 24 hours before
            timedelta(hours=2),  # 2 hours before
            timedelta(minutes=15) # 15 minutes before
        ]
        
        for delta in reminder_times:
            reminder_time = appointment.start_time - delta
            
            event = {
                "id": f"reminder_{appointment.id}_{delta.total_seconds()}",
                "type": "APPOINTMENT_REMINDER",
                "service_id": "communication",
                "entity_id": str(appointment.id),
                "scheduled_time": reminder_time.isoformat(),
                "timezone_context": {
                    "resource_timezone": resource_tz,
                    "user_timezone": user_tz,
                    "execution_timezone": user_tz  # Send in user's timezone
                },
                "payload": {
                    "appointment_id": str(appointment.id),
                    "reminder_type": f"{delta.total_seconds()}_seconds_before",
                    "channels": ["email", "sms", "push"],
                    "template_data": {
                        "appointment_title": appointment.title,
                        "start_time": appointment.start_time.isoformat(),
                        "location": appointment.location,
                        "time_until": self._format_time_delta(delta)
                    }
                }
            }
            
            await self._send_to_scheduler(event)
    
    async def _schedule_follow_ups(
        self,
        appointment: 'Appointment',
        user_tz: str,
        resource_tz: str
    ):
        """Schedule post-appointment follow-ups"""
        
        # Follow-up 1 hour after appointment ends
        follow_up_time = appointment.end_time + timedelta(hours=1)
        
        event = {
            "id": f"followup_{appointment.id}",
            "type": "APPOINTMENT_FOLLOW_UP",
            "service_id": "communication",
            "entity_id": str(appointment.id),
            "scheduled_time": follow_up_time.isoformat(),
            "timezone_context": {
                "resource_timezone": resource_tz,
                "user_timezone": user_tz,
                "execution_timezone": resource_tz  # Process in resource timezone
            },
            "payload": {
                "appointment_id": str(appointment.id),
                "follow_up_type": "satisfaction_survey",
                "channels": ["email"],
                "template": "appointment_follow_up_survey"
            }
        }
        
        await self._send_to_scheduler(event)
    
    async def _schedule_workflow_triggers(
        self,
        appointment: 'Appointment',
        user_tz: str,
        resource_tz: str
    ):
        """Schedule workflow automation triggers"""
        
        # Trigger no-show detection 30 minutes after start
        no_show_check = appointment.start_time + timedelta(minutes=30)
        
        event = {
            "id": f"workflow_noshow_{appointment.id}",
            "type": "WORKFLOW_TRIGGER",
            "service_id": "workflow-intelligence",
            "entity_id": str(appointment.id),
            "scheduled_time": no_show_check.isoformat(),
            "timezone_context": {
                "resource_timezone": resource_tz,
                "user_timezone": user_tz,
                "execution_timezone": resource_tz
            },
            "payload": {
                "workflow_id": "appointment_no_show_detection",
                "context": {
                    "appointment_id": str(appointment.id),
                    "check_type": "no_show",
                    "threshold_minutes": 30
                }
            }
        }
        
        await self._send_to_scheduler(event)
    
    async def _send_to_scheduler(self, event: Dict[str, Any]):
        """Send event to scheduler service"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.scheduler_url}/api/events/schedule",
                json=event,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    
    async def cancel_appointment_events(self, appointment_id: str):
        """Cancel all events for an appointment"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.scheduler_url}/api/events/entity/{appointment_id}",
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()

# Celery task handler for incoming events
from celery import shared_task

@shared_task(name="backend.process_event")
def process_scheduled_event(event_data: Dict[str, Any]):
    """Process events from scheduler service"""
    
    event_type = event_data["type"]
    
    if event_type == "APPOINTMENT_REMINDER":
        # This should actually be handled by communication service
        # But we might update appointment status
        from .models import Appointment
        appointment = Appointment.objects.get(id=event_data["entity_id"])
        appointment.last_reminder_sent = datetime.utcnow()
        appointment.save()
        
    elif event_type == "BUSINESS_RULE":
        # Execute business rule
        from .business_rules import execute_rule
        execute_rule(event_data["payload"]["rule_id"], event_data["payload"]["context"])
        
    return {"status": "processed", "event_id": event_data["id"]}
```

### 5. API Design for Event Scheduler Service

```python
# services/event-scheduler-service/api.py

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/events", tags=["events"])

@router.post("/schedule")
async def schedule_event(
    event: ScheduledEventRequest,
    current_user: dict = Depends(validate_jwt_token)
) -> ScheduledEventResponse:
    """Schedule a new event"""
    
    # Validate service permissions
    if not has_service_permission(current_user, event.service_id):
        raise HTTPException(403, "No permission for target service")
    
    # Create event
    scheduled_event = ScheduledEvent(
        id=generate_event_id(),
        created_by=current_user["user_id"],
        created_at=datetime.utcnow(),
        status="scheduled",
        **event.dict()
    )
    
    # Schedule with engine
    event_id = await scheduler_engine.schedule_event(scheduled_event)
    
    return ScheduledEventResponse(
        event_id=event_id,
        scheduled_time=scheduled_event.scheduled_time,
        timezone_context=scheduled_event.timezone_context,
        status="scheduled"
    )

@router.get("/upcoming")
async def get_upcoming_events(
    entity_id: Optional[str] = None,
    service_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    timezone: str = "UTC",
    limit: int = 100
) -> List[ScheduledEventResponse]:
    """Get upcoming scheduled events"""
    
    events = await event_repository.get_upcoming_events(
        entity_id=entity_id,
        service_id=service_id,
        start_time=start_time or datetime.utcnow(),
        end_time=end_time,
        timezone=timezone,
        limit=limit
    )
    
    return [ScheduledEventResponse.from_orm(e) for e in events]

@router.delete("/{event_id}")
async def cancel_event(
    event_id: str,
    current_user: dict = Depends(validate_jwt_token)
) -> dict:
    """Cancel a scheduled event"""
    
    cancelled = await scheduler_engine.cancel_event(event_id)
    
    if not cancelled:
        raise HTTPException(404, "Event not found")
    
    return {"status": "cancelled", "event_id": event_id}

@router.delete("/entity/{entity_id}")
async def cancel_entity_events(
    entity_id: str,
    current_user: dict = Depends(validate_jwt_token)
) -> dict:
    """Cancel all events for an entity"""
    
    count = await event_repository.cancel_entity_events(entity_id)
    
    return {
        "status": "cancelled",
        "entity_id": entity_id,
        "events_cancelled": count
    }

@router.post("/timezone/convert")
async def convert_timezone(
    request: TimezoneConversionRequest
) -> TimezoneConversionResponse:
    """Convert time between timezones"""
    
    tz_manager = TimezoneManager()
    
    times = tz_manager.calculate_event_times(
        base_time=request.time,
        resource_tz=request.from_timezone,
        participant_timezones=request.to_timezones
    )
    
    return TimezoneConversionResponse(
        original_time=request.time,
        conversions=times
    )

@router.post("/timezone/validate")
async def validate_timezones(
    request: TimezoneValidationRequest
) -> TimezoneValidationResponse:
    """Validate timezone compatibility"""
    
    tz_manager = TimezoneManager()
    
    validation = tz_manager.validate_timezone_compatibility(
        resource_tz=request.resource_timezone,
        user_tz=request.user_timezone
    )
    
    return TimezoneValidationResponse(**validation)
```

## Consequences

### Positive

1. **Centralized Event Management**
   - Single source of truth for all time-based events
   - Consistent timezone handling across all services
   - Unified monitoring and debugging of scheduled events

2. **Reliability & Resilience**
   - At-least-once delivery guarantee with idempotent handlers
   - Automatic retry with exponential backoff
   - Graceful handling of service failures

3. **Timezone Accuracy**
   - Sophisticated timezone conversion and DST handling
   - Support for multiple timezone contexts per event
   - Validation and warnings for timezone issues

4. **Scalability**
   - Horizontal scaling of scheduler service
   - Efficient time-based queries with Redis
   - Distributed event processing across services

5. **Flexibility**
   - Support for complex recurrence patterns
   - Service-agnostic event scheduling
   - Easy to add new event types and handlers

### Negative

1. **Additional Complexity**
   - New service to deploy and maintain
   - More complex debugging across services
   - Additional failure points in the system

2. **Operational Overhead**
   - Need to monitor scheduler service health
   - Database maintenance for event history
   - Timezone database updates required

3. **Latency Considerations**
   - Additional network hop for event scheduling
   - Potential delays in event processing
   - Queue congestion during peak times

### Risks

1. **Clock Synchronization**
   - Risk Level: **Medium**
   - Mitigation: Use NTP across all services, implement clock drift detection

2. **Event Storm**
   - Risk Level: **Medium**
   - Mitigation: Rate limiting, circuit breakers, queue management

3. **Timezone Database Inconsistency**
   - Risk Level: **Low**
   - Mitigation: Regular updates, version tracking, validation

4. **Data Loss on Failure**
   - Risk Level: **Medium**
   - Mitigation: Persistent storage, event sourcing, regular backups

## Alternatives Considered

### Alternative 1: Distributed Scheduling (Each Service Manages Own Events)

**Pros:**
- No central point of failure
- Services maintain autonomy
- Simpler architecture

**Cons:**
- Inconsistent timezone handling
- Difficult to coordinate cross-service events
- Duplicated scheduling logic
- Hard to monitor and debug

**Why Rejected:** The complexity of timezone management and cross-service coordination makes centralized scheduling more maintainable.

### Alternative 2: Use Existing Workflow Service

**Pros:**
- No new service needed
- Leverage existing workflow capabilities
- Integrated with business processes

**Cons:**
- Workflow service becomes overloaded
- Not optimized for time-based operations
- Mixing concerns (workflows vs. scheduling)

**Why Rejected:** Scheduling is a distinct concern that deserves dedicated optimization and shouldn't be coupled with workflow logic.

### Alternative 3: Third-Party Scheduling Service (e.g., Temporal, Airflow)

**Pros:**
- Battle-tested solutions
- Rich feature set
- Community support

**Cons:**
- Additional external dependency
- May be overkill for our needs
- Learning curve for team
- Integration complexity

**Why Rejected:** While viable, building a focused solution gives us exactly what we need without unnecessary complexity.

## Implementation Plan

### Phase 1: Core Scheduler Service (Week 1-2)
1. Set up Event Scheduler Service structure
2. Implement timezone management module
3. Build core scheduling engine
4. Create event storage with PostgreSQL/TimescaleDB
5. Implement Redis-based event queue

### Phase 2: Service Integration (Week 3)
1. Add Celery task routing
2. Implement event handlers in each service
3. Create service client libraries
4. Build appointment event integration
5. Add workflow trigger support

### Phase 3: Reliability & Monitoring (Week 4)
1. Implement retry mechanisms
2. Add circuit breakers
3. Create monitoring dashboards
4. Set up alerting
5. Build event replay capability

### Phase 4: Advanced Features (Week 5)
1. Complex recurrence patterns
2. Bulk event operations
3. Event templates
4. Performance optimization
5. Admin UI for event management

## Monitoring and Success Metrics

### Key Performance Indicators
- Event scheduling latency < 100ms (p95)
- Event execution accuracy > 99.99%
- Timezone conversion accuracy: 100%
- Event retry success rate > 95%
- System uptime > 99.9%

### Monitoring Strategy
- Track event lifecycle metrics (scheduled, executed, failed)
- Monitor timezone conversion requests
- Alert on failed events after max retries
- Dashboard for upcoming events by service
- Track queue depth and processing rates

## Security Considerations

1. **Event Payload Encryption**
   - Encrypt sensitive data in event payloads
   - Use service-specific encryption keys

2. **Access Control**
   - Service-level authentication for event scheduling
   - Audit trail for all event operations

3. **Rate Limiting**
   - Prevent event bombing
   - Per-service quotas

## Conclusion

The Event Scheduler Service architecture provides a robust, timezone-aware event scheduling system that addresses all requirements:

1. **Sophisticated timezone handling** with support for resource and user timezone contexts
2. **Reliable event execution** with retry mechanisms and failure handling
3. **Scalable architecture** supporting the entire platform's scheduling needs
4. **Clear separation of concerns** with centralized scheduling and distributed processing

This design ensures events fire at the correct time regardless of timezone complexity while maintaining system reliability and performance.

## References

- IANA Time Zone Database: https://www.iana.org/time-zones
- RFC 5545 (iCalendar Recurrence Rules): https://tools.ietf.org/html/rfc5545
- TimescaleDB Documentation: https://docs.timescale.com/
- Celery Beat for Periodic Tasks: https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html
- Python zoneinfo Documentation: https://docs.python.org/3/library/zoneinfo.html

## Review and Approval

- **Author**: Technical Lead Agent (ag-techlead)
- **Date**: 2025-01-10
- **Status**: Proposed
- **Reviewers**: Backend Team, Infrastructure Team, Communication Team, Workflow Team
- **Implementation Start**: Upon approval