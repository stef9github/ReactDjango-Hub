"""Models for task queue management."""
from django.db import models
from django.utils import timezone
from agents.models import Agent


class Task(models.Model):
    """Task queue management."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Normal'),
        (3, 'High'),
        (4, 'Critical'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    task_type = models.CharField(max_length=50)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Assignment
    assigned_to = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    assigned_at = models.DateTimeField(null=True, blank=True)
    
    # Timing
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.IntegerField(null=True, blank=True, help_text="Estimated duration in minutes")
    
    # Context and results
    context = models.JSONField(default=dict)
    result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Dependencies
    depends_on = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='dependents')
    
    class Meta:
        ordering = ['-priority', 'created_at']
        indexes = [
            models.Index(fields=['status', '-priority']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.status})"
    
    @property
    def duration(self):
        """Calculate actual duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() / 60
        return None
    
    @property
    def is_ready(self):
        """Check if all dependencies are completed."""
        return not self.depends_on.filter(status__in=['pending', 'running', 'failed']).exists()


class TaskExecution(models.Model):
    """Task execution history and logs."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='executions')
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    success = models.BooleanField(default=False)
    output = models.TextField(blank=True)
    error = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Execution of {self.task.title} at {self.started_at}"


class TaskTemplate(models.Model):
    """Reusable task templates."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    task_type = models.CharField(max_length=50)
    default_priority = models.IntegerField(choices=Task.PRIORITY_CHOICES, default=2)
    default_context = models.JSONField(default=dict)
    estimated_duration = models.IntegerField(null=True, blank=True)
    
    # Which agents can handle this template
    compatible_agents = models.ManyToManyField(Agent, blank=True)
    
    def __str__(self):
        return self.name
    
    def create_task(self, **overrides):
        """Create a task from this template."""
        task_data = {
            'title': overrides.get('title', self.name),
            'description': overrides.get('description', self.description),
            'task_type': self.task_type,
            'priority': overrides.get('priority', self.default_priority),
            'context': {**self.default_context, **overrides.get('context', {})},
            'estimated_duration': self.estimated_duration,
        }
        return Task.objects.create(**task_data)