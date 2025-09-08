#!/bin/bash
# Git commit script for frontend agent - only commits frontend files

set -e

# Ensure we're in the right directory
if [[ ! "$PWD" == *"frontend-dev"* ]]; then
    echo -e "\033[1;31m❌ Error: This script must be run from the frontend-dev worktree\033[0m"
    exit 1
fi

# Define frontend-specific paths
FRONTEND_PATHS=(
    "frontend/"
    "*.tsx"
    "*.ts"
    "*.jsx"
    "*.js"
    "*.css"
    "*.scss"
    "*.html"
    "package*.json"
    "vite.config.*"
    "tailwind.config.*"
    "tsconfig*.json"
    ".eslintrc*"
    ".prettierrc*"
    "docker/development/Dockerfile.frontend"
    "docker/production/Dockerfile.frontend"
    "docker/production/nginx-frontend.conf"
    ".env.frontend"
    "public/"
    "src/"
    "frontend/docs/"
)

echo -e "\033[1;35m🎨 Frontend Agent Git Commit\033[0m"
echo -e "\033[1;34m📁 Working in: $PWD\033[0m"

# Check git status
echo -e "\033[1;36m📊 Checking git status...\033[0m"
git status --porcelain

# Get all changed files
CHANGED_FILES=$(git status --porcelain | awk '{print $2}')

if [ -z "$CHANGED_FILES" ]; then
    echo -e "\033[1;33m⚠️  No changes to commit\033[0m"
    exit 0
fi

# Filter files to only include frontend-related paths
FRONTEND_FILES=""
for file in $CHANGED_FILES; do
    for pattern in "${FRONTEND_PATHS[@]}"; do
        if [[ "$file" == $pattern* ]] || [[ "$file" == *"$pattern"* ]]; then
            FRONTEND_FILES="$FRONTEND_FILES $file"
            break
        fi
    done
done

if [ -z "$FRONTEND_FILES" ]; then
    echo -e "\033[1;33m⚠️  No frontend files to commit\033[0m"
    echo -e "\033[1;33m    Changed files are not in frontend scope:\033[0m"
    for file in $CHANGED_FILES; do
        echo -e "\033[1;33m    - $file\033[0m"
    done
    exit 1
fi

echo -e "\033[1;32m✅ Frontend files to commit:\033[0m"
for file in $FRONTEND_FILES; do
    echo -e "\033[1;32m  + $file\033[0m"
done

# Add only frontend files
git add $FRONTEND_FILES

# Show diff of what will be committed
echo -e "\033[1;36m📝 Changes to be committed:\033[0m"
git diff --cached --stat

# Get commit message
if [ -z "$1" ]; then
    echo -e "\033[1;33m💬 Enter commit message:\033[0m"
    read -r commit_message
else
    commit_message="$1"
fi

# Commit with frontend agent signature
git commit -m "$(cat <<EOF
$commit_message

🤖 Generated with [Claude Code](https://claude.ai/code) - Frontend Agent

Co-Authored-By: Claude Frontend Agent <noreply@anthropic.com>
EOF
)"

echo -e "\033[1;32m✅ Frontend commit completed!\033[0m"