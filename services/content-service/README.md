# Content Service

**Service**: Document Management, Search & Audit  
**Port**: 8002  
**Technology**: FastAPI + SQLAlchemy + Redis + PostgreSQL  

## 🎯 Purpose

Centralized handling of documents, with search capabilities and full audit/compliance traceability.

**Multi-Domain Usage**:
- **PublicHub**: RC, CCAP, CCTP, supplier offers, contracts
- **Medical**: Ordonnances, consent forms, medical documents, imaging reports

## ⚙️ Architecture

- **API**: FastAPI service with async endpoints
- **Database**: PostgreSQL for metadata (doc owner, type, status, version)
- **Storage**: PostgreSQL bytea (MVP) → S3/MinIO migration path
- **Cache**: Redis for search results and rate limiting
- **Search**: PostgreSQL full-text search → Elasticsearch migration
- **Migrations**: Alembic for schema versioning

## 🛠 Feature Set

### **MVP**
- ✅ Upload/download documents (PDF, Word, images)
- ✅ Metadata tagging (doc type, owner, timestamps)
- ✅ Simple full-text search
- ✅ Complete audit log (who uploaded/downloaded/modified)

### **Later**
- 📋 Document versioning & diff between docs
- 📋 OCR for scanned PDFs
- 📋 Encrypted storage (field-level or file-level)
- 📋 Document templates (auto-generate contracts, certificates)
- 📋 Export to signed PDF (digital signature support)

## 🚀 Quick Start

```bash
cd services/content-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

## 📡 API Endpoints

```
POST   /api/v1/documents              # Upload document
GET    /api/v1/documents              # List documents
GET    /api/v1/documents/{doc_id}     # Get document
DELETE /api/v1/documents/{doc_id}     # Delete document
GET    /api/v1/search                 # Search documents
GET    /api/v1/audit/documents/{id}   # Document audit trail
```

**Dependencies**: PostgreSQL, Redis, identity-service (port 8001)