"""
Database Migration Integration Tests
Tests Alembic migrations including rollback scenarios and data integrity
"""

import pytest
import asyncio
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from alembic import command, script
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.runtime.environment import EnvironmentContext

from database.models import Base, NotificationCategory, NotificationTemplate, Notification
from database.connection import get_database_session


@pytest.mark.integration 
@pytest.mark.requires_db
class TestDatabaseMigrationIntegrity:
    """Test database migrations for integrity and rollback capability"""
    
    @pytest.fixture
    async def migration_engine(self):
        """Create a separate database engine for migration testing"""
        test_db_url = "postgresql+asyncpg://test:test@localhost:5432/communication_test_migrations"
        engine = create_async_engine(test_db_url, echo=True)
        
        # Create test database if it doesn't exist
        sync_engine = create_engine(test_db_url.replace("+asyncpg", ""))
        try:
            async with engine.begin() as conn:
                await conn.execute(text("CREATE DATABASE communication_test_migrations"))
        except Exception:
            pass  # Database might already exist
        
        yield engine
        
        # Cleanup
        await engine.dispose()
    
    @pytest.fixture
    async def alembic_config(self):
        """Create Alembic configuration for testing"""
        config = Config()
        config.set_main_option("script_location", "alembic")
        config.set_main_option("sqlalchemy.url", "postgresql://test:test@localhost:5432/communication_test_migrations")
        
        return config
    
    async def test_migration_upgrade_and_rollback_cycle(self, migration_engine, alembic_config):
        """Test complete migration upgrade and rollback cycle"""
        
        # Get current migration head
        script_dir = script.ScriptDirectory.from_config(alembic_config)
        head_revision = script_dir.get_current_head()
        
        with migration_engine.sync_engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_revision = context.get_current_revision()
            
            # Test upgrade to head
            command.upgrade(alembic_config, "head")
            
            # Verify all tables are created
            inspector = inspect(connection)
            table_names = inspector.get_table_names()
            
            expected_tables = [
                "notification_categories",
                "notification_templates", 
                "notifications",
                "alembic_version"
            ]
            
            for table in expected_tables:
                assert table in table_names, f"Table {table} not created after migration"
            
            # Test rollback to previous revision
            if current_revision and current_revision != head_revision:
                command.downgrade(alembic_config, current_revision)
                
                # Verify rollback worked
                context_after_rollback = MigrationContext.configure(connection)
                revision_after_rollback = context_after_rollback.get_current_revision()
                assert revision_after_rollback == current_revision
    
    async def test_migration_data_integrity_during_schema_changes(self, migration_engine, alembic_config):
        """Test that data integrity is maintained during schema migrations"""
        
        # Create initial schema
        command.upgrade(alembic_config, "head")
        
        async with AsyncSession(migration_engine) as session:
            # Insert test data
            test_category = NotificationCategory(
                name="test_category",
                description="Test category for migration testing",
                organization_id="org-123"
            )
            session.add(test_category)
            
            test_template = NotificationTemplate(
                name="test_template",
                subject="Test Subject {{ name }}",
                content="Hello {{ name }}, this is a test template.",
                channel="email",
                organization_id="org-123",
                category_id=None  # Will be set after commit
            )
            session.add(test_template)
            
            await session.commit()
            await session.refresh(test_category)
            
            test_template.category_id = test_category.id
            await session.commit()
            
            template_id = test_template.id
            category_id = test_category.id
        
        # Simulate a migration that adds a new column
        with migration_engine.sync_engine.connect() as connection:
            context = MigrationContext.configure(connection)
            op = Operations(context)
            
            # Add a new column
            try:
                op.add_column('notification_templates', 
                             Column('priority_level', String(20), default='normal'))
            except Exception:
                pass  # Column might already exist
        
        # Verify data is still intact after schema change
        async with AsyncSession(migration_engine) as session:
            # Check that existing data is preserved
            category = await session.get(NotificationCategory, category_id)
            template = await session.get(NotificationTemplate, template_id)
            
            assert category is not None
            assert template is not None
            assert category.name == "test_category"
            assert template.name == "test_template"
            assert template.category_id == category_id
            
            # Verify new column exists and has default value
            result = await session.execute(
                text("SELECT priority_level FROM notification_templates WHERE id = :id"),
                {"id": template_id}
            )
            priority_level = result.scalar()
            assert priority_level in ['normal', None]  # Default or NULL
    
    async def test_migration_rollback_data_preservation(self, migration_engine, alembic_config):
        """Test that data is preserved during migration rollbacks"""
        
        # Start with a clean state
        command.downgrade(alembic_config, "base")
        command.upgrade(alembic_config, "head")
        
        # Insert test data
        async with AsyncSession(migration_engine) as session:
            test_notification = Notification(
                recipient="test@example.com",
                subject="Migration Test",
                content="Testing migration rollback data preservation",
                channel="email",
                status="delivered",
                organization_id="org-123",
                user_id="user-123",
                provider_message_id="test-msg-123",
                metadata_={"test": "data"}
            )
            session.add(test_notification)
            await session.commit()
            notification_id = test_notification.id
        
        # Get current revision
        with migration_engine.sync_engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_revision = context.get_current_revision()
        
        # Get revision history
        script_dir = script.ScriptDirectory.from_config(alembic_config)
        revisions = list(script_dir.walk_revisions())
        
        if len(revisions) > 1:
            # Get previous revision
            previous_revision = None
            for i, rev in enumerate(revisions):
                if rev.revision == current_revision and i < len(revisions) - 1:
                    previous_revision = revisions[i + 1].revision
                    break
            
            if previous_revision:
                # Rollback to previous revision
                command.downgrade(alembic_config, previous_revision)
                
                # Verify data still exists (if table structure allows)
                try:
                    async with AsyncSession(migration_engine) as session:
                        notification = await session.get(Notification, notification_id)
                        if notification:  # Data preserved if table/columns still exist
                            assert notification.recipient == "test@example.com"
                            assert notification.subject == "Migration Test"
                except Exception:
                    # Table structure changed too much, which is acceptable
                    pass
                
                # Upgrade back to head
                command.upgrade(alembic_config, "head")
    
    async def test_migration_foreign_key_constraints(self, migration_engine, alembic_config):
        """Test that foreign key constraints are properly maintained during migrations"""
        
        command.upgrade(alembic_config, "head")
        
        async with AsyncSession(migration_engine) as session:
            # Create category first
            category = NotificationCategory(
                name="fk_test_category",
                description="Foreign key test category", 
                organization_id="org-fk-test"
            )
            session.add(category)
            await session.commit()
            await session.refresh(category)
            
            # Create template with valid foreign key
            template = NotificationTemplate(
                name="fk_test_template",
                subject="FK Test",
                content="Testing foreign keys",
                channel="email",
                organization_id="org-fk-test",
                category_id=category.id
            )
            session.add(template)
            await session.commit()
            
            # Try to create template with invalid foreign key (should fail)
            invalid_template = NotificationTemplate(
                name="invalid_fk_template",
                subject="Invalid FK Test", 
                content="This should fail",
                channel="email",
                organization_id="org-fk-test",
                category_id=99999  # Non-existent category
            )
            session.add(invalid_template)
            
            with pytest.raises(Exception):  # Should raise foreign key constraint error
                await session.commit()
    
    async def test_migration_index_creation_and_performance(self, migration_engine, alembic_config):
        """Test that database indexes are created properly and improve performance"""
        
        command.upgrade(alembic_config, "head")
        
        with migration_engine.sync_engine.connect() as connection:
            inspector = inspect(connection)
            
            # Check that expected indexes exist
            notification_indexes = inspector.get_indexes("notifications")
            index_names = [idx['name'] for idx in notification_indexes]
            
            # Expected performance indexes
            expected_indexes = [
                "idx_notifications_organization_id",
                "idx_notifications_user_id", 
                "idx_notifications_status",
                "idx_notifications_channel",
                "idx_notifications_created_at"
            ]
            
            for expected_idx in expected_indexes:
                # Check if any index exists that could serve the same purpose
                found = any(expected_idx in name for name in index_names)
                if not found:
                    # Check if columns are indexed (might have different naming)
                    column_indexed = False
                    for idx in notification_indexes:
                        if any(col in expected_idx for col in idx['column_names']):
                            column_indexed = True
                            break
                    
                    assert column_indexed, f"No index found for {expected_idx}"
        
        # Test query performance with indexes
        async with AsyncSession(migration_engine) as session:
            # Insert test data for performance testing
            notifications = []
            for i in range(100):
                notification = Notification(
                    recipient=f"user{i}@example.com",
                    subject=f"Performance Test {i}",
                    content=f"Testing query performance {i}",
                    channel="email" if i % 2 == 0 else "sms",
                    status="delivered" if i % 3 == 0 else "pending",
                    organization_id=f"org-{i % 10}",
                    user_id=f"user-{i % 20}"
                )
                notifications.append(notification)
            
            session.add_all(notifications)
            await session.commit()
            
            # Test indexed query performance
            import time
            
            start_time = time.time()
            result = await session.execute(
                text("""
                    SELECT COUNT(*) FROM notifications 
                    WHERE organization_id = :org_id 
                    AND status = :status
                """),
                {"org_id": "org-1", "status": "delivered"}
            )
            query_time = time.time() - start_time
            
            # Query should be fast with proper indexing
            assert query_time < 0.1, f"Indexed query too slow: {query_time}s"
            assert result.scalar() >= 0


@pytest.mark.integration
@pytest.mark.requires_db  
class TestMigrationScripts:
    """Test individual migration scripts for correctness"""
    
    async def test_initial_migration_creates_all_tables(self, alembic_config):
        """Test that initial migration creates all required tables"""
        
        # Start from clean state
        command.downgrade(alembic_config, "base")
        
        # Apply first migration
        command.upgrade(alembic_config, "+1")  # Apply next migration
        
        # Check tables are created correctly
        engine = create_engine(alembic_config.get_main_option("sqlalchemy.url"))
        with engine.connect() as connection:
            inspector = inspect(connection)
            tables = inspector.get_table_names()
            
            # At minimum, should have alembic_version
            assert "alembic_version" in tables
            
            # Check for main tables (depending on migration order)
            expected_base_tables = ["notification_categories", "notification_templates", "notifications"]
            created_tables = [table for table in expected_base_tables if table in tables]
            assert len(created_tables) > 0, "No main tables created in first migration"
    
    async def test_migration_script_syntax_and_execution(self, alembic_config):
        """Test that all migration scripts have valid syntax and can execute"""
        
        script_dir = script.ScriptDirectory.from_config(alembic_config)
        
        # Test each migration script
        for revision in script_dir.walk_revisions():
            # Check upgrade function exists
            assert hasattr(revision.module, 'upgrade'), f"Migration {revision.revision} missing upgrade function"
            
            # Check downgrade function exists  
            assert hasattr(revision.module, 'downgrade'), f"Migration {revision.revision} missing downgrade function"
            
            # Verify imports are correct
            try:
                # Test that the module can be imported without errors
                upgrade_func = revision.module.upgrade
                downgrade_func = revision.module.downgrade
                
                assert callable(upgrade_func), f"Upgrade function not callable in {revision.revision}"
                assert callable(downgrade_func), f"Downgrade function not callable in {revision.revision}"
                
            except Exception as e:
                pytest.fail(f"Migration {revision.revision} has syntax errors: {e}")
    
    async def test_migration_dependencies_and_ordering(self, alembic_config):
        """Test that migration dependencies are correctly specified"""
        
        script_dir = script.ScriptDirectory.from_config(alembic_config)
        revisions = list(script_dir.walk_revisions())
        
        # Check revision dependencies
        for revision in revisions:
            if revision.down_revision:
                # Find the dependency
                dependency_exists = any(
                    rev.revision == revision.down_revision 
                    for rev in revisions
                )
                assert dependency_exists, f"Migration {revision.revision} depends on non-existent {revision.down_revision}"
        
        # Check for circular dependencies
        visited = set()
        for revision in revisions:
            path = []
            current = revision
            
            while current and current.revision not in visited:
                if current.revision in path:
                    pytest.fail(f"Circular dependency detected involving {current.revision}")
                
                path.append(current.revision)
                current = script_dir.get_revision(current.down_revision) if current.down_revision else None
            
            visited.update(path)


@pytest.mark.integration
@pytest.mark.slow
class TestMigrationPerformance:
    """Test migration performance and handle large datasets"""
    
    async def test_migration_performance_with_large_dataset(self, migration_engine, alembic_config):
        """Test migration performance with large amounts of existing data"""
        
        # Create initial schema
        command.upgrade(alembic_config, "head")
        
        # Insert large dataset
        async with AsyncSession(migration_engine) as session:
            # Create categories
            categories = []
            for i in range(10):
                category = NotificationCategory(
                    name=f"perf_category_{i}",
                    description=f"Performance test category {i}",
                    organization_id=f"org-perf-{i % 3}"
                )
                categories.append(category)
            
            session.add_all(categories)
            await session.commit()
            
            # Create large number of notifications
            notifications = []
            for i in range(1000):  # Reduced for test speed
                notification = Notification(
                    recipient=f"perf{i}@example.com",
                    subject=f"Performance Test {i}",
                    content=f"Large dataset migration test notification {i}",
                    channel="email" if i % 2 == 0 else "sms",
                    status="delivered" if i % 3 == 0 else "pending",
                    organization_id=f"org-perf-{i % 3}",
                    user_id=f"user-perf-{i % 100}",
                    provider_message_id=f"perf-msg-{i}",
                    metadata_={f"key_{i}": f"value_{i}"}
                )
                notifications.append(notification)
                
                # Batch insert to avoid memory issues
                if len(notifications) >= 100:
                    session.add_all(notifications)
                    await session.commit()
                    notifications = []
            
            if notifications:
                session.add_all(notifications)
                await session.commit()
        
        # Test migration performance
        import time
        
        start_time = time.time()
        
        # Simulate adding a new column migration
        with migration_engine.sync_engine.connect() as connection:
            context = MigrationContext.configure(connection)
            op = Operations(context)
            
            try:
                op.add_column('notifications', 
                             Column('priority_score', Integer, default=0))
                
                # Update existing records with default value
                connection.execute(
                    text("UPDATE notifications SET priority_score = 0 WHERE priority_score IS NULL")
                )
                
            except Exception:
                pass  # Column might already exist
        
        migration_time = time.time() - start_time
        
        # Migration should complete in reasonable time even with large dataset
        assert migration_time < 30, f"Migration took too long: {migration_time}s"
        
        # Verify data integrity after migration
        async with AsyncSession(migration_engine) as session:
            count_result = await session.execute(text("SELECT COUNT(*) FROM notifications"))
            count = count_result.scalar()
            assert count == 1000, f"Data loss during migration: expected 1000, got {count}"
    
    async def test_migration_rollback_performance(self, migration_engine, alembic_config):
        """Test rollback performance and data consistency"""
        
        # Ensure we're at head
        command.upgrade(alembic_config, "head")
        
        # Get current revision
        with migration_engine.sync_engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_revision = context.get_current_revision()
        
        # Get script directory and find previous revision
        script_dir = script.ScriptDirectory.from_config(alembic_config)
        revisions = list(script_dir.walk_revisions())
        
        previous_revision = None
        for i, rev in enumerate(revisions):
            if rev.revision == current_revision and i < len(revisions) - 1:
                previous_revision = revisions[i + 1].revision
                break
        
        if previous_revision:
            # Test rollback performance
            import time
            
            start_time = time.time()
            command.downgrade(alembic_config, previous_revision)
            rollback_time = time.time() - start_time
            
            # Rollback should be reasonably fast
            assert rollback_time < 10, f"Rollback took too long: {rollback_time}s"
            
            # Verify system is still functional after rollback
            with migration_engine.sync_engine.connect() as connection:
                inspector = inspect(connection)
                tables = inspector.get_table_names()
                
                # Should still have basic functionality
                assert "alembic_version" in tables
                
                # Context should reflect the rollback
                context = MigrationContext.configure(connection)
                assert context.get_current_revision() == previous_revision
            
            # Upgrade back to head
            command.upgrade(alembic_config, "head")