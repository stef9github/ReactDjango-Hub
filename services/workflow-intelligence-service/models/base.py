"""
Base model configuration for all database models
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class UUIDMixin:
    """Mixin to add UUID primary key"""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

class UserTrackingMixin:
    """Mixin to track which user created/updated records"""
    created_by = Column(String(255), nullable=True)  # User ID from identity service
    updated_by = Column(String(255), nullable=True)  # User ID from identity service

class OrganizationMixin:
    """Mixin for multi-tenant organization isolation"""
    organization_id = Column(String(255), nullable=False, index=True)  # Organization ID from identity service