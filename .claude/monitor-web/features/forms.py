from django import forms
from django.forms import ModelForm, widgets
from .models import (
    Feature, FeatureTemplate, FeatureComment, 
    FeatureTask, FeatureCategory, FeatureRoadmap
)


class FeatureForm(ModelForm):
    """Form for creating and editing features"""
    
    class Meta:
        model = Feature
        fields = [
            'title', 'description', 'detailed_description',
            'status', 'priority', 'category', 'tags',
            'estimated_effort', 'assigned_agents', 'assigned_to',
            'due_date', 'acceptance_criteria', 'implementation_notes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter feature title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of the feature'
            }),
            'detailed_description': forms.Textarea(attrs={
                'class': 'form-control tinymce',
                'rows': 10,
                'placeholder': 'Detailed description with formatting'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Comma-separated tags',
                'data-role': 'tagsinput'
            }),
            'estimated_effort': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 21,
                'placeholder': 'Story points (1-21)'
            }),
            'assigned_agents': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'backend, frontend, infrastructure',
                'data-role': 'tagsinput'
            }),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'acceptance_criteria': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Define acceptance criteria'
            }),
            'implementation_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Technical implementation notes'
            }),
        }
    
    def clean_tags(self):
        """Convert comma-separated tags to list"""
        tags = self.cleaned_data.get('tags', '')
        if isinstance(tags, str):
            return [tag.strip() for tag in tags.split(',') if tag.strip()]
        return tags
    
    def clean_assigned_agents(self):
        """Convert comma-separated agents to list"""
        agents = self.cleaned_data.get('assigned_agents', '')
        if isinstance(agents, str):
            return [agent.strip() for agent in agents.split(',') if agent.strip()]
        return agents


class FeatureTemplateForm(ModelForm):
    """Form for creating feature templates"""
    
    class Meta:
        model = FeatureTemplate
        fields = [
            'name', 'description', 'category',
            'default_priority', 'default_effort', 'template_content'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Template name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Template description'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'default_priority': forms.Select(attrs={'class': 'form-select'}),
            'default_effort': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 21
            }),
            'template_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'JSON template content'
            }),
        }


class FeatureCommentForm(ModelForm):
    """Form for adding comments to features"""
    
    class Meta:
        model = FeatureComment
        fields = ['content', 'is_internal']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add your comment...'
            }),
            'is_internal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'is_internal': 'Internal note (visible to team only)'
        }


class FeatureTaskForm(ModelForm):
    """Form for creating tasks from features"""
    
    AGENT_CHOICES = [
        ('backend', 'Backend Agent'),
        ('frontend', 'Frontend Agent'),
        ('infrastructure', 'Infrastructure Agent'),
        ('security', 'Security Agent'),
        ('testing', 'Testing Agent'),
        ('documentation', 'Documentation Agent'),
    ]
    
    assigned_agent = forms.ChoiceField(
        choices=AGENT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = FeatureTask
        fields = ['title', 'description', 'assigned_agent', 'order']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Task title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Task description'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
        }


class FeatureBulkActionForm(forms.Form):
    """Form for bulk actions on features"""
    
    ACTION_CHOICES = [
        ('archive', 'Archive Selected'),
        ('delete', 'Delete Selected'),
        ('assign', 'Assign to Agent'),
        ('set_priority', 'Set Priority'),
        ('set_status', 'Set Status'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    feature_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    # Optional fields for specific actions
    agent = forms.ChoiceField(
        choices=FeatureTaskForm.AGENT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    priority = forms.ChoiceField(
        choices=Feature.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=Feature.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class FeatureCategoryForm(ModelForm):
    """Form for creating feature categories"""
    
    class Meta:
        model = FeatureCategory
        fields = ['name', 'color', 'icon', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Icon name (e.g., folder, code, database)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Category description'
            }),
        }


class FeatureRoadmapForm(ModelForm):
    """Form for creating roadmaps"""
    
    class Meta:
        model = FeatureRoadmap
        fields = ['name', 'description', 'start_date', 'end_date', 'features', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Roadmap name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Roadmap description'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'features': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 10
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class FeatureFilterForm(forms.Form):
    """Form for filtering features in list view"""
    
    status = forms.ChoiceField(
        choices=[('all', 'All Status')] + Feature.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    priority = forms.ChoiceField(
        choices=[('all', 'All Priority')] + Feature.PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    category = forms.ModelChoiceField(
        queryset=FeatureCategory.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Search features...'
        })
    )
    
    show_archived = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Show Archived'
    )