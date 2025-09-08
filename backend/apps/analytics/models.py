from django.db import models
from apps.core.models import BaseModel
from auditlog.registry import auditlog


class AnalyticsRecord(BaseModel):
    """Basic analytics record model with audit logging."""
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    
    class Meta:
        permissions = [
            ("view_analytics_data", "Can view analytics data"),
            ("export_analytics_data", "Can export analytics data"),
        ]
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value}"


# Register model for audit logging (HIPAA compliance)
auditlog.register(AnalyticsRecord)