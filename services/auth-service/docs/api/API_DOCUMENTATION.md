# Auth Service API Documentation

## 🎯 **Complete API Reference**

This document provides comprehensive documentation for all 30 production-ready endpoints in the Auth Service.

## 📋 **Table of Contents**

1. [Core Authentication](#core-authentication-7-endpoints)
2. [Enhanced Authentication](#enhanced-authentication-7-endpoints)
3. [User Management](#user-management-4-endpoints)
4. [Organization Management](#organization-management-4-endpoints)
5. [Multi-Factor Authentication](#multi-factor-authentication-6-endpoints)
6. [Monitoring & Health](#monitoring--health-2-endpoints)
7. [Authentication & Authorization](#authentication--authorization)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)

---

## **Core Authentication (7 endpoints)**

### `POST /auth/login`
**Enhanced login with MFA support**

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "tenant_id": "org-123",
  "mfa_code": "123456"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "refresh_token_here",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user_id": "user-uuid",
  "tenant_id": "org-123"
}
```

### `POST /auth/register`
**User registration with enhanced profiles**

```http
POST /auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "tenant_id": "org-123"
}
```

### `POST /auth/refresh`
**Token refresh mechanism**

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "refresh_token_here"
}
```

### `POST /auth/logout`
**Enhanced logout with activity logging**

```http
POST /auth/logout
Authorization: Bearer {access_token}
```

### `POST /auth/validate`
**Token validation for other services**

```http
POST /auth/validate
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "valid": true,
  "user_id": "user-uuid",
  "email": "user@example.com",
  "tenant_id": "org-123",
  "roles": ["user", "admin"],
  "permissions": ["read:profile", "write:profile"],
  "expires_at": 1704067200
}
```

### `POST /auth/authorize`
**Permission checking for resources**

```http
POST /auth/authorize
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "resource": "user_profile",
  "action": "read",
  "context": {"tenant_id": "org-123"}
}
```

### `GET /auth/permissions/{user_id}`
**Get user permissions for caching**

```http
GET /auth/permissions/user-uuid
Authorization: Bearer {access_token}
```

---

## **Enhanced Authentication (7 endpoints)**

### `GET /auth/me`
**Get current user with complete data**

```http
GET /auth/me
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "user_id": "user-uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "first_name": "John",
  "last_name": "Doe",
  "display_name": "John Doe",
  "phone_number": "+1234567890",
  "job_title": "Software Engineer",
  "department": "Engineering",
  "bio": "Passionate about building great products",
  "skills": ["Python", "FastAPI", "React"],
  "interests": ["Technology", "Music"],
  "status": "active",
  "preferences": {
    "theme": "dark",
    "language": "en",
    "timezone": "UTC"
  },
  "mfa_enabled": true,
  "mfa_methods_count": 2,
  "last_login_at": "2024-01-01T12:00:00Z",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### `GET /auth/sessions`
**List user's active sessions**

```http
GET /auth/sessions
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "session-uuid",
      "device_info": "Chrome on macOS",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "location": "San Francisco, CA",
      "is_current": true,
      "created_at": "2024-01-01T10:00:00Z",
      "last_activity_at": "2024-01-01T12:00:00Z",
      "expires_at": "2024-01-08T10:00:00Z"
    }
  ],
  "current_session_id": "session-uuid",
  "total_count": 1
}
```

### `DELETE /auth/sessions/{session_id}`
**Revoke specific session**

```http
DELETE /auth/sessions/session-uuid
Authorization: Bearer {access_token}
```

### `POST /auth/forgot-password`
**Initiate password reset via email**

```http
POST /auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```

### `POST /auth/reset-password`
**Reset password with token**

```http
POST /auth/reset-password
Content-Type: application/json

{
  "token": "reset-token-here",
  "new_password": "newsecurepassword123"
}
```

### `POST /auth/verify-email`
**Verify email with token**

```http
POST /auth/verify-email
Content-Type: application/json

{
  "token": "verification-token-here"
}
```

### `POST /auth/resend-verification`
**Resend email verification**

```http
POST /auth/resend-verification
Content-Type: application/json

{
  "email": "user@example.com"
}
```

---

## **User Management (4 endpoints)**

### `POST /users/profile`
**Create complete user with profile**

```http
POST /users/profile
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "job_title": "Software Engineer",
  "department": "Engineering",
  "bio": "Passionate developer",
  "skills": ["Python", "FastAPI"],
  "interests": ["Technology", "Music"],
  "tenant_id": "org-123"
}
```

### `GET /users/{user_id}/dashboard`
**Get user dashboard data**

```http
GET /users/user-uuid/dashboard
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "user": {
    "user_id": "user-uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "status": "active",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
  },
  "recent_activity": [
    {
      "id": "activity-uuid",
      "action": "login",
      "timestamp": "2024-01-01T12:00:00Z",
      "ip_address": "192.168.1.100"
    }
  ],
  "statistics": {
    "total_logins": 150,
    "organizations_count": 2,
    "mfa_methods": 2
  },
  "preferences": {
    "theme": "dark",
    "language": "en",
    "timezone": "UTC"
  }
}
```

### `PATCH /users/{user_id}/preferences`
**Update user preferences**

```http
PATCH /users/user-uuid/preferences
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "theme": "dark",
  "language": "en",
  "timezone": "America/New_York",
  "email_notifications": true,
  "push_notifications": false,
  "privacy_level": "public"
}
```

### `GET /users/{user_id}/activity`
**Get user activity summary**

```http
GET /users/user-uuid/activity?page=1&page_size=20
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "activities": [
    {
      "id": "activity-uuid",
      "action": "login",
      "resource": "auth",
      "timestamp": "2024-01-01T12:00:00Z",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "metadata": {
        "login_method": "password",
        "mfa_used": true
      }
    }
  ],
  "total_count": 150,
  "page": 1,
  "page_size": 20
}
```

---

## **Organization Management (4 endpoints)**

### `POST /organizations`
**Create organization**

```http
POST /organizations
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "description": "Leading technology company",
  "website_url": "https://acme.com",
  "contact_email": "contact@acme.com",
  "organization_type": "enterprise",
  "industry": "Technology"
}
```

**Response:**
```json
{
  "id": "org-uuid",
  "name": "Acme Corporation",
  "slug": "acme-corp",
  "description": "Leading technology company",
  "website_url": "https://acme.com",
  "contact_email": "contact@acme.com",
  "organization_type": "enterprise",
  "industry": "Technology",
  "member_count": 1,
  "status": "active",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### `GET /organizations/{org_id}/dashboard`
**Get organization dashboard**

```http
GET /organizations/org-uuid/dashboard
Authorization: Bearer {access_token}
```

### `POST /organizations/{org_id}/users`
**Add user to organization**

```http
POST /organizations/org-uuid/users
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "user_id": "user-uuid",
  "role": "member"
}
```

### `GET /organizations/{org_id}/users`
**List organization users**

```http
GET /organizations/org-uuid/users?page=1&page_size=20
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "members": [
    {
      "user_id": "user-uuid",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "admin",
      "status": "active",
      "joined_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total_count": 1,
  "page": 1,
  "page_size": 20
}
```

---

## **Multi-Factor Authentication (6 endpoints)**

### `POST /mfa/setup`
**Setup new MFA method**

```http
POST /mfa/setup
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "method_type": "totp",
  "phone_number": "+1234567890"
}
```

**Response:**
```json
{
  "method_id": "mfa-method-uuid",
  "method_type": "totp",
  "setup_data": {
    "qr_code": "data:image/png;base64,...",
    "secret_key": "JBSWY3DPEHPK3PXP",
    "backup_codes": ["123456789", "987654321"]
  },
  "is_verified": false,
  "message": "Scan QR code with authenticator app"
}
```

### `GET /mfa/methods`
**List user's MFA methods**

```http
GET /mfa/methods
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "methods": [
    {
      "method_id": "mfa-method-uuid",
      "method_type": "email",
      "destination": "u***@example.com",
      "is_primary": true,
      "is_verified": true,
      "created_at": "2023-01-01T00:00:00Z",
      "last_used_at": "2024-01-01T12:00:00Z"
    }
  ],
  "has_verified_methods": true,
  "primary_method": "email"
}
```

### `POST /mfa/challenge`
**Initiate MFA challenge**

```http
POST /mfa/challenge
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "method_id": "mfa-method-uuid"
}
```

**Response:**
```json
{
  "challenge_id": "challenge-uuid",
  "method_type": "email",
  "destination": "u***@example.com",
  "expires_at": "2024-01-01T12:05:00Z",
  "attempts_remaining": 3,
  "message": "Verification code sent to your email"
}
```

### `POST /mfa/verify`
**Verify MFA challenge response**

```http
POST /mfa/verify
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "challenge_id": "challenge-uuid",
  "code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "MFA verification successful",
  "tokens": {
    "access_token": "new-access-token",
    "refresh_token": "new-refresh-token"
  }
}
```

### `DELETE /mfa/methods/{method_id}`
**Remove MFA method**

```http
DELETE /mfa/methods/mfa-method-uuid
Authorization: Bearer {access_token}
```

### `POST /mfa/backup-codes/regenerate`
**Generate new backup codes**

```http
POST /mfa/backup-codes/regenerate
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "backup_codes": [
    "123456789",
    "987654321",
    "456789123",
    "789123456",
    "321654987"
  ],
  "codes_remaining": 5,
  "regenerated_at": "2024-01-01T12:00:00Z",
  "message": "New backup codes generated. Store them securely."
}
```

---

## **Monitoring & Health (2 endpoints)**

### `GET /health`
**Service health check**

```http
GET /health
```

**Response:**
```json
{
  "service": "auth-service",
  "status": "healthy",
  "version": "1.0.0",
  "database": "healthy",
  "cache": "healthy"
}
```

### `GET /metrics`
**Prometheus metrics endpoint**

```http
GET /metrics
```

**Response:**
```
# HELP auth_requests_total Total authentication requests
# TYPE auth_requests_total counter
auth_requests_total 1500

# HELP auth_failures_total Total authentication failures
# TYPE auth_failures_total counter
auth_failures_total 25
```

---

## **Authentication & Authorization**

### **JWT Token Format**
All authenticated endpoints require a Bearer token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### **Token Claims**
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "tenant_id": "org-uuid",
  "roles": ["user", "admin"],
  "permissions": ["read:profile", "write:profile"],
  "exp": 1704067200,
  "iat": 1704063600
}
```

### **Permission Levels**
- **Public**: No authentication required
- **Authenticated**: Valid JWT token required
- **Self-only**: User can only access their own data
- **Admin**: Organization admin/owner permissions required
- **System**: Internal service-to-service communication

---

## **Error Handling**

### **HTTP Status Codes**
- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required or failed
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource already exists
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### **Error Response Format**
```json
{
  "detail": "Error message description",
  "error_code": "AUTH_001",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### **Common Error Codes**
- `AUTH_001` - Invalid credentials
- `AUTH_002` - Token expired
- `AUTH_003` - MFA required
- `AUTH_004` - Rate limit exceeded
- `USER_001` - User not found
- `ORG_001` - Organization not found
- `MFA_001` - MFA setup required

---

## **Rate Limiting**

### **Rate Limits**
- **Login attempts**: 5 per minute per email
- **Password reset**: 3 per hour per email
- **MFA challenges**: 10 per hour per user
- **API requests**: 1000 per hour per user

### **Rate Limit Headers**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1704067200
Retry-After: 3600
```

---

## **Development & Testing**

### **Base URL**
- Development: `http://localhost:8001`
- Staging: `https://auth-staging.example.com`
- Production: `https://auth.example.com`

### **OpenAPI Documentation**
Interactive API documentation is available at:
- Swagger UI: `{base_url}/docs`
- ReDoc: `{base_url}/redoc`
- OpenAPI JSON: `{base_url}/openapi.json`

### **Postman Collection**
Import the OpenAPI spec into Postman for easy testing and development.

---

## **Support**

For API support and questions:
- **Documentation**: This file and inline OpenAPI docs
- **Issues**: GitHub repository issues
- **Security**: security@example.com
- **General**: support@example.com

---

*Last updated: September 9, 2024*  
*API Version: 1.0.0*  
*Service: Auth Service v1.0.0*