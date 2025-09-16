from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class FeatureCategory(models.Model):
    """Categories for organizing features"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#6B7280')  # Hex color
    icon = models.CharField(max_length=50, default='folder')
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Feature Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class FeatureTemplate(models.Model):
    """Predefined templates for quick feature creation"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.ForeignKey(FeatureCategory, on_delete=models.SET_NULL, null=True, blank=True)
    default_priority = models.CharField(max_length=10, choices=[
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical')
    ], default='MEDIUM')
    default_effort = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(21)])
    template_content = models.JSONField(default=dict)  # Store structured template data
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Feature(models.Model):
    """Main feature model for tracking development features"""
    STATUS_CHOICES = [
        ('BACKLOG', 'Backlog'),
        ('PLANNED', 'Planned'),
        ('IN_PROGRESS', 'In Progress'),
        ('TESTING', 'Testing'),
        ('REVIEW', 'Review'),
        ('DONE', 'Done'),
        ('ARCHIVED', 'Archived'),
        ('BLOCKED', 'Blocked')
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical')
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField()
    detailed_description = models.TextField(blank=True)  # Rich text content
    
    # Status and Priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BACKLOG')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    priority_order = models.IntegerField(default=0)  # For drag-and-drop ordering
    
    # Categorization
    category = models.ForeignKey(FeatureCategory, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)  # Store as JSON array
    
    # Effort and Assignment
    estimated_effort = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(21)],
        help_text="Story points (1-21 Fibonacci scale)"
    )
    assigned_agents = models.JSONField(default=list, blank=True)  # List of agent names
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_features')
    
    # Progress Tracking
    progress_percentage = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    implementation_started_at = models.DateTimeField(null=True, blank=True)
    implementation_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Related Items
    parent_feature = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_features')
    dependencies = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='dependent_features')
    related_commits = models.JSONField(default=list, blank=True)  # Store commit hashes
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_features')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    # Additional fields for workflow
    is_template_based = models.BooleanField(default=False)
    source_template = models.ForeignKey(FeatureTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    implementation_notes = models.TextField(blank=True)
    acceptance_criteria = models.TextField(blank=True)
    
    class Meta:
        ordering = ['priority_order', '-priority', '-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['priority_order']),
        ]
    
    def __str__(self):
        return f"[{self.priority}] {self.title}"
    
    def get_priority_color(self):
        """Return color for priority level"""
        colors = {
            'LOW': '#10B981',      # Green
            'MEDIUM': '#F59E0B',   # Amber
            'HIGH': '#EF4444',     # Red
            'CRITICAL': '#7C3AED'  # Purple
        }
        return colors.get(self.priority, '#6B7280')
    
    def get_status_color(self):
        """Return color for status"""
        colors = {
            'BACKLOG': '#6B7280',     # Gray
            'PLANNED': '#3B82F6',     # Blue
            'IN_PROGRESS': '#F59E0B', # Amber
            'TESTING': '#8B5CF6',     # Purple
            'REVIEW': '#EC4899',      # Pink
            'DONE': '#10B981',        # Green
            'ARCHIVED': '#9CA3AF',    # Light Gray
            'BLOCKED': '#EF4444'      # Red
        }
        return colors.get(self.status, '#6B7280')
    
    def update_progress(self):
        """Calculate progress based on tasks or sub-features"""
        if self.sub_features.exists():
            total = self.sub_features.count()
            completed = self.sub_features.filter(status='DONE').count()
            self.progress_percentage = int((completed / total) * 100) if total > 0 else 0
            self.save(update_fields=['progress_percentage'])
    
    def start_implementation(self):
        """Mark feature as started"""
        self.status = 'IN_PROGRESS'
        self.implementation_started_at = timezone.now()
        self.save(update_fields=['status', 'implementation_started_at'])
    
    def complete_implementation(self):
        """Mark feature as completed"""
        self.status = 'DONE'
        self.implementation_completed_at = timezone.now()
        self.progress_percentage = 100
        self.save(update_fields=['status', 'implementation_completed_at', 'progress_percentage'])


class FeatureHistory(models.Model):
    """Track changes to features for audit trail"""
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50)  # created, updated, status_changed, etc.
    field_name = models.CharField(max_length=50, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Feature Histories"
    
    def __str__(self):
        return f"{self.feature.title} - {self.action} by {self.user} at {self.timestamp}"


class FeatureComment(models.Model):
    """Discussion and notes on features"""
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_internal = models.BooleanField(default=False)  # Internal notes vs public comments
    mentioned_users = models.ManyToManyField(User, blank=True, related_name='mentioned_in_comments')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment on {self.feature.title} by {self.user}"


class FeatureTask(models.Model):
    """Tasks generated from features for implementation"""
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField()
    assigned_agent = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('SKIPPED', 'Skipped')
    ], default='PENDING')
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    output = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.feature.title} - {self.title}"
    
    def start(self):
        """Mark task as started"""
        self.status = 'IN_PROGRESS'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def complete(self, output=''):
        """Mark task as completed"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.output = output
        self.save(update_fields=['status', 'completed_at', 'output'])
        # Update feature progress
        self.feature.update_progress()
    
    def fail(self, error_message=''):
        """Mark task as failed"""
        self.status = 'FAILED'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'error_message'])


class FeatureAttachment(models.Model):
    """File attachments for features"""
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='attachments')
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='feature_attachments/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.IntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.name} - {self.feature.title}"


class FeatureRoadmap(models.Model):
    """Roadmap planning for features"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    features = models.ManyToManyField(Feature, blank=True, related_name='roadmaps')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name
