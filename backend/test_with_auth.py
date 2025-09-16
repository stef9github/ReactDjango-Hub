#!/usr/bin/env python
"""
Test API endpoints with real JWT authentication
"""
import os
import sys
import django
import requests
import json
from django.test import Client

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def get_jwt_token():
    """Get a JWT token from the Identity Service"""
    print("=== OBTAINING JWT TOKEN ===")
    
    # Test user credentials
    test_user = {
        "email": "test@example.com",
        "password": "testpass123",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        # First, try to register a test user
        register_response = requests.post(
            'http://localhost:8001/auth/register',
            json=test_user,
            timeout=10
        )
        print(f"Registration attempt: {register_response.status_code}")
        
        # Login to get JWT token (whether registration succeeded or failed)
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        
        login_response = requests.post(
            'http://localhost:8001/auth/login',
            json=login_data,
            timeout=10
        )
        
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            jwt_token = token_data.get('access_token')
            print(f"✅ JWT token obtained: {jwt_token[:20]}...{jwt_token[-10:] if jwt_token else 'None'}")
            return jwt_token
        else:
            print(f"❌ Login failed: {login_response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Identity Service")
        return None
    except Exception as e:
        print(f"❌ Error getting JWT: {e}")
        return None

def test_authenticated_endpoints(jwt_token):
    """Test endpoints with valid JWT token"""
    print(f"\n=== TESTING WITH VALID JWT ===")
    
    if not jwt_token:
        print("❌ No JWT token available, skipping authenticated tests")
        return
    
    client = Client()
    auth_header = f"Bearer {jwt_token}"
    
    # Test Contacts API
    print("\n1. Contacts API:")
    
    # List contacts (should be empty initially)
    try:
        response = client.get('/api/business/contacts', HTTP_AUTHORIZATION=auth_header)
        print(f"   GET /api/business/contacts: {response.status_code}")
        if response.status_code == 200:
            contacts = response.json()
            print(f"   ✅ Success: Found {len(contacts)} contacts")
        else:
            error_data = response.json() if response.content else {"message": "No content"}
            print(f"   ❌ Error: {error_data}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Create a contact
    test_contact = {
        "first_name": "John",
        "last_name": "Doe", 
        "email": "john.doe@example.com",
        "contact_type": "patient"
    }
    
    try:
        response = client.post(
            '/api/business/contacts',
            data=json.dumps(test_contact),
            content_type='application/json',
            HTTP_AUTHORIZATION=auth_header
        )
        print(f"   POST /api/business/contacts: {response.status_code}")
        if response.status_code in [200, 201]:
            contact = response.json()
            print(f"   ✅ Contact created: {contact.get('first_name')} {contact.get('last_name')}")
            contact_id = contact.get('id')
            return contact_id
        else:
            error_data = response.json() if response.content else {"message": "No content"}
            print(f"   ❌ Error creating contact: {error_data}")
    except Exception as e:
        print(f"   ❌ Exception creating contact: {e}")
    
    # Test Analytics API
    print("\n2. Analytics API:")
    try:
        response = client.get('/api/analytics/records', HTTP_AUTHORIZATION=auth_header)
        print(f"   GET /api/analytics/records: {response.status_code}")
        if response.status_code == 200:
            records = response.json()
            print(f"   ✅ Success: Found {len(records)} analytics records")
        else:
            error_data = response.json() if response.content else {"message": "No content"}
            print(f"   ❌ Error: {error_data}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def test_audit_functionality(jwt_token):
    """Test audit trail functionality"""
    print(f"\n=== TESTING AUDIT FUNCTIONALITY ===")
    
    if not jwt_token:
        print("❌ No JWT token available, skipping audit tests")
        return
    
    # The audit functionality would be tested by:
    # 1. Creating records and checking created_by is populated
    # 2. Updating records and checking updated_by is populated  
    # 3. Deleting records and checking deleted_by is populated
    # 4. Checking AuditLog entries are created
    
    print("Note: Audit functionality testing requires database inspection")
    print("This would typically be done with Django test fixtures and database queries")

def main():
    """Main testing function"""
    print("=== COMPREHENSIVE AUTHENTICATION & API TESTING ===\n")
    
    # Get JWT token from Identity Service
    jwt_token = get_jwt_token()
    
    # Test authenticated endpoints
    test_authenticated_endpoints(jwt_token)
    
    # Test audit functionality
    test_audit_functionality(jwt_token)
    
    print(f"\n=== TESTING COMPLETE ===")

if __name__ == '__main__':
    main()