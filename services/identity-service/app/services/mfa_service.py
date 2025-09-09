"""
Multi-Factor Authentication (MFA) Service
Handles email, SMS, TOTP, and other verification methods
"""

import uuid
import secrets
import qrcode
import pyotp
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from .enhanced_models import User, UserActivityLog


class MFAMethodType(str, Enum):
    """Multi-factor authentication method types"""
    EMAIL = "email"
    SMS = "sms"
    TOTP = "totp"  # Time-based OTP (Google Authenticator)
    BACKUP_CODES = "backup_codes"
    WEBAUTHN = "webauthn"  # Future: Passkeys/FIDO2


class MFAStatus(str, Enum):
    """MFA verification status"""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class MFAChallenge:
    """MFA challenge data"""
    challenge_id: str
    method_type: MFAMethodType
    destination: str  # email address, phone number, etc.
    expires_at: datetime
    attempts_remaining: int


@dataclass
class MFASetupData:
    """Data for setting up MFA method"""
    method_type: MFAMethodType
    destination: Optional[str] = None  # email/phone
    secret: Optional[str] = None  # for TOTP
    backup_codes: Optional[List[str]] = None


class MFAService:
    """Multi-factor authentication service"""
    
    def __init__(self, db_session: AsyncSession, email_service=None, sms_service=None):
        self.db = db_session
        self.email_service = email_service
        self.sms_service = sms_service
        
        # Configuration
        self.code_length = 6
        self.code_expiry_minutes = 10
        self.max_attempts = 3
        self.totp_issuer = "Auth Service"
    
    async def setup_mfa_method(
        self, 
        user_id: str, 
        method_type: MFAMethodType,
        destination: Optional[str] = None
    ) -> Dict[str, Any]:
        """Setup a new MFA method for user"""
        
        user = await self._get_user(user_id)
        if not user:
            raise ValueError("User not found")
        
        if method_type == MFAMethodType.EMAIL:
            return await self._setup_email_mfa(user, destination or user.email)
        
        elif method_type == MFAMethodType.SMS:
            if not destination:
                destination = user.phone_number
            if not destination:
                raise ValueError("Phone number required for SMS MFA")
            return await self._setup_sms_mfa(user, destination)
        
        elif method_type == MFAMethodType.TOTP:
            return await self._setup_totp_mfa(user)
        
        elif method_type == MFAMethodType.BACKUP_CODES:
            return await self._setup_backup_codes_mfa(user)
        
        else:
            raise ValueError(f"Unsupported MFA method: {method_type}")
    
    async def initiate_mfa_challenge(
        self, 
        user_id: str, 
        method_type: MFAMethodType,
        session_id: Optional[str] = None
    ) -> MFAChallenge:
        """Initiate MFA challenge (send code, etc.)"""
        
        # Get user's MFA method
        mfa_method = await self._get_user_mfa_method(user_id, method_type)
        if not mfa_method or not mfa_method.is_active:
            raise ValueError(f"MFA method {method_type} not configured for user")
        
        challenge_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=self.code_expiry_minutes)
        
        if method_type == MFAMethodType.EMAIL:
            return await self._send_email_challenge(
                mfa_method, challenge_id, expires_at, session_id
            )
        
        elif method_type == MFAMethodType.SMS:
            return await self._send_sms_challenge(
                mfa_method, challenge_id, expires_at, session_id
            )
        
        elif method_type == MFAMethodType.TOTP:
            # TOTP doesn't need a challenge - user enters current TOTP code
            return MFAChallenge(
                challenge_id=challenge_id,
                method_type=method_type,
                destination="authenticator_app",
                expires_at=expires_at,
                attempts_remaining=self.max_attempts
            )
        
        else:
            raise ValueError(f"Cannot initiate challenge for {method_type}")
    
    async def verify_mfa_challenge(
        self, 
        challenge_id: str, 
        code: str,
        user_id: str,
        method_type: MFAMethodType
    ) -> bool:
        """Verify MFA challenge response"""
        
        # Get stored challenge
        challenge = await self._get_stored_challenge(challenge_id)
        if not challenge:
            await self._log_mfa_activity(user_id, "mfa.verify_failed", 
                                        {"reason": "invalid_challenge"})
            return False
        
        # Check expiry
        if datetime.utcnow() > challenge['expires_at']:
            await self._log_mfa_activity(user_id, "mfa.verify_failed", 
                                        {"reason": "expired_challenge"})
            return False
        
        # Check attempts
        if challenge['attempts_used'] >= self.max_attempts:
            await self._log_mfa_activity(user_id, "mfa.verify_failed", 
                                        {"reason": "max_attempts_exceeded"})
            return False
        
        # Verify code based on method
        is_valid = False
        
        if method_type == MFAMethodType.EMAIL:
            is_valid = await self._verify_email_code(challenge_id, code)
        
        elif method_type == MFAMethodType.SMS:
            is_valid = await self._verify_sms_code(challenge_id, code)
        
        elif method_type == MFAMethodType.TOTP:
            is_valid = await self._verify_totp_code(user_id, code)
        
        elif method_type == MFAMethodType.BACKUP_CODES:
            is_valid = await self._verify_backup_code(user_id, code)
        
        # Update challenge attempts
        await self._update_challenge_attempts(challenge_id)
        
        # Log result
        if is_valid:
            await self._log_mfa_activity(user_id, "mfa.verify_success", 
                                        {"method": method_type})
            await self._cleanup_challenge(challenge_id)
        else:
            await self._log_mfa_activity(user_id, "mfa.verify_failed", 
                                        {"method": method_type, "reason": "invalid_code"})
        
        return is_valid
    
    async def get_user_mfa_methods(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all MFA methods configured for user"""
        
        from .models import MFAMethod
        
        result = await self.db.execute(
            select(MFAMethod).where(
                MFAMethod.user_id == user_id,
                MFAMethod.is_active == True
            )
        )
        methods = result.scalars().all()
        
        return [
            {
                "id": str(method.id),
                "method_type": method.method_type,
                "is_primary": method.is_primary,
                "verified_at": method.verified_at.isoformat() if method.verified_at else None,
                "last_used_at": method.last_used_at.isoformat() if method.last_used_at else None,
                "destination": self._mask_destination(method.method_type, 
                                                    method.phone_number or method.email)
            }
            for method in methods
        ]
    
    async def _setup_email_mfa(self, user: User, email: str) -> Dict[str, Any]:
        """Setup email-based MFA"""
        
        # Create or update MFA method
        mfa_method = await self._create_mfa_method(
            user_id=user.id,
            method_type=MFAMethodType.EMAIL,
            email=email
        )
        
        # Send verification email
        verification_code = self._generate_code()
        await self._store_verification_code(str(mfa_method.id), verification_code)
        
        if self.email_service:
            await self.email_service.send_mfa_setup_email(
                email, verification_code, user.first_name
            )
        
        await self._log_mfa_activity(user.id, "mfa.email_setup", 
                                    {"email": email})
        
        return {
            "method_id": str(mfa_method.id),
            "method_type": "email",
            "destination": email,
            "status": "verification_sent",
            "message": f"Verification code sent to {email}"
        }
    
    async def _setup_sms_mfa(self, user: User, phone: str) -> Dict[str, Any]:
        """Setup SMS-based MFA"""
        
        # Create or update MFA method
        mfa_method = await self._create_mfa_method(
            user_id=user.id,
            method_type=MFAMethodType.SMS,
            phone_number=phone
        )
        
        # Send verification SMS
        verification_code = self._generate_code()
        await self._store_verification_code(str(mfa_method.id), verification_code)
        
        if self.sms_service:
            await self.sms_service.send_mfa_setup_sms(
                phone, verification_code
            )
        
        await self._log_mfa_activity(user.id, "mfa.sms_setup", 
                                    {"phone": self._mask_phone(phone)})
        
        return {
            "method_id": str(mfa_method.id),
            "method_type": "sms",
            "destination": self._mask_phone(phone),
            "status": "verification_sent",
            "message": f"Verification code sent to {self._mask_phone(phone)}"
        }
    
    async def _setup_totp_mfa(self, user: User) -> Dict[str, Any]:
        """Setup TOTP (authenticator app) MFA"""
        
        # Generate TOTP secret
        secret = pyotp.random_base32()
        
        # Create MFA method
        mfa_method = await self._create_mfa_method(
            user_id=user.id,
            method_type=MFAMethodType.TOTP,
            secret=secret
        )
        
        # Generate QR code for setup
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name=self.totp_issuer
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        await self._log_mfa_activity(user.id, "mfa.totp_setup", {})
        
        return {
            "method_id": str(mfa_method.id),
            "method_type": "totp",
            "secret": secret,  # For manual entry
            "qr_code_uri": provisioning_uri,
            "status": "setup_required",
            "message": "Scan QR code with authenticator app and verify"
        }
    
    async def _setup_backup_codes_mfa(self, user: User) -> Dict[str, Any]:
        """Setup backup codes MFA"""
        
        # Generate backup codes
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
        
        # Create MFA method
        mfa_method = await self._create_mfa_method(
            user_id=user.id,
            method_type=MFAMethodType.BACKUP_CODES,
            secret=",".join(backup_codes)  # Store comma-separated
        )
        
        await self._log_mfa_activity(user.id, "mfa.backup_codes_setup", 
                                    {"codes_generated": len(backup_codes)})
        
        return {
            "method_id": str(mfa_method.id),
            "method_type": "backup_codes",
            "backup_codes": backup_codes,
            "status": "active",
            "message": "Save these backup codes in a secure location"
        }
    
    def _generate_code(self) -> str:
        """Generate random verification code"""
        return ''.join(secrets.choice('0123456789') for _ in range(self.code_length))
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone number for display"""
        if len(phone) >= 4:
            return f"***-***-{phone[-4:]}"
        return "***"
    
    def _mask_destination(self, method_type: MFAMethodType, destination: str) -> str:
        """Mask destination for display"""
        if method_type == MFAMethodType.EMAIL:
            if '@' in destination:
                local, domain = destination.split('@', 1)
                return f"{local[0]}***@{domain}"
        elif method_type == MFAMethodType.SMS:
            return self._mask_phone(destination)
        return destination
    
    async def _get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def _create_mfa_method(
        self, 
        user_id: str, 
        method_type: MFAMethodType,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        secret: Optional[str] = None
    ):
        """Create or update MFA method"""
        from .models import MFAMethod
        
        # Check if method already exists
        existing = await self.db.execute(
            select(MFAMethod).where(
                MFAMethod.user_id == user_id,
                MFAMethod.method_type == method_type
            )
        )
        method = existing.scalar_one_or_none()
        
        if method:
            # Update existing
            method.email = email
            method.phone_number = phone_number
            method.secret = secret
            method.is_active = True
        else:
            # Create new
            method = MFAMethod(
                user_id=user_id,
                method_type=method_type,
                email=email,
                phone_number=phone_number,
                secret=secret,
                is_active=True
            )
            self.db.add(method)
        
        await self.db.flush()
        return method
    
    async def _log_mfa_activity(
        self, 
        user_id: str, 
        action: str, 
        metadata: Dict[str, Any]
    ):
        """Log MFA-related activity"""
        activity = UserActivityLog(
            user_id=user_id,
            action=action,
            resource="mfa",
            metadata=metadata,
            success=True
        )
        self.db.add(activity)
    
    # Additional methods for challenge storage, verification, etc.
    # These would use Redis or database for temporary challenge storage
    async def _store_verification_code(self, method_id: str, code: str):
        """Store verification code temporarily (Redis recommended)"""
        # Implementation depends on your caching strategy
        pass
    
    async def _get_stored_challenge(self, challenge_id: str) -> Optional[Dict]:
        """Get stored challenge data"""
        # Implementation depends on your caching strategy
        pass
    
    async def _verify_email_code(self, challenge_id: str, code: str) -> bool:
        """Verify email verification code"""
        # Implementation depends on your caching strategy
        pass
    
    async def _verify_sms_code(self, challenge_id: str, code: str) -> bool:
        """Verify SMS verification code"""
        # Implementation depends on your caching strategy
        pass
    
    async def _verify_totp_code(self, user_id: str, code: str) -> bool:
        """Verify TOTP code"""
        from .models import MFAMethod
        
        result = await self.db.execute(
            select(MFAMethod).where(
                MFAMethod.user_id == user_id,
                MFAMethod.method_type == MFAMethodType.TOTP,
                MFAMethod.is_active == True
            )
        )
        method = result.scalar_one_or_none()
        
        if not method or not method.secret:
            return False
        
        totp = pyotp.TOTP(method.secret)
        return totp.verify(code, valid_window=1)  # Allow 1 time step tolerance
    
    async def _verify_backup_code(self, user_id: str, code: str) -> bool:
        """Verify and consume backup code"""
        from .models import MFAMethod
        
        result = await self.db.execute(
            select(MFAMethod).where(
                MFAMethod.user_id == user_id,
                MFAMethod.method_type == MFAMethodType.BACKUP_CODES,
                MFAMethod.is_active == True
            )
        )
        method = result.scalar_one_or_none()
        
        if not method or not method.secret:
            return False
        
        backup_codes = method.secret.split(',')
        if code.upper() in backup_codes:
            # Remove used code
            backup_codes.remove(code.upper())
            method.secret = ','.join(backup_codes)
            await self.db.flush()
            return True
        
        return False