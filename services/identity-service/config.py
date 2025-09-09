"""
Application configuration
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = "postgresql+asyncpg://stephanerichard@localhost:5432/auth_service"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT Configuration
    jwt_secret_key: str = "development-secret-key-not-for-production"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"
    
    # Email Configuration
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = False
    smtp_use_ssl: bool = False
    from_email: str = "noreply@authservice.local"
    from_name: str = "Auth Service"
    
    # Application URLs
    base_url: str = "http://localhost:8001"
    frontend_url: str = "http://localhost:3000"
    
    # Token expiry (hours)
    email_verification_expire_hours: int = 24
    password_reset_expire_hours: int = 1
    
    # Rate Limiting
    login_rate_limit: int = 10
    login_rate_window: int = 300  # 5 minutes
    api_rate_limit: int = 10000
    
    # Service Configuration
    service_host: str = "localhost"
    service_port: int = 8001
    instance_id: str = "auth-service-dev"
    
    # Development Settings
    debug: bool = True
    log_level: str = "DEBUG"
    
    # Test Mode
    test_mode: bool = False
    skip_email_verification: bool = False  # For testing without SMTP

    class Config:
        env_file = ".env.local"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()