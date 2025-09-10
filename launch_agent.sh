#!/bin/bash
# Master Launch Script for ReactDjango-Hub Agent System
# This script launches specialized Claude agents with proper configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art Header
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║     ReactDjango-Hub Medical - Agent Configuration System      ║
║                 Specialized Claude Agent Launcher             ║
╚═══════════════════════════════════════════════════════════════╝
EOF

# Function to display usage
usage() {
    echo ""
    echo -e "${YELLOW}Usage:${NC} $0 <agent-type> [options]"
    echo ""
    echo -e "${CYAN}Available Agent Types:${NC}"
    echo "  backend         - Django backend development specialist"
    echo "  frontend        - React frontend development specialist"
    echo "  identity        - Identity service specialist (auth, MFA, users)"
    echo "  content         - Content service specialist"
    echo "  communication   - Communication service specialist"
    echo "  workflow        - Workflow intelligence specialist"
    echo "  infrastructure  - Docker/Kubernetes/CI-CD specialist"
    echo "  testing         - Testing and QA specialist"
    echo "  security        - Security and compliance specialist"
    echo "  documentation   - Documentation specialist"
    echo "  claude-code-expert - Claude Code optimization and workflow specialist"
    echo ""
    echo -e "${CYAN}Options:${NC}"
    echo "  --setup-worktree    Setup git worktree for the agent"
    echo "  --generate-script   Generate individual launch script"
    echo "  --validate          Validate agent configuration"
    echo "  --list              List all available agents"
    echo "  --help              Show this help message"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  $0 backend                    # Launch backend agent"
    echo "  $0 frontend --setup-worktree  # Setup worktree and launch frontend agent"
    echo "  $0 --list                     # List all available agents"
    echo ""
}

# Function to check dependencies
check_dependencies() {
    echo -e "${BLUE}Checking dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is not installed${NC}"
        exit 1
    fi
    
    # Check PyYAML
    if ! python3 -c "import yaml" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  PyYAML not installed. Installing...${NC}"
        pip install pyyaml
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        echo -e "${RED}❌ Git is not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All dependencies satisfied${NC}"
}

# Function to launch agent
launch_agent() {
    local agent_type=$1
    
    echo ""
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🚀 Launching ${agent_type} agent...${NC}"
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    # Run the agent configurator from project root
    python3 .claude/agent_configurator.py launch "$agent_type"
    
    # Check if launch script was created
    LAUNCH_SCRIPT=".claude/agents/scripts/launch_${agent_type}.sh"
    if [ -f "$LAUNCH_SCRIPT" ]; then
        echo ""
        echo -e "${CYAN}Executing agent launch script...${NC}"
        echo ""
        bash "$LAUNCH_SCRIPT"
    else
        echo -e "${RED}❌ Failed to generate launch script${NC}"
        exit 1
    fi
}

# Function to setup worktree
setup_worktree() {
    local agent_type=$1
    
    echo -e "${BLUE}Setting up git worktree for ${agent_type} agent...${NC}"
    python3 .claude/agent_configurator.py worktree "$agent_type"
}

# Function to validate agent
validate_agent() {
    local agent_type=$1
    
    echo -e "${BLUE}Validating ${agent_type} agent configuration...${NC}"
    python3 .claude/agent_configurator.py validate "$agent_type"
}

# Function to list agents
list_agents() {
    echo ""
    echo -e "${CYAN}Available Specialized Agents:${NC}"
    echo ""
    python3 .claude/agent_configurator.py list
}

# Main script logic
main() {
    # Check if no arguments provided
    if [ $# -eq 0 ]; then
        usage
        exit 0
    fi
    
    # Parse arguments
    AGENT_TYPE=""
    SETUP_WORKTREE=false
    GENERATE_SCRIPT=false
    VALIDATE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                usage
                exit 0
                ;;
            --list)
                list_agents
                exit 0
                ;;
            --setup-worktree)
                SETUP_WORKTREE=true
                shift
                ;;
            --generate-script)
                GENERATE_SCRIPT=true
                shift
                ;;
            --validate)
                VALIDATE=true
                shift
                ;;
            backend|frontend|identity|content|communication|workflow|infrastructure|testing|security|documentation|claude-code-expert)
                AGENT_TYPE=$1
                shift
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                usage
                exit 1
                ;;
        esac
    done
    
    # Check if agent type is specified
    if [ -z "$AGENT_TYPE" ]; then
        echo -e "${RED}Error: No agent type specified${NC}"
        usage
        exit 1
    fi
    
    # Check dependencies
    check_dependencies
    
    # Validate if requested
    if [ "$VALIDATE" = true ]; then
        validate_agent "$AGENT_TYPE"
    fi
    
    # Setup worktree if requested
    if [ "$SETUP_WORKTREE" = true ]; then
        setup_worktree "$AGENT_TYPE"
    fi
    
    # Launch the agent
    launch_agent "$AGENT_TYPE"
    
    echo ""
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✨ Agent successfully configured and ready!${NC}"
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}Quick Commands:${NC}"
    echo "  • Access agents in Claude Code: /agents"
    echo "  • View agent config: cat .claude/agents/${AGENT_TYPE}.md"
    echo "  • Edit agent config: nano .claude/agents/${AGENT_TYPE}.md"
    echo "  • Re-launch agent:   ./launch_agent.sh ${AGENT_TYPE}"
    echo ""
    echo -e "${YELLOW}Note: Use '/agents' in Claude Code to access your specialized agents${NC}"
    echo ""
}

# Run main function
main "$@"