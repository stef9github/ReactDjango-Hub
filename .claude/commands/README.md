# Claude Code Parallel Development Commands

This directory contains scripts to run multiple Claude Code instances simultaneously using git worktrees.

## 📁 Worktree Structure

```
ReactDjango-Hub/                    # Main repo (main branch)
├── .claude/agents/                 # Agent configurations
├── .claude/commands/              # This directory
└── ...

ReactDjango-Hub-worktrees/         # Parallel worktrees
├── backend-dev/                   # feature/backend-development
├── frontend-dev/                  # feature/frontend-development
└── api-dev/                      # feature/api-development
```

## 🚀 Available Commands

### Individual Agent Instances
```bash
# Start backend development instance
bash .claude/commands/start-backend-dev.sh

# Start frontend development instance  
bash .claude/commands/start-frontend-dev.sh

# Start API development instance
bash .claude/commands/start-api-dev.sh
```

### All Parallel Instances
```bash
# Start all instances in separate terminal tabs
bash .claude/commands/start-all-parallel.sh
```

## 🎯 Agent Specializations

| **Worktree** | **Branch** | **Agent Focus** | **Specialization** |
|--------------|------------|-----------------|-------------------|
| `backend-dev` | `feature/backend-development` | Backend Agent | Django + RGPD + French Medical |
| `frontend-dev` | `feature/frontend-development` | Frontend Agent | React + French-first UI + A11y |
| `api-dev` | `feature/api-development` | API Agent | REST + Trilingual Docs + Testing |

## 📋 Workflow

1. **Start Parallel Instances**: Run `bash .claude/commands/start-all-parallel.sh`
2. **Develop in Parallel**: Work on different features simultaneously
3. **Merge Changes**: Use git to merge branches back to main when ready

## 🔧 Git Worktree Management

```bash
# List all worktrees
git worktree list

# Remove a worktree (from main repo)
git worktree remove ../ReactDjango-Hub-worktrees/backend-dev

# Add new worktree
git worktree add ../ReactDjango-Hub-worktrees/new-feature feature/new-feature
```

## 🇫🇷 French Medical SaaS Context

All instances are configured for:
- **RGPD Compliance**: French data protection law
- **Trilingual Support**: French → German → English
- **Medical Terminology**: Surgical procedures and medical forms
- **CNIL Guidelines**: French healthcare data authority standards

Each agent maintains awareness of the French medical market requirements while working in their specialized domain.