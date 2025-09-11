#!/bin/bash

# Start a new code review
# Usage: ./start-review.sh [component] [feature] [--emergency]

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
COMPONENT=$1
FEATURE=$2
EMERGENCY=false

if [[ "$3" == "--emergency" ]] || [[ "$1" == "--emergency" ]]; then
    EMERGENCY=true
fi

# Validate arguments
if [[ -z "$COMPONENT" ]] || [[ -z "$FEATURE" ]]; then
    echo -e "${RED}Error: Component and feature are required${NC}"
    echo "Usage: $0 [component] [feature] [--emergency]"
    echo "Example: $0 backend user-auth"
    exit 1
fi

# Generate review ID
REVIEW_ID="$(date +%Y-%m-%d)-${COMPONENT}-${FEATURE}"
REVIEW_DIR="/Users/stephanerichard/Documents/CODING/ReactDjango-Hub/reviews/active/${REVIEW_ID}"

# Check if review already exists
if [[ -d "$REVIEW_DIR" ]]; then
    echo -e "${YELLOW}Warning: Review ${REVIEW_ID} already exists${NC}"
    read -p "Do you want to overwrite? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    rm -rf "$REVIEW_DIR"
fi

# Create review directory
echo -e "${GREEN}Creating review workspace: ${REVIEW_ID}${NC}"
mkdir -p "$REVIEW_DIR"

# Initialize review files
cat > "$REVIEW_DIR/assessment.md" << EOF
# Review Assessment: ${REVIEW_ID}

**Date Created**: $(date +"%Y-%m-%d %H:%M:%S")
**Review Type**: $(if $EMERGENCY; then echo "EMERGENCY"; else echo "STANDARD"; fi)

## Scope
- Component: ${COMPONENT}
- Feature: ${FEATURE}
- Files affected: TBD
- Lines of code: TBD
- Review requestor: TBD
- Priority: $(if $EMERGENCY; then echo "CRITICAL"; else echo "NORMAL"; fi)

## Context
- Related requirements: TBD
- Previous reviews: None
- Dependencies: TBD

## Review Focus Areas
- [ ] Security implications
- [ ] Performance impact
- [ ] Data handling
- [ ] API changes
- [ ] UI/UX changes
- [ ] Database migrations
- [ ] Compliance requirements
- [ ] Test coverage

## Files to Review
\`\`\`
# List files here
\`\`\`

## Initial Notes
EOF

# Initialize findings file
cat > "$REVIEW_DIR/findings.json" << EOF
{
  "review_id": "${REVIEW_ID}",
  "created": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "component": "${COMPONENT}",
  "feature": "${FEATURE}",
  "emergency": ${EMERGENCY},
  "status": "in_progress",
  "findings": []
}
EOF

# Initialize metrics file
cat > "$REVIEW_DIR/metrics.json" << EOF
{
  "review_id": "${REVIEW_ID}",
  "metrics": {
    "files_reviewed": 0,
    "lines_reviewed": 0,
    "issues": {
      "critical": 0,
      "high": 0,
      "medium": 0,
      "low": 0
    },
    "coverage": {
      "before": 0,
      "after": 0
    },
    "complexity": {
      "cyclomatic": 0,
      "cognitive": 0
    }
  }
}
EOF

# Copy report template
cp /Users/stephanerichard/Documents/CODING/ReactDjango-Hub/reviews/templates/report-template.md "$REVIEW_DIR/report.md"

# Copy appropriate checklists
echo -e "${GREEN}Copying review checklists...${NC}"
cp /Users/stephanerichard/Documents/CODING/ReactDjango-Hub/reviews/templates/security-checklist.md "$REVIEW_DIR/"
cp /Users/stephanerichard/Documents/CODING/ReactDjango-Hub/reviews/templates/quality-checklist.md "$REVIEW_DIR/"

if [[ "$COMPONENT" == "backend" ]] || [[ "$COMPONENT" == "identity" ]]; then
    cp /Users/stephanerichard/Documents/CODING/ReactDjango-Hub/reviews/templates/performance-checklist.md "$REVIEW_DIR/"
fi

cp /Users/stephanerichard/Documents/CODING/ReactDjango-Hub/reviews/templates/compliance-checklist.md "$REVIEW_DIR/"

# Create review status file
cat > "$REVIEW_DIR/status.txt" << EOF
IN_PROGRESS
Started: $(date +"%Y-%m-%d %H:%M:%S")
EOF

echo -e "${GREEN}✅ Review workspace created successfully!${NC}"
echo
echo "Review ID: ${REVIEW_ID}"
echo "Location: ${REVIEW_DIR}"
echo
echo "Next steps:"
echo "1. Update assessment.md with specific scope"
echo "2. Run automated checks: ./run-checks.sh ${REVIEW_ID}"
echo "3. Perform manual review using checklists"
echo "4. Document findings in findings.json"
echo "5. Generate report: ./generate-report.sh ${REVIEW_ID}"

if $EMERGENCY; then
    echo
    echo -e "${YELLOW}⚠️  EMERGENCY REVIEW MODE${NC}"
    echo "Focus on critical security and functionality issues only"
    echo "Full review should be scheduled post-deployment"
fi