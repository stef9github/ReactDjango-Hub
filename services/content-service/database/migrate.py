"""
Database migration management for content service.
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import List, Tuple
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine

logger = logging.getLogger(__name__)


class MigrationManager:
    """Handles database migrations for the content service."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL is required")
        
        # Convert to async URL if needed
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.migrations_dir.mkdir(exist_ok=True)
    
    async def create_migrations_table(self, conn: asyncpg.Connection) -> None:
        """Create the migrations tracking table."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                checksum VARCHAR(64) NOT NULL
            )
        """)
        logger.info("Migrations table created/verified")
    
    def get_migration_files(self) -> List[Path]:
        """Get all migration files in order."""
        migration_files = list(self.migrations_dir.glob("*.sql"))
        return sorted(migration_files, key=lambda f: f.name)
    
    def calculate_checksum(self, content: str) -> str:
        """Calculate SHA-256 checksum of migration content."""
        import hashlib
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    async def get_applied_migrations(self, conn: asyncpg.Connection) -> List[Tuple[str, str]]:
        """Get list of applied migrations with checksums."""
        rows = await conn.fetch("SELECT filename, checksum FROM migrations ORDER BY id")
        return [(row['filename'], row['checksum']) for row in rows]
    
    async def apply_migration(self, conn: asyncpg.Connection, migration_file: Path) -> None:
        """Apply a single migration file."""
        content = migration_file.read_text()
        checksum = self.calculate_checksum(content)
        
        logger.info(f"Applying migration: {migration_file.name}")
        
        try:
            # Execute the migration in a transaction
            async with conn.transaction():
                await conn.execute(content)
                await conn.execute(
                    "INSERT INTO migrations (filename, checksum) VALUES ($1, $2)",
                    migration_file.name,
                    checksum
                )
            logger.info(f"Successfully applied migration: {migration_file.name}")
        except Exception as e:
            logger.error(f"Failed to apply migration {migration_file.name}: {e}")
            raise
    
    async def verify_migration(self, conn: asyncpg.Connection, filename: str, checksum: str) -> bool:
        """Verify that a migration hasn't been modified."""
        migration_file = self.migrations_dir / filename
        if not migration_file.exists():
            logger.warning(f"Migration file not found: {filename}")
            return False
        
        content = migration_file.read_text()
        current_checksum = self.calculate_checksum(content)
        
        if current_checksum != checksum:
            logger.error(
                f"Migration checksum mismatch for {filename}. "
                f"Expected: {checksum}, Got: {current_checksum}"
            )
            return False
        
        return True
    
    async def run_migrations(self, verify_checksums: bool = True) -> None:
        """Run all pending migrations."""
        # Parse connection URL for direct asyncpg connection
        from urllib.parse import urlparse
        parsed = urlparse(self.database_url.replace("postgresql+asyncpg://", "postgresql://"))
        
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:] if parsed.path else None
        )
        
        try:
            await self.create_migrations_table(conn)
            
            # Get applied migrations
            applied_migrations = await self.get_applied_migrations(conn)
            applied_filenames = {filename for filename, _ in applied_migrations}
            
            # Verify existing migrations if requested
            if verify_checksums:
                for filename, checksum in applied_migrations:
                    if not await self.verify_migration(conn, filename, checksum):
                        raise ValueError(f"Migration verification failed for: {filename}")
                logger.info("All existing migrations verified successfully")
            
            # Get pending migrations
            migration_files = self.get_migration_files()
            pending_migrations = [f for f in migration_files if f.name not in applied_filenames]
            
            if not pending_migrations:
                logger.info("No pending migrations")
                return
            
            logger.info(f"Found {len(pending_migrations)} pending migrations")
            
            # Apply pending migrations
            for migration_file in pending_migrations:
                await self.apply_migration(conn, migration_file)
            
            logger.info("All migrations applied successfully")
        
        finally:
            await conn.close()
    
    async def create_migration(self, name: str, content: str = None) -> Path:
        """Create a new migration file."""
        import time
        
        # Generate timestamp prefix
        timestamp = str(int(time.time()))
        filename = f"{timestamp}_{name.replace(' ', '_').lower()}.sql"
        migration_file = self.migrations_dir / filename
        
        if content is None:
            content = f"""-- Migration: {name}
-- Created: {timestamp}

-- Add your SQL statements here

"""
        
        migration_file.write_text(content)
        logger.info(f"Created migration file: {filename}")
        return migration_file
    
    async def rollback_migration(self, filename: str) -> None:
        """Rollback a specific migration (if rollback script exists)."""
        rollback_file = self.migrations_dir / f"rollback_{filename}"
        if not rollback_file.exists():
            raise ValueError(f"No rollback script found for migration: {filename}")
        
        from urllib.parse import urlparse
        parsed = urlparse(self.database_url.replace("postgresql+asyncpg://", "postgresql://"))
        
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:] if parsed.path else None
        )
        
        try:
            content = rollback_file.read_text()
            logger.info(f"Rolling back migration: {filename}")
            
            async with conn.transaction():
                await conn.execute(content)
                await conn.execute("DELETE FROM migrations WHERE filename = $1", filename)
            
            logger.info(f"Successfully rolled back migration: {filename}")
        
        finally:
            await conn.close()
    
    async def migration_status(self) -> None:
        """Show migration status."""
        from urllib.parse import urlparse
        parsed = urlparse(self.database_url.replace("postgresql+asyncpg://", "postgresql://"))
        
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:] if parsed.path else None
        )
        
        try:
            await self.create_migrations_table(conn)
            
            applied_migrations = await self.get_applied_migrations(conn)
            migration_files = self.get_migration_files()
            
            print("\nMigration Status:")
            print("================")
            
            for migration_file in migration_files:
                status = "APPLIED" if migration_file.name in [f[0] for f in applied_migrations] else "PENDING"
                print(f"{migration_file.name}: {status}")
            
            print(f"\nTotal migrations: {len(migration_files)}")
            print(f"Applied: {len(applied_migrations)}")
            print(f"Pending: {len(migration_files) - len(applied_migrations)}")
        
        finally:
            await conn.close()


async def main():
    """CLI interface for migration management."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [migrate|status|create <name>|rollback <filename>]")
        return
    
    command = sys.argv[1]
    manager = MigrationManager()
    
    try:
        if command == "migrate":
            await manager.run_migrations()
        elif command == "status":
            await manager.migration_status()
        elif command == "create" and len(sys.argv) > 2:
            name = " ".join(sys.argv[2:])
            await manager.create_migration(name)
        elif command == "rollback" and len(sys.argv) > 2:
            filename = sys.argv[2]
            await manager.rollback_migration(filename)
        else:
            print("Invalid command or missing arguments")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())