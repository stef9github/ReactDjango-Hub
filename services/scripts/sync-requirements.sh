#!/bin/bash

# =============================================
# Services Requirements Synchronization Script
# =============================================
# This script helps maintain consistent dependencies across all services
# Run from services/ directory: bash scripts/sync-requirements.sh

set -e

echo "🔄 Services Requirements Synchronization"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a service exists
check_service_exists() {
    local service_name=$1
    if [ ! -d "$service_name" ]; then
        echo -e "${YELLOW}⚠️  Service directory '$service_name' not found - skipping${NC}"
        return 1
    fi
    return 0
}

# Function to check requirements format
check_requirements_format() {
    local service_name=$1
    local req_file="$service_name/requirements.txt"
    
    if [ ! -f "$req_file" ]; then
        echo -e "${RED}❌ $service_name: requirements.txt not found${NC}"
        return 1
    fi
    
    if ! grep -q "^-r \.\./requirements\.shared\.txt" "$req_file"; then
        echo -e "${YELLOW}⚠️  $service_name: Not using shared requirements${NC}"
        echo "   Add this line at the top of $req_file:"
        echo "   -r ../requirements.shared.txt"
        return 1
    fi
    
    echo -e "${GREEN}✅ $service_name: Using shared requirements${NC}"
    return 0
}

# Function to check for version conflicts
check_version_conflicts() {
    local service_name=$1
    local req_file="$service_name/requirements.txt"
    
    echo "🔍 Checking $service_name for version conflicts..."
    
    # Extract package names from shared requirements (excluding comments and options)
    shared_packages=$(grep -E "^[a-zA-Z].*==" requirements.shared.txt | cut -d'=' -f1 | tr '[:upper:]' '[:lower:]')
    
    conflicts=0
    for package in $shared_packages; do
        # Check if service overrides this package
        if grep -i "^${package}==" "$req_file" > /dev/null 2>&1; then
            local service_version=$(grep -i "^${package}==" "$req_file" | cut -d'=' -f3)
            local shared_version=$(grep -i "^${package}==" requirements.shared.txt | cut -d'=' -f3)
            
            if [ "$service_version" != "$shared_version" ]; then
                echo -e "${RED}❌ Version conflict: $package${NC}"
                echo "   Shared: $shared_version"
                echo "   $service_name: $service_version"
                conflicts=$((conflicts + 1))
            fi
        fi
    done
    
    if [ $conflicts -eq 0 ]; then
        echo -e "${GREEN}✅ No version conflicts found${NC}"
    else
        echo -e "${RED}❌ Found $conflicts version conflicts${NC}"
    fi
    
    return $conflicts
}

# Function to show outdated packages
show_outdated_info() {
    echo ""
    echo -e "${BLUE}📦 Dependency Analysis${NC}"
    echo "======================"
    
    if command -v pip &> /dev/null; then
        echo "🔍 To check for outdated packages:"
        echo "   cd identity-service && pip list --outdated"
        echo ""
        echo "📝 To update shared requirements:"
        echo "   1. Check latest versions: pip install --dry-run --upgrade package-name"
        echo "   2. Update requirements.shared.txt with new versions"
        echo "   3. Run this script again to verify consistency"
    else
        echo -e "${YELLOW}⚠️  pip not available - cannot check outdated packages${NC}"
    fi
}

# Main execution
echo "🏗️  Checking services architecture..."

# Check if we're in the right directory
if [ ! -f "requirements.shared.txt" ]; then
    echo -e "${RED}❌ Error: requirements.shared.txt not found${NC}"
    echo "   Please run this script from the services/ directory"
    exit 1
fi

echo -e "${GREEN}✅ Found shared requirements file${NC}"
echo ""

# List of services to check
services=("identity-service" "content-service" "communication-service" "workflow-intelligence-service")
implemented_services=("identity-service")
planned_services=("content-service" "communication-service" "workflow-intelligence-service")

echo "📋 Checking implemented services..."
echo "=================================="

total_conflicts=0
for service in "${implemented_services[@]}"; do
    if check_service_exists "$service"; then
        echo ""
        echo "🔍 Analyzing $service..."
        check_requirements_format "$service"
        check_version_conflicts "$service"
        total_conflicts=$((total_conflicts + $?))
        echo ""
    fi
done

echo "📋 Checking planned services..."
echo "==============================="

for service in "${planned_services[@]}"; do
    if check_service_exists "$service"; then
        echo ""
        echo "🔍 Analyzing $service..."
        if check_requirements_format "$service"; then
            check_version_conflicts "$service"
            total_conflicts=$((total_conflicts + $?))
        fi
        echo ""
    else
        echo -e "${BLUE}ℹ️  $service: Not implemented yet${NC}"
    fi
done

# Summary
echo ""
echo "📊 Summary"
echo "=========="

if [ $total_conflicts -eq 0 ]; then
    echo -e "${GREEN}✅ All services have consistent requirements${NC}"
else
    echo -e "${RED}❌ Found $total_conflicts total version conflicts${NC}"
    echo ""
    echo "🛠️  To fix conflicts:"
    echo "   1. Update service-specific requirements to match shared versions"
    echo "   2. OR update shared requirements if newer version is needed"
    echo "   3. Test all services after changes"
fi

show_outdated_info

echo ""
echo "🎯 Next Steps:"
echo "============="
echo "1. Review any conflicts shown above"
echo "2. Update requirements.shared.txt with latest stable versions" 
echo "3. Ensure all services use: -r ../requirements.shared.txt"
echo "4. Test services after dependency updates"
echo ""
echo -e "${BLUE}📖 Documentation: See README.md section 'Requirements Management'${NC}"