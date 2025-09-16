"""URL patterns for tasks app."""
from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.TaskListView.as_view(), name='list'),
    path('create/', views.TaskCreateView.as_view(), name='create'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='detail'),
    path('<int:pk>/assign/', views.assign_task, name='assign'),
    path('<int:pk>/execute/', views.execute_task, name='execute'),
    path('<int:pk>/cancel/', views.cancel_task, name='cancel'),
    path('api/queue/', views.api_task_queue, name='api_queue'),
    path('api/create/', views.api_create_task, name='api_create'),
    path('templates/', views.template_list, name='templates'),
    path('templates/<int:pk>/create/', views.create_from_template, name='create_from_template'),
]