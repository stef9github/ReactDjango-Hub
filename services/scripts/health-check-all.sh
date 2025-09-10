#!/bin/bash

# Health Check All Services
# Managed by Services Coordinator Agent

echo "🔍 Checking all microservices health..."
echo "========================================="

services=(
    "identity-service:8001"
    "content-service:8002"
    "communication-service:8003"
    "workflow-service:8004"
)

all_healthy=true

for service in "${services[@]}"; do
    name="${service%:*}"
    port="${service#*:}"
    
    echo -n "🔍 $name (port $port): "
    
    if curl -s -f "http://localhost:$port/health" > /dev/null; then
        echo "✅ Healthy"
        
        # Get detailed health info
        health_info=$(curl -s "http://localhost:$port/health" | jq -r '.status // "unknown"' 2>/dev/null)
        if [ "$health_info" != "unknown" ]; then
            echo "   Status: $health_info"
        fi
    else
        echo "❌ Unhealthy"
        all_healthy=false
    fi
done

echo "========================================="

if $all_healthy; then
    echo "🎉 All services are healthy!"
    exit 0
else
    echo "⚠️  Some services are unhealthy. Check the logs."
    exit 1
fi