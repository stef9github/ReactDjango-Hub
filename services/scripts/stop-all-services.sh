#!/bin/bash

# Stop All Services - Graceful shutdown
# Managed by Services Coordinator Agent

echo "🛑 Stopping all ReactDjango Hub microservices..."
echo "==============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Services may already be stopped."
    exit 0
fi

# Gracefully stop Docker Compose services
echo "⏹️  Gracefully stopping Docker Compose services..."
docker-compose stop --timeout 30

# Stop any standalone service processes
echo "🛑 Checking for standalone service processes..."

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

# Show Docker status
echo ""
echo "📊 Docker service status after shutdown:"
docker-compose ps

echo ""
echo "✅ All services (Docker and standalone) have been stopped gracefully."
echo "💡 Use 'docker-compose start' to restart Docker services or './scripts/start-all-services.sh' for a fresh start."
echo "🗑️  Use './scripts/cleanup-services.sh' to completely remove all containers and volumes."