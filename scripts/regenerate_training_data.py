#!/usr/bin/env python
"""Regenerate training data from .skills golden examples.

This script reads the skill files from .skills/ and generates updated
trainset.json and gold_skills.json files with v2 Golden Standard format.
"""

import json
import re
from pathlib import Path
from typing import Any

import yaml


def extract_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter and body from markdown content."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    try:
        frontmatter = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        frontmatter = {}

    body = parts[2].strip()
    return frontmatter, body


def detect_skill_style(body: str, subdirs: dict[str, list[str]]) -> str:
    """Detect skill style based on content characteristics."""
    body_length = len(body)
    has_many_subdirectory_refs = (
        len(re.findall(r"(?:references|guides|templates|scripts|examples)/", body, re.IGNORECASE))
        >= 3
    )
    has_detailed_sections = len(re.findall(r"^##\s+", body, re.MULTILINE)) >= 5
    total_subdir_files = sum(len(files) for files in subdirs.values())

    if body_length < 4000 and (has_many_subdirectory_refs or total_subdir_files >= 2):
        return "navigation_hub"
    elif body_length > 8000 or has_detailed_sections:
        return "comprehensive"
    else:
        return "minimal"


def process_skill_directory(skill_dir: Path) -> dict[str, Any] | None:
    """Process a single skill directory and extract data."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None

    content = skill_md.read_text()
    frontmatter, body = extract_frontmatter(content)

    if not frontmatter.get("name"):
        print(f"  Skipping {skill_dir.name}: Missing name in frontmatter")
        return None

    # Collect subdirectory files
    subdirs: dict[str, list[str]] = {}
    for subdir_name in ["references", "guides", "templates", "scripts", "examples"]:
        subdir_path = skill_dir / subdir_name
        if subdir_path.exists() and subdir_path.is_dir():
            files = [f.name for f in subdir_path.glob("*.md")]
            if files:
                subdirs[subdir_name] = sorted(files)

    skill_style = detect_skill_style(body, subdirs)

    # Extract sections for quality assessment
    has_when_to_use = bool(re.search(r"##\s*When\s+to\s+Use", body, re.IGNORECASE))
    has_quick_start = bool(
        re.search(r"##\s*(Quick\s+Start|Quick\s+Examples?)", body, re.IGNORECASE)
    )
    has_overview = bool(re.search(r"##\s*(Overview|Introduction|Purpose)", body, re.IGNORECASE))

    return {
        "skill_id": f".skills/{skill_dir.name}",
        "name": frontmatter.get("name"),
        "description": frontmatter.get("description", ""),
        "allowed_tools": frontmatter.get("allowed-tools", []),
        "skill_style": skill_style,
        "subdirectory_files": subdirs,
        "structure": {
            "has_when_to_use": has_when_to_use,
            "has_quick_start": has_quick_start,
            "has_overview": has_overview,
        },
        "skill_path": str(skill_md.relative_to(skill_dir.parent.parent)),
        "content_length": len(body),
        "source": "golden_example",
    }


def generate_trainset_entry(skill_data: dict[str, Any]) -> dict[str, Any]:
    """Generate a trainset.json entry from skill data."""
    name = skill_data["name"]
    description = skill_data["description"]

    # Infer task description from skill
    task_description = f"Create a {name.replace('-', ' ')} skill: {description}"

    # Infer taxonomy path (simplified for v2)
    parts = name.split("-")
    if len(parts) >= 2:
        expected_taxonomy = f"{parts[0]}/{name}"
    else:
        expected_taxonomy = f"general/{name}"

    # Infer capabilities from name and description
    keywords = name.split("-")
    for word in ["and", "the", "for", "with"]:
        if word in keywords:
            keywords.remove(word)

    return {
        "task_description": task_description,
        "expected_taxonomy_path": expected_taxonomy,
        "expected_name": name,
        "expected_skill_style": skill_data["skill_style"],
        "expected_subdirectories": list(skill_data.get("subdirectory_files", {}).keys()),
        "expected_keywords": keywords,
        "expected_description": description[:200],  # Truncate long descriptions
        "source": "golden_example",
    }


def main():
    """Main function to regenerate training data."""
    skills_dir = Path(".skills")
    if not skills_dir.exists():
        print("Error: .skills directory not found")
        return

    gold_skills = []
    trainset = []

    print("Processing .skills golden examples...")
    for item in sorted(skills_dir.iterdir()):
        if item.is_dir():
            # Check for nested skills (like neon-db/)
            nested_skills = [d for d in item.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
            if nested_skills:
                # Process nested skills
                for nested in nested_skills:
                    print(f"  Processing nested: {item.name}/{nested.name}")
                    skill_data = process_skill_directory(nested)
                    if skill_data:
                        skill_data["skill_id"] = f".skills/{item.name}/{nested.name}"
                        skill_data["skill_path"] = f".skills/{item.name}/{nested.name}/SKILL.md"
                        gold_skills.append(skill_data)
                        trainset.append(generate_trainset_entry(skill_data))
            elif (item / "SKILL.md").exists():
                # Process top-level skill
                print(f"  Processing: {item.name}")
                skill_data = process_skill_directory(item)
                if skill_data:
                    gold_skills.append(skill_data)
                    trainset.append(generate_trainset_entry(skill_data))

    # Save gold_skills.json
    gold_output = {
        "version": "2.0",
        "description": "Golden skill examples extracted from .skills/ directory",
        "skills": gold_skills,
    }
    with open("config/training/gold_skills_v2.json", "w") as f:
        json.dump(gold_output, f, indent=2)
    print(f"\nGenerated config/training/gold_skills_v2.json with {len(gold_skills)} skills")

    # Save trainset_v2.json
    with open("config/training/trainset_v2.json", "w") as f:
        json.dump(trainset, f, indent=2)
    print(f"Generated config/training/trainset_v2.json with {len(trainset)} examples")


if __name__ == "__main__":
    main()
