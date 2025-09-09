# Auth Service Maintenance Scripts

## 🛠️ **Organization Maintenance System**

This directory contains automated scripts to maintain code quality, organization, and development workflow for the Auth Service.

## 📋 **Available Scripts**

### **1. Organization Maintenance** (`maintain_organization.py`)
**Purpose**: Validates and maintains proper code organization

**Features**:
- ✅ **Directory Structure Validation** - Ensures clean architecture compliance
- ✅ **Import Organization** - Validates proper layer separation (API → Services → Models)
- ✅ **Code Organization** - Checks FastAPI patterns, service structure
- ✅ **File Naming** - Validates snake_case conventions
- ✅ **Circular Import Detection** - Prevents dependency cycles
- ✅ **Auto-fix Capabilities** - Automatically resolves common issues

**Usage**:
```bash
# Check organization
python3 scripts/maintain_organization.py

# Auto-fix issues
python3 scripts/maintain_organization.py --fix

# Generate detailed report
python3 scripts/maintain_organization.py --report
```

### **2. Code Quality Checker** (`code_quality_check.py`)
**Purpose**: Validates code quality and best practices

**Features**:
- ✅ **Style Validation** - Line length, formatting, documentation coverage
- ✅ **Complexity Analysis** - Function/class length, cyclomatic complexity
- ✅ **Security Patterns** - Detects hardcoded secrets, unsafe functions
- ✅ **Performance** - Identifies anti-patterns and inefficiencies
- ✅ **Error Handling** - Validates exception handling best practices
- ✅ **External Tools** - Integrates with flake8, mypy, bandit

**Usage**:
```bash
# Check code quality
python3 scripts/code_quality_check.py

# Check specific path
python3 scripts/code_quality_check.py --path app/services/
```

### **3. Pre-commit Setup** (`setup_pre_commit.py`)
**Purpose**: Sets up development automation and CI/CD integration

**Features**:
- ✅ **Git Integration** - Pre-commit hooks for automatic validation
- ✅ **Makefile Generation** - Convenient development commands
- ✅ **GitHub Actions** - CI/CD workflow for pull requests
- ✅ **VSCode Integration** - IDE tasks for development workflow

**Usage**:
```bash
# Setup automation (run once)
python3 scripts/setup_pre_commit.py

# Use generated Makefile commands
make -f Makefile.auth check-org
make -f Makefile.auth fix-org
make -f Makefile.auth report-org
```

## 🚀 **Quick Start**

### **Initial Setup (One-time)**
```bash
# 1. Setup automation
python3 scripts/setup_pre_commit.py

# 2. Fix any existing issues
python3 scripts/maintain_organization.py --fix

# 3. Verify everything is good
python3 scripts/maintain_organization.py
python3 scripts/code_quality_check.py
```

### **Daily Development Workflow**
```bash
# Before starting development
make -f Makefile.auth check-org

# During development (as needed)
python3 scripts/maintain_organization.py --fix

# Before committing (automatic via pre-commit hooks)
git commit -m "Add new feature"  # Automatically runs checks
```

## 🔧 **Generated Automation**

After running `setup_pre_commit.py`, you'll have:

### **Makefile Commands**
```bash
make -f Makefile.auth check-org    # Check organization
make -f Makefile.auth fix-org      # Auto-fix issues
make -f Makefile.auth report-org   # Generate detailed report
make -f Makefile.auth setup-hooks  # Setup git hooks
make -f Makefile.auth dev-setup    # Complete dev environment setup
```

### **Git Pre-commit Hook**
Automatically runs before each commit:
- Organization structure validation
- Import pattern checking
- Code quality validation
- Fails commit if issues found (can bypass with `--no-verify`)

### **GitHub Actions Workflow**
Automatically runs on pull requests:
- Full organization validation
- Code quality checks
- Generates reports as artifacts on failure

### **VSCode Tasks**
Available in Command Palette:
- `Auth: Check Organization`
- `Auth: Fix Organization` 
- `Auth: Generate Report`

## 📊 **What Gets Validated**

### **Directory Structure**
```
✅ app/api/v1/*.py              - API endpoints exist
✅ app/services/*.py            - Service classes exist  
✅ app/models/enhanced_models.py - Database models exist
✅ app/schemas/*.py             - Pydantic schemas exist
✅ app/core/*.py                - Core infrastructure exists
✅ Missing __init__.py files    - Auto-created if missing
```

### **Import Organization**
```
✅ API Layer:    Can import schemas, deps, services
❌ API Layer:    Cannot import models directly
✅ Services:     Can import models, core, utils  
❌ Services:     Cannot import API or schemas
✅ Schemas:      Independent (pydantic only)
❌ Models:       Cannot import business logic
```

### **Code Quality**
```
✅ Documentation:    Docstrings for classes and functions
✅ Complexity:       Function/class length, complexity metrics
✅ Security:         No hardcoded secrets, safe patterns
✅ Performance:      No anti-patterns, efficient code
✅ Error Handling:   Proper exception handling
✅ Style:            Line length, formatting, naming
```

## 🔍 **Validation Rules**

### **Architecture Rules (Enforced)**
1. **Clean Architecture**: API → Services → Models → Core
2. **Layer Separation**: No imports violating layer boundaries
3. **Single Responsibility**: Each module has clear purpose
4. **Dependency Direction**: Higher layers depend on lower layers

### **Code Quality Rules**
1. **Documentation**: Public functions/classes must have docstrings
2. **Complexity**: Functions <50 lines, cyclomatic complexity <10
3. **Security**: No hardcoded secrets, use secure patterns
4. **Performance**: No obvious anti-patterns
5. **Style**: Follow PEP 8, max line length 88 chars

### **File Organization Rules**
1. **Naming**: snake_case for files, PascalCase for classes
2. **Structure**: Proper directory hierarchy
3. **Init Files**: Required for Python packages
4. **Imports**: Organized and minimal

## 🛡️ **Quality Gates**

### **Pre-commit Gate**
Prevents commits with:
- ❌ Organization structure violations
- ❌ Import pattern violations  
- ❌ Critical security issues
- ❌ Major code quality issues

### **CI/CD Gate**
Prevents pull request merges with:
- ❌ Any organization violations
- ❌ Code quality failures
- ❌ Missing documentation
- ❌ Test coverage drops

## 📈 **Benefits**

### **For Developers**
- 🔍 **Clear Guidelines** - Know exactly where code belongs
- 🚀 **Automated Fixes** - Common issues resolved automatically
- 📊 **Quality Feedback** - Immediate feedback on code quality
- 🛠️ **IDE Integration** - Quality checks available in editor

### **For Teams**
- 🤝 **Consistency** - All code follows same patterns
- 📖 **Self-Documenting** - Architecture is enforced and clear
- 🔄 **Scalability** - Easy to add features without breaking patterns
- 🛡️ **Quality Assurance** - Automated quality gates prevent issues

### **For Production**
- 🚀 **Reliability** - Consistent code quality
- 🔧 **Maintainability** - Clear separation of concerns
- 📈 **Scalability** - Clean architecture supports growth
- 🔒 **Security** - Automated security pattern validation

## 🎯 **Next Steps**

1. **Run Setup**: `python3 scripts/setup_pre_commit.py`
2. **Fix Issues**: `python3 scripts/maintain_organization.py --fix`
3. **Verify Quality**: `python3 scripts/code_quality_check.py`
4. **Commit Changes**: Git hooks will now automatically validate
5. **Develop Confidently**: Organization is automatically maintained!

---

**🎉 Your Auth Service now has enterprise-grade code organization and quality assurance!**