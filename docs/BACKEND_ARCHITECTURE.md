# Backend Architecture Documentation

## 🏗️ **Architecture Overview**

ReactDjango Hub Medical is a Django 5.1.4 backend built for the French medical SaaS market, featuring multi-tenant architecture, RGPD compliance, and comprehensive audit logging. The system is designed for scalability, security, and regulatory compliance in healthcare environments.

### **Core Technologies**
- **Framework**: Django 5.1.4 LTS + Django Ninja 1.4.3
- **Database**: PostgreSQL 17 with UUID primary keys
- **API**: Django Ninja (FastAPI-style) - Single API approach
- **Cache**: Redis with django-cachalot for ORM caching
- **Monitoring**: django-health-check, django-silk profiling
- **Security**: django-guardian (object-level permissions), django-auditlog
- **Medical Standards**: HL7 v0.4.5, DICOM v3.0.1 support
- **Documentation**: Automatic OpenAPI/Swagger generation

## 📁 **Project Structure**

```
backend/
├── config/                     # Django project configuration
│   ├── settings/              # Split settings (base, development, production)
│   ├── urls.py                # Main URL configuration
│   ├── ninja_api.py           # Django Ninja API routes
│   ├── schema.py              # GraphQL schema (if applicable)
│   └── wsgi.py                # WSGI application
├── apps/                      # Django applications
│   ├── core/                  # Core utilities and base models
│   ├── analytics/             # Analytics and reporting
│   ├── billing/               # Billing and payment processing
│   ├── clinical/              # Clinical records and workflows
│   └── compliance/            # RGPD/HIPAA compliance features
├── locale/                    # Internationalization (FR/DE/EN)
├── media/                     # User uploaded files
├── static/                    # Static assets
├── templates/                 # Django templates
└── manage.py                  # Django management script
```

## 🏥 **Django Applications Architecture**

### **apps.core** - Foundation Layer
**Purpose**: Provides base functionality and shared utilities across all applications.

**Key Components**:
- `BaseModel`: Abstract model with UUID primary key and timestamps
- `rgpd_compliance.py`: RGPD compliance utilities
- `translation_utils.py`: Multi-language support (FR/DE/EN)

**Responsibilities**:
- Common model patterns and mixins
- Shared utilities and helper functions
- Base authentication and permission logic
- RGPD compliance framework

### **apps.analytics** - Data Intelligence Layer
**Purpose**: Handles metrics collection, reporting, and business intelligence.

**Key Models**:
- `AnalyticsRecord`: Metrics storage with audit logging
- Custom permissions: `view_analytics_data`, `export_analytics_data`

**Features**:
- Real-time analytics data collection
- Object-level permissions via django-guardian
- Comprehensive audit trails for regulatory compliance
- Export capabilities for data analysis

### **apps.clinical** - Medical Records Layer
**Purpose**: Manages clinical data, patient records, and medical workflows.

**Key Models**:
- `ClinicalRecord`: Core clinical data storage
- Medical workflow management
- HL7 and DICOM integration capabilities

**Features**:
- Encrypted medical data storage
- Clinical workflow automation
- Medical standards compliance (HL7/DICOM)
- Audit logging for patient data access

### **apps.billing** - Financial Management Layer
**Purpose**: Handles billing, invoicing, and payment processing.

**Key Models**:
- `BillingRecord`: Financial transaction records
- Multi-tenant billing isolation
- Decimal precision for financial calculations

**Features**:
- Secure financial data handling
- Multi-tenant billing separation
- Integration-ready for payment providers
- Financial audit trails

### **apps.compliance** - Regulatory Framework Layer
**Purpose**: Ensures RGPD, HIPAA, and medical regulation compliance.

**Key Models**:
- `ComplianceRecord`: Regulatory compliance tracking
- Audit trail management
- Data protection compliance

**Features**:
- RGPD compliance automation
- Audit log management
- Data retention policy enforcement
- Regulatory reporting capabilities

## 🔗 **API Architecture**

### **Django Ninja - Single API Strategy**

#### **Primary API Framework**
- **Endpoint Pattern**: `/api/`
- **Framework**: Django Ninja 1.4.3 (FastAPI-style)
- **Type Safety**: Full Pydantic schema validation
- **Performance**: High-performance async-ready endpoints
- **Authentication**: Django session + custom authentication
- **Documentation**: Automatic OpenAPI/Swagger generation

#### **Key Features**
- **Automatic Schema Generation**: OpenAPI 3.0 compliant
- **Type Hints**: Full Python type checking support
- **Pydantic Integration**: Request/response validation
- **Async Support**: Ready for async operations
- **Django Integration**: Native Django ORM and auth

### **API Documentation Endpoints**
- `/api/docs` - Interactive Swagger UI documentation
- `/api/openapi.json` - OpenAPI schema JSON
- Built-in schema introspection and validation

## 🔐 **Security Architecture**

### **Authentication & Authorization**
- **Primary Backend**: Django ModelBackend
- **Object Permissions**: django-guardian ObjectPermissionBackend
- **Session Management**: Django sessions with Redis storage
- **Permission Model**: Role-based + Object-level permissions

### **Data Protection**
- **Encryption**: django-encrypted-model-fields for sensitive data
- **Audit Logging**: django-auditlog for all model changes
- **Data Isolation**: Multi-tenant architecture with strict separation
- **Access Control**: Object-level permissions for fine-grained access

### **Compliance Features**
- **RGPD Compliance**: Built-in data protection utilities
- **Audit Trails**: Comprehensive logging for regulatory requirements
- **Data Retention**: Automated data lifecycle management
- **Medical Standards**: HL7/DICOM support for healthcare interoperability

## 🌐 **Internationalization Architecture**

### **Multi-Language Support**
- **Primary Language**: French (fr-fr)
- **Secondary Languages**: German (de), English (en)
- **Locale Configuration**: Europe/Paris timezone
- **Translation Files**: `/backend/locale/` directory

### **Market-Specific Features**
- French medical regulations compliance
- European data protection (RGPD) compliance
- Multi-currency support for EU markets
- Localized date/time formats

## 📊 **Performance & Monitoring**

### **Caching Strategy**
- **Primary Cache**: Redis with django-redis
- **ORM Caching**: django-cachalot for query optimization
- **Cache Invalidation**: Automatic cache management
- **Performance Monitoring**: django-silk profiling

### **Health Monitoring**
- **Health Checks**: `/health/` endpoint
- **Database Health**: Automatic DB connectivity checks
- **Cache Health**: Redis connectivity monitoring
- **Storage Health**: File system health checks

### **Development Tools**
- **Debug Toolbar**: Development environment debugging
- **Silk Profiling**: SQL query and performance analysis
- **Django Extensions**: Enhanced management commands
- **IPython Integration**: Enhanced Django shell

## 🗄️ **Database Architecture**

### **Database Design Principles**
- **Primary Keys**: UUID for all models (security + scalability)
- **Timestamps**: created_at/updated_at on all models
- **Soft Deletes**: Preservation for audit requirements
- **Multi-tenancy**: Strict data isolation between medical practices

### **Model Inheritance**
- **BaseModel**: Abstract base with UUID, timestamps
- **Audit Integration**: Automatic change logging
- **Permission Integration**: Object-level access control
- **Encryption Support**: Sensitive field encryption

## 🔧 **Configuration Architecture**

### **Settings Structure**
- **Base Settings**: `config/settings/base.py` - Core configuration
- **Environment Settings**: Development/Production split
- **Environment Variables**: python-decouple for secure config
- **Database**: PostgreSQL with connection pooling

### **Third-Party Integrations**
- **Medical Standards**: HL7 message parsing, DICOM image handling
- **Monitoring**: Health checks, performance profiling
- **Security**: Object permissions, audit logging
- **Performance**: Caching, query optimization

## 🚀 **Deployment Architecture**

### **Production Readiness**
- **WSGI Server**: Configured for production deployment
- **Static Files**: Separate static file serving
- **Media Handling**: Secure medical file storage
- **Environment Separation**: Clear dev/staging/production split

### **Medical Compliance**
- **Data Security**: End-to-end encryption support
- **Audit Requirements**: Comprehensive change logging
- **Backup Strategy**: Data retention and recovery
- **Access Control**: Multi-level permission system

---

*This architecture supports a scalable, secure, and compliant medical SaaS platform for the French market with European expansion capabilities.*