# Security Review Checklist

## Authentication & Authorization
- [ ] All API endpoints require authentication where appropriate
- [ ] Role-based access control (RBAC) properly implemented
- [ ] JWT tokens have appropriate expiration times
- [ ] Refresh token rotation implemented
- [ ] Password reset tokens expire after single use
- [ ] Multi-factor authentication available for sensitive operations
- [ ] Session management secure (HttpOnly, Secure flags)
- [ ] Account lockout after failed attempts
- [ ] Privilege escalation prevented

## Input Validation & Sanitization
- [ ] All user inputs validated on both client and server
- [ ] SQL injection prevention (parameterized queries/ORM)
- [ ] XSS prevention (output encoding, CSP headers)
- [ ] CSRF protection enabled
- [ ] Command injection prevention
- [ ] Path traversal prevention
- [ ] XML external entity (XXE) prevention
- [ ] File upload restrictions (type, size, content validation)
- [ ] Rate limiting implemented

## Data Protection
- [ ] Sensitive data encrypted at rest (AES-256 or better)
- [ ] TLS 1.2+ enforced for data in transit
- [ ] PII properly classified and protected
- [ ] Secrets stored in secure vault (not in code)
- [ ] Database credentials properly secured
- [ ] API keys rotated regularly
- [ ] Sensitive data masked in logs
- [ ] Backup encryption enabled
- [ ] Data retention policies enforced

## Security Headers
- [ ] Content-Security-Policy configured
- [ ] X-Frame-Options set to prevent clickjacking
- [ ] X-Content-Type-Options: nosniff
- [ ] Strict-Transport-Security (HSTS) enabled
- [ ] X-XSS-Protection configured
- [ ] Referrer-Policy set appropriately
- [ ] Feature-Policy/Permissions-Policy configured

## Error Handling & Logging
- [ ] Generic error messages for users
- [ ] Detailed errors logged server-side only
- [ ] Stack traces never exposed to users
- [ ] Security events logged (login, failed auth, etc.)
- [ ] Log injection prevention
- [ ] Logs contain request correlation IDs
- [ ] Sensitive data not logged
- [ ] Log retention and rotation configured

## Third-Party Dependencies
- [ ] Dependencies scanned for vulnerabilities
- [ ] Latest security patches applied
- [ ] Unused dependencies removed
- [ ] Dependency licenses reviewed
- [ ] Supply chain attacks considered
- [ ] Package integrity verification
- [ ] Private package registry used where appropriate

## API Security
- [ ] API versioning implemented
- [ ] API rate limiting per user/IP
- [ ] API documentation doesn't expose sensitive info
- [ ] GraphQL query depth limiting
- [ ] REST API follows least privilege principle
- [ ] CORS properly configured
- [ ] API gateway security rules
- [ ] Service-to-service authentication

## Infrastructure Security
- [ ] Container security scanning
- [ ] Kubernetes security policies
- [ ] Network segmentation implemented
- [ ] Firewall rules properly configured
- [ ] Intrusion detection/prevention
- [ ] Security groups/network ACLs
- [ ] Bastion hosts for admin access
- [ ] Infrastructure as Code security

## Compliance & Privacy
- [ ] GDPR compliance (if applicable)
- [ ] HIPAA compliance (if applicable)
- [ ] PCI DSS compliance (if applicable)
- [ ] Data residency requirements met
- [ ] Privacy policy implementation
- [ ] User consent management
- [ ] Right to deletion implemented
- [ ] Data portability supported
- [ ] Audit trail comprehensive

## Security Testing
- [ ] Static Application Security Testing (SAST)
- [ ] Dynamic Application Security Testing (DAST)
- [ ] Software Composition Analysis (SCA)
- [ ] Penetration testing performed
- [ ] Security unit tests written
- [ ] Security integration tests
- [ ] Fuzzing performed where appropriate
- [ ] Security regression tests

## Incident Response
- [ ] Security incident response plan exists
- [ ] Contact information current
- [ ] Breach notification process defined
- [ ] Forensics capability available
- [ ] Backup and recovery tested
- [ ] Security patches can be deployed quickly
- [ ] Kill switches for critical features

## Additional Checks
- [ ] No hardcoded credentials
- [ ] No use of unsafe functions
- [ ] Cryptographically secure random numbers
- [ ] Time-of-check to time-of-use (TOCTOU) issues
- [ ] Race conditions addressed
- [ ] Memory safety (buffer overflows, etc.)
- [ ] Integer overflow/underflow checks
- [ ] Business logic security flaws