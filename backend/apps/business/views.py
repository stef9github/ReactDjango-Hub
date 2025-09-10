# TODO: Update for auth-service integration
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated  # TODO: Replace with auth-service JWT
from django_filters.rest_framework import DjangoFilterBackend
from .models import BusinessRecord, Client
from .serializers import BusinessRecordSerializer, ClientSerializer


class BusinessRecordViewSet(viewsets.ModelViewSet):
    """
    TODO: Replace IsAuthenticated with auth-service JWT validation
    """
    queryset = BusinessRecord.objects.all()
    serializer_class = BusinessRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['title']
    ordering = ['-created_at']


class ClientViewSet(viewsets.ModelViewSet):
    """
    Client management viewset
    TODO: Replace IsAuthenticated with auth-service JWT validation
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'company']
    ordering = ['-created_at']