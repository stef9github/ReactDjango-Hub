"""
Base repository class with common database operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Union
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import Select

from database.connection import Base

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T], ABC):
    """Base repository with common CRUD operations."""
    
    def __init__(self, session: AsyncSession, model_class: Type[T]):
        self.session = session
        self.model_class = model_class
    
    async def create(self, **kwargs) -> T:
        """Create a new entity."""
        entity = self.model_class(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get entity by ID."""
        stmt = select(self.model_class).where(self.model_class.id == entity_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_ids(self, entity_ids: List[UUID]) -> List[T]:
        """Get multiple entities by IDs."""
        stmt = select(self.model_class).where(self.model_class.id.in_(entity_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update_by_id(self, entity_id: UUID, **kwargs) -> Optional[T]:
        """Update entity by ID."""
        stmt = (
            update(self.model_class)
            .where(self.model_class.id == entity_id)
            .values(**kwargs)
            .returning(self.model_class)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def delete_by_id(self, entity_id: UUID) -> bool:
        """Delete entity by ID."""
        stmt = delete(self.model_class).where(self.model_class.id == entity_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0
    
    async def delete_by_ids(self, entity_ids: List[UUID]) -> int:
        """Delete multiple entities by IDs."""
        stmt = delete(self.model_class).where(self.model_class.id.in_(entity_ids))
        result = await self.session.execute(stmt)
        return result.rowcount
    
    async def exists(self, entity_id: UUID) -> bool:
        """Check if entity exists."""
        stmt = select(func.count()).where(self.model_class.id == entity_id)
        result = await self.session.execute(stmt)
        count = result.scalar()
        return count > 0
    
    async def count(self, **filters) -> int:
        """Count entities with optional filters."""
        stmt = select(func.count())
        stmt = self._apply_filters(stmt, **filters)
        result = await self.session.execute(stmt)
        return result.scalar()
    
    async def list_all(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: Optional[str] = None,
        order_dir: str = "asc",
        **filters
    ) -> List[T]:
        """List entities with pagination and filtering."""
        stmt = select(self.model_class)
        stmt = self._apply_filters(stmt, **filters)
        stmt = self._apply_ordering(stmt, order_by, order_dir)
        stmt = self._apply_pagination(stmt, limit, offset)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def find_one(self, **filters) -> Optional[T]:
        """Find single entity by filters."""
        stmt = select(self.model_class)
        stmt = self._apply_filters(stmt, **filters)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def find_many(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: Optional[str] = None,
        order_dir: str = "asc",
        **filters
    ) -> List[T]:
        """Find multiple entities by filters."""
        return await self.list_all(limit, offset, order_by, order_dir, **filters)
    
    def _apply_filters(self, stmt: Select, **filters) -> Select:
        """Apply filters to the query."""
        conditions = []
        
        for key, value in filters.items():
            if value is None:
                continue
                
            # Handle special filter operators
            if key.endswith("__in") and isinstance(value, (list, tuple)):
                field_name = key[:-4]
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    conditions.append(field.in_(value))
            
            elif key.endswith("__gt"):
                field_name = key[:-4]
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    conditions.append(field > value)
            
            elif key.endswith("__gte"):
                field_name = key[:-5]
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    conditions.append(field >= value)
            
            elif key.endswith("__lt"):
                field_name = key[:-4]
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    conditions.append(field < value)
            
            elif key.endswith("__lte"):
                field_name = key[:-5]
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    conditions.append(field <= value)
            
            elif key.endswith("__like"):
                field_name = key[:-6]
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    conditions.append(field.like(value))
            
            elif key.endswith("__ilike"):
                field_name = key[:-7]
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    conditions.append(field.ilike(value))
            
            elif key.endswith("__not"):
                field_name = key[:-5]
                if hasattr(self.model_class, field_name):
                    field = getattr(self.model_class, field_name)
                    conditions.append(field != value)
            
            # Handle direct field matches
            elif hasattr(self.model_class, key):
                field = getattr(self.model_class, key)
                conditions.append(field == value)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        return stmt
    
    def _apply_ordering(
        self, 
        stmt: Select, 
        order_by: Optional[str], 
        order_dir: str
    ) -> Select:
        """Apply ordering to the query."""
        if order_by and hasattr(self.model_class, order_by):
            field = getattr(self.model_class, order_by)
            if order_dir.lower() == "desc":
                stmt = stmt.order_by(desc(field))
            else:
                stmt = stmt.order_by(asc(field))
        elif hasattr(self.model_class, 'created_at'):
            # Default ordering by created_at desc
            stmt = stmt.order_by(desc(self.model_class.created_at))
        
        return stmt
    
    def _apply_pagination(
        self, 
        stmt: Select, 
        limit: Optional[int], 
        offset: int
    ) -> Select:
        """Apply pagination to the query."""
        if offset > 0:
            stmt = stmt.offset(offset)
        if limit is not None and limit > 0:
            stmt = stmt.limit(limit)
        return stmt
    
    async def bulk_create(self, entities_data: List[Dict[str, Any]]) -> List[T]:
        """Create multiple entities in bulk."""
        entities = [self.model_class(**data) for data in entities_data]
        self.session.add_all(entities)
        await self.session.flush()
        
        # Refresh all entities to get IDs
        for entity in entities:
            await self.session.refresh(entity)
        
        return entities
    
    async def bulk_update(
        self, 
        updates: List[Dict[str, Any]], 
        key_field: str = "id"
    ) -> List[T]:
        """Update multiple entities in bulk."""
        updated_entities = []
        
        for update_data in updates:
            key_value = update_data.pop(key_field)
            entity = await self.update_by_id(key_value, **update_data)
            if entity:
                updated_entities.append(entity)
        
        return updated_entities
    
    async def get_or_create(
        self, 
        defaults: Optional[Dict[str, Any]] = None, 
        **kwargs
    ) -> tuple[T, bool]:
        """Get existing entity or create a new one."""
        entity = await self.find_one(**kwargs)
        
        if entity:
            return entity, False
        
        create_data = kwargs.copy()
        if defaults:
            create_data.update(defaults)
        
        entity = await self.create(**create_data)
        return entity, True
    
    async def update_or_create(
        self, 
        defaults: Optional[Dict[str, Any]] = None, 
        **kwargs
    ) -> tuple[T, bool]:
        """Update existing entity or create a new one."""
        entity = await self.find_one(**kwargs)
        
        if entity:
            if defaults:
                for key, value in defaults.items():
                    setattr(entity, key, value)
                await self.session.flush()
                await self.session.refresh(entity)
            return entity, False
        
        create_data = kwargs.copy()
        if defaults:
            create_data.update(defaults)
        
        entity = await self.create(**create_data)
        return entity, True