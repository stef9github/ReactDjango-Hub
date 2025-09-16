#!/bin/bash

# =============================================================================
# Local Development Startup Script (No Docker Required)
# =============================================================================
# This script starts all microservices locally without Docker dependencies.
# Prerequisites:
#   - Local PostgreSQL server running on port 5432
#   - Local Redis server running on port 6379
#   - Python 3.13+ installed
#   - All service dependencies installed (requirements.txt)

set -e  # Exit on any error

echo "🚀 Starting ReactDjango Hub Services (Local Development Mode)"
echo "=============================================================="

# Set environment variables for local development
export USE_DOCKER=false
export DEBUG=true
export LOG_LEVEL=INFO

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to start a service in the background
start_service() {
    local service_name=$1
    local service_dir=$2
    local service_port=$3
    local main_file=${4:-main.py}
    
    echo -e "${BLUE}Starting ${service_name}...${NC}"
    
    cd "$service_dir"
    
    # Check if virtual environment exists, if not create it
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment for ${service_name}...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies if requirements.txt exists and is newer than last install
    if [ -f "requirements.txt" ]; then
        if [ ! -f ".requirements_installed" ] || [ "requirements.txt" -nt ".requirements_installed" ]; then
            echo -e "${YELLOW}Installing dependencies for ${service_name}...${NC}"
            pip install -r requirements.txt
            touch .requirements_installed
        fi
    fi
    
    # Check if port is already in use
    if port_in_use $service_port; then
        echo -e "${RED}Port $service_port is already in use. ${service_name} may already be running.${NC}"
        echo -e "${YELLOW}Skipping ${service_name} startup.${NC}"
        cd ..
        return
    fi
    
    # Start the service
    echo -e "${GREEN}${service_name} starting on port ${service_port}${NC}"
    nohup python $main_file > ${service_name}.log 2>&1 &
    echo $! > ${service_name}.pid
    
    # Wait a moment and check if the service started successfully
    sleep 2
    if kill -0 $! 2>/dev/null; then
        echo -e "${GREEN}✅ ${service_name} started successfully (PID: $!)${NC}"
    else
        echo -e "${RED}❌ ${service_name} failed to start. Check ${service_name}.log for details.${NC}"
    fi
    
    cd ..
}

# Function to check service health
check_service_health() {
    local service_name=$1
    local service_url=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${BLUE}Waiting for ${service_name} to be healthy...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$service_url/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ ${service_name} is healthy${NC}"
            return 0
        fi
        
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}❌ ${service_name} failed to become healthy after ${max_attempts} attempts${NC}"
    return 1
}

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check Python
if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed. Please install Python 3.13+${NC}"
    exit 1
fi

# Check PostgreSQL
if ! command_exists psql; then
    echo -e "${YELLOW}⚠️  PostgreSQL client (psql) not found. Please ensure PostgreSQL is installed.${NC}"
fi

# Check if PostgreSQL is running
if ! nc -z localhost 5432 2>/dev/null; then
    echo -e "${RED}❌ PostgreSQL is not running on localhost:5432${NC}"
    echo -e "${YELLOW}Please start PostgreSQL server first:${NC}"
    echo -e "${YELLOW}  macOS: brew services start postgresql${NC}"
    echo -e "${YELLOW}  Linux: sudo systemctl start postgresql${NC}"
    exit 1
fi

# Check if Redis is running
if ! nc -z localhost 6379 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Redis is not running on localhost:6379${NC}"
    echo -e "${YELLOW}Starting Redis may be optional, but recommended for full functionality.${NC}"
    echo -e "${YELLOW}To start Redis:${NC}"
    echo -e "${YELLOW}  macOS: brew services start redis${NC}"
    echo -e "${YELLOW}  Linux: sudo systemctl start redis${NC}"
fi

echo -e "${GREEN}✅ Prerequisites check completed${NC}"
echo

# Create databases if they don't exist
echo -e "${BLUE}Creating databases if they don't exist...${NC}"

databases=("auth_service" "communication_service" "content_service" "workflow_intelligence_service")

for db in "${databases[@]}"; do
    if ! psql -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$db'" | grep -q 1; then
        echo -e "${YELLOW}Creating database: $db${NC}"
        createdb "$db" 2>/dev/null || echo -e "${YELLOW}Database $db may already exist or could not be created${NC}"
    else
        echo -e "${GREEN}Database $db already exists${NC}"
    fi
done

echo

# Start services in dependency order
echo -e "${BLUE}Starting services...${NC}"

# 1. Identity Service (no dependencies)
start_service "identity-service" "identity-service" 8001

# 2. Content Service (depends on identity)
start_service "content-service" "content-service" 8002

# 3. Communication Service (depends on identity)
start_service "communication-service" "communication-service" 8003

# 4. Workflow Intelligence Service (depends on identity, content, communication)
start_service "workflow-intelligence-service" "workflow-intelligence-service" 8004

echo
echo -e "${BLUE}Waiting for services to start up...${NC}"
sleep 5

# Check service health
echo
echo -e "${BLUE}Checking service health...${NC}"

services=(
    "Identity Service:http://localhost:8001"
    "Content Service:http://localhost:8002"  
    "Communication Service:http://localhost:8003"
    "Workflow Intelligence Service:http://localhost:8004"
)

all_healthy=true

for service in "${services[@]}"; do
    service_name="${service%%:*}"
    service_url="${service##*:}"
    
    if ! check_service_health "$service_name" "$service_url"; then
        all_healthy=false
    fi
done

echo
echo "=============================================================="

if $all_healthy; then
    echo -e "${GREEN}🎉 All services started successfully!${NC}"
    echo
    echo -e "${BLUE}Service URLs:${NC}"
    echo -e "${GREEN}  • Identity Service:       http://localhost:8001${NC}"
    echo -e "${GREEN}  • Content Service:        http://localhost:8002${NC}"
    echo -e "${GREEN}  • Communication Service:  http://localhost:8003${NC}"
    echo -e "${GREEN}  • Workflow Intelligence:  http://localhost:8004${NC}"
    echo
    echo -e "${BLUE}API Documentation:${NC}"
    echo -e "${GREEN}  • Identity Service:       http://localhost:8001/docs${NC}"
    echo -e "${GREEN}  • Content Service:        http://localhost:8002/docs${NC}"
    echo -e "${GREEN}  • Communication Service:  http://localhost:8003/docs${NC}"
    echo -e "${GREEN}  • Workflow Intelligence:  http://localhost:8004/docs${NC}"
    echo
    echo -e "${YELLOW}To stop all services, run: ./dev-stop-local.sh${NC}"
    echo -e "${YELLOW}To view logs: tail -f */service-name.log${NC}"
else
    echo -e "${RED}❌ Some services failed to start properly.${NC}"
    echo -e "${YELLOW}Check the individual service log files for details.${NC}"
    exit 1
fi