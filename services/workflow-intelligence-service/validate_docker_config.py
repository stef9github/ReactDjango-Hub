#!/usr/bin/env python3
"""
Docker Configuration Validation Script
Validates the Docker setup for Workflow Intelligence Service
"""
import os
import yaml
import sys
from pathlib import Path

def validate_docker_config():
    """Validate Docker configuration files"""
    print("🐳 Validating Docker Configuration")
    print("=" * 50)
    
    errors = []
    warnings = []
    
    # Check Dockerfile
    dockerfile_path = Path("Dockerfile")
    if dockerfile_path.exists():
        print("✅ Dockerfile exists")
        
        with open(dockerfile_path, 'r') as f:
            dockerfile_content = f.read()
            
        # Check for required elements
        required_elements = [
            "FROM python:3.13-slim",
            "WORKDIR /app",
            "ENV PYTHONDONTWRITEBYTECODE=1",
            "ENV PYTHONUNBUFFERED=1",
            "COPY requirements.txt",
            "RUN pip install",
            "EXPOSE 8004",
            "USER app",
            "HEALTHCHECK"
        ]
        
        for element in required_elements:
            if element in dockerfile_content:
                print(f"✅ Dockerfile contains: {element}")
            else:
                errors.append(f"Dockerfile missing: {element}")
    else:
        errors.append("Dockerfile does not exist")
    
    # Check docker-compose.yml
    compose_path = Path("docker-compose.yml")
    if compose_path.exists():
        print("✅ docker-compose.yml exists")
        
        try:
            with open(compose_path, 'r') as f:
                compose_config = yaml.safe_load(f)
            
            # Validate structure
            if 'services' in compose_config:
                services = compose_config['services']
                
                # Check workflow service
                if 'workflow-service' in services:
                    print("✅ workflow-service defined")
                    workflow_service = services['workflow-service']
                    
                    # Check required fields
                    required_fields = ['build', 'container_name', 'ports', 'environment']
                    for field in required_fields:
                        if field in workflow_service:
                            print(f"✅ workflow-service has {field}")
                        else:
                            errors.append(f"workflow-service missing {field}")
                    
                    # Check ports
                    if 'ports' in workflow_service:
                        ports = workflow_service['ports']
                        if '8004:8004' in ports:
                            print("✅ Port 8004 correctly mapped")
                        else:
                            warnings.append("Port 8004 not found in port mapping")
                
                else:
                    errors.append("workflow-service not defined in docker-compose.yml")
                
                # Check Redis service
                if 'workflow-redis' in services:
                    print("✅ workflow-redis service defined")
                else:
                    warnings.append("workflow-redis service not defined")
            
            else:
                errors.append("docker-compose.yml missing services section")
        
        except yaml.YAMLError as e:
            errors.append(f"docker-compose.yml YAML syntax error: {e}")
    else:
        errors.append("docker-compose.yml does not exist")
    
    # Check .env file
    env_path = Path(".env")
    if env_path.exists():
        print("✅ .env file exists")
        
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        # Check for required environment variables
        required_env_vars = [
            "JWT_SECRET_KEY",
            "DATABASE_URL",
            "REDIS_URL",
            "SERVICE_NAME",
            "SERVICE_PORT"
        ]
        
        for var in required_env_vars:
            if var in env_content:
                print(f"✅ Environment variable defined: {var}")
            else:
                warnings.append(f"Environment variable missing: {var}")
    else:
        warnings.append(".env file does not exist")
    
    # Check for shared .env
    shared_env_path = Path("../.env.shared")
    if shared_env_path.exists():
        print("✅ Shared .env.shared file exists")
    else:
        warnings.append("../.env.shared file not found")
    
    # Check Redis configuration
    redis_config_path = Path("redis/redis.conf")
    if redis_config_path.exists():
        print("✅ Redis configuration file exists")
    else:
        warnings.append("Redis configuration file missing")
    
    # Check requirements.txt
    requirements_path = Path("requirements.txt")
    if requirements_path.exists():
        print("✅ requirements.txt exists")
    else:
        errors.append("requirements.txt does not exist")
    
    # Print summary
    print("\n📊 Validation Summary:")
    print("-" * 30)
    
    if not errors and not warnings:
        print("🎉 All validations passed! Docker configuration is ready.")
        return True
    
    if warnings:
        print(f"⚠️  {len(warnings)} warnings:")
        for warning in warnings:
            print(f"   - {warning}")
    
    if errors:
        print(f"❌ {len(errors)} errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print("✅ Configuration is valid with minor warnings.")
    return True

def check_main_py_compatibility():
    """Check if main.py is compatible with Docker"""
    print("\n🔍 Checking main.py Docker Compatibility")
    print("-" * 40)
    
    main_py_path = Path("main.py")
    if not main_py_path.exists():
        print("❌ main.py not found")
        return False
    
    with open(main_py_path, 'r') as f:
        main_content = f.read()
    
    # Check for Docker-friendly patterns
    checks = [
        ('if __name__ == "__main__":', 'Main execution guard'),
        ('uvicorn.run', 'Uvicorn server setup'),
        ('host="0.0.0.0"', 'Docker-compatible host binding'),
        ('port=SERVICE_PORT', 'Port configuration from environment')
    ]
    
    for pattern, description in checks:
        if pattern in main_content:
            print(f"✅ {description} found")
        else:
            print(f"⚠️  {description} not found")
    
    return True

if __name__ == "__main__":
    print("🚀 Docker Configuration Validator")
    print("For Workflow Intelligence Service")
    print("=" * 50)
    
    # Run validations
    config_valid = validate_docker_config()
    main_compatible = check_main_py_compatibility()
    
    if config_valid and main_compatible:
        print("\n🎉 Docker configuration is ready for deployment!")
        print("\n📋 Next steps:")
        print("1. Create services network: docker network create services-network")
        print("2. Build and start: docker-compose up --build -d")
        print("3. Check health: curl http://localhost:8004/health")
        sys.exit(0)
    else:
        print("\n❌ Configuration issues found. Please fix the errors above.")
        sys.exit(1)