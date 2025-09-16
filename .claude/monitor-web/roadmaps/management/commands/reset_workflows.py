from django.core.management.base import BaseCommand
from roadmaps.models import Feature, ApprovalWorkflow, WorkflowHistory

class Command(BaseCommand):
    help = 'Reset workflows for all features'

    def handle(self, *args, **options):
        # Ensure all features have workflows
        for feature in Feature.objects.all():
            if not hasattr(feature, 'workflow'):
                workflow = ApprovalWorkflow.objects.create(
                    feature=feature,
                    current_state='draft' if feature.status == 'backlog' else 'pm_review'
                )
                self.stdout.write(f"Created workflow for {feature.title}")
            else:
                # Reset features that are stuck
                if feature.workflow.current_state in ['approved', 'rejected']:
                    feature.workflow.current_state = 'draft'
                    feature.workflow.save()
                    self.stdout.write(f"Reset workflow for {feature.title} to draft")
                else:
                    self.stdout.write(f"{feature.title}: {feature.workflow.current_state}")
        
        self.stdout.write(self.style.SUCCESS('Successfully reset workflows'))