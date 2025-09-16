from django.core.management.base import BaseCommand
from agents.models import Agent
from tasks.models import Task
from datetime import datetime
import random
import time

class Command(BaseCommand):
    help = 'Simulate agent activity by processing tasks'

    def handle(self, *args, **options):
        self.stdout.write("Starting agent simulation...")
        
        # Update all agents to "running" status
        Agent.objects.update(status='running')
        
        while True:
            # Get pending or running tasks
            tasks = Task.objects.filter(status__in=['pending', 'running']).order_by('priority', 'created_at')
            
            if not tasks:
                self.stdout.write("No tasks to process. Waiting...")
                time.sleep(5)
                continue
            
            for task in tasks[:5]:  # Process up to 5 tasks at a time
                # Assign to an available agent if not assigned
                if not task.assigned_agent:
                    available_agents = Agent.objects.filter(status='running')
                    if available_agents:
                        task.assigned_agent = random.choice(available_agents)
                        task.save()
                        self.stdout.write(f"Assigned task '{task.title}' to {task.assigned_agent.name}")
                
                # Simulate task progress
                if task.status == 'pending':
                    task.status = 'running'
                    task.started_at = datetime.now()
                    task.save()
                    self.stdout.write(f"Started task: {task.title}")
                    
                elif task.status == 'running':
                    # Simulate progress
                    if task.progress < 100:
                        task.progress = min(task.progress + random.randint(10, 30), 100)
                        task.save()
                        self.stdout.write(f"Task '{task.title}' progress: {task.progress}%")
                        
                        if task.progress >= 100:
                            task.status = 'completed'
                            task.completed_at = datetime.now()
                            task.save()
                            self.stdout.write(self.style.SUCCESS(f"Completed task: {task.title}"))
                            
                            # Update agent stats
                            if task.assigned_agent:
                                agent = task.assigned_agent
                                agent.tasks_completed += 1
                                agent.save()
            
            # Wait before next iteration
            time.sleep(3)