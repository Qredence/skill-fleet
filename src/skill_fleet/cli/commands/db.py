"""Database management commands.

Provides CLI commands for:
- Initializing database schema
- Checking database health
- Resetting database (dev only)
"""

from __future__ import annotations

import logging
from typing import Optional

import typer

logger = logging.getLogger(__name__)

db_app = typer.Typer(help="Database management commands", invoke_without_command=False)


@db_app.command()
def init(
    force: bool = typer.Option(
        False,
        "--force",
        help="Force re-creation of all tables (WARNING: will delete data)",
    ),
) -> None:
    """Initialize database schema.
    
    Creates all necessary tables for skills-fleet persistence.
    Idempotent - safe to run multiple times.
    """
    from skill_fleet.db.database import init_db, drop_db, SessionLocal
    from skill_fleet.db.models import Job, Skill, HITLInteraction
    
    try:
        if force:
            typer.confirm(
                "⚠️  This will DELETE all data. Are you sure?",
                abort=True,
            )
            logger.info("Dropping all tables...")
            drop_db()
            logger.info("✅ Tables dropped")
        
        logger.info("Initializing database schema...")
        init_db()
        logger.info("✅ Database schema initialized")
        
        # Verify tables exist
        session = SessionLocal()
        try:
            # Try a simple query to each main table
            session.query(Skill).first()
            session.query(Job).first()
            session.query(HITLInteraction).first()
            logger.info("✅ All tables verified")
        finally:
            session.close()
        
        typer.echo("\n✅ Database initialized successfully!\n")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        typer.echo(f"\n❌ Error: {e}\n", err=True)
        raise typer.Exit(1)


@db_app.command()
def status() -> None:
    """Check database connection and table status.
    
    Verifies that the database is accessible and all required
    tables exist.
    """
    from skill_fleet.db.database import SessionLocal
    from skill_fleet.db.models import Job, Skill, HITLInteraction, TaxonomyCategory
    
    try:
        session = SessionLocal()
        try:
            # Check connection
            session.execute("SELECT 1")
            logger.info("✅ Database connection OK")
            
            # Check tables
            tables_to_check = [
                ("skills", Skill),
                ("jobs", Job),
                ("hitl_interactions", HITLInteraction),
                ("taxonomy_categories", TaxonomyCategory),
            ]
            
            all_ok = True
            for table_name, model_class in tables_to_check:
                try:
                    count = session.query(model_class).count()
                    typer.echo(f"  ✅ {table_name:30s} ({count:4d} rows)")
                except Exception as e:
                    typer.echo(f"  ❌ {table_name:30s} (error: {str(e)[:50]})")
                    all_ok = False
            
            if all_ok:
                typer.echo("\n✅ Database status: OK\n")
            else:
                typer.echo("\n⚠️  Database status: Some tables missing\n")
                raise typer.Exit(1)
                
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}", exc_info=True)
        typer.echo(f"\n❌ Error: {e}\n", err=True)
        raise typer.Exit(1)


@db_app.command()
def migrate() -> None:
    """Run database migrations.
    
    Currently, migrations are handled automatically via SQLAlchemy
    in the init command. This is a placeholder for future migration
    system integration (e.g., Alembic).
    """
    typer.echo("✅ Database migrations are handled automatically.")
    typer.echo("   Run 'skill-fleet db init' to initialize the schema.\n")


@db_app.command(name="reset")
def reset_db(
    force: bool = typer.Option(
        False,
        "--force",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Reset database to empty state (DEVELOPMENT ONLY).
    
    WARNING: This will delete ALL data. Use only in development.
    """
    if not force:
        typer.confirm(
            "⚠️  This will DELETE ALL DATA. This operation cannot be undone.\n"
            "   Are you sure you want to continue?",
            abort=True,
        )
    
    from skill_fleet.db.database import drop_db, init_db
    
    try:
        logger.info("Dropping database...")
        drop_db()
        logger.info("✅ Database dropped")
        
        logger.info("Re-initializing database...")
        init_db()
        logger.info("✅ Database re-initialized")
        
        typer.echo("\n✅ Database reset successfully!\n")
        
    except Exception as e:
        logger.error(f"Failed to reset database: {e}", exc_info=True)
        typer.echo(f"\n❌ Error: {e}\n", err=True)
        raise typer.Exit(1)
