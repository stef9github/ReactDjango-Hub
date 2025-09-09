"""Authentication schemas for request/response validation"""

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tenant_id: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    email: str
    tenant_id: Optional[str]
    requires_mfa: bool = False
    mfa_challenge_id: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer" 
    expires_in: int


class TokenValidationRequest(BaseModel):
    token: str


class TokenValidationResponse(BaseModel):
    valid: bool
    user_id: Optional[str]
    email: Optional[str]
    tenant_id: Optional[str]
    roles: List[str]
    permissions: List[str]
    expires_at: Optional[int]


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class VerifyEmailRequest(BaseModel):
    token: str


class ServiceHealthResponse(BaseModel):
    service: str = "auth-service"
    status: str
    version: str
    database: str
    cache: str