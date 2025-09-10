# 🐳 ReactDjango Hub - Containerized Development

Complete Docker container setup for local development of all microservices.

## 📊 **Current Status: September 10, 2025**

### ✅ **Production Ready Services**
- **Identity Service**: 100% operational in containers
- **Infrastructure Services**: All databases, Redis, and MinIO running
- **Development Tooling**: Management scripts and health checks working

### 🚧 **In Progress**
- **Other Microservices**: Building communication, content, workflow services
- **Database Migrations**: Setting up proper Alembic configurations
- **Inter-service Communication**: Testing service-to-service connectivity

### 📋 **Next Sprint Priorities**
1. Complete containerization of remaining microservices
2. Fix database migration workflows for all services  
3. Add backend Django service with proper auth integration
4. Implement frontend service with full stack connectivity

## 🚀 Quick Start

### Prerequisites
- Docker (>= 20.10)
- Docker Compose (>= 1.29)
- Make (optional, for convenience commands)

### Start All Services
```bash
# Using the management script
./scripts/dev-stack.sh start

# OR using Make
make start

# OR using Docker Compose directly
docker-compose -f docker-compose.local.yml up -d
```

### Check Service Health
```bash
make health
# OR
./scripts/dev-stack.sh health
```

## 🏗️ Architecture

### Services Overview
| Service | Port | Purpose | Status | Dependencies |
|---------|------|---------|--------|--------------|
| **identity-service** | 8001 | Auth & Users | ✅ **Running** | identity-db, identity-redis |
| **communication-service** | 8002 | Notifications | 🔄 **Building** | communication-db, communication-redis, identity-service |
| **content-service** | 8003 | File Management | 🔄 **Building** | content-db, content-redis, minio, identity-service |
| **workflow-intelligence-service** | 8004 | AI Workflows | 🔄 **Building** | workflow-db, workflow-redis, identity-service |
| **backend** | 8000 | Django API | 🚧 **Pending** | main-db, main-redis, identity-service |
| **frontend** | 3000, 5173 | React UI | 🚧 **Pending** | backend, identity-service |

### Infrastructure Services
| Service | Port | Purpose | Status |
|---------|------|---------|--------|
| **main-db** | 5432 | Main PostgreSQL | ⚠️ **Port Conflict** |
| **identity-db** | 5433 | Identity PostgreSQL | ✅ **Running** |
| **communication-db** | 5434 | Communication PostgreSQL | ✅ **Running** |
| **content-db** | 5435 | Content PostgreSQL | ✅ **Running** |
| **workflow-db** | 5436 | Workflow PostgreSQL | ✅ **Running** |
| **main-redis** | 6379 | Main Redis | ⚠️ **Port Conflict** |
| **identity-redis** | 6380 | Identity Redis | ✅ **Running** |
| **communication-redis** | 6381 | Communication Redis | ✅ **Running** |
| **content-redis** | 6382 | Content Redis | ✅ **Running** |
| **workflow-redis** | 6383 | Workflow Redis | ✅ **Running** |
| **minio** | 9000, 9001 | S3-compatible storage | ✅ **Running** |

## 📋 Management Commands

### Using Make (Recommended)
```bash
make help              # Show all available commands
make start             # Start all services
make stop              # Stop all services  
make restart           # Restart all services
make build             # Build all images
make status            # Show service status
make health            # Check service health
make services          # Show service URLs
make logs              # Show all logs
make test              # Run tests in all services
make clean             # Remove containers and volumes
```

### Using the Management Script
```bash
./scripts/dev-stack.sh help      # Show help
./scripts/dev-stack.sh start     # Start all services
./scripts/dev-stack.sh stop      # Stop all services
./scripts/dev-stack.sh health    # Health check
./scripts/dev-stack.sh logs      # Show logs
./scripts/dev-stack.sh services  # Show URLs
```

### Service-Specific Commands
```bash
# Shell access
make shell-backend
make shell-frontend
make shell-identity
./scripts/dev-stack.sh shell identity-service

# Service-specific logs
make logs-service SERVICE=backend
./scripts/dev-stack.sh logs backend

# Database operations
make db-migrate        # Run Django migrations
make db-shell         # Django database shell
```

## 🔍 Service URLs

### Application URLs
- **Frontend**: http://localhost:3000 (React) / http://localhost:5173 (Vite)
- **Backend API**: http://localhost:8000/api/docs/
- **Identity Service**: http://localhost:8001/docs
- **Communication Service**: http://localhost:8002/docs  
- **Content Service**: http://localhost:8003/docs
- **Workflow Service**: http://localhost:8004/docs

### Infrastructure URLs
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **PostgreSQL**: localhost:5432-5436 (various services)
- **Redis**: localhost:6379-6383 (various services)

## ✅ Health Checks

All services include comprehensive health checks:

### Automated Health Monitoring
```bash
# Check all services
make health

# Continuous health monitoring
watch -n 5 'make health'
```

### Health Check Endpoints
- Identity Service: `GET /health`
- Communication Service: `GET /health`
- Content Service: `GET /health` 
- Workflow Service: `GET /health`
- Backend: `GET /api/health/`
- Frontend: `GET /` (React app)

### Health Check Features
- **Database connectivity** verification
- **Redis connectivity** verification  
- **Service dependencies** validation
- **API endpoint** responsiveness
- **Resource utilization** monitoring

## 🧪 Testing

### Run All Tests
```bash
make test
# OR
./scripts/dev-stack.sh test
```

### Service-Specific Testing
```bash
# Identity Service
docker-compose -f docker-compose.local.yml exec identity-service pytest -v

# Communication Service  
docker-compose -f docker-compose.local.yml exec communication-service pytest -v

# Backend (Django)
docker-compose -f docker-compose.local.yml exec backend python manage.py test

# Frontend (React)
docker-compose -f docker-compose.local.yml exec frontend npm test -- --watchAll=false
```

## 🔧 Development Workflow

### 1. Initial Setup
```bash
# Clone and enter project
git clone <repo> && cd ReactDjango-Hub

# Start all services
make start

# Wait for services to be ready
make health

# View service URLs
make services
```

### 2. Development Cycle
```bash
# Check status
make status

# View logs during development
make logs-service SERVICE=backend

# Run tests
make test

# Make code changes (files are mounted as volumes)

# Restart specific service if needed
docker-compose -f docker-compose.local.yml restart backend
```

### 3. Debugging
```bash
# Shell access for debugging
make shell-backend
make shell-identity

# Database access
make db-shell

# View detailed logs
make logs-service SERVICE=identity-service
```

## 🌐 Service Communication

### Internal Network
- All services communicate via `microservices_network` bridge network
- Internal URLs use container names: `http://identity-service:8001`
- Database connections use container names: `identity-db:5432`

### External Access
- Services expose ports for external access
- Frontend connects to services via localhost URLs
- API documentation available at service URLs

### Environment Configuration
- Configuration in `.env.local` file
- Service discovery via environment variables
- Consistent naming convention across services

## 🔒 Security Features

### Development Security
- Isolated Docker network for services
- Non-root containers where possible
- Resource limits and health checks
- Separate databases per service

### Configuration Management
- Environment-specific configuration
- Secrets isolated from code
- Development vs production settings

## 📊 Monitoring & Logging

### Log Management
```bash
# All services logs
make logs

# Service-specific logs
./scripts/dev-stack.sh logs backend

# Follow logs in real-time
docker-compose -f docker-compose.local.yml logs -f backend
```

### Service Monitoring
```bash
# Resource usage
docker stats

# Service health
make health

# Container status
make status
```

## 🚨 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check for port conflicts
netstat -tulpn | grep :8000

# Clean and rebuild
make clean
make build
make start
```

#### Database Connection Issues
```bash
# Check database health
docker-compose -f docker-compose.local.yml exec main-db pg_isready -U postgres

# Reset databases
make clean
make start
```

#### Service Communication Issues
```bash
# Check network connectivity
docker network ls
docker network inspect microservices_network

# Verify service discovery
docker-compose -f docker-compose.local.yml exec backend nslookup identity-service
```

### Performance Issues
```bash
# Check resource usage
docker stats --no-stream

# Adjust resource limits in docker-compose.local.yml
# Restart specific services
docker-compose -f docker-compose.local.yml restart <service>
```

### Log Analysis
```bash
# Search logs for errors
./scripts/dev-stack.sh logs | grep ERROR

# Service-specific error analysis
docker-compose -f docker-compose.local.yml logs backend | grep -i error
```

## 🔄 Advanced Operations

### Scaling Services
```bash
# Scale specific service
docker-compose -f docker-compose.local.yml up -d --scale backend=2

# Load balancing requires additional configuration
```

### Data Management
```bash
# Database backups
docker-compose -f docker-compose.local.yml exec main-db pg_dump -U postgres reactdjango_hub > backup.sql

# Volume management
docker volume ls | grep reactdjango-hub
```

### Custom Configuration
```bash
# Override environment variables
cp .env.local .env.local.custom
# Edit .env.local.custom
docker-compose -f docker-compose.local.yml --env-file .env.local.custom up -d
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Service-Specific Documentation](./services/)
- [Deployment Guide](./infrastructure/README.md)
- [API Documentation](http://localhost:8000/api/docs/) (when running)

---

For questions or issues, check the service logs and health status first, then consult the troubleshooting section above.