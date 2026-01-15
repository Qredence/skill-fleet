"""Skill evaluation pipeline using DSPy Evaluate.

This module provides evaluation capabilities for assessing skill generation quality.
It integrates with DSPy's Evaluate class and the skill quality metrics.

Usage:
    from skill_fleet.core.dspy.evaluation import SkillEvaluator

    evaluator = SkillEvaluator()

    # Evaluate a single skill
    result = evaluator.evaluate_skill(skill_content)

    # Evaluate a skill creation program
    results = evaluator.evaluate_program(program, test_set)

    # Run evaluation from existing skills directory
    results = evaluator.evaluate_existing_skills("skills/")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import dspy
import yaml

from ...common.paths import default_config_path
from ...llm.dspy_config import configure_dspy
from .metrics import (
    SkillQualityScores,
    assess_skill_quality,
    parse_skill_content,
    skill_quality_metric,
)

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of evaluating a single skill."""

    skill_path: str | None = None
    skill_name: str | None = None
    quality_scores: SkillQualityScores | None = None
    passed: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "skill_path": self.skill_path,
            "skill_name": self.skill_name,
            "quality_scores": self.quality_scores.to_dict() if self.quality_scores else None,
            "passed": self.passed,
            "error": self.error,
        }


@dataclass
class EvaluationReport:
    """Aggregated evaluation report for multiple skills."""

    total_skills: int = 0
    passed_skills: int = 0
    failed_skills: int = 0
    average_score: float = 0.0
    min_score: float = 0.0
    max_score: float = 0.0
    results: list[EvaluationResult] = field(default_factory=list)
    thresholds: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_skills": self.total_skills,
            "passed_skills": self.passed_skills,
            "failed_skills": self.failed_skills,
            "average_score": self.average_score,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "pass_rate": self.passed_skills / self.total_skills if self.total_skills > 0 else 0.0,
            "thresholds": self.thresholds,
            "results": [r.to_dict() for r in self.results],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 60,
            "SKILL EVALUATION REPORT",
            "=" * 60,
            f"Total Skills Evaluated: {self.total_skills}",
            f"Passed: {self.passed_skills} ({self.passed_skills / self.total_skills * 100:.1f}%)"
            if self.total_skills > 0
            else "Passed: 0",
            f"Failed: {self.failed_skills}",
            "",
            f"Average Score: {self.average_score:.3f}",
            f"Min Score: {self.min_score:.3f}",
            f"Max Score: {self.max_score:.3f}",
            "",
            f"Quality Threshold: {self.thresholds.get('minimum_quality', 0.6):.2f}",
            "=" * 60,
        ]

        if self.failed_skills > 0:
            lines.append("\nFailed Skills:")
            for result in self.results:
                if not result.passed:
                    score = result.quality_scores.overall_score if result.quality_scores else 0.0
                    lines.append(f"  - {result.skill_name or result.skill_path}: {score:.3f}")
                    if result.quality_scores and result.quality_scores.issues:
                        for issue in result.quality_scores.issues[:3]:
                            lines.append(f"      • {issue}")

        return "\n".join(lines)


class SkillEvaluator:
    """Evaluator for skill quality assessment.

    This class provides methods for evaluating individual skills,
    skill creation programs, and existing skill directories.
    """

    def __init__(
        self,
        config_path: Path | None = None,
        configure_lm: bool = True,
    ):
        """Initialize the evaluator.

        Args:
            config_path: Path to config.yaml (default: auto-detect)
            configure_lm: Whether to configure DSPy LM on init
        """
        self.config_path = config_path or default_config_path()
        self.config = self._load_config()
        self.thresholds = self.config.get("evaluation", {}).get(
            "thresholds",
            {
                "minimum_quality": 0.6,
                "target_quality": 0.8,
                "excellent_quality": 0.9,
            },
        )
        self.metric_weights = self.config.get("evaluation", {}).get("metric_weights", None)

        if configure_lm:
            configure_dspy(self.config_path, default_task="skill_evaluate")

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f) or {}
        return {}

    def evaluate_skill(
        self,
        skill_content: str,
        skill_path: str | None = None,
        skill_name: str | None = None,
    ) -> EvaluationResult:
        """Evaluate a single skill's quality.

        Args:
            skill_content: Raw SKILL.md content
            skill_path: Optional path for reporting
            skill_name: Optional name for reporting

        Returns:
            EvaluationResult with quality scores
        """
        try:
            if skill_name is None:
                frontmatter, _body = parse_skill_content(skill_content)
                frontmatter_name = frontmatter.get("name")
                if frontmatter_name:
                    skill_name = str(frontmatter_name)

            scores = assess_skill_quality(skill_content, weights=self.metric_weights)
            passed = scores.overall_score >= self.thresholds.get("minimum_quality", 0.6)

            return EvaluationResult(
                skill_path=skill_path,
                skill_name=skill_name,
                quality_scores=scores,
                passed=passed,
            )
        except Exception as e:
            logger.error(f"Error evaluating skill {skill_path or skill_name}: {e}")
            return EvaluationResult(
                skill_path=skill_path,
                skill_name=skill_name,
                passed=False,
                error=str(e),
            )

    def evaluate_skill_file(self, skill_path: Path) -> EvaluationResult:
        """Evaluate a skill from a SKILL.md file.

        Args:
            skill_path: Path to SKILL.md file

        Returns:
            EvaluationResult with quality scores
        """
        try:
            content = skill_path.read_text(encoding="utf-8")
            return self.evaluate_skill(
                skill_content=content,
                skill_path=str(skill_path),
                skill_name=skill_path.parent.name,
            )
        except Exception as e:
            logger.error(f"Error reading skill file {skill_path}: {e}")
            return EvaluationResult(
                skill_path=str(skill_path),
                passed=False,
                error=str(e),
            )

    def evaluate_existing_skills(
        self,
        skills_dir: Path | str,
        recursive: bool = True,
        exclude_drafts: bool = False,
    ) -> EvaluationReport:
        """Evaluate all skills in a directory.

        Args:
            skills_dir: Path to skills directory
            recursive: Whether to search recursively
            exclude_drafts: Whether to exclude _drafts directory

        Returns:
            EvaluationReport with aggregated results
        """
        skills_dir = Path(skills_dir)
        results: list[EvaluationResult] = []

        # Find all SKILL.md files
        pattern = "**/SKILL.md" if recursive else "*/SKILL.md"
        skill_files = list(skills_dir.glob(pattern))

        if exclude_drafts:
            skill_files = [f for f in skill_files if "_drafts" not in str(f)]

        logger.info(f"Found {len(skill_files)} skills to evaluate")

        for skill_file in skill_files:
            result = self.evaluate_skill_file(skill_file)
            results.append(result)

        return self._aggregate_results(results)

    def evaluate_program(
        self,
        program: dspy.Module,
        test_set: list[dspy.Example],
        num_threads: int | None = None,
        display_progress: bool = True,
        display_table: bool = True,
    ) -> tuple[float, EvaluationReport]:
        """Evaluate a skill creation program using DSPy Evaluate.

        Args:
            program: DSPy program to evaluate
            test_set: List of test examples
            num_threads: Number of threads for parallel evaluation
            display_progress: Whether to show progress bar
            display_table: Whether to display results table

        Returns:
            Tuple of (average_score, detailed_report)
        """
        eval_config = self.config.get("evaluation", {})
        num_threads = num_threads or eval_config.get("num_threads", 8)

        # Create DSPy Evaluate instance
        evaluator = dspy.Evaluate(
            devset=test_set,
            metric=skill_quality_metric,
            num_threads=num_threads,
            display_progress=display_progress,
            display_table=display_table,
        )

        # Run evaluation
        average_score = evaluator(program)

        # Collect detailed results
        results: list[EvaluationResult] = []
        for example in test_set:
            try:
                prediction = program(**example.inputs())
                skill_content = getattr(prediction, "skill_content", str(prediction))
                result = self.evaluate_skill(
                    skill_content=skill_content,
                    skill_name=example.get("task_description", "unknown")[:50],
                )
                results.append(result)
            except Exception as e:
                results.append(
                    EvaluationResult(
                        skill_name=example.get("task_description", "unknown")[:50],
                        passed=False,
                        error=str(e),
                    )
                )

        report = self._aggregate_results(results)
        return average_score, report

    def _aggregate_results(self, results: list[EvaluationResult]) -> EvaluationReport:
        """Aggregate individual results into a report.

        Args:
            results: List of individual evaluation results

        Returns:
            Aggregated EvaluationReport
        """
        if not results:
            return EvaluationReport(thresholds=self.thresholds)

        scores = [r.quality_scores.overall_score for r in results if r.quality_scores is not None]

        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        return EvaluationReport(
            total_skills=len(results),
            passed_skills=passed,
            failed_skills=failed,
            average_score=sum(scores) / len(scores) if scores else 0.0,
            min_score=min(scores) if scores else 0.0,
            max_score=max(scores) if scores else 0.0,
            results=results,
            thresholds=self.thresholds,
        )

    def compare_programs(
        self,
        baseline_program: dspy.Module,
        optimized_program: dspy.Module,
        test_set: list[dspy.Example],
    ) -> dict[str, Any]:
        """Compare baseline and optimized programs.

        Args:
            baseline_program: Original program
            optimized_program: Optimized program
            test_set: Test examples

        Returns:
            Comparison results with improvement metrics
        """
        logger.info("Evaluating baseline program...")
        baseline_score, baseline_report = self.evaluate_program(
            baseline_program, test_set, display_progress=True, display_table=False
        )

        logger.info("Evaluating optimized program...")
        optimized_score, optimized_report = self.evaluate_program(
            optimized_program, test_set, display_progress=True, display_table=False
        )

        improvement = optimized_score - baseline_score
        improvement_pct = (improvement / baseline_score * 100) if baseline_score > 0 else 0.0

        return {
            "baseline": {
                "score": baseline_score,
                "passed": baseline_report.passed_skills,
                "failed": baseline_report.failed_skills,
            },
            "optimized": {
                "score": optimized_score,
                "passed": optimized_report.passed_skills,
                "failed": optimized_report.failed_skills,
            },
            "improvement": {
                "absolute": improvement,
                "percentage": improvement_pct,
                "additional_passed": optimized_report.passed_skills - baseline_report.passed_skills,
            },
        }


def run_evaluation(
    skills_dir: str | Path | None = None,
    output_file: str | Path | None = None,
    exclude_drafts: bool = False,
    verbose: bool = True,
) -> EvaluationReport:
    """Run evaluation on existing skills.

    This is a convenience function for running evaluations from CLI or scripts.

    Args:
        skills_dir: Path to skills directory (default: skills/)
        output_file: Optional path to save JSON report
        exclude_drafts: Whether to exclude _drafts directory
        verbose: Whether to print summary

    Returns:
        EvaluationReport with results
    """
    from ...common.paths import find_repo_root

    # Find skills directory
    if skills_dir is None:
        repo_root = find_repo_root(Path.cwd())
        if repo_root:
            skills_dir = repo_root / "skills"
        else:
            skills_dir = Path("skills")

    skills_dir = Path(skills_dir)
    if not skills_dir.exists():
        raise FileNotFoundError(f"Skills directory not found: {skills_dir}")

    # Run evaluation
    evaluator = SkillEvaluator()
    report = evaluator.evaluate_existing_skills(
        skills_dir,
        recursive=True,
        exclude_drafts=exclude_drafts,
    )

    # Output results
    if verbose:
        print(report.summary())

    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report.to_json())
        logger.info(f"Report saved to {output_path}")

    return report


__all__ = [
    "EvaluationReport",
    "EvaluationResult",
    "SkillEvaluator",
    "run_evaluation",
]
