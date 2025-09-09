#!/bin/bash
# Auth Service Management Script
# Usage: ./scripts/manage.sh [command]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="auth-service"
SERVICE_PORT="8001"
SERVICE_URL="http://localhost:$SERVICE_PORT"

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if service is running
check_service() {
    if curl -s "$SERVICE_URL/health" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Wait for service to be ready
wait_for_service() {
    local max_attempts=30
    local attempt=1
    
    log_info "Waiting for service to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if check_service; then
            log_success "Service is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 1
        ((attempt++))
    done
    
    log_error "Service failed to start within ${max_attempts} seconds"
    return 1
}

# Commands
cmd_help() {
    echo "Auth Service Management Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start           Start the auth service"
    echo "  stop            Stop the auth service"
    echo "  restart         Restart the auth service"
    echo "  status          Check service status"
    echo "  health          Check service health"
    echo "  logs            Show service logs"
    echo "  test            Run service tests"
    echo "  migrate         Run database migrations"
    echo "  reset-db        Reset database (DESTRUCTIVE!)"
    echo "  backup-db       Backup database"
    echo "  install         Install dependencies"
    echo "  setup           Complete setup for new environment"
    echo "  monitor         Monitor service continuously"
    echo ""
}

cmd_start() {
    log_info "Starting $SERVICE_NAME..."
    
    # Check dependencies
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is not installed"
        exit 1
    fi
    
    # Check if already running
    if check_service; then
        log_warning "Service is already running"
        return 0
    fi
    
    # Start service
    if [ -f "main.py" ]; then
        python main.py &
        SERVICE_PID=$!
        echo $SERVICE_PID > .service.pid
        
        # Wait for service to be ready
        if wait_for_service; then
            log_success "Service started successfully (PID: $SERVICE_PID)"
            log_info "Service available at: $SERVICE_URL"
            log_info "API docs at: $SERVICE_URL/docs"
        else
            log_error "Service failed to start properly"
            cmd_stop
            exit 1
        fi
    else
        log_error "main.py not found. Run from service directory."
        exit 1
    fi
}

cmd_stop() {
    log_info "Stopping $SERVICE_NAME..."
    
    # Kill service by PID if available
    if [ -f ".service.pid" ]; then
        SERVICE_PID=$(cat .service.pid)
        if ps -p $SERVICE_PID > /dev/null 2>&1; then
            kill $SERVICE_PID
            log_success "Service stopped (PID: $SERVICE_PID)"
        else
            log_warning "Service PID $SERVICE_PID not found"
        fi
        rm -f .service.pid
    fi
    
    # Kill any remaining python processes running main.py
    pkill -f "python.*main.py" || true
    
    log_success "Service stopped"
}

cmd_restart() {
    cmd_stop
    sleep 2
    cmd_start
}

cmd_status() {
    if check_service; then
        log_success "Service is running"
        
        # Get service info
        HEALTH=$(curl -s "$SERVICE_URL/health" 2>/dev/null || echo '{}')
        STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
        VERSION=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('version', 'unknown'))" 2>/dev/null || echo "unknown")
        
        echo "  Status: $STATUS"
        echo "  Version: $VERSION"
        echo "  URL: $SERVICE_URL"
    else
        log_error "Service is not running"
        exit 1
    fi
}

cmd_health() {
    if check_service; then
        log_success "Service is healthy"
        curl -s "$SERVICE_URL/health" | python3 -m json.tool
    else
        log_error "Service is not responding"
        exit 1
    fi
}

cmd_logs() {
    if [ -f ".service.pid" ]; then
        SERVICE_PID=$(cat .service.pid)
        log_info "Following logs for PID: $SERVICE_PID"
        # In a real setup, you'd tail actual log files
        # For now, just show the process
        ps -p $SERVICE_PID -o pid,ppid,cmd
    else
        log_warning "No service PID file found"
    fi
}

cmd_test() {
    log_info "Running service tests..."
    
    if [ ! -f "test_full_service.py" ]; then
        log_error "Test file not found"
        exit 1
    fi
    
    if check_service; then
        python test_full_service.py
        log_success "Tests completed"
    else
        log_error "Service is not running. Start service first."
        exit 1
    fi
}

cmd_migrate() {
    log_info "Running database migrations..."
    
    if command -v alembic &> /dev/null; then
        alembic upgrade head
        log_success "Migrations completed"
    else
        log_error "Alembic not found. Install dependencies first."
        exit 1
    fi
}

cmd_reset_db() {
    log_warning "This will DESTROY all data in the database!"
    read -p "Are you sure? Type 'yes' to confirm: " -r
    
    if [[ $REPLY == "yes" ]]; then
        log_info "Resetting database..."
        
        # Drop and recreate database
        if command -v dropdb &> /dev/null && command -v createdb &> /dev/null; then
            dropdb auth_service || true
            createdb auth_service
            
            # Run migrations
            cmd_migrate
            
            log_success "Database reset completed"
        else
            log_error "PostgreSQL tools not found"
            exit 1
        fi
    else
        log_info "Database reset cancelled"
    fi
}

cmd_backup_db() {
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    
    log_info "Creating database backup: $backup_file"
    
    if command -v pg_dump &> /dev/null; then
        pg_dump auth_service > "$backup_file"
        log_success "Database backup created: $backup_file"
    else
        log_error "pg_dump not found"
        exit 1
    fi
}

cmd_install() {
    log_info "Installing dependencies..."
    
    # Check if in virtual environment
    if [[ -z "$VIRTUAL_ENV" ]]; then
        log_warning "Not in a virtual environment"
        read -p "Continue anyway? (y/N): " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
    
    if [ -f "requirements-latest.txt" ]; then
        pip install -r requirements-latest.txt
        log_success "Dependencies installed"
    else
        log_error "requirements-latest.txt not found"
        exit 1
    fi
}

cmd_setup() {
    log_info "Setting up auth service environment..."
    
    # Install dependencies
    cmd_install
    
    # Check and start database services
    if command -v brew &> /dev/null; then
        log_info "Starting PostgreSQL and Redis..."
        brew services start postgresql@17 || true
        brew services start redis || true
        sleep 2
    fi
    
    # Run migrations
    cmd_migrate
    
    log_success "Setup completed!"
    log_info "Run './scripts/manage.sh start' to start the service"
}

cmd_monitor() {
    log_info "Monitoring $SERVICE_NAME (Press Ctrl+C to stop)..."
    
    while true; do
        clear
        echo "🔍 Auth Service Monitor - $(date)"
        echo "=================================="
        
        if check_service; then
            # Get service info
            HEALTH=$(curl -s "$SERVICE_URL/health" 2>/dev/null || echo '{}')
            TEST_INFO=$(curl -s "$SERVICE_URL/test-info" 2>/dev/null || echo '{}')
            
            echo "✅ Service: Running"
            echo "🔗 URL: $SERVICE_URL"
            
            # Extract stats if available
            TOTAL_USERS=$(echo "$TEST_INFO" | python3 -c "
import sys,json
try:
    data = json.load(sys.stdin)
    print(data.get('statistics', {}).get('total_users', 'N/A'))
except:
    print('N/A')
" 2>/dev/null)
            
            VERIFIED_USERS=$(echo "$TEST_INFO" | python3 -c "
import sys,json
try:
    data = json.load(sys.stdin)
    print(data.get('statistics', {}).get('verified_users', 'N/A'))
except:
    print('N/A')
" 2>/dev/null)
            
            echo "👥 Total Users: $TOTAL_USERS"
            echo "✅ Verified Users: $VERIFIED_USERS"
            
        else
            echo "❌ Service: Not Running"
        fi
        
        sleep 5
    done
}

# Main command dispatcher
case "${1:-help}" in
    start)      cmd_start ;;
    stop)       cmd_stop ;;
    restart)    cmd_restart ;;
    status)     cmd_status ;;
    health)     cmd_health ;;
    logs)       cmd_logs ;;
    test)       cmd_test ;;
    migrate)    cmd_migrate ;;
    reset-db)   cmd_reset_db ;;
    backup-db)  cmd_backup_db ;;
    install)    cmd_install ;;
    setup)      cmd_setup ;;
    monitor)    cmd_monitor ;;
    help|*)     cmd_help ;;
esac