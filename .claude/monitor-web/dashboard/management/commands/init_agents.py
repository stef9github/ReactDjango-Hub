"""Management command to initialize agents from configuration."""
from django.core.management.base import BaseCommand
from django.conf import settings
import yaml
from pathlib import Path
from agents.models import Agent


class Command(BaseCommand):
    help = 'Initialize agents from agents.yaml configuration'
    
    def handle(self, *args, **options):
        # Load agent configuration
        config_file = settings.AGENT_CONFIG_PATH
        
        if not config_file.exists():
            self.stdout.write(self.style.ERROR(f'Configuration file not found: {config_file}'))
            return
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        agents_config = config.get('agents', {})
        
        created_count = 0
        updated_count = 0
        
        for agent_name, agent_config in agents_config.items():
            # Skip template entries
            if agent_name.startswith('_'):
                continue
            
            # Determine agent type from role
            role = agent_config.get('role', 'general')
            agent_type = self.get_agent_type(role)
            
            # Create or update agent
            agent, created = Agent.objects.update_or_create(
                name=agent_name,
                defaults={
                    'description': agent_config.get('description', ''),
                    'type': agent_type,
                    'config': agent_config,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Created agent: {agent_name}')
            else:
                updated_count += 1
                self.stdout.write(f'Updated agent: {agent_name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully initialized agents: {created_count} created, {updated_count} updated'
            )
        )
    
    def get_agent_type(self, role):
        """Map role to agent type."""
        type_mapping = {
            'backend': 'backend',
            'frontend': 'frontend',
            'infrastructure': 'infrastructure',
            'deployment': 'deployment',
            'services_coordinator': 'coordinator',
            'identity': 'service',
            'communication': 'service',
            'content': 'service',
            'workflow': 'service',
            'security': 'quality',
            'review': 'quality',
            'techlead': 'leadership',
        }
        
        for key, value in type_mapping.items():
            if key in role.lower():
                return value
        
        return 'general'