# Workflow Intelligence Service - Claude Code Agent Configuration

This file provides guidance to Claude Code when working specifically on the **Workflow Intelligence Microservice**.

## 🎯 **Service Identity**
- **Service Name**: workflow-intelligence-service  
- **Technology**: FastAPI + SQLAlchemy + PostgreSQL + OpenAI/Anthropic
- **Port**: 8004
- **Database**: workflow_service (isolated from other services)

## 🧠 **Your Exclusive Domain**

You are the **Workflow Intelligence Service specialist**. Your responsibilities are:

### **Workflow Engine**
- State machine implementation and transitions
- Conditional routing and decision trees
- Parallel and sequential execution paths
- Workflow versioning and migration
- SLA monitoring and escalation

### **AI-Powered Intelligence**
- Natural language processing for workflow triggers
- Intelligent routing and assignment
- Automated decision making
- Document summarization and extraction
- Predictive analytics for process optimization

### **Business Process Management**
- Approval workflows and chains
- Document review processes
- Onboarding workflows
- Compliance workflows
- Custom workflow designer

### **Integration Hub**
- Trigger workflows from other services
- Orchestrate multi-service operations
- Event-driven workflow initiation
- Webhook management for external systems
- API callbacks and notifications

### **Analytics & Monitoring**
- Workflow performance metrics
- Bottleneck identification
- Process mining and optimization
- Compliance reporting
- Audit trail management

## 🚫 **Service Boundaries (STRICT)**

### **You CANNOT Modify:**
- Other microservices (identity-service, communication-service, content-service)
- API Gateway configuration  
- Shared infrastructure code
- Other service databases

### **Integration Only:**
- Call Identity Service for JWT validation
- Send notifications via Communication Service
- Access documents via Content Service
- Publish workflow events to message queue

## 🔧 **Development Commands**

### **Start Development**
```bash
# Start service dependencies
docker-compose -f docker-compose.yml up -d postgres redis

# Start FastAPI service
uvicorn main:app --reload --port 8004

# Health check
curl http://localhost:8004/health

# Access API documentation
# http://localhost:8004/docs
```

### **Database Operations**  
```bash
# Initialize Alembic (NEEDED - NOT SET UP YET!)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial workflow schema"

# Run migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### **Testing**
```bash
# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# Run workflow engine tests (TO BE CREATED)
pytest tests/unit/test_workflow_engine.py -v

# Run AI integration tests (TO BE CREATED)
pytest tests/unit/test_ai_processor.py -v
```

## 📊 **Service Architecture**

### **Current Structure**
```
workflow-intelligence-service/
├── main.py                      # FastAPI application entry
├── models.py                    # Database models
├── schemas.py                   # Pydantic schemas
├── services/                    # Business logic
│   ├── workflow_engine.py      # Core workflow engine
│   ├── ai_processor.py         # AI integration
│   └── analytics_service.py    # Analytics and reporting
├── api/                         # API endpoints
│   └── v1/
│       ├── workflows.py        # Workflow management
│       ├── ai.py               # AI endpoints
│       └── analytics.py        # Analytics endpoints
├── workflows/                   # Workflow definitions
│   ├── approval_workflow.py    # Approval chain workflow
│   ├── onboarding_workflow.py  # Employee onboarding
│   └── compliance_workflow.py  # Compliance checks
├── tests/                       # Test suite (INCOMPLETE)
├── docs/                        # Documentation
├── requirements.txt             # Dependencies
├── test_requirements.txt        # Test dependencies
├── pytest.ini                   # Test configuration
├── Dockerfile                   # Container definition
└── docker-compose.yml          # Local development stack
```

### **Database Models You Manage**
```python
# WORKFLOW TABLES:
- workflow_definitions       # Workflow templates/blueprints
- workflow_instances        # Active workflow instances
- workflow_states          # Current state of each instance
- workflow_transitions     # State transition history
- workflow_variables       # Instance variables/context

# TASK TABLES:
- tasks                    # Individual workflow tasks
- task_assignments        # User/role assignments
- task_deadlines         # SLA and deadline tracking
- task_dependencies      # Task ordering and dependencies
- task_comments          # Task discussions

# AI PROCESSING:
- ai_prompts             # Prompt templates
- ai_responses           # AI response history
- ai_embeddings         # Document embeddings
- ai_training_data      # Feedback for improvement

# ANALYTICS:
- workflow_metrics       # Performance metrics
- process_analytics     # Process mining data
- bottleneck_analysis   # Identified bottlenecks
- sla_violations        # SLA breach records

# INTEGRATION:
- workflow_triggers      # Event-based triggers
- webhook_endpoints     # External webhooks
- api_callbacks         # Callback configurations
```

## 🔌 **Service Integrations**

### **AI Provider Configuration**
```python
# OpenAI Configuration
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-4"
OPENAI_TEMPERATURE = 0.7

# Anthropic Configuration (Alternative)
ANTHROPIC_API_KEY = "sk-ant-..."
ANTHROPIC_MODEL = "claude-3-opus"

# Local LLM (Development)
LOCAL_LLM_ENDPOINT = "http://localhost:11434"  # Ollama
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

### **Workflow Event Publishing**
```python
# Publish workflow events
await publish_event("workflow.started", {
    "workflow_id": workflow_id,
    "definition_id": definition_id,
    "user_id": user_id,
    "timestamp": datetime.utcnow()
})

await publish_event("workflow.completed", {
    "workflow_id": workflow_id,
    "outcome": "approved",
    "duration_seconds": duration
})

await publish_event("workflow.task.assigned", {
    "task_id": task_id,
    "assignee_id": assignee_id,
    "deadline": deadline
})
```

## 🚨 **Critical Issues to Fix**

### **1. Core Workflow Engine Tests (URGENT)**
```python
# tests/unit/test_workflow_engine.py (TO CREATE)
class TestWorkflowEngine:
    async def test_workflow_initialization(self):
        """Test workflow instance creation"""
        pass
    
    async def test_state_transition_valid(self):
        """Test valid state transitions"""
        pass
    
    async def test_state_transition_invalid(self):
        """Test invalid state transitions are rejected"""
        pass
    
    async def test_parallel_execution_paths(self):
        """Test parallel branch execution"""
        pass
    
    async def test_conditional_routing(self):
        """Test conditional decision points"""
        pass
    
    async def test_workflow_rollback(self):
        """Test rollback on failure"""
        pass
```

### **2. AI Integration Tests (CRITICAL)**
```python
# tests/unit/test_ai_processor.py (TO CREATE)
class TestAIProcessor:
    @patch('openai.ChatCompletion.create')
    async def test_ai_summarization(self, mock_openai):
        """Test document summarization"""
        mock_openai.return_value = {
            "choices": [{"message": {"content": "Summary text"}}]
        }
        # Test summarization logic
        pass
    
    async def test_ai_decision_making(self):
        """Test AI-powered routing decisions"""
        pass
    
    async def test_prompt_template_rendering(self):
        """Test prompt template with variables"""
        pass
    
    async def test_ai_retry_on_rate_limit(self):
        """Test retry logic for rate limits"""
        pass
```

### **3. State Machine Testing (REQUIRED)**
```python
# tests/unit/test_state_machine.py (TO CREATE)
from transitions import Machine

class TestStateMachine:
    def test_approval_workflow_states(self):
        """Test approval workflow state machine"""
        states = ['draft', 'submitted', 'reviewing', 'approved', 'rejected']
        transitions = [
            {'trigger': 'submit', 'source': 'draft', 'dest': 'submitted'},
            {'trigger': 'review', 'source': 'submitted', 'dest': 'reviewing'},
            {'trigger': 'approve', 'source': 'reviewing', 'dest': 'approved'},
            {'trigger': 'reject', 'source': 'reviewing', 'dest': 'rejected'}
        ]
        # Test all transitions
        pass
```

### **4. Performance Testing (MISSING)**
```python
# tests/performance/test_workflow_performance.py (TO CREATE)
@pytest.mark.performance
class TestWorkflowPerformance:
    async def test_concurrent_workflow_execution(self):
        """Test handling 100 concurrent workflows"""
        pass
    
    async def test_large_workflow_processing(self):
        """Test workflow with 1000+ tasks"""
        pass
    
    async def test_ai_response_caching(self):
        """Test AI response caching effectiveness"""
        pass
```

### **5. Database Migrations (SETUP REQUIRED)**
```bash
# Initialize Alembic
alembic init alembic

# Configure alembic.ini
sed -i 's|sqlalchemy.url = .*|sqlalchemy.url = postgresql://user:pass@localhost/workflow_service|' alembic.ini

# Create initial migration
alembic revision --autogenerate -m "Initial workflow schema"
alembic upgrade head
```

## 🎯 **Development Priorities**

### **Week 1: Core Testing (URGENT)**
1. 🔴 Create workflow engine unit tests
2. 🔴 Implement state machine tests
3. 🔴 Add AI integration tests with mocking
4. 🔴 Setup database migrations

### **Week 2: Integration Testing**
1. 🔴 Complete workflow lifecycle tests
2. 🔴 Test multi-service orchestration
3. 🔴 Add webhook integration tests
4. 🔴 Implement SLA monitoring tests

### **Week 3: Performance & Documentation**
1. 🔴 Add performance benchmarks
2. 🔴 Create load testing suite
3. 🔴 Document workflow patterns
4. 🔴 Create workflow design guide

## 🔍 **Testing Strategy**

### **Critical Test Coverage Areas**
```python
# Workflow Engine (0% coverage - URGENT)
- Workflow initialization
- State transitions
- Parallel execution
- Conditional routing
- Error handling
- Rollback mechanisms

# AI Integration (0% coverage - URGENT)
- OpenAI API mocking
- Prompt engineering
- Response parsing
- Cost tracking
- Rate limit handling
- Fallback strategies

# State Machine (0% coverage - URGENT)
- State definitions
- Transition validation
- Guard conditions
- State persistence
- History tracking

# Integration Points (30% coverage - NEEDS IMPROVEMENT)
- JWT validation
- Service orchestration
- Event publishing
- Webhook handling
```

### **Test Data Factories Needed**
```python
# tests/factories/workflow_factory.py (TO CREATE)
class WorkflowFactory:
    @staticmethod
    def create_approval_workflow():
        return {
            "definition_id": "approval-workflow",
            "name": "Document Approval",
            "states": ["draft", "submitted", "approved", "rejected"],
            "initial_state": "draft"
        }
    
    @staticmethod
    def create_workflow_instance(definition_id: str, user_id: str):
        return {
            "definition_id": definition_id,
            "user_id": user_id,
            "state": "draft",
            "variables": {},
            "created_at": datetime.utcnow()
        }
```

## 📈 **Success Metrics**

### **Performance Targets**
- Workflow creation: <200ms
- State transition: <100ms
- AI processing: <3s for standard requests
- Concurrent workflows: >100 simultaneous
- SLA compliance: >99%

### **Quality Targets**
- Test coverage: >80% (currently ~30%)
- Zero critical bugs in production
- API documentation: 100% complete
- Workflow success rate: >95%

## 🚨 **Immediate Action Items**

### **1. Create Core Test Files (TODAY)**
```bash
# Create essential test files
touch tests/unit/test_workflow_engine.py
touch tests/unit/test_state_machine.py
touch tests/unit/test_ai_processor.py
touch tests/integration/test_workflow_lifecycle.py
touch tests/performance/test_concurrent_workflows.py
```

### **2. Implement Workflow Engine Tests (THIS WEEK)**
```python
# tests/unit/test_workflow_engine.py
"""
Must test:
- All state transitions
- Guard conditions
- Parallel execution
- Variable management
- Error scenarios
"""
```

### **3. Add AI Mocking (THIS WEEK)**
```python
# tests/mocks/ai_mocks.py
def mock_openai_response(prompt_type: str):
    responses = {
        "summarize": "This is a summary",
        "extract": {"field1": "value1"},
        "decide": {"route": "approve", "confidence": 0.95}
    }
    return responses.get(prompt_type)
```

### **4. Setup Database Migrations (URGENT)**
```bash
# Run these commands now
cd workflow-intelligence-service
alembic init alembic
# Edit alembic/env.py to import your models
# Create first migration
alembic revision --autogenerate -m "Initial workflow schema"
alembic upgrade head
```

## 🛠️ **Code Quality Standards**

### **Workflow Definition Standards**
```python
from enum import Enum
from typing import List, Dict, Optional

class WorkflowState(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"

class WorkflowDefinition:
    def __init__(self, definition_id: str, name: str):
        self.definition_id = definition_id
        self.name = name
        self.states: List[WorkflowState] = []
        self.transitions: Dict[str, Dict] = {}
        self.guards: Dict[str, callable] = {}
    
    def add_transition(
        self,
        trigger: str,
        source: WorkflowState,
        dest: WorkflowState,
        guard: Optional[callable] = None
    ):
        """Add a state transition with optional guard condition"""
        pass
```

### **AI Integration Standards**
```python
from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    async def process(self, prompt: str, context: dict) -> dict:
        """Process AI request with context"""
        pass
    
    @abstractmethod
    async def estimate_cost(self, prompt: str) -> float:
        """Estimate processing cost"""
        pass

class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
    
    async def process(self, prompt: str, context: dict) -> dict:
        # Implementation with retry logic
        pass
```

---

**🔄 You are the Workflow Intelligence Service expert. Focus on building robust, testable workflow automation with AI-powered intelligence.**

**🚨 CRITICAL: Your service's core functionality (workflow engine and AI integration) is completely untested. This is the highest priority.**

## 🔥 **URGENT: CONTAINERIZATION (IMMEDIATE - SEPTEMBER 10, 2025)**

**DEPLOYMENT-AGENT PRIORITY INSTRUCTIONS:**

Your service containerization is **MEDIUM PRIORITY** (after Communication + Content) - infrastructure is ready:
- ✅ Database: `workflow-db` running on port 5436
- ✅ Redis: `workflow-redis` running on port 6383
- ✅ Identity Service: Available for integration at port 8001
- ⚠️ **DEPENDENCY**: Wait for Communication + Content services to be containerized first

### **1. Create Requirements Standalone with AI Libraries**
```bash
# Create requirements-standalone.txt with AI and workflow support
cat > requirements-standalone.txt << 'EOF'
# Workflow Intelligence Service - Standalone Requirements
# Consolidated from shared + workflow/AI-specific requirements

# Core Framework
fastapi==0.116.1
uvicorn[standard]==0.35.0
pydantic==2.11.7
pydantic[email]==2.11.7
pydantic-settings==2.8.0

# Database & ORM  
sqlalchemy==2.0.43
alembic==1.14.0
asyncpg==0.30.0

# Redis & Caching
redis==6.4.0
aioredis==2.0.1

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
PyJWT==2.8.0
bcrypt==4.2.0
cryptography==42.0.8

# HTTP Client
httpx==0.27.2

# Environment & Config
python-dotenv==1.0.1
python-multipart==0.0.12

# Task Queue (Workflow Specific)
celery==5.3.4

# AI/ML Libraries (Workflow Specific)
openai==1.3.5
numpy==1.24.3
pandas==2.0.3

# Development & Testing
pytest==8.3.4
pytest-asyncio==0.24.0
black==25.1.0
isort==5.13.2
flake8==7.1.1

# Monitoring
prometheus-client==0.21.1
structlog==25.1.0
EOF
```

### **2. Create Dockerfile with AI Dependencies**
```bash
# Create Dockerfile following identity-service pattern + AI libs
cat > Dockerfile << 'EOF'
# Multi-stage build for Workflow Intelligence Service
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-standalone.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure the PATH includes local installed packages
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Environment variables
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    SERVICE_PORT=8004

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# Expose port
EXPOSE 8004

# Run the service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
EOF
```

### **3. Add Health Endpoint with Service Dependencies**
```python
# Add to your FastAPI app in main.py:
from datetime import datetime
import httpx

@app.get("/health")
async def health_check():
    # Test service dependencies
    service_status = {}
    
    async with httpx.AsyncClient() as client:
        # Test identity service
        try:
            response = await client.get("http://identity-service:8001/health", timeout=5.0)
            service_status["identity"] = "connected" if response.status_code == 200 else "error"
        except:
            service_status["identity"] = "disconnected"
            
        # Test communication service (if available)
        try:
            response = await client.get("http://communication-service:8002/health", timeout=5.0)
            service_status["communication"] = "connected" if response.status_code == 200 else "error"
        except:
            service_status["communication"] = "disconnected"
            
        # Test content service (if available)
        try:
            response = await client.get("http://content-service:8003/health", timeout=5.0)
            service_status["content"] = "connected" if response.status_code == 200 else "error"
        except:
            service_status["content"] = "disconnected"
    
    return {
        "status": "healthy",
        "service": "workflow-intelligence-service", 
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected",  # Add actual DB check
        "redis": "connected",     # Add actual Redis check
        "services": service_status,
        "features": [
            "✅ Workflow automation",
            "✅ AI integration", 
            "✅ Process management",
            "✅ State machine"
        ]
    }
```

### **4. Test Container Build (AFTER Communication + Content)**
```bash
# WAIT for communication-service and content-service to be running first

# Build your service
docker-compose -f ../../docker-compose.local.yml build workflow-intelligence-service

# Start your service  
docker-compose -f ../../docker-compose.local.yml up -d workflow-intelligence-service

# Check status
docker-compose -f ../../docker-compose.local.yml ps workflow-intelligence-service

# Test health endpoint
curl http://localhost:8004/health

# Check logs if issues
docker-compose -f ../../docker-compose.local.yml logs workflow-intelligence-service
```

### **5. Environment Variables (Already Configured)**
Your service will receive these environment variables:
```bash
DATABASE_URL=postgresql+asyncpg://workflow_user:workflow_pass@workflow-db:5432/workflow_service
REDIS_URL=redis://workflow-redis:6379/0
CELERY_BROKER_URL=redis://workflow-redis:6379/1
IDENTITY_SERVICE_URL=http://identity-service:8001
COMMUNICATION_SERVICE_URL=http://communication-service:8002
CONTENT_SERVICE_URL=http://content-service:8003
SERVICE_NAME=workflow-intelligence-service
SERVICE_PORT=8004
DEBUG=true
LOG_LEVEL=info
OPENAI_API_KEY=${OPENAI_API_KEY:-}
```

**Current Priority After Container Working:** 
1. ✅ **CONTAINERIZATION FIRST** (this section)
2. Create workflow engine unit tests
3. Implement state machine testing
4. Add AI integration tests with proper mocking
5. Setup database migrations with Alembic
6. Achieve >80% test coverage for core functionality**

**Remember: A workflow engine without tests is a liability, not an asset. Every state transition must be validated, every AI call must be mocked, and every edge case must be covered.**