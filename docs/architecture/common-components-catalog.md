# Common Components Catalog
## Shared Platform Components Across All Verticals

**Version**: 1.0  
**Date**: January 2025  
**Status**: Active  
**Purpose**: Comprehensive catalog of all reusable components across the ReactDjango Hub platform

---

## Overview

This document catalogs all shared components that form the foundation of the ReactDjango Hub platform. These components are used across all verticals (Medical Hub, Public Hub, and future verticals) and provide consistent functionality, UI/UX, and technical patterns.

---

## 1. Microservices (Fully Shared)

### 1.1 Identity Service
**Location**: `services/identity-service/`  
**Port**: 8001  
**Technology**: FastAPI, SQLAlchemy, PostgreSQL  

#### Purpose
Centralized authentication and user management for all verticals.

#### Interface
```python
# REST API Endpoints
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh
POST   /api/v1/auth/verify-mfa
GET    /api/v1/users/me
PUT    /api/v1/users/{user_id}
GET    /api/v1/organizations/{org_id}
POST   /api/v1/organizations
```

#### Extensibility Points
```python
# Custom user attributes per vertical
class UserExtension(BaseModel):
    vertical: str
    attributes: Dict[str, Any]
    
    # Medical: medical_license, specialization
    # Public: procurement_authority, clearance_level
```

#### Usage Example
```python
# From Django backend
from apps.core.auth.client import IdentityServiceClient

client = IdentityServiceClient()
user = client.get_user(user_id="...")
token = client.validate_token(jwt_token="...")
```

---

### 1.2 Communication Service
**Location**: `services/communication-service/`  
**Port**: 8002  
**Technology**: FastAPI, PostgreSQL, Redis, Celery  

#### Purpose
Unified communication hub for all notification types across verticals.

#### Interface
```python
# REST API Endpoints
POST   /api/v1/notifications/email
POST   /api/v1/notifications/sms
POST   /api/v1/notifications/push
POST   /api/v1/notifications/in-app
GET    /api/v1/notifications/templates
POST   /api/v1/notifications/bulk
GET    /api/v1/notifications/status/{notification_id}
```

#### Extensibility Points
```python
# Custom notification templates per vertical
class NotificationTemplate(BaseModel):
    vertical: str
    template_id: str
    content: Dict[str, str]  # Multi-language support
    variables: List[str]
    
    # Medical: appointment_reminder, procedure_update
    # Public: tender_deadline, bid_status_change
```

#### Usage Example
```python
# Sending a notification
from apps.core.notifications.client import CommunicationClient

comm = CommunicationClient()
comm.send_email(
    template="appointment_reminder",
    recipient="user@example.com",
    variables={
        "patient_name": "John Doe",
        "appointment_time": "2025-01-15 10:00"
    }
)
```

---

### 1.3 Content Service
**Location**: `services/content-service/`  
**Port**: 8003  
**Technology**: FastAPI, PostgreSQL, S3/MinIO  

#### Purpose
Document and media management with versioning and access control.

#### Interface
```python
# REST API Endpoints
POST   /api/v1/documents/upload
GET    /api/v1/documents/{document_id}
PUT    /api/v1/documents/{document_id}
DELETE /api/v1/documents/{document_id}
GET    /api/v1/documents/{document_id}/versions
POST   /api/v1/documents/{document_id}/share
GET    /api/v1/documents/search
```

#### Extensibility Points
```python
# Custom document types per vertical
class DocumentType(BaseModel):
    vertical: str
    type_name: str
    metadata_schema: Dict
    retention_policy: Dict
    
    # Medical: medical_record, lab_report, prescription
    # Public: tender_document, contract, compliance_cert
```

#### Usage Example
```python
# Document upload with metadata
from apps.core.documents.client import ContentClient

content = ContentClient()
doc_id = content.upload_document(
    file=file_stream,
    document_type="medical_record",
    metadata={
        "patient_id": "12345",
        "procedure_date": "2025-01-10",
        "confidentiality": "high"
    }
)
```

---

### 1.4 Workflow Intelligence Service
**Location**: `services/workflow-intelligence-service/`  
**Port**: 8004  
**Technology**: FastAPI, PostgreSQL, Celery, Redis  

#### Purpose
Process automation and workflow orchestration across verticals.

#### Interface
```python
# REST API Endpoints
POST   /api/v1/workflows/create
GET    /api/v1/workflows/{workflow_id}
POST   /api/v1/workflows/{workflow_id}/execute
GET    /api/v1/workflows/{workflow_id}/status
POST   /api/v1/workflows/templates
GET    /api/v1/tasks/pending
POST   /api/v1/tasks/{task_id}/complete
```

#### Extensibility Points
```python
# Custom workflow definitions
class WorkflowDefinition(BaseModel):
    vertical: str
    workflow_type: str
    steps: List[WorkflowStep]
    triggers: List[WorkflowTrigger]
    
    # Medical: surgery_approval, patient_onboarding
    # Public: tender_evaluation, contract_approval
```

---

## 2. Django Core Apps (Shared Base)

### 2.1 Base Models and Mixins
**Location**: `backend/apps/core/base/`

#### TimeStampedModel
```python
class TimeStampedModel(models.Model):
    """Base model with created/updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        abstract = True
```

#### TenantModel
```python
class TenantModel(TimeStampedModel):
    """Base model with multi-tenant support"""
    organization = models.ForeignKey(
        'core.Organization',
        on_delete=models.CASCADE,
        related_name='%(class)s_set'
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['organization', '-created_at']),
        ]
```

#### SoftDeleteModel
```python
class SoftDeleteModel(models.Model):
    """Soft delete functionality"""
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    
    class Meta:
        abstract = True
```

#### AuditModel
```python
class AuditModel(models.Model):
    """Comprehensive audit trail"""
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_created',
        on_delete=models.PROTECT
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_modified',
        on_delete=models.PROTECT
    )
    version = models.IntegerField(default=1)
    change_history = models.JSONField(default=list)
    
    class Meta:
        abstract = True
```

---

### 2.2 Common Utilities
**Location**: `backend/apps/core/utils/`

#### API Response Builders
```python
class APIResponse:
    @staticmethod
    def success(data=None, message="Success", status=200):
        return Response({
            "success": True,
            "message": message,
            "data": data,
            "timestamp": timezone.now().isoformat()
        }, status=status)
    
    @staticmethod
    def error(message="Error", errors=None, status=400):
        return Response({
            "success": False,
            "message": message,
            "errors": errors,
            "timestamp": timezone.now().isoformat()
        }, status=status)
```

#### Pagination Utilities
```python
class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'page_size': self.page_size,
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'results': data
        })
```

#### Validation Utilities
```python
class Validators:
    @staticmethod
    def validate_phone(phone: str) -> str:
        """International phone validation"""
        try:
            parsed = phonenumbers.parse(phone, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValidationError("Invalid phone number")
            return phonenumbers.format_number(
                parsed, 
                phonenumbers.PhoneNumberFormat.E164
            )
        except Exception as e:
            raise ValidationError(f"Phone validation failed: {e}")
    
    @staticmethod
    def validate_email_domain(email: str, allowed_domains: List[str]) -> bool:
        """Validate email against allowed domains"""
        domain = email.split('@')[1]
        return domain in allowed_domains
```

---

### 2.3 API Base Classes
**Location**: `backend/apps/core/api/`

#### BaseAPIView
```python
class BaseAPIView(APIView):
    """Base API view with common functionality"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_organization(self):
        """Get current user's organization"""
        return self.request.user.organization
    
    def filter_by_organization(self, queryset):
        """Filter queryset by organization"""
        return queryset.filter(organization=self.get_organization())
```

#### BaseModelViewSet
```python
class BaseModelViewSet(ModelViewSet):
    """Base viewset with tenant filtering"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            return queryset.filter(organization=self.request.user.organization)
        return queryset.none()
    
    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            organization=self.request.user.organization
        )
```

---

## 3. Frontend Common Components

### 3.1 UI Component Library
**Location**: `frontend/src/components/common/`

#### DataTable Component
```typescript
// components/common/DataTable/DataTable.tsx
interface DataTableProps<T> {
  data: T[];
  columns: ColumnDefinition<T>[];
  onSort?: (column: string, direction: 'asc' | 'desc') => void;
  onFilter?: (filters: FilterDefinition[]) => void;
  onRowClick?: (row: T) => void;
  selectable?: boolean;
  onSelectionChange?: (selected: T[]) => void;
  pagination?: PaginationConfig;
  loading?: boolean;
  emptyMessage?: string;
  customRowRenderer?: (row: T) => React.ReactNode;
}

export const DataTable = <T extends Record<string, any>>({
  data,
  columns,
  ...props
}: DataTableProps<T>) => {
  // Reusable table implementation
  return (
    <div className="data-table-container">
      <TableHeader columns={columns} onSort={props.onSort} />
      <TableBody data={data} columns={columns} />
      {props.pagination && <TablePagination {...props.pagination} />}
    </div>
  );
};
```

#### Form Components
```typescript
// components/common/Forms/FormField.tsx
interface FormFieldProps {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'select' | 'date' | 'file';
  required?: boolean;
  validation?: ValidationRule[];
  placeholder?: string;
  helpText?: string;
  error?: string;
  vertical?: 'medical' | 'public'; // For vertical-specific styling
}

export const FormField: React.FC<FormFieldProps> = ({
  name,
  label,
  type,
  ...props
}) => {
  const fieldClassName = cn(
    'form-field',
    props.vertical && `form-field--${props.vertical}`,
    props.error && 'form-field--error'
  );
  
  return (
    <div className={fieldClassName}>
      <Label htmlFor={name}>{label}</Label>
      <Input id={name} type={type} {...props} />
      {props.helpText && <HelpText>{props.helpText}</HelpText>}
      {props.error && <ErrorMessage>{props.error}</ErrorMessage>}
    </div>
  );
};
```

#### Modal Component
```typescript
// components/common/Modal/Modal.tsx
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  footer?: React.ReactNode;
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  children,
  ...props
}) => {
  if (!isOpen) return null;
  
  return createPortal(
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className={`modal modal--${props.size || 'md'}`}>
        <ModalHeader title={props.title} onClose={onClose} />
        <ModalBody>{children}</ModalBody>
        {props.footer && <ModalFooter>{props.footer}</ModalFooter>}
      </div>
    </div>,
    document.body
  );
};
```

#### Notification System
```typescript
// components/common/Notifications/NotificationProvider.tsx
interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const NotificationProvider: React.FC = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  
  const notify = useCallback((notification: Omit<Notification, 'id'>) => {
    const id = generateId();
    setNotifications(prev => [...prev, { ...notification, id }]);
    
    if (notification.duration !== 0) {
      setTimeout(() => {
        dismiss(id);
      }, notification.duration || 5000);
    }
  }, []);
  
  return (
    <NotificationContext.Provider value={{ notify, dismiss }}>
      {children}
      <NotificationContainer notifications={notifications} />
    </NotificationContext.Provider>
  );
};
```

---

### 3.2 Common Hooks
**Location**: `frontend/src/hooks/common/`

#### useAuth Hook
```typescript
// hooks/common/useAuth.ts
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  permissions: string[];
}

export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    permissions: []
  });
  
  const login = async (credentials: LoginCredentials) => {
    const response = await authApi.login(credentials);
    setAuthState({
      user: response.user,
      isAuthenticated: true,
      isLoading: false,
      permissions: response.permissions
    });
    localStorage.setItem('token', response.token);
  };
  
  const logout = async () => {
    await authApi.logout();
    setAuthState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      permissions: []
    });
    localStorage.removeItem('token');
  };
  
  const hasPermission = (permission: string) => {
    return authState.permissions.includes(permission);
  };
  
  return {
    ...authState,
    login,
    logout,
    hasPermission
  };
};
```

#### useApi Hook
```typescript
// hooks/common/useApi.ts
interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

export const useApi = <T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = []
) => {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: false,
    error: null
  });
  
  const execute = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const data = await apiCall();
      setState({ data, loading: false, error: null });
      return data;
    } catch (error) {
      setState({ data: null, loading: false, error: error as Error });
      throw error;
    }
  }, dependencies);
  
  useEffect(() => {
    execute();
  }, dependencies);
  
  return { ...state, refetch: execute };
};
```

#### usePagination Hook
```typescript
// hooks/common/usePagination.ts
interface PaginationState {
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

export const usePagination = (initialPageSize = 20) => {
  const [state, setState] = useState<PaginationState>({
    page: 1,
    pageSize: initialPageSize,
    totalItems: 0,
    totalPages: 0
  });
  
  const setPage = (page: number) => {
    setState(prev => ({ ...prev, page }));
  };
  
  const setPageSize = (pageSize: number) => {
    setState(prev => ({ 
      ...prev, 
      pageSize,
      page: 1 // Reset to first page
    }));
  };
  
  const updateTotals = (totalItems: number) => {
    setState(prev => ({
      ...prev,
      totalItems,
      totalPages: Math.ceil(totalItems / prev.pageSize)
    }));
  };
  
  return {
    ...state,
    setPage,
    setPageSize,
    updateTotals,
    hasNext: state.page < state.totalPages,
    hasPrev: state.page > 1
  };
};
```

---

### 3.3 Common API Clients
**Location**: `frontend/src/api/common/`

#### Base API Client
```typescript
// api/common/BaseApiClient.ts
class BaseApiClient {
  private baseURL: string;
  private timeout: number;
  
  constructor(baseURL: string, timeout = 30000) {
    this.baseURL = baseURL;
    this.timeout = timeout;
  }
  
  private async request<T>(
    method: string,
    endpoint: string,
    data?: any,
    config?: RequestConfig
  ): Promise<T> {
    const token = localStorage.getItem('token');
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
        ...config?.headers
      },
      body: data ? JSON.stringify(data) : undefined,
      signal: AbortSignal.timeout(this.timeout)
    });
    
    if (!response.ok) {
      throw new ApiError(response.status, await response.text());
    }
    
    return response.json();
  }
  
  get<T>(endpoint: string, config?: RequestConfig) {
    return this.request<T>('GET', endpoint, undefined, config);
  }
  
  post<T>(endpoint: string, data?: any, config?: RequestConfig) {
    return this.request<T>('POST', endpoint, data, config);
  }
  
  put<T>(endpoint: string, data?: any, config?: RequestConfig) {
    return this.request<T>('PUT', endpoint, data, config);
  }
  
  delete<T>(endpoint: string, config?: RequestConfig) {
    return this.request<T>('DELETE', endpoint, undefined, config);
  }
}
```

#### Auth API Client
```typescript
// api/common/AuthApiClient.ts
class AuthApiClient extends BaseApiClient {
  constructor() {
    super(process.env.REACT_APP_AUTH_API_URL || 'http://localhost:8001');
  }
  
  async login(credentials: LoginCredentials) {
    return this.post<LoginResponse>('/api/v1/auth/login', credentials);
  }
  
  async logout() {
    return this.post('/api/v1/auth/logout');
  }
  
  async refreshToken(refreshToken: string) {
    return this.post<TokenResponse>('/api/v1/auth/refresh', { 
      refresh_token: refreshToken 
    });
  }
  
  async getCurrentUser() {
    return this.get<User>('/api/v1/users/me');
  }
  
  async updateProfile(data: Partial<User>) {
    return this.put<User>('/api/v1/users/me', data);
  }
}

export const authApi = new AuthApiClient();
```

---

## 4. Infrastructure Components

### 4.1 Docker Base Images
**Location**: `infrastructure/docker/base/`

#### Python Service Base
```dockerfile
# infrastructure/docker/base/python-service.dockerfile
FROM python:3.13-slim

# Common Python service setup
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install common Python packages
COPY requirements.shared.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.shared.txt

# Health check script
COPY scripts/health-check.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/health-check.sh

# Common environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
```

#### Node.js Frontend Base
```dockerfile
# infrastructure/docker/base/node-frontend.dockerfile
FROM node:20-alpine AS base

# Install common dependencies
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy shared package configurations
COPY package.shared.json ./
COPY .eslintrc.shared.json ./
COPY tsconfig.shared.json ./

# Install shared dependencies
RUN npm ci --only=production
```

---

### 4.2 Kubernetes Resources
**Location**: `infrastructure/kubernetes/base/`

#### ConfigMaps
```yaml
# infrastructure/kubernetes/base/configmap-common.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: common-config
  namespace: default
data:
  LOG_LEVEL: "info"
  TIMEZONE: "UTC"
  MAX_REQUEST_SIZE: "10485760"
  SESSION_TIMEOUT: "3600"
  CORS_ALLOWED_ORIGINS: "*"
  API_VERSION: "v1"
```

#### Service Templates
```yaml
# infrastructure/kubernetes/base/service-template.yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ .ServiceName }}
  labels:
    app: {{ .AppName }}
    vertical: {{ .Vertical }}
spec:
  type: ClusterIP
  ports:
    - port: {{ .Port }}
      targetPort: {{ .TargetPort }}
      protocol: TCP
  selector:
    app: {{ .AppName }}
    vertical: {{ .Vertical }}
```

---

### 4.3 CI/CD Templates
**Location**: `.github/workflows/templates/`

#### Test Pipeline Template
```yaml
# .github/workflows/templates/test-template.yml
name: Test Template

on:
  workflow_call:
    inputs:
      service_name:
        required: true
        type: string
      test_command:
        required: true
        type: string

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
      
      - name: Install dependencies
        run: |
          pip install -r services/${{ inputs.service_name }}/requirements.txt
      
      - name: Run tests
        run: ${{ inputs.test_command }}
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: ${{ inputs.service_name }}
```

---

## 5. Shared Utilities and Libraries

### 5.1 Authentication Library
**Location**: `backend/apps/core/auth/`

```python
# backend/apps/core/auth/decorators.py
def require_permission(permission: str):
    """Decorator to check user permissions"""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.has_permission(permission):
                raise PermissionDenied(f"Permission '{permission}' required")
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_vertical(vertical: str):
    """Decorator to check vertical access"""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if request.user.organization.vertical != vertical:
                raise PermissionDenied(f"Access limited to {vertical} vertical")
            return func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### 5.2 Data Export/Import Utilities
**Location**: `backend/apps/core/utils/data/`

```python
# backend/apps/core/utils/data/exporters.py
class BaseExporter:
    """Base class for data export"""
    
    def export_csv(self, queryset, fields):
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        
        for obj in queryset:
            row = {field: getattr(obj, field) for field in fields}
            writer.writerow(row)
        
        return output.getvalue()
    
    def export_excel(self, queryset, fields):
        wb = Workbook()
        ws = wb.active
        
        # Write headers
        for col, field in enumerate(fields, 1):
            ws.cell(row=1, column=col, value=field)
        
        # Write data
        for row_num, obj in enumerate(queryset, 2):
            for col, field in enumerate(fields, 1):
                ws.cell(row=row_num, column=col, value=getattr(obj, field))
        
        output = BytesIO()
        wb.save(output)
        return output.getvalue()
```

### 5.3 Caching Utilities
**Location**: `backend/apps/core/cache/`

```python
# backend/apps/core/cache/decorators.py
def cache_result(timeout=300, key_prefix=None):
    """Cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix or func.__name__}:"
            cache_key += hashlib.md5(
                f"{args}{kwargs}".encode()
            ).hexdigest()
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Calculate and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator
```

---

## 6. Testing Infrastructure

### 6.1 Test Base Classes
**Location**: `backend/tests/base/`

```python
# backend/tests/base/test_cases.py
class BaseTestCase(TestCase):
    """Base test case with common setup"""
    
    def setUp(self):
        self.organization = self.create_organization()
        self.user = self.create_user(organization=self.organization)
        self.client.force_authenticate(user=self.user)
    
    def create_organization(self, **kwargs):
        defaults = {
            'name': 'Test Organization',
            'vertical': 'medical',
            'is_active': True
        }
        defaults.update(kwargs)
        return Organization.objects.create(**defaults)
    
    def create_user(self, **kwargs):
        defaults = {
            'email': f'test{uuid.uuid4()}@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'is_active': True
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)
```

### 6.2 Test Utilities
**Location**: `frontend/src/test-utils/`

```typescript
// frontend/src/test-utils/render.tsx
export const renderWithProviders = (
  ui: React.ReactElement,
  options?: RenderOptions
) => {
  const AllTheProviders: React.FC = ({ children }) => {
    return (
      <BrowserRouter>
        <AuthProvider>
          <NotificationProvider>
            <ThemeProvider>
              {children}
            </ThemeProvider>
          </NotificationProvider>
        </AuthProvider>
      </BrowserRouter>
    );
  };
  
  return render(ui, { wrapper: AllTheProviders, ...options });
};
```

---

## 7. Configuration Management

### 7.1 Environment Configuration
**Location**: `config/`

```python
# config/settings/base.py
class BaseSettings:
    """Base configuration for all environments"""
    
    # Core settings
    DEBUG = False
    SECRET_KEY = env('SECRET_KEY')
    ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
    
    # Database
    DATABASES = {
        'default': env.db('DATABASE_URL')
    }
    
    # Cache
    CACHES = {
        'default': env.cache('REDIS_URL')
    }
    
    # Services
    IDENTITY_SERVICE_URL = env('IDENTITY_SERVICE_URL', default='http://identity-service:8001')
    COMMUNICATION_SERVICE_URL = env('COMMUNICATION_SERVICE_URL', default='http://communication-service:8002')
    CONTENT_SERVICE_URL = env('CONTENT_SERVICE_URL', default='http://content-service:8003')
    WORKFLOW_SERVICE_URL = env('WORKFLOW_SERVICE_URL', default='http://workflow-service:8004')
    
    # Feature flags
    FEATURES = {
        'MEDICAL_VERTICAL': env.bool('MEDICAL_ENABLED', default=True),
        'PUBLIC_VERTICAL': env.bool('PUBLIC_ENABLED', default=True),
    }
```

### 7.2 Logging Configuration
**Location**: `config/logging/`

```python
# config/logging/config.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'json': {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'file']
    }
}
```

---

## Summary

This catalog documents all shared components that form the foundation of the ReactDjango Hub platform. These components provide:

1. **Consistency**: Unified patterns across all verticals
2. **Reusability**: Significant code sharing and reduced duplication
3. **Maintainability**: Single source of truth for common functionality
4. **Scalability**: Components designed to support multiple verticals
5. **Extensibility**: Clear extension points for vertical-specific needs

Each component is designed with clear interfaces, extensive documentation, and well-defined extension points to support both current verticals (Medical Hub and Public Hub) and future expansions.