"""
Database connection and session management for the content service.
"""

import os
import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from sqlalchemy import event, text


logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        self.engine: AsyncEngine = None
        self.session_factory: async_sessionmaker = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize database connection."""
        if self._initialized:
            return
            
        database_url = os.getenv("DATABASE_URL")
        use_docker = os.getenv("USE_DOCKER", "false").lower() == "true"
        
        if not database_url:
            if use_docker:
                # Docker environment - use Docker service names
                database_url = "postgresql+asyncpg://content_user:content_pass@content-db:5432/content_service"
            else:
                # Local development - use localhost and default PostgreSQL setup
                user = os.getenv("DATABASE_USER", "stephanerichard")
                password = os.getenv("DATABASE_PASSWORD", "")
                host = os.getenv("DATABASE_HOST", "localhost")
                port = os.getenv("DATABASE_PORT", "5432")
                database = os.getenv("DATABASE_NAME", "content_service")
                
                # Build URL with or without password
                if password:
                    database_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
                else:
                    database_url = f"postgresql+asyncpg://{user}@{host}:{port}/{database}"
        
        # Convert PostgreSQL URL to async version if needed
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif not database_url.startswith("postgresql+asyncpg://"):
            database_url = f"postgresql+asyncpg://{database_url}"
        
        # Engine configuration
        engine_kwargs = {
            "echo": os.getenv("DEBUG", "false").lower() == "true",
            "pool_size": int(os.getenv("DATABASE_POOL_SIZE", "10")),
            "max_overflow": int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # 1 hour
        }
        
        # Use NullPool for testing
        if "test" in database_url or os.getenv("TESTING"):
            engine_kwargs["poolclass"] = NullPool
        
        self.engine = create_async_engine(database_url, **engine_kwargs)
        
        # Configure session factory
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        
        # Set up event listeners
        self._setup_event_listeners()
        
        self._initialized = True
        logger.info("Database connection initialized")
    
    def _setup_event_listeners(self) -> None:
        """Set up SQLAlchemy event listeners."""
        
        @event.listens_for(self.engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set up connection-level settings."""
            try:
                # For PostgreSQL connections (both sync and async)
                if "postgresql" in self.url.lower():
                    cursor = dbapi_connection.cursor()
                    cursor.execute("SET timezone TO 'UTC'")
                    cursor.close()
            except Exception:
                # Skip if connection doesn't support cursor operations
                pass
        
        @event.listens_for(self.engine.sync_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Handle connection checkout."""
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(self.engine.sync_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Handle connection checkin."""
            logger.debug("Connection returned to pool")
    
    async def get_session(self) -> AsyncSession:
        """Get a new database session."""
        if not self._initialized:
            self.initialize()
        
        return self.session_factory()
    
    @asynccontextmanager
    async def get_session_context(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with automatic cleanup."""
        session = await self.get_session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.get_session_context() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    
    async def drop_tables(self) -> None:
        """Drop all database tables (for testing)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped")


# Global database manager instance
db = DatabaseManager()


# Dependency for FastAPI
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get database session."""
    async with db.get_session_context() as session:
        yield session


# Utility functions
async def init_database() -> None:
    """Initialize database connection."""
    db.initialize()
    await db.create_tables()


async def close_database() -> None:
    """Close database connections."""
    await db.close()


async def check_database_health() -> bool:
    """Check database health."""
    return await db.health_check()