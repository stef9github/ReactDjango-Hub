#!/bin/bash
# Start Claude Code instance for frontend development
# Uses: Frontend Agent (React + French-first UI)

echo "🎨 Starting Claude Code Frontend Development Instance..."
echo "📁 Worktree: ../ReactDjango-Hub-worktrees/frontend-dev"
echo "🎯 Agent Focus: React Frontend + French-first UI + Accessibility"

cd ../ReactDjango-Hub-worktrees/frontend-dev

# Set environment for frontend development
export CLAUDE_AGENT_FOCUS="frontend"
export CLAUDE_PROJECT_TYPE="french-medical-frontend"

# Start Claude Code with frontend agent context
claude "En tant qu'agent frontend React spécialisé pour le marché médical français (voir .claude/agents/frontend-agent.md), je suis prêt à créer des interfaces utilisateur français-première avec traduction automatique vers l'allemand et l'anglais. Comment puis-je vous aider aujourd'hui?"