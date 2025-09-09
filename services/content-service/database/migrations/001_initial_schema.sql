-- Initial database schema for content service
-- This migration creates all core tables and indexes

-- Create custom types
CREATE TYPE document_status AS ENUM ('active', 'processing', 'error', 'archived', 'deleted');
CREATE TYPE audit_action AS ENUM ('create', 'read', 'update', 'delete', 'share', 'unshare', 'download', 'process');
CREATE TYPE processing_job_type AS ENUM ('ocr', 'thumbnail', 'metadata_extraction', 'classification', 'virus_scan', 'text_extraction', 'entity_extraction');
CREATE TYPE job_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled', 'retrying');

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL CHECK (file_size > 0),
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    storage_path TEXT NOT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ownership & Organization
    created_by UUID NOT NULL,
    organization_id UUID NOT NULL,
    
    -- Status & Classification
    status document_status DEFAULT 'active',
    document_type VARCHAR(50),
    classification VARCHAR(20) DEFAULT 'internal',
    
    -- Searchable content & metadata
    extracted_text TEXT,
    search_vector tsvector,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Processing information
    processing_status VARCHAR(20) DEFAULT 'pending',
    ocr_completed BOOLEAN DEFAULT false,
    thumbnail_generated BOOLEAN DEFAULT false,
    
    -- Constraints
    CONSTRAINT valid_content_type CHECK (content_type ~ '^[a-z]+/[a-z0-9][a-z0-9!#$&\-\^]*$'),
    CONSTRAINT valid_classification CHECK (classification IN ('public', 'internal', 'confidential', 'restricted')),
    CONSTRAINT valid_processing_status CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))
);

-- Document versions table
CREATE TABLE document_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    
    -- Version content
    filename VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    file_size BIGINT NOT NULL CHECK (file_size > 0),
    file_hash VARCHAR(64) NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID NOT NULL,
    change_summary TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Ensure version uniqueness per document
    UNIQUE(document_id, version_number),
    CHECK (version_number > 0)
);

-- Document permissions table
CREATE TABLE document_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Permission target (user or role)
    user_id UUID,
    role_name VARCHAR(50),
    
    -- Permissions
    can_read BOOLEAN DEFAULT false,
    can_write BOOLEAN DEFAULT false,
    can_delete BOOLEAN DEFAULT false,
    can_share BOOLEAN DEFAULT false,
    can_admin BOOLEAN DEFAULT false,
    
    -- Metadata
    granted_by UUID NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Inheritance tracking
    inherited BOOLEAN DEFAULT false,
    source_type VARCHAR(50),
    source_id UUID,
    
    -- Constraints
    CONSTRAINT permission_target_check CHECK (
        (user_id IS NOT NULL AND role_name IS NULL) OR 
        (user_id IS NULL AND role_name IS NOT NULL)
    ),
    CONSTRAINT permission_granted_check CHECK (can_read OR can_write OR can_delete OR can_share OR can_admin),
    CONSTRAINT valid_expiration_check CHECK (expires_at IS NULL OR expires_at > granted_at)
);

-- Audit trail table
CREATE TABLE document_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    
    -- Action details
    action audit_action NOT NULL,
    resource_type VARCHAR(50) DEFAULT 'document',
    resource_id UUID,
    
    -- User context
    user_id UUID NOT NULL,
    organization_id UUID NOT NULL,
    session_id VARCHAR(100),
    
    -- Request context
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    
    -- Event details
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Performance tracking
    execution_time_ms INTEGER
);

-- Processing jobs table
CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Job details
    job_type processing_job_type NOT NULL,
    status job_status DEFAULT 'pending',
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    
    -- Processing details
    processor_name VARCHAR(100),
    processor_version VARCHAR(20),
    config JSONB DEFAULT '{}'::jsonb,
    
    -- Results
    result JSONB,
    error_message TEXT,
    error_details JSONB,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Retry logic
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- Webhook configuration
    webhook_url TEXT,
    webhook_headers JSONB,
    
    CHECK (retry_count >= 0),
    CHECK (max_retries >= 0)
);

-- Indexes for documents table
CREATE INDEX idx_documents_org_created ON documents(organization_id, created_at DESC);
CREATE INDEX idx_documents_created_by ON documents(created_by);
CREATE INDEX idx_documents_type ON documents(document_type) WHERE document_type IS NOT NULL;
CREATE INDEX idx_documents_status ON documents(status) WHERE status != 'active';
CREATE INDEX idx_documents_hash ON documents(file_hash);
CREATE INDEX idx_documents_metadata ON documents USING GIN(metadata);
CREATE INDEX idx_documents_search ON documents USING GIN(search_vector);
CREATE INDEX idx_documents_text ON documents USING GIN(to_tsvector('english', extracted_text)) WHERE extracted_text IS NOT NULL;

-- Indexes for document versions
CREATE INDEX idx_versions_document ON document_versions(document_id, version_number DESC);
CREATE INDEX idx_versions_created ON document_versions(created_at DESC);

-- Indexes for document permissions
CREATE INDEX idx_permissions_document ON document_permissions(document_id);
CREATE INDEX idx_permissions_user ON document_permissions(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_permissions_role ON document_permissions(role_name) WHERE role_name IS NOT NULL;
CREATE INDEX idx_permissions_granted_by ON document_permissions(granted_by);
CREATE INDEX idx_permissions_expires ON document_permissions(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_permissions_source ON document_permissions(source_type, source_id) WHERE source_type IS NOT NULL;

-- Unique constraints for permissions
CREATE UNIQUE INDEX idx_permissions_unique_user ON document_permissions(document_id, user_id) 
WHERE user_id IS NOT NULL;
CREATE UNIQUE INDEX idx_permissions_unique_role ON document_permissions(document_id, role_name) 
WHERE role_name IS NOT NULL;

-- Indexes for audit trail
CREATE INDEX idx_audit_document ON document_audit(document_id, created_at DESC);
CREATE INDEX idx_audit_user ON document_audit(user_id, created_at DESC);
CREATE INDEX idx_audit_org ON document_audit(organization_id, created_at DESC);
CREATE INDEX idx_audit_action ON document_audit(action, created_at DESC);
CREATE INDEX idx_audit_session ON document_audit(session_id);
CREATE INDEX idx_audit_request ON document_audit(request_id);
CREATE INDEX idx_audit_details ON document_audit USING GIN(details);

-- Indexes for processing jobs
CREATE INDEX idx_jobs_document ON processing_jobs(document_id);
CREATE INDEX idx_jobs_status ON processing_jobs(status, priority DESC, created_at);
CREATE INDEX idx_jobs_retry ON processing_jobs(next_retry_at) WHERE status = 'failed' AND retry_count < max_retries;
CREATE INDEX idx_jobs_type ON processing_jobs(job_type, status);
CREATE INDEX idx_jobs_created ON processing_jobs(created_at DESC);
CREATE INDEX idx_jobs_webhook ON processing_jobs(webhook_url) WHERE webhook_url IS NOT NULL;
CREATE INDEX idx_jobs_config ON processing_jobs USING GIN(config);
CREATE INDEX idx_jobs_result ON processing_jobs USING GIN(result) WHERE result IS NOT NULL;

-- Triggers and functions
CREATE OR REPLACE FUNCTION update_document_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', 
        COALESCE(NEW.filename, '') || ' ' ||
        COALESCE(NEW.original_filename, '') || ' ' ||
        COALESCE(NEW.extracted_text, '') || ' ' ||
        COALESCE(NEW.metadata->>'title', '') || ' ' ||
        COALESCE(NEW.metadata->>'description', '') || ' ' ||
        COALESCE(array_to_string(ARRAY(SELECT jsonb_array_elements_text(NEW.metadata->'tags')), ' '), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER documents_search_vector_update
    BEFORE INSERT OR UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_document_search_vector();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create initial admin permissions function
CREATE OR REPLACE FUNCTION create_document_owner_permissions()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO document_permissions (
        document_id,
        user_id,
        can_read,
        can_write,
        can_delete,
        can_share,
        can_admin,
        granted_by
    ) VALUES (
        NEW.id,
        NEW.created_by,
        true,
        true,
        true,
        true,
        true,
        NEW.created_by
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER create_owner_permissions
    AFTER INSERT ON documents
    FOR EACH ROW
    EXECUTE FUNCTION create_document_owner_permissions();