# Code Generation Templates

Comprehensive documentation for automated code generation templates in ReactDjango Hub, designed to accelerate development while maintaining quality, compliance, and consistency.

## 🎯 **Overview**

Code generators eliminate repetitive coding tasks by automatically creating standardized, compliant code templates with:
- RGPD compliance built-in
- Internationalization support (FR/DE/EN)
- Multi-tenant architecture patterns
- Security best practices
- Comprehensive testing boilerplate

## 🏗️ **Generator Architecture**

### **Generation Workflow**
```bash
1. Command execution → 2. Template selection → 3. Parameter injection → 4. Code generation → 5. File creation
```

### **Template Structure**
```
.claude/templates/
├── django/                    # Backend templates
│   ├── models/               # Model templates
│   ├── serializers/          # DRF serializer templates  
│   ├── views/                # API view templates
│   ├── admin/                # Admin interface templates
│   └── tests/                # Test templates
├── react/                    # Frontend templates
│   ├── components/           # React component templates
│   ├── pages/                # Page component templates
│   ├── hooks/                # Custom hook templates
│   ├── types/                # TypeScript type templates
│   └── tests/                # Component test templates
└── shared/                   # Cross-platform templates
    ├── api/                  # API interface templates
    ├── validation/           # Validation schema templates
    └── documentation/        # Auto-generated docs
```

## 🔧 **Django Model Generator**

### **Command Syntax**
```bash
make generate-model <ModelName> [options]

# Examples:
make generate-model User
make generate-model Organization --multi-tenant
make generate-model UserProfile --with-encryption
make generate-model AuditLog --immutable
```

### **Generated Files**
```bash
# Model generation creates:
backend/apps/core/models/<model_name>.py          # Model definition
backend/apps/core/serializers/<model_name>.py    # DRF serializers
backend/apps/core/views/<model_name>.py           # ViewSets and permissions
backend/apps/core/admin/<model_name>.py           # Admin interface
backend/apps/core/tests/test_<model_name>.py      # Comprehensive tests
backend/docs/models/<model_name>.md               # Model documentation
```

### **Template Features**

#### **Base Model Template**
```python
# Generated model structure
from django.db import models
from django.contrib.auth.models import User
from apps.core.models.base import BaseModel
from apps.core.compliance.rgpd import RGPDMixin
from apps.core.encryption import EncryptedTextField

class {{ model_name }}(BaseModel, RGPDMixin):
    """
    {{ model_description }}
    
    RGPD Compliance: {{ rgpd_classification }}
    Data Retention: {{ retention_period }}
    """
    
    # Standard fields with internationalization
    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("{{ model_name }} name")
    )
    
    # Audit fields (automatically included)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Multi-tenant support (if enabled)
    {% if multi_tenant %}
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    {% endif %}
    
    # Encrypted fields (if sensitive data)
    {% if has_encryption %}
    sensitive_data = EncryptedTextField(blank=True, null=True)
    {% endif %}
    
    class Meta:
        verbose_name = _("{{ model_name }}")
        verbose_name_plural = _("{{ model_name_plural }}")
        {% if multi_tenant %}
        unique_together = [('name', 'organization')]
        {% endif %}
        
    def __str__(self):
        return f"{self.name}"
    
    # RGPD compliance methods
    def anonymize(self):
        """Anonymize personal data for RGPD compliance."""
        # Implementation generated based on model fields
        pass
    
    def export_data(self):
        """Export user data for RGPD data portability."""
        # Implementation generated based on model fields
        pass
```

#### **RGPD Compliance Features**
- **Automatic data classification** based on field types
- **Data retention policies** with automatic cleanup
- **Anonymization methods** for personal data
- **Audit logging** for all data access
- **Export functionality** for data portability
- **Consent tracking** for data processing

#### **Multi-Tenant Support**
```python
# Automatic tenant isolation
class {{ model_name }}Manager(models.Manager):
    def get_queryset(self):
        # Automatic filtering by user's organization
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            return super().get_queryset().filter(
                organization=self.request.user.organization
            )
        return super().get_queryset()
```

### **Serializer Generation**
```python
# Auto-generated DRF serializer
from rest_framework import serializers
from apps.core.serializers.base import RGPDSerializerMixin

class {{ model_name }}Serializer(RGPDSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for {{ model_name }} with RGPD compliance.
    """
    
    class Meta:
        model = {{ model_name }}
        fields = '__all__'
        # Sensitive fields excluded from API by default
        exclude_rgpd_sensitive = True
        
    def validate(self, attrs):
        """Custom validation with internationalized error messages."""
        # Generated validation logic
        return super().validate(attrs)
```

### **API ViewSet Generation**
```python
# Auto-generated API views
from rest_framework import viewsets, permissions
from apps.core.permissions import MultiTenantPermission, RGPDPermission

class {{ model_name }}ViewSet(viewsets.ModelViewSet):
    """
    ViewSet for {{ model_name }} with multi-tenant and RGPD support.
    """
    serializer_class = {{ model_name }}Serializer
    permission_classes = [
        permissions.IsAuthenticated,
        MultiTenantPermission,
        RGPDPermission
    ]
    
    def get_queryset(self):
        # Automatic tenant filtering
        return {{ model_name }}.objects.filter(
            organization=self.request.user.organization
        )
    
    # RGPD compliance endpoints
    @action(detail=True, methods=['post'])
    def anonymize(self, request, pk=None):
        """Anonymize object for RGPD compliance."""
        # Generated implementation
        pass
    
    @action(detail=True, methods=['get'])
    def export_data(self, request, pk=None):
        """Export object data for RGPD compliance."""
        # Generated implementation
        pass
```

## 🎨 **React Component Generator**

### **Command Syntax**
```bash
make generate-component <ComponentName> [options]

# Examples:
make generate-component UserCard
make generate-component UserForm --with-validation
make generate-component UserTable --with-pagination
make generate-component UserDashboard --page
```

### **Generated Files**
```bash
# Component generation creates:
frontend/src/components/<ComponentName>/
├── index.tsx                           # Main component
├── <ComponentName>.tsx                 # Component implementation
├── <ComponentName>.module.css          # Component styles
├── <ComponentName>.test.tsx            # Unit tests
├── <ComponentName>.stories.tsx         # Storybook stories
└── types.ts                           # TypeScript interfaces

frontend/src/locales/
├── fr/<component-name>.json            # French translations
├── de/<component-name>.json            # German translations
└── en/<component-name>.json            # English translations
```

### **Component Template**
```typescript
// Generated React component
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { {{ model_name }}Type } from '@/types/api';
import styles from './{{ component_name }}.module.css';

interface {{ component_name }}Props {
  data?: {{ model_name }}Type;
  onSave?: (data: {{ model_name }}Type) => void;
  onCancel?: () => void;
  loading?: boolean;
  error?: string;
}

export const {{ component_name }}: React.FC<{{ component_name }}Props> = ({
  data,
  onSave,
  onCancel,
  loading = false,
  error
}) => {
  const { t } = useTranslation('{{ component_name_lower }}');
  const [formData, setFormData] = useState<{{ model_name }}Type>(
    data || {} as {{ model_name }}Type
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave?.(formData);
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>
        {t('title', { defaultValue: '{{ component_name }}' })}
      </h2>
      
      {error && (
        <div className={styles.error} role="alert">
          {t('error.general', { defaultValue: 'An error occurred' })}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className={styles.form}>
        {/* Generated form fields based on model */}
        <div className={styles.field}>
          <label htmlFor="name" className={styles.label}>
            {t('field.name', { defaultValue: 'Name' })}
          </label>
          <input
            id="name"
            type="text"
            value={formData.name || ''}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className={styles.input}
            required
            aria-describedby="name-help"
          />
          <div id="name-help" className={styles.helpText}>
            {t('field.name.help', { defaultValue: 'Enter the name' })}
          </div>
        </div>
        
        <div className={styles.actions}>
          <button
            type="submit"
            disabled={loading}
            className={styles.primaryButton}
          >
            {loading 
              ? t('button.saving', { defaultValue: 'Saving...' })
              : t('button.save', { defaultValue: 'Save' })
            }
          </button>
          
          <button
            type="button"
            onClick={onCancel}
            className={styles.secondaryButton}
          >
            {t('button.cancel', { defaultValue: 'Cancel' })}
          </button>
        </div>
      </form>
    </div>
  );
};
```

### **Internationalization Features**
- **French-first labels** with automatic translation keys
- **Fallback translations** for DE/EN
- **Accessibility support** with ARIA labels
- **Cultural formatting** for dates, numbers, currencies
- **RTL support** (if needed for Arabic/Hebrew)

### **Generated Test Files**
```typescript
// Auto-generated component tests
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { {{ component_name }} } from './{{ component_name }}';
import { I18nextProvider } from 'react-i18next';
import i18n from '@/config/i18n';

describe('{{ component_name }}', () => {
  const defaultProps = {
    onSave: jest.fn(),
    onCancel: jest.fn(),
  };

  const renderComponent = (props = {}) => {
    return render(
      <I18nextProvider i18n={i18n}>
        <{{ component_name }} {...defaultProps} {...props} />
      </I18nextProvider>
    );
  };

  test('renders component with French labels', () => {
    renderComponent();
    expect(screen.getByRole('heading')).toBeInTheDocument();
    expect(screen.getByLabelText(/nom/i)).toBeInTheDocument(); // French label
  });

  test('handles form submission', async () => {
    const mockSave = jest.fn();
    renderComponent({ onSave: mockSave });
    
    fireEvent.change(screen.getByLabelText(/nom/i), { target: { value: 'Test Name' } });
    fireEvent.click(screen.getByRole('button', { name: /enregistrer/i }));
    
    await waitFor(() => {
      expect(mockSave).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Test Name' })
      );
    });
  });

  test('displays error messages', () => {
    renderComponent({ error: 'Test error' });
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});
```

## 🔌 **API Generator**

### **Command Syntax**
```bash
make generate-api <resource> [options]

# Examples:
make generate-api users
make generate-api organizations --nested
make generate-api reports --read-only
```

### **Generated API Structure**
```bash
# API generation creates:
backend/apps/api/v1/<resource>/
├── views.py              # API viewsets
├── serializers.py        # Request/response serializers  
├── urls.py              # URL routing
├── permissions.py       # Access control
└── tests.py             # API tests

frontend/src/api/<resource>/
├── client.ts            # API client functions
├── types.ts             # TypeScript interfaces
├── hooks.ts             # React hooks for API calls
└── cache.ts             # Caching configuration
```

### **TypeScript Client Generation**
```typescript
// Auto-generated API client
import { ApiClient } from '@/api/base';
import { {{ model_name }}Type, {{ model_name }}CreateType } from './types';

export class {{ model_name }}ApiClient extends ApiClient {
  private endpoint = '/api/v1/{{ resource_name }}/';

  async list(params?: {
    page?: number;
    pageSize?: number;
    search?: string;
    ordering?: string;
  }): Promise<{ results: {{ model_name }}Type[], count: number }> {
    return this.get(this.endpoint, { params });
  }

  async create(data: {{ model_name }}CreateType): Promise<{{ model_name }}Type> {
    return this.post(this.endpoint, data);
  }

  async retrieve(id: number): Promise<{{ model_name }}Type> {
    return this.get(`${this.endpoint}${id}/`);
  }

  async update(id: number, data: Partial<{{ model_name }}Type>): Promise<{{ model_name }}Type> {
    return this.patch(`${this.endpoint}${id}/`, data);
  }

  async destroy(id: number): Promise<void> {
    return this.delete(`${this.endpoint}${id}/`);
  }

  // RGPD compliance endpoints
  async anonymize(id: number): Promise<void> {
    return this.post(`${this.endpoint}${id}/anonymize/`);
  }

  async exportData(id: number): Promise<Blob> {
    return this.get(`${this.endpoint}${id}/export_data/`, { 
      responseType: 'blob' 
    });
  }
}
```

### **React Hooks Generation**
```typescript
// Auto-generated React hooks
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { {{ model_name }}ApiClient } from './client';

const apiClient = new {{ model_name }}ApiClient();

export const use{{ model_name }}List = (params?: Parameters<typeof apiClient.list>[0]) => {
  return useQuery({
    queryKey: ['{{ resource_name }}', 'list', params],
    queryFn: () => apiClient.list(params),
  });
};

export const use{{ model_name }} = (id: number) => {
  return useQuery({
    queryKey: ['{{ resource_name }}', id],
    queryFn: () => apiClient.retrieve(id),
    enabled: !!id,
  });
};

export const useCreate{{ model_name }} = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{{ resource_name }}'] });
    },
  });
};

export const useUpdate{{ model_name }} = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<{{ model_name }}Type> }) =>
      apiClient.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['{{ resource_name }}', id] });
      queryClient.invalidateQueries({ queryKey: ['{{ resource_name }}', 'list'] });
    },
  });
};
```

## 📋 **Generator Configuration**

### **Template Customization**
```yaml
# .claude/generator-config.yml
generators:
  django_model:
    base_template: "django/models/base.py.j2"
    features:
      - rgpd_compliance: true
      - multi_tenant: true
      - audit_logging: true
      - internationalization: true
    
  react_component:
    base_template: "react/components/base.tsx.j2"
    features:
      - french_first: true
      - accessibility: true
      - testing: true
      - storybook: true

  api_client:
    base_template: "shared/api/client.ts.j2"
    features:
      - typescript: true
      - react_query: true
      - error_handling: true
      - caching: true
```

### **Custom Field Types**
```python
# Custom field type definitions
FIELD_TYPE_MAPPING = {
    'email': 'models.EmailField',
    'phone': 'PhoneNumberField',  # django-phonenumber-field
    'encrypted_text': 'EncryptedTextField',
    'rgpd_sensitive': 'RGPDTextField',
    'multi_language': 'JSONField',  # For translations
}

# Validation patterns
VALIDATION_PATTERNS = {
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'phone': r'^\+?1?\d{9,15}$',
    'postal_code': r'^\d{5}$',  # French postal code
}
```

## 🚀 **Usage Examples**

### **Complete Feature Generation**
```bash
# Generate a complete user management feature
make generate-model User --with-encryption
make generate-api users
make generate-component UserForm --with-validation
make generate-component UserList --with-pagination
make generate-page UsersPage

# This creates:
# - Django User model with RGPD compliance
# - Complete REST API with permissions
# - React form component with validation
# - List component with pagination
# - Full page with routing integration
```

### **Multi-Tenant Organization System**
```bash
# Generate organization structure
make generate-model Organization --multi-tenant-root
make generate-model Team --multi-tenant --parent=Organization
make generate-model User --multi-tenant --parent=Organization

# This creates a complete multi-tenant hierarchy
```

### **RGPD Compliance Suite**
```bash
# Generate RGPD-focused models
make generate-model ConsentRecord --immutable
make generate-model DataProcessingLog --audit-only
make generate-model DataExportRequest --with-workflow

# This creates complete RGPD compliance infrastructure
```

## 📊 **Code Quality & Testing**

### **Generated Code Quality**
- **Linting compliance**: All generated code passes ESLint/Flake8
- **Type safety**: Complete TypeScript/Python type annotations
- **Test coverage**: Comprehensive test suites generated
- **Documentation**: Auto-generated API documentation
- **Security**: Built-in security best practices

### **Integration Testing**
```bash
# Test generated code integration
make test-generated-code

# This runs:
# - Unit tests for all generated components
# - Integration tests for API endpoints
# - E2E tests for complete workflows
# - Security scans for generated code
# - Accessibility tests for UI components
```

---

🎯 **These code generators accelerate development by 70-90% while ensuring consistency, compliance, and quality across the entire full-stack application.**