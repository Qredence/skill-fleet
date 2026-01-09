"""CLI entrypoints for the agentic skills system."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

# Ensure DSPy disk cache uses a writable location (avoids defaulting to `~/.dspy_cache`).
os.environ.setdefault("DSPY_CACHEDIR", str(Path.cwd() / ".dspy_cache"))

from skill_fleet.llm import FleetConfigError, build_lm_for_task, load_fleet_config

from .analytics.engine import AnalyticsEngine, RecommendationEngine
from .onboarding.bootstrap import SkillBootstrapper
from .taxonomy.manager import TaxonomyManager
from .validators import SkillValidator
from .workflow.optimizer import WorkflowOptimizer
from .workflow.skill_creator import TaxonomySkillCreator


def _repo_root() -> Path:
    """Find repository root from .git or pyproject.toml."""
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("Cannot find repository root")


def _default_config_path() -> Path:
    # Config at: src/skill_fleet/config.yaml
    return _repo_root() / "src/skill_fleet/config.yaml"


def _default_skills_root() -> Path:
    # Skills now at repo root: skills/
    return _repo_root() / "skills"


def _default_profiles_path() -> Path:
    # Still within skill-fleet package
    return Path(__file__).resolve().parent / "config" / "profiles" / "bootstrap_profiles.json"


def onboard_user_cli(args: argparse.Namespace) -> int:
    """Interactive onboarding workflow."""
    from rich.console import Console

    from .cli_submodules.onboarding_cli import collect_onboarding_responses

    console = Console()
    console.print("\n[bold cyan]Welcome to the Agentic Skills System![/bold cyan]\n")
    console.print("Let's set up your personalized skill set.\n")

    taxonomy = TaxonomyManager(Path(args.skills_root))
    creator = TaxonomySkillCreator(taxonomy_manager=taxonomy)
    bootstrapper = SkillBootstrapper(
        taxonomy_manager=taxonomy, skill_creator=creator, profiles_path=Path(args.profiles_path)
    )

    responses = collect_onboarding_responses()

    console.print("\n[bold green]Setting up your skills...[/bold green]\n")

    from rich.progress import Progress

    with Progress() as progress:
        task = progress.add_task("[cyan]Bootstrapping skills...", total=100)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        user_profile = loop.run_until_complete(bootstrapper.onboard_user(args.user_id, responses))

        progress.update(task, completed=100)

    console.print("\n[bold green]✓ Onboarding complete![/bold green]\n")
    console.print(f"Profile: {user_profile['profile']['primaryRole']}")
    console.print(f"Mounted Skills: {len(user_profile['mounted_skills'])}")
    console.print(f"On-Demand Skills: {len(user_profile['on_demand_skills'])}")

    console.print("\n[bold]You're ready to start![/bold]")
    console.print('Try: skills-fleet create-skill --task "your task here"')
    return 0


def create_skill(args: argparse.Namespace) -> int:
    """Run the full skill creation workflow for a single task description."""
    config = load_fleet_config(Path(args.config))
    task_names = [
        "skill_understand",
        "skill_plan",
        "skill_initialize",
        "skill_edit",
        "skill_package",
        "skill_validate",
    ]
    task_lms = {task_name: build_lm_for_task(config, task_name) for task_name in task_names}

    taxonomy = TaxonomyManager(Path(args.skills_root))
    optimizer = None
    if args.cache_dir:
        optimizer = WorkflowOptimizer(Path(args.cache_dir))
    creator = TaxonomySkillCreator(taxonomy_manager=taxonomy, optimizer=optimizer)

    # Determine feedback type: --auto-approve is a shortcut for --feedback-type=auto
    feedback_type = args.feedback_type
    if args.auto_approve:
        feedback_type = "auto"

    # Build feedback handler kwargs for interactive mode
    feedback_kwargs = {}
    if feedback_type == "interactive":
        feedback_kwargs["min_rounds"] = max(1, min(args.min_rounds, 4))
        feedback_kwargs["max_rounds"] = max(feedback_kwargs["min_rounds"], min(args.max_rounds, 4))

    result: dict[str, Any] = creator.forward(
        task_description=str(args.task),
        user_context={"user_id": str(args.user_id)},
        max_iterations=int(args.max_iterations),
        auto_approve=(feedback_type == "auto"),
        feedback_type=feedback_type,
        feedback_kwargs=feedback_kwargs,
        task_lms=task_lms,
    )

    if result.get("warnings"):
        for warning in result["warnings"]:
            print(f"⚠️ Warning: {warning}", file=sys.stderr)

    cache_stats = optimizer.get_cache_stats() if optimizer else None
    if cache_stats:
        result["cache_stats"] = cache_stats

    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result.get("status") in {"approved", "exists"} else 2

    print(f"status: {result.get('status')}")
    print(json.dumps(result, indent=2))
    if cache_stats:
        print("cache stats:")
        print(json.dumps(cache_stats, indent=2))
    return 0


def validate_skill(args: argparse.Namespace) -> int:
    """Validate a skill's metadata and structure."""
    skills_root = Path(args.skills_root)
    validator = SkillValidator(skills_root)

    skill_path = Path(args.skill_path)
    if not skill_path.is_absolute():
        skill_path = skills_root / skill_path

    results = validator.validate_complete(skill_path)

    if args.json:
        print(json.dumps(results, indent=2))
        return 0 if results.get("passed") else 2

    status = "passed" if results.get("passed") else "failed"
    print(f"validation: {status}")
    if results.get("errors"):
        print("errors:")
        for message in results["errors"]:
            print(f"- {message}")
    if results.get("warnings"):
        print("warnings:")
        for message in results["warnings"]:
            print(f"- {message}")
    return 0 if results.get("passed") else 2


def migrate_skills_cli(args: argparse.Namespace) -> int:
    """Migrate existing skills to agentskills.io format."""
    from .migration import migrate_all_skills

    skills_root = Path(args.skills_root)

    if args.json:
        # Quiet mode for JSON output
        result = migrate_all_skills(skills_root, dry_run=args.dry_run, verbose=False)
        print(json.dumps(result, indent=2))
        return 0 if result["failed"] == 0 else 1

    print(f"\n{'=' * 60}")
    print("Migrating skills to agentskills.io format")
    print(f"Skills root: {skills_root}")
    if args.dry_run:
        print("[DRY RUN MODE - no changes will be written]")
    print(f"{'=' * 60}\n")

    result = migrate_all_skills(skills_root, dry_run=args.dry_run, verbose=True)

    return 0 if result["failed"] == 0 else 1


def generate_xml_cli(args: argparse.Namespace) -> int:
    """Generate <available_skills> XML for agent prompt injection."""
    taxonomy = TaxonomyManager(Path(args.skills_root))
    xml_content = taxonomy.generate_available_skills_xml()

    if args.output:
        Path(args.output).write_text(xml_content, encoding="utf-8")
        print(f"XML written to: {args.output}")
    else:
        print(xml_content)

    return 0


def optimize_workflow_cli(args: argparse.Namespace) -> int:
    """Optimize the skill creation workflow using MIPROv2 or GEPA.

    Approved LLM Models:
    - gemini-3-flash-preview: Primary model for all steps
    - gemini-3-pro-preview: For GEPA reflection
    - deepseek-v3.2: Cost-effective alternative
    - Nemotron-3-Nano-30B-A3B: Lightweight operations
    """
    from .workflow.optimize import (
        APPROVED_MODELS,
        optimize_with_gepa,
        optimize_with_miprov2,
        optimize_with_tracking,
        quick_evaluate,
    )
    from .workflow.programs import SkillCreationProgram

    # Validate model
    if args.model not in APPROVED_MODELS:
        print(f"Error: Model '{args.model}' is not approved.", file=sys.stderr)
        print(f"Approved models: {list(APPROVED_MODELS.keys())}", file=sys.stderr)
        return 2

    print(f"\n{'=' * 60}")
    print("DSPy Workflow Optimization")
    print(f"{'=' * 60}")
    print(f"Optimizer: {args.optimizer}")
    print(f"Model: {args.model}")
    print(f"Trainset: {args.trainset}")
    print(f"Output: {args.output}")
    print(f"Intensity: {args.auto}")

    if args.evaluate_only:
        print("\n[EVALUATE ONLY MODE]\n")
        program = SkillCreationProgram()
        quick_evaluate(program, args.trainset, args.model, n_examples=args.n_examples)
        return 0

    if args.track:
        print("MLflow tracking: ENABLED")

    print(f"{'=' * 60}\n")

    # Create program
    program = SkillCreationProgram()

    # Run optimization
    try:
        if args.track:
            _optimized = optimize_with_tracking(
                program,
                trainset_path=args.trainset,
                output_path=args.output,
                optimizer_type=args.optimizer,
                model=args.model,
                auto=args.auto,
            )
        elif args.optimizer == "miprov2":
            _optimized = optimize_with_miprov2(
                program,
                trainset_path=args.trainset,
                output_path=args.output,
                model=args.model,
                auto=args.auto,
            )
        else:
            _optimized = optimize_with_gepa(
                program,
                trainset_path=args.trainset,
                output_path=args.output,
                model=args.model,
                auto=args.auto,
            )

        print(f"\n[SUCCESS] Optimized program saved to: {args.output}")
        return 0

    except FileNotFoundError as e:
        print(f"\nError: {e}", file=sys.stderr)
        print("Make sure the trainset file exists.", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"\nError during optimization: {e}", file=sys.stderr)
        return 1


def show_analytics(args: argparse.Namespace) -> int:
    """Show skill usage analytics and recommendations."""
    skills_root = Path(args.skills_root)
    taxonomy = TaxonomyManager(skills_root)
    analytics_file = skills_root / "_analytics" / "usage_log.jsonl"

    engine = AnalyticsEngine(analytics_file)
    stats = engine.analyze_usage(args.user_id if args.user_id != "all" else None)

    if args.json:
        print(json.dumps(stats, indent=2))
        return 0

    from rich.console import Console
    from rich.table import Table

    console = Console()
    console.print(f"\n[bold cyan]Skill Usage Analytics[/bold cyan] (User: {args.user_id})\n")

    console.print(f"Total Events: {stats['total_events']}")
    console.print(f"Success Rate: {stats['success_rate']:.1%}")
    console.print(f"Unique Skills Used: {stats['unique_skills_used']}\n")

    if stats["most_used_skills"]:
        table = Table(title="Most Used Skills")
        table.add_column("Skill ID", style="cyan")
        table.add_column("Usage Count", style="magenta")
        for skill_id, count in stats["most_used_skills"]:
            table.add_row(skill_id, str(count))
        console.print(table)
        console.print()

    if stats["common_combinations"]:
        table = Table(title="Common Skill Combinations")
        table.add_column("Skills", style="cyan")
        table.add_column("Co-occurrence", style="magenta")
        for combo in stats["common_combinations"]:
            table.add_row(", ".join(combo["skills"]), str(combo["count"]))
        console.print(table)
        console.print()

    # Recommendations
    recommender = RecommendationEngine(engine, taxonomy)
    recs = recommender.recommend_skills(args.user_id if args.user_id != "all" else "default")

    if recs:
        console.print("[bold green]Recommendations:[/bold green]")
        for rec in recs:
            console.print(
                f"  • [cyan]{rec['skill_id']}[/cyan]: {rec['reason']} ([yellow]{rec['priority']}[/yellow])"
            )
    else:
        console.print("[italic]No recommendations at this time.[/italic]")

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(prog="skills-fleet")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create-skill", help="Generate and register a new skill")
    create.add_argument("--task", required=True, help="Task/capability request for the skill")
    create.add_argument("--user-id", default="default", help="User id for mounted skills context")
    create.add_argument(
        "--skills-root", default=str(_default_skills_root()), help="Skills taxonomy root"
    )
    create.add_argument(
        "--config", default=str(_default_config_path()), help="Fleet LLM config YAML"
    )
    create.add_argument("--max-iterations", type=int, default=3, help="Max HITL iterations")
    create.add_argument(
        "--feedback-type",
        choices=["auto", "cli", "interactive", "webhook"],
        default="interactive",
        help="Feedback handler type: 'interactive' (recommended, multi-choice HITL), "
        "'cli' (simple approve/reject), 'auto' (no HITL), 'webhook' (external review)",
    )
    create.add_argument(
        "--auto-approve",
        action="store_true",
        help="Auto-approve (skip HITL); shortcut for --feedback-type=auto",
    )
    create.add_argument(
        "--min-rounds",
        type=int,
        default=1,
        help="Minimum HITL rounds for interactive feedback (1-4, default: 1)",
    )
    create.add_argument(
        "--max-rounds",
        type=int,
        default=4,
        help="Maximum HITL rounds for interactive feedback (1-4, default: 4)",
    )
    create.add_argument(
        "--cache-dir",
        help="Optional cache directory for workflow step outputs",
    )
    create.add_argument("--json", action="store_true", help="Output JSON only")
    create.set_defaults(func=create_skill)

    validate = subparsers.add_parser(
        "validate-skill", help="Validate a skill's metadata and structure"
    )
    validate.add_argument("skill_path", help="Path to a skill directory or JSON file")
    validate.add_argument(
        "--skills-root", default=str(_default_skills_root()), help="Skills taxonomy root"
    )
    validate.add_argument("--json", action="store_true", help="Output JSON only")
    validate.set_defaults(func=validate_skill)

    onboard = subparsers.add_parser("onboard", help="Interactive user onboarding")
    onboard.add_argument("--user-id", required=True, help="Unique user identifier")
    onboard.add_argument(
        "--skills-root", default=str(_default_skills_root()), help="Skills taxonomy root"
    )
    onboard.add_argument(
        "--profiles-path",
        default=str(_default_profiles_path()),
        help="Path to bootstrap profiles JSON",
    )
    onboard.set_defaults(func=onboard_user_cli)

    analytics = subparsers.add_parser("analytics", help="Show skill usage analytics")
    analytics.add_argument("--user-id", default="all", help="Filter by user ID or 'all'")
    analytics.add_argument(
        "--skills-root", default=str(_default_skills_root()), help="Skills taxonomy root"
    )
    analytics.add_argument("--json", action="store_true", help="Output JSON only")
    analytics.set_defaults(func=show_analytics)

    # Migration command for agentskills.io compliance
    migrate = subparsers.add_parser(
        "migrate", help="Migrate existing skills to agentskills.io format (add YAML frontmatter)"
    )
    migrate.add_argument(
        "--skills-root", default=str(_default_skills_root()), help="Skills taxonomy root"
    )
    migrate.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    migrate.add_argument("--json", action="store_true", help="Output JSON only")
    migrate.set_defaults(func=migrate_skills_cli)

    # XML generation for agent prompts
    generate_xml = subparsers.add_parser(
        "generate-xml", help="Generate <available_skills> XML for agent prompt injection"
    )
    generate_xml.add_argument(
        "--skills-root", default=str(_default_skills_root()), help="Skills taxonomy root"
    )
    generate_xml.add_argument("--output", "-o", help="Output file (default: stdout)")
    generate_xml.set_defaults(func=generate_xml_cli)

    # Workflow optimization with MIPROv2/GEPA
    optimize = subparsers.add_parser(
        "optimize",
        help="Optimize skill creation workflow with MIPROv2 or GEPA",
        description="""
Optimize the DSPy skill creation workflow using prompt optimization.

Approved LLM Models:
- gemini-3-flash-preview: Primary model for all steps (default)
- gemini-3-pro-preview: For GEPA reflection (stronger reasoning)
- deepseek-v3.2: Cost-effective alternative
- Nemotron-3-Nano-30B-A3B: Lightweight/fast operations
        """,
    )
    optimize.add_argument(
        "--optimizer",
        choices=["miprov2", "gepa"],
        default="miprov2",
        help="Optimizer algorithm (default: miprov2)",
    )
    optimize.add_argument(
        "--model",
        choices=[
            "gemini-3-flash-preview",
            "gemini-3-pro-preview",
            "deepseek-v3.2",
            "Nemotron-3-Nano-30B-A3B",
        ],
        default="gemini-3-flash-preview",
        help="LLM model to use (default: gemini-3-flash-preview)",
    )
    optimize.add_argument(
        "--trainset",
        default=str(Path(__file__).parent / "workflow" / "data" / "trainset.json"),
        help="Path to training data JSON",
    )
    optimize.add_argument(
        "--output",
        default=str(Path(__file__).parent / "workflow" / "optimized"),
        help="Output directory for optimized program",
    )
    optimize.add_argument(
        "--auto",
        choices=["light", "medium", "heavy"],
        default="medium",
        help="Optimization intensity (default: medium)",
    )
    optimize.add_argument(
        "--track",
        action="store_true",
        help="Enable MLflow tracking (requires mlflow>=2.21.1)",
    )
    optimize.add_argument(
        "--evaluate-only",
        action="store_true",
        help="Only run evaluation, don't optimize",
    )
    optimize.add_argument(
        "--n-examples",
        type=int,
        default=None,
        help="Number of examples to evaluate (for --evaluate-only)",
    )
    optimize.set_defaults(func=optimize_workflow_cli)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except FleetConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2


def cli_entrypoint() -> None:
    """Console-script entrypoint (`skills-fleet`)."""
    raise SystemExit(main())


if __name__ == "__main__":
    raise SystemExit(main())
