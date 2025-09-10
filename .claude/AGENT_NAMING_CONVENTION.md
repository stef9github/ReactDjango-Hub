# Claude Agent Naming Convention

## Overview
All Claude agents in this project follow a consistent naming scheme with the `ag-` prefix.

## Agent Names

### Core Service Agents
- `ag-backend` - Django Backend Agent (backend/)
- `ag-frontend` - React Frontend Agent (frontend/)
- `ag-identity` - Identity Service Agent (services/identity-service/)
- `ag-communication` - Communication Service Agent (services/communication-service/)
- `ag-content` - Content Service Agent (services/content-service/)
- `ag-workflow` - Workflow Intelligence Agent (services/workflow-intelligence-service/)

### Infrastructure & Coordination
- `ag-infrastructure` - Infrastructure Agent (infrastructure/)
- `ag-coordinator` - Services Coordinator Agent (services/)

### Quality & Compliance
- `ag-security` - Security & Compliance Agent (project-wide)
- `ag-reviewer` - Code Review Agent (project-wide)

## Usage

### Command Line
```bash
# Launch an agent session
./.claude/launch-agent.sh ag-backend
./.claude/launch-agent.sh ag-frontend
```

### VS Code Terminal Profiles
All agents are available as terminal profiles in VS Code. Open the terminal dropdown and select any agent profile to launch it.

## Benefits
- **Consistency**: All agent names follow the same pattern
- **Clarity**: The `ag-` prefix clearly identifies agent-related configurations
- **Namespace Organization**: Prevents naming conflicts with other project components
- **Easy Discovery**: Simple to find all agent-related items by searching for `ag-`

## Testing
Run the test script to verify all agent names are working:
```bash
bash .claude/test-agent-names.sh
```