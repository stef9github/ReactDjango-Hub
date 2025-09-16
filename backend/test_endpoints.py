#!/usr/bin/env python
"""
Test all API endpoints comprehensively
"""
import os
import sys
import django
import json
from django.test import Client

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def test_all_endpoints():
    """Test all API endpoints"""
    print("=== COMPREHENSIVE API ENDPOINT TESTING ===\n")
    
    client = Client()
    
    # Test API Documentation
    print("1. API Documentation:")
    try:
        response = client.get('/api/docs')
        if response.status_code == 200:
            print("✅ API docs accessible")
            # Check if it's HTML docs or JSON
            content_type = response.get('content-type', '')
            print(f"   Content-Type: {content_type}")
            if 'json' in content_type:
                print("   Format: JSON")
            elif 'html' in content_type:
                print("   Format: HTML documentation")
        else:
            print(f"❌ API docs issue: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test OpenAPI JSON
    print("\n2. OpenAPI Specification:")
    try:
        response = client.get('/api/openapi.json')
        if response.status_code == 200:
            spec = response.json()
            print("✅ OpenAPI spec accessible")
            print(f"   Title: {spec.get('info', {}).get('title', 'N/A')}")
            print(f"   Version: {spec.get('info', {}).get('version', 'N/A')}")
            print(f"   Paths: {len(spec.get('paths', {}))}")
            
            # Show available endpoints
            paths = list(spec.get('paths', {}).keys())
            print(f"   Available endpoints: {len(paths)}")
            for path in sorted(paths)[:5]:  # Show first 5
                print(f"     - {path}")
            if len(paths) > 5:
                print(f"     ... and {len(paths)-5} more")
        else:
            print(f"❌ OpenAPI spec issue: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test unauthenticated endpoints (should return 401)
    print("\n3. Authentication Requirements:")
    protected_endpoints = [
        '/api/business/contacts',
        '/api/business/appointments', 
        '/api/business/documents',
        '/api/business/transactions',
        '/api/analytics/records'
    ]
    
    for endpoint in protected_endpoints:
        try:
            response = client.get(endpoint)
            if response.status_code in [401, 403]:
                print(f"✅ {endpoint}: Properly protected ({response.status_code})")
            else:
                print(f"❌ {endpoint}: Not protected ({response.status_code})")
        except Exception as e:
            print(f"❌ {endpoint}: Error ({e})")
    
    # Test with mock JWT (should still fail validation but process)
    print("\n4. JWT Processing:")
    mock_jwt = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IlRlc3QgVXNlciIsImlhdCI6MTUxNjIzOTAyMn0.invalid-signature"
    
    try:
        response = client.get('/api/business/contacts', HTTP_AUTHORIZATION=mock_jwt)
        if response.status_code in [401, 403]:
            result = response.json() if response.content else {"message": "No content"}
            print(f"✅ JWT validation working: {response.status_code}")
            print(f"   Response: {result.get('message', result)}")
        else:
            print(f"❓ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n=== ENDPOINT TESTING COMPLETE ===")

if __name__ == '__main__':
    test_all_endpoints()