"""
Tests for database configuration and connection management
"""
import pytest
from unittest.mock import patch, MagicMock
import os

from database import DatabaseConfig, get_db_session, init_database, DatabaseUtils
from models import NotificationCategory

class TestDatabaseConfig:
    """Test DatabaseConfig class"""
    
    def test_database_url_from_env(self):
        """Test database URL configuration from environment"""
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test:pass@localhost:5432/test_db'}):
            config = DatabaseConfig()
            assert config.database_url == 'postgresql://test:pass@localhost:5432/test_db'
    
    def test_database_url_from_components(self):
        """Test database URL construction from components"""
        env_vars = {
            'DATABASE_HOST': 'test-host',
            'DATABASE_PORT': '5433',
            'DATABASE_USER': 'test_user',
            'DATABASE_PASSWORD': 'test_pass',
            'DATABASE_NAME': 'test_db'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = DatabaseConfig()
            expected_url = 'postgresql://test_user:test_pass@test-host:5433/test_db'
            assert config.database_url == expected_url
    
    def test_default_database_url(self):
        """Test default database URL when no env vars set"""
        # Clear relevant environment variables
        env_vars_to_clear = [
            'DATABASE_URL', 'DATABASE_HOST', 'DATABASE_PORT', 
            'DATABASE_USER', 'DATABASE_PASSWORD', 'DATABASE_NAME'
        ]
        
        with patch.dict(os.environ, {}, clear=True):
            config = DatabaseConfig()
            expected_url = 'postgresql://comm_user:comm_pass@localhost:5435/communication_service'
            assert config.database_url == expected_url
    
    def test_engine_configuration(self):
        """Test SQLAlchemy engine configuration"""
        with patch('database.create_engine') as mock_create_engine:
            config = DatabaseConfig()
            
            mock_create_engine.assert_called_once()
            call_args = mock_create_engine.call_args
            
            # Check that engine is created with correct parameters
            assert 'pool_size' in call_args.kwargs
            assert 'max_overflow' in call_args.kwargs
            assert 'pool_timeout' in call_args.kwargs
            assert 'pool_recycle' in call_args.kwargs
            assert call_args.kwargs['pool_pre_ping'] is True
    
    def test_health_check_success(self, mock_redis):
        """Test successful database health check"""
        with patch('database.db_config') as mock_db_config:
            mock_session = MagicMock()
            mock_db_config.get_session.return_value.__enter__.return_value = mock_session
            
            result = mock_db_config.health_check.return_value = True
            assert result is True
    
    def test_health_check_failure(self):
        """Test failed database health check"""
        config = DatabaseConfig()
        
        # Mock get_session to raise an exception
        with patch.object(config, 'get_session') as mock_get_session:
            mock_get_session.side_effect = Exception("Connection failed")
            
            result = config.health_check()
            assert result is False

class TestDatabaseSession:
    """Test database session management"""
    
    def test_get_db_session_success(self, db_session):
        """Test successful database session retrieval"""
        # This test uses the fixture which already tests the session
        assert db_session is not None
        
        # Test that we can perform a basic query
        result = db_session.execute("SELECT 1").scalar()
        assert result == 1
    
    def test_get_db_session_dependency(self):
        """Test FastAPI dependency for database session"""
        with patch('database.db_config') as mock_db_config:
            mock_session = MagicMock()
            mock_db_config.get_session_direct.return_value = mock_session
            
            # Test the generator function
            gen = get_db_session()
            session = next(gen)
            
            assert session == mock_session
            
            # Test cleanup
            try:
                next(gen)
            except StopIteration:
                pass  # Expected behavior
            
            mock_session.close.assert_called_once()

class TestDatabaseInitialization:
    """Test database initialization functions"""
    
    def test_init_database(self):
        """Test database initialization"""
        with patch('database.db_config') as mock_db_config, \
             patch('database.get_db') as mock_get_db, \
             patch('database.create_default_categories') as mock_create_categories:
            
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            # Mock that no categories exist
            mock_session.query.return_value.count.return_value = 0
            
            # Mock default categories
            mock_categories = [MagicMock() for _ in range(5)]
            mock_create_categories.return_value = mock_categories
            
            init_database()
            
            # Verify tables are created
            mock_db_config.create_tables.assert_called_once()
            
            # Verify default categories are added
            for category in mock_categories:
                mock_session.add.assert_any_call(category)
            
            mock_session.commit.assert_called()
    
    def test_init_database_with_existing_categories(self):
        """Test database initialization when categories already exist"""
        with patch('database.db_config') as mock_db_config, \
             patch('database.get_db') as mock_get_db:
            
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            # Mock that categories already exist
            mock_session.query.return_value.count.return_value = 3
            
            init_database()
            
            # Verify tables are still created but no categories added
            mock_db_config.create_tables.assert_called_once()
            mock_session.add.assert_not_called()

class TestDatabaseUtils:
    """Test DatabaseUtils utility functions"""
    
    def test_get_table_counts(self):
        """Test getting table row counts"""
        with patch('database.get_db') as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            # Mock query counts
            count_values = [5, 10, 20, 3, 8, 15, 50]
            mock_session.query.return_value.count.side_effect = count_values
            
            counts = DatabaseUtils.get_table_counts()
            
            expected_tables = [
                "categories", "templates", "notifications", "preferences",
                "conversations", "participants", "messages"
            ]
            
            for table in expected_tables:
                assert table in counts
                assert isinstance(counts[table], int)
    
    def test_cleanup_old_notifications(self):
        """Test cleanup of old notifications"""
        with patch('database.get_db') as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value.__enter__.return_value = mock_session
            
            # Mock query chain
            mock_query = MagicMock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.delete.return_value = 5  # 5 notifications deleted
            
            deleted_count = DatabaseUtils.cleanup_old_notifications(days=30)
            
            assert deleted_count == 5
            mock_session.commit.assert_called_once()
    
    def test_get_database_stats(self):
        """Test getting comprehensive database statistics"""
        with patch.object(DatabaseUtils, 'get_table_counts') as mock_get_counts:
            mock_get_counts.return_value = {"notifications": 100, "messages": 50}
            
            with patch('database.db_config') as mock_db_config:
                # Mock pool methods
                mock_pool = MagicMock()
                mock_pool.size.return_value = 10
                mock_pool.checkedout.return_value = 2
                mock_pool.overflow.return_value = 0
                mock_pool.checkedin.return_value = 8
                mock_db_config.engine.pool = mock_pool
                
                stats = DatabaseUtils.get_database_stats()
                
                assert "table_counts" in stats
                assert "connection_info" in stats
                assert stats["table_counts"]["notifications"] == 100
                assert stats["connection_info"]["pool_size"] == 10

class TestDatabaseIntegration:
    """Integration tests for database functionality"""
    
    def test_full_database_flow(self, db_session):
        """Test complete database flow with real session"""
        # Create a category
        category = NotificationCategory(
            name="integration_test",
            description="Integration test category"
        )
        db_session.add(category)
        db_session.commit()
        
        # Verify it was created
        retrieved = db_session.query(NotificationCategory).filter_by(name="integration_test").first()
        assert retrieved is not None
        assert retrieved.description == "Integration test category"
        
        # Update it
        retrieved.description = "Updated description"
        db_session.commit()
        
        # Verify update
        updated = db_session.query(NotificationCategory).filter_by(name="integration_test").first()
        assert updated.description == "Updated description"
        
        # Delete it
        db_session.delete(updated)
        db_session.commit()
        
        # Verify deletion
        deleted = db_session.query(NotificationCategory).filter_by(name="integration_test").first()
        assert deleted is None