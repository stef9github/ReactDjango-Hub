"""Management command to simulate agent activity for testing."""
from django.core.management.base import BaseCommand
from django.utils import timezone
import random
import time
from agents.models import Agent, AgentStatus, AgentCommunication
from tasks.models import Task, TaskExecution
from logs.models import LogEntry
from dashboard.models import Alert


class Command(BaseCommand):
    help = 'Simulate agent activity for testing the monitor interface'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--duration',
            type=int,
            default=60,
            help='Duration to run simulation in seconds'
        )
    
    def handle(self, *args, **options):
        duration = options['duration']
        end_time = time.time() + duration
        
        self.stdout.write(f'Starting simulation for {duration} seconds...')
        
        # Create sample agents if they don't exist
        self.create_sample_agents()
        
        agents = list(Agent.objects.all())
        
        while time.time() < end_time:
            # Simulate various activities
            self.simulate_agent_status_change(agents)
            self.simulate_task_creation()
            self.simulate_task_execution(agents)
            self.simulate_log_entries(agents)
            self.simulate_agent_communication(agents)
            self.simulate_alerts()
            
            time.sleep(random.uniform(1, 3))
        
        self.stdout.write(self.style.SUCCESS('Simulation completed'))
    
    def create_sample_agents(self):
        """Create sample agents for testing."""
        sample_agents = [
            ('backend', 'Backend development agent', 'backend'),
            ('frontend', 'Frontend development agent', 'frontend'),
            ('infrastructure', 'Infrastructure management agent', 'infrastructure'),
            ('security', 'Security scanning agent', 'security'),
            ('review', 'Code review agent', 'quality'),
        ]
        
        for name, description, agent_type in sample_agents:
            Agent.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'type': agent_type,
                    'status': random.choice(['idle', 'running', 'stopped']),
                }
            )
    
    def simulate_agent_status_change(self, agents):
        """Simulate agent status changes."""
        if random.random() < 0.3:
            agent = random.choice(agents)
            old_status = agent.status
            new_status = random.choice(['idle', 'running', 'stopped'])
            
            if old_status != new_status:
                agent.status = new_status
                agent.last_heartbeat = timezone.now()
                agent.cpu_usage = random.uniform(5, 95) if new_status == 'running' else 0
                agent.memory_usage = random.uniform(100, 2000) if new_status == 'running' else 0
                agent.save()
                
                AgentStatus.objects.create(
                    agent=agent,
                    status=new_status,
                    message=f'Status changed from {old_status} to {new_status}'
                )
                
                self.stdout.write(f'Agent {agent.name}: {old_status} -> {new_status}')
    
    def simulate_task_creation(self):
        """Simulate task creation."""
        if random.random() < 0.2:
            task_types = ['build', 'test', 'deploy', 'analyze', 'scan']
            priorities = [1, 2, 2, 3, 3, 3, 4]  # Weighted towards normal/high
            
            task = Task.objects.create(
                title=f'{random.choice(task_types).capitalize()} task {random.randint(1000, 9999)}',
                description='Simulated task for testing',
                task_type=random.choice(task_types),
                priority=random.choice(priorities),
                estimated_duration=random.randint(5, 60),
            )
            
            self.stdout.write(f'Created task: {task.title}')
    
    def simulate_task_execution(self, agents):
        """Simulate task execution."""
        pending_tasks = Task.objects.filter(status='pending')[:5]
        idle_agents = [a for a in agents if a.status == 'idle']
        
        if pending_tasks and idle_agents:
            task = random.choice(pending_tasks)
            agent = random.choice(idle_agents)
            
            # Assign and start task
            task.assigned_to = agent
            task.assigned_at = timezone.now()
            task.status = 'running'
            task.started_at = timezone.now()
            task.save()
            
            agent.status = 'running'
            agent.save()
            
            # Simulate completion after a short delay
            if random.random() < 0.7:
                # Success
                task.status = 'completed'
                task.completed_at = timezone.now()
                task.result = {'status': 'success', 'output': 'Task completed successfully'}
                agent.tasks_completed += 1
            else:
                # Failure
                task.status = 'failed'
                task.completed_at = timezone.now()
                task.error_message = 'Simulated failure for testing'
                agent.tasks_failed += 1
            
            task.save()
            
            agent.status = 'idle'
            agent.save()
            
            TaskExecution.objects.create(
                task=task,
                agent=agent,
                completed_at=task.completed_at,
                success=(task.status == 'completed'),
                output=task.result.get('output', '') if task.result else '',
                error=task.error_message,
            )
            
            self.stdout.write(f'Task {task.title} executed by {agent.name}: {task.status}')
    
    def simulate_log_entries(self, agents):
        """Simulate log entries."""
        if random.random() < 0.5:
            levels = ['debug', 'debug', 'info', 'info', 'info', 'warning', 'error']
            sources = ['system', 'api', 'database', 'cache', 'scheduler']
            messages = [
                'Processing request',
                'Database query executed',
                'Cache miss',
                'Task scheduled',
                'API call completed',
                'Connection timeout',
                'Resource limit reached',
                'Configuration updated',
            ]
            
            log = LogEntry.objects.create(
                level=random.choice(levels),
                source=random.choice(sources),
                agent=random.choice(agents) if random.random() < 0.7 else None,
                message=random.choice(messages),
                context={'simulation': True, 'random_id': random.randint(1000, 9999)},
            )
            
            self.stdout.write(f'Log: [{log.level}] {log.source}: {log.message}')
    
    def simulate_agent_communication(self, agents):
        """Simulate inter-agent communication."""
        if random.random() < 0.1 and len(agents) >= 2:
            from_agent = random.choice(agents)
            to_agent = random.choice([a for a in agents if a != from_agent])
            
            message_types = ['task_delegation', 'status_update', 'resource_request', 'sync']
            
            comm = AgentCommunication.objects.create(
                from_agent=from_agent,
                to_agent=to_agent,
                message_type=random.choice(message_types),
                content={'message': 'Simulated communication', 'test': True},
                success=random.random() < 0.9,
            )
            
            self.stdout.write(f'Communication: {from_agent.name} -> {to_agent.name}')
    
    def simulate_alerts(self):
        """Simulate system alerts."""
        if random.random() < 0.05:
            severities = ['info', 'warning', 'error', 'critical']
            sources = ['System Monitor', 'Resource Manager', 'Security Scanner']
            messages = [
                'High CPU usage detected',
                'Memory threshold exceeded',
                'Disk space running low',
                'Network latency increased',
                'Service health check failed',
                'Configuration drift detected',
            ]
            
            alert = Alert.objects.create(
                severity=random.choice(severities),
                source=random.choice(sources),
                message=random.choice(messages),
            )
            
            self.stdout.write(f'Alert: [{alert.severity}] {alert.message}')