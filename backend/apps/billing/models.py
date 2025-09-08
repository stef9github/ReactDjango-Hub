from django.db import models
from apps.core.models import BaseModel


class BillingRecord(BaseModel):
    """Basic billing record model."""
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)
    
    def __str__(self):
        return f"${self.amount} - {self.description}"
