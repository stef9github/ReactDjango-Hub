"""
Redis client configuration for Communication Service
Handles caching, session storage, and real-time features
"""
import os
import json
import pickle
from typing import Optional, Any, Dict, List, Union
from contextlib import asynccontextmanager, contextmanager
import redis
import redis.asyncio as aioredis
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RedisConfig:
    """Redis configuration and connection management"""
    
    def __init__(self):
        self.redis_url = self._get_redis_url()
        self.cache_ttl = int(os.getenv("REDIS_CACHE_TTL", "3600"))  # 1 hour default
        self.max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
        
        # Initialize sync and async clients
        self.sync_client = self._create_sync_client()
        self.async_client = None  # Will be initialized when needed
    
    def _get_redis_url(self) -> str:
        """Get Redis URL from environment variables"""
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            # Fallback to component parts
            host = os.getenv("REDIS_HOST", "localhost")
            port = os.getenv("REDIS_PORT", "6382")
            db = os.getenv("REDIS_DB", "0")
            password = os.getenv("REDIS_PASSWORD", "")
            
            if password:
                redis_url = f"redis://:{password}@{host}:{port}/{db}"
            else:
                redis_url = f"redis://{host}:{port}/{db}"
        
        logger.info(f"Redis URL configured: {redis_url.split('@')[-1] if '@' in redis_url else redis_url}")
        return redis_url
    
    def _create_sync_client(self) -> redis.Redis:
        """Create synchronous Redis client"""
        client = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=self.max_connections,
            health_check_interval=30,
        )
        
        # Test connection
        try:
            client.ping()
            logger.info("Redis sync client connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        
        return client
    
    async def _create_async_client(self) -> aioredis.Redis:
        """Create asynchronous Redis client"""
        if self.async_client is None:
            self.async_client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=self.max_connections,
                health_check_interval=30,
            )
            
            # Test connection
            try:
                await self.async_client.ping()
                logger.info("Redis async client connected successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis async: {e}")
                raise
        
        return self.async_client
    
    def health_check(self) -> bool:
        """Check Redis connectivity"""
        try:
            self.sync_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def async_health_check(self) -> bool:
        """Check Redis connectivity (async)"""
        try:
            client = await self._create_async_client()
            await client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis async health check failed: {e}")
            return False

# Global Redis configuration
redis_config = RedisConfig()

class CacheManager:
    """Generic caching functionality"""
    
    def __init__(self, redis_client: redis.Redis, prefix: str = "comm"):
        self.client = redis_client
        self.prefix = prefix
    
    def _key(self, key: str) -> str:
        """Add service prefix to cache key"""
        return f"{self.prefix}:{key}"
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cache value with optional TTL"""
        try:
            ttl = ttl or redis_config.cache_ttl
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            
            if ttl:
                return self.client.setex(self._key(key), ttl, serialized_value)
            else:
                return self.client.set(self._key(key), serialized_value)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get cache value"""
        try:
            value = self.client.get(self._key(key))
            if value is None:
                return default
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """Delete cache entry"""
        try:
            return bool(self.client.delete(self._key(key)))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if cache key exists"""
        try:
            return bool(self.client.exists(self._key(key)))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """Get time to live for cache key"""
        try:
            return self.client.ttl(self._key(key))
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -1
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            keys = self.client.keys(self._key(pattern))
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0

class TemplateCache:
    """Specialized caching for notification templates"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get cached template"""
        return self.cache.get(f"template:{template_id}")
    
    def set_template(self, template_id: str, template_data: Dict[str, Any], ttl: int = 1800) -> bool:
        """Cache template for 30 minutes by default"""
        return self.cache.set(f"template:{template_id}", template_data, ttl)
    
    def invalidate_template(self, template_id: str) -> bool:
        """Remove template from cache"""
        return self.cache.delete(f"template:{template_id}")
    
    def get_rendered_template(self, template_id: str, data_hash: str) -> Optional[str]:
        """Get cached rendered template"""
        cache_key = f"rendered:{template_id}:{data_hash}"
        return self.cache.get(cache_key)
    
    def set_rendered_template(
        self, 
        template_id: str, 
        data_hash: str, 
        rendered_content: str, 
        ttl: int = 300
    ) -> bool:
        """Cache rendered template for 5 minutes by default"""
        cache_key = f"rendered:{template_id}:{data_hash}"
        return self.cache.set(cache_key, rendered_content, ttl)

class UserPreferenceCache:
    """Caching for user notification preferences"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user preferences"""
        return self.cache.get(f"prefs:{user_id}")
    
    def set_preferences(self, user_id: str, preferences: Dict[str, Any], ttl: int = 1800) -> bool:
        """Cache user preferences for 30 minutes"""
        return self.cache.set(f"prefs:{user_id}", preferences, ttl)
    
    def invalidate_preferences(self, user_id: str) -> bool:
        """Remove user preferences from cache"""
        return self.cache.delete(f"prefs:{user_id}")

class SessionManager:
    """WebSocket session management for real-time features"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    def create_session(self, user_id: str, session_id: str, metadata: Dict[str, Any]) -> bool:
        """Create user session"""
        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "metadata": metadata
        }
        return self.cache.set(f"session:{session_id}", session_data, ttl=3600)  # 1 hour
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return self.cache.get(f"session:{session_id}")
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity"""
        session = self.get_session(session_id)
        if session:
            session["last_activity"] = datetime.utcnow().isoformat()
            return self.cache.set(f"session:{session_id}", session, ttl=3600)
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        return self.cache.delete(f"session:{session_id}")
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all session IDs for a user"""
        pattern = "session:*"
        session_keys = redis_config.sync_client.keys(f"comm:{pattern}")
        
        user_sessions = []
        for key in session_keys:
            session_data = self.cache.get(key.replace("comm:", ""))
            if session_data and session_data.get("user_id") == user_id:
                session_id = key.split(":")[-1]
                user_sessions.append(session_id)
        
        return user_sessions

class NotificationQueue:
    """Queue management for background notification processing"""
    
    def __init__(self, redis_client: redis.Redis):
        self.client = redis_client
        self.queue_name = "comm:notification_queue"
        self.processing_queue = "comm:processing_queue"
        self.failed_queue = "comm:failed_queue"
    
    def enqueue_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Add notification to processing queue"""
        try:
            serialized = json.dumps(notification_data)
            return bool(self.client.lpush(self.queue_name, serialized))
        except Exception as e:
            logger.error(f"Failed to enqueue notification: {e}")
            return False
    
    def dequeue_notification(self, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """Get next notification from queue"""
        try:
            result = self.client.brpop(self.queue_name, timeout=timeout)
            if result:
                _, data = result
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue notification: {e}")
            return None
    
    def get_queue_length(self) -> int:
        """Get current queue length"""
        try:
            return self.client.llen(self.queue_name)
        except Exception as e:
            logger.error(f"Failed to get queue length: {e}")
            return 0
    
    def move_to_failed(self, notification_data: Dict[str, Any]) -> bool:
        """Move failed notification to failed queue"""
        try:
            notification_data["failed_at"] = datetime.utcnow().isoformat()
            serialized = json.dumps(notification_data)
            return bool(self.client.lpush(self.failed_queue, serialized))
        except Exception as e:
            logger.error(f"Failed to move notification to failed queue: {e}")
            return False

# Initialize global instances
cache_manager = CacheManager(redis_config.sync_client)
template_cache = TemplateCache(cache_manager)
user_preference_cache = UserPreferenceCache(cache_manager)
session_manager = SessionManager(cache_manager)
notification_queue = NotificationQueue(redis_config.sync_client)

# Utility functions
def get_cache_stats() -> Dict[str, Any]:
    """Get Redis cache statistics"""
    try:
        info = redis_config.sync_client.info()
        return {
            "redis_version": info.get("redis_version"),
            "used_memory": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients"),
            "total_commands_processed": info.get("total_commands_processed"),
            "keyspace": info.get("db0", {}),
            "queue_lengths": {
                "notifications": notification_queue.get_queue_length(),
                "failed": redis_config.sync_client.llen("comm:failed_queue"),
            }
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"error": str(e)}

def clear_all_cache() -> bool:
    """Clear all communication service cache entries"""
    try:
        keys = redis_config.sync_client.keys("comm:*")
        if keys:
            redis_config.sync_client.delete(*keys)
            logger.info(f"Cleared {len(keys)} cache entries")
        return True
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        return False