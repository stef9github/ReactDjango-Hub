# Content Service - Claude Code Agent Configuration

This file provides guidance to Claude Code when working specifically on the **Content Microservice**.

## 🎯 **Service Identity**
- **Service Name**: content-service  
- **Technology**: FastAPI + SQLAlchemy + PostgreSQL + MinIO/S3
- **Port**: 8003
- **Database**: content_service (isolated from other services)
- **Storage**: Object storage for files (MinIO locally, S3 in production)

## 🧠 **Your Exclusive Domain**

You are the **Content Service specialist**. Your responsibilities are:

### **Document Management**
- File upload with validation and virus scanning
- Secure file storage and retrieval
- Document versioning and history
- Metadata extraction and indexing
- Full-text search capabilities

### **File Processing**
- Format conversion (PDF, DOCX, images)
- Thumbnail generation
- Text extraction and OCR
- Compression and optimization
- Chunked uploads for large files

### **Access Control**
- Document-level permissions
- Sharing and collaboration features
- Temporary access links
- Audit trail for all operations
- Organization-based isolation

### **Storage Management**
- Multi-tier storage (hot/cold)
- Quota management per organization
- Automatic archival policies
- CDN integration for distribution
- Backup and disaster recovery

### **Content Analytics**
- Usage statistics and reporting
- Popular content tracking
- Storage usage monitoring
- Access pattern analysis

## 🚫 **Service Boundaries (STRICT)**

### **You CANNOT Modify:**
- Other microservices (identity-service, communication-service, workflow-intelligence-service)
- API Gateway configuration  
- Shared infrastructure code
- Other service databases

### **Integration Only:**
- Call Identity Service for JWT validation
- Send notifications via Communication Service
- Trigger workflows in Workflow Intelligence Service
- Store files in object storage (MinIO/S3)

## 🔧 **Development Commands**

### **Start Development**
```bash
# Start service dependencies
docker-compose -f docker-compose.yml up -d postgres redis minio

# Start FastAPI service
uvicorn main:app --reload --port 8003

# Health check
curl http://localhost:8003/health

# MinIO console (for storage management)
# http://localhost:9001 (default: minioadmin/minioadmin)
```

### **Database Operations**  
```bash
# Initialize Alembic (NEEDED - NOT SET UP YET!)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial content schema"

# Run migrations
alembic upgrade head

# Generate migration SQL
alembic upgrade head --sql
```

### **Testing**
```bash
# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test category
pytest tests/unit/ -v
pytest tests/integration/ -v

# Run with fixtures
pytest tests/ -v --fixtures

# Performance testing
pytest tests/performance/ -v --benchmark-only
```

## 📊 **Service Architecture (NEEDS RESTRUCTURING)**

### **Current Structure (NEEDS IMPROVEMENT)**
```
content-service/
├── main.py                      # FastAPI application (needs refactoring)
├── models.py                    # Database models (needs splitting)
├── database.py                  # Database connection
├── storage.py                   # Storage operations
├── repositories.py              # Data access layer
├── tests/                       # Test suite (incomplete)
├── requirements.txt             # Dependencies
├── test_requirements.txt        # Test dependencies
├── pytest.ini                   # Test configuration
├── Dockerfile                   # Container definition
└── docker-compose.yml          # Local development stack
```

### **Target Structure (TO IMPLEMENT)**
```
content-service/
├── main.py                      # FastAPI application entry
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── documents.py    # Document CRUD endpoints
│   │       ├── upload.py        # Upload handling endpoints
│   │       ├── download.py      # Download/streaming endpoints
│   │       ├── search.py        # Search endpoints
│   │       └── admin.py         # Admin operations
│   ├── core/
│   │   ├── config.py           # Service configuration
│   │   ├── database.py         # Database connection
│   │   ├── security.py         # Auth & permissions
│   │   └── storage.py          # Storage abstraction
│   ├── models/
│   │   ├── document.py         # Document model
│   │   ├── permission.py       # Permission model
│   │   ├── audit.py            # Audit log model
│   │   └── metadata.py         # Metadata models
│   ├── schemas/
│   │   ├── document.py         # Document DTOs
│   │   ├── upload.py           # Upload validation
│   │   └── search.py           # Search parameters
│   ├── services/
│   │   ├── document_service.py # Document operations
│   │   ├── storage_service.py  # Storage operations
│   │   ├── search_service.py   # Search functionality
│   │   ├── permission_service.py # Access control
│   │   └── processing/
│   │       ├── thumbnail.py    # Thumbnail generation
│   │       ├── text_extractor.py # Text extraction
│   │       └── virus_scanner.py  # Virus scanning
│   ├── repositories/
│   │   ├── document_repo.py    # Document data access
│   │   ├── permission_repo.py  # Permission data access
│   │   └── audit_repo.py       # Audit data access
│   └── utils/
│       ├── validators.py       # File validation
│       ├── converters.py       # Format converters
│       └── helpers.py          # Utility functions
├── alembic/                     # Database migrations (TO CREATE)
├── docs/                        # Documentation (TO CREATE)
│   ├── api/                    # API documentation
│   ├── architecture/           # Architecture diagrams
│   └── storage/                # Storage patterns
└── tests/
    ├── unit/                    # Unit tests (TO COMPLETE)
    ├── integration/             # Integration tests (TO CREATE)
    └── e2e/                     # End-to-end tests (TO CREATE)
```

### **Database Models You Manage**
```python
# DOCUMENT TABLES:
- documents                 # Core document records
- document_versions        # Version history
- document_metadata        # Extracted metadata
- document_tags           # Tagging system
- document_comments       # Comments/annotations

# PERMISSION TABLES:
- document_permissions    # Access control lists
- document_shares        # Sharing records
- access_tokens          # Temporary access tokens
- permission_groups      # Permission templates

# STORAGE TABLES:
- storage_locations      # File storage paths
- storage_quotas        # Organization quotas
- storage_metrics       # Usage statistics
- archive_policies      # Archival rules

# AUDIT TABLES:
- audit_logs            # All operations
- download_logs        # Download tracking
- search_logs          # Search history
- access_violations    # Security events
```

## 🔌 **Service Integrations**

### **Storage Configuration**
```python
# MinIO/S3 Configuration
MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "documents"

# S3 Production
AWS_S3_BUCKET = "content-service-prod"
AWS_S3_REGION = "us-east-1"
AWS_CLOUDFRONT_DISTRIBUTION = "xyz123"
```

### **Identity Service Integration**
```python
# Validate JWT and get user context
async def get_user_context(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://identity-service:8001/auth/validate",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()
```

### **Processing Pipeline**
```python
# Document processing workflow
async def process_uploaded_document(document_id: str):
    # 1. Virus scan
    await scan_for_viruses(document_id)
    
    # 2. Extract metadata
    metadata = await extract_metadata(document_id)
    
    # 3. Generate thumbnails
    if is_image(document):
        await generate_thumbnails(document_id)
    
    # 4. Extract text for search
    text = await extract_text(document_id)
    await index_for_search(document_id, text)
    
    # 5. Notify completion
    await notify_upload_complete(document_id)
```

## 🚨 **Critical Issues to Fix**

### **1. Architecture Refactoring (URGENT)**
```bash
# Create proper structure
mkdir -p app/{api/v1,core,models,schemas,services,repositories}

# Move existing code to proper locations
mv models.py app/models/
mv database.py app/core/
mv repositories.py app/repositories/
mv storage.py app/services/storage_service.py
```

### **2. Complete Test Implementation (CRITICAL)**
```python
# tests/unit/test_document_service.py
class TestDocumentService:
    async def test_create_document(self):
        # Test document creation with metadata
        pass
    
    async def test_update_document_version(self):
        # Test versioning system
        pass
    
    async def test_delete_document_cascade(self):
        # Test cascade deletion
        pass

# tests/integration/test_upload_flow.py
class TestUploadFlow:
    async def test_complete_upload_flow(self):
        # Upload -> Scan -> Process -> Store -> Index
        pass
    
    async def test_large_file_chunked_upload(self):
        # Test chunked upload for files >100MB
        pass
```

### **3. Database Migrations (REQUIRED)**
```bash
# Initialize Alembic
alembic init alembic

# Configure alembic.ini
sed -i 's|sqlalchemy.url = .*|sqlalchemy.url = postgresql://user:pass@localhost/content_service|' alembic.ini

# Create initial migration
alembic revision --autogenerate -m "Initial content schema with documents, permissions, audit"
alembic upgrade head
```

### **4. Service Layer Implementation**
```python
# app/services/document_service.py
class DocumentService:
    def __init__(self, db_session: AsyncSession, storage: StorageService):
        self.db = db_session
        self.storage = storage
        self.repo = DocumentRepository(db_session)
    
    async def upload_document(
        self,
        file: UploadFile,
        user_id: str,
        organization_id: str,
        metadata: dict
    ) -> Document:
        # Validate file
        await self.validate_file(file)
        
        # Check quota
        await self.check_quota(organization_id)
        
        # Store file
        storage_path = await self.storage.store(file)
        
        # Create database record
        document = await self.repo.create(
            filename=file.filename,
            storage_path=storage_path,
            user_id=user_id,
            organization_id=organization_id,
            metadata=metadata
        )
        
        # Queue for processing
        await self.queue_for_processing(document.id)
        
        return document
```

## 🎯 **Development Priorities**

### **Week 1: Foundation**
1. ✅ Fix conftest.py (DONE by user)
2. 🔴 Refactor to proper architecture
3. 🔴 Setup Alembic migrations
4. 🔴 Implement service layer

### **Week 2: Core Features**
1. 🔴 Complete document CRUD operations
2. 🔴 Implement permission system
3. 🔴 Add virus scanning
4. 🔴 Setup text extraction

### **Week 3: Testing & Documentation**
1. 🔴 Complete unit tests (80% coverage)
2. 🔴 Add integration tests
3. 🔴 Create API documentation
4. 🔴 Write architecture docs

## 🔍 **Testing Strategy**

### **Unit Tests Required**
```python
# Document Operations
- test_create_document_with_metadata
- test_update_document_version
- test_delete_document_with_permissions
- test_search_documents_by_content
- test_get_document_history

# Storage Operations  
- test_store_file_to_minio
- test_retrieve_file_from_storage
- test_delete_file_from_storage
- test_generate_presigned_url
- test_check_storage_quota

# Permission Checks
- test_user_can_read_document
- test_user_can_write_document
- test_organization_isolation
- test_temporary_access_token
- test_permission_inheritance
```

### **Integration Tests Required**
```python
# Complete Flows
- test_upload_scan_process_store_flow
- test_download_with_permission_check
- test_search_across_organizations
- test_bulk_upload_operation
- test_document_sharing_workflow

# External Services
- test_minio_connection_failure
- test_identity_service_timeout
- test_virus_scanner_integration
- test_text_extraction_service
```

## 📈 **Success Metrics**

### **Performance Targets**
- Upload speed: >10MB/s
- Download speed: >20MB/s
- Search response: <200ms
- Thumbnail generation: <2s
- Virus scan: <5s for 100MB file

### **Quality Targets**
- Test coverage: >80%
- Zero security vulnerabilities
- 99.9% uptime
- <0.01% data loss rate

## 🚨 **Immediate Action Items**

### **1. Fix Architecture (TODAY)**
```bash
# Create proper structure
bash << 'EOF'
mkdir -p app/{api/v1,core,models,schemas,services,repositories,utils}
touch app/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
# Move and refactor existing code
EOF
```

### **2. Implement Core Service (THIS WEEK)**
```python
# app/services/document_service.py
# Implement complete document lifecycle
# - Upload with validation
# - Storage with versioning
# - Permissions with inheritance
# - Search with full-text
```

### **3. Complete Testing (NEXT WEEK)**
```bash
# Create comprehensive tests
touch tests/unit/test_document_service.py
touch tests/unit/test_storage_service.py
touch tests/unit/test_permission_service.py
touch tests/integration/test_upload_flow.py
touch tests/integration/test_search_flow.py
```

## 🛠️ **Code Quality Standards**

### **File Validation**
```python
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.jpg', '.png'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
DANGEROUS_EXTENSIONS = {'.exe', '.dll', '.sh', '.bat'}

async def validate_file(file: UploadFile):
    # Check extension
    # Check MIME type
    # Check file size
    # Scan for malware
    # Validate content
```

### **Error Handling**
```python
class DocumentNotFoundError(Exception):
    pass

class StorageQuotaExceededError(Exception):
    pass

class PermissionDeniedError(Exception):
    pass

class VirusDetectedError(Exception):
    pass
```

---

**📁 You are the Content Service expert. Focus on secure, efficient document management with proper architecture and comprehensive testing.**

**🚨 URGENT: Your service needs significant refactoring. Start with architecture reorganization and service layer implementation.**

**Current Priority: 
1. Refactor to proper architecture (app/ structure)
2. Implement document service layer
3. Complete unit tests for core operations
4. Setup database migrations with Alembic**