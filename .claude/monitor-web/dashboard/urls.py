"""URL patterns for dashboard app."""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='index'),
    path('api/metrics/', views.api_metrics, name='api_metrics'),
    path('api/metrics/history/', views.api_metrics_history, name='api_metrics_history'),
    path('api/alerts/', views.api_alerts, name='api_alerts'),
]