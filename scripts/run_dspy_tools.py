#!/usr/bin/env python3
"""CLI tool for running DSPy evaluation and optimization.

This script provides commands for:
1. Evaluating existing skills quality
2. Optimizing skill creation programs
3. Comparing baseline vs optimized performance

Usage:
    # Evaluate all skills
    python scripts/run_dspy_tools.py evaluate

    # Evaluate specific directory
    python scripts/run_dspy_tools.py evaluate --skills-dir skills/technical_skills

    # Run optimization
    python scripts/run_dspy_tools.py optimize

    # Run optimization with specific optimizer
    python scripts/run_dspy_tools.py optimize --optimizer bootstrap_fewshot

    # List saved optimized programs
    python scripts/run_dspy_tools.py list-programs

    # Evaluate a single skill file
    python scripts/run_dspy_tools.py evaluate-file skills/path/to/SKILL.md
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from skill_fleet.core.dspy.evaluation import run_evaluation
from skill_fleet.core.dspy.metrics import assess_skill_quality
from skill_fleet.core.dspy.optimization import SkillOptimizer, run_optimization

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_evaluate(args: argparse.Namespace) -> int:
    """Run evaluation on existing skills."""
    try:
        report = run_evaluation(
            skills_dir=args.skills_dir,
            output_file=args.output,
            exclude_drafts=args.exclude_drafts,
            verbose=True,
        )

        if args.json:
            print(report.to_json())

        # Return non-zero if any skills failed
        return 0 if report.failed_skills == 0 else 1

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return 1


def cmd_evaluate_file(args: argparse.Namespace) -> int:
    """Evaluate a single skill file."""
    try:
        skill_path = Path(args.file)
        if not skill_path.exists():
            logger.error(f"File not found: {skill_path}")
            return 1

        content = skill_path.read_text(encoding="utf-8")
        scores = assess_skill_quality(content)

        print(f"\n{'=' * 60}")
        print(f"SKILL QUALITY ASSESSMENT: {skill_path.name}")
        print(f"{'=' * 60}")
        print(f"\nOverall Score: {scores.overall_score:.3f}")
        print("\n--- Detailed Scores ---")
        print(f"Frontmatter Completeness: {scores.frontmatter_completeness:.2f}")
        print(f"Pattern Count: {scores.pattern_count}")
        print(f"Has Anti-patterns: {scores.has_anti_patterns}")
        print(f"Has Key Insights: {scores.has_key_insights}")
        print(f"Has Quick Reference: {scores.has_quick_reference}")
        print(f"Has Common Mistakes: {scores.has_common_mistakes}")
        print(f"Has Red Flags: {scores.has_red_flags}")
        print(f"Has Real-World Impact: {scores.has_real_world_impact}")
        print(f"Code Examples Count: {scores.code_examples_count}")
        print(f"Code Examples Quality: {scores.code_examples_quality:.2f}")

        if scores.strengths:
            print(f"\n--- Strengths ({len(scores.strengths)}) ---")
            for strength in scores.strengths:
                print(f"  ✓ {strength}")

        if scores.issues:
            print(f"\n--- Issues ({len(scores.issues)}) ---")
            for issue in scores.issues:
                print(f"  ✗ {issue}")

        print(f"\n{'=' * 60}")

        if args.json:
            print("\nJSON Output:")
            print(json.dumps(scores.to_dict(), indent=2))

        # Return based on quality threshold
        threshold = args.threshold or 0.6
        return 0 if scores.overall_score >= threshold else 1

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        return 1


def cmd_optimize(args: argparse.Namespace) -> int:
    """Run optimization on skill creation program."""
    try:
        logger.info("Starting optimization...")
        logger.info(f"Optimizer: {args.optimizer or 'default (miprov2)'}")

        optimized_program, result = run_optimization(
            optimizer_type=args.optimizer,
            save_program=not args.no_save,
            program_name=args.name,
            verbose=True,
        )

        if args.json:
            print("\nJSON Output:")
            print(json.dumps(result.to_dict(), indent=2))

        # Return based on improvement
        return 0 if result.improvement >= 0 else 1

    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        return 1


def cmd_list_programs(args: argparse.Namespace) -> int:
    """List saved optimized programs."""
    try:
        optimizer = SkillOptimizer(configure_lm=False)
        programs = optimizer.list_optimized_programs()

        if not programs:
            print("No optimized programs found.")
            return 0

        print(f"\n{'=' * 60}")
        print("SAVED OPTIMIZED PROGRAMS")
        print(f"{'=' * 60}")

        for prog in programs:
            print(f"\nName: {prog.get('name', 'unknown')}")
            print(f"  Path: {prog.get('path', 'unknown')}")
            if prog.get("saved_at"):
                print(f"  Saved: {prog['saved_at']}")
            if prog.get("dspy_version"):
                print(f"  DSPy Version: {prog['dspy_version']}")

        print(f"\n{'=' * 60}")

        if args.json:
            print("\nJSON Output:")
            print(json.dumps(programs, indent=2))

        return 0

    except Exception as e:
        logger.error(f"Failed to list programs: {e}")
        return 1


def cmd_compare(args: argparse.Namespace) -> int:
    """Compare baseline vs optimized program."""
    try:
        optimizer = SkillOptimizer()

        # Load optimized program
        from skill_fleet.core.dspy.skill_creator import SkillCreationProgram

        # Baseline comparisons must not auto-load optimized weights, otherwise the
        # "baseline vs optimized" evaluation becomes misleading whenever
        # config/optimized/* exists.
        baseline = SkillCreationProgram(
            quality_assured=True,
            hitl_enabled=False,
            load_optimized=False,
        )
        optimized = optimizer.load_optimized_program(args.program, SkillCreationProgram)

        if optimized is None:
            logger.error(f"Could not load optimized program: {args.program}")
            return 1

        # Load test set
        from skill_fleet.core.dspy.training import load_testset

        testset = load_testset(min_quality=0.6)

        if not testset:
            logger.error("No test examples available")
            return 1

        # Compare
        comparison = optimizer.evaluator.compare_programs(baseline, optimized, testset)

        print(f"\n{'=' * 60}")
        print("PROGRAM COMPARISON")
        print(f"{'=' * 60}")
        print(f"\nBaseline Score: {comparison['baseline']['score']:.3f}")
        print(f"Optimized Score: {comparison['optimized']['score']:.3f}")
        print(
            f"\nImprovement: {comparison['improvement']['absolute']:+.3f} ({comparison['improvement']['percentage']:+.1f}%)"
        )
        print(f"Additional Passed: {comparison['improvement']['additional_passed']}")
        print(f"\n{'=' * 60}")

        if args.json:
            print("\nJSON Output:")
            print(json.dumps(comparison, indent=2))

        return 0

    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="DSPy evaluation and optimization tools for skill-fleet",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate existing skills")
    eval_parser.add_argument(
        "--skills-dir",
        type=str,
        default=None,
        help="Path to skills directory (default: skills/)",
    )
    eval_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output file for JSON report",
    )
    eval_parser.add_argument(
        "--exclude-drafts",
        action="store_true",
        help="Exclude _drafts directory from evaluation",
    )
    eval_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    eval_parser.set_defaults(func=cmd_evaluate)

    # Evaluate file command
    eval_file_parser = subparsers.add_parser("evaluate-file", help="Evaluate a single skill file")
    eval_file_parser.add_argument(
        "file",
        type=str,
        help="Path to SKILL.md file",
    )
    eval_file_parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=0.6,
        help="Quality threshold for pass/fail (default: 0.6)",
    )
    eval_file_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    eval_file_parser.set_defaults(func=cmd_evaluate_file)

    # Optimize command
    opt_parser = subparsers.add_parser(
        "optimize", help="Run optimization on skill creation program"
    )
    opt_parser.add_argument(
        "--optimizer",
        type=str,
        choices=["miprov2", "bootstrap_fewshot"],
        default=None,
        help="Optimizer type (default: from config)",
    )
    opt_parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Name for saved optimized program",
    )
    opt_parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save the optimized program",
    )
    opt_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    opt_parser.set_defaults(func=cmd_optimize)

    # List programs command
    list_parser = subparsers.add_parser("list-programs", help="List saved optimized programs")
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    list_parser.set_defaults(func=cmd_list_programs)

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare baseline vs optimized program")
    compare_parser.add_argument(
        "program",
        type=str,
        help="Name of optimized program to compare",
    )
    compare_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    compare_parser.set_defaults(func=cmd_compare)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
