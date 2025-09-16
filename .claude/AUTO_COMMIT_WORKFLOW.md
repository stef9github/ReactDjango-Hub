# Claude Code Auto-Commit Workflow

## Overview

The Claude Code Auto-Commit Workflow provides automated git commit functionality for all Claude agents with comprehensive safety checks, boundary enforcement, and test validation. This system ensures that agents can autonomously commit their successful work while maintaining code quality and security standards.

## Features

### 🔒 Safety & Security
- **Boundary Enforcement**: Each agent can only commit files within their designated directories
- **Sensitive File Detection**: Prevents committing credentials, keys, or secrets
- **Secret Pattern Scanning**: Checks file content for potential sensitive information
- **Large File Warning**: Alerts for files over 10MB
- **Merge Conflict Detection**: Prevents committing files with unresolved conflicts

### ✅ Quality Assurance
- **Automated Testing**: Runs agent-specific tests before committing
- **Build Validation**: Ensures code compiles and builds successfully
- **Linting & Type Checking**: Validates code style and type safety
- **Security Scanning**: Runs security checks for vulnerabilities

### 📝 Commit Standards
- **Conventional Commits**: Enforces consistent commit message format
- **Agent Attribution**: Automatically adds agent metadata to commits
- **Claude Code Attribution**: Includes proper co-authorship
- **Detailed Logging**: Maintains audit trail of all commits

## Installation

### 1. Install Git Hooks (Recommended)
```bash
# Install safety hooks for all commits
.claude/scripts/install-hooks.sh
```

### 2. Verify Scripts are Executable
```bash
# Should already be executable, but verify:
chmod +x .claude/scripts/auto-commit.sh
chmod +x .claude/scripts/test-runner.sh
chmod +x .claude/scripts/update-all-agents.sh
```

## Usage

### Basic Auto-Commit
```bash
# Syntax
.claude/scripts/auto-commit.sh <agent> <type> "<message>" [--test-first]

# Examples
.claude/scripts/auto-commit.sh backend feat "Add user authentication API" --test-first
.claude/scripts/auto-commit.sh frontend fix "Resolve dropdown alignment issue" --test-first
.claude/scripts/auto-commit.sh infrastructure chore "Update Docker configuration"
```

### Commit Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or updates
- `chore`: Maintenance tasks

### Agent Names
- `backend` - Django backend service
- `frontend` - React frontend application
- `identity` - Identity/authentication service
- `communication` - Communication service
- `content` - Content management service
- `workflow` - Workflow automation service
- `infrastructure` - Infrastructure and DevOps
- `coordinator` - API gateway and service mesh
- `documentation` - Documentation updates
- `security` - Security configurations

## Agent Boundaries

Each agent has strict boundaries for file modifications:

| Agent | Allowed Paths | Example Files |
|-------|---------------|---------------|
| `backend` | `backend/**` | Django models, views, APIs, tests |
| `frontend` | `frontend/**` | React components, styles, hooks |
| `identity` | `services/identity-service/**` | Auth endpoints, user management |
| `communication` | `services/communication-service/**` | Messaging, notifications |
| `content` | `services/content-service/**` | File storage, documents |
| `workflow` | `services/workflow-service/**` | Process automation, AI workflows |
| `infrastructure` | `infrastructure/**`, `docker/**`, `.github/**` | Docker, K8s, CI/CD |
| `coordinator` | `services/api-gateway/**`, `services/service-mesh/**` | Kong, service discovery |
| `documentation` | `docs/**`, `*.md` | All documentation files |
| `security` | `.claude/security/**`, `security-configs/**` | Security policies, scans |

## Testing Workflow

### Manual Testing
```bash
# Run tests for a specific agent
.claude/scripts/test-runner.sh backend
.claude/scripts/test-runner.sh frontend
```

### Automated Testing with Commit
```bash
# The --test-first flag runs tests before committing
.claude/scripts/auto-commit.sh backend feat "New feature" --test-first
```

### Test Coverage by Agent

#### Backend (Django)
- Django deployment checks
- Unit and integration tests
- Migration validation
- Security scanning with bandit

#### Frontend (React)
- ESLint code linting
- TypeScript type checking
- Jest unit tests
- Build validation

#### Services (FastAPI/Python)
- Pytest test suites
- API endpoint validation
- Health check verification

## Workflow Examples

### Feature Development
```bash
# 1. Develop feature
# ... make code changes ...

# 2. Test locally
.claude/scripts/test-runner.sh backend

# 3. Auto-commit with tests
.claude/scripts/auto-commit.sh backend feat "Add analytics dashboard" --test-first
```

### Bug Fix
```bash
# 1. Fix the bug
# ... fix code ...

# 2. Verify fix with tests
python manage.py test apps.users

# 3. Commit the fix
.claude/scripts/auto-commit.sh backend fix "Resolve authentication timeout" --test-first
```

### Documentation Update
```bash
# 1. Update documentation
# ... edit docs ...

# 2. Commit without tests (docs don't need tests)
.claude/scripts/auto-commit.sh documentation docs "Update API documentation"
```

## Git Hooks

The system includes three git hooks for additional safety:

### Pre-Commit Hook
- Checks for sensitive files (keys, .env, secrets)
- Scans for hardcoded credentials
- Warns about large files
- Detects merge conflict markers

### Commit-Msg Hook
- Validates conventional commit format
- Adds Claude Code attribution
- Ensures consistent message structure

### Pre-Push Hook
- Warns about pushing to main/master
- Suggests feature branch workflow
- Final safety check before remote push

## Logging and Auditing

All commits are logged to `.claude/logs/commits.log` with:
- Timestamp
- Agent name
- Commit hash
- Commit message
- Test results (if applicable)

## Troubleshooting

### Common Issues

#### "Agent tried to modify files outside its boundaries"
- Ensure you're only modifying files in your agent's allowed directories
- Use `git status` to check which files are staged
- Use `git reset <file>` to unstage files outside your boundary

#### "Tests failed - commit aborted"
- Review test output for specific failures
- Fix the failing tests or code issues
- Re-run tests manually: `.claude/scripts/test-runner.sh <agent>`
- Retry commit after fixes

#### "No staged files to commit"
- Ensure you have made changes to files
- Check `git status` to see modified files
- The script automatically stages files in your boundary

#### "Sensitive file detected"
- Remove sensitive files from staging
- Add them to `.gitignore`
- Use environment variables instead of hardcoded secrets

## Best Practices

### For Claude Agents

1. **Test Before Committing**: Always verify your changes work correctly
2. **Small, Focused Commits**: Make atomic commits for single features/fixes
3. **Clear Commit Messages**: Describe what and why, not just how
4. **Stay Within Boundaries**: Never modify files outside your domain
5. **Review Before Committing**: Check `git diff` before auto-commit

### For Human Developers

1. **Let Agents Auto-Commit**: Allow agents to handle their own commits
2. **Review Agent Commits**: Periodically review agent commit history
3. **Update Boundaries**: Adjust agent boundaries as project evolves
4. **Monitor Logs**: Check commit logs for patterns or issues
5. **Maintain Tests**: Ensure test suites stay comprehensive

## Integration with ADR-010

This auto-commit workflow aligns with ADR-010 (Local-First Development Strategy):

- **No Container Complexity**: Direct file system operations
- **Fast Feedback**: Immediate test results and commit status
- **Simple Tools**: Standard git commands without abstraction
- **Developer Friendly**: Familiar git workflow with safety nets
- **AI Agent Optimized**: Designed for autonomous agent operation

## Security Considerations

1. **No Credentials in Code**: Enforced by pre-commit hooks
2. **Boundary Isolation**: Agents cannot access other services' code
3. **Audit Trail**: All commits logged with agent attribution
4. **Manual Override**: Humans can always review and modify
5. **Test Validation**: Code must pass tests before committing

## Future Enhancements

Potential improvements for the auto-commit workflow:

- [ ] Integration with PR creation workflow
- [ ] Automatic semantic versioning
- [ ] Commit squashing for feature branches
- [ ] Integration with code review agents
- [ ] Metrics dashboard for agent commits
- [ ] Automated rollback on test failures
- [ ] Branch protection rule integration

## Support

For issues or questions about the auto-commit workflow:

1. Check the troubleshooting section above
2. Review logs in `.claude/logs/`
3. Examine git hooks in `.claude/hooks/`
4. Test scripts manually with verbose output
5. Consult the main CLAUDE.md documentation

---

**Version**: 1.0.0
**Last Updated**: September 13, 2025
**Status**: Active
**Compatibility**: Claude Code with local-first development (ADR-010)