# Local Development Setup (No Docker Required)

This guide explains how to run all 4 microservices locally without Docker dependencies for simplified development.

## 🎯 Overview

The microservices have been configured to run locally by default, with Docker as an optional configuration. This approach makes development faster and simpler while preserving the ability to use Docker when needed.

### Services Architecture

| Service | Port | Purpose | Dependencies |
|---------|------|---------|--------------|
| **Identity Service** | 8001 | Authentication, Users, Organizations, MFA | PostgreSQL, Redis |
| **Content Service** | 8002 | Document Management, Search, Audit | PostgreSQL, Redis, Identity Service |
| **Communication Service** | 8003 | Notifications, Messaging, Multi-channel | PostgreSQL, Redis, Identity Service |
| **Workflow Intelligence** | 8004 | Process Automation, AI Integration | PostgreSQL, Redis, All Services |
| **API Gateway (Kong)** | 8080 | Load Balancing, Routing, Security | All Services |

## 📋 Prerequisites

### 1. System Requirements

- **Python 3.13+** with pip
- **PostgreSQL 17** (running on localhost:5432)
- **Redis** (running on localhost:6379) - optional but recommended
- **Kong API Gateway** (optional, for API routing)

### 2. macOS Installation

```bash
# Install PostgreSQL
brew install postgresql
brew services start postgresql

# Install Redis (optional)
brew install redis
brew services start redis

# Install Kong (optional)
brew install kong

# Verify installations
psql --version
redis-cli --version
kong version
```

### 3. Linux Installation

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib redis-server

# Start services
sudo systemctl start postgresql
sudo systemctl start redis-server

# Kong installation (optional)
# Follow: https://docs.konghq.com/gateway/latest/install/linux/
```

## 🚀 Quick Start

### Option 1: Start All Services (Recommended)

```bash
cd services
./dev-start-local.sh
```

This script will:
- ✅ Check all prerequisites (PostgreSQL, Redis, Python)
- ✅ Create virtual environments for each service
- ✅ Install dependencies automatically  
- ✅ Create databases if they don't exist
- ✅ Start all services in dependency order
- ✅ Perform health checks
- ✅ Display service URLs and documentation links

### Option 2: Start Services Individually

```bash
# 1. Identity Service (start first)
cd services/identity-service
./dev-start.sh

# 2. Content Service (in new terminal)
cd services/content-service  
./dev-start.sh

# 3. Communication Service (in new terminal)
cd services/communication-service
./dev-start.sh

# 4. Workflow Intelligence Service (in new terminal)
cd services/workflow-intelligence-service
./dev-start.sh
```

### Option 3: API Gateway (Kong) Setup

```bash
# After all services are running
cd services/api-gateway
./start-kong-local.sh
```

## 🛑 Stopping Services

```bash
cd services
./dev-stop-local.sh
```

Or manually:
- Press `Ctrl+C` in each service terminal
- Kill processes: `lsof -ti:8001,8002,8003,8004 | xargs kill`

## 🔧 Configuration

### Environment Variables

The services automatically detect the environment and use appropriate defaults:

| Variable | Default (Local) | Docker Override |
|----------|-----------------|-----------------|
| `USE_DOCKER` | `false` | `true` |
| `DATABASE_URL` | `postgresql://user@localhost:5432/dbname` | `postgresql://user:pass@service:5432/dbname` |
| `REDIS_URL` | `redis://localhost:6379/0` | `redis://service:6379/0` |
| `IDENTITY_SERVICE_URL` | `http://localhost:8001` | `http://identity-service:8001` |

### Database Configuration

Each service creates its own database:

```sql
-- Databases created automatically
auth_service                    -- Identity Service
content_service                 -- Content Service  
communication_service           -- Communication Service
workflow_intelligence_service   -- Workflow Intelligence Service
```

### Local Development Defaults

- **PostgreSQL**: Uses your local user account (no password required)
- **Redis**: Optional, services degrade gracefully if not available
- **Inter-service Communication**: Direct localhost HTTP calls
- **File Storage**: Local filesystem in each service directory

## 📊 Service URLs

### Direct Service Access

| Service | Base URL | Health Check | API Docs |
|---------|----------|--------------|----------|
| Identity | http://localhost:8001 | /health | /docs |
| Content | http://localhost:8002 | /health | /docs |
| Communication | http://localhost:8003 | /health | /docs |
| Workflow | http://localhost:8004 | /health | /docs |

### Via API Gateway (if running)

| Service | Gateway URL | Direct URL |
|---------|------------|------------|
| Identity | http://localhost:8080/api/v1/auth | http://localhost:8001/auth |
| Content | http://localhost:8080/api/v1/documents | http://localhost:8002/api/v1/documents |
| Communication | http://localhost:8080/api/v1/notifications | http://localhost:8003/api/v1/notifications |
| Workflow | http://localhost:8080/api/v1/workflows | http://localhost:8004/api/v1/workflows |

## 🔍 Development Workflow

### Typical Development Session

```bash
# 1. Start all services
cd services
./dev-start-local.sh

# 2. Develop and test
# Services auto-reload on code changes (uvicorn --reload)

# 3. Check service health
curl http://localhost:8001/health
curl http://localhost:8002/health  
curl http://localhost:8003/health
curl http://localhost:8004/health

# 4. Stop when done
./dev-stop-local.sh
```

### Working with Individual Services

```bash
# Work on identity service only
cd services/identity-service
source venv/bin/activate
python main.py

# Check logs in real-time
tail -f services/identity-service/identity-service.log
```

### Database Operations

```bash
# Connect to service databases
psql auth_service                    # Identity Service
psql content_service                 # Content Service
psql communication_service           # Communication Service  
psql workflow_intelligence_service   # Workflow Intelligence

# Reset a database (careful!)
dropdb content_service && createdb content_service
```

## 🐛 Troubleshooting

### Common Issues

#### 1. PostgreSQL Connection Errors

```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL if needed
brew services start postgresql  # macOS
sudo systemctl start postgresql # Linux

# Check PostgreSQL status
brew services list | grep postgresql  # macOS
sudo systemctl status postgresql      # Linux
```

#### 2. Port Already in Use

```bash
# Find what's using a port
lsof -i :8001

# Kill process on port
lsof -ti:8001 | xargs kill
```

#### 3. Database Permission Issues

```bash
# Create PostgreSQL user if needed
createuser -s $(whoami)

# Or connect as postgres user
sudo -u postgres createuser -s $(whoami)
```

#### 4. Missing Dependencies

```bash
# Reinstall dependencies for a service
cd services/identity-service
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 5. Redis Connection Issues

```bash
# Check if Redis is running
redis-cli ping

# Start Redis if needed
brew services start redis  # macOS
sudo systemctl start redis # Linux

# Services work without Redis, but with degraded functionality
```

### Service-Specific Logs

Each service creates its own log file:

```bash
# View service logs
tail -f services/identity-service/identity-service.log
tail -f services/content-service/content-service.log
tail -f services/communication-service/communication-service.log
tail -f services/workflow-intelligence-service/workflow-intelligence-service.log
```

### Health Check Status

```bash
# Check all services
curl -s http://localhost:8001/health | jq
curl -s http://localhost:8002/health | jq  
curl -s http://localhost:8003/health | jq
curl -s http://localhost:8004/health | jq

# Via API Gateway (if running)
curl -s http://localhost:8080/health | jq
```

## 🔄 Docker Compatibility

The services maintain full Docker compatibility. To use Docker:

```bash
# Set Docker mode
export USE_DOCKER=true

# Use Docker Compose
cd services
docker-compose up -d

# Or use the original Docker setup
docker-compose -f docker/development/docker-compose.yml up -d
```

## 🧪 Testing

### Running Tests

```bash
# Test individual services
cd services/identity-service
source venv/bin/activate
python -m pytest

# Test all services
cd services
for service in */; do
    if [ -f "$service/requirements.txt" ]; then
        echo "Testing $service"
        (cd "$service" && source venv/bin/activate && python -m pytest)
    fi
done
```

### Integration Testing

```bash
# All services must be running
./dev-start-local.sh

# Test service communication
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","first_name":"Test","last_name":"User"}'

# Test via API Gateway
curl -X GET http://localhost:8080/health
```

## 📈 Performance Considerations

### Local Development Optimizations

- **Auto-reload**: Services use `uvicorn --reload` for instant code changes
- **Database pooling**: Optimized connection pools for local development
- **Reduced logging**: Less verbose logging in development mode
- **No containerization overhead**: Direct Python execution is faster

### Resource Usage

| Service | Memory | CPU | Notes |
|---------|--------|-----|-------|
| Identity | ~50MB | Low | Lightweight authentication |
| Content | ~100MB | Medium | File processing overhead |
| Communication | ~75MB | Low-Medium | Queue processing |
| Workflow | ~80MB | Medium | AI integration |
| **Total** | **~300MB** | **Light** | Much lighter than Docker |

## 🚀 Production Considerations

This local setup is designed for development. For production:

1. **Use Docker**: Better isolation and consistency
2. **External Databases**: Managed PostgreSQL and Redis
3. **Load Balancing**: Multiple service instances
4. **API Gateway**: Kong with production plugins
5. **Monitoring**: Prometheus, Grafana, Jaeger
6. **Security**: TLS, secrets management, network policies

## 📚 Next Steps

1. **Frontend Development**: Connect React app to http://localhost:8001 (or http://localhost:8080 via gateway)
2. **API Integration**: Use service documentation at /docs endpoints
3. **Database Migrations**: Services auto-create tables on startup
4. **Custom Configuration**: Create `.env.local` files in service directories
5. **Service Extension**: Add new endpoints following existing patterns

---

🎉 **Happy Development!** You now have a fully functional microservices environment running locally without Docker dependencies.