"""
Auth Service Configuration
"""

import os
from typing import List


class Settings:
    """Application settings"""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://auth_user:auth_password@localhost:5432/auth_service"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # JWT Settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # 7 days
    
    # Email Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@example.com")
    FROM_NAME: str = os.getenv("FROM_NAME", "Auth Service")
    
    # Application URLs
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8001")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Security
    BCRYPT_ROUNDS: int = 12
    PASSWORD_MIN_LENGTH: int = 8
    
    # Rate Limiting
    LOGIN_RATE_LIMIT: int = int(os.getenv("LOGIN_RATE_LIMIT", "5"))  # attempts per window
    LOGIN_RATE_WINDOW: int = int(os.getenv("LOGIN_RATE_WINDOW", "300"))  # 5 minutes
    API_RATE_LIMIT: int = int(os.getenv("API_RATE_LIMIT", "1000"))  # per hour
    
    # Token Expiry
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_EXPIRE_HOURS: int = 1
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://localhost:3000",
        "https://localhost:8000",
    ]
    
    # Service Discovery (Consul)
    CONSUL_HOST: str = os.getenv("CONSUL_HOST", "localhost")
    CONSUL_PORT: int = int(os.getenv("CONSUL_PORT", "8500"))
    SERVICE_HOST: str = os.getenv("SERVICE_HOST", "localhost")
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8001"))
    INSTANCE_ID: str = os.getenv("INSTANCE_ID", "auth-service-1")
    
    # Development/Debug
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Kafka (for events)
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC_PREFIX: str = os.getenv("KAFKA_TOPIC_PREFIX", "auth-service")
    
    # Email Templates
    def get_verification_url_template(self) -> str:
        """Get email verification URL template"""
        return f"{self.FRONTEND_URL}/verify-email?token={{token}}"
    
    def get_password_reset_url_template(self) -> str:
        """Get password reset URL template"""
        return f"{self.FRONTEND_URL}/reset-password?token={{token}}"


# Global settings instance
settings = Settings()


# Validation
def validate_settings():
    """Validate required settings"""
    errors = []
    
    if not settings.JWT_SECRET_KEY or settings.JWT_SECRET_KEY == "your-super-secret-jwt-key-change-in-production":
        errors.append("JWT_SECRET_KEY must be set to a secure value in production")
    
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL is required")
    
    if not settings.REDIS_URL:
        errors.append("REDIS_URL is required")
    
    # Email configuration validation
    if settings.SMTP_HOST and settings.SMTP_HOST != "localhost":
        if not settings.SMTP_USERNAME:
            errors.append("SMTP_USERNAME is required when using external SMTP")
        if not settings.SMTP_PASSWORD:
            errors.append("SMTP_PASSWORD is required when using external SMTP")
    
    if not settings.FROM_EMAIL:
        errors.append("FROM_EMAIL is required for email notifications")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"- {error}" for error in errors))


# Email provider configurations for common services
EMAIL_PROVIDER_CONFIGS = {
    "gmail": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "use_tls": True
    },
    "sendgrid": {
        "smtp_host": "smtp.sendgrid.net",
        "smtp_port": 587,
        "use_tls": True
    },
    "mailgun": {
        "smtp_host": "smtp.mailgun.org",
        "smtp_port": 587,
        "use_tls": True
    },
    "ses": {
        "smtp_host": "email-smtp.us-east-1.amazonaws.com",
        "smtp_port": 587,
        "use_tls": True
    }
}


def configure_email_provider(provider: str, username: str, password: str):
    """Configure email provider settings"""
    if provider not in EMAIL_PROVIDER_CONFIGS:
        raise ValueError(f"Unsupported email provider: {provider}")
    
    config = EMAIL_PROVIDER_CONFIGS[provider]
    settings.SMTP_HOST = config["smtp_host"]
    settings.SMTP_PORT = config["smtp_port"]
    settings.SMTP_USERNAME = username
    settings.SMTP_PASSWORD = password