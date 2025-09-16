#!/bin/bash

# =============================================================================
# AGENT COORDINATOR - Central orchestration for Claude Code agents
# =============================================================================
# This script provides high-level coordination and task delegation for all agents
# It integrates with the communication hub for inter-agent messaging
#
# Usage: agent_coordinator.sh <command> [options]
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
HUB_DIR="$SCRIPT_DIR/communication_hub"
CONTEXT_DIR="$SCRIPT_DIR/shared_context"
LOG_DIR="$SCRIPT_DIR/logs"

# Ensure directories exist
mkdir -p "$HUB_DIR" "$CONTEXT_DIR" "$LOG_DIR"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${level}[COORDINATOR] ${message}${NC}"
    echo "[${timestamp}] [COORDINATOR] ${message}" >> "$LOG_DIR/coordinator.log"
}

show_header() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           AGENT COORDINATOR - Task Orchestration             ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# =============================================================================
# AGENT TASK DELEGATION
# =============================================================================

delegate_task() {
    local task_type=$1
    local description=$2
    local priority=${3:-normal}
    
    log_message "$BLUE" "Delegating task: $task_type"
    
    # Use Python hub for intelligent routing
    python3 "$SCRIPT_DIR/agent_communication_hub.py" task \
        "$task_type" \
        --description "$description" \
        --priority "$priority"
}

# =============================================================================
# WORKFLOW ORCHESTRATION
# =============================================================================

orchestrate_feature_development() {
    local feature_name=$1
    local feature_description=$2
    
    show_header
    log_message "$GREEN" "Starting feature development: $feature_name"
    echo ""
    
    # Create workflow tasks
    log_message "$BLUE" "Creating development workflow..."
    
    # 1. Architecture design
    delegate_task "architecture_decision" \
        "Design architecture for feature: $feature_description" \
        "high"
    
    # 2. Backend implementation
    delegate_task "django_model" \
        "Implement backend models and APIs for: $feature_description" \
        "high"
    
    # 3. Frontend implementation
    delegate_task "react_component" \
        "Create React components for: $feature_description" \
        "high"
    
    # 4. Integration testing
    delegate_task "api_integration" \
        "Test API integration for: $feature_description" \
        "normal"
    
    # 5. Security review
    delegate_task "security_audit" \
        "Security review for: $feature_description" \
        "high"
    
    # 6. Documentation
    delegate_task "documentation" \
        "Document feature: $feature_description" \
        "low"
    
    log_message "$GREEN" "Feature workflow initiated successfully"
}

orchestrate_bug_fix() {
    local bug_id=$1
    local bug_description=$2
    local affected_service=$3
    
    show_header
    log_message "$YELLOW" "Starting bug fix: $bug_id"
    echo ""
    
    # Route to appropriate agent based on affected service
    case "$affected_service" in
        backend)
            delegate_task "bug_fix" "Fix bug in Django backend: $bug_description" "critical"
            ;;
        frontend)
            delegate_task "bug_fix" "Fix bug in React frontend: $bug_description" "critical"
            ;;
        identity)
            delegate_task "bug_fix" "Fix bug in Identity service: $bug_description" "critical"
            ;;
        *)
            # Unknown service - route to coordinator for analysis
            delegate_task "bug_analysis" "Analyze and fix bug: $bug_description" "critical"
            ;;
    esac
    
    # Add testing task
    delegate_task "test_creation" "Create tests for bug fix: $bug_id" "high"
    
    log_message "$GREEN" "Bug fix workflow initiated"
}

orchestrate_deployment() {
    local environment=$1
    local version=$2
    
    show_header
    log_message "$MAGENTA" "Starting deployment to $environment"
    echo ""
    
    # Pre-deployment tasks
    log_message "$BLUE" "Running pre-deployment checks..."
    
    # 1. Run all tests
    delegate_task "test_all" "Run all tests before deployment" "critical"
    
    # 2. Security scan
    delegate_task "security_scan" "Security scan before deployment" "critical"
    
    # 3. Build artifacts
    delegate_task "build_artifacts" "Build deployment artifacts for $version" "high"
    
    # 4. Deploy
    delegate_task "deployment" "Deploy version $version to $environment" "critical"
    
    # 5. Post-deployment verification
    delegate_task "health_check" "Verify deployment health in $environment" "critical"
    
    log_message "$GREEN" "Deployment workflow initiated"
}

# =============================================================================
# AGENT STATUS MONITORING
# =============================================================================

monitor_agents() {
    show_header
    log_message "$BLUE" "Agent Status Monitor"
    echo ""
    
    # Get status from Python hub
    python3 "$SCRIPT_DIR/agent_communication_hub.py" status
    
    echo ""
    echo -e "${CYAN}Task Queue Status:${NC}"
    
    # Show task queue status
    if command -v sqlite3 &> /dev/null; then
        sqlite3 "$HUB_DIR/hub.db" "
            SELECT agent, status, COUNT(*) as count 
            FROM tasks 
            GROUP BY agent, status 
            ORDER BY agent, status;
        " | column -t -s '|'
    fi
}

# =============================================================================
# SHARED CONTEXT MANAGEMENT
# =============================================================================

share_context() {
    local key=$1
    local value=$2
    local agent=$3
    local ttl=${4:-3600}
    
    log_message "$BLUE" "Sharing context: $key"
    
    python3 "$SCRIPT_DIR/agent_communication_hub.py" context \
        "$key" "$value" \
        --agent "$agent" \
        --ttl "$ttl"
}

get_context() {
    local key=$1
    
    # Read from shared context directory
    local context_file="$CONTEXT_DIR/${key}.json"
    if [[ -f "$context_file" ]]; then
        cat "$context_file" | jq -r '.value'
    else
        echo "Context not found: $key" >&2
        return 1
    fi
}

# =============================================================================
# CONFLICT RESOLUTION
# =============================================================================

resolve_conflict() {
    local conflict_type=$1
    local resource=$2
    local agents=$3
    
    log_message "$YELLOW" "Resolving conflict: $conflict_type"
    
    case "$conflict_type" in
        file_conflict)
            log_message "$BLUE" "File conflict on $resource between $agents"
            log_message "$GREEN" "Resolution: Sequential access granted"
            ;;
        boundary_violation)
            log_message "$RED" "Boundary violation detected"
            log_message "$GREEN" "Resolution: Operation blocked, delegating to appropriate agent"
            ;;
        dependency_conflict)
            log_message "$YELLOW" "Dependency conflict detected"
            log_message "$GREEN" "Resolution: Waiting for dependency resolution"
            ;;
        *)
            log_message "$RED" "Unknown conflict type: $conflict_type"
            log_message "$YELLOW" "Resolution: Manual intervention required"
            ;;
    esac
}

# =============================================================================
# PROGRESS REPORTING
# =============================================================================

generate_progress_report() {
    show_header
    log_message "$BLUE" "Progress Report"
    echo ""
    
    # Get metrics from Python hub
    python3 "$SCRIPT_DIR/agent_communication_hub.py" metrics
    
    echo ""
    echo -e "${CYAN}Recent Activity:${NC}"
    
    # Show recent commits
    if command -v git &> /dev/null && git rev-parse --git-dir &> /dev/null; then
        echo -e "${GREEN}Recent Commits:${NC}"
        git log --oneline -5 --pretty=format:"  %h - %s (%cr)"
        echo ""
    fi
    
    # Show recent tasks
    if [[ -f "$LOG_DIR/coordinator.log" ]]; then
        echo -e "${GREEN}Recent Tasks:${NC}"
        tail -5 "$LOG_DIR/coordinator.log" | sed 's/^/  /'
    fi
}

# =============================================================================
# AGENT HEALTH CHECK
# =============================================================================

health_check() {
    show_header
    log_message "$BLUE" "Running health checks..."
    echo ""
    
    local all_healthy=true
    
    # Check each service
    services=("backend" "frontend" "identity" "communication" "content" "workflow")
    
    for service in "${services[@]}"; do
        echo -n "Checking $service... "
        
        case "$service" in
            backend)
                if curl -f -s "http://localhost:8000/health/" > /dev/null 2>&1; then
                    echo -e "${GREEN}✓ Healthy${NC}"
                else
                    echo -e "${RED}✗ Unhealthy${NC}"
                    all_healthy=false
                fi
                ;;
            frontend)
                if curl -f -s "http://localhost:3000/" > /dev/null 2>&1; then
                    echo -e "${GREEN}✓ Healthy${NC}"
                else
                    echo -e "${RED}✗ Unhealthy${NC}"
                    all_healthy=false
                fi
                ;;
            identity)
                if curl -f -s "http://localhost:8001/health" > /dev/null 2>&1; then
                    echo -e "${GREEN}✓ Healthy${NC}"
                else
                    echo -e "${RED}✗ Unhealthy${NC}"
                    all_healthy=false
                fi
                ;;
            *)
                echo -e "${YELLOW}⚠ Not implemented${NC}"
                ;;
        esac
    done
    
    echo ""
    if $all_healthy; then
        log_message "$GREEN" "All services healthy"
    else
        log_message "$YELLOW" "Some services need attention"
    fi
}

# =============================================================================
# BATCH OPERATIONS
# =============================================================================

batch_update_dependencies() {
    show_header
    log_message "$BLUE" "Updating all dependencies..."
    echo ""
    
    # Backend dependencies
    delegate_task "update_dependencies" "Update Python dependencies in backend" "normal"
    
    # Frontend dependencies
    delegate_task "update_dependencies" "Update npm dependencies in frontend" "normal"
    
    # Service dependencies
    for service in identity communication content workflow; do
        delegate_task "update_dependencies" \
            "Update dependencies in $service service" \
            "normal"
    done
    
    log_message "$GREEN" "Dependency update tasks queued"
}

batch_security_audit() {
    show_header
    log_message "$BLUE" "Running comprehensive security audit..."
    echo ""
    
    # Audit each component
    components=("backend" "frontend" "identity" "communication" "content" "workflow" "infrastructure")
    
    for component in "${components[@]}"; do
        delegate_task "security_audit" \
            "Security audit for $component" \
            "high"
    done
    
    log_message "$GREEN" "Security audit tasks initiated"
}

# =============================================================================
# INTERACTIVE MODE
# =============================================================================

interactive_mode() {
    show_header
    log_message "$GREEN" "Interactive Coordinator Mode"
    echo ""
    
    while true; do
        echo -e "${CYAN}Available Commands:${NC}"
        echo "  1) Delegate Task"
        echo "  2) Monitor Agents"
        echo "  3) Health Check"
        echo "  4) Progress Report"
        echo "  5) Share Context"
        echo "  6) Feature Development"
        echo "  7) Bug Fix"
        echo "  8) Deployment"
        echo "  9) Security Audit"
        echo "  0) Exit"
        echo ""
        
        read -p "Select command: " choice
        
        case $choice in
            1)
                read -p "Task type: " task_type
                read -p "Description: " description
                read -p "Priority (critical/high/normal/low): " priority
                delegate_task "$task_type" "$description" "$priority"
                ;;
            2)
                monitor_agents
                ;;
            3)
                health_check
                ;;
            4)
                generate_progress_report
                ;;
            5)
                read -p "Context key: " key
                read -p "Context value: " value
                read -p "Agent name: " agent
                share_context "$key" "$value" "$agent"
                ;;
            6)
                read -p "Feature name: " feature_name
                read -p "Feature description: " feature_desc
                orchestrate_feature_development "$feature_name" "$feature_desc"
                ;;
            7)
                read -p "Bug ID: " bug_id
                read -p "Bug description: " bug_desc
                read -p "Affected service: " service
                orchestrate_bug_fix "$bug_id" "$bug_desc" "$service"
                ;;
            8)
                read -p "Environment (dev/staging/prod): " env
                read -p "Version: " version
                orchestrate_deployment "$env" "$version"
                ;;
            9)
                batch_security_audit
                ;;
            0)
                echo "Exiting..."
                break
                ;;
            *)
                echo -e "${RED}Invalid choice${NC}"
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
        clear
        show_header
    done
}

# =============================================================================
# MAIN COMMAND HANDLER
# =============================================================================

show_usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  delegate <type> <description> [priority]  - Delegate a task to appropriate agent"
    echo "  monitor                                    - Monitor agent status"
    echo "  health                                     - Run health checks"
    echo "  report                                     - Generate progress report"
    echo "  context <key> <value> <agent>             - Share context between agents"
    echo "  feature <name> <description>               - Orchestrate feature development"
    echo "  bugfix <id> <description> <service>       - Orchestrate bug fix"
    echo "  deploy <environment> <version>            - Orchestrate deployment"
    echo "  update-deps                                - Update all dependencies"
    echo "  security-audit                             - Run security audit"
    echo "  interactive                                - Interactive mode"
    echo "  help                                       - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 delegate \"django_model\" \"Create user profile model\" high"
    echo "  $0 feature \"user-auth\" \"Implement user authentication\""
    echo "  $0 bugfix \"BUG-123\" \"Login fails with special characters\" frontend"
    echo "  $0 deploy staging v1.2.3"
}

# Main execution
main() {
    local command=${1:-help}
    
    case "$command" in
        delegate)
            delegate_task "$2" "$3" "${4:-normal}"
            ;;
        monitor)
            monitor_agents
            ;;
        health)
            health_check
            ;;
        report)
            generate_progress_report
            ;;
        context)
            share_context "$2" "$3" "$4" "${5:-3600}"
            ;;
        feature)
            orchestrate_feature_development "$2" "$3"
            ;;
        bugfix)
            orchestrate_bug_fix "$2" "$3" "$4"
            ;;
        deploy)
            orchestrate_deployment "$2" "$3"
            ;;
        update-deps)
            batch_update_dependencies
            ;;
        security-audit)
            batch_security_audit
            ;;
        interactive)
            interactive_mode
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"