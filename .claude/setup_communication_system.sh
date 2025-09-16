#!/bin/bash

# =============================================================================
# AGENT COMMUNICATION SYSTEM SETUP
# =============================================================================
# This script initializes and configures the complete agent communication system
# Run this once to set up all components for agent coordination
#
# Usage: ./setup_communication_system.sh [--reset]
# =============================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Directories to create
DIRS=(
    ".claude/communication_hub"
    ".claude/shared_context"
    ".claude/logs"
    ".claude/docs"
    ".claude/scripts"
    ".claude/agents/configs"
    ".claude/agents/templates"
)

# Python dependencies
PYTHON_DEPS=(
    "pyyaml"
    "aiofiles"
    "asyncio"
)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

log_step() {
    echo -e "${BLUE}==>${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

show_header() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║         AGENT COMMUNICATION SYSTEM SETUP                     ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# =============================================================================
# SETUP FUNCTIONS
# =============================================================================

create_directories() {
    log_step "Creating directory structure..."
    
    for dir in "${DIRS[@]}"; do
        mkdir -p "$PROJECT_ROOT/$dir"
        log_success "Created $dir"
    done
}

check_python_dependencies() {
    log_step "Checking Python dependencies..."
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version | cut -d' ' -f2)
        log_success "Python $python_version found"
    else
        log_error "Python 3 is required but not found"
        exit 1
    fi
    
    # Check/Install Python packages
    for dep in "${PYTHON_DEPS[@]}"; do
        if python3 -c "import $dep" 2>/dev/null; then
            log_success "$dep is installed"
        else
            log_warning "$dep not found, installing..."
            pip3 install "$dep" || pip install "$dep"
        fi
    done
}

make_scripts_executable() {
    log_step "Making scripts executable..."
    
    chmod +x "$SCRIPT_DIR/agent_communication_hub.py" 2>/dev/null || true
    chmod +x "$SCRIPT_DIR/agent_coordinator.sh" 2>/dev/null || true
    chmod +x "$SCRIPT_DIR/agent_monitor_dashboard.py" 2>/dev/null || true
    chmod +x "$SCRIPT_DIR/agent_configurator.py" 2>/dev/null || true
    chmod +x "$SCRIPT_DIR/launch-agent.sh" 2>/dev/null || true
    chmod +x "$SCRIPT_DIR/scripts/auto-commit.sh" 2>/dev/null || true
    
    log_success "Scripts are now executable"
}

initialize_database() {
    log_step "Initializing communication hub database..."
    
    # Start hub briefly to create database
    timeout 2 python3 "$SCRIPT_DIR/agent_communication_hub.py" start 2>/dev/null || true
    
    if [[ -f "$SCRIPT_DIR/communication_hub/hub.db" ]]; then
        log_success "Database initialized"
    else
        log_warning "Database will be created on first run"
    fi
}

create_initial_configs() {
    log_step "Creating initial configurations..."
    
    # Create sample shared context
    cat > "$SCRIPT_DIR/shared_context/README.md" << 'EOF'
# Shared Context Directory

This directory contains shared context files that agents use to communicate state and information.

Files are automatically managed by the communication hub.
EOF
    
    # Create initial log file
    touch "$SCRIPT_DIR/logs/coordinator.log"
    touch "$SCRIPT_DIR/logs/commits.log"
    
    log_success "Initial configurations created"
}

setup_git_hooks() {
    log_step "Setting up git hooks for agent coordination..."
    
    # Create pre-commit hook for agent boundary checking
    cat > "$PROJECT_ROOT/.git/hooks/pre-commit" << 'EOF'
#!/bin/bash
# Agent boundary check pre-commit hook

# Get current agent from environment
AGENT=${CLAUDE_AGENT:-unknown}

if [[ "$AGENT" != "unknown" ]]; then
    echo "Checking agent boundaries for $AGENT..."
    
    # Run boundary check
    python3 .claude/agent_communication_hub.py check-boundaries "$AGENT"
    
    if [[ $? -ne 0 ]]; then
        echo "Boundary violation detected! Please review changes."
        exit 1
    fi
fi

exit 0
EOF
    
    chmod +x "$PROJECT_ROOT/.git/hooks/pre-commit" 2>/dev/null || true
    log_success "Git hooks configured"
}

create_shortcuts() {
    log_step "Creating command shortcuts..."
    
    # Create main command shortcuts
    cat > "$PROJECT_ROOT/agent" << 'EOF'
#!/bin/bash
# Quick agent launcher
exec .claude/launch-agent.sh "$@"
EOF
    
    cat > "$PROJECT_ROOT/coordinate" << 'EOF'
#!/bin/bash
# Quick coordinator access
exec .claude/agent_coordinator.sh "$@"
EOF
    
    cat > "$PROJECT_ROOT/monitor" << 'EOF'
#!/bin/bash
# Quick monitor dashboard
exec python3 .claude/agent_monitor_dashboard.py "$@"
EOF
    
    chmod +x "$PROJECT_ROOT/agent" 2>/dev/null || true
    chmod +x "$PROJECT_ROOT/coordinate" 2>/dev/null || true
    chmod +x "$PROJECT_ROOT/monitor" 2>/dev/null || true
    
    log_success "Command shortcuts created"
}

verify_installation() {
    log_step "Verifying installation..."
    
    errors=0
    
    # Check directories
    for dir in "${DIRS[@]}"; do
        if [[ ! -d "$PROJECT_ROOT/$dir" ]]; then
            log_error "Directory missing: $dir"
            ((errors++))
        fi
    done
    
    # Check scripts
    scripts=(
        "agent_communication_hub.py"
        "agent_coordinator.sh"
        "agent_monitor_dashboard.py"
    )
    
    for script in "${scripts[@]}"; do
        if [[ ! -f "$SCRIPT_DIR/$script" ]]; then
            log_error "Script missing: $script"
            ((errors++))
        elif [[ ! -x "$SCRIPT_DIR/$script" ]]; then
            log_warning "Script not executable: $script"
        fi
    done
    
    if [[ $errors -eq 0 ]]; then
        log_success "Installation verified successfully"
        return 0
    else
        log_error "Installation has $errors errors"
        return 1
    fi
}

show_usage_instructions() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         SETUP COMPLETE - QUICK START GUIDE                   ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Essential Commands:${NC}"
    echo ""
    echo -e "  ${YELLOW}Launch an agent:${NC}"
    echo "    ./agent backend              # Start backend agent"
    echo "    ./agent frontend             # Start frontend agent"
    echo ""
    echo -e "  ${YELLOW}Coordinate tasks:${NC}"
    echo "    ./coordinate delegate <task> <description>"
    echo "    ./coordinate feature <name> <description>"
    echo "    ./coordinate monitor         # View agent status"
    echo ""
    echo -e "  ${YELLOW}Monitor activity:${NC}"
    echo "    ./monitor                    # Real-time dashboard"
    echo ""
    echo -e "${CYAN}Full Commands:${NC}"
    echo ""
    echo -e "  ${YELLOW}Communication Hub:${NC}"
    echo "    python3 .claude/agent_communication_hub.py start"
    echo "    python3 .claude/agent_communication_hub.py status"
    echo "    python3 .claude/agent_communication_hub.py task <title>"
    echo ""
    echo -e "  ${YELLOW}Coordinator:${NC}"
    echo "    .claude/agent_coordinator.sh interactive"
    echo "    .claude/agent_coordinator.sh health"
    echo "    .claude/agent_coordinator.sh report"
    echo ""
    echo -e "  ${YELLOW}Auto-commit:${NC}"
    echo "    .claude/scripts/auto-commit.sh <agent> <type> <message>"
    echo ""
    echo -e "${CYAN}Example Workflows:${NC}"
    echo ""
    echo -e "  ${YELLOW}1. Feature Development:${NC}"
    echo "    ./coordinate feature \"user-auth\" \"Add user authentication\""
    echo ""
    echo -e "  ${YELLOW}2. Bug Fix:${NC}"
    echo "    ./coordinate bugfix \"BUG-123\" \"Fix login issue\" \"frontend\""
    echo ""
    echo -e "  ${YELLOW}3. Deployment:${NC}"
    echo "    ./coordinate deploy staging v1.2.3"
    echo ""
    echo -e "${CYAN}Documentation:${NC}"
    echo "    .claude/docs/AGENT_COMMUNICATION_PATTERNS.md"
    echo ""
    echo -e "${GREEN}System is ready! Start with: ./coordinate interactive${NC}"
    echo ""
}

reset_system() {
    log_warning "Resetting communication system..."
    
    # Remove database
    rm -f "$SCRIPT_DIR/communication_hub/hub.db"
    
    # Clear logs
    rm -f "$SCRIPT_DIR/logs/"*.log
    
    # Clear shared context
    rm -f "$SCRIPT_DIR/shared_context/"*.json
    
    log_success "System reset complete"
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    show_header
    
    # Check for reset flag
    if [[ "$1" == "--reset" ]]; then
        reset_system
    fi
    
    # Run setup steps
    create_directories
    check_python_dependencies
    make_scripts_executable
    initialize_database
    create_initial_configs
    setup_git_hooks
    create_shortcuts
    
    # Verify installation
    if verify_installation; then
        show_usage_instructions
    else
        echo ""
        log_error "Setup completed with errors. Please review and fix issues."
        exit 1
    fi
}

# Run main function
main "$@"