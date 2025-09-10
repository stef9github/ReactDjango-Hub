-- Migration: Add Document Collaboration System
-- Created: 2024-09-09
-- Description: Add collaboration features including sharing notifications, comments, activities, and workspaces

-- Create share notification status enum
CREATE TYPE share_notification_status AS ENUM ('pending', 'sent', 'delivered', 'read', 'failed');

-- Create document_shares table
CREATE TABLE IF NOT EXISTS document_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES document_permissions(id) ON DELETE CASCADE,
    
    -- Sharing details
    shared_by UUID NOT NULL,
    shared_with_type VARCHAR(10) NOT NULL CHECK (shared_with_type IN ('user', 'role')),
    shared_with_id VARCHAR(255) NOT NULL,
    
    -- Message and metadata
    share_message TEXT NULL,
    access_level VARCHAR(20) NOT NULL DEFAULT 'read',
    
    -- Timestamps
    shared_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NULL,
    
    -- Notification status
    notification_status share_notification_status NOT NULL DEFAULT 'pending',
    notification_sent_at TIMESTAMP WITH TIME ZONE NULL,
    notification_read_at TIMESTAMP WITH TIME ZONE NULL,
    
    -- Additional metadata
    metadata JSONB NOT NULL DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create document_comments table
CREATE TABLE IF NOT EXISTS document_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Comment details
    author_id UUID NOT NULL,
    content TEXT NOT NULL,
    
    -- Threading support
    parent_comment_id UUID NULL REFERENCES document_comments(id) ON DELETE CASCADE,
    
    -- Position in document (for annotations)
    page_number INTEGER NULL,
    position_data JSONB NULL,
    
    -- Status and visibility
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'deleted')),
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_by UUID NULL,
    resolved_at TIMESTAMP WITH TIME ZONE NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create document_activities table
CREATE TABLE IF NOT EXISTS document_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Activity details
    user_id UUID NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    activity_description TEXT NOT NULL,
    
    -- Activity context
    target_user_id UUID NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create document_workspaces table
CREATE TABLE IF NOT EXISTS document_workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Workspace details
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    organization_id UUID NOT NULL,
    
    -- Access control
    created_by UUID NOT NULL,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Settings
    settings JSONB NOT NULL DEFAULT '{}'
);

-- Create indexes for document_shares
CREATE INDEX IF NOT EXISTS idx_shares_document ON document_shares(document_id);
CREATE INDEX IF NOT EXISTS idx_shares_shared_by ON document_shares(shared_by);
CREATE INDEX IF NOT EXISTS idx_shares_shared_with ON document_shares(shared_with_type, shared_with_id);
CREATE INDEX IF NOT EXISTS idx_shares_notification_status ON document_shares(notification_status);
CREATE INDEX IF NOT EXISTS idx_shares_expires ON document_shares(expires_at);

-- Create indexes for document_comments
CREATE INDEX IF NOT EXISTS idx_comments_document ON document_comments(document_id);
CREATE INDEX IF NOT EXISTS idx_comments_author ON document_comments(author_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent ON document_comments(parent_comment_id);
CREATE INDEX IF NOT EXISTS idx_comments_status ON document_comments(status);
CREATE INDEX IF NOT EXISTS idx_comments_created ON document_comments(created_at);
CREATE INDEX IF NOT EXISTS idx_comments_position ON document_comments(page_number);

-- Create indexes for document_activities
CREATE INDEX IF NOT EXISTS idx_activities_document ON document_activities(document_id);
CREATE INDEX IF NOT EXISTS idx_activities_user ON document_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_activities_type ON document_activities(activity_type);
CREATE INDEX IF NOT EXISTS idx_activities_created ON document_activities(created_at);
CREATE INDEX IF NOT EXISTS idx_activities_target ON document_activities(target_user_id);

-- Create indexes for document_workspaces
CREATE INDEX IF NOT EXISTS idx_workspaces_org ON document_workspaces(organization_id);
CREATE INDEX IF NOT EXISTS idx_workspaces_created_by ON document_workspaces(created_by);
CREATE INDEX IF NOT EXISTS idx_workspaces_status ON document_workspaces(status);
CREATE INDEX IF NOT EXISTS idx_workspaces_name ON document_workspaces(name);

-- Add updated_at triggers
CREATE OR REPLACE FUNCTION update_collaboration_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_document_shares_updated_at
    BEFORE UPDATE ON document_shares
    FOR EACH ROW
    EXECUTE FUNCTION update_collaboration_updated_at();

CREATE TRIGGER update_document_comments_updated_at
    BEFORE UPDATE ON document_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_collaboration_updated_at();

CREATE TRIGGER update_document_workspaces_updated_at
    BEFORE UPDATE ON document_workspaces
    FOR EACH ROW
    EXECUTE FUNCTION update_collaboration_updated_at();

-- Add comments for documentation
COMMENT ON TABLE document_shares IS 'Document sharing records with notifications and metadata';
COMMENT ON TABLE document_comments IS 'Comments and annotations on documents for collaboration';
COMMENT ON TABLE document_activities IS 'Activity log for document collaboration tracking';
COMMENT ON TABLE document_workspaces IS 'Shared workspaces for document collaboration';

-- Add column comments
COMMENT ON COLUMN document_shares.shared_with_type IS 'Type of recipient: user or role';
COMMENT ON COLUMN document_shares.shared_with_id IS 'User ID or role name depending on type';
COMMENT ON COLUMN document_shares.notification_status IS 'Status of share notification delivery';

COMMENT ON COLUMN document_comments.parent_comment_id IS 'Parent comment for threaded discussions';
COMMENT ON COLUMN document_comments.position_data IS 'Position/selection data for document annotations';
COMMENT ON COLUMN document_comments.is_resolved IS 'Whether the comment/issue is resolved';

COMMENT ON COLUMN document_activities.activity_type IS 'Type of activity: shared, commented, viewed, downloaded, etc.';
COMMENT ON COLUMN document_activities.target_user_id IS 'Target user for activities like sharing';

COMMENT ON COLUMN document_workspaces.is_public IS 'Whether workspace is public within organization';