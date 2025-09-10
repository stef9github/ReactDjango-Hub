"""
Document repository for advanced document operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from .base import BaseRepository
from models.document import Document, DocumentVersion
from ..schemas.document import DocumentListItem, DocumentStatsResponse


class DocumentRepository(BaseRepository[Document]):
    """Repository for document operations with business logic."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Document)
    
    async def create_document(
        self,
        filename: str,
        original_filename: str,
        content_type: str,
        file_size: int,
        file_hash: str,
        storage_path: str,
        created_by: UUID,
        organization_id: UUID,
        metadata: Dict[str, Any] = None,
        classification: str = "internal"
    ) -> Document:
        """Create a new document with proper initialization."""
        document = await self.create(
            filename=filename,
            original_filename=original_filename,
            content_type=content_type,
            file_size=file_size,
            file_hash=file_hash,
            storage_path=storage_path,
            created_by=created_by,
            organization_id=organization_id,
            metadata=metadata or {},
            classification=classification,
            status="active",
            processing_status="pending"
        )
        
        # Load relationships for the response
        await self.session.refresh(document)
        return document
    
    async def find_by_hash(self, file_hash: str) -> Optional[Document]:
        """Find document by file hash (duplicate detection)."""
        return await self.find_one(file_hash=file_hash)
    
    async def get_by_id_and_organization(self, document_id: UUID, organization_id: UUID) -> Optional[Document]:
        """Get document by ID with organization check for security."""
        stmt = select(Document).where(
            and_(
                Document.id == document_id,
                Document.organization_id == organization_id,
                Document.status == "active"
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_by_organization(
        self,
        organization_id: UUID,
        limit: int = 20,
        offset: int = 0,
        status: str = "active",
        order_by: str = "created_at",
        order_dir: str = "desc"
    ) -> List[Document]:
        """Find documents by organization with filtering."""
        return await self.find_many(
            organization_id=organization_id,
            status=status,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_dir=order_dir
        )
    
    async def search_documents(
        self,
        organization_id: UUID,
        query: str,
        limit: int = 20,
        offset: int = 0,
        document_types: Optional[List[str]] = None,
        classifications: Optional[List[str]] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None
    ) -> Tuple[List[Document], int]:
        """Full-text search documents with filtering."""
        # Build the base query
        stmt = select(Document).where(Document.organization_id == organization_id)
        count_stmt = select(func.count(Document.id)).where(Document.organization_id == organization_id)
        
        # Add text search
        if query.strip():
            search_condition = Document.search_vector.match(query)
            stmt = stmt.where(search_condition)
            count_stmt = count_stmt.where(search_condition)
        
        # Add filters
        filters = []
        
        if document_types:
            filters.append(Document.document_type.in_(document_types))
        
        if classifications:
            filters.append(Document.classification.in_(classifications))
        
        if created_after:
            filters.append(Document.created_at >= created_after)
        
        if created_before:
            filters.append(Document.created_at <= created_before)
        
        if filters:
            combined_filter = and_(*filters)
            stmt = stmt.where(combined_filter)
            count_stmt = count_stmt.where(combined_filter)
        
        # Add ordering and pagination
        if query.strip():
            # Order by relevance when searching
            stmt = stmt.order_by(
                func.ts_rank(Document.search_vector, func.plainto_tsquery(query)).desc(),
                Document.created_at.desc()
            )
        else:
            stmt = stmt.order_by(Document.created_at.desc())
        
        stmt = stmt.offset(offset).limit(limit)
        
        # Execute queries
        result = await self.session.execute(stmt)
        documents = list(result.scalars().all())
        
        count_result = await self.session.execute(count_stmt)
        total_count = count_result.scalar()
        
        return documents, total_count
    
    async def get_document_with_versions(self, document_id: UUID) -> Optional[Document]:
        """Get document with all versions loaded."""
        stmt = (
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.versions))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_document_with_permissions(self, document_id: UUID) -> Optional[Document]:
        """Get document with permissions loaded."""
        stmt = (
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.permissions))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_documents_for_processing(
        self, 
        limit: int = 10,
        processing_type: Optional[str] = None
    ) -> List[Document]:
        """Get documents that need processing."""
        conditions = [Document.processing_status == "pending"]
        
        if processing_type == "ocr":
            conditions.append(Document.ocr_completed == False)
        elif processing_type == "thumbnail":
            conditions.append(Document.thumbnail_generated == False)
        
        stmt = (
            select(Document)
            .where(and_(*conditions))
            .order_by(Document.created_at)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update_processing_status(
        self,
        document_id: UUID,
        processing_status: str,
        ocr_completed: Optional[bool] = None,
        thumbnail_generated: Optional[bool] = None,
        extracted_text: Optional[str] = None
    ) -> Optional[Document]:
        """Update document processing status."""
        update_data = {"processing_status": processing_status}
        
        if ocr_completed is not None:
            update_data["ocr_completed"] = ocr_completed
        
        if thumbnail_generated is not None:
            update_data["thumbnail_generated"] = thumbnail_generated
        
        if extracted_text is not None:
            update_data["extracted_text"] = extracted_text
        
        return await self.update_by_id(document_id, **update_data)
    
    async def mark_as_deleted(self, document_id: UUID) -> Optional[Document]:
        """Soft delete a document."""
        return await self.update_by_id(document_id, status="deleted")
    
    async def get_organization_stats(self, organization_id: UUID) -> Dict[str, Any]:
        """Get document statistics for an organization."""
        # Total documents and size
        total_stmt = (
            select(func.count(Document.id), func.sum(Document.file_size))
            .where(and_(Document.organization_id == organization_id, Document.status == "active"))
        )
        total_result = await self.session.execute(total_stmt)
        total_count, total_size = total_result.one()
        
        # Documents by type
        type_stmt = (
            select(Document.document_type, func.count(Document.id))
            .where(and_(Document.organization_id == organization_id, Document.status == "active"))
            .group_by(Document.document_type)
        )
        type_result = await self.session.execute(type_stmt)
        documents_by_type = {row[0] or "unknown": row[1] for row in type_result}
        
        # Documents by status
        status_stmt = (
            select(Document.status, func.count(Document.id))
            .where(Document.organization_id == organization_id)
            .group_by(Document.status)
        )
        status_result = await self.session.execute(status_stmt)
        documents_by_status = {row[0]: row[1] for row in status_result}
        
        # Processing queue size
        processing_stmt = (
            select(func.count(Document.id))
            .where(and_(
                Document.organization_id == organization_id,
                Document.processing_status.in_(["pending", "processing"])
            ))
        )
        processing_result = await self.session.execute(processing_stmt)
        processing_queue_size = processing_result.scalar()
        
        return {
            "total_documents": total_count or 0,
            "total_size": total_size or 0,
            "documents_by_type": documents_by_type,
            "documents_by_status": documents_by_status,
            "processing_queue_size": processing_queue_size or 0
        }
    
    async def get_recent_documents(
        self,
        organization_id: UUID,
        limit: int = 10
    ) -> List[Document]:
        """Get recently uploaded documents."""
        stmt = (
            select(Document)
            .where(and_(Document.organization_id == organization_id, Document.status == "active"))
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_documents_by_user(
        self,
        user_id: UUID,
        organization_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> List[Document]:
        """Get documents created by a specific user."""
        return await self.find_many(
            created_by=user_id,
            organization_id=organization_id,
            status="active",
            limit=limit,
            offset=offset,
            order_by="created_at",
            order_dir="desc"
        )
    
    async def bulk_update_classification(
        self,
        document_ids: List[UUID],
        classification: str,
        updated_by: UUID
    ) -> List[Document]:
        """Bulk update document classification."""
        documents = await self.get_by_ids(document_ids)
        updated_documents = []
        
        for doc in documents:
            if doc:
                doc.classification = classification
                doc.updated_at = func.now()
                updated_documents.append(doc)
        
        await self.session.flush()
        return updated_documents
    
    async def find_duplicates(self, organization_id: UUID) -> List[Tuple[str, List[Document]]]:
        """Find duplicate documents by hash within an organization."""
        stmt = (
            select(Document.file_hash, func.array_agg(Document.id))
            .where(and_(Document.organization_id == organization_id, Document.status == "active"))
            .group_by(Document.file_hash)
            .having(func.count(Document.id) > 1)
        )
        result = await self.session.execute(stmt)
        
        duplicates = []
        for file_hash, doc_ids in result:
            docs = await self.get_by_ids(doc_ids)
            duplicates.append((file_hash, docs))
        
        return duplicates
    
    async def get_documents_by_classification(
        self,
        organization_id: UUID,
        classification: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Document]:
        """Get documents by security classification."""
        return await self.find_many(
            organization_id=organization_id,
            classification=classification,
            status="active",
            limit=limit,
            offset=offset,
            order_by="created_at",
            order_dir="desc"
        )