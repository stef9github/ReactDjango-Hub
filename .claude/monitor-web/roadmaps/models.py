from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ProductManager(models.Model):
    """Represents a product manager (surgical, procurement, or platform)"""
    MANAGER_TYPES = [
        ('surgical', 'Surgical Practice Management'),
        ('procurement', 'Public Procurement'),
        ('platform', 'Platform/Generic'),
    ]
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=MANAGER_TYPES)
    agent_name = models.CharField(max_length=100)  # e.g., 'ag-surgical-product-manager'
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Roadmap(models.Model):
    """A product roadmap for a specific product manager"""
    product_manager = models.ForeignKey(ProductManager, on_delete=models.CASCADE, related_name='roadmaps')
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.product_manager.name}"


class Feature(models.Model):
    """A feature in a roadmap"""
    FEATURE_CATEGORIES = [
        ('platform', 'Platform/Generic'),
        ('specific', 'Industry Specific'),
    ]
    
    PRIORITY_LEVELS = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    STATUS_CHOICES = [
        ('proposed', 'Proposed'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    
    QUARTERS = [
        ('Q1', 'Q1'),
        ('Q2', 'Q2'),
        ('Q3', 'Q3'),
        ('Q4', 'Q4'),
    ]
    
    roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='features')
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=FEATURE_CATEGORIES)
    priority = models.CharField(max_length=20, choices=PRIORITY_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='proposed')
    quarter = models.CharField(max_length=10, choices=QUARTERS)
    year = models.IntegerField()
    
    # Technical details
    effort_days = models.IntegerField(null=True, blank=True)
    technical_components = models.JSONField(default=list)  # List of technical components
    api_endpoints = models.JSONField(default=list)  # List of API endpoints
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Platform analysis
    is_reusable = models.BooleanField(default=False)
    platform_score = models.FloatField(default=0.0)  # Score indicating platform potential (0-1)
    
    class Meta:
        ordering = ['year', 'quarter', '-priority']
    
    def __str__(self):
        return f"{self.title} ({self.get_category_display()}) - {self.quarter} {self.year}"


class FeatureOverlap(models.Model):
    """Tracks overlapping features between different roadmaps"""
    feature1 = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='overlaps_as_feature1')
    feature2 = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='overlaps_as_feature2')
    similarity_score = models.FloatField()  # 0-1 score indicating similarity
    overlap_type = models.CharField(max_length=50)  # e.g., 'identical', 'similar', 'related'
    platform_candidate = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['feature1', 'feature2']
    
    def __str__(self):
        return f"Overlap: {self.feature1.title} <-> {self.feature2.title} ({self.similarity_score:.2f})"


class FeatureDependency(models.Model):
    """Tracks dependencies between features"""
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='dependencies')
    depends_on = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='dependents')
    dependency_type = models.CharField(max_length=50)  # e.g., 'requires', 'blocks', 'related'
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['feature', 'depends_on']
    
    def __str__(self):
        return f"{self.feature.title} depends on {self.depends_on.title}"


class ApprovalWorkflow(models.Model):
    """Workflow for feature approval"""
    WORKFLOW_STATES = [
        ('draft', 'Draft'),
        ('pm_review', 'PM Review'),
        ('tech_review', 'Technical Review'),
        ('documentation', 'Documentation'),
        ('user_approval', 'User Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    feature = models.OneToOneField(Feature, on_delete=models.CASCADE, related_name='workflow')
    current_state = models.CharField(max_length=20, choices=WORKFLOW_STATES, default='draft')
    
    # Assignments
    assigned_pm = models.ForeignKey(ProductManager, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_workflows')
    assigned_techlead = models.CharField(max_length=100, blank=True)
    assigned_agents = models.JSONField(default=list)  # List of agent names for implementation
    
    # Documentation
    technical_doc = models.TextField(blank=True)
    implementation_plan = models.TextField(blank=True)
    test_plan = models.TextField(blank=True)
    
    # Tracking
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Workflow for {self.feature.title} ({self.get_current_state_display()})"


class WorkflowHistory(models.Model):
    """History of workflow state changes"""
    workflow = models.ForeignKey(ApprovalWorkflow, on_delete=models.CASCADE, related_name='history')
    from_state = models.CharField(max_length=20)
    to_state = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.workflow.feature.title}: {self.from_state} -> {self.to_state}"


class PlatformBacklog(models.Model):
    """Platform-wide backlog for common features"""
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    platform_priority = models.IntegerField()  # Platform-specific priority
    business_value = models.IntegerField()  # 1-10 scale
    technical_complexity = models.IntegerField()  # 1-10 scale
    products_benefited = models.JSONField(default=list)  # List of products that benefit
    estimated_savings_hours = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['platform_priority']
    
    def __str__(self):
        return f"Platform Backlog: {self.feature.title} (Priority: {self.platform_priority})"


class RoadmapSync(models.Model):
    """Tracks synchronization between product roadmaps"""
    source_roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='syncs_as_source')
    target_roadmap = models.ForeignKey(Roadmap, on_delete=models.CASCADE, related_name='syncs_as_target')
    last_sync = models.DateTimeField()
    features_synced = models.IntegerField(default=0)
    overlaps_identified = models.IntegerField(default=0)
    platform_candidates = models.IntegerField(default=0)
    sync_notes = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ['source_roadmap', 'target_roadmap']
    
    def __str__(self):
        return f"Sync: {self.source_roadmap.title} <-> {self.target_roadmap.title}"
