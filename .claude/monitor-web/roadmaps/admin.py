from django.contrib import admin
from .models import (
    ProductManager, Roadmap, Feature, FeatureOverlap,
    FeatureDependency, ApprovalWorkflow, WorkflowHistory,
    PlatformBacklog, RoadmapSync
)


@admin.register(ProductManager)
class ProductManagerAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'agent_name', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['name', 'agent_name', 'description']


@admin.register(Roadmap)
class RoadmapAdmin(admin.ModelAdmin):
    list_display = ['title', 'product_manager', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'product_manager', 'start_date']
    search_fields = ['title', 'description']
    date_hierarchy = 'start_date'


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['title', 'roadmap', 'category', 'priority', 'status', 'quarter', 'year']
    list_filter = ['category', 'priority', 'status', 'quarter', 'year', 'is_reusable']
    search_fields = ['title', 'description']
    list_editable = ['priority', 'status']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('Basic Information', {
            'fields': ['roadmap', 'title', 'description', 'category']
        }),
        ('Planning', {
            'fields': ['priority', 'status', 'quarter', 'year']
        }),
        ('Technical Details', {
            'fields': ['effort_days', 'technical_components', 'api_endpoints']
        }),
        ('Platform Analysis', {
            'fields': ['is_reusable', 'platform_score']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at']
        }),
    ]


@admin.register(FeatureOverlap)
class FeatureOverlapAdmin(admin.ModelAdmin):
    list_display = ['feature1', 'feature2', 'similarity_score', 'overlap_type', 'platform_candidate']
    list_filter = ['overlap_type', 'platform_candidate']
    search_fields = ['feature1__title', 'feature2__title', 'notes']


@admin.register(FeatureDependency)
class FeatureDependencyAdmin(admin.ModelAdmin):
    list_display = ['feature', 'depends_on', 'dependency_type', 'created_at']
    list_filter = ['dependency_type', 'created_at']
    search_fields = ['feature__title', 'depends_on__title', 'notes']


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = ['feature', 'current_state', 'assigned_pm', 'assigned_techlead', 'approved_by']
    list_filter = ['current_state', 'created_at']
    search_fields = ['feature__title', 'assigned_techlead']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WorkflowHistory)
class WorkflowHistoryAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'from_state', 'to_state', 'changed_by', 'timestamp']
    list_filter = ['timestamp', 'from_state', 'to_state']
    search_fields = ['workflow__feature__title', 'notes']
    readonly_fields = ['timestamp']


@admin.register(PlatformBacklog)
class PlatformBacklogAdmin(admin.ModelAdmin):
    list_display = ['feature', 'platform_priority', 'business_value', 'technical_complexity']
    list_filter = ['platform_priority', 'business_value', 'technical_complexity']
    search_fields = ['feature__title', 'notes']
    list_editable = ['platform_priority']


@admin.register(RoadmapSync)
class RoadmapSyncAdmin(admin.ModelAdmin):
    list_display = ['source_roadmap', 'target_roadmap', 'last_sync', 'features_synced', 'overlaps_identified']
    list_filter = ['last_sync']
    search_fields = ['source_roadmap__title', 'target_roadmap__title']
