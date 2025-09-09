"""
SMS Notification Providers
Twilio and other SMS delivery implementations
"""
import asyncio
import re
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
import logging

from .base import NotificationProvider, NotificationPayload, NotificationResult, NotificationStatus

logger = logging.getLogger(__name__)


class SMSProvider(NotificationProvider):
    """Base class for SMS notification providers"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.from_number = config.get("from_number", "+1234567890")
        self.max_message_length = config.get("max_message_length", 160)
        self.enable_unicode = config.get("enable_unicode", True)
        
    def get_provider_info(self) -> Dict[str, Any]:
        info = super().get_provider_info()
        info.update({
            "supports_unicode": self.enable_unicode,
            "max_content_length": self.max_message_length,
            "from_number": self.from_number,
        })
        return info
    
    async def validate_recipient(self, recipient: str) -> bool:
        """Validate phone number format"""
        # Basic phone number validation (E.164 format)
        phone_pattern = r'^\+[1-9]\d{1,14}$'
        return bool(re.match(phone_pattern, recipient))
    
    def format_phone_number(self, phone: str) -> str:
        """Format phone number to E.164 format"""
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Add + if not present
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
            
        return cleaned
    
    def truncate_message(self, content: str, max_length: int = None) -> str:
        """Truncate message to fit SMS length limits"""
        max_len = max_length or self.max_message_length
        
        if len(content) <= max_len:
            return content
            
        # Truncate and add ellipsis
        return content[:max_len-3] + "..."


class TwilioProvider(SMSProvider):
    """Twilio SMS provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.account_sid = config.get("account_sid")
        self.auth_token = config.get("auth_token")
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"
        
        if not self.account_sid or not self.auth_token:
            raise ValueError("Twilio account_sid and auth_token are required")
    
    async def send(self, payload: NotificationPayload) -> NotificationResult:
        """Send SMS via Twilio API"""
        try:
            # Format and validate phone number
            recipient = self.format_phone_number(payload.recipient)
            if not await self.validate_recipient(recipient):
                return NotificationResult(
                    id="",
                    status=NotificationStatus.REJECTED,
                    error_message=f"Invalid phone number: {payload.recipient}"
                )
            
            # Prepare message content
            content = self.truncate_message(payload.content)
            
            # Twilio API request
            url = f"{self.base_url}/Messages.json"
            data = {
                "From": self.from_number,
                "To": recipient,
                "Body": content
            }
            
            # Add media URLs if present (MMS)
            media_urls = []
            if payload.metadata:
                media_urls = payload.metadata.get("media_urls", [])
                if media_urls:
                    data["MediaUrl"] = media_urls
            
            # Make API request
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                auth = (self.account_sid, self.auth_token)
                response = await client.post(url, data=data, auth=auth)
                
                if response.status_code == 201:
                    response_data = response.json()
                    return NotificationResult(
                        id=response_data.get("sid", ""),
                        status=NotificationStatus.QUEUED,
                        provider_id=self.provider_name,
                        provider_response=response_data,
                        sent_at=datetime.utcnow(),
                        cost=float(response_data.get("price", 0)) if response_data.get("price") else None,
                        metadata={
                            "twilio_sid": response_data.get("sid"),
                            "to": recipient,
                            "from": self.from_number,
                            "body": content,
                            "num_segments": response_data.get("num_segments", 1)
                        }
                    )
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"error": response.text}
                    return NotificationResult(
                        id="",
                        status=NotificationStatus.FAILED,
                        error_message=error_data.get("message", f"HTTP {response.status_code}"),
                        provider_response=error_data
                    )
                    
        except httpx.TimeoutException:
            return NotificationResult(
                id="",
                status=NotificationStatus.FAILED,
                error_message="Request timeout"
            )
        except Exception as e:
            logger.error(f"Twilio send failed: {str(e)}")
            return NotificationResult(
                id="",
                status=NotificationStatus.FAILED,
                error_message=str(e)
            )
    
    async def get_delivery_status(self, notification_id: str) -> NotificationStatus:
        """Get SMS delivery status from Twilio"""
        try:
            url = f"{self.base_url}/Messages/{notification_id}.json"
            
            async with httpx.AsyncClient(timeout=10) as client:
                auth = (self.account_sid, self.auth_token)
                response = await client.get(url, auth=auth)
                
                if response.status_code == 200:
                    data = response.json()
                    twilio_status = data.get("status", "unknown")
                    
                    # Map Twilio statuses to our enum
                    status_mapping = {
                        "queued": NotificationStatus.QUEUED,
                        "sending": NotificationStatus.SENDING,
                        "sent": NotificationStatus.SENT,
                        "delivered": NotificationStatus.DELIVERED,
                        "failed": NotificationStatus.FAILED,
                        "undelivered": NotificationStatus.FAILED,
                        "canceled": NotificationStatus.CANCELLED,
                    }
                    
                    return status_mapping.get(twilio_status, NotificationStatus.FAILED)
                else:
                    return NotificationStatus.FAILED
                    
        except Exception as e:
            logger.error(f"Failed to get Twilio status for {notification_id}: {e}")
            return NotificationStatus.FAILED
    
    async def cancel_notification(self, notification_id: str) -> bool:
        """Cancel SMS in Twilio (only works for scheduled messages)"""
        try:
            url = f"{self.base_url}/Messages/{notification_id}.json"
            data = {"Status": "canceled"}
            
            async with httpx.AsyncClient(timeout=10) as client:
                auth = (self.account_sid, self.auth_token)
                response = await client.post(url, data=data, auth=auth)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Failed to cancel Twilio message {notification_id}: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check Twilio API connectivity"""
        if not self.is_enabled:
            return False
            
        try:
            # Test API connectivity by fetching account info
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}.json"
            
            async with httpx.AsyncClient(timeout=5) as client:
                auth = (self.account_sid, self.auth_token)
                response = await client.get(url, auth=auth)
                return response.status_code == 200
                
        except Exception as e:
            logger.warning(f"Twilio health check failed: {e}")
            return False
    
    async def estimate_cost(self, payload: NotificationPayload) -> Optional[float]:
        """Estimate SMS cost based on content length and destination"""
        # Basic cost estimation (would need to be more sophisticated in production)
        content_length = len(payload.content)
        segments = (content_length // 160) + (1 if content_length % 160 > 0 else 0)
        
        # Basic US SMS pricing (actual pricing varies by destination)
        base_cost_per_segment = 0.0075  # $0.0075 per segment
        
        return segments * base_cost_per_segment


class AWSSNSProvider(SMSProvider):
    """AWS SNS SMS provider (placeholder for future implementation)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.aws_access_key = config.get("aws_access_key_id")
        self.aws_secret_key = config.get("aws_secret_access_key")
        self.region = config.get("region", "us-east-1")
    
    async def send(self, payload: NotificationPayload) -> NotificationResult:
        """Send SMS via AWS SNS"""
        # TODO: Implement AWS SNS integration
        return NotificationResult(
            id="",
            status=NotificationStatus.FAILED,
            error_message="AWS SNS provider not implemented yet"
        )
    
    async def get_delivery_status(self, notification_id: str) -> NotificationStatus:
        """Get delivery status from AWS SNS"""
        # TODO: Implement SNS delivery status
        return NotificationStatus.SENT
    
    async def cancel_notification(self, notification_id: str) -> bool:
        """Cancel SMS in AWS SNS"""
        # TODO: Implement SNS cancellation
        return False


class OVHSMSProvider(SMSProvider):
    """OVH SMS provider for European markets (placeholder)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.application_key = config.get("application_key")
        self.application_secret = config.get("application_secret")
        self.consumer_key = config.get("consumer_key")
        self.service_name = config.get("service_name")
        self.endpoint = config.get("endpoint", "ovh-eu")
    
    async def send(self, payload: NotificationPayload) -> NotificationResult:
        """Send SMS via OVH API"""
        # TODO: Implement OVH SMS API integration
        return NotificationResult(
            id="",
            status=NotificationStatus.FAILED,
            error_message="OVH SMS provider not implemented yet"
        )
    
    async def get_delivery_status(self, notification_id: str) -> NotificationStatus:
        """Get delivery status from OVH"""
        # TODO: Implement OVH delivery status
        return NotificationStatus.SENT
    
    async def cancel_notification(self, notification_id: str) -> bool:
        """Cancel SMS in OVH"""
        # TODO: Implement OVH cancellation
        return False


# Provider factory
def create_sms_provider(provider_type: str, config: Dict[str, Any]) -> SMSProvider:
    """Create SMS provider instance based on type"""
    providers = {
        "twilio": TwilioProvider,
        "aws_sns": AWSSNSProvider,
        "ovh": OVHSMSProvider,
    }
    
    provider_class = providers.get(provider_type.lower())
    if not provider_class:
        raise ValueError(f"Unknown SMS provider type: {provider_type}")
    
    return provider_class(config)