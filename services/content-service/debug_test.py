#!/usr/bin/env python3
"""Debug the failing test"""

import sys
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import httpx
from fastapi import HTTPException, status

sys.path.insert(0, 'tests')
from test_service_layer import validate_jwt_token

async def debug_unauthorized_test():
    """Debug the unauthorized test case"""
    print("🔍 Debugging unauthorized test case...")
    
    mock_token = Mock()
    mock_token.credentials = "invalid_token"
    
    print(f"Mock token credentials: {mock_token.credentials}")
    
    with patch('httpx.AsyncClient') as mock_client_cls:
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_client.post.return_value = mock_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        
        print("Mock setup complete - should raise HTTPException with 401")
        
        try:
            result = await validate_jwt_token(mock_token)
            print(f"❌ Expected HTTPException but got result: {result}")
        except HTTPException as e:
            print(f"✓ Caught HTTPException with status {e.status_code}")
            print(f"  Detail: {e.detail}")
            
            # Check assertions
            print("\n🧪 Testing assertions:")
            try:
                assert e.status_code == status.HTTP_401_UNAUTHORIZED
                print("✓ Status code assertion passed")
            except AssertionError as ae:
                print(f"❌ Status code assertion failed: {ae}")
                print(f"  Expected: {status.HTTP_401_UNAUTHORIZED}")
                print(f"  Actual: {e.status_code}")
            
            try:
                assert "Invalid or expired token" in e.detail
                print("✓ Detail assertion passed")
            except AssertionError as ae:
                print(f"❌ Detail assertion failed: {ae}")
                print(f"  Expected substring: 'Invalid or expired token'")
                print(f"  Actual detail: '{e.detail}'")
        except Exception as e:
            print(f"❌ Unexpected exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(debug_unauthorized_test())