#!/bin/bash
# Setup agent-specific documentation directories

echo -e "\033[1;32m📚 Setting up agent-specific documentation structure...\033[0m"

# Create backend docs structure
echo -e "\033[1;34m🔧 Creating backend documentation structure...\033[0m"
mkdir -p backend/docs/{api,models,database,authentication,testing,deployment}

# Create frontend docs structure  
echo -e "\033[1;35m🎨 Creating frontend documentation structure...\033[0m"
mkdir -p frontend/docs/{components,pages,styling,routing,state-management,testing,deployment}

# Create worktree-specific docs
echo -e "\033[1;36m📁 Setting up worktree documentation...\033[0m"
if [ -d "../ReactDjango-Hub-worktrees/backend-dev" ]; then
    mkdir -p ../ReactDjango-Hub-worktrees/backend-dev/docs/{api,models,database,authentication,testing,deployment}
fi

if [ -d "../ReactDjango-Hub-worktrees/frontend-dev" ]; then
    mkdir -p ../ReactDjango-Hub-worktrees/frontend-dev/docs/{components,pages,styling,routing,state-management,testing,deployment}
fi

echo -e "\033[1;32m✅ Agent-specific documentation structure created!\033[0m"
echo -e "\033[1;33m📖 Documentation structure:\033[0m"
echo -e "\033[1;33m  📂 backend/docs/ - Backend agent documentation\033[0m"
echo -e "\033[1;33m  📂 frontend/docs/ - Frontend agent documentation\033[0m"
echo -e "\033[1;33m  📂 docs/ - Global project documentation\033[0m"