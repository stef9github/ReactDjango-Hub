#!/usr/bin/env python3
"""
Pre-commit Hook Setup for Auth Service
Automatically runs organization checks before commits
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_pre_commit_hook():
    """Setup git pre-commit hook"""
    
    # Get git hooks directory
    git_dir = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True,
        text=True
    ).stdout.strip()
    
    if not git_dir:
        print("❌ Not in a git repository")
        return False
    
    hooks_dir = Path(git_dir) / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    
    pre_commit_hook = hooks_dir / "pre-commit"
    
    hook_content = '''#!/bin/bash
#
# Auth Service Pre-commit Hook
# Runs organization checks before allowing commits
#

echo "🔧 Running Auth Service organization checks..."

# Run organization maintenance script
python3 scripts/maintain_organization.py

exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo ""
    echo "❌ Organization checks failed!"
    echo "💡 Run 'python3 scripts/maintain_organization.py --fix' to auto-fix issues"
    echo "   Or use 'git commit --no-verify' to bypass checks"
    exit 1
fi

echo "✅ Organization checks passed!"
exit 0
'''
    
    # Write hook
    with open(pre_commit_hook, 'w') as f:
        f.write(hook_content)
    
    # Make executable
    os.chmod(pre_commit_hook, 0o755)
    
    print(f"✅ Pre-commit hook installed: {pre_commit_hook}")
    return True

def create_makefile_targets():
    """Add organization targets to Makefile"""
    
    makefile_content = '''
# Auth Service Organization Maintenance
.PHONY: check-org fix-org report-org setup-hooks

check-org:
	@echo "🔧 Checking auth service organization..."
	@python3 scripts/maintain_organization.py

fix-org:
	@echo "🔧 Auto-fixing organization issues..."
	@python3 scripts/maintain_organization.py --fix

report-org:
	@echo "📄 Generating organization report..."
	@python3 scripts/maintain_organization.py --report

setup-hooks:
	@echo "⚙️  Setting up git hooks..."
	@python3 scripts/setup_pre_commit.py

# Run before commits
pre-commit: check-org
	@echo "✅ Ready to commit!"

# Development workflow
dev-setup: setup-hooks
	@echo "🚀 Development environment setup complete!"
'''
    
    makefile_path = Path("Makefile.auth")
    
    with open(makefile_path, 'w') as f:
        f.write(makefile_content)
    
    print(f"✅ Makefile targets created: {makefile_path}")
    print("\n📖 Usage:")
    print("  make -f Makefile.auth check-org    # Check organization")
    print("  make -f Makefile.auth fix-org      # Auto-fix issues") 
    print("  make -f Makefile.auth report-org   # Generate report")
    print("  make -f Makefile.auth setup-hooks  # Setup git hooks")

def create_github_workflow():
    """Create GitHub Actions workflow for organization checks"""
    
    workflow_dir = Path(".github/workflows")
    workflow_dir.mkdir(parents=True, exist_ok=True)
    
    workflow_content = '''name: Auth Service Organization Check

on:
  push:
    paths:
      - 'services/auth-service/**'
  pull_request:
    paths:
      - 'services/auth-service/**'

jobs:
  organization-check:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      working-directory: services/auth-service
      run: |
        pip install -r requirements.txt
    
    - name: Run organization check
      working-directory: services/auth-service
      run: |
        python3 scripts/maintain_organization.py
    
    - name: Generate organization report
      if: failure()
      working-directory: services/auth-service
      run: |
        python3 scripts/maintain_organization.py --report
    
    - name: Upload organization report
      if: failure()
      uses: actions/upload-artifact@v3
      with:
        name: organization-report
        path: services/auth-service/ORGANIZATION_REPORT.md
'''
    
    workflow_path = workflow_dir / "auth-service-organization.yml"
    
    with open(workflow_path, 'w') as f:
        f.write(workflow_content)
    
    print(f"✅ GitHub workflow created: {workflow_path}")

def create_vscode_tasks():
    """Create VSCode tasks for organization maintenance"""
    
    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)
    
    tasks_content = '''{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Auth: Check Organization",
            "type": "shell",
            "command": "python3",
            "args": ["scripts/maintain_organization.py"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "options": {
                "cwd": "${workspaceFolder}/services/auth-service"
            },
            "problemMatcher": []
        },
        {
            "label": "Auth: Fix Organization",
            "type": "shell", 
            "command": "python3",
            "args": ["scripts/maintain_organization.py", "--fix"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "options": {
                "cwd": "${workspaceFolder}/services/auth-service"
            },
            "problemMatcher": []
        },
        {
            "label": "Auth: Generate Report",
            "type": "shell",
            "command": "python3", 
            "args": ["scripts/maintain_organization.py", "--report"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "options": {
                "cwd": "${workspaceFolder}/services/auth-service"
            },
            "problemMatcher": []
        }
    ]
}'''
    
    tasks_path = vscode_dir / "tasks.json"
    
    # Read existing tasks or create new
    existing_tasks = {}
    if tasks_path.exists():
        import json
        with open(tasks_path, 'r') as f:
            existing_tasks = json.load(f)
    
    # Merge with auth service tasks
    import json
    new_tasks = json.loads(tasks_content)
    
    if "tasks" in existing_tasks:
        existing_tasks["tasks"].extend(new_tasks["tasks"])
    else:
        existing_tasks = new_tasks
    
    with open(tasks_path, 'w') as f:
        json.dump(existing_tasks, f, indent=2)
    
    print(f"✅ VSCode tasks updated: {tasks_path}")

def main():
    """Main setup function"""
    print("🚀 Setting up Auth Service organization maintenance...")
    
    # Setup pre-commit hook
    setup_pre_commit_hook()
    
    # Create Makefile targets
    create_makefile_targets()
    
    # Create GitHub workflow
    create_github_workflow()
    
    # Create VSCode tasks
    create_vscode_tasks()
    
    print("\n✨ Organization maintenance setup complete!")
    print("\n📖 Next steps:")
    print("1. Run: python3 scripts/maintain_organization.py --fix")
    print("2. Test: make -f Makefile.auth check-org")
    print("3. Commit changes to activate pre-commit hooks")

if __name__ == "__main__":
    main()