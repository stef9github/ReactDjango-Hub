#!/usr/bin/env python3
"""
Database migration management script for Identity Service
Provides safe database migration operations with backup and rollback capabilities
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from typing import Optional
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('migration.log')
    ]
)

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handles database migration operations"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL must be provided via environment or parameter")
        
        # Set environment for Alembic
        os.environ['DATABASE_URL'] = self.database_url
    
    def run_command(self, command: list) -> bool:
        """Run a command and return success status"""
        try:
            logger.info(f"Running: {' '.join(command)}")
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            if result.stdout:
                logger.info(f"Output: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            if e.stderr:
                logger.error(f"Error: {e.stderr}")
            return False
    
    def check_database_connection(self) -> bool:
        """Check if database is accessible"""
        logger.info("Checking database connection...")
        try:
            # Simple connection test using Alembic
            return self.run_command(['alembic', 'current'])
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def get_current_revision(self) -> Optional[str]:
        """Get the current database revision"""
        try:
            result = subprocess.run(['alembic', 'current'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None
    
    def list_migrations(self):
        """List all available migrations"""
        logger.info("Available migrations:")
        return self.run_command(['alembic', 'history', '--verbose'])
    
    def migrate_to_latest(self, dry_run: bool = False) -> bool:
        """Migrate to the latest revision"""
        logger.info("Migrating to latest revision...")
        
        if dry_run:
            logger.info("DRY RUN MODE - No actual changes will be made")
            return self.run_command(['alembic', 'upgrade', 'head', '--sql'])
        
        # Check current revision
        current = self.get_current_revision()
        logger.info(f"Current revision: {current}")
        
        # Perform migration
        success = self.run_command(['alembic', 'upgrade', 'head'])
        
        if success:
            new_revision = self.get_current_revision()
            logger.info(f"Migration successful! New revision: {new_revision}")
        
        return success
    
    def migrate_to_revision(self, revision: str, dry_run: bool = False) -> bool:
        """Migrate to a specific revision"""
        logger.info(f"Migrating to revision: {revision}")
        
        if dry_run:
            logger.info("DRY RUN MODE - No actual changes will be made")
            return self.run_command(['alembic', 'upgrade', revision, '--sql'])
        
        return self.run_command(['alembic', 'upgrade', revision])
    
    def rollback_to_revision(self, revision: str, dry_run: bool = False) -> bool:
        """Rollback to a specific revision"""
        logger.info(f"Rolling back to revision: {revision}")
        
        if dry_run:
            logger.info("DRY RUN MODE - No actual changes will be made")
            return self.run_command(['alembic', 'downgrade', revision, '--sql'])
        
        return self.run_command(['alembic', 'downgrade', revision])
    
    def generate_migration_sql(self, output_file: str = None) -> bool:
        """Generate SQL for migration without executing"""
        output_file = output_file or f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        logger.info(f"Generating migration SQL to: {output_file}")
        
        with open(output_file, 'w') as f:
            try:
                result = subprocess.run(['alembic', 'upgrade', 'head', '--sql'], 
                                      capture_output=True, text=True, check=True)
                f.write(result.stdout)
                logger.info(f"Migration SQL saved to: {output_file}")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to generate SQL: {e}")
                return False
    
    def create_database_backup(self, backup_file: str = None) -> Optional[str]:
        """Create a database backup (PostgreSQL)"""
        if not backup_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"identity_service_backup_{timestamp}.sql"
        
        logger.info(f"Creating database backup: {backup_file}")
        
        # Extract database connection details from URL
        # Format: postgresql://user:password@host:port/database
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(self.database_url)
            
            pg_dump_cmd = [
                'pg_dump',
                '-h', parsed.hostname,
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path.lstrip('/'),
                '--verbose',
                '--clean',
                '--no-owner',
                '--no-privileges',
                '-f', backup_file
            ]
            
            # Set password via environment
            env = os.environ.copy()
            if parsed.password:
                env['PGPASSWORD'] = parsed.password
            
            result = subprocess.run(pg_dump_cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Backup created successfully: {backup_file}")
                return backup_file
            else:
                logger.error(f"Backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def restore_database_backup(self, backup_file: str) -> bool:
        """Restore a database backup (PostgreSQL)"""
        logger.info(f"Restoring database from backup: {backup_file}")
        
        if not os.path.exists(backup_file):
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(self.database_url)
            
            psql_cmd = [
                'psql',
                '-h', parsed.hostname,
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path.lstrip('/'),
                '-f', backup_file
            ]
            
            # Set password via environment
            env = os.environ.copy()
            if parsed.password:
                env['PGPASSWORD'] = parsed.password
            
            result = subprocess.run(psql_cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Database restored successfully")
                return True
            else:
                logger.error(f"Restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Identity Service Database Migration Tool')
    parser.add_argument('--database-url', help='Database URL (or use DATABASE_URL env var)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    subparsers.add_parser('status', help='Show current migration status')
    
    # List command  
    subparsers.add_parser('list', help='List all migrations')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate to latest revision')
    migrate_parser.add_argument('--dry-run', action='store_true', help='Show SQL without executing')
    migrate_parser.add_argument('--backup', action='store_true', help='Create backup before migration')
    
    # Migrate to specific revision
    migrate_to_parser = subparsers.add_parser('migrate-to', help='Migrate to specific revision')
    migrate_to_parser.add_argument('revision', help='Target revision')
    migrate_to_parser.add_argument('--dry-run', action='store_true', help='Show SQL without executing')
    migrate_to_parser.add_argument('--backup', action='store_true', help='Create backup before migration')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback to specific revision')
    rollback_parser.add_argument('revision', help='Target revision')
    rollback_parser.add_argument('--dry-run', action='store_true', help='Show SQL without executing')
    rollback_parser.add_argument('--backup', action='store_true', help='Create backup before rollback')
    
    # Generate SQL command
    sql_parser = subparsers.add_parser('generate-sql', help='Generate migration SQL file')
    sql_parser.add_argument('--output', help='Output file name')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('--output', help='Backup file name')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore database backup')
    restore_parser.add_argument('backup_file', help='Backup file to restore')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        migrator = DatabaseMigrator(args.database_url)
        
        if args.command == 'status':
            if not migrator.check_database_connection():
                return 1
            current = migrator.get_current_revision()
            logger.info(f"Current revision: {current}")
            
        elif args.command == 'list':
            migrator.list_migrations()
            
        elif args.command == 'migrate':
            if not migrator.check_database_connection():
                return 1
            
            if hasattr(args, 'backup') and args.backup:
                backup_file = migrator.create_database_backup()
                if not backup_file:
                    logger.error("Backup failed - aborting migration")
                    return 1
            
            success = migrator.migrate_to_latest(args.dry_run)
            return 0 if success else 1
            
        elif args.command == 'migrate-to':
            if not migrator.check_database_connection():
                return 1
            
            if hasattr(args, 'backup') and args.backup:
                backup_file = migrator.create_database_backup()
                if not backup_file:
                    logger.error("Backup failed - aborting migration")
                    return 1
            
            success = migrator.migrate_to_revision(args.revision, args.dry_run)
            return 0 if success else 1
            
        elif args.command == 'rollback':
            if not migrator.check_database_connection():
                return 1
            
            if hasattr(args, 'backup') and args.backup:
                backup_file = migrator.create_database_backup()
                if not backup_file:
                    logger.error("Backup failed - aborting rollback")
                    return 1
            
            success = migrator.rollback_to_revision(args.revision, args.dry_run)
            return 0 if success else 1
            
        elif args.command == 'generate-sql':
            success = migrator.generate_migration_sql(args.output)
            return 0 if success else 1
            
        elif args.command == 'backup':
            backup_file = migrator.create_database_backup(args.output)
            return 0 if backup_file else 1
            
        elif args.command == 'restore':
            if not os.path.exists(args.backup_file):
                logger.error(f"Backup file not found: {args.backup_file}")
                return 1
            success = migrator.restore_database_backup(args.backup_file)
            return 0 if success else 1
        
        return 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())