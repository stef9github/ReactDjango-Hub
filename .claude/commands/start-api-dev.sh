#!/bin/bash
# Start Claude Code instance for API development
# Uses: API Agent (REST + trilingual docs)

echo "🔌 Starting Claude Code API Development Instance..."
echo "📁 Worktree: ../ReactDjango-Hub-worktrees/api-dev"
echo "🎯 Agent Focus: REST APIs + OpenAPI Docs + Testing"

cd ../ReactDjango-Hub-worktrees/api-dev

# Set environment for API development
export CLAUDE_AGENT_FOCUS="api"
export CLAUDE_PROJECT_TYPE="french-medical-api"

# Start Claude Code with API agent context
claude "En tant qu'agent API spécialisé pour le marché médical français (voir .claude/agents/api-agent.md), je suis prêt à développer des APIs REST avec documentation trilingue et tests complets. Comment puis-je vous aider aujourd'hui?"