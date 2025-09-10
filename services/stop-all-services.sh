#!/bin/bash

# ReactDjango Hub - Services Coordinator Stop Script
# Graceful shutdown for all microservices

set -e

echo "🛑 ReactDjango Hub - Stopping All Services"
echo "=========================================="
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
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Navigate to services directory
cd "$(dirname "$0")"

print_status "Current directory: $(pwd)"

if [[ ! -f "docker-compose.yml" ]]; then
    print_error "docker-compose.yml not found in $(pwd)"
    exit 1
fi

print_status "Gracefully stopping all services..."

# Stop services in reverse dependency order
print_status "1. Stopping API Gateway (Kong)..."
docker-compose stop kong

print_status "2. Stopping Workflow Intelligence Service..."
docker-compose stop workflow-service workflow-worker

print_status "3. Stopping Communication Service..."
docker-compose stop communication-service communication-worker

print_status "4. Stopping Content Service..."
docker-compose stop content-service

print_status "5. Stopping Identity Service..."
docker-compose stop identity-service

print_status "6. Stopping Redis instances..."
docker-compose stop identity-redis content-redis communication-redis workflow-redis

print_status "7. Stopping databases..."
docker-compose stop identity-db content-db communication-db workflow-db

print_status "Removing containers and networks..."
docker-compose down --remove-orphans

echo ""
print_success "All services stopped successfully!"

# Optionally clean up volumes (ask user)
echo ""
read -p "Do you want to remove data volumes? This will delete all database data. (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Removing data volumes..."
    docker-compose down -v
    print_success "Data volumes removed."
else
    print_status "Data volumes preserved."
fi

print_success "🎉 ReactDjango Hub services stopped cleanly!"