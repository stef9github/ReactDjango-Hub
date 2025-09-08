from rest_framework import serializers
from .models import AnalyticsRecord


class AnalyticsRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyticsRecord
        fields = ['id', 'metric_name', 'metric_value', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']