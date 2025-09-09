# Development Setup Guide

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 17
- Redis 7+

### **1. Clone and Setup**
```bash
# Navigate to auth service
cd services/auth-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### **2. Environment Configuration**
```bash
# Copy example environment
cp .env.example .env

# Edit configuration
nano .env
```

Required environment variables:
```bash
# Database
DATABASE_URL=postgresql://auth_user:auth_pass@localhost:5432/auth_service

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key

# Email (optional for development)
SMTP_SERVER=localhost
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
```

### **3. Database Setup**
```bash
# Start database services
docker-compose -f docker-compose.yml up -d auth-db auth-redis

# Run database migrations
alembic upgrade head

# Create initial data (optional)
python scripts/setup_local.py
```

### **4. Start Development Server**
```bash
# Method 1: Organized structure (recommended)
uvicorn app.main:app --reload --port 8001

# Method 2: Root main.py (backwards compatible)
uvicorn main:app --reload --port 8001

# Method 3: Python module
python -m app.main
```

### **5. Verify Installation**
```bash
# Health check
curl http://localhost:8001/health

# API documentation
open http://localhost:8001/docs

# Alternative docs
open http://localhost:8001/redoc
```

## 🛠️ **Development Workflow**

### **Code Organization Check**
```bash
# Check organization (run daily)
python3 scripts/maintain_organization.py

# Auto-fix issues
python3 scripts/maintain_organization.py --fix

# Generate report
python3 scripts/maintain_organization.py --report
```

### **Quality Assurance**
```bash
# Code quality check
python3 scripts/code_quality_check.py

# Setup automation (one-time)
python3 scripts/setup_pre_commit.py

# Use Makefile commands
make -f Makefile.auth check-org
make -f Makefile.auth fix-org
```

### **Testing**
```bash
# Run all tests
pytest tests/ -v --cov

# Run specific test file
pytest tests/test_authentication.py -v

# Generate coverage report
pytest --cov=app --cov-report=html
```

### **Database Operations**
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Reset database
alembic downgrade base && alembic upgrade head

# Database shell
python -c "from app.core.database import *; import asyncio; asyncio.run(init_db())"
```

## 🏗️ **Project Structure**

```
services/auth-service/
├── app/                         # Main application
│   ├── api/v1/                  # API endpoints
│   ├── core/                    # Configuration & database
│   ├── models/                  # SQLAlchemy models
│   ├── schemas/                 # Pydantic schemas
│   ├── services/                # Business logic
│   └── utils/                   # Utilities
├── tests/                       # Test suite
├── scripts/                     # Maintenance scripts
├── docs/                        # Documentation
└── alembic/                     # Database migrations
```

## 🔧 **Development Tools**

### **VS Code Integration**
The service includes VS Code tasks:
- `Auth: Check Organization`
- `Auth: Fix Organization`
- `Auth: Generate Report`

### **Pre-commit Hooks**
Automatically run organization checks:
```bash
# Setup hooks (one-time)
python3 scripts/setup_pre_commit.py

# Manual commit check
python3 scripts/maintain_organization.py
```

### **Debugging**
```bash
# Enable debug mode
export DEBUG=True

# Verbose logging
export LOG_LEVEL=DEBUG

# Start with debugger
python -m pdb app/main.py
```

## 📝 **Common Tasks**

### **Adding New Endpoint**
1. Add route to appropriate `app/api/v1/*.py`
2. Create request/response schemas in `app/schemas/`
3. Implement business logic in `app/services/`
4. Add tests in `tests/`
5. Run organization check: `python3 scripts/maintain_organization.py`

### **Adding New Model**
1. Add SQLAlchemy model to `app/models/enhanced_models.py`
2. Create migration: `alembic revision --autogenerate -m "Add model"`
3. Apply migration: `alembic upgrade head`
4. Update services to use new model

### **Troubleshooting**
```bash
# Check service health
curl http://localhost:8001/health

# View logs
docker-compose logs auth-service

# Database connection test
python -c "from app.core.database import get_session; print('DB OK')"

# Redis connection test
python -c "import redis; r=redis.Redis(); r.ping(); print('Redis OK')"
```

## 🚀 **Ready for Development!**

Your auth service is now ready for development with:
- ✅ Organized project structure
- ✅ Automated quality checks
- ✅ Development server running
- ✅ Database and Redis connected
- ✅ API documentation available at `/docs`