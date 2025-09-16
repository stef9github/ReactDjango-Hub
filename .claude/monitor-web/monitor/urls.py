"""URL Configuration for monitor project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('agents/', include('agents.urls')),
    path('tasks/', include('tasks.urls')),
    path('logs/', include('logs.urls')),
    path('features/', include('features.urls')),
    path('roadmaps/', include('roadmaps.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)