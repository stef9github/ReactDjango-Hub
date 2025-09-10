#!/bin/bash

# ReactDjango Hub - Services Coordinator Startup Script
# Centralized orchestration for all microservices

set -e

echo "🚀 ReactDjango Hub - Services Coordinator"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

print_status "Starting ReactDjango Hub Microservices..."
echo ""

# Navigate to services directory
cd "$(dirname "$0")"

print_status "Current directory: $(pwd)"
print_status "Checking for docker-compose.yml..."

if [[ ! -f "docker-compose.yml" ]]; then
    print_error "docker-compose.yml not found in $(pwd)"
    print_error "Please run this script from the services/ directory"
    exit 1
fi

print_success "Found docker-compose.yml"
echo ""

# Stop any existing services
print_status "Stopping any existing services..."
docker-compose down --remove-orphans

# Pull latest images
print_status "Pulling latest images..."
docker-compose pull

# Build services
print_status "Building services..."
docker-compose build

# Start services with dependency order
print_status "Starting services in dependency order..."
echo ""

print_status "1. Starting databases and Redis instances..."
docker-compose up -d identity-db content-db communication-db workflow-db
docker-compose up -d identity-redis content-redis communication-redis workflow-redis

# Wait for databases to be ready
print_status "Waiting for databases to be ready..."
sleep 10

print_status "2. Starting Identity Service (authentication)..."
docker-compose up -d identity-service
sleep 5

print_status "3. Starting Content Service..."
docker-compose up -d content-service
sleep 5

print_status "4. Starting Communication Service..."
docker-compose up -d communication-service communication-worker
sleep 5

print_status "5. Starting Workflow Intelligence Service..."
docker-compose up -d workflow-service workflow-worker
sleep 5

print_status "6. Starting API Gateway (Kong)..."
docker-compose up -d kong

echo ""
print_success "All services started successfully!"
echo ""

# Display service status
print_status "Service Status:"
docker-compose ps

echo ""
print_status "Service Endpoints:"
echo "  🔐 Identity Service:        http://localhost:8001/docs"
echo "  📄 Content Service:         http://localhost:8002/docs"
echo "  📢 Communication Service:   http://localhost:8003/docs"
echo "  🔄 Workflow Service:        http://localhost:8004/docs"
echo "  🚪 API Gateway (Kong):      http://localhost:8000"
echo "  🛠️  Kong Admin API:          http://localhost:8445"
echo ""

print_status "Database Connections:"
echo "  Identity DB:        localhost:5433 (identity_user/identity_pass)"
echo "  Content DB:         localhost:5434 (content_user/content_pass)"
echo "  Communication DB:   localhost:5435 (communication_user/communication_pass)"
echo "  Workflow DB:        localhost:5436 (workflow_user/workflow_pass)"
echo ""

print_status "Redis Connections:"
echo "  Identity Redis:     localhost:6380"
echo "  Content Redis:      localhost:6381"
echo "  Communication Redis: localhost:6382"
echo "  Workflow Redis:     localhost:6383"
echo ""

print_warning "Note: Services may take a few moments to fully initialize."
print_status "Use 'docker-compose logs -f <service-name>' to monitor individual services."
print_status "Use './stop-all-services.sh' to stop all services."

echo ""
print_success "🎉 ReactDjango Hub is ready for development!"