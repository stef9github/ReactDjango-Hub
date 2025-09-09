#!/bin/bash

# Sync Dependencies Across Services
# Managed by Services Coordinator Agent

echo "🔄 Synchronizing dependencies across all services..."
echo "=================================================="

# Define shared dependencies that should be consistent
shared_deps=(
    "fastapi"
    "sqlalchemy"
    "alembic"
    "redis"
    "psycopg2-binary"
    "httpx"
    "python-jose"
    "python-dotenv"
    "pydantic"
    "pytest"
    "black"
    "isort"
    "flake8"
)

services=(
    "identity-service"
    "content-service"
    "communication-service"
    "workflow-intelligence-service"
)

echo "📋 Checking shared dependencies:"
echo ""

for dep in "${shared_deps[@]}"; do
    echo "🔍 Checking $dep versions:"
    
    for service in "${services[@]}"; do
        if [ -f "$service/requirements.txt" ]; then
            version=$(grep "^$dep==" "$service/requirements.txt" | cut -d'=' -f3)
            if [ -n "$version" ]; then
                echo "  $service: $version"
            else
                echo "  $service: ❌ Not found"
            fi
        else
            echo "  $service: ❌ No requirements.txt"
        fi
    done
    echo ""
done

echo "⚠️  Manual Review Required:"
echo "  1. Check for version mismatches above"
echo "  2. Update requirements.txt files manually if needed"
echo "  3. Test compatibility after updates"
echo ""
echo "💡 Common update command:"
echo "  find . -name 'requirements.txt' -exec sed -i 's/package==old_version/package==new_version/' {} +"