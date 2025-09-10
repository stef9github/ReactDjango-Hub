#!/usr/bin/env python3
"""
Test Airtable credentials and permissions
"""

import requests
import json

# Your credentials from the main script
API_KEY = "patYPbtTOgdQYYgTU.827b7b384156c120e07cd4381bb177aa116b689267bdf88313b521e6848e5c66"
BASE_ID = "app1SIhMIMJaKqAOZ"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("🔍 Testing Airtable API credentials...")
print(f"Base ID: {BASE_ID}")
print(f"Token starts with: {API_KEY[:20]}...")

# Test 1: Try to access base schema (requires schema.bases:read permission)
print("\n📋 Testing schema access...")
schema_url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}"
try:
    response = requests.get(schema_url, headers=headers)
    print(f"Schema API Response: {response.status_code}")
    if response.status_code == 200:
        print("✅ Schema access successful!")
        schema = response.json()
        print(f"Found {len(schema.get('tables', []))} tables")
    else:
        print(f"❌ Schema access failed: {response.status_code}")
        print(f"Error: {response.text}")
except Exception as e:
    print(f"❌ Schema request error: {e}")

# Test 2: Try to list tables the old way (without schema API)
print("\n📝 Testing basic table access...")
# Try to get data from the base without specifying a table
basic_url = f"https://api.airtable.com/v0/{BASE_ID}"
try:
    response = requests.get(basic_url, headers=headers)
    print(f"Basic API Response: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"❌ Basic request error: {e}")

# Test 3: Check token permissions
print("\n🔑 Token requirements for full export:")
print("Your token needs these permissions:")
print("- data.records:read (to read table data)")  
print("- schema.bases:read (to read table structure)")
print("\nTo fix:")
print("1. Go to https://airtable.com/create/tokens")
print("2. Create a new token or edit existing one")
print("3. Make sure both permissions above are selected")
print("4. Make sure the token has access to your specific base")