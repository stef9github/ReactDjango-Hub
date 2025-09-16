#!/bin/bash

# =============================================================================
# GIT HOOKS INSTALLER FOR CLAUDE CODE AGENTS
# =============================================================================
# This script installs git hooks for automated safety checks
#
# Usage: ./install-hooks.sh
# =============================================================================

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
CLAUDE_HOOKS_DIR="$SCRIPT_DIR/../hooks"

echo -e "${GREEN}Installing Claude Code git hooks...${NC}"

# Create hooks directory in .claude if it doesn't exist
mkdir -p "$CLAUDE_HOOKS_DIR"

# =============================================================================
# CREATE PRE-COMMIT HOOK
# =============================================================================

cat > "$CLAUDE_HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash

# Claude Code Pre-Commit Hook
# Performs safety checks before allowing commits

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Running Claude Code pre-commit checks...${NC}"

# Check for sensitive files
sensitive_patterns=(
    "*.key"
    "*.pem"
    "*.p12"
    ".env"
    ".env.*"
    "secrets.json"
    "credentials.json"
    "*_rsa"
    "*_dsa"
)

staged_files=$(git diff --cached --name-only)

for file in $staged_files; do
    for pattern in "${sensitive_patterns[@]}"; do
        if [[ "$file" == $pattern ]]; then
            echo -e "${RED}ERROR: Attempting to commit sensitive file: $file${NC}"
            echo "Please remove this file from staging and add it to .gitignore"
            exit 1
        fi
    done
    
    # Check file content for common secret patterns
    if [ -f "$file" ]; then
        if grep -qE "(api[_-]?key|secret[_-]?key|password|token).*=.*['\"].*['\"]" "$file" 2>/dev/null; then
            echo -e "${YELLOW}WARNING: File $file may contain sensitive information${NC}"
            echo "Please review the file content before committing"
            
            # Show the potentially sensitive lines
            grep -nE "(api[_-]?key|secret[_-]?key|password|token).*=.*['\"].*['\"]" "$file" 2>/dev/null || true
            
            read -p "Continue with commit? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
done

# Check for large files (>10MB)
for file in $staged_files; do
    if [ -f "$file" ]; then
        file_size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
        if [ "$file_size" -gt 10485760 ]; then
            echo -e "${YELLOW}WARNING: Large file detected: $file ($(( file_size / 1048576 ))MB)${NC}"
            read -p "Continue with commit? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
done

# Check for merge conflict markers
for file in $staged_files; do
    if [ -f "$file" ]; then
        if grep -qE "^(<<<<<<<|=======|>>>>>>>)" "$file" 2>/dev/null; then
            echo -e "${RED}ERROR: Merge conflict markers found in: $file${NC}"
            exit 1
        fi
    fi
done

echo -e "${GREEN}Pre-commit checks passed${NC}"
exit 0
EOF

# =============================================================================
# CREATE COMMIT-MSG HOOK
# =============================================================================

cat > "$CLAUDE_HOOKS_DIR/commit-msg" << 'EOF'
#!/bin/bash

# Claude Code Commit Message Hook
# Validates and enhances commit messages

# Color codes
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

commit_msg_file=$1
commit_msg=$(cat "$commit_msg_file")

# Check if commit message follows conventional format
if ! echo "$commit_msg" | grep -qE "^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+"; then
    echo -e "${YELLOW}WARNING: Commit message doesn't follow conventional format${NC}"
    echo "Expected format: type(scope): description"
    echo "Types: feat, fix, docs, style, refactor, test, chore"
fi

# Add Claude Code attribution if not present
if ! echo "$commit_msg" | grep -q "Claude Code"; then
    echo "" >> "$commit_msg_file"
    echo "Generated with Claude Code (https://claude.ai/code)" >> "$commit_msg_file"
    echo "Co-Authored-By: Claude <noreply@anthropic.com>" >> "$commit_msg_file"
fi

echo -e "${GREEN}Commit message validated${NC}"
exit 0
EOF

# =============================================================================
# CREATE PRE-PUSH HOOK
# =============================================================================

cat > "$CLAUDE_HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash

# Claude Code Pre-Push Hook
# Final checks before pushing to remote

# Color codes
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${YELLOW}Running pre-push checks...${NC}"

# Get the remote and branch
remote="$1"
url="$2"

# Check if pushing to main/master branch
while read local_ref local_sha remote_ref remote_sha; do
    if [[ "$remote_ref" == "refs/heads/main" ]] || [[ "$remote_ref" == "refs/heads/master" ]]; then
        echo -e "${YELLOW}WARNING: Pushing directly to main/master branch${NC}"
        echo "Consider creating a feature branch instead"
        read -p "Continue with push? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
done

echo -e "${GREEN}Pre-push checks passed${NC}"
exit 0
EOF

# =============================================================================
# INSTALL HOOKS
# =============================================================================

# Make hooks executable
chmod +x "$CLAUDE_HOOKS_DIR/pre-commit"
chmod +x "$CLAUDE_HOOKS_DIR/commit-msg"
chmod +x "$CLAUDE_HOOKS_DIR/pre-push"

# Backup existing hooks if they exist
for hook in pre-commit commit-msg pre-push; do
    if [ -f "$GIT_HOOKS_DIR/$hook" ] && [ ! -L "$GIT_HOOKS_DIR/$hook" ]; then
        echo -e "${YELLOW}Backing up existing $hook hook to $hook.backup${NC}"
        mv "$GIT_HOOKS_DIR/$hook" "$GIT_HOOKS_DIR/$hook.backup"
    fi
done

# Create symlinks to our hooks
ln -sf "$CLAUDE_HOOKS_DIR/pre-commit" "$GIT_HOOKS_DIR/pre-commit"
ln -sf "$CLAUDE_HOOKS_DIR/commit-msg" "$GIT_HOOKS_DIR/commit-msg"
ln -sf "$CLAUDE_HOOKS_DIR/pre-push" "$GIT_HOOKS_DIR/pre-push"

echo -e "${GREEN}✓ Git hooks installed successfully!${NC}"
echo ""
echo "Installed hooks:"
echo "  - pre-commit: Checks for sensitive files and patterns"
echo "  - commit-msg: Validates commit message format"
echo "  - pre-push: Warns about pushing to main/master"
echo ""
echo "To uninstall, run: $0 --uninstall"

# Handle uninstall option
if [ "$1" == "--uninstall" ]; then
    echo -e "${YELLOW}Uninstalling Claude Code git hooks...${NC}"
    
    rm -f "$GIT_HOOKS_DIR/pre-commit"
    rm -f "$GIT_HOOKS_DIR/commit-msg"
    rm -f "$GIT_HOOKS_DIR/pre-push"
    
    # Restore backups if they exist
    for hook in pre-commit commit-msg pre-push; do
        if [ -f "$GIT_HOOKS_DIR/$hook.backup" ]; then
            mv "$GIT_HOOKS_DIR/$hook.backup" "$GIT_HOOKS_DIR/$hook"
            echo "Restored original $hook hook"
        fi
    done
    
    echo -e "${GREEN}Git hooks uninstalled${NC}"
fi