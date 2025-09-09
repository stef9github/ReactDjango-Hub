#!/bin/bash

# Claude Code optimized development commands for microservices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service configuration
SERVICES=("auth-service" "analytics-service" "billing-service" "core-service")
SERVICE_PORTS=("8001" "8002" "8003" "8004")
CLAUDE_AGENTS=("auth-service-agent" "analytics-service-agent" "billing-service-agent" "core-service-agent")

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if service exists
check_service() {
    local service=$1
    if [[ ! -d "services/$service" ]]; then
        log_error "Service '$service' not found in services/ directory"
        exit 1
    fi
}

# Start individual service for development
start_service() {
    local service=$1
    check_service $service
    
    log_info "Starting $service for Claude Code development..."
    
    cd "services/$service"
    
    # Check if requirements.txt exists and install
    if [[ -f "requirements.txt" ]]; then
        log_info "Installing dependencies for $service..."
        pip install -r requirements.txt
    fi
    
    # Start service based on type
    case $service in
        "auth-service")
            log_info "Starting Auth Service on port 8001..."
            uvicorn main:app --reload --port 8001 --host 0.0.0.0
            ;;
        "analytics-service")
            log_info "Starting Analytics Service on port 8002..."
            # Assuming Go service
            go run main.go
            ;;
        "billing-service") 
            log_info "Starting Billing Service on port 8003..."
            # Assuming Java service
            ./gradlew bootRun
            ;;
        "core-service")
            log_info "Starting Core Service on port 8004..."
            python manage.py runserver 0.0.0.0:8004
            ;;
        *)
            log_error "Unknown service: $service"
            exit 1
            ;;
    esac
}

# Start Claude Code agent for specific service
start_agent() {
    local service=$1
    check_service $service
    
    log_info "Starting Claude Code agent for $service..."
    
    # Create agent-specific working directory
    mkdir -p ".claude/agents/$service/workspace"
    
    # Set service-specific context
    export CLAUDE_SERVICE_CONTEXT="$service"
    export CLAUDE_SERVICE_PATH="services/$service"
    export CLAUDE_AGENT_CONFIG=".claude/agents/${service}-agent.md"
    
    # Launch Claude with service context
    if command -v claude &> /dev/null; then
        log_info "Opening Claude Code in $service directory..."
        log_info "Agent will be configured for: $service"
        log_info "Working directory: services/$service"
        
        # Show agent configuration
        if [[ -f ".claude/agents/${service}-agent.md" ]]; then
            log_info "Loading agent configuration: .claude/agents/${service}-agent.md"
            echo ""
            echo "📋 Agent Configuration:"
            head -10 ".claude/agents/${service}-agent.md"
            echo ""
        fi
        
        # Change to service directory and start Claude
        cd "services/$service"
        log_info "Starting Claude Code CLI..."
        log_info "The agent will focus only on $service development."
        
        # Start Claude Code (it will read CLAUDE.md automatically)
        claude
    else
        log_error "Claude Code CLI not found. Please install: https://claude.ai/code"
        log_info "Installation: Visit https://claude.ai/code for setup instructions"
        exit 1
    fi
}

# Start development environment for specific service
dev_service() {
    local service=$1
    check_service $service
    
    log_info "Setting up development environment for $service..."
    
    # Start service dependencies
    case $service in
        "auth-service")
            docker-compose -f services/auth-service/docker-compose.yml up -d auth-db auth-redis consul
            ;;
        "analytics-service")
            docker-compose -f services/analytics-service/docker-compose.yml up -d analytics-db kafka zookeeper
            ;;
        "billing-service")
            docker-compose -f services/billing-service/docker-compose.yml up -d billing-db redis
            ;;
        "core-service")
            docker-compose -f services/core-service/docker-compose.yml up -d core-db redis
            ;;
    esac
    
    # Wait for dependencies to be ready
    sleep 5
    
    # Start the service
    start_service $service
}

# Health check for all services
health_check() {
    log_info "Checking health of all microservices..."
    
    local all_healthy=true
    
    for i in "${!SERVICES[@]}"; do
        local service="${SERVICES[$i]}"
        local port="${SERVICE_PORTS[$i]}"
        
        if curl -f -s "http://localhost:$port/health" > /dev/null; then
            log_success "$service is healthy (port $port)"
        else
            log_error "$service is unhealthy or not running (port $port)"
            all_healthy=false
        fi
    done
    
    if $all_healthy; then
        log_success "All microservices are healthy!"
    else
        log_warning "Some microservices are not healthy"
        exit 1
    fi
}

# Start all services for development
start_all() {
    log_info "Starting all microservices development environment..."
    
    # Start infrastructure services
    docker-compose up -d consul kafka zookeeper redis postgres
    
    # Wait for infrastructure
    sleep 10
    
    # Start each service in background
    for service in "${SERVICES[@]}"; do
        (dev_service $service) &
    done
    
    # Wait for all services to start
    sleep 15
    
    # Run health check
    health_check
}

# Stop all services
stop_all() {
    log_info "Stopping all microservices..."
    
    # Stop Docker services
    docker-compose down
    
    # Kill any running services
    for port in "${SERVICE_PORTS[@]}"; do
        local pid=$(lsof -t -i:$port)
        if [[ ! -z "$pid" ]]; then
            kill $pid
            log_info "Killed process on port $port"
        fi
    done
    
    log_success "All services stopped"
}

# Generate service template
generate_service() {
    local service_name=$1
    local service_type=${2:-"fastapi"}
    local service_port=${3:-"8005"}
    
    if [[ -z "$service_name" ]]; then
        log_error "Service name is required"
        echo "Usage: $0 generate <service-name> [type] [port]"
        exit 1
    fi
    
    local service_dir="services/$service_name"
    
    if [[ -d "$service_dir" ]]; then
        log_error "Service '$service_name' already exists"
        exit 1
    fi
    
    log_info "Generating new $service_type service: $service_name"
    
    mkdir -p "$service_dir"
    
    # Generate based on type
    case $service_type in
        "fastapi")
            generate_fastapi_service "$service_dir" "$service_name" "$service_port"
            ;;
        "django")
            generate_django_service "$service_dir" "$service_name" "$service_port"
            ;;
        "go")
            generate_go_service "$service_dir" "$service_name" "$service_port"
            ;;
        *)
            log_error "Unknown service type: $service_type"
            exit 1
            ;;
    esac
    
    # Generate Claude agent config
    generate_agent_config "$service_name" "$service_type" "$service_port"
    
    log_success "Service '$service_name' generated successfully!"
    log_info "To start development: $0 dev $service_name"
    log_info "To start Claude agent: $0 agent $service_name"
}

# Generate FastAPI service template
generate_fastapi_service() {
    local service_dir=$1
    local service_name=$2
    local service_port=$3
    
    cat > "$service_dir/main.py" << EOF
"""
$service_name - Microservice
Generated by Claude Code development tools
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="$service_name",
    description="Generated microservice",
    version="1.0.0"
)

class HealthResponse(BaseModel):
    service: str = "$service_name"
    status: str
    version: str = "1.0.0"

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy")

@app.get("/")
async def root():
    return {"message": "Welcome to $service_name"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=$service_port)
EOF

    cat > "$service_dir/requirements.txt" << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
EOF

    cat > "$service_dir/Dockerfile" << EOF
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE $service_port
CMD ["python", "main.py"]
EOF
}

# Generate Claude agent configuration
generate_agent_config() {
    local service_name=$1
    local service_type=$2
    local service_port=$3
    
    cat > ".claude/agents/${service_name}-agent.md" << EOF
# $service_name Agent Configuration

You are a specialized Claude Code agent for the **$service_name** microservice.

## 🎯 Service Scope
- **Directory**: \`services/$service_name/\`
- **Technology**: $service_type
- **Port**: $service_port

## 🧠 Context Boundaries
- Focus only on $service_name development
- Do not modify other microservices
- Communicate with other services via APIs only

## 🔧 Development Commands
\`\`\`bash
cd services/$service_name
# Your service-specific commands here
\`\`\`

## 📊 Responsibilities
- Implement $service_name business logic
- Maintain service health endpoints
- Handle service-specific testing
- Optimize service performance

Remember: Stay focused on $service_name only!
EOF
}

# Main command dispatcher
case "${1:-help}" in
    "start")
        if [[ -n "$2" ]]; then
            start_service "$2"
        else
            start_all
        fi
        ;;
    "agent")
        if [[ -n "$2" ]]; then
            start_agent "$2"
        else
            log_error "Specify service name: $0 agent <service-name>"
            exit 1
        fi
        ;;
    "dev")
        if [[ -n "$2" ]]; then
            dev_service "$2"
        else
            start_all
        fi
        ;;
    "stop")
        stop_all
        ;;
    "health")
        health_check
        ;;
    "generate")
        generate_service "$2" "$3" "$4"
        ;;
    "help")
        echo "Claude Code Microservices Development Tool"
        echo ""
        echo "Commands:"
        echo "  start [service]     Start specific service or all services"
        echo "  agent <service>     Start Claude Code agent for service"
        echo "  dev [service]       Start development environment"
        echo "  stop               Stop all services"
        echo "  health             Check health of all services"
        echo "  generate <name>    Generate new service template"
        echo "  help               Show this help"
        echo ""
        echo "Available services: ${SERVICES[*]}"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Run '$0 help' for available commands"
        exit 1
        ;;
esac