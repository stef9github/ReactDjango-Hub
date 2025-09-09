# Enhanced Development Environment Setup

Complete setup guide for ReactDjango Hub full-stack development with Claude Code optimizations.

## 🚀 **One-Command Setup (Recommended)**

### **Instant Development Environment**
```bash
# Clone and setup everything automatically
git clone <repository-url> ReactDjango-Hub
cd ReactDjango-Hub
make claude-dev-setup

# This single command:
# ✅ Sets up Python virtual environments
# ✅ Installs all dependencies (backend + frontend)  
# ✅ Configures database and runs migrations
# ✅ Seeds with test data
# ✅ Starts all development servers
# ✅ Opens browser tabs to relevant URLs
# ✅ Validates entire stack is running
```

### **Verification**
```bash
# Check development environment health
make claude-health

# Expected output:
# ✅ Backend API: http://localhost:8000/api/
# ✅ Frontend: http://localhost:5173
# ✅ PostgreSQL: Connected
# ✅ Redis: Connected
# ✅ Agent terminals: Ready
```

## 📋 **Prerequisites**

### **System Requirements**
```bash
# Required tools (auto-checked by setup script)
- Python 3.13+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose
- Git 2.40+
- Claude Code CLI
```

### **Operating System Support**
- ✅ macOS (recommended)
- ✅ Linux (Ubuntu 20.04+)
- ✅ Windows 11 (with WSL2)

## 🔧 **Manual Setup (Advanced)**

### **Backend Django Setup**

#### **Environment Configuration**
```bash
# Create backend environment
cd backend
cp .env.example .env

# Configure variables
DATABASE_URL=postgresql://user:password@localhost:5432/reactdjango_hub
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-min-50-chars
FIELD_ENCRYPTION_KEY=your-32-byte-encryption-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### **Python Environment**
```bash
# Virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt  # Development dependencies
```

#### **Database Setup**
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data
python manage.py loaddata fixtures/sample_data.json

# Verify backend
python manage.py runserver
# Test: http://localhost:8000/api/
```

### **Frontend React Setup**

#### **Node.js Environment**
```bash
cd frontend

# Install dependencies
npm install

# Verify installation
npm run typecheck
npm run lint
npm test
```

#### **Environment Configuration**
```bash
# Create .env.local
VITE_API_URL=http://localhost:8000/api
VITE_DEFAULT_LANGUAGE=fr
VITE_SUPPORTED_LANGUAGES=fr,de,en
VITE_ENVIRONMENT=development
```

#### **Development Server**
```bash
# Start development server
npm run dev
# Access: http://localhost:5173
```

## 🤖 **Claude Code Agent Setup**

### **Agent Configuration**
```bash
# Configure agent-specific git workflows
make claude-git-setup

# Setup agent documentation structure
make claude-docs-setup

# Show API documentation locations
make claude-api-docs
```

### **Worktree Configuration**
```bash
# Setup parallel development worktrees
git worktree add ../ReactDjango-Hub-worktrees/backend-dev main
git worktree add ../ReactDjango-Hub-worktrees/frontend-dev main

# Verify worktrees
git worktree list
```

### **Launch Claude Agents**
```bash
# Start all agents in parallel
make claude-agents

# This opens:
# 🔧 Backend Agent in backend-dev worktree
# 🎨 Frontend Agent in frontend-dev worktree
# 📚 API documentation references
# 💡 Scoped commit instructions
```

### **Agent-Specific Commands**

#### **Backend Agent (in backend-dev worktree)**
```bash
# Scoped backend commits
git bcommit "feat: add user authentication with RGPD compliance"

# Backend-specific operations
python manage.py test
make claude-format  # Backend formatting
make claude-security  # Security scan
make rgpd-check  # Data protection compliance
```

#### **Frontend Agent (in frontend-dev worktree)**
```bash
# Scoped frontend commits
git fcommit "feat: add user dashboard with French-first UI"

# Frontend-specific operations
npm test
npm run lint
npm run typecheck
npm run build
```

## 🐳 **Docker Development (Alternative)**

### **Complete Docker Setup**
```bash
# Start development environment
make dev

# This starts:
# - PostgreSQL database
# - Redis cache
# - Django backend with hot reloading
# - React frontend with hot reloading
```

### **Docker Commands**
```bash
# Environment management
make dev              # Start development
make stop             # Stop all services
make clean            # Clean up containers

# Production deployment
make prod-up          # Start production environment
make prod-down        # Stop production

# Monitoring
make docker-logs      # View service logs
make docker-health    # Check service health
```

## 🧪 **Testing & Quality Assurance**

### **Automated Testing**
```bash
# Complete test suite
make test-all

# Backend tests
python manage.py test
pytest --cov=apps

# Frontend tests  
npm test
npm run test:coverage

# Cross-agent integration tests
make test-integration
```

### **Code Quality**
```bash
# Comprehensive quality check
make claude-quality

# Individual checks
make claude-format    # Code formatting
make claude-security  # Security scan
make rgpd-check      # RGPD compliance
make i18n-validate   # Translation consistency
```

## 🔒 **Security & Compliance**

### **Data Protection Setup**
```python
# Encrypted fields for sensitive data
from apps.core.encryption import EncryptedTextField

class UserProfile(BaseModel):
    name = models.CharField(max_length=100)
    sensitive_data = EncryptedTextField(blank=True, null=True)
    
    class Meta:
        # RGPD compliance metadata
        rgpd_sensitive = True
        retention_period = timedelta(days=365*3)  # 3 years
```

### **Audit Logging**
```python
# Automatic audit trails
from apps.core.compliance import RGPDMixin

class UserProfile(BaseModel, RGPDMixin):
    # Automatic audit logging for all data access
    # RGPD compliance methods auto-generated
    pass
```

## 🌍 **Internationalization Setup**

### **Multi-Language Configuration**
```python
# Django settings
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
LANGUAGES = [
    ('fr', 'Français'),    # Primary language
    ('de', 'Deutsch'),     # Secondary language
    ('en', 'English'),     # Tertiary language
]
USE_I18N = True
USE_L10N = True
USE_TZ = True
```

### **Translation Management**
```bash
# Generate translation files
python manage.py makemessages -l fr -l de -l en

# Compile translations
python manage.py compilemessages

# Frontend translations
npm run extract-messages  # Extract new translatable text
npm run validate-i18n     # Validate translation consistency
```

## 📊 **Development Monitoring**

### **Health Checks**
```bash
# System health validation
make claude-health

# Service-specific checks
curl http://localhost:8000/api/health/  # Backend API
curl http://localhost:5173/health       # Frontend
```

### **Performance Monitoring**
```bash
# Development performance check
make perf-check

# Database performance
python manage.py dbshell
# \timing on
# SELECT * FROM django_session LIMIT 10;

# Frontend bundle analysis
npm run analyze
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Port Conflicts**
```bash
# Check port usage
lsof -i :5173 :8000 :5432 :6379

# Kill conflicting processes
make stop
make clean
```

#### **Database Connection Issues**
```bash
# Reset database
make stop
docker volume rm reactdjango-hub_postgres_data
make dev
make migrate
```

#### **Agent Terminal Issues**
```bash
# Reset agent terminals
pkill -f claude
make claude-agents
```

#### **Permission Issues (macOS)**
```bash
# Fix file permissions
sudo chown -R $USER:staff .
chmod +x .claude/commands/*.sh
```

### **Environment Reset**
```bash
# Complete environment reset
make clean
rm -rf backend/venv
rm -rf frontend/node_modules
make claude-dev-setup
```

## ⚡ **Performance Optimization**

### **Development Speed**
```bash
# Parallel dependency installation
make install-parallel

# Pre-commit hooks for fast validation
make setup-hooks

# Development server optimization
export DJANGO_DEVELOPMENT=1
export NODE_ENV=development
```

### **Resource Usage**
```bash
# Monitor resource usage
make resource-monitor

# Optimize development containers
make docker-optimize
```

## 📚 **Next Steps**

### **After Setup**
1. **Verify Installation**: `make claude-health`
2. **Run Tests**: `make test-all`  
3. **Start Development**: `make claude-agents`
4. **Read Documentation**: Browse `docs/` directory

### **Development Workflow**
1. **Choose Agent**: Backend or Frontend development
2. **Use Generators**: `make generate-model User` or `make generate-component UserCard`
3. **Scoped Commits**: `git bcommit` or `git fcommit`
4. **Quality Checks**: `make claude-quality`

### **Advanced Features**
- **Code Generators**: See `docs/development/code-generators.md`
- **Quality Assurance**: See `docs/development/automated-qa.md`
- **Agent Workflows**: See `docs/development/claude-workflow-guide.md`

---

🎯 **This enhanced setup provides a complete Claude Code-optimized development environment with automated quality assurance, agent coordination, and comprehensive tooling for full-stack development.**