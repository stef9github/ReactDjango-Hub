-- Content Service Database Initialization Script
-- This script sets up the initial database configuration

-- Ensure UTF-8 encoding is properly set
ALTER DATABASE content_service SET client_encoding TO 'utf8';
ALTER DATABASE content_service SET timezone TO 'UTC';

-- Create extension for UUID generation if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create extension for full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create audit logging function for database changes
CREATE OR REPLACE FUNCTION audit_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        NEW.created_at = COALESCE(NEW.created_at, NOW());
        NEW.updated_at = NOW();
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        NEW.updated_at = NOW();
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Grant proper permissions to content_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO content_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO content_user;
GRANT USAGE ON SCHEMA public TO content_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO content_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO content_user;