"""URL patterns for logs app."""
from django.urls import path
from . import views

app_name = 'logs'

urlpatterns = [
    path('', views.LogListView.as_view(), name='list'),
    path('git/', views.git_commits_view, name='git_commits'),
    path('workflows/', views.workflow_logs_view, name='workflows'),
    path('performance/', views.performance_view, name='performance'),
    path('api/stream/', views.api_logs_stream, name='api_stream'),
    path('api/stats/', views.api_log_stats, name='api_stats'),
]