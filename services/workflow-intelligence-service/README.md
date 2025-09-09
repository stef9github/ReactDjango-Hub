# Workflow & Intelligence Service

**Service**: Workflow Automation + AI Assistance  
**Port**: 8004  
**Technology**: FastAPI + SQLAlchemy + Redis + Celery + PostgreSQL + AI/ML  

## 🎯 Purpose

Provides business process automation (multi-step workflows) + AI helpers for text/doc tasks.

**Multi-Domain Usage**:
- **PublicHub**: Consultation lifecycle (need definition → publication → evaluation → award)
- **Medical**: Patient care pathway (pre-op → surgery → post-op), appointment workflows

## ⚙️ Architecture

- **API**: FastAPI endpoints for workflow management
- **Database**: PostgreSQL for workflows, steps, state machine
- **Queue**: Redis pub/sub for state changes + Celery for scheduled tasks
- **AI/NLP**: Claude/OpenAI integration (custom ML later)
- **Rules Engine**: Business logic validation and conditional workflows

## 🛠 Feature Set

### **MVP**
- ✅ Workflow definition (JSON schema of steps + transitions)
- ✅ API to create workflow instances (patient X, consultation Y)
- ✅ State transitions (`PATCH /workflow/{id}/next`)
- ✅ Basic rules engine (if missing doc, block transition)
- ✅ AI helper endpoints:
  - Text summarization (summarize reports/offers)
  - Smart form suggestions (pre-fill from context)

### **Later**
- 📋 Parallel workflows (e.g., multiple specialists at once)
- 📋 SLA/deadline monitoring (alert if workflow step overdue)
- 📋 Predictive insights (AI suggests next best step)
- 📋 Plug-in scoring engines (PublicHub offer scoring, patient risk detection)
- 📋 Visual workflow editor (drag & drop steps)

## 🚀 Quick Start

```bash
cd services/workflow-intelligence-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8004

# Start Celery worker (separate terminal)
celery -A workflow_intelligence_service.celery worker --loglevel=info
```

## 📡 API Endpoints

```
POST   /api/v1/workflows              # Create workflow instance
PATCH  /api/v1/workflows/{id}/next    # Advance workflow state
GET    /api/v1/workflows/{id}/status  # Get workflow status
GET    /api/v1/workflows/user/{id}    # Get user workflows
POST   /api/v1/ai/summarize           # AI text summarization
POST   /api/v1/ai/suggest             # Smart form suggestions
GET    /api/v1/workflows/sla-check    # SLA compliance monitoring
```

**Dependencies**: PostgreSQL, Redis, Celery, AI APIs (Claude/OpenAI), identity-service (port 8001)