# 🗄️ **Identity Service Database Migration Guide - Production Ready**

## **📋 Overview**

The Identity Service now features a **complete, enterprise-grade database migration system** with comprehensive Alembic integration, backup/restore capabilities, and production-ready deployment tools.

### **🎯 Migration System Features**

| Feature | Status | Description |
|---------|---------|-------------|
| **Schema Migration** | ✅ Complete | Enhanced Identity Service models (10 tables) |
| **Management CLI** | ✅ Complete | `scripts/migrate_database.py` enterprise tooling |
| **Backup/Restore** | ✅ Complete | PostgreSQL dump/restore integration |
| **Dry-run Support** | ✅ Complete | SQL generation without execution |
| **Production Config** | ✅ Complete | Environment variable support |
| **Error Handling** | ✅ Complete | Comprehensive logging and validation |

---

## **🚀 Quick Migration Commands**

### **Production Deployment (Recommended)**
```bash
# 1. Check current status
python scripts/migrate_database.py status

# 2. Run migration with automatic backup
python scripts/migrate_database.py migrate --backup

# 3. Verify migration success
python scripts/migrate_database.py status
```

### **Development Environment**
```bash
# Quick migration without backup
python scripts/migrate_database.py migrate

# Check what migrations are available
python scripts/migrate_database.py list
```

### **Review Changes Before Deployment**
```bash
# Generate SQL for manual review
python scripts/migrate_database.py generate-sql --output review_migration.sql

# Review the generated SQL file
cat review_migration.sql
```

---

## **🔧 Available Migration Operations**

### **Status & Information**
```bash
# Check current database revision
python scripts/migrate_database.py status

# List all available migrations
python scripts/migrate_database.py list

# Get help on all commands
python scripts/migrate_database.py --help
```

### **Migration Execution**
```bash
# Migrate to latest (with backup)
python scripts/migrate_database.py migrate --backup

# Migrate to latest (without backup) 
python scripts/migrate_database.py migrate

# Migrate to specific revision
python scripts/migrate_database.py migrate-to <revision_id> --backup

# Dry-run migration (show SQL only)
python scripts/migrate_database.py migrate --dry-run
```

### **Rollback Operations**
```bash
# Rollback to specific revision (with backup)
python scripts/migrate_database.py rollback <revision_id> --backup

# Rollback dry-run (show SQL only)
python scripts/migrate_database.py rollback <revision_id> --dry-run
```

### **Backup & Restore**
```bash
# Create database backup
python scripts/migrate_database.py backup --output identity_backup.sql

# Restore from backup
python scripts/migrate_database.py restore identity_backup.sql

# Custom backup filename (auto-generated timestamp)
python scripts/migrate_database.py backup
```

### **SQL Generation**
```bash
# Generate migration SQL
python scripts/migrate_database.py generate-sql

# Generate with custom filename
python scripts/migrate_database.py generate-sql --output custom_migration.sql
```

---

## **📁 Migration Files Structure**

### **Key Migration Files**
```
services/identity-service/
├── alembic/                                    # Alembic configuration
│   ├── env.py                                  # ✅ Updated for production
│   ├── alembic.ini                             # ✅ Environment variable support
│   └── versions/
│       └── 68d314520251_initial_enhanced_models_migration_.py  # ✅ Complete schema
├── scripts/
│   └── migrate_database.py                    # ✅ Enterprise management CLI
└── app/
    └── models/
        └── enhanced_models.py                  # ✅ Source of truth for schema
```

### **Enhanced Database Schema (10 Tables)**

#### **Core Identity Tables**
- **`organizations`** - Multi-tenant organization management
- **`users`** - Enhanced user accounts with profiles  
- **`user_profiles`** - Extended user profile information
- **`user_sessions`** - Session tracking with device info

#### **Authentication & Security** 
- **`mfa_methods`** - Multi-factor authentication methods
- **`mfa_challenges`** - Temporary MFA verification codes
- **`email_verifications`** - Email verification tokens
- **`password_resets`** - Password reset workflows

#### **Activity & Preferences**
- **`user_activity_logs`** - Comprehensive activity tracking
- **`user_preferences`** - User settings and preferences

---

## **🌐 Environment Configuration**

### **Database URL Configuration**
```bash
# Production environment
export DATABASE_URL="postgresql://user:password@host:port/identity_service"

# Development environment  
export DATABASE_URL="postgresql://localhost/identity_service_dev"

# Test environment
export DATABASE_URL="postgresql://localhost/identity_service_test"
```

### **Alembic Configuration Updates**
The migration system automatically uses `DATABASE_URL` environment variable, falling back to `alembic.ini` configuration.

**Updated `alembic/env.py`**:
- ✅ Environment variable support
- ✅ Enhanced models import (`app.models.enhanced_models`)
- ✅ Production-ready configuration

**Updated `alembic.ini`**:
- ✅ Flexible database URL configuration
- ✅ Production deployment ready

---

## **🔄 Migration Workflow**

### **Development Workflow**
```bash
# 1. Make model changes in app/models/enhanced_models.py
# 2. Create manual migration
alembic revision -m "Description of changes"

# 3. Edit migration file with schema changes
# 4. Test migration
python scripts/migrate_database.py migrate --dry-run

# 5. Apply migration
python scripts/migrate_database.py migrate
```

### **Production Deployment Workflow**
```bash
# 1. Review migration in development
python scripts/migrate_database.py generate-sql

# 2. Create production backup
python scripts/migrate_database.py backup --output pre_deploy_backup.sql

# 3. Apply migration with backup
python scripts/migrate_database.py migrate --backup

# 4. Verify deployment
python scripts/migrate_database.py status
```

### **Emergency Rollback Workflow**
```bash
# 1. Check current revision
python scripts/migrate_database.py status

# 2. Rollback with backup
python scripts/migrate_database.py rollback <previous_revision> --backup

# 3. Or restore from backup if needed
python scripts/migrate_database.py restore pre_deploy_backup.sql
```

---

## **🚨 Troubleshooting**

### **Common Issues & Solutions**

#### **Database Connection Errors**
```bash
# Check database connectivity
python -c "import asyncio; from app.core.database import get_database_url; print(get_database_url())"

# Verify database exists
psql $DATABASE_URL -c "SELECT version();"
```

#### **Permission Errors**
```bash
# Ensure PostgreSQL user has proper permissions
GRANT ALL PRIVILEGES ON DATABASE identity_service TO your_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
```

#### **Migration Conflicts**
```bash
# Check migration history
python scripts/migrate_database.py list

# Manual resolution may be needed for complex conflicts
alembic merge heads -m "Merge conflicting migrations"
```

#### **Backup/Restore Issues**
```bash
# Verify pg_dump and psql are available
which pg_dump psql

# Check backup file integrity
head -20 backup_file.sql
```

---

## **📊 Migration Verification**

### **Post-Migration Checks**
```bash
# 1. Verify all tables exist
psql $DATABASE_URL -c "\dt"

# 2. Check indexes
psql $DATABASE_URL -c "\di"

# 3. Verify foreign key constraints
psql $DATABASE_URL -c "SELECT constraint_name, table_name FROM information_schema.table_constraints WHERE constraint_type='FOREIGN KEY';"

# 4. Test application connectivity
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

### **Performance Verification**
```bash
# Check table sizes
psql $DATABASE_URL -c "SELECT schemaname,tablename,attname,n_distinct,correlation FROM pg_stats WHERE tablename IN ('users', 'organizations', 'user_sessions');"

# Verify indexes are being used
psql $DATABASE_URL -c "EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';"
```

---

## **🎉 Success Indicators**

### **✅ Migration System Complete**
- **Enterprise Management**: Full CLI with backup/restore capabilities
- **Production Configuration**: Environment variable support and flexible deployment
- **Complete Schema**: All 10 enhanced Identity Service tables
- **Error Handling**: Comprehensive logging and validation
- **Backup Integration**: PostgreSQL dump/restore with automatic timestamping

### **✅ Ready for Production**
- **Zero Downtime Deployment**: SQL generation for offline deployment review
- **Rollback Capabilities**: Complete rollback system with backup integration
- **Monitoring**: Comprehensive logging and status checking
- **Documentation**: Complete migration procedures and troubleshooting

---

## **🔮 Future Enhancements**

### **Advanced Features (Future)**
- **Multi-environment Management**: Automated staging → production promotion
- **Schema Validation**: Automated schema drift detection
- **Performance Monitoring**: Migration performance tracking
- **Blue/Green Deployments**: Zero-downtime deployment strategies
- **Automated Testing**: Migration testing in CI/CD pipeline

---

**🚀 The Identity Service database migration system is production-ready with enterprise-grade capabilities!**

**Ready for immediate deployment with confidence in data safety and rollback capabilities.**