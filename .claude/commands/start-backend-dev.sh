#!/bin/bash
# Start Claude Code instance for backend development
# Uses: Backend Agent (Django + RGPD compliance)

echo "🔧 Starting Claude Code Backend Development Instance..."
echo "📁 Worktree: ../ReactDjango-Hub-worktrees/backend-dev"
echo "🎯 Agent Focus: Django Backend + RGPD Compliance + French Medical"

cd ../ReactDjango-Hub-worktrees/backend-dev

# Set environment for backend development
export CLAUDE_AGENT_FOCUS="backend"
export CLAUDE_PROJECT_TYPE="french-medical-backend"

# Start Claude Code with backend agent context
claude "En tant qu'agent backend Django spécialisé pour le marché médical français (voir .claude/agents/backend-agent.md), je suis prêt à développer des fonctionnalités backend avec conformité RGPD et support trilingue FR/DE/EN. Comment puis-je vous aider aujourd'hui?"