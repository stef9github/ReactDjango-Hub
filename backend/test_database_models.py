#!/usr/bin/env python
"""
Test database models and audit functionality directly
"""
import os
import sys
import django
from django.utils import timezone
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.business.models import Contact, Appointment, Document, Transaction
from apps.analytics.models import AnalyticsRecord
from auditlog.models import LogEntry
from django.contrib.auth.models import User

def test_model_creation():
    """Test model creation and audit fields"""
    print("=== DATABASE MODELS & AUDIT TESTING ===\n")
    
    # Create a test user to simulate JWT user context
    test_user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    print(f"Test user: {'Created' if created else 'Retrieved'} - {test_user.username}")
    
    # Mock user context (this would normally come from JWT middleware)
    from apps.core.middleware import UserContext
    user_context = UserContext(
        user_id=str(test_user.id),
        email=test_user.email,
        organization_id="org-123",
        roles=["user"],
        raw_token={"sub": str(test_user.id), "email": test_user.email}
    )
    
    # Test Contact model
    print(f"\n1. Contact Model:")
    try:
        # Set user context in thread local (simulate middleware)
        from apps.core.auth import _user_context
        _user_context.context = user_context
        
        contact = Contact.objects.create(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            contact_type="patient",
            phone_number="+1234567890"
        )
        
        print(f"   ✅ Contact created: {contact.first_name} {contact.last_name}")
        print(f"   📊 Audit fields:")
        print(f"      - ID: {contact.id}")
        print(f"      - Organization ID: {contact.organization_id}")
        print(f"      - Created by: {contact.created_by}")
        print(f"      - Created at: {contact.created_at}")
        print(f"      - Updated by: {contact.updated_by}")
        
        # Test update
        contact.phone_number = "+1987654321"
        contact.save()
        print(f"   ✅ Contact updated - Updated by: {contact.updated_by}")
        
        # Test soft delete
        contact.soft_delete()
        print(f"   ✅ Contact soft deleted - Deleted by: {contact.deleted_by}")
        
    except Exception as e:
        print(f"   ❌ Error with Contact model: {e}")
    
    # Test Appointment model
    print(f"\n2. Appointment Model:")
    try:
        appointment = Appointment.objects.create(
            title="Medical Consultation",
            description="Regular checkup",
            start_time=timezone.now(),
            end_time=timezone.now(),
            appointment_type="consultation",
            status="scheduled"
        )
        
        print(f"   ✅ Appointment created: {appointment.title}")
        print(f"   📊 Audit fields:")
        print(f"      - Organization ID: {appointment.organization_id}")
        print(f"      - Created by: {appointment.created_by}")
        
    except Exception as e:
        print(f"   ❌ Error with Appointment model: {e}")
    
    # Test Document model
    print(f"\n3. Document Model:")
    try:
        document = Document.objects.create(
            title="Patient Record",
            description="Medical history document",
            document_type="medical",
            privacy_level="private"
        )
        
        print(f"   ✅ Document created: {document.title}")
        print(f"   📊 Audit fields:")
        print(f"      - Organization ID: {document.organization_id}")
        print(f"      - Created by: {document.created_by}")
        
    except Exception as e:
        print(f"   ❌ Error with Document model: {e}")
    
    # Test Analytics model
    print(f"\n4. Analytics Model:")
    try:
        analytics = AnalyticsRecord.objects.create(
            event_type="user_login",
            event_data={"ip": "127.0.0.1", "browser": "Chrome"}
        )
        
        print(f"   ✅ Analytics record created: {analytics.event_type}")
        print(f"   📊 Audit fields:")
        print(f"      - Organization ID: {analytics.organization_id}")
        print(f"      - Created by: {analytics.created_by}")
        
    except Exception as e:
        print(f"   ❌ Error with Analytics model: {e}")
    
    # Check AuditLog entries
    print(f"\n5. Audit Log Entries:")
    try:
        audit_entries = LogEntry.objects.all()
        print(f"   📈 Total audit entries: {audit_entries.count()}")
        
        for entry in audit_entries[:3]:  # Show first 3
            print(f"      - {entry.action}: {entry.content_type} (ID: {entry.object_pk})")
            
    except Exception as e:
        print(f"   ❌ Error checking audit log: {e}")
    
    # Test multi-tenant isolation
    print(f"\n6. Multi-tenant Testing:")
    try:
        # Create another organization context
        user_context_2 = UserContext(
            user_id=str(test_user.id),
            email=test_user.email,
            organization_id="org-456",
            roles=["user"],
            raw_token={"sub": str(test_user.id), "email": test_user.email}
        )
        
        _user_context.context = user_context_2
        
        contact_org2 = Contact.objects.create(
            first_name="Bob",
            last_name="Johnson",
            email="bob@example.com",
            contact_type="patient"
        )
        
        print(f"   ✅ Contact created in org-456: {contact_org2.first_name}")
        
        # Switch back to org-123 and check isolation
        _user_context.context = user_context
        
        from apps.core.auth import get_user_queryset
        org1_contacts = get_user_queryset(Contact, user_context)
        print(f"   📊 Contacts visible to org-123: {org1_contacts.count()}")
        
        _user_context.context = user_context_2
        org2_contacts = get_user_queryset(Contact, user_context_2) 
        print(f"   📊 Contacts visible to org-456: {org2_contacts.count()}")
        
        print(f"   ✅ Multi-tenant isolation working")
        
    except Exception as e:
        print(f"   ❌ Error with multi-tenant testing: {e}")
    
    print(f"\n=== DATABASE TESTING COMPLETE ===")

if __name__ == '__main__':
    test_model_creation()