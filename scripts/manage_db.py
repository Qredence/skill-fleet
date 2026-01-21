#!/usr/bin/env python3
"""
Unified Database Management Script for Skill Fleet.

Handles migrations, seeding, and verification.
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Import existing utilities if available
try:
    from scripts.internal.db.seed_taxonomy import seed_taxonomy
except ImportError:
    seed_taxonomy = None

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL and not DATABASE_URL.startswith("postgresql+"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")


def get_migration_script_path() -> str:
    """Get path to migration SQL file."""
    root = Path(__file__).resolve().parents[1]
    return str(root / "migrations" / "001_init_skills_schema.sql")


def split_sql_script(script: str) -> list[str]:
    """Split SQL script into individual statements, handling PostgreSQL dollar quotes."""
    statements = []
    current = []
    in_body = False

    for line in script.split("\n"):
        if "$$" in line:
            if not in_body:
                in_body = True
                current.append(line)
                continue
            elif in_body:
                in_body = False
                current.append(line)
                if ";" in line:
                    stmt = "\n".join(current).strip()
                    if stmt:
                        statements.append(stmt)
                    current = []
                continue

        current.append(line)

        if not in_body and line.strip().endswith(";"):
            stmt = "\n".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []

    if current:
        stmt = "\n".join(current).strip()
        if stmt:
            statements.append(stmt)

    return statements


def run_migration(check: bool = False):
    """Run database migration."""
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        sys.exit(1)

    print(f"Connecting to {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'db'}...")
    engine = create_engine(DATABASE_URL)

    if check:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            sys.exit(1)

    migration_path = get_migration_script_path()
    if not os.path.exists(migration_path):
        print(f"❌ Migration file not found: {migration_path}")
        sys.exit(1)

    with open(migration_path) as f:
        sql = f.read()

    statements = split_sql_script(sql)
    print(f"Applying {len(statements)} statements...")

    with engine.begin() as conn:
        for stmt in statements:
            if not stmt.strip() or stmt.strip().startswith("--"):
                continue
            try:
                conn.execute(text(stmt))
            except Exception as e:
                print(f"❌ Error executing statement:\n{stmt[:100]}...\nError: {e}")
                if "already exists" in str(e):
                    print("   (Ignored 'already exists' error)")
                    continue
                sys.exit(1)

    print("✅ Migration complete")


def run_seed():
    """Run taxonomy seeding."""
    if seed_taxonomy:
        print("Seeding taxonomy...")
        seed_taxonomy()
    else:
        print("❌ seed_taxonomy module not found")
        sys.exit(1)


def verify_db():
    """Verify database state."""
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set")
        sys.exit(1)

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        # Check tables
        result = conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        )
        tables = [row[0] for row in result]
        print(f"Found {len(tables)} tables: {', '.join(tables)}")

        if "taxonomy_categories" in tables:
            count = conn.execute(text("SELECT COUNT(*) FROM taxonomy_categories")).scalar()
            print(f"Taxonomy categories: {count}")


def main():
    parser = argparse.ArgumentParser(description="Skill Fleet Database Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    subparsers.add_parser("init", help="Run migration and seed")
    subparsers.add_parser("migrate", help="Run only migration")
    subparsers.add_parser("seed", help="Run only seeding")
    subparsers.add_parser("verify", help="Verify database state")

    args = parser.parse_args()

    if args.command == "init":
        run_migration()
        run_seed()
    elif args.command == "migrate":
        run_migration()
    elif args.command == "seed":
        run_seed()
    elif args.command == "verify":
        verify_db()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
