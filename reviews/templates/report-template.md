# Code Review Report

**Review ID**: [REVIEW_ID]  
**Date**: [DATE]  
**Reviewer**: Code Review Agent  
**Component**: [COMPONENT]  
**Feature**: [FEATURE]  

---

## Executive Summary

### Overall Assessment
**Status**: ⬜ APPROVED | ⬜ APPROVED_WITH_CONDITIONS | ⬜ REQUIRES_CHANGES | ⬜ REJECTED

### Summary
[Provide a 2-3 sentence summary of the review, highlighting the main findings and overall quality of the code]

### Key Metrics
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Files Reviewed | [X] | N/A | - |
| Lines of Code | [X] | N/A | - |
| Test Coverage | [X]% | >80% | ✅/❌ |
| Critical Issues | [X] | 0 | ✅/❌ |
| High Priority Issues | [X] | <3 | ✅/❌ |
| Security Vulnerabilities | [X] | 0 | ✅/❌ |
| Performance Issues | [X] | <2 | ✅/❌ |

### Risk Assessment
**Overall Risk Level**: ⬜ Low | ⬜ Medium | ⬜ High | ⬜ Critical

**Risk Factors**:
- [ ] Security vulnerabilities present
- [ ] Data integrity concerns
- [ ] Performance degradation likely
- [ ] Technical debt accumulation
- [ ] Compliance violations
- [ ] User experience impact

---

## Detailed Findings

### 🔴 Critical Issues (Must Fix)
*These issues must be resolved before the code can be merged*

#### Issue #1: [Issue Title]
- **File**: `path/to/file.ext` (Line: X)
- **Category**: Security/Data Loss/Compliance
- **Description**: [Detailed description of the issue]
- **Impact**: [Potential impact if not fixed]
- **Recommendation**: [Specific steps to fix]
- **Code Example**:
```[language]
// Current problematic code
[code snippet]

// Suggested fix
[code snippet]
```

### 🟠 High Priority Issues (Should Fix)
*These issues should be addressed before deployment*

#### Issue #2: [Issue Title]
- **File**: `path/to/file.ext` (Line: X)
- **Category**: Performance/Quality/Security
- **Description**: [Detailed description]
- **Impact**: [Potential impact]
- **Recommendation**: [Fix recommendation]

### 🟡 Medium Priority Issues (Consider Fixing)
*These issues should be addressed in the current sprint*

#### Issue #3: [Issue Title]
- **File**: `path/to/file.ext` (Line: X)
- **Category**: Maintainability/Documentation
- **Description**: [Description]
- **Recommendation**: [Suggestion]

### 🟢 Low Priority Issues (Nice to Have)
*These are suggestions for improvement*

#### Issue #4: [Issue Title]
- **File**: `path/to/file.ext` 
- **Category**: Style/Optimization
- **Suggestion**: [Improvement suggestion]

---

## Positive Observations

### What Was Done Well
- ✅ [Positive observation 1]
- ✅ [Positive observation 2]
- ✅ [Positive observation 3]

### Best Practices Followed
- [Best practice example with file reference]
- [Design pattern properly implemented]
- [Good test coverage in specific area]

---

## Compliance & Standards

### Security Compliance
| Check | Status | Notes |
|-------|--------|-------|
| Authentication | ✅/❌ | [Notes] |
| Authorization | ✅/❌ | [Notes] |
| Data Encryption | ✅/❌ | [Notes] |
| Input Validation | ✅/❌ | [Notes] |
| OWASP Top 10 | ✅/❌ | [Notes] |

### Code Standards
| Standard | Compliance | Notes |
|----------|------------|-------|
| Style Guide | [X]% | [Notes] |
| Documentation | [X]% | [Notes] |
| Test Coverage | [X]% | [Notes] |
| Complexity Limits | ✅/❌ | [Notes] |

### Regulatory Compliance
- [ ] GDPR Requirements Met
- [ ] HIPAA Requirements Met (if applicable)
- [ ] PCI DSS Requirements Met (if applicable)
- [ ] Accessibility Standards Met
- [ ] Industry Standards Followed

---

## Testing Analysis

### Test Coverage Summary
```
Component          | Coverage | Status
-------------------|----------|--------
Business Logic     | [X]%     | ✅/⚠️/❌
API Endpoints      | [X]%     | ✅/⚠️/❌
UI Components      | [X]%     | ✅/⚠️/❌
Integration Tests  | [X]%     | ✅/⚠️/❌
```

### Test Quality Assessment
- **Unit Tests**: [Assessment]
- **Integration Tests**: [Assessment]
- **E2E Tests**: [Assessment]
- **Performance Tests**: [Assessment]

### Missing Test Coverage
- [ ] [Area needing tests]
- [ ] [Critical path not tested]
- [ ] [Edge case not covered]

---

## Performance Analysis

### Performance Metrics
| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| API Response Time | [X]ms | <200ms | ✅/❌ |
| Database Queries | [X] | <10 | ✅/❌ |
| Bundle Size | [X]KB | <500KB | ✅/❌ |
| Memory Usage | [X]MB | <100MB | ✅/❌ |

### Performance Concerns
- [Performance issue identified]
- [Optimization opportunity]

---

## Recommendations

### Immediate Actions Required
1. **[Critical Fix]**: [Description and priority]
2. **[Security Patch]**: [Description and timeline]
3. **[Data Fix]**: [Description and impact]

### Short-term Improvements (This Sprint)
1. [Improvement item with justification]
2. [Refactoring suggestion]
3. [Documentation update needed]

### Long-term Considerations
1. [Architectural improvement]
2. [Technical debt to address]
3. [Future enhancement opportunity]

---

## Follow-up Items

### Action Items
| Item | Assignee | Priority | Due Date |
|------|----------|----------|----------|
| [Fix critical security issue] | [Developer] | Critical | [Date] |
| [Add missing tests] | [Developer] | High | [Date] |
| [Update documentation] | [Developer] | Medium | [Date] |

### Re-review Requirements
- [ ] All critical issues must be fixed
- [ ] Security vulnerabilities addressed
- [ ] Test coverage improved to >80%
- [ ] Documentation updated

### Next Steps
1. Developer addresses critical issues
2. Re-review scheduled for [Date]
3. Deployment approval pending fixes

---

## Appendix

### Files Reviewed
```
[List of all files reviewed with line counts]
path/to/file1.ext (250 lines)
path/to/file2.ext (180 lines)
...
```

### Tools & Automation Results
- **Static Analysis**: [Tool output summary]
- **Security Scan**: [Scanner results]
- **Dependency Check**: [Vulnerability summary]
- **Performance Profile**: [Key findings]

### References
- [Link to PR/MR]
- [Link to requirements]
- [Link to design docs]
- [Link to related reviews]

---

## Review Certification

By approving this review, I certify that:
- [ ] The code has been thoroughly reviewed
- [ ] All critical issues have been identified
- [ ] Security considerations have been evaluated
- [ ] Performance impact has been assessed
- [ ] Compliance requirements have been verified

**Reviewer Signature**: Code Review Agent  
**Date**: [DATE]  
**Review Duration**: [X] hours

---

*This report was generated using the standardized code review process. For questions or concerns, please contact the review team.*