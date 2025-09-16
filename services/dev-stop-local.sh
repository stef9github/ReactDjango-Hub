#!/bin/bash

# =============================================================================
# Local Development Stop Script
# =============================================================================
# This script stops all locally running microservices.

set -e  # Exit on any error

echo "🛑 Stopping ReactDjango Hub Services (Local Development Mode)"
echo "=============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to stop a service
stop_service() {
    local service_name=$1
    local service_dir=$2
    
    echo -e "${BLUE}Stopping ${service_name}...${NC}"
    
    cd "$service_dir"
    
    if [ -f "${service_name}.pid" ]; then
        local pid=$(cat "${service_name}.pid")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            echo -e "${GREEN}✅ ${service_name} stopped (PID: $pid)${NC}"
            
            # Wait for graceful shutdown
            local attempts=0
            while kill -0 "$pid" 2>/dev/null && [ $attempts -lt 10 ]; do
                sleep 1
                ((attempts++))
            done
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${YELLOW}Force killing ${service_name}...${NC}"
                kill -9 "$pid" 2>/dev/null || true
            fi
        else
            echo -e "${YELLOW}${service_name} was not running (stale PID file)${NC}"
        fi
        rm -f "${service_name}.pid"
    else
        echo -e "${YELLOW}No PID file found for ${service_name}${NC}"
    fi
    
    cd ..
}

# Function to kill processes on specific ports (fallback)
kill_port() {
    local port=$1
    local service_name=$2
    
    local pid=$(lsof -t -i:$port 2>/dev/null || true)
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}Found process on port $port (PID: $pid) - killing...${NC}"
        kill "$pid" 2>/dev/null || true
        sleep 2
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
        echo -e "${GREEN}✅ Process on port $port killed${NC}"
    fi
}

# Stop services in reverse dependency order
echo -e "${BLUE}Stopping services...${NC}"

# 4. Workflow Intelligence Service
stop_service "workflow-intelligence-service" "workflow-intelligence-service"

# 3. Communication Service
stop_service "communication-service" "communication-service"

# 2. Content Service  
stop_service "content-service" "content-service"

# 1. Identity Service
stop_service "identity-service" "identity-service"

echo
echo -e "${BLUE}Checking for any remaining processes on service ports...${NC}"

# Fallback: kill any remaining processes on service ports
ports_services=(
    "8001:Identity Service"
    "8002:Content Service"
    "8003:Communication Service"
    "8004:Workflow Intelligence Service"
)

for port_service in "${ports_services[@]}"; do
    port="${port_service%%:*}"
    service="${port_service##*:}"
    kill_port "$port" "$service"
done

echo
echo -e "${BLUE}Cleaning up log files (optional)...${NC}"

# Ask user if they want to clean up log files
read -p "Do you want to delete service log files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f */service-*.log
    rm -f */*.log
    echo -e "${GREEN}✅ Log files cleaned up${NC}"
else
    echo -e "${YELLOW}Log files preserved${NC}"
fi

echo
echo "=============================================================="
echo -e "${GREEN}🎉 All services stopped successfully!${NC}"
echo
echo -e "${YELLOW}Service log files are located in each service directory:${NC}"
echo -e "${YELLOW}  • identity-service/identity-service.log${NC}"
echo -e "${YELLOW}  • content-service/content-service.log${NC}"
echo -e "${YELLOW}  • communication-service/communication-service.log${NC}"
echo -e "${YELLOW}  • workflow-intelligence-service/workflow-intelligence-service.log${NC}"
echo
echo -e "${BLUE}To restart services: ./dev-start-local.sh${NC}"