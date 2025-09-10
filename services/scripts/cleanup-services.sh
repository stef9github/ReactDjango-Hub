#!/bin/bash

# Cleanup Services - Remove all containers, volumes, and networks
# Managed by Services Coordinator Agent

echo "🧹 Cleaning up ReactDjango Hub microservices..."
echo "==============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Stop and remove all services containers and volumes
echo "🛑 Stopping and removing all services containers..."
docker-compose down --volumes --remove-orphans --timeout 30

# Remove any containers that might have the same names
echo "🗑️  Removing any conflicting containers..."
docker rm -f $(docker ps -aq --filter "name=services-") 2>/dev/null || true
docker rm -f $(docker ps -aq --filter "name=identity-service") 2>/dev/null || true
docker rm -f $(docker ps -aq --filter "name=content-service") 2>/dev/null || true
docker rm -f $(docker ps -aq --filter "name=communication-service") 2>/dev/null || true
docker rm -f $(docker ps -aq --filter "name=workflow-service") 2>/dev/null || true
docker rm -f $(docker ps -aq --filter "name=kong") 2>/dev/null || true

# Remove any networks that might conflict
echo "🌐 Removing conflicting networks..."
docker network rm reactdjango-hub-services 2>/dev/null || true
docker network rm services_services-network 2>/dev/null || true

# Remove any volumes that might conflict
echo "💾 Removing conflicting volumes..."
docker volume rm $(docker volume ls -q --filter name=services_) 2>/dev/null || true

# Stop any standalone service processes
echo "🛑 Checking for standalone service processes..."
echo "Stopping standalone services on ports 8001-8004..."

# Function to stop process on specific port
stop_service_on_port() {
    local port=$1
    local service_name=$2
    local pid=$(lsof -t -i:$port 2>/dev/null)
    if [ -n "$pid" ]; then
        echo "   🔍 Found standalone $service_name (PID: $pid) on port $port"
        kill -TERM $pid 2>/dev/null && echo "   ✅ Stopped $service_name" || echo "   ⚠️  Failed to stop $service_name"
        sleep 2
        # Force kill if still running
        if kill -0 $pid 2>/dev/null; then
            kill -KILL $pid 2>/dev/null && echo "   ⚡ Force stopped $service_name"
        fi
    fi
}

# Check and stop all service ports
stop_service_on_port 8001 "Identity Service"
stop_service_on_port 8002 "Content Service"
stop_service_on_port 8003 "Communication Service"
stop_service_on_port 8004 "Workflow Intelligence Service"

# Clean up dangling resources
echo "🔄 Cleaning up dangling resources..."
docker system prune -f --volumes

# Clean up Docker build cache
echo "📦 Cleaning up build cache..."
docker builder prune -f

echo ""
echo "✅ Cleanup complete! All Docker containers and standalone services have been stopped."
echo "You can now start services cleanly with: ./scripts/start-all-services.sh"