#!/usr/bin/env python3
"""
Agent Configuration Manager for ReactDjango-Hub
Manages specialized Claude agents for different aspects of the project
"""

import os
import json
import yaml
import argparse
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class AgentType(Enum):
    """Available agent specializations"""
    BACKEND = "backend"
    FRONTEND = "frontend"
    IDENTITY = "identity"
    CONTENT = "content"
    COMMUNICATION = "communication"
    WORKFLOW = "workflow"
    INFRASTRUCTURE = "infrastructure"
    TESTING = "testing"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    CLAUDE_CODE_EXPERT = "claude-code-expert"


@dataclass
class AgentConfig:
    """Agent configuration structure"""
    name: str
    type: AgentType
    description: str
    workdir: str
    permissions: Dict[str, List[str]]
    tools: List[str]
    restrictions: List[str]
    git_worktree: Optional[str] = None
    environment: Dict[str, str] = None
    aliases: Dict[str, str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for YAML/JSON export"""
        config = asdict(self)
        config['type'] = self.type.value
        return config


class AgentConfigurator:
    """Main agent configuration manager"""
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path.cwd()
        self.claude_dir = self.base_path / ".claude"
        self.agents_dir = self.claude_dir / "agents"
        self.templates_dir = self.agents_dir / "templates"
        self.configs_dir = self.agents_dir / "configs"
        self.scripts_dir = self.agents_dir / "scripts"
        self.services_dir = self.base_path / "services"
        
        # Ensure directories exist
        for dir_path in [self.templates_dir, self.configs_dir, self.scripts_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Migrate service configurations if they exist
        self._migrate_service_configs()
    
    def create_agent_templates(self):
        """Create default agent configuration templates"""
        
        templates = {
            AgentType.BACKEND: {
                "name": "Backend Django Agent",
                "description": "Specializes in Django backend development, APIs, and database operations",
                "workdir": "backend",
                "permissions": {
                    "read": ["backend/**", "docs/**", "CLAUDE.md"],
                    "write": ["backend/**"],
                    "execute": ["python", "pip", "django-admin", "pytest"]
                },
                "tools": ["Bash", "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob"],
                "restrictions": [
                    "Cannot modify frontend code",
                    "Cannot modify infrastructure without approval",
                    "Must follow Django best practices"
                ],
                "git_worktree": "backend-dev",
                "environment": {
                    "DJANGO_SETTINGS_MODULE": "config.settings.development",
                    "PYTHONPATH": "${workdir}"
                },
                "aliases": {
                    "migrate": "python manage.py migrate",
                    "test": "python manage.py test",
                    "shell": "python manage.py shell"
                }
            },
            
            AgentType.FRONTEND: {
                "name": "Frontend React Agent",
                "description": "Specializes in React, TypeScript, Vite, and UI/UX development",
                "workdir": "frontend",
                "permissions": {
                    "read": ["frontend/**", "docs/**", "CLAUDE.md"],
                    "write": ["frontend/**"],
                    "execute": ["npm", "node", "vite", "jest", "vitest"]
                },
                "tools": ["Bash", "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob"],
                "restrictions": [
                    "Cannot modify backend code",
                    "Cannot modify API endpoints",
                    "Must follow React best practices"
                ],
                "git_worktree": "frontend-dev",
                "environment": {
                    "NODE_ENV": "development"
                },
                "aliases": {
                    "dev": "npm run dev",
                    "build": "npm run build",
                    "test": "npm test",
                    "lint": "npm run lint"
                }
            },
            
            AgentType.IDENTITY: {
                "name": "Identity Service Agent",
                "description": "Manages authentication, authorization, MFA, and user management",
                "workdir": "services/identity-service",
                "permissions": {
                    "read": ["services/identity-service/**", "docs/**", "CLAUDE.md"],
                    "write": ["services/identity-service/**"],
                    "execute": ["python", "pip", "alembic", "pytest", "uvicorn"]
                },
                "tools": ["Bash", "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob"],
                "restrictions": [
                    "Cannot modify other services directly",
                    "Must maintain HIPAA/RGPD compliance",
                    "Must follow security best practices"
                ],
                "environment": {
                    "SERVICE_NAME": "identity-service",
                    "PORT": "8001"
                },
                "aliases": {
                    "run": "python main.py",
                    "test": "pytest",
                    "migrate": "alembic upgrade head"
                }
            },
            
            AgentType.CONTENT: {
                "name": "Content Service Agent",
                "description": "Manages document processing, file storage, and content management",
                "workdir": "services/content-service",
                "permissions": {
                    "read": ["services/content-service/**", "docs/**", "CLAUDE.md"],
                    "write": ["services/content-service/**"],
                    "execute": ["python", "pip", "pytest"]
                },
                "tools": ["Bash", "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob"],
                "restrictions": [
                    "Cannot modify other services directly",
                    "Must handle file uploads securely",
                    "Must follow data retention policies"
                ],
                "environment": {
                    "SERVICE_NAME": "content-service",
                    "PORT": "8002"
                },
                "aliases": {
                    "run": "python main.py",
                    "test": "pytest"
                }
            },
            
            AgentType.COMMUNICATION: {
                "name": "Communication Service Agent",
                "description": "Handles notifications, emails, SMS, and messaging",
                "workdir": "services/communication-service",
                "permissions": {
                    "read": ["services/communication-service/**", "docs/**", "CLAUDE.md"],
                    "write": ["services/communication-service/**"],
                    "execute": ["python", "pip", "pytest"]
                },
                "tools": ["Bash", "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob"],
                "restrictions": [
                    "Cannot modify other services directly",
                    "Must handle PII securely in communications",
                    "Must respect communication preferences"
                ],
                "environment": {
                    "SERVICE_NAME": "communication-service",
                    "PORT": "8003"
                },
                "aliases": {
                    "run": "python main.py",
                    "test": "pytest"
                }
            },
            
            AgentType.WORKFLOW: {
                "name": "Workflow Intelligence Agent",
                "description": "Manages workflow automation, business rules, and process intelligence",
                "workdir": "services/workflow-intelligence-service",
                "permissions": {
                    "read": ["services/workflow-intelligence-service/**", "docs/**", "CLAUDE.md"],
                    "write": ["services/workflow-intelligence-service/**"],
                    "execute": ["python", "pip", "pytest"]
                },
                "tools": ["Bash", "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob"],
                "restrictions": [
                    "Cannot modify other services directly",
                    "Must validate business rules",
                    "Must maintain audit trails"
                ],
                "environment": {
                    "SERVICE_NAME": "workflow-intelligence-service",
                    "PORT": "8004"
                },
                "aliases": {
                    "run": "python main.py",
                    "test": "pytest"
                }
            },
            
            AgentType.TESTING: {
                "name": "Testing Specialist Agent",
                "description": "Focuses on test creation, coverage, CI/CD, and quality assurance",
                "workdir": ".",
                "permissions": {
                    "read": ["**"],
                    "write": ["**/tests/**", "**/test_*.py", "**/*.test.js", "**/*.spec.ts"],
                    "execute": ["pytest", "jest", "vitest", "coverage", "npm", "python"]
                },
                "tools": ["Bash", "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob"],
                "restrictions": [
                    "Should not modify business logic",
                    "Focus on test coverage and quality"
                ],
                "environment": {
                    "TESTING": "true"
                },
                "aliases": {
                    "test-all": "make test",
                    "coverage": "make coverage"
                }
            },
            
            AgentType.INFRASTRUCTURE: {
                "name": "Infrastructure Agent",
                "description": "Manages Docker, Kubernetes, CI/CD, and deployment configurations",
                "workdir": ".",
                "permissions": {
                    "read": ["**"],
                    "write": ["docker/**", "kubernetes/**", ".github/**", "Makefile", "docker-compose*.yml"],
                    "execute": ["docker", "docker-compose", "kubectl", "make"]
                },
                "tools": ["Bash", "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob"],
                "restrictions": [
                    "Cannot modify application code",
                    "Must follow infrastructure as code principles"
                ],
                "environment": {
                    "ENVIRONMENT": "development"
                },
                "aliases": {
                    "up": "docker-compose up -d",
                    "down": "docker-compose down",
                    "logs": "docker-compose logs -f"
                }
            },
            
            AgentType.SECURITY: {
                "name": "Security Agent",
                "description": "Focuses on security audits, HIPAA/RGPD compliance, and vulnerability scanning",
                "workdir": ".",
                "permissions": {
                    "read": ["**"],
                    "write": ["docs/security/**", "**/security.py", "**/auth*.py"],
                    "execute": ["bandit", "safety", "pip-audit", "npm audit"]
                },
                "tools": ["Bash", "Read", "Write", "Edit", "Grep", "Glob", "WebSearch"],
                "restrictions": [
                    "Must prioritize security over features",
                    "Cannot disable security features",
                    "Must maintain compliance standards"
                ],
                "environment": {
                    "SECURITY_SCAN": "true"
                },
                "aliases": {
                    "audit": "make security-audit",
                    "scan": "make vulnerability-scan"
                }
            },
            
            AgentType.CLAUDE_CODE_EXPERT: {
                "name": "Claude Code Expert Agent",
                "description": "Claude Code optimization specialist for agent configuration, workflow automation, and development efficiency",
                "workdir": ".",
                "permissions": {
                    "read": ["**"],
                    "write": [
                        ".claude/**",
                        "**/.claude/**", 
                        "**/CLAUDE.md",
                        "launch_agent.sh",
                        "**/*.sh",
                        "**/*.py",
                        "Makefile",
                        "docker-compose*.yml",
                        ".github/**",
                        "docs/**"
                    ],
                    "execute": [
                        "python", "pip", "npm", "node", "git", "docker", "docker-compose", 
                        "make", "bash", "chmod", "find", "grep", "sed", "awk"
                    ]
                },
                "tools": [
                    "Bash", "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob", 
                    "Task", "WebSearch", "WebFetch", "TodoWrite"
                ],
                "restrictions": [
                    "Focus on optimization and efficiency improvements",
                    "Must maintain backward compatibility",
                    "Should document all configuration changes",
                    "Must test configurations before deployment"
                ],
                "git_worktree": "claude-code-expert-dev",
                "environment": {
                    "CLAUDE_CODE_EXPERT": "true",
                    "OPTIMIZATION_MODE": "enabled",
                    "PYTHONPATH": "."
                },
                "aliases": {
                    "configure": "python .claude/agent_configurator.py",
                    "launch": "./launch_agent.sh",
                    "optimize": "python .claude/agent_configurator.py optimize",
                    "validate-all": "python .claude/agent_configurator.py validate-all",
                    "agent-status": "python .claude/agent_configurator.py status",
                    "create-agent": "python .claude/agent_configurator.py create",
                    "lint-configs": "python .claude/agent_configurator.py lint",
                    "backup-configs": "python .claude/agent_configurator.py backup"
                },
                "specializations": [
                    "Agent configuration optimization",
                    "Workflow automation and scripting", 
                    "Development environment setup",
                    "CI/CD pipeline optimization",
                    "Git workflow management",
                    "Docker and containerization",
                    "Claude Code best practices",
                    "Performance monitoring and profiling",
                    "Code quality and linting setup",
                    "Documentation automation"
                ]
            }
        }
        
        # Save each template
        for agent_type, config in templates.items():
            template_path = self.templates_dir / f"{agent_type.value}.yaml"
            with open(template_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        return templates
    
    def load_agent_config(self, agent_type: str) -> Optional[Dict]:
        """Load an agent configuration"""
        config_path = self.configs_dir / f"{agent_type}.yaml"
        if not config_path.exists():
            # Try loading from templates
            template_path = self.templates_dir / f"{agent_type}.yaml"
            if template_path.exists():
                with open(template_path, 'r') as f:
                    return yaml.safe_load(f)
        else:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return None
    
    def save_agent_config(self, agent_type: str, config: Dict):
        """Save an agent configuration"""
        config_path = self.configs_dir / f"{agent_type}.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    def setup_git_worktree(self, agent_type: str, branch_name: str = None):
        """Setup git worktree for an agent"""
        config = self.load_agent_config(agent_type)
        if not config:
            raise ValueError(f"No configuration found for agent type: {agent_type}")
        
        worktree_name = config.get('git_worktree', f"{agent_type}-dev")
        branch_name = branch_name or worktree_name
        worktree_path = self.base_path.parent / f"{self.base_path.name}-worktrees" / worktree_name
        
        # Check if worktree exists
        result = subprocess.run(["git", "worktree", "list"], capture_output=True, text=True)
        if str(worktree_path) in result.stdout:
            print(f"Worktree already exists at {worktree_path}")
            return worktree_path
        
        # Create worktree
        subprocess.run([
            "git", "worktree", "add", 
            "-b", branch_name,
            str(worktree_path),
            "main"
        ], check=True)
        
        print(f"Created git worktree at {worktree_path}")
        return worktree_path
    
    def generate_launch_script(self, agent_type: str) -> Path:
        """Generate a launch script for an agent"""
        config = self.load_agent_config(agent_type)
        if not config:
            raise ValueError(f"No configuration found for agent type: {agent_type}")
        
        script_path = self.scripts_dir / f"launch_{agent_type}.sh"
        
        script_content = f'''#!/bin/bash
# Launch script for {config.get('name', agent_type)}
# Generated by Agent Configurator

set -e

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

echo -e "${{GREEN}}🚀 Launching {config.get('name', agent_type)}${{NC}}"
echo -e "${{YELLOW}}{config.get('description', '')}${{NC}}"
echo ""

# Set working directory
WORKDIR="{config.get('workdir', '.')}"
cd "$(dirname "$0")/../../../$WORKDIR"

# Export environment variables
'''
        
        # Add environment variables
        if config.get('environment'):
            for key, value in config['environment'].items():
                script_content += f'export {key}="{value}"\n'
        
        script_content += '''
# Display agent information
echo "📁 Working Directory: $(pwd)"
echo "🔧 Available Tools: {tools}"
echo ""

# Display permissions
echo "📝 Permissions:"
echo "  Read: {read_perms}"
echo "  Write: {write_perms}"
echo "  Execute: {execute_perms}"
echo ""

# Display restrictions
echo "⚠️  Restrictions:"
'''.format(
            tools=', '.join(config.get('tools', [])),
            read_perms=', '.join(config.get('permissions', {}).get('read', [])[:3]) + '...',
            write_perms=', '.join(config.get('permissions', {}).get('write', [])[:3]) + '...',
            execute_perms=', '.join(config.get('permissions', {}).get('execute', [])[:3]) + '...'
        )
        
        for restriction in config.get('restrictions', []):
            script_content += f'echo "  - {restriction}"\n'
        
        script_content += '''
echo ""

# Display available aliases
echo "🔗 Available Aliases:"
'''
        
        if config.get('aliases'):
            for alias, command in config['aliases'].items():
                script_content += f'echo "  {alias}: {command}"\n'
        
        script_content += '''
echo ""
echo -e "${GREEN}✅ Agent is configured and ready!${NC}"
echo ""
echo "You can now start working with this specialized agent configuration."
echo "All operations will be scoped to the defined permissions and restrictions."
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        script_path.chmod(0o755)
        
        return script_path
    
    def create_master_config(self):
        """Create the master configuration file"""
        master_config = {
            "version": "1.0.0",
            "project": "ReactDjango-Hub Medical",
            "description": "Agent configuration system for specialized Claude assistants",
            "agents": {
                agent_type.value: {
                    "enabled": True,
                    "template": f"templates/{agent_type.value}.yaml",
                    "config": f"configs/{agent_type.value}.yaml"
                }
                for agent_type in AgentType
            },
            "global_settings": {
                "audit_logging": True,
                "compliance": ["HIPAA", "RGPD"],
                "default_branch": "main",
                "worktree_base": "../ReactDjango-Hub-worktrees"
            },
            "communication": {
                "protocol": "file-based",
                "shared_directory": ".claude/shared",
                "message_format": "yaml"
            }
        }
        
        config_path = self.agents_dir / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(master_config, f, default_flow_style=False, sort_keys=False)
        
        return master_config
    
    def list_agents(self) -> List[str]:
        """List all available agents"""
        agents = []
        for template_file in self.templates_dir.glob("*.yaml"):
            agents.append(template_file.stem)
        return agents
    
    def validate_agent_config(self, agent_type: str) -> bool:
        """Validate an agent configuration"""
        config = self.load_agent_config(agent_type)
        if not config:
            return False
        
        required_fields = ['name', 'description', 'workdir', 'permissions', 'tools']
        for field in required_fields:
            if field not in config:
                print(f"Missing required field: {field}")
                return False
        
        return True
    
    def _migrate_service_configs(self):
        """Migrate existing service configurations to unified structure"""
        if not self.services_dir.exists():
            return
        
        # Map of service directories to their agent type
        service_mapping = {
            "identity-service": "identity-service",
            "content-service": "content-service",
            "communication-service": "communication-service",
            "workflow-intelligence-service": "workflow-intelligence-service"
        }
        
        for service_name, config_name in service_mapping.items():
            service_claude_dir = self.services_dir / service_name / ".claude"
            if service_claude_dir.exists():
                # Check if settings.local.json exists
                settings_file = service_claude_dir / "settings.local.json"
                if settings_file.exists():
                    # Create service-specific config directory
                    service_config_dir = self.configs_dir / config_name
                    service_config_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Copy settings file
                    import shutil
                    dest_file = service_config_dir / "settings.local.json"
                    if not dest_file.exists():
                        shutil.copy2(settings_file, dest_file)
                        print(f"Migrated {service_name} configuration")


def main():
    """CLI interface for agent configurator"""
    parser = argparse.ArgumentParser(description='Agent Configuration Manager for ReactDjango-Hub')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize agent configuration system')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available agents')
    
    # Configure command
    config_parser = subparsers.add_parser('configure', help='Configure an agent')
    config_parser.add_argument('agent_type', choices=[t.value for t in AgentType], 
                               help='Type of agent to configure')
    
    # Launch command
    launch_parser = subparsers.add_parser('launch', help='Generate launch script for an agent')
    launch_parser.add_argument('agent_type', choices=[t.value for t in AgentType], 
                               help='Type of agent to launch')
    
    # Setup worktree command
    worktree_parser = subparsers.add_parser('worktree', help='Setup git worktree for an agent')
    worktree_parser.add_argument('agent_type', choices=[t.value for t in AgentType], 
                                 help='Type of agent')
    worktree_parser.add_argument('--branch', help='Branch name (optional)')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate agent configuration')
    validate_parser.add_argument('agent_type', choices=[t.value for t in AgentType], 
                                 help='Type of agent to validate')
    
    args = parser.parse_args()
    
    configurator = AgentConfigurator()
    
    if args.command == 'init':
        print("🔧 Initializing agent configuration system...")
        configurator.create_agent_templates()
        configurator.create_master_config()
        print("✅ Agent templates created")
        print("✅ Master configuration created")
        print(f"📁 Configuration directory: {configurator.agents_dir}")
        
    elif args.command == 'list':
        agents = configurator.list_agents()
        print("📋 Available agents:")
        for agent in agents:
            config = configurator.load_agent_config(agent)
            if config:
                print(f"  • {agent}: {config.get('description', 'No description')}")
    
    elif args.command == 'configure':
        config = configurator.load_agent_config(args.agent_type)
        if config:
            configurator.save_agent_config(args.agent_type, config)
            print(f"✅ Configured {args.agent_type} agent")
        else:
            print(f"❌ No template found for {args.agent_type}")
    
    elif args.command == 'launch':
        script_path = configurator.generate_launch_script(args.agent_type)
        print(f"✅ Launch script created: {script_path}")
        print(f"🚀 Run with: bash {script_path}")
    
    elif args.command == 'worktree':
        worktree_path = configurator.setup_git_worktree(args.agent_type, args.branch)
        print(f"✅ Worktree ready at: {worktree_path}")
    
    elif args.command == 'validate':
        if configurator.validate_agent_config(args.agent_type):
            print(f"✅ {args.agent_type} configuration is valid")
        else:
            print(f"❌ {args.agent_type} configuration is invalid")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()