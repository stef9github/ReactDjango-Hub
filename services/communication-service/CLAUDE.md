# Communication Service - Claude Code Agent Configuration

This file provides guidance to Claude Code when working specifically on the **Communication Microservice**.

## 🎯 **Service Identity**
- **Service Name**: communication-service  
- **Technology**: FastAPI + SQLAlchemy + PostgreSQL + Redis + Celery
- **Port**: 8002
- **Database**: communication_service (isolated from other services)

## 🧠 **Your Exclusive Domain**

You are the **Communication Service specialist**. Your responsibilities are:

### **Core Messaging**
- Multi-channel notification delivery (Email, SMS, Push, In-App)
- Template management and rendering
- Message queuing and scheduling
- Delivery tracking and retry logic
- Bulk messaging operations

### **Real-time Communication**
- WebSocket connections for live notifications
- Presence management
- Real-time message broadcasting
- Connection pooling and management

### **Conversation Management**
- Thread-based conversations
- Message history and archiving
- Read receipts and typing indicators
- Attachment handling

### **Queue Management**
- Priority-based message queuing
- Rate limiting per channel
- Batch processing for bulk sends
- Dead letter queue handling

### **Integration Points**
- Email providers (SendGrid, AWS SES, SMTP)
- SMS providers (Twilio, AWS SNS)
- Push notification services (FCM, APNS)
- Identity Service for user validation

## 🚫 **Service Boundaries (STRICT)**

### **You CANNOT Modify:**
- Other microservices (identity-service, content-service, workflow-intelligence-service)
- API Gateway configuration  
- Shared infrastructure code
- Other service databases

### **Integration Only:**
- Call Identity Service for JWT validation
- Publish events to message queue
- Use shared Redis for caching
- Call external notification providers

## 🔧 **Development Commands**

### **Start Development**
```bash
# Start service dependencies
docker-compose -f docker-compose.yml up -d postgres redis rabbitmq

# Start Celery worker
celery -A app.tasks worker --loglevel=info

# Start Celery beat scheduler
celery -A app.tasks beat --loglevel=info

# Start FastAPI service
uvicorn main:app --reload --port 8002

# Health check
curl http://localhost:8002/health
```

### **Database Operations**  
```bash
# Initialize Alembic (if not done)
alembic init alembic

# Create new migration
alembic revision --autogenerate -m "Description"

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

# Run with parallel execution
pytest tests/ -n auto

# Run performance tests
pytest tests/performance/ -v --benchmark-only
```

## 📊 **Service Architecture**

### **Key Files You Own**
```
communication-service/
├── main.py                      # FastAPI application entry
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── notifications.py # Notification endpoints
│   │       ├── conversations.py # Conversation endpoints
│   │       ├── templates.py     # Template management
│   │       └── webhooks.py      # Provider webhooks
│   ├── core/
│   │   ├── config.py           # Service configuration
│   │   ├── database.py         # Database connection
│   │   └── security.py         # Auth integration
│   ├── models/
│   │   ├── notification.py     # Notification models
│   │   ├── conversation.py     # Conversation models
│   │   └── template.py         # Template models
│   ├── services/
│   │   ├── notification_service.py  # Core notification logic
│   │   ├── template_engine.py       # Template rendering
│   │   ├── queue_manager.py         # Queue operations
│   │   └── providers/               # External provider integrations
│   │       ├── email_provider.py
│   │       ├── sms_provider.py
│   │       └── push_provider.py
│   ├── tasks/                  # Celery async tasks
│   │   ├── send_tasks.py       # Message sending tasks
│   │   └── cleanup_tasks.py    # Maintenance tasks
│   └── utils/
│       ├── rate_limiter.py     # Rate limiting logic
│       └── validators.py       # Input validation
├── tests/                       # Comprehensive test suite
├── alembic/                     # Database migrations
├── requirements.txt             # Python dependencies
├── test_requirements.txt        # Testing dependencies
├── pytest.ini                   # Test configuration
├── Dockerfile                   # Container definition
└── docker-compose.yml          # Local development stack
```

### **Database Models You Manage**
```python
# CORE NOTIFICATION TABLES:
- notifications              # All notifications across channels
- notification_templates     # Reusable message templates
- notification_categories    # Notification type categorization
- notification_preferences   # User channel preferences
- notification_schedules     # Scheduled notifications

# CONVERSATION TABLES:
- conversations             # Conversation threads
- conversation_messages     # Individual messages
- conversation_participants # Thread participants
- message_attachments       # File attachments
- message_reactions         # Emoji reactions

# DELIVERY TRACKING:
- delivery_logs            # Detailed delivery attempts
- delivery_failures        # Failed delivery records
- bounce_records          # Email/SMS bounce tracking
- unsubscribe_lists       # Opt-out management

# QUEUE MANAGEMENT:
- message_queue           # Pending messages
- queue_metrics          # Queue performance metrics
- rate_limit_buckets     # Rate limiting state
```

## 🔌 **Service Integrations**

### **External Services to Configure**
```python
# Email Providers
SENDGRID_API_KEY = "your-key"
AWS_SES_REGION = "us-east-1"
SMTP_HOST = "smtp.gmail.com"

# SMS Providers  
TWILIO_ACCOUNT_SID = "your-sid"
TWILIO_AUTH_TOKEN = "your-token"
AWS_SNS_REGION = "us-east-1"

# Push Notifications
FCM_SERVER_KEY = "your-fcm-key"
APNS_CERT_PATH = "/path/to/cert.pem"
```

### **Identity Service Integration**
```python
# Validate JWT tokens
async def validate_user(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://identity-service:8001/auth/validate",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()
```

### **Event Publishing**
```python
# Events to publish
await publish_event("notification.sent", {
    "notification_id": notification_id,
    "user_id": user_id,
    "channel": channel,
    "timestamp": datetime.utcnow()
})

await publish_event("notification.failed", {
    "notification_id": notification_id,
    "error": error_message,
    "retry_count": retry_count
})

await publish_event("conversation.message.sent", {
    "conversation_id": conversation_id,
    "message_id": message_id,
    "sender_id": sender_id
})
```

## 🎯 **Current Status & Priority Tasks**

### **✅ Completed**
- Basic notification endpoints
- JWT authentication integration
- Template management system
- Redis caching setup
- Unit tests for services

### **🔥 URGENT: CONTAINERIZATION (IMMEDIATE)**

**DEPLOYMENT-AGENT INSTRUCTIONS - September 10, 2025:**

Your service containerization is **HIGH PRIORITY** - infrastructure is ready and waiting:
- ✅ Database: `communication-db` running on port 5434
- ✅ Redis: `communication-redis` running on port 6381  
- ✅ Identity Service: Available for integration at port 8001

#### **1. Create Requirements Standalone**
```bash
# Create requirements-standalone.txt with async database support
cat > requirements-standalone.txt << 'EOF'
# Communication Service - Standalone Requirements
# Consolidated from shared + communication-specific requirements

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

# Task Queue (Communication Specific)
celery==5.3.4

# External Provider Integrations
aiosmtplib==3.0.1
twilio==8.10.1

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

#### **2. Create Dockerfile**
```bash
# Create Dockerfile following identity-service pattern
cat > Dockerfile << 'EOF'
# Multi-stage build for Communication Service
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
    SERVICE_PORT=8002

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Expose port
EXPOSE 8002

# Run the service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
EOF
```

#### **3. Add Health Endpoint (CRITICAL)**
```python
# Add to your FastAPI app in main.py:
from datetime import datetime

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "communication-service", 
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected",  # Add actual DB check
        "redis": "connected",     # Add actual Redis check
        "features": [
            "✅ Multi-channel notifications",
            "✅ Template management",
            "✅ Queue processing",
            "✅ Provider integrations"
        ]
    }
```

#### **4. Test Container Build**
```bash
# Build your service
docker-compose -f ../../docker-compose.local.yml build communication-service

# Start your service  
docker-compose -f ../../docker-compose.local.yml up -d communication-service

# Check status
docker-compose -f ../../docker-compose.local.yml ps communication-service

# Test health endpoint
curl http://localhost:8002/health

# Check logs if issues
docker-compose -f ../../docker-compose.local.yml logs communication-service
```

#### **5. Environment Variables (Already Configured)**
Your service will receive these environment variables:
```bash
DATABASE_URL=postgresql+asyncpg://comm_user:comm_pass@communication-db:5432/communication_service
REDIS_URL=redis://communication-redis:6379/0
CELERY_BROKER_URL=redis://communication-redis:6379/1
IDENTITY_SERVICE_URL=http://identity-service:8001
SERVICE_NAME=communication-service
SERVICE_PORT=8002
DEBUG=true
LOG_LEVEL=info
```

### **🚨 Critical Tasks (After Container Working)**

### **⚠️ Important Tasks (This Week)**
1. **OpenAPI Documentation**
   - Generate OpenAPI schema
   - Add endpoint descriptions
   - Include request/response examples

2. **Performance Testing**
   - Load test notification queues
   - Benchmark template rendering
   - Test WebSocket scalability

3. **Provider Integrations**
   - Complete SendGrid integration
   - Add Twilio SMS support
   - Implement FCM push notifications

### **📋 Nice to Have (Backlog)**
1. Advanced template features (loops, conditionals)
2. A/B testing for notifications
3. Analytics dashboard
4. Webhook management UI

## 🎯 **Development Focus**

### **When Working on Features**
1. **Channel Abstraction**: Keep provider implementations swappable
2. **Async First**: Use Celery for all external API calls
3. **Retry Logic**: Implement exponential backoff for failures
4. **Rate Limiting**: Respect provider rate limits
5. **Monitoring**: Log all delivery attempts and failures

### **Code Patterns to Follow**
```python
# Service Pattern
class NotificationService:
    def __init__(self, db_session: AsyncSession, cache: Redis):
        self.db = db_session
        self.cache = cache
    
    async def send_notification(
        self,
        user_id: str,
        template_id: str,
        channel: NotificationChannel,
        data: dict
    ) -> Notification:
        # Validate user preferences
        # Render template
        # Queue for sending
        # Return tracking info
        pass

# Provider Interface
class NotificationProvider(ABC):
    @abstractmethod
    async def send(self, recipient: str, message: str) -> DeliveryResult:
        pass
    
    @abstractmethod
    async def get_status(self, message_id: str) -> DeliveryStatus:
        pass

# Task Pattern
@celery.task(bind=True, max_retries=3)
def send_email_task(self, notification_id: str):
    try:
        # Send email
        pass
    except Exception as exc:
        # Exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

## 🔍 **Testing Requirements**

### **Test Coverage Goals**
- Unit Tests: 80% coverage minimum
- Integration Tests: All API endpoints
- E2E Tests: Complete notification flows
- Performance Tests: Queue throughput

### **Key Test Scenarios**
```python
# Test notification delivery
async def test_send_notification_success():
    # Create notification
    # Mock provider response
    # Verify delivery
    # Check audit log

# Test retry logic
async def test_notification_retry_on_failure():
    # Mock provider failure
    # Verify retry attempt
    # Check exponential backoff
    # Verify dead letter queue

# Test rate limiting
async def test_rate_limiting_enforcement():
    # Send burst of notifications
    # Verify rate limit applied
    # Check queue throttling
```

## 🚨 **Critical Reminders**

1. **Data Privacy**: Never log message content in production
2. **Provider Limits**: Always respect rate limits and quotas
3. **Delivery Guarantees**: Implement at-least-once delivery
4. **Security**: Sanitize all template inputs to prevent injection
5. **Monitoring**: Track delivery rates and failures

## 📈 **Success Metrics**

### **Performance Targets**
- Message sending: <500ms to queue
- Template rendering: <50ms
- Delivery rate: >95% success
- Queue processing: >1000 msg/sec

### **Quality Targets**
- Test coverage: >80%
- API documentation: 100% endpoints documented
- Zero security vulnerabilities
- <1% message loss rate

## 🛠️ **Immediate Action Items**

1. **Fix Documentation Gap**
   ```bash
   # Create comprehensive docs
   mkdir -p docs
   echo "# Communication Service API" > docs/README.md
   ```

2. **Complete Integration Tests**
   ```python
   # tests/integration/test_notification_flow.py
   async def test_complete_email_flow():
       # User triggers notification
       # Template is rendered
       # Email is queued
       # Provider sends email
       # Delivery is confirmed
   ```

3. **Add Missing Migrations**
   ```bash
   alembic revision --autogenerate -m "Add notification tables"
   alembic upgrade head
   ```

---

**📢 You are the Communication Service expert. Focus on reliable, scalable message delivery across all channels while maintaining clean separation from other services.**

**Current Priority: Complete integration tests and setup database migrations to achieve production readiness.**