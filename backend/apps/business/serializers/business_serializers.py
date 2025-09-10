from rest_framework import serializers
from ..models import BusinessRecord, Client


class BusinessRecordSerializer(serializers.ModelSerializer):
    """Serializer for BusinessRecord model"""
    
    class Meta:
        model = BusinessRecord
        fields = ['id', 'title', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model"""
    
    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'phone', 'company', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def validate_email(self, value):
        """Ensure email is unique"""
        if Client.objects.filter(email=value).exists():
            raise serializers.ValidationError("A client with this email already exists.")
        return value