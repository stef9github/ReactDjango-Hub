from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
import json
from datetime import datetime, timedelta

from .models import (
    Feature, FeatureCategory, FeatureTemplate,
    FeatureHistory, FeatureComment, FeatureTask,
    FeatureAttachment, FeatureRoadmap
)
from .forms import (
    FeatureForm, FeatureTemplateForm, FeatureCommentForm,
    FeatureTaskForm, FeatureBulkActionForm
)


class FeatureListView(LoginRequiredMixin, ListView):
    """Main feature list view with filtering and sorting"""
    model = Feature
    template_name = 'features/feature_list.html'
    context_object_name = 'features'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Feature.objects.select_related('category', 'assigned_to').prefetch_related('tasks')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        # Filter by priority
        priority = self.request.GET.get('priority')
        if priority and priority != 'all':
            queryset = queryset.filter(priority=priority)
        
        # Filter by category
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
        
        # Exclude archived by default
        if not self.request.GET.get('show_archived'):
            queryset = queryset.exclude(status='ARCHIVED')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = FeatureCategory.objects.all()
        context['status_choices'] = Feature.STATUS_CHOICES
        context['priority_choices'] = Feature.PRIORITY_CHOICES
        
        # Statistics
        features = Feature.objects.exclude(status='ARCHIVED')
        context['stats'] = {
            'total': features.count(),
            'backlog': features.filter(status='BACKLOG').count(),
            'in_progress': features.filter(status='IN_PROGRESS').count(),
            'done': features.filter(status='DONE').count(),
            'avg_effort': features.aggregate(Avg('estimated_effort'))['estimated_effort__avg'] or 0,
            'total_effort': features.aggregate(Sum('estimated_effort'))['estimated_effort__sum'] or 0,
        }
        
        return context


class FeatureKanbanView(LoginRequiredMixin, ListView):
    """Kanban board view for features"""
    model = Feature
    template_name = 'features/feature_kanban.html'
    context_object_name = 'features'
    
    def get_queryset(self):
        return Feature.objects.select_related('category', 'assigned_to').exclude(status='ARCHIVED')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Group features by status
        features_by_status = {}
        for status_code, status_name in Feature.STATUS_CHOICES:
            if status_code != 'ARCHIVED':
                features_by_status[status_code] = {
                    'name': status_name,
                    'features': self.get_queryset().filter(status=status_code).order_by('priority_order')
                }
        
        context['features_by_status'] = features_by_status
        context['categories'] = FeatureCategory.objects.all()
        return context


class FeatureRoadmapView(LoginRequiredMixin, ListView):
    """Timeline/roadmap view for features"""
    model = Feature
    template_name = 'features/feature_roadmap.html'
    context_object_name = 'features'
    
    def get_queryset(self):
        return Feature.objects.filter(
            due_date__isnull=False
        ).select_related('category').order_by('due_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Group features by month
        features_by_month = {}
        for feature in self.get_queryset():
            month_key = feature.due_date.strftime('%Y-%m')
            month_name = feature.due_date.strftime('%B %Y')
            if month_key not in features_by_month:
                features_by_month[month_key] = {
                    'name': month_name,
                    'features': []
                }
            features_by_month[month_key]['features'].append(feature)
        
        context['features_by_month'] = features_by_month
        context['roadmaps'] = FeatureRoadmap.objects.filter(is_active=True)
        return context


class FeatureCreateView(LoginRequiredMixin, CreateView):
    """Create new feature view"""
    model = Feature
    form_class = FeatureForm
    template_name = 'features/feature_form.html'
    success_url = reverse_lazy('features:list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = FeatureTemplate.objects.all()
        context['categories'] = FeatureCategory.objects.all()
        return context
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Create history entry
        FeatureHistory.objects.create(
            feature=self.object,
            user=self.request.user,
            action='created',
            comment=f'Feature "{self.object.title}" created'
        )
        
        messages.success(self.request, f'Feature "{self.object.title}" created successfully!')
        return response


class FeatureUpdateView(LoginRequiredMixin, UpdateView):
    """Update feature view"""
    model = Feature
    form_class = FeatureForm
    template_name = 'features/feature_form.html'
    
    def get_success_url(self):
        return reverse('features:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Track changes for history
        if form.has_changed():
            for field_name in form.changed_data:
                old_value = form.initial.get(field_name)
                new_value = form.cleaned_data.get(field_name)
                
                FeatureHistory.objects.create(
                    feature=self.object,
                    user=self.request.user,
                    action='updated',
                    field_name=field_name,
                    old_value=str(old_value) if old_value else '',
                    new_value=str(new_value) if new_value else '',
                )
        
        response = super().form_valid(form)
        messages.success(self.request, f'Feature "{self.object.title}" updated successfully!')
        return response


class FeatureDetailView(LoginRequiredMixin, DetailView):
    """Feature detail view with comments and tasks"""
    model = Feature
    template_name = 'features/feature_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.select_related('user')
        context['tasks'] = self.object.tasks.all()
        context['history'] = self.object.history.select_related('user')[:10]
        context['attachments'] = self.object.attachments.all()
        context['comment_form'] = FeatureCommentForm()
        return context


class FeatureDeleteView(LoginRequiredMixin, DeleteView):
    """Delete feature view"""
    model = Feature
    template_name = 'features/feature_confirm_delete.html'
    success_url = reverse_lazy('features:list')
    
    def delete(self, request, *args, **kwargs):
        feature = self.get_object()
        messages.success(request, f'Feature "{feature.title}" deleted successfully!')
        return super().delete(request, *args, **kwargs)


# AJAX Views for drag-and-drop and inline editing

@login_required
@require_POST
def update_feature_order(request):
    """Update feature priority order via drag-and-drop"""
    try:
        data = json.loads(request.body)
        feature_id = data.get('feature_id')
        new_order = data.get('new_order')
        
        feature = get_object_or_404(Feature, pk=feature_id)
        feature.priority_order = new_order
        feature.save(update_fields=['priority_order'])
        
        # Log the change
        FeatureHistory.objects.create(
            feature=feature,
            user=request.user,
            action='reordered',
            comment=f'Priority order changed to {new_order}'
        )
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def update_feature_status(request):
    """Update feature status (for kanban board)"""
    try:
        data = json.loads(request.body)
        feature_id = data.get('feature_id')
        new_status = data.get('new_status')
        
        feature = get_object_or_404(Feature, pk=feature_id)
        old_status = feature.status
        feature.status = new_status
        
        # Update timestamps based on status
        if new_status == 'IN_PROGRESS' and not feature.implementation_started_at:
            feature.implementation_started_at = timezone.now()
        elif new_status == 'DONE':
            feature.implementation_completed_at = timezone.now()
            feature.progress_percentage = 100
        
        feature.save()
        
        # Log the change
        FeatureHistory.objects.create(
            feature=feature,
            user=request.user,
            action='status_changed',
            field_name='status',
            old_value=old_status,
            new_value=new_status
        )
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def inline_edit_feature(request):
    """Inline edit feature fields"""
    try:
        data = json.loads(request.body)
        feature_id = data.get('feature_id')
        field_name = data.get('field_name')
        new_value = data.get('new_value')
        
        feature = get_object_or_404(Feature, pk=feature_id)
        
        # Validate field name
        allowed_fields = ['title', 'description', 'estimated_effort', 'priority']
        if field_name not in allowed_fields:
            return JsonResponse({'status': 'error', 'message': 'Invalid field'}, status=400)
        
        old_value = getattr(feature, field_name)
        setattr(feature, field_name, new_value)
        feature.save(update_fields=[field_name])
        
        # Log the change
        FeatureHistory.objects.create(
            feature=feature,
            user=request.user,
            action='inline_edited',
            field_name=field_name,
            old_value=str(old_value),
            new_value=str(new_value)
        )
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_POST
def add_feature_comment(request, pk):
    """Add comment to feature"""
    feature = get_object_or_404(Feature, pk=pk)
    form = FeatureCommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.feature = feature
        comment.user = request.user
        comment.save()
        
        messages.success(request, 'Comment added successfully!')
        return redirect('features:detail', pk=pk)
    
    messages.error(request, 'Error adding comment.')
    return redirect('features:detail', pk=pk)


@login_required
def create_from_template(request, template_id):
    """Create feature from template"""
    template = get_object_or_404(FeatureTemplate, pk=template_id)
    
    if request.method == 'POST':
        form = FeatureForm(request.POST)
        if form.is_valid():
            feature = form.save(commit=False)
            feature.created_by = request.user
            feature.is_template_based = True
            feature.source_template = template
            feature.save()
            
            messages.success(request, f'Feature created from template "{template.name}"')
            return redirect('features:detail', pk=feature.pk)
    else:
        # Pre-fill form with template data
        initial_data = {
            'title': template.name,
            'description': template.description,
            'category': template.category,
            'priority': template.default_priority,
            'estimated_effort': template.default_effort,
        }
        
        # Add template content if available
        if template.template_content:
            initial_data.update(template.template_content)
        
        form = FeatureForm(initial=initial_data)
    
    return render(request, 'features/feature_form.html', {
        'form': form,
        'template': template,
        'is_from_template': True
    })


@login_required
@require_POST
def bulk_action(request):
    """Handle bulk actions on features"""
    try:
        data = json.loads(request.body)
        feature_ids = data.get('feature_ids', [])
        action = data.get('action')
        
        features = Feature.objects.filter(pk__in=feature_ids)
        
        if action == 'archive':
            features.update(status='ARCHIVED')
            message = f'{features.count()} features archived'
        elif action == 'delete':
            count = features.count()
            features.delete()
            message = f'{count} features deleted'
        elif action == 'assign':
            agent = data.get('agent')
            for feature in features:
                if agent not in feature.assigned_agents:
                    feature.assigned_agents.append(agent)
                    feature.save()
            message = f'{features.count()} features assigned to {agent}'
        elif action == 'set_priority':
            priority = data.get('priority')
            features.update(priority=priority)
            message = f'{features.count()} features priority set to {priority}'
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)
        
        return JsonResponse({'status': 'success', 'message': message})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def plan_feature(request, pk):
    """Plan feature for implementation"""
    feature = get_object_or_404(Feature, pk=pk)
    
    if request.method == 'POST':
        # Update feature with planning details
        feature.status = 'PLANNED'
        feature.implementation_notes = request.POST.get('implementation_notes', '')
        feature.acceptance_criteria = request.POST.get('acceptance_criteria', '')
        feature.save()
        
        # Create tasks if provided
        tasks_data = json.loads(request.POST.get('tasks', '[]'))
        for i, task_data in enumerate(tasks_data):
            FeatureTask.objects.create(
                feature=feature,
                title=task_data.get('title'),
                description=task_data.get('description', ''),
                assigned_agent=task_data.get('agent', ''),
                order=i
            )
        
        messages.success(request, f'Feature "{feature.title}" planned successfully!')
        return redirect('features:detail', pk=pk)
    
    return render(request, 'features/feature_plan.html', {
        'feature': feature,
        'available_agents': ['backend', 'frontend', 'infrastructure', 'security', 'testing']
    })


@login_required
@require_POST
def implement_feature(request, pk):
    """Start implementation of a feature"""
    feature = get_object_or_404(Feature, pk=pk)
    
    # Mark feature as in progress
    feature.start_implementation()
    
    # Start first task if exists
    first_task = feature.tasks.filter(status='PENDING').first()
    if first_task:
        first_task.start()
    
    messages.success(request, f'Implementation started for "{feature.title}"')
    return redirect('features:detail', pk=pk)


@login_required
def feature_statistics(request):
    """Feature statistics dashboard"""
    features = Feature.objects.exclude(status='ARCHIVED')
    
    # Calculate statistics
    stats = {
        'by_status': {},
        'by_priority': {},
        'by_category': {},
        'by_month': {},
        'effort_by_status': {},
        'completion_rate': 0,
        'avg_completion_time': 0,
    }
    
    # Group by status
    for status_code, status_name in Feature.STATUS_CHOICES:
        if status_code != 'ARCHIVED':
            count = features.filter(status=status_code).count()
            stats['by_status'][status_name] = count
    
    # Group by priority
    for priority_code, priority_name in Feature.PRIORITY_CHOICES:
        count = features.filter(priority=priority_code).count()
        stats['by_priority'][priority_name] = count
    
    # Group by category
    for category in FeatureCategory.objects.all():
        count = features.filter(category=category).count()
        stats['by_category'][category.name] = count
    
    # Features created by month (last 6 months)
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_features = features.filter(created_at__gte=six_months_ago)
    
    for feature in monthly_features:
        month_key = feature.created_at.strftime('%Y-%m')
        month_name = feature.created_at.strftime('%b %Y')
        if month_name not in stats['by_month']:
            stats['by_month'][month_name] = 0
        stats['by_month'][month_name] += 1
    
    # Calculate completion rate
    total = features.count()
    completed = features.filter(status='DONE').count()
    if total > 0:
        stats['completion_rate'] = round((completed / total) * 100, 1)
    
    # Average completion time
    completed_features = features.filter(
        status='DONE',
        implementation_started_at__isnull=False,
        implementation_completed_at__isnull=False
    )
    
    if completed_features.exists():
        total_time = timedelta()
        for feature in completed_features:
            total_time += (feature.implementation_completed_at - feature.implementation_started_at)
        avg_time = total_time / completed_features.count()
        stats['avg_completion_time'] = avg_time.days
    
    return render(request, 'features/feature_statistics.html', {'stats': stats})