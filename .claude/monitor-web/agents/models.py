"""Models for agent tracking and management."""
from django.db import models
from django.utils import timezone
import json


class Agent(models.Model):
    """Agent configuration and status."""
    STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('running', 'Running'),
        ('error', 'Error'),
        ('stopped', 'Stopped'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    type = models.CharField(max_length=50)  # backend, frontend, infrastructure, etc.
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='idle')
    pid = models.IntegerField(null=True, blank=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    config = models.JSONField(default=dict)
    
    # Performance metrics
    cpu_usage = models.FloatField(default=0)
    memory_usage = models.FloatField(default=0)
    tasks_completed = models.IntegerField(default=0)
    tasks_failed = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.status})"
    
    @property
    def is_alive(self):
        """Check if agent is responding."""
        if not self.last_heartbeat:
            return False
        return (timezone.now() - self.last_heartbeat).seconds < 30
    
    @property
    def latest_status(self):
        """Get the latest status update."""
        return self.status_updates.first()


class AgentStatus(models.Model):
    """Agent status updates and history."""
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='status_updates')
    timestamp = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20)
    message = models.TextField(blank=True)
    context = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.agent.name} - {self.status} at {self.timestamp}"


class AgentCommunication(models.Model):
    """Inter-agent communication logs."""
    from_agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='sent_messages')
    to_agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='received_messages')
    timestamp = models.DateTimeField(default=timezone.now)
    message_type = models.CharField(max_length=50)
    content = models.JSONField()
    response = models.JSONField(null=True, blank=True)
    success = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.from_agent.name} → {self.to_agent.name}: {self.message_type}"


class AgentConflict(models.Model):
    """Conflict detection and resolution tracking."""
    RESOLUTION_CHOICES = [
        ('pending', 'Pending'),
        ('auto_resolved', 'Auto Resolved'),
        ('manual_resolved', 'Manual Resolved'),
        ('ignored', 'Ignored'),
    ]
    
    timestamp = models.DateTimeField(default=timezone.now)
    agents = models.ManyToManyField(Agent, related_name='conflicts')
    conflict_type = models.CharField(max_length=100)
    description = models.TextField()
    file_paths = models.JSONField(default=list)
    resolution_status = models.CharField(max_length=20, choices=RESOLUTION_CHOICES, default='pending')
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        agent_names = ', '.join([a.name for a in self.agents.all()])
        return f"Conflict: {self.conflict_type} - {agent_names}"