#!/usr/bin/env python3
"""
Test client for Auth Service
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8001"

async def test_auth_endpoints():
    """Test all auth service endpoints"""
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Auth Service Endpoints")
        print("=" * 50)
        
        # Test health endpoint
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"✅ Health Check: {response.status_code}")
            if response.status_code == 200:
                health = response.json()
                print(f"   Status: {health['status']}")
                print(f"   Service: {health['service']}")
                print(f"   Mode: {health['mode']}")
        except Exception as e:
            print(f"❌ Health Check Failed: {str(e)}")
        
        print("\n" + "-" * 30)
        
        # Test test-info endpoint
        try:
            response = await client.get(f"{BASE_URL}/test-info")
            print(f"✅ Test Info: {response.status_code}")
            if response.status_code == 200:
                info = response.json()
                print(f"   Message: {info['message']}")
                print(f"   Users Count: {info['users_count']}")
                print(f"   Test Mode: {info['test_mode']}")
        except Exception as e:
            print(f"❌ Test Info Failed: {str(e)}")
        
        print("\n" + "-" * 30)
        
        # Test registration
        user_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/auth/register", json=user_data)
            print(f"✅ Registration: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Message: {result.get('message')}")
                print(f"   User ID: {result.get('user_id')}")
                print(f"   Email: {result.get('email')}")
                print(f"   Verification Required: {result.get('verification_required')}")
                print(f"   Next Step: {result.get('next_step')}")
            else:
                print(f"   Error: {response.json()}")
        except Exception as e:
            print(f"❌ Registration Failed: {str(e)}")
        
        print("\n" + "-" * 30)
        
        # Test login
        login_data = {
            "email": "test@example.com", 
            "password": "TestPassword123!"
        }
        
        try:
            response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
            print(f"✅ Login: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Access Token: {result.get('access_token')[:50]}...")
                print(f"   Token Type: {result.get('token_type')}")
                print(f"   Expires In: {result.get('expires_in')}s")
                print(f"   User ID: {result.get('user_id')}")
            else:
                print(f"   Error: {response.json()}")
        except Exception as e:
            print(f"❌ Login Failed: {str(e)}")
        
        print("\n" + "-" * 30)
        
        # Test current user
        try:
            response = await client.get(f"{BASE_URL}/auth/me")
            print(f"✅ Current User: {response.status_code}")
            if response.status_code == 200:
                user = response.json()
                print(f"   ID: {user.get('id')}")
                print(f"   Email: {user.get('email')}")
                print(f"   Name: {user.get('first_name')} {user.get('last_name')}")
                print(f"   Verified: {user.get('is_verified')}")
                print(f"   Status: {user.get('status')}")
        except Exception as e:
            print(f"❌ Current User Failed: {str(e)}")
        
        print("\n" + "-" * 30)
        
        # Test list users
        try:
            response = await client.get(f"{BASE_URL}/users")
            print(f"✅ List Users: {response.status_code}")
            if response.status_code == 200:
                users = response.json()
                print(f"   Total Users: {len(users)}")
                for user in users:
                    print(f"   - {user['email']} ({user['first_name']} {user['last_name']})")
        except Exception as e:
            print(f"❌ List Users Failed: {str(e)}")
        
        print("\n" + "=" * 50)
        print("🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_auth_endpoints())