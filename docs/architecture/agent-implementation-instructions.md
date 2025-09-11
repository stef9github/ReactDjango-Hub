# Agent Implementation Instructions
## Specific Tasks and Priorities for Each Agent

**Version**: 1.0  
**Date**: January 2025  
**Purpose**: Actionable implementation instructions for all ReactDjango Hub agents  

---

## Executive Summary

This document provides specific, actionable instructions for each agent in the ReactDjango Hub ecosystem. Each section contains concrete tasks, file paths, integration requirements, and success criteria to enable agents to begin work immediately without requiring clarification.

---

## Part 1: Existing Service Agent Extensions

### ag-identity: Identity Service Agent

#### Immediate Tasks (Priority 1)

1. **Multi-Vertical User Roles**
   ```python
   # File: services/identity-service/app/models/roles.py
   # ADD: Vertical-specific role definitions
   VERTICAL_ROLES = {
       'medical': [
           'surgeon', 'physician', 'nurse', 'patient', 
           'medical_admin', 'billing_specialist'
       ],
       'public': [
           'buyer', 'supplier', 'procurement_officer',
           'evaluator', 'public_viewer', 'auditor'
       ]
   }
   ```

2. **Internationalization Support**
   ```python
   # File: services/identity-service/app/models/user.py
   # ADD: Language preference field
   preferred_language = Column(String(10), default='fr')
   locale_settings = Column(JSON, default={})
   
   # File: services/identity-service/app/api/auth.py
   # MODIFY: Include language in JWT claims
   claims['preferred_language'] = user.preferred_language
   claims['locale'] = user.locale_settings
   ```

3. **Organization Type Extensions**
   ```python
   # File: services/identity-service/app/models/organization.py
   # ADD: Vertical-specific organization types
   ORGANIZATION_TYPES = {
       'medical': ['hospital', 'clinic', 'practice', 'laboratory'],
       'public': ['ministry', 'agency', 'municipality', 'supplier_company']
   }
   ```

#### Testing Requirements
- Unit tests for each vertical role type
- Integration tests for multi-language JWT tokens
- Performance tests for 10,000+ organizations

#### Success Criteria
- [ ] All vertical roles implemented and tested
- [ ] Language preferences stored and retrievable
- [ ] JWT tokens include locale information
- [ ] Organization types support both verticals

---

### ag-communication: Communication Service Agent

#### Immediate Tasks (Priority 1)

1. **Multi-Language Template System**
   ```python
   # File: services/communication-service/app/templates/manager.py
   class MultiLanguageTemplateManager:
       def get_template(self, template_name: str, language: str):
           # Implementation for language-specific templates
           template_path = f"templates/{language}/{template_name}.html"
           return self.load_template(template_path)
   ```

2. **Vertical-Specific Notification Templates**
   ```yaml
   # File: services/communication-service/templates/medical/fr/surgery_reminder.yaml
   subject: "Rappel: Intervention chirurgicale prévue"
   body: |
     Bonjour {{ patient_name }},
     Votre intervention est prévue le {{ surgery_date }}.
     Lieu: {{ facility_name }}
     Heure: {{ surgery_time }}
   
   # File: services/communication-service/templates/public/fr/tender_alert.yaml
   subject: "Nouvel appel d'offres: {{ tender_title }}"
   body: |
     Un nouvel appel d'offres correspondant à vos critères:
     Référence: {{ tender_reference }}
     Date limite: {{ submission_deadline }}
   ```

3. **Channel Priority by Vertical**
   ```python
   # File: services/communication-service/app/config/channels.py
   VERTICAL_CHANNEL_PRIORITY = {
       'medical': {
           'urgent': ['sms', 'push', 'email'],
           'normal': ['email', 'in_app']
       },
       'public': {
           'tender_alert': ['email', 'platform'],
           'deadline_reminder': ['email', 'sms']
       }
   }
   ```

#### Testing Requirements
- Template rendering tests for all 5 languages
- Channel delivery tests for each vertical
- Load tests for bulk notifications (1000+ recipients)

#### Success Criteria
- [ ] Templates available in FR, EN, DE, IT, ES
- [ ] Vertical-specific templates implemented
- [ ] Channel routing by vertical works
- [ ] Bulk notification performance < 5 seconds for 1000 recipients

---

### ag-content: Content Service Agent

#### Immediate Tasks (Priority 1)

1. **Multi-Language Document Metadata**
   ```python
   # File: services/content-service/app/models/document.py
   class Document(Base):
       # ADD: Language support
       language = Column(String(10), nullable=False, default='fr')
       translations = relationship("DocumentTranslation", back_populates="document")
       
   class DocumentTranslation(Base):
       document_id = Column(UUID, ForeignKey('documents.id'))
       language = Column(String(10))
       translated_content_url = Column(String(500))
   ```

2. **Vertical-Specific Document Types**
   ```python
   # File: services/content-service/app/config/document_types.py
   VERTICAL_DOCUMENT_TYPES = {
       'medical': {
           'clinical_note': {'retention_years': 7, 'encryption': 'required'},
           'lab_result': {'retention_years': 5, 'encryption': 'required'},
           'consent_form': {'retention_years': 10, 'encryption': 'required'}
       },
       'public': {
           'tender_document': {'retention_years': 10, 'public': True},
           'bid_submission': {'retention_years': 10, 'encryption': 'required'},
           'contract': {'retention_years': 10, 'versioning': True}
       }
   }
   ```

3. **Document Generation with i18n**
   ```python
   # File: services/content-service/app/generators/pdf_generator.py
   class LocalizedPDFGenerator:
       def generate(self, template: str, data: dict, language: str):
           # Load language-specific template
           template_obj = self.get_template(template, language)
           # Apply locale-specific formatting
           formatted_data = self.format_for_locale(data, language)
           # Generate PDF with proper fonts for language
           return self.render_pdf(template_obj, formatted_data, language)
   ```

#### Testing Requirements
- Document upload/download tests in all languages
- Encryption verification for sensitive documents
- PDF generation tests with special characters (accents, umlauts)

#### Success Criteria
- [ ] Documents support language metadata
- [ ] Vertical-specific retention policies implemented
- [ ] PDF generation works for all 5 languages
- [ ] Document search works across languages

---

### ag-workflow: Workflow Service Agent

#### Immediate Tasks (Priority 1)

1. **Vertical-Specific Workflow Templates**
   ```python
   # File: services/workflow-service/app/templates/medical_workflows.py
   MEDICAL_WORKFLOWS = {
       'surgery_approval': {
           'steps': [
               {'name': 'insurance_verification', 'sla_hours': 24},
               {'name': 'medical_clearance', 'sla_hours': 48},
               {'name': 'facility_scheduling', 'sla_hours': 24}
           ]
       },
       'patient_discharge': {
           'steps': [
               {'name': 'discharge_summary', 'sla_hours': 4},
               {'name': 'medication_reconciliation', 'sla_hours': 2},
               {'name': 'follow_up_scheduling', 'sla_hours': 1}
           ]
       }
   }
   
   # File: services/workflow-service/app/templates/public_workflows.py
   PUBLIC_WORKFLOWS = {
       'tender_evaluation': {
           'steps': [
               {'name': 'administrative_check', 'sla_hours': 48},
               {'name': 'technical_evaluation', 'sla_hours': 120},
               {'name': 'financial_evaluation', 'sla_hours': 72},
               {'name': 'award_decision', 'sla_hours': 48}
           ]
       }
   }
   ```

2. **Multi-Language Workflow Notifications**
   ```python
   # File: services/workflow-service/app/notifications/workflow_notifier.py
   def notify_step_completion(self, workflow, step, language='fr'):
       template = f"workflow_step_{step.status}"
       recipients = self.get_step_stakeholders(workflow, step)
       
       for recipient in recipients:
           self.comm_service.send_notification({
               'template': template,
               'language': recipient.preferred_language or language,
               'data': {
                   'workflow_type': workflow.type,
                   'step_name': self.translate(step.name, recipient.preferred_language),
                   'next_step': self.translate(workflow.next_step, recipient.preferred_language)
               }
           })
   ```

#### Testing Requirements
- Workflow execution tests for each vertical template
- SLA monitoring and alerting tests
- Multi-language notification tests

#### Success Criteria
- [ ] All vertical workflows implemented
- [ ] SLA tracking functional
- [ ] Notifications sent in user's preferred language
- [ ] Workflow state persistence works

---

### ag-backend: Django Backend Agent

#### Immediate Tasks (Priority 1)

1. **Create Common Core Apps Structure**
   ```bash
   # Directory structure to create:
   backend/apps/core/
   ├── base/
   │   ├── models.py      # BaseEntity, AuditModel, SoftDeleteModel
   │   ├── views.py       # BaseModelViewSet, BaseAPIView
   │   └── serializers.py # BaseSerializer
   ├── permissions/
   │   ├── models.py      # Permission models
   │   └── decorators.py  # @require_vertical, @require_role
   ├── i18n/
   │   ├── middleware.py  # LanguageMiddleware
   │   └── utils.py       # Translation utilities
   └── cache/
       ├── backends.py    # Vertical-aware cache backend
       └── decorators.py  # @cache_by_vertical
   ```

2. **Implement Vertical Routing**
   ```python
   # File: backend/config/urls.py
   urlpatterns = [
       path('api/v1/medical/', include('apps.medical.urls')),
       path('api/v1/public/', include('apps.public.urls')),
       path('api/v1/common/', include('apps.core.urls')),
   ]
   
   # File: backend/apps/core/middleware/vertical_routing.py
   class VerticalRoutingMiddleware:
       def process_request(self, request):
           # Detect vertical from URL or header
           request.vertical = self.detect_vertical(request)
           # Set database routing hints
           request._db_vertical = f"{request.vertical}_db"
   ```

3. **Service Client Integration**
   ```python
   # File: backend/apps/core/services/clients.py
   class IdentityServiceClient:
       BASE_URL = "http://identity-service:8001"
       
       @classmethod
       def get_user(cls, user_id: str):
           response = requests.get(f"{cls.BASE_URL}/users/{user_id}")
           return response.json()
   
   class CommunicationServiceClient:
       # Similar implementation
   
   class ContentServiceClient:
       # Similar implementation
   
   class WorkflowServiceClient:
       # Similar implementation
   ```

#### Testing Requirements
- Unit tests for all base classes
- Integration tests with all microservices
- Multi-database routing tests
- i18n middleware tests

#### Success Criteria
- [ ] Core apps structure created
- [ ] Service clients functional
- [ ] Vertical routing works
- [ ] i18n middleware processes all requests

---

### ag-frontend: React Frontend Agent

#### Immediate Tasks (Priority 1)

1. **Configure i18next for Multi-Language**
   ```typescript
   // File: frontend/src/i18n/config.ts
   import i18n from 'i18next';
   import { initReactI18next } from 'react-i18next';
   
   // Import all translation files
   import frCommon from '../locales/fr/common.json';
   import frMedical from '../locales/fr/medical.json';
   import frPublic from '../locales/fr/public.json';
   // ... import other languages
   
   i18n.use(initReactI18next).init({
     lng: 'fr',
     fallbackLng: 'fr',
     ns: ['common', 'medical', 'public'],
     defaultNS: 'common',
     resources: {
       fr: { common: frCommon, medical: frMedical, public: frPublic },
       en: { /* ... */ },
       de: { /* ... */ },
       it: { /* ... */ },
       es: { /* ... */ }
     }
   });
   ```

2. **Create Vertical App Structure**
   ```typescript
   // File: frontend/src/verticals/medical/MedicalApp.tsx
   export const MedicalApp: React.FC = () => {
     return (
       <Routes>
         <Route path="/dashboard" element={<SurgeonDashboard />} />
         <Route path="/patients" element={<PatientList />} />
         <Route path="/surgery" element={<SurgeryScheduler />} />
         {/* ... other medical routes */}
       </Routes>
     );
   };
   
   // File: frontend/src/verticals/public/PublicApp.tsx
   export const PublicApp: React.FC = () => {
     return (
       <Routes>
         <Route path="/tenders" element={<TenderList />} />
         <Route path="/suppliers" element={<SupplierRegistry />} />
         <Route path="/bids" element={<BidManagement />} />
         {/* ... other public routes */}
       </Routes>
     );
   };
   ```

3. **Implement Component Library**
   ```typescript
   // File: frontend/src/components/common/DataTable/DataTable.tsx
   interface DataTableProps<T> {
     data: T[];
     columns: Column<T>[];
     onSort?: (column: string) => void;
     onFilter?: (filters: Filter[]) => void;
     locale?: string;
   }
   
   export const DataTable = <T,>({ data, columns, locale = 'fr' }: DataTableProps<T>) => {
     const { t } = useTranslation('common');
     // Implementation with i18n support
   };
   ```

#### Testing Requirements
- Component tests with all language variations
- Routing tests for both verticals
- API integration tests
- Accessibility tests (WCAG 2.1 AA)

#### Success Criteria
- [ ] i18next configured and working
- [ ] Both vertical apps routing correctly
- [ ] Common components support i18n
- [ ] Language switcher functional

---

### ag-infrastructure: Infrastructure Agent

#### Immediate Tasks (Priority 1)

1. **Multi-Vertical Docker Compose**
   ```yaml
   # File: docker/docker-compose.multi-vertical.yml
   version: '3.8'
   
   services:
     # Common services
     kong:
       image: kong:3.0
       environment:
         - KONG_DATABASE=postgres
         - KONG_PG_HOST=postgres
       volumes:
         - ./kong/config:/usr/local/kong/declarative
     
     # Medical vertical
     medical-frontend:
       build:
         context: ../frontend
         args:
           - VERTICAL=medical
       environment:
         - VITE_VERTICAL=medical
         - VITE_API_URL=http://localhost:8000/api/v1/medical
     
     # Public vertical
     public-frontend:
       build:
         context: ../frontend
         args:
           - VERTICAL=public
       environment:
         - VITE_VERTICAL=public
         - VITE_API_URL=http://localhost:8000/api/v1/public
   ```

2. **Kubernetes Manifests for Production**
   ```yaml
   # File: infrastructure/k8s/verticals/medical/deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: medical-hub
     namespace: medical
   spec:
     replicas: 3
     template:
       spec:
         containers:
         - name: app
           image: reactdjango-hub/medical:latest
           env:
           - name: VERTICAL
             value: "medical"
           - name: LANGUAGE_DEFAULT
             value: "fr"
   ```

3. **CI/CD Pipeline Configuration**
   ```yaml
   # File: .github/workflows/deploy-verticals.yml
   name: Deploy Verticals
   on:
     push:
       branches: [main]
   
   jobs:
     deploy-medical:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Build Medical Hub
           run: |
             docker build -t medical-hub:${{ github.sha }} \
               --build-arg VERTICAL=medical \
               --build-arg DEFAULT_LANG=fr .
         - name: Deploy to K8s
           run: |
             kubectl set image deployment/medical-hub \
               app=medical-hub:${{ github.sha }} \
               -n medical
   
     deploy-public:
       # Similar configuration for public hub
   ```

#### Testing Requirements
- Container health check tests
- Multi-vertical routing tests
- Load balancing tests
- Disaster recovery tests

#### Success Criteria
- [ ] Both verticals deployable independently
- [ ] Kong routing works for both verticals
- [ ] Kubernetes manifests validated
- [ ] CI/CD pipeline executes successfully

---

### ag-coordinator: Services Coordinator Agent

#### Immediate Tasks (Priority 1)

1. **API Gateway Configuration**
   ```yaml
   # File: kong/config/routes.yaml
   services:
     - name: medical-backend
       url: http://django-backend:8000
       routes:
         - name: medical-api
           paths:
             - /api/v1/medical
           strip_path: false
           plugins:
             - name: jwt
             - name: rate-limiting
               config:
                 minute: 100
             - name: request-transformer
               config:
                 add:
                   headers:
                     X-Vertical: medical
     
     - name: public-backend
       url: http://django-backend:8000
       routes:
         - name: public-api
           paths:
             - /api/v1/public
           strip_path: false
           plugins:
             - name: jwt
             - name: cors
   ```

2. **Service Discovery Configuration**
   ```python
   # File: services/coordinator/service_registry.py
   SERVICE_REGISTRY = {
       'identity': {
           'url': 'http://identity-service:8001',
           'health': '/health',
           'timeout': 5
       },
       'communication': {
           'url': 'http://communication-service:8002',
           'health': '/health',
           'timeout': 5
       },
       'content': {
           'url': 'http://content-service:8003',
           'health': '/health',
           'timeout': 5
       },
       'workflow': {
           'url': 'http://workflow-service:8004',
           'health': '/health',
           'timeout': 5
       }
   }
   ```

3. **Cross-Service Integration Tests**
   ```python
   # File: tests/integration/test_cross_service.py
   def test_medical_patient_creation_flow():
       # 1. Create user in identity service
       # 2. Create patient in medical app
       # 3. Send welcome notification
       # 4. Store consent documents
       # 5. Start onboarding workflow
       pass
   
   def test_public_tender_publication_flow():
       # 1. Authenticate buyer
       # 2. Create tender
       # 3. Upload documents
       # 4. Notify suppliers
       # 5. Start submission workflow
       pass
   ```

#### Testing Requirements
- API gateway routing tests
- Service health monitoring tests
- Cross-service transaction tests
- Rate limiting tests

#### Success Criteria
- [ ] Kong routes configured for both verticals
- [ ] Service discovery operational
- [ ] Health checks passing
- [ ] Cross-service flows tested

---

## Part 2: New Service Agent Instructions

### ag-scheduling: Scheduling Service Agent

#### Service Overview
- **Purpose**: Centralized scheduling for appointments, resources, and deadlines
- **Port**: 8005
- **Database**: PostgreSQL (scheduling_db)
- **Technology**: FastAPI + SQLAlchemy

#### Implementation Tasks

1. **Create Service Structure**
   ```bash
   services/scheduling-service/
   ├── app/
   │   ├── main.py
   │   ├── models/
   │   │   ├── appointment.py
   │   │   ├── resource.py
   │   │   └── availability.py
   │   ├── api/
   │   │   ├── appointments.py
   │   │   ├── resources.py
   │   │   └── calendar.py
   │   ├── services/
   │   │   ├── scheduler.py
   │   │   ├── conflict_resolver.py
   │   │   └── reminder_service.py
   │   └── config/
   │       └── settings.py
   ├── tests/
   ├── requirements.txt
   └── Dockerfile
   ```

2. **Core Models**
   ```python
   # File: services/scheduling-service/app/models/appointment.py
   class Appointment(Base):
       __tablename__ = 'appointments'
       
       id = Column(UUID, primary_key=True)
       vertical = Column(String(50))  # medical, public
       entity_type = Column(String(50))  # surgery, meeting, deadline
       entity_id = Column(UUID)
       
       start_time = Column(DateTime, nullable=False)
       end_time = Column(DateTime, nullable=False)
       
       resources = relationship("ResourceBooking")
       participants = relationship("Participant")
       
       recurrence_rule = Column(String(200))  # RFC 5545 RRULE
       timezone = Column(String(50), default='Europe/Paris')
   ```

3. **Vertical-Specific Features**
   ```python
   # Medical scheduling
   class SurgeryScheduler:
       def schedule_surgery(self, surgery_data):
           # Check OR availability
           # Check surgeon availability
           # Check anesthesiologist availability
           # Book all resources atomically
           pass
   
   # Public scheduling
   class TenderDeadlineManager:
       def set_tender_deadlines(self, tender):
           # Set submission deadline
           # Set evaluation milestones
           # Set award date
           # Send reminder schedules
           pass
   ```

#### Testing Requirements
- Conflict detection tests
- Timezone handling tests
- Recurrence rule tests
- Performance tests (1000+ concurrent bookings)

#### Success Criteria
- [ ] Service running on port 8005
- [ ] REST API documented in OpenAPI
- [ ] Integration with both verticals
- [ ] Reminder system functional

---

### ag-financial: Financial Service Agent

#### Service Overview
- **Purpose**: Billing, payments, invoicing, financial reporting
- **Port**: 8006
- **Database**: PostgreSQL (financial_db)
- **Technology**: FastAPI + SQLAlchemy

#### Implementation Tasks

1. **Core Financial Models**
   ```python
   # File: services/financial-service/app/models/invoice.py
   class Invoice(Base):
       __tablename__ = 'invoices'
       
       id = Column(UUID, primary_key=True)
       invoice_number = Column(String(50), unique=True)
       vertical = Column(String(50))
       
       # Multi-currency support
       amount = Column(Decimal(15, 2))
       currency = Column(String(3), default='EUR')
       
       # i18n support
       language = Column(String(10), default='fr')
       
       # Medical: patient billing, insurance claims
       # Public: supplier payments, guarantees
       entity_type = Column(String(50))
       entity_id = Column(UUID)
   ```

2. **Payment Processing**
   ```python
   # File: services/financial-service/app/services/payment_processor.py
   class PaymentProcessor:
       def process_payment(self, payment_data):
           # Validate payment data
           # Check fraud rules
           # Process through payment gateway
           # Update invoice status
           # Send confirmation
           pass
   
   class InsuranceClaimProcessor:
       def submit_claim(self, claim_data):
           # Medical-specific insurance claim handling
           pass
   
   class PublicProcurementPayment:
       def process_contract_payment(self, contract):
           # Public-specific payment with validation
           pass
   ```

3. **Financial Reporting**
   ```python
   # File: services/financial-service/app/reports/generator.py
   class FinancialReportGenerator:
       def generate_report(self, report_type, filters, language='fr'):
           # Generate financial reports in requested language
           # Support PDF, Excel, CSV formats
           pass
   ```

#### Testing Requirements
- Payment gateway integration tests
- Multi-currency calculation tests
- Report generation tests
- Audit trail tests

#### Success Criteria
- [ ] Service running on port 8006
- [ ] Payment processing functional
- [ ] Multi-currency support
- [ ] Reports generated in all languages

---

### ag-search: Search Service Agent

#### Service Overview
- **Purpose**: Full-text search, faceted search, analytics
- **Port**: 8007
- **Database**: ElasticSearch
- **Technology**: FastAPI + ElasticSearch client

#### Implementation Tasks

1. **ElasticSearch Index Configuration**
   ```python
   # File: services/search-service/app/indices/medical_index.py
   MEDICAL_PATIENT_INDEX = {
       "mappings": {
           "properties": {
               "name": {
                   "type": "text",
                   "fields": {
                       "keyword": {"type": "keyword"},
                       "french": {"type": "text", "analyzer": "french"},
                       "english": {"type": "text", "analyzer": "english"}
                   }
               },
               "medical_record": {"type": "keyword"},
               "conditions": {"type": "text", "analyzer": "medical_analyzer"}
           }
       }
   }
   
   # File: services/search-service/app/indices/public_index.py
   PUBLIC_TENDER_INDEX = {
       "mappings": {
           "properties": {
               "title": {
                   "type": "text",
                   "fields": {
                       "french": {"type": "text", "analyzer": "french"},
                       "english": {"type": "text", "analyzer": "english"}
                   }
               },
               "cpv_codes": {"type": "keyword"},
               "value_range": {"type": "long_range"}
           }
       }
   }
   ```

2. **Multi-Language Search**
   ```python
   # File: services/search-service/app/services/search_engine.py
   class MultiLanguageSearchEngine:
       def search(self, query, language='fr', vertical=None):
           # Detect language if not specified
           # Apply language-specific analyzers
           # Search across appropriate indices
           # Return faceted results
           pass
   ```

3. **Search Synchronization**
   ```python
   # File: services/search-service/app/sync/data_sync.py
   class SearchDataSynchronizer:
       def sync_from_database(self, entity_type, entity_id):
           # Fetch from appropriate service
           # Transform for search index
           # Update ElasticSearch
           pass
   ```

#### Testing Requirements
- Multi-language search tests
- Faceted search tests
- Performance tests (sub-second for 1M documents)
- Relevance scoring tests

#### Success Criteria
- [ ] ElasticSearch cluster running
- [ ] Indices created for both verticals
- [ ] Multi-language search working
- [ ] Real-time synchronization

---

### ag-ai-engine: AI/ML Service Agent

#### Service Overview
- **Purpose**: AI/ML models, predictions, NLP processing
- **Port**: 8008
- **Database**: PostgreSQL (ai_db) + Vector DB
- **Technology**: FastAPI + Transformers + scikit-learn

#### Implementation Tasks

1. **Medical AI Features**
   ```python
   # File: services/ai-service/app/medical/diagnosis_assistant.py
   class DiagnosisAssistant:
       def suggest_diagnoses(self, symptoms, patient_history):
           # Use ML model to suggest possible diagnoses
           # Return with confidence scores
           pass
   
   class SurgeryRiskPredictor:
       def predict_risk(self, patient, procedure):
           # Predict surgical risk factors
           pass
   ```

2. **Public Procurement AI**
   ```python
   # File: services/ai-service/app/public/tender_analyzer.py
   class TenderAnalyzer:
       def analyze_tender(self, tender_text, language='fr'):
           # Extract key information
           # Classify tender category
           # Identify requirements
           pass
   
   class BidOptimizer:
       def optimize_bid(self, tender, supplier_profile):
           # Suggest optimal bid strategy
           pass
   ```

3. **NLP Processing**
   ```python
   # File: services/ai-service/app/nlp/multilingual_processor.py
   class MultilingualNLPProcessor:
       def process_text(self, text, language, task):
           # Load language-specific model
           # Perform NLP task (NER, classification, summarization)
           # Return structured results
           pass
   ```

#### Testing Requirements
- Model accuracy tests
- Multi-language NLP tests
- Performance benchmarks
- Bias detection tests

#### Success Criteria
- [ ] AI models deployed and accessible
- [ ] Multi-language NLP functional
- [ ] Vertical-specific features working
- [ ] API response time < 2 seconds

---

### ag-market-intelligence: Market Intelligence Agent

#### Service Overview
- **Purpose**: Opportunity matching, market analysis, competitive intelligence
- **Port**: 8009
- **Database**: PostgreSQL (market_db)
- **Technology**: FastAPI + Data processing pipelines

#### Implementation Tasks

1. **Opportunity Matching Engine**
   ```python
   # File: services/market-service/app/matching/opportunity_matcher.py
   class OpportunityMatcher:
       def match_suppliers_to_tenders(self, tender):
           # Analyze tender requirements
           # Match with supplier capabilities
           # Score matches
           # Return ranked suppliers
           pass
   
   class MedicalReferralMatcher:
       def match_patient_to_specialists(self, patient_needs):
           # Match patients with appropriate specialists
           pass
   ```

2. **Market Analytics**
   ```python
   # File: services/market-service/app/analytics/market_analyzer.py
   class MarketAnalyzer:
       def analyze_procurement_trends(self, filters):
           # Analyze tender trends
           # Price benchmarking
           # Supplier performance metrics
           pass
   
   class MedicalMarketAnalytics:
       def analyze_procedure_trends(self):
           # Analyze medical procedure trends
           # Insurance coverage patterns
           pass
   ```

3. **Competitive Intelligence**
   ```python
   # File: services/market-service/app/intelligence/competitor_tracker.py
   class CompetitorTracker:
       def track_competitor_bids(self, supplier_id):
           # Track competitor bidding patterns
           # Analyze win/loss rates
           pass
   ```

#### Testing Requirements
- Matching algorithm tests
- Analytics accuracy tests
- Data pipeline tests
- Performance tests with large datasets

#### Success Criteria
- [ ] Matching engine operational
- [ ] Analytics dashboards functional
- [ ] Real-time data processing
- [ ] API documented and tested

---

### ag-contract: Contract Management Agent

#### Service Overview
- **Purpose**: Contract lifecycle management, compliance tracking
- **Port**: 8010
- **Database**: PostgreSQL (contract_db)
- **Technology**: FastAPI + Document processing

#### Implementation Tasks

1. **Contract Models**
   ```python
   # File: services/contract-service/app/models/contract.py
   class Contract(Base):
       __tablename__ = 'contracts'
       
       id = Column(UUID, primary_key=True)
       contract_number = Column(String(100), unique=True)
       vertical = Column(String(50))
       
       # Multi-language support
       language = Column(String(10))
       
       # Version control
       version = Column(Integer, default=1)
       parent_contract_id = Column(UUID, nullable=True)
       
       # Digital signatures
       signatures = relationship("ContractSignature")
       
       # Compliance tracking
       compliance_checks = relationship("ComplianceCheck")
   ```

2. **Contract Templates**
   ```python
   # File: services/contract-service/app/templates/template_engine.py
   class ContractTemplateEngine:
       def generate_contract(self, template_id, data, language='fr'):
           # Load language-specific template
           # Merge with data
           # Apply legal clauses
           # Generate PDF
           pass
   ```

3. **Compliance Monitoring**
   ```python
   # File: services/contract-service/app/compliance/monitor.py
   class ContractComplianceMonitor:
       def monitor_contract(self, contract):
           # Check milestones
           # Verify deliverables
           # Track payments
           # Alert on violations
           pass
   ```

#### Testing Requirements
- Template generation tests
- Digital signature tests
- Compliance rule tests
- Multi-language document tests

#### Success Criteria
- [ ] Contract CRUD operations working
- [ ] Template engine functional
- [ ] Digital signatures implemented
- [ ] Compliance monitoring active

---

## Part 3: Implementation Priority Matrix

### Phase 1: Foundation (Weeks 1-2)
**Critical Path - Must Complete First**

| Agent | Task | Dependencies | Priority |
|-------|------|--------------|----------|
| ag-backend | Create core apps structure | None | P0 |
| ag-backend | Implement service clients | None | P0 |
| ag-frontend | Configure i18next | None | P0 |
| ag-identity | Add vertical roles | None | P0 |
| ag-infrastructure | Setup Docker compose | None | P0 |

### Phase 2: Vertical Implementation (Weeks 3-4)
**Parallel Work Streams Possible**

| Agent | Task | Dependencies | Priority |
|-------|------|--------------|----------|
| ag-backend | Medical Django apps | Phase 1 | P1 |
| ag-backend | Public Django apps | Phase 1 | P1 |
| ag-frontend | Medical UI components | Phase 1 | P1 |
| ag-frontend | Public UI components | Phase 1 | P1 |
| ag-communication | Vertical templates | Phase 1 | P1 |

### Phase 3: Service Extensions (Weeks 5-6)
**Enhance Existing Services**

| Agent | Task | Dependencies | Priority |
|-------|------|--------------|----------|
| ag-identity | Organization types | Phase 2 | P2 |
| ag-content | Document types | Phase 2 | P2 |
| ag-workflow | Vertical workflows | Phase 2 | P2 |
| ag-coordinator | API gateway config | Phase 2 | P2 |

### Phase 4: New Services (Weeks 7-9)
**Can Be Developed in Parallel**

| Agent | Task | Dependencies | Priority |
|-------|------|--------------|----------|
| ag-scheduling | Build service | Phase 3 | P3 |
| ag-financial | Build service | Phase 3 | P3 |
| ag-search | Build service | Phase 3 | P3 |

### Phase 5: Advanced Services (Weeks 10-12)
**Requires Core Platform Stable**

| Agent | Task | Dependencies | Priority |
|-------|------|--------------|----------|
| ag-ai-engine | Build service | Phase 4 | P4 |
| ag-market-intelligence | Build service | Phase 4 | P4 |
| ag-contract | Build service | Phase 4 | P4 |

---

## Success Metrics

### Overall Platform Success Criteria
- [ ] Both verticals (Medical & Public) fully functional
- [ ] All 5 languages (FR, EN, DE, IT, ES) supported
- [ ] All microservices communicating successfully
- [ ] Performance: <200ms API response time
- [ ] Availability: 99.9% uptime
- [ ] Security: All OWASP Top 10 addressed
- [ ] Compliance: GDPR, HIPAA compliant
- [ ] Testing: >80% code coverage

### Agent-Specific Deliverables
Each agent must:
1. Complete all P0 and P1 tasks
2. Achieve >80% test coverage
3. Document all APIs
4. Pass integration tests
5. Deploy to staging environment

---

## Conclusion

These instructions provide each agent with specific, actionable tasks to implement the ReactDjango Hub platform. Agents should begin with their Phase 1 tasks immediately, coordinating through the ag-coordinator for integration points. All code should follow the established patterns, support internationalization, and include comprehensive testing.

For questions or clarifications, agents should consult the architecture documentation or coordinate with ag-techlead for architectural decisions.