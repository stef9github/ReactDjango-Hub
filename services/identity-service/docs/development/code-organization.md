# Code Organization Guide

## 🏗️ **Clean Architecture Overview**

The Auth Service follows a **clean architecture** pattern with strict layer separation:

```
┌─────────────────┐
│   API Layer     │  ← app/api/v1/*.py (FastAPI routes)
├─────────────────┤
│ Business Layer  │  ← app/services/*.py (business logic)  
├─────────────────┤
│   Data Layer    │  ← app/models/*.py (SQLAlchemy models)
├─────────────────┤
│   Core Layer    │  ← app/core/*.py (config, database, security)
└─────────────────┘
```

## 📁 **Directory Structure**

### **Organized Structure (Current)**
```
app/
├── api/                    # API Layer (FastAPI routes)
│   ├── deps.py            # Dependency injection
│   └── v1/                # API version 1
│       ├── auth.py        # Authentication endpoints
│       ├── users.py       # User management endpoints
│       ├── organizations.py # Organization endpoints
│       └── mfa.py         # MFA endpoints
├── core/                  # Infrastructure Layer
│   ├── config.py         # Configuration settings
│   ├── database.py       # Database connection
│   └── security.py       # Security utilities
├── models/               # Data Layer
│   └── enhanced_models.py # All SQLAlchemy models
├── schemas/              # Validation Layer
│   ├── auth.py          # Auth request/response schemas
│   ├── user.py          # User schemas
│   ├── organization.py  # Organization schemas
│   └── mfa.py           # MFA schemas
├── services/            # Business Logic Layer
│   ├── auth_service.py  # Core authentication
│   ├── user_service.py  # User & organization management
│   ├── mfa_service.py   # Multi-factor authentication
│   └── email_service.py # Email functionality
└── utils/               # Utilities
    └── messaging.py     # Event publishing
```

## 🔧 **Layer Responsibilities**

### **API Layer (`app/api/v1/*.py`)**
**Purpose**: HTTP request handling, input validation, response formatting

**Rules**:
- ✅ Keep route handlers thin (business logic belongs in services)
- ✅ Use dependency injection for services
- ✅ Return Pydantic response models
- ❌ NO direct database access
- ❌ NO business logic in routes

```python
# ✅ GOOD: Thin route handler
@router.post("/users/profile", response_model=UserProfileResponse)
async def create_user_profile(
    request: CreateUserProfileRequest,
    user_service: UserManagementService = Depends(get_user_service)
):
    return await user_service.create_complete_user(request.email, request.dict())

# ❌ BAD: Business logic in route
@router.post("/users/profile")
async def create_user_profile(request: CreateUserProfileRequest):
    # Don't do database operations here!
    user = User(email=request.email)
    session.add(user)
    # Business logic should be in service
```

### **Services Layer (`app/services/*.py`)**
**Purpose**: Business logic, data processing, external service integration

**Rules**:
- ✅ Contains ALL business logic
- ✅ Handles database operations
- ✅ Manages external service calls
- ✅ Implements domain rules
- ❌ NO FastAPI dependencies (Request, Response, etc.)
- ❌ NO schema imports (use native Python types)

```python
# ✅ GOOD: Service with business logic
class UserManagementService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_complete_user(self, email: str, profile_data: dict) -> dict:
        # Business logic here
        if await self._email_exists(email):
            raise ValueError("Email already exists")
        
        # Create user with profile
        user = await self._create_user_with_profile(email, profile_data)
        return self._format_user_response(user)

# ❌ BAD: Service importing schemas
from app.schemas.user import UserProfileResponse  # Don't do this!
```

### **Models Layer (`app/models/*.py`)**
**Purpose**: Data structure definitions, database relationships

**Rules**:
- ✅ Only SQLAlchemy model definitions
- ✅ Database relationships and constraints
- ✅ Basic model methods (if needed)
- ❌ NO business logic
- ❌ NO external service calls

```python
# ✅ GOOD: Clean model definition
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user")
    
    # Simple utility method is OK
    @property
    def display_name(self) -> str:
        return self.profile.display_name if self.profile else self.email

# ❌ BAD: Business logic in model
class User(Base):
    def send_welcome_email(self):  # Don't do this!
        # Business logic belongs in services
```

### **Schemas Layer (`app/schemas/*.py`)**
**Purpose**: Request/response validation, data serialization

**Rules**:
- ✅ Pure Pydantic models
- ✅ Input validation and serialization
- ✅ API contract definitions
- ❌ NO app imports (completely independent)
- ❌ NO business logic

```python
# ✅ GOOD: Pure Pydantic schema
class CreateUserProfileRequest(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    password: str = Field(..., min_length=8)

# ❌ BAD: Schema importing app modules
from app.services.user_service import UserManagementService  # Don't do this!
```

### **Core Layer (`app/core/*.py`)**
**Purpose**: Infrastructure, configuration, utilities

**Rules**:
- ✅ Configuration management
- ✅ Database connection setup
- ✅ Security utilities
- ✅ Minimal dependencies

## 🔄 **Data Flow Pattern**

```
HTTP Request
     ↓
API Layer (FastAPI route)
     ↓
Pydantic Schema (validation)
     ↓
Service Layer (business logic)
     ↓
Model Layer (database operations)
     ↓
Database
     ↓
Model Layer (data retrieval)
     ↓
Service Layer (data processing)
     ↓
API Layer (response formatting)
     ↓
HTTP Response
```

## 📋 **Import Rules**

### **Allowed Import Patterns**
```python
# API Layer can import:
from app.api.deps import *           # Dependencies
from app.schemas.* import *          # Request/response models
from app.services.* import *         # Business logic services

# Services Layer can import:
from app.models.* import *           # Database models
from app.core.* import *             # Config, database, security
from app.utils.* import *            # Utilities

# Schemas Layer can import:
from pydantic import *               # Pydantic only
from typing import *                 # Standard library only
from datetime import *               # Standard library only

# Models Layer can import:
from app.core.database import Base   # Database base class
from sqlalchemy import *             # SQLAlchemy
```

### **Forbidden Import Patterns**
```python
# ❌ API Layer CANNOT import:
from app.models.* import *           # Use services instead
from app.core.database import *      # Use deps.py

# ❌ Services Layer CANNOT import:
from app.api.* import *              # Services are lower level
from app.schemas.* import *          # Use native Python types

# ❌ Schemas Layer CANNOT import:
from app.* import *                  # Must be independent

# ❌ Models Layer CANNOT import:
from app.services.* import *         # Models are lower level
from app.api.* import *              # Models don't know about API
```

## 🔧 **Development Patterns**

### **Adding New Feature**
1. **Define API contract** → Add schemas in `app/schemas/`
2. **Create business logic** → Add service methods in `app/services/`
3. **Add database models** → Update `app/models/enhanced_models.py`
4. **Expose API endpoint** → Add route in `app/api/v1/`
5. **Test integration** → Add tests in `tests/`

### **Dependency Injection Pattern**
```python
# deps.py - Centralized dependency management
async def get_user_service(session: AsyncSession = Depends(get_session)) -> UserManagementService:
    return UserManagementService(session)

# API route - Clean dependency injection
@router.post("/users")
async def create_user(
    request: CreateUserRequest,
    user_service: UserManagementService = Depends(get_user_service),
    current_user: dict = Depends(get_current_user)
):
    return await user_service.create_user(request.dict(), current_user["user_id"])
```

## 🛠️ **Organization Maintenance**

### **Automated Validation**
The organization maintenance system automatically checks:
- ✅ Directory structure compliance
- ✅ Import pattern validation
- ✅ Layer separation rules
- ✅ File naming conventions
- ✅ Circular import detection

### **Daily Workflow**
```bash
# Check organization (run daily)
python3 scripts/maintain_organization.py

# Auto-fix common issues
python3 scripts/maintain_organization.py --fix

# Generate detailed report
python3 scripts/maintain_organization.py --report
```

### **Pre-commit Integration**
```bash
# Setup automatic validation
python3 scripts/setup_pre_commit.py

# Now organization is checked automatically before commits
git commit -m "Add new feature"  # Runs organization check
```

## ✨ **Benefits of This Organization**

1. **🔍 Clear Separation of Concerns** - Each layer has a single responsibility
2. **🔄 Easy Testing** - Business logic isolated in services
3. **📈 Scalable** - Add features without breaking existing code
4. **🛠️ Maintainable** - Clear patterns for where code belongs
5. **🤝 Team Friendly** - Multiple developers can work without conflicts
6. **🔒 Secure** - Security concerns properly layered
7. **📖 Self-Documenting** - Code structure explains the architecture

This organization ensures the Auth Service remains **clean, maintainable, and scalable** as it grows! 🚀