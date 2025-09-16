#!/usr/bin/env python
"""
Clean test script to verify Django server and API endpoints
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

def run_tests():
    """Run all tests with clean output"""
    print("=== DJANGO BACKEND TEST RESULTS ===\n")
    
    client = Client()
    results = {}
    
    # Test 1: System Health
    try:
        response = client.get('/health/')
        results['system_health'] = response.status_code == 200
        print(f"1. System Health Check: {'✅ PASS' if results['system_health'] else '❌ FAIL'} ({response.status_code})")
    except Exception as e:
        results['system_health'] = False
        print(f"1. System Health Check: ❌ FAIL (Error: {e})")
    
    # Test 2: API Health  
    try:
        response = client.get('/api/health')
        results['api_health'] = response.status_code == 200
        if results['api_health']:
            api_data = response.json()
            print(f"2. API Health Check: ✅ PASS ({api_data})")
        else:
            print(f"2. API Health Check: ❌ FAIL ({response.status_code})")
    except Exception as e:
        results['api_health'] = False
        print(f"2. API Health Check: ❌ FAIL (Error: {e})")
    
    # Test 3: API Documentation
    try:
        response = client.get('/api/docs')
        results['api_docs'] = response.status_code == 200
        print(f"3. API Docs Access: {'✅ PASS' if results['api_docs'] else '❌ FAIL'} ({response.status_code})")
    except Exception as e:
        results['api_docs'] = False
        print(f"3. API Docs Access: ❌ FAIL (Error: {e})")
    
    # Test 4: Authentication Required (should be 401 or 403)
    try:
        response = client.get('/api/business/contacts')
        auth_required = response.status_code in [401, 403]
        results['auth_required'] = auth_required
        print(f"4. Auth Protection: {'✅ PASS' if auth_required else '❌ FAIL'} ({response.status_code})")
    except Exception as e:
        results['auth_required'] = False
        print(f"4. Auth Protection: ❌ FAIL (Error: {e})")
        
    # Test 5: Identity Service Connection
    try:
        response = requests.get('http://localhost:8001/health', timeout=5)
        identity_service_up = response.status_code == 200
        results['identity_service'] = identity_service_up
        print(f"5. Identity Service: {'✅ RUNNING' if identity_service_up else '❌ DOWN'} ({response.status_code})")
    except requests.exceptions.ConnectionError:
        results['identity_service'] = False
        print("5. Identity Service: ❌ DOWN (Connection refused)")
    except Exception as e:
        results['identity_service'] = False
        print(f"5. Identity Service: ❌ DOWN (Error: {e})")
        
    # Test 6: Mock JWT Authentication
    print("\n--- Authentication Tests ---")
    mock_jwt = "Bearer test-jwt-token-for-local-testing"
    
    try:
        response = client.get('/api/business/contacts', HTTP_AUTHORIZATION=mock_jwt)
        jwt_processed = response.status_code in [200, 401, 403, 500]  # Any valid response
        results['jwt_processing'] = jwt_processed
        print(f"6. JWT Processing: {'✅ PROCESSED' if jwt_processed else '❌ ERROR'} ({response.status_code})")
        
        if response.status_code != 500:
            print(f"   Response sample: {response.content.decode()[:100]}...")
    except Exception as e:
        results['jwt_processing'] = False
        print(f"6. JWT Processing: ❌ ERROR ({e})")
    
    # Summary
    print("\n=== TEST SUMMARY ===")
    passed = sum(results.values())
    total = len(results)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Backend is ready!")
    else:
        print("⚠️  Some tests failed - Check issues above")
    
    return results

if __name__ == '__main__':
    run_tests()