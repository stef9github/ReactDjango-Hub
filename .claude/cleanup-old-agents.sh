#!/bin/bash
# Cleanup script to remove old agent launcher files
# This consolidates to the new unified launcher system

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Cleaning Up Old Agent Configuration Files${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# List of old agent files to remove (keeping only essential ones)
OLD_AGENT_FILES=(
    # Medical-specific agents (to be removed)
    "claude-medical-frontend-specialization"
    "claude-medical-translator-agent"
    
    # Redundant expert agents (consolidated into main agents)
    "claude-django-backend-expert"
    "claude-react-frontend-expert"
    "claude-identity-service-expert"
    "claude-security-compliance-expert"
    
    # Duplicate/generic versions
    "claude-backend"
    "claude-frontend"
    "claude-identity"
    "claude-communication"
    "claude-content"
    "claude-security"
    
    # Redundant workflow agents
    "claude-commit-workflow"
    "claude-workflow"
    "claude-tech-lead"
    
    # Multi-app and optimization agents (too specialized)
    "claude-frontend-agent-multi-app"
    "claude-claude-code-optimization-expert"
    
    # Old individual service agents (replaced by unified launcher)
    "claude-backend-agent"
    "claude-frontend-agent"
    "claude-deployment-agent"
    "claude-communication-service"
    "claude-content-service"
    "claude-workflow-intelligence-service"
    "claude-services-coordinator"
    "claude-code-reviewer"
    "claude-documentation-agent"
    "claude-testing"
)

# Files to keep (for reference)
KEEP_FILES=(
    "launch-agent.sh"           # New unified launcher
    "agents.yaml"               # Agent configuration
    "agent_session_manager.py"  # Session manager (if exists)
    "enhance_status_line.sh"    # Status utility (if exists)
)

echo -e "${RED}The following files will be removed:${NC}"
echo ""

removed_count=0
for file in "${OLD_AGENT_FILES[@]}"; do
    file_path="$SCRIPT_DIR/$file"
    if [[ -f "$file_path" ]]; then
        echo "  ❌ Removing: $file"
        rm -f "$file_path"
        ((removed_count++))
    fi
done

echo ""
echo -e "${GREEN}Cleanup complete! Removed $removed_count files.${NC}"
echo ""

echo -e "${GREEN}The following files are preserved:${NC}"
for file in "${KEEP_FILES[@]}"; do
    file_path="$SCRIPT_DIR/$file"
    if [[ -f "$file_path" ]]; then
        echo "  ✅ Kept: $file"
    fi
done

echo ""
echo -e "${YELLOW}Note: Old agent documentation in .claude/agents/ directory${NC}"
echo -e "${YELLOW}will be reorganized separately.${NC}"
echo ""

# Create a backup directory for reference
BACKUP_DIR="$SCRIPT_DIR/old-agents-backup"
if [[ ! -d "$BACKUP_DIR" ]]; then
    echo -e "${YELLOW}Creating backup directory for reference...${NC}"
    mkdir -p "$BACKUP_DIR"
    echo "Backup directory created at: $BACKUP_DIR"
fi

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Cleanup Complete!${NC}"
echo -e "${GREEN}  Use: ./.claude/launch-agent.sh <agent-name>${NC}"
echo -e "${GREEN}  Available agents: backend, frontend, identity, etc.${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"