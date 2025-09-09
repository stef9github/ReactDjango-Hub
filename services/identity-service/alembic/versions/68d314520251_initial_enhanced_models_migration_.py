"""Initial enhanced models migration - complete identity service schema

Revision ID: 68d314520251
Revises: 974799e38366
Create Date: 2025-09-09 21:44:47.141727

This migration creates the complete enhanced Identity Service schema with:
- Enhanced user model with profiles and preferences
- Multi-tenant organization management
- Comprehensive MFA support (Email, SMS, TOTP, Backup Codes)
- Session management and activity tracking
- Email verification and password reset
- Audit logging and security features
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '68d314520251'
down_revision: Union[str, None] = '974799e38366'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the complete enhanced Identity Service schema"""
    
    # Drop existing simplified tables if they exist
    op.execute("DROP TABLE IF EXISTS password_resets_simple CASCADE")
    op.execute("DROP TABLE IF EXISTS email_verifications_simple CASCADE")
    op.execute("DROP TABLE IF EXISTS users_simple CASCADE")
    
    # Create Organizations table
    op.create_table('organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        
        # Organization details
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website_url', sa.String(500), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        
        # Contact information
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        
        # Address information
        sa.Column('address_line1', sa.String(255), nullable=True),
        sa.Column('address_line2', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state_province', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('country_code', sa.String(2), nullable=True),
        
        # Organization metadata
        sa.Column('organization_type', sa.String(30), nullable=False, default='individual'),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('employee_count_range', sa.String(20), nullable=True),
        sa.Column('subscription_tier', sa.String(20), nullable=False, default='free'),
        sa.Column('subscription_status', sa.String(20), nullable=False, default='active'),
        
        # Settings and preferences
        sa.Column('settings', postgresql.JSON, nullable=False, default={}),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_organizations_slug', 'organizations', ['slug'], unique=True)
    op.create_index('ix_organizations_name', 'organizations', ['name'])
    op.create_index('ix_organizations_type', 'organizations', ['organization_type'])
    
    # Create Users table (Enhanced)
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('username', sa.String(150), nullable=True, unique=True, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        
        # Profile information
        sa.Column('first_name', sa.String(150), nullable=True),
        sa.Column('last_name', sa.String(150), nullable=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        
        # Contact information
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('secondary_email', sa.String(255), nullable=True),
        
        # Preferences and settings
        sa.Column('language_code', sa.String(10), nullable=False, default='en'),
        sa.Column('timezone', sa.String(50), nullable=False, default='UTC'),
        sa.Column('theme_preference', sa.String(20), nullable=False, default='light'),
        sa.Column('notification_preferences', postgresql.JSON, nullable=False, default={}),
        sa.Column('privacy_settings', postgresql.JSON, nullable=False, default={}),
        
        # Status and verification
        sa.Column('status', sa.String(30), nullable=False, default='pending_verification'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        
        # Security
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_ip', sa.String(45), nullable=True),
        
        # Organizational relationship
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_organization_id', 'users', ['organization_id'])
    op.create_index('ix_users_status', 'users', ['status'])
    
    # Create User Profiles table
    op.create_table('user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        
        # Professional information
        sa.Column('job_title', sa.String(255), nullable=True),
        sa.Column('department', sa.String(255), nullable=True),
        sa.Column('manager_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Social links
        sa.Column('social_links', postgresql.JSON, nullable=False, default={}),
        
        # Emergency contact
        sa.Column('emergency_contact_name', sa.String(255), nullable=True),
        sa.Column('emergency_contact_phone', sa.String(20), nullable=True),
        sa.Column('emergency_contact_relationship', sa.String(100), nullable=True),
        
        # Skills and interests
        sa.Column('skills', postgresql.JSON, nullable=False, default=[]),
        sa.Column('interests', postgresql.JSON, nullable=False, default=[]),
        sa.Column('certifications', postgresql.JSON, nullable=False, default=[]),
        
        # Additional metadata
        sa.Column('metadata', postgresql.JSON, nullable=False, default={}),
        sa.Column('custom_fields', postgresql.JSON, nullable=False, default={}),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['manager_user_id'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index('ix_user_profiles_user_id', 'user_profiles', ['user_id'], unique=True)
    
    # Create User Activity Logs table
    op.create_table('user_activity_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('details', postgresql.JSON, nullable=False, default={}),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, default=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_activity_logs_user_id', 'user_activity_logs', ['user_id'])
    op.create_index('ix_activity_logs_action', 'user_activity_logs', ['action'])
    op.create_index('ix_activity_logs_timestamp', 'user_activity_logs', ['timestamp'])
    
    # Create User Preferences table
    op.create_table('user_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('preference_key', sa.String(100), nullable=False),
        sa.Column('preference_value', postgresql.JSON, nullable=False),
        sa.Column('preference_type', sa.String(50), nullable=False),
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'preference_key', name='uq_user_preference_key')
    )
    op.create_index('ix_preferences_user_id', 'user_preferences', ['user_id'])
    op.create_index('ix_preferences_key', 'user_preferences', ['preference_key'])
    
    # Create User Sessions table
    op.create_table('user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_token_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('refresh_token_hash', sa.String(255), nullable=True, unique=True),
        sa.Column('device_info', postgresql.JSON, nullable=False, default={}),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('location_info', postgresql.JSON, nullable=False, default={}),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('ix_sessions_token_hash', 'user_sessions', ['session_token_hash'], unique=True)
    op.create_index('ix_sessions_expires_at', 'user_sessions', ['expires_at'])
    
    # Create MFA Methods table
    op.create_table('mfa_methods',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('method_type', sa.String(20), nullable=False),
        sa.Column('identifier', sa.String(255), nullable=False),
        sa.Column('secret_encrypted', sa.Text(), nullable=True),
        sa.Column('backup_codes_encrypted', sa.Text(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('verification_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'method_type', 'identifier', name='uq_user_mfa_method')
    )
    op.create_index('ix_mfa_methods_user_id', 'mfa_methods', ['user_id'])
    op.create_index('ix_mfa_methods_type', 'mfa_methods', ['method_type'])
    
    # Create MFA Challenges table
    op.create_table('mfa_challenges',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mfa_method_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('challenge_code_hash', sa.String(255), nullable=False),
        sa.Column('challenge_type', sa.String(20), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('is_used', sa.Boolean(), nullable=False, default=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mfa_method_id'], ['mfa_methods.id'], ondelete='CASCADE')
    )
    op.create_index('ix_mfa_challenges_user_id', 'mfa_challenges', ['user_id'])
    op.create_index('ix_mfa_challenges_expires_at', 'mfa_challenges', ['expires_at'])
    
    # Create Email Verifications table
    op.create_table('email_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('verification_type', sa.String(30), nullable=False, default='registration'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_email_verifications_user_id', 'email_verifications', ['user_id'])
    op.create_index('ix_email_verifications_token', 'email_verifications', ['token_hash'], unique=True)
    op.create_index('ix_email_verifications_expires_at', 'email_verifications', ['expires_at'])
    
    # Create Password Resets table
    op.create_table('password_resets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, default=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_password_resets_user_id', 'password_resets', ['user_id'])
    op.create_index('ix_password_resets_token', 'password_resets', ['token_hash'], unique=True)
    op.create_index('ix_password_resets_expires_at', 'password_resets', ['expires_at'])


def downgrade() -> None:
    """Drop all enhanced Identity Service tables"""
    
    # Drop tables in reverse order (considering foreign key constraints)
    op.drop_table('password_resets')
    op.drop_table('email_verifications')  
    op.drop_table('mfa_challenges')
    op.drop_table('mfa_methods')
    op.drop_table('user_sessions')
    op.drop_table('user_preferences')
    op.drop_table('user_activity_logs')
    op.drop_table('user_profiles')
    op.drop_table('users')
    op.drop_table('organizations')
    
    # Recreate simplified schema if needed (for rollback compatibility)
    # This would recreate the previous simplified tables
    # For production, you might want to include the previous schema here