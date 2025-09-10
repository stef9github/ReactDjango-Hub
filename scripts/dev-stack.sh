#!/bin/bash

# Local Development Stack Management Script
# Manages all microservices containers for local development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.local.yml"

print_banner() {
    echo -e "${BLUE}"
    echo "=========================================="
    echo "  ReactDjango Hub - Dev Stack Manager"
    echo "=========================================="
    echo -e "${NC}"
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    print_status "Dependencies check passed"
}

build_services() {
    print_status "Building all microservices..."
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    print_status "Build completed"
}

start_stack() {
    print_status "Starting all microservices stack..."
    cd "$PROJECT_ROOT"
    
    # Start infrastructure first (databases, redis)
    print_status "Starting infrastructure services..."
    docker-compose -f "$COMPOSE_FILE" up -d main-db identity-db communication-db content-db workflow-db
    docker-compose -f "$COMPOSE_FILE" up -d main-redis identity-redis communication-redis content-redis workflow-redis
    docker-compose -f "$COMPOSE_FILE" up -d minio
    
    # Wait for infrastructure to be ready
    print_status "Waiting for infrastructure to be ready..."
    sleep 10
    
    # Start microservices
    print_status "Starting microservices..."
    docker-compose -f "$COMPOSE_FILE" up -d identity-service
    sleep 5
    docker-compose -f "$COMPOSE_FILE" up -d communication-service content-service
    sleep 5
    docker-compose -f "$COMPOSE_FILE" up -d workflow-intelligence-service
    sleep 5
    docker-compose -f "$COMPOSE_FILE" up -d backend frontend
    
    print_status "All services started!"
    show_services
}

stop_stack() {
    print_status "Stopping all microservices..."
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" down
    print_status "All services stopped"
}

restart_stack() {
    print_status "Restarting all microservices..."
    stop_stack
    sleep 2
    start_stack
}

show_status() {
    print_status "Service status:"
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" ps
}

show_logs() {
    cd "$PROJECT_ROOT"
    if [ -z "$1" ]; then
        print_status "Showing logs for all services..."
        docker-compose -f "$COMPOSE_FILE" logs -f --tail=100
    else
        print_status "Showing logs for service: $1"
        docker-compose -f "$COMPOSE_FILE" logs -f --tail=100 "$1"
    fi
}

health_check() {
    print_status "Checking service health..."
    cd "$PROJECT_ROOT"
    
    services=(
        "identity-service:8001:/health"
        "communication-service:8002:/health" 
        "content-service:8003:/health"
        "workflow-intelligence-service:8004:/health"
        "backend:8000:/api/health/"
        "frontend:3000:/"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port path <<< "$service"
        url="http://localhost:${port}${path}"
        
        echo -n "Checking $name ($url)... "
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Healthy${NC}"
        else
            echo -e "${RED}✗ Unhealthy${NC}"
        fi
    done
    
    # Check databases
    echo -n "Checking databases... "
    if docker-compose -f "$COMPOSE_FILE" exec -T main-db pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
    else
        echo -e "${RED}✗ Unhealthy${NC}"
    fi
    
    # Check Redis
    echo -n "Checking Redis... "
    if docker-compose -f "$COMPOSE_FILE" exec -T main-redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Healthy${NC}"
    else
        echo -e "${RED}✗ Unhealthy${NC}"
    fi
}

show_services() {
    print_status "Available services:"
    echo -e "${BLUE}Frontend:${NC}"
    echo "  • React App: http://localhost:3000"
    echo "  • Vite Dev: http://localhost:5173"
    echo ""
    echo -e "${BLUE}Backend Services:${NC}"
    echo "  • Django API: http://localhost:8000/api/docs/"
    echo "  • Identity Service: http://localhost:8001/docs"
    echo "  • Communication Service: http://localhost:8002/docs"
    echo "  • Content Service: http://localhost:8003/docs"
    echo "  • Workflow Service: http://localhost:8004/docs"
    echo ""
    echo -e "${BLUE}Infrastructure:${NC}"
    echo "  • MinIO Console: http://localhost:9001 (admin/minioadmin)"
    echo "  • PostgreSQL: localhost:5432 (main), 5433-5436 (services)"
    echo "  • Redis: localhost:6379 (main), 6380-6383 (services)"
}

clean_stack() {
    print_warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$PROJECT_ROOT"
        docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
        docker system prune -f
        print_status "Stack cleaned"
    else
        print_status "Clean cancelled"
    fi
}

run_tests() {
    print_status "Running tests in all services..."
    cd "$PROJECT_ROOT"
    
    # Test identity service
    print_status "Testing Identity Service..."
    docker-compose -f "$COMPOSE_FILE" exec identity-service pytest -v || true
    
    # Test communication service
    print_status "Testing Communication Service..."
    docker-compose -f "$COMPOSE_FILE" exec communication-service pytest -v || true
    
    # Test content service
    print_status "Testing Content Service..."
    docker-compose -f "$COMPOSE_FILE" exec content-service pytest -v || true
    
    # Test workflow service
    print_status "Testing Workflow Intelligence Service..."
    docker-compose -f "$COMPOSE_FILE" exec workflow-intelligence-service pytest -v || true
    
    # Test Django backend
    print_status "Testing Django Backend..."
    docker-compose -f "$COMPOSE_FILE" exec backend python manage.py test || true
    
    # Test React frontend
    print_status "Testing React Frontend..."
    docker-compose -f "$COMPOSE_FILE" exec frontend npm test -- --watchAll=false || true
}

shell_access() {
    if [ -z "$1" ]; then
        print_error "Please specify a service name"
        echo "Available services: identity-service, communication-service, content-service, workflow-intelligence-service, backend, frontend"
        return 1
    fi
    
    print_status "Opening shell in $1..."
    cd "$PROJECT_ROOT"
    docker-compose -f "$COMPOSE_FILE" exec "$1" /bin/bash
}

show_help() {
    print_banner
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start          Start all microservices"
    echo "  stop           Stop all microservices"
    echo "  restart        Restart all microservices"
    echo "  build          Build all service images"
    echo "  status         Show service status"
    echo "  health         Check service health"
    echo "  logs [service] Show logs (all services or specific service)"
    echo "  services       Show available services and URLs"
    echo "  test           Run tests in all services"
    echo "  shell <service> Open shell in service container"
    echo "  clean          Remove all containers and volumes"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start all services"
    echo "  $0 logs backend            # Show backend logs"
    echo "  $0 shell identity-service  # Open shell in identity service"
}

# Main execution
case "${1:-help}" in
    start)
        print_banner
        check_dependencies
        start_stack
        ;;
    stop)
        print_banner
        stop_stack
        ;;
    restart)
        print_banner
        check_dependencies
        restart_stack
        ;;
    build)
        print_banner
        check_dependencies
        build_services
        ;;
    status)
        show_status
        ;;
    health)
        health_check
        ;;
    logs)
        show_logs "$2"
        ;;
    services)
        show_services
        ;;
    test)
        run_tests
        ;;
    shell)
        shell_access "$2"
        ;;
    clean)
        clean_stack
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac