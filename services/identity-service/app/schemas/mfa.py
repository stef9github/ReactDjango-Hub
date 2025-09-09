"""Multi-Factor Authentication schemas for request/response validation"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr
from enum import Enum


class MFAMethodType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    TOTP = "totp"
    BACKUP_CODES = "backup_codes"


class MFASetupRequest(BaseModel):
    method_type: MFAMethodType
    phone_number: Optional[str] = None
    backup_email: Optional[str] = None


class MFASetupResponse(BaseModel):
    method_id: str
    method_type: MFAMethodType
    setup_data: Dict[str, Any]
    backup_codes: Optional[List[str]]
    qr_code: Optional[str]
    secret_key: Optional[str]


class MFAChallengeRequest(BaseModel):
    method_type: MFAMethodType
    method_id: Optional[str] = None


class MFAChallengeResponse(BaseModel):
    challenge_id: str
    method_type: MFAMethodType
    message: str


class MFAVerifyRequest(BaseModel):
    challenge_id: str
    code: str


class MFAVerifyResponse(BaseModel):
    verified: bool
    token: Optional[str] = None
    message: str


class MFAMethodResponse(BaseModel):
    method_id: str
    method_type: MFAMethodType
    is_primary: bool
    phone_number: Optional[str]
    backup_email: Optional[str]
    created_at: datetime
    last_used: Optional[datetime]


class RegenerateBackupCodesResponse(BaseModel):
    backup_codes: List[str]
    created_at: datetime