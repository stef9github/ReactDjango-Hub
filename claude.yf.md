# CLAUDE.md - Development Guide

## Key Commands
```bash
# Run Django development server
cd mental_health_crm
python manage.py runserver

# Run tests
python manage.py test
python manage.py test patients.tests  # Run specific app tests
python manage.py test mental_health_crm.tests  # Run specific app tests
python manage.py test mental_health_crm.tests.test_appointment_creation  # Run specific test file

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create users/groups
python manage.py create_groups_and_users

# Celery task processing
celery -A mental_health_crm worker -l INFO

# Restart Celery workers (after transcription method changes)
python manage.py restart_celery                    # Using Django management command
sudo systemctl restart celery.service             # Direct systemd restart  
celery -A mental_health_crm control shutdown      # Graceful shutdown (systemd auto-restarts)

# Tailwind CSS
python manage.py tailwind start

# Requirements Management
python scripts/sync_requirements.py  # Sync production requirements with main requirements
python scripts/sync_requirements.py --check-only  # Check if requirements are in sync
python scripts/install_git_hooks.py  # Install git hooks to prevent sync issues

# API Testing
python test_appointments_api.py    # Test appointments API functionality
python test_patients_api.py        # Test patients API functionality
```

## Requirements Management

The project uses two requirements files:
- `requirements.txt` - Main requirements file (used for development)
- `scripts/requirements_ubuntu_prod.txt` - Production requirements file (used for deployment)

## Database Setup

The project uses separate databases:
- `db.sqlite3` - Main application database
- `sessions.sqlite3` - Dedicated sessions database (to prevent database locks)

### Sessions Database Setup
When deploying to new environments or after database changes:

```bash
# Check if sessions database is properly set up
python manage.py setup_sessions_db --check-only

# Set up sessions database (creates tables if needed)
python manage.py setup_sessions_db

# Alternative: Run sessions migrations directly
python manage.py migrate --database=sessions sessions
```

**Note:** The deployment script (`deploy_requirements.py`) now automatically sets up the sessions database during deployment.

### Preventing Requirements Sync Issues

To prevent deployment issues where packages are missing from production:

1. **Install Git Hooks** (one-time setup):
   ```bash
   python scripts/install_git_hooks.py
   ```
   This installs a pre-commit hook that blocks commits when requirements files are out of sync.

2. **Manual Sync Check**:
   ```bash
   python scripts/sync_requirements.py --check-only
   ```

3. **Automatic Sync**:
   ```bash
   python scripts/sync_requirements.py
   ```

4. **Deployment Protection**: The deployment script automatically checks and syncs requirements before deploying.

### Adding New Packages

When adding new packages:
1. Add to `requirements.txt` 
2. Run `python scripts/sync_requirements.py` to update production requirements
3. Or just commit - the git hook will remind you if needed

## Testing

### Test Case Reference
The main test file for appointment creation and scheduling functionality is:
- `/mental_health_crm/mental_health_crm/tests/test_appointment_creation.py`

Other important test files:
- `/mental_health_crm/mental_health_crm/tests/test_working_hours.py`
- `/mental_health_crm/mental_health_crm/tests/test_urls.py`
- `/mental_health_crm/mental_health_crm/tests/test_appointment_urls.py`
- `/mental_health_crm/patients/tests/test_patients_urls.py`

### Test Case Creation
When creating test cases:
1. Ensure proper imports (TestCase, reverse, necessary models)
2. Use setUp method to create necessary test data
3. Use UUID fields for users to match production environment
4. Group tests by functionality (URL tests, model tests, etc.)
5. Use descriptive method names like `test_appointment_creation` or `test_appointment_listing`

### Creating Test Models
```python
# Create a customer admin user
self.admin_user = User.objects.create(
    email='test.admin@example.com',
    first_name='Test',
    last_name='Admin',
    is_active=True,
    user_type='customer_admin',
    id=uuid.uuid4(),
    phone_number='555-789-1234',
    street_address='789 Admin Ave',
    city='Adminville',
    state='TX',
    postal_code='75001'
)

# Create a CustomerAdminProfile
from patients.models import CustomerAdminProfile, Customer
self.admin_profile = CustomerAdminProfile.objects.create(
    user=self.admin_user,
    title='Clinic Director'
)

# Create a Customer
self.customer = Customer.objects.create(
    name='Test Mental Health Clinic',
    description='A test clinic for mental health services',
    contact_email='contact@testclinic.com',
    phone_number='555-789-5678',
    website='https://testclinic.com',
    admin_user=self.admin_user,  # Administrator user reference
    street_address='789 Clinic Blvd',
    city='Clinicville',
    state='TX',
    postal_code='75001'
)

# Create a provider user
self.provider = User.objects.create(
    email='test.provider@example.com',
    first_name='Test',
    last_name='Provider',
    is_active=True,
    user_type='provider',
    id=uuid.uuid4(),
    phone_number='555-123-4567',
    street_address='123 Provider St',
    city='Providertown',
    state='CA',
    postal_code='90210'
)
self.provider.set_password('testpassword123')
self.provider.save()

# Create provider profile with customer association
self.provider_profile = ProviderProfile.objects.create(
    user=self.provider,
    customer=self.customer
)

# Create a patient user
self.patient = User.objects.create(
    email='test.patient@example.com',
    first_name='Test',
    last_name='Patient',
    is_active=True,
    user_type='patient',
    id=uuid.uuid4(),
    phone_number='555-987-6543',
    street_address='456 Patient Ave',
    city='Patientville',
    state='NY',
    postal_code='10001'
)

# Create patient profile
self.patient_profile = PatientProfile.objects.create(
    user=self.patient,
    provider=self.provider,
    date_of_birth=timezone.now().date() - timedelta(days=365*30)  # 30 years old
)
```

### Testing Appointments with AJAX Endpoints
```python
# SETUP: Get models and create StaffMember & Service
Appointment = apps.get_model('appointment', 'Appointment')
AppointmentRequest = apps.get_model('appointment', 'AppointmentRequest')
StaffMember = apps.get_model('appointment', 'StaffMember') 
Service = apps.get_model('appointment', 'Service')

staff_member, created = StaffMember.objects.get_or_create(user=self.provider)
service, created = Service.objects.get_or_create(
    name="Test Service",
    defaults={
        'duration': timedelta(minutes=60),
        'price': 100.00,
        'background_color': "#FF5733",
        'description': "Test service description"
    }
)
staff_member.services_offered.add(service)

# Track AJAX calls with a counter
ajax_calls = {
    'fetch_service_list': 0,
    'get_non_working_days': 0,
    'get_available_slots': 0,
    'get_next_available_date': 0
}

# STEP 1: Fetch services for provider using AJAX
from django.test import RequestFactory
from mental_health_crm.ajax_views import fetch_service_list_for_staff_ajax

factory = RequestFactory()
request = factory.get(f'/appointments/ajax/services_for_staff/?staff_id={provider_id}')
request.user = self.provider  # Simulate authenticated user

services_response = fetch_service_list_for_staff_ajax(request)
ajax_calls['fetch_service_list'] += 1
services_data = json.loads(services_response.content)

# STEP 2: Check for non-working days using AJAX
from mental_health_crm.ajax_views import get_non_working_days_ajax

request = factory.get(
    f'/appointments/ajax/non_working_days/?staff_id={staff_id}&month={month}&year={year}'
)
request.user = self.provider

non_working_days_response = get_non_working_days_ajax(request)
ajax_calls['get_non_working_days'] += 1
non_working_days_data = json.loads(non_working_days_response.content)

# STEP 3: Get available time slots using AJAX
from mental_health_crm.ajax_views import get_available_slots_ajax

date_str = tomorrow.strftime('%Y-%m-%d')
request = factory.get(
    f'/appointments/ajax/available_slots/?date={date_str}&staff_id={staff_id}&service_id={service_id}'
)
request.user = self.provider

slots_response = get_available_slots_ajax(request)
ajax_calls['get_available_slots'] += 1
slots_data = json.loads(slots_response.content)

# Choose a slot and parse it
chosen_slot = slots_data['available_slots'][0]['value']  # e.g. "09:00"
slot_hour, slot_minute = map(int, chosen_slot.split(':'))
start_time = time(slot_hour, slot_minute)

# Calculate end time based on service duration
end_hour, end_minute = slot_hour, slot_minute
end_minute += 60  # 60-minute appointment
if end_minute >= 60:
    end_hour += end_minute // 60
    end_minute = end_minute % 60
end_time = time(end_hour, end_minute)

# Create appointment with the chosen slot
appointment_request = AppointmentRequest.objects.create(
    date=tomorrow,
    start_time=start_time,
    end_time=end_time,
    service=service,
    staff_member=staff_member
)

appointment = Appointment.objects.create(
    client=self.patient,
    appointment_request=appointment_request,
    want_reminder=True,
    additional_info="Test appointment notes"
)

# Verify all AJAX endpoints were called
self.assertEqual(ajax_calls['fetch_service_list'], 1, "fetch_service_list_for_staff_ajax was not called")
self.assertEqual(ajax_calls['get_non_working_days'], 1, "get_non_working_days_ajax was not called")
self.assertEqual(ajax_calls['get_available_slots'], 1, "get_available_slots_ajax was not called")
```

### Setting Up Working Hours for Tests
```python
# In setUp method, set up working hours for the provider
StaffMember = apps.get_model('appointment', 'StaffMember')
WorkingHours = apps.get_model('appointment', 'WorkingHours')

staff_member, created = StaffMember.objects.get_or_create(user=self.provider)

# Add working hours for all days of the week (0=Monday, 6=Sunday)
from datetime import time
for day in range(7):  # Every day of the week
    WorkingHours.objects.create(
        staff_member=staff_member,
        day_of_week=day,
        start_time=time(9, 0),  # 9 AM
        end_time=time(17, 0)    # 5 PM
    )
```

### Testing Custom Working Hours for Specific Days
```python
# Get Wednesday's working hours (day_of_week=2, 0=Monday)
wednesday_working_hours = WorkingHours.objects.get(staff_member=staff_member, day_of_week=2)

# Change Wednesday's working hours to be 12:00 - 14:00 only (shorter day)
from datetime import time
wednesday_working_hours.start_time = time(12, 0)  # 12:00 PM
wednesday_working_hours.end_time = time(14, 0)    # 2:00 PM
wednesday_working_hours.save()

# Find the next Wednesday
import datetime
today = datetime.date.today()
days_until_wednesday = (2 - today.weekday()) % 7  # 2 = Wednesday
next_wednesday = today + datetime.timedelta(days=days_until_wednesday)

# Get available slots for Wednesday
date_str = next_wednesday.strftime('%Y-%m-%d')
request = factory.get(
    f'/appointments/ajax/available_slots/?date={date_str}&staff_id={staff_member.id}&service_id={service.id}'
)
request.user = self.provider

slots_response = get_available_slots_ajax(request)
slots_data = json.loads(slots_response.content)

# Verify the slots are only within the custom hours (12-2 PM)
for slot in slots_data['available_slots']:
    slot_hour = int(slot['value'].split(':')[0])
    self.assertTrue(12 <= slot_hour < 14)
```

## Customer Administration Model

The system supports two types of administrators for customers:
1. Customer Admin users (user_type='customer_admin')
2. Provider users (user_type='provider')

When working with customer administration, always:
- Use the `admin_user` field on the Customer model
- Use helper methods like `customer.get_admin_user()`, `customer.get_admin_email()`, etc.
- Use `is_customer_admin(user, customer)` utility function for permission checks

The legacy `admin` field has been completely removed, and all code now uses the `admin_user` field exclusively.

For more details, see `/Users/stephanerichard/Documents/CODING/yf/mental_health_crm/ADMIN_TRANSITION.md`

## Testing Customer Administration
```python
# Test with a Provider as admin:
provider_admin = User.objects.create(
    email='admin.provider@example.com',
    first_name='Admin',
    last_name='Provider',
    is_active=True,
    user_type='provider',
    id=uuid.uuid4()
    # ... other required fields
)

# Create provider profile
provider_profile = ProviderProfile.objects.create(
    user=provider_admin,
    # ... other fields
)

# Create customer with provider as admin
customer = Customer.objects.create(
    name='Provider Administered Clinic',
    admin_user=provider_admin,  # Set provider as admin
    # ... other required fields
)

# To check if a user is the admin for a customer:
from staff.views import is_customer_admin
is_admin = is_customer_admin(user, customer)
```

## Code Style Guidelines
- Follow PEP 8 naming conventions (snake_case for variables/functions, CamelCase for classes)
- Group imports: stdlib, third-party, Django, local apps
- Use Django's model conventions and class-based views
- Templates belong in app-specific template directories
- Use descriptive docstrings for functions and classes
- Handle errors with try/except and appropriate logging
- Follow Django URL naming conventions and use reverse()

## Form Styling Best Practices

### Form Field Styling with Tailwind
For form fields, use the `addclass` filter to apply Tailwind classes:

```html
{{ form.field_name|addclass:"w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-400" }}
```

### Select/Dropdown Fields
For select/dropdown fields, avoid custom arrow implementations which can cause double arrows. Instead:

```html
<!-- Simple approach - works best -->
{{ form.dropdown_field|addclass:"w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-400" }}

<!-- AVOID: Custom arrow implementations like this which cause double arrows -->
<div class="relative">
    {{ form.dropdown_field|addclass:"appearance-none..." }}
    <div class="absolute inset-y-0 right-0 pointer-events-none...">
        <!-- Custom SVG arrow -->
    </div>
</div>
```

The simple approach lets the browser handle the select styling, which is better for accessibility and cross-browser compatibility.

## Transcription Method Management

The system supports switching between different transcription methods:
- **Standard**: Basic transcription without speaker identification
- **Diarized**: Advanced transcription with speaker identification (Therapist: / Patient:)

### Changing Transcription Methods

**Via Web UI:**
1. Navigate to Staff Dashboard → Transcription Settings
2. Select the desired method
3. System automatically attempts to restart Celery workers
4. If automatic restart fails, use manual restart commands below

**Manual Restart Commands:**
```bash
# Recommended: Django management command (tries multiple methods)
python manage.py restart_celery

# Direct systemd restart (requires sudo permissions)
sudo systemctl restart celery.service

# Graceful shutdown (systemd auto-restarts due to Restart=always)
celery -A mental_health_crm control shutdown

# Check status
sudo systemctl status celery.service
```

**Via Command Line Script:**
```bash
# Switch to diarized method and restart workers
cd mental_health_crm/patients/tasks
python switch_transcription.py diarized

# Switch to standard method
python switch_transcription.py standard

# Check current method
python switch_transcription.py --current
```

### Important Notes:
- Method changes update the database and modify `patients/tasks/__init__.py`
- Celery workers must be restarted for changes to take full effect
- The system attempts automatic restart when methods are changed via UI
- Both transcription modules load on startup but only the active one logs initialization

## Documentation Policy
- Always add important information to CLAUDE.md
- Document common commands, test patterns, and code conventions
- Include examples of proper model creation and relationship setup
- Document AJAX endpoints, their parameters and expected responses
- Add test patterns that should be reused across the codebase
- Update this file whenever new important patterns or workflows are discovered

## Version Management

The project follows a semantic versioning system with automated versioning for deployments. Please refer to the [VERSION_MANAGEMENT.md](docs/maintenance/VERSION_MANAGEMENT.md) file for detailed documentation on:

- Semantic versioning structure (X.Y.Z build N)
- Automated version updates for beta and production deployments
- Commands for deploying and managing versions
- Local version synchronization with servers
- Best practices for version management

## URL and Web Page Testing

### Testing URL Routes Command
To run URL tests, use the following command:
```bash
# Test all URL routes in the appointment_urls test file
python manage.py test mental_health_crm.tests.test_appointment_urls

# Test a specific URL test method
python manage.py test mental_health_crm.tests.test_appointment_urls.AppointmentURLsTest.test_web_page_access
```

### URL Test Files
The main URL test file is:
- `mental_health_crm/mental_health_crm/tests/test_appointment_urls.py`

This test file includes multiple test methods:
- `test_appointment_namespace_urls`: Tests URLs in the appointment namespace
- `test_custom_appointment_view_urls`: Tests custom appointment view URLs
- `test_staff_specific_urls`: Tests staff-specific URL patterns
- `test_web_page_access`: Tests actual HTTP access to URL endpoints
- `test_ajax_endpoints`: Tests AJAX endpoints with parameters
- `test_crm_integration_urls`: Tests CRM integration URLs
- `test_appointment_dashboard_url`: Tests the custom dashboard URL

### Best Practices for URL Testing
1. Test both direct URL patterns and URL names via `reverse()`
2. For AJAX endpoints, test with required parameters
3. Check for appropriate status codes (200, 302, 401, 403, 400)
4. For authenticated endpoints, test both unauthenticated and authenticated access
5. For permission-based views, test with different user roles
6. Use logging to capture actual response status codes for debugging

## Project Task Management

### TODO.md
The project includes a `TODO.md` file for tracking improvements and future enhancements:
- **Location**: `/mental_health_crm/TODO.md`
- **Purpose**: Document pending improvements, API enhancements, and feature requests
- **Usage**: Add new tasks as they are identified during development
- **Current items**: Appointments API improvements for session type indicators (virtual vs in-person)

When identifying improvements during development, add them to TODO.md for future implementation.

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

      
      IMPORTANT: this context may or may not be relevant to your tasks. You should not respond to this context unless it is highly relevant to your task.
- beta is ssh -i ~/.ssh/yf-aws.pem ubuntu@ec2-3-226-175-20.compute-1.amazonaws.com
- prod is ssh -i ~/.ssh/yf-aws.pem ubuntu@ec2-34-238-181-64.compute-1.amazonaws.com