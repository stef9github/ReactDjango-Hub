# Communication Service

**Service**: Notifications + Messaging  
**Port**: 8003  
**Technology**: FastAPI + SQLAlchemy + Redis + Celery + PostgreSQL  

## 🎯 Purpose

Unifies all user communication (one-off notifications, reminders, and two-way messaging).

**Multi-Domain Usage**:
- **PublicHub**: Notify suppliers, send bid updates, procurement communications
- **Medical**: Send patient reminders, doctor-patient chat, appointment notifications

## ⚙️ Architecture

- **API**: FastAPI endpoints for sending/receiving messages
- **Database**: PostgreSQL for notification logs + message history
- **Queue**: Redis + Celery for async job queue (email/SMS sending)
- **Providers**: 
  - **Email**: SendGrid/Mailgun/SMTP
  - **SMS**: Twilio/OVH  
  - **Push**: Firebase or WebPush

## 🛠 Feature Set

### **MVP**
- ✅ Notification API: `POST /notify` (email, SMS, in-app)
- ✅ Messaging API: `POST /message`, `GET /conversation/{id}`
- ✅ Templates: notification text with variables
- ✅ Read/unread status tracking

### **Later**
- 📋 Message threads with attachments
- 📋 Rich notifications (clickable links, deep links)
- 📋 Scheduling (send at X time)
- 📋 Delivery receipts (opened/read)
- 📋 Group messaging / broadcasts

## 🚀 Quick Start

```bash
cd services/communication-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8003

# Start Celery worker (separate terminal)
celery -A communication_service.celery worker --loglevel=info
```

## 📡 API Endpoints

```
POST   /api/v1/notifications          # Send notification
GET    /api/v1/notifications/unread   # Get unread notifications
POST   /api/v1/messages               # Send message
GET    /api/v1/conversations          # List conversations
GET    /api/v1/conversations/{id}     # Get conversation history
POST   /api/v1/templates              # Create message template
```

**Dependencies**: PostgreSQL, Redis, Celery, identity-service (port 8001)