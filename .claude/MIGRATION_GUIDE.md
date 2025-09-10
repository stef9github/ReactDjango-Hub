# Migration Guide: Simplified Claude Agent System

## What Changed?

We've simplified the Claude Code agent system from 30+ specialized agents to just 10 essential agents, removing redundancy and improving maintainability.

### Before (Complex)
- 30+ individual agent launcher scripts
- Medical-specific agents
- Duplicate "expert" agents
- Multiple agents for same service
- Confusing naming conventions

### After (Simplified)
- Single unified launcher script
- 10 essential agents (one per domain)
- Domain-agnostic, enterprise-focused
- Clear, consistent naming
- Centralized configuration

## Migration Steps

### 1. Update VSCode Settings

The terminal profiles in VSCode have been updated. To apply:
1. Restart VSCode
2. Open a new terminal
3. Use the dropdown to see the new simplified agent list

### 2. Clean Up Old Files

Run the cleanup script to remove old agent files:
```bash
cd .claude
./cleanup-old-agents.sh
```

### 3. Update Your Workflow

#### Old Way:
```bash
# Launching agents with individual scripts
./.claude/claude-backend-agent
./.claude/claude-django-backend-expert
./.claude/claude-medical-frontend-specialization
```

#### New Way:
```bash
# Single launcher with agent name
./.claude/launch-agent.sh backend
./.claude/launch-agent.sh frontend
./.claude/launch-agent.sh identity
```

## Agent Name Mappings

| Old Agent Names | New Agent Name | Purpose |
|----------------|----------------|---------|
| claude-backend-agent<br>claude-django-backend-expert<br>claude-backend | **backend** | Django development |
| claude-frontend-agent<br>claude-react-frontend-expert<br>claude-frontend<br>claude-medical-frontend-specialization | **frontend** | React development |
| claude-identity-service-expert<br>claude-identity | **identity** | Identity service |
| claude-communication-service<br>claude-communication | **communication** | Communication service |
| claude-content-service<br>claude-content | **content** | Content service |
| claude-workflow-intelligence-service<br>claude-workflow | **workflow** | Workflow service |
| claude-deployment-agent | **infrastructure** | Docker, K8s, CI/CD |
| claude-services-coordinator | **coordinator** | Service integration |
| claude-security-compliance-expert<br>claude-security | **security** | Security & compliance |
| claude-code-reviewer<br>claude-testing | **review** | Code review & quality |

## Removed Agents

The following specialized agents have been removed:
- Medical-specific agents (medical-frontend-specialization, medical-translator-agent)
- Redundant expert agents (now consolidated into main agents)
- Tech lead agent (responsibilities distributed)
- Documentation agent (integrated into service agents)
- Commit workflow agent (standard git workflow)

## Benefits of Simplification

1. **Easier to remember** - Just 10 agents with clear names
2. **Less confusion** - One agent per service/domain
3. **Faster startup** - Single launcher script
4. **Better maintenance** - Centralized configuration in agents.yaml
5. **Cleaner workspace** - Fewer files to manage

## Quick Reference

```bash
# List all available agents
./.claude/launch-agent.sh

# Launch specific agent
./.claude/launch-agent.sh <agent-name>

# Available agents:
# - backend         (Django)
# - frontend        (React)
# - identity        (Auth service)
# - communication   (Messaging)
# - content         (Documents)
# - workflow        (Automation)
# - infrastructure  (DevOps)
# - coordinator     (Integration)
# - security        (Compliance)
# - review          (Quality)
```

## Troubleshooting

### Issue: Old agent commands not working
**Solution:** Use the new launcher with simplified names

### Issue: VSCode terminal profiles showing old agents
**Solution:** Restart VSCode to reload the updated settings.json

### Issue: Can't find specific expert agent
**Solution:** Expert functionality is now integrated into main agents (e.g., Django expertise is in 'backend' agent)

### Issue: Need medical-specific functionality
**Solution:** All agents are now domain-agnostic. Medical features should be implemented as regular business logic

## Need Help?

- Check `.claude/README.md` for detailed documentation
- Review `.claude/agents.yaml` for agent definitions
- Use `.claude/launch-agent.sh` without arguments to see all options