# Agent Delegation Pattern Documentation

## Overview
This document describes the delegation pattern implemented for the ag-coordinator agent to efficiently handle service-specific issues by delegating to specialized service agents.

## Delegation Architecture

### Agent Hierarchy
```
ag-coordinator (Orchestration Layer)
    ├── ag-identity (Identity Service)
    ├── ag-content (Content Service)
    ├── ag-communication (Communication Service)
    └── ag-workflow (Workflow Intelligence Service)
```

## Delegation Rules

### When ag-coordinator Delegates

The ag-coordinator agent delegates to service-specific agents when:

1. **Service-Internal Issues**: Problems within a specific service's business logic, database, or internal components
2. **Service-Specific Features**: Implementation or modification of service-specific functionality
3. **Service Configuration**: Service-specific configuration that doesn't affect inter-service communication

### When ag-coordinator Handles Directly

The ag-coordinator handles issues directly when:

1. **Cross-Service Communication**: Problems with service-to-service communication
2. **API Gateway**: Kong configuration, routing rules, load balancing
3. **Docker Orchestration**: Container networking, service discovery
4. **Documentation**: Cross-service documentation and architecture docs

## Service Agent Mapping

| Service | Agent | Port | Responsibilities |
|---------|-------|------|------------------|
| identity-service | ag-identity | 8001 | Authentication, JWT, users, roles, permissions |
| content-service | ag-content | 8002 | Documents, storage, search, indexing |
| communication-service | ag-communication | 8003 | Notifications, email, SMS, WebSocket |
| workflow-intelligence-service | ag-workflow | 8004 | Workflows, automation, AI integration, scheduling |

## Delegation Workflow

### 1. Detection Phase
```bash
# Check service health
curl http://localhost:8001/health  # Identity
curl http://localhost:8002/health  # Content
curl http://localhost:8003/health  # Communication
curl http://localhost:8004/health  # Workflow

# Check service logs
docker logs [service-name] 2>&1 | grep ERROR
```

### 2. Analysis Phase
Determine if the issue is:
- **Coordination Issue**: Networking, gateway, cross-service → ag-coordinator handles
- **Service Issue**: Business logic, service internals → Delegate to service agent

### 3. Delegation Phase
```markdown
Pattern: "This is a [service-name] issue. Delegating to [agent-name]..."

Example: "This is an identity-service authentication issue. Delegating to ag-identity..."
```

### 4. Handoff Phase
Provide the service agent with:
- Full error messages and stack traces
- Service health status
- Impact on other services
- Expected resolution

## Error Pattern Recognition

### Identity Service Patterns
Keywords that trigger delegation to ag-identity:
- JWT, token, authentication, auth
- User, role, permission, RBAC
- Login, logout, session
- 401, 403 errors

### Content Service Patterns
Keywords that trigger delegation to ag-content:
- Document, file, upload, download
- Storage, S3, filesystem
- Search, index, query
- Document processing

### Communication Service Patterns
Keywords that trigger delegation to ag-communication:
- Email, SMS, notification
- WebSocket, real-time
- Message queue, Redis
- Notification delivery

### Workflow Service Patterns
Keywords that trigger delegation to ag-workflow:
- Workflow, automation, process
- Task, schedule, cron
- AI, model, inference
- Workflow execution

## Implementation Examples

### Example 1: JWT Token Issue
```python
# Detected in logs:
"ERROR: JWT token validation failed: Token expired"

# ag-coordinator action:
"JWT authentication error detected. This is an identity-service issue.
Delegating to ag-identity with error context..."

# Handoff to ag-identity:
"ag-identity: JWT token expiration errors on port 8001. 
Please investigate token generation and validation logic."
```

### Example 2: Network Issue
```python
# Detected in logs:
"ERROR: Connection refused between services"

# ag-coordinator action:
"Inter-service networking issue detected. This is a coordination problem.
Handling within ag-coordinator scope..."

# Resolution by ag-coordinator:
- Check Docker network configuration
- Verify service discovery settings
- Ensure services are on same network
```

## Benefits of Delegation Pattern

1. **Clear Separation of Concerns**: Each agent focuses on its domain expertise
2. **Efficient Problem Resolution**: Issues are handled by the most qualified agent
3. **Reduced Complexity**: ag-coordinator doesn't need deep knowledge of each service
4. **Scalability**: New services can be added with their own agents
5. **Maintainability**: Service-specific logic stays with service agents

## Monitoring and Metrics

### Delegation Metrics to Track
- Number of delegations per service agent
- Time to resolution after delegation
- Success rate of delegated issues
- Most common delegation patterns

### Health Check Dashboard
```bash
# Script to check all services and determine delegation needs
#!/bin/bash
for service in identity content communication workflow; do
    echo "Checking $service-service..."
    if ! curl -f http://localhost:800X/health; then
        echo "  → Issue detected, should delegate to ag-$service"
    fi
done
```

## Best Practices

1. **Always Provide Context**: When delegating, include all relevant error information
2. **Document Delegations**: Keep track of delegation patterns for future reference
3. **Verify Resolution**: After delegation, confirm the issue was resolved
4. **Update Patterns**: Add new error patterns as they're discovered
5. **Maintain Boundaries**: Never let ag-coordinator modify service internals

## Conclusion

The delegation pattern ensures that:
- ag-coordinator focuses on orchestration and coordination
- Service agents handle their specific domain issues
- Problems are resolved by the most appropriate agent
- The system remains modular and maintainable

This pattern has been implemented in the ag-coordinator agent configuration and should be followed consistently for all service-related issues.