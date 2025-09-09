"""
Test script for email verification flow
Run with: python test_email_verification.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import AsyncSessionLocal, init_db
from services import AuthService
from email_service import EmailService
from messaging import EventPublisher
from config import settings
import redis.asyncio as redis


async def test_email_verification_flow():
    """Test the complete email verification flow"""
    print("🧪 Testing Email Verification Flow")
    print("=" * 50)
    
    # Initialize database
    print("📊 Initializing database...")
    await init_db()
    print("✅ Database initialized")
    
    # Create Redis connection
    print("🔌 Connecting to Redis...")
    redis_client = redis.from_url(settings.REDIS_URL)
    await redis_client.ping()
    print("✅ Redis connected")
    
    # Create services
    async with AsyncSessionLocal() as session:
        auth_service = AuthService(session, redis_client)
        email_service = EmailService(session)
        event_publisher = EventPublisher()
        
        print("\n📝 Step 1: User Registration with Email Verification")
        print("-" * 50)
        
        test_email = "test@example.com"
        test_password = "SecurePassword123!"
        
        try:
            # Register user
            registration_result = await auth_service.register_with_verification(
                email=test_email,
                password=test_password,
                first_name="John",
                last_name="Doe"
            )
            
            print(f"✅ User registered:")
            print(f"   User ID: {registration_result['user_id']}")
            print(f"   Email: {registration_result['email']}")
            print(f"   Status: {registration_result['status']}")
            
            user_id = registration_result['user_id']
            
        except Exception as e:
            print(f"❌ Registration failed: {str(e)}")
            return
        
        print("\n📧 Step 2: Send Verification Email")
        print("-" * 50)
        
        try:
            # Send verification email
            email_result = await auth_service.send_verification_email(test_email)
            
            if email_result['success']:
                print("✅ Verification email sent successfully")
                print(f"   Message: {email_result['message']}")
                
                # Extract token for testing (in production, this would come from email)
                verification_token = email_result.get('verification_token')
                print(f"   Verification Token: {verification_token[:20]}...")
                
            else:
                print(f"❌ Email sending failed: {email_result['message']}")
                return
                
        except Exception as e:
            print(f"❌ Email sending error: {str(e)}")
            return
        
        print("\n🔍 Step 3: Check User Status Before Verification")
        print("-" * 50)
        
        try:
            # Check verification status
            status_result = await auth_service.check_user_verification_status(test_email)
            print(f"✅ User status check:")
            print(f"   Exists: {status_result['exists']}")
            print(f"   Email Verified: {status_result['email_verified']}")
            print(f"   Status: {status_result.get('status', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Status check error: {str(e)}")
        
        print("\n🔐 Step 4: Attempt Login Before Verification (Should Fail)")
        print("-" * 50)
        
        try:
            # Try to login before verification
            login_result = await auth_service.authenticate(
                email=test_email,
                password=test_password
            )
            print("❌ Login should have failed but succeeded!")
            
        except Exception as e:
            print(f"✅ Login correctly failed: {str(e)}")
        
        print("\n✅ Step 5: Verify Email")
        print("-" * 50)
        
        try:
            # Verify email with token
            verification_result = await auth_service.verify_email(
                token=verification_token,
                ip_address="127.0.0.1"
            )
            
            if verification_result['success']:
                print("✅ Email verification successful")
                print(f"   Message: {verification_result['message']}")
                print(f"   User ID: {verification_result['user_id']}")
                print(f"   Verified At: {verification_result['verified_at']}")
            else:
                print(f"❌ Verification failed: {verification_result['message']}")
                return
                
        except Exception as e:
            print(f"❌ Verification error: {str(e)}")
            return
        
        print("\n🔍 Step 6: Check User Status After Verification")
        print("-" * 50)
        
        try:
            # Check verification status again
            status_result = await auth_service.check_user_verification_status(test_email)
            print(f"✅ User status check after verification:")
            print(f"   Exists: {status_result['exists']}")
            print(f"   Email Verified: {status_result['email_verified']}")
            print(f"   Status: {status_result.get('status', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Status check error: {str(e)}")
        
        print("\n🔐 Step 7: Login After Verification (Should Succeed)")
        print("-" * 50)
        
        try:
            # Try to login after verification
            login_result = await auth_service.authenticate(
                email=test_email,
                password=test_password,
                ip_address="127.0.0.1"
            )
            
            print("✅ Login successful after verification")
            print(f"   User ID: {login_result['user_id']}")
            print(f"   Token Type: {login_result['token_type']}")
            print(f"   Expires In: {login_result['expires_in']} seconds")
            print(f"   Access Token: {login_result['access_token'][:50]}...")
            
        except Exception as e:
            print(f"❌ Login failed: {str(e)}")
        
        print("\n📧 Step 8: Test Password Reset Flow")
        print("-" * 50)
        
        try:
            # Test password reset
            reset_result = await auth_service.initiate_password_reset(test_email)
            
            if reset_result['success']:
                print("✅ Password reset email sent")
                print(f"   Message: {reset_result['message']}")
                
                # Extract reset token for testing
                reset_token = reset_result.get('reset_token')
                if reset_token:
                    print(f"   Reset Token: {reset_token[:20]}...")
                    
                    # Test password reset
                    new_password = "NewSecurePassword456!"
                    reset_complete = await auth_service.reset_password(reset_token, new_password)
                    print(f"✅ Password reset successful: {reset_complete['message']}")
                
            else:
                print(f"❌ Password reset failed: {reset_result['message']}")
                
        except Exception as e:
            print(f"❌ Password reset error: {str(e)}")
        
        print("\n📊 Step 9: Review Published Events")
        print("-" * 50)
        
        recent_events = event_publisher.get_recent_events()
        print(f"✅ Published {len(recent_events)} events:")
        for i, event in enumerate(recent_events, 1):
            print(f"   {i}. {event['type']} - {event['timestamp']}")
    
    # Close Redis connection
    await redis_client.close()
    
    print("\n🎉 Email Verification Flow Test Complete!")
    print("=" * 50)


async def test_configuration():
    """Test service configuration"""
    print("\n⚙️  Testing Configuration")
    print("-" * 30)
    
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Redis URL: {settings.REDIS_URL}")
    print(f"SMTP Host: {settings.SMTP_HOST}")
    print(f"From Email: {settings.FROM_EMAIL}")
    print(f"Base URL: {settings.BASE_URL}")
    print(f"Debug Mode: {settings.DEBUG}")
    
    # Test email configuration
    if settings.SMTP_HOST == "localhost":
        print("\n⚠️  SMTP Configuration Notice:")
        print("   Currently using localhost SMTP (development mode)")
        print("   For production, configure these environment variables:")
        print("   - SMTP_HOST")
        print("   - SMTP_PORT")
        print("   - SMTP_USERNAME")
        print("   - SMTP_PASSWORD")
        print("   - FROM_EMAIL")


if __name__ == "__main__":
    print("🚀 Auth Service Email Verification Test Suite")
    print("=" * 60)
    
    # Set up test environment variables if not set
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://auth_user:auth_password@localhost:5432/auth_service_test"
    
    if not os.getenv("JWT_SECRET_KEY"):
        os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-development-only"
    
    if not os.getenv("FROM_EMAIL"):
        os.environ["FROM_EMAIL"] = "test@authservice.local"
    
    try:
        # Run configuration test first
        asyncio.run(test_configuration())
        
        # Run main test
        asyncio.run(test_email_verification_flow())
        
    except KeyboardInterrupt:
        print("\n\n⛔ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()