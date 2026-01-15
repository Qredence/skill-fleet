"""CLI command for evaluating skill quality."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from ...common.paths import find_repo_root
from ...core.dspy.metrics import assess_skill_quality


def evaluate_command(
    path: str = typer.Argument(
        ...,
        help="Path to skill directory or SKILL.md file to evaluate",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output results as JSON",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed metrics breakdown",
    ),
):
    """Evaluate skill quality using calibrated metrics.

    Evaluates a skill's SKILL.md content against quality criteria calibrated
    from golden skills (Obra/superpowers, Anthropics).

    Examples:
        # Evaluate a skill by path
        skill-fleet evaluate skills/technical_skills/programming/python/fastapi

        # Evaluate a specific SKILL.md file
        skill-fleet evaluate path/to/SKILL.md

        # Get JSON output
        skill-fleet evaluate skills/my-skill --json
    """
    # Resolve the path
    skill_path = Path(path)

    # If relative path, try to resolve from repo root
    if not skill_path.is_absolute():
        repo_root = find_repo_root(Path.cwd())
        if repo_root:
            skill_path = repo_root / path

    # Determine SKILL.md location
    if skill_path.is_dir():
        skill_md = skill_path / "SKILL.md"
    elif skill_path.suffix == ".md":
        skill_md = skill_path
    else:
        skill_md = skill_path / "SKILL.md"

    if not skill_md.exists():
        print(f"Error: SKILL.md not found at {skill_md}", file=sys.stderr)
        raise typer.Exit(code=1)

    # Read and evaluate
    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        raise typer.Exit(code=1) from e

    scores = assess_skill_quality(content)

    if json_output:
        # JSON output
        print(json.dumps(scores.to_dict(), indent=2))
    else:
        # Human-readable output
        print(f"\n{'=' * 60}")
        print("Skill Quality Evaluation")
        print(f"{'=' * 60}")
        print(f"File: {skill_md}")
        print(f"\nOverall Score: {scores.overall_score:.3f}")
        print(f"{'=' * 60}")

        if verbose:
            print("\n📊 Detailed Metrics:")
            print(f"  Frontmatter Completeness: {scores.frontmatter_completeness:.2f}")
            print(f"  Pattern Count: {scores.pattern_count}")
            print(f"  Code Examples: {scores.code_examples_count}")
            print(f"  Code Quality: {scores.code_examples_quality:.2f}")
            print(f"  Description Quality: {scores.description_quality:.2f}")
            print()
            print("  Quality Indicators:")
            print(f"    Has Overview: {'✓' if scores.has_overview else '✗'}")
            print(f"    Has When to Use: {'✓' if scores.has_when_to_use else '✗'}")
            print(f"    Has Quick Reference: {'✓' if scores.has_quick_reference else '✗'}")
            print(f"    Has Anti-patterns: {'✓' if scores.has_anti_patterns else '✗'}")
            print(f"    Has Key Insights: {'✓' if scores.has_key_insights else '✗'}")
            print(f"    Has Common Mistakes: {'✓' if scores.has_common_mistakes else '✗'}")
            print(f"    Has Red Flags: {'✓' if scores.has_red_flags else '✗'}")
            print(f"    Has Real-World Impact: {'✓' if scores.has_real_world_impact else '✗'}")
            print()
            print("  Obra/Superpowers Criteria:")
            print(f"    Has Core Principle: {'✓' if scores.has_core_principle else '✗'}")
            print(f"    Has Strong Guidance: {'✓' if scores.has_strong_guidance else '✗'}")
            print(f"    Has Good/Bad Contrast: {'✓' if scores.has_good_bad_contrast else '✗'}")

        if scores.strengths:
            print(f"\n✅ Strengths ({len(scores.strengths)}):")
            for strength in scores.strengths[:10]:  # Limit to 10
                print(f"  • {strength}")
            if len(scores.strengths) > 10:
                print(f"  ... and {len(scores.strengths) - 10} more")

        if scores.issues:
            print(f"\n⚠️  Issues ({len(scores.issues)}):")
            for issue in scores.issues:
                print(f"  • {issue}")

        # Quality rating
        print(f"\n{'=' * 60}")
        if scores.overall_score >= 0.85:
            print("Rating: ⭐⭐⭐ EXCELLENT")
        elif scores.overall_score >= 0.70:
            print("Rating: ⭐⭐ GOOD")
        elif scores.overall_score >= 0.50:
            print("Rating: ⭐ NEEDS IMPROVEMENT")
        else:
            print("Rating: ❌ POOR")
        print(f"{'=' * 60}\n")


def evaluate_batch_command(
    paths: list[str] = typer.Argument(
        ...,
        help="Paths to skill directories to evaluate",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output results as JSON",
    ),
):
    """Evaluate multiple skills and show summary statistics.

    Examples:
        skill-fleet evaluate-batch skills/technical_skills/programming/python/*
    """
    results = []
    repo_root = find_repo_root(Path.cwd())

    for path in paths:
        skill_path = Path(path)
        if not skill_path.is_absolute() and repo_root:
            skill_path = repo_root / path

        skill_md = skill_path / "SKILL.md" if skill_path.is_dir() else skill_path

        if not skill_md.exists():
            results.append({"path": path, "error": "SKILL.md not found", "score": 0.0})
            continue

        try:
            content = skill_md.read_text(encoding="utf-8")
            scores = assess_skill_quality(content)
            results.append(
                {
                    "path": path,
                    "score": scores.overall_score,
                    "issues_count": len(scores.issues),
                    "strengths_count": len(scores.strengths),
                }
            )
        except Exception as e:
            results.append({"path": path, "error": str(e), "score": 0.0})

    if json_output:
        print(json.dumps(results, indent=2))
    else:
        print(f"\n{'=' * 60}")
        print("Batch Skill Evaluation")
        print(f"{'=' * 60}\n")

        valid_results = [r for r in results if "error" not in r]
        if valid_results:
            avg_score = sum(r["score"] for r in valid_results) / len(valid_results)
            print(f"Skills Evaluated: {len(valid_results)}")
            print(f"Average Score: {avg_score:.3f}")
            print()

            # Sort by score
            sorted_results = sorted(valid_results, key=lambda x: x["score"], reverse=True)
            print("Results (sorted by score):")
            for r in sorted_results:
                score = r["score"]
                rating = (
                    "⭐⭐⭐"
                    if score >= 0.85
                    else "⭐⭐"
                    if score >= 0.70
                    else "⭐"
                    if score >= 0.50
                    else "❌"
                )
                print(f"  {rating} {r['score']:.3f} - {r['path']}")

        errors = [r for r in results if "error" in r]
        if errors:
            print(f"\nErrors ({len(errors)}):")
            for r in errors:
                print(f"  ✗ {r['path']}: {r['error']}")

        print(f"\n{'=' * 60}\n")
