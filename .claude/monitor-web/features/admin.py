from django.contrib import admin
from .models import (
    Feature, FeatureCategory, FeatureTemplate, 
    FeatureHistory, FeatureComment, FeatureTask,
    FeatureAttachment, FeatureRoadmap
)


@admin.register(FeatureCategory)
class FeatureCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'icon', 'description']
    search_fields = ['name', 'description']


@admin.register(FeatureTemplate)
class FeatureTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'default_priority', 'default_effort', 'created_at']
    list_filter = ['category', 'default_priority', 'created_at']
    search_fields = ['name', 'description']


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'status', 'category', 'estimated_effort', 
                    'progress_percentage', 'created_at']
    list_filter = ['status', 'priority', 'category', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['priority_order', '-priority', '-created_at']
    readonly_fields = ['created_at', 'updated_at', 'progress_percentage']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'detailed_description')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'priority_order', 'progress_percentage')
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('Assignment & Effort', {
            'fields': ('estimated_effort', 'assigned_agents', 'assigned_to')
        }),
        ('Dates', {
            'fields': ('due_date', 'implementation_started_at', 'implementation_completed_at',
                      'created_at', 'updated_at')
        }),
        ('Workflow', {
            'fields': ('is_template_based', 'source_template', 'implementation_notes', 
                      'acceptance_criteria')
        }),
        ('Relations', {
            'fields': ('parent_feature', 'dependencies', 'related_commits')
        })
    )


@admin.register(FeatureHistory)
class FeatureHistoryAdmin(admin.ModelAdmin):
    list_display = ['feature', 'user', 'action', 'field_name', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['feature__title', 'user__username', 'action']
    readonly_fields = ['feature', 'user', 'timestamp', 'action', 'field_name', 
                      'old_value', 'new_value', 'comment']


@admin.register(FeatureComment)
class FeatureCommentAdmin(admin.ModelAdmin):
    list_display = ['feature', 'user', 'created_at', 'is_internal']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['feature__title', 'user__username', 'content']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FeatureTask)
class FeatureTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'feature', 'assigned_agent', 'status', 'order', 'created_at']
    list_filter = ['status', 'assigned_agent', 'created_at']
    search_fields = ['title', 'feature__title', 'description']
    ordering = ['order', 'created_at']


@admin.register(FeatureAttachment)
class FeatureAttachmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'feature', 'uploaded_by', 'uploaded_at', 'file_size']
    list_filter = ['uploaded_at']
    search_fields = ['name', 'feature__title']
    readonly_fields = ['uploaded_at', 'file_size', 'mime_type']


@admin.register(FeatureRoadmap)
class FeatureRoadmapAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_active', 'created_by']
    list_filter = ['is_active', 'start_date']
    search_fields = ['name', 'description']
    filter_horizontal = ['features']
