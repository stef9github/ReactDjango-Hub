# AUTO-COMMIT INSTRUCTIONS FOR CLAUDE AGENTS

## Automated Commit Workflow

As a Claude Code agent, you are equipped with an automated commit workflow that ensures your successful work is committed to git with appropriate safety checks.

### When to Auto-Commit

You should automatically commit your work when:

1. **Feature Complete**: A feature or functionality is fully implemented and tested
2. **Bug Fixed**: A bug has been successfully resolved and verified
3. **Tests Pass**: All relevant tests are passing for your changes
4. **Documentation Updated**: Documentation changes are complete and reviewed
5. **Refactoring Done**: Code refactoring is complete without breaking functionality

### How to Use Auto-Commit

After completing a task successfully, use the auto-commit script:

```bash
# Basic usage
.claude/scripts/auto-commit.sh <agent-name> <commit-type> "<commit-message>"

# With test verification first
.claude/scripts/auto-commit.sh <agent-name> <commit-type> "<commit-message>" --test-first
```

#### Commit Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semi-colons, etc.)
- `refactor`: Code refactoring without changing functionality
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependency updates, etc.

### Example Workflows

#### Backend Agent Example
```bash
# After implementing a new API endpoint
.claude/scripts/auto-commit.sh backend feat "Add user profile API endpoint with validation" --test-first
```

#### Frontend Agent Example
```bash
# After fixing a UI bug
.claude/scripts/auto-commit.sh frontend fix "Resolve dropdown menu alignment issue on mobile" --test-first
```

#### Infrastructure Agent Example
```bash
# After updating Docker configuration
.claude/scripts/auto-commit.sh infrastructure chore "Update Docker compose for local development setup"
```

### Safety Checks

The auto-commit script performs these safety checks:

1. **Boundary Validation**: Ensures you only commit files within your agent's allowed directories
2. **Sensitive File Detection**: Prevents committing credentials, keys, or secrets
3. **Test Execution**: Runs relevant tests before committing (with --test-first flag)
4. **Staged Files Review**: Only commits files that have been properly staged
5. **Commit Message Formatting**: Ensures consistent commit message format

### Agent Boundaries

Each agent has specific boundaries for file modifications:

| Agent | Allowed Paths |
|-------|---------------|
| backend | `backend/**` |
| frontend | `frontend/**` |
| identity | `services/identity-service/**` |
| communication | `services/communication-service/**` |
| content | `services/content-service/**` |
| workflow | `services/workflow-service/**` |
| infrastructure | `infrastructure/**`, `docker/**`, `.github/**`, `kubernetes/**` |
| coordinator | `services/api-gateway/**`, `services/service-mesh/**` |
| documentation | `docs/**`, `*.md` |
| security | `.claude/security/**`, `security-configs/**` |

### Workflow Integration

1. **Development Phase**
   - Make changes within your boundary
   - Test locally to ensure functionality works
   - Review changes with `git diff`

2. **Pre-Commit Phase**
   - Run agent-specific tests
   - Validate no files outside boundary are modified
   - Check for sensitive information

3. **Commit Phase**
   - Use auto-commit script with appropriate parameters
   - Script validates all safety checks
   - Commit is created with proper attribution

4. **Post-Commit Phase**
   - Review commit with `git show HEAD`
   - Update task tracking if applicable
   - Continue with next task or handoff to another agent

### Best Practices

1. **Commit Frequently**: Make small, focused commits rather than large, complex ones
2. **Test First**: Always use `--test-first` flag for code changes
3. **Clear Messages**: Write descriptive commit messages that explain the "why"
4. **Review Changes**: Always review your changes before committing
5. **Stay in Boundary**: Never attempt to modify files outside your agent's scope

### Error Handling

If the auto-commit fails:

1. **Check Error Message**: The script provides detailed error messages
2. **Fix Issues**: Address any test failures or boundary violations
3. **Manual Review**: For complex cases, request human review
4. **Retry**: After fixing issues, retry the auto-commit

### Commit Log

All commits are logged to `.claude/logs/commits.log` for audit and tracking purposes.

### Manual Override

In special cases where auto-commit is not suitable:

```bash
# Stage specific files manually
git add <specific-files>

# Create commit with proper message format
git commit -m "type(agent): message

Agent: <agent-name>
Manual commit: Required due to <reason>

Generated with Claude Code (https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Integration with Local Development

Following ADR-010 (Local-First Development Strategy), the auto-commit workflow:

- Works with local file system directly
- No Docker/container complexity
- Immediate feedback on test results
- Fast iteration cycles
- Direct git operations without abstraction layers

This ensures maximum development velocity while maintaining code quality and safety.