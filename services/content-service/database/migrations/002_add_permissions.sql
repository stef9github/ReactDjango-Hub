-- Migration: Add Document Permission System
-- Created: 2024-09-09
-- Description: Add role-based permission system for documents

-- Create document_permissions table
CREATE TABLE IF NOT EXISTS document_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Permission target (either user or role, not both)
    user_id UUID NULL,
    role_name VARCHAR(50) NULL,
    
    -- Permission flags
    can_read BOOLEAN NOT NULL DEFAULT FALSE,
    can_write BOOLEAN NOT NULL DEFAULT FALSE,
    can_delete BOOLEAN NOT NULL DEFAULT FALSE,
    can_share BOOLEAN NOT NULL DEFAULT FALSE,
    can_admin BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Permission metadata
    granted_by UUID NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NULL,
    
    -- Inheritance and source tracking
    inherited BOOLEAN NOT NULL DEFAULT FALSE,
    source_type VARCHAR(50) NULL,
    source_id UUID NULL,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT permission_target_check CHECK (
        (user_id IS NOT NULL AND role_name IS NULL) OR 
        (user_id IS NULL AND role_name IS NOT NULL)
    ),
    CONSTRAINT permission_granted_check CHECK (
        can_read OR can_write OR can_delete OR can_share OR can_admin
    ),
    CONSTRAINT valid_expiration_check CHECK (
        expires_at IS NULL OR expires_at > granted_at
    )
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_permissions_document ON document_permissions(document_id);
CREATE INDEX IF NOT EXISTS idx_permissions_user ON document_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_permissions_role ON document_permissions(role_name);
CREATE INDEX IF NOT EXISTS idx_permissions_granted_by ON document_permissions(granted_by);
CREATE INDEX IF NOT EXISTS idx_permissions_expires ON document_permissions(expires_at);
CREATE INDEX IF NOT EXISTS idx_permissions_source ON document_permissions(source_type, source_id);

-- Create unique constraints to prevent duplicate permissions
CREATE UNIQUE INDEX IF NOT EXISTS idx_permissions_unique_user 
    ON document_permissions(document_id, user_id) 
    WHERE user_id IS NOT NULL;
    
CREATE UNIQUE INDEX IF NOT EXISTS idx_permissions_unique_role 
    ON document_permissions(document_id, role_name) 
    WHERE role_name IS NOT NULL;

-- Add updated_at trigger for document_permissions
CREATE OR REPLACE FUNCTION update_document_permissions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_document_permissions_updated_at
    BEFORE UPDATE ON document_permissions
    FOR EACH ROW
    EXECUTE FUNCTION update_document_permissions_updated_at();

-- Add some comments for documentation
COMMENT ON TABLE document_permissions IS 'Role-based permission system for document access control';
COMMENT ON COLUMN document_permissions.user_id IS 'User ID (if permission is for a specific user)';
COMMENT ON COLUMN document_permissions.role_name IS 'Role name (if permission is for a role)';
COMMENT ON COLUMN document_permissions.can_read IS 'Permission to read/view the document';
COMMENT ON COLUMN document_permissions.can_write IS 'Permission to modify the document';
COMMENT ON COLUMN document_permissions.can_delete IS 'Permission to delete the document';
COMMENT ON COLUMN document_permissions.can_share IS 'Permission to share the document with others';
COMMENT ON COLUMN document_permissions.can_admin IS 'Administrative permissions (manage permissions, etc.)';
COMMENT ON COLUMN document_permissions.granted_by IS 'User ID who granted this permission';
COMMENT ON COLUMN document_permissions.expires_at IS 'When the permission expires (null = never expires)';
COMMENT ON COLUMN document_permissions.inherited IS 'Whether this permission is inherited from a parent resource';
COMMENT ON COLUMN document_permissions.source_type IS 'Source of inherited permission (folder, organization, etc.)';
COMMENT ON COLUMN document_permissions.source_id IS 'ID of the source resource for inherited permissions';