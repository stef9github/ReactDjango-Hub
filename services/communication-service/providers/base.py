"""
Base Notification Provider Classes
Abstract interfaces for multi-channel notification delivery
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid


class NotificationStatus(Enum):
    """Notification delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class NotificationResult:
    """Result of notification delivery attempt"""
    id: str
    status: NotificationStatus
    provider_id: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cost: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.status == NotificationStatus.SENT and not self.sent_at:
            self.sent_at = datetime.utcnow()


@dataclass
class NotificationPayload:
    """Generic notification payload"""
    recipient: str
    subject: Optional[str] = None
    content: str = ""
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    priority: str = "normal"  # low, normal, high, urgent
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class NotificationProvider(ABC):
    """
    Abstract base class for notification providers
    Defines the interface that all notification providers must implement
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize provider with configuration
        
        Args:
            config: Provider-specific configuration dict
        """
        self.config = config
        self.provider_name = self.__class__.__name__
        self.is_enabled = config.get("enabled", True)
        self.rate_limit = config.get("rate_limit_per_minute", 60)
        self.retry_attempts = config.get("retry_attempts", 3)
        self.timeout_seconds = config.get("timeout_seconds", 30)

    @abstractmethod
    async def send(self, payload: NotificationPayload) -> NotificationResult:
        """
        Send notification using this provider
        
        Args:
            payload: Notification data to send
            
        Returns:
            NotificationResult with delivery status and details
        """
        pass

    @abstractmethod
    async def get_delivery_status(self, notification_id: str) -> NotificationStatus:
        """
        Get current delivery status of a notification
        
        Args:
            notification_id: ID of notification to check
            
        Returns:
            Current NotificationStatus
        """
        pass

    @abstractmethod
    async def cancel_notification(self, notification_id: str) -> bool:
        """
        Cancel a pending/scheduled notification
        
        Args:
            notification_id: ID of notification to cancel
            
        Returns:
            True if successfully cancelled
        """
        pass

    async def health_check(self) -> bool:
        """
        Check if provider is healthy and can send notifications
        
        Returns:
            True if provider is operational
        """
        return self.is_enabled

    async def validate_recipient(self, recipient: str) -> bool:
        """
        Validate if recipient address/number is valid for this provider
        
        Args:
            recipient: Recipient address to validate
            
        Returns:
            True if recipient is valid
        """
        return bool(recipient and recipient.strip())

    async def estimate_cost(self, payload: NotificationPayload) -> Optional[float]:
        """
        Estimate cost for sending this notification
        
        Args:
            payload: Notification payload
            
        Returns:
            Estimated cost in USD, or None if not available
        """
        return None

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get provider information and capabilities
        
        Returns:
            Dict with provider details
        """
        return {
            "name": self.provider_name,
            "enabled": self.is_enabled,
            "rate_limit": self.rate_limit,
            "retry_attempts": self.retry_attempts,
            "timeout_seconds": self.timeout_seconds,
            "supports_scheduling": False,
            "supports_templates": False,
            "supports_delivery_receipts": False,
            "max_content_length": None,
        }


class FailoverProvider:
    """
    Failover provider that tries multiple providers in order
    """

    def __init__(self, providers: List[NotificationProvider], max_retries: int = 3):
        """
        Initialize with list of providers in priority order
        
        Args:
            providers: List of providers to try in order
            max_retries: Maximum retry attempts across all providers
        """
        self.providers = providers
        self.max_retries = max_retries

    async def send(self, payload: NotificationPayload) -> NotificationResult:
        """
        Send notification with failover logic
        
        Args:
            payload: Notification payload to send
            
        Returns:
            NotificationResult from successful provider or last failure
        """
        last_result = None
        
        for attempt in range(self.max_retries):
            for provider in self.providers:
                if not provider.is_enabled:
                    continue
                    
                try:
                    # Check provider health before sending
                    if not await provider.health_check():
                        continue
                    
                    # Validate recipient for this provider
                    if not await provider.validate_recipient(payload.recipient):
                        continue
                    
                    # Attempt to send
                    result = await provider.send(payload)
                    
                    # Return on success
                    if result.status in [NotificationStatus.SENT, NotificationStatus.QUEUED]:
                        return result
                    
                    last_result = result
                    
                except Exception as e:
                    last_result = NotificationResult(
                        id=str(uuid.uuid4()),
                        status=NotificationStatus.FAILED,
                        error_message=f"{provider.provider_name}: {str(e)}",
                        metadata={"attempt": attempt + 1, "provider": provider.provider_name}
                    )

        # All providers failed
        return last_result or NotificationResult(
            id=str(uuid.uuid4()),
            status=NotificationStatus.FAILED,
            error_message="All providers failed"
        )


class LoadBalancingProvider:
    """
    Load balancing provider that distributes notifications across multiple providers
    """

    def __init__(self, providers: List[NotificationProvider], strategy: str = "round_robin"):
        """
        Initialize with providers and load balancing strategy
        
        Args:
            providers: List of providers to distribute load across
            strategy: Load balancing strategy (round_robin, random, weighted)
        """
        self.providers = [p for p in providers if p.is_enabled]
        self.strategy = strategy
        self.current_index = 0

    def _select_provider(self) -> NotificationProvider:
        """Select next provider based on strategy"""
        if not self.providers:
            raise ValueError("No enabled providers available")
        
        if self.strategy == "round_robin":
            provider = self.providers[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.providers)
            return provider
        
        elif self.strategy == "random":
            import random
            return random.choice(self.providers)
        
        else:  # Default to first available
            return self.providers[0]

    async def send(self, payload: NotificationPayload) -> NotificationResult:
        """
        Send notification using load balancing
        
        Args:
            payload: Notification payload to send
            
        Returns:
            NotificationResult from selected provider
        """
        provider = self._select_provider()
        return await provider.send(payload)