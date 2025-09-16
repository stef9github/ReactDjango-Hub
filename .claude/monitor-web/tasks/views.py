"""Views for task queue management."""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse_lazy
import json

from .models import Task, TaskExecution, TaskTemplate
from agents.models import Agent, AgentStatus


class TaskListView(ListView):
    """List all tasks with filtering."""
    model = Task
    template_name = 'tasks/list.html'
    context_object_name = 'tasks'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by agent
        agent_id = self.request.GET.get('agent')
        if agent_id:
            queryset = queryset.filter(assigned_to_id=agent_id)
        
        # Filter by priority
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agents'] = Agent.objects.all()
        context['current_filters'] = {
            'status': self.request.GET.get('status', ''),
            'agent': self.request.GET.get('agent', ''),
            'priority': self.request.GET.get('priority', ''),
        }
        
        # Task statistics
        context['stats'] = {
            'pending': Task.objects.filter(status='pending').count(),
            'running': Task.objects.filter(status='running').count(),
            'completed': Task.objects.filter(status='completed').count(),
            'failed': Task.objects.filter(status='failed').count(),
        }
        
        return context


class TaskDetailView(DetailView):
    """Detailed view of a single task."""
    model = Task
    template_name = 'tasks/detail.html'
    context_object_name = 'task'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.object
        
        # Get execution history
        context['executions'] = task.executions.all()[:10]
        
        # Get dependencies and dependents
        context['dependencies'] = task.depends_on.all()
        context['dependents'] = task.dependents.all()
        
        # Get available agents for assignment
        if not task.assigned_to:
            context['available_agents'] = Agent.objects.filter(status='idle')
        
        return context


class TaskCreateView(CreateView):
    """Create a new task."""
    model = Task
    template_name = 'tasks/create.html'
    fields = ['title', 'description', 'task_type', 'priority', 'estimated_duration']
    success_url = reverse_lazy('tasks:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = TaskTemplate.objects.all()
        context['agents'] = Agent.objects.filter(status__in=['idle', 'running'])
        return context


@require_POST
def assign_task(request, pk):
    """Assign a task to an agent."""
    task = get_object_or_404(Task, pk=pk)
    agent_id = request.POST.get('agent_id')
    
    if agent_id:
        agent = get_object_or_404(Agent, pk=agent_id)
        
        # Check if agent is available
        if agent.status in ['idle', 'running']:
            task.assigned_to = agent
            task.assigned_at = timezone.now()
            task.status = 'assigned'
            task.save()
            
            # Log the assignment
            AgentStatus.objects.create(
                agent=agent,
                status='assigned',
                message=f'Assigned task: {task.title}',
                context={'task_id': task.id}
            )
            
            messages.success(request, f'Task assigned to {agent.name}')
        else:
            messages.error(request, f'Agent {agent.name} is not available')
    else:
        # Auto-assign to best available agent
        agent = Agent.objects.filter(status='idle').first()
        if agent:
            task.assigned_to = agent
            task.assigned_at = timezone.now()
            task.status = 'assigned'
            task.save()
            messages.success(request, f'Task auto-assigned to {agent.name}')
        else:
            messages.warning(request, 'No available agents for auto-assignment')
    
    return redirect('tasks:detail', pk=pk)


@require_POST
def execute_task(request, pk):
    """Execute a task."""
    task = get_object_or_404(Task, pk=pk)
    
    if task.status in ['pending', 'assigned']:
        if not task.assigned_to:
            # Auto-assign if not assigned
            agent = Agent.objects.filter(status='idle').first()
            if not agent:
                messages.error(request, 'No available agents')
                return redirect('tasks:detail', pk=pk)
            task.assigned_to = agent
            task.assigned_at = timezone.now()
        
        # Start execution
        task.status = 'running'
        task.started_at = timezone.now()
        task.save()
        
        # Create execution record
        execution = TaskExecution.objects.create(
            task=task,
            agent=task.assigned_to
        )
        
        # Update agent status
        task.assigned_to.status = 'running'
        task.assigned_to.save()
        
        messages.success(request, f'Task execution started')
    else:
        messages.warning(request, f'Task cannot be executed in {task.status} status')
    
    return redirect('tasks:detail', pk=pk)


@require_POST
def cancel_task(request, pk):
    """Cancel a task."""
    task = get_object_or_404(Task, pk=pk)
    
    if task.status in ['pending', 'assigned', 'running']:
        task.status = 'cancelled'
        task.save()
        
        # Free up agent if assigned
        if task.assigned_to:
            task.assigned_to.status = 'idle'
            task.assigned_to.save()
        
        messages.success(request, 'Task cancelled')
    else:
        messages.warning(request, f'Cannot cancel task in {task.status} status')
    
    return redirect('tasks:detail', pk=pk)


def api_task_queue(request):
    """API endpoint for task queue status."""
    tasks = Task.objects.filter(status__in=['pending', 'assigned', 'running']).values(
        'id', 'title', 'priority', 'status', 'task_type',
        'assigned_to__name', 'created_at', 'started_at'
    )
    
    queue = {
        'pending': [],
        'assigned': [],
        'running': [],
    }
    
    for task in tasks:
        task_data = {
            'id': task['id'],
            'title': task['title'],
            'priority': task['priority'],
            'type': task['task_type'],
            'agent': task['assigned_to__name'],
            'created': task['created_at'].isoformat() if task['created_at'] else None,
            'started': task['started_at'].isoformat() if task['started_at'] else None,
        }
        queue[task['status']].append(task_data)
    
    return JsonResponse(queue)


def api_create_task(request):
    """API endpoint to create a task."""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        task = Task.objects.create(
            title=data['title'],
            description=data.get('description', ''),
            task_type=data.get('type', 'general'),
            priority=data.get('priority', 2),
            context=data.get('context', {})
        )
        
        # Auto-assign if requested
        if data.get('auto_assign'):
            agent = Agent.objects.filter(status='idle').first()
            if agent:
                task.assigned_to = agent
                task.assigned_at = timezone.now()
                task.status = 'assigned'
                task.save()
        
        return JsonResponse({
            'id': task.id,
            'title': task.title,
            'status': task.status,
            'assigned_to': task.assigned_to.name if task.assigned_to else None
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def template_list(request):
    """List task templates."""
    templates = TaskTemplate.objects.all()
    
    context = {
        'templates': templates,
    }
    
    return render(request, 'tasks/templates.html', context)


@require_POST
def create_from_template(request, pk):
    """Create a task from a template."""
    template = get_object_or_404(TaskTemplate, pk=pk)
    
    # Get overrides from POST data
    overrides = {
        'title': request.POST.get('title', template.name),
        'priority': int(request.POST.get('priority', template.default_priority)),
    }
    
    # Create task from template
    task = template.create_task(**overrides)
    
    messages.success(request, f'Task created from template: {template.name}')
    
    return redirect('tasks:detail', pk=task.pk)