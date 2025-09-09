# TODO: Update for auth-service integration
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated  # TODO: Replace with auth-service JWT
from django_filters.rest_framework import DjangoFilterBackend
from .models import ClinicalRecord
from .serializers import ClinicalRecordSerializer


class ClinicalRecordViewSet(viewsets.ModelViewSet):
    """
    TODO: Replace IsAuthenticated with auth-service JWT validation
    """
    queryset = ClinicalRecord.objects.all()
    serializer_class = ClinicalRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['title']
    ordering = ['-created_at']