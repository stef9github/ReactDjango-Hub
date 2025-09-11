from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel


class Contact(BaseModel):
    """Enhanced contact model for patients, providers, or business contacts."""
    
    CONTACT_TYPES = [
        ('patient', 'Patient'),
        ('provider', 'Healthcare Provider'),
        ('vendor', 'Vendor'),
        ('staff', 'Staff Member'),
        ('other', 'Other'),
    ]
    
    TITLE_CHOICES = [
        ('mr', 'Mr.'),
        ('mrs', 'Mrs.'),
        ('ms', 'Ms.'),
        ('dr', 'Dr.'),
        ('prof', 'Prof.'),
    ]
    
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPES, default='patient')
    title = models.CharField(max_length=10, choices=TITLE_CHOICES, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Address information
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default='France')
    
    # Medical/Business specific fields
    medical_record_number = models.CharField(max_length=50, blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)
    company = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    
    # Preferences
    preferred_language = models.CharField(max_length=10, default='fr', help_text='Language preference (fr, en, de)')
    communication_preference = models.CharField(max_length=20, choices=[
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('sms', 'SMS'),
        ('mail', 'Mail'),
    ], default='email')
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)
    
    # Compliance fields
    consent_given = models.BooleanField(default=False, help_text='RGPD consent for data processing')
    consent_date = models.DateTimeField(null=True, blank=True)
    data_retention_until = models.DateField(null=True, blank=True, help_text='Data retention expiry date')
    
    class Meta:
        indexes = [
            models.Index(fields=['contact_type', 'organization_id']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['email']),
            models.Index(fields=['medical_record_number']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'organization_id'],
                condition=models.Q(email__gt=''),
                name='unique_email_per_organization'
            ),
            models.UniqueConstraint(
                fields=['medical_record_number', 'organization_id'],
                condition=models.Q(medical_record_number__gt=''),
                name='unique_medical_record_per_organization'
            ),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self):
        if self.title:
            return f"{self.title} {self.first_name} {self.last_name}"
        return self.full_name


class Appointment(BaseModel):
    """Appointment/scheduling model for medical or business meetings."""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    APPOINTMENT_TYPES = [
        ('consultation', 'Consultation'),
        ('follow_up', 'Follow-up'),
        ('procedure', 'Procedure'),
        ('surgery', 'Surgery'),
        ('meeting', 'Business Meeting'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='appointments')
    
    # Scheduling
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    timezone = models.CharField(max_length=50, default='Europe/Paris')
    
    # Classification
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPES, default='consultation')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    priority = models.PositiveSmallIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Priority 1=Urgent, 5=Low'
    )
    
    # Provider/Staff assignment
    assigned_provider = models.UUIDField(null=True, blank=True, help_text='Provider ID from Identity Service')
    assigned_staff = models.UUIDField(null=True, blank=True, help_text='Staff member ID from Identity Service')
    
    # Location and resources
    location = models.CharField(max_length=200, blank=True, help_text='Room, building, or location')
    required_equipment = models.TextField(blank=True)
    estimated_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    
    # Billing and insurance
    billing_code = models.CharField(max_length=50, blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    insurance_authorized = models.BooleanField(default=False)
    
    # Workflow fields
    preparation_notes = models.TextField(blank=True)
    post_appointment_notes = models.TextField(blank=True)
    requires_follow_up = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    
    # Communication
    reminder_sent = models.BooleanField(default=False)
    confirmation_required = models.BooleanField(default=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['start_datetime', 'organization_id']),
            models.Index(fields=['status', 'organization_id']),
            models.Index(fields=['contact', 'start_datetime']),
            models.Index(fields=['assigned_provider', 'start_datetime']),
            models.Index(fields=['appointment_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.contact.full_name} ({self.start_datetime.strftime('%Y-%m-%d %H:%M')})"


class Document(BaseModel):
    """Document management for medical records, contracts, reports, etc."""
    
    DOCUMENT_TYPES = [
        ('medical_record', 'Medical Record'),
        ('lab_result', 'Lab Result'),
        ('imaging', 'Medical Imaging'),
        ('prescription', 'Prescription'),
        ('invoice', 'Invoice'),
        ('contract', 'Contract'),
        ('report', 'Report'),
        ('consent_form', 'Consent Form'),
        ('insurance', 'Insurance Document'),
        ('other', 'Other'),
    ]
    
    PRIVACY_LEVELS = [
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='other')
    
    # File information
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500, blank=True, help_text='Path to file in storage system')
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    checksum_md5 = models.CharField(max_length=32, blank=True)
    
    # Relationships
    related_contact = models.ForeignKey(Contact, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    related_appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    
    # Classification and access control
    privacy_level = models.CharField(max_length=20, choices=PRIVACY_LEVELS, default='internal')
    tags = models.JSONField(default=list, blank=True, help_text='List of tags for categorization')
    
    # Versioning
    version = models.PositiveSmallIntegerField(default=1)
    parent_document = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='versions')
    
    # Compliance and retention
    retention_until = models.DateField(null=True, blank=True, help_text='Document retention expiry date')
    is_encrypted = models.BooleanField(default=True, help_text='Whether the document is encrypted at rest')
    access_log_required = models.BooleanField(default=True, help_text='Whether access to this document should be logged')
    
    # Approval workflow
    requires_approval = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)
    approved_by = models.UUIDField(null=True, blank=True, help_text='User ID who approved the document')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['document_type', 'organization_id']),
            models.Index(fields=['related_contact', 'document_type']),
            models.Index(fields=['privacy_level']),
            models.Index(fields=['created_at', 'organization_id']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.document_type})"


class Transaction(BaseModel):
    """Financial transactions, billing, and payment tracking."""
    
    TRANSACTION_TYPES = [
        ('payment', 'Payment Received'),
        ('charge', 'Service Charge'),
        ('refund', 'Refund'),
        ('adjustment', 'Adjustment'),
        ('fee', 'Fee'),
        ('subscription', 'Subscription'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('insurance', 'Insurance'),
        ('other', 'Other'),
    ]
    
    # Basic transaction info
    transaction_id = models.CharField(max_length=100, unique=True, help_text='External transaction ID')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Amounts
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Relationships
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='transactions')
    related_appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, blank=True)
    payment_reference = models.CharField(max_length=200, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Billing
    invoice_number = models.CharField(max_length=100, blank=True)
    billing_period_start = models.DateField(null=True, blank=True)
    billing_period_end = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    
    # Description and notes
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Compliance
    requires_receipt = models.BooleanField(default=True)
    receipt_sent = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status', 'organization_id']),
            models.Index(fields=['contact', 'payment_date']),
            models.Index(fields=['transaction_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} {self.currency} ({self.contact.full_name})"


class AuditLog(BaseModel):
    """Comprehensive audit logging for compliance (HIPAA/RGPD)."""
    
    ACTION_TYPES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export'),
        ('print', 'Print'),
        ('access', 'Access'),
    ]
    
    # Who, What, When, Where
    user_id = models.UUIDField(help_text='User ID from Identity Service who performed the action')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    resource_type = models.CharField(max_length=100, help_text='Type of resource accessed (Contact, Appointment, etc.)')
    resource_id = models.UUIDField(null=True, blank=True, help_text='ID of the specific resource')
    
    # Context
    description = models.TextField(help_text='Detailed description of the action')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.UUIDField(null=True, blank=True)
    
    # Before/After state for data changes
    previous_values = models.JSONField(null=True, blank=True, help_text='Previous values before change')
    new_values = models.JSONField(null=True, blank=True, help_text='New values after change')
    
    # Risk assessment
    risk_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='low')
    
    # Success/failure
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['risk_level', 'created_at']),
            models.Index(fields=['success', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.action_type} on {self.resource_type} by {self.user_id} at {self.created_at}"
