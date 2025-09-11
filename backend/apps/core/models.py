from django.db import models
from django.conf import settings
import uuid


class SoftDeleteManager(models.Manager):
    """Custom manager that excludes soft-deleted objects by default."""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteAllManager(models.Manager):
    """Manager that includes soft-deleted objects."""
    
    def get_queryset(self):
        return super().get_queryset()


class BaseModel(models.Model):
    """
    Base model with:
    - UUID primary key
    - Audit timestamps (created_at, updated_at)
    - Audit users (created_by, updated_by)
    - Multi-tenant support (organization_id)
    - Soft delete functionality
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Audit fields - track who created/modified records
    created_by = models.UUIDField(null=True, blank=True, help_text="User ID from Identity Service who created this record")
    updated_by = models.UUIDField(null=True, blank=True, help_text="User ID from Identity Service who last updated this record")
    
    # Multi-tenant support - organization isolation
    organization_id = models.UUIDField(null=True, blank=True, help_text="Organization ID from Identity Service for multi-tenant isolation")
    
    # Soft delete functionality
    is_deleted = models.BooleanField(default=False, help_text="Mark record as deleted without actually removing it")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when record was soft deleted")
    deleted_by = models.UUIDField(null=True, blank=True, help_text="User ID from Identity Service who deleted this record")
    
    # Managers
    objects = SoftDeleteManager()  # Default manager excludes deleted objects
    all_objects = SoftDeleteAllManager()  # Manager that includes deleted objects
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['organization_id']),
            models.Index(fields=['is_deleted']),
            models.Index(fields=['created_at']),
        ]
    
    def soft_delete(self, user_id=None):
        """Soft delete the object."""
        from django.utils import timezone
        from .middleware import get_current_user
        
        self.is_deleted = True
        self.deleted_at = timezone.now()
        
        # Use provided user_id, or get from current context
        if user_id:
            self.deleted_by = user_id
        else:
            current_user = get_current_user()
            if current_user:
                self.deleted_by = current_user.user_id
                
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
    
    def restore(self):
        """Restore a soft-deleted object."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
    
    def save(self, *args, **kwargs):
        """Override save to automatically set audit fields from user context."""
        from .middleware import get_current_user
        
        current_user = get_current_user()
        
        if current_user:
            # Set created_by and organization_id for new objects
            if self._state.adding:
                if not self.created_by:
                    self.created_by = current_user.user_id
                if not self.organization_id:
                    self.organization_id = current_user.organization_id
            
            # Always update updated_by for any save
            self.updated_by = current_user.user_id
        
        super().save(*args, **kwargs)
