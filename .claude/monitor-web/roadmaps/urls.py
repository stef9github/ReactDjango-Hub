from django.urls import path
from . import views

urlpatterns = [
    path('', views.roadmap_dashboard, name='roadmap_dashboard'),
    path('feature-comparison/', views.feature_comparison, name='feature_comparison'),
    path('generate/<str:pm_type>/', views.generate_roadmap, name='generate_roadmap'),
    path('create-platform-feature/', views.create_platform_feature, name='create_platform_feature'),
    path('workflow/<int:feature_id>/update/', views.update_workflow_state, name='update_workflow_state'),
    path('workflow/<int:feature_id>/implement/', views.implement_feature, name='implement_feature'),
    path('analyze-overlaps/', views.analyze_overlaps, name='analyze_overlaps'),
    path('workflow/', views.workflow_management, name='workflow_management'),
    path('platform-backlog/', views.platform_backlog_view, name='platform_backlog'),
    path('sprint/', views.sprint_view, name='sprint_view'),
    path('agent/<int:agent_id>/invoke/', views.invoke_agent, name='invoke_agent'),
    path('agent-control/', views.agent_control_panel, name='agent_control_panel'),
]