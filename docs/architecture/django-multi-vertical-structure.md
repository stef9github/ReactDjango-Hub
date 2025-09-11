# Django Multi-Vertical Structure
## Supporting Multiple Industry Verticals in a Single Django Project

**Version**: 1.0  
**Date**: January 2025  
**Status**: Active  
**Purpose**: Define Django project structure and patterns for multi-vertical SaaS platform

---

## Overview

This document outlines how the Django backend is structured to support multiple industry verticals (Medical Hub, Public Hub, and future verticals) within a single Django project. It covers the organization of apps, models, settings management, database schema design, and code patterns that enable clean separation while maximizing code reuse.

---

## Project Structure

### Directory Organization

```
backend/
├── config/                      # Django configuration
│   ├── settings/
│   │   ├── base.py             # Base settings for all environments
│   │   ├── development.py      # Development settings
│   │   ├── production.py       # Production settings
│   │   ├── testing.py          # Test settings
│   │   └── verticals/          # Vertical-specific settings
│   │       ├── medical.py      # Medical Hub settings
│   │       └── public.py       # Public Hub settings
│   ├── urls.py                 # Main URL configuration
│   ├── wsgi.py                 # WSGI configuration
│   └── asgi.py                 # ASGI configuration
│
├── apps/                        # Django applications
│   ├── core/                   # Shared core functionality
│   │   ├── auth/              # Authentication integration
│   │   ├── base/              # Base models and mixins
│   │   ├── api/               # Common API utilities
│   │   ├── notifications/     # Notification integration
│   │   ├── documents/         # Document management
│   │   ├── workflow/          # Workflow integration
│   │   ├── cache/             # Caching utilities
│   │   ├── utils/             # Shared utilities
│   │   └── middleware/        # Custom middleware
│   │
│   ├── medical/                # Medical vertical apps
│   │   ├── __init__.py
│   │   ├── patients/          # Patient management
│   │   ├── surgery/           # Surgery planning
│   │   ├── clinical/          # Clinical documentation
│   │   ├── appointments/      # Appointment scheduling
│   │   ├── billing/           # Medical billing
│   │   └── integrations/      # Medical-specific integrations
│   │
│   ├── public/                 # Public procurement vertical
│   │   ├── __init__.py
│   │   ├── tenders/           # Tender management
│   │   ├── suppliers/         # Supplier registry
│   │   ├── contracts/         # Contract management
│   │   ├── compliance/        # Compliance tracking
│   │   ├── procurement/       # Procurement workflows
│   │   └── integrations/      # Public-specific integrations
│   │
│   └── analytics/              # Shared analytics (all verticals)
│       ├── models.py
│       ├── views.py
│       └── services.py
│
├── migrations/                  # Database migrations
├── static/                     # Static files
├── media/                      # User-uploaded files
├── templates/                  # Django templates
├── tests/                      # Test files
├── scripts/                    # Management scripts
└── requirements/               # Requirements files
    ├── base.txt               # Base requirements
    ├── medical.txt            # Medical-specific requirements
    └── public.txt             # Public-specific requirements
```

---

## Core Django Apps (Shared)

### 1. Base Models and Mixins

#### Abstract Base Models
```python
# apps/core/base/models.py
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class UUIDModel(models.Model):
    """Base model with UUID primary key"""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Adds created and modified timestamps"""
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


class OrganizationScopedModel(models.Model):
    """Multi-tenant model scoped to organization"""
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set'
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['organization', '-created_at']),
        ]


class VerticalScopedModel(models.Model):
    """Model that tracks which vertical it belongs to"""
    VERTICAL_CHOICES = [
        ('medical', 'Medical Hub'),
        ('public', 'Public Hub'),
    ]
    
    vertical = models.CharField(
        max_length=20,
        choices=VERTICAL_CHOICES,
        db_index=True
    )
    
    class Meta:
        abstract = True


class BaseEntity(UUIDModel, TimeStampedModel, OrganizationScopedModel):
    """Combined base model for most entities"""
    
    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """Soft delete functionality"""
    is_deleted = models.BooleanField(
        default=False,
        db_index=True
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_deleted'
    )
    
    class Meta:
        abstract = True
    
    def soft_delete(self, user=None):
        """Soft delete the object"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
    
    def restore(self):
        """Restore soft deleted object"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class AuditModel(models.Model):
    """Comprehensive audit trail"""
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_created'
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_modified'
    )
    version = models.IntegerField(
        default=1,
        help_text="Version number for optimistic locking"
    )
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """Auto-increment version on save"""
        if self.pk:
            self.version += 1
        super().save(*args, **kwargs)
```

#### Shared Mixins
```python
# apps/core/base/mixins.py
from django.db import models
from django.core.exceptions import ValidationError

class StatusMixin(models.Model):
    """Adds status field with transitions"""
    
    STATUS_CHOICES = []  # Override in subclass
    STATUS_TRANSITIONS = {}  # Override in subclass
    
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        db_index=True
    )
    status_changed_at = models.DateTimeField(
        auto_now_add=True
    )
    status_history = models.JSONField(
        default=list,
        blank=True
    )
    
    class Meta:
        abstract = True
    
    def can_transition_to(self, new_status):
        """Check if status transition is allowed"""
        allowed = self.STATUS_TRANSITIONS.get(self.status, [])
        return new_status in allowed
    
    def transition_to(self, new_status, user=None, notes=None):
        """Transition to new status with validation"""
        if not self.can_transition_to(new_status):
            raise ValidationError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        
        # Record history
        self.status_history.append({
            'from': self.status,
            'to': new_status,
            'timestamp': timezone.now().isoformat(),
            'user': str(user.id) if user else None,
            'notes': notes
        })
        
        self.status = new_status
        self.status_changed_at = timezone.now()
        self.save()


class TaggableMixin(models.Model):
    """Adds tagging functionality"""
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="List of tags"
    )
    
    class Meta:
        abstract = True
    
    def add_tag(self, tag):
        """Add a tag if not present"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.save(update_fields=['tags'])
    
    def remove_tag(self, tag):
        """Remove a tag if present"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.save(update_fields=['tags'])


class MetadataMixin(models.Model):
    """Adds flexible metadata storage"""
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata"
    )
    
    class Meta:
        abstract = True
    
    def get_metadata(self, key, default=None):
        """Get metadata value"""
        return self.metadata.get(key, default)
    
    def set_metadata(self, key, value):
        """Set metadata value"""
        self.metadata[key] = value
        self.save(update_fields=['metadata'])
```

---

### 2. Core Organization Model

```python
# apps/core/models.py
from django.db import models
from .base.models import UUIDModel, TimeStampedModel

class Organization(UUIDModel, TimeStampedModel):
    """Base organization model for all verticals"""
    
    # Basic Information
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=100)
    
    # Vertical Configuration
    vertical = models.CharField(
        max_length=20,
        choices=[
            ('medical', 'Medical Hub'),
            ('public', 'Public Hub'),
        ],
        db_index=True
    )
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    
    # Address
    address = models.JSONField(
        default=dict,
        help_text="Structured address data"
    )
    
    # Settings
    settings = models.JSONField(
        default=dict,
        help_text="Organization-specific settings"
    )
    
    # Features
    enabled_features = models.JSONField(
        default=list,
        help_text="List of enabled features"
    )
    
    # Subscription
    subscription_tier = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free'),
            ('starter', 'Starter'),
            ('professional', 'Professional'),
            ('enterprise', 'Enterprise'),
        ],
        default='free'
    )
    subscription_expires = models.DateField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'organizations'
        indexes = [
            models.Index(fields=['vertical', 'is_active']),
        ]
    
    def get_vertical_config(self):
        """Get vertical-specific configuration"""
        from django.conf import settings
        vertical_configs = settings.VERTICAL_CONFIGS
        return vertical_configs.get(self.vertical, {})
    
    def has_feature(self, feature_name):
        """Check if organization has a feature enabled"""
        return feature_name in self.enabled_features
```

---

## Vertical-Specific Django Apps

### Medical Vertical Extension Pattern

```python
# apps/medical/patients/models.py
from apps.core.base import BaseEntity, SoftDeleteModel, AuditModel

class MedicalOrganization(models.Model):
    """Medical-specific organization extension"""
    organization = models.OneToOneField(
        'core.Organization',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='medical_profile'
    )
    
    # Medical-specific fields
    facility_type = models.CharField(
        max_length=50,
        choices=[
            ('hospital', 'Hospital'),
            ('clinic', 'Clinic'),
            ('surgical_center', 'Surgical Center'),
            ('private_practice', 'Private Practice'),
        ]
    )
    
    accreditation_number = models.CharField(
        max_length=100,
        blank=True
    )
    
    medical_specialties = models.JSONField(
        default=list,
        help_text="List of medical specialties"
    )
    
    # Compliance
    hipaa_compliant = models.BooleanField(default=False)
    last_compliance_audit = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'med_organizations'


class MedicalPatient(BaseEntity, SoftDeleteModel, AuditModel):
    """Patient model for medical vertical"""
    
    # Ensure only medical organizations can create patients
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='medical_patients',
        limit_choices_to={'vertical': 'medical'}
    )
    
    # Patient fields...
    medical_record_number = models.CharField(
        max_length=50,
        unique=True
    )
    
    class Meta:
        db_table = 'med_patients'
        
    def clean(self):
        """Validate organization is medical vertical"""
        if self.organization.vertical != 'medical':
            raise ValidationError(
                "Patients can only be created for medical organizations"
            )
```

### Public Vertical Extension Pattern

```python
# apps/public/organizations/models.py
from apps.core.base import BaseEntity

class PublicOrganization(models.Model):
    """Public sector organization extension"""
    organization = models.OneToOneField(
        'core.Organization',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='public_profile'
    )
    
    # Public sector specific
    entity_type = models.CharField(
        max_length=50,
        choices=[
            ('ministry', 'Government Ministry'),
            ('agency', 'Government Agency'),
            ('municipality', 'Municipality'),
            ('public_corp', 'Public Corporation'),
            ('university', 'University'),
        ]
    )
    
    government_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Government entity identifier"
    )
    
    procurement_authority = models.BooleanField(
        default=True,
        help_text="Authorized to conduct public procurement"
    )
    
    budget_code = models.CharField(
        max_length=50,
        blank=True
    )
    
    class Meta:
        db_table = 'pub_organizations'


class PublicTender(BaseEntity, AuditModel):
    """Tender model for public vertical"""
    
    # Ensure only public organizations can create tenders
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='public_tenders',
        limit_choices_to={'vertical': 'public'}
    )
    
    # Tender fields...
    tender_number = models.CharField(
        max_length=50,
        unique=True
    )
    
    class Meta:
        db_table = 'pub_tenders'
```

---

## Settings Management

### Base Settings Structure

```python
# config/settings/base.py
import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Core Settings
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = []

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'django_filters',
    'django_extensions',
]

# Core apps always loaded
CORE_APPS = [
    'apps.core',
    'apps.core.auth',
    'apps.core.base',
    'apps.core.api',
    'apps.core.notifications',
    'apps.core.documents',
    'apps.core.workflow',
    'apps.analytics',
]

# Vertical apps loaded conditionally
MEDICAL_APPS = [
    'apps.medical',
    'apps.medical.patients',
    'apps.medical.surgery',
    'apps.medical.clinical',
    'apps.medical.appointments',
    'apps.medical.billing',
]

PUBLIC_APPS = [
    'apps.public',
    'apps.public.tenders',
    'apps.public.suppliers',
    'apps.public.contracts',
    'apps.public.compliance',
    'apps.public.procurement',
]

# Dynamic app loading based on enabled verticals
ENABLED_VERTICALS = os.environ.get('ENABLED_VERTICALS', 'medical,public').split(',')

LOCAL_APPS = CORE_APPS.copy()

if 'medical' in ENABLED_VERTICALS:
    LOCAL_APPS.extend(MEDICAL_APPS)

if 'public' in ENABLED_VERTICALS:
    LOCAL_APPS.extend(PUBLIC_APPS)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Vertical Configurations
VERTICAL_CONFIGS = {
    'medical': {
        'name': 'Medical Hub',
        'features': [
            'patient_management',
            'surgery_planning',
            'clinical_notes',
            'medical_billing',
        ],
        'required_apps': MEDICAL_APPS,
        'url_namespace': 'medical',
        'api_prefix': 'medical',
    },
    'public': {
        'name': 'Public Hub',
        'features': [
            'tender_management',
            'supplier_registry',
            'bid_evaluation',
            'contract_management',
        ],
        'required_apps': PUBLIC_APPS,
        'url_namespace': 'public',
        'api_prefix': 'public',
    },
}

# Database Configuration with vertical-specific routing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'reactdjango_hub'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

DATABASE_ROUTERS = ['config.routers.VerticalDatabaseRouter']

# Middleware with vertical awareness
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.OrganizationMiddleware',  # Adds organization to request
    'apps.core.middleware.VerticalMiddleware',      # Adds vertical context
]
```

### Vertical-Specific Settings

```python
# config/settings/verticals/medical.py
from ..base import *

# Medical-specific settings
MEDICAL_FEATURES = {
    'ENABLE_HIPAA_COMPLIANCE': True,
    'REQUIRE_MEDICAL_LICENSE': True,
    'ENABLE_PRESCRIPTION_MODULE': True,
    'ENABLE_LAB_INTEGRATION': True,
    'ENABLE_PACS_INTEGRATION': False,
}

# Medical regulatory settings
MEDICAL_COMPLIANCE = {
    'HIPAA_AUDIT_LEVEL': 'full',
    'PHI_ENCRYPTION_REQUIRED': True,
    'MEDICAL_RECORD_RETENTION_YEARS': 7,
    'REQUIRE_PHYSICIAN_SIGNATURE': True,
}

# HL7/FHIR Configuration
HL7_CONFIG = {
    'LISTENER_HOST': '0.0.0.0',
    'LISTENER_PORT': 2575,
    'MESSAGE_TYPES': ['ADT', 'ORM', 'ORU'],
}

FHIR_SERVER = {
    'URL': os.environ.get('FHIR_SERVER_URL'),
    'VERSION': 'R4',
    'AUTH_TYPE': 'oauth2',
}

# Override middleware for medical
MIDDLEWARE += [
    'apps.medical.middleware.HIPAAComplianceMiddleware',
    'apps.medical.middleware.MedicalAuditMiddleware',
]
```

```python
# config/settings/verticals/public.py
from ..base import *

# Public procurement settings
PUBLIC_FEATURES = {
    'ENABLE_PUBLIC_PORTAL': True,
    'REQUIRE_TENDER_PUBLICATION': True,
    'ENABLE_SUPPLIER_PREQUALIFICATION': True,
    'ENABLE_BID_ENCRYPTION': True,
    'ENABLE_CONTRACT_MANAGEMENT': True,
}

# Transparency and compliance
PUBLIC_COMPLIANCE = {
    'TRANSPARENCY_LEVEL': 'full',
    'PUBLIC_DISCLOSURE_REQUIRED': True,
    'TENDER_ARCHIVE_YEARS': 10,
    'REQUIRE_INTEGRITY_PACT': True,
}

# Government portal integration
GOV_PORTAL = {
    'API_URL': os.environ.get('GOV_PORTAL_URL'),
    'API_KEY': os.environ.get('GOV_PORTAL_KEY'),
    'AUTO_PUBLISH': True,
}

# Override middleware for public
MIDDLEWARE += [
    'apps.public.middleware.TransparencyMiddleware',
    'apps.public.middleware.AntiCorruptionMiddleware',
]
```

---

## Database Schema Strategy

### Table Naming Convention

```sql
-- Core tables (no prefix)
CREATE TABLE organizations (...);
CREATE TABLE users (...);
CREATE TABLE audit_logs (...);

-- Medical vertical tables (med_ prefix)
CREATE TABLE med_patients (...);
CREATE TABLE med_appointments (...);
CREATE TABLE med_procedures (...);
CREATE TABLE med_clinical_notes (...);

-- Public vertical tables (pub_ prefix)
CREATE TABLE pub_tenders (...);
CREATE TABLE pub_suppliers (...);
CREATE TABLE pub_bids (...);
CREATE TABLE pub_contracts (...);

-- Shared feature tables (feature_ prefix)
CREATE TABLE analytics_events (...);
CREATE TABLE notification_templates (...);
```

### Database Routing

```python
# config/routers.py
class VerticalDatabaseRouter:
    """
    Route database operations based on app labels
    """
    
    def db_for_read(self, model, **hints):
        """Suggest the database to read from"""
        app_label = model._meta.app_label
        
        # All models read from default database
        return 'default'
    
    def db_for_write(self, model, **hints):
        """Suggest the database for writes"""
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations between models"""
        # Get app prefixes
        app1_prefix = obj1._meta.app_label.split('.')[0]
        app2_prefix = obj2._meta.app_label.split('.')[0]
        
        # Allow relations within same vertical or with core
        if app1_prefix == app2_prefix:
            return True
        if 'core' in [app1_prefix, app2_prefix]:
            return True
        
        # Prevent cross-vertical relations
        return False
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure migrations run on correct database"""
        return db == 'default'
```

### Migration Management

```python
# apps/medical/patients/migrations/0001_initial.py
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    
    dependencies = [
        ('core', '0001_initial'),  # Depends on core
    ]
    
    operations = [
        migrations.CreateModel(
            name='MedicalPatient',
            fields=[
                # Fields...
            ],
            options={
                'db_table': 'med_patients',  # Explicit table name
            },
        ),
        migrations.AddIndex(
            model_name='medicalpatient',
            index=models.Index(
                fields=['organization', '-created_at'],
                name='med_patients_org_created_idx'
            ),
        ),
    ]
```

---

## URL Configuration

### Main URL Router

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/core/', include('apps.core.urls')),
    path('api/v1/auth/', include('apps.core.auth.urls')),
]

# Conditionally include vertical URLs
if 'medical' in settings.ENABLED_VERTICALS:
    urlpatterns += [
        path('api/v1/medical/', include('apps.medical.urls')),
    ]

if 'public' in settings.ENABLED_VERTICALS:
    urlpatterns += [
        path('api/v1/public/', include('apps.public.urls')),
    ]

# API documentation
if settings.DEBUG:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
    
    urlpatterns += [
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    ]
```

### Vertical URL Configuration

```python
# apps/medical/urls.py
from django.urls import path, include

app_name = 'medical'

urlpatterns = [
    path('patients/', include('apps.medical.patients.urls')),
    path('surgery/', include('apps.medical.surgery.urls')),
    path('clinical/', include('apps.medical.clinical.urls')),
    path('appointments/', include('apps.medical.appointments.urls')),
    path('billing/', include('apps.medical.billing.urls')),
]
```

---

## Middleware for Multi-Vertical Support

### Organization Middleware

```python
# apps/core/middleware.py
from django.utils.functional import SimpleLazyObject
from .models import Organization

class OrganizationMiddleware:
    """Add organization to request based on user"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request.organization = SimpleLazyObject(
            lambda: self.get_organization(request)
        )
        return self.get_response(request)
    
    def get_organization(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            return request.user.organization
        return None


class VerticalMiddleware:
    """Add vertical context to request"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        request.vertical = SimpleLazyObject(
            lambda: self.get_vertical(request)
        )
        return self.get_response(request)
    
    def get_vertical(self, request):
        # Determine from URL path
        if '/medical/' in request.path:
            return 'medical'
        elif '/public/' in request.path:
            return 'public'
        
        # Fallback to organization vertical
        if hasattr(request, 'organization') and request.organization:
            return request.organization.vertical
        
        return None
```

---

## Manager Classes for Vertical Filtering

```python
# apps/core/managers.py
from django.db import models

class VerticalManager(models.Manager):
    """Manager that filters by vertical"""
    
    def __init__(self, vertical=None):
        super().__init__()
        self.vertical = vertical
    
    def get_queryset(self):
        qs = super().get_queryset()
        if self.vertical:
            return qs.filter(organization__vertical=self.vertical)
        return qs


class OrganizationScopedManager(models.Manager):
    """Manager that filters by organization"""
    
    def for_organization(self, organization):
        return self.get_queryset().filter(organization=organization)
    
    def for_user(self, user):
        if user.is_superuser:
            return self.get_queryset()
        return self.for_organization(user.organization)


# Usage in models
class MedicalPatient(BaseEntity):
    # Default manager
    objects = models.Manager()
    
    # Vertical-specific manager
    medical = VerticalManager(vertical='medical')
    
    # Organization-scoped manager
    scoped = OrganizationScopedManager()
    
    class Meta:
        db_table = 'med_patients'

# Usage in views
def get_patients(request):
    # Get only medical patients for user's organization
    patients = MedicalPatient.scoped.for_user(request.user)
    return patients
```

---

## Testing Strategy for Multi-Vertical

### Test Structure

```python
# tests/test_verticals.py
from django.test import TestCase
from apps.core.models import Organization
from apps.medical.patients.models import MedicalPatient
from apps.public.tenders.models import PublicTender

class VerticalIsolationTest(TestCase):
    """Test that verticals are properly isolated"""
    
    def setUp(self):
        # Create organizations for each vertical
        self.medical_org = Organization.objects.create(
            name="Test Hospital",
            vertical="medical"
        )
        
        self.public_org = Organization.objects.create(
            name="Test Ministry",
            vertical="public"
        )
    
    def test_medical_model_requires_medical_org(self):
        """Medical models should only accept medical organizations"""
        with self.assertRaises(ValidationError):
            patient = MedicalPatient.objects.create(
                organization=self.public_org,  # Wrong vertical!
                medical_record_number="12345"
            )
    
    def test_public_model_requires_public_org(self):
        """Public models should only accept public organizations"""
        with self.assertRaises(ValidationError):
            tender = PublicTender.objects.create(
                organization=self.medical_org,  # Wrong vertical!
                tender_number="TEND-001"
            )
    
    def test_cross_vertical_relation_prevented(self):
        """Test that cross-vertical relations are prevented"""
        # This should be prevented by the database router
        pass


class VerticalFeatureTest(TestCase):
    """Test vertical-specific features"""
    
    def test_medical_features_only_for_medical(self):
        """Medical features should only be available for medical orgs"""
        medical_org = Organization.objects.create(
            name="Hospital",
            vertical="medical",
            enabled_features=['patient_management', 'surgery_planning']
        )
        
        self.assertTrue(medical_org.has_feature('patient_management'))
        self.assertTrue(medical_org.has_feature('surgery_planning'))
        self.assertFalse(medical_org.has_feature('tender_management'))
    
    def test_public_features_only_for_public(self):
        """Public features should only be available for public orgs"""
        public_org = Organization.objects.create(
            name="Ministry",
            vertical="public",
            enabled_features=['tender_management', 'supplier_registry']
        )
        
        self.assertTrue(public_org.has_feature('tender_management'))
        self.assertTrue(public_org.has_feature('supplier_registry'))
        self.assertFalse(public_org.has_feature('patient_management'))
```

---

## Adding a New Vertical

### Step-by-Step Process

1. **Create vertical app structure**:
```bash
cd backend/apps
mkdir new_vertical
cd new_vertical
python ../../manage.py startapp core
python ../../manage.py startapp feature1
python ../../manage.py startapp feature2
```

2. **Define vertical models**:
```python
# apps/new_vertical/core/models.py
from apps.core.base import BaseEntity

class NewVerticalEntity(BaseEntity):
    """Base entity for new vertical"""
    
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        limit_choices_to={'vertical': 'new_vertical'}
    )
    
    # Vertical-specific fields
    
    class Meta:
        db_table = 'new_vertical_entities'
        abstract = True
```

3. **Add vertical to settings**:
```python
# config/settings/base.py
VERTICAL_CONFIGS['new_vertical'] = {
    'name': 'New Vertical Hub',
    'features': [...],
    'required_apps': [...],
    'url_namespace': 'new_vertical',
    'api_prefix': 'new_vertical',
}
```

4. **Create vertical settings**:
```python
# config/settings/verticals/new_vertical.py
from ..base import *

NEW_VERTICAL_FEATURES = {
    # Vertical-specific feature flags
}
```

5. **Add URL routing**:
```python
# config/urls.py
if 'new_vertical' in settings.ENABLED_VERTICALS:
    urlpatterns += [
        path('api/v1/new_vertical/', include('apps.new_vertical.urls')),
    ]
```

6. **Run migrations**:
```bash
python manage.py makemigrations new_vertical
python manage.py migrate
```

---

## Best Practices

### 1. Model Inheritance
- Always inherit from appropriate base classes
- Use abstract models for shared functionality
- Override Meta.db_table with vertical prefix

### 2. Foreign Key Constraints
- Use limit_choices_to for vertical-specific relations
- Validate vertical in model clean() method
- Use select_related/prefetch_related for performance

### 3. API Design
- Namespace URLs by vertical
- Use vertical-specific serializers
- Implement proper permission classes

### 4. Testing
- Test vertical isolation
- Test cross-vertical prevention
- Test feature availability

### 5. Database
- Use consistent table naming
- Create appropriate indexes
- Consider partitioning for large tables

---

## Summary

This Django multi-vertical structure provides:

1. **Clear Separation**: Each vertical has its own apps and models
2. **Maximum Reuse**: Shared base classes and mixins
3. **Flexible Configuration**: Per-vertical settings and features
4. **Data Isolation**: Organization and vertical scoping
5. **Easy Extension**: Clear patterns for adding new verticals
6. **Type Safety**: Proper model constraints and validation
7. **Performance**: Optimized queries with proper managers
8. **Maintainability**: Consistent structure and naming conventions

The architecture scales from 2 to N verticals while maintaining clean code organization and preventing cross-vertical data leakage.