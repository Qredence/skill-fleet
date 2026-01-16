"""Test suite for job management and session persistence.

Following TDD principles, these tests were written before implementing
the features they test.
"""

import json
from datetime import datetime

from skill_fleet.api.jobs import (
    SESSION_DIR,
    cleanup_old_sessions,
    create_job,
    delete_job_session,
    get_job,
    list_saved_sessions,
    load_job_session,
    save_job_session,
)
from skill_fleet.api.schemas import (
    DeepUnderstandingState,
    JobState,
    TDDWorkflowState,
)


class TestTDDWorkflowState:
    """Tests for TDDWorkflowState model."""

    def test_default_tdd_workflow_state(self):
        """Test creating a TDDWorkflowState with default values."""
        # Arrange & Act
        state = TDDWorkflowState()

        # Assert
        assert state.phase is None
        assert state.baseline_tests_run is False
        assert state.compliance_tests_run is False
        assert state.rationalizations_identified == []
        # ChecklistState should have default values
        assert hasattr(state, "checklist")

    def test_tdd_workflow_state_with_values(self):
        """Test creating a TDDWorkflowState with specific values."""
        # Arrange & Act
        state = TDDWorkflowState(
            phase="red",
            baseline_tests_run=True,
            compliance_tests_run=False,
            rationalizations_identified=["just this once", "too simple"],
        )

        # Assert
        assert state.phase == "red"
        assert state.baseline_tests_run is True
        assert state.compliance_tests_run is False
        assert state.rationalizations_identified == ["just this once", "too simple"]

    def test_tdd_workflow_serialization(self):
        """Test that TDDWorkflowState can be serialized to dict."""
        # Arrange
        state = TDDWorkflowState(phase="green", baseline_tests_run=True)

        # Act
        data = state.model_dump()

        # Assert
        assert data["phase"] == "green"
        assert data["baseline_tests_run"] is True
        assert "checklist" in data


class TestDeepUnderstandingState:
    """Tests for DeepUnderstandingState model."""

    def test_default_deep_understanding_state(self):
        """Test creating a DeepUnderstandingState with default values."""
        # Arrange & Act
        state = DeepUnderstandingState()

        # Assert
        assert state.questions_asked == []
        assert state.answers == []
        assert state.research_performed == []
        assert state.understanding_summary == ""
        assert state.user_problem == ""
        assert state.user_goals == []
        assert state.readiness_score == 0.0
        assert state.complete is False

    def test_deep_understanding_state_with_values(self):
        """Test creating a DeepUnderstandingState with specific values."""
        # Arrange & Act
        state = DeepUnderstandingState(
            understanding_summary="User wants a Python testing skill",
            user_problem="Tests are flaky",
            user_goals=["reliability", "speed"],
            readiness_score=0.85,
            complete=True,
        )

        # Assert
        assert state.understanding_summary == "User wants a Python testing skill"
        assert state.user_problem == "Tests are flaky"
        assert state.user_goals == ["reliability", "speed"]
        assert state.readiness_score == 0.85
        assert state.complete is True

    def test_deep_understanding_add_question(self):
        """Test adding questions to DeepUnderstandingState."""
        # Arrange
        state = DeepUnderstandingState()
        question = {"id": "q1", "question": "Why do you need this?"}

        # Act
        state.questions_asked.append(question)

        # Assert
        assert len(state.questions_asked) == 1
        assert state.questions_asked[0] == question


class TestJobState:
    """Tests for enhanced JobState model."""

    def test_default_job_state(self):
        """Test creating a JobState with default values."""
        # Arrange & Act
        job = JobState(job_id="test-job-1")

        # Assert
        assert job.job_id == "test-job-1"
        assert job.status == "pending"
        assert job.hitl_type is None
        assert job.hitl_data is None
        assert job.result is None
        assert job.error is None
        assert job.saved_path is None
        # Enhanced features
        assert job.tdd_workflow.phase is None
        assert job.deep_understanding.complete is False
        assert job.multi_skill_queue == []
        assert job.current_skill_index == 0
        assert job.task_description_refined == ""
        # Session metadata
        assert isinstance(job.created_at, datetime)
        assert isinstance(job.updated_at, datetime)
        assert job.user_id == "default"
        assert job.user_context == {}

    def test_job_state_with_enhanced_features(self):
        """Test JobState with TDD and deep understanding populated."""
        # Arrange & Act
        job = JobState(
            job_id="test-job-2",
            status="running",
            user_id="user-123",
            tdd_workflow=TDDWorkflowState(phase="refactor"),
            deep_understanding=DeepUnderstandingState(readiness_score=0.9),
            multi_skill_queue=["skill-a", "skill-b"],
            current_skill_index=1,
            task_description_refined="Create Python testing skill",
        )

        # Assert
        assert job.job_id == "test-job-2"
        assert job.status == "running"
        assert job.user_id == "user-123"
        assert job.tdd_workflow.phase == "refactor"
        assert job.deep_understanding.readiness_score == 0.9
        assert job.multi_skill_queue == ["skill-a", "skill-b"]
        assert job.current_skill_index == 1
        assert job.task_description_refined == "Create Python testing skill"

    def test_job_state_serialization(self):
        """Test that JobState serializes correctly for persistence."""
        # Arrange
        job = JobState(
            job_id="test-job-3",
            tdd_workflow=TDDWorkflowState(phase="green"),
            deep_understanding=DeepUnderstandingState(complete=True),
        )

        # Act
        data = job.model_dump(mode="json", exclude_none=True)

        # Assert
        assert data["job_id"] == "test-job-3"
        assert "tdd_workflow" in data
        assert data["tdd_workflow"]["phase"] == "green"
        assert "deep_understanding" in data
        assert data["deep_understanding"]["complete"] is True


class TestJobManagement:
    """Tests for job creation and retrieval."""

    def test_create_job_returns_unique_id(self):
        """Test that create_job returns a unique ID."""
        # Arrange & Act
        job_id_1 = create_job()
        job_id_2 = create_job()

        # Assert
        assert job_id_1 != job_id_2
        assert isinstance(job_id_1, str)
        assert isinstance(job_id_2, str)

    def test_create_job_stores_job(self):
        """Test that create_job stores the job in JOBS dict."""
        # Arrange & Act
        job_id = create_job()

        # Assert
        job = get_job(job_id)
        assert job is not None
        assert job.job_id == job_id
        assert job.status == "pending"

    def test_get_job_returns_none_for_unknown_id(self):
        """Test that get_job returns None for unknown job ID."""
        # Arrange & Act
        job = get_job("unknown-job-id")

        # Assert
        assert job is None

    def test_created_job_has_enhanced_features(self):
        """Test that newly created jobs have enhanced feature structures."""
        # Arrange & Act
        job_id = create_job()
        job = get_job(job_id)

        # Assert
        assert job is not None
        assert hasattr(job, "tdd_workflow")
        assert hasattr(job, "deep_understanding")
        assert hasattr(job, "multi_skill_queue")
        assert isinstance(job.tdd_workflow, TDDWorkflowState)
        assert isinstance(job.deep_understanding, DeepUnderstandingState)


class TestSessionPersistence:
    """Tests for session save/load functionality."""

    def setup_method(self):
        """Clean up session directory before each test."""
        if SESSION_DIR.exists():
            for f in SESSION_DIR.glob("*.json"):
                f.unlink()

    def teardown_method(self):
        """Clean up session directory after each test."""
        if SESSION_DIR.exists():
            for f in SESSION_DIR.glob("*.json"):
                f.unlink()

    def test_save_job_session_creates_file(self):
        """Test that save_job_session creates a JSON file."""
        # Arrange
        job_id = create_job()

        # Act
        success = save_job_session(job_id)

        # Assert
        assert success is True
        session_file = SESSION_DIR / f"{job_id}.json"
        assert session_file.exists()

    def test_save_job_session_returns_false_for_unknown_job(self):
        """Test that save_job_session returns False for unknown job."""
        # Act
        success = save_job_session("unknown-job-id")

        # Assert
        assert success is False

    def test_save_job_session_includes_enhanced_features(self):
        """Test that saved session includes TDD and deep understanding data."""
        # Arrange
        job_id = create_job()
        job = get_job(job_id)
        job.tdd_workflow.phase = "red"
        job.deep_understanding.readiness_score = 0.75

        # Act
        save_job_session(job_id)
        session_file = SESSION_DIR / f"{job_id}.json"
        content = json.loads(session_file.read_text())

        # Assert
        assert "tdd_workflow" in content
        assert content["tdd_workflow"]["phase"] == "red"
        assert "deep_understanding" in content
        assert content["deep_understanding"]["readiness_score"] == 0.75

    def test_load_job_session_restores_job(self):
        """Test that load_job_session restores a job from disk."""
        # Arrange
        job_id = create_job()
        job = get_job(job_id)
        job.status = "running"
        job.tdd_workflow.phase = "green"
        job.user_id = "test-user"
        save_job_session(job_id)

        # Clear from memory
        from skill_fleet.api.jobs import JOBS

        JOBS.clear()

        # Act
        restored = load_job_session(job_id)

        # Assert
        assert restored is not None
        assert restored.job_id == job_id
        assert restored.status == "running"
        assert restored.tdd_workflow.phase == "green"
        assert restored.user_id == "test-user"

    def test_load_job_session_returns_none_for_missing_file(self):
        """Test that load_job_session returns None when file doesn't exist."""
        # Act
        restored = load_job_session("non-existent-job")

        # Assert
        assert restored is None

    def test_load_job_session_rejects_path_traversal(self):
        """Test that load_job_session rejects traversal-style job IDs."""
        # Act
        restored = load_job_session("../evil")

        # Assert
        assert restored is None

    def test_load_job_session_restores_nested_models(self):
        """Test that load_job_session properly restores TDD and deep understanding models."""
        # Arrange
        job_id = create_job()
        job = get_job(job_id)
        job.tdd_workflow = TDDWorkflowState(phase="refactor", baseline_tests_run=True)
        job.deep_understanding = DeepUnderstandingState(
            understanding_summary="Test summary",
            readiness_score=0.95,
        )
        save_job_session(job_id)

        # Clear from memory
        from skill_fleet.api.jobs import JOBS

        JOBS.clear()

        # Act
        restored = load_job_session(job_id)

        # Assert
        assert restored is not None
        assert isinstance(restored.tdd_workflow, TDDWorkflowState)
        assert restored.tdd_workflow.phase == "refactor"
        assert restored.tdd_workflow.baseline_tests_run is True
        assert isinstance(restored.deep_understanding, DeepUnderstandingState)
        assert restored.deep_understanding.understanding_summary == "Test summary"
        assert restored.deep_understanding.readiness_score == 0.95

    def test_list_saved_sessions(self):
        """Test that list_saved_sessions returns all session IDs."""
        # Arrange
        job_id_1 = create_job()
        job_id_2 = create_job()
        save_job_session(job_id_1)
        save_job_session(job_id_2)

        # Act
        sessions = list_saved_sessions()

        # Assert
        assert len(sessions) == 2
        assert job_id_1 in sessions
        assert job_id_2 in sessions

    def test_list_saved_sessions_empty_when_none(self):
        """Test that list_saved_sessions returns empty list when no sessions."""
        # Act
        sessions = list_saved_sessions()

        # Assert
        assert sessions == []

    def test_delete_job_session_removes_file(self):
        """Test that delete_job_session removes the session file."""
        # Arrange
        job_id = create_job()
        save_job_session(job_id)
        session_file = SESSION_DIR / f"{job_id}.json"
        assert session_file.exists()

        # Act
        success = delete_job_session(job_id)

        # Assert
        assert success is True
        assert not session_file.exists()

    def test_delete_job_session_returns_false_for_missing_file(self):
        """Test that delete_job_session returns False when file doesn't exist."""
        # Act
        success = delete_job_session("non-existent-job")

        # Assert
        assert success is False

    def test_cleanup_old_sessions(self):
        """Test that cleanup_old_sessions removes old session files."""
        import time

        # Arrange - create sessions with different ages
        job_id_1 = create_job()
        save_job_session(job_id_1)
        session_file_1 = SESSION_DIR / f"{job_id_1}.json"

        job_id_2 = create_job()
        save_job_session(job_id_2)

        # Both sessions exist
        assert len(list_saved_sessions()) == 2

        # Manually set file modification time to make job_id_1 old (25 hours ago)
        # and job_id_2 recent (current time)
        current_time = time.time()
        old_time = current_time - (25 * 3600)  # 25 hours ago

        # Set old file modification time (requires platform-specific approach)
        import os

        os.utime(session_file_1, (old_time, old_time))

        # Act - cleanup sessions older than 24 hours
        cleaned = cleanup_old_sessions(max_age_hours=24.0)

        # Assert
        assert cleaned == 1
        assert job_id_1 not in list_saved_sessions()
        assert job_id_2 in list_saved_sessions()
