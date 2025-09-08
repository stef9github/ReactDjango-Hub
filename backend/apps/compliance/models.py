from django.db import models
from apps.core.models import BaseModel


class ComplianceRecord(BaseModel):
    """Basic compliance record model."""
    regulation_type = models.CharField(max_length=100)
    status = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.regulation_type}: {self.status}"