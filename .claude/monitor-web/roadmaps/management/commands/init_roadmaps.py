from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from roadmaps.models import ProductManager, Roadmap, Feature, FeatureOverlap, ApprovalWorkflow, PlatformBacklog


class Command(BaseCommand):
    help = 'Initialize roadmap data with sample features'

    def handle(self, *args, **options):
        self.stdout.write('Initializing roadmap data...')
        
        # Create Product Managers
        surgical_pm, _ = ProductManager.objects.get_or_create(
            type='surgical',
            defaults={
                'name': 'Surgical Practice Product Manager',
                'agent_name': 'ag-surgical-product-manager',
                'description': 'Manages surgical practice management product roadmap'
            }
        )
        
        procurement_pm, _ = ProductManager.objects.get_or_create(
            type='procurement',
            defaults={
                'name': 'Public Procurement Product Manager',
                'agent_name': 'ag-public-procurement-product-manager',
                'description': 'Manages public procurement product roadmap'
            }
        )
        
        platform_pm, _ = ProductManager.objects.get_or_create(
            type='platform',
            defaults={
                'name': 'Platform Product Manager',
                'agent_name': 'ag-platform-product-manager',
                'description': 'Manages shared platform features'
            }
        )
        
        # Create Roadmaps
        start_date = date.today()
        end_date = start_date + timedelta(days=180)
        
        surgical_roadmap, _ = Roadmap.objects.get_or_create(
            product_manager=surgical_pm,
            is_active=True,
            defaults={
                'title': 'Surgical Practice Q1-Q2 2025 Roadmap',
                'description': '6-month roadmap for surgical practice management platform',
                'start_date': start_date,
                'end_date': end_date
            }
        )
        
        procurement_roadmap, _ = Roadmap.objects.get_or_create(
            product_manager=procurement_pm,
            is_active=True,
            defaults={
                'title': 'Public Procurement Q1-Q2 2025 Roadmap',
                'description': '6-month roadmap for public procurement platform',
                'start_date': start_date,
                'end_date': end_date
            }
        )
        
        platform_roadmap, _ = Roadmap.objects.get_or_create(
            product_manager=platform_pm,
            is_active=True,
            defaults={
                'title': 'Platform Features Q1-Q2 2025',
                'description': 'Shared platform features roadmap',
                'start_date': start_date,
                'end_date': end_date
            }
        )
        
        # Create Surgical Features
        surgical_features = [
            {
                'title': 'Patient Portal',
                'description': 'Web and mobile portal for patients to access medical records, schedule appointments, and communicate with providers',
                'category': 'platform',
                'priority': 'high',
                'quarter': 'Q1',
                'year': 2025,
                'effort_days': 45,
                'technical_components': ['React', 'Django', 'PostgreSQL', 'JWT'],
                'api_endpoints': ['/api/patients/', '/api/appointments/', '/api/messages/'],
                'is_reusable': True,
                'platform_score': 0.9
            },
            {
                'title': 'Surgery Scheduling System',
                'description': 'Advanced OR scheduling with conflict detection, resource optimization, and staff assignment',
                'category': 'specific',
                'priority': 'critical',
                'quarter': 'Q1',
                'year': 2025,
                'effort_days': 60,
                'technical_components': ['Django', 'PostgreSQL', 'Celery', 'React'],
                'api_endpoints': ['/api/surgeries/', '/api/or-schedule/', '/api/staff-assignments/'],
                'is_reusable': False,
                'platform_score': 0.2
            },
            {
                'title': 'Document Management System',
                'description': 'Secure document storage, sharing, and version control with HIPAA compliance',
                'category': 'platform',
                'priority': 'high',
                'quarter': 'Q2',
                'year': 2025,
                'effort_days': 30,
                'technical_components': ['S3', 'Django', 'PostgreSQL', 'Encryption'],
                'api_endpoints': ['/api/documents/', '/api/versions/', '/api/sharing/'],
                'is_reusable': True,
                'platform_score': 0.95
            },
            {
                'title': 'Multi-channel Notification System',
                'description': 'Configurable notifications via email, SMS, and push for appointments, reminders, and alerts',
                'category': 'platform',
                'priority': 'high',
                'quarter': 'Q1',
                'year': 2025,
                'effort_days': 25,
                'technical_components': ['Celery', 'Redis', 'SendGrid', 'Twilio', 'FCM'],
                'api_endpoints': ['/api/notifications/', '/api/preferences/', '/api/templates/'],
                'is_reusable': True,
                'platform_score': 1.0
            },
            {
                'title': 'Medical Device Integration',
                'description': 'Integration with surgical equipment, monitoring devices, and medical imaging systems',
                'category': 'specific',
                'priority': 'medium',
                'quarter': 'Q2',
                'year': 2025,
                'effort_days': 40,
                'technical_components': ['HL7', 'FHIR', 'DICOM', 'Django', 'WebSocket'],
                'api_endpoints': ['/api/devices/', '/api/device-data/', '/api/imaging/'],
                'is_reusable': False,
                'platform_score': 0.1
            }
        ]
        
        for feature_data in surgical_features:
            Feature.objects.get_or_create(
                roadmap=surgical_roadmap,
                title=feature_data['title'],
                defaults=feature_data
            )
        
        # Create Procurement Features
        procurement_features = [
            {
                'title': 'Vendor Portal',
                'description': 'Self-service portal for vendors to register, submit bids, manage contracts, and track payments',
                'category': 'platform',
                'priority': 'high',
                'quarter': 'Q1',
                'year': 2025,
                'effort_days': 40,
                'technical_components': ['React', 'Django', 'PostgreSQL', 'JWT'],
                'api_endpoints': ['/api/vendors/', '/api/bids/', '/api/contracts/'],
                'is_reusable': True,
                'platform_score': 0.8
            },
            {
                'title': 'RFP Management System',
                'description': 'Create, publish, and manage requests for proposals with automated workflow',
                'category': 'specific',
                'priority': 'critical',
                'quarter': 'Q1',
                'year': 2025,
                'effort_days': 50,
                'technical_components': ['Django', 'PostgreSQL', 'Elasticsearch', 'Celery'],
                'api_endpoints': ['/api/rfps/', '/api/proposals/', '/api/evaluations/'],
                'is_reusable': False,
                'platform_score': 0.3
            },
            {
                'title': 'Document Repository',
                'description': 'Centralized document management with access controls and audit trail',
                'category': 'platform',
                'priority': 'high',
                'quarter': 'Q2',
                'year': 2025,
                'effort_days': 30,
                'technical_components': ['S3', 'Django', 'PostgreSQL', 'ElasticSearch'],
                'api_endpoints': ['/api/documents/', '/api/permissions/', '/api/audit/'],
                'is_reusable': True,
                'platform_score': 0.95
            },
            {
                'title': 'Automated Notifications',
                'description': 'Configurable notifications for bid deadlines, status updates, and announcements',
                'category': 'platform',
                'priority': 'high',
                'quarter': 'Q1',
                'year': 2025,
                'effort_days': 25,
                'technical_components': ['Celery', 'Redis', 'SendGrid', 'SMS Gateway'],
                'api_endpoints': ['/api/notifications/', '/api/subscriptions/', '/api/broadcasts/'],
                'is_reusable': True,
                'platform_score': 1.0
            },
            {
                'title': 'Compliance Tracking',
                'description': 'Track and ensure compliance with public procurement regulations and policies',
                'category': 'specific',
                'priority': 'high',
                'quarter': 'Q2',
                'year': 2025,
                'effort_days': 35,
                'technical_components': ['Django', 'PostgreSQL', 'Reporting Engine'],
                'api_endpoints': ['/api/compliance/', '/api/audits/', '/api/reports/'],
                'is_reusable': False,
                'platform_score': 0.4
            }
        ]
        
        for feature_data in procurement_features:
            Feature.objects.get_or_create(
                roadmap=procurement_roadmap,
                title=feature_data['title'],
                defaults=feature_data
            )
        
        # Identify and create overlaps
        self.stdout.write('Analyzing feature overlaps...')
        
        surgical_notification = Feature.objects.filter(
            roadmap=surgical_roadmap,
            title__icontains='notification'
        ).first()
        
        procurement_notification = Feature.objects.filter(
            roadmap=procurement_roadmap,
            title__icontains='notification'
        ).first()
        
        if surgical_notification and procurement_notification:
            FeatureOverlap.objects.get_or_create(
                feature1=surgical_notification,
                feature2=procurement_notification,
                defaults={
                    'similarity_score': 0.95,
                    'overlap_type': 'identical',
                    'platform_candidate': True,
                    'notes': 'Both products need multi-channel notification system'
                }
            )
        
        surgical_docs = Feature.objects.filter(
            roadmap=surgical_roadmap,
            title__icontains='document'
        ).first()
        
        procurement_docs = Feature.objects.filter(
            roadmap=procurement_roadmap,
            title__icontains='document'
        ).first()
        
        if surgical_docs and procurement_docs:
            FeatureOverlap.objects.get_or_create(
                feature1=surgical_docs,
                feature2=procurement_docs,
                defaults={
                    'similarity_score': 0.90,
                    'overlap_type': 'similar',
                    'platform_candidate': True,
                    'notes': 'Both need document management with different compliance requirements'
                }
            )
        
        # Create platform features
        platform_features = [
            {
                'title': 'Unified Notification Service',
                'description': 'Multi-channel notification system supporting email, SMS, push, and in-app notifications with template management',
                'category': 'platform',
                'priority': 'critical',
                'quarter': 'Q1',
                'year': 2025,
                'effort_days': 30,
                'technical_components': ['Celery', 'Redis', 'SendGrid', 'Twilio', 'FCM', 'Django'],
                'api_endpoints': ['/api/v1/notifications/', '/api/v1/templates/', '/api/v1/channels/'],
                'is_reusable': True,
                'platform_score': 1.0
            },
            {
                'title': 'Document Management Platform',
                'description': 'Enterprise document management with versioning, access control, and compliance features',
                'category': 'platform',
                'priority': 'high',
                'quarter': 'Q1',
                'year': 2025,
                'effort_days': 35,
                'technical_components': ['S3', 'Django', 'PostgreSQL', 'Elasticsearch', 'Encryption'],
                'api_endpoints': ['/api/v1/documents/', '/api/v1/folders/', '/api/v1/permissions/'],
                'is_reusable': True,
                'platform_score': 1.0
            },
            {
                'title': 'User Portal Framework',
                'description': 'Reusable portal framework for different user types with customizable dashboards',
                'category': 'platform',
                'priority': 'high',
                'quarter': 'Q2',
                'year': 2025,
                'effort_days': 40,
                'technical_components': ['React', 'Django', 'PostgreSQL', 'Redis', 'WebSocket'],
                'api_endpoints': ['/api/v1/portal/', '/api/v1/dashboards/', '/api/v1/widgets/'],
                'is_reusable': True,
                'platform_score': 1.0
            }
        ]
        
        for feature_data in platform_features:
            feature, created = Feature.objects.get_or_create(
                roadmap=platform_roadmap,
                title=feature_data['title'],
                defaults=feature_data
            )
            
            if created:
                # Create platform backlog entry
                PlatformBacklog.objects.create(
                    feature=feature,
                    platform_priority=len(PlatformBacklog.objects.all()) + 1,
                    business_value=9,
                    technical_complexity=6,
                    products_benefited=['surgical', 'procurement'],
                    estimated_savings_hours=100,
                    notes=f'Platform feature to replace product-specific implementations'
                )
                
                # Create approval workflow
                ApprovalWorkflow.objects.create(
                    feature=feature,
                    current_state='pm_review',
                    assigned_pm=platform_pm,
                    assigned_techlead='ag-techlead'
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully initialized roadmap data'))
        self.stdout.write(f'Created {Feature.objects.count()} features')
        self.stdout.write(f'Created {FeatureOverlap.objects.count()} overlaps')
        self.stdout.write(f'Created {PlatformBacklog.objects.count()} platform backlog items')