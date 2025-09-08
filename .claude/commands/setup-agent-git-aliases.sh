#!/bin/bash
# Setup git aliases for each agent to enforce scoped commits

echo -e "\033[1;32m🔧 Setting up agent-specific git aliases...\033[0m"

# Backend worktree setup
if [ -d "../ReactDjango-Hub-worktrees/backend-dev" ]; then
    echo -e "\033[1;34m📁 Configuring backend-dev worktree...\033[0m"
    cd ../ReactDjango-Hub-worktrees/backend-dev
    
    # Set git config for backend agent
    git config user.name "Claude Backend Agent"
    git config user.email "backend-agent@claude.anthropic.com"
    
    # Create git aliases for scoped commits
    git config alias.backend-commit '!bash ../../ReactDjango-Hub/.claude/commands/git-commit-backend.sh'
    git config alias.bcommit '!bash ../../ReactDjango-Hub/.claude/commands/git-commit-backend.sh'
    
    echo -e "\033[1;32m  ✅ Backend aliases: git backend-commit, git bcommit\033[0m"
    cd - > /dev/null
fi

# Frontend worktree setup
if [ -d "../ReactDjango-Hub-worktrees/frontend-dev" ]; then
    echo -e "\033[1;34m📁 Configuring frontend-dev worktree...\033[0m"
    cd ../ReactDjango-Hub-worktrees/frontend-dev
    
    # Set git config for frontend agent
    git config user.name "Claude Frontend Agent"
    git config user.email "frontend-agent@claude.anthropic.com"
    
    # Create git aliases for scoped commits
    git config alias.frontend-commit '!bash ../../ReactDjango-Hub/.claude/commands/git-commit-frontend.sh'
    git config alias.fcommit '!bash ../../ReactDjango-Hub/.claude/commands/git-commit-frontend.sh'
    
    echo -e "\033[1;32m  ✅ Frontend aliases: git frontend-commit, git fcommit\033[0m"
    cd - > /dev/null
fi

echo -e "\033[1;32m🎯 Agent git aliases configured!\033[0m"
echo -e "\033[1;36mUsage:\033[0m"
echo -e "\033[1;36m  Backend: git bcommit \"commit message\"\033[0m"
echo -e "\033[1;36m  Frontend: git fcommit \"commit message\"\033[0m"