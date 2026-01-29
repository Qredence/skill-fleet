#!/usr/bin/env python3
"""
Expand training data for DSPy optimization.

This script extracts training examples from existing skills to expand
the trainset from 19 examples to 50-100 examples for better optimization results.

Usage:
    uv run python scripts/expand_training_data.py --output config/training/trainset_v3.json
    uv run python scripts/expand_training_data.py --merge  # Merge with trainset_v2.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml


def parse_skill_frontmatter(skill_content: str) -> dict[str, Any]:
    """Extract YAML frontmatter from SKILL.md content."""
    if not skill_content.startswith("---"):
        return {}

    parts = skill_content.split("---", 2)
    if len(parts) < 3:
        return {}

    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return {}


def detect_skill_style(skill_content: str, skill_path: Path) -> str:
    """Detect skill style based on content characteristics."""
    body_length = len(skill_content)

    # Check for subdirectory references
    subdirectory_refs = len(
        re.findall(
            r"(?:references|guides|templates|scripts|examples)/", skill_content, re.IGNORECASE
        )
    )
    has_many_refs = subdirectory_refs >= 3

    # Check for detailed sections
    section_count = len(re.findall(r"^##\s+", skill_content, re.MULTILINE))
    has_detailed_sections = section_count >= 5

    # Check actual subdirectories
    has_subdirs = any(
        (skill_path.parent / subdir).exists()
        for subdir in ["references", "guides", "templates", "scripts"]
    )

    if body_length < 6000 and (has_many_refs or has_subdirs):
        return "navigation_hub"
    elif body_length > 10000 or has_detailed_sections:
        return "comprehensive"
    else:
        return "minimal"


def get_subdirectories(skill_path: Path) -> list[str]:
    """Get list of subdirectories for a skill."""
    subdirs = []
    skill_dir = skill_path.parent

    for potential_subdir in ["references", "guides", "templates", "scripts", "examples"]:
        if (
            (skill_dir / potential_subdir).exists()
            and (skill_dir / potential_subdir).is_dir()
            and list((skill_dir / potential_subdir).glob("*"))
        ):
            subdirs.append(potential_subdir)

    return subdirs


def extract_keywords_from_description(description: str, name: str) -> list[str]:
    """Extract keywords from description and name."""
    # Start with words from name
    keywords = [word for word in name.split("-") if len(word) > 2]

    # Add important words from description
    description_lower = description.lower()
    important_words = set()

    # Technology keywords
    tech_patterns = [
        r"\b(python|javascript|typescript|react|fastapi|dspy|neon|drizzle)\b",
        r"\b(async|auth|database|api|cli|frontend|backend)\b",
        r"\b(testing|optimization|configuration|deployment)\b",
    ]

    for pattern in tech_patterns:
        matches = re.findall(pattern, description_lower)
        important_words.update(matches)

    keywords.extend(sorted(important_words)[:5])
    return keywords[:7]  # Max 7 keywords


def extract_training_example(skill_path: Path) -> dict[str, Any] | None:
    """Extract a training example from a skill."""
    try:
        skill_content = skill_path.read_text(encoding="utf-8")
        frontmatter = parse_skill_frontmatter(skill_content)

        if not frontmatter.get("name") or not frontmatter.get("description"):
            print(f"  ⚠️  Skipping {skill_path} - missing required frontmatter fields")
            return None

        name = frontmatter["name"]
        description = frontmatter["description"]

        # Determine taxonomy path from file location
        # Path format: .skills/category/skill-name/SKILL.md or skills/category/skill-name/SKILL.md
        parts = skill_path.parts

        # Find the skills or .skills directory
        skills_idx = -1
        for i, part in enumerate(parts):
            if part in ["skills", ".skills"]:
                skills_idx = i
                break

        if skills_idx == -1:
            print(f"  ⚠️  Skipping {skill_path} - cannot determine taxonomy path")
            return None

        # Extract path components after skills/ or .skills/
        path_parts = parts[skills_idx + 1 : -1]  # Exclude SKILL.md filename

        # Handle neon-db special case
        if "neon-db" in path_parts:
            # neon-db/neon-auth -> neon-db/neon-auth
            taxonomy_path = "/".join(path_parts)
        else:
            # category/skill-name
            taxonomy_path = "/".join(path_parts)

        # Detect style and subdirectories
        skill_style = detect_skill_style(skill_content, skill_path)
        subdirs = get_subdirectories(skill_path)
        keywords = extract_keywords_from_description(description, name)

        # Create task description
        task_description = f"Create a {name} skill: {description}"

        training_example = {
            "task_description": task_description,
            "expected_taxonomy_path": taxonomy_path,
            "expected_name": name,
            "expected_skill_style": skill_style,
            "expected_subdirectories": subdirs,
            "expected_keywords": keywords,
            "expected_description": description[:200],  # Truncate for consistency
            "source": "extracted_from_existing",
        }

        print(f"  ✓ Extracted: {name} ({skill_style}, {len(subdirs)} subdirs)")
        return training_example

    except Exception as e:
        print(f"  ✗ Error extracting from {skill_path}: {e}")
        return None


def load_existing_trainset(trainset_path: Path) -> list[dict[str, Any]]:
    """Load existing training set."""
    if not trainset_path.exists():
        return []

    try:
        with trainset_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"  ⚠️  Could not parse {trainset_path}, starting fresh")
        return []


def deduplicate_examples(examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate examples based on expected_name."""
    seen_names = set()
    unique_examples = []

    for example in examples:
        name = example.get("expected_name")
        if name and name not in seen_names:
            seen_names.add(name)
            unique_examples.append(example)

    return unique_examples


def main():
    """
    Expand training data from existing skills.

    Reads skills from the skills directory and generates
    training examples for DSPy optimization.
    """
    parser = argparse.ArgumentParser(description="Expand training data from existing skills")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("config/training/trainset_v3.json"),
        help="Output path for expanded training set",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge with existing trainset_v2.json instead of replacing",
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=Path(".skills"),
        help="Directory containing golden skills",
    )
    parser.add_argument(
        "--additional-skills",
        type=Path,
        default=Path("skills"),
        help="Additional skills directory to scan",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Training Data Expansion Script")
    print("=" * 60)

    # Find all SKILL.md files
    skill_paths = []

    if args.skills_dir.exists():
        skill_paths.extend(args.skills_dir.glob("**/SKILL.md"))
        print(
            f"\n📁 Found {len(list(args.skills_dir.glob('**/SKILL.md')))} skills in {args.skills_dir}"
        )

    if args.additional_skills.exists():
        additional = list(args.additional_skills.glob("**/SKILL.md"))
        skill_paths.extend(additional)
        print(f"📁 Found {len(additional)} skills in {args.additional_skills}")

    skill_paths = sorted(set(skill_paths))
    print(f"\n🎯 Total skills to process: {len(skill_paths)}")

    # Extract examples
    print("\n📝 Extracting training examples...\n")
    new_examples = []

    for skill_path in skill_paths:
        example = extract_training_example(skill_path)
        if example:
            new_examples.append(example)

    print(f"\n✓ Successfully extracted {len(new_examples)} examples")

    # Merge with existing if requested
    if args.merge:
        existing_trainset_path = Path("config/training/trainset_v2.json")
        existing_examples = load_existing_trainset(existing_trainset_path)
        print(f"📦 Loaded {len(existing_examples)} existing examples from {existing_trainset_path}")

        # Combine and deduplicate
        all_examples = existing_examples + new_examples
        all_examples = deduplicate_examples(all_examples)
        print(f"🔧 After deduplication: {len(all_examples)} total examples")
    else:
        all_examples = deduplicate_examples(new_examples)

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Save expanded trainset
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(all_examples, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved {len(all_examples)} training examples to {args.output}")

    # Print statistics
    print("\n" + "=" * 60)
    print("Training Set Statistics")
    print("=" * 60)

    styles = {}
    categories = {}
    sources = {}

    for example in all_examples:
        style = example.get("expected_skill_style", "unknown")
        styles[style] = styles.get(style, 0) + 1

        taxonomy_path = example.get("expected_taxonomy_path", "")
        category = taxonomy_path.split("/")[0] if taxonomy_path else "unknown"
        categories[category] = categories.get(category, 0) + 1

        source = example.get("source", "unknown")
        sources[source] = sources.get(source, 0) + 1

    print(f"\nTotal examples: {len(all_examples)}")
    print(f"\nBy style: {dict(sorted(styles.items()))}")
    print(f"By category: {dict(sorted(categories.items()))}")
    print(f"By source: {dict(sorted(sources.items()))}")

    # Check DSPy best practice thresholds
    print("\n" + "=" * 60)
    print("DSPy Optimization Readiness")
    print("=" * 60)

    if len(all_examples) < 20:
        print("❌ Too few examples (<20) - optimization will be weak")
        print("   Recommendation: Add more synthetic examples or extract from more sources")
    elif len(all_examples) < 50:
        print("⚠️  Marginal example count (20-49) - optimization possible but limited")
        print("   Recommendation: Aim for 50+ examples for robust optimization")
    elif len(all_examples) < 100:
        print("✅ Good example count (50-99) - optimization should work well")
        print("   MIPROv2 auto='medium' recommended")
    else:
        print("✅ Excellent example count (100+) - optimization will be very effective")
        print("   MIPROv2 auto='heavy' can be used for maximum quality")

    # Diversity check
    style_diversity = len(styles) / 3  # 3 possible styles
    category_diversity = len(categories) / 9  # 9 expected categories

    print(f"\nStyle diversity: {style_diversity * 100:.0f}% ({len(styles)}/3 styles)")
    print(f"Category diversity: {category_diversity * 100:.0f}% ({len(categories)}/9 categories)")

    if style_diversity < 0.67:
        print("   ⚠️  Low style diversity - consider adding more varied skill types")
    if category_diversity < 0.5:
        print("   ⚠️  Low category diversity - consider adding skills from more categories")

    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print(f"1. Review generated examples in {args.output}")
    print("2. Add synthetic examples for underrepresented categories")
    print("3. Run optimization: uv run skill-fleet optimize --optimizer miprov2")
    print("=" * 60)


if __name__ == "__main__":
    main()
