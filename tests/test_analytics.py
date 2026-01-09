import json

import pytest

from skill_fleet.analytics.engine import (
    AnalyticsEngine,
    RecommendationEngine,
    UsageTracker,
)


@pytest.fixture
def temp_analytics_dir(tmp_path):
    return tmp_path / "analytics"


def test_usage_tracking(temp_analytics_dir):
    tracker = UsageTracker(temp_analytics_dir)
    tracker.track_usage("skill_1", "user_1", success=True, task_id="task_1")
    tracker.track_usage("skill_2", "user_1", success=False, task_id="task_1")

    usage_file = temp_analytics_dir / "usage_log.jsonl"
    assert usage_file.exists()

    with usage_file.open("r") as f:
        lines = f.readlines()
        assert len(lines) == 2
        event1 = json.loads(lines[0])
        assert event1["skill_id"] == "skill_1"
        assert event1["user_id"] == "user_1"
        assert event1["success"] is True
        assert event1["task_id"] == "task_1"


def test_analytics_engine(temp_analytics_dir):
    tracker = UsageTracker(temp_analytics_dir)
    tracker.track_usage("skill_1", "user_1", success=True, task_id="task_1")
    tracker.track_usage("skill_2", "user_1", success=True, task_id="task_1")
    tracker.track_usage("skill_1", "user_1", success=True, task_id="task_2")
    tracker.track_usage("skill_1", "user_2", success=True, task_id="task_3")

    engine = AnalyticsEngine(temp_analytics_dir / "usage_log.jsonl")

    # Global stats
    stats = engine.analyze_usage()
    assert stats["total_events"] == 4
    assert stats["unique_skills_used"] == 2
    assert stats["most_used_skills"][0] == ("skill_1", 3)

    # User specific stats
    user1_stats = engine.analyze_usage("user_1")
    assert user1_stats["total_events"] == 3

    # Combinations
    assert len(stats["common_combinations"]) == 1
    assert set(stats["common_combinations"][0]["skills"]) == {"skill_1", "skill_2"}
    assert stats["common_combinations"][0]["count"] == 1


def test_recommendation_engine(temp_analytics_dir):
    class MockTaxonomy:
        def get_skill_metadata(self, skill_id):
            if skill_id == "skill_1":

                class Meta:
                    dependencies = ["dep_1"]

                return Meta()
            return None

    tracker = UsageTracker(temp_analytics_dir)
    tracker.track_usage("skill_1", "user_1")

    engine = AnalyticsEngine(temp_analytics_dir / "usage_log.jsonl")
    recommender = RecommendationEngine(engine, MockTaxonomy())

    recs = recommender.recommend_skills("user_1")
    assert len(recs) == 1
    assert recs[0]["skill_id"] == "dep_1"
    assert "Required by" in recs[0]["reason"]
