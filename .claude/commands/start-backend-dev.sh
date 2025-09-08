#!/bin/bash
# Start Claude Code instance for unified backend + API development
# Uses: Full-Stack Backend & API Agent (Django + DRF/Ninja + RGPD compliance)

echo "🔧 Starting Claude Code Backend + API Development Instance..."
echo "📁 Worktree: ../ReactDjango-Hub-worktrees/backend-dev"
echo "🎯 Agent Focus: Django Backend + REST APIs + RGPD Compliance + French Medical"

cd ../ReactDjango-Hub-worktrees/backend-dev

# Set environment for unified backend + API development
export CLAUDE_AGENT_FOCUS="backend-api"
export CLAUDE_PROJECT_TYPE="french-medical-fullstack-backend"

# Start Claude Code with unified backend + API agent context
claude "En tant qu'agent backend et API Django spécialisé pour le marché médical français (voir .claude/agents/backend-agent.md), je suis prêt à développer des modèles, migrations, sérialiseurs DRF, endpoints Ninja, et documentation API avec conformité RGPD et support trilingue FR/DE/EN. Comment puis-je vous aider aujourd'hui?"