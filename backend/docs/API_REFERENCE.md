# Django Backend API Reference

## Overview

This document provides comprehensive API reference for the ReactDjango Hub Django backend service. All endpoints require JWT authentication via the Identity Service unless otherwise specified.

**Base URL**: `http://localhost:8000/api`
**Documentation**: `http://localhost:8000/api/docs`
**OpenAPI Schema**: `http://localhost:8000/api/openapi.json`

---

## Authentication

### JWT Authentication
All protected endpoints require a valid JWT token obtained from the Identity Service (port 8001).

**Header Format**:
```
Authorization: Bearer <jwt_token>
```

**Authentication Flow**:
1. Obtain JWT token from Identity Service: `POST http://localhost:8001/auth/login`
2. Include token in all API requests to Django backend
3. Middleware validates token with Identity Service and extracts user context
4. User context includes: `user_id`, `email`, `organization_id`, `roles`

**Authentication Errors**:
- `401 Unauthorized`: Missing, invalid, or expired token
- `403 Forbidden`: Insufficient permissions for requested resource

---

## System Endpoints

### Health Check
**Endpoint**: `GET /health`
**Authentication**: Not required
**Description**: Service health check

**Response**:
```json
{
  "status": "healthy",
  "service": "django-backend"
}
```

---

## Business Logic API

All business endpoints are prefixed with `/business/` and require authentication.

### Common Response Formats

**Success Response Schema**:
```json
{
  "message": "string"
}
```

**Error Response Schema**:
```json
{
  "error": "string",
  "code": "string"
}
```

**Bulk Delete Response Schema**:
```json
{
  "deleted_count": 0,
  "message": "string"
}
```

---

## Contact Management API

### List Contacts
**Endpoint**: `GET /business/contacts`
**Authentication**: Required
**Description**: Retrieve paginated list of contacts with optional filtering

**Query Parameters**:
- `page` (integer, optional): Page number (default: 1, min: 1)
- `page_size` (integer, optional): Items per page (default: 20, min: 1, max: 100)
- `contact_type` (string, optional): Filter by type (`patient`, `provider`, `vendor`, `staff`, `other`)
- `search` (string, optional): Search in name, email, or medical record number
- `organization_id` (string, optional): Filter by organization (UUID)

**Response**: Array of Contact objects
```json
[
  {
    "id": "uuid",
    "contact_type": "patient",
    "title": "Dr.",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "display_name": "Dr. John Doe",
    "email": "john.doe@example.com",
    "phone": "+33123456789",
    "mobile": "+33987654321",
    "date_of_birth": "1980-01-01",
    "address_line1": "123 Main St",
    "address_line2": "Apt 4B",
    "city": "Paris",
    "state": "Île-de-France",
    "postal_code": "75001",
    "country": "France",
    "medical_record_number": "MRN123456",
    "insurance_number": "INS789012",
    "company": "Health Corp",
    "job_title": "Manager",
    "preferred_language": "fr",
    "communication_preference": "email",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+33555666777",
    "emergency_contact_relationship": "spouse",
    "consent_given": true,
    "consent_date": "2024-01-01T10:00:00Z",
    "data_retention_until": "2030-01-01",
    "is_deleted": false,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z",
    "created_by": "uuid",
    "updated_by": "uuid",
    "organization_id": "uuid"
  }
]
```

### Get Contact
**Endpoint**: `GET /business/contacts/{contact_id}`
**Authentication**: Required
**Description**: Retrieve a specific contact by ID

**Path Parameters**:
- `contact_id` (string, required): Contact UUID

**Response**: Contact object (same schema as list response)

### Create Contact
**Endpoint**: `POST /business/contacts`
**Authentication**: Required
**Description**: Create a new contact

**Request Body**:
```json
{
  "contact_type": "patient",
  "title": "Dr.",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+33123456789",
  "mobile": "+33987654321",
  "date_of_birth": "1980-01-01",
  "address_line1": "123 Main St",
  "city": "Paris",
  "postal_code": "75001",
  "country": "France",
  "preferred_language": "fr",
  "consent_given": true
}
```

**Response**: `201 Created` with Contact object

### Update Contact
**Endpoint**: `PUT /business/contacts/{contact_id}`
**Authentication**: Required
**Description**: Update an existing contact

**Path Parameters**:
- `contact_id` (string, required): Contact UUID

**Request Body**: Partial Contact object (only fields to update)

**Response**: `200 OK` with updated Contact object

### Delete Contact
**Endpoint**: `DELETE /business/contacts/{contact_id}`
**Authentication**: Required
**Description**: Soft delete a contact (sets is_deleted=true)

**Path Parameters**:
- `contact_id` (string, required): Contact UUID

**Response**: `200 OK` with success message

### Bulk Delete Contacts
**Endpoint**: `DELETE /business/contacts/bulk`
**Authentication**: Required
**Description**: Soft delete multiple contacts

**Request Body**:
```json
["uuid1", "uuid2", "uuid3"]
```

**Response**: Bulk delete response with count

---

## Appointment Management API

### List Appointments
**Endpoint**: `GET /business/appointments`
**Authentication**: Required
**Description**: Retrieve paginated list of appointments with optional filtering

**Query Parameters**:
- `page` (integer, optional): Page number (default: 1, min: 1)
- `page_size` (integer, optional): Items per page (default: 20, min: 1, max: 100)
- `contact_id` (string, optional): Filter by contact UUID
- `status` (string, optional): Filter by status (`scheduled`, `confirmed`, `in_progress`, `completed`, `cancelled`, `no_show`, `rescheduled`)
- `appointment_type` (string, optional): Filter by type (`consultation`, `follow_up`, `procedure`, `surgery`, `meeting`, `other`)
- `assigned_provider` (string, optional): Filter by provider UUID
- `organization_id` (string, optional): Filter by organization UUID

**Response**: Array of Appointment objects
```json
[
  {
    "id": "uuid",
    "title": "Annual Checkup",
    "description": "Annual health checkup",
    "contact": { /* Contact object */ },
    "start_datetime": "2024-01-15T14:00:00Z",
    "end_datetime": "2024-01-15T15:00:00Z",
    "timezone": "Europe/Paris",
    "appointment_type": "consultation",
    "status": "scheduled",
    "priority": 3,
    "assigned_provider": "uuid",
    "assigned_staff": "uuid",
    "location": "Room 101",
    "required_equipment": "Stethoscope, Blood pressure monitor",
    "estimated_duration_minutes": 60,
    "billing_code": "99213",
    "estimated_cost": 150.00,
    "insurance_authorized": true,
    "preparation_notes": "Patient should fast for 8 hours",
    "post_appointment_notes": "Follow up in 6 months",
    "requires_follow_up": true,
    "follow_up_date": "2024-07-15",
    "reminder_sent": false,
    "confirmation_required": true,
    "confirmed_at": null,
    "is_deleted": false,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z",
    "created_by": "uuid",
    "updated_by": "uuid",
    "organization_id": "uuid"
  }
]
```

### Get Appointment
**Endpoint**: `GET /business/appointments/{appointment_id}`
**Authentication**: Required
**Description**: Retrieve a specific appointment by ID

**Path Parameters**:
- `appointment_id` (string, required): Appointment UUID

**Response**: Appointment object

### Create Appointment
**Endpoint**: `POST /business/appointments`
**Authentication**: Required
**Description**: Create a new appointment

**Request Body**:
```json
{
  "title": "Annual Checkup",
  "description": "Annual health checkup",
  "contact_id": "uuid",
  "start_datetime": "2024-01-15T14:00:00Z",
  "end_datetime": "2024-01-15T15:00:00Z",
  "appointment_type": "consultation",
  "status": "scheduled",
  "priority": 3,
  "location": "Room 101"
}
```

**Response**: `201 Created` with Appointment object

### Update Appointment
**Endpoint**: `PUT /business/appointments/{appointment_id}`
**Authentication**: Required
**Description**: Update an existing appointment

**Path Parameters**:
- `appointment_id` (string, required): Appointment UUID

**Request Body**: Partial Appointment object

**Response**: `200 OK` with updated appointment summary

### Delete Appointment
**Endpoint**: `DELETE /business/appointments/{appointment_id}`
**Authentication**: Required
**Description**: Soft delete an appointment

**Path Parameters**:
- `appointment_id` (string, required): Appointment UUID

**Response**: `200 OK` with success message

---

## Document Management API

### List Documents
**Endpoint**: `GET /business/documents`
**Authentication**: Required
**Description**: Retrieve paginated list of documents with optional filtering

**Query Parameters**:
- `page` (integer, optional): Page number (default: 1, min: 1)
- `page_size` (integer, optional): Items per page (default: 20, min: 1, max: 100)
- `document_type` (string, optional): Filter by type (`medical_record`, `lab_result`, `imaging`, `prescription`, `invoice`, `contract`, `report`, `consent_form`, `insurance`, `other`)
- `related_contact_id` (string, optional): Filter by related contact UUID
- `privacy_level` (string, optional): Filter by privacy level (`public`, `internal`, `confidential`, `restricted`)
- `organization_id` (string, optional): Filter by organization UUID

**Response**: Array of Document objects
```json
[
  {
    "id": "uuid",
    "title": "Lab Results - Blood Work",
    "document_type": "lab_result",
    "file_name": "blood_work_2024_01_15.pdf",
    "file_size_bytes": 245760,
    "mime_type": "application/pdf",
    "privacy_level": "confidential",
    "version": 1,
    "is_encrypted": true,
    "requires_approval": false,
    "approved": true,
    "created_at": "2024-01-15T10:00:00Z",
    "created_by": "uuid"
  }
]
```

### Create Document
**Endpoint**: `POST /business/documents`
**Authentication**: Required
**Description**: Create a new document record

**Request Body**:
```json
{
  "title": "Lab Results - Blood Work",
  "document_type": "lab_result",
  "file_name": "blood_work_2024_01_15.pdf",
  "file_size_bytes": 245760,
  "mime_type": "application/pdf",
  "privacy_level": "confidential",
  "related_contact_id": "uuid",
  "is_encrypted": true
}
```

**Response**: `201 Created` with Document object summary

---

## Transaction Management API

### List Transactions
**Endpoint**: `GET /business/transactions`
**Authentication**: Required
**Description**: Retrieve paginated list of transactions with optional filtering

**Query Parameters**:
- `page` (integer, optional): Page number (default: 1, min: 1)
- `page_size` (integer, optional): Items per page (default: 20, min: 1, max: 100)
- `contact_id` (string, optional): Filter by contact UUID
- `transaction_type` (string, optional): Filter by type (`payment`, `charge`, `refund`, `adjustment`, `fee`, `subscription`)
- `status` (string, optional): Filter by status (`pending`, `processing`, `completed`, `failed`, `cancelled`, `refunded`)
- `organization_id` (string, optional): Filter by organization UUID

**Response**: Array of Transaction objects
```json
[
  {
    "id": "uuid",
    "transaction_id": "TXN123456789",
    "transaction_type": "payment",
    "status": "completed",
    "amount": 150.00,
    "currency": "EUR",
    "contact": { /* Contact object */ },
    "payment_method": "card",
    "payment_date": "2024-01-15T14:30:00Z",
    "invoice_number": "INV-2024-001",
    "description": "Payment for consultation",
    "created_at": "2024-01-15T14:00:00Z"
  }
]
```

### Create Transaction
**Endpoint**: `POST /business/transactions`
**Authentication**: Required
**Description**: Create a new transaction

**Request Body**:
```json
{
  "transaction_id": "TXN123456789",
  "transaction_type": "payment",
  "amount": 150.00,
  "currency": "EUR",
  "contact_id": "uuid",
  "payment_method": "card",
  "description": "Payment for consultation"
}
```

**Response**: `201 Created` with Transaction object

---

## Analytics API

### List Analytics Records
**Endpoint**: `GET /analytics/records`
**Authentication**: Required
**Description**: Retrieve analytics records for the authenticated user's organization

**Response**: Array of Analytics Record objects

### Get Analytics Record
**Endpoint**: `GET /analytics/records/{record_id}`
**Authentication**: Required
**Description**: Retrieve a specific analytics record

**Path Parameters**:
- `record_id` (string, required): Record UUID

### Create Analytics Record
**Endpoint**: `POST /analytics/records`
**Authentication**: Required
**Description**: Create a new analytics record

### Update Analytics Record
**Endpoint**: `PUT /analytics/records/{record_id}`
**Authentication**: Required
**Description**: Update an existing analytics record

### Delete Analytics Record
**Endpoint**: `DELETE /analytics/records/{record_id}`
**Authentication**: Required
**Description**: Soft delete an analytics record

---

## Error Handling

### Common HTTP Status Codes

- `200 OK`: Successful GET, PUT, DELETE operations
- `201 Created`: Successful POST operations
- `400 Bad Request`: Validation errors, malformed requests
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side errors

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE_CONSTANT"
}
```

### Common Error Codes

- `VALIDATION_ERROR`: Data validation failed
- `NOT_FOUND`: Requested resource not found
- `CONTACT_NOT_FOUND`: Referenced contact not found
- `APPOINTMENT_NOT_FOUND`: Referenced appointment not found
- `RELATED_OBJECT_NOT_FOUND`: Referenced related object not found
- `AUTHENTICATION_REQUIRED`: Authentication token missing
- `INSUFFICIENT_PERMISSIONS`: User lacks required permissions

---

## Data Validation

### UUID Format
All UUIDs must be in standard UUID format: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`

### Date/DateTime Format
- **Dates**: ISO 8601 format `YYYY-MM-DD`
- **DateTimes**: ISO 8601 format with timezone `YYYY-MM-DDTHH:MM:SSZ`

### String Length Limits
- `first_name`, `last_name`: 100 characters max
- `email`: Standard email format validation
- `phone`, `mobile`: 20 characters max
- `address_line1`, `address_line2`: 255 characters max
- `title`: 200 characters max (for appointments/documents)

### Required Fields
Each model has different required fields. Check the OpenAPI documentation at `/api/docs/` for detailed field requirements.

---

## Multi-tenant Isolation

### Organization-based Data Isolation
All business data is automatically filtered by the authenticated user's organization:

1. **Automatic Filtering**: All queries are automatically filtered by `organization_id`
2. **Cross-organization Protection**: Users cannot access data from other organizations
3. **Audit Trail**: All actions are logged with organization context
4. **Data Creation**: New records automatically inherit the user's organization

### Organization ID Handling
- Organization IDs are extracted from JWT tokens by the Identity Service
- No need to manually specify organization ID in API calls
- All responses only include data from the user's organization

---

## Performance Considerations

### Pagination
- **Default Page Size**: 20 items per page
- **Maximum Page Size**: 100 items per page
- **Large Datasets**: Use pagination for all list endpoints

### Database Optimization
- All frequent query fields are indexed
- Use `select_related()` for foreign key relationships
- Soft deletes require filtering by `is_deleted=False`

### Caching
- JWT tokens are cached for 5 minutes to reduce Identity Service calls
- Consider implementing response caching for read-heavy operations

---

## Security Considerations

### Data Protection
- All sensitive data requires appropriate privacy levels
- Medical data automatically flagged for encryption
- Audit logging for all data access and modifications

### Access Control
- Role-based access control via Identity Service
- Organization-based data isolation
- Audit trail for all user actions

### Input Validation
- All inputs validated via Pydantic schemas
- SQL injection protection via Django ORM
- XSS prevention through proper serialization

---

## Examples

### Complete Contact Creation Flow

1. **Authenticate with Identity Service**:
```bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

2. **Create Contact with Django Backend**:
```bash
curl -X POST http://localhost:8000/api/business/contacts \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_type": "patient",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+33123456789",
    "consent_given": true
  }'
```

3. **List User's Contacts**:
```bash
curl -X GET http://localhost:8000/api/business/contacts \
  -H "Authorization: Bearer <jwt_token>"
```

This comprehensive API reference provides all the information needed to integrate with the Django backend service. All endpoints are production-ready and include comprehensive error handling, validation, and multi-tenant security.