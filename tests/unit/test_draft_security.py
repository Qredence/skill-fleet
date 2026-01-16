"""Security tests for draft promotion endpoint.

Tests path traversal protection and validation of untrusted data
in the promote_draft endpoint.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from skill_fleet.api.jobs import create_job
from skill_fleet.api.routes.drafts import PromoteDraftRequest, promote_draft


class TestPromoteDraftSecurity:
    """Security tests for promote_draft endpoint."""

    @pytest.fixture
    def tmp_skills_root(self, tmp_path: Path) -> Path:
        """Create a temporary skills root directory."""
        skills_root = tmp_path / "skills"
        skills_root.mkdir()
        (skills_root / "_drafts").mkdir()
        return skills_root

    @pytest.fixture
    def mock_taxonomy_manager(self):
        """Mock taxonomy manager."""
        manager = Mock()
        manager._ensure_all_skills_loaded = Mock()
        return manager

    @pytest.fixture
    def valid_job_with_draft(self, tmp_skills_root: Path) -> tuple[str, Path]:
        """Create a valid job with a draft."""
        job_id = create_job()
        from skill_fleet.api.jobs import JOBS

        job = JOBS[job_id]
        job.status = "completed"

        # Create a valid draft directory
        draft_dir = tmp_skills_root / "_drafts" / job_id / "test_skill"
        draft_dir.mkdir(parents=True)
        (draft_dir / "SKILL.md").write_text("# Test Skill\n", encoding="utf-8")
        (draft_dir / "metadata.json").write_text('{"skill_id": "test"}', encoding="utf-8")

        job.draft_path = str(draft_dir)
        job.intended_taxonomy_path = "general/test_skill"
        job.validation_passed = True

        return job_id, draft_dir

    @pytest.mark.asyncio
    async def test_promote_draft_rejects_path_traversal_in_draft_path(
        self, tmp_skills_root: Path, mock_taxonomy_manager
    ):
        """Test that promote_draft rejects path traversal in draft_path."""
        # Arrange
        job_id = create_job()
        from skill_fleet.api.jobs import JOBS

        job = JOBS[job_id]
        job.status = "completed"
        job.draft_path = str(tmp_skills_root / "_drafts" / ".." / ".." / "etc" / "passwd")
        job.intended_taxonomy_path = "general/test"
        job.validation_passed = True

        request = PromoteDraftRequest()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await promote_draft(
                job_id=job_id,
                request=request,
                skills_root=tmp_skills_root,
                taxonomy_manager=mock_taxonomy_manager,
            )

        assert exc_info.value.status_code == 400
        assert "Invalid draft path" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_promote_draft_rejects_absolute_path_outside_drafts(
        self, tmp_skills_root: Path, mock_taxonomy_manager
    ):
        """Test that promote_draft rejects absolute paths outside drafts directory."""
        # Arrange
        job_id = create_job()
        from skill_fleet.api.jobs import JOBS

        job = JOBS[job_id]
        job.status = "completed"
        # Use an absolute path that's not in the drafts directory
        job.draft_path = "/etc/passwd"
        job.intended_taxonomy_path = "general/test"
        job.validation_passed = True

        request = PromoteDraftRequest()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await promote_draft(
                job_id=job_id,
                request=request,
                skills_root=tmp_skills_root,
                taxonomy_manager=mock_taxonomy_manager,
            )

        assert exc_info.value.status_code == 400
        assert "Invalid draft path" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_promote_draft_rejects_symlink_escape(
        self, tmp_skills_root: Path, mock_taxonomy_manager, tmp_path: Path
    ):
        """Test that promote_draft detects symlink-based escapes."""
        # Arrange
        job_id = create_job()
        from skill_fleet.api.jobs import JOBS

        job = JOBS[job_id]
        job.status = "completed"

        # Create a directory outside the skills root
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()

        # Create a symlink from inside _drafts to outside
        symlink_path = tmp_skills_root / "_drafts" / "symlink_escape"
        if not symlink_path.parent.exists():
            symlink_path.parent.mkdir(parents=True)

        try:
            symlink_path.symlink_to(outside_dir, target_is_directory=True)
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        job.draft_path = str(symlink_path)
        job.intended_taxonomy_path = "general/test"
        job.validation_passed = True

        request = PromoteDraftRequest()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await promote_draft(
                job_id=job_id,
                request=request,
                skills_root=tmp_skills_root,
                taxonomy_manager=mock_taxonomy_manager,
            )

        assert exc_info.value.status_code == 400
        assert "Invalid draft path" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_promote_draft_rejects_invalid_intended_taxonomy_path(
        self, tmp_skills_root: Path, mock_taxonomy_manager, valid_job_with_draft
    ):
        """Test that promote_draft rejects path traversal in intended_taxonomy_path."""
        # Arrange
        job_id, draft_dir = valid_job_with_draft
        from skill_fleet.api.jobs import JOBS

        job = JOBS[job_id]
        # Try to escape using ../
        job.intended_taxonomy_path = "../../../etc/passwd"

        request = PromoteDraftRequest()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await promote_draft(
                job_id=job_id,
                request=request,
                skills_root=tmp_skills_root,
                taxonomy_manager=mock_taxonomy_manager,
            )

        assert exc_info.value.status_code == 400
        assert "Invalid target path" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_promote_draft_accepts_valid_paths(
        self, tmp_skills_root: Path, mock_taxonomy_manager, valid_job_with_draft
    ):
        """Test that promote_draft accepts valid paths within expected directories."""
        # Arrange
        job_id, draft_dir = valid_job_with_draft

        request = PromoteDraftRequest(overwrite=True)

        # Act
        result = await promote_draft(
            job_id=job_id,
            request=request,
            skills_root=tmp_skills_root,
            taxonomy_manager=mock_taxonomy_manager,
        )

        # Assert
        assert result.job_id == job_id
        assert result.status == "promoted"
        assert "general/test_skill" in result.final_path

        # Verify the skill was copied to the correct location
        expected_path = tmp_skills_root / "general" / "test_skill"
        assert expected_path.exists()
        assert (expected_path / "SKILL.md").exists()

    @pytest.mark.asyncio
    async def test_promote_draft_with_nested_taxonomy_path(
        self, tmp_skills_root: Path, mock_taxonomy_manager
    ):
        """Test promotion with deeply nested taxonomy path."""
        # Arrange
        job_id = create_job()
        from skill_fleet.api.jobs import JOBS

        job = JOBS[job_id]
        job.status = "completed"

        # Create a valid draft with nested path
        nested_path = "technical_skills/programming/python/testing"
        draft_dir = tmp_skills_root / "_drafts" / job_id / nested_path
        draft_dir.mkdir(parents=True)
        (draft_dir / "SKILL.md").write_text("# Test\n", encoding="utf-8")
        (draft_dir / "metadata.json").write_text('{"skill_id": "test"}', encoding="utf-8")

        job.draft_path = str(draft_dir)
        job.intended_taxonomy_path = nested_path
        job.validation_passed = True

        request = PromoteDraftRequest(overwrite=True)

        # Act
        result = await promote_draft(
            job_id=job_id,
            request=request,
            skills_root=tmp_skills_root,
            taxonomy_manager=mock_taxonomy_manager,
        )

        # Assert
        assert result.status == "promoted"
        expected_path = tmp_skills_root / nested_path
        assert expected_path.exists()
        assert (expected_path / "SKILL.md").exists()

    @pytest.mark.asyncio
    async def test_promote_draft_rejects_relative_draft_path(
        self, tmp_skills_root: Path, mock_taxonomy_manager
    ):
        """Test that relative draft paths are rejected."""
        # Arrange
        job_id = create_job()
        from skill_fleet.api.jobs import JOBS

        job = JOBS[job_id]
        job.status = "completed"
        # Use a relative path instead of absolute
        job.draft_path = "_drafts/job123/skill"
        job.intended_taxonomy_path = "general/test"
        job.validation_passed = True

        request = PromoteDraftRequest()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await promote_draft(
                job_id=job_id,
                request=request,
                skills_root=tmp_skills_root,
                taxonomy_manager=mock_taxonomy_manager,
            )

        assert exc_info.value.status_code == 400
        assert "Invalid draft path" in exc_info.value.detail
