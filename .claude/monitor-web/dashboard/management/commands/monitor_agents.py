"""Management command to monitor agent processes."""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import psutil
import time
from agents.models import Agent, AgentStatus
from dashboard.models import Alert


class Command(BaseCommand):
    help = 'Monitor agent processes and update their status'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Monitoring interval in seconds'
        )
    
    def handle(self, *args, **options):
        interval = options['interval']
        self.stdout.write(f'Starting agent monitoring (interval: {interval}s)...')
        
        while True:
            try:
                self.check_agents()
                time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write('Monitoring stopped.')
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {e}'))
                time.sleep(interval)
    
    def check_agents(self):
        """Check status of all agents."""
        for agent in Agent.objects.all():
            # Check if process is running
            if agent.pid:
                if psutil.pid_exists(agent.pid):
                    try:
                        process = psutil.Process(agent.pid)
                        
                        # Update resource usage
                        agent.cpu_usage = process.cpu_percent()
                        agent.memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                        
                        # Check if responsive (based on heartbeat)
                        if agent.last_heartbeat:
                            time_since_heartbeat = timezone.now() - agent.last_heartbeat
                            if time_since_heartbeat > timedelta(seconds=60):
                                # Agent is unresponsive
                                if agent.status != 'error':
                                    agent.status = 'error'
                                    self.create_alert(
                                        'error',
                                        f'Agent {agent.name}',
                                        f'Agent {agent.name} is unresponsive'
                                    )
                                    AgentStatus.objects.create(
                                        agent=agent,
                                        status='error',
                                        message='Agent unresponsive - no heartbeat'
                                    )
                    except psutil.NoSuchProcess:
                        # Process died
                        agent.pid = None
                        agent.status = 'stopped'
                        self.create_alert(
                            'warning',
                            f'Agent {agent.name}',
                            f'Agent {agent.name} process terminated unexpectedly'
                        )
                else:
                    # PID doesn't exist
                    agent.pid = None
                    if agent.status == 'running':
                        agent.status = 'stopped'
                        self.create_alert(
                            'warning',
                            f'Agent {agent.name}',
                            f'Agent {agent.name} stopped unexpectedly'
                        )
            
            agent.save()
    
    def create_alert(self, severity, source, message):
        """Create an alert."""
        Alert.objects.create(
            severity=severity,
            source=source,
            message=message
        )
        self.stdout.write(f'[{severity.upper()}] {source}: {message}')