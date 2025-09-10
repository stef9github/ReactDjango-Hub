"""
Comprehensive test fixtures and configuration for content service tests.
"""

import pytest
import asyncio
import tempfile
import uuid
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

# FastAPI and HTTP testing
import httpx
from fastapi.testclient import TestClient
from fastapi import UploadFile

# SQLAlchemy and Database testing
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy_utils import create_database, drop_database, database_exists

# Redis testing
import fakeredis.aioredis

# Application imports
from main import app
from database import Base, get_db_session
from models import Document, DocumentPermission, DocumentShare, DocumentComment
from repositories import DocumentRepository, PermissionRepository, AuditRepository


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
async def test_database_url():
    """Create a test database URL."""
    import uuid
    db_name = f"test_content_service_{uuid.uuid4().hex[:8]}"
    db_url = f"postgresql://postgres:password@localhost:5432/{db_name}"
    
    # Create the test database
    sync_url = db_url.replace("postgresql://", "postgresql://")
    if not database_exists(sync_url):
        create_database(sync_url)
    
    yield f"postgresql+asyncpg://postgres:password@localhost:5432/{db_name}"
    
    # Cleanup: Drop the test database
    if database_exists(sync_url):
        drop_database(sync_url)


@pytest.fixture(scope="session")
async def test_engine(test_database_url):
    """Create a test database engine."""
    engine = create_async_engine(
        test_database_url,
        echo=False,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
            "server_settings": {"application_name": "test_content_service"}
        }
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_get_db_session(db_session):
    """Override the database session dependency."""
    async def _get_test_db_session():
        yield db_session
    
    app.dependency_overrides[get_db_session] = _get_test_db_session
    yield
    del app.dependency_overrides[get_db_session]


# ============================================================================
# HTTP CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async test client for FastAPI app."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest.fixture
def valid_token():
    """Mock valid JWT token."""
    return "valid.jwt.token.12345"


@pytest.fixture
def invalid_token():
    """Mock invalid JWT token."""
    return "invalid.jwt.token"


@pytest.fixture
def expired_token():
    """Mock expired JWT token."""
    return "expired.jwt.token"


@pytest.fixture
def mock_user_data():
    """Mock user data returned by Identity Service."""
    return {
        "user_id": "12345678-1234-5678-9012-123456789012",
        "organization_id": "87654321-4321-8765-2109-876543210987",
        "email": "test@example.com",
        "roles": ["user"],
        "permissions": ["read", "write"],
        "is_verified": True,
        "expires_at": "2025-12-31T23:59:59Z"
    }


@pytest.fixture
def admin_user_data():
    """Mock admin user data."""
    return {
        "user_id": "admin-uuid-1234-5678-9012-123456789012",
        "organization_id": "87654321-4321-8765-2109-876543210987",
        "email": "admin@example.com",
        "roles": ["admin", "user"],
        "permissions": ["read", "write", "delete", "admin"],
        "is_verified": True,
        "expires_at": "2025-12-31T23:59:59Z"
    }


@pytest.fixture
def regular_user_data():
    """Mock regular user data."""
    return {
        "user_id": "user-uuid-1234-5678-9012-123456789012",
        "organization_id": "87654321-4321-8765-2109-876543210987",
        "email": "user@example.com",
        "roles": ["user"],
        "permissions": ["read", "write"],
        "is_verified": True,
        "expires_at": "2025-12-31T23:59:59Z"
    }


@pytest.fixture
def mock_identity_service_success():
    """Mock successful Identity Service response."""
    def _mock_response(user_data):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = user_data
        return mock_response
    return _mock_response


@pytest.fixture
def mock_identity_service_failure():
    """Mock failed Identity Service response."""
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"detail": "Invalid token"}
    return mock_response


# ============================================================================
# FILE SYSTEM FIXTURES
# ============================================================================

@pytest.fixture
def temp_directory():
    """Create a temporary directory for file operations."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield Path(path)
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


@pytest.fixture
def sample_text_file(temp_directory):
    """Create a sample text file for testing."""
    file_path = temp_directory / "sample.txt"
    content = "This is a sample text file for testing.\nIt contains multiple lines.\nAnd some keywords like important, document, test."
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_pdf_file(temp_directory):
    """Create a sample PDF file for testing."""
    file_path = temp_directory / "sample.pdf"
    # Create a minimal PDF content (mock)
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000125 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n191\n%%EOF"
    file_path.write_bytes(pdf_content)
    return file_path


@pytest.fixture
def sample_image_file(temp_directory):
    """Create a sample image file for testing."""
    try:
        from PIL import Image
        file_path = temp_directory / "sample.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(file_path, 'JPEG')
        return file_path
    except ImportError:
        # Fallback: create a fake image file
        file_path = temp_directory / "sample.jpg"
        # JPEG file header
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f'
        file_path.write_bytes(jpeg_header)
        return file_path


@pytest.fixture
def large_file(temp_directory):
    """Create a large file for testing file size limits."""
    file_path = temp_directory / "large_file.txt"
    # Create a 10MB file
    with file_path.open('wb') as f:
        f.write(b'A' * (10 * 1024 * 1024))
    return file_path


@pytest.fixture
def dangerous_filename_file(temp_directory):
    """Create a file with a dangerous filename."""
    safe_path = temp_directory / "safe_name.txt"
    safe_path.write_text("content")
    return safe_path, "../../../etc/passwd"


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis client using fakeredis."""
    return fakeredis.aioredis.FakeRedis()


@pytest.fixture
def mock_file_storage():
    """Mock file storage operations."""
    with patch('aiofiles.open') as mock_open, \
         patch('aiofiles.os.makedirs') as mock_makedirs, \
         patch('aiofiles.os.path.exists') as mock_exists, \
         patch('pathlib.Path.unlink') as mock_unlink:
        
        mock_file = AsyncMock()
        mock_file.read.return_value = b"test file content"
        mock_file.write.return_value = None
        mock_open.return_value.__aenter__.return_value = mock_file
        mock_makedirs.return_value = None
        mock_exists.return_value = True
        
        yield {
            'open': mock_open,
            'makedirs': mock_makedirs,
            'exists': mock_exists,
            'unlink': mock_unlink,
            'file': mock_file
        }


@pytest.fixture
def mock_magic():
    """Mock python-magic library."""
    with patch('magic.from_buffer') as mock_from_buffer:
        mock_from_buffer.return_value = "text/plain"
        yield mock_from_buffer


@pytest.fixture
def mock_processing_queue():
    """Mock processing queue operations."""
    with patch('processing.queue_manager.ProcessingQueueManager') as mock_queue:
        mock_instance = AsyncMock()
        mock_instance.connect.return_value = None
        mock_instance.disconnect.return_value = None
        mock_instance.add_task.return_value = True
        mock_instance.get_queue_stats.return_value = {
            "queue_high_length": 0,
            "queue_normal_length": 0,
            "queue_low_length": 0,
            "processing_count": 0
        }
        mock_queue.return_value = mock_instance
        yield mock_instance


# ============================================================================
# DATABASE MODEL FIXTURES
# ============================================================================

@pytest.fixture
async def sample_document(db_session, mock_user_data) -> Document:
    """Create a sample document in the database."""
    from models import Document
    
    document = Document(
        filename="test_document.pdf",
        original_filename="test_document.pdf",
        content_type="application/pdf",
        file_size=1024,
        file_hash="abc123def456",
        storage_path="/test/path/test_document.pdf",
        created_by=uuid.UUID(mock_user_data["user_id"]),
        organization_id=uuid.UUID(mock_user_data["organization_id"]),
        status="active"
    )
    
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    return document


@pytest.fixture
async def sample_permission(db_session, sample_document, mock_user_data) -> DocumentPermission:
    """Create a sample document permission."""
    permission = DocumentPermission.create_user_permission(
        document_id=sample_document.id,
        user_id=uuid.UUID(mock_user_data["user_id"]),
        granted_by=uuid.UUID(mock_user_data["user_id"]),
        permissions=["read", "write"]
    )
    
    db_session.add(permission)
    await db_session.commit()
    await db_session.refresh(permission)
    return permission


@pytest.fixture
async def sample_comment(db_session, sample_document, mock_user_data):
    """Create a sample document comment."""
    from models import DocumentComment
    
    comment = DocumentComment(
        document_id=sample_document.id,
        author_id=uuid.UUID(mock_user_data["user_id"]),
        content="This is a test comment",
        status="active"
    )
    
    db_session.add(comment)
    await db_session.commit()
    await db_session.refresh(comment)
    return comment


# ============================================================================
# REPOSITORY FIXTURES
# ============================================================================

@pytest.fixture
def document_repository(db_session):
    """Create a document repository instance."""
    return DocumentRepository(db_session)


@pytest.fixture
def permission_repository(db_session):
    """Create a permission repository instance."""
    return PermissionRepository(db_session)


@pytest.fixture
def audit_repository(db_session):
    """Create an audit repository instance."""
    return AuditRepository(db_session)


# ============================================================================
# UPLOAD FILE FIXTURES
# ============================================================================

@pytest.fixture
def mock_upload_file():
    """Create a mock UploadFile for testing."""
    def _create_upload_file(filename: str = "test.txt", content: bytes = b"test content", content_type: str = "text/plain"):
        upload_file = MagicMock(spec=UploadFile)
        upload_file.filename = filename
        upload_file.content_type = content_type
        upload_file.size = len(content)
        upload_file.read = AsyncMock(return_value=content)
        upload_file.seek = AsyncMock(return_value=None)
        upload_file.close = AsyncMock(return_value=None)
        return upload_file
    return _create_upload_file


@pytest.fixture
def valid_upload_files(mock_upload_file):
    """Create various valid upload files for testing."""
    return {
        'text': mock_upload_file("document.txt", b"Sample text content", "text/plain"),
        'pdf': mock_upload_file("document.pdf", b"%PDF-1.4\ntest pdf content", "application/pdf"),
        'image': mock_upload_file("image.jpg", b"\xff\xd8\xff\xe0JFIF", "image/jpeg"),
        'word': mock_upload_file("document.docx", b"PK\x03\x04word content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }


@pytest.fixture
def invalid_upload_files(mock_upload_file):
    """Create various invalid upload files for testing."""
    return {
        'too_large': mock_upload_file("large.txt", b"X" * (100 * 1024 * 1024), "text/plain"),  # 100MB
        'empty': mock_upload_file("empty.txt", b"", "text/plain"),
        'dangerous_ext': mock_upload_file("malware.exe", b"MZ\x90\x00", "application/x-executable"),
        'no_extension': mock_upload_file("noextension", b"content", "text/plain"),
        'dangerous_path': mock_upload_file("../../../etc/passwd", b"root:x:0:0:", "text/plain")
    }


# ============================================================================
# HTTP MOCKING FIXTURES
# ============================================================================

@pytest.fixture
def mock_identity_service():
    """Mock the Identity Service HTTP calls."""
    def _mock_service(user_data=None, status_code=200, exception=None):
        async def mock_post(*args, **kwargs):
            if exception:
                raise exception
            
            mock_response = AsyncMock()
            mock_response.status_code = status_code
            mock_response.json.return_value = user_data or {}
            return mock_response
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = mock_post
            yield mock_client
    
    return _mock_service


# ============================================================================
# PERFORMANCE TESTING FIXTURES
# ============================================================================

@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            self.end_time = time.perf_counter()
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
async def cleanup_after_test(db_session):
    """Automatically cleanup after each test."""
    yield
    # Clean up database
    if db_session:
        await db_session.rollback()


# ============================================================================
# ERROR SIMULATION FIXTURES
# ============================================================================

@pytest.fixture
def simulate_database_error():
    """Simulate database errors for testing."""
    def _simulate_error(error_type="connection"):
        if error_type == "connection":
            return Exception("Database connection failed")
        elif error_type == "integrity":
            from sqlalchemy.exc import IntegrityError
            return IntegrityError("", "", "")
        elif error_type == "timeout":
            from sqlalchemy.exc import TimeoutError
            return TimeoutError("", "", "")
        else:
            return Exception("Unknown database error")
    
    return _simulate_error


@pytest.fixture
def simulate_file_system_error():
    """Simulate file system errors for testing."""
    def _simulate_error(error_type="permission"):
        if error_type == "permission":
            return PermissionError("Permission denied")
        elif error_type == "not_found":
            return FileNotFoundError("File not found")
        elif error_type == "disk_full":
            return OSError("No space left on device")
        else:
            return IOError("File system error")
    
    return _simulate_error


# ============================================================================
# TEST DATA FACTORIES
# ============================================================================

class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_user_data(**overrides):
        """Create test user data with optional overrides."""
        base_data = {
            "user_id": str(uuid.uuid4()),
            "organization_id": str(uuid.uuid4()),
            "email": "test@example.com",
            "roles": ["user"],
            "permissions": ["read", "write"],
            "is_verified": True,
            "expires_at": "2025-12-31T23:59:59Z"
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_document_data(**overrides):
        """Create test document data with optional overrides."""
        base_data = {
            "filename": "test_document.pdf",
            "original_filename": "test_document.pdf",
            "content_type": "application/pdf",
            "file_size": 1024,
            "file_hash": "abc123def456",
            "storage_path": "/test/path/test_document.pdf",
            "status": "active"
        }
        base_data.update(overrides)
        return base_data


@pytest.fixture
def test_data_factory():
    """Provide the test data factory."""
    return TestDataFactory