#!/bin/bash

# =============================================================================
# AUTO-COMMIT SCRIPT FOR CLAUDE CODE AGENTS
# =============================================================================
# This script provides automated git commit functionality for Claude agents
# with comprehensive safety checks and boundary enforcement.
#
# Usage: auto-commit.sh <agent-name> <commit-type> <commit-message> [--test-first]
# Example: auto-commit.sh backend feat "Add user authentication" --test-first
# =============================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
AGENT_CONFIG_DIR="$SCRIPT_DIR/../agents"
COMMIT_LOG="$PROJECT_ROOT/.claude/logs/commits.log"

# Ensure log directory exists
mkdir -p "$(dirname "$COMMIT_LOG")"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${level}[${timestamp}] ${message}${NC}"
    echo "[${timestamp}] [${level}] ${message}" >> "$COMMIT_LOG"
}

error_exit() {
    log_message "$RED" "ERROR: $1"
    exit 1
}

success_message() {
    log_message "$GREEN" "SUCCESS: $1"
}

warning_message() {
    log_message "$YELLOW" "WARNING: $1"
}

info_message() {
    log_message "$BLUE" "INFO: $1"
}

# =============================================================================
# AGENT BOUNDARY DEFINITIONS
# =============================================================================

get_agent_boundaries() {
    local agent=$1
    
    case "$agent" in
        backend)
            echo "backend/**"
            ;;
        frontend)
            echo "frontend/**"
            ;;
        identity)
            echo "services/identity-service/**"
            ;;
        communication)
            echo "services/communication-service/**"
            ;;
        content)
            echo "services/content-service/**"
            ;;
        workflow)
            echo "services/workflow-service/**"
            ;;
        infrastructure)
            echo "infrastructure/** docker/** .github/** kubernetes/**"
            ;;
        coordinator)
            echo "services/api-gateway/** services/service-mesh/**"
            ;;
        documentation)
            echo "docs/** *.md"
            ;;
        security)
            echo ".claude/security/** security-configs/**"
            ;;
        *)
            error_exit "Unknown agent: $agent"
            ;;
    esac
}

# =============================================================================
# TEST RUNNERS BY AGENT TYPE
# =============================================================================

run_agent_tests() {
    local agent=$1
    local test_result=0
    
    info_message "Running tests for $agent agent..."
    
    case "$agent" in
        backend)
            cd "$PROJECT_ROOT/backend"
            if [ -f "manage.py" ]; then
                python manage.py check --deploy || test_result=$?
                python manage.py test || test_result=$?
            fi
            ;;
            
        frontend)
            cd "$PROJECT_ROOT/frontend"
            if [ -f "package.json" ]; then
                npm run lint || test_result=$?
                npm run type-check || test_result=$?
                npm run test --if-present || test_result=$?
                npm run build || test_result=$?
            fi
            ;;
            
        identity)
            cd "$PROJECT_ROOT/services/identity-service"
            if [ -f "requirements.txt" ]; then
                pytest tests/ -v || test_result=$?
            fi
            ;;
            
        communication|content|workflow)
            local service_dir="$PROJECT_ROOT/services/${agent}-service"
            if [ -d "$service_dir" ]; then
                cd "$service_dir"
                if [ -f "requirements.txt" ]; then
                    pytest tests/ -v || test_result=$?
                fi
            fi
            ;;
            
        infrastructure)
            # Validate Docker and Kubernetes configs
            if command -v docker &> /dev/null; then
                docker-compose -f "$PROJECT_ROOT/docker-compose.yml" config -q || test_result=$?
            fi
            ;;
            
        *)
            warning_message "No specific tests defined for $agent agent"
            ;;
    esac
    
    cd "$PROJECT_ROOT"
    return $test_result
}

# =============================================================================
# FILE VALIDATION
# =============================================================================

validate_changed_files() {
    local agent=$1
    local boundaries=$(get_agent_boundaries "$agent")
    local invalid_files=""
    
    info_message "Validating file boundaries for $agent agent..."
    
    # Get list of changed files
    local changed_files=$(git diff --cached --name-only)
    
    if [ -z "$changed_files" ]; then
        warning_message "No staged files to commit"
        return 1
    fi
    
    # Check each changed file against agent boundaries
    for file in $changed_files; do
        local is_valid=false
        
        for boundary in $boundaries; do
            # Convert glob pattern to regex-like match
            if [[ "$file" == $boundary ]] || [[ "$file" == ${boundary%/\*\*}/* ]]; then
                is_valid=true
                break
            fi
        done
        
        if [ "$is_valid" = false ]; then
            invalid_files="$invalid_files\n  - $file"
        fi
    done
    
    if [ -n "$invalid_files" ]; then
        error_exit "Agent $agent tried to modify files outside its boundaries:$invalid_files"
    fi
    
    success_message "All files within agent boundaries"
    return 0
}

# =============================================================================
# SENSITIVE FILE CHECKS
# =============================================================================

check_sensitive_files() {
    local sensitive_patterns=(
        "*.key"
        "*.pem"
        "*.p12"
        ".env"
        ".env.*"
        "secrets.json"
        "credentials.json"
        "*_rsa"
        "*_dsa"
        "*_ecdsa"
        "*_ed25519"
    )
    
    info_message "Checking for sensitive files..."
    
    local staged_files=$(git diff --cached --name-only)
    
    for file in $staged_files; do
        for pattern in "${sensitive_patterns[@]}"; do
            if [[ "$file" == $pattern ]]; then
                error_exit "Attempting to commit sensitive file: $file"
            fi
        done
        
        # Check file content for secrets
        if [ -f "$file" ]; then
            if grep -qE "(api[_-]?key|secret[_-]?key|password|token|private[_-]?key)" "$file" 2>/dev/null; then
                warning_message "File $file may contain sensitive information - please review"
            fi
        fi
    done
    
    success_message "No sensitive files detected"
}

# =============================================================================
# COMMIT MESSAGE FORMATTING
# =============================================================================

format_commit_message() {
    local agent=$1
    local commit_type=$2
    local message=$3
    
    # Add agent context to commit message
    local formatted_message="${commit_type}(${agent}): ${message}"
    
    # Add metadata footer
    formatted_message="${formatted_message}

Agent: ${agent}
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
Auto-commit: true"
    
    # Add Claude Code attribution if not already present
    if [[ ! "$formatted_message" == *"Claude Code"* ]]; then
        formatted_message="${formatted_message}

Generated with Claude Code (https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>"
    fi
    
    echo "$formatted_message"
}

# =============================================================================
# MAIN COMMIT WORKFLOW
# =============================================================================

perform_commit() {
    local agent=$1
    local commit_type=$2
    local message=$3
    local test_first=$4
    
    info_message "Starting auto-commit for $agent agent..."
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        error_exit "Not in a git repository"
    fi
    
    # Check for uncommitted changes
    if [ -z "$(git status --porcelain)" ]; then
        warning_message "No changes to commit"
        return 0
    fi
    
    # Stage changes for the agent's allowed paths
    local boundaries=$(get_agent_boundaries "$agent")
    for boundary in $boundaries; do
        # Remove the /** suffix for git add
        local path=${boundary%/\*\*}
        if [ -d "$PROJECT_ROOT/$path" ] || [ -f "$PROJECT_ROOT/$path" ]; then
            git add "$path" 2>/dev/null || true
        fi
    done
    
    # Validate changed files are within boundaries
    validate_changed_files "$agent"
    
    # Check for sensitive files
    check_sensitive_files
    
    # Run tests if requested
    if [ "$test_first" = "--test-first" ]; then
        if ! run_agent_tests "$agent"; then
            error_exit "Tests failed - commit aborted"
        fi
        success_message "All tests passed"
    fi
    
    # Format commit message
    local formatted_message=$(format_commit_message "$agent" "$commit_type" "$message")
    
    # Perform the commit
    if git commit -m "$formatted_message"; then
        success_message "Commit successful!"
        
        # Log the commit
        local commit_hash=$(git rev-parse HEAD)
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Agent: $agent, Commit: $commit_hash, Message: $message" >> "$COMMIT_LOG"
        
        # Show commit details
        info_message "Commit details:"
        git show --stat HEAD
    else
        error_exit "Commit failed"
    fi
}

# =============================================================================
# MAIN SCRIPT EXECUTION
# =============================================================================

main() {
    # Check arguments
    if [ $# -lt 3 ]; then
        echo "Usage: $0 <agent-name> <commit-type> <commit-message> [--test-first]"
        echo ""
        echo "Agent names: backend, frontend, identity, communication, content, workflow, infrastructure, coordinator, documentation, security"
        echo "Commit types: feat, fix, docs, style, refactor, test, chore"
        echo ""
        echo "Example: $0 backend feat \"Add user authentication\" --test-first"
        exit 1
    fi
    
    local agent=$1
    local commit_type=$2
    local message=$3
    local test_first=${4:-""}
    
    # Validate commit type
    case "$commit_type" in
        feat|fix|docs|style|refactor|test|chore)
            ;;
        *)
            error_exit "Invalid commit type: $commit_type. Use: feat, fix, docs, style, refactor, test, chore"
            ;;
    esac
    
    # Perform the commit
    perform_commit "$agent" "$commit_type" "$message" "$test_first"
}

# Run main function
main "$@"