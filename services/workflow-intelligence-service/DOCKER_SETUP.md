# Docker Configuration for Workflow Intelligence Service

## 🐳 **Configuration Overview**

The Workflow Intelligence Service now has complete Docker configuration following the standardized deployment patterns for ReactDjango Hub.

### **Created Files**

✅ **Dockerfile** - Python 3.13-slim with security best practices  
✅ **docker-compose.yml** - Complete service orchestration with SQLite + Redis  
✅ **.env** - Service-specific environment configuration  
✅ **redis/redis.conf** - Redis configuration with password authentication  
✅ **validate_docker_config.py** - Configuration validation script  

### **Key Features**

- **Python 3.13 Runtime** with optimized container size
- **Non-root User** for enhanced security  
- **Health Checks** with automatic restart policies
- **SQLite Database** with persistent volume mounting
- **Redis Cache** with password authentication
- **Network Isolation** with shared services network
- **Environment Configuration** with shared and service-specific variables

## 🚀 **Quick Start**

### **1. Create Shared Network**
```bash
docker network create services-network
```

### **2. Start the Service**
```bash
# From workflow-intelligence-service directory
docker-compose up --build -d
```

### **3. Verify Health**
```bash
curl http://localhost:8004/health
```

### **4. View Logs**
```bash
docker-compose logs -f workflow-service
```

## 📋 **Service Architecture**

### **Services Defined**
- **workflow-service** - Main application (Port 8004)
- **workflow-redis** - Cache layer (Port 6383)
- **workflow-db** - Optional PostgreSQL (Port 5436, profile-based)

### **Volumes**
- `workflow_data` - Application data persistence
- `workflow_logs` - Log file persistence  
- `workflow_redis_data` - Redis data persistence
- `workflow_db_data` - PostgreSQL data persistence

### **Networks**
- `workflow-network` - Internal service communication
- `services-network` - Inter-service communication (external)

## ⚙️ **Configuration Details**

### **Environment Variables**
- **JWT_SECRET_KEY** - Service-specific JWT signing key
- **DATABASE_URL** - SQLite connection (upgradeable to PostgreSQL)
- **REDIS_URL** - Redis connection with authentication
- **AI Integration** - OpenAI/Anthropic API configuration
- **SLA Monitoring** - Workflow timeout and cleanup settings

### **Health Checks**
- **Application**: HTTP GET /health every 30s
- **Redis**: Redis CLI ping with auth every 10s
- **PostgreSQL**: pg_isready check every 10s (when enabled)

## 🔧 **Development Commands**

```bash
# Build and start in development
docker-compose up --build -d

# View real-time logs
docker-compose logs -f workflow-service workflow-redis

# Enter container for debugging
docker-compose exec workflow-service bash

# Restart specific service
docker-compose restart workflow-service

# Stop all services
docker-compose down

# Stop and remove volumes (careful!)
docker-compose down -v
```

## 🏗️ **Production Considerations**

### **Database Migration**
To migrate from SQLite to PostgreSQL:
1. Uncomment PostgreSQL configuration in .env
2. Enable the postgres profile: `docker-compose --profile postgres up -d`
3. Run data migration scripts
4. Update DATABASE_URL in environment

### **Scaling**
```bash
# Scale the main service (if needed)
docker-compose up -d --scale workflow-service=2
```

### **Monitoring**
- Health checks are configured for all services
- Logs are persisted in dedicated volumes
- Metrics can be collected via health endpoints

## 🔒 **Security Features**

- Non-root container execution
- Password-protected Redis
- Environment variable isolation
- Network segmentation
- Resource limits (can be added via deploy section)

## ✅ **Validation Checklist**

- [x] Dockerfile follows Python 3.13 best practices
- [x] docker-compose.yml includes all required services
- [x] .env contains all necessary configuration
- [x] Redis configuration with authentication
- [x] Health checks implemented for all services
- [x] Volume mounts for data persistence
- [x] Network configuration for service discovery
- [x] Main.py compatible with Docker execution

## 📞 **Support & Troubleshooting**

**Common Issues:**
- **Port conflicts**: Adjust port mappings in docker-compose.yml
- **Permission errors**: Ensure proper file ownership
- **Network issues**: Verify services-network exists
- **Health check failures**: Check service startup logs

**Debug Commands:**
```bash
docker-compose ps                    # Check container status
docker-compose logs service-name     # View service logs
docker-compose exec service bash    # Enter container
docker network ls                   # Check networks
```

---

**🎯 The Workflow Intelligence Service is now Docker-ready with production-grade configuration!**

Next steps: Test with full microservices stack integration.