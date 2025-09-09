# Services Coordination Issue Tracking

## 🎯 **Purpose**
This file tracks cross-service coordination issues that require Services Coordinator Agent attention. Service agents should report issues here when they encounter problems that affect multiple services or violate coordination standards.

---

## 📋 **Current Open Issues**

### ✅ **RESOLVED** - Issue #001: Requirements Management Pattern
**Date**: 2025-09-09  
**Reporter**: Services Coordinator (detected during identity-service requirements update)  
**Severity**: High  
**Description**: Identity service agent initially duplicated shared requirements instead of using `-r ../requirements.shared.txt` pattern  
**Impact**: Breaks centralized dependency management, causes version drift  
**Resolution**: Identity service corrected to use proper shared requirements pattern  
**Status**: ✅ **RESOLVED**

### ✅ **RESOLVED** - Issue #002: Database Driver Conflicts
**Date**: 2025-09-09  
**Reporter**: Identity Service Agent (via REQUIREMENTS_UPGRADE_REPORT.md)  
**Severity**: Critical  
**Description**: Shared requirements included conflicting database drivers (asyncpg + psycopg2-binary), causing compilation failures  
**Impact**: Blocks all service upgrades, identity service cannot install dependencies  
**Service(s) Affected**: identity-service, potentially all future services  
**Error Details**:
```
- psycopg2-binary fails with "pg_config executable not found"
- grpcio compilation failures on some systems
- Async/sync PostgreSQL driver conflicts
```
**Resolution**: 
- Removed database drivers from shared requirements
- Made database drivers service-specific (asyncpg for identity, psycopg2-binary for others)  
- Updated documentation with clear driver selection patterns
- Identity service now includes asyncpg==0.29.0 in service-specific dependencies
**Files Updated**:
- `requirements.shared.txt` - Removed conflicting database drivers
- `identity-service/requirements.txt` - Added asyncpg==0.29.0
- `docs/SERVICE_INTEGRATION_PATTERNS.md` - Added database driver patterns
- `README.md` - Updated requirements management documentation  
**Status**: ✅ **RESOLVED**

---

## 🚨 **Issue Reporting Format**

When reporting issues, service agents should use this format:

```markdown
### 🔴 **NEW** - Issue #XXX: [Title]
**Date**: YYYY-MM-DD  
**Reporter**: [Agent Name]  
**Severity**: Critical/High/Medium/Low  
**Description**: [What went wrong]  
**Impact**: [How it affects other services]  
**Service(s) Affected**: [List services]  
**Error Details**: 
```
[Error logs, stack traces, etc.]
```
**Attempted Solutions**: [What was tried]  
**Status**: 🔴 **OPEN** / 🟡 **IN PROGRESS** / ✅ **RESOLVED**
```

---

## 📊 **Issue Categories**

### 🔴 **Critical** (Immediate Action Required)
- Service cannot start due to coordination issue
- Authentication integration failures
- Database/Redis connection conflicts
- Security vulnerabilities

### 🟡 **High** (Fix Within 24h)
- Requirements/dependency conflicts
- Configuration inconsistencies  
- Performance degradation affecting multiple services
- Documentation gaps causing implementation errors

### 🟢 **Medium** (Fix Within Week)
- Non-breaking configuration improvements
- Documentation updates needed
- Development workflow inefficiencies

### ⚪ **Low** (Backlog)
- Code style inconsistencies
- Optimization opportunities
- Nice-to-have improvements

---

## 🔄 **Escalation Workflow**

### **Step 1: Self-Resolution Attempt**
- Service agent tries to resolve using existing documentation
- Check `docs/SERVICE_INTEGRATION_PATTERNS.md`
- Review `requirements.shared.txt` and coordination standards

### **Step 2: Report to Coordinator**
- Add issue to this file using the format above
- Include all relevant details and attempted solutions
- Set appropriate severity level

### **Step 3: Coordinator Response**
- Services Coordinator will respond within:
  - **Critical**: Within 1 hour
  - **High**: Within 4 hours  
  - **Medium**: Within 24 hours
  - **Low**: Within 1 week

### **Step 4: Resolution and Documentation**
- Coordinator provides solution and updates documentation
- Issue marked as resolved with solution details
- Prevention measures added to avoid similar issues

---

## 🛠️ **Common Issues and Quick Fixes**

### **Requirements Management**
```bash
# ❌ WRONG: Duplicating shared dependencies
fastapi==0.116.1
pydantic==2.11.7
# ... (duplicating everything)

# ✅ CORRECT: Using shared requirements
-r ../requirements.shared.txt
# Only service-specific dependencies below
aiosmtplib==3.0.1
```

### **Authentication Integration**
```python
# ❌ WRONG: Hardcoded endpoints
identity_url = "http://localhost:8001"

# ✅ CORRECT: Environment-based configuration
IDENTITY_SERVICE_URL = os.getenv("IDENTITY_SERVICE_URL", "http://identity-service:8001")
```

### **Database Configuration**
```python
# ❌ WRONG: Service-specific database naming
DATABASE_URL = "postgresql://user:pass@db:5432/myservice"

# ✅ CORRECT: Following naming convention
DATABASE_URL = "postgresql://content_user:content_pass@content-db:5432/content_service"
```

---

## 📈 **Issue Statistics**

| Month | Critical | High | Medium | Low | Total | Avg Resolution Time |
|-------|----------|------|--------|-----|-------|-------------------|
| Sep 2025 | 0 | 1 | 0 | 0 | 1 | 2 hours |

---

## 🔧 **Prevention Measures**

### **Automated Checks** (Planned)
- [ ] Pre-commit hooks to validate requirements format
- [ ] CI/CD checks for configuration consistency
- [ ] Automated service health monitoring
- [ ] Integration test validation

### **Documentation Improvements**
- [x] Service integration patterns documented
- [x] Requirements management strategy established
- [ ] Docker configuration templates
- [ ] Testing standards documentation

### **Agent Training**
- [x] Clear coordination patterns documented
- [ ] Common error scenarios and solutions
- [ ] Best practices checklist for each service type

---

## 📞 **Emergency Contact Protocol**

### **Critical Issues (Service Down)**
1. **Immediate**: Report in this file with 🚨 CRITICAL marker
2. **Fallback**: Update issue directly in relevant service documentation
3. **Recovery**: Follow disaster recovery procedures in `docs/DISASTER_RECOVERY.md` (TODO)

### **Non-Critical Issues**
1. Report using standard format above
2. Continue development while awaiting resolution
3. Document workarounds if found

---

**Maintained by**: Services Coordinator Agent  
**Last Updated**: 2025-09-09  
**Next Review**: Weekly on Mondays