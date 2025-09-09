"""
Event publishing and messaging service
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from .config import settings


@dataclass
class Event:
    """Event data structure"""
    type: str
    data: Dict[str, Any]
    timestamp: str
    service: str = "auth-service"
    version: str = "1.0"


class EventPublisher:
    """Event publisher for Kafka integration"""
    
    def __init__(self):
        self.kafka_enabled = bool(settings.KAFKA_BOOTSTRAP_SERVERS)
        self.topic_prefix = settings.KAFKA_TOPIC_PREFIX
        self.events_queue = []  # In-memory queue for development
    
    async def publish(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Publish event to message queue"""
        try:
            event = Event(
                type=event_type,
                data=data,
                timestamp=datetime.utcnow().isoformat()
            )
            
            if self.kafka_enabled:
                return await self._publish_to_kafka(event)
            else:
                return await self._publish_to_memory(event)
                
        except Exception as e:
            print(f"Failed to publish event {event_type}: {str(e)}")
            return False
    
    async def _publish_to_kafka(self, event: Event) -> bool:
        """Publish event to Kafka"""
        try:
            # In a real implementation, you would use aiokafka or similar
            # from aiokafka import AIOKafkaProducer
            # 
            # producer = AIOKafkaProducer(
            #     bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            #     value_serializer=lambda v: json.dumps(v).encode('utf-8')
            # )
            # await producer.start()
            # 
            # topic = f"{self.topic_prefix}.{event.type}"
            # await producer.send(topic, asdict(event))
            # await producer.stop()
            
            # For now, just log the event
            print(f"Kafka Event: {event.type} - {json.dumps(asdict(event), indent=2)}")
            return True
            
        except Exception as e:
            print(f"Kafka publish error: {str(e)}")
            return False
    
    async def _publish_to_memory(self, event: Event) -> bool:
        """Publish event to in-memory queue (development)"""
        try:
            self.events_queue.append(event)
            print(f"Memory Event: {event.type} - {json.dumps(asdict(event), indent=2)}")
            
            # Keep only last 100 events in memory
            if len(self.events_queue) > 100:
                self.events_queue = self.events_queue[-100:]
            
            return True
            
        except Exception as e:
            print(f"Memory publish error: {str(e)}")
            return False
    
    def get_recent_events(self, limit: int = 10) -> list:
        """Get recent events from memory queue"""
        return [asdict(event) for event in self.events_queue[-limit:]]