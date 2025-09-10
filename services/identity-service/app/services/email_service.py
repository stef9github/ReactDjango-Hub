"""
Email Service for Auth Service
Handles email verification, password reset, and notification emails
"""

import smtplib
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.models.enhanced_models import User, EmailVerification, PasswordReset
from app.core.config import settings


@dataclass
class EmailTemplate:
    """Email template data"""
    subject: str
    html_body: str
    text_body: str


class EmailService:
    """Email service for authentication-related emails"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME or "Auth Service"
        self.base_url = settings.BASE_URL
    
    async def send_email(self, to_email: str, template: EmailTemplate) -> bool:
        """Send email using SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = template.subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text and HTML parts
            text_part = MIMEText(template.text_body, 'plain')
            html_part = MIMEText(template.html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            return False
    
    def _generate_token(self) -> tuple[str, str]:
        """Generate a secure token and its hash"""
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token, token_hash
    
    async def send_verification_email(
        self, 
        user_id: str, 
        email: str, 
        first_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email verification email"""
        try:
            # Generate verification token
            token, token_hash = self._generate_token()
            expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hour expiry
            
            # Store verification token in database
            verification = EmailVerification(
                user_id=user_id,
                email=email,
                token_hash=token_hash,
                verification_type="account_verification",
                expires_at=expires_at
            )
            
            self.db.add(verification)
            await self.db.commit()
            
            # Create verification URL
            verification_url = f"{self.base_url}/auth/verify-email?token={token}"
            
            # Create email template
            template = self._get_verification_email_template(
                email, first_name or "User", verification_url
            )
            
            # Send email
            email_sent = await self.send_email(email, template)
            
            if email_sent:
                return {
                    "success": True,
                    "message": "Verification email sent successfully",
                    "verification_id": str(verification.id),
                    "expires_at": expires_at.isoformat(),
                    "verification_token": token  # Only for internal use/testing
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to send verification email"
                }
                
        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Error sending verification email: {str(e)}"
            }
    
    async def verify_email(self, token: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Verify email with token"""
        try:
            # Hash the provided token
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # Find verification record
            stmt = select(EmailVerification).where(
                EmailVerification.token_hash == token_hash,
                EmailVerification.is_verified == False,
                EmailVerification.expires_at > datetime.utcnow()
            )
            result = await self.db.execute(stmt)
            verification = result.scalar_one_or_none()
            
            if not verification:
                return {
                    "success": False,
                    "message": "Invalid or expired verification token"
                }
            
            # Update verification record
            verification.is_verified = True
            verification.verified_at = datetime.utcnow()
            if ip_address:
                verification.ip_address = ip_address
            
            # Update user's verification status
            stmt = update(User).where(User.id == verification.user_id).values(
                is_verified=True,
                status="active",
                updated_at=datetime.utcnow()
            )
            await self.db.execute(stmt)
            
            # Get user info for response
            user_stmt = select(User).where(User.id == verification.user_id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            await self.db.commit()
            
            return {
                "success": True,
                "message": "Email verified successfully",
                "user_id": str(verification.user_id),
                "email": verification.email,
                "verified_at": verification.verified_at.isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Error verifying email: {str(e)}"
            }
    
    async def send_password_reset_email(
        self, 
        user_id: str, 
        email: str, 
        first_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send password reset email"""
        try:
            # Generate reset token
            token, token_hash = self._generate_token()
            expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
            
            # Store reset token in database
            reset = PasswordReset(
                user_id=user_id,
                email=email,
                token_hash=token_hash,
                expires_at=expires_at
            )
            
            self.db.add(reset)
            await self.db.commit()
            
            # Create reset URL
            reset_url = f"{self.base_url}/auth/reset-password?token={token}"
            
            # Create email template
            template = self._get_password_reset_email_template(
                email, first_name or "User", reset_url
            )
            
            # Send email
            email_sent = await self.send_email(email, template)
            
            if email_sent:
                return {
                    "success": True,
                    "message": "Password reset email sent successfully",
                    "reset_id": str(reset.id),
                    "expires_at": expires_at.isoformat(),
                    "reset_token": token  # Only for internal use/testing
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to send password reset email"
                }
                
        except Exception as e:
            await self.db.rollback()
            return {
                "success": False,
                "message": f"Error sending password reset email: {str(e)}"
            }
    
    def _get_verification_email_template(
        self, 
        email: str, 
        first_name: str, 
        verification_url: str
    ) -> EmailTemplate:
        """Get email verification template"""
        
        subject = "Verify Your Email Address"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Email Verification</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .button {{ 
                    display: inline-block; 
                    background: #4F46E5; 
                    color: white; 
                    padding: 12px 24px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }}
                .footer {{ padding: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Auth Service!</h1>
                </div>
                <div class="content">
                    <p>Hello {first_name},</p>
                    
                    <p>Thank you for creating your account! Please verify your email address to complete your registration and start using our service.</p>
                    
                    <p>Click the button below to verify your email:</p>
                    
                    <a href="{verification_url}" class="button">Verify Email Address</a>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p><a href="{verification_url}">{verification_url}</a></p>
                    
                    <p><strong>This verification link will expire in 24 hours.</strong></p>
                    
                    <p>If you didn't create this account, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>This email was sent to {email}</p>
                    <p>© 2024 Auth Service. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Hello {first_name},
        
        Thank you for creating your account! Please verify your email address to complete your registration.
        
        Click this link to verify your email:
        {verification_url}
        
        This verification link will expire in 24 hours.
        
        If you didn't create this account, you can safely ignore this email.
        
        This email was sent to {email}
        © 2024 Auth Service. All rights reserved.
        """
        
        return EmailTemplate(
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
    
    def _get_password_reset_email_template(
        self, 
        email: str, 
        first_name: str, 
        reset_url: str
    ) -> EmailTemplate:
        """Get password reset email template"""
        
        subject = "Reset Your Password"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Password Reset</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #DC2626; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .button {{ 
                    display: inline-block; 
                    background: #DC2626; 
                    color: white; 
                    padding: 12px 24px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }}
                .footer {{ padding: 20px; font-size: 12px; color: #666; }}
                .warning {{ background: #FEF3CD; padding: 15px; border-left: 4px solid #F59E0B; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hello {first_name},</p>
                    
                    <p>We received a request to reset your password. If you made this request, click the button below to set a new password:</p>
                    
                    <a href="{reset_url}" class="button">Reset Password</a>
                    
                    <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                    <p><a href="{reset_url}">{reset_url}</a></p>
                    
                    <div class="warning">
                        <strong>Important:</strong> This password reset link will expire in 1 hour for security reasons.
                    </div>
                    
                    <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
                </div>
                <div class="footer">
                    <p>This email was sent to {email}</p>
                    <p>© 2024 Auth Service. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Hello {first_name},
        
        We received a request to reset your password. If you made this request, click this link to set a new password:
        
        {reset_url}
        
        This password reset link will expire in 1 hour for security reasons.
        
        If you didn't request a password reset, you can safely ignore this email.
        
        This email was sent to {email}
        © 2024 Auth Service. All rights reserved.
        """
        
        return EmailTemplate(
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
    
    async def resend_verification_email(self, email: str) -> Dict[str, Any]:
        """Resend verification email to user"""
        try:
            # Find user by email
            stmt = select(User).where(User.email == email)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                # Don't reveal if email exists for security
                return {
                    "success": True,
                    "message": "If this email address exists, a verification email has been sent."
                }
            
            if user.is_verified:
                return {
                    "success": False,
                    "message": "This email address is already verified."
                }
            
            # Send verification email
            result = await self.send_verification_email(
                str(user.id), 
                user.email, 
                user.first_name
            )
            
            return {
                "success": True,
                "message": "Verification email sent successfully."
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": "Error sending verification email."
            }