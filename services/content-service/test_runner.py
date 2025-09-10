#!/usr/bin/env python3
"""
Simple test runner for service layer tests that bypasses conftest.py
"""
import sys
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
import httpx
import psutil

# Import the test classes directly
sys.path.insert(0, 'tests')
from test_service_layer import (
    TestHealthCheckHelpers,
    TestJWTValidation, 
    TestCurrentUser,
    TestUserPermissions,
    TestServiceLayerIntegration
)

async def run_async_test(test_method):
    """Run an async test method"""
    try:
        await test_method()
        print(f"✓ {test_method.__name__}")
        return True
    except AssertionError as e:
        print(f"✗ {test_method.__name__}: Assertion failed - {e}")
        return False
    except Exception as e:
        print(f"✗ {test_method.__name__}: {e}")
        return False

def run_sync_test(test_method):
    """Run a sync test method"""
    try:
        test_method()
        print(f"✓ {test_method.__name__}")
        return True
    except Exception as e:
        print(f"✗ {test_method.__name__}: {e}")
        return False

async def main():
    """Run all service layer tests"""
    print("🧪 Running Service Layer Unit Tests")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    # Health Check Tests
    print("\n📊 Health Check Helper Tests:")
    health_tests = TestHealthCheckHelpers()
    for test_name in ['test_get_uptime', 'test_get_memory_usage', 'test_get_active_connections']:
        test_method = getattr(health_tests, test_name)
        if run_sync_test(test_method):
            passed += 1
        else:
            failed += 1
    
    # JWT Validation Tests
    print("\n🔐 JWT Validation Tests:")
    jwt_tests = TestJWTValidation()
    async_test_names = [
        'test_validate_jwt_token_success',
        'test_validate_jwt_token_unauthorized', 
        'test_validate_jwt_token_service_error',
        'test_validate_jwt_token_timeout',
        'test_validate_jwt_token_network_error',
        'test_validate_jwt_token_unexpected_error'
    ]
    for test_name in async_test_names:
        test_method = getattr(jwt_tests, test_name)
        if await run_async_test(test_method):
            passed += 1
        else:
            failed += 1
    
    # Current User Tests
    print("\n👤 Current User Tests:")
    user_tests = TestCurrentUser()
    user_test_names = [
        'test_get_current_user_success',
        'test_get_current_user_missing_roles'
    ]
    for test_name in user_test_names:
        test_method = getattr(user_tests, test_name)
        if await run_async_test(test_method):
            passed += 1
        else:
            failed += 1
    
    # Permission Tests
    print("\n🔒 User Permissions Tests:")
    perm_tests = TestUserPermissions()
    perm_test_names = [
        'test_get_user_permissions_owner',
        'test_get_user_permissions_non_owner',
        'test_get_user_permissions_missing_roles'
    ]
    for test_name in perm_test_names:
        test_method = getattr(perm_tests, test_name)
        if await run_async_test(test_method):
            passed += 1
        else:
            failed += 1
    
    # Integration Tests
    print("\n🔗 Service Layer Integration Tests:")
    integration_tests = TestServiceLayerIntegration()
    integration_test_names = [
        'test_jwt_to_user_flow'
    ]
    for test_name in integration_test_names:
        test_method = getattr(integration_tests, test_name)
        if await run_async_test(test_method):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📈 Test Results:")
    print(f"✓ Passed: {passed}")
    print(f"✗ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("🎉 All service layer tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)