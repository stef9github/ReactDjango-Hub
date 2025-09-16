#!/bin/bash

# =============================================================================
# Communication Service - Local Development Startup Script
# =============================================================================

set -e

echo "🚀 Starting Communication Service (Local Development Mode)"
echo "=========================================================="

# Set environment variables for local development
export USE_DOCKER=false
export DEBUG=true
export LOG_LEVEL=INFO

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
if [ -f "requirements.txt" ]; then
    echo -e "${BLUE}Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Create database if it doesn't exist
echo -e "${BLUE}Ensuring database exists...${NC}"
createdb communication_service 2>/dev/null || echo -e "${YELLOW}Database may already exist${NC}"

echo -e "${GREEN}Starting Communication Service on port 8003...${NC}"
echo -e "${GREEN}API Documentation: http://localhost:8003/docs${NC}"
echo -e "${GREEN}Health Check: http://localhost:8003/health${NC}"
echo -e "${YELLOW}Note: This service depends on Identity Service (port 8001)${NC}"
echo

# Start the service
python main.py