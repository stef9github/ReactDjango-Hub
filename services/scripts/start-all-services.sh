#!/bin/bash

# Start All Services - Development Mode
# Managed by Services Coordinator Agent

echo "🚀 Starting all ReactDjango Hub microservices..."
echo "================================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start services with Docker Compose
echo "🐳 Starting services with Docker Compose..."
docker-compose up -d

# Wait a moment for services to start
echo "⏳ Waiting for services to initialize..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service health..."
./scripts/health-check-all.sh

echo ""
echo "📡 Service URLs:"
echo "  🔐 Identity Service:     http://localhost:8001/docs"
echo "  📄 Content Service:      http://localhost:8002/docs"
echo "  📢 Communication Service: http://localhost:8003/docs"
echo "  🔄 Workflow Service:     http://localhost:8004/docs"
echo ""
echo "🗄️  Database Ports:"
echo "  Identity DB:     localhost:5433"
echo "  Content DB:      localhost:5434"
echo "  Communication DB: localhost:5435"
echo "  Workflow DB:     localhost:5436"
echo ""
echo "🔴 Redis Ports:"
echo "  Identity Redis:     localhost:6380"
echo "  Content Redis:      localhost:6381"
echo "  Communication Redis: localhost:6382"
echo "  Workflow Redis:     localhost:6383"

echo ""
echo "✅ All services started! Use 'docker-compose logs -f' to view logs."