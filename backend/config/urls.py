from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .ninja_api import api

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Django Ninja API - Primary API
    path('api/', api.urls),
    
    # Health Check
    path('health/', include('health_check.urls')),
    
    # Development Tools
    path('silk/', include('silk.urls', namespace='silk')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
