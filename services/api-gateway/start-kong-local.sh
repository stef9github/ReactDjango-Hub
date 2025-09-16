#!/bin/bash

# =============================================================================
# Kong API Gateway - Local Development Startup Script
# =============================================================================

set -e

echo "🚀 Starting Kong API Gateway (Local Development Mode)"
echo "====================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if Kong is installed
if ! command -v kong >/dev/null 2>&1; then
    echo -e "${RED}❌ Kong is not installed.${NC}"
    echo -e "${YELLOW}Please install Kong:${NC}"
    echo -e "${YELLOW}  macOS: brew install kong${NC}"
    echo -e "${YELLOW}  Linux: https://docs.konghq.com/gateway/latest/install/linux/#{NC}"
    echo -e "${YELLOW}  Docker: docker run --rm kong:3.4 kong version${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Kong found: $(kong version --vv | head -1)${NC}"

# Check if port 8080 is already in use (Kong proxy port)
if lsof -i :8080 >/dev/null 2>&1; then
    echo -e "${RED}❌ Port 8080 is already in use.${NC}"
    echo -e "${YELLOW}Kong may already be running or another service is using this port.${NC}"
    echo -e "${YELLOW}To stop Kong: kong stop${NC}"
    echo -e "${YELLOW}To check running processes: lsof -i :8080${NC}"
    exit 1
fi

# Check if the local configuration file exists
if [ ! -f "kong-local.yml" ]; then
    echo -e "${RED}❌ kong-local.yml configuration file not found.${NC}"
    exit 1
fi

echo -e "${BLUE}Using configuration: kong-local.yml${NC}"

# Set Kong environment variables for local development
export KONG_DATABASE=off
export KONG_DECLARATIVE_CONFIG=kong-local.yml
export KONG_PROXY_ACCESS_LOG=/dev/stdout
export KONG_ADMIN_ACCESS_LOG=/dev/stdout  
export KONG_PROXY_ERROR_LOG=/dev/stderr
export KONG_ADMIN_ERROR_LOG=/dev/stderr
export KONG_ADMIN_LISTEN="127.0.0.1:8001"
export KONG_PROXY_LISTEN="0.0.0.0:8080"
export KONG_LOG_LEVEL=info

# Validate the configuration
echo -e "${BLUE}Validating Kong configuration...${NC}"
if ! kong config -c kong-local.yml parse; then
    echo -e "${RED}❌ Kong configuration validation failed.${NC}"
    echo -e "${YELLOW}Please check kong-local.yml for syntax errors.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Kong configuration is valid${NC}"

# Start Kong
echo -e "${BLUE}Starting Kong API Gateway...${NC}"

# Create a temporary Kong configuration file for local development
cat > kong.conf << EOF
# Kong configuration for local development
database = off
declarative_config = kong-local.yml

# Proxy configuration  
proxy_listen = 0.0.0.0:8080
admin_listen = 127.0.0.1:8444

# Logging
proxy_access_log = /dev/stdout
admin_access_log = /dev/stdout
proxy_error_log = /dev/stderr  
admin_error_log = /dev/stderr
log_level = info

# Performance
nginx_worker_processes = auto
EOF

# Start Kong with the configuration
kong start -c kong.conf

# Wait for Kong to be ready
echo -e "${BLUE}Waiting for Kong to start...${NC}"
sleep 3

# Check if Kong is running
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -s -f http://localhost:8444/status >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Kong is running and healthy${NC}"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}❌ Kong failed to start after ${max_attempts} attempts${NC}"
        echo -e "${YELLOW}Check Kong logs for details${NC}"
        exit 1
    fi
    
    sleep 2
    ((attempt++))
done

# Display service information
echo
echo "=============================================================="
echo -e "${GREEN}🎉 Kong API Gateway started successfully!${NC}"
echo
echo -e "${BLUE}Kong Gateway URLs:${NC}"
echo -e "${GREEN}  • Proxy (API Gateway):    http://localhost:8080${NC}"
echo -e "${GREEN}  • Admin API:              http://localhost:8444${NC}"
echo -e "${GREEN}  • Gateway Health Check:   http://localhost:8080/health${NC}"
echo
echo -e "${BLUE}Proxied Service Routes:${NC}"
echo -e "${GREEN}  • Identity Service:       http://localhost:8080/api/v1/auth${NC}"
echo -e "${GREEN}  • Content Service:        http://localhost:8080/api/v1/documents${NC}"
echo -e "${GREEN}  • Communication Service:  http://localhost:8080/api/v1/notifications${NC}"
echo -e "${GREEN}  • Workflow Service:       http://localhost:8080/api/v1/workflows${NC}"
echo
echo -e "${YELLOW}Prerequisites:${NC}"
echo -e "${YELLOW}  • Make sure all microservices are running on their expected ports${NC}"
echo -e "${YELLOW}  • Identity Service: http://localhost:8001${NC}"
echo -e "${YELLOW}  • Content Service: http://localhost:8002${NC}"
echo -e "${YELLOW}  • Communication Service: http://localhost:8003${NC}"
echo -e "${YELLOW}  • Workflow Service: http://localhost:8004${NC}"
echo
echo -e "${YELLOW}To stop Kong: kong stop${NC}"
echo -e "${YELLOW}To reload config: kong reload${NC}"
echo -e "${YELLOW}To check status: curl http://localhost:8444/status${NC}"