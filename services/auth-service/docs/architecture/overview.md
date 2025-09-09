# Auth Service - System Architecture Overview

## 🏗️ **High-Level Architecture**

The Auth Service is designed as a modern, scalable microservice using clean architecture principles with clear separation of concerns.

## 🔧 **Technology Stack**

### **Core Framework**
- **FastAPI**: Async web framework with automatic OpenAPI documentation
- **Pydantic**: Data validation and serialization
- **SQLAlchemy 2.0**: Async ORM with PostgreSQL
- **Alembic**: Database migration management
- **Uvicorn**: ASGI server with hot reload

### **Database & Caching**
- **PostgreSQL 17**: Primary database for persistent data
- **Redis**: Session caching and rate limiting
- **AsyncPG**: High-performance PostgreSQL driver

### **Security & Authentication**
- **bcrypt**: Password hashing
- **PyJWT**: JSON Web Token handling
- **Python-multipart**: Form data parsing
- **Email-validator**: Email validation

## 📁 **Clean Architecture Structure**

```
services/auth-service/
├── main.py                    # Entry point with FastAPI app
├── app/                       # Main application (future organized structure)
├── config.py                  # Configuration management
├── database.py                # Database connection and session management
├── simple_models.py           # SQLAlchemy models (current implementation)
├── services.py                # Business logic services
├── alembic/                   # Database migrations
├── scripts/                   # Management and maintenance
└── tests/                     # Test suites
```

## 🔄 **Request Flow Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client        │    │   FastAPI       │    │   Auth Service  │
│   Application   │───▶│   Router        │───▶│   Business      │
│                 │    │   (main.py)     │    │   Logic         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Pydantic      │    │   SQLAlchemy    │
                       │   Validation    │    │   Models        │
                       │   (Schemas)     │    │   (Database)    │
                       └─────────────────┘    └─────────────────┘
```

## 🎯 **Core Components**

### **1. API Layer (main.py)**
- **Responsibility**: HTTP request handling, routing, validation
- **Components**: FastAPI routers, dependency injection, error handling
- **Patterns**: RESTful endpoints, async/await, Pydantic validation

### **2. Business Logic Layer (services.py)**
- **Responsibility**: Authentication logic, user management, security
- **Components**: AuthService, TokenService, email verification
- **Patterns**: Service pattern, dependency injection, async operations

### **3. Data Layer (simple_models.py + database.py)**
- **Responsibility**: Data persistence, relationships, transactions
- **Components**: SQLAlchemy models, database sessions, migrations
- **Patterns**: Active Record, Repository pattern, async database operations

### **4. Configuration Layer (config.py)**
- **Responsibility**: Environment management, settings validation
- **Components**: Pydantic Settings, environment variables
- **Patterns**: Configuration as code, environment-based settings

## 🔐 **Security Architecture**

### **Authentication Flow**
```
Registration → Email Verification → Login → JWT Token Generation
     │              │                │              │
     ▼              ▼                ▼              ▼
Password Hash → Token Storage → Session Create → Access Control
```

### **Security Layers**
1. **Input Validation**: Pydantic schemas validate all requests
2. **Password Security**: bcrypt hashing with salt
3. **Token Security**: JWT with configurable expiration
4. **Rate Limiting**: Built-in protection against brute force
5. **Session Management**: Device tracking and session expiration
6. **Audit Logging**: Comprehensive activity tracking

## 🗄️ **Data Architecture**

### **Core Entities**
- **User**: Central entity with profile and authentication data
- **EmailVerification**: Email verification workflow management
- **UserSession**: JWT session tracking with device information
- **UserActivity**: Comprehensive audit trail

### **Data Relationships**
```
User (1) ───── (N) EmailVerification
 │
 └─── (N) UserSession
 │
 └─── (N) UserActivity
```

### **Data Flow**
1. **Registration**: User → EmailVerification → User.is_verified = True
2. **Login**: User verification → UserSession creation → JWT generation
3. **Activity**: All operations → UserActivity logging

## 🚀 **Scalability Design**

### **Horizontal Scaling**
- **Stateless Design**: No server-side session storage
- **Database Connection Pooling**: Efficient connection management
- **Redis Caching**: Session and rate limit data caching
- **Async Operations**: Non-blocking I/O for high concurrency

### **Performance Optimizations**
- **Database Indexing**: Optimized queries on email, tokens
- **Connection Pooling**: AsyncPG with connection reuse
- **Caching Strategy**: Redis for frequently accessed data
- **Lazy Loading**: Efficient relationship loading

## 🔧 **Integration Architecture**

### **External Dependencies**
```
Auth Service
    │
    ├── PostgreSQL 17 (Primary Database)
    ├── Redis (Caching & Rate Limiting)
    ├── SMTP Server (Email Verification)
    └── Environment Config (.env files)
```

### **API Integration Points**
- **Health Check**: `/health` for monitoring systems
- **Metrics**: `/test-info` for operational insights
- **Admin APIs**: User management for administrative systems
- **Authentication APIs**: Token validation for other services

## 📊 **Monitoring Architecture**

### **Health Monitoring**
- **Application Health**: `/health` endpoint with dependency checks
- **Database Health**: Connection status and query performance
- **Redis Health**: Cache connectivity and performance
- **Service Metrics**: Request/response times, error rates

### **Logging Strategy**
- **Structured Logging**: JSON format for log aggregation
- **Activity Logging**: User actions and security events
- **Error Logging**: Exception tracking and debugging
- **Performance Logging**: Request timing and database queries

## 🔄 **Development Workflow**

### **Local Development**
```bash
# Dependencies
brew services start postgresql@17
brew services start redis

# Development
python main.py  # Hot reload enabled
curl http://localhost:8001/health  # Health check
```

### **Database Management**
```bash
# Migrations
alembic upgrade head     # Apply migrations
alembic revision --autogenerate -m "Description"  # Create migration

# Management
./scripts/manage.sh status   # Service status
./scripts/manage.sh test     # Run tests
```

## 🎯 **Architecture Principles**

### **1. Separation of Concerns**
- Clear boundaries between API, business logic, and data layers
- Single responsibility for each component
- Dependency injection for loose coupling

### **2. Security First**
- All inputs validated at API boundary
- Comprehensive authentication and authorization
- Audit logging for all security-relevant operations

### **3. Async by Design**
- Non-blocking I/O throughout the stack
- Async database operations with connection pooling
- Scalable request handling

### **4. Configuration as Code**
- Environment-based configuration management
- Type-safe configuration with Pydantic
- Secrets management through environment variables

### **5. Observability Built-in**
- Health checks for all dependencies
- Comprehensive logging and metrics
- Error tracking and performance monitoring

## 🚀 **Future Architecture Considerations**

### **Microservice Evolution**
- **Service Mesh**: Istio for inter-service communication
- **Event Streaming**: Kafka for async communication
- **API Gateway**: Centralized routing and authentication
- **Container Orchestration**: Kubernetes for production deployment

### **Advanced Features**
- **Multi-tenant Architecture**: Organization-based data isolation
- **CQRS Pattern**: Command/Query separation for complex operations
- **Event Sourcing**: Audit trail through event streaming
- **Circuit Breakers**: Resilience patterns for external dependencies

---

**This architecture provides a solid foundation for a production-ready authentication service with clear scaling paths and maintainability.**