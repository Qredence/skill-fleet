"""Usage tracking and analytics for the agentic skills system."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class UsageTracker:
    """Tracks skill usage events in a JSONL log file."""

    def __init__(self, analytics_root: Path, *, trusted_root: Path | None = None) -> None:
        analytics_root_path = Path(analytics_root)

        # Defensive path validation: allow callers to constrain analytics output
        # to a known-safe root (e.g., skills_root) to prevent traversal/redirects.
        if trusted_root is not None:
            trusted_root_resolved = Path(trusted_root).resolve()
            analytics_root_resolved = analytics_root_path.resolve(strict=False)
            try:
                analytics_root_resolved.relative_to(trusted_root_resolved)
            except ValueError as e:
                raise ValueError(
                    f"Analytics root must be within {trusted_root_resolved}. Got: {analytics_root_resolved}"
                ) from e
            self.analytics_root = analytics_root_resolved
        else:
            self.analytics_root = analytics_root_path.resolve(strict=False)

        self.analytics_root.mkdir(parents=True, exist_ok=True)
        self.usage_file = self.analytics_root / "usage_log.jsonl"

    def track_usage(
        self,
        skill_id: str,
        user_id: str,
        success: bool = True,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record a skill usage event."""
        entry = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "skill_id": skill_id,
            "user_id": user_id,
            "success": success,
            "task_id": task_id,
            "metadata": metadata or {},
        }
        with self.usage_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


class AnalyticsEngine:
    """Analyzes skill usage patterns from logs."""

    def __init__(self, usage_file: Path) -> None:
        self.usage_file = Path(usage_file).resolve(strict=False)

    def get_usage_data(self, user_id: str | None = None) -> list[dict[str, Any]]:
        """Read all usage events, optionally filtered by user."""
        if not self.usage_file.exists():
            return []

        events = []
        with self.usage_file.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                event = json.loads(line)
                if user_id is None or event["user_id"] == user_id:
                    events.append(event)
        return events

    def analyze_usage(self, user_id: str | None = None) -> dict[str, Any]:
        """Perform comprehensive usage analysis."""
        events = self.get_usage_data(user_id)
        if not events:
            return {
                "total_events": 0,
                "most_used_skills": [],
                "success_rate": 0.0,
                "common_combinations": [],
                "unique_skills_used": 0,
                "cold_skills": [],
            }

        skill_counts = Counter(e["skill_id"] for e in events)
        successes = [e for e in events if e.get("success", True)]

        # Simple combination analysis (skills used in the same task)
        task_skills: dict[str, set[str]] = {}
        for e in events:
            task_id = e.get("task_id")
            if task_id:
                task_skills.setdefault(task_id, set()).add(e["skill_id"])

        combinations = Counter()
        for skills in task_skills.values():
            if len(skills) > 1:
                # Store sorted tuple to ensure order doesn't matter
                sorted_skills = tuple(sorted(list(skills)))
                combinations[sorted_skills] += 1

        return {
            "total_events": len(events),
            "most_used_skills": skill_counts.most_common(10),
            "success_rate": len(successes) / len(events) if events else 0.0,
            "common_combinations": [
                {"skills": combo, "count": count} for combo, count in combinations.most_common(5)
            ],
            "unique_skills_used": len(skill_counts),
            "cold_skills": self._identify_cold_skills(skill_counts),
        }

    def _identify_cold_skills(self, skill_counts: Counter) -> list[str]:
        """Identify skills that haven't been used much (placeholder for actual aging logic)."""
        # In a real system, this would compare against all available skills
        # and check the last usage timestamp.
        return [skill_id for skill_id, count in skill_counts.items() if count == 1]


class RecommendationEngine:
    """Suggests skills based on usage patterns and taxonomy."""

    def __init__(self, analytics: AnalyticsEngine, taxonomy_manager: Any) -> None:
        self.analytics = analytics
        self.taxonomy = taxonomy_manager

    def recommend_skills(self, user_id: str) -> list[dict[str, Any]]:
        """Recommend skills the user might need."""
        stats = self.analytics.analyze_usage(user_id)
        most_used = [skill_id for skill_id, _ in stats["most_used_skills"]]

        recommendations = []

        # 1. Recommend dependencies of most used skills that aren't mounted/frequently used
        for skill_id in most_used:
            meta = self.taxonomy.get_skill_metadata(skill_id)
            if meta:
                for dep_id in meta.dependencies:
                    if dep_id not in most_used:
                        recommendations.append(
                            {
                                "skill_id": dep_id,
                                "reason": f"Required by frequently used skill: {skill_id}",
                                "priority": "high",
                            }
                        )

        # 2. Recommend based on common combinations (if user uses A but not B, and A+B is common)
        # TODO: Implement more complex pattern matching

        return recommendations
