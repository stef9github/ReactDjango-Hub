# Docker Configuration Standardization Guide

**For**: Content Service Agent, Workflow Intelligence Service Agent  
**Priority**: 🟡 **HIGH** - Deployment consistency requirement  
**Current Issue**: Content and Workflow services missing Docker configuration  
**Services Coordinator**: Standardization requirement for production deployment

---

## 🎯 **Current Status Analysis**

### **✅ Services with Docker Configuration**
- **Identity Service**: Complete Docker configuration ✅
- **Communication Service**: Has docker configuration ✅

### **❌ Services Missing Docker Configuration**
- **Content Service**: Missing docker-compose.yml ❌
- **Workflow Intelligence Service**: Missing docker-compose.yml ❌

---

## 🐳 **Standard Docker Configuration Templates**

### **Content Service Docker Configuration**

Create `content-service/docker-compose.yml`:

```yaml
version: '3.8'

services:
  content-service:
    build: 
      context: .
      dockerfile: Dockerfile
    container_name: content-service
    ports:
      - "8002:8002"
    environment:
      - SERVICE_NAME=content-service
      - SERVICE_VERSION=1.0.0
      - SERVICE_PORT=8002
      - DATABASE_URL=postgresql+asyncpg://content_user:content_pass@content-db:5432/content_service
      - REDIS_URL=redis://content-redis:6379/0
      - IDENTITY_SERVICE_URL=http://identity-service:8001
      - LOG_LEVEL=INFO
    env_file:
      - ../.env.shared    # Load shared configuration first
      - .env              # Then service-specific configuration
    depends_on:
      - content-db
      - content-redis
    volumes:
      - content_uploads:/app/uploads
      - content_storage:/app/storage
      - content_logs:/app/logs
    restart: unless-stopped
    networks:
      - content-network
      - services-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  content-db:
    image: postgres:17-alpine
    container_name: content-db
    environment:
      - POSTGRES_DB=content_service
      - POSTGRES_USER=content_user
      - POSTGRES_PASSWORD=content_pass
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8
    ports:
      - "5434:5432"  # External port for development access
    volumes:
      - content_db_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d  # Initialization scripts
    restart: unless-stopped
    networks:
      - content-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U content_user -d content_service"]
      interval: 10s
      timeout: 5s
      retries: 5

  content-redis:
    image: redis:7-alpine
    container_name: content-redis
    command: redis-server --appendonly yes --requirepass content_redis_password
    ports:
      - "6381:6379"  # External port for development access
    volumes:
      - content_redis_data:/data
      - ./redis/redis.conf:/etc/redis/redis.conf
    restart: unless-stopped
    networks:
      - content-network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "content_redis_password", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

volumes:
  content_db_data:
    driver: local
  content_redis_data:
    driver: local
  content_uploads:
    driver: local
  content_storage:
    driver: local
  content_logs:
    driver: local

networks:
  content-network:
    driver: bridge
  services-network:
    external: true  # Shared network for inter-service communication
```

### **Content Service Dockerfile**

Create `content-service/Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        curl \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/uploads /app/storage /app/logs

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Expose port
EXPOSE 8002

# Run the application
CMD ["python", "main.py"]
```

---

### **Workflow Intelligence Service Docker Configuration**

Create `workflow-intelligence-service/docker-compose.yml`:

```yaml
version: '3.8'

services:
  workflow-service:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: workflow-intelligence-service
    ports:
      - "8004:8004"
    environment:
      - SERVICE_NAME=workflow-intelligence-service
      - SERVICE_VERSION=1.0.0
      - SERVICE_PORT=8004
      - DATABASE_URL=sqlite:///./workflow.db  # Use SQLite as currently implemented
      - REDIS_URL=redis://workflow-redis:6379/0
      - IDENTITY_SERVICE_URL=http://identity-service:8001
      - CONTENT_SERVICE_URL=http://content-service:8002
      - COMMUNICATION_SERVICE_URL=http://communication-service:8003
      - LOG_LEVEL=INFO
    env_file:
      - ../.env.shared    # Load shared configuration first
      - .env              # Then service-specific configuration
    depends_on:
      - workflow-redis
      # Note: No database dependency since using SQLite
    volumes:
      - workflow_data:/app/data
      - workflow_logs:/app/logs
      - ./workflow.db:/app/workflow.db  # Mount SQLite database file
    restart: unless-stopped
    networks:
      - workflow-network
      - services-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  workflow-redis:
    image: redis:7-alpine
    container_name: workflow-redis
    command: redis-server --appendonly yes --requirepass workflow_redis_password
    ports:
      - "6383:6379"  # External port for development access
    volumes:
      - workflow_redis_data:/data
      - ./redis/redis.conf:/etc/redis/redis.conf
    restart: unless-stopped
    networks:
      - workflow-network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "workflow_redis_password", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  # Optional: PostgreSQL for production (when migrating from SQLite)
  workflow-db:
    image: postgres:17-alpine
    container_name: workflow-db
    environment:
      - POSTGRES_DB=workflow_service
      - POSTGRES_USER=workflow_user
      - POSTGRES_PASSWORD=workflow_pass
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8
    ports:
      - "5436:5432"  # External port for development access
    volumes:
      - workflow_db_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d
    restart: unless-stopped
    networks:
      - workflow-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U workflow_user -d workflow_service"]
      interval: 10s
      timeout: 5s
      retries: 5
    profiles:
      - postgres  # Only start when explicitly requested

volumes:
  workflow_data:
    driver: local
  workflow_redis_data:
    driver: local
  workflow_db_data:
    driver: local
  workflow_logs:
    driver: local

networks:
  workflow-network:
    driver: bridge
  services-network:
    external: true  # Shared network for inter-service communication
```

### **Workflow Intelligence Service Dockerfile**

Create `workflow-intelligence-service/Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        curl \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Initialize SQLite database if it doesn't exist
RUN python -c "import sqlite3; sqlite3.connect('/app/workflow.db').close()"

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# Expose port
EXPOSE 8004

# Run the application
CMD ["python", "main.py"]
```

---

## 🚀 **Complete Stack Configuration**

### **Root Level docker-compose.yml**

Create or update `services/docker-compose.yml` for the complete stack:

```yaml
version: '3.8'

services:
  # Identity Service (existing)
  identity-service:
    build: ./identity-service
    container_name: identity-service
    ports:
      - "8001:8001"
    environment:
      - SERVICE_NAME=identity-service
      - SERVICE_PORT=8001
    env_file:
      - .env.shared
      - identity-service/.env
    depends_on:
      - identity-db
      - identity-redis
    networks:
      - services-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Communication Service (existing)
  communication-service:
    build: ./communication-service
    container_name: communication-service
    ports:
      - "8003:8003"
    environment:
      - SERVICE_NAME=communication-service
      - SERVICE_PORT=8003
      - IDENTITY_SERVICE_URL=http://identity-service:8001
    env_file:
      - .env.shared
      - communication-service/.env
    depends_on:
      - communication-db
      - communication-redis
      - identity-service
    networks:
      - services-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Content Service (NEW)
  content-service:
    build: ./content-service
    container_name: content-service
    ports:
      - "8002:8002"
    environment:
      - SERVICE_NAME=content-service
      - SERVICE_PORT=8002
      - IDENTITY_SERVICE_URL=http://identity-service:8001
    env_file:
      - .env.shared
      - content-service/.env
    depends_on:
      - content-db
      - content-redis
      - identity-service
    networks:
      - services-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Workflow Intelligence Service (NEW)
  workflow-intelligence-service:
    build: ./workflow-intelligence-service
    container_name: workflow-intelligence-service
    ports:
      - "8004:8004"
    environment:
      - SERVICE_NAME=workflow-intelligence-service
      - SERVICE_PORT=8004
      - IDENTITY_SERVICE_URL=http://identity-service:8001
      - CONTENT_SERVICE_URL=http://content-service:8002
      - COMMUNICATION_SERVICE_URL=http://communication-service:8003
    env_file:
      - .env.shared
      - workflow-intelligence-service/.env
    depends_on:
      - workflow-redis
      - identity-service
      - content-service
      - communication-service
    networks:
      - services-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Databases
  identity-db:
    image: postgres:17-alpine
    container_name: identity-db
    environment:
      - POSTGRES_DB=identity_service
      - POSTGRES_USER=identity_user
      - POSTGRES_PASSWORD=identity_pass
    ports:
      - "5433:5432"
    volumes:
      - identity_db_data:/var/lib/postgresql/data
    networks:
      - services-network

  communication-db:
    image: postgres:17-alpine
    container_name: communication-db
    environment:
      - POSTGRES_DB=communication_service
      - POSTGRES_USER=communication_user
      - POSTGRES_PASSWORD=communication_pass
    ports:
      - "5435:5432"
    volumes:
      - communication_db_data:/var/lib/postgresql/data
    networks:
      - services-network

  content-db:
    image: postgres:17-alpine
    container_name: content-db
    environment:
      - POSTGRES_DB=content_service
      - POSTGRES_USER=content_user
      - POSTGRES_PASSWORD=content_pass
    ports:
      - "5434:5432"
    volumes:
      - content_db_data:/var/lib/postgresql/data
    networks:
      - services-network

  # Redis instances
  identity-redis:
    image: redis:7-alpine
    container_name: identity-redis
    ports:
      - "6380:6379"
    volumes:
      - identity_redis_data:/data
    networks:
      - services-network

  communication-redis:
    image: redis:7-alpine
    container_name: communication-redis
    ports:
      - "6382:6379"
    volumes:
      - communication_redis_data:/data
    networks:
      - services-network

  content-redis:
    image: redis:7-alpine
    container_name: content-redis
    ports:
      - "6381:6379"
    volumes:
      - content_redis_data:/data
    networks:
      - services-network

  workflow-redis:
    image: redis:7-alpine
    container_name: workflow-redis
    ports:
      - "6383:6379"
    volumes:
      - workflow_redis_data:/data
    networks:
      - services-network

volumes:
  identity_db_data:
  communication_db_data:
  content_db_data:
  identity_redis_data:
  communication_redis_data:
  content_redis_data:
  workflow_redis_data:

networks:
  services-network:
    driver: bridge
```

---

## 🔧 **Environment Configuration Files**

### **Service-Specific .env Files**

#### **Content Service (.env)**
```bash
# Service-specific secrets
JWT_SECRET_KEY=content_service_super_secret_key_32_chars_min
DATABASE_URL=postgresql+asyncpg://content_user:content_pass@content-db:5432/content_service
REDIS_URL=redis://content-redis:6379/0

# Content-specific configuration
MAX_FILE_SIZE_MB=100
SUPPORTED_FILE_TYPES=pdf,jpg,jpeg,png,docx,xlsx,pptx,txt
FILE_RETENTION_DAYS=2555  # 7 years for compliance
STORAGE_PATH=/app/storage
UPLOAD_PATH=/app/uploads

# OCR and processing
OCR_ENABLED=true
THUMBNAIL_GENERATION=true
TEXT_EXTRACTION=true

# Search configuration
SEARCH_INDEX_ENABLED=true
FULL_TEXT_SEARCH=true
```

#### **Workflow Intelligence Service (.env)**
```bash
# Service-specific secrets  
JWT_SECRET_KEY=workflow_service_super_secret_key_32_chars_min
DATABASE_URL=sqlite:///./workflow.db  # Currently using SQLite
REDIS_URL=redis://workflow-redis:6379/0

# Workflow engine configuration
MAX_WORKFLOW_INSTANCES=1000
WORKFLOW_TIMEOUT_HOURS=24
AUTOMATIC_CLEANUP_ENABLED=true

# AI integration
AI_PROVIDER=openai  # or anthropic
AI_ENABLED=true
AI_MAX_TOKENS=4000
AI_TEMPERATURE=0.7

# SLA monitoring
SLA_MONITORING_ENABLED=true
SLA_CHECK_INTERVAL_MINUTES=30
ALERT_ON_SLA_BREACH=true
```

---

## 🚀 **Usage Instructions**

### **Starting Individual Services**

```bash
# Start Content Service with dependencies
cd content-service
docker-compose up -d

# Start Workflow Intelligence Service with dependencies
cd workflow-intelligence-service
docker-compose up -d
```

### **Starting Complete Stack**

```bash
# Start all services from root
cd services
docker-compose up -d

# Start specific services
docker-compose up -d identity-service content-service

# View logs
docker-compose logs -f content-service
docker-compose logs -f workflow-intelligence-service

# Check health
curl http://localhost:8002/health  # Content Service
curl http://localhost:8004/health  # Workflow Service
```

### **Development Commands**

```bash
# Build and start in development mode
docker-compose up --build -d

# Rebuild specific service
docker-compose build content-service
docker-compose up -d content-service

# Enter service container for debugging
docker-compose exec content-service bash
docker-compose exec workflow-intelligence-service bash

# View service logs in real-time
docker-compose logs -f content-service workflow-intelligence-service

# Stop and remove all containers
docker-compose down

# Stop and remove with volumes (careful - deletes data!)
docker-compose down -v
```

### **Production Commands**

```bash
# Production build and deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services (if needed)
docker-compose up -d --scale content-service=2

# Update services (rolling update)
docker-compose pull
docker-compose up -d --no-deps content-service
```

---

## 🔍 **Monitoring and Health Checks**

### **Health Check URLs**
```bash
# Check all services
curl http://localhost:8001/health  # Identity Service
curl http://localhost:8002/health  # Content Service  
curl http://localhost:8003/health  # Communication Service
curl http://localhost:8004/health  # Workflow Intelligence Service

# Check databases
docker-compose exec content-db pg_isready -U content_user
docker-compose exec workflow-redis redis-cli ping

# Check container status
docker-compose ps
docker-compose top
```

### **Log Monitoring**

```bash
# Follow logs for all services
docker-compose logs -f

# Follow logs for specific services
docker-compose logs -f content-service workflow-intelligence-service

# View recent logs
docker-compose logs --tail=100 content-service

# Export logs
docker-compose logs --no-color > services.log
```

---

## ✅ **Validation Checklist**

After implementing Docker configuration:

### **Content Service**
- [ ] `docker-compose.yml` created with all required services
- [ ] `Dockerfile` created with proper Python environment
- [ ] `.env` file configured with service-specific settings
- [ ] PostgreSQL database container configured
- [ ] Redis cache container configured  
- [ ] Health checks implemented and working
- [ ] File upload volumes properly mounted
- [ ] Service starts successfully with `docker-compose up -d`
- [ ] `/health` endpoint returns 200 OK
- [ ] Service accessible at http://localhost:8002

### **Workflow Intelligence Service**
- [ ] `docker-compose.yml` created with SQLite support
- [ ] `Dockerfile` created with proper Python environment
- [ ] `.env` file configured with workflow-specific settings
- [ ] Redis container configured for caching
- [ ] Health checks implemented and working
- [ ] SQLite database file properly mounted
- [ ] Service starts successfully with `docker-compose up -d`
- [ ] `/health` endpoint returns 200 OK
- [ ] Service accessible at http://localhost:8004

### **Complete Stack**
- [ ] Root `docker-compose.yml` includes all services
- [ ] All services can communicate with each other
- [ ] Shared network configuration working
- [ ] All health checks passing
- [ ] Services start in correct dependency order
- [ ] Environment configuration loading properly

---

## 🆘 **Troubleshooting**

### **Common Issues**

**Issue**: Service fails to connect to database  
**Solution**: Check database container is running and environment variables are correct

**Issue**: Port already in use  
**Solution**: Change port mapping in docker-compose.yml or stop conflicting services

**Issue**: Permission denied errors  
**Solution**: Ensure proper user permissions in Dockerfile

**Issue**: Service health check failing  
**Solution**: Check service is properly starting and health endpoint is accessible

**Issue**: Volume mount issues  
**Solution**: Ensure directories exist and have proper permissions

### **Debug Commands**

```bash
# Check container status
docker-compose ps

# View container logs
docker-compose logs service-name

# Enter container for debugging
docker-compose exec service-name bash

# Check network connectivity
docker-compose exec service-name ping other-service-name

# Restart specific service
docker-compose restart service-name

# Rebuild and restart
docker-compose up --build -d service-name
```

---

## 📞 **Implementation Support**

**Questions**: Add to `COORDINATION_ISSUES.md` if you encounter Docker configuration problems  
**Testing**: Use health endpoints and service integration tests  
**Documentation**: Update your service README with Docker instructions

---

**🎯 After implementing Docker configuration, all microservices will have consistent, production-ready deployment capabilities with proper service isolation and inter-service communication!**

---

**Document Maintainer**: Services Coordinator Agent  
**Last Updated**: 2025-09-09  
**Next Review**: After all services implement Docker configuration