"""Views for log viewing and analysis."""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import ListView
from django.db import models
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from datetime import timedelta
import git
import json
from pathlib import Path

from .models import LogEntry, GitCommit, WorkflowLog, PerformanceLog
from agents.models import Agent


class LogListView(ListView):
    """List all log entries with filtering."""
    model = LogEntry
    template_name = 'logs/list.html'
    context_object_name = 'logs'
    paginate_by = 100
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by level
        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        # Filter by source
        source = self.request.GET.get('source')
        if source:
            queryset = queryset.filter(source=source)
        
        # Filter by agent
        agent_id = self.request.GET.get('agent')
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
        
        # Search in message
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(message__icontains=search)
        
        # Time range filter
        hours = self.request.GET.get('hours')
        if hours:
            cutoff = timezone.now() - timedelta(hours=int(hours))
            queryset = queryset.filter(timestamp__gte=cutoff)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agents'] = Agent.objects.all()
        context['sources'] = LogEntry.objects.values_list('source', flat=True).distinct()[:20]
        context['current_filters'] = {
            'level': self.request.GET.get('level', ''),
            'source': self.request.GET.get('source', ''),
            'agent': self.request.GET.get('agent', ''),
            'search': self.request.GET.get('search', ''),
            'hours': self.request.GET.get('hours', ''),
        }
        
        # Log statistics
        context['stats'] = {
            'total': LogEntry.objects.count(),
            'errors': LogEntry.objects.filter(level='error').count(),
            'warnings': LogEntry.objects.filter(level='warning').count(),
            'last_hour': LogEntry.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=1)
            ).count(),
        }
        
        return context


def git_commits_view(request):
    """View git commit history."""
    # Try to read from git repository
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    
    try:
        repo = git.Repo(project_root)
        
        # Get recent commits
        recent_commits = []
        for commit in repo.iter_commits('HEAD', max_count=50):
            # Try to match commit to agent based on message patterns
            agent = None
            message_lower = commit.message.lower()
            
            # Simple agent detection based on common patterns
            if 'backend' in message_lower:
                agent = Agent.objects.filter(name='backend').first()
            elif 'frontend' in message_lower:
                agent = Agent.objects.filter(name='frontend').first()
            
            # Store or update commit in database
            git_commit, created = GitCommit.objects.update_or_create(
                commit_hash=commit.hexsha,
                defaults={
                    'timestamp': timezone.make_aware(
                        timezone.datetime.fromtimestamp(commit.committed_date)
                    ),
                    'author': commit.author.name,
                    'agent': agent,
                    'message': commit.message,
                    'files_changed': list(commit.stats.files.keys()),
                    'branch': repo.active_branch.name if repo.active_branch else 'unknown',
                }
            )
            recent_commits.append(git_commit)
    except:
        # Fall back to database records
        recent_commits = GitCommit.objects.all()[:50]
    
    context = {
        'commits': recent_commits,
        'total_commits': GitCommit.objects.count(),
    }
    
    return render(request, 'logs/git_commits.html', context)


def workflow_logs_view(request):
    """View workflow execution logs."""
    workflows = WorkflowLog.objects.all()[:50]
    
    # Calculate statistics
    stats = {
        'total': WorkflowLog.objects.count(),
        'successful': WorkflowLog.objects.filter(status='completed').count(),
        'failed': WorkflowLog.objects.filter(status='failed').count(),
        'avg_duration': WorkflowLog.objects.filter(
            completed_at__isnull=False
        ).annotate(
            duration_seconds=models.F('completed_at') - models.F('started_at')
        ).aggregate(
            avg=Avg('duration_seconds')
        )['avg'],
    }
    
    context = {
        'workflows': workflows,
        'stats': stats,
    }
    
    return render(request, 'logs/workflows.html', context)


def performance_view(request):
    """View performance metrics."""
    # Get agent performance metrics
    agent_metrics = []
    for agent in Agent.objects.all():
        recent_logs = agent.performance_logs.filter(
            timestamp__gte=timezone.now() - timedelta(hours=24)
        )
        
        if recent_logs.exists():
            metrics = recent_logs.aggregate(
                avg_duration=Avg('duration'),
                total_operations=Count('id'),
                success_rate=Avg('success') * 100,
                avg_cpu=Avg('cpu_usage'),
                avg_memory=Avg('memory_usage'),
            )
            
            agent_metrics.append({
                'agent': agent,
                'metrics': metrics,
                'recent_operations': recent_logs[:5],
            })
    
    context = {
        'agent_metrics': agent_metrics,
    }
    
    return render(request, 'logs/performance.html', context)


def api_logs_stream(request):
    """API endpoint for streaming logs."""
    last_id = request.GET.get('last_id', 0)
    
    # Get new logs since last_id
    logs = LogEntry.objects.filter(id__gt=last_id).order_by('id')[:50]
    
    log_data = []
    for log in logs:
        log_data.append({
            'id': log.id,
            'timestamp': log.timestamp.isoformat(),
            'level': log.level,
            'source': log.source,
            'agent': log.agent.name if log.agent else None,
            'message': log.message,
        })
    
    return JsonResponse({
        'logs': log_data,
        'last_id': logs.last().id if logs else last_id,
    })


def api_log_stats(request):
    """API endpoint for log statistics."""
    hours = int(request.GET.get('hours', 24))
    cutoff = timezone.now() - timedelta(hours=hours)
    
    # Get log counts by level over time
    stats = []
    for i in range(hours):
        hour_start = cutoff + timedelta(hours=i)
        hour_end = hour_start + timedelta(hours=1)
        
        counts = LogEntry.objects.filter(
            timestamp__gte=hour_start,
            timestamp__lt=hour_end
        ).values('level').annotate(count=Count('id'))
        
        hour_stats = {
            'hour': hour_start.strftime('%H:%M'),
            'debug': 0,
            'info': 0,
            'warning': 0,
            'error': 0,
            'critical': 0,
        }
        
        for count in counts:
            hour_stats[count['level']] = count['count']
        
        stats.append(hour_stats)
    
    return JsonResponse({'stats': stats})