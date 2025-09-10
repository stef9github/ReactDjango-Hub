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

# Gracefully stop services
echo "⏹️  Gracefully stopping services..."
docker-compose stop --timeout 30

# Show status
echo ""
echo "📊 Service status after shutdown:"
docker-compose ps

echo ""
echo "✅ All services have been stopped gracefully."
echo "💡 Use 'docker-compose start' to restart or './scripts/start-all-services.sh' for a fresh start."
echo "🗑️  Use './scripts/cleanup-services.sh' to completely remove all containers and volumes."