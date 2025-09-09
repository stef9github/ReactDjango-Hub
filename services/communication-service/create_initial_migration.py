#!/usr/bin/env python3
"""
Create initial Alembic migration for Communication Service
Run this script to generate the first migration file
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Create initial database migration"""
    print("🔧 Creating initial database migration for Communication Service...")
    
    # Ensure we're in the right directory
    service_dir = Path(__file__).parent
    os.chdir(service_dir)
    
    try:
        # Generate initial migration
        print("📝 Generating initial migration...")
        result = subprocess.run([
            "alembic", "revision", "--autogenerate", 
            "-m", "Initial database schema with all communication models"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Initial migration created successfully!")
            print(f"📋 Output: {result.stdout}")
            
            # List migration files
            migrations_dir = service_dir / "alembic" / "versions"
            if migrations_dir.exists():
                migration_files = list(migrations_dir.glob("*.py"))
                if migration_files:
                    print(f"📁 Migration files created: {len(migration_files)}")
                    for file in migration_files:
                        print(f"   - {file.name}")
            
            print("\n🚀 Next steps:")
            print("1. Review the generated migration file in alembic/versions/")
            print("2. Run 'alembic upgrade head' to apply the migration")
            print("3. Start the Communication Service with 'python main.py'")
            
        else:
            print("❌ Failed to create migration!")
            print(f"Error: {result.stderr}")
            return 1
            
    except FileNotFoundError:
        print("❌ Alembic not found! Please install requirements.txt first:")
        print("   pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Error creating migration: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())