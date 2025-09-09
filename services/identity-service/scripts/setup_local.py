#!/usr/bin/env python3
"""
Local Development Setup Script for Auth Service
Run this script to set up your local development environment
"""

import asyncio
import os
import sys
import subprocess
import time
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")

def print_step(step: str, status: str = ""):
    """Print a formatted step"""
    if status == "SUCCESS":
        print(f"✅ {step}")
    elif status == "ERROR":
        print(f"❌ {step}")
    elif status == "WARNING":
        print(f"⚠️  {step}")
    else:
        print(f"📋 {step}")

def run_command(command: str, description: str) -> bool:
    """Run a shell command and return success status"""
    try:
        print(f"   Running: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print_step(f"{description}", "SUCCESS")
            if result.stdout:
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print_step(f"{description} - {result.stderr.strip()}", "ERROR")
            return False
    except Exception as e:
        print_step(f"{description} - {str(e)}", "ERROR")
        return False

def check_prerequisites():
    """Check if required software is installed"""
    print_header("Checking Prerequisites")
    
    prereqs = [
        ("python3 --version", "Python 3.7+"),
        ("pip --version", "pip package manager"),
        ("docker --version", "Docker (for PostgreSQL/Redis)"),
        ("docker-compose --version", "Docker Compose"),
    ]
    
    all_good = True
    for command, description in prereqs:
        if not run_command(command, description):
            all_good = False
    
    if not all_good:
        print_step("Please install missing prerequisites before continuing", "ERROR")
        sys.exit(1)

def setup_python_environment():
    """Set up Python virtual environment and dependencies"""
    print_header("Setting Up Python Environment")
    
    # Check if we're in a virtual environment
    if sys.prefix == sys.base_prefix:
        print_step("No virtual environment detected. Creating one...", "WARNING")
        if not run_command("python3 -m venv venv", "Create virtual environment"):
            return False
        print_step("Virtual environment created. Please activate it:", "SUCCESS")
        print("   source venv/bin/activate  # On macOS/Linux")
        print("   .\\venv\\Scripts\\activate  # On Windows")
        print("   Then run this script again.")
        return False
    
    print_step("Virtual environment detected", "SUCCESS")
    
    # Install dependencies
    if not run_command("pip install --upgrade pip", "Upgrade pip"):
        return False
    
    if not run_command("pip install -r requirements.txt", "Install Python dependencies"):
        return False
    
    return True

def setup_services():
    """Set up PostgreSQL and Redis using Docker"""
    print_header("Setting Up Database and Cache Services")
    
    # Create docker-compose.yml if it doesn't exist
    compose_content = '''version: '3.8'

services:
  auth-db:
    image: postgres:17
    environment:
      POSTGRES_DB: auth_service
      POSTGRES_USER: auth_user
      POSTGRES_PASSWORD: auth_password
    ports:
      - "5432:5432"
    volumes:
      - auth_db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U auth_user -d auth_service"]
      interval: 10s
      timeout: 5s
      retries: 5

  auth-redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - auth_redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"  # SMTP server
      - "8025:8025"  # Web UI
    environment:
      MH_STORAGE: maildir
      MH_MAILDIR_PATH: /maildir
    volumes:
      - mailhog_data:/maildir

volumes:
  auth_db_data:
  auth_redis_data:
  mailhog_data:
'''
    
    # Write docker-compose.yml
    with open("docker-compose.local.yml", "w") as f:
        f.write(compose_content)
    
    print_step("Created docker-compose.local.yml", "SUCCESS")
    
    # Start services
    if not run_command("docker-compose -f docker-compose.local.yml up -d", 
                      "Start PostgreSQL, Redis, and MailHog"):
        return False
    
    # Wait for services to be ready
    print("⏳ Waiting for services to be ready...")
    time.sleep(10)
    
    # Check service health
    if run_command("docker-compose -f docker-compose.local.yml ps", "Check service status"):
        print_step("Services are running", "SUCCESS")
        print("   📊 PostgreSQL: localhost:5432")
        print("   🔄 Redis: localhost:6379") 
        print("   📧 MailHog Web UI: http://localhost:8025")
        return True
    
    return False

async def setup_database():
    """Initialize database tables"""
    print_header("Setting Up Database")
    
    try:
        from database import init_db
        print_step("Initializing database tables...")
        await init_db()
        print_step("Database tables created successfully", "SUCCESS")
        return True
    except Exception as e:
        print_step(f"Database setup failed: {str(e)}", "ERROR")
        return False

def create_test_script():
    """Create a simple test script"""
    print_header("Creating Test Script")
    
    test_script = '''#!/usr/bin/env python3
"""
Quick test script for auth service
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8001"

async def test_endpoints():
    """Test basic auth endpoints"""
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Auth Service Endpoints")
        print("-" * 40)
        
        # Test health endpoint
        try:
            response = await client.get(f"{BASE_URL}/health")
            print(f"✅ Health Check: {response.status_code}")
            if response.status_code == 200:
                print(f"   Status: {response.json()}")
        except Exception as e:
            print(f"❌ Health Check Failed: {str(e)}")
        
        # Test registration
        try:
            user_data = {
                "email": "test@example.com",
                "password": "TestPassword123!",
                "first_name": "Test",
                "last_name": "User"
            }
            
            response = await client.post(f"{BASE_URL}/auth/register", json=user_data)
            print(f"✅ Registration: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   User ID: {result.get('user_id')}")
                print(f"   Message: {result.get('message')}")
                print(f"   📧 Check MailHog at http://localhost:8025 for verification email")
            else:
                print(f"   Error: {response.json()}")
                
        except Exception as e:
            print(f"❌ Registration Failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
'''
    
    with open("quick_test.py", "w") as f:
        f.write(test_script)
    
    # Make it executable
    os.chmod("quick_test.py", 0o755)
    print_step("Created quick_test.py script", "SUCCESS")

def print_next_steps():
    """Print next steps for the user"""
    print_header("🎉 Setup Complete!")
    
    print("Your local development environment is ready!")
    print("\n📋 Next Steps:")
    print("   1. Start the auth service:")
    print("      uvicorn main:app --reload --port 8001")
    print()
    print("   2. Test the service:")
    print("      python quick_test.py")
    print()
    print("   3. Run comprehensive tests:")
    print("      python test_email_verification.py")
    print()
    print("   4. View emails in MailHog:")
    print("      http://localhost:8025")
    print()
    print("   5. Check service health:")
    print("      http://localhost:8001/health")
    print("      http://localhost:8001/docs (API documentation)")
    print()
    print("🔧 Useful Commands:")
    print("   - Stop services: docker-compose -f docker-compose.local.yml down")
    print("   - View logs: docker-compose -f docker-compose.local.yml logs")
    print("   - Reset database: docker-compose -f docker-compose.local.yml down -v")

async def main():
    """Main setup function"""
    print_header("Auth Service Local Development Setup")
    
    # Check prerequisites
    check_prerequisites()
    
    # Setup Python environment
    if not setup_python_environment():
        return
    
    # Setup services
    if not setup_services():
        print_step("Service setup failed. Please check Docker is running.", "ERROR")
        return
    
    # Setup database
    if not await setup_database():
        print_step("Database setup failed. Check connection settings.", "ERROR")
        return
    
    # Create test script
    create_test_script()
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⛔ Setup interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Setup failed: {str(e)}")
        import traceback
        traceback.print_exc()