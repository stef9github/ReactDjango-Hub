from django.urls import path
from . import views

app_name = 'features'

urlpatterns = [
    # Main views
    path('', views.FeatureListView.as_view(), name='list'),
    path('kanban/', views.FeatureKanbanView.as_view(), name='kanban'),
    path('roadmap/', views.FeatureRoadmapView.as_view(), name='roadmap'),
    path('statistics/', views.feature_statistics, name='statistics'),
    
    # CRUD operations
    path('create/', views.FeatureCreateView.as_view(), name='create'),
    path('<int:pk>/', views.FeatureDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.FeatureUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.FeatureDeleteView.as_view(), name='delete'),
    
    # Feature actions
    path('<int:pk>/plan/', views.plan_feature, name='plan'),
    path('<int:pk>/implement/', views.implement_feature, name='implement'),
    path('<int:pk>/comment/', views.add_feature_comment, name='add_comment'),
    
    # Template operations
    path('template/<int:template_id>/create/', views.create_from_template, name='create_from_template'),
    
    # AJAX endpoints
    path('ajax/update-order/', views.update_feature_order, name='update_order'),
    path('ajax/update-status/', views.update_feature_status, name='update_status'),
    path('ajax/inline-edit/', views.inline_edit_feature, name='inline_edit'),
    path('ajax/bulk-action/', views.bulk_action, name='bulk_action'),
]