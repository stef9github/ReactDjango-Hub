#!/bin/bash
# Unified Claude Agent Launcher
# Single entry point for all agent sessions

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Define available agents
VALID_AGENTS="backend frontend identity communication content workflow infrastructure coordinator security review"

# Function to get agent info
get_agent_info() {
    local agent="$1"
    case "$agent" in
        backend) echo "Django Backend|Core business logic, APIs, data models" ;;
        frontend) echo "React Frontend|User interface, components, state management" ;;
        identity) echo "Identity Service|Authentication, users, MFA, RBAC" ;;
        communication) echo "Communication Service|Notifications, messaging, real-time" ;;
        content) echo "Content Service|Document management, file storage" ;;
        workflow) echo "Workflow Intelligence|Process automation, AI workflows" ;;
        infrastructure) echo "Infrastructure Agent|Docker, Kubernetes, CI/CD, deployment" ;;
        coordinator) echo "Services Coordinator|API contracts, service mesh, integration" ;;
        security) echo "Security & Compliance|Security audits, compliance, vulnerability scanning" ;;
        review) echo "Code Review|Code quality, PR reviews, best practices" ;;
        *) echo "Unknown|Unknown agent" ;;
    esac
}

# Function to display usage
show_usage() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Claude Agent Launcher - Simplified Agent Management${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Usage:${NC} $0 <agent-name>"
    echo ""
    echo -e "${YELLOW}Available Agents:${NC}"
    echo ""
    
    # Display agents grouped by category
    echo -e "${GREEN}Core Service Agents:${NC}"
    for agent in backend frontend identity communication content workflow; do
        info=$(get_agent_info "$agent")
        IFS='|' read -r title desc <<< "$info"
        printf "  %-20s - %s\n" "$agent" "$desc"
    done
    echo ""
    
    echo -e "${GREEN}Infrastructure & Coordination:${NC}"
    for agent in infrastructure coordinator; do
        info=$(get_agent_info "$agent")
        IFS='|' read -r title desc <<< "$info"
        printf "  %-20s - %s\n" "$agent" "$desc"
    done
    echo ""
    
    echo -e "${GREEN}Quality & Compliance:${NC}"
    for agent in security review; do
        info=$(get_agent_info "$agent")
        IFS='|' read -r title desc <<< "$info"
        printf "  %-20s - %s\n" "$agent" "$desc"
    done
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

# Function to activate agent session
activate_agent_session() {
    local agent_name="$1"
    echo -e "${BLUE}🤖 Activating ${agent_name} agent session...${NC}"
    
    # Check if agent session manager exists
    if [[ -f "$SCRIPT_DIR/agent_session_manager.py" ]]; then
        python3 "$SCRIPT_DIR/agent_session_manager.py" activate "$agent_name" 2>/dev/null || true
    fi
    
    # Set agent-specific environment variables
    export CLAUDE_AGENT="$agent_name"
    export CLAUDE_AGENT_ACTIVE="true"
    echo ""
}

# Function to show status
show_status() {
    echo -e "${YELLOW}📊 Current Project Status:${NC}"
    
    # Show git status
    if command -v git &> /dev/null && git rev-parse --git-dir &> /dev/null; then
        branch=$(git branch --show-current 2>/dev/null || echo "unknown")
        echo -e "  Branch: ${GREEN}$branch${NC}"
        
        # Count changes
        changes=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
        if [[ $changes -gt 0 ]]; then
            echo -e "  Changes: ${YELLOW}$changes files modified${NC}"
        else
            echo -e "  Changes: ${GREEN}Clean working tree${NC}"
        fi
    fi
    
    # Show active services status if available
    if [[ -f "$SCRIPT_DIR/enhance_status_line.sh" ]]; then
        bash "$SCRIPT_DIR/enhance_status_line.sh" compact 2>/dev/null || true
    fi
    
    echo ""
}

# Function to display agent instructions
show_agent_instructions() {
    local agent_name="$1"
    local info=$(get_agent_info "$agent_name")
    IFS='|' read -r title desc <<< "$info"
    
    echo -e "${GREEN}╭─ $title Agent ─────────────────────────────────╮${NC}"
    echo -e "${GREEN}│  ${NC}Focus: $desc"
    echo -e "${GREEN}╰────────────────────────────────────────────────────────╯${NC}"
    echo ""
    
    # Show agent-specific paths
    case "$agent_name" in
        backend)
            echo "  📁 Working Directory: $PROJECT_ROOT/backend"
            echo "  🔧 Key Commands: python manage.py [command]"
            ;;
        frontend)
            echo "  📁 Working Directory: $PROJECT_ROOT/frontend"
            echo "  🔧 Key Commands: npm run [dev|build|test]"
            ;;
        identity)
            echo "  📁 Working Directory: $PROJECT_ROOT/services/identity-service"
            echo "  🔧 Key Commands: python main.py"
            ;;
        communication)
            echo "  📁 Working Directory: $PROJECT_ROOT/services/communication-service"
            ;;
        content)
            echo "  📁 Working Directory: $PROJECT_ROOT/services/content-service"
            ;;
        workflow)
            echo "  📁 Working Directory: $PROJECT_ROOT/services/workflow-intelligence-service"
            ;;
        infrastructure)
            echo "  📁 Working Directory: $PROJECT_ROOT/infrastructure"
            echo "  🔧 Key Commands: docker-compose, kubectl"
            ;;
        coordinator)
            echo "  📁 Working Directory: $PROJECT_ROOT/services"
            echo "  🔧 Focus: Service integration and API contracts"
            ;;
        security)
            echo "  📁 Working Directory: $PROJECT_ROOT"
            echo "  🔧 Focus: Security audits and compliance"
            ;;
        review)
            echo "  📁 Working Directory: $PROJECT_ROOT"
            echo "  🔧 Focus: Code quality and PR reviews"
            ;;
    esac
    echo ""
}

# Function to launch Claude Code
launch_claude_code() {
    local agent_name="$1"
    
    echo -e "${GREEN}🚀 Launching Claude Code...${NC}"
    echo -e "${YELLOW}💡 Agent Context: @$agent_name${NC}"
    echo ""
    
    # Try different Claude Code launch methods
    if command -v claude &> /dev/null; then
        echo "Starting Claude Code CLI..."
        exec claude
    elif command -v code &> /dev/null && [[ -f "$PROJECT_ROOT/.vscode/settings.json" ]]; then
        # If using VS Code with Claude extension
        echo "Opening VS Code with Claude integration..."
        exec code "$PROJECT_ROOT"
    else
        echo -e "${YELLOW}⚠️  Claude Code command not found${NC}"
        echo "Please launch Claude Code manually with the agent context: @$agent_name"
        echo ""
        echo "Session is active and ready for use!"
        
        # Keep session alive with a shell
        echo -e "${GREEN}Starting interactive shell for $agent_name agent...${NC}"
        export PS1="[$agent_name] \w $ "
        exec bash
    fi
}

# Main execution
main() {
    # Check if agent name is provided
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 0
    fi
    
    local agent_name="$1"
    
    # Validate agent name
    if [[ ! " $VALID_AGENTS " =~ " $agent_name " ]]; then
        echo -e "${RED}❌ Error: Unknown agent '$agent_name'${NC}"
        echo ""
        show_usage
        exit 1
    fi
    
    clear
    echo ""
    
    # Display agent instructions
    show_agent_instructions "$agent_name"
    
    # Activate the agent session
    activate_agent_session "$agent_name"
    
    # Show current status
    show_status
    
    # Launch Claude Code
    launch_claude_code "$agent_name"
}

# Run main function
main "$@"