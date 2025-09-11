# ReactDjango Hub Microservices - Quick Start Guide

## Prerequisites

Before starting, ensure you have:
- Docker Desktop installed and running
- Docker Compose installed (usually comes with Docker Desktop)
- At least 4GB of free RAM
- Ports 3000, 5173, 8000-8004, 8445, 5433-5436, 6380-6383 available

## 🚀 Quick Start (3 Steps)

### Step 1: Start All Services

```bash
# Navigate to services directory
cd services

# Start everything with one command
./start-all-services.sh
```

This will:
- Start 4 PostgreSQL databases
- Start 4 Redis instances
- Launch 4 microservices (Identity, Content, Communication, Workflow)
- Configure Kong API Gateway
- Set up health monitoring

**Expected output:**
```
🚀 ReactDjango Hub - Services Coordinator
========================================

[INFO] Starting ReactDjango Hub Microservices...
[SUCCESS] All services started successfully!
```

### Step 2: Verify Services Are Running

```bash
# Check health of all services
./health-check-all.sh
```

**Expected output:**
```
🏥 ReactDjango Hub - Health Check
=================================

[✅ HEALTHY] Identity Service is healthy (HTTP 200)
[✅ HEALTHY] Content Service is healthy (HTTP 200)
[✅ HEALTHY] Communication Service is healthy (HTTP 200)
[✅ HEALTHY] Workflow Service is healthy (HTTP 200)
[✅ HEALTHY] Kong Proxy is healthy (HTTP 200)
🎉 All services are healthy!
```

### Step 3: Start Frontend (Optional)

```bash
# In a new terminal, navigate to frontend
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:5173

## 📍 Service Endpoints

### API Gateway (Kong)
- **Main Gateway**: http://localhost:8000
- **Admin API**: http://localhost:8445
- **Health Check**: http://localhost:8000/health

### Microservices API Documentation
- **Identity Service**: http://localhost:8001/docs
- **Content Service**: http://localhost:8002/docs
- **Communication Service**: http://localhost:8003/docs
- **Workflow Service**: http://localhost:8004/docs

### Frontend Routes (Through Kong)
```javascript
const API_BASE = 'http://localhost:8000/api/v1';

// Authentication
POST ${API_BASE}/auth/register
POST ${API_BASE}/auth/login
POST ${API_BASE}/auth/refresh
POST ${API_BASE}/auth/logout

// Users
GET  ${API_BASE}/users
GET  ${API_BASE}/users/{id}
PUT  ${API_BASE}/users/{id}

// Documents
GET  ${API_BASE}/documents
POST ${API_BASE}/documents
GET  ${API_BASE}/documents/{id}

// Notifications
GET  ${API_BASE}/notifications
POST ${API_BASE}/notifications/send

// Workflows
GET  ${API_BASE}/workflows
POST ${API_BASE}/workflows/execute
```

## 🔧 Common Operations

### View Service Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f identity-service
docker-compose logs -f kong
docker-compose logs -f identity-db
```

### Restart a Service

```bash
# Restart specific service
docker-compose restart identity-service

# Restart all services
docker-compose restart
```

### Stop All Services

```bash
# Graceful shutdown
./stop-all-services.sh

# Or manually
docker-compose down
```

### Reset Everything

```bash
# Stop and remove all containers, volumes, and networks
docker-compose down -v

# Then start fresh
./start-all-services.sh
```

## 🧪 Testing the Setup

### Test Authentication Flow

```bash
# 1. Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Response will include JWT token
# {
#   "access_token": "eyJ...",
#   "refresh_token": "eyJ...",
#   "token_type": "bearer"
# }

# 3. Use token for authenticated requests
TOKEN="your-jwt-token-here"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/users/profile
```

### Test Service Communication

```bash
# Test Kong routing to each service
curl http://localhost:8000/api/v1/auth/health        # → Identity Service
curl http://localhost:8000/api/v1/documents/health   # → Content Service
curl http://localhost:8000/api/v1/notifications/health # → Communication Service
curl http://localhost:8000/api/v1/workflows/health   # → Workflow Service
```

## 🐛 Troubleshooting

### Services Won't Start

**Problem**: Docker is not running
```bash
# Check Docker status
docker info

# Solution: Start Docker Desktop
```

**Problem**: Port already in use
```bash
# Check what's using the port (example for port 8000)
lsof -i :8000

# Solution: Stop the conflicting service or change ports in docker-compose.yml
```

### Service Unhealthy

**Problem**: Service fails health check
```bash
# Check service logs
docker-compose logs identity-service

# Common issues:
# - Database not ready: Wait 30 seconds and retry
# - Configuration error: Check .env files
# - Migration failed: Check database logs
```

### Can't Connect from Frontend

**Problem**: CORS errors
```bash
# Verify Kong CORS configuration
curl -i http://localhost:8000/api/v1/auth/health

# Should include CORS headers:
# Access-Control-Allow-Origin: http://localhost:3000
```

**Problem**: 401 Unauthorized
```bash
# Token might be expired or invalid
# Get a new token by logging in again
```

### Database Connection Issues

```bash
# Check database is running
docker-compose ps identity-db

# Test database connection
docker-compose exec identity-db psql -U identity_user -d identity_service -c "SELECT 1"

# If connection fails, restart database
docker-compose restart identity-db
```

## 📊 Resource Usage

Typical resource consumption in development:

| Component | CPU | Memory |
|-----------|-----|--------|
| All Services | ~10% | ~1.2GB |
| Databases | ~4% | ~320MB |
| Redis | ~2% | ~80MB |
| Microservices | ~4% | ~480MB |
| Kong Gateway | ~2% | ~150MB |

## 🔑 Default Credentials

### Databases
- **Identity DB**: identity_user / identity_pass
- **Content DB**: content_user / content_pass
- **Communication DB**: communication_user / communication_pass
- **Workflow DB**: workflow_user / workflow_pass

### Test User (After Registration)
- **Email**: test@example.com
- **Password**: SecurePass123!

## 📝 Environment Configuration

### Frontend Environment Variables

Create `frontend/.env.development`:
```env
VITE_KONG_URL=http://localhost:8000
VITE_KONG_ADMIN_URL=http://localhost:8445
VITE_API_VERSION=v1
```

### Service Environment Variables

Shared configuration in `services/.env.shared`:
```env
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
```

## 🎯 Next Steps

1. **Explore API Documentation**
   - Visit http://localhost:8001/docs for Identity Service API
   - Try out the interactive API documentation

2. **Implement Frontend Features**
   - Set up authentication flow
   - Create user dashboard
   - Implement document management

3. **Configure Production Settings**
   - Set up SSL/TLS
   - Configure production databases
   - Set up monitoring and logging

## 🆘 Getting Help

1. **Check Logs**: `docker-compose logs -f <service-name>`
2. **View Documentation**: See `/docs/architecture/` for detailed docs
3. **Health Check**: Run `./health-check-all.sh` to diagnose issues
4. **Reset Environment**: `docker-compose down -v` and start fresh

## 📚 Additional Resources

- [Service Discovery Documentation](./architecture/service-discovery.md)
- [Frontend-Backend Integration Guide](./architecture/frontend-backend-integration.md)
- [Integration Status Report](./architecture/integration-status.md)
- [Kong API Gateway Documentation](https://docs.konghq.com/)

---

**Remember**: Services take 10-30 seconds to fully initialize. If something doesn't work immediately, wait a moment and try again!