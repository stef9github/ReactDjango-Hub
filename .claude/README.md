# Claude Agent System - Simplified Configuration

## Overview

This directory contains the simplified Claude Code agent configuration for the ReactDjango Hub enterprise SaaS platform. The system has been streamlined to provide one agent per service/domain with a unified launcher.

## Quick Start

Launch any agent using the unified launcher:

```bash
# Basic usage
./.claude/launch-agent.sh <agent-name>

# Examples
./.claude/launch-agent.sh backend      # Django backend development
./.claude/launch-agent.sh frontend     # React frontend development
./.claude/launch-agent.sh identity     # Identity service development
```

To see all available agents:
```bash
./.claude/launch-agent.sh
```

## Available Agents

### Core Service Agents
- **backend** - Django Backend (port 8000)
- **frontend** - React Frontend (port 3000/5173)
- **identity** - Identity Service (port 8001)
- **communication** - Communication Service
- **content** - Content Service
- **workflow** - Workflow Intelligence Service

### Infrastructure & Coordination
- **infrastructure** - Docker, Kubernetes, CI/CD
- **coordinator** - API Gateway, Service Mesh

### Quality & Compliance
- **security** - Security audits and compliance
- **review** - Code review and quality

## File Structure

```
.claude/
├── launch-agent.sh           # Unified agent launcher
├── agents.yaml              # Agent configuration definitions
├── agent_session_manager.py # Session management (if needed)
├── enhance_status_line.sh   # Status display utility
└── README.md               # This file
```

## VSCode Integration

The VSCode terminal profiles have been configured to launch agents directly. Access them through:
1. Open Terminal in VSCode
2. Click the dropdown arrow next to the + button
3. Select the agent you want to launch

## Agent Boundaries

Each agent has specific responsibilities:
- **Service agents** manage their own service code only
- **Infrastructure agent** handles deployment and containerization
- **Coordinator agent** manages inter-service communication
- **Security/Review agents** ensure quality and compliance

## Key Principles

1. **One agent per domain** - Each service has exactly one responsible agent
2. **Clear boundaries** - Agents don't modify code outside their domain
3. **API-first communication** - Services interact only through defined APIs
4. **Unified launcher** - Single entry point for all agents

## Migrating from Old System

If you had the old multi-agent system:
1. Run `./cleanup-old-agents.sh` to remove old files
2. Use the new `launch-agent.sh` script
3. Agent names are simplified (e.g., `backend` instead of `claude-backend-agent`)

## Configuration

Agent definitions are centralized in `agents.yaml`. Each agent specifies:
- Name and description
- Working directory
- Responsibilities
- Common commands

## Support

For issues or questions about the agent system:
1. Check the main `CLAUDE.md` file in the project root
2. Review service-specific documentation
3. Use the `review` agent for code quality questions