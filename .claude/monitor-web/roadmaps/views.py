from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime, date, timedelta
import json
import subprocess
import tempfile
import os
from .models import (
    ProductManager, Roadmap, Feature, FeatureOverlap,
    FeatureDependency, ApprovalWorkflow, WorkflowHistory,
    PlatformBacklog, RoadmapSync
)


def roadmap_dashboard(request):
    """Main dashboard showing all roadmaps side by side"""
    surgical_pm = ProductManager.objects.filter(type='surgical').first()
    procurement_pm = ProductManager.objects.filter(type='procurement').first()
    platform_pm = ProductManager.objects.filter(type='platform').first()
    
    surgical_roadmap = None
    procurement_roadmap = None
    platform_roadmap = None
    
    if surgical_pm:
        surgical_roadmap = Roadmap.objects.filter(product_manager=surgical_pm, is_active=True).first()
    if procurement_pm:
        procurement_roadmap = Roadmap.objects.filter(product_manager=procurement_pm, is_active=True).first()
    if platform_pm:
        platform_roadmap = Roadmap.objects.filter(product_manager=platform_pm, is_active=True).first()
    
    # Get feature overlaps
    overlaps = FeatureOverlap.objects.filter(platform_candidate=True).select_related('feature1', 'feature2')
    
    # Get platform backlog
    platform_backlog = PlatformBacklog.objects.all()[:10]
    
    # Get recent workflow updates
    recent_workflows = ApprovalWorkflow.objects.exclude(current_state='approved').order_by('-updated_at')[:5]
    
    context = {
        'surgical_roadmap': surgical_roadmap,
        'procurement_roadmap': procurement_roadmap,
        'platform_roadmap': platform_roadmap,
        'overlaps': overlaps,
        'platform_backlog': platform_backlog,
        'recent_workflows': recent_workflows,
    }
    
    return render(request, 'roadmaps/dashboard.html', context)


def feature_comparison(request):
    """Compare features across roadmaps to identify platform opportunities"""
    surgical_features = Feature.objects.filter(
        roadmap__product_manager__type='surgical',
        roadmap__is_active=True
    )
    procurement_features = Feature.objects.filter(
        roadmap__product_manager__type='procurement',
        roadmap__is_active=True
    )
    
    # Analyze for common patterns
    platform_candidates = []
    
    for s_feature in surgical_features:
        for p_feature in procurement_features:
            similarity = calculate_feature_similarity(s_feature, p_feature)
            if similarity > 0.6:  # 60% similarity threshold
                platform_candidates.append({
                    'surgical': s_feature,
                    'procurement': p_feature,
                    'similarity': similarity,
                    'suggested_platform_feature': suggest_platform_feature(s_feature, p_feature)
                })
    
    context = {
        'surgical_features': surgical_features,
        'procurement_features': procurement_features,
        'platform_candidates': platform_candidates,
    }
    
    return render(request, 'roadmaps/feature_comparison.html', context)


def calculate_feature_similarity(feature1, feature2):
    """Calculate similarity score between two features"""
    # Simple keyword-based similarity for now
    keywords1 = set(feature1.title.lower().split() + feature1.description.lower().split())
    keywords2 = set(feature2.title.lower().split() + feature2.description.lower().split())
    
    intersection = keywords1.intersection(keywords2)
    union = keywords1.union(keywords2)
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)


def suggest_platform_feature(feature1, feature2):
    """Suggest a platform feature based on two similar features"""
    # Extract common keywords
    keywords1 = set(feature1.title.lower().split())
    keywords2 = set(feature2.title.lower().split())
    common_keywords = keywords1.intersection(keywords2)
    
    title = ' '.join(common_keywords).title() + " Platform Service"
    description = f"Common functionality extracted from:\n- {feature1.title}\n- {feature2.title}"
    
    return {
        'title': title,
        'description': description,
        'category': 'platform',
    }


@require_http_methods(["POST"])
def generate_roadmap(request, pm_type):
    """Generate roadmap by calling the appropriate product manager agent"""
    try:
        # Get or create product manager
        pm, created = ProductManager.objects.get_or_create(
            type=pm_type,
            defaults={
                'name': f'{pm_type.title()} Product Manager',
                'agent_name': f'ag-{pm_type}-product-manager',
                'description': f'Product manager for {pm_type} products'
            }
        )
        
        # Create roadmap
        start_date = date.today()
        end_date = start_date + timedelta(days=180)  # 6 months
        
        roadmap = Roadmap.objects.create(
            product_manager=pm,
            title=f'{pm_type.title()} 6-Month Roadmap',
            description=f'Generated roadmap for {pm_type} product',
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        
        # Call the agent to generate features
        features_data = call_agent_for_roadmap(pm.agent_name)
        
        # Create features from agent response
        for feature_data in features_data:
            Feature.objects.create(
                roadmap=roadmap,
                title=feature_data.get('title', ''),
                description=feature_data.get('description', ''),
                category=feature_data.get('category', 'specific'),
                priority=feature_data.get('priority', 'medium'),
                quarter=feature_data.get('quarter', 'Q1'),
                year=feature_data.get('year', 2025),
                effort_days=feature_data.get('effort_days'),
                technical_components=feature_data.get('technical_components', []),
                api_endpoints=feature_data.get('api_endpoints', []),
                is_reusable=feature_data.get('category') == 'platform',
                platform_score=feature_data.get('platform_score', 0.0)
            )
        
        messages.success(request, f"Successfully generated {pm_type} roadmap with {len(features_data)} features")
        
    except Exception as e:
        messages.error(request, f"Failed to generate roadmap: {str(e)}")
    
    return redirect('roadmap_dashboard')


def call_agent_for_roadmap(agent_name):
    """Call an agent to generate roadmap features"""
    # For now, return sample data. In production, this would call the actual agent
    if 'surgical' in agent_name:
        return [
            {
                'title': 'Patient Portal',
                'description': 'Web and mobile portal for patients to access records, schedule appointments',
                'category': 'platform',
                'priority': 'high',
                'quarter': 'Q4',
                'year': 2025,
                'effort_days': 45,
                'technical_components': ['React', 'Django', 'PostgreSQL'],
                'api_endpoints': ['/api/patients/', '/api/appointments/'],
                'platform_score': 0.9
            },
            {
                'title': 'Surgery Scheduling System',
                'description': 'Advanced OR scheduling with conflict detection and resource optimization',
                'category': 'specific',
                'priority': 'critical',
                'quarter': 'Q4',
                'year': 2025,
                'effort_days': 60,
                'technical_components': ['Django', 'PostgreSQL', 'Celery'],
                'api_endpoints': ['/api/surgeries/', '/api/or-schedule/'],
                'platform_score': 0.2
            },
            {
                'title': 'Document Management',
                'description': 'Secure document storage and sharing with version control',
                'category': 'platform',
                'priority': 'high',
                'quarter': 'Q1',
                'year': 2026,
                'effort_days': 3,  # AI-assisted: 3 days
                'technical_components': ['S3', 'Django', 'PostgreSQL'],
                'api_endpoints': ['/api/documents/', '/api/versions/'],
                'platform_score': 0.95
            },
            {
                'title': 'Notification System',
                'description': 'Multi-channel notifications (email, SMS, push) for appointments and alerts',
                'category': 'platform',
                'priority': 'high',
                'quarter': 'Q4',
                'year': 2025,
                'effort_days': 25,
                'technical_components': ['Celery', 'Redis', 'SendGrid', 'Twilio'],
                'api_endpoints': ['/api/notifications/', '/api/preferences/'],
                'platform_score': 1.0
            },
            {
                'title': 'Medical Device Integration',
                'description': 'Integration with surgical equipment and monitoring devices',
                'category': 'specific',
                'priority': 'medium',
                'quarter': 'Q1',
                'year': 2026,
                'effort_days': 40,
                'technical_components': ['HL7', 'FHIR', 'Django'],
                'api_endpoints': ['/api/devices/', '/api/device-data/'],
                'platform_score': 0.1
            }
        ]
    elif 'procurement' in agent_name:
        return [
            {
                'title': 'Vendor Portal',
                'description': 'Portal for vendors to submit bids and manage contracts',
                'category': 'platform',
                'priority': 'high',
                'quarter': 'Q4',
                'year': 2025,
                'effort_days': 40,
                'technical_components': ['React', 'Django', 'PostgreSQL'],
                'api_endpoints': ['/api/vendors/', '/api/bids/'],
                'platform_score': 0.8
            },
            {
                'title': 'RFP Management System',
                'description': 'Create, publish, and manage requests for proposals',
                'category': 'specific',
                'priority': 'critical',
                'quarter': 'Q4',
                'year': 2025,
                'effort_days': 50,
                'technical_components': ['Django', 'PostgreSQL', 'Elasticsearch'],
                'api_endpoints': ['/api/rfps/', '/api/proposals/'],
                'platform_score': 0.3
            },
            {
                'title': 'Document Management',
                'description': 'Centralized document repository with access controls',
                'category': 'platform',
                'priority': 'high',
                'quarter': 'Q1',
                'year': 2026,
                'effort_days': 3,  # AI-assisted: 3 days
                'technical_components': ['S3', 'Django', 'PostgreSQL'],
                'api_endpoints': ['/api/documents/', '/api/permissions/'],
                'platform_score': 0.95
            },
            {
                'title': 'Notification System',
                'description': 'Automated notifications for bid deadlines and updates',
                'category': 'platform',
                'priority': 'high',
                'quarter': 'Q4',
                'year': 2025,
                'effort_days': 25,
                'technical_components': ['Celery', 'Redis', 'SendGrid'],
                'api_endpoints': ['/api/notifications/', '/api/subscriptions/'],
                'platform_score': 1.0
            },
            {
                'title': 'Compliance Tracking',
                'description': 'Track and ensure compliance with procurement regulations',
                'category': 'specific',
                'priority': 'high',
                'quarter': 'Q1',
                'year': 2026,
                'effort_days': 35,
                'technical_components': ['Django', 'PostgreSQL'],
                'api_endpoints': ['/api/compliance/', '/api/audits/'],
                'platform_score': 0.4
            }
        ]
    else:
        return []


@require_http_methods(["POST"])
def create_platform_feature(request):
    """Create a platform feature from the agent control panel"""
    from agents.models import Agent
    from tasks.models import Task
    from datetime import date, timedelta
    import json
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    data = json.loads(request.body)
    
    # Get or create platform PM
    platform_pm, created = ProductManager.objects.get_or_create(
        type='platform',
        defaults={
            'name': 'Platform Product Manager',
            'agent_name': 'ag-platform-product-manager',
            'description': 'Manages common platform features'
        }
    )
    
    # Get or create platform roadmap
    platform_roadmap, created = Roadmap.objects.get_or_create(
        product_manager=platform_pm,
        is_active=True,
        defaults={
            'title': 'Platform Roadmap',
            'description': 'Common platform features roadmap',
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=180)
        }
    )
    
    # Calculate week based on effort days (AI-accelerated development)
    current_week = date.today().isocalendar()[1]
    effort_days = int(data.get('effort_days', 3))
    
    # Create platform feature
    feature = Feature.objects.create(
        roadmap=platform_roadmap,
        title=data.get('title'),
        description=data.get('description'),
        category='platform',
        priority=data.get('priority', 'high'),
        quarter=f'Week {current_week}',  # Using weeks instead of quarters
        year=date.today().year,
        effort_days=effort_days,
        is_reusable=True,
        platform_score=1.0
    )
    
    # Create platform backlog entry
    PlatformBacklog.objects.create(
        feature=feature,
        platform_priority=1,
        business_value=8,
        technical_complexity=5,
        products_benefited=['surgical', 'procurement'],
        estimated_savings_hours=effort_days * 8  # Convert days to hours
    )
    
    # Create tasks for assigned agents
    assigned_agents = data.get('assigned_agents', [])
    if assigned_agents:
        for agent_id in assigned_agents:
            try:
                agent = Agent.objects.get(id=agent_id)
                Task.objects.create(
                    title=f"Implement {feature.title}",
                    description=f"Implement platform feature: {feature.description}",
                    task_type='implementation',
                    priority=3 if feature.priority == 'critical' else 2,
                    assigned_to=agent,
                    assigned_at=timezone.now(),
                    estimated_duration=effort_days * 480,  # days to minutes
                    context={
                        'feature_id': feature.id,
                        'feature_title': feature.title,
                        'priority': feature.priority
                    }
                )
            except Agent.DoesNotExist:
                continue
    
    # Create approval workflow
    ApprovalWorkflow.objects.create(
        feature=feature,
        assigned_pm=platform_pm,
        assigned_techlead='ag-techlead'
    )
    
    return JsonResponse({'success': True, 'feature_id': feature.id})


@require_http_methods(["POST"])
def update_workflow_state(request, feature_id):
    """Update the workflow state for a feature"""
    feature = get_object_or_404(Feature, id=feature_id)
    workflow = feature.workflow
    
    data = json.loads(request.body)
    new_state = data.get('state')
    notes = data.get('notes', '')
    
    # Record history
    WorkflowHistory.objects.create(
        workflow=workflow,
        from_state=workflow.current_state,
        to_state=new_state,
        changed_by=request.user if request.user.is_authenticated else None,
        notes=notes
    )
    
    # Update workflow
    workflow.current_state = new_state
    
    if new_state == 'approved':
        workflow.approved_at = timezone.now()
        workflow.approved_by = request.user if request.user.is_authenticated else None
    
    workflow.save()
    
    return JsonResponse({'success': True, 'new_state': new_state})


@require_http_methods(["POST"])
def analyze_overlaps(request):
    """Analyze features for overlaps and platform opportunities"""
    surgical_features = Feature.objects.filter(
        roadmap__product_manager__type='surgical',
        roadmap__is_active=True
    )
    procurement_features = Feature.objects.filter(
        roadmap__product_manager__type='procurement',
        roadmap__is_active=True
    )
    
    overlaps_created = 0
    
    for s_feature in surgical_features:
        for p_feature in procurement_features:
            similarity = calculate_feature_similarity(s_feature, p_feature)
            
            if similarity > 0.5:  # 50% similarity threshold
                overlap, created = FeatureOverlap.objects.get_or_create(
                    feature1=s_feature,
                    feature2=p_feature,
                    defaults={
                        'similarity_score': similarity,
                        'overlap_type': 'similar' if similarity < 0.8 else 'identical',
                        'platform_candidate': similarity > 0.7,
                        'notes': f"Automated analysis detected {similarity*100:.1f}% similarity"
                    }
                )
                
                if created:
                    overlaps_created += 1
    
    messages.success(request, f"Analysis complete. Found {overlaps_created} new overlaps.")
    return redirect('feature_comparison')


def workflow_management(request):
    """Manage approval workflows"""
    workflows = ApprovalWorkflow.objects.all().select_related('feature', 'assigned_pm')
    
    context = {
        'workflows': workflows,
        'workflow_states': ApprovalWorkflow.WORKFLOW_STATES,
    }
    
    return render(request, 'roadmaps/workflow_management.html', context)


def platform_backlog_view(request):
    """View and manage platform backlog"""
    backlog = PlatformBacklog.objects.all().select_related('feature')
    
    context = {
        'backlog': backlog,
    }
    
    return render(request, 'roadmaps/platform_backlog.html', context)


def implement_feature(request, feature_id):
    """Start implementation of an approved feature"""
    from agents.models import Agent
    from tasks.models import Task
    
    feature = get_object_or_404(Feature, id=feature_id)
    
    if request.method == "GET":
        # Show implementation planning page
        context = {
            "feature": feature,
            "available_agents": Agent.objects.filter(status__in=["idle", "running"]),
        }
        return render(request, "roadmaps/implement_feature.html", context)
    
    elif request.method == "POST":
        # Create tasks and start implementation
        lead_agent_id = request.POST.get("lead_agent")
        task_titles = request.POST.getlist("task_titles[]")
        task_descriptions = request.POST.getlist("task_descriptions[]")
        task_agents = request.POST.getlist("task_agents[]")
        auto_start = request.POST.get("auto_start") == "on"
        
        # Create tasks for the feature
        created_tasks = []
        for i, title in enumerate(task_titles):
            if title.strip():
                agent_id = task_agents[i] if i < len(task_agents) and task_agents[i] else lead_agent_id
                task = Task.objects.create(
                    title=f"{feature.title}: {title}",
                    description=task_descriptions[i] if i < len(task_descriptions) else "",
                    assigned_agent_id=agent_id if agent_id else None,
                    priority=3,  # Medium priority
                    status="pending" if not auto_start else "running",
                    metadata={"feature_id": feature.id, "feature_title": feature.title}
                )
                created_tasks.append(task)
        
        # Update feature status
        feature.status = "in_progress"
        feature.save()
        
        # Update workflow
        if hasattr(feature, "workflow"):
            WorkflowHistory.objects.create(
                workflow=feature.workflow,
                from_state=feature.workflow.current_state,
                to_state="in_development",
                notes=f"Implementation started with {len(created_tasks)} tasks"
            )
        
        messages.success(request, f"Created {len(created_tasks)} tasks for {feature.title}")
        return redirect("tasks:list")



def sprint_view(request):
    """Show features organized by weekly sprints"""
    from datetime import date, timedelta
    from collections import defaultdict
    
    current_date = date.today()
    current_week = current_date.isocalendar()[1]
    
    # Get all active features
    features = Feature.objects.filter(
        roadmap__is_active=True
    ).select_related("workflow").order_by("quarter", "priority")
    
    # Group features by week
    weekly_features = defaultdict(list)
    for feature in features:
        weekly_features[feature.quarter].append(feature)
    
    # Get features for this week
    features_this_week = [f for f in features if f"Week {current_week}" in f.quarter]
    total_effort_this_week = sum(f.effort_days or 0 for f in features_this_week)
    
    context = {
        "current_week": current_week,
        "current_date": current_date,
        "next_week": current_week + 1,
        "next_week_date": current_date + timedelta(days=7),
        "weekly_features": dict(weekly_features),
        "features_this_week": features_this_week,
        "total_effort_this_week": total_effort_this_week,
    }
    
    return render(request, "roadmaps/sprint_view.html", context)



def invoke_agent(request, agent_id):
    """Invoke a Claude agent from the web interface"""
    from agents.models import Agent
    import subprocess
    import os
    
    agent = get_object_or_404(Agent, id=agent_id)
    
    if request.method == "POST":
        data = json.loads(request.body)
        action = data.get("action")
        instructions = data.get("instructions", "")
        
        # Build the command to invoke the Claude agent
        agent_script = f"/Users/stephanerichard/Documents/CODING/ReactDjango-Hub/.claude/launch-agent.sh"
        
        # Map agent names to their script names
        agent_map = {
            "ag-backend": "backend",
            "ag-frontend": "frontend",
            "ag-identity": "identity",
            "ag-communication": "communication",
            "ag-content": "content",
            "ag-workflow": "workflow",
            "ag-infrastructure": "infrastructure",
            "ag-coordinator": "coordinator",
            "ag-security": "security",
            "ag-reviewer": "reviewer",
            "ag-techlead": "techlead",
        }
        
        agent_script_name = agent_map.get(agent.name, agent.name.replace("ag-", ""))
        
        # Build the command
        command = f"{agent_script} {agent_script_name}"
        
        # Add specific instructions based on action
        if action == "implement-features":
            command += " \"Implement the approved features in the backlog\""
        elif action == "fix-bugs":
            command += " \"Find and fix bugs in the codebase\""
        elif action == "write-tests":
            command += " \"Write comprehensive tests for the codebase\""
        elif action == "refactor":
            command += " \"Refactor and improve code quality\""
        elif action == "custom" and instructions:
            command += f" \"{instructions}\""
        
        # Log the invocation
        messages.success(request, f"Invoked {agent.name} with command: {command}")
        
        return JsonResponse({
            "success": True,
            "command": command,
            "message": f"Agent {agent.name} has been invoked"
        })
    
    return JsonResponse({"error": "Method not allowed"}, status=405)


def agent_control_panel(request):
    """Show the agent control panel"""
    from agents.models import Agent
    from tasks.models import Task
    
    agents = Agent.objects.all()
    
    # Add pending tasks to each agent
    for agent in agents:
        agent.pending_tasks = Task.objects.filter(
            assigned_to=agent,
            status__in=["pending", "running"]
        )[:3]
    
    context = {
        "agents": agents,
    }
    
    return render(request, "agents/agent_control.html", context)

