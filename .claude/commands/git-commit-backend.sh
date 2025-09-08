#!/bin/bash
# Git commit script for backend agent - only commits backend files

set -e

# Ensure we're in the right directory
if [[ ! "$PWD" == *"backend-dev"* ]]; then
    echo -e "\033[1;31m❌ Error: This script must be run from the backend-dev worktree\033[0m"
    exit 1
fi

# Define backend-specific paths
BACKEND_PATHS=(
    "backend/"
    "*.py"
    "requirements*.txt"
    "manage.py"
    "pyproject.toml"
    "poetry.lock"
    ".python-version"
    "docker/development/Dockerfile.backend"
    "docker/production/Dockerfile.backend"
    "docker/development/docker-compose.yml"
    "docker/production/docker-compose.yml"
    "docker/production/nginx.conf"
    "docker/.env*"
    "docker/docker-manager.sh"
    ".env.backend"
    "backend/docs/"
)

echo -e "\033[1;32m🔧 Backend Agent Git Commit\033[0m"
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

# Filter files to only include backend-related paths
BACKEND_FILES=""
for file in $CHANGED_FILES; do
    for pattern in "${BACKEND_PATHS[@]}"; do
        if [[ "$file" == $pattern* ]] || [[ "$file" == *"$pattern"* ]]; then
            BACKEND_FILES="$BACKEND_FILES $file"
            break
        fi
    done
done

if [ -z "$BACKEND_FILES" ]; then
    echo -e "\033[1;33m⚠️  No backend files to commit\033[0m"
    echo -e "\033[1;33m    Changed files are not in backend scope:\033[0m"
    for file in $CHANGED_FILES; do
        echo -e "\033[1;33m    - $file\033[0m"
    done
    exit 1
fi

echo -e "\033[1;32m✅ Backend files to commit:\033[0m"
for file in $BACKEND_FILES; do
    echo -e "\033[1;32m  + $file\033[0m"
done

# Add only backend files
git add $BACKEND_FILES

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

# Commit with backend agent signature
git commit -m "$(cat <<EOF
$commit_message

🤖 Generated with [Claude Code](https://claude.ai/code) - Backend Agent

Co-Authored-By: Claude Backend Agent <noreply@anthropic.com>
EOF
)"

echo -e "\033[1;32m✅ Backend commit completed!\033[0m"