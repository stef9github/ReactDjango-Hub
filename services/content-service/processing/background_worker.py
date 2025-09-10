"""
Background worker for processing document tasks
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, Any, Optional, Callable, List
import time
import traceback
from datetime import datetime

from .queue_manager import ProcessingQueueManager, ProcessingTask
from .metadata_processor import metadata_processor

logger = logging.getLogger(__name__)


class BackgroundWorker:
    """Background worker that processes tasks from the queue"""
    
    def __init__(
        self, 
        queue_manager: ProcessingQueueManager,
        worker_id: str = None,
        max_concurrent_tasks: int = 3,
        polling_interval: int = 5,
        health_check_interval: int = 60
    ):
        self.queue_manager = queue_manager
        self.worker_id = worker_id or f"worker-{int(time.time())}"
        self.max_concurrent_tasks = max_concurrent_tasks
        self.polling_interval = polling_interval
        self.health_check_interval = health_check_interval
        
        # Worker state
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        self.current_tasks: List[asyncio.Task] = []
        
        # Statistics
        self.stats = {
            "started_at": datetime.utcnow().isoformat(),
            "tasks_processed": 0,
            "tasks_successful": 0,
            "tasks_failed": 0,
            "last_activity": None,
            "current_load": 0
        }
        
        # Processors
        self.processors = {
            "metadata_extraction": metadata_processor,
            "ocr": metadata_processor,
            "content_analysis": metadata_processor
        }
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        logger.info(f"Initialized BackgroundWorker {self.worker_id}")
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    async def start(self):
        """Start the background worker"""
        if self.is_running:
            logger.warning(f"Worker {self.worker_id} is already running")
            return
        
        self.is_running = True
        logger.info(f"Starting background worker {self.worker_id}")
        
        # Start main processing loop
        processing_task = asyncio.create_task(self._processing_loop())
        
        # Start health check loop
        health_task = asyncio.create_task(self._health_check_loop())
        
        # Start delayed task processor
        delayed_task = asyncio.create_task(self._delayed_task_loop())
        
        try:
            # Wait for shutdown event
            await self.shutdown_event.wait()
            
            logger.info(f"Worker {self.worker_id} shutting down...")
            
            # Cancel background tasks
            processing_task.cancel()
            health_task.cancel()
            delayed_task.cancel()
            
            # Wait for current tasks to complete (with timeout)
            if self.current_tasks:
                logger.info(f"Waiting for {len(self.current_tasks)} active tasks to complete...")
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*self.current_tasks, return_exceptions=True),
                        timeout=30.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("Tasks did not complete within timeout, forcing shutdown")
                    for task in self.current_tasks:
                        task.cancel()
            
            logger.info(f"Worker {self.worker_id} stopped")
            
        except asyncio.CancelledError:
            logger.info(f"Worker {self.worker_id} cancelled")
        except Exception as e:
            logger.error(f"Worker {self.worker_id} error: {e}")
        finally:
            self.is_running = False
    
    async def shutdown(self):
        """Gracefully shutdown the worker"""
        logger.info(f"Shutdown requested for worker {self.worker_id}")
        self.shutdown_event.set()
    
    async def _processing_loop(self):
        """Main processing loop"""
        logger.info(f"Started processing loop for worker {self.worker_id}")
        
        while not self.shutdown_event.is_set():
            try:
                # Check if we can handle more tasks
                if len(self.current_tasks) >= self.max_concurrent_tasks:
                    # Clean up completed tasks
                    self.current_tasks = [task for task in self.current_tasks if not task.done()]
                    
                    if len(self.current_tasks) >= self.max_concurrent_tasks:
                        # Wait a bit before checking again
                        await asyncio.sleep(1)
                        continue
                
                # Try to get a task from the queue
                task = await self.queue_manager.dequeue_task(timeout=self.polling_interval)
                
                if task:
                    # Process task in background
                    processing_task = asyncio.create_task(self._process_task(task))
                    self.current_tasks.append(processing_task)
                    
                    logger.debug(f"Started processing task {task.id}, active tasks: {len(self.current_tasks)}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
        
        logger.info(f"Processing loop stopped for worker {self.worker_id}")
    
    async def _process_task(self, task: ProcessingTask):
        """Process a single task"""
        start_time = time.time()
        
        try:
            logger.info(f"Processing task {task.id} (type: {task.task_type}, attempt: {task.attempts})")
            
            # Update statistics
            self.stats["tasks_processed"] += 1
            self.stats["current_load"] = len(self.current_tasks)
            self.stats["last_activity"] = datetime.utcnow().isoformat()
            
            # Get appropriate processor
            processor = self.processors.get(task.task_type)
            if not processor:
                raise ValueError(f"No processor available for task type: {task.task_type}")
            
            # Validate task
            if hasattr(processor, 'validate_task_parameters'):
                validation_result = await processor.validate_task_parameters(task)
                if not validation_result["valid"]:
                    raise ValueError(f"Task validation failed: {validation_result['errors']}")
                
                if validation_result["warnings"]:
                    logger.warning(f"Task {task.id} warnings: {validation_result['warnings']}")
            
            # Process the task
            result = await processor.process_task(task)
            
            # Mark task as completed
            await self.queue_manager.complete_task(task, result)
            
            # Update statistics
            self.stats["tasks_successful"] += 1
            processing_time = time.time() - start_time
            
            logger.info(f"Successfully processed task {task.id} in {processing_time:.2f}s")
            
        except asyncio.CancelledError:
            logger.info(f"Task {task.id} was cancelled")
            await self.queue_manager.fail_task(task, "Task cancelled", retry=False)
            
        except Exception as e:
            error_msg = f"Task processing failed: {str(e)}"
            logger.error(f"Failed to process task {task.id}: {error_msg}")
            logger.debug(f"Task {task.id} error traceback: {traceback.format_exc()}")
            
            # Mark task as failed (with retry if appropriate)
            await self.queue_manager.fail_task(task, error_msg, retry=True)
            
            # Update statistics
            self.stats["tasks_failed"] += 1
        
        finally:
            # Update current load
            self.stats["current_load"] = len(self.current_tasks) - 1
    
    async def _health_check_loop(self):
        """Health check and maintenance loop"""
        logger.info(f"Started health check loop for worker {self.worker_id}")
        
        while not self.shutdown_event.is_set():
            try:
                # Clean up completed tasks
                before_cleanup = len(self.current_tasks)
                self.current_tasks = [task for task in self.current_tasks if not task.done()]
                after_cleanup = len(self.current_tasks)
                
                if before_cleanup != after_cleanup:
                    logger.debug(f"Cleaned up {before_cleanup - after_cleanup} completed tasks")
                
                # Update current load
                self.stats["current_load"] = len(self.current_tasks)
                
                # Log health status
                logger.info(f"Worker {self.worker_id} health: "
                          f"active_tasks={len(self.current_tasks)}, "
                          f"processed={self.stats['tasks_processed']}, "
                          f"successful={self.stats['tasks_successful']}, "
                          f"failed={self.stats['tasks_failed']}")
                
                # Wait for next health check
                try:
                    await asyncio.wait_for(
                        self.shutdown_event.wait(),
                        timeout=self.health_check_interval
                    )
                    break  # Shutdown event was set
                except asyncio.TimeoutError:
                    continue  # Continue health check loop
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(10)
        
        logger.info(f"Health check loop stopped for worker {self.worker_id}")
    
    async def _delayed_task_loop(self):
        """Process delayed tasks loop"""
        logger.info(f"Started delayed task processor for worker {self.worker_id}")
        
        while not self.shutdown_event.is_set():
            try:
                # Process delayed tasks that are ready
                await self.queue_manager.process_delayed_tasks()
                
                # Wait before next check (shorter interval for delayed tasks)
                try:
                    await asyncio.wait_for(
                        self.shutdown_event.wait(),
                        timeout=10  # Check delayed tasks every 10 seconds
                    )
                    break
                except asyncio.TimeoutError:
                    continue
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in delayed task loop: {e}")
                await asyncio.sleep(10)
        
        logger.info(f"Delayed task processor stopped for worker {self.worker_id}")
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        return {
            "worker_id": self.worker_id,
            "is_running": self.is_running,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "current_tasks": len(self.current_tasks),
            **self.stats
        }
    
    def get_processor_info(self) -> Dict[str, Any]:
        """Get information about available processors"""
        processors_info = {}
        for task_type, processor in self.processors.items():
            if hasattr(processor, 'get_processor_info'):
                processors_info[task_type] = processor.get_processor_info()
            else:
                processors_info[task_type] = {
                    "name": processor.__class__.__name__,
                    "version": getattr(processor, 'version', 'unknown')
                }
        
        return {
            "supported_task_types": list(self.processors.keys()),
            "processors": processors_info
        }


async def start_worker(
    redis_url: str = "redis://localhost:6379/0",
    worker_id: str = None,
    max_concurrent_tasks: int = 3
) -> BackgroundWorker:
    """Convenience function to start a background worker"""
    
    # Create queue manager
    queue_manager = ProcessingQueueManager(redis_url)
    await queue_manager.connect()
    
    # Create and start worker
    worker = BackgroundWorker(
        queue_manager=queue_manager,
        worker_id=worker_id,
        max_concurrent_tasks=max_concurrent_tasks
    )
    
    # Start worker (this will run until shutdown)
    await worker.start()
    
    # Cleanup
    await queue_manager.disconnect()
    
    return worker


if __name__ == "__main__":
    """Run worker as standalone script"""
    import os
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get configuration from environment
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    worker_id = os.getenv("WORKER_ID", None)
    max_concurrent_tasks = int(os.getenv("MAX_CONCURRENT_TASKS", "3"))
    
    logger.info(f"Starting background worker with Redis: {redis_url}")
    
    try:
        asyncio.run(start_worker(
            redis_url=redis_url,
            worker_id=worker_id,
            max_concurrent_tasks=max_concurrent_tasks
        ))
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)