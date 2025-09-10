"""
Redis-based processing queue manager for async document processing
"""

import json
import asyncio
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from uuid import UUID, uuid4
import time

import aioredis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


@dataclass
class ProcessingTask:
    """Represents a document processing task"""
    id: str
    document_id: str
    organization_id: str
    user_id: str
    task_type: str  # 'metadata_extraction', 'ocr', 'thumbnail', etc.
    priority: int = 5  # 1 (highest) to 10 (lowest)
    attempts: int = 0
    max_attempts: int = 3
    created_at: str = ""
    scheduled_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    failed_at: Optional[str] = None
    status: str = "pending"  # pending, processing, completed, failed, cancelled
    
    # Task-specific data
    file_path: str = ""
    mime_type: str = ""
    parameters: Dict[str, Any] = None
    
    # Results and error handling
    result: Dict[str, Any] = None
    error_message: Optional[str] = None
    retry_after: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.scheduled_at:
            self.scheduled_at = self.created_at
        if self.parameters is None:
            self.parameters = {}
        if self.result is None:
            self.result = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingTask':
        """Create task from dictionary"""
        return cls(**data)
    
    def should_retry(self) -> bool:
        """Check if task should be retried"""
        return (
            self.status == "failed" and
            self.attempts < self.max_attempts and
            (not self.retry_after or datetime.fromisoformat(self.retry_after) <= datetime.utcnow())
        )
    
    def calculate_retry_delay(self) -> int:
        """Calculate exponential backoff delay in seconds"""
        base_delay = 60  # 1 minute
        return min(base_delay * (2 ** self.attempts), 3600)  # Max 1 hour


class ProcessingQueueManager:
    """Redis-based queue manager for document processing tasks"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", queue_prefix: str = "content_processing"):
        self.redis_url = redis_url
        self.queue_prefix = queue_prefix
        self.redis_client: Optional[aioredis.Redis] = None
        
        # Queue names
        self.priority_queues = [
            f"{queue_prefix}:high",    # Priority 1-3
            f"{queue_prefix}:normal",  # Priority 4-6  
            f"{queue_prefix}:low"      # Priority 7-10
        ]
        
        self.processing_set = f"{queue_prefix}:processing"
        self.completed_set = f"{queue_prefix}:completed"
        self.failed_set = f"{queue_prefix}:failed"
        self.task_data_key = f"{queue_prefix}:tasks"
        self.stats_key = f"{queue_prefix}:stats"
        
        # Worker management
        self.workers: List['BackgroundWorker'] = []
        self.shutdown_event = asyncio.Event()
        
        logger.info(f"Initialized ProcessingQueueManager with prefix '{queue_prefix}'")
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Successfully connected to Redis")
            
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def enqueue_task(self, task: ProcessingTask) -> bool:
        """Add task to processing queue"""
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")
        
        try:
            # Serialize task
            task_json = json.dumps(task.to_dict())
            
            # Store task data
            await self.redis_client.hset(self.task_data_key, task.id, task_json)
            
            # Add to appropriate priority queue
            queue_name = self._get_queue_for_priority(task.priority)
            await self.redis_client.lpush(queue_name, task.id)
            
            # Update statistics
            await self._increment_stat("tasks_enqueued")
            await self._increment_stat(f"tasks_enqueued_{task.task_type}")
            
            logger.info(f"Enqueued task {task.id} of type {task.task_type} to queue {queue_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue task {task.id}: {e}")
            return False
    
    async def dequeue_task(self, timeout: int = 10) -> Optional[ProcessingTask]:
        """Get next task from queues (blocking)"""
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")
        
        try:
            # Try to get task from priority queues (high to low)
            result = await self.redis_client.brpop(self.priority_queues, timeout=timeout)
            
            if not result:
                return None
            
            queue_name, task_id = result
            
            # Get task data
            task_json = await self.redis_client.hget(self.task_data_key, task_id)
            if not task_json:
                logger.warning(f"Task {task_id} not found in task data")
                return None
            
            # Deserialize task
            task_data = json.loads(task_json)
            task = ProcessingTask.from_dict(task_data)
            
            # Mark as processing
            task.status = "processing"
            task.started_at = datetime.utcnow().isoformat()
            task.attempts += 1
            
            # Move to processing set
            await self.redis_client.sadd(self.processing_set, task_id)
            
            # Update task data
            await self._update_task(task)
            
            logger.debug(f"Dequeued task {task_id} from {queue_name}")
            return task
            
        except Exception as e:
            logger.error(f"Failed to dequeue task: {e}")
            return None
    
    async def complete_task(self, task: ProcessingTask, result: Dict[str, Any] = None):
        """Mark task as completed"""
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")
        
        try:
            task.status = "completed"
            task.completed_at = datetime.utcnow().isoformat()
            if result:
                task.result = result
            
            # Move from processing to completed
            await self.redis_client.srem(self.processing_set, task.id)
            await self.redis_client.sadd(self.completed_set, task.id)
            
            # Update task data
            await self._update_task(task)
            
            # Update statistics
            await self._increment_stat("tasks_completed")
            await self._increment_stat(f"tasks_completed_{task.task_type}")
            
            # Set TTL for completed tasks (cleanup after 7 days)
            await self.redis_client.expire(f"{self.task_data_key}:{task.id}", 7 * 24 * 3600)
            
            logger.info(f"Completed task {task.id}")
            
        except Exception as e:
            logger.error(f"Failed to complete task {task.id}: {e}")
    
    async def fail_task(self, task: ProcessingTask, error_message: str, retry: bool = True):
        """Mark task as failed and optionally retry"""
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")
        
        try:
            task.status = "failed"
            task.failed_at = datetime.utcnow().isoformat()
            task.error_message = error_message
            
            # Remove from processing set
            await self.redis_client.srem(self.processing_set, task.id)
            
            if retry and task.should_retry():
                # Schedule for retry
                retry_delay = task.calculate_retry_delay()
                task.retry_after = (datetime.utcnow() + timedelta(seconds=retry_delay)).isoformat()
                task.status = "pending"  # Reset to pending for retry
                
                # Re-queue with delay (using sorted set for scheduling)
                score = time.time() + retry_delay
                await self.redis_client.zadd(f"{self.queue_prefix}:delayed", {task.id: score})
                
                logger.info(f"Scheduled task {task.id} for retry in {retry_delay} seconds (attempt {task.attempts})")
            else:
                # Move to failed set
                await self.redis_client.sadd(self.failed_set, task.id)
                logger.error(f"Failed task {task.id} permanently: {error_message}")
            
            # Update task data
            await self._update_task(task)
            
            # Update statistics
            await self._increment_stat("tasks_failed")
            await self._increment_stat(f"tasks_failed_{task.task_type}")
            
        except Exception as e:
            logger.error(f"Failed to handle task failure {task.id}: {e}")
    
    async def get_task(self, task_id: str) -> Optional[ProcessingTask]:
        """Get task by ID"""
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")
        
        try:
            task_json = await self.redis_client.hget(self.task_data_key, task_id)
            if task_json:
                task_data = json.loads(task_json)
                return ProcessingTask.from_dict(task_data)
            return None
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")
        
        try:
            task = await self.get_task(task_id)
            if not task:
                return False
            
            if task.status in ["completed", "cancelled"]:
                return True
            
            if task.status == "processing":
                logger.warning(f"Cannot cancel task {task_id} - already processing")
                return False
            
            # Remove from all queues
            for queue in self.priority_queues:
                await self.redis_client.lrem(queue, 0, task_id)
            
            await self.redis_client.zrem(f"{self.queue_prefix}:delayed", task_id)
            
            # Mark as cancelled
            task.status = "cancelled"
            await self._update_task(task)
            
            logger.info(f"Cancelled task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")
        
        try:
            stats = {}
            
            # Queue lengths
            for queue in self.priority_queues:
                length = await self.redis_client.llen(queue)
                queue_name = queue.split(':')[-1]
                stats[f"queue_{queue_name}_length"] = length
            
            # Set sizes
            stats["processing_count"] = await self.redis_client.scard(self.processing_set)
            stats["completed_count"] = await self.redis_client.scard(self.completed_set)
            stats["failed_count"] = await self.redis_client.scard(self.failed_set)
            
            # Delayed tasks
            stats["delayed_count"] = await self.redis_client.zcard(f"{self.queue_prefix}:delayed")
            
            # Performance stats
            perf_stats = await self.redis_client.hgetall(self.stats_key)
            stats.update({k: int(v) for k, v in perf_stats.items() if v.isdigit()})
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {}
    
    async def process_delayed_tasks(self):
        """Process delayed tasks that are ready to run"""
        if not self.redis_client:
            return
        
        try:
            current_time = time.time()
            
            # Get ready tasks from delayed queue
            ready_tasks = await self.redis_client.zrangebyscore(
                f"{self.queue_prefix}:delayed", 0, current_time
            )
            
            for task_id in ready_tasks:
                # Remove from delayed queue
                await self.redis_client.zrem(f"{self.queue_prefix}:delayed", task_id)
                
                # Get task data
                task = await self.get_task(task_id)
                if task:
                    # Re-queue task
                    queue_name = self._get_queue_for_priority(task.priority)
                    await self.redis_client.lpush(queue_name, task_id)
                    logger.info(f"Re-queued delayed task {task_id}")
                    
        except Exception as e:
            logger.error(f"Failed to process delayed tasks: {e}")
    
    def _get_queue_for_priority(self, priority: int) -> str:
        """Get queue name for given priority"""
        if priority <= 3:
            return self.priority_queues[0]  # high
        elif priority <= 6:
            return self.priority_queues[1]  # normal
        else:
            return self.priority_queues[2]  # low
    
    async def _update_task(self, task: ProcessingTask):
        """Update task data in Redis"""
        task_json = json.dumps(task.to_dict())
        await self.redis_client.hset(self.task_data_key, task.id, task_json)
    
    async def _increment_stat(self, stat_name: str):
        """Increment a statistic counter"""
        await self.redis_client.hincrby(self.stats_key, stat_name, 1)
        
        # Also increment daily stat
        today = datetime.utcnow().strftime('%Y-%m-%d')
        await self.redis_client.hincrby(f"{self.stats_key}:daily:{today}", stat_name, 1)
        
        # Set TTL on daily stats (keep for 30 days)
        await self.redis_client.expire(f"{self.stats_key}:daily:{today}", 30 * 24 * 3600)
    
    async def cleanup_old_tasks(self, days_to_keep: int = 7):
        """Clean up old completed and failed tasks"""
        if not self.redis_client:
            return
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        cutoff_timestamp = cutoff_date.isoformat()
        
        try:
            # Get all completed and failed task IDs
            completed_tasks = await self.redis_client.smembers(self.completed_set)
            failed_tasks = await self.redis_client.smembers(self.failed_set)
            
            tasks_to_cleanup = []
            
            for task_id in completed_tasks + failed_tasks:
                task = await self.get_task(task_id)
                if task and (
                    (task.completed_at and task.completed_at < cutoff_timestamp) or
                    (task.failed_at and task.failed_at < cutoff_timestamp)
                ):
                    tasks_to_cleanup.append(task_id)
            
            # Remove old tasks
            for task_id in tasks_to_cleanup:
                await self.redis_client.hdel(self.task_data_key, task_id)
                await self.redis_client.srem(self.completed_set, task_id)
                await self.redis_client.srem(self.failed_set, task_id)
            
            if tasks_to_cleanup:
                logger.info(f"Cleaned up {len(tasks_to_cleanup)} old tasks")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old tasks: {e}")