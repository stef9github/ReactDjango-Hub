# Auth Service - Database Schema Architecture

## 🗄️ **Database Design Overview**

The Auth Service uses PostgreSQL 17 with SQLAlchemy 2.0 async ORM, designed for high performance, data integrity, and comprehensive audit trails.

## 📊 **Database Schema**

### **Core Tables (4 Primary Tables)**

```sql
-- Main user accounts table
CREATE TABLE users_simple (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    status VARCHAR(30) DEFAULT 'pending_verification',
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    phone_number VARCHAR(20),
    bio TEXT,
    avatar_url VARCHAR(500),
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    last_login_at TIMESTAMP,
    password_changed_at TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

-- Email verification workflow
CREATE TABLE email_verifications_simple (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users_simple(id),
    email VARCHAR(255) NOT NULL,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    verification_type VARCHAR(30) DEFAULT 'registration',
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

-- JWT session tracking
CREATE TABLE user_sessions_simple (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users_simple(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE NOT NULL,
    device_name VARCHAR(255),
    device_type VARCHAR(50),
    user_agent TEXT,
    ip_address VARCHAR(45),
    country VARCHAR(100),
    region VARCHAR(100),
    city VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_activity TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

-- Comprehensive audit trail
CREATE TABLE user_activities_simple (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users_simple(id),
    activity_type VARCHAR(50) NOT NULL,
    description TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    activity_metadata TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🔗 **Entity Relationships**

### **Relationship Diagram**
```
┌─────────────────────┐
│     users_simple    │
│ (Primary Entity)    │
├─────────────────────┤
│ id (UUID)           │──┐
│ email (UNIQUE)      │  │
│ password_hash       │  │
│ is_verified         │  │
│ status              │  │
│ ...profile_data     │  │
│ created_at          │  │
└─────────────────────┘  │
                         │
        ┌────────────────┼────────────────┬────────────────┐
        │                │                │                │
        ▼                ▼                ▼                ▼
┌─────────────────┐ ┌────────────────┐ ┌───────────────┐ ┌─────────────────┐
│ email_          │ │ user_sessions_ │ │ user_         │ │ (Future Tables) │
│ verifications_  │ │ simple         │ │ activities_   │ │ - mfa_methods   │
│ simple          │ │                │ │ simple        │ │ - organizations │
├─────────────────┤ ├────────────────┤ ├───────────────┤ │ - roles         │
│ user_id (FK)    │ │ user_id (FK)   │ │ user_id (FK)  │ │ - permissions   │
│ token_hash      │ │ session_token  │ │ activity_type │ └─────────────────┘
│ verification_   │ │ refresh_token  │ │ description   │
│ type            │ │ device_info    │ │ metadata      │
│ expires_at      │ │ expires_at     │ │ created_at    │
└─────────────────┘ └────────────────┘ └───────────────┘
```

### **Foreign Key Relationships**
```python
# One-to-Many Relationships
User (1) ←──── (N) EmailVerification
User (1) ←──── (N) UserSession  
User (1) ←──── (N) UserActivity

# Cascading Rules
ON DELETE CASCADE: EmailVerification, UserSession, UserActivity
ON UPDATE CASCADE: All foreign keys
```

## 🔍 **SQLAlchemy Models**

### **Core Model Pattern**
```python
from sqlalchemy import Column, String, Boolean, DateTime, UUID, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users_simple"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    status = Column(String(30), default=UserStatus.PENDING_VERIFICATION)
    
    # Profile Information
    first_name = Column(String(150))
    last_name = Column(String(150))
    phone_number = Column(String(20))
    bio = Column(Text)
    avatar_url = Column(String(500))
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    
    # Security & Audit
    last_login_at = Column(DateTime)
    password_changed_at = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)  # Soft delete
    
    # Relationships (defined but not enforced for performance)
    # email_verifications = relationship("EmailVerification", back_populates="user")
    # sessions = relationship("UserSession", back_populates="user")
    # activities = relationship("UserActivity", back_populates="user")
```

### **Related Models**
```python
class EmailVerification(Base):
    __tablename__ = "email_verifications_simple"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users_simple.id'), nullable=False)
    email = Column(String(255), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    verification_type = Column(String(30), default=VerificationType.REGISTRATION)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)

class UserSession(Base):
    __tablename__ = "user_sessions_simple"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users_simple.id'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Device Information
    device_name = Column(String(255))
    device_type = Column(String(50))
    user_agent = Column(Text)
    ip_address = Column(String(45))
    country = Column(String(100))
    region = Column(String(100))
    city = Column(String(100))
    
    # Session Management
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)

class UserActivity(Base):
    __tablename__ = "user_activities_simple"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users_simple.id'), nullable=False)
    activity_type = Column(String(50), nullable=False)
    description = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    activity_metadata = Column(Text)  # JSON stored as text
    created_at = Column(DateTime, default=func.now())
```

## 🔒 **Security & Performance Indexes**

### **Primary Indexes**
```sql
-- Unique constraints for security
CREATE UNIQUE INDEX ix_users_simple_email ON users_simple(email);
CREATE UNIQUE INDEX ix_email_verifications_simple_token_hash ON email_verifications_simple(token_hash);
CREATE UNIQUE INDEX ix_user_sessions_simple_session_token ON user_sessions_simple(session_token);
CREATE UNIQUE INDEX ix_user_sessions_simple_refresh_token ON user_sessions_simple(refresh_token);

-- Performance indexes
CREATE INDEX ix_users_simple_status_verified ON users_simple(status, is_verified);
CREATE INDEX ix_user_sessions_simple_user_active ON user_sessions_simple(user_id, is_active);
CREATE INDEX ix_user_activities_simple_user_time ON user_activities_simple(user_id, created_at DESC);
CREATE INDEX ix_email_verifications_simple_expires ON email_verifications_simple(expires_at);
```

### **Query Optimization Patterns**
```sql
-- Fast user lookup by email
SELECT id, password_hash, is_verified, status 
FROM users_simple 
WHERE email = ? AND deleted_at IS NULL;

-- Active sessions for user
SELECT session_token, expires_at, device_name, ip_address
FROM user_sessions_simple 
WHERE user_id = ? AND is_active = TRUE AND expires_at > NOW();

-- Recent user activity
SELECT activity_type, description, created_at
FROM user_activities_simple 
WHERE user_id = ? 
ORDER BY created_at DESC 
LIMIT 10;
```

## 📈 **Data Migration Strategy**

### **Alembic Migration Management**
```python
# Example migration structure
"""Add user profile enhancements

Revision ID: 12345abcde
Revises: 974799e38366
Create Date: 2025-09-09 10:26:59.520371
"""

def upgrade():
    # Add new columns
    op.add_column('users_simple', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('users_simple', sa.Column('avatar_url', sa.String(500), nullable=True))
    
    # Add indexes for performance
    op.create_index('ix_users_simple_status_verified', 'users_simple', ['status', 'is_verified'])

def downgrade():
    # Remove indexes
    op.drop_index('ix_users_simple_status_verified')
    
    # Remove columns
    op.drop_column('users_simple', 'avatar_url')
    op.drop_column('users_simple', 'bio')
```

### **Migration Commands**
```bash
# Create new migration
alembic revision --autogenerate -m "Add user profile enhancements"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check current version
alembic current

# Show migration history
alembic history --verbose
```

## 🔄 **Data Lifecycle Management**

### **Soft Delete Pattern**
```python
# Soft delete implementation
async def soft_delete_user(user_id: str):
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(deleted_at=datetime.utcnow())
    )
    
# Query excluding soft-deleted records
stmt = select(User).where(User.deleted_at.is_(None))
```

### **Data Retention Policies**
```sql
-- Clean up expired email verifications (monthly)
DELETE FROM email_verifications_simple 
WHERE expires_at < NOW() - INTERVAL '30 days';

-- Clean up expired sessions (daily)
DELETE FROM user_sessions_simple 
WHERE expires_at < NOW() - INTERVAL '7 days';

-- Archive old user activities (quarterly)
-- Move activities older than 1 year to archive table
```

## 🎯 **Performance Characteristics**

### **Expected Query Performance**
- **User Login**: `< 50ms` (indexed email lookup + password verification)
- **Session Validation**: `< 10ms` (indexed token lookup)
- **User Profile**: `< 30ms` (single table query with indexes)
- **Activity Logging**: `< 5ms` (insert with minimal indexes)

### **Scaling Considerations**
- **Connection Pooling**: AsyncPG with connection pool (10-20 connections)
- **Query Optimization**: All frequent queries use proper indexes
- **Horizontal Scaling**: Read replicas for session validation
- **Caching**: Redis for frequently accessed user data

### **Storage Estimates**
```
Users Table: ~500 bytes per user
Sessions Table: ~400 bytes per session (avg 2 sessions per user)
Activities Table: ~300 bytes per activity (avg 10 activities per user/day)
Email Verifications: ~200 bytes per verification (1 per user typically)

For 100,000 users:
- Users: ~50 MB
- Sessions: ~80 MB  
- Activities (1 year): ~1.1 GB
- Verifications: ~20 MB
Total: ~1.25 GB (without indexes, approximately 2x with indexes)
```

## 🔮 **Future Schema Evolution**

### **Planned Enhancements**
```sql
-- Multi-factor authentication
CREATE TABLE mfa_methods (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users_simple(id),
    method_type VARCHAR(20), -- 'email', 'sms', 'totp', 'backup_codes'
    method_data TEXT, -- encrypted method-specific data
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Organization management (multi-tenancy)
CREATE TABLE organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    settings TEXT, -- JSON configuration
    created_at TIMESTAMP DEFAULT NOW()
);

-- Role-based access control
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    permissions TEXT -- JSON array of permissions
);

CREATE TABLE user_roles (
    user_id UUID REFERENCES users_simple(id),
    role_id UUID REFERENCES roles(id),
    organization_id UUID REFERENCES organizations(id),
    granted_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id, organization_id)
);
```

### **Migration Strategy for Extensions**
1. **Backward Compatibility**: All new columns nullable initially
2. **Feature Flags**: Enable new features gradually
3. **Data Migration**: Populate new structures from existing data
4. **Performance Testing**: Validate query performance with new schema
5. **Rollback Plan**: Ensure safe rollback for each migration

---

**This database schema provides a robust foundation for authentication services with comprehensive audit trails, performance optimization, and clear evolution paths for future enhancements.**