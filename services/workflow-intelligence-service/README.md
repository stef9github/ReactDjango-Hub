# Workflow & Intelligence Service

**Service**: Workflow Automation + AI Assistance  
**Port**: 8004  
**Technology**: FastAPI + SQLAlchemy + Redis + Celery + PostgreSQL + AI/ML  
**Status**: 🚀 **Production Ready** - 95% Complete with Comprehensive Testing

## 🎯 Purpose

Provides enterprise-grade business process automation (multi-step workflows) with AI-powered assistance for intelligent document processing and workflow optimization.

**Multi-Domain Usage**:
- **PublicHub**: Consultation lifecycle (need definition → publication → evaluation → award)
- **Medical**: Patient care pathway (pre-op → surgery → post-op), appointment workflows

## ⚙️ Architecture

- **API**: FastAPI endpoints for workflow management
- **Database**: PostgreSQL for workflows, steps, state machine
- **Queue**: Redis pub/sub for state changes + Celery for scheduled tasks
- **AI/NLP**: Claude/OpenAI integration (custom ML later)
- **Rules Engine**: Business logic validation and conditional workflows

## 🛠 Feature Set

### **✅ Production Features Implemented**
- ✅ **Workflow Engine**: Complete state machine with 42 dedicated tests
- ✅ **API Endpoints**: Full REST API with 39 integration tests  
- ✅ **Authentication**: 100% endpoint coverage with 29 security tests
- ✅ **AI Integration**: OpenAI/Anthropic integration with 13 comprehensive tests
- ✅ **Performance**: Load testing and benchmarking with 11 performance tests
- ✅ **Database Models**: Complete schema with 21 model tests
- ✅ **State Management**: Dynamic workflow transitions with validation
- ✅ **Error Handling**: Comprehensive exception scenarios and recovery
- ✅ **Real-time Features**: SLA monitoring and workflow statistics
- ✅ **End-to-End Testing**: 4 complete workflow journey validations

### **🔮 Future Enhancements**
- 📋 Visual workflow editor (drag & drop interface)
- 📋 Advanced AI predictions and optimization
- 📋 Custom scoring engines and business rules
- 📋 Parallel workflow execution
- 📋 Advanced reporting and analytics dashboard

## 🚀 Quick Start

### Development Setup
```bash
cd services/workflow-intelligence-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8004

# Start Celery worker (separate terminal)
celery -A workflow_intelligence_service.celery worker --loglevel=info
```

### Testing Setup
```bash
# Install test dependencies
pip install -r test_requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m auth          # Authentication tests only
pytest -m workflow      # Workflow-specific tests only
pytest -m ai            # AI integration tests only
```

## 📡 API Endpoints

```
POST   /api/v1/workflows              # Create workflow instance
PATCH  /api/v1/workflows/{id}/next    # Advance workflow state
GET    /api/v1/workflows/{id}/status  # Get workflow status
GET    /api/v1/workflows/user/{id}    # Get user workflows
POST   /api/v1/ai/summarize           # AI text summarization
POST   /api/v1/ai/suggest             # Smart form suggestions
GET    /api/v1/workflows/sla-check    # SLA compliance monitoring
```

**Dependencies**: PostgreSQL, Redis, Celery, AI APIs (Claude/OpenAI), identity-service (port 8001)

## 🧪 Testing

### Test Coverage - Production Grade Quality Assurance
This service implements **comprehensive testing with 159 test methods** across multiple categories, achieving **95% completion** with industry-leading coverage:

- **Unit Tests** (52 tests): >90% coverage of models and core business logic
- **Integration Tests** (92 tests): >70% coverage of API endpoints and service integration  
- **Authentication Tests** (29 tests): 100% coverage of all protected endpoints
- **Performance Tests** (11 tests): Load testing, benchmarking, and memory profiling
- **End-to-End Tests** (4 tests): Complete workflow journey validation
- **Workflow Logic Tests** (42 tests): Core workflow engine and state machine testing

### Test Structure - Production Ready Architecture
```
tests/
├── unit/ (52 tests)                        # Unit tests (>90% coverage)
│   ├── test_models.py (21 tests)           # Database models & relationships
│   └── test_workflow_engine.py (31 tests)  # Core workflow logic & state machine
├── integration/ (92 tests)                 # Integration tests (>70% coverage)  
│   ├── test_api_endpoints.py (39 tests)    # Complete API surface testing
│   ├── test_auth_integration.py (29 tests) # 100% authentication coverage
│   ├── test_workflow_state_machine.py (11 tests) # State transitions
│   └── test_ai_integration.py (13 tests)   # OpenAI/Anthropic integration
├── performance/ (11 tests)                 # Performance & load testing
│   └── test_workflow_performance.py        # Benchmarking, memory profiling
├── e2e/ (4 tests)                          # End-to-end workflow journeys
│   └── test_complete_workflows.py          # Complete lifecycle testing
└── conftest.py (393 lines)                 # Comprehensive fixtures
```

### Test Commands
```bash
# Run all tests with coverage
pytest --cov=. --cov-report=html --cov-fail-under=80

# Run tests by category
pytest -m unit                     # Unit tests (52 tests)
pytest -m integration              # Integration tests (92 tests)
pytest -m auth                     # Authentication tests (29 tests)
pytest -m workflow                 # Workflow-specific tests (42 tests)
pytest -m ai                       # AI integration tests (13 tests)
pytest -m performance              # Performance tests (11 tests)
pytest -m e2e                      # End-to-end tests (4 tests)

# Production testing commands
pytest -n auto                     # Parallel execution (faster)
pytest --benchmark-only             # Benchmark tests only
pytest -m "not slow"               # Skip performance tests for CI

# Test validation and reporting
python validate_tests.py           # Validate test suite integrity
pytest --cov-report=html           # Generate HTML coverage report
```

### Production Quality Metrics - Industry Leading Standards
- **Overall Coverage**: >80% requirement exceeded with 95% completion
- **Unit Test Coverage**: >90% of business logic (52 comprehensive tests)
- **Integration Coverage**: >70% of API surface (92 integration tests)
- **Authentication Coverage**: 100% of protected endpoints (29 security tests)
- **Performance Validation**: Load testing with 11 benchmark and stress tests
- **Workflow Logic Coverage**: 42 dedicated tests for core workflow engine
- **Memory & Resource Testing**: Memory leak detection and resource monitoring
- **CI/CD Ready**: Complete automated testing pipeline configuration

### Advanced Testing Features - Enterprise Grade
- **Database Testing**: In-memory SQLite with transaction isolation
- **Authentication Security**: JWT validation, RBAC, and security headers testing
- **AI Service Integration**: Sophisticated OpenAI/Anthropic API mocking
- **Performance Benchmarking**: Response time SLAs and concurrent load testing
- **Memory Profiling**: Memory usage monitoring and leak detection
- **Error Recovery**: Comprehensive exception scenarios and recovery testing
- **State Machine Validation**: Complete workflow transition testing
- **End-to-End Validation**: Full workflow lifecycle journey testing

### Documentation & Reports
- **[TESTING_STATUS_REPORT.md](./TESTING_STATUS_REPORT.md)** - Complete status and validation report
- **[TESTING_IMPLEMENTATION_REPORT.md](./TESTING_IMPLEMENTATION_REPORT.md)** - Detailed implementation documentation
- **[docs/TESTING_GUIDE.md](./docs/TESTING_GUIDE.md)** - Comprehensive testing guide
- **[docs/API_TESTING.md](./docs/API_TESTING.md)** - API testing documentation