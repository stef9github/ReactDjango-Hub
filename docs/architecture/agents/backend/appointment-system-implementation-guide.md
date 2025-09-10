# Backend Agent: Appointment System Implementation Guide

## Architecture Context for Backend Agent

This guide provides the Backend Agent (ag-backend) with specific architectural guidance for implementing the appointment system within the Django backend service, as decided in ADR-005.

## Service Integration Overview

### Your Domain Boundaries
As the Backend Agent, you are responsible for implementing the appointment system within the Django backend service (Port 8000). This includes:
- Creating the appointments Django app
- Implementing data models and migrations
- Building Django Ninja API endpoints
- Integrating with the Identity Service for authentication
- Managing business logic and data persistence

### Service Dependencies

#### Identity Service Integration (Port 8001)
The Identity Service provides authentication and user data. You will need to:

```python
# backend/apps/appointments/clients/identity.py
import httpx
from typing import Optional, Dict, Any

class IdentityServiceClient:
    """Client for interacting with Identity Service"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and get user info"""
        response = await self.client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_user(self, user_id: str, token: str) -> Dict[str, Any]:
        """Get user details by ID"""
        response = await self.client.get(
            f"/users/{user_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()
    
    async def get_organization(self, org_id: str, token: str) -> Dict[str, Any]:
        """Get organization details"""
        # To be implemented when organization endpoints are available
        pass
```

## Implementation Checklist

### Phase 1: Core Setup (Priority 1)

#### 1. Create Django App Structure
```bash
# Run from backend directory
python manage.py startapp appointments
mv appointments apps/

# Create the following structure:
apps/appointments/
├── __init__.py
├── models.py
├── api.py
├── services.py
├── serializers.py
├── tasks.py
├── clients/
│   ├── __init__.py
│   └── identity.py
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_api.py
│   └── test_services.py
└── migrations/
    └── __init__.py
```

#### 2. Update Django Settings
```python
# backend/config/settings/base.py

INSTALLED_APPS = [
    # ... existing apps
    'apps.appointments',
]

# Add appointment-specific settings
APPOINTMENT_SETTINGS = {
    'DEFAULT_DURATION_MINUTES': 30,
    'MAX_ADVANCE_BOOKING_DAYS': 90,
    'MIN_ADVANCE_BOOKING_HOURS': 24,
    'MAX_APPOINTMENTS_PER_DAY': 20,
    'WORKING_HOURS': {
        'start': '09:00',
        'end': '17:00',
    },
    'REMINDER_INTERVALS': [24, 2],  # Hours before appointment
}
```

### Phase 2: Data Models (Priority 1)

```python
# apps/appointments/models.py

from django.db import models
from apps.core.models import BaseModel
import uuid
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator

class AppointmentStatus(models.TextChoices):
    SCHEDULED = 'scheduled', 'Scheduled'
    CONFIRMED = 'confirmed', 'Confirmed'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    NO_SHOW = 'no_show', 'No Show'

class Appointment(BaseModel):
    """Core appointment model"""
    # Identity Service References
    organizer_id = models.UUIDField(
        help_text="User ID from Identity Service who created the appointment"
    )
    participant_ids = ArrayField(
        models.UUIDField(),
        default=list,
        help_text="List of participant user IDs from Identity Service"
    )
    
    # Local References
    client = models.ForeignKey(
        'business.Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='appointments'
    )
    
    # Scheduling
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField()
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Details
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=500, blank=True)
    meeting_url = models.URLField(blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.SCHEDULED
    )
    
    # Metadata
    notes = models.TextField(blank=True)
    tags = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True
    )
    custom_fields = models.JSONField(default=dict, blank=True)
    
    # Tracking
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['organizer_id', 'status']),
            models.Index(fields=['status', 'start_time']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.start_time}"

class TimeSlot(BaseModel):
    """Available time slots for scheduling"""
    user_id = models.UUIDField(db_index=True)
    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_slots'
    )
    
    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['user_id', 'date', 'start_time']
        indexes = [
            models.Index(fields=['user_id', 'date', 'is_available']),
        ]

class AvailabilityRule(BaseModel):
    """Recurring availability patterns"""
    user_id = models.UUIDField(db_index=True)
    day_of_week = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        help_text="0=Monday, 6=Sunday"
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    effective_from = models.DateField()
    effective_until = models.DateField(null=True, blank=True)
    
    # Breaks and exceptions
    break_start = models.TimeField(null=True, blank=True)
    break_end = models.TimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['day_of_week', 'start_time']
        unique_together = ['user_id', 'day_of_week', 'start_time']

class AppointmentReminder(BaseModel):
    """Appointment reminder tracking"""
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    hours_before = models.IntegerField()
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True)
```

### Phase 3: API Implementation (Priority 1)

```python
# apps/appointments/api.py

from ninja import Router, Schema
from ninja.security import HttpBearer
from typing import List, Optional
from datetime import datetime, date
from pydantic import Field
import uuid

from .models import Appointment, AppointmentStatus, TimeSlot
from .services import AppointmentService
from .clients.identity import IdentityServiceClient

router = Router(tags=["appointments"])

class AuthBearer(HttpBearer):
    async def authenticate(self, request, token):
        identity_client = IdentityServiceClient()
        try:
            user_data = await identity_client.validate_token(token)
            request.user_data = user_data
            return token
        except Exception:
            return None

auth = AuthBearer()

# Schemas
class AppointmentCreateSchema(Schema):
    title: str = Field(..., max_length=200)
    description: Optional[str] = ""
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"
    participant_ids: List[str] = []
    client_id: Optional[int] = None
    location: Optional[str] = ""
    meeting_url: Optional[str] = ""
    notes: Optional[str] = ""
    tags: List[str] = []

class AppointmentResponseSchema(Schema):
    id: uuid.UUID
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    timezone: str
    status: str
    organizer_id: str
    participant_ids: List[str]
    location: str
    meeting_url: str
    created_at: datetime
    updated_at: datetime

class TimeSlotSchema(Schema):
    date: date
    start_time: str
    end_time: str
    is_available: bool

# Endpoints
@router.post("/", response=AppointmentResponseSchema, auth=auth)
async def create_appointment(request, data: AppointmentCreateSchema):
    """Create a new appointment"""
    service = AppointmentService()
    appointment = await service.create_appointment(
        organizer_id=request.user_data['id'],
        **data.dict()
    )
    return appointment

@router.get("/", response=List[AppointmentResponseSchema], auth=auth)
async def list_appointments(
    request,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """List appointments for the current user"""
    service = AppointmentService()
    appointments = await service.list_appointments(
        user_id=request.user_data['id'],
        start_date=start_date,
        end_date=end_date,
        status=status,
        limit=limit,
        offset=offset
    )
    return appointments

@router.get("/{appointment_id}/", response=AppointmentResponseSchema, auth=auth)
async def get_appointment(request, appointment_id: uuid.UUID):
    """Get appointment details"""
    service = AppointmentService()
    appointment = await service.get_appointment(
        appointment_id=appointment_id,
        user_id=request.user_data['id']
    )
    return appointment

@router.patch("/{appointment_id}/", response=AppointmentResponseSchema, auth=auth)
async def update_appointment(
    request,
    appointment_id: uuid.UUID,
    data: AppointmentCreateSchema
):
    """Update appointment"""
    service = AppointmentService()
    appointment = await service.update_appointment(
        appointment_id=appointment_id,
        user_id=request.user_data['id'],
        **data.dict(exclude_unset=True)
    )
    return appointment

@router.post("/{appointment_id}/confirm/", auth=auth)
async def confirm_appointment(request, appointment_id: uuid.UUID):
    """Confirm an appointment"""
    service = AppointmentService()
    await service.confirm_appointment(
        appointment_id=appointment_id,
        user_id=request.user_data['id']
    )
    return {"message": "Appointment confirmed successfully"}

@router.post("/{appointment_id}/cancel/", auth=auth)
async def cancel_appointment(
    request,
    appointment_id: uuid.UUID,
    reason: Optional[str] = ""
):
    """Cancel an appointment"""
    service = AppointmentService()
    await service.cancel_appointment(
        appointment_id=appointment_id,
        user_id=request.user_data['id'],
        reason=reason
    )
    return {"message": "Appointment cancelled successfully"}

@router.get("/availability/", response=List[TimeSlotSchema], auth=auth)
async def get_availability(
    request,
    user_id: str,
    start_date: date,
    end_date: date
):
    """Get available time slots for a user"""
    service = AppointmentService()
    slots = await service.get_availability(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    return slots
```

### Phase 4: Service Layer (Priority 1)

```python
# apps/appointments/services.py

from typing import List, Optional
from datetime import datetime, date, timedelta
import uuid
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Appointment, AppointmentStatus, TimeSlot, AvailabilityRule
from .clients.identity import IdentityServiceClient

class AppointmentService:
    """Business logic for appointment operations"""
    
    def __init__(self):
        self.identity_client = IdentityServiceClient()
    
    @transaction.atomic
    async def create_appointment(
        self,
        organizer_id: str,
        title: str,
        start_time: datetime,
        end_time: datetime,
        **kwargs
    ) -> Appointment:
        """Create a new appointment with validation"""
        
        # Validate time range
        if start_time >= end_time:
            raise ValidationError("End time must be after start time")
        
        if start_time < timezone.now():
            raise ValidationError("Cannot create appointments in the past")
        
        # Check for conflicts
        conflicts = await self._check_conflicts(
            organizer_id,
            start_time,
            end_time,
            kwargs.get('participant_ids', [])
        )
        
        if conflicts:
            raise ValidationError(f"Time slot conflicts with existing appointments")
        
        # Create appointment
        appointment = await Appointment.objects.acreate(
            organizer_id=organizer_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            **kwargs
        )
        
        # Create time slots
        await self._create_time_slots(appointment)
        
        # Schedule reminders
        await self._schedule_reminders(appointment)
        
        return appointment
    
    async def list_appointments(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Appointment]:
        """List appointments for a user"""
        
        queryset = Appointment.objects.filter(
            models.Q(organizer_id=user_id) | 
            models.Q(participant_ids__contains=[user_id])
        )
        
        if start_date:
            queryset = queryset.filter(start_time__date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(start_time__date__lte=end_date)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return await queryset[offset:offset+limit].aall()
    
    async def get_appointment(
        self,
        appointment_id: uuid.UUID,
        user_id: str
    ) -> Appointment:
        """Get appointment details with access control"""
        
        appointment = await Appointment.objects.aget(id=appointment_id)
        
        # Check access
        if not (str(appointment.organizer_id) == user_id or 
                user_id in [str(p) for p in appointment.participant_ids]):
            raise PermissionError("You don't have access to this appointment")
        
        return appointment
    
    async def update_appointment(
        self,
        appointment_id: uuid.UUID,
        user_id: str,
        **updates
    ) -> Appointment:
        """Update appointment with validation"""
        
        appointment = await self.get_appointment(appointment_id, user_id)
        
        # Only organizer can update
        if str(appointment.organizer_id) != user_id:
            raise PermissionError("Only the organizer can update the appointment")
        
        # Update fields
        for field, value in updates.items():
            if hasattr(appointment, field):
                setattr(appointment, field, value)
        
        await appointment.asave()
        return appointment
    
    async def confirm_appointment(
        self,
        appointment_id: uuid.UUID,
        user_id: str
    ):
        """Confirm appointment attendance"""
        
        appointment = await self.get_appointment(appointment_id, user_id)
        
        if appointment.status != AppointmentStatus.SCHEDULED:
            raise ValidationError("Can only confirm scheduled appointments")
        
        appointment.status = AppointmentStatus.CONFIRMED
        appointment.confirmed_at = timezone.now()
        await appointment.asave()
    
    async def cancel_appointment(
        self,
        appointment_id: uuid.UUID,
        user_id: str,
        reason: str = ""
    ):
        """Cancel an appointment"""
        
        appointment = await self.get_appointment(appointment_id, user_id)
        
        if appointment.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
            raise ValidationError("Cannot cancel completed or already cancelled appointments")
        
        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_at = timezone.now()
        appointment.cancellation_reason = reason
        await appointment.asave()
        
        # Free up time slots
        await TimeSlot.objects.filter(appointment=appointment).aupdate(
            is_available=True,
            appointment=None
        )
    
    async def get_availability(
        self,
        user_id: str,
        start_date: date,
        end_date: date
    ) -> List[TimeSlot]:
        """Get available time slots for a user"""
        
        # Generate slots from availability rules
        await self._generate_time_slots(user_id, start_date, end_date)
        
        # Get available slots
        slots = await TimeSlot.objects.filter(
            user_id=user_id,
            date__gte=start_date,
            date__lte=end_date,
            is_available=True
        ).aall()
        
        return slots
    
    async def _check_conflicts(
        self,
        organizer_id: str,
        start_time: datetime,
        end_time: datetime,
        participant_ids: List[str]
    ) -> bool:
        """Check for scheduling conflicts"""
        
        all_user_ids = [organizer_id] + participant_ids
        
        conflicts = await Appointment.objects.filter(
            models.Q(organizer_id__in=all_user_ids) |
            models.Q(participant_ids__overlap=all_user_ids),
            status__in=[AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED],
            start_time__lt=end_time,
            end_time__gt=start_time
        ).aexists()
        
        return conflicts
    
    async def _create_time_slots(self, appointment: Appointment):
        """Create time slots for the appointment"""
        
        slots_to_create = []
        
        # Create slots for organizer
        slots_to_create.append(
            TimeSlot(
                user_id=appointment.organizer_id,
                date=appointment.start_time.date(),
                start_time=appointment.start_time.time(),
                end_time=appointment.end_time.time(),
                is_available=False,
                appointment=appointment
            )
        )
        
        # Create slots for participants
        for participant_id in appointment.participant_ids:
            slots_to_create.append(
                TimeSlot(
                    user_id=participant_id,
                    date=appointment.start_time.date(),
                    start_time=appointment.start_time.time(),
                    end_time=appointment.end_time.time(),
                    is_available=False,
                    appointment=appointment
                )
            )
        
        await TimeSlot.objects.abulk_create(slots_to_create, ignore_conflicts=True)
    
    async def _schedule_reminders(self, appointment: Appointment):
        """Schedule appointment reminders"""
        # This will be implemented with Celery in Phase 5
        pass
    
    async def _generate_time_slots(
        self,
        user_id: str,
        start_date: date,
        end_date: date
    ):
        """Generate time slots from availability rules"""
        
        rules = await AvailabilityRule.objects.filter(
            user_id=user_id,
            is_active=True,
            effective_from__lte=end_date
        ).aall()
        
        slots_to_create = []
        current_date = start_date
        
        while current_date <= end_date:
            day_of_week = current_date.weekday()
            
            for rule in rules:
                if rule.day_of_week == day_of_week:
                    # Check if rule is effective for this date
                    if rule.effective_until and current_date > rule.effective_until:
                        continue
                    
                    # Create slot for this rule
                    slots_to_create.append(
                        TimeSlot(
                            user_id=user_id,
                            date=current_date,
                            start_time=rule.start_time,
                            end_time=rule.end_time,
                            is_available=True
                        )
                    )
            
            current_date += timedelta(days=1)
        
        # Bulk create slots (ignore conflicts for existing slots)
        if slots_to_create:
            await TimeSlot.objects.abulk_create(
                slots_to_create,
                ignore_conflicts=True
            )
```

### Phase 5: Background Tasks (Priority 2)

```python
# apps/appointments/tasks.py

from celery import shared_task
from datetime import datetime, timedelta
from django.utils import timezone

from .models import Appointment, AppointmentReminder, AppointmentStatus

@shared_task
def send_appointment_reminders():
    """Send reminders for upcoming appointments"""
    
    # Get appointments that need reminders
    now = timezone.now()
    reminder_windows = [
        (24, now + timedelta(hours=24)),
        (2, now + timedelta(hours=2)),
    ]
    
    for hours_before, reminder_time in reminder_windows:
        appointments = Appointment.objects.filter(
            status__in=[AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED],
            start_time__gte=reminder_time,
            start_time__lt=reminder_time + timedelta(minutes=30),
            reminders__hours_before=hours_before,
            reminders__status='pending'
        ).select_related('reminders')
        
        for appointment in appointments:
            send_reminder.delay(appointment.id, hours_before)

@shared_task
def send_reminder(appointment_id, hours_before):
    """Send a single appointment reminder"""
    
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        reminder = appointment.reminders.get(hours_before=hours_before)
        
        # TODO: Integrate with Communication Service when available
        # For now, just log
        print(f"Sending reminder for appointment {appointment.title} to users")
        
        reminder.status = 'sent'
        reminder.sent_at = timezone.now()
        reminder.save()
        
    except Exception as e:
        reminder.status = 'failed'
        reminder.error_message = str(e)
        reminder.save()

@shared_task
def cleanup_old_appointments():
    """Archive old completed appointments"""
    
    cutoff_date = timezone.now() - timedelta(days=90)
    
    old_appointments = Appointment.objects.filter(
        status=AppointmentStatus.COMPLETED,
        end_time__lt=cutoff_date
    )
    
    # Archive to separate storage or mark as archived
    for appointment in old_appointments:
        appointment.custom_fields['archived'] = True
        appointment.save()
```

## Testing Requirements

### Unit Tests
```python
# apps/appointments/tests/test_models.py

from django.test import TestCase
from datetime import datetime, timedelta
from django.utils import timezone

from ..models import Appointment, AppointmentStatus

class AppointmentModelTest(TestCase):
    def test_appointment_creation(self):
        appointment = Appointment.objects.create(
            organizer_id='123e4567-e89b-12d3-a456-426614174000',
            title='Test Meeting',
            start_time=timezone.now() + timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=2),
            status=AppointmentStatus.SCHEDULED
        )
        self.assertEqual(appointment.status, AppointmentStatus.SCHEDULED)
        self.assertEqual(appointment.title, 'Test Meeting')
```

### API Tests
```python
# apps/appointments/tests/test_api.py

from django.test import TestCase
from ninja.testing import TestClient
from unittest.mock import patch, MagicMock

from ..api import router

class AppointmentAPITest(TestCase):
    def setUp(self):
        self.client = TestClient(router)
    
    @patch('apps.appointments.api.IdentityServiceClient')
    def test_create_appointment(self, mock_identity):
        mock_identity.return_value.validate_token.return_value = {
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'email': 'test@example.com'
        }
        
        response = self.client.post(
            '/appointments/',
            json={
                'title': 'Test Meeting',
                'start_time': '2025-01-15T10:00:00Z',
                'end_time': '2025-01-15T11:00:00Z',
            },
            headers={'Authorization': 'Bearer test-token'}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], 'Test Meeting')
```

## Integration with Frontend

The Frontend Agent should use these API endpoints:

```typescript
// frontend/src/api/appointments.ts

interface Appointment {
  id: string;
  title: string;
  description: string;
  startTime: string;
  endTime: string;
  status: string;
  organizerId: string;
  participantIds: string[];
}

class AppointmentAPI {
  private baseURL = 'http://localhost:8000/api';
  
  async createAppointment(data: Partial<Appointment>): Promise<Appointment> {
    const response = await fetch(`${this.baseURL}/appointments/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`,
      },
      body: JSON.stringify(data),
    });
    return response.json();
  }
  
  async listAppointments(params?: {
    startDate?: string;
    endDate?: string;
    status?: string;
  }): Promise<Appointment[]> {
    const queryString = new URLSearchParams(params).toString();
    const response = await fetch(
      `${this.baseURL}/appointments/?${queryString}`,
      {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
        },
      }
    );
    return response.json();
  }
  
  async getAvailability(
    userId: string,
    startDate: string,
    endDate: string
  ): Promise<TimeSlot[]> {
    const response = await fetch(
      `${this.baseURL}/appointments/availability/?user_id=${userId}&start_date=${startDate}&end_date=${endDate}`,
      {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
        },
      }
    );
    return response.json();
  }
}
```

## Migration Strategy (Future)

If the appointment system needs to be extracted into a microservice in the future:

1. **Database Migration**
   - Export appointment-related tables to new database
   - Implement dual-write during transition period
   - Verify data consistency

2. **API Migration**
   - Create facade in Django backend that proxies to new service
   - Gradually migrate frontend to call new service directly
   - Maintain backward compatibility during transition

3. **Code Migration**
   - Move models, services, and API code to new FastAPI service
   - Update import statements and dependencies
   - Migrate background tasks to new service

## Performance Considerations

1. **Database Indexing**
   - Ensure proper indexes on frequently queried fields
   - Monitor query performance with Django Debug Toolbar
   - Use database query optimization techniques

2. **Caching Strategy**
   ```python
   from django.core.cache import cache
   
   def get_user_availability_cached(user_id, date):
       cache_key = f"availability:{user_id}:{date}"
       result = cache.get(cache_key)
       if result is None:
           result = calculate_availability(user_id, date)
           cache.set(cache_key, result, timeout=300)  # 5 minutes
       return result
   ```

3. **Async Processing**
   - Use Celery for background tasks
   - Implement async views where beneficial
   - Consider using Django Channels for real-time updates

## Security Considerations

1. **Authentication**: All endpoints require valid JWT from Identity Service
2. **Authorization**: Users can only access their own appointments
3. **Data Validation**: Strict input validation on all endpoints
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Audit Logging**: Log all appointment modifications

## Next Steps for Backend Agent

1. **Immediate Actions**:
   - Create the appointments app structure
   - Implement the data models
   - Run migrations
   - Create basic CRUD APIs

2. **Testing**:
   - Write comprehensive unit tests
   - Create API integration tests
   - Test Identity Service integration

3. **Documentation**:
   - Update API documentation
   - Create usage examples
   - Document any deviations from this guide

4. **Coordination**:
   - Notify Frontend Agent when APIs are ready
   - Coordinate with Infrastructure Agent for deployment
   - Prepare for Communication Service integration

Remember: Keep the implementation modular and well-documented to facilitate potential future extraction into a microservice.