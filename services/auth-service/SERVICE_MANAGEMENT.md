# Auth Service - Configuration & Management Guide

## 🚀 **Service Management Overview**

This guide covers how to configure, run, monitor, and manage your auth service in different environments.

---

## ⚙️ **Configuration Management**

### **Environment Files**

The service uses environment-based configuration:

```bash
# Current files available:
.env.local          # Local development (PostgreSQL + Redis)
.env.test           # Testing (in-memory, no dependencies)  
config.py           # Configuration class with defaults
```

### **Create Production Configuration**

```bash
# Create .env.production
cp .env.local .env.production

# Edit for production
vim .env.production
```

**Production .env.production example:**
```bash
# Database (use your production database)
DATABASE_URL=postgresql+asyncpg://prod_user:secure_password@prod-db:5432/auth_service_prod

# Redis (use your production Redis)
REDIS_URL=redis://prod-redis:6379/0

# Security (CRITICAL - change these!)
JWT_SECRET_KEY=your-super-secure-256-bit-secret-key-here
DEBUG=false
LOG_LEVEL=INFO

# Email (use real SMTP provider)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Your App Name

# URLs (update to your domains)
BASE_URL=https://api.yourdomain.com
FRONTEND_URL=https://app.yourdomain.com

# Security settings
LOGIN_RATE_LIMIT=5
LOGIN_RATE_WINDOW=900
API_RATE_LIMIT=1000
EMAIL_VERIFICATION_EXPIRE_HOURS=24
PASSWORD_RESET_EXPIRE_HOURS=1
```

---

## 🏃 **Running the Service**

### **1. Local Development**
```bash
# Start dependencies
brew services start postgresql@17
brew services start redis

# Start service
python main.py
# OR
uvicorn main:app --reload --port 8001

# Service available at:
# - API: http://localhost:8001
# - Docs: http://localhost:8001/docs
```

### **2. Production Deployment**

**Option A: Direct Python**
```bash
# Set environment
export ENV_FILE=.env.production

# Start with Gunicorn (recommended for production)
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001

# OR start with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4
```

**Option B: Docker (Recommended)**
```bash
# Build image
docker build -t auth-service:latest .

# Run container
docker run -d \
  --name auth-service \
  -p 8001:8001 \
  --env-file .env.production \
  auth-service:latest
```

**Option C: Docker Compose**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  auth-service:
    build: .
    ports:
      - "8001:8001"
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: auth_service_prod
      POSTGRES_USER: prod_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

```bash
# Start production stack
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🗄️ **Database Management**

### **Migrations**
```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback to previous version
alembic downgrade -1

# Check current version
alembic current

# Show migration history
alembic history
```

### **Database Operations**
```bash
# Initialize fresh database
python -c "
import asyncio
from database import init_db
asyncio.run(init_db())
"

# Reset database (DESTRUCTIVE!)
python -c "
import asyncio  
from database import reset_db
asyncio.run(reset_db())
"

# Backup database
pg_dump auth_service > backup_$(date +%Y%m%d).sql

# Restore database
psql auth_service < backup_20250909.sql
```

---

## 📊 **Monitoring & Health Checks**

### **Health Endpoints**
```bash
# Basic health check
curl http://localhost:8001/health

# Detailed service info
curl http://localhost:8001/test-info

# Root endpoint (API overview)
curl http://localhost:8001/
```

### **Monitoring Script**
```bash
#!/bin/bash
# monitor_auth_service.sh

SERVICE_URL="http://localhost:8001"

echo "🔍 Auth Service Monitoring Report"
echo "=================================="

# Health check
HEALTH=$(curl -s $SERVICE_URL/health)
STATUS=$(echo $HEALTH | jq -r '.status // "unknown"')
echo "📊 Health Status: $STATUS"

# Service info
INFO=$(curl -s $SERVICE_URL/test-info)
USERS=$(echo $INFO | jq -r '.statistics.total_users // "N/A"')
VERIFIED=$(echo $INFO | jq -r '.statistics.verified_users // "N/A"')
echo "👥 Total Users: $USERS"
echo "✅ Verified Users: $VERIFIED"

# Database connection
if [[ "$STATUS" == "healthy" ]]; then
    echo "🗄️  Database: Connected"
else
    echo "❌ Database: Issues detected"
fi

echo "🕒 Report generated: $(date)"
```

### **Log Management**
```bash
# View service logs (if running with systemd)
journalctl -u auth-service -f

# View Docker logs
docker logs auth-service -f

# View uvicorn logs (if running directly)
tail -f auth-service.log
```

---

## 🔒 **Security Management**

### **JWT Secret Rotation**
```bash
# Generate new secret
python -c "
import secrets
import base64
secret = secrets.token_bytes(32)
print(base64.b64encode(secret).decode())
"

# Update .env file with new JWT_SECRET_KEY
# Restart service for changes to take effect
```

### **User Management**
```bash
# Create admin user (via API)
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourdomain.com",
    "password": "SecureAdminPassword123!",
    "first_name": "System",
    "last_name": "Administrator"
  }'

# List all users
curl http://localhost:8001/users

# Delete user
curl -X DELETE http://localhost:8001/users/USER_ID_HERE
```

### **Security Auditing**
```bash
# Check failed login attempts
psql auth_service -c "
SELECT email, failed_login_attempts, locked_until 
FROM users_simple 
WHERE failed_login_attempts > 0;
"

# View recent user activity
psql auth_service -c "
SELECT u.email, ua.activity_type, ua.description, ua.created_at
FROM user_activities_simple ua
JOIN users_simple u ON ua.user_id = u.id
ORDER BY ua.created_at DESC
LIMIT 20;
"
```

---

## 🚀 **Deployment Strategies**

### **1. Single Server Deployment**
```bash
# systemd service file: /etc/systemd/system/auth-service.service
[Unit]
Description=Auth Service
After=network.target

[Service]
Type=exec
User=appuser
WorkingDirectory=/opt/auth-service
Environment=PATH=/opt/auth-service/venv/bin
EnvironmentFile=/opt/auth-service/.env.production
ExecStart=/opt/auth-service/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable auth-service
sudo systemctl start auth-service
sudo systemctl status auth-service
```

### **2. Load Balanced Deployment**
```bash
# Behind nginx/Apache reverse proxy
# nginx config example:
upstream auth_service {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://auth_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **3. Container Orchestration**
```yaml
# kubernetes/auth-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: auth-service
        image: auth-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: auth-secrets
              key: database-url
---
apiVersion: v1
kind: Service
metadata:
  name: auth-service
spec:
  selector:
    app: auth-service
  ports:
  - port: 80
    targetPort: 8001
```

---

## 🛠️ **Troubleshooting**

### **Common Issues**

**1. Database Connection Issues**
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT version();"

# Check if database exists
psql -l | grep auth_service
```

**2. Email Not Sending**
```bash
# Test SMTP connection
python -c "
import aiosmtplib
import asyncio
async def test():
    smtp = aiosmtplib.SMTP('$SMTP_HOST', $SMTP_PORT)
    await smtp.connect()
    print('SMTP connection successful')
    await smtp.quit()
asyncio.run(test())
"
```

**3. JWT Token Issues**
```bash
# Decode JWT token for debugging
python -c "
import jwt
token = 'YOUR_JWT_TOKEN_HERE'
decoded = jwt.decode(token, options={'verify_signature': False})
print(decoded)
"
```

### **Performance Tuning**

**Database Optimization**
```sql
-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email_status ON users_simple(email, status);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions_simple(is_active, expires_at);
CREATE INDEX IF NOT EXISTS idx_activities_user_time ON user_activities_simple(user_id, created_at);
```

**Redis Optimization**
```bash
# Configure Redis for auth service
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET timeout 300
```

---

## 📋 **Maintenance Tasks**

### **Daily Tasks**
- Monitor service health (`/health` endpoint)
- Check error logs
- Verify database connections

### **Weekly Tasks**
- Review user activity logs
- Check failed login patterns
- Update security patches

### **Monthly Tasks**
- Rotate JWT secrets
- Clean up expired sessions
- Database maintenance and backups
- Performance analysis

---

## 🔧 **Development Workflow**

### **Local Development Setup**
```bash
# 1. Clone and setup
git clone <repository>
cd services/auth-service

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements-latest.txt

# 4. Setup local services
brew services start postgresql@17
brew services start redis

# 5. Initialize database
alembic upgrade head

# 6. Start development server
python main.py
```

### **Testing Workflow**
```bash
# Run basic tests
python test_full_service.py

# Run with pytest (when available)
pytest tests/ -v

# Load testing
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","first_name":"Test","last_name":"User"}'
```

---

**This service is now fully manageable across all environments!** 🎉

Choose the deployment method that fits your infrastructure and scale requirements.