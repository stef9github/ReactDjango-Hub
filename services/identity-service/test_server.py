#!/usr/bin/env python3
"""
Simplified Auth Service for Testing
Runs without external dependencies (PostgreSQL, Redis)
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Set test environment
os.environ['TEST_MODE'] = 'true'
os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key-for-local-development')

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
import jwt
from datetime import datetime, timedelta
import hashlib
import uuid

# Simple in-memory storage for testing
users_db: Dict[str, dict] = {}
tokens_db: Dict[str, dict] = {}

app = FastAPI(
    title="Auth Service - Test Mode",
    description="Simplified auth service for testing without external dependencies",
    version="1.0.0-test"
)

# Request/Response Models
class RegisterRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user_id: str

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    is_verified: bool
    status: str

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_jwt_token(user_id: str) -> dict:
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow()
    }
    token = jwt.encode(payload, os.environ['JWT_SECRET_KEY'], algorithm='HS256')
    return {
        'access_token': token,
        'token_type': 'Bearer',
        'expires_in': 3600,
        'user_id': user_id
    }

# API Endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "auth-service",
        "mode": "test",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/auth/register", response_model=dict)
async def register(request: RegisterRequest):
    # Check if user exists
    if request.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = str(uuid.uuid4())
    user_data = {
        'id': user_id,
        'email': request.email,
        'password_hash': hash_password(request.password),
        'first_name': request.first_name,
        'last_name': request.last_name,
        'is_verified': True,  # Auto-verify in test mode
        'status': 'active',
        'created_at': datetime.utcnow().isoformat()
    }
    
    users_db[request.email] = user_data
    
    return {
        "message": "Account created successfully (test mode - auto-verified)",
        "user_id": user_id,
        "email": request.email,
        "verification_required": False,
        "next_step": "You can now login immediately"
    }

@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    # Check if user exists
    if request.email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user = users_db[request.email]
    
    # Verify password
    if not verify_password(request.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create JWT token
    token_data = create_jwt_token(user['id'])
    return TokenResponse(**token_data)

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user():
    # For testing, return a sample user
    sample_user = {
        "id": "test-user-id",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_verified": True,
        "status": "active"
    }
    return UserResponse(**sample_user)

@app.get("/users", response_model=list)
async def list_users():
    """List all registered users (test endpoint)"""
    users = []
    for email, user_data in users_db.items():
        users.append({
            "id": user_data['id'],
            "email": email,
            "first_name": user_data['first_name'],
            "last_name": user_data['last_name'],
            "is_verified": user_data['is_verified'],
            "status": user_data['status'],
            "created_at": user_data['created_at']
        })
    return users

@app.delete("/users/{email}")
async def delete_user(email: str):
    """Delete a user (test endpoint)"""
    if email not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    del users_db[email]
    return {"message": f"User {email} deleted successfully"}

@app.get("/test-info")
async def test_info():
    """Test information endpoint"""
    return {
        "message": "Auth Service Test Mode",
        "features": [
            "✅ User registration (auto-verified)",
            "✅ User login with JWT tokens", 
            "✅ In-memory user storage",
            "✅ Password hashing",
            "✅ Health checks",
            "⚠️  No email verification (auto-verify)",
            "⚠️  No external dependencies (PostgreSQL/Redis)",
            "⚠️  Data lost on restart"
        ],
        "endpoints": [
            "POST /auth/register - Register new user",
            "POST /auth/login - Login user", 
            "GET /auth/me - Get current user",
            "GET /users - List all users",
            "DELETE /users/{email} - Delete user",
            "GET /health - Health check",
            "GET /test-info - This endpoint"
        ],
        "users_count": len(users_db),
        "test_mode": True
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Auth Service in TEST MODE")
    print("=" * 50)
    print("📍 URL: http://localhost:8001")
    print("📖 Docs: http://localhost:8001/docs")
    print("🧪 Test Info: http://localhost:8001/test-info")
    print("=" * 50)
    
    uvicorn.run(
        "test_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )