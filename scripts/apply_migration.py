#!/usr/bin/env python3
"""
Skills-Fleet Migration Script

This script applies the database migration to your Neon database.
Run this script to initialize the database schema.
"""

import os
import sys

import psycopg
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skill_fleet.db.database import DATABASE_URL

# Load environment variables
load_dotenv()


def get_migration_script_path() -> str:
    """Get the path to the migration SQL file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    return os.path.join(project_root, 'migrations', '001_init_skills_schema.sql')


def read_migration_script() -> str:
    """Read the migration SQL script."""
    migration_path = get_migration_script_path()
    if not os.path.exists(migration_path):
        raise FileNotFoundError(f"Migration file not found: {migration_path}")
    with open(migration_path, 'r') as f:
        return f.read()


def apply_migration() -> None:
    """
    Apply the database migration to Neon.

    This will:
    1. Connect to your Neon database
    2. Execute the migration SQL script
    3. Create all tables, indexes, enums, and views
    """
    # Get database URL from environment or default
    database_url = os.getenv('DATABASE_URL', DATABASE_URL)

    print(f"Connecting to Neon database...")
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")

    # Read migration script
    print("\n📄 Reading migration script...")
    migration_sql = read_migration_script()
    print(f"   Migration script loaded ({len(migration_sql)} characters)")

    # Connect and apply migration
    print("\n🚀 Applying migration...")
    try:
        with psycopg.connect(database_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                # Execute the migration
                cur.execute(migration_sql)

                # Verify tables were created
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """)
                tables = [row[0] for row in cur.fetchall()]

                # Verify enums were created
                cur.execute("""
                    SELECT typname
                    FROM pg_type
                    WHERE typtype = 'e'
                    ORDER BY typname;
                """)
                enums = [row[0] for row in cur.fetchall()]

                # Verify views were created
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.views
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """)
                views = [row[0] for row in cur.fetchall()]

        print("\n✅ Migration applied successfully!")
        print(f"\n📊 Summary:")
        print(f"   - {len(tables)} tables created")
        print(f"   - {len(enums)} enum types created")
        print(f"   - {len(views)} views created")
        print(f"\n📋 Tables:")
        for table in tables[:10]:  # Show first 10
            print(f"   - {table}")
        if len(tables) > 10:
            print(f"   ... and {len(tables) - 10} more")
        print(f"\n🔷 Enums:")
        for enum in enums:
            print(f"   - {enum}")
        print(f"\n👁️  Views:")
        for view in views:
            print(f"   - {view}")

    except psycopg.Error as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)


def check_database_exists() -> bool:
    """Check if the database connection works."""
    database_url = os.getenv('DATABASE_URL', DATABASE_URL)
    try:
        with psycopg.connect(database_url, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
    except psycopg.Error:
        return False


def main() -> int:
    """Main entry point."""
    print("=" * 60)
    print("Skills-Fleet Database Migration")
    print("=" * 60)

    # Check database connection
    print("\n🔍 Checking database connection...")
    if not check_database_exists():
        print("❌ Cannot connect to database!")
        print("\n💡 Tips:")
        print("   1. Make sure DATABASE_URL is set in your environment")
        print("   2. Format: postgresql://user:password@host/database?sslmode=require")
        print("   3. Get connection string from: https://console.neon.tech")
        return 1

    print("✅ Database connection verified")

    # Confirm before proceeding
    print("\n⚠️  This will create/modify database tables.")
    response = input("Proceed? (yes/no): ").strip().lower()
    if response not in ('yes', 'y'):
        print("Migration cancelled.")
        return 0

    # Apply migration
    try:
        apply_migration()
        print("\n" + "=" * 60)
        print("Migration complete! 🎉")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
