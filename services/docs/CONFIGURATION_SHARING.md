# Cross-Service Configuration Sharing Guidelines

## 🎯 **Purpose**
This document defines how configuration should be shared across microservices to ensure consistent behavior while maintaining service isolation and security.

---

## 📋 **Configuration Sharing Strategy**

### **🌐 What SHOULD Be Shared (.env.shared)**

#### **1. Service Discovery**
```bash
# All services need to know how to reach each other
IDENTITY_SERVICE_URL=http://identity-service:8001
CONTENT_SERVICE_URL=http://content-service:8002
COMMUNICATION_SERVICE_URL=http://communication-service:8003
WORKFLOW_SERVICE_URL=http://workflow-service:8004
```

#### **2. Security Standards**
```bash
# JWT configuration for consistent auth across services
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
# Note: JWT_SECRET_KEY remains service-specific for security
```

#### **3. Infrastructure Patterns**
```bash
# Database connection patterns (services customize the specifics)
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_ECHO=false

# Redis connection patterns  
REDIS_MAX_CONNECTIONS=10
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
```

#### **4. Logging & Monitoring Standards**
```bash
# Consistent logging across all services
LOG_LEVEL=INFO
LOG_FORMAT=json
TRACE_ENABLED=true
METRICS_ENABLED=true
```

#### **5. API Standards**
```bash
# Consistent API behavior
API_VERSION=v1
API_TITLE_SUFFIX=" - ReactDjango Hub"
API_DESCRIPTION_SUFFIX=" microservice for ReactDjango Hub platform"

# CORS settings for consistent frontend integration
CORS_ALLOW_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["*"]
CORS_ALLOW_HEADERS=["*"]
```

#### **6. Development Flags**
```bash
# Development environment consistency
DEBUG=false
DEVELOPMENT_MODE=true
AUTO_RELOAD=true
```

#### **7. Security Headers**
```bash
# Consistent security posture
SECURE_HEADERS_ENABLED=true
RATE_LIMITING_ENABLED=true
DEFAULT_RATE_LIMIT="100/minute"
```

---

### **🔒 What MUST Remain Service-Specific**

#### **1. Secrets & Authentication**
```bash
# Each service has its own secrets for security isolation
JWT_SECRET_KEY=service_specific_secret_key
DATABASE_PASSWORD=service_specific_password
REDIS_PASSWORD=service_specific_redis_password
```

#### **2. Service-Specific Configuration**
```bash
# Identity Service specific
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=auth@company.com  
SMTP_PASSWORD=secret_smtp_password

# Communication Service specific
SENDGRID_API_KEY=service_specific_sendgrid_key
TWILIO_ACCOUNT_SID=service_specific_twilio_sid
TWILIO_AUTH_TOKEN=service_specific_twilio_token

# Content Service specific
S3_BUCKET_NAME=content-service-bucket
S3_ACCESS_KEY=service_specific_s3_key
S3_SECRET_KEY=service_specific_s3_secret
```

#### **3. Database & Redis Instances**
```bash
# Each service has its own isolated data stores
# Identity Service
DATABASE_URL=postgresql+asyncpg://identity_user:identity_pass@identity-db:5432/identity_service
REDIS_URL=redis://identity-redis:6379/0

# Communication Service  
DATABASE_URL=postgresql+asyncpg://comm_user:comm_pass@communication-db:5432/communication_service
REDIS_URL=redis://communication-redis:6379/0

# Content Service
DATABASE_URL=postgresql+asyncpg://content_user:content_pass@content-db:5432/content_service
REDIS_URL=redis://content-redis:6379/0
```

#### **4. Business Logic Configuration**
```bash
# Service-specific business rules and thresholds
# Identity Service
MAX_LOGIN_ATTEMPTS=5
PASSWORD_RESET_EXPIRY_HOURS=1
MFA_CODE_EXPIRY_MINUTES=10

# Communication Service
EMAIL_BATCH_SIZE=100
SMS_RATE_LIMIT_PER_MINUTE=60
NOTIFICATION_RETRY_ATTEMPTS=3

# Content Service
MAX_FILE_SIZE_MB=100
SUPPORTED_FILE_TYPES=['pdf', 'jpg', 'png', 'docx']
FILE_RETENTION_DAYS=2555  # 7 years for medical compliance
```

---

## 🛠️ **Implementation Patterns**

### **Service Configuration Loading**
Each service follows this pattern:

```python
# service/app/core/config.py
import os
from pydantic import BaseSettings
from typing import List

class Settings(BaseSettings):
    # ============================================
    # SHARED CONFIGURATION (from .env.shared)
    # ============================================
    
    # Service Discovery
    IDENTITY_SERVICE_URL: str = os.getenv("IDENTITY_SERVICE_URL", "http://identity-service:8001")
    COMMUNICATION_SERVICE_URL: str = os.getenv("COMMUNICATION_SERVICE_URL", "http://communication-service:8003")
    
    # Security Standards
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    
    # Infrastructure Patterns
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    REDIS_MAX_CONNECTIONS: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
    
    # Logging Standards
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    
    # ============================================
    # SERVICE-SPECIFIC CONFIGURATION (.env)
    # ============================================
    
    # Service Secrets (NEVER shared)
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "service-specific-secret")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@db:5432/dbname")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # Service Business Logic
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "sendgrid")
    
    class Config:
        env_file = [".env.shared", ".env"]  # Load shared first, then service-specific
        env_file_encoding = "utf-8"

settings = Settings()
```

### **Docker Environment Loading**
```yaml
# docker-compose.yml
version: '3.8'

services:
  identity-service:
    build: ./identity-service
    env_file:
      - .env.shared        # Shared configuration
      - identity-service/.env   # Service-specific configuration
    environment:
      # Override patterns for service-specific database
      - DATABASE_URL=postgresql+asyncpg://identity_user:identity_pass@identity-db:5432/identity_service
```

---

## 🔄 **Configuration Update Workflow**

### **Shared Configuration Updates**
1. **Update Source**: Modify `.env.shared` in services root
2. **Validate Impact**: Check which services are affected
3. **Test Services**: Verify all services work with new shared config
4. **Deploy Coordination**: Update all services simultaneously
5. **Monitor**: Verify consistent behavior across services

### **Service-Specific Updates**
1. **Update Service**: Modify individual service `.env` files
2. **Test Isolation**: Verify change doesn't affect other services  
3. **Deploy Service**: Independent deployment of single service
4. **Validate Integration**: Confirm service still integrates properly

---

## 🚨 **Security Guidelines**

### **Secret Management**
- **NEVER** put secrets in `.env.shared`
- **ALWAYS** use service-specific secrets for isolation
- **ROTATE** secrets independently per service
- **ENCRYPT** secrets at rest and in transit

### **Service Discovery Security**  
```bash
# ✅ GOOD: Environment-based service discovery
IDENTITY_SERVICE_URL=http://identity-service:8001

# ❌ BAD: Hardcoded URLs in code
identity_url = "http://10.0.1.5:8001"
```

### **Configuration Validation**
```python
# Each service validates its configuration on startup
class Settings(BaseSettings):
    JWT_SECRET_KEY: str
    
    @validator('JWT_SECRET_KEY')
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v
    
    def validate_service_connectivity(self):
        """Validate that required services are reachable"""
        try:
            response = requests.get(f"{self.IDENTITY_SERVICE_URL}/health", timeout=5)
            if response.status_code != 200:
                raise ValueError(f"Identity service not accessible at {self.IDENTITY_SERVICE_URL}")
        except Exception as e:
            raise ValueError(f"Cannot reach identity service: {e}")
```

---

## 📊 **Configuration Examples**

### **Option A Architecture - Service-Specific Examples**

#### **Identity Service (.env)**
```bash
# Service-specific secrets
JWT_SECRET_KEY=identity_service_super_secret_key_32_chars_min
DATABASE_URL=postgresql+asyncpg://identity_user:identity_pass@identity-db:5432/identity_service
REDIS_URL=redis://identity-redis:6379/0

# Authentication-specific configuration  
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=auth@medicalhub.com
SMTP_PASSWORD=secret_gmail_app_password
FROM_EMAIL=auth@medicalhub.com
FROM_NAME=Medical Hub Authentication

# MFA configuration
MFA_CODE_EXPIRY_MINUTES=10
MAX_LOGIN_ATTEMPTS=5
PASSWORD_RESET_EXPIRY_HOURS=1

# Email templates
BASE_URL=https://medicalhub.com
```

#### **Communication Service (.env)**
```bash
# Service-specific secrets
JWT_SECRET_KEY=communication_service_different_secret_key  
DATABASE_URL=postgresql+asyncpg://comm_user:comm_pass@communication-db:5432/communication_service
REDIS_URL=redis://communication-redis:6379/0

# Business communication providers
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token

# Business notification settings
EMAIL_BATCH_SIZE=100
SMS_RATE_LIMIT_PER_MINUTE=60
NOTIFICATION_RETRY_ATTEMPTS=3
DEFAULT_FROM_EMAIL=notifications@medicalhub.com
```

---

## ✅ **Best Practices Summary**

### **DO:**
- ✅ Share infrastructure patterns and service discovery
- ✅ Share security standards and logging configuration  
- ✅ Share API conventions and development flags
- ✅ Use environment-based service discovery
- ✅ Validate configuration on service startup
- ✅ Load `.env.shared` first, then service-specific `.env`

### **DON'T:**
- ❌ Share secrets or authentication credentials
- ❌ Share business logic configuration between services
- ❌ Share database connection strings or Redis URLs
- ❌ Put service-specific settings in shared config
- ❌ Hardcode service URLs in application code
- ❌ Mix development and production configuration

---

**✅ Configuration sharing enables consistency while maintaining security and service isolation. Follow these patterns to ensure robust microservice coordination.**

---

**Maintained by**: Services Coordinator Agent  
**Last Updated**: 2025-09-09  
**Next Review**: When new services are added or configuration patterns change