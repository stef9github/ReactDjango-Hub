"""
Tests for Redis client and caching functionality
"""
import pytest
from unittest.mock import patch, MagicMock
import json
import os

from redis_client import (
    RedisConfig, CacheManager, TemplateCache, UserPreferenceCache, 
    SessionManager, NotificationQueue, get_cache_stats, clear_all_cache
)

class TestRedisConfig:
    """Test RedisConfig class"""
    
    def test_redis_url_from_env(self):
        """Test Redis URL configuration from environment"""
        with patch.dict(os.environ, {'REDIS_URL': 'redis://localhost:6379/5'}):
            config = RedisConfig()
            assert config.redis_url == 'redis://localhost:6379/5'
    
    def test_redis_url_from_components(self):
        """Test Redis URL construction from components"""
        env_vars = {
            'REDIS_HOST': 'redis-host',
            'REDIS_PORT': '6380',
            'REDIS_DB': '3',
            'REDIS_PASSWORD': 'secret'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = RedisConfig()
            expected_url = 'redis://:secret@redis-host:6380/3'
            assert config.redis_url == expected_url
    
    def test_redis_url_without_password(self):
        """Test Redis URL construction without password"""
        env_vars = {
            'REDIS_HOST': 'redis-host',
            'REDIS_PORT': '6380',
            'REDIS_DB': '3'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = RedisConfig()
            expected_url = 'redis://redis-host:6380/3'
            assert config.redis_url == expected_url
    
    def test_default_redis_url(self):
        """Test default Redis URL"""
        env_vars_to_clear = ['REDIS_URL', 'REDIS_HOST', 'REDIS_PORT', 'REDIS_DB', 'REDIS_PASSWORD']
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('redis_client.redis.from_url') as mock_redis:
                mock_redis.return_value.ping.return_value = True
                config = RedisConfig()
                expected_url = 'redis://localhost:6382/0'
                assert config.redis_url == expected_url
    
    def test_health_check_success(self, mock_redis):
        """Test successful Redis health check"""
        config = RedisConfig()
        config.sync_client = mock_redis
        
        mock_redis.ping.return_value = True
        assert config.health_check() is True
    
    def test_health_check_failure(self, mock_redis):
        """Test failed Redis health check"""
        config = RedisConfig()
        config.sync_client = mock_redis
        
        mock_redis.ping.side_effect = Exception("Connection failed")
        assert config.health_check() is False

class TestCacheManager:
    """Test CacheManager functionality"""
    
    def test_cache_key_prefix(self, mock_redis):
        """Test cache key prefixing"""
        cache = CacheManager(mock_redis, prefix="test")
        
        cache.set("key1", "value1")
        mock_redis.setex.assert_called_with("test:key1", cache.client.cache_ttl, "value1")
    
    def test_set_cache_with_ttl(self, mock_redis):
        """Test setting cache value with TTL"""
        cache = CacheManager(mock_redis)
        
        cache.set("test_key", {"data": "value"}, ttl=300)
        
        expected_value = json.dumps({"data": "value"})
        mock_redis.setex.assert_called_with("comm:test_key", 300, expected_value)
    
    def test_set_cache_without_ttl(self, mock_redis):
        """Test setting cache value without TTL"""
        cache = CacheManager(mock_redis)
        
        cache.set("test_key", "simple_value")
        mock_redis.set.assert_called_with("comm:test_key", "simple_value")
    
    def test_get_cache_json_value(self, mock_redis):
        """Test getting JSON cache value"""
        cache = CacheManager(mock_redis)
        
        json_value = json.dumps({"data": "value"})
        mock_redis.get.return_value = json_value
        
        result = cache.get("test_key")
        assert result == {"data": "value"}
    
    def test_get_cache_string_value(self, mock_redis):
        """Test getting string cache value"""
        cache = CacheManager(mock_redis)
        
        mock_redis.get.return_value = "simple_value"
        
        result = cache.get("test_key")
        assert result == "simple_value"
    
    def test_get_cache_nonexistent(self, mock_redis):
        """Test getting nonexistent cache value"""
        cache = CacheManager(mock_redis)
        
        mock_redis.get.return_value = None
        
        result = cache.get("nonexistent_key", default="default_value")
        assert result == "default_value"
    
    def test_delete_cache(self, mock_redis):
        """Test deleting cache entry"""
        cache = CacheManager(mock_redis)
        
        mock_redis.delete.return_value = 1
        result = cache.delete("test_key")
        
        assert result is True
        mock_redis.delete.assert_called_with("comm:test_key")
    
    def test_cache_exists(self, mock_redis):
        """Test checking cache existence"""
        cache = CacheManager(mock_redis)
        
        mock_redis.exists.return_value = 1
        result = cache.exists("test_key")
        
        assert result is True
        mock_redis.exists.assert_called_with("comm:test_key")
    
    def test_cache_ttl(self, mock_redis):
        """Test getting cache TTL"""
        cache = CacheManager(mock_redis)
        
        mock_redis.ttl.return_value = 300
        result = cache.ttl("test_key")
        
        assert result == 300
        mock_redis.ttl.assert_called_with("comm:test_key")
    
    def test_clear_pattern(self, mock_redis):
        """Test clearing cache entries by pattern"""
        cache = CacheManager(mock_redis)
        
        mock_redis.keys.return_value = ["comm:pattern:key1", "comm:pattern:key2"]
        mock_redis.delete.return_value = 2
        
        result = cache.clear_pattern("pattern:*")
        
        assert result == 2
        mock_redis.keys.assert_called_with("comm:pattern:*")
        mock_redis.delete.assert_called_with("comm:pattern:key1", "comm:pattern:key2")

class TestTemplateCache:
    """Test TemplateCache functionality"""
    
    def test_get_template(self, mock_cache_manager):
        """Test getting cached template"""
        template_cache = TemplateCache(mock_cache_manager)
        
        mock_cache_manager.get.return_value = {"name": "test_template", "content": "Hello {{name}}"}
        
        result = template_cache.get_template("template_123")
        
        assert result["name"] == "test_template"
        mock_cache_manager.get.assert_called_with("template:template_123")
    
    def test_set_template(self, mock_cache_manager):
        """Test setting cached template"""
        template_cache = TemplateCache(mock_cache_manager)
        
        template_data = {"name": "test_template", "content": "Hello {{name}}"}
        
        template_cache.set_template("template_123", template_data, ttl=600)
        
        mock_cache_manager.set.assert_called_with("template:template_123", template_data, 600)
    
    def test_invalidate_template(self, mock_cache_manager):
        """Test invalidating cached template"""
        template_cache = TemplateCache(mock_cache_manager)
        
        template_cache.invalidate_template("template_123")
        
        mock_cache_manager.delete.assert_called_with("template:template_123")
    
    def test_rendered_template_cache(self, mock_cache_manager):
        """Test rendered template caching"""
        template_cache = TemplateCache(mock_cache_manager)
        
        # Test setting rendered template
        template_cache.set_rendered_template("template_123", "hash_abc", "Rendered content", ttl=300)
        mock_cache_manager.set.assert_called_with("rendered:template_123:hash_abc", "Rendered content", 300)
        
        # Test getting rendered template
        mock_cache_manager.get.return_value = "Rendered content"
        result = template_cache.get_rendered_template("template_123", "hash_abc")
        
        assert result == "Rendered content"
        mock_cache_manager.get.assert_called_with("rendered:template_123:hash_abc")

class TestUserPreferenceCache:
    """Test UserPreferenceCache functionality"""
    
    def test_get_preferences(self, mock_cache_manager):
        """Test getting cached user preferences"""
        pref_cache = UserPreferenceCache(mock_cache_manager)
        
        prefs = {"email_enabled": True, "sms_enabled": False}
        mock_cache_manager.get.return_value = prefs
        
        result = pref_cache.get_preferences("user_123")
        
        assert result == prefs
        mock_cache_manager.get.assert_called_with("prefs:user_123")
    
    def test_set_preferences(self, mock_cache_manager):
        """Test setting cached user preferences"""
        pref_cache = UserPreferenceCache(mock_cache_manager)
        
        prefs = {"email_enabled": True, "sms_enabled": False}
        
        pref_cache.set_preferences("user_123", prefs, ttl=600)
        
        mock_cache_manager.set.assert_called_with("prefs:user_123", prefs, 600)
    
    def test_invalidate_preferences(self, mock_cache_manager):
        """Test invalidating cached user preferences"""
        pref_cache = UserPreferenceCache(mock_cache_manager)
        
        pref_cache.invalidate_preferences("user_123")
        
        mock_cache_manager.delete.assert_called_with("prefs:user_123")

class TestSessionManager:
    """Test SessionManager functionality"""
    
    def test_create_session(self, mock_cache_manager):
        """Test creating user session"""
        session_manager = SessionManager(mock_cache_manager)
        
        metadata = {"device": "mobile", "location": "US"}
        session_manager.create_session("user_123", "session_abc", metadata)
        
        # Verify cache.set was called with session data
        call_args = mock_cache_manager.set.call_args
        assert call_args[0][0] == "session:session_abc"
        
        session_data = call_args[0][1]
        assert session_data["user_id"] == "user_123"
        assert session_data["metadata"] == metadata
        assert "created_at" in session_data
    
    def test_get_session(self, mock_cache_manager):
        """Test getting session data"""
        session_manager = SessionManager(mock_cache_manager)
        
        session_data = {
            "user_id": "user_123",
            "created_at": "2023-01-01T00:00:00",
            "metadata": {"device": "mobile"}
        }
        mock_cache_manager.get.return_value = session_data
        
        result = session_manager.get_session("session_abc")
        
        assert result == session_data
        mock_cache_manager.get.assert_called_with("session:session_abc")
    
    def test_update_session_activity(self, mock_cache_manager):
        """Test updating session activity"""
        session_manager = SessionManager(mock_cache_manager)
        
        # Mock existing session
        session_data = {
            "user_id": "user_123",
            "created_at": "2023-01-01T00:00:00",
            "metadata": {}
        }
        mock_cache_manager.get.return_value = session_data
        
        session_manager.update_session_activity("session_abc")
        
        # Verify that set was called with updated session data
        call_args = mock_cache_manager.set.call_args
        updated_data = call_args[0][1]
        assert "last_activity" in updated_data
    
    def test_delete_session(self, mock_cache_manager):
        """Test deleting session"""
        session_manager = SessionManager(mock_cache_manager)
        
        session_manager.delete_session("session_abc")
        
        mock_cache_manager.delete.assert_called_with("session:session_abc")

class TestNotificationQueue:
    """Test NotificationQueue functionality"""
    
    def test_enqueue_notification(self, mock_redis):
        """Test enqueueing notification"""
        queue = NotificationQueue(mock_redis)
        
        notification_data = {"user_id": "123", "content": "Test notification"}
        
        mock_redis.lpush.return_value = 1
        result = queue.enqueue_notification(notification_data)
        
        assert result is True
        
        # Verify data was serialized and enqueued
        call_args = mock_redis.lpush.call_args[0]
        assert call_args[0] == "comm:notification_queue"
        assert json.loads(call_args[1]) == notification_data
    
    def test_dequeue_notification(self, mock_redis):
        """Test dequeueing notification"""
        queue = NotificationQueue(mock_redis)
        
        notification_data = {"user_id": "123", "content": "Test notification"}
        serialized_data = json.dumps(notification_data)
        mock_redis.brpop.return_value = ("comm:notification_queue", serialized_data)
        
        result = queue.dequeue_notification()
        
        assert result == notification_data
        mock_redis.brpop.assert_called_with("comm:notification_queue", timeout=0)
    
    def test_dequeue_empty_queue(self, mock_redis):
        """Test dequeueing from empty queue"""
        queue = NotificationQueue(mock_redis)
        
        mock_redis.brpop.return_value = None
        
        result = queue.dequeue_notification()
        
        assert result is None
    
    def test_get_queue_length(self, mock_redis):
        """Test getting queue length"""
        queue = NotificationQueue(mock_redis)
        
        mock_redis.llen.return_value = 5
        result = queue.get_queue_length()
        
        assert result == 5
        mock_redis.llen.assert_called_with("comm:notification_queue")
    
    def test_move_to_failed(self, mock_redis):
        """Test moving notification to failed queue"""
        queue = NotificationQueue(mock_redis)
        
        notification_data = {"user_id": "123", "content": "Test notification"}
        
        mock_redis.lpush.return_value = 1
        result = queue.move_to_failed(notification_data)
        
        assert result is True
        
        # Verify data includes failed_at timestamp
        call_args = mock_redis.lpush.call_args[0]
        assert call_args[0] == "comm:failed_queue"
        
        failed_data = json.loads(call_args[1])
        assert "failed_at" in failed_data
        assert failed_data["user_id"] == "123"

class TestRedisUtilities:
    """Test Redis utility functions"""
    
    def test_get_cache_stats(self, mock_redis):
        """Test getting cache statistics"""
        with patch('redis_client.redis_config') as mock_config:
            mock_config.sync_client = mock_redis
            
            # Mock Redis info
            mock_redis.info.return_value = {
                "redis_version": "6.2.0",
                "used_memory_human": "1.5M",
                "connected_clients": 5,
                "total_commands_processed": 1000,
                "db0": {"keys": 100, "expires": 50}
            }
            
            # Mock queue lengths
            mock_redis.llen.side_effect = [10, 2]  # notification queue, failed queue
            
            with patch('redis_client.notification_queue') as mock_queue:
                mock_queue.get_queue_length.return_value = 10
                
                stats = get_cache_stats()
                
                assert stats["redis_version"] == "6.2.0"
                assert stats["used_memory"] == "1.5M"
                assert stats["connected_clients"] == 5
                assert stats["queue_lengths"]["notifications"] == 10
    
    def test_clear_all_cache(self, mock_redis):
        """Test clearing all cache entries"""
        with patch('redis_client.redis_config') as mock_config:
            mock_config.sync_client = mock_redis
            
            mock_redis.keys.return_value = ["comm:key1", "comm:key2", "comm:key3"]
            
            result = clear_all_cache()
            
            assert result is True
            mock_redis.keys.assert_called_with("comm:*")
            mock_redis.delete.assert_called_with("comm:key1", "comm:key2", "comm:key3")