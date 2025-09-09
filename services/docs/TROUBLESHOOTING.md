# Microservices Troubleshooting Guide

**Managed by**: Services Coordinator Agent

## 🚨 **Common Issues & Solutions**

### **Service Won't Start**

#### **Symptom**: Service exits immediately or won't respond
```bash
# Check service logs
docker-compose logs service-name

# Check if port is available
lsof -i :8001  # Replace with service port
```

**Common Causes**:
- Port already in use
- Database connection failed
- Missing environment variables
- Redis connection failed

**Solutions**:
```bash
# Kill process on port
kill -9 $(lsof -ti:8001)

# Check environment variables
docker-compose config

# Restart dependencies
docker-compose restart identity-db identity-redis
```

### **Database Connection Issues**

#### **Symptom**: `sqlalchemy.exc.OperationalError` or `asyncpg.exceptions.CannotConnectNowError`

**Check Database Status**:
```bash
# Check if database is running
docker-compose ps | grep db

# Connect to database directly
docker-compose exec identity-db psql -U identity_user -d identity_service
```

**Solutions**:
```bash
# Restart database
docker-compose restart identity-db

# Check database logs
docker-compose logs identity-db

# Reset database (⚠️ DESTRUCTIVE)
docker-compose down
docker volume rm services_identity_db_data
docker-compose up -d identity-db
```

### **Redis Connection Issues**

#### **Symptom**: `redis.exceptions.ConnectionError` or Celery workers not responding

**Check Redis Status**:
```bash
# Check Redis connectivity
docker-compose exec identity-redis redis-cli ping

# Monitor Redis
docker-compose exec identity-redis redis-cli monitor
```

**Solutions**:
```bash
# Restart Redis
docker-compose restart identity-redis

# Clear Redis cache
docker-compose exec identity-redis redis-cli FLUSHALL
```

### **Authentication Issues**

#### **Symptom**: 401 Unauthorized across multiple services

**Debug Authentication**:
```bash
# Test identity service directly
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# Validate token
curl -X POST http://localhost:8001/auth/validate \
  -H "Content-Type: application/json" \
  -d '{"token":"your-jwt-token"}'
```

**Common Issues**:
- JWT secret mismatch between services
- Token expired
- Identity service down
- Wrong token format

**Solutions**:
```bash
# Check JWT configuration consistency
grep -r "JWT_SECRET_KEY" */
grep -r "JWT_ALGORITHM" */

# Restart identity service
docker-compose restart identity-service
```

### **Service Communication Issues**

#### **Symptom**: Services can't communicate with each other

**Test Service Communication**:
```bash
# From inside a container
docker-compose exec content-service curl http://identity-service:8001/health

# Check network connectivity
docker network ls
docker network inspect services_default
```

**Solutions**:
```bash
# Recreate network
docker-compose down
docker-compose up -d

# Check service discovery
docker-compose ps
```

## 🔍 **Debugging Commands**

### **Service Health Check**
```bash
# Check all services
./scripts/health-check-all.sh

# Individual service health
curl http://localhost:8001/health  # Identity
curl http://localhost:8002/health  # Content  
curl http://localhost:8003/health  # Communication
curl http://localhost:8004/health  # Workflow
```

### **Container Inspection**
```bash
# View all containers
docker-compose ps

# Container logs
docker-compose logs -f service-name

# Execute commands in container
docker-compose exec service-name bash

# Check container resource usage
docker stats
```

### **Database Debugging**
```bash
# Connect to each database
docker-compose exec identity-db psql -U identity_user -d identity_service
docker-compose exec content-db psql -U content_user -d content_service
docker-compose exec communication-db psql -U communication_user -d communication_service
docker-compose exec workflow-db psql -U workflow_user -d workflow_intelligence_service

# Check database size
\l+  # List databases with size
\dt+  # List tables with size
```

### **Redis Debugging**
```bash
# Connect to each Redis instance
docker-compose exec identity-redis redis-cli
docker-compose exec content-redis redis-cli  
docker-compose exec communication-redis redis-cli
docker-compose exec workflow-redis redis-cli

# Redis commands
INFO  # Redis info
KEYS *  # List all keys
MONITOR  # Monitor commands
```

## 🚀 **Performance Issues**

### **Slow API Responses**

**Diagnosis**:
```bash
# Check response times
curl -w "Time: %{time_total}s\n" http://localhost:8001/health

# Monitor database queries (if enabled)
docker-compose logs identity-service | grep "Query"
```

**Solutions**:
- Add database indexes
- Implement Redis caching
- Optimize query patterns
- Scale service replicas

### **High Memory Usage**

**Check Memory Usage**:
```bash
# Container memory usage
docker stats --no-stream

# System memory
free -h
```

**Solutions**:
- Adjust database connection pools
- Implement memory limits in Docker
- Optimize data structures
- Add garbage collection tuning

### **Database Connection Pool Exhaustion**

**Symptoms**: `QueuePool limit exceeded` or connection timeouts

**Solutions**:
```bash
# Increase pool size in environment
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Monitor active connections
# In PostgreSQL:
SELECT count(*) FROM pg_stat_activity;
```

## 🔄 **Recovery Procedures**

### **Complete System Reset**
```bash
# ⚠️ DESTRUCTIVE - Will lose all data
docker-compose down
docker system prune -a --volumes
docker-compose up -d
```

### **Individual Service Reset**
```bash
# Reset specific service
docker-compose stop service-name
docker-compose rm -f service-name
docker-compose up -d service-name
```

### **Database Reset**
```bash
# Reset specific database (⚠️ DESTRUCTIVE)
docker-compose stop service-name
docker volume rm services_service-name_db_data
docker-compose up -d service-name-db
# Run migrations
```

## 📊 **Monitoring & Alerting**

### **Service Monitoring**
```bash
# Continuous health monitoring
watch -n 30 './scripts/health-check-all.sh'

# Log monitoring
docker-compose logs -f --tail=100
```

### **Resource Monitoring**
```bash
# System resources
htop
df -h  # Disk space
netstat -tulpn  # Network connections
```

### **Application Metrics**
- Monitor response times
- Track error rates
- Watch database performance
- Monitor queue lengths (Celery)

## 📋 **Emergency Contacts & Escalation**

### **Service Ownership**
- **Identity Service**: Identity service specialist
- **Content Service**: Content service specialist
- **Communication Service**: Communication service specialist
- **Workflow Service**: Workflow service specialist
- **Cross-Service Issues**: Services coordinator

### **Escalation Path**
1. Check troubleshooting guide (this document)
2. Review service-specific documentation
3. Check service logs and metrics
4. Contact service owner
5. Escalate to architecture team

---

**🆘 This guide is maintained by the Services Coordinator Agent. Report new issues or solutions to keep this guide current.**