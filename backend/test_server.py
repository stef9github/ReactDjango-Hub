#!/usr/bin/env python
"""
Test script to verify Django server and API endpoints
"""
import os
import sys
import django
import requests
import json
from django.test import Client
from django.core.management import execute_from_command_line

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def test_server_locally():
    """Test Django endpoints using Django test client"""
    print("=== Testing Django Backend with Local Client ===")
    
    client = Client()
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    try:
        response = client.get('/health/')
        print(f"Health endpoint status: {response.status_code}")
        print(f"Health endpoint content: {response.content.decode()}")
    except Exception as e:
        print(f"Health endpoint error: {e}")
    
    # Test API health endpoint  
    print("\n2. Testing API health endpoint...")
    try:
        response = client.get('/api/health')
        print(f"API health status: {response.status_code}")
        if response.status_code == 200:
            content = response.json()
            print(f"API health content: {content}")
        else:
            print(f"API health content: {response.content.decode()[:200]}")
    except Exception as e:
        print(f"API health error: {e}")
        
    # Test API docs endpoint
    print("\n3. Testing API docs endpoint...")
    try:
        response = client.get('/api/docs')
        print(f"API docs status: {response.status_code}")
        if response.status_code == 200:
            print("✅ API docs accessible")
        else:
            print(f"❌ API docs issue: {response.content.decode()[:200]}")
    except Exception as e:
        print(f"API docs error: {e}")
        
    # Test business endpoints (without auth - should return 401)
    print("\n4. Testing business endpoints (without auth)...")
    try:
        response = client.get('/api/business/contacts')
        print(f"Contacts endpoint status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Authentication properly required")
        elif response.status_code == 403:
            print("✅ Authorization properly required")
        else:
            print(f"❓ Unexpected response: {response.content.decode()[:200]}")
    except Exception as e:
        print(f"Contacts endpoint error: {e}")

def test_identity_service():
    """Test if Identity Service is available"""
    print("\n=== Testing Identity Service Connection ===")
    
    try:
        response = requests.get('http://localhost:8001/health', timeout=5)
        print(f"Identity Service health status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Identity Service is running")
            return True
        else:
            print("❌ Identity Service health check failed")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Identity Service not accessible - Connection refused")
        print("   Run: cd services/identity-service && python main.py")
        return False
    except requests.exceptions.Timeout:
        print("❌ Identity Service timeout")
        return False
    except Exception as e:
        print(f"❌ Identity Service error: {e}")
        return False

def test_with_auth():
    """Test endpoints with mock JWT token for local testing"""
    print("\n=== Testing with Mock Authentication ===")
    
    client = Client()
    
    # Create a mock JWT header for testing
    # In real testing, you'd get this from the identity service
    mock_jwt = "Bearer test-jwt-token-for-local-testing"
    
    print("\n1. Testing authenticated contacts endpoint...")
    try:
        response = client.get('/api/business/contacts', 
                            HTTP_AUTHORIZATION=mock_jwt)
        print(f"Authenticated contacts status: {response.status_code}")
        if response.status_code in [200, 401, 403]:
            print(f"Response: {response.content.decode()[:200]}")
        else:
            print(f"Unexpected status: {response.content.decode()[:200]}")
    except Exception as e:
        print(f"Authenticated contacts error: {e}")
        
    print("\n2. Testing analytics endpoint...")
    try:
        response = client.get('/api/analytics/records', 
                            HTTP_AUTHORIZATION=mock_jwt)
        print(f"Analytics endpoint status: {response.status_code}")
        if response.status_code in [200, 401, 403]:
            print(f"Response: {response.content.decode()[:200]}")
        else:
            print(f"Unexpected status: {response.content.decode()[:200]}")
    except Exception as e:
        print(f"Analytics endpoint error: {e}")

if __name__ == '__main__':
    test_server_locally()
    test_identity_service()
    test_with_auth()