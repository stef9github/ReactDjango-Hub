"""URL patterns for agents app."""
from django.urls import path
from . import views

app_name = 'agents'

urlpatterns = [
    path('', views.AgentListView.as_view(), name='list'),
    path('<int:pk>/', views.AgentDetailView.as_view(), name='detail'),
    path('<int:pk>/start/', views.start_agent, name='start'),
    path('<int:pk>/stop/', views.stop_agent, name='stop'),
    path('<int:pk>/restart/', views.restart_agent, name='restart'),
    path('api/<int:pk>/status/', views.api_agent_status, name='api_status'),
    path('api/<int:pk>/logs/', views.api_agent_logs, name='api_logs'),
    path('conflicts/', views.conflicts_view, name='conflicts'),
    path('conflicts/<int:pk>/resolve/', views.resolve_conflict, name='resolve_conflict'),
]