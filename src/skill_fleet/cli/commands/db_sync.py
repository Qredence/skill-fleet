"""
Database Export/Import Commands for Skill Fleet

Export skills from local directory to database, and import from database to local directory.
"""

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
import os
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

console = Console()


def export_to_db_command(
    skills_dir: str = typer.Option(
        ".skills",
        "--skills-dir",
        "-s",
        help="Directory containing skill files (SKILL.md)",
        envvar="SKILL_FLEET_SKILLS_DIR"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Preview changes without writing to database"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force overwrite of existing skills in database"
    ),
):
    """
    Export skills from local directory to Neon database.

    This command reads SKILL.md files from the local skills directory
    and imports them into the Neon database with full metadata.

    Example:
        skill-fleet export-to-db
        skill-fleet export-to-db --dry-run
        skill-fleet export-to-db --skills-dir ./skills --force
    """
    try:
        # Import here to avoid issues if DATABASE_URL not set
        from scripts.import_skills import SkillImporter
        from dotenv import load_dotenv

        load_dotenv()

        # Resolve skills directory path
        skills_path = Path(skills_dir).resolve()
        if not skills_path.exists():
            console.print(f"[red]✗ Skills directory not found: {skills_path}[/red]")
            raise typer.Exit(1)

        # Get DATABASE_URL
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            console.print("[red]✗ DATABASE_URL not set in environment[/red]")
            raise typer.Exit(1)

        # Create importer
        importer = SkillImporter(str(skills_path), db_url)

        # Run import
        console.print(f"\n[bold]Exporting skills to database...[/bold]")
        console.print(f"Source: {skills_path}")
        console.print(f"Database: {db_url.split('@')[1] if '@' in db_url else 'unknown'}")

        if dry_run:
            console.print("\n[yellow]⚠️  DRY RUN MODE - No changes will be made[/yellow]")

        stats = importer.import_all(dry_run=dry_run)

        # Print summary
        table = Table(title="Export Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green")

        table.add_row("Created", str(stats['created']))
        table.add_row("Updated", str(stats['updated']))
        table.add_row("Skipped", str(stats['skipped']))
        table.add_row("Errors", str(stats['errors']))

        console.print("\n")
        console.print(table)

        if dry_run:
            console.print("\n[yellow]Run without --dry-run to apply changes.[/yellow]")

        if stats['errors'] > 0:
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"\n[red]✗ Export failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


def import_from_db_command(
    skills_dir: str = typer.Option(
        "skills",
        "--skills-dir",
        "-s",
        help="Directory to write skill files to",
        envvar="SKILL_FLEET_SKILLS_DIR"
    ),
    skill_path: str = typer.Option(
        None,
        "--skill-path",
        "-p",
        help="Import specific skill by path (e.g., 'development/languages/python')"
    ),
    status_filter: str = typer.Option(
        "active",
        "--status",
        help="Filter skills by status (active, draft, all)",
    ),
):
    """
    Import skills from Neon database to local directory.

    This command reads skills from the Neon database and writes
    them as SKILL.md files to the local skills directory.

    Example:
        skill-fleet import-from-db
        skill-fleet import-from-db --skill-path "development/languages/python"
        skill-fleet import-from-db --status draft
    """
    try:
        # Import here to avoid issues if DATABASE_URL not set
        from dotenv import load_dotenv
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        load_dotenv()

        # Get DATABASE_URL
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            console.print("[red]✗ DATABASE_URL not set in environment[/red]")
            raise typer.Exit(1)

        # Normalize database URL
        if db_url and not db_url.startswith("postgresql+"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://")

        # Create database connection
        engine = create_engine(db_url)

        with Session(engine) as session:
            console.print(f"\n[bold]Importing skills from database...[/bold]")
            console.print(f"Target: {skills_dir}")
            console.print(f"Database: {os.getenv('DATABASE_URL', '').split('@')[1] if '@' in os.getenv('DATABASE_URL', '') else 'unknown'}")

            # Build query
            from skill_fleet.db.models import Skill, TaxonomyCategory, SkillCategory, skill_status_enum

            query = session.query(Skill).join(SkillCategory).join(TaxonomyCategory)

            # Apply filters
            if skill_path:
                query = query.filter(Skill.skill_path == skill_path)
                console.print(f"Filter: path='{skill_path}'")
            else:
                if status_filter == "active":
                    query = query.filter(Skill.status == skill_status_enum.active)
                    console.print(f"Filter: status=active")
                elif status_filter == "draft":
                    query = query.filter(Skill.status == skill_status_enum.draft)
                    console.print(f"Filter: status=draft")
                # If "all", no filter

            skills = query.order_by(Skill.skill_path).all()

            if not skills:
                console.print("[yellow]⚠️  No skills found matching criteria[/yellow]")
                return

            # Import skills
            created_count = 0
            updated_count = 0

            for skill in skills:
                # Resolve target directory
                target_dir = Path(skills_dir) / skill.skill_path.replace('/', os.sep)
                target_dir.mkdir(parents=True, exist_ok=True)

                skill_file = target_dir / "SKILL.md"

                # Build YAML frontmatter
                import yaml

                frontmatter = {
                    "name": skill.name,
                    "description": skill.description,
                    "version": skill.version,
                }

                # Add optional fields
                if skill.type:
                    frontmatter["type"] = skill.type.value
                if skill.weight:
                    frontmatter["weight"] = skill.weight.value
                if skill.load_priority:
                    frontmatter["load_priority"] = skill.load_priority.value
                if skill.status:
                    frontmatter["status"] = skill.status.value

                # Add keywords
                if skill.keywords:
                    frontmatter["keywords"] = [kw.keyword for kw in skill.keywords]

                # Add tags
                if skill.tags:
                    frontmatter["tags"] = [t.tag for t in skill.tags]

                # Write file
                content = skill.skill_content or ""

                if skill_file.exists():
                    updated_count += 1
                    console.print(f"  [yellow]→ Updating:[/yellow] {skill.skill_path}")
                else:
                    created_count += 1
                    console.print(f"  [green]→ Created:[/green] {skill.skill_path}")

                with open(skill_file, 'w', encoding='utf-8') as f:
                    # Write YAML frontmatter
                    f.write("---\n")
                    yaml.dump(frontmatter, f, default_flow_style=False, sort_keys=False)
                    f.write("---\n\n")
                    # Write content
                    f.write(content)

            # Print summary
            table = Table(title="Import Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="green")

            table.add_row("Created", str(created_count))
            table.add_row("Updated", str(updated_count))
            table.add_row("Total Imported", str(len(skills)))

            console.print("\n")
            console.print(table)

        engine.dispose()

    except Exception as e:
        console.print(f"\n[red]✗ Import failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        raise typer.Exit(1)


def sync_command(
    skills_dir: str = typer.Option(
        ".skills",
        "--skills-dir",
        "-s",
        help="Directory containing skill files (SKILL.md)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Preview changes without writing"
    ),
):
    """
    Bidirectional sync between local files and database.

    Performs both export and import operations to ensure
    local files and database are synchronized.

    Example:
        skill-fleet sync-db
        skill-fleet sync-db --dry-run
    """
    console.print("[bold]Starting bidirectional sync...[/bold]")
    console.print()

    # First export: local -> database
    console.print("[cyan]1. Exporting local files to database...[/cyan]")
    try:
        export_to_db_command(skills_dir=skills_dir, dry_run=dry_run, force=True)
    except SystemExit as e:
        if e.code != 0:
            console.print("[yellow]Export encountered issues, continuing...[/yellow]")

    console.print()

    # Then import: database -> local
    console.print("[cyan]2. Importing database to local files...[/cyan]")
    try:
        import_from_db_command(skills_dir=skills_dir, status_filter="all")
    except SystemExit as e:
        if e.code != 0:
            console.print("[yellow]Import encountered issues.[/yellow]")

    console.print()
    console.print("[bold green]✓ Sync complete[/bold green]")
