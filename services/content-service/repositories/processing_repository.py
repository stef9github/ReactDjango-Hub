"""
Processing job repository for managing document processing tasks.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from models.processing import ProcessingJob, ProcessingJobType, JobStatus


class ProcessingJobRepository(BaseRepository[ProcessingJob]):
    """Repository for processing job operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ProcessingJob)
    
    async def create_job(
        self,
        document_id: UUID,
        job_type: ProcessingJobType,
        priority: int = 5,
        config: Dict[str, Any] = None,
        webhook_url: Optional[str] = None,
        webhook_headers: Dict[str, str] = None,
        max_retries: int = 3
    ) -> ProcessingJob:
        """Create a new processing job."""
        job = await self.create(
            document_id=document_id,
            job_type=job_type,
            priority=priority,
            config=config or {},
            webhook_url=webhook_url,
            webhook_headers=webhook_headers or {},
            max_retries=max_retries,
            status=JobStatus.PENDING
        )
        return job
    
    async def get_next_job(self, processor_types: List[ProcessingJobType] = None) -> Optional[ProcessingJob]:
        """Get the next job to process from the queue."""
        conditions = [ProcessingJob.status == JobStatus.PENDING]
        
        if processor_types:
            conditions.append(ProcessingJob.job_type.in_(processor_types))
        
        stmt = (
            select(ProcessingJob)
            .where(and_(*conditions))
            .options(selectinload(ProcessingJob.document))
            .order_by(ProcessingJob.priority, ProcessingJob.created_at)
            .limit(1)
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_retry_jobs(self, limit: int = 10) -> List[ProcessingJob]:
        """Get jobs that are ready for retry."""
        now = datetime.utcnow()
        
        stmt = (
            select(ProcessingJob)
            .where(and_(
                ProcessingJob.status == JobStatus.FAILED,
                ProcessingJob.retry_count < ProcessingJob.max_retries,
                ProcessingJob.next_retry_at <= now
            ))
            .options(selectinload(ProcessingJob.document))
            .order_by(ProcessingJob.next_retry_at)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def mark_job_started(self, job_id: UUID, processor_name: str = None) -> Optional[ProcessingJob]:
        """Mark a job as started."""
        job = await self.get_by_id(job_id)
        if job and job.status == JobStatus.PENDING:
            job.mark_started()
            if processor_name:
                job.processor_name = processor_name
            await self.session.flush()
            await self.session.refresh(job)
        return job
    
    async def mark_job_completed(
        self,
        job_id: UUID,
        result: Dict[str, Any],
        processor_version: str = None
    ) -> Optional[ProcessingJob]:
        """Mark a job as completed with results."""
        job = await self.get_by_id(job_id)
        if job and job.status == JobStatus.RUNNING:
            job.mark_completed(result)
            if processor_version:
                job.processor_version = processor_version
            await self.session.flush()
            await self.session.refresh(job)
        return job
    
    async def mark_job_failed(
        self,
        job_id: UUID,
        error_message: str,
        error_details: Dict[str, Any] = None,
        schedule_retry: bool = True
    ) -> Optional[ProcessingJob]:
        """Mark a job as failed with error information."""
        job = await self.get_by_id(job_id)
        if job and job.status == JobStatus.RUNNING:
            job.mark_failed(error_message, error_details, schedule_retry)
            await self.session.flush()
            await self.session.refresh(job)
        return job
    
    async def cancel_job(self, job_id: UUID) -> Optional[ProcessingJob]:
        """Cancel a pending or running job."""
        job = await self.get_by_id(job_id)
        if job and job.status in (JobStatus.PENDING, JobStatus.RUNNING):
            job.mark_cancelled()
            await self.session.flush()
            await self.session.refresh(job)
        return job
    
    async def get_document_jobs(
        self,
        document_id: UUID,
        status: Optional[JobStatus] = None,
        job_type: Optional[ProcessingJobType] = None
    ) -> List[ProcessingJob]:
        """Get all jobs for a specific document."""
        filters = {"document_id": document_id}
        
        if status:
            filters["status"] = status
        
        if job_type:
            filters["job_type"] = job_type
        
        return await self.find_many(
            **filters,
            order_by="created_at",
            order_dir="desc"
        )
    
    async def get_active_jobs(self, limit: int = 100) -> List[ProcessingJob]:
        """Get currently active (running) jobs."""
        return await self.find_many(
            status=JobStatus.RUNNING,
            limit=limit,
            order_by="started_at",
            order_dir="asc"
        )
    
    async def get_failed_jobs(
        self,
        limit: int = 100,
        include_exhausted: bool = False
    ) -> List[ProcessingJob]:
        """Get failed jobs."""
        conditions = {"status": JobStatus.FAILED}
        
        if not include_exhausted:
            # Only jobs that can still be retried
            stmt = (
                select(ProcessingJob)
                .where(and_(
                    ProcessingJob.status == JobStatus.FAILED,
                    ProcessingJob.retry_count < ProcessingJob.max_retries
                ))
                .order_by(ProcessingJob.next_retry_at.nulls_last())
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        
        return await self.find_many(
            **conditions,
            limit=limit,
            order_by="completed_at",
            order_dir="desc"
        )
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get processing queue statistics."""
        # Count by status
        status_stmt = (
            select(ProcessingJob.status, func.count(ProcessingJob.id))
            .group_by(ProcessingJob.status)
        )
        status_result = await self.session.execute(status_stmt)
        status_counts = {status: count for status, count in status_result}
        
        # Count by job type
        type_stmt = (
            select(ProcessingJob.job_type, func.count(ProcessingJob.id))
            .group_by(ProcessingJob.job_type)
        )
        type_result = await self.session.execute(type_stmt)
        type_counts = {job_type: count for job_type, count in type_result}
        
        # Average processing time for completed jobs (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        avg_time_stmt = (
            select(func.avg(
                func.extract('epoch', ProcessingJob.completed_at - ProcessingJob.started_at)
            ))
            .where(and_(
                ProcessingJob.status == JobStatus.COMPLETED,
                ProcessingJob.completed_at >= yesterday
            ))
        )
        avg_time_result = await self.session.execute(avg_time_stmt)
        avg_processing_time = avg_time_result.scalar() or 0
        
        # Error rate (last 24 hours)
        total_completed_stmt = (
            select(func.count(ProcessingJob.id))
            .where(and_(
                ProcessingJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED]),
                ProcessingJob.completed_at >= yesterday
            ))
        )
        total_completed_result = await self.session.execute(total_completed_stmt)
        total_completed = total_completed_result.scalar() or 0
        
        failed_count = status_counts.get(JobStatus.FAILED, 0)
        error_rate = (failed_count / total_completed) if total_completed > 0 else 0
        
        return {
            "total_jobs": sum(status_counts.values()),
            "pending_jobs": status_counts.get(JobStatus.PENDING, 0),
            "running_jobs": status_counts.get(JobStatus.RUNNING, 0),
            "completed_jobs": status_counts.get(JobStatus.COMPLETED, 0),
            "failed_jobs": failed_count,
            "cancelled_jobs": status_counts.get(JobStatus.CANCELLED, 0),
            "jobs_by_type": type_counts,
            "average_processing_time": avg_processing_time,
            "error_rate": error_rate
        }
    
    async def cleanup_old_jobs(self, days_old: int = 30) -> int:
        """Clean up old completed/failed jobs."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Only delete terminal state jobs
        deleted_count = 0
        
        # Get old jobs in batches
        while True:
            stmt = (
                select(ProcessingJob.id)
                .where(and_(
                    ProcessingJob.status.in_([
                        JobStatus.COMPLETED, 
                        JobStatus.FAILED, 
                        JobStatus.CANCELLED
                    ]),
                    ProcessingJob.completed_at < cutoff_date
                ))
                .limit(1000)
            )
            result = await self.session.execute(stmt)
            job_ids = [row[0] for row in result]
            
            if not job_ids:
                break
            
            batch_deleted = await self.delete_by_ids(job_ids)
            deleted_count += batch_deleted
            
            if batch_deleted < len(job_ids):
                break
        
        await self.session.commit()
        return deleted_count
    
    async def reset_stuck_jobs(self, timeout_minutes: int = 30) -> List[ProcessingJob]:
        """Reset jobs that have been running too long."""
        timeout_threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        
        stmt = (
            select(ProcessingJob)
            .where(and_(
                ProcessingJob.status == JobStatus.RUNNING,
                ProcessingJob.started_at < timeout_threshold
            ))
        )
        result = await self.session.execute(stmt)
        stuck_jobs = list(result.scalars().all())
        
        for job in stuck_jobs:
            job.status = JobStatus.FAILED
            job.completed_at = func.now()
            job.error_message = f"Job timed out after {timeout_minutes} minutes"
            job.error_details = {"timeout": True, "timeout_minutes": timeout_minutes}
        
        await self.session.flush()
        return stuck_jobs
    
    async def retry_job(self, job_id: UUID) -> Optional[ProcessingJob]:
        """Manually retry a failed job."""
        job = await self.get_by_id(job_id)
        if job and job.status == JobStatus.FAILED and job.can_retry:
            job.reset_for_retry()
            await self.session.flush()
            await self.session.refresh(job)
        return job
    
    async def get_jobs_with_webhooks(self, status: JobStatus) -> List[ProcessingJob]:
        """Get jobs that have webhook URLs and are in a specific status."""
        return await self.find_many(
            status=status,
            webhook_url__not=None,
            order_by="completed_at",
            order_dir="asc"
        )