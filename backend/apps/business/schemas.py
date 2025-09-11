"""
Django Ninja schemas for business models.
Provides request/response schemas for API endpoints.
"""

from ninja import Schema, Field
from pydantic import EmailStr, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
import uuid


# Base schemas for common fields
class TimestampSchema(Schema):
    """Base schema with timestamp fields."""
    created_at: datetime
    updated_at: datetime


class AuditSchema(TimestampSchema):
    """Base schema with full audit fields."""
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    organization_id: Optional[str] = None


# Contact schemas
class ContactCreateSchema(Schema):
    """Schema for creating a new contact."""
    contact_type: str = 'patient'
    title: Optional[str] = None
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    date_of_birth: Optional[date] = None
    
    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = 'France'
    
    # Medical/Business fields
    medical_record_number: Optional[str] = None
    insurance_number: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    
    # Preferences
    preferred_language: str = 'fr'
    communication_preference: str = 'email'
    
    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    
    # Compliance
    consent_given: bool = False
    consent_date: Optional[datetime] = None
    data_retention_until: Optional[date] = None


class ContactUpdateSchema(Schema):
    """Schema for updating a contact."""
    contact_type: Optional[str] = None
    title: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    date_of_birth: Optional[date] = None
    
    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    
    # Medical/Business fields
    medical_record_number: Optional[str] = None
    insurance_number: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    
    # Preferences
    preferred_language: Optional[str] = None
    communication_preference: Optional[str] = None
    
    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    
    # Compliance
    consent_given: Optional[bool] = None
    consent_date: Optional[datetime] = None
    data_retention_until: Optional[date] = None


class ContactResponseSchema(AuditSchema):
    """Schema for contact responses."""
    id: str
    contact_type: str
    title: Optional[str] = None
    first_name: str
    last_name: str
    full_name: str
    display_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    date_of_birth: Optional[date] = None
    
    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    
    # Medical/Business fields
    medical_record_number: Optional[str] = None
    insurance_number: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    
    # Preferences
    preferred_language: str
    communication_preference: str
    
    # Emergency contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    
    # Compliance
    consent_given: bool
    consent_date: Optional[datetime] = None
    data_retention_until: Optional[date] = None
    is_deleted: bool


# Appointment schemas
class AppointmentCreateSchema(Schema):
    """Schema for creating a new appointment."""
    title: str
    description: Optional[str] = None
    contact_id: str
    
    # Scheduling
    start_datetime: datetime
    end_datetime: datetime
    timezone: str = 'Europe/Paris'
    
    # Classification
    appointment_type: str = 'consultation'
    status: str = 'scheduled'
    priority: int = Field(3, ge=1, le=5)
    
    # Assignment
    assigned_provider: Optional[str] = None
    assigned_staff: Optional[str] = None
    
    # Location and resources
    location: Optional[str] = None
    required_equipment: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    
    # Billing
    billing_code: Optional[str] = None
    estimated_cost: Optional[Decimal] = None
    insurance_authorized: bool = False
    
    # Workflow
    preparation_notes: Optional[str] = None
    requires_follow_up: bool = False
    follow_up_date: Optional[date] = None
    
    # Communication
    confirmation_required: bool = True


class AppointmentUpdateSchema(Schema):
    """Schema for updating an appointment."""
    title: Optional[str] = None
    description: Optional[str] = None
    
    # Scheduling
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    timezone: Optional[str] = None
    
    # Classification
    appointment_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    
    # Assignment
    assigned_provider: Optional[str] = None
    assigned_staff: Optional[str] = None
    
    # Location and resources
    location: Optional[str] = None
    required_equipment: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    
    # Billing
    billing_code: Optional[str] = None
    estimated_cost: Optional[Decimal] = None
    insurance_authorized: Optional[bool] = None
    
    # Workflow
    preparation_notes: Optional[str] = None
    post_appointment_notes: Optional[str] = None
    requires_follow_up: Optional[bool] = None
    follow_up_date: Optional[date] = None
    
    # Communication
    reminder_sent: Optional[bool] = None
    confirmation_required: Optional[bool] = None
    confirmed_at: Optional[datetime] = None


class AppointmentResponseSchema(AuditSchema):
    """Schema for appointment responses."""
    id: str
    title: str
    description: Optional[str] = None
    contact: ContactResponseSchema
    
    # Scheduling
    start_datetime: datetime
    end_datetime: datetime
    timezone: str
    
    # Classification
    appointment_type: str
    status: str
    priority: int
    
    # Assignment
    assigned_provider: Optional[str] = None
    assigned_staff: Optional[str] = None
    
    # Location and resources
    location: Optional[str] = None
    required_equipment: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    
    # Billing
    billing_code: Optional[str] = None
    estimated_cost: Optional[Decimal] = None
    insurance_authorized: bool
    
    # Workflow
    preparation_notes: Optional[str] = None
    post_appointment_notes: Optional[str] = None
    requires_follow_up: bool
    follow_up_date: Optional[date] = None
    
    # Communication
    reminder_sent: bool
    confirmation_required: bool
    confirmed_at: Optional[datetime] = None
    is_deleted: bool


# Document schemas
class DocumentCreateSchema(Schema):
    """Schema for creating a new document."""
    title: str
    description: Optional[str] = None
    document_type: str = 'other'
    file_name: str
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    checksum_md5: Optional[str] = None
    
    # Relationships
    related_contact_id: Optional[str] = None
    related_appointment_id: Optional[str] = None
    
    # Classification
    privacy_level: str = 'internal'
    tags: List[str] = Field(default_factory=list)
    
    # Versioning
    version: int = 1
    parent_document_id: Optional[str] = None
    
    # Compliance
    retention_until: Optional[date] = None
    is_encrypted: bool = True
    access_log_required: bool = True
    
    # Approval
    requires_approval: bool = False


class DocumentUpdateSchema(Schema):
    """Schema for updating a document."""
    title: Optional[str] = None
    description: Optional[str] = None
    document_type: Optional[str] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    checksum_md5: Optional[str] = None
    
    # Classification
    privacy_level: Optional[str] = None
    tags: Optional[List[str]] = None
    
    # Compliance
    retention_until: Optional[date] = None
    is_encrypted: Optional[bool] = None
    access_log_required: Optional[bool] = None
    
    # Approval
    requires_approval: Optional[bool] = None
    approved: Optional[bool] = None


class DocumentResponseSchema(AuditSchema):
    """Schema for document responses."""
    id: str
    title: str
    description: Optional[str] = None
    document_type: str
    file_name: str
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    checksum_md5: Optional[str] = None
    
    # Relationships
    related_contact_id: Optional[str] = None
    related_appointment_id: Optional[str] = None
    
    # Classification
    privacy_level: str
    tags: List[str]
    
    # Versioning
    version: int
    parent_document_id: Optional[str] = None
    
    # Compliance
    retention_until: Optional[date] = None
    is_encrypted: bool
    access_log_required: bool
    
    # Approval
    requires_approval: bool
    approved: bool
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    is_deleted: bool


# Transaction schemas
class TransactionCreateSchema(Schema):
    """Schema for creating a new transaction."""
    transaction_id: str
    transaction_type: str
    amount: Decimal
    currency: str = 'EUR'
    tax_amount: Decimal = 0
    contact_id: str
    
    # Optional relationships
    related_appointment_id: Optional[str] = None
    
    # Payment details
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    payment_date: Optional[datetime] = None
    
    # Billing
    invoice_number: Optional[str] = None
    billing_period_start: Optional[date] = None
    billing_period_end: Optional[date] = None
    due_date: Optional[date] = None
    
    # Description
    description: Optional[str] = None
    notes: Optional[str] = None
    
    # Compliance
    requires_receipt: bool = True


class TransactionUpdateSchema(Schema):
    """Schema for updating a transaction."""
    transaction_type: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    tax_amount: Optional[Decimal] = None
    
    # Payment details
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    payment_date: Optional[datetime] = None
    
    # Billing
    invoice_number: Optional[str] = None
    billing_period_start: Optional[date] = None
    billing_period_end: Optional[date] = None
    due_date: Optional[date] = None
    
    # Description
    description: Optional[str] = None
    notes: Optional[str] = None
    
    # Compliance
    requires_receipt: Optional[bool] = None
    receipt_sent: Optional[bool] = None


class TransactionResponseSchema(AuditSchema):
    """Schema for transaction responses."""
    id: str
    transaction_id: str
    transaction_type: str
    status: str
    amount: Decimal
    currency: str
    tax_amount: Decimal
    contact: ContactResponseSchema
    
    # Optional relationships
    related_appointment_id: Optional[str] = None
    
    # Payment details
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    payment_date: Optional[datetime] = None
    
    # Billing
    invoice_number: Optional[str] = None
    billing_period_start: Optional[date] = None
    billing_period_end: Optional[date] = None
    due_date: Optional[date] = None
    
    # Description
    description: Optional[str] = None
    notes: Optional[str] = None
    
    # Compliance
    requires_receipt: bool
    receipt_sent: bool
    is_deleted: bool


# Pagination schema
class PaginatedResponse(Schema):
    """Generic pagination response schema."""
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    page_size: int
    total_pages: int


class PaginatedContactResponse(PaginatedResponse):
    """Paginated contact response."""
    results: List[ContactResponseSchema]


class PaginatedAppointmentResponse(PaginatedResponse):
    """Paginated appointment response."""
    results: List[AppointmentResponseSchema]


class PaginatedDocumentResponse(PaginatedResponse):
    """Paginated document response."""
    results: List[DocumentResponseSchema]


class PaginatedTransactionResponse(PaginatedResponse):
    """Paginated transaction response."""
    results: List[TransactionResponseSchema]


# Response schemas for common operations
class SuccessResponse(Schema):
    """Generic success response."""
    message: str
    success: bool = True


class ErrorResponse(Schema):
    """Generic error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    success: bool = False


class BulkDeleteResponse(Schema):
    """Response for bulk delete operations."""
    deleted_count: int
    message: str
    success: bool = True