# Content Service - Technical Specifications

## 📐 **Architecture Overview**

### **Service Architecture Pattern**
```
┌─────────────────────────────────────────────────────────────┐
│                    Content Service API                      │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │   Upload    │  │   Search     │  │     Processing      │ │
│  │   Manager   │  │   Engine     │  │     Pipeline        │ │
│  └─────────────┘  └──────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
            │                    │                    │
    ┌───────▼─────────┐  ┌──────▼──────┐    ┌────────▼─────────┐
    │  File Storage   │  │ Search Index │    │ Processing Queue │
    │   (Local/S3)    │  │ (PostgreSQL) │    │    (Redis)      │
    └─────────────────┘  └─────────────────┘ └──────────────────┘
            │                    │                    │
    ┌───────▼─────────────────────▼──────────────────▼─────────┐
    │              PostgreSQL Database                         │
    │     Documents │ Versions │ Audit │ Users │ Permissions   │
    └─────────────────────────────────────────────────────────┘
```

### **Technology Stack**

#### **Core Framework**
- **FastAPI 0.104+**: High-performance async web framework
- **Python 3.11+**: Latest stable Python with performance improvements
- **Uvicorn**: ASGI server for production deployment
- **Pydantic v2**: Data validation and serialization

#### **Database Layer**
- **PostgreSQL 14+**: Primary database with JSON support
- **SQLAlchemy 2.0+**: Modern async ORM with type safety
- **Asyncpg**: High-performance async PostgreSQL driver
- **Alembic**: Database migrations management

#### **Caching & Messaging**
- **Redis 7+**: Caching and job queue
- **aioredis**: Async Redis client
- **Celery** (Optional): Advanced task queue for complex processing

#### **File Processing**
- **python-magic**: File type detection
- **PyPDF2**: PDF text extraction
- **python-docx**: Word document processing  
- **Pillow (PIL)**: Image processing and thumbnails
- **pytesseract**: OCR text extraction

#### **Authentication & Security**
- **JWT**: Token-based authentication
- **httpx**: HTTP client for identity service integration
- **cryptography**: File encryption and hashing
- **python-multipart**: File upload handling

---

## 🗃️ **Database Schema Design**

### **Core Tables**

#### **Documents Table**
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL CHECK (file_size > 0),
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    storage_path TEXT NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ownership & Organization
    created_by UUID NOT NULL,
    organization_id UUID NOT NULL,
    
    -- Status & Classification
    status document_status DEFAULT 'active',
    document_type VARCHAR(50),
    classification VARCHAR(20) DEFAULT 'internal',
    
    -- Searchable content & metadata
    extracted_text TEXT,
    search_vector tsvector,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Constraints
    CONSTRAINT valid_content_type CHECK (content_type ~ '^[a-z]+/[a-z0-9][a-z0-9!#$&\-\^]*$'),
    CONSTRAINT valid_status CHECK (status IN ('active', 'processing', 'error', 'archived', 'deleted'))
);

-- Indexes
CREATE INDEX idx_documents_org_created ON documents(organization_id, created_at DESC);
CREATE INDEX idx_documents_created_by ON documents(created_by);
CREATE INDEX idx_documents_type ON documents(document_type) WHERE document_type IS NOT NULL;
CREATE INDEX idx_documents_search ON documents USING GIN(search_vector);
CREATE INDEX idx_documents_metadata ON documents USING GIN(metadata);
CREATE INDEX idx_documents_status ON documents(status) WHERE status != 'active';
```

#### **Document Versions Table**
```sql
CREATE TABLE document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    
    -- Version content
    filename VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID NOT NULL,
    change_summary TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Ensure version uniqueness per document
    UNIQUE(document_id, version_number)
);

CREATE INDEX idx_versions_document ON document_versions(document_id, version_number DESC);
```

#### **Document Permissions Table**
```sql
CREATE TABLE document_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Permission target (user or role)
    user_id UUID,
    role_name VARCHAR(50),
    
    -- Permissions
    can_read BOOLEAN DEFAULT false,
    can_write BOOLEAN DEFAULT false,
    can_delete BOOLEAN DEFAULT false,
    can_share BOOLEAN DEFAULT false,
    
    -- Metadata
    granted_by UUID NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT permission_target_check CHECK (
        (user_id IS NOT NULL AND role_name IS NULL) OR 
        (user_id IS NULL AND role_name IS NOT NULL)
    ),
    CONSTRAINT permission_granted CHECK (can_read OR can_write OR can_delete OR can_share)
);

CREATE INDEX idx_permissions_document ON document_permissions(document_id);
CREATE INDEX idx_permissions_user ON document_permissions(user_id) WHERE user_id IS NOT NULL;
```

#### **Audit Trail Table**
```sql
CREATE TABLE document_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    
    -- Action details
    action audit_action NOT NULL,
    resource_type VARCHAR(50) DEFAULT 'document',
    resource_id UUID,
    
    -- User context
    user_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    session_id VARCHAR(100),
    
    -- Request context
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    
    -- Event details
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Performance tracking
    execution_time_ms INTEGER
);

-- Partitioning by month for performance
CREATE TABLE document_audit_y2024m01 PARTITION OF document_audit 
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Indexes
CREATE INDEX idx_audit_document ON document_audit(document_id, created_at DESC);
CREATE INDEX idx_audit_user ON document_audit(user_id, created_at DESC);
CREATE INDEX idx_audit_org ON document_audit(organization_id, created_at DESC);
CREATE INDEX idx_audit_action ON document_audit(action, created_at DESC);
```

#### **Processing Jobs Table**
```sql
CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Job details
    job_type processing_job_type NOT NULL,
    status job_status DEFAULT 'pending',
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    
    -- Processing details
    processor_name VARCHAR(100),
    processor_version VARCHAR(20),
    config JSONB DEFAULT '{}'::jsonb,
    
    -- Results
    result JSONB,
    error_message TEXT,
    error_details JSONB,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Retry logic
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_jobs_document ON processing_jobs(document_id);
CREATE INDEX idx_jobs_status ON processing_jobs(status, priority DESC, created_at);
CREATE INDEX idx_jobs_retry ON processing_jobs(next_retry_at) WHERE status = 'failed' AND retry_count < max_retries;
```

### **Custom Types**
```sql
-- Enums for type safety
CREATE TYPE document_status AS ENUM ('active', 'processing', 'error', 'archived', 'deleted');
CREATE TYPE audit_action AS ENUM ('create', 'read', 'update', 'delete', 'share', 'unshare', 'download', 'process');
CREATE TYPE processing_job_type AS ENUM ('ocr', 'thumbnail', 'metadata_extraction', 'classification', 'virus_scan');
CREATE TYPE job_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
```

---

## 🔌 **API Design Specifications**

### **RESTful API Endpoints**

#### **Document Management**
```python
# Upload document
POST /api/v1/documents
Content-Type: multipart/form-data
Body: {
    "file": <binary>,
    "metadata": {
        "title": "string",
        "description": "string",
        "tags": ["string"],
        "classification": "public|internal|confidential|restricted"
    }
}
Response: DocumentResponse

# List documents with filtering and pagination
GET /api/v1/documents
Query Parameters:
    - limit: int = 20
    - offset: int = 0
    - search: str = None
    - document_type: str = None
    - created_after: datetime = None
    - created_before: datetime = None
    - order_by: str = "created_at"
    - order_dir: str = "desc"
Response: DocumentListResponse

# Get document details
GET /api/v1/documents/{document_id}
Response: DocumentDetailResponse

# Update document metadata
PUT /api/v1/documents/{document_id}
Body: DocumentUpdateRequest
Response: DocumentResponse

# Delete document (soft delete)
DELETE /api/v1/documents/{document_id}
Response: DeleteResponse
```

#### **File Operations**
```python
# Download document
GET /api/v1/documents/{document_id}/download
Response: StreamingResponse (file content)

# Get document thumbnail
GET /api/v1/documents/{document_id}/thumbnail
Query Parameters:
    - size: str = "medium" (small|medium|large)
Response: StreamingResponse (image)

# Get document preview
GET /api/v1/documents/{document_id}/preview
Response: PreviewResponse
```

#### **Processing & OCR**
```python
# Trigger document processing
POST /api/v1/documents/{document_id}/process
Body: {
    "processors": ["ocr", "thumbnail", "classification"],
    "priority": 5,
    "webhook_url": "https://example.com/webhook"
}
Response: ProcessingJobResponse

# Get processing status
GET /api/v1/documents/{document_id}/processing
Response: ProcessingStatusResponse

# Get extracted text
GET /api/v1/documents/{document_id}/text
Response: ExtractedTextResponse
```

#### **Search & Discovery**
```python
# Full-text search
GET /api/v1/search
Query Parameters:
    - q: str (search query)
    - filters: dict = {}
    - limit: int = 20
    - offset: int = 0
    - highlight: bool = true
Response: SearchResponse

# Semantic search
POST /api/v1/search/semantic
Body: {
    "query": "string",
    "similarity_threshold": 0.7,
    "limit": 10
}
Response: SemanticSearchResponse

# Search suggestions
GET /api/v1/search/suggestions
Query Parameters:
    - prefix: str
Response: SuggestionResponse
```

### **WebSocket Endpoints**
```python
# Real-time document updates
WS /ws/documents/{document_id}
Messages:
    - document_updated
    - processing_status_changed
    - comment_added
    - annotation_added

# Real-time search
WS /ws/search
Messages:
    - search_results
    - search_suggestions
```

---

## 🔒 **Security Specifications**

### **Authentication & Authorization**

#### **JWT Token Structure**
```json
{
    "sub": "user_uuid",
    "organization_id": "org_uuid",
    "roles": ["admin", "editor", "viewer"],
    "permissions": ["documents:read", "documents:write"],
    "exp": 1672531200,
    "iat": 1672444800,
    "scope": "content-service"
}
```

#### **Permission System**
```python
# Permission levels (hierarchical)
class PermissionLevel(Enum):
    NONE = 0
    READ = 1
    WRITE = 2
    ADMIN = 3
    OWNER = 4

# Resource-based permissions
class ResourcePermission:
    resource_type: str  # "document", "folder", "organization"
    resource_id: str
    permission_level: PermissionLevel
    inherited: bool = False
```

### **File Security**

#### **Upload Validation**
```python
# File validation rules
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg", "image/png", "image/gif",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain", "text/csv"
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_FILES_PER_UPLOAD = 10

# Security scanning
class SecurityScanner:
    def scan_file(self, file_path: str) -> ScanResult:
        # Virus scanning
        # Content validation
        # Malware detection
        pass
```

#### **Encryption**
```python
# File encryption at rest
class FileEncryption:
    algorithm: str = "AES-256-GCM"
    key_rotation_period: timedelta = timedelta(days=90)
    
    def encrypt_file(self, file_data: bytes, key_id: str) -> bytes
    def decrypt_file(self, encrypted_data: bytes, key_id: str) -> bytes
```

---

## ⚡ **Performance Specifications**

### **Response Time Requirements**
- Document upload: < 2s for 10MB files
- Document download: < 500ms time to first byte
- Search queries: < 200ms for simple queries
- OCR processing: < 30s for 10-page PDF
- API health check: < 50ms

### **Throughput Requirements**
- Concurrent uploads: 100 files/second
- Search queries: 1000 queries/second
- Download requests: 500 downloads/second
- Processing jobs: 50 jobs/second

### **Caching Strategy**
```python
# Multi-level caching
class CacheConfiguration:
    # Application cache
    redis_cache = {
        "document_metadata": {"ttl": 3600, "max_size": "100MB"},
        "search_results": {"ttl": 300, "max_size": "50MB"},
        "user_permissions": {"ttl": 1800, "max_size": "20MB"}
    }
    
    # Database query cache
    query_cache = {
        "enabled": True,
        "ttl": 300,
        "max_entries": 1000
    }
    
    # File cache
    file_cache = {
        "thumbnails": {"ttl": 86400, "max_size": "1GB"},
        "processed_text": {"ttl": 3600, "max_size": "500MB"}
    }
```

### **Database Optimization**
```sql
-- Connection pooling
database_pool_config = {
    "min_size": 10,
    "max_size": 50,
    "max_queries": 50000,
    "max_inactive_connection_lifetime": 300
}

-- Query optimization indexes
CREATE INDEX CONCURRENTLY idx_documents_composite 
ON documents(organization_id, status, created_at DESC) 
WHERE status = 'active';

-- Partitioning strategy
CREATE TABLE documents_2024 PARTITION OF documents 
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

---

## 📊 **Monitoring & Observability**

### **Health Check Specification**
```python
class HealthCheck:
    def __init__(self):
        self.checks = [
            DatabaseHealthCheck(),
            RedisHealthCheck(),
            StorageHealthCheck(),
            IdentityServiceHealthCheck(),
            ProcessingQueueHealthCheck()
        ]
    
    async def get_health_status(self) -> HealthStatus:
        # Comprehensive health check
        pass

class HealthStatus:
    service: str
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    uptime: int
    dependencies: Dict[str, str]
    metrics: Dict[str, Union[int, float]]
    checks: List[CheckResult]
```

### **Metrics Collection**
```python
# Performance metrics
class ServiceMetrics:
    request_count: Counter
    request_duration: Histogram
    error_rate: Counter
    active_connections: Gauge
    
    # Business metrics
    documents_uploaded: Counter
    documents_processed: Counter
    search_queries: Counter
    storage_usage: Gauge

# Custom metrics
upload_size_histogram = Histogram('upload_file_size_bytes', 'File upload sizes')
processing_duration = Histogram('processing_duration_seconds', 'Processing time by type')
search_latency = Histogram('search_query_duration_seconds', 'Search query latency')
```

### **Logging Specification**
```python
# Structured logging format
log_format = {
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "service": "content-service",
    "version": "1.0.0",
    "request_id": "uuid",
    "user_id": "uuid",
    "organization_id": "uuid",
    "operation": "document_upload",
    "duration_ms": 1250,
    "status": "success",
    "details": {},
    "trace_id": "uuid"
}
```

---

## 🚀 **Deployment Specifications**

### **Container Configuration**
```dockerfile
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    tesseract-ocr \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Application setup
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Security
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8002
CMD ["python", "main.py"]
```

### **Environment Variables**
```bash
# Service configuration
SERVICE_NAME=content-service
SERVICE_VERSION=1.0.0
SERVICE_PORT=8002
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/content_db
DATABASE_POOL_MIN=10
DATABASE_POOL_MAX=50

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_POOL_MAX=20

# Storage
STORAGE_BACKEND=local  # local|s3|azure
STORAGE_PATH=/app/storage
MAX_FILE_SIZE=104857600  # 100MB

# Processing
OCR_ENABLED=true
TESSERACT_LANG=eng+fra+spa
PROCESSING_WORKERS=4

# Security
JWT_SECRET_KEY=${JWT_SECRET}
ALLOWED_ORIGINS=http://localhost:3000,https://app.example.com
```

### **Resource Requirements**
```yaml
# Kubernetes resource specs
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"

# Horizontal Pod Autoscaler
autoscaling:
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilization: 70
  targetMemoryUtilization: 80
```

---

This technical specification provides the detailed blueprint for implementing a production-ready content management service with enterprise-grade security, performance, and scalability features.