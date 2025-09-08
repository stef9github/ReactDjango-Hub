from django.db import models
from apps.core.models import BaseModel


class ClinicalRecord(BaseModel):
    """Basic clinical record model."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.title
