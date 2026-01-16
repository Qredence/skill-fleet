"""Migration utilities for skill fleet taxonomy and format updates."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def migrate_all_skills(
    skills_root_path: Path,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """Migrate skill directories to canonical paths based on taxonomy_index.json.

    Args:
        skills_root_path: Path to skills directory
        dry_run: If True, preview changes without writing
        verbose: If True, print detailed migration progress

    Returns:
        Dict with migration results: {'migrated': count, 'skipped': count, 'failed': count, 'errors': list}
    """
    index_path = skills_root_path / "taxonomy_index.json"

    if not index_path.exists():
        error_msg = "Error: taxonomy_index.json not found"
        if verbose:
            print(error_msg)
        return {
            "migrated": 0,
            "skipped": 0,
            "failed": 1,
            "errors": [error_msg],
        }

    if verbose:
        print("Loading taxonomy index...")

    with open(index_path, encoding="utf-8") as f:
        data = json.load(f)

    skills_map = data.get("skills", {})

    if verbose:
        print(f"Found {len(skills_map)} skills to migrate")

    migrated_count = 0
    skipped_count = 0
    failed_count = 0
    errors = []

    for skill_id, entry in skills_map.items():
        canonical_path = entry.get("canonical_path", "")
        aliases = entry.get("aliases", [])

        if not aliases:
            if verbose:
                print(f"Skipping {skill_id}: No aliases (source path) defined")
            skipped_count += 1
            continue

        # Use first alias as source path
        source_rel_path = aliases[0]
        source_path = skills_root_path / source_rel_path
        dest_path = skills_root_path / canonical_path

        if dest_path.exists():
            if verbose:
                print(f"Skipping {skill_id}: Destination already exists ({canonical_path})")
            skipped_count += 1
            continue

        if not source_path.exists():
            warning_msg = f"Source path not found for {skill_id}: {source_rel_path}"
            if verbose:
                print(f"Warning: {warning_msg}")
            errors.append(warning_msg)
            failed_count += 1
            continue

        if verbose:
            print(f"Migrating {skill_id}...")
            print(f"  From: {source_rel_path}")
            print(f"  To:   {canonical_path}")

        if not dry_run:
            # Create destination parent directories
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                shutil.move(str(source_path), str(dest_path))
                migrated_count += 1
            except Exception as e:
                error_msg = f"ERROR moving {skill_id}: {e}"
                if verbose:
                    print(error_msg)
                errors.append(f"{skill_id}: {e}")
                failed_count += 1
        else:
            migrated_count += 1

    if verbose:
        print(f"\nMigration complete. Moved {migrated_count} skills.")
        if errors:
            print("Errors:")
            for e in errors:
                print(f"  - {e}")
        if not dry_run:
            print("\nCleaning up empty directories...")
            _remove_empty_dirs(skills_root_path)

    return {
        "migrated": migrated_count,
        "skipped": skipped_count,
        "failed": failed_count,
        "errors": errors,
    }


def _remove_empty_dirs(path: Path) -> None:
    """Recursively remove empty directories and .gitkeep files."""
    if not path.is_dir():
        return

    # First pass: Remove all .gitkeep files
    for p in path.rglob(".gitkeep"):
        try:
            p.unlink()
            print(f"Removed: {p.relative_to(path.parent.parent)}")
        except OSError as e:
            print(f"Error removing {p}: {e}")

    # Second pass: Remove empty directories bottom up
    for p in list(path.rglob("*"))[::-1]:
        if p.is_dir():
            try:
                # Don't delete metadata directories or root itself
                if p.name.startswith("_") or p == path:
                    continue
                # Check if empty
                if not any(p.iterdir()):
                    p.rmdir()
                    print(f"Removed empty dir: {p.relative_to(path.parent.parent)}")
            except OSError as e:
                print(f"Error removing directory {p}: {e}")
