"""Views for agent management and control."""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
import subprocess
import psutil
import os
import signal
import yaml
from pathlib import Path

from .models import Agent, AgentStatus, AgentCommunication, AgentConflict


class AgentListView(ListView):
    """List all agents with their status."""
    model = Agent
    template_name = 'agents/list.html'
    context_object_name = 'agents'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Update agent statuses
        for agent in context['agents']:
            agent.is_active = agent.is_alive
        return context


class AgentDetailView(DetailView):
    """Detailed view of a single agent."""
    model = Agent
    template_name = 'agents/detail.html'
    context_object_name = 'agent'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agent = self.object
        
        # Get recent status updates
        context['status_updates'] = agent.status_updates.all()[:20]
        
        # Get recent communications
        context['sent_messages'] = agent.sent_messages.all()[:10]
        context['received_messages'] = agent.received_messages.all()[:10]
        
        # Get active conflicts
        context['conflicts'] = agent.conflicts.filter(resolution_status='pending')
        
        # Get performance metrics
        context['performance'] = {
            'cpu': agent.cpu_usage,
            'memory': agent.memory_usage,
            'tasks_completed': agent.tasks_completed,
            'tasks_failed': agent.tasks_failed,
            'success_rate': (agent.tasks_completed / max(1, agent.tasks_completed + agent.tasks_failed)) * 100
        }
        
        return context


@require_POST
def start_agent(request, pk):
    """Start an agent."""
    agent = get_object_or_404(Agent, pk=pk)
    
    try:
        # Launch agent using the launch script
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        launch_script = project_root / '.claude' / 'launch-agent.sh'
        
        if launch_script.exists():
            process = subprocess.Popen(
                [str(launch_script), agent.name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(project_root)
            )
            
            agent.pid = process.pid
            agent.status = 'running'
            agent.last_heartbeat = timezone.now()
            agent.save()
            
            # Log status update
            AgentStatus.objects.create(
                agent=agent,
                status='running',
                message=f'Agent started with PID {process.pid}'
            )
            
            messages.success(request, f'Agent {agent.name} started successfully')
        else:
            messages.error(request, 'Launch script not found')
            
    except Exception as e:
        messages.error(request, f'Failed to start agent: {str(e)}')
        agent.status = 'error'
        agent.save()
    
    return redirect('agents:detail', pk=pk)


@require_POST
def stop_agent(request, pk):
    """Stop an agent."""
    agent = get_object_or_404(Agent, pk=pk)
    
    try:
        if agent.pid:
            try:
                # Try graceful shutdown first
                os.kill(agent.pid, signal.SIGTERM)
                # Give it a moment to clean up
                import time
                time.sleep(1)
                
                # Check if still running
                if psutil.pid_exists(agent.pid):
                    # Force kill if necessary
                    os.kill(agent.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass  # Process already dead
            
            agent.pid = None
            agent.status = 'stopped'
            agent.save()
            
            # Log status update
            AgentStatus.objects.create(
                agent=agent,
                status='stopped',
                message='Agent stopped by user'
            )
            
            messages.success(request, f'Agent {agent.name} stopped successfully')
        else:
            messages.warning(request, f'Agent {agent.name} was not running')
            
    except Exception as e:
        messages.error(request, f'Failed to stop agent: {str(e)}')
    
    return redirect('agents:detail', pk=pk)


@require_POST
def restart_agent(request, pk):
    """Restart an agent."""
    agent = get_object_or_404(Agent, pk=pk)
    
    # Stop if running
    if agent.pid:
        try:
            os.kill(agent.pid, signal.SIGTERM)
            import time
            time.sleep(1)
        except:
            pass
    
    # Start again
    return start_agent(request, pk)


def api_agent_status(request, pk):
    """API endpoint for agent status."""
    agent = get_object_or_404(Agent, pk=pk)
    
    # Check if process is still running
    if agent.pid:
        agent.is_running = psutil.pid_exists(agent.pid)
        if agent.is_running:
            try:
                process = psutil.Process(agent.pid)
                agent.cpu_usage = process.cpu_percent()
                agent.memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                agent.save()
            except:
                agent.is_running = False
    else:
        agent.is_running = False
    
    data = {
        'id': agent.id,
        'name': agent.name,
        'status': agent.status,
        'is_running': agent.is_running,
        'is_alive': agent.is_alive,
        'pid': agent.pid,
        'cpu_usage': agent.cpu_usage,
        'memory_usage': agent.memory_usage,
        'last_heartbeat': agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
    }
    
    return JsonResponse(data)


def api_agent_logs(request, pk):
    """API endpoint for agent logs."""
    agent = get_object_or_404(Agent, pk=pk)
    limit = int(request.GET.get('limit', 50))
    
    # Get recent status updates
    updates = agent.status_updates.all()[:limit]
    
    logs = []
    for update in updates:
        logs.append({
            'timestamp': update.timestamp.isoformat(),
            'status': update.status,
            'message': update.message,
            'context': update.context,
        })
    
    return JsonResponse({'logs': logs})


def conflicts_view(request):
    """View for conflict resolution interface."""
    conflicts = AgentConflict.objects.filter(resolution_status='pending')
    
    context = {
        'conflicts': conflicts,
        'total_conflicts': conflicts.count(),
    }
    
    return render(request, 'agents/conflicts.html', context)


@require_POST
def resolve_conflict(request, pk):
    """Resolve a conflict."""
    conflict = get_object_or_404(AgentConflict, pk=pk)
    resolution = request.POST.get('resolution')
    notes = request.POST.get('notes', '')
    
    conflict.resolution_status = resolution
    conflict.resolution_notes = notes
    conflict.resolved_at = timezone.now()
    conflict.save()
    
    messages.success(request, f'Conflict resolved as {resolution}')
    
    return redirect('agents:conflicts')