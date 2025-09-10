"""
Database connection and session management for Workflow Intelligence Service
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://workflow_user:workflow_pass@localhost:5436/workflow_intelligence_service"
)
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))

# Create database engine
engine = create_engine(
    DATABASE_URL,
    pool_size=DATABASE_POOL_SIZE,
    max_overflow=DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before use
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"  # Log SQL queries if needed
)

# Create session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_database_session() -> Generator[Session, None, None]:
    """
    Dependency function to get database session for FastAPI endpoints.
    
    Yields:
        Session: SQLAlchemy database session
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()

def create_tables():
    """Create all database tables"""
    from models import Base
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False

def get_database_info() -> dict:
    """
    Get database connection information for health checks.
    
    Returns:
        dict: Database status information
    """
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))  # PostgreSQL version
            db_version = result.fetchone()[0] if result.rowcount > 0 else "Unknown"
            
            # Get connection pool info
            pool = engine.pool
            
            return {
                "status": "healthy",
                "version": db_version,
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": 0  # invalid() method doesn't exist in newer SQLAlchemy
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "pool_size": 0,
            "checked_in": 0,
            "checked_out": 0,
            "overflow": 0,
            "invalid": 0
        }

class DatabaseManager:
    """Database manager for advanced operations"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def execute_raw_query(self, query: str, params: dict = None):
        """Execute raw SQL query"""
        with self.engine.connect() as connection:
            return connection.execute(text(query), params or {})
    
    def get_table_count(self, table_name: str) -> int:
        """Get record count for a specific table"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                return result.fetchone()[0]
        except Exception:
            return 0
    
    def get_workflow_statistics(self) -> dict:
        """Get workflow statistics for monitoring"""
        try:
            with self.engine.connect() as connection:
                stats = {}
                
                # Workflow definitions count
                result = connection.execute(text("SELECT COUNT(*) FROM workflow_definitions WHERE is_active = 1"))
                stats["active_definitions"] = result.fetchone()[0]
                
                # Workflow instances by status
                result = connection.execute(text("""
                    SELECT status, COUNT(*) 
                    FROM workflow_instances 
                    GROUP BY status
                """))
                stats["instances_by_status"] = dict(result.fetchall())
                
                # Total AI insights
                result = connection.execute(text("SELECT COUNT(*) FROM ai_insights"))
                stats["total_ai_insights"] = result.fetchone()[0]
                
                return stats
        except Exception as e:
            logger.error(f"Error getting workflow statistics: {str(e)}")
            return {
                "active_definitions": 0,
                "instances_by_status": {},
                "total_ai_insights": 0,
                "error": str(e)
            }

# Global database manager instance
db_manager = DatabaseManager()