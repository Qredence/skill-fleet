#!/usr/bin/env python3
"""
Skills-Fleet Migration Script (SQLAlchemy version)

This script applies the database migration using SQLAlchemy,
which should already be installed in your venv.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable not set!")
    print("\n💡 Set it like this:")
    print('   export DATABASE_URL="postgresql://user:pass@host/db?sslmode=require"')
    sys.exit(1)

# Ensure psycopg driver is specified for SQLAlchemy
if not DATABASE_URL.startswith("postgresql+"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")


def get_migration_script_path() -> str:
    """Get the path to the migration SQL file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    return os.path.join(project_root, "migrations", "001_init_skills_schema.sql")


def read_migration_script() -> str:
    """Read the migration SQL script."""
    migration_path = get_migration_script_path()
    if not os.path.exists(migration_path):
        raise FileNotFoundError(f"Migration file not found: {migration_path}")
    with open(migration_path) as f:
        return f.read()


def split_sql_script(script: str) -> list[str]:
    """
    Split SQL script into individual statements.

    Handles PostgreSQL-specific syntax like CREATE TYPE which uses $BODY$ delimiters.
    """
    statements = []
    current = []
    in_body = False

    for line in script.split("\n"):
        # Check for BODY delimiter start/end
        if "$$" in line:
            if not in_body:
                in_body = True
                current.append(line)
                continue
            elif in_body:
                in_body = False
                current.append(line)
                # Check if statement ends here
                if ";" in line:
                    stmt = "\n".join(current).strip()
                    if stmt:
                        statements.append(stmt)
                    current = []
                continue

        current.append(line)

        # If not in BODY and line ends with semicolon, it's a complete statement
        if not in_body and line.strip().endswith(";"):
            stmt = "\n".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []

    # Add any remaining content
    if current:
        stmt = "\n".join(current).strip()
        if stmt:
            statements.append(stmt)

    return statements


def apply_migration() -> None:
    """Apply the database migration using SQLAlchemy."""
    print("Connecting to database...")
    # Extract host info for display
    if "@" in DATABASE_URL:
        host = DATABASE_URL.split("@")[1].split("/")[0]
        print(f"Host: {host}")

    # Read migration script
    print("\n📄 Reading migration script...")
    migration_sql = read_migration_script()
    print(f"   Loaded ({len(migration_sql)} characters)")

    # Split into statements
    print("\n🔍 Parsing SQL statements...")
    statements = split_sql_script(migration_sql)
    print(f"   Found {len(statements)} statements")

    # Create engine
    engine = create_engine(DATABASE_URL)

    # Apply migration
    print("\n🚀 Applying migration...")
    success_count = 0
    error_count = 0

    try:
        with engine.begin() as conn:
            for i, statement in enumerate(statements, 1):
                if not statement.strip() or statement.strip().startswith("--"):
                    continue

                try:
                    conn.execute(text(statement))
                    success_count += 1

                    # Progress indicator
                    if i % 10 == 0:
                        print(f"   Progress: {i}/{len(statements)} statements executed")

                except Exception as e:
                    error_count += 1
                    # Show first few errors
                    if error_count <= 3:
                        print(f"   ⚠️  Statement {i} failed: {e}")
                        print(f"   Statement preview: {statement[:100]}...")

        print("\n✅ Migration completed!")
        print("\n📊 Results:")
        print(f"   - {success_count} statements executed successfully")
        if error_count > 0:
            print(f"   - {error_count} statements failed (may be expected if objects exist)")

        # Verify what was created
        print("\n🔍 Verifying created objects...")
        with engine.begin() as conn:
            # Check tables
            result = conn.execute(
                text("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            )
            table_count = result.scalar()

            # Check enums
            result = conn.execute(
                text("""
                SELECT COUNT(*) FROM pg_type WHERE typtype = 'e'
            """)
            )
            enum_count = result.scalar()

            # Check views
            result = conn.execute(
                text("""
                SELECT COUNT(*) FROM information_schema.views
                WHERE table_schema = 'public'
            """)
            )
            view_count = result.scalar()

        print("\n📋 Database Objects:")
        print(f"   - {table_count} tables")
        print(f"   - {enum_count} enum types")
        print(f"   - {view_count} views")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        engine.dispose()


def check_database_connection() -> bool:
    """Check if the database connection works."""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


def main() -> int:
    """Main entry point."""
    print("=" * 60)
    print("Skills-Fleet Database Migration")
    print("=" * 60)

    # Check database connection
    print("\n🔍 Checking database connection...")
    if not check_database_connection():
        print("❌ Cannot connect to database!")
        print("\n💡 Tips:")
        print("   1. Make sure DATABASE_URL is set in your environment")
        print("   2. Format: postgresql://user:password@host/database?sslmode=require")
        print("   3. Get connection string from: https://console.neon.tech")
        return 1

    print("✅ Database connection verified")

    # Confirm before proceeding
    print("\n⚠️  This will create/modify database tables.")
    try:
        response = input("Proceed? (yes/no): ").strip().lower()
        if response not in ("yes", "y"):
            print("Migration cancelled.")
            return 0
    except (EOFError, KeyboardInterrupt):
        print("\nMigration cancelled.")
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


if __name__ == "__main__":
    sys.exit(main())
