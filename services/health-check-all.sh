#!/bin/bash

# ReactDjango Hub - Services Health Check Script
# Comprehensive health monitoring for all microservices

set -e

echo "🏥 ReactDjango Hub - Health Check"
echo "================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✅ HEALTHY]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠️  WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[❌ ERROR]${NC} $1"
}

check_service_health() {
    local service_name="$1"
    local service_url="$2"
    local expected_status="${3:-200}"
    
    echo -n "Checking $service_name... "
    
    # Check if service is responding
    if response=$(curl -s -w "%{http_code}" -o /dev/null --connect-timeout 5 "$service_url" 2>/dev/null); then
        if [[ "$response" == "$expected_status" ]]; then
            print_success "$service_name is healthy (HTTP $response)"
            return 0
        else
            print_warning "$service_name returned HTTP $response (expected $expected_status)"
            return 1
        fi
    else
        print_error "$service_name is not responding or unreachable"
        return 1
    fi
}

check_database_connection() {
    local db_name="$1"
    local port="$2"
    local user="$3"
    
    echo -n "Checking $db_name database... "
    
    # Use docker-compose to check database connectivity
    if docker-compose exec -T "${db_name}" pg_isready -U "$user" >/dev/null 2>&1; then
        print_success "$db_name database is healthy"
        return 0
    else
        print_error "$db_name database is not responding"
        return 1
    fi
}

check_redis_connection() {
    local redis_name="$1"
    
    echo -n "Checking $redis_name... "
    
    # Use docker-compose to check Redis connectivity
    if docker-compose exec -T "${redis_name}" redis-cli ping | grep -q "PONG" >/dev/null 2>&1; then
        print_success "$redis_name is healthy"
        return 0
    else
        print_error "$redis_name is not responding"
        return 1
    fi
}

# Navigate to services directory
cd "$(dirname "$0")"

if [[ ! -f "docker-compose.yml" ]]; then
    print_error "docker-compose.yml not found. Please run from services/ directory."
    exit 1
fi

print_status "Checking all ReactDjango Hub services..."
echo ""

# Check Docker Compose services status
print_status "Docker Compose Service Status:"
docker-compose ps
echo ""

# Initialize counters
healthy_services=0
total_services=0

# Check databases
print_status "=== DATABASE HEALTH CHECKS ==="
((total_services+=4))

if check_database_connection "identity-db" "5433" "identity_user"; then
    ((healthy_services++))
fi

if check_database_connection "content-db" "5434" "content_user"; then
    ((healthy_services++))
fi

if check_database_connection "communication-db" "5435" "communication_user"; then
    ((healthy_services++))
fi

if check_database_connection "workflow-db" "5436" "workflow_user"; then
    ((healthy_services++))
fi

echo ""

# Check Redis instances
print_status "=== REDIS HEALTH CHECKS ==="
((total_services+=4))

if check_redis_connection "identity-redis"; then
    ((healthy_services++))
fi

if check_redis_connection "content-redis"; then
    ((healthy_services++))
fi

if check_redis_connection "communication-redis"; then
    ((healthy_services++))
fi

if check_redis_connection "workflow-redis"; then
    ((healthy_services++))
fi

echo ""

# Check microservices
print_status "=== MICROSERVICE HEALTH CHECKS ==="
((total_services+=4))

if check_service_health "Identity Service" "http://localhost:8001/health"; then
    ((healthy_services++))
fi

if check_service_health "Content Service" "http://localhost:8002/health"; then
    ((healthy_services++))
fi

if check_service_health "Communication Service" "http://localhost:8003/health"; then
    ((healthy_services++))
fi

if check_service_health "Workflow Intelligence Service" "http://localhost:8004/health"; then
    ((healthy_services++))
fi

echo ""

# Check API Gateway
print_status "=== API GATEWAY HEALTH CHECKS ==="
((total_services+=2))

if check_service_health "Kong Proxy" "http://localhost:8000/health"; then
    ((healthy_services++))
fi

if check_service_health "Kong Admin API" "http://localhost:8445/status"; then
    ((healthy_services++))
fi

echo ""

# Summary
print_status "=== HEALTH CHECK SUMMARY ==="
echo "Healthy Services: $healthy_services / $total_services"

if [[ $healthy_services -eq $total_services ]]; then
    print_success "🎉 All services are healthy!"
    exit 0
elif [[ $healthy_services -gt $((total_services / 2)) ]]; then
    print_warning "⚠️  Some services have issues but system is partially functional"
    exit 1
else
    print_error "❌ Multiple services are down - system may be non-functional"
    exit 2
fi