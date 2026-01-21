#!/usr/bin/env python3
"""
Unified Training Data Manager for Skill Fleet.

Orchestrates extraction, synthetic generation, and merging of training data.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from scripts.internal.data.expand_training_data import extract_training_example
    from scripts.internal.data.generate_synthetic_examples import SYNTHETIC_EXAMPLES
except ImportError:
    # Fallback for when running from scripts/ directory directly
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from internal.data.expand_training_data import extract_training_example
    from internal.data.generate_synthetic_examples import SYNTHETIC_EXAMPLES


def load_existing(path: Path) -> list:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []


def run_extract(skills_dirs: list[Path]) -> list:
    """Extract examples from skill directories."""
    examples = []
    print(f"Scanning {len(skills_dirs)} directories for skills...")

    for d in skills_dirs:
        if not d.exists():
            continue
        for skill_path in d.glob("**/SKILL.md"):
            ex = extract_training_example(skill_path)
            if ex:
                examples.append(ex)

    print(f"✅ Extracted {len(examples)} examples from files")
    return examples


def run_synthetic() -> list:
    """Return synthetic examples."""
    print(f"✅ Loaded {len(SYNTHETIC_EXAMPLES)} synthetic examples")
    return SYNTHETIC_EXAMPLES


def deduplicate(examples: list) -> list:
    seen = set()
    unique = []
    for ex in examples:
        name = ex.get("expected_name")
        if name and name not in seen:
            seen.add(name)
            unique.append(ex)
    return unique


def save_dataset(examples: list, output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(examples, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved {len(examples)} examples to {output}")


def main():
    parser = argparse.ArgumentParser(description="Skill Fleet Training Data Manager")
    parser.add_argument(
        "command", choices=["extract", "synthetic", "prepare"], help="Action to perform"
    )
    parser.add_argument("--output", type=Path, default=Path("config/training/trainset_v4.json"))
    parser.add_argument("--skills-dir", type=Path, default=Path(".skills"))
    parser.add_argument("--repo-skills", type=Path, default=Path("skills"))

    args = parser.parse_args()

    all_examples = []

    if args.command in ["extract", "prepare"]:
        all_examples += run_extract([args.skills_dir, args.repo_skills])

    if args.command in ["synthetic", "prepare"]:
        all_examples += run_synthetic()

    # Deduplicate
    unique_examples = deduplicate(all_examples)
    print(f"Total unique examples: {len(unique_examples)}")

    save_dataset(unique_examples, args.output)


if __name__ == "__main__":
    main()
