"""
Audit repository for tracking document operations and compliance.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from models.audit import DocumentAudit


class AuditRepository(BaseRepository[DocumentAudit]):
    """Repository for audit trail operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentAudit)
    
    async def log_action(
        self,
        action: str,
        user_id: UUID,
        organization_id: UUID,
        document_id: Optional[UUID] = None,
        resource_type: str = "document",
        resource_id: Optional[UUID] = None,
        details: Dict[str, Any] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[UUID] = None,
        execution_time_ms: Optional[int] = None
    ) -> DocumentAudit:
        """Log an audit action."""
        audit_entry = DocumentAudit.create_audit_entry(
            action=action,
            user_id=user_id,
            organization_id=organization_id,
            document_id=document_id,
            resource_type=resource_type,
            resource_id=resource_id or document_id,
            details=details,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            execution_time_ms=execution_time_ms
        )
        
        self.session.add(audit_entry)
        await self.session.flush()
        await self.session.refresh(audit_entry)
        return audit_entry
    
    async def get_document_audit_trail(
        self,
        document_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[DocumentAudit]:
        """Get audit trail for a specific document."""
        return await self.find_many(
            document_id=document_id,
            limit=limit,
            offset=offset,
            order_by="created_at",
            order_dir="desc"
        )
    
    async def get_user_activity(
        self,
        user_id: UUID,
        organization_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DocumentAudit]:
        """Get user activity within a date range."""
        filters = {
            "user_id": user_id,
            "organization_id": organization_id
        }
        
        if start_date:
            filters["created_at__gte"] = start_date
        
        if end_date:
            filters["created_at__lte"] = end_date
        
        return await self.find_many(
            **filters,
            limit=limit,
            offset=offset,
            order_by="created_at",
            order_dir="desc"
        )
    
    async def get_organization_activity(
        self,
        organization_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        actions: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DocumentAudit]:
        """Get organization-wide activity."""
        filters = {"organization_id": organization_id}
        
        if start_date:
            filters["created_at__gte"] = start_date
        
        if end_date:
            filters["created_at__lte"] = end_date
        
        if actions:
            filters["action__in"] = actions
        
        return await self.find_many(
            **filters,
            limit=limit,
            offset=offset,
            order_by="created_at",
            order_dir="desc"
        )
    
    async def get_security_events(
        self,
        organization_id: UUID,
        hours_back: int = 24,
        limit: int = 100
    ) -> List[DocumentAudit]:
        """Get security-related events (access, sharing, etc.)."""
        start_time = datetime.utcnow() - timedelta(hours=hours_back)
        security_actions = ["share", "unshare", "delete", "download"]
        
        return await self.get_organization_activity(
            organization_id=organization_id,
            start_date=start_time,
            actions=security_actions,
            limit=limit
        )
    
    async def get_action_statistics(
        self,
        organization_id: UUID,
        days_back: int = 30
    ) -> Dict[str, int]:
        """Get statistics of actions performed."""
        start_date = datetime.utcnow() - timedelta(days=days_back)
        
        stmt = (
            select(DocumentAudit.action, func.count(DocumentAudit.id))
            .where(and_(
                DocumentAudit.organization_id == organization_id,
                DocumentAudit.created_at >= start_date
            ))
            .group_by(DocumentAudit.action)
        )
        
        result = await self.session.execute(stmt)
        return {action: count for action, count in result}
    
    async def get_user_statistics(
        self,
        organization_id: UUID,
        days_back: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top active users by audit events."""
        start_date = datetime.utcnow() - timedelta(days=days_back)
        
        stmt = (
            select(
                DocumentAudit.user_id,
                func.count(DocumentAudit.id).label("activity_count"),
                func.count(func.distinct(DocumentAudit.document_id)).label("unique_documents")
            )
            .where(and_(
                DocumentAudit.organization_id == organization_id,
                DocumentAudit.created_at >= start_date
            ))
            .group_by(DocumentAudit.user_id)
            .order_by(desc("activity_count"))
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return [
            {
                "user_id": str(user_id),
                "activity_count": activity_count,
                "unique_documents": unique_documents
            }
            for user_id, activity_count, unique_documents in result
        ]
    
    async def get_document_access_log(
        self,
        document_id: UUID,
        limit: int = 50
    ) -> List[DocumentAudit]:
        """Get access log for a specific document."""
        return await self.find_many(
            document_id=document_id,
            action__in=["read", "download"],
            limit=limit,
            order_by="created_at",
            order_dir="desc"
        )
    
    async def check_suspicious_activity(
        self,
        organization_id: UUID,
        hours_back: int = 1
    ) -> Dict[str, Any]:
        """Check for suspicious activity patterns."""
        start_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Multiple failed access attempts from same IP
        failed_access_stmt = (
            select(
                DocumentAudit.ip_address,
                func.count(DocumentAudit.id).label("failure_count")
            )
            .where(and_(
                DocumentAudit.organization_id == organization_id,
                DocumentAudit.created_at >= start_time,
                DocumentAudit.details.contains({"status": "failed"})
            ))
            .group_by(DocumentAudit.ip_address)
            .having(func.count(DocumentAudit.id) > 5)
        )
        failed_access_result = await self.session.execute(failed_access_stmt)
        suspicious_ips = [
            {"ip_address": ip, "failure_count": count}
            for ip, count in failed_access_result
        ]
        
        # Bulk download activity
        bulk_download_stmt = (
            select(
                DocumentAudit.user_id,
                func.count(DocumentAudit.id).label("download_count")
            )
            .where(and_(
                DocumentAudit.organization_id == organization_id,
                DocumentAudit.created_at >= start_time,
                DocumentAudit.action == "download"
            ))
            .group_by(DocumentAudit.user_id)
            .having(func.count(DocumentAudit.id) > 50)
        )
        bulk_download_result = await self.session.execute(bulk_download_stmt)
        bulk_downloaders = [
            {"user_id": str(user_id), "download_count": count}
            for user_id, count in bulk_download_result
        ]
        
        # Unusual after-hours activity
        after_hours_stmt = (
            select(func.count(DocumentAudit.id))
            .where(and_(
                DocumentAudit.organization_id == organization_id,
                DocumentAudit.created_at >= start_time,
                func.extract('hour', DocumentAudit.created_at).between(22, 6)
            ))
        )
        after_hours_result = await self.session.execute(after_hours_stmt)
        after_hours_count = after_hours_result.scalar() or 0
        
        return {
            "suspicious_ips": suspicious_ips,
            "bulk_downloaders": bulk_downloaders,
            "after_hours_activity": after_hours_count,
            "check_timestamp": datetime.utcnow()
        }
    
    async def generate_compliance_report(
        self,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate compliance report for audit purposes."""
        # Total activities
        total_stmt = (
            select(func.count(DocumentAudit.id))
            .where(and_(
                DocumentAudit.organization_id == organization_id,
                DocumentAudit.created_at.between(start_date, end_date)
            ))
        )
        total_result = await self.session.execute(total_stmt)
        total_activities = total_result.scalar() or 0
        
        # Activities by action type
        action_stmt = (
            select(DocumentAudit.action, func.count(DocumentAudit.id))
            .where(and_(
                DocumentAudit.organization_id == organization_id,
                DocumentAudit.created_at.between(start_date, end_date)
            ))
            .group_by(DocumentAudit.action)
        )
        action_result = await self.session.execute(action_stmt)
        activities_by_action = {action: count for action, count in action_result}
        
        # Unique users
        unique_users_stmt = (
            select(func.count(func.distinct(DocumentAudit.user_id)))
            .where(and_(
                DocumentAudit.organization_id == organization_id,
                DocumentAudit.created_at.between(start_date, end_date)
            ))
        )
        unique_users_result = await self.session.execute(unique_users_stmt)
        unique_users = unique_users_result.scalar() or 0
        
        # Documents accessed
        documents_accessed_stmt = (
            select(func.count(func.distinct(DocumentAudit.document_id)))
            .where(and_(
                DocumentAudit.organization_id == organization_id,
                DocumentAudit.created_at.between(start_date, end_date),
                DocumentAudit.document_id.isnot(None)
            ))
        )
        documents_result = await self.session.execute(documents_accessed_stmt)
        documents_accessed = documents_result.scalar() or 0
        
        return {
            "report_period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "total_activities": total_activities,
            "activities_by_action": activities_by_action,
            "unique_users": unique_users,
            "documents_accessed": documents_accessed,
            "generated_at": datetime.utcnow()
        }
    
    async def cleanup_old_audit_logs(self, days_to_keep: int = 365) -> int:
        """Clean up old audit logs (for storage management)."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Delete in batches to avoid long-running transactions
        deleted_count = 0
        batch_size = 10000
        
        while True:
            stmt = (
                select(DocumentAudit.id)
                .where(DocumentAudit.created_at < cutoff_date)
                .limit(batch_size)
            )
            result = await self.session.execute(stmt)
            audit_ids = [row[0] for row in result]
            
            if not audit_ids:
                break
            
            batch_deleted = await self.delete_by_ids(audit_ids)
            deleted_count += batch_deleted
            
            # Commit each batch
            await self.session.commit()
            
            if len(audit_ids) < batch_size:
                break
        
        return deleted_count