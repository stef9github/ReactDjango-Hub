from django.core.management.base import BaseCommand
from features.models import FeatureCategory, FeatureTemplate, Feature
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Sets up initial feature categories and templates'

    def handle(self, *args, **options):
        # Create categories
        categories = [
            {'name': 'Frontend', 'color': '#3B82F6', 'icon': 'browser', 'description': 'User interface and client-side features'},
            {'name': 'Backend', 'color': '#10B981', 'icon': 'server', 'description': 'Server-side logic and APIs'},
            {'name': 'Infrastructure', 'color': '#F59E0B', 'icon': 'cloud', 'description': 'DevOps and infrastructure'},
            {'name': 'Security', 'color': '#EF4444', 'icon': 'shield', 'description': 'Security and compliance features'},
            {'name': 'Documentation', 'color': '#8B5CF6', 'icon': 'book', 'description': 'Documentation and guides'},
            {'name': 'Testing', 'color': '#EC4899', 'icon': 'check-circle', 'description': 'Testing and quality assurance'},
        ]
        
        for cat_data in categories:
            category, created = FeatureCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f"Created category: {category.name}")
        
        # Create templates
        backend_cat = FeatureCategory.objects.get(name='Backend')
        frontend_cat = FeatureCategory.objects.get(name='Frontend')
        
        templates = [
            {
                'name': 'API Endpoint',
                'description': 'Create a new REST API endpoint',
                'category': backend_cat,
                'default_priority': 'MEDIUM',
                'default_effort': 5,
                'template_content': {
                    'acceptance_criteria': '- Endpoint responds with correct status codes\n- Input validation is implemented\n- Response format is documented\n- Unit tests cover all cases',
                    'implementation_notes': '- Use Django REST Framework\n- Follow existing API patterns\n- Add swagger documentation'
                }
            },
            {
                'name': 'React Component',
                'description': 'Create a new React component',
                'category': frontend_cat,
                'default_priority': 'MEDIUM',
                'default_effort': 3,
                'template_content': {
                    'acceptance_criteria': '- Component renders correctly\n- Props are properly typed\n- Component is responsive\n- Unit tests are written',
                    'implementation_notes': '- Use functional components with hooks\n- Follow existing component patterns\n- Add Storybook story'
                }
            },
            {
                'name': 'Database Migration',
                'description': 'Database schema change',
                'category': backend_cat,
                'default_priority': 'HIGH',
                'default_effort': 8,
                'template_content': {
                    'acceptance_criteria': '- Migration runs without errors\n- Rollback is possible\n- Data integrity is maintained\n- Performance impact is acceptable',
                    'implementation_notes': '- Test migration on staging first\n- Consider backwards compatibility\n- Update related models and serializers'
                }
            },
            {
                'name': 'Bug Fix',
                'description': 'Fix a reported bug',
                'category': backend_cat,
                'default_priority': 'HIGH',
                'default_effort': 2,
                'template_content': {
                    'acceptance_criteria': '- Bug is reproducible before fix\n- Fix resolves the issue\n- No regressions introduced\n- Test case added to prevent recurrence',
                    'implementation_notes': '- Identify root cause\n- Consider edge cases\n- Update documentation if needed'
                }
            },
            {
                'name': 'UI Enhancement',
                'description': 'Improve user interface',
                'category': frontend_cat,
                'default_priority': 'LOW',
                'default_effort': 3,
                'template_content': {
                    'acceptance_criteria': '- Design follows UI guidelines\n- Feature is accessible\n- Works across browsers\n- Mobile responsive',
                    'implementation_notes': '- Use Tailwind CSS classes\n- Consider dark mode support\n- Test on different screen sizes'
                }
            }
        ]
        
        for tmpl_data in templates:
            template, created = FeatureTemplate.objects.get_or_create(
                name=tmpl_data['name'],
                defaults=tmpl_data
            )
            if created:
                self.stdout.write(f"Created template: {template.name}")
        
        # Create sample features
        admin_user = User.objects.filter(username='admin').first()
        if admin_user:
            sample_features = [
                {
                    'title': 'Add user authentication to API',
                    'description': 'Implement JWT-based authentication for API endpoints',
                    'status': 'IN_PROGRESS',
                    'priority': 'HIGH',
                    'category': backend_cat,
                    'estimated_effort': 8,
                    'assigned_agents': ['backend', 'security'],
                    'progress_percentage': 60,
                    'tags': ['authentication', 'security', 'api']
                },
                {
                    'title': 'Create dashboard component',
                    'description': 'Build main dashboard component with metrics display',
                    'status': 'PLANNED',
                    'priority': 'MEDIUM',
                    'category': frontend_cat,
                    'estimated_effort': 5,
                    'assigned_agents': ['frontend'],
                    'progress_percentage': 0,
                    'tags': ['dashboard', 'ui', 'metrics']
                },
                {
                    'title': 'Setup CI/CD pipeline',
                    'description': 'Configure GitHub Actions for automated testing and deployment',
                    'status': 'BACKLOG',
                    'priority': 'MEDIUM',
                    'category': FeatureCategory.objects.get(name='Infrastructure'),
                    'estimated_effort': 13,
                    'assigned_agents': ['infrastructure'],
                    'progress_percentage': 0,
                    'tags': ['cicd', 'automation', 'deployment']
                },
                {
                    'title': 'Write API documentation',
                    'description': 'Document all API endpoints with examples',
                    'status': 'TESTING',
                    'priority': 'LOW',
                    'category': FeatureCategory.objects.get(name='Documentation'),
                    'estimated_effort': 3,
                    'assigned_agents': ['documentation'],
                    'progress_percentage': 80,
                    'tags': ['documentation', 'api']
                },
                {
                    'title': 'Implement data caching',
                    'description': 'Add Redis caching for frequently accessed data',
                    'status': 'DONE',
                    'priority': 'HIGH',
                    'category': backend_cat,
                    'estimated_effort': 8,
                    'assigned_agents': ['backend', 'infrastructure'],
                    'progress_percentage': 100,
                    'tags': ['performance', 'caching', 'redis']
                }
            ]
            
            for i, feat_data in enumerate(sample_features):
                feat_data['created_by'] = admin_user
                feat_data['priority_order'] = i
                feature, created = Feature.objects.get_or_create(
                    title=feat_data['title'],
                    defaults=feat_data
                )
                if created:
                    self.stdout.write(f"Created feature: {feature.title}")
        
        self.stdout.write(self.style.SUCCESS('Successfully set up features app'))