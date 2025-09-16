"""Models for logging and audit trails."""
from django.db import models
from django.utils import timezone
from agents.models import Agent


class LogEntry(models.Model):
    """General log entries."""
    LEVEL_CHOICES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, db_index=True)
    source = models.CharField(max_length=100, db_index=True)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='log_entries')
    message = models.TextField()
    context = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'level']),
            models.Index(fields=['source', '-timestamp']),
        ]
    
    def __str__(self):
        return f"[{self.level}] {self.source}: {self.message[:50]}"


class GitCommit(models.Model):
    """Git commit history tracking."""
    commit_hash = models.CharField(max_length=40, unique=True)
    timestamp = models.DateTimeField()
    author = models.CharField(max_length=200)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='commits')
    message = models.TextField()
    files_changed = models.JSONField(default=list)
    branch = models.CharField(max_length=100)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.commit_hash[:8]} - {self.message[:50]}"


class WorkflowLog(models.Model):
    """Workflow execution logs."""
    workflow_id = models.CharField(max_length=100)
    workflow_name = models.CharField(max_length=200)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20)
    agents_involved = models.ManyToManyField(Agent, related_name='workflows')
    steps = models.JSONField(default=list)
    result = models.JSONField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.workflow_name} - {self.status}"
    
    @property
    def duration(self):
        """Calculate workflow duration."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class PerformanceLog(models.Model):
    """Performance metrics logging."""
    timestamp = models.DateTimeField(default=timezone.now)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='performance_logs')
    operation = models.CharField(max_length=100)
    duration = models.FloatField(help_text="Duration in seconds")
    success = models.BooleanField(default=True)
    cpu_usage = models.FloatField(null=True, blank=True)
    memory_usage = models.FloatField(null=True, blank=True)
    details = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['agent', '-timestamp']),
            models.Index(fields=['operation', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.agent.name} - {self.operation}: {self.duration}s"