# Code Review Process Documentation

This document provides comprehensive guidance for the Code Reviewer agent when conducting systematic code reviews across all project verticals.

## Review Philosophy

Code reviews are not just about finding bugs - they are about:
- Ensuring maintainability and scalability
- Knowledge sharing across the team
- Maintaining consistent quality standards
- Preventing future issues through proactive identification
- Building a culture of continuous improvement

## Deterministic Review Process

### Phase 1: Pre-Review Setup (15 minutes)

#### 1.1 Create Review Workspace
```bash
# Generate unique review ID
REVIEW_ID="$(date +%Y-%m-%d)-${COMPONENT}-${FEATURE}"
mkdir -p /reviews/active/${REVIEW_ID}
cd /reviews/active/${REVIEW_ID}

# Initialize review structure
touch assessment.md findings.json metrics.json report.md
cp /reviews/templates/review-checklist.md ./checklist.md
```

#### 1.2 Gather Context
- Identify the pull request or commit range
- Review product requirements from relevant PM agent
- Check previous reviews for this component
- Note any specific compliance requirements

#### 1.3 Initial Assessment
Document in `assessment.md`:
```markdown
# Review Assessment: [REVIEW_ID]

## Scope
- Component: [component name]
- Feature: [feature description]
- Files affected: [count]
- Lines of code: [count]
- Review requestor: [name/agent]
- Priority: [Critical/High/Medium/Low]

## Context
- Related requirements: [PM requirements doc]
- Previous reviews: [links]
- Dependencies: [list]

## Review Focus Areas
- [ ] Security implications
- [ ] Performance impact
- [ ] Data handling
- [ ] API changes
- [ ] UI/UX changes
- [ ] Database migrations
```

### Phase 2: Automated Analysis (30 minutes)

#### 2.1 Static Code Analysis
```bash
# Backend (Python/Django)
pylint --output-format=json backend/ > static_analysis_backend.json
flake8 --format=json backend/ > flake8_backend.json
bandit -r backend/ -f json > security_backend.json

# Frontend (React/TypeScript)
npm run lint --format=json > static_analysis_frontend.json
npm audit --json > security_frontend.json

# Common
git secrets --scan > secrets_scan.txt
```

#### 2.2 Test Coverage Analysis
```bash
# Backend coverage
cd backend && coverage run --source='.' manage.py test
coverage report --format=json > ../coverage_backend.json

# Frontend coverage
cd frontend && npm test -- --coverage --json > ../coverage_frontend.json
```

#### 2.3 Dependency Analysis
```bash
# Check for vulnerabilities
pip-audit --format json > vulnerabilities_python.json
npm audit --json > vulnerabilities_npm.json

# Check for outdated packages
pip list --outdated --format json > outdated_python.json
npm outdated --json > outdated_npm.json
```

### Phase 3: Manual Code Inspection (60-120 minutes)

#### 3.1 Architecture Review Checklist

##### Separation of Concerns
- [ ] Business logic separated from presentation
- [ ] Data access layer properly abstracted
- [ ] No circular dependencies
- [ ] Clear module boundaries
- [ ] Proper use of design patterns

##### Code Organization
- [ ] Consistent file and folder structure
- [ ] Logical grouping of related functionality
- [ ] No god objects or mega-functions
- [ ] Proper use of inheritance vs composition
- [ ] Clear naming conventions followed

#### 3.2 Security Review Checklist

##### Authentication & Authorization
- [ ] All endpoints require appropriate authentication
- [ ] Role-based access control properly implemented
- [ ] Session management secure
- [ ] Token expiration and refresh handled
- [ ] No privilege escalation vulnerabilities

##### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] HTTPS enforced for data in transit
- [ ] PII properly handled and masked
- [ ] No sensitive data in logs
- [ ] Secure password storage (bcrypt/argon2)

##### Input Validation
- [ ] All user inputs validated and sanitized
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] CSRF tokens implemented
- [ ] File upload restrictions enforced

#### 3.3 Performance Review Checklist

##### Database Operations
- [ ] N+1 queries eliminated
- [ ] Proper indexing on frequently queried columns
- [ ] Pagination implemented for large datasets
- [ ] Database connection pooling configured
- [ ] Transactions used appropriately

##### Caching Strategy
- [ ] Appropriate caching layers implemented
- [ ] Cache invalidation strategy defined
- [ ] Static assets properly cached
- [ ] CDN utilization where appropriate
- [ ] Memory usage optimized

##### Frontend Performance
- [ ] Bundle size optimized
- [ ] Lazy loading implemented
- [ ] Images optimized and responsive
- [ ] Unnecessary re-renders prevented
- [ ] Web vitals metrics acceptable

#### 3.4 Code Quality Checklist

##### Maintainability
- [ ] Code is self-documenting
- [ ] Complex logic has explanatory comments
- [ ] No code duplication (DRY principle)
- [ ] Functions have single responsibility
- [ ] Cyclomatic complexity within limits (<10)

##### Error Handling
- [ ] All exceptions properly caught and handled
- [ ] Meaningful error messages provided
- [ ] Graceful degradation implemented
- [ ] Logging at appropriate levels
- [ ] No silent failures

##### Testing
- [ ] Unit tests for business logic
- [ ] Integration tests for APIs
- [ ] Edge cases covered
- [ ] Mocks used appropriately
- [ ] Test data properly managed

### Phase 4: Findings Documentation (30 minutes)

#### 4.1 Finding Structure
Document each finding in `findings.json`:
```json
{
  "findings": [
    {
      "id": "FIND-001",
      "severity": "Critical|High|Medium|Low",
      "category": "Security|Performance|Quality|Compliance",
      "file": "path/to/file.py",
      "line": 142,
      "description": "Clear description of the issue",
      "impact": "Potential impact if not addressed",
      "recommendation": "Specific fix recommendation",
      "code_snippet": "relevant code",
      "references": ["OWASP-A01", "CWE-79"]
    }
  ]
}
```

#### 4.2 Severity Classification

##### Critical (Must fix before merge)
- Security vulnerabilities with immediate risk
- Data loss or corruption possibilities
- System stability threats
- Legal/compliance violations
- Complete functionality breakdown

##### High (Should fix before deployment)
- Performance issues affecting user experience
- Missing critical error handling
- Significant technical debt
- Important missing tests
- Accessibility barriers

##### Medium (Fix in current sprint)
- Code quality issues affecting maintainability
- Minor performance optimizations needed
- Documentation gaps
- Non-critical missing tests
- Code style inconsistencies

##### Low (Fix when convenient)
- Nice-to-have improvements
- Minor refactoring opportunities
- Additional documentation
- Code formatting issues
- Optional optimizations

### Phase 5: Report Generation (30 minutes)

#### 5.1 Executive Summary Template
```markdown
# Code Review Report: [REVIEW_ID]

## Executive Summary
**Review Date**: [date]
**Reviewer**: Code Review Agent
**Status**: APPROVED | APPROVED_WITH_CONDITIONS | REQUIRES_CHANGES | REJECTED

### Overview
[Brief description of what was reviewed]

### Key Metrics
- Lines of Code Reviewed: [count]
- Files Reviewed: [count]
- Total Findings: [count]
  - Critical: [count]
  - High: [count]
  - Medium: [count]
  - Low: [count]

### Recommendation
[Clear pass/fail recommendation with reasoning]
```

#### 5.2 Detailed Findings Report
```markdown
## Detailed Findings

### Critical Issues
[List each critical finding with full details]

### High Priority Issues
[List each high priority finding with full details]

### Medium Priority Issues
[List each medium priority finding with full details]

### Low Priority Issues
[List each low priority finding with full details]

## Positive Observations
[Highlight good practices observed]

## Metrics Analysis
[Coverage reports, complexity metrics, etc.]
```

### Phase 6: Follow-up Process (Ongoing)

#### 6.1 Issue Tracking
- Create tracking entry for each finding
- Assign to appropriate developer/agent
- Set resolution deadline based on severity
- Monitor progress daily

#### 6.2 Re-review Process
Once fixes are submitted:
1. Verify each issue is addressed
2. Run automated checks again
3. Perform targeted manual review
4. Update finding status
5. Generate updated report

#### 6.3 Review Closure
```bash
# Archive completed review
REVIEW_ID="[review-id]"
YEAR=$(date +%Y)
MONTH=$(date +%m)

mkdir -p /reviews/completed/${YEAR}/${MONTH}
mv /reviews/active/${REVIEW_ID} /reviews/completed/${YEAR}/${MONTH}/

# Update metrics
./scripts/update-metrics.sh ${REVIEW_ID}
```

## Review Templates

### Security Checklist Template
Located at: `/reviews/templates/security-checklist.md`

### Performance Checklist Template
Located at: `/reviews/templates/performance-checklist.md`

### Compliance Checklist Template
Located at: `/reviews/templates/compliance-checklist.md`

### Quality Checklist Template
Located at: `/reviews/templates/quality-checklist.md`

## Metrics and Reporting

### Weekly Metrics Report
Generate every Monday:
```bash
./reviews/scripts/generate-weekly-report.sh
```

Includes:
- Number of reviews completed
- Average review time
- Finding distribution by severity
- Resolution time by severity
- Trending issues

### Monthly Dashboard
Generate on the 1st of each month:
```bash
./reviews/scripts/generate-monthly-dashboard.sh
```

Includes:
- Review velocity trends
- Quality metrics trends
- Common issue patterns
- Component heat map
- Developer/agent performance

## Integration Points

### With Product Manager Agents
- Pull requirements from: `/docs/product/requirements/`
- Validate against acceptance criteria
- Report compliance status

### With Development Agents
- Read code from service directories
- Provide feedback via review reports
- Track fix implementation

### With Infrastructure Agent
- Review deployment configurations
- Validate security settings
- Check scalability considerations

## Continuous Improvement

### Pattern Recognition
Track recurring issues and update:
- Review checklists
- Automated checks
- Developer guidelines
- Training materials

### Process Optimization
Monthly review of:
- Review cycle time
- False positive rate
- Issue detection rate
- Developer satisfaction

### Knowledge Base
Maintain and update:
- Common issue solutions
- Best practice examples
- Anti-pattern catalog
- Review case studies

## Emergency Review Process

For critical hotfixes or security patches:

1. **Rapid Assessment** (5 minutes)
   - Focus only on changed code
   - Check for obvious security issues
   - Verify basic functionality

2. **Targeted Analysis** (10 minutes)
   - Run security scanners on changes
   - Quick manual inspection
   - Document any concerns

3. **Conditional Approval**
   - Approve with follow-up requirements
   - Schedule full review post-deployment
   - Track technical debt created

## Review Agent Commands

### Start New Review
```bash
# Standard review
./reviews/scripts/start-review.sh --component backend --feature user-auth

# Emergency review
./reviews/scripts/start-review.sh --emergency --pr 123
```

### Generate Reports
```bash
# Individual review report
./reviews/scripts/generate-report.sh --review-id 2025-01-11-backend-auth

# Weekly summary
./reviews/scripts/generate-weekly-summary.sh

# Component analysis
./reviews/scripts/analyze-component.sh --component frontend
```

### Query Review Status
```bash
# Active reviews
./reviews/scripts/list-active.sh

# Pending fixes
./reviews/scripts/list-pending-fixes.sh

# Review history
./reviews/scripts/history.sh --component backend --days 30
```

## Quality Gates

### Automated Gates (Must Pass)
- [ ] No critical security vulnerabilities
- [ ] Test coverage >80%
- [ ] No failing tests
- [ ] No hardcoded secrets
- [ ] Build successful

### Manual Gates (Reviewer Discretion)
- [ ] Code maintainability acceptable
- [ ] Performance impact acceptable
- [ ] Documentation adequate
- [ ] Follows architectural patterns
- [ ] Technical debt justified

## Review Ethics

### Principles
1. **Constructive**: Focus on improvement, not criticism
2. **Objective**: Base feedback on standards, not opinions
3. **Educational**: Explain why, not just what
4. **Respectful**: Acknowledge good work alongside issues
5. **Actionable**: Provide specific, implementable solutions

### Communication Guidelines
- Use "Consider..." instead of "You should..."
- Explain the impact of issues
- Provide code examples for fixes
- Link to relevant documentation
- Acknowledge time constraints

Remember: The goal is to improve code quality while maintaining team velocity and morale.