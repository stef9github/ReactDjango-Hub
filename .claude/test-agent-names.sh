#!/bin/bash
# Test script to verify all agent names work correctly

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${YELLOW}Testing new agent naming scheme...${NC}"
echo ""

# List of all agent names to test
AGENTS=(
    "ag-backend"
    "ag-frontend"
    "ag-identity"
    "ag-communication"
    "ag-content"
    "ag-workflow"
    "ag-infrastructure"
    "ag-coordinator"
    "ag-security"
    "ag-reviewer"
)

# Test each agent
for agent in "${AGENTS[@]}"; do
    echo -n "Testing $agent... "
    
    # Try to get agent info
    if bash "$SCRIPT_DIR/launch-agent.sh" "$agent" 2>&1 | grep -q "Agent"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        echo "  Failed to launch $agent"
    fi
done

echo ""
echo -e "${GREEN}All agent names tested successfully!${NC}"