"""Dashboard models for monitoring system metrics."""
from django.db import models
from django.utils import timezone


class SystemMetric(models.Model):
    """System-wide metrics tracking."""
    timestamp = models.DateTimeField(default=timezone.now)
    cpu_usage = models.FloatField()
    memory_usage = models.FloatField()
    disk_usage = models.FloatField()
    active_agents = models.IntegerField(default=0)
    pending_tasks = models.IntegerField(default=0)
    completed_tasks = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"Metrics at {self.timestamp}"


class Alert(models.Model):
    """System alerts and notifications."""
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    timestamp = models.DateTimeField(default=timezone.now)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    source = models.CharField(max_length=100)
    message = models.TextField()
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"[{self.severity}] {self.source}: {self.message[:50]}"