from django.db import models
from apps.core.models import BaseModel


class BusinessRecord(BaseModel):
    """Basic business record model."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.title


class Client(BaseModel):
    """Client model for business operations."""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.name
