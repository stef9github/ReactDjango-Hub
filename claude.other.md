# CLAUDE.md

This file provides essential guidance to Claude Code (claude.ai/code) when working with this repository.

## ⚡ **LOCAL DEVELOPMENT FIRST** ⭐ **FASTEST WORKFLOW**

**For Speed: Always Test Locally Before Deploying**

```bash
# 1. Check environment health (instant)
npm run dev:status
./scripts/dev-status.sh

# 2. Start local development (2-3 seconds)
npm run dev:start
./scripts/dev-start.sh

# 3. Test locally (instant feedback)
# Frontend: http://localhost:3000
# Backend:  http://localhost:3001/api
# Health:   http://localhost:3001/health

# 4. Run comprehensive tests (30 seconds)
npm run dev:test
./scripts/dev-test.sh

# 5. Only deploy when ready (30s-3min)
./scripts/deploy-ec2-production.sh --selective
```

**⚡ Local Development Benefits:**

- **Instant startup**: 2-3 seconds vs 5-8 minutes for Docker
- **Hot reload**: Code changes appear immediately
- **Full debugging**: Native breakpoints and inspection
- **Real APIs**: OpenAI and Gmail integration with actual keys
- **Complete feature parity**: All production functionality available locally

**🔧 Local Development Commands:**

```bash
# Essential workflow
npm run dev:setup     # One-time setup (if not done)
npm run dev:start     # Start all services
npm run dev:status    # Check health (25+ automated tests)
npm run dev:logs      # View real-time logs
npm run dev:stop      # Clean shutdown
npm run dev:reset     # Reset database with test data
```

**🧪 Local Testing Requirements** ⭐ **ESSENTIAL**

```bash
# Comprehensive testing (includes UI/browser testing)
npm run dev:test-comprehensive  # Core + UI tests (95%+ success rate, 20+ tests)

# Individual test suites
npm run dev:test-core          # Core functionality only (100% success, 13 tests)
npm run dev:test-ui            # Headless browser tests (100% success, 11 tests)

# Test with verified user account
# Email: stef.richard@gmail.com
# Password: testPassword123!
# Reference: docs/testing/test-accounts.md

# Additional production tests
npm run test:real-upload # Dashboard with actual user
npm run test:dashboard   # Frontend components
```

**Local Testing Workflow:**

1. **Start services**: `npm run dev:start`
2. **Test authentication**: Login with stef.richard@gmail.com
3. **Test core features**: Resume upload, profile management, dashboard
4. **Run comprehensive tests**: `npm run dev:test-comprehensive` (includes headless UI testing)
5. **Verify API health**: http://localhost:3001/api/health

**🎯 Development Workflow:**

1. **Code locally** with instant feedback
2. **Test locally** with real data and APIs
3. **Deploy only when ready** using selective deployment
4. **Verify production** with health checks

## 🚀 **ESSENTIAL PROCESSES**

### **Deployment Process** ⭐ **CRITICAL**

**Production Deployment:**

```bash
# Standard deployment (all services) - Takes 5-8 minutes
./scripts/deploy-ec2-production.sh deploy

# Selective deployment (only changed services) - Takes 30s-3 minutes ⚡
./scripts/deploy-ec2-production.sh --selective

# Health check only - Takes ~30 seconds
./scripts/deploy-ec2-production.sh health
```

**⚡ Selective Deployment Benefits:**

- **Only rebuilds changed services** (uses checksums to detect changes)
- **Massive time savings**: 30 seconds if no changes vs 5-8 minutes full rebuild
- **Intelligent detection**: Compares backend/, frontend/, config/ directories
- **Safe**: Automatically falls back to full rebuild if needed

**⏱️ Deployment Timing:**

- **Health check**: ~30 seconds
- **Full deployment**: 5-8 minutes
- **Selective deployment**: 30 seconds - 3 minutes (depending on changes)
  - No changes: ~30 seconds ⚡
  - Frontend only: ~1-2 minutes
  - Backend only: ~3-5 minutes
  - All changed: Same as full deployment
- **Timeouts**: Backend build (5m), Frontend build (1m), npm install (2m)

**Manual Frontend Update (if deployment fails):**

```bash
# Build frontend with proper environment
cd frontend && VITE_API_URL=https://jobtailor.stephanerichard.com/api npm run build

# Deploy to production
rsync -avz --delete dist/ ubuntu@52.2.58.6:/home/ubuntu/jobtailor/frontend/dist/

# Restart frontend container
ssh ubuntu@52.2.58.6 "docker restart jobtailor-frontend-static"
```

### **Testing Process** ⭐ **MANDATORY**

**Before Any Commit:**

```bash
# Run comprehensive tests
./scripts/test-harness.sh regression

# Test specific functionality
npm run test:real-upload        # Dashboard upload with real account
npm run test:api-calls         # API endpoint monitoring
npm run test:dashboard         # Dashboard components
```

**Testing Infrastructure:**

- **All tests**: Centralized in `tests/utils/` (NOT in backend/frontend subdirs)
- **Container tests**: Use `docker/docker-compose.test.yml`
- **Real user testing**: Account `stef.richard@gmail.com` with password in test scripts

### **Git Commit Process** ⭐ **MANDATORY**

**Always commit after successful tasks:**

```bash
git add [files]
git commit -m "🔧 TYPE: Brief Description - Specific Issue

Detailed explanation of changes and verification.
- Result 1: status ✅
- Production: deployment confirmed ✅

**Commit Types:** 🔧 FIX, ✨ FEAT, 📚 DOCS, 🚀 DEPLOY, 🧪 TEST, 🔒 SECURITY, 🎨 STYLE

## 📋 **PROJECT ESSENTIALS**

### **Tech Stack**
- **Backend**: Node.js/TypeScript + Express + PostgreSQL + Prisma + Redis + JWT
- **Frontend**: React/TypeScript + Material-UI + Redux Toolkit
- **Infrastructure**: Docker containers on Ubuntu EC2 with SSL (Let's Encrypt)

### **Production Environment**
- **Domain**: https://jobtailor.stephanerichard.com
- **API Health**: https://jobtailor.stephanerichard.com/api/health
- **Database**: PostgreSQL 15 with all migrations applied
- **Container Network**: `jobtailor-network` (critical for service communication)

### **Key API Endpoints**
- **Authentication**: `/api/auth/login`, `/api/auth/register`
- **Resume Upload**: `/api/resumes/upload` (fixed from double /api/ prefix)
- **Health Check**: `/api/health`

## 🗂️ **FILE ORGANIZATION** ⭐ **ENFORCED**

```

JobTailor/
├── docs/ # ALL documentation (.md files)
├── scripts/ # ALL scripts (.sh, .js files)
├── tests/utils/ # CENTRALIZED test utilities (unified)
├── docker/ # Container configurations
├── config/environments/ # Environment variables
├── backend/ # Node.js/TypeScript API
└── frontend/ # React/TypeScript UI

```

**Rules:**
- ✅ **All .md files** → `docs/` (organized by category)
- ✅ **All scripts** → `scripts/` (organized by purpose)
- ✅ **Test utilities** → `tests/utils/` (centralized, NOT in backend/frontend)
- ❌ **Never scatter** documentation or scripts across random directories

## 🔧 **DEVELOPMENT GUIDELINES**

### **API Patterns**
- RESTful endpoints with JWT authentication
- Consistent error responses
- UUID primary keys with timestamps
- Bilingual field support (field + field_fr)

### **Testing Requirements** ⭐ **CRITICAL**
- **Unit tests** for services (mandatory)
- **Integration tests** for APIs (mandatory)
- **ALL tests** must work in Docker containers
- Mock external services (LinkedIn, Gmail, OpenAI)
- Maintain >80% coverage

### **Known Working Features**
- ✅ **Authentication system**: Complete with password reset
- ✅ **Resume upload & parsing**: Backend fully operational
- ✅ **Dashboard integration**: Frontend upload components working
- ✅ **Production deployment**: Docker + SSL + database migrations

## 📚 **DOCUMENTATION REFERENCES**

**Core Documentation:**
- Project structure: `docs/project-structure.md`
- API specifications: `docs/architecture/api-specification.md`
- Deployment guides: `docs/deployment/`
- Testing strategy: `docs/testing/unified-test-architecture-roadmap.md`

**Implementation Status:**
- Current features: `docs/implementation/`
- Development roadmap: `docs/development-prompts.md`

**Production Operations:**
- SSL/Domain setup: `docs/deployment/ssl-configuration.md`
- Container management: `docs/deployment/docker-operations.md`
- Database management: `docs/deployment/database-management.md`

## ⚠️ **CRITICAL REMINDERS**

1. **Always use centralized test utilities** in `tests/utils/`
2. **Run deployment script** for consistent deployments
3. **Commit after every successful task/fix**
4. **Test in Docker containers** before production
5. **Check API health** after any deployment
6. **Use proper git commit format** with co-authors

---

*For detailed technical specifications, implementation roadmaps, and historical information, see documentation in `docs/` directory.*
```
- resume to use for testing /Users/stephanerichard/Documents/CODING/JobTailor/docs/examples/2024 Stephane Richard CPO Resume    gen.pdf