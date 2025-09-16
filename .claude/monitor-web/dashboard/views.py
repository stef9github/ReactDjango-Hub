"""Dashboard views for the monitoring interface."""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.utils import timezone
from datetime import timedelta
import psutil
import json
import os
import yaml
from pathlib import Path

from .models import SystemMetric, Alert
from agents.models import Agent, AgentStatus
from tasks.models import Task
from logs.models import LogEntry


class DashboardView(TemplateView):
    """Main dashboard view."""
    template_name = 'dashboard/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current system metrics
        context['cpu_usage'] = psutil.cpu_percent(interval=1)
        context['memory_usage'] = psutil.virtual_memory().percent
        context['disk_usage'] = psutil.disk_usage('/').percent
        
        # Get agent statistics
        context['total_agents'] = Agent.objects.count()
        context['active_agents'] = Agent.objects.filter(status='running').count()
        context['idle_agents'] = Agent.objects.filter(status='idle').count()
        context['error_agents'] = Agent.objects.filter(status='error').count()
        
        # Get task statistics
        context['pending_tasks'] = Task.objects.filter(status='pending').count()
        context['running_tasks'] = Task.objects.filter(status='running').count()
        context['completed_tasks'] = Task.objects.filter(status='completed').count()
        context['failed_tasks'] = Task.objects.filter(status='failed').count()
        
        # Get recent alerts
        context['recent_alerts'] = Alert.objects.filter(resolved=False)[:5]
        context['alert_count'] = Alert.objects.filter(resolved=False).count()
        
        # Get recent log entries
        context['recent_logs'] = LogEntry.objects.all()[:10]
        
        # Get agents with their latest status
        context['agents'] = Agent.objects.all().prefetch_related('status_updates')
        
        return context


def api_metrics(request):
    """API endpoint for real-time metrics."""
    metrics = {
        'timestamp': timezone.now().isoformat(),
        'system': {
            'cpu': psutil.cpu_percent(interval=0.1),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent,
            'processes': len(psutil.pids()),
        },
        'agents': {
            'total': Agent.objects.count(),
            'running': Agent.objects.filter(status='running').count(),
            'idle': Agent.objects.filter(status='idle').count(),
            'error': Agent.objects.filter(status='error').count(),
        },
        'tasks': {
            'pending': Task.objects.filter(status='pending').count(),
            'running': Task.objects.filter(status='running').count(),
            'completed': Task.objects.filter(status='completed').count(),
            'failed': Task.objects.filter(status='failed').count(),
        },
        'alerts': {
            'unresolved': Alert.objects.filter(resolved=False).count(),
            'critical': Alert.objects.filter(resolved=False, severity='critical').count(),
            'warning': Alert.objects.filter(resolved=False, severity='warning').count(),
        }
    }
    
    # Store metrics for history
    SystemMetric.objects.create(
        cpu_usage=metrics['system']['cpu'],
        memory_usage=metrics['system']['memory'],
        disk_usage=metrics['system']['disk'],
        active_agents=metrics['agents']['running'],
        pending_tasks=metrics['tasks']['pending'],
        completed_tasks=metrics['tasks']['completed'],
        error_count=metrics['agents']['error'] + metrics['tasks']['failed']
    )
    
    # Clean old metrics (keep last 24 hours)
    cutoff = timezone.now() - timedelta(hours=24)
    SystemMetric.objects.filter(timestamp__lt=cutoff).delete()
    
    return JsonResponse(metrics)


def api_metrics_history(request):
    """API endpoint for historical metrics."""
    hours = int(request.GET.get('hours', 6))
    cutoff = timezone.now() - timedelta(hours=hours)
    
    metrics = SystemMetric.objects.filter(timestamp__gte=cutoff).values(
        'timestamp', 'cpu_usage', 'memory_usage', 'disk_usage',
        'active_agents', 'pending_tasks', 'completed_tasks', 'error_count'
    )
    
    # Format for Chart.js
    data = {
        'labels': [],
        'datasets': {
            'cpu': [],
            'memory': [],
            'disk': [],
            'agents': [],
            'tasks': [],
            'errors': [],
        }
    }
    
    for metric in metrics:
        data['labels'].append(metric['timestamp'].strftime('%H:%M'))
        data['datasets']['cpu'].append(metric['cpu_usage'])
        data['datasets']['memory'].append(metric['memory_usage'])
        data['datasets']['disk'].append(metric['disk_usage'])
        data['datasets']['agents'].append(metric['active_agents'])
        data['datasets']['tasks'].append(metric['pending_tasks'])
        data['datasets']['errors'].append(metric['error_count'])
    
    return JsonResponse(data)


def api_alerts(request):
    """API endpoint for alerts."""
    if request.method == 'POST':
        # Mark alert as resolved
        alert_id = request.POST.get('alert_id')
        if alert_id:
            alert = Alert.objects.get(id=alert_id)
            alert.resolved = True
            alert.resolved_at = timezone.now()
            alert.save()
            return JsonResponse({'status': 'success'})
    
    # Get unresolved alerts
    alerts = Alert.objects.filter(resolved=False).values(
        'id', 'timestamp', 'severity', 'source', 'message'
    )
    
    return JsonResponse({'alerts': list(alerts)})