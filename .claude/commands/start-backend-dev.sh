#!/bin/bash
# Start Claude Code instance for unified backend + API development
# Uses: Full-Stack Backend & API Agent (Django + DRF/Ninja + RGPD compliance)

# Set better terminal colors and environment
export TERM=xterm-256color
export CLICOLOR=1
export LSCOLORS=ExFxBxDxCxegedabagacad

echo -e "\033[1;32m🔧 Starting Claude Code Backend + API Development Instance...\033[0m"
echo -e "\033[1;34m📁 Worktree: ../ReactDjango-Hub-worktrees/backend-dev\033[0m"
echo -e "\033[1;36m🎯 Agent Focus: Django Backend + REST APIs + RGPD Compliance + French Medical\033[0m"

# Check if directory exists before changing to it
if [ ! -d "../ReactDjango-Hub-worktrees/backend-dev" ]; then
    echo -e "\033[1;31m❌ Error: Backend worktree directory not found!\033[0m"
    echo -e "\033[1;33m💡 Run 'git worktree add ../ReactDjango-Hub-worktrees/backend-dev main' first\033[0m"
    exit 1
fi

cd ../ReactDjango-Hub-worktrees/backend-dev || exit 1

# Set environment for unified backend + API development
export CLAUDE_AGENT_FOCUS="backend-api"
export CLAUDE_PROJECT_TYPE="french-medical-fullstack-backend"

# Start Claude Code with unified backend + API agent context
echo -e "\033[1;32m✨ Launching Claude Code...\033[0m"
claude "En tant qu'agent backend et API Django spécialisé pour le marché médical français (voir .claude/agents/backend-agent.md), je suis prêt à développer des modèles, migrations, sérialiseurs DRF, endpoints Ninja, et documentation API avec conformité RGPD et support trilingue FR/DE/EN. Comment puis-je vous aider aujourd'hui?"