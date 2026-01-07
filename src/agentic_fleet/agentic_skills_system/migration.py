"""Migration utilities to convert skills to agentskills.io format.

This module provides tools to migrate existing skills to be compliant
with the agentskills.io specification by adding YAML frontmatter to SKILL.md files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from .taxonomy.manager import skill_id_to_name


def migrate_skill_to_agentskills_format(
    skill_dir: Path,
    dry_run: bool = False,
    verbose: bool = True,
) -> dict[str, Any]:
    """Migrate a single skill directory to agentskills.io format.

    This function:
    1. Reads existing metadata.json
    2. Generates kebab-case name from skill_id
    3. Reads existing SKILL.md content
    4. Prepends YAML frontmatter (if not already present)
    5. Writes updated SKILL.md

    Args:
        skill_dir: Path to the skill directory
        dry_run: If True, don't write changes
        verbose: If True, print progress

    Returns:
        Dict with migration results:
        - success: bool
        - skill_id: str
        - name: str
        - changes: list of changes made
        - errors: list of errors encountered
    """
    result = {
        "success": False,
        "skill_id": "",
        "name": "",
        "changes": [],
        "errors": [],
    }

    # Check for metadata.json
    metadata_path = skill_dir / "metadata.json"
    if not metadata_path.exists():
        result["errors"].append("metadata.json not found")
        return result

    # Load metadata
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        result["errors"].append(f"Invalid JSON in metadata.json: {e}")
        return result

    skill_id = metadata.get("skill_id", "")
    if not skill_id:
        result["errors"].append("Missing skill_id in metadata.json")
        return result

    result["skill_id"] = skill_id

    # Generate kebab-case name (always convert to ensure agentskills.io compliance)
    existing_name = metadata.get("name", "")
    # If existing name isn't valid kebab-case, regenerate it
    if existing_name and re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", existing_name):
        name = existing_name
    else:
        name = skill_id_to_name(skill_id)
    result["name"] = name

    # Get description
    description = metadata.get("description", "")
    if not description:
        # Try to extract from SKILL.md first paragraph
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            content = skill_md_path.read_text(encoding="utf-8")
            # Strip frontmatter if present
            if content.startswith("---"):
                end_marker = content.find("---", 3)
                if end_marker != -1:
                    content = content[end_marker + 3 :]
            # Get first non-empty, non-header paragraph
            for para in content.split("\n\n"):
                para = para.strip()
                if para and not para.startswith("#"):
                    description = re.sub(r"\*+", "", para)[:1024]
                    break

    if not description:
        description = f"Skill for {skill_id.replace('/', ' ').replace('_', ' ')}"

    # Check SKILL.md
    skill_md_path = skill_dir / "SKILL.md"
    if not skill_md_path.exists():
        result["errors"].append("SKILL.md not found")
        return result

    skill_content = skill_md_path.read_text(encoding="utf-8")

    # Check if frontmatter already exists
    if skill_content.startswith("---"):
        end_marker = skill_content.find("---", 3)
        if end_marker != -1:
            # Frontmatter exists, check if it's valid
            try:
                existing_fm = yaml.safe_load(skill_content[3:end_marker])
                if (
                    isinstance(existing_fm, dict)
                    and "name" in existing_fm
                    and "description" in existing_fm
                ):
                    # Check if name is valid kebab-case
                    fm_name = str(existing_fm.get("name", ""))
                    if re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", fm_name):
                        result["changes"].append("Frontmatter already present and valid")
                        result["success"] = True
                        return result
                    else:
                        # Name is not valid kebab-case, regenerate
                        skill_content = skill_content[end_marker + 3 :].lstrip("\n")
                        result["changes"].append(
                            f"Replaced frontmatter with invalid name: {fm_name}"
                        )
            except yaml.YAMLError:
                pass

            # Invalid or incomplete frontmatter, remove it
            if skill_content.startswith("---"):
                # Still has frontmatter, hasn't been stripped yet
                skill_content = skill_content[end_marker + 3 :].lstrip("\n")
                result["changes"].append("Replaced invalid frontmatter")

    # Build frontmatter
    frontmatter = {
        "name": name,
        "description": description[:1024],
    }

    # Add extended metadata
    extended_meta = {}
    if skill_id:
        extended_meta["skill_id"] = skill_id
    if metadata.get("version"):
        extended_meta["version"] = metadata["version"]
    if metadata.get("type"):
        extended_meta["type"] = metadata["type"]
    if metadata.get("weight"):
        extended_meta["weight"] = metadata["weight"]

    if extended_meta:
        frontmatter["metadata"] = extended_meta

    # Generate new SKILL.md content
    yaml_content = yaml.dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    new_content = f"---\n{yaml_content}---\n\n{skill_content}"

    result["changes"].append("Added YAML frontmatter")

    # Update metadata.json with name and description if missing
    metadata_updated = False
    if "name" not in metadata:
        metadata["name"] = name
        metadata_updated = True
        result["changes"].append("Added name to metadata.json")

    if "description" not in metadata:
        metadata["description"] = description
        metadata_updated = True
        result["changes"].append("Added description to metadata.json")

    # Write changes
    if not dry_run:
        skill_md_path.write_text(new_content, encoding="utf-8")

        if metadata_updated:
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    if verbose:
        status = "[DRY RUN] " if dry_run else ""
        print(f"{status}Migrated: {skill_id} -> {name}")
        for change in result["changes"]:
            print(f"  - {change}")

    result["success"] = True
    return result


def migrate_all_skills(
    skills_root: Path,
    dry_run: bool = False,
    verbose: bool = True,
) -> dict[str, Any]:
    """Migrate all skills in taxonomy to agentskills.io format.

    Args:
        skills_root: Root path of the skills taxonomy
        dry_run: If True, don't write changes
        verbose: If True, print progress

    Returns:
        Dict with migration summary:
        - total: int
        - successful: int
        - failed: int
        - skipped: int
        - results: list of individual results
    """
    summary = {
        "total": 0,
        "successful": 0,
        "failed": 0,
        "skipped": 0,
        "results": [],
    }

    # Find all skill directories (those with metadata.json)
    for metadata_path in skills_root.rglob("metadata.json"):
        # Skip template and special directories
        skill_dir = metadata_path.parent
        rel_path = skill_dir.relative_to(skills_root)

        if any(part.startswith("_") for part in rel_path.parts):
            continue

        summary["total"] += 1

        result = migrate_skill_to_agentskills_format(
            skill_dir,
            dry_run=dry_run,
            verbose=verbose,
        )

        summary["results"].append(result)

        if result["success"]:
            if "already present" in str(result.get("changes", [])):
                summary["skipped"] += 1
            else:
                summary["successful"] += 1
        else:
            summary["failed"] += 1

    if verbose:
        print(f"\n{'=' * 60}")
        print("Migration Summary:")
        print(f"  Total skills: {summary['total']}")
        print(f"  Successful: {summary['successful']}")
        print(f"  Skipped (already compliant): {summary['skipped']}")
        print(f"  Failed: {summary['failed']}")

    return summary


def validate_migration(skills_root: Path) -> dict[str, Any]:
    """Validate that all skills have valid agentskills.io frontmatter.

    Returns:
        Dict with validation results
    """
    from .validators.skill_validator import SkillValidator

    validator = SkillValidator(skills_root)
    results = {
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "issues": [],
    }

    for metadata_path in skills_root.rglob("metadata.json"):
        skill_dir = metadata_path.parent
        rel_path = skill_dir.relative_to(skills_root)

        if any(part.startswith("_") for part in rel_path.parts):
            continue

        results["total"] += 1

        skill_md_path = skill_dir / "SKILL.md"
        fm_result = validator.validate_frontmatter(skill_md_path)

        if fm_result.passed:
            results["valid"] += 1
        else:
            results["invalid"] += 1
            results["issues"].append(
                {
                    "skill": str(rel_path),
                    "errors": fm_result.errors,
                    "warnings": fm_result.warnings,
                }
            )

    return results
