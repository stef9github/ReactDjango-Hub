# TODO: Update for auth-service integration
# Current DRF permissions need to be replaced with auth-service JWT validation
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from django_filters.rest_framework import DjangoFilterBackend
from guardian.shortcuts import get_objects_for_user
from .models import AnalyticsRecord
from .serializers import AnalyticsRecordSerializer


class AnalyticsRecordViewSet(viewsets.ModelViewSet):
    """
    TODO: Replace with auth-service integration
    - JWT token validation via auth-service
    - User permissions from auth-service
    """
    serializer_class = AnalyticsRecordSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['metric_name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter analytics records based on user permissions"""
        user = self.request.user
        if user.is_superuser:
            return AnalyticsRecord.objects.all()
        return get_objects_for_user(
            user, 
            'analytics.view_analyticsrecord',
            AnalyticsRecord.objects.all()
        )