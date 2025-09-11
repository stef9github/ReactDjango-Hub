"""
Django Ninja API endpoints for business models.
Provides CRUD operations with pagination, filtering, and sorting.
"""

from ninja import Router, Query, Field
from ninja.pagination import paginate
from typing import List, Optional
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import Http404

from .models import Contact, Appointment, Document, Transaction, AuditLog
from .schemas import (
    # Contact schemas
    ContactCreateSchema, ContactUpdateSchema, ContactResponseSchema,
    PaginatedContactResponse,
    
    # Appointment schemas
    AppointmentCreateSchema, AppointmentUpdateSchema, AppointmentResponseSchema,
    PaginatedAppointmentResponse,
    
    # Document schemas
    DocumentCreateSchema, DocumentUpdateSchema, DocumentResponseSchema,
    PaginatedDocumentResponse,
    
    # Transaction schemas
    TransactionCreateSchema, TransactionUpdateSchema, TransactionResponseSchema,
    PaginatedTransactionResponse,
    
    # Common responses
    SuccessResponse, ErrorResponse, BulkDeleteResponse
)

# Create router
router = Router(tags=["Business"])


# Helper functions
def create_paginated_response(queryset, page: int = 1, page_size: int = 20, response_class=None):
    """Create paginated response with metadata."""
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    return {
        'results': list(page_obj),
        'count': paginator.count,
        'page_size': page_size,
        'total_pages': paginator.num_pages,
        'next': f'?page={page_obj.next_page_number()}' if page_obj.has_next() else None,
        'previous': f'?page={page_obj.previous_page_number()}' if page_obj.has_previous() else None,
    }


def contact_to_schema(contact):
    """Convert Contact model to ContactResponseSchema."""
    return ContactResponseSchema(
        id=str(contact.id),
        contact_type=contact.contact_type,
        title=contact.title,
        first_name=contact.first_name,
        last_name=contact.last_name,
        full_name=contact.full_name,
        display_name=contact.display_name,
        email=contact.email,
        phone=contact.phone,
        mobile=contact.mobile,
        date_of_birth=contact.date_of_birth,
        address_line1=contact.address_line1,
        address_line2=contact.address_line2,
        city=contact.city,
        state=contact.state,
        postal_code=contact.postal_code,
        country=contact.country,
        medical_record_number=contact.medical_record_number,
        insurance_number=contact.insurance_number,
        company=contact.company,
        job_title=contact.job_title,
        preferred_language=contact.preferred_language,
        communication_preference=contact.communication_preference,
        emergency_contact_name=contact.emergency_contact_name,
        emergency_contact_phone=contact.emergency_contact_phone,
        emergency_contact_relationship=contact.emergency_contact_relationship,
        consent_given=contact.consent_given,
        consent_date=contact.consent_date,
        data_retention_until=contact.data_retention_until,
        is_deleted=contact.is_deleted,
        created_at=contact.created_at,
        updated_at=contact.updated_at,
        created_by=str(contact.created_by) if contact.created_by else None,
        updated_by=str(contact.updated_by) if contact.updated_by else None,
        organization_id=str(contact.organization_id) if contact.organization_id else None,
    )


# CONTACT ENDPOINTS

@router.get("/contacts", response=List[ContactResponseSchema], summary="List contacts")
def list_contacts(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    contact_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search in name, email, or medical record number"),
    organization_id: Optional[str] = Query(None)
):
    """
    List contacts with optional filtering and pagination.
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **contact_type**: Filter by contact type (patient, provider, vendor, staff, other)
    - **search**: Search in names, email, or medical record number
    - **organization_id**: Filter by organization (multi-tenant support)
    """
    queryset = Contact.objects.all()
    
    # Apply filters
    if contact_type:
        queryset = queryset.filter(contact_type=contact_type)
    
    if organization_id:
        queryset = queryset.filter(organization_id=organization_id)
    
    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(medical_record_number__icontains=search)
        )
    
    # Order by last name, first name
    queryset = queryset.order_by('last_name', 'first_name')
    
    # Apply pagination
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    # Convert to schema objects
    results = [contact_to_schema(contact) for contact in page_obj]
    return results


@router.get("/contacts/{contact_id}", response=ContactResponseSchema, summary="Get contact")
def get_contact(request, contact_id: str):
    """Get a specific contact by ID."""
    contact = get_object_or_404(Contact, id=contact_id)
    return contact_to_schema(contact)


@router.post("/contacts", response={201: ContactResponseSchema, 400: ErrorResponse}, summary="Create contact")
def create_contact(request, payload: ContactCreateSchema):
    """Create a new contact."""
    try:
        # TODO: Get current user from Identity Service middleware
        contact = Contact.objects.create(**payload.dict())
        return 201, contact_to_schema(contact)
    except Exception as e:
        return 400, ErrorResponse(error=str(e), code="VALIDATION_ERROR")


@router.put("/contacts/{contact_id}", response={200: ContactResponseSchema, 400: ErrorResponse, 404: ErrorResponse}, summary="Update contact")
def update_contact(request, contact_id: str, payload: ContactUpdateSchema):
    """Update an existing contact."""
    try:
        contact = get_object_or_404(Contact, id=contact_id)
        
        # Update only provided fields
        for field, value in payload.dict(exclude_unset=True).items():
            setattr(contact, field, value)
        
        # TODO: Set updated_by from Identity Service middleware
        contact.save()
        
        return 200, contact_to_schema(contact)
    except Contact.DoesNotExist:
        return 404, ErrorResponse(error="Contact not found", code="NOT_FOUND")
    except Exception as e:
        return 400, ErrorResponse(error=str(e), code="VALIDATION_ERROR")


@router.delete("/contacts/{contact_id}", response={200: SuccessResponse, 404: ErrorResponse}, summary="Delete contact")
def delete_contact(request, contact_id: str):
    """Soft delete a contact."""
    try:
        contact = get_object_or_404(Contact, id=contact_id)
        # TODO: Get current user ID from Identity Service middleware
        contact.soft_delete()  # Using soft delete from BaseModel
        return 200, SuccessResponse(message="Contact deleted successfully")
    except Contact.DoesNotExist:
        return 404, ErrorResponse(error="Contact not found", code="NOT_FOUND")


# APPOINTMENT ENDPOINTS

@router.get("/appointments", response=List[dict], summary="List appointments")
def list_appointments(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    contact_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    appointment_type: Optional[str] = Query(None),
    assigned_provider: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None)
):
    """
    List appointments with optional filtering and pagination.
    """
    queryset = Appointment.objects.select_related('contact').all()
    
    # Apply filters
    if contact_id:
        queryset = queryset.filter(contact_id=contact_id)
    if status:
        queryset = queryset.filter(status=status)
    if appointment_type:
        queryset = queryset.filter(appointment_type=appointment_type)
    if assigned_provider:
        queryset = queryset.filter(assigned_provider=assigned_provider)
    if organization_id:
        queryset = queryset.filter(organization_id=organization_id)
    
    # Order by start datetime
    queryset = queryset.order_by('start_datetime')
    
    # Apply pagination
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    # Convert to response format
    results = []
    for appointment in page_obj:
        results.append({
            'id': str(appointment.id),
            'title': appointment.title,
            'description': appointment.description,
            'contact': contact_to_schema(appointment.contact).dict(),
            'start_datetime': appointment.start_datetime,
            'end_datetime': appointment.end_datetime,
            'timezone': appointment.timezone,
            'appointment_type': appointment.appointment_type,
            'status': appointment.status,
            'priority': appointment.priority,
            'assigned_provider': str(appointment.assigned_provider) if appointment.assigned_provider else None,
            'assigned_staff': str(appointment.assigned_staff) if appointment.assigned_staff else None,
            'location': appointment.location,
            'required_equipment': appointment.required_equipment,
            'estimated_duration_minutes': appointment.estimated_duration_minutes,
            'billing_code': appointment.billing_code,
            'estimated_cost': float(appointment.estimated_cost) if appointment.estimated_cost else None,
            'insurance_authorized': appointment.insurance_authorized,
            'preparation_notes': appointment.preparation_notes,
            'post_appointment_notes': appointment.post_appointment_notes,
            'requires_follow_up': appointment.requires_follow_up,
            'follow_up_date': appointment.follow_up_date,
            'reminder_sent': appointment.reminder_sent,
            'confirmation_required': appointment.confirmation_required,
            'confirmed_at': appointment.confirmed_at,
            'is_deleted': appointment.is_deleted,
            'created_at': appointment.created_at,
            'updated_at': appointment.updated_at,
            'created_by': str(appointment.created_by) if appointment.created_by else None,
            'updated_by': str(appointment.updated_by) if appointment.updated_by else None,
            'organization_id': str(appointment.organization_id) if appointment.organization_id else None,
        })
    
    return results


@router.get("/appointments/{appointment_id}", response=dict, summary="Get appointment")
def get_appointment(request, appointment_id: str):
    """Get a specific appointment by ID."""
    appointment = get_object_or_404(Appointment.objects.select_related('contact'), id=appointment_id)
    
    return {
        'id': str(appointment.id),
        'title': appointment.title,
        'description': appointment.description,
        'contact': contact_to_schema(appointment.contact).dict(),
        'start_datetime': appointment.start_datetime,
        'end_datetime': appointment.end_datetime,
        'timezone': appointment.timezone,
        'appointment_type': appointment.appointment_type,
        'status': appointment.status,
        'priority': appointment.priority,
        'assigned_provider': str(appointment.assigned_provider) if appointment.assigned_provider else None,
        'assigned_staff': str(appointment.assigned_staff) if appointment.assigned_staff else None,
        'location': appointment.location,
        'required_equipment': appointment.required_equipment,
        'estimated_duration_minutes': appointment.estimated_duration_minutes,
        'billing_code': appointment.billing_code,
        'estimated_cost': float(appointment.estimated_cost) if appointment.estimated_cost else None,
        'insurance_authorized': appointment.insurance_authorized,
        'preparation_notes': appointment.preparation_notes,
        'post_appointment_notes': appointment.post_appointment_notes,
        'requires_follow_up': appointment.requires_follow_up,
        'follow_up_date': appointment.follow_up_date,
        'reminder_sent': appointment.reminder_sent,
        'confirmation_required': appointment.confirmation_required,
        'confirmed_at': appointment.confirmed_at,
        'is_deleted': appointment.is_deleted,
        'created_at': appointment.created_at,
        'updated_at': appointment.updated_at,
        'created_by': str(appointment.created_by) if appointment.created_by else None,
        'updated_by': str(appointment.updated_by) if appointment.updated_by else None,
        'organization_id': str(appointment.organization_id) if appointment.organization_id else None,
    }


@router.post("/appointments", response={201: dict, 400: ErrorResponse}, summary="Create appointment")
def create_appointment(request, payload: AppointmentCreateSchema):
    """Create a new appointment."""
    try:
        contact = get_object_or_404(Contact, id=payload.contact_id)
        
        appointment_data = payload.dict()
        appointment_data['contact'] = contact
        del appointment_data['contact_id']
        
        appointment = Appointment.objects.create(**appointment_data)
        
        return 201, {
            'id': str(appointment.id),
            'title': appointment.title,
            'description': appointment.description,
            'contact': contact_to_schema(appointment.contact).dict(),
            'start_datetime': appointment.start_datetime,
            'end_datetime': appointment.end_datetime,
            'appointment_type': appointment.appointment_type,
            'status': appointment.status,
            'created_at': appointment.created_at,
        }
    except Contact.DoesNotExist:
        return 400, ErrorResponse(error="Contact not found", code="CONTACT_NOT_FOUND")
    except Exception as e:
        return 400, ErrorResponse(error=str(e), code="VALIDATION_ERROR")


@router.put("/appointments/{appointment_id}", response={200: dict, 400: ErrorResponse, 404: ErrorResponse}, summary="Update appointment")
def update_appointment(request, appointment_id: str, payload: AppointmentUpdateSchema):
    """Update an existing appointment."""
    try:
        appointment = get_object_or_404(Appointment.objects.select_related('contact'), id=appointment_id)
        
        # Update only provided fields
        for field, value in payload.dict(exclude_unset=True).items():
            setattr(appointment, field, value)
        
        appointment.save()
        
        return 200, {
            'id': str(appointment.id),
            'title': appointment.title,
            'status': appointment.status,
            'updated_at': appointment.updated_at,
        }
    except Appointment.DoesNotExist:
        return 404, ErrorResponse(error="Appointment not found", code="NOT_FOUND")
    except Exception as e:
        return 400, ErrorResponse(error=str(e), code="VALIDATION_ERROR")


@router.delete("/appointments/{appointment_id}", response={200: SuccessResponse, 404: ErrorResponse}, summary="Delete appointment")
def delete_appointment(request, appointment_id: str):
    """Soft delete an appointment."""
    try:
        appointment = get_object_or_404(Appointment, id=appointment_id)
        appointment.soft_delete()
        return 200, SuccessResponse(message="Appointment deleted successfully")
    except Appointment.DoesNotExist:
        return 404, ErrorResponse(error="Appointment not found", code="NOT_FOUND")


# DOCUMENT ENDPOINTS

@router.get("/documents", response=List[dict], summary="List documents")
def list_documents(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    document_type: Optional[str] = Query(None),
    related_contact_id: Optional[str] = Query(None),
    privacy_level: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None)
):
    """List documents with optional filtering and pagination."""
    queryset = Document.objects.all()
    
    # Apply filters
    if document_type:
        queryset = queryset.filter(document_type=document_type)
    if related_contact_id:
        queryset = queryset.filter(related_contact_id=related_contact_id)
    if privacy_level:
        queryset = queryset.filter(privacy_level=privacy_level)
    if organization_id:
        queryset = queryset.filter(organization_id=organization_id)
    
    # Order by creation date
    queryset = queryset.order_by('-created_at')
    
    # Apply pagination
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    # Convert to response format
    results = []
    for document in page_obj:
        results.append({
            'id': str(document.id),
            'title': document.title,
            'document_type': document.document_type,
            'file_name': document.file_name,
            'file_size_bytes': document.file_size_bytes,
            'mime_type': document.mime_type,
            'privacy_level': document.privacy_level,
            'version': document.version,
            'is_encrypted': document.is_encrypted,
            'requires_approval': document.requires_approval,
            'approved': document.approved,
            'created_at': document.created_at,
            'created_by': str(document.created_by) if document.created_by else None,
        })
    
    return results


@router.post("/documents", response={201: dict, 400: ErrorResponse}, summary="Create document")
def create_document(request, payload: DocumentCreateSchema):
    """Create a new document."""
    try:
        document_data = payload.dict()
        
        # Handle foreign key relationships
        if document_data.get('related_contact_id'):
            contact = get_object_or_404(Contact, id=document_data['related_contact_id'])
            document_data['related_contact'] = contact
            del document_data['related_contact_id']
        
        if document_data.get('related_appointment_id'):
            appointment = get_object_or_404(Appointment, id=document_data['related_appointment_id'])
            document_data['related_appointment'] = appointment
            del document_data['related_appointment_id']
        
        if document_data.get('parent_document_id'):
            parent = get_object_or_404(Document, id=document_data['parent_document_id'])
            document_data['parent_document'] = parent
            del document_data['parent_document_id']
        
        document = Document.objects.create(**document_data)
        
        return 201, {
            'id': str(document.id),
            'title': document.title,
            'document_type': document.document_type,
            'file_name': document.file_name,
            'created_at': document.created_at,
        }
    except (Contact.DoesNotExist, Appointment.DoesNotExist, Document.DoesNotExist) as e:
        return 400, ErrorResponse(error="Related object not found", code="RELATED_OBJECT_NOT_FOUND")
    except Exception as e:
        return 400, ErrorResponse(error=str(e), code="VALIDATION_ERROR")


# TRANSACTION ENDPOINTS

@router.get("/transactions", response=List[dict], summary="List transactions")
def list_transactions(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    contact_id: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None)
):
    """List transactions with optional filtering and pagination."""
    queryset = Transaction.objects.select_related('contact').all()
    
    # Apply filters
    if contact_id:
        queryset = queryset.filter(contact_id=contact_id)
    if transaction_type:
        queryset = queryset.filter(transaction_type=transaction_type)
    if status:
        queryset = queryset.filter(status=status)
    if organization_id:
        queryset = queryset.filter(organization_id=organization_id)
    
    # Order by creation date (newest first)
    queryset = queryset.order_by('-created_at')
    
    # Apply pagination
    from django.core.paginator import Paginator
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    # Convert to response format
    results = []
    for transaction in page_obj:
        results.append({
            'id': str(transaction.id),
            'transaction_id': transaction.transaction_id,
            'transaction_type': transaction.transaction_type,
            'status': transaction.status,
            'amount': float(transaction.amount),
            'currency': transaction.currency,
            'contact': contact_to_schema(transaction.contact).dict(),
            'payment_method': transaction.payment_method,
            'payment_date': transaction.payment_date,
            'invoice_number': transaction.invoice_number,
            'description': transaction.description,
            'created_at': transaction.created_at,
        })
    
    return results


@router.post("/transactions", response={201: dict, 400: ErrorResponse}, summary="Create transaction")
def create_transaction(request, payload: TransactionCreateSchema):
    """Create a new transaction."""
    try:
        contact = get_object_or_404(Contact, id=payload.contact_id)
        
        transaction_data = payload.dict()
        transaction_data['contact'] = contact
        del transaction_data['contact_id']
        
        if transaction_data.get('related_appointment_id'):
            appointment = get_object_or_404(Appointment, id=transaction_data['related_appointment_id'])
            transaction_data['related_appointment'] = appointment
            del transaction_data['related_appointment_id']
        
        transaction = Transaction.objects.create(**transaction_data)
        
        return 201, {
            'id': str(transaction.id),
            'transaction_id': transaction.transaction_id,
            'transaction_type': transaction.transaction_type,
            'amount': float(transaction.amount),
            'currency': transaction.currency,
            'contact': contact_to_schema(transaction.contact).dict(),
            'created_at': transaction.created_at,
        }
    except Contact.DoesNotExist:
        return 400, ErrorResponse(error="Contact not found", code="CONTACT_NOT_FOUND")
    except Appointment.DoesNotExist:
        return 400, ErrorResponse(error="Appointment not found", code="APPOINTMENT_NOT_FOUND")
    except Exception as e:
        return 400, ErrorResponse(error=str(e), code="VALIDATION_ERROR")


# BULK OPERATIONS

@router.delete("/contacts/bulk", response=BulkDeleteResponse, summary="Bulk delete contacts")
def bulk_delete_contacts(request, contact_ids: List[str]):
    """Bulk soft delete multiple contacts."""
    contacts = Contact.objects.filter(id__in=contact_ids)
    count = contacts.count()
    
    for contact in contacts:
        contact.soft_delete()
    
    return BulkDeleteResponse(
        deleted_count=count,
        message=f"Successfully deleted {count} contacts"
    )