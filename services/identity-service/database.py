"""
Database configuration and connection management
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from simple_models import Base

# Get database URL from settings configuration
from config import settings

DATABASE_URL = settings.get_database_url()

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv('DEBUG', 'false').lower() == 'true',  # Log SQL queries in debug mode
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db_session():
    """
    Get database session for dependency injection
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """
    Create all tables in the database
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully")

async def drop_db():
    """
    Drop all tables in the database (use with caution!)
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("⚠️  All database tables dropped")

async def reset_db():
    """
    Drop and recreate all tables
    """
    await drop_db()
    await init_db()
    print("🔄 Database reset complete")