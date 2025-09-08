#!/bin/bash
# Test script to verify agent commit scoping works correctly

echo -e "\033[1;32m🧪 Testing Agent Commit Scoping\033[0m"

# Create test files in different directories
echo -e "\033[1;34m📝 Creating test files...\033[0m"

# Backend test files
mkdir -p backend/test_backend
echo "# Backend test file" > backend/test_backend/test.py
echo "Django==5.2.6" >> requirements.txt

# Frontend test files  
mkdir -p frontend/test_frontend
echo "// Frontend test file" > frontend/test_frontend/test.ts
echo '{"test": "frontend"}' > frontend/package.json

echo -e "\033[1;33m📊 Files created for testing:\033[0m"
ls -la backend/test_backend/
ls -la frontend/test_frontend/
echo ""

# Test backend commit script
echo -e "\033[1;32m🔧 Testing Backend Commit Scope...\033[0m"
cd ../ReactDjango-Hub-worktrees/backend-dev 2>/dev/null || echo "Backend worktree not found"
if [ $? -eq 0 ]; then
    echo "Backend files that would be committed:"
    bash ../../ReactDjango-Hub/.claude/commands/git-commit-backend.sh --dry-run 2>/dev/null || echo "No backend files to commit"
    cd - > /dev/null
fi

echo ""

# Test frontend commit script  
echo -e "\033[1;35m🎨 Testing Frontend Commit Scope...\033[0m"
cd ../ReactDjango-Hub-worktrees/frontend-dev 2>/dev/null || echo "Frontend worktree not found"
if [ $? -eq 0 ]; then
    echo "Frontend files that would be committed:"
    bash ../../ReactDjango-Hub/.claude/commands/git-commit-frontend.sh --dry-run 2>/dev/null || echo "No frontend files to commit"
    cd - > /dev/null
fi

echo -e "\033[1;32m✅ Agent commit scoping test completed!\033[0m"