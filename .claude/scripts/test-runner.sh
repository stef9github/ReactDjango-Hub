#!/bin/bash

# =============================================================================
# TEST RUNNER SCRIPT FOR CLAUDE CODE AGENTS
# =============================================================================
# This script runs tests specific to each agent before committing
#
# Usage: test-runner.sh <agent-name>
# Example: test-runner.sh backend
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
TEST_LOG="$PROJECT_ROOT/.claude/logs/tests.log"

# Ensure log directory exists
mkdir -p "$(dirname "$TEST_LOG")"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${level}[${timestamp}] ${message}${NC}"
    echo "[${timestamp}] [${level}] ${message}" >> "$TEST_LOG"
}

error_message() {
    log_message "$RED" "ERROR: $1"
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
# AGENT-SPECIFIC TEST RUNNERS
# =============================================================================

test_backend() {
    info_message "Running Django backend tests..."
    cd "$PROJECT_ROOT/backend"
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    # Run Django checks
    python manage.py check --deploy || return 1
    info_message "Django deployment checks passed"
    
    # Run migrations check
    python manage.py makemigrations --check --dry-run || {
        warning_message "Unmigrated changes detected"
    }
    
    # Run tests
    python manage.py test --parallel || return 1
    success_message "Django tests passed"
    
    # Run security checks if bandit is installed
    if command -v bandit &> /dev/null; then
        info_message "Running security scan..."
        bandit -r apps/ -ll || warning_message "Security warnings found"
    fi
    
    return 0
}

test_frontend() {
    info_message "Running React frontend tests..."
    cd "$PROJECT_ROOT/frontend"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        warning_message "node_modules not found, running npm install..."
        npm install
    fi
    
    # Run linting
    npm run lint || return 1
    info_message "Linting passed"
    
    # Run type checking
    npm run type-check || return 1
    info_message "Type checking passed"
    
    # Run tests if available
    if npm run | grep -q "test"; then
        npm run test -- --watchAll=false || return 1
        success_message "Frontend tests passed"
    else
        warning_message "No test script found in package.json"
    fi
    
    # Run build to ensure it compiles
    npm run build || return 1
    success_message "Frontend build successful"
    
    return 0
}

test_identity() {
    info_message "Running Identity service tests..."
    cd "$PROJECT_ROOT/services/identity-service"
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
    
    # Run pytest
    if [ -d "tests" ]; then
        pytest tests/ -v --tb=short || return 1
        success_message "Identity service tests passed"
    else
        warning_message "No tests directory found"
    fi
    
    # Check API health endpoint
    if pgrep -f "main.py" > /dev/null; then
        curl -f http://localhost:8001/health || warning_message "Health check failed"
    fi
    
    return 0
}

test_communication() {
    info_message "Running Communication service tests..."
    cd "$PROJECT_ROOT/services/communication-service"
    
    if [ -d "tests" ]; then
        pytest tests/ -v --tb=short || return 1
        success_message "Communication service tests passed"
    else
        warning_message "Communication service not yet implemented"
    fi
    
    return 0
}

test_content() {
    info_message "Running Content service tests..."
    cd "$PROJECT_ROOT/services/content-service"
    
    if [ -d "tests" ]; then
        pytest tests/ -v --tb=short || return 1
        success_message "Content service tests passed"
    else
        warning_message "Content service not yet implemented"
    fi
    
    return 0
}

test_workflow() {
    info_message "Running Workflow service tests..."
    cd "$PROJECT_ROOT/services/workflow-service"
    
    if [ -d "tests" ]; then
        pytest tests/ -v --tb=short || return 1
        success_message "Workflow service tests passed"
    else
        warning_message "Workflow service not yet implemented"
    fi
    
    return 0
}

test_infrastructure() {
    info_message "Validating infrastructure configurations..."
    cd "$PROJECT_ROOT"
    
    # Validate Docker Compose if exists
    if [ -f "docker-compose.yml" ]; then
        docker-compose config -q || return 1
        info_message "Docker Compose configuration valid"
    fi
    
    # Validate Kubernetes manifests if exist
    if [ -d "kubernetes" ]; then
        for manifest in kubernetes/*.yaml kubernetes/*.yml; do
            if [ -f "$manifest" ]; then
                kubectl --dry-run=client apply -f "$manifest" > /dev/null 2>&1 || {
                    warning_message "Invalid Kubernetes manifest: $manifest"
                }
            fi
        done
    fi
    
    # Validate GitHub Actions if exist
    if [ -d ".github/workflows" ]; then
        for workflow in .github/workflows/*.yml .github/workflows/*.yaml; do
            if [ -f "$workflow" ]; then
                # Basic YAML validation
                python -c "import yaml; yaml.safe_load(open('$workflow'))" || {
                    error_message "Invalid GitHub workflow: $workflow"
                    return 1
                }
            fi
        done
        info_message "GitHub workflows validated"
    fi
    
    success_message "Infrastructure validation passed"
    return 0
}

test_coordinator() {
    info_message "Running API Gateway/Coordinator tests..."
    cd "$PROJECT_ROOT"
    
    # Check Kong configuration if exists
    if [ -f "services/api-gateway/kong.yml" ]; then
        # Validate Kong configuration
        info_message "Kong configuration found"
    fi
    
    warning_message "Coordinator service tests not yet implemented"
    return 0
}

test_documentation() {
    info_message "Validating documentation..."
    cd "$PROJECT_ROOT"
    
    # Check for broken markdown links
    if command -v markdownlint &> /dev/null; then
        markdownlint docs/ --config .markdownlint.json || warning_message "Markdown issues found"
    fi
    
    # Validate README exists
    if [ ! -f "README.md" ]; then
        warning_message "README.md not found"
    fi
    
    success_message "Documentation validation complete"
    return 0
}

test_security() {
    info_message "Running security scans..."
    cd "$PROJECT_ROOT"
    
    # Run general security checks
    if command -v safety &> /dev/null; then
        safety check || warning_message "Vulnerable dependencies found"
    fi
    
    # Check for secrets
    if command -v gitleaks &> /dev/null; then
        gitleaks detect --no-git || {
            error_message "Potential secrets detected"
            return 1
        }
    fi
    
    success_message "Security checks complete"
    return 0
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    if [ $# -ne 1 ]; then
        echo "Usage: $0 <agent-name>"
        echo "Available agents: backend, frontend, identity, communication, content, workflow, infrastructure, coordinator, documentation, security"
        exit 1
    fi
    
    local agent=$1
    local test_result=0
    
    info_message "Starting tests for $agent agent..."
    
    case "$agent" in
        backend)
            test_backend || test_result=$?
            ;;
        frontend)
            test_frontend || test_result=$?
            ;;
        identity)
            test_identity || test_result=$?
            ;;
        communication)
            test_communication || test_result=$?
            ;;
        content)
            test_content || test_result=$?
            ;;
        workflow)
            test_workflow || test_result=$?
            ;;
        infrastructure)
            test_infrastructure || test_result=$?
            ;;
        coordinator)
            test_coordinator || test_result=$?
            ;;
        documentation)
            test_documentation || test_result=$?
            ;;
        security)
            test_security || test_result=$?
            ;;
        *)
            error_message "Unknown agent: $agent"
            exit 1
            ;;
    esac
    
    # Return to project root
    cd "$PROJECT_ROOT"
    
    if [ $test_result -eq 0 ]; then
        success_message "All tests passed for $agent agent"
    else
        error_message "Tests failed for $agent agent"
    fi
    
    exit $test_result
}

# Run main function
main "$@"