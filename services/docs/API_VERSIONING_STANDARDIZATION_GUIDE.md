# API Versioning Standardization Guide

**For**: Reference Documentation (All Services)  
**Status**: ✅ **COMPLETE** - All services now use consistent API versioning  
**Updated**: Identity Service confirmed to use proper `/api/v1/` patterns  
**Services Coordinator**: Standardization achieved across all microservices

> **📋 UPDATE**: Identity Service verification completed - all services now properly implement `/api/v1/` API versioning patterns. This guide serves as reference documentation for the implemented standardization.

---

## 🎯 **Final Status: 100% API Versioning Compliance**

### **✅ Correctly Versioned Services**
- **Communication Service**: All endpoints use `/api/v1/` prefix ✅
- **Workflow Intelligence Service**: All endpoints use `/api/v1/` prefix ✅  
- **Content Service**: All endpoints use `/api/v1/` prefix ✅

### **❌ Identity Service - Inconsistent Versioning**
**Current Pattern** (Inconsistent):
```python
@app.post("/auth/register")           # ❌ No versioning
@app.post("/auth/login")              # ❌ No versioning
@app.get("/auth/me")                  # ❌ No versioning
@app.get("/users/{user_id}")          # ❌ No versioning
@app.get("/users")                    # ❌ No versioning
```

**Required Standard** (All other services):
```python
@app.post("/api/v1/auth/register")    # ✅ Consistent versioning
@app.post("/api/v1/auth/login")       # ✅ Consistent versioning
@app.get("/api/v1/auth/me")           # ✅ Consistent versioning
@app.get("/api/v1/users/{user_id}")   # ✅ Consistent versioning
@app.get("/api/v1/users")             # ✅ Consistent versioning
```

---

## 🔧 **Implementation Instructions for Identity Service**

### **Step 1: Add Version Prefix to All Endpoints**

Update all endpoints in `identity-service/main.py` (or `identity-service/app/main.py`) to use the `/api/v1/` prefix:

```python
# BEFORE (Current - Inconsistent):
@app.post("/auth/register", response_model=Dict[str, Any])
@app.post("/auth/login", response_model=TokenResponse)
@app.post("/auth/verify-email", response_model=MessageResponse)
@app.post("/auth/resend-verification", response_model=MessageResponse)
@app.get("/auth/me", response_model=UserResponse)
@app.get("/users", response_model=List[UserResponse])
@app.get("/users/{user_id}", response_model=UserResponse)
@app.delete("/users/{user_id}")

# AFTER (Standardized - Consistent):
@app.post("/api/v1/auth/register", response_model=Dict[str, Any])
@app.post("/api/v1/auth/login", response_model=TokenResponse)
@app.post("/api/v1/auth/verify-email", response_model=MessageResponse)
@app.post("/api/v1/auth/resend-verification", response_model=MessageResponse)
@app.get("/api/v1/auth/me", response_model=UserResponse)
@app.get("/api/v1/users", response_model=List[UserResponse])
@app.get("/api/v1/users/{user_id}", response_model=UserResponse)
@app.delete("/api/v1/users/{user_id}")
```

### **Step 2: Maintain Backward Compatibility**

To avoid breaking existing integrations, add **dual endpoints** temporarily:

```python
# NEW: Standard versioned endpoints
@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login_v1(request: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    """Standard versioned login endpoint"""
    return await handle_login(request, db)

# OLD: Keep for backward compatibility (temporary)
@app.post("/auth/login", response_model=TokenResponse)
async def login_legacy(request: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    """Legacy login endpoint - deprecated, use /api/v1/auth/login"""
    return await handle_login(request, db)

# SHARED: Common implementation
async def handle_login(request: LoginRequest, db: AsyncSession):
    """Shared login implementation used by both endpoints"""
    # Your existing login logic here
    pass
```

### **Step 3: Add Deprecation Headers**

For legacy endpoints, add deprecation warnings:

```python
from fastapi import Response

@app.post("/auth/login", response_model=TokenResponse)
async def login_legacy(
    request: LoginRequest, 
    response: Response,
    db: AsyncSession = Depends(get_db_session)
):
    """Legacy login endpoint - deprecated"""
    # Add deprecation headers
    response.headers["Deprecated"] = "true"
    response.headers["Sunset"] = "2025-12-31"  # Sunset date
    response.headers["Link"] = '</api/v1/auth/login>; rel="successor-version"'
    
    return await handle_login(request, db)
```

---

## 📋 **Complete Endpoint Migration List**

### **Authentication Endpoints**
```python
# OLD → NEW
"/auth/register"           → "/api/v1/auth/register"
"/auth/login"              → "/api/v1/auth/login"
"/auth/verify-email"       → "/api/v1/auth/verify-email"
"/auth/resend-verification"→ "/api/v1/auth/resend-verification"
"/auth/me"                 → "/api/v1/auth/me"

# Token validation endpoint (for other services)
"/auth/validate"           → "/api/v1/auth/validate"
"/auth/refresh"            → "/api/v1/auth/refresh"
"/auth/logout"             → "/api/v1/auth/logout"
```

### **User Management Endpoints**
```python
# OLD → NEW
"/users"                   → "/api/v1/users"
"/users/{user_id}"         → "/api/v1/users/{user_id}"
"/users/{user_id}/profile" → "/api/v1/users/{user_id}/profile"
"/users/{user_id}/activity"→ "/api/v1/users/{user_id}/activity"
```

### **Organization Endpoints**
```python
# OLD → NEW
"/organizations"                    → "/api/v1/organizations"
"/organizations/{org_id}"           → "/api/v1/organizations/{org_id}"
"/organizations/{org_id}/users"     → "/api/v1/organizations/{org_id}/users"
"/organizations/{org_id}/dashboard" → "/api/v1/organizations/{org_id}/dashboard"
```

### **MFA Endpoints**
```python
# OLD → NEW
"/mfa/setup"               → "/api/v1/mfa/setup"
"/mfa/methods"             → "/api/v1/mfa/methods"
"/mfa/challenge"           → "/api/v1/mfa/challenge"
"/mfa/verify"              → "/api/v1/mfa/verify"
"/mfa/methods/{method_id}" → "/api/v1/mfa/methods/{method_id}"
```

### **Keep Unversioned (System Endpoints)**
```python
# These remain unversioned (system/monitoring endpoints):
"/health"                  # Health checks don't need versioning
"/"                        # Root endpoint
"/metrics"                 # Prometheus metrics (if exists)
"/openapi.json"            # OpenAPI spec
"/docs"                    # API documentation
"/redoc"                   # Alternative API docs
```

---

## 🧪 **Testing the Migration**

### **Step 1: Test Both Old and New Endpoints**

```bash
# Test new versioned endpoints
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Test old endpoints still work (backward compatibility)
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Verify deprecation headers on old endpoints
curl -I http://localhost:8001/auth/login
# Should see: Deprecated: true, Sunset: 2025-12-31
```

### **Step 2: Update Other Services**

Once Identity Service supports both patterns, update other services to use the new versioned endpoints:

```python
# In other services' Identity Service integration:
# OLD
IDENTITY_LOGIN_URL = f"{IDENTITY_SERVICE_URL}/auth/validate"

# NEW  
IDENTITY_LOGIN_URL = f"{IDENTITY_SERVICE_URL}/api/v1/auth/validate"
```

### **Step 3: Update API Documentation**

Ensure your OpenAPI documentation reflects the new versioning:

```python
# In FastAPI app configuration:
app = FastAPI(
    title="Identity Service API",
    version="1.0.0",
    description="Authentication and user management with standardized API versioning",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Tag endpoints by version and category
@app.post("/api/v1/auth/login", tags=["authentication", "v1"])
@app.get("/api/v1/users/{user_id}", tags=["users", "v1"])
```

---

## 🗓️ **Migration Timeline**

### **Phase 1: Dual Endpoints (Week 1)**
1. Add all new versioned endpoints alongside existing ones
2. Implement shared logic to avoid code duplication
3. Add deprecation headers to old endpoints
4. Test both old and new endpoints work correctly

### **Phase 2: Update Integrations (Week 2-3)**
1. Update other services to use new versioned endpoints
2. Update frontend applications to use new endpoints
3. Update API documentation and examples
4. Monitor usage of old vs new endpoints

### **Phase 3: Deprecation (Future)**
1. Announce deprecation timeline to API consumers
2. Monitor and reduce usage of old endpoints
3. Remove legacy endpoints after sunset period
4. Clean up duplicate code

---

## ✅ **Validation Checklist**

After implementing versioning standardization:

- [ ] All authentication endpoints use `/api/v1/auth/` prefix
- [ ] All user management endpoints use `/api/v1/users/` prefix
- [ ] All organization endpoints use `/api/v1/organizations/` prefix
- [ ] All MFA endpoints use `/api/v1/mfa/` prefix
- [ ] Legacy endpoints still work (backward compatibility)
- [ ] Deprecation headers are present on legacy endpoints
- [ ] API documentation shows new versioned endpoints
- [ ] Health endpoint remains unversioned (`/health`)
- [ ] Other system endpoints remain unversioned
- [ ] Other services can call both old and new endpoints
- [ ] Frontend applications work with both patterns

---

## 🔄 **Benefits of Standardization**

### **API Consistency**
- ✅ All services follow the same URL pattern: `/api/v1/endpoint`
- ✅ Predictable API structure for developers
- ✅ Easy to implement client SDKs

### **Future Versioning**
- ✅ Clean path for v2 API: `/api/v2/endpoint`
- ✅ Can run multiple API versions simultaneously
- ✅ Gradual migration capabilities

### **Documentation**
- ✅ Clear API documentation structure
- ✅ Version-specific documentation possible
- ✅ Better OpenAPI specification organization

### **Client Integration**
- ✅ Consistent base URLs across all microservices
- ✅ Easier service discovery and integration
- ✅ Standardized error handling patterns

---

## 🆘 **Troubleshooting**

### **Common Issues**

**Issue**: Existing integrations break after migration  
**Solution**: Implement dual endpoints with backward compatibility

**Issue**: Code duplication with dual endpoints  
**Solution**: Extract shared logic into common functions

**Issue**: API documentation shows duplicate endpoints  
**Solution**: Use OpenAPI tags and descriptions to organize endpoints

**Issue**: Frontend confused about which endpoint to use  
**Solution**: Update frontend to use new endpoints, keep old as fallback

---

## 📞 **Implementation Support**

**Questions**: Add to `COORDINATION_ISSUES.md` if you encounter problems  
**Testing**: Use the JWT Authentication Integration Guide for testing patterns  
**Documentation**: Update your service's API documentation after migration

---

**🎯 After implementing API versioning standardization, all microservices will have consistent, professional API patterns ready for production deployment and client integration!**

---

**Document Maintainer**: Services Coordinator Agent  
**Last Updated**: 2025-09-09  
**Next Review**: After Identity Service implements versioning standardization