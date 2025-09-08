#!/bin/bash
# Start Claude Code instance for frontend development
# Uses: Frontend Agent (React + French-first UI)

# Set better terminal colors and environment
export TERM=xterm-256color
export CLICOLOR=1
export LSCOLORS=ExFxBxDxCxegedabagacad

echo -e "\033[1;35m🎨 Starting Claude Code Frontend Development Instance...\033[0m"
echo -e "\033[1;34m📁 Worktree: ../ReactDjango-Hub-worktrees/frontend-dev\033[0m"
echo -e "\033[1;36m🎯 Agent Focus: React Frontend + French-first UI + Accessibility\033[0m"

# Check if directory exists before changing to it
if [ ! -d "../ReactDjango-Hub-worktrees/frontend-dev" ]; then
    echo -e "\033[1;31m❌ Error: Frontend worktree directory not found!\033[0m"
    echo -e "\033[1;33m💡 Run 'git worktree add ../ReactDjango-Hub-worktrees/frontend-dev main' first\033[0m"
    exit 1
fi

cd ../ReactDjango-Hub-worktrees/frontend-dev || exit 1

# Set environment for frontend development
export CLAUDE_AGENT_FOCUS="frontend"
export CLAUDE_PROJECT_TYPE="french-medical-frontend"

# Setup git config and aliases for frontend agent
git config user.name "Claude Frontend Agent" 2>/dev/null || true
git config user.email "frontend-agent@claude.anthropic.com" 2>/dev/null || true
git config alias.fcommit '!bash ../../ReactDjango-Hub/.claude/commands/git-commit-frontend.sh' 2>/dev/null || true

# Start Claude Code with frontend agent context
echo -e "\033[1;32m✨ Launching Claude Code...\033[0m"
echo -e "\033[1;33m💡 Use 'git fcommit \"message\"' to commit only frontend files\033[0m"
echo -e "\033[1;36m📚 API Integration Guide: frontend/docs/api/README.md\033[0m"
echo -e "\033[1;36m📚 Backend API Spec: ../../ReactDjango-Hub/backend/docs/api/README.md\033[0m"
claude "En tant qu'agent frontend React spécialisé pour le marché médical français (voir .claude/agents/frontend-agent.md), je suis prêt à créer des interfaces utilisateur français-première avec traduction automatique vers l'allemand et l'anglais. Comment puis-je vous aider aujourd'hui?"