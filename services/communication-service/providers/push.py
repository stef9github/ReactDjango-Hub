"""
Push Notification Providers
Firebase, Apple Push Notification Service (APNS), and other push delivery implementations
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import httpx
import jwt
import time
import logging

from .base import NotificationProvider, NotificationPayload, NotificationResult, NotificationStatus

logger = logging.getLogger(__name__)


class PushProvider(NotificationProvider):
    """Base class for push notification providers"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_payload_size = config.get("max_payload_size", 4096)  # 4KB default
        self.supports_batching = config.get("supports_batching", True)
        self.max_batch_size = config.get("max_batch_size", 500)
        
    def get_provider_info(self) -> Dict[str, Any]:
        info = super().get_provider_info()
        info.update({
            "supports_rich_content": True,
            "supports_actions": True,
            "supports_scheduling": True,
            "max_payload_size": self.max_payload_size,
            "supports_batching": self.supports_batching,
            "max_batch_size": self.max_batch_size,
        })
        return info
    
    async def validate_recipient(self, recipient: str) -> bool:
        """Validate push token format"""
        # Basic validation - token should be non-empty string
        return bool(recipient and len(recipient.strip()) > 10)


class FirebasePushProvider(PushProvider):
    """Firebase Cloud Messaging (FCM) push notification provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.project_id = config.get("project_id")
        self.private_key_id = config.get("private_key_id")
        self.private_key = config.get("private_key", "").replace("\\n", "\n")
        self.client_email = config.get("client_email")
        self.client_id = config.get("client_id")
        self.auth_uri = config.get("auth_uri", "https://accounts.google.com/o/oauth2/auth")
        self.token_uri = config.get("token_uri", "https://oauth2.googleapis.com/token")
        
        self.fcm_endpoint = f"https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send"
        self._access_token = None
        self._token_expires_at = 0
        
        if not all([self.project_id, self.private_key, self.client_email]):
            raise ValueError("Firebase project_id, private_key, and client_email are required")
    
    async def _get_access_token(self) -> str:
        """Get OAuth2 access token for FCM API"""
        # Check if current token is still valid
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token
        
        # Generate JWT for token request
        now = int(time.time())
        payload = {
            "iss": self.client_email,
            "scope": "https://www.googleapis.com/auth/firebase.messaging",
            "aud": self.token_uri,
            "iat": now,
            "exp": now + 3600,
        }
        
        # Create JWT
        token = jwt.encode(payload, self.private_key, algorithm="RS256")
        
        # Request access token
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": token
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self.token_uri, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self._access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self._token_expires_at = time.time() + expires_in
                return self._access_token
            else:
                raise Exception(f"Failed to get FCM access token: {response.status_code} {response.text}")
    
    async def send(self, payload: NotificationPayload) -> NotificationResult:
        """Send push notification via FCM"""
        try:
            # Validate push token
            if not await self.validate_recipient(payload.recipient):
                return NotificationResult(
                    id="",
                    status=NotificationStatus.REJECTED,
                    error_message=f"Invalid push token: {payload.recipient}"
                )
            
            # Get access token
            access_token = await self._get_access_token()
            
            # Build FCM message
            message = await self._build_fcm_message(payload)
            
            # Send to FCM
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    self.fcm_endpoint,
                    json={"message": message},
                    headers=headers
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    return NotificationResult(
                        id=response_data.get("name", "").split("/")[-1],
                        status=NotificationStatus.SENT,
                        provider_id=self.provider_name,
                        provider_response=response_data,
                        sent_at=datetime.utcnow(),
                        metadata={
                            "fcm_message_id": response_data.get("name"),
                            "token": payload.recipient,
                            "title": payload.subject,
                            "body": payload.content[:100]  # Truncate for logging
                        }
                    )
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"error": response.text}
                    return NotificationResult(
                        id="",
                        status=NotificationStatus.FAILED,
                        error_message=error_data.get("error", {}).get("message", f"HTTP {response.status_code}"),
                        provider_response=error_data
                    )
                    
        except Exception as e:
            logger.error(f"FCM send failed: {str(e)}")
            return NotificationResult(
                id="",
                status=NotificationStatus.FAILED,
                error_message=str(e)
            )
    
    async def _build_fcm_message(self, payload: NotificationPayload) -> Dict[str, Any]:
        """Build FCM message payload"""
        message = {
            "token": payload.recipient,
            "notification": {
                "title": payload.subject or "Notification",
                "body": payload.content[:4000]  # FCM body limit
            }
        }
        
        # Add data payload if present
        if payload.metadata:
            data = payload.metadata.get("data", {})
            if data:
                # Convert all values to strings (FCM requirement)
                message["data"] = {k: str(v) for k, v in data.items()}
            
            # Add Android-specific settings
            android_config = payload.metadata.get("android", {})
            if android_config:
                message["android"] = android_config
            
            # Add iOS-specific settings
            apns_config = payload.metadata.get("apns", {})
            if apns_config:
                message["apns"] = apns_config
            
            # Add web push settings
            webpush_config = payload.metadata.get("webpush", {})
            if webpush_config:
                message["webpush"] = webpush_config
        
        return message
    
    async def send_batch(self, payloads: List[NotificationPayload]) -> List[NotificationResult]:
        """Send multiple push notifications in batch"""
        # FCM doesn't have a native batch API, so we'll send individually but concurrently
        tasks = [self.send(payload) for payload in payloads[:self.max_batch_size]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to failed results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(NotificationResult(
                    id="",
                    status=NotificationStatus.FAILED,
                    error_message=str(result),
                    metadata={"batch_index": i}
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def get_delivery_status(self, notification_id: str) -> NotificationStatus:
        """Get push notification delivery status"""
        # FCM doesn't provide detailed delivery tracking by default
        # This would require implementing FCM analytics or delivery receipts
        return NotificationStatus.SENT
    
    async def cancel_notification(self, notification_id: str) -> bool:
        """Cancel push notification (not supported by FCM after sending)"""
        return False
    
    async def health_check(self) -> bool:
        """Check FCM connectivity"""
        if not self.is_enabled:
            return False
            
        try:
            # Try to get access token as health check
            await self._get_access_token()
            return True
            
        except Exception as e:
            logger.warning(f"FCM health check failed: {e}")
            return False


class APNSProvider(PushProvider):
    """Apple Push Notification Service provider (placeholder)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.team_id = config.get("team_id")
        self.key_id = config.get("key_id")
        self.private_key = config.get("private_key")
        self.bundle_id = config.get("bundle_id")
        self.use_sandbox = config.get("use_sandbox", False)
        
        self.apns_endpoint = "api.sandbox.push.apple.com" if self.use_sandbox else "api.push.apple.com"
    
    async def send(self, payload: NotificationPayload) -> NotificationResult:
        """Send push notification via APNS"""
        # TODO: Implement APNS HTTP/2 integration
        return NotificationResult(
            id="",
            status=NotificationStatus.FAILED,
            error_message="APNS provider not implemented yet"
        )
    
    async def get_delivery_status(self, notification_id: str) -> NotificationStatus:
        """Get delivery status from APNS"""
        return NotificationStatus.SENT
    
    async def cancel_notification(self, notification_id: str) -> bool:
        """Cancel push notification in APNS"""
        return False


class WebPushProvider(PushProvider):
    """Web Push protocol provider (placeholder)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.vapid_public_key = config.get("vapid_public_key")
        self.vapid_private_key = config.get("vapid_private_key")
        self.vapid_subject = config.get("vapid_subject")
    
    async def send(self, payload: NotificationPayload) -> NotificationResult:
        """Send web push notification"""
        # TODO: Implement Web Push protocol
        return NotificationResult(
            id="",
            status=NotificationStatus.FAILED,
            error_message="Web Push provider not implemented yet"
        )
    
    async def get_delivery_status(self, notification_id: str) -> NotificationStatus:
        """Get web push delivery status"""
        return NotificationStatus.SENT
    
    async def cancel_notification(self, notification_id: str) -> bool:
        """Cancel web push notification"""
        return False


# Provider factory
def create_push_provider(provider_type: str, config: Dict[str, Any]) -> PushProvider:
    """Create push provider instance based on type"""
    providers = {
        "firebase": FirebasePushProvider,
        "fcm": FirebasePushProvider,  # Alias
        "apns": APNSProvider,
        "webpush": WebPushProvider,
    }
    
    provider_class = providers.get(provider_type.lower())
    if not provider_class:
        raise ValueError(f"Unknown push provider type: {provider_type}")
    
    return provider_class(config)