# SaaS Hub Architecture Specification

## Table of Contents
1. [Project Overview](#project-overview)
2. [Project Setup and Documentation](#project-setup-and-documentation)
3. [Folder Organization](#folder-organization)
4. [Microservices Architecture](#microservices-architecture)
5. [Common UI Components](#common-ui-components)
6. [Service-Specific Components](#service-specific-components)
7. [Implementation Guidelines](#implementation-guidelines)
8. [Development Environment](#development-environment)
9. [Deployment Strategy](#deployment-strategy)

## Project Overview

A comprehensive SaaS hub platform supporting multiple business applications with shared UI components and microservices architecture. The platform supports both Single Page Applications (SPA) and Web Application Platform (WAP) apps.

### Core Applications
- **PublicHub**: Public procurement platform
- **MedicalHub**: Medical/surgical pathway management system
- **Admin Portal**: Central administration dashboard
- **Mobile WAP Apps**: Progressive web applications for field use

### Microservices Architecture
- 🔐 **Identity Service** (Port 8001): Authentication, user management, MFA, organizations, and RBAC
- 📄 **Content Service** (Port 8002): Document management, file storage, search, permissions, and audit trails
- 📢 **Communication Service** (Port 8003): Multi-channel notifications, messaging, templates, and real-time communication
- 🔄 **Workflow Intelligence Service** (Port 8004): Process automation, AI insights, task management, and analytics

All services communicate through Kong API Gateway with standardized authentication and error handling.

## Project Setup and Documentation

### 1. claude.md Configuration

```markdown
# Claude Code Instructions

## Project Architecture Overview
This is a monorepo SaaS platform with:
- 4 microservices (Identity, Content, Communication, Workflow)
- Shared UI component library
- Multiple frontend applications (SPA and WAP)
- Kong API Gateway for service orchestration

## Coding Conventions
### Component Development
- Use functional components with TypeScript
- Follow atomic design principles
- Implement proper error boundaries
- Use composition over inheritance
- Maintain single responsibility principle

### API Integration Patterns
- All API calls go through Kong Gateway (localhost:8000)
- Use generated TypeScript clients from OpenAPI specs
- Implement retry logic with exponential backoff
- Handle errors at service boundaries
- Use TanStack Query for server state management

### Testing Requirements
- Unit tests for all shared components (>80% coverage)
- Integration tests for service communication
- E2E tests for critical user flows
- Visual regression tests for UI components
- Performance tests for API endpoints

## Monorepo Structure Guidelines
- Shared packages in /packages folder
- Applications in /apps folder (spa/ and wap/ subfolders)
- Services in /services folder
- Use pnpm workspaces for dependency management
- Follow semantic versioning for packages

## Service Communication
- Identity Service (8001): JWT-based authentication
- Content Service (8002): Document and file management
- Communication Service (8003): Notifications and messaging
- Workflow Service (8004): Process automation and AI

## Component Reusability Guidelines
- Abstract domain logic into props/callbacks
- Use composition for variant creation
- Implement proper TypeScript generics
- Document all public APIs
- Provide Storybook examples

## WAP vs SPA Architecture
- SPAs: Full React with Next.js, client-side routing
- WAPs: Lightweight with Preact, offline-first, service workers
- Shared components must work in both contexts
- Consider bundle size for WAP apps (<200KB target)
```

### 2. README.md Configuration

```markdown
# SaaS Hub Platform

## Quick Start

### Prerequisites
- Node.js 20 LTS
- pnpm 8+
- Docker Desktop
- PostgreSQL 17
- Redis

### Installation
\`\`\`bash
# Clone repository
git clone <repository-url>
cd saas-hub

# Install dependencies
pnpm install

# Setup environment variables
cp .env.example .env

# Start services with Docker
docker-compose up -d

# Run database migrations
pnpm migrate

# Start development servers
pnpm dev
\`\`\`

## Project Structure

### Monorepo Organization
- `/packages` - Shared libraries and components
- `/apps/spa` - Single page applications
- `/apps/wap` - Progressive web applications
- `/services` - Backend microservices
- `/gateway` - Kong API Gateway configuration
- `/infrastructure` - Deployment configurations

## Development Workflow

### Adding a New Component
\`\`\`bash
pnpm generate:component ComponentName
\`\`\`

### Adding a New App
\`\`\`bash
# For SPA
pnpm generate:spa-app app-name

# For WAP
pnpm generate:wap-app app-name
\`\`\`

### Running Tests
\`\`\`bash
# Unit tests
pnpm test

# E2E tests
pnpm test:e2e

# Visual regression
pnpm test:visual
\`\`\`

## Service Architecture

### API Gateway Routes
- `/api/identity/*` → Identity Service (8001)
- `/api/content/*` → Content Service (8002)
- `/api/communication/*` → Communication Service (8003)
- `/api/workflow/*` → Workflow Service (8004)

### Authentication Flow
1. User authenticates via Identity Service
2. Receives JWT token
3. Token included in all subsequent requests
4. Gateway validates token before routing

## Deployment

### Production Build
\`\`\`bash
pnpm build
\`\`\`

### Docker Deployment
\`\`\`bash
docker-compose -f docker-compose.prod.yml up
\`\`\`

### Kubernetes Deployment
\`\`\`bash
kubectl apply -k infrastructure/kubernetes/overlays/production
\`\`\`
```

## Folder Organization

```
project-root/
├── packages/
│   ├── shared-ui/                    # Common UI components
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── Identity/        # Auth, users, MFA, RBAC components
│   │   │   │   ├── Content/         # Documents, search, audit components
│   │   │   │   ├── Communication/   # Notifications, messaging components
│   │   │   │   ├── Workflow/        # Process, AI, analytics components
│   │   │   │   └── Common/          # Shared base components
│   │   │   ├── hooks/               # Shared React hooks
│   │   │   ├── contexts/            # Shared contexts
│   │   │   └── styles/              # Component styles
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── shared-utils/                 # Common utilities
│   │   ├── src/
│   │   │   ├── api/                 # API client utilities
│   │   │   │   ├── identity.client.ts
│   │   │   │   ├── content.client.ts
│   │   │   │   ├── communication.client.ts
│   │   │   │   ├── workflow.client.ts
│   │   │   │   └── kong.gateway.ts
│   │   │   ├── auth/                # Auth helpers
│   │   │   ├── validation/          # Shared validators
│   │   │   └── formatters/          # Data formatters
│   │   └── package.json
│   │
│   ├── shared-types/                 # TypeScript types/interfaces
│   │   ├── src/
│   │   │   ├── api/                 # API response types for all 4 services
│   │   │   ├── domain/              # Business domain types
│   │   │   └── ui/                  # UI component types
│   │   └── package.json
│   │
│   ├── design-system/                # Theme, tokens, base styles
│   │   ├── tokens/                   # Design tokens
│   │   ├── themes/                   # Theme configurations
│   │   └── assets/                   # Shared assets
│   │
│   └── wap-core/                     # WAP framework utilities
│       ├── src/
│       │   ├── routing/              # WAP routing logic
│       │   ├── state/                # WAP state management
│       │   └── platform/             # Platform-specific code
│       └── package.json
│
├── apps/
│   ├── spa/                          # Single Page Applications
│   │   ├── publichub/                # Public procurement app
│   │   │   ├── src/
│   │   │   ├── public/
│   │   │   ├── .env.example
│   │   │   └── package.json
│   │   ├── medicalhub/               # Medical/surgical pathway app
│   │   │   ├── src/
│   │   │   ├── public/
│   │   │   ├── .env.example
│   │   │   └── package.json
│   │   └── admin-portal/             # Central admin dashboard
│   │       ├── src/
│   │       ├── public/
│   │       ├── .env.example
│   │       └── package.json
│   │
│   └── wap/                          # Web Application Platform apps
│       ├── mobile-publichub/         # Mobile WAP for PublicHub
│       │   ├── src/
│       │   ├── manifest.json
│       │   └── package.json
│       ├── mobile-medicalhub/        # Mobile WAP for MedicalHub
│       │   ├── src/
│       │   ├── manifest.json
│       │   └── package.json
│       └── field-service/            # Field service WAP app
│           ├── src/
│           ├── manifest.json
│           └── package.json
│
├── services/                          # Backend microservices
│   ├── identity/                      # Port 8001 - FastAPI
│   │   ├── app/
│   │   │   ├── auth/                 # Authentication, JWT, MFA
│   │   │   ├── users/                # User management
│   │   │   ├── orgs/                 # Organizations
│   │   │   └── rbac/                 # Role-based access control
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── content/                       # Port 8002 - Django/DRF
│   │   ├── app/
│   │   │   ├── documents/            # Document management
│   │   │   ├── storage/              # File storage
│   │   │   ├── search/               # Search functionality
│   │   │   └── audit/                # Audit trails
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── communication/                 # Port 8003 - FastAPI
│   │   ├── app/
│   │   │   ├── notifications/        # Multi-channel notifications
│   │   │   ├── messaging/            # Real-time messaging
│   │   │   └── templates/            # Message templates
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── workflow/                      # Port 8004 - Django/DRF
│       ├── app/
│       │   ├── processes/            # Process automation
│       │   ├── ai/                   # AI insights
│       │   ├── tasks/                # Task management
│       │   └── analytics/            # Analytics
│       ├── tests/
│       ├── requirements.txt
│       └── Dockerfile
│
├── gateway/                           # Kong API Gateway configuration
│   ├── kong.yml                      # Kong declarative config
│   ├── plugins/                      # Custom Kong plugins
│   └── docker-compose.yml            # Kong + Konga setup
│
├── infrastructure/
│   ├── docker/
│   │   └── docker-compose.yml        # Full stack with all services
│   ├── kubernetes/
│   │   ├── base/
│   │   │   ├── identity/
│   │   │   ├── content/
│   │   │   ├── communication/
│   │   │   ├── workflow/
│   │   │   └── kong/
│   │   └── overlays/
│   └── terraform/
│       ├── modules/
│       └── environments/
│
├── docs/
│   ├── architecture/
│   │   ├── ADRs/                     # Architecture Decision Records
│   │   ├── diagrams/                 # Service communication diagrams
│   │   └── api-specs/                # OpenAPI specs for all 4 services
│   ├── api/
│   │   ├── identity/                 # Port 8001 API docs
│   │   ├── content/                  # Port 8002 API docs
│   │   ├── communication/            # Port 8003 API docs
│   │   ├── workflow/                 # Port 8004 API docs
│   │   └── postman/                  # Postman collections
│   └── components/
│       └── storybook/                # Component documentation
│
└── tools/
    ├── scripts/
    │   ├── setup.sh                  # Initial setup script
    │   ├── dev.sh                    # Development helper
    │   ├── deploy.sh                 # Deployment script
    │   └── generate-api-client.sh    # Generate TS clients from OpenAPI
    └── generators/                    # Component/service generators
        ├── component/
        ├── service/
        ├── spa-app/                  # SPA app generator
        └── wap-app/                  # WAP app generator
```

## Microservices Architecture

### Service Overview

| Service | Port | Technology | Purpose |
|---------|------|------------|---------|
| Identity | 8001 | FastAPI | Authentication, users, MFA, organizations, RBAC |
| Content | 8002 | Django/DRF | Documents, storage, search, audit trails |
| Communication | 8003 | FastAPI | Notifications, messaging, templates |
| Workflow | 8004 | Django/DRF | Process automation, AI insights, analytics |

### Kong API Gateway Configuration

```yaml
# gateway/kong.yml
_format_version: "2.1"

services:
  - name: identity-service
    url: http://identity:8001
    routes:
      - name: identity-route
        paths:
          - /api/identity
    plugins:
      - name: jwt
      - name: cors
      - name: rate-limiting
        config:
          minute: 100

  - name: content-service
    url: http://content:8002
    routes:
      - name: content-route
        paths:
          - /api/content
    plugins:
      - name: jwt
      - name: cors
      - name: request-size-limiting
        config:
          allowed_payload_size: 100

  - name: communication-service
    url: http://communication:8003
    routes:
      - name: communication-route
        paths:
          - /api/communication
    plugins:
      - name: jwt
      - name: cors
      - name: rate-limiting
        config:
          second: 10

  - name: workflow-service
    url: http://workflow:8004
    routes:
      - name: workflow-route
        paths:
          - /api/workflow
    plugins:
      - name: jwt
      - name: cors
      - name: response-transformer
```

### Service Communication Patterns

```typescript
// packages/shared-utils/src/api/kong.gateway.ts
import { IdentityClient } from './identity.client';
import { ContentClient } from './content.client';
import { CommunicationClient } from './communication.client';
import { WorkflowClient } from './workflow.client';

export class KongGateway {
  private baseURL: string;
  public identity: IdentityClient;
  public content: ContentClient;
  public communication: CommunicationClient;
  public workflow: WorkflowClient;

  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.identity = new IdentityClient(`${this.baseURL}/api/identity`);
    this.content = new ContentClient(`${this.baseURL}/api/content`);
    this.communication = new CommunicationClient(`${this.baseURL}/api/communication`);
    this.workflow = new WorkflowClient(`${this.baseURL}/api/workflow`);
  }

  setAuthToken(token: string) {
    this.identity.setToken(token);
    this.content.setToken(token);
    this.communication.setToken(token);
    this.workflow.setToken(token);
  }
}
```

## Common UI Components

### 1. Dashboard Framework

**Location**: `packages/shared-ui/src/components/Common/Dashboard/`

#### Core Features (MVP)
- Configurable widget grid system
- Drag-and-drop widget positioning
- Real-time data updates
- Responsive layout
- Widget registry system

#### Advanced Features
- Custom widget creation API
- Dashboard templates
- Export to PDF/Excel
- Scheduled email reports
- Mobile-optimized views

#### Technical Specifications
```typescript
interface DashboardConfig {
  id: string;
  name: string;
  layout: GridLayout;
  widgets: Widget[];
  refreshInterval?: number;
  permissions: string[];
}

interface Widget {
  id: string;
  type: 'chart' | 'metric' | 'table' | 'list' | 'custom';
  title: string;
  dataSource: {
    service: 'identity' | 'content' | 'communication' | 'workflow';
    endpoint: string;
    params?: Record<string, any>;
  };
  config: WidgetConfig;
  position: GridPosition;
}
```

### 2. Dynamic Form Builder

**Location**: `packages/shared-ui/src/components/Common/FormBuilder/`

#### Core Features (MVP)
- Drag-and-drop form designer
- Field validation rules
- Conditional logic
- Multi-step forms
- Form templates

#### Advanced Features
- Custom field types
- Form versioning
- A/B testing
- Auto-save drafts
- Prefill from external sources

#### Technical Specifications
```typescript
interface FormSchema {
  id: string;
  version: string;
  fields: FormField[];
  validation: ValidationSchema;
  steps?: FormStep[];
  conditionals?: ConditionalRule[];
}

interface FormField {
  id: string;
  type: 'text' | 'number' | 'select' | 'date' | 'file' | 'custom';
  label: string;
  required: boolean;
  validation?: FieldValidation;
  dependencies?: string[];
}
```

### 3. Document Preview/Generator

**Location**: `packages/shared-ui/src/components/Common/DocumentManager/`

#### Core Features (MVP)
- PDF generation from templates
- Document preview
- Digital signatures
- Version control
- Template variables

#### Advanced Features
- Batch document generation
- OCR for scanned documents
- Collaborative editing
- Watermarking
- Document comparison

### 4. Notification Center

**Location**: `packages/shared-ui/src/components/Common/NotificationCenter/`

#### Core Features (MVP)
- Multi-channel support (email, SMS, push, in-app)
- Notification preferences
- Read/unread status
- Notification history
- Real-time updates

#### Advanced Features
- Notification scheduling
- Digest mode
- Smart grouping
- Priority levels
- Do not disturb settings

### 5. File Upload System

**Location**: `packages/shared-ui/src/components/Common/FileUpload/`

#### Core Features (MVP)
- Drag-and-drop interface
- Progress tracking
- Multiple file selection
- File type validation
- Size limits

#### Advanced Features
- Chunked uploads
- Resume interrupted uploads
- Virus scanning
- Image optimization
- Cloud storage integration

### 6. Universal Search Bar

**Location**: `packages/shared-ui/src/components/Common/SearchBar/`

#### Core Features (MVP)
- Full-text search
- Autocomplete suggestions
- Search history
- Filter options
- Quick actions

#### Advanced Features
- Federated search
- Search analytics
- Saved searches
- Voice search
- AI-powered suggestions

### 7. Messaging Module

**Location**: `packages/shared-ui/src/components/Common/Messaging/`

#### Core Features (MVP)
- Real-time chat
- Message threads
- File attachments
- Typing indicators
- Read receipts

#### Advanced Features
- Video calls
- Screen sharing
- Message encryption
- Translation
- Chatbots integration

### 8. Role-Based Access Control UI

**Location**: `packages/shared-ui/src/components/Common/AccessControl/`

#### Core Features (MVP)
- User management
- Role assignment
- Permission matrix
- Access logs
- Multi-tenant support

#### Advanced Features
- Dynamic permissions
- Delegation workflows
- Access reviews
- Compliance reports
- SSO integration

## Service-Specific Components

### Identity Service Components (Port 8001)

#### Authentication Module
```typescript
interface AuthenticationProps {
  onSuccess: (user: User, token: string) => void;
  onError: (error: Error) => void;
  enableMFA?: boolean;
  socialProviders?: SocialProvider[];
}

// Features:
// - JWT token management
// - Refresh token rotation
// - MFA (TOTP, SMS, Email)
// - Social login (OAuth2)
// - Password policies
```

#### User Management Interface
```typescript
interface UserManagementProps {
  canCreate: boolean;
  canEdit: boolean;
  canDelete: boolean;
  bulkActions?: BulkAction[];
  customFields?: CustomField[];
}

// Features:
// - User CRUD operations
// - Bulk import/export
// - Profile customization
// - Avatar management
// - Activity tracking
```

### Content Service Components (Port 8002)

#### Document Manager
```typescript
interface DocumentManagerProps {
  storageBackend: 'local' | 's3' | 'azure';
  maxFileSize: number;
  allowedTypes: string[];
  enableVersioning: boolean;
  enableEncryption: boolean;
}

// Features:
// - File upload/download
// - Folder structure
// - Metadata management
// - Full-text search
// - Access control
```

#### Audit Trail Viewer
```typescript
interface AuditTrailProps {
  retentionDays: number;
  exportFormats: ('csv' | 'json' | 'pdf')[];
  complianceMode?: 'GDPR' | 'HIPAA' | 'SOC2';
}

// Features:
// - Activity timeline
// - Advanced filtering
// - Compliance reports
// - Anomaly detection
// - Data retention policies
```

### Communication Service Components (Port 8003)

#### Notification System
```typescript
interface NotificationSystemProps {
  channels: NotificationChannel[];
  templates: NotificationTemplate[];
  schedulingEnabled: boolean;
  analyticsEnabled: boolean;
}

// Features:
// - Multi-channel delivery
// - Template management
// - Batch notifications
// - Delivery tracking
// - A/B testing
```

#### Real-time Messaging
```typescript
interface MessagingProps {
  transport: 'websocket' | 'sse' | 'polling';
  encryption: boolean;
  maxMessageSize: number;
  enablePresence: boolean;
}

// Features:
// - WebSocket communication
// - Message persistence
// - Group chats
// - File sharing
// - Message search
```

### Workflow Intelligence Service Components (Port 8004)

#### Process Designer
```typescript
interface ProcessDesignerProps {
  nodeTypes: NodeType[];
  allowParallel: boolean;
  enableConditionals: boolean;
  aiAssisted: boolean;
}

// Features:
// - Visual workflow builder
// - Node configuration
// - Condition editor
// - Process templates
// - Simulation mode
```

#### Analytics Dashboard
```typescript
interface AnalyticsDashboardProps {
  metrics: Metric[];
  refreshRate: number;
  exportEnabled: boolean;
  aiInsights: boolean;
}

// Features:
// - Custom KPIs
// - Real-time updates
// - Predictive analytics
// - Anomaly detection
// - Report scheduling
```

## Implementation Guidelines

### Development Workflow

#### 1. Component Development Process
```bash
# 1. Generate component scaffold
pnpm generate:component MyComponent

# 2. Develop component
cd packages/shared-ui/src/components/MyComponent

# 3. Write tests
pnpm test:unit MyComponent

# 4. Create Storybook stories
pnpm storybook

# 5. Visual regression testing
pnpm test:visual MyComponent

# 6. Build and publish
pnpm build:component MyComponent
```

#### 2. Service Integration Pattern
```typescript
// Example: Cross-service integration
import { useKongGateway } from '@shared-utils/api';

export const useUserDocuments = (userId: string) => {
  const gateway = useKongGateway();
  
  return useQuery({
    queryKey: ['user-documents', userId],
    queryFn: async () => {
      // Get user details
      const user = await gateway.identity.users.get(userId);
      
      // Get user's documents
      const documents = await gateway.content.documents.list({
        ownerId: userId,
        organizationId: user.organizationId
      });
      
      // Get document analytics
      const analytics = await gateway.workflow.analytics.getDocumentMetrics({
        documentIds: documents.map(d => d.id)
      });
      
      return { user, documents, analytics };
    }
  });
};
```

### State Management Architecture

```typescript
// Global state with Zustand
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface AppState {
  // Identity Service state
  user: User | null;
  organization: Organization | null;
  permissions: Permission[];
  
  // Content Service state
  documents: Document[];
  searchResults: SearchResult[];
  uploadProgress: Record<string, number>;
  
  // Communication Service state
  notifications: Notification[];
  unreadCount: number;
  activeChats: Chat[];
  
  // Workflow Service state
  activeWorkflows: Workflow[];
  tasks: Task[];
  aiSuggestions: Suggestion[];
  
  // Actions
  setUser: (user: User) => void;
  addNotification: (notification: Notification) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    persist(
      (set) => ({
        // Initial state
        user: null,
        organization: null,
        permissions: [],
        documents: [],
        searchResults: [],
        uploadProgress: {},
        notifications: [],
        unreadCount: 0,
        activeChats: [],
        activeWorkflows: [],
        tasks: [],
        aiSuggestions: [],
        
        // Actions
        setUser: (user) => set({ user }),
        addNotification: (notification) => 
          set((state) => ({ 
            notifications: [...state.notifications, notification],
            unreadCount: state.unreadCount + 1
          })),
        updateTask: (taskId, updates) =>
          set((state) => ({
            tasks: state.tasks.map(task =>
              task.id === taskId ? { ...task, ...updates } : task
            )
          }))
      }),
      {
        name: 'app-storage',
        partialize: (state) => ({ user: state.user, organization: state.organization })
      }
    )
  )
);
```

### Error Handling Strategy

```typescript
// Centralized error handling
export class ServiceError extends Error {
  constructor(
    public service: 'identity' | 'content' | 'communication' | 'workflow',
    public code: string,
    public statusCode: number,
    message: string,
    public details?: any
  ) {
    super(message);
    this.name = 'ServiceError';
  }
}

// Error boundary component
export class ServiceErrorBoundary extends React.Component<Props, State> {
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    if (error instanceof ServiceError) {
      // Log to monitoring service
      logger.error({
        service: error.service,
        code: error.code,
        message: error.message,
        details: error.details,
        stack: errorInfo.componentStack
      });
      
      // Show user-friendly error
      toast.error(`Service ${error.service} is temporarily unavailable`);
    }
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback onRetry={this.retry} />;
    }
    return this.props.children;
  }
}
```

### Performance Optimization

```typescript
// Request batching for multiple service calls
export const batchServiceRequests = async (requests: ServiceRequest[]) => {
  const batches = groupBy(requests, 'service');
  
  const results = await Promise.all(
    Object.entries(batches).map(async ([service, batch]) => {
      const response = await fetch(`/api/${service}/batch`, {
        method: 'POST',
        body: JSON.stringify(batch)
      });
      return response.json();
    })
  );
  
  return flatten(results);
};

// Optimistic updates
export const useOptimisticUpdate = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: updateResource,
    onMutate: async (newData) => {
      await queryClient.cancelQueries({ queryKey: ['resource'] });
      const previousData = queryClient.getQueryData(['resource']);
      queryClient.setQueryData(['resource'], newData);
      return { previousData };
    },
    onError: (err, newData, context) => {
      queryClient.setQueryData(['resource'], context.previousData);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['resource'] });
    }
  });
};
```

### Security Implementation

```typescript
// JWT refresh token management
export class TokenManager {
  private refreshTimer?: NodeJS.Timeout;
  
  async initializeTokens(accessToken: string, refreshToken: string) {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    this.scheduleTokenRefresh();
  }
  
  private scheduleTokenRefresh() {
    const token = this.getAccessToken();
    if (!token) return;
    
    const payload = jwt.decode(token) as JWTPayload;
    const expiresIn = payload.exp * 1000 - Date.now();
    const refreshTime = expiresIn - 60000; // Refresh 1 minute before expiry
    
    this.refreshTimer = setTimeout(() => {
      this.refreshAccessToken();
    }, refreshTime);
  }
  
  async refreshAccessToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) throw new Error('No refresh token');
    
    const response = await fetch('/api/identity/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken })
    });
    
    const { accessToken } = await response.json();
    localStorage.setItem('access_token', accessToken);
    this.scheduleTokenRefresh();
  }
}
```

## Development Environment

### Docker Compose Configuration

```yaml
# infrastructure/docker/docker-compose.yml
version: '3.8'

services:
  # Databases
  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: saas_user
      POSTGRES_PASSWORD: saas_pass
      POSTGRES_DB: saas_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Kong API Gateway
  kong:
    image: kong:3.4
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: postgres
      KONG_PG_USER: saas_user
      KONG_PG_PASSWORD: saas_pass
    ports:
      - "8000:8000"  # Proxy port
      - "8001:8001"  # Admin API
    depends_on:
      - postgres

  # Microservices
  identity-service:
    build: ./services/identity
    ports:
      - "8001:8001"
    environment:
      DATABASE_URL: postgresql://saas_user:saas_pass@postgres/identity_db
      REDIS_URL: redis://redis:6379
      JWT_SECRET: ${JWT_SECRET}
    depends_on:
      - postgres
      - redis

  content-service:
    build: ./services/content
    ports:
      - "8002:8002"
    environment:
      DATABASE_URL: postgresql://saas_user:saas_pass@postgres/content_db
      REDIS_URL: redis://redis:6379
      STORAGE_BACKEND: local
    volumes:
      - content_storage:/app/storage
    depends_on:
      - postgres
      - redis

  communication-service:
    build: ./services/communication
    ports:
      - "8003:8003"
    environment:
      DATABASE_URL: postgresql://saas_user:saas_pass@postgres/comm_db
      REDIS_URL: redis://redis:6379
      SMTP_HOST: ${SMTP_HOST}
      SMTP_PORT: ${SMTP_PORT}
    depends_on:
      - postgres
      - redis

  workflow-service:
    build: ./services/workflow
    ports:
      - "8004:8004"
    environment:
      DATABASE_URL: postgresql://saas_user:saas_pass@postgres/workflow_db
      REDIS_URL: redis://redis:6379
      AI_API_KEY: ${AI_API_KEY}
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
  content_storage:
```

### Environment Variables

```bash
# .env.example

# General
NODE_ENV=development
APP_URL=http://localhost:3000

# Database
DATABASE_URL=postgresql://saas_user:saas_pass@localhost/saas_db
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRY=15m
REFRESH_TOKEN_EXPIRY=7d

# Services
IDENTITY_SERVICE_URL=http://localhost:8001
CONTENT_SERVICE_URL=http://localhost:8002
COMMUNICATION_SERVICE_URL=http://localhost:8003
WORKFLOW_SERVICE_URL=http://localhost:8004

# Kong Gateway
KONG_ADMIN_URL=http://localhost:8001
KONG_PROXY_URL=http://localhost:8000

# Storage
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=saas-hub-storage
AWS_REGION=us-east-1

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# SMS
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# AI Services
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Monitoring
SENTRY_DSN=your-sentry-dsn
DATADOG_API_KEY=your-datadog-key

# Feature Flags
ENABLE_AI_FEATURES=true
ENABLE_ADVANCED_ANALYTICS=true
ENABLE_BETA_FEATURES=false
```

### Package.json Scripts

```json
{
  "name": "saas-hub",
  "version": "1.0.0",
  "private": true,
  "workspaces": [
    "packages/*",
    "apps/spa/*",
    "apps/wap/*",
    "services/*"
  ],
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test",
    "test:e2e": "turbo run test:e2e",
    "test:visual": "turbo run test:visual",
    "lint": "turbo run lint",
    "format": "prettier --write \"**/*.{ts,tsx,md,json}\"",
    "clean": "turbo run clean && rm -rf node_modules",
    "generate:component": "plop component",
    "generate:service": "plop service",
    "generate:spa-app": "plop spa-app",
    "generate:wap-app": "plop wap-app",
    "migrate": "turbo run migrate",
    "seed": "turbo run seed",
    "docker:up": "docker-compose up -d",
    "docker:down": "docker-compose down",
    "docker:logs": "docker-compose logs -f",
    "storybook": "turbo run storybook",
    "analyze": "turbo run analyze",
    "release": "changeset publish"
  },
  "devDependencies": {
    "@changesets/cli": "^2.27.0",
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint": "^8.50.0",
    "eslint-config-prettier": "^9.0.0",
    "husky": "^8.0.0",
    "lint-staged": "^15.0.0",
    "plop": "^4.0.0",
    "prettier": "^3.0.0",
    "turbo": "^1.11.0",
    "typescript": "^5.3.0"
  }
}
```

## Deployment Strategy

### Production Build Process

```bash
#!/bin/bash
# tools/scripts/deploy.sh

# Build all services and apps
echo "Building services..."
docker build -t saas-hub/identity:$VERSION ./services/identity
docker build -t saas-hub/content:$VERSION ./services/content
docker build -t saas-hub/communication:$VERSION ./services/communication
docker build -t saas-hub/workflow:$VERSION ./services/workflow

echo "Building frontend apps..."
pnpm build:apps

# Run tests
echo "Running tests..."
pnpm test
pnpm test:e2e

# Push to registry
echo "Pushing to registry..."
docker push saas-hub/identity:$VERSION
docker push saas-hub/content:$VERSION
docker push saas-hub/communication:$VERSION
docker push saas-hub/workflow:$VERSION

# Deploy to Kubernetes
echo "Deploying to Kubernetes..."
kubectl apply -k infrastructure/kubernetes/overlays/production

# Run database migrations
echo "Running migrations..."
kubectl exec -it deployment/identity -- python manage.py migrate
kubectl exec -it deployment/content -- python manage.py migrate
kubectl exec -it deployment/workflow -- python manage.py migrate

echo "Deployment complete!"
```

### Kubernetes Configuration

```yaml
# infrastructure/kubernetes/base/identity/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: identity-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: identity
  template:
    metadata:
      labels:
        app: identity
    spec:
      containers:
      - name: identity
        image: saas-hub/identity:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: identity-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'pnpm'
      - run: pnpm install
      - run: pnpm test
      - run: pnpm lint
      - run: pnpm build

  visual-regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: pnpm/action-setup@v2
      - run: pnpm install
      - run: pnpm test:visual
      - uses: chromaui/action@v1
        with:
          projectToken: ${{ secrets.CHROMATIC_PROJECT_TOKEN }}

  deploy:
    needs: [test, visual-regression]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Build and push Docker images
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          ./tools/scripts/build-and-push.sh
      - name: Deploy to Kubernetes
        run: |
          echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig
          kubectl apply -k infrastructure/kubernetes/overlays/production
      - name: Notify deployment
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Deployment to production completed'
        if: always()
```

## Monitoring and Observability

### Logging Strategy

```typescript
// packages/shared-utils/src/logging/logger.ts
import winston from 'winston';
import { Sentry } from '@sentry/node';

export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.json(),
  defaultMeta: { 
    service: process.env.SERVICE_NAME,
    environment: process.env.NODE_ENV 
  },
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// Sentry integration for error tracking
export const captureError = (error: Error, context?: any) => {
  logger.error(error.message, { error, context });
  Sentry.captureException(error, { extra: context });
};
```

### Performance Monitoring

```typescript
// packages/shared-utils/src/monitoring/performance.ts
export class PerformanceMonitor {
  private metrics: Map<string, number[]> = new Map();
  
  startTimer(operation: string): () => void {
    const start = performance.now();
    
    return () => {
      const duration = performance.now() - start;
      this.recordMetric(operation, duration);
      
      // Send to monitoring service
      if (duration > 1000) {
        logger.warn(`Slow operation: ${operation} took ${duration}ms`);
      }
    };
  }
  
  recordMetric(name: string, value: number) {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }
    this.metrics.get(name)!.push(value);
    
    // Send to DataDog/New Relic
    sendMetric(name, value);
  }
  
  getStats(name: string) {
    const values = this.metrics.get(name) || [];
    return {
      count: values.length,
      mean: mean(values),
      median: median(values),
      p95: percentile(values, 95),
      p99: percentile(values, 99)
    };
  }
}
```

## Testing Strategy

### Unit Testing

```typescript
// Example unit test
import { render, screen, fireEvent } from '@testing-library/react';
import { Dashboard } from '@shared-ui/components/Dashboard';

describe('Dashboard Component', () => {
  it('should render widgets in correct positions', () => {
    const widgets = [
      { id: '1', type: 'chart', position: { x: 0, y: 0 } },
      { id: '2', type: 'metric', position: { x: 1, y: 0 } }
    ];
    
    render(<Dashboard widgets={widgets} />);
    
    expect(screen.getByTestId('widget-1')).toBeInTheDocument();
    expect(screen.getByTestId('widget-2')).toBeInTheDocument();
  });
  
  it('should handle widget drag and drop', async () => {
    const onLayoutChange = jest.fn();
    render(<Dashboard widgets={[]} onLayoutChange={onLayoutChange} />);
    
    // Simulate drag and drop
    const widget = screen.getByTestId('widget-1');
    fireEvent.dragStart(widget);
    fireEvent.drop(screen.getByTestId('drop-zone-2'));
    
    expect(onLayoutChange).toHaveBeenCalledWith(
      expect.objectContaining({
        widgetId: '1',
        newPosition: { x: 2, y: 0 }
      })
    );
  });
});
```

### Integration Testing

```typescript
// Example integration test
import { setupServer } from 'msw/node';
import { rest } from 'msw';
import { renderHook, waitFor } from '@testing-library/react';
import { useUserDocuments } from '@shared-utils/hooks';

const server = setupServer(
  rest.get('/api/identity/users/:id', (req, res, ctx) => {
    return res(ctx.json({ id: req.params.id, name: 'John Doe' }));
  }),
  rest.get('/api/content/documents', (req, res, ctx) => {
    return res(ctx.json([
      { id: '1', name: 'Document 1' },
      { id: '2', name: 'Document 2' }
    ]));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test('fetches user documents with analytics', async () => {
  const { result } = renderHook(() => useUserDocuments('user-1'));
  
  await waitFor(() => {
    expect(result.current.data).toEqual({
      user: { id: 'user-1', name: 'John Doe' },
      documents: [
        { id: '1', name: 'Document 1' },
        { id: '2', name: 'Document 2' }
      ],
      analytics: expect.any(Object)
    });
  });
});
```

### E2E Testing

```typescript
// Example E2E test with Playwright
import { test, expect } from '@playwright/test';

test.describe('User Journey: Document Upload', () => {
  test('should upload and search for a document', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'password');
    await page.click('button[type="submit"]');
    
    // Navigate to documents
    await page.click('a[href="/documents"]');
    
    // Upload document
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles('test-document.pdf');
    
    // Wait for upload to complete
    await expect(page.locator('.upload-progress')).toHaveText('100%');
    
    // Search for document
    await page.fill('[placeholder="Search documents..."]', 'test-document');
    await page.keyboard.press('Enter');
    
    // Verify document appears in results
    await expect(page.locator('.document-card')).toContainText('test-document.pdf');
  });
});
```

## Conclusion

This architecture provides a scalable, maintainable foundation for building multiple SaaS applications with shared components and microservices. The modular design allows for independent development and deployment of services while maintaining consistency through shared UI components and standardized communication patterns.

Key benefits:
- **Reusability**: Shared components reduce development time
- **Scalability**: Microservices architecture allows independent scaling
- **Maintainability**: Clear separation of concerns and modular structure
- **Flexibility**: Support for both SPA and WAP applications
- **Security**: Centralized authentication and authorization
- **Observability**: Comprehensive monitoring and logging

For questions or support, please refer to the documentation in the `/docs` folder or contact the development team.
