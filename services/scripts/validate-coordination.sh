#!/bin/bash

# =============================================
# Services Coordination Validation Script
# =============================================
# This script validates that all services follow coordination standards
# Run from services/ directory: bash scripts/validate-coordination.sh

set -e

echo "🔍 Services Coordination Validation"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Issue tracking variables
CRITICAL_ISSUES=0
HIGH_ISSUES=0
MEDIUM_ISSUES=0
LOW_ISSUES=0
TOTAL_ISSUES=0

# Function to log issues to coordination file
log_issue() {
    local severity=$1
    local service=$2
    local title=$3
    local description=$4
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $severity in
        "CRITICAL") CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1)) ;;
        "HIGH") HIGH_ISSUES=$((HIGH_ISSUES + 1)) ;;
        "MEDIUM") MEDIUM_ISSUES=$((MEDIUM_ISSUES + 1)) ;;
        "LOW") LOW_ISSUES=$((LOW_ISSUES + 1)) ;;
    esac
    TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
    
    echo -e "${RED}❌ $severity ISSUE:${NC} $service - $title"
    echo "   Description: $description"
    echo "   Timestamp: $timestamp"
    echo ""
    
    # Append to issues file if in auto-report mode
    if [ "$AUTO_REPORT" = "true" ]; then
        cat >> COORDINATION_ISSUES.md << EOF

### 🔴 **NEW** - Issue #AUTO-$(date +%s): $title
**Date**: $(date '+%Y-%m-%d')  
**Reporter**: Coordination Validator (Automated)  
**Severity**: $severity  
**Service(s) Affected**: $service  
**Description**: $description  
**Status**: 🔴 **OPEN**

EOF
    fi
}

# Function to validate requirements format
validate_requirements() {
    local service_name=$1
    local req_file="$service_name/requirements.txt"
    
    echo "📦 Validating $service_name requirements..."
    
    if [ ! -f "$req_file" ]; then
        log_issue "HIGH" "$service_name" "Missing requirements.txt" "Service does not have a requirements.txt file"
        return 1
    fi
    
    # Check if using shared requirements pattern
    if ! head -n 5 "$req_file" | grep -q "^-r \.\./requirements\.shared\.txt"; then
        log_issue "HIGH" "$service_name" "Not using shared requirements" "Service does not reference ../requirements.shared.txt in first 5 lines"
        return 1
    fi
    
    # Check for duplicated dependencies
    shared_packages=$(grep -E "^[a-zA-Z].*==" requirements.shared.txt 2>/dev/null | cut -d'=' -f1 | tr '[:upper:]' '[:lower:]' || echo "")
    
    for package in $shared_packages; do
        if grep -i "^${package}==" "$req_file" > /dev/null 2>&1; then
            log_issue "HIGH" "$service_name" "Duplicated dependency: $package" "Service duplicates $package which is already in shared requirements"
        fi
    done
    
    echo -e "${GREEN}✅ $service_name requirements format OK${NC}"
    return 0
}

# Function to validate service structure
validate_service_structure() {
    local service_name=$1
    
    echo "🏗️  Validating $service_name structure..."
    
    local required_files=(
        "$service_name/main.py"
        "$service_name/Dockerfile"
        "$service_name/requirements.txt"
        "$service_name/.env.example"
    )
    
    local missing_files=()
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$(basename "$file")")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        log_issue "MEDIUM" "$service_name" "Missing required files" "Missing files: ${missing_files[*]}"
        return 1
    fi
    
    echo -e "${GREEN}✅ $service_name structure OK${NC}"
    return 0
}

# Function to validate Docker configuration
validate_docker_config() {
    local service_name=$1
    local dockerfile="$service_name/Dockerfile"
    
    echo "🐳 Validating $service_name Docker configuration..."
    
    if [ ! -f "$dockerfile" ]; then
        log_issue "MEDIUM" "$service_name" "Missing Dockerfile" "Service does not have a Dockerfile"
        return 1
    fi
    
    # Check for health check
    if ! grep -q "HEALTHCHECK" "$dockerfile"; then
        log_issue "LOW" "$service_name" "Missing health check in Dockerfile" "Dockerfile does not include HEALTHCHECK instruction"
    fi
    
    # Check for non-root user
    if ! grep -q "USER " "$dockerfile"; then
        log_issue "MEDIUM" "$service_name" "Running as root in Docker" "Dockerfile does not specify USER instruction for security"
    fi
    
    echo -e "${GREEN}✅ $service_name Docker configuration OK${NC}"
    return 0
}

# Function to validate environment configuration
validate_environment() {
    local service_name=$1
    local env_example="$service_name/.env.example"
    
    echo "🌍 Validating $service_name environment configuration..."
    
    if [ ! -f "$env_example" ]; then
        log_issue "HIGH" "$service_name" "Missing .env.example" "Service does not have .env.example file for environment variable documentation"
        return 1
    fi
    
    # Check for required environment variables
    local required_vars=(
        "SERVICE_NAME"
        "SERVICE_PORT"
        "DATABASE_URL"
        "REDIS_URL"
        "IDENTITY_SERVICE_URL"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$env_example"; then
            log_issue "MEDIUM" "$service_name" "Missing environment variable: $var" "$var is not documented in .env.example"
        fi
    done
    
    echo -e "${GREEN}✅ $service_name environment configuration OK${NC}"
    return 0
}

# Function to validate docker-compose integration
validate_docker_compose() {
    echo "🐳 Validating docker-compose.yml..."
    
    if [ ! -f "docker-compose.yml" ]; then
        log_issue "CRITICAL" "services-root" "Missing docker-compose.yml" "No docker-compose.yml file found in services root"
        return 1
    fi
    
    # Check for version specification
    if ! grep -q "^version:" docker-compose.yml; then
        log_issue "LOW" "services-root" "Missing version in docker-compose.yml" "docker-compose.yml does not specify version"
    fi
    
    # Check for network configuration
    if ! grep -q "networks:" docker-compose.yml; then
        log_issue "MEDIUM" "services-root" "No network configuration" "docker-compose.yml does not define custom networks"
    fi
    
    echo -e "${GREEN}✅ docker-compose.yml OK${NC}"
    return 0
}

# Function to check for shared requirements file
validate_shared_requirements() {
    echo "📋 Validating shared requirements..."
    
    if [ ! -f "requirements.shared.txt" ]; then
        log_issue "CRITICAL" "services-root" "Missing shared requirements" "requirements.shared.txt file not found"
        return 1
    fi
    
    # Check for required core dependencies
    local required_deps=(
        "fastapi"
        "uvicorn"
        "pydantic"
        "sqlalchemy"
        "redis"
        "httpx"
    )
    
    for dep in "${required_deps[@]}"; do
        # Handle both regular and extras syntax (e.g., uvicorn[standard]==)
        if ! grep -i "^${dep}\(\[\|==\)" requirements.shared.txt > /dev/null; then
            log_issue "HIGH" "services-root" "Missing core dependency: $dep" "$dep is not specified in shared requirements"
        fi
    done
    
    echo -e "${GREEN}✅ shared requirements OK${NC}"
    return 0
}

# Main execution
echo "🚀 Starting coordination validation..."
echo ""

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d ".claude" ]; then
    echo -e "${RED}❌ Error: Please run this script from the services/ directory${NC}"
    exit 1
fi

# Parse command line arguments
AUTO_REPORT=false
if [ "$1" = "--auto-report" ]; then
    AUTO_REPORT=true
    echo -e "${YELLOW}📝 Auto-reporting mode enabled - issues will be logged to COORDINATION_ISSUES.md${NC}"
    echo ""
fi

# Validate shared infrastructure
validate_shared_requirements
validate_docker_compose

# List of services to check
services=(
    "identity-service"
    "content-service"
    "communication-service"  
    "workflow-intelligence-service"
)

implemented_services=("identity-service")
planned_services=("content-service" "communication-service" "workflow-intelligence-service")

echo ""
echo "🔍 Validating implemented services..."
echo "===================================="

for service in "${implemented_services[@]}"; do
    if [ -d "$service" ]; then
        echo ""
        echo -e "${BLUE}🔍 Validating $service...${NC}"
        validate_requirements "$service"
        validate_service_structure "$service"
        validate_docker_config "$service"
        validate_environment "$service"
    else
        log_issue "CRITICAL" "$service" "Service directory missing" "Expected implemented service directory not found"
    fi
done

echo ""
echo "🔮 Checking planned services..."
echo "=============================="

for service in "${planned_services[@]}"; do
    if [ -d "$service" ]; then
        echo ""
        echo -e "${BLUE}🔍 Validating $service (planned)...${NC}"
        validate_requirements "$service"
        validate_service_structure "$service"
        validate_docker_config "$service"
        validate_environment "$service"
    else
        echo -e "${YELLOW}⚠️  $service: Not implemented yet (expected)${NC}"
    fi
done

# Summary
echo ""
echo "📊 Validation Summary"
echo "===================="

if [ $TOTAL_ISSUES -eq 0 ]; then
    echo -e "${GREEN}🎉 All coordination standards are being followed!${NC}"
    echo -e "${GREEN}✅ No issues found${NC}"
else
    echo -e "${RED}❌ Found $TOTAL_ISSUES coordination issues:${NC}"
    echo -e "   🔴 Critical: $CRITICAL_ISSUES"
    echo -e "   🟡 High: $HIGH_ISSUES"  
    echo -e "   🟠 Medium: $MEDIUM_ISSUES"
    echo -e "   ⚪ Low: $LOW_ISSUES"
    echo ""
    
    if [ $CRITICAL_ISSUES -gt 0 ]; then
        echo -e "${RED}🚨 CRITICAL ISSUES DETECTED - Immediate action required!${NC}"
        echo "   Services may not function properly until resolved."
    elif [ $HIGH_ISSUES -gt 0 ]; then
        echo -e "${YELLOW}⚠️  HIGH PRIORITY ISSUES - Should be resolved within 24h${NC}"
        echo "   These issues may cause problems during development or deployment."
    fi
fi

echo ""
echo "📋 Next Steps:"
echo "=============="
echo "1. Review issues listed above"
echo "2. Check COORDINATION_ISSUES.md for detailed issue tracking"
echo "3. Follow SERVICE_INTEGRATION_PATTERNS.md for standards"
echo "4. Run coordination validation after fixes: bash scripts/validate-coordination.sh"

if [ "$AUTO_REPORT" = "true" ] && [ $TOTAL_ISSUES -gt 0 ]; then
    echo ""
    echo -e "${BLUE}📝 Issues have been automatically logged to COORDINATION_ISSUES.md${NC}"
fi

echo ""
echo -e "${BLUE}🤖 Coordination validation complete!${NC}"

# Exit with appropriate code
if [ $CRITICAL_ISSUES -gt 0 ]; then
    exit 2  # Critical issues
elif [ $HIGH_ISSUES -gt 0 ]; then
    exit 1  # High priority issues  
else
    exit 0  # Success or only low/medium issues
fi