"""
Database configuration and session management for Communication Service
Sync PostgreSQL pattern using psycopg2-binary
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging

from models import Base

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration and connection management"""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.engine = self._create_engine()
        self.session_maker = sessionmaker(bind=self.engine)
    
    def _get_database_url(self) -> str:
        """Get database URL from environment variables with local development defaults"""
        database_url = os.getenv("DATABASE_URL")
        use_docker = os.getenv("USE_DOCKER", "false").lower() == "true"
        
        if not database_url:
            if use_docker:
                # Docker environment - use Docker service names and ports
                host = os.getenv("DATABASE_HOST", "communication-db")
                port = os.getenv("DATABASE_PORT", "5432")
                user = os.getenv("DATABASE_USER", "communication_user")
                password = os.getenv("DATABASE_PASSWORD", "communication_pass")
                database = os.getenv("DATABASE_NAME", "communication_service")
            else:
                # Local development - use localhost and default PostgreSQL setup
                host = os.getenv("DATABASE_HOST", "localhost")
                port = os.getenv("DATABASE_PORT", "5432")
                user = os.getenv("DATABASE_USER", "stephanerichard")
                password = os.getenv("DATABASE_PASSWORD", "")
                database = os.getenv("DATABASE_NAME", "communication_service")
            
            # Build URL with or without password
            if password:
                database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            else:
                database_url = f"postgresql://{user}@{host}:{port}/{database}"
        
        logger.info(f"Database URL configured: {database_url.split('@')[0]}@...")
        return database_url
    
    def _create_engine(self):
        """Create SQLAlchemy engine with connection pooling"""
        pool_size = int(os.getenv("DATABASE_POOL_SIZE", "10"))
        max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
        pool_timeout = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
        pool_recycle = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
        
        engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,  # Validate connections before use
            echo=os.getenv("DEBUG") == "true",  # SQL logging in debug mode
        )
        
        # Add connection event listeners
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set connection-level settings (PostgreSQL specific)"""
            pass
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout in debug mode"""
            if os.getenv("DEBUG") == "true":
                logger.debug("Connection checked out from pool")
        
        logger.info(f"Database engine created with pool_size={pool_size}, max_overflow={max_overflow}")
        return engine
    
    def create_tables(self):
        """Create all database tables"""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("Database tables dropped")
    
    @contextmanager
    def get_session(self):
        """Get a database session with proper cleanup"""
        session = self.session_maker()
        try:
            yield session
            session.commit()
        except Exception as e:
            logger.error(f"Database session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """Get a database session for direct use (remember to close!)"""
        return self.session_maker()
    
    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database configuration instance
db_config = DatabaseConfig()

# Convenience functions for use in FastAPI dependencies
def get_db_session():
    """FastAPI dependency to get database session"""
    session = db_config.get_session_direct()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@contextmanager
def get_db():
    """Context manager for database sessions"""
    with db_config.get_session() as session:
        yield session

def init_database():
    """Initialize database tables and default data"""
    from models import create_default_categories
    
    logger.info("Initializing database...")
    
    # Create tables
    db_config.create_tables()
    
    # Create default notification categories
    with get_db() as session:
        # Check if categories already exist
        from models import NotificationCategory
        existing_categories = session.query(NotificationCategory).count()
        
        if existing_categories == 0:
            logger.info("Creating default notification categories...")
            default_categories = create_default_categories()
            for category in default_categories:
                session.add(category)
            session.commit()
            logger.info(f"Created {len(default_categories)} default categories")
        else:
            logger.info(f"Found {existing_categories} existing categories, skipping creation")
    
    logger.info("Database initialization complete")

def reset_database():
    """Reset database (drop and recreate all tables)"""
    logger.warning("Resetting database - all data will be lost!")
    db_config.drop_tables()
    init_database()
    logger.info("Database reset complete")

# Database utilities
class DatabaseUtils:
    """Utility functions for database operations"""
    
    @staticmethod
    def get_table_counts() -> dict:
        """Get row counts for all tables"""
        from models import (
            NotificationCategory, NotificationTemplate, Notification,
            NotificationPreference, Conversation, ConversationParticipant, Message
        )
        
        models = {
            "categories": NotificationCategory,
            "templates": NotificationTemplate,
            "notifications": Notification,
            "preferences": NotificationPreference,
            "conversations": Conversation,
            "participants": ConversationParticipant,
            "messages": Message,
        }
        
        counts = {}
        with get_db() as session:
            for name, model in models.items():
                counts[name] = session.query(model).count()
        
        return counts
    
    @staticmethod
    def cleanup_old_notifications(days: int = 30):
        """Clean up old notifications older than specified days"""
        from datetime import datetime, timedelta
        from models import Notification
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        with get_db() as session:
            deleted_count = session.query(Notification)\
                .filter(Notification.created_at < cutoff_date)\
                .filter(Notification.status.in_(["delivered", "failed"]))\
                .delete()
            
            session.commit()
            logger.info(f"Cleaned up {deleted_count} old notifications")
            return deleted_count
    
    @staticmethod
    def get_database_stats() -> dict:
        """Get comprehensive database statistics"""
        stats = {
            "table_counts": DatabaseUtils.get_table_counts(),
            "connection_info": {
                "pool_size": db_config.engine.pool.size(),
                "checked_out_connections": db_config.engine.pool.checkedout(),
                "overflow_connections": db_config.engine.pool.overflow(),
                "checked_in_connections": db_config.engine.pool.checkedin(),
            }
        }
        return stats