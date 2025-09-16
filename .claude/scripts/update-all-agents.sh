#!/bin/bash

# =============================================================================
# UPDATE ALL AGENTS WITH AUTO-COMMIT AND DATE HANDLING INSTRUCTIONS
# =============================================================================
# This script updates all agent configuration files to include:
# - Auto-commit workflow instructions
# - Proper date handling from environment context
#
# Usage: ./update-all-agents.sh [--date-only]
# Options:
#   --date-only: Only add date handling instructions
# =============================================================================

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
AGENTS_DIR="$SCRIPT_DIR/../agents"

echo -e "${GREEN}Updating all agents with auto-commit and date handling instructions...${NC}"

# Parse command line arguments
DATE_ONLY=false
if [[ "$1" == "--date-only" ]]; then
    DATE_ONLY=true
    echo -e "${BLUE}Running in date-only mode${NC}"
fi

# Function to add date handling section to an agent file
add_date_handling_section() {
    local agent_file=$1
    local agent_name=$2
    
    # Check if date handling section already exists
    if grep -q "## 📅 Date Handling Instructions" "$agent_file"; then
        echo -e "${YELLOW}Date handling section already exists in $agent_name${NC}"
        return
    fi
    
    # Append date handling instructions
    cat >> "$agent_file" << 'EOF'

## 📅 Date Handling Instructions

**IMPORTANT**: Always use the actual current date from the environment context.

### Date Usage Guidelines
- **Check Environment Context**: Always refer to the `<env>` block which contains "Today's date: YYYY-MM-DD"
- **Use Real Dates**: Never use placeholder dates or outdated years
- **Documentation Dates**: Ensure all ADRs, documentation, and dated content use the actual current date
- **Commit Messages**: Use the current date in any dated references
- **No Hardcoding**: Never hardcode dates - always reference the environment date

### Example Date Reference
When creating or updating any dated content:
1. Check the `<env>` block for "Today's date: YYYY-MM-DD"
2. Use that exact date in your documentation
3. For year references, use the current year from the environment date
4. When in doubt, explicitly mention you're using the date from the environment

**Current Date Reminder**: The environment will always provide today's actual date. Use it consistently across all your work.
EOF
    
    echo -e "${GREEN}✓ Added date handling to $agent_name${NC}"
}

# Function to add auto-commit section to an agent file
add_auto_commit_section() {
    local agent_file=$1
    local agent_name=$2
    
    # Check if auto-commit section already exists
    if grep -q "## Automated Commit Workflow" "$agent_file"; then
        echo -e "${YELLOW}Auto-commit section already exists in $agent_name${NC}"
        return
    fi
    
    # Append auto-commit instructions
    cat >> "$agent_file" << EOF

## Automated Commit Workflow

### Auto-Commit After Successful Development

You are equipped with an automated commit workflow. After successfully completing development tasks:

1. **Test Your Changes**: Run relevant tests for your domain
   \`\`\`bash
   .claude/scripts/test-runner.sh $agent_name
   \`\`\`

2. **Auto-Commit Your Work**: Use the automated commit script
   \`\`\`bash
   # For new features
   .claude/scripts/auto-commit.sh $agent_name feat "Description of feature" --test-first
   
   # For bug fixes
   .claude/scripts/auto-commit.sh $agent_name fix "Description of fix" --test-first
   
   # For documentation updates
   .claude/scripts/auto-commit.sh $agent_name docs "Description of documentation" --test-first
   
   # For refactoring
   .claude/scripts/auto-commit.sh $agent_name refactor "Description of refactoring" --test-first
   \`\`\`

3. **Boundary Enforcement**: You can only commit files within your designated directories

### When to Auto-Commit

- After completing a feature or functionality
- After fixing bugs and verifying the fix
- After adding comprehensive test coverage
- After updating documentation
- After refactoring code without breaking functionality

### Safety Checks

The auto-commit script will:
- Verify all changes are within your boundaries
- Run tests automatically (with --test-first flag)
- Check for sensitive information
- Format commit messages properly
- Add proper attribution

### Manual Testing

Before using auto-commit, you can manually test your changes:
\`\`\`bash
.claude/scripts/test-runner.sh $agent_name
\`\`\`

This ensures your changes are ready for commit.
EOF
    
    echo -e "${GREEN}✓ Updated $agent_name${NC}"
}

# List of agents to update
agents=(
    "ag-backend:backend"
    "ag-frontend:frontend"
    "ag-identity:identity"
    "ag-communication:communication"
    "ag-content:content"
    "ag-workflow:workflow"
    "ag-infrastructure:infrastructure"
    "ag-coordinator:coordinator"
    "ag-security:security"
    "ag-techlead:techlead"
    "ag-reviewer:reviewer"
    "ag-claude:claude"
    "ag-surgical-product-manager:surgical-pm"
    "ag-public-procurement-product-manager:procurement-pm"
)

# Update each agent
for agent_config in "${agents[@]}"; do
    IFS=':' read -r filename agent_name <<< "$agent_config"
    agent_file="$AGENTS_DIR/${filename}.md"
    
    if [ -f "$agent_file" ]; then
        echo -e "${BLUE}Updating ${agent_name} agent...${NC}"
        
        # Add date handling section
        add_date_handling_section "$agent_file" "$agent_name"
        
        # Add auto-commit section if not in date-only mode
        if [ "$DATE_ONLY" = false ]; then
            add_auto_commit_section "$agent_file" "$agent_name"
        fi
    else
        echo -e "${YELLOW}Agent file not found: $agent_file${NC}"
    fi
done

# Special handling for documentation agent (if it exists)
if [ -f "$AGENTS_DIR/ag-documentation.md" ]; then
    echo -e "${BLUE}Updating documentation agent...${NC}"
    add_date_handling_section "$AGENTS_DIR/ag-documentation.md" "documentation"
    if [ "$DATE_ONLY" = false ]; then
        add_auto_commit_section "$AGENTS_DIR/ag-documentation.md" "documentation"
    fi
fi

echo ""
if [ "$DATE_ONLY" = true ]; then
    echo -e "${GREEN}✅ All agents have been updated with date handling instructions!${NC}"
    echo ""
    echo "Date handling notes:"
    echo "• Agents will now use the actual date from the environment context"
    echo "• Documentation and ADRs will use real dates (e.g., 2025-09-13)"
    echo "• No more placeholder or hardcoded dates"
else
    echo -e "${GREEN}✅ All agents have been updated with auto-commit and date handling instructions!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Install git hooks: .claude/scripts/install-hooks.sh"
    echo "2. Test the workflow: .claude/scripts/test-runner.sh <agent-name>"
    echo "3. Agents can now auto-commit with: .claude/scripts/auto-commit.sh <agent> <type> <message> --test-first"
    echo ""
    echo "Date handling:"
    echo "• All agents now reference the environment date context"
    echo "• Documentation will use actual dates from Today's date: YYYY-MM-DD"
fi