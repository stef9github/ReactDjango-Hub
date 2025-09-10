# 🤖 Agent Configuration System

## Overview

The Agent Configuration System provides specialized Claude agents for different aspects of the ReactDjango-Hub Medical project. Each agent has specific permissions, tools, and expertise areas to maximize efficiency and maintain code quality.

## 🚀 Quick Start

### Launch an Agent

```bash
# From project root
./launch_agent.sh backend        # Launch backend Django specialist
./launch_agent.sh frontend       # Launch frontend React specialist
./launch_agent.sh identity       # Launch identity service specialist
./launch_agent.sh testing        # Launch testing specialist
```

### List Available Agents

```bash
./launch_agent.sh --list
```

## 📋 Available Agents

### Backend Agent
- **Specialization**: Django backend, APIs, database operations
- **Working Directory**: `backend/`
- **Key Tools**: Python, Django, PostgreSQL
- **Git Worktree**: `backend-dev`

### Frontend Agent
- **Specialization**: React, TypeScript, UI/UX development
- **Working Directory**: `frontend/`
- **Key Tools**: npm, React, Vite, Tailwind CSS
- **Git Worktree**: `frontend-dev`

### Identity Service Agent
- **Specialization**: Authentication, MFA, user management
- **Working Directory**: `services/identity-service/`
- **Key Tools**: FastAPI, SQLAlchemy, Alembic
- **Port**: 8001

### Content Service Agent
- **Specialization**: Document management, file processing
- **Working Directory**: `services/content-service/`
- **Key Tools**: Python, file processing libraries

### Testing Agent
- **Specialization**: Test creation, coverage, quality assurance
- **Working Directory**: Project root
- **Key Tools**: pytest, jest, coverage tools
- **Access**: Can read all files, write only test files

### Infrastructure Agent
- **Specialization**: Docker, Kubernetes, CI/CD
- **Working Directory**: Project root
- **Key Tools**: Docker, docker-compose, kubectl, make

### Security Agent
- **Specialization**: Security audits, HIPAA/RGPD compliance
- **Working Directory**: Project root
- **Key Tools**: Security scanners, audit tools

## 🔧 Advanced Usage

### Setup Git Worktree for Agent

```bash
# Create isolated git worktree for agent development
./launch_agent.sh backend --setup-worktree
```

### Validate Agent Configuration

```bash
./launch_agent.sh backend --validate
```

### Direct CLI Usage

```bash
cd .claude
python agent_configurator.py init       # Initialize system
python agent_configurator.py list       # List agents
python agent_configurator.py configure backend  # Configure specific agent
python agent_configurator.py launch backend     # Generate launch script
python agent_configurator.py worktree backend   # Setup git worktree
```

## 📁 Configuration Structure

```
.claude/
├── agent_configurator.py       # Main configuration tool
├── agents/
│   ├── config.yaml             # Master configuration
│   ├── templates/              # Agent templates
│   │   ├── backend.yaml
│   │   ├── frontend.yaml
│   │   ├── identity.yaml
│   │   └── ...
│   ├── configs/                # Active configurations
│   │   └── [generated configs]
│   └── scripts/                # Launch scripts
│       └── launch_*.sh
└── AGENT_CONFIGURATION.md      # This file
```

## 🔐 Agent Permissions

Each agent has scoped permissions:

### Read Permissions
- Agents can only read files in their designated areas
- All agents can read documentation and CLAUDE.md

### Write Permissions
- Backend agent: Can only modify `backend/**`
- Frontend agent: Can only modify `frontend/**`
- Service agents: Can only modify their service directory
- Testing agent: Can only create/modify test files

### Execute Permissions
- Each agent has specific command restrictions
- Language-specific tools (python, npm, etc.)
- Service-specific tools (django-admin, pytest, etc.)

## 🔄 Agent Communication

Agents can communicate through:
- Shared configuration files in `.claude/shared/`
- Git commits and branches
- Documentation updates

## 🎯 Best Practices

1. **Use the Right Agent**: Launch the specialized agent for your task
2. **Respect Boundaries**: Agents are restricted for a reason
3. **Document Changes**: Update relevant documentation
4. **Test Coverage**: Use the testing agent to maintain coverage
5. **Security First**: Use security agent for compliance checks

## 🛠️ Customization

### Modify Agent Template

1. Edit template file in `.claude/agents/templates/`
2. Regenerate configuration:
   ```bash
   cd .claude
   python agent_configurator.py configure <agent-type>
   ```

### Add Custom Aliases

Edit the agent's template to add shortcuts:
```yaml
aliases:
  migrate: "python manage.py migrate"
  test: "python manage.py test"
```

### Adjust Permissions

Modify the `permissions` section in templates:
```yaml
permissions:
  read: ["backend/**", "docs/**"]
  write: ["backend/**"]
  execute: ["python", "pip", "django-admin"]
```

## 🐛 Troubleshooting

### Agent Won't Launch
- Check Python 3 is installed
- Install PyYAML: `pip install pyyaml`
- Verify git is configured

### Permission Denied
- Agent is trying to access restricted areas
- Check agent configuration for proper permissions

### Worktree Issues
- Ensure you're on a git repository
- Check for existing worktrees: `git worktree list`
- Remove old worktrees: `git worktree remove <path>`

## 📚 Additional Resources

- Project Documentation: `/docs/`
- Service-specific docs: `services/*/README.md`
- CLAUDE.md: Main project instructions

## 💡 Tips

- Use `--list` to see all available agents
- Combine flags: `./launch_agent.sh backend --setup-worktree --validate`
- Check agent config: `cat .claude/agents/configs/<agent>.yaml`
- View agent restrictions before starting work

---

*Agent Configuration System v1.0.0 - ReactDjango-Hub Medical*