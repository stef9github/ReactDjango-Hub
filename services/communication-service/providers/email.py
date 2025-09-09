"""
Email Notification Providers
SMTP and email delivery implementations
"""
import asyncio
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, Any, Optional, List
import aiosmtplib
import logging

from .base import NotificationProvider, NotificationPayload, NotificationResult, NotificationStatus

logger = logging.getLogger(__name__)


class EmailProvider(NotificationProvider):
    """Base class for email notification providers"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.from_email = config.get("from_email", "noreply@example.com")
        self.from_name = config.get("from_name", "Communication Service")
        self.reply_to = config.get("reply_to")
        self.max_content_length = config.get("max_content_length", 1000000)  # 1MB
        
    def get_provider_info(self) -> Dict[str, Any]:
        info = super().get_provider_info()
        info.update({
            "supports_html": True,
            "supports_attachments": True,
            "supports_delivery_receipts": True,
            "max_content_length": self.max_content_length,
            "from_email": self.from_email,
        })
        return info
    
    async def validate_recipient(self, recipient: str) -> bool:
        """Validate email address format"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, recipient))


class SMTPProvider(EmailProvider):
    """SMTP-based email provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_host = config.get("smtp_host", "localhost")
        self.smtp_port = config.get("smtp_port", 587)
        self.smtp_username = config.get("smtp_username")
        self.smtp_password = config.get("smtp_password")
        self.use_tls = config.get("use_tls", True)
        self.use_ssl = config.get("use_ssl", False)
        
    async def send(self, payload: NotificationPayload) -> NotificationResult:
        """Send email via SMTP"""
        try:
            # Validate recipient
            if not await self.validate_recipient(payload.recipient):
                return NotificationResult(
                    id="",
                    status=NotificationStatus.REJECTED,
                    error_message=f"Invalid email address: {payload.recipient}"
                )
            
            # Create email message
            message = await self._create_message(payload)
            
            # Send email
            result = await self._send_smtp(message, payload.recipient)
            return result
            
        except Exception as e:
            logger.error(f"SMTP send failed: {str(e)}")
            return NotificationResult(
                id="",
                status=NotificationStatus.FAILED,
                error_message=str(e)
            )
    
    async def _create_message(self, payload: NotificationPayload) -> MIMEMultipart:
        """Create email message from payload"""
        message = MIMEMultipart("alternative")
        
        # Headers
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = payload.recipient
        message["Subject"] = payload.subject or "Notification"
        
        if self.reply_to:
            message["Reply-To"] = self.reply_to
            
        # Add message ID for tracking
        message_id = f"<{payload.metadata.get('id', 'unknown')}@{self.smtp_host}>"
        message["Message-ID"] = message_id
        
        # Content - support both plain text and HTML
        if payload.metadata and payload.metadata.get("content_type") == "html":
            # HTML content
            html_part = MIMEText(payload.content, "html", "utf-8")
            message.attach(html_part)
            
            # Also include plain text version
            plain_content = self._html_to_text(payload.content)
            text_part = MIMEText(plain_content, "plain", "utf-8")
            message.attach(text_part)
        else:
            # Plain text content
            text_part = MIMEText(payload.content, "plain", "utf-8")
            message.attach(text_part)
        
        # Add attachments if present
        attachments = payload.metadata.get("attachments", []) if payload.metadata else []
        for attachment in attachments:
            await self._add_attachment(message, attachment)
        
        return message
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text (basic implementation)"""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return text.strip()
    
    async def _add_attachment(self, message: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message"""
        try:
            filename = attachment.get("filename", "attachment")
            content = attachment.get("content", b"")
            content_type = attachment.get("content_type", "application/octet-stream")
            
            part = MIMEBase(*content_type.split("/"))
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}"
            )
            message.attach(part)
        except Exception as e:
            logger.warning(f"Failed to add attachment {attachment.get('filename', 'unknown')}: {e}")
    
    async def _send_smtp(self, message: MIMEMultipart, recipient: str) -> NotificationResult:
        """Send email via SMTP using aiosmtplib"""
        try:
            # Configure SMTP connection
            smtp_kwargs = {
                "hostname": self.smtp_host,
                "port": self.smtp_port,
                "timeout": self.timeout_seconds,
            }
            
            if self.use_ssl:
                smtp_kwargs["use_tls"] = True
                smtp_kwargs["tls_context"] = ssl.create_default_context()
            elif self.use_tls:
                smtp_kwargs["start_tls"] = True
                smtp_kwargs["tls_context"] = ssl.create_default_context()
            
            # Send email
            async with aiosmtplib.SMTP(**smtp_kwargs) as smtp:
                if self.smtp_username and self.smtp_password:
                    await smtp.login(self.smtp_username, self.smtp_password)
                
                await smtp.send_message(message, recipients=[recipient])
            
            return NotificationResult(
                id=message["Message-ID"].strip("<>"),
                status=NotificationStatus.SENT,
                provider_id=self.provider_name,
                sent_at=datetime.utcnow(),
                metadata={
                    "smtp_host": self.smtp_host,
                    "recipient": recipient,
                    "subject": message["Subject"]
                }
            )
            
        except aiosmtplib.SMTPException as e:
            logger.error(f"SMTP error sending to {recipient}: {e}")
            return NotificationResult(
                id="",
                status=NotificationStatus.FAILED,
                error_message=f"SMTP error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error sending email to {recipient}: {e}")
            return NotificationResult(
                id="",
                status=NotificationStatus.FAILED,
                error_message=str(e)
            )
    
    async def get_delivery_status(self, notification_id: str) -> NotificationStatus:
        """Get delivery status (basic implementation - SMTP doesn't provide detailed tracking)"""
        # SMTP doesn't provide delivery receipts by default
        # This would need to be implemented with bounce handling or external services
        return NotificationStatus.SENT
    
    async def cancel_notification(self, notification_id: str) -> bool:
        """Cancel notification (not supported for SMTP after sending)"""
        return False
    
    async def health_check(self) -> bool:
        """Check SMTP server connectivity"""
        if not self.is_enabled:
            return False
            
        try:
            # Quick connection test
            smtp_kwargs = {
                "hostname": self.smtp_host,
                "port": self.smtp_port,
                "timeout": 5,  # Short timeout for health check
            }
            
            async with aiosmtplib.SMTP(**smtp_kwargs) as smtp:
                # Just test connection, don't authenticate
                pass
            
            return True
            
        except Exception as e:
            logger.warning(f"SMTP health check failed: {e}")
            return False


class SendGridProvider(EmailProvider):
    """SendGrid email provider (placeholder for future implementation)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = "https://api.sendgrid.com/v3"
    
    async def send(self, payload: NotificationPayload) -> NotificationResult:
        """Send email via SendGrid API"""
        # TODO: Implement SendGrid API integration
        return NotificationResult(
            id="",
            status=NotificationStatus.FAILED,
            error_message="SendGrid provider not implemented yet"
        )
    
    async def get_delivery_status(self, notification_id: str) -> NotificationStatus:
        """Get delivery status from SendGrid"""
        # TODO: Implement SendGrid webhook handling
        return NotificationStatus.SENT
    
    async def cancel_notification(self, notification_id: str) -> bool:
        """Cancel scheduled email in SendGrid"""
        # TODO: Implement SendGrid cancellation
        return False


class MailgunProvider(EmailProvider):
    """Mailgun email provider (placeholder for future implementation)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.domain = config.get("domain")
        self.base_url = f"https://api.mailgun.net/v3/{self.domain}"
    
    async def send(self, payload: NotificationPayload) -> NotificationResult:
        """Send email via Mailgun API"""
        # TODO: Implement Mailgun API integration
        return NotificationResult(
            id="",
            status=NotificationStatus.FAILED,
            error_message="Mailgun provider not implemented yet"
        )
    
    async def get_delivery_status(self, notification_id: str) -> NotificationStatus:
        """Get delivery status from Mailgun"""
        # TODO: Implement Mailgun event tracking
        return NotificationStatus.SENT
    
    async def cancel_notification(self, notification_id: str) -> bool:
        """Cancel scheduled email in Mailgun"""
        # TODO: Implement Mailgun cancellation
        return False


# Provider factory
def create_email_provider(provider_type: str, config: Dict[str, Any]) -> EmailProvider:
    """Create email provider instance based on type"""
    providers = {
        "smtp": SMTPProvider,
        "sendgrid": SendGridProvider,
        "mailgun": MailgunProvider,
    }
    
    provider_class = providers.get(provider_type.lower())
    if not provider_class:
        raise ValueError(f"Unknown email provider type: {provider_type}")
    
    return provider_class(config)