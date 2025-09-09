"""Security utilities and helpers"""

import hashlib
import secrets
import string
from typing import Optional
import bcrypt
import jwt
from datetime import datetime, timedelta

from app.core.config import settings


class SecurityUtils:
    """Security utility functions"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate secure random token"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_numeric_code(length: int = 6) -> str:
        """Generate numeric verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    @staticmethod
    def create_jwt_token(
        payload: dict,
        expires_delta: Optional[timedelta] = None,
        secret_key: Optional[str] = None
    ) -> str:
        """Create JWT token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        payload.update({"exp": expire})
        
        return jwt.encode(
            payload,
            secret_key or settings.SECRET_KEY,
            algorithm="HS256"
        )
    
    @staticmethod
    def verify_jwt_token(
        token: str,
        secret_key: Optional[str] = None
    ) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                secret_key or settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    @staticmethod
    def hash_string(value: str) -> str:
        """Create SHA256 hash of string"""
        return hashlib.sha256(value.encode()).hexdigest()


# Export commonly used functions
hash_password = SecurityUtils.hash_password
verify_password = SecurityUtils.verify_password
generate_token = SecurityUtils.generate_token
generate_numeric_code = SecurityUtils.generate_numeric_code
create_jwt_token = SecurityUtils.create_jwt_token
verify_jwt_token = SecurityUtils.verify_jwt_token