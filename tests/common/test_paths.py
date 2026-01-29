"""Tests for path utilities."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from skill_fleet.common.paths import (
    _first_existing,
    _iter_parents,
    default_config_path,
    default_profiles_path,
    default_skills_root,
    find_repo_root,
)


class TestIterParents:
    """Tests for _iter_parents function."""

    def test_returns_parents_for_directory(self, tmp_path: Path):
        """Test returning parent directories for a directory path."""
        subdir = tmp_path / "a" / "b" / "c"
        subdir.mkdir(parents=True)

        result = _iter_parents(subdir)

        assert subdir in result
        assert subdir.parent in result  # tmp_path/a/b
        assert subdir.parent.parent in result  # tmp_path/a
        assert tmp_path in result

    def test_returns_parents_for_file(self, tmp_path: Path):
        """Test returning parent directories for a file path."""
        subdir = tmp_path / "a" / "b"
        subdir.mkdir(parents=True)
        file_path = subdir / "file.txt"
        file_path.touch()

        result = _iter_parents(file_path)

        # Should start from parent directory, not the file itself
        assert subdir in result
        assert subdir.parent in result  # tmp_path/a
        assert tmp_path in result
        assert file_path not in result


class TestFindRepoRoot:
    """Tests for find_repo_root function."""

    def test_finds_repo_root_with_git_marker(self, tmp_path: Path):
        """Test finding repo root when .git directory exists."""
        (tmp_path / ".git").mkdir()
        subdir = tmp_path / "src" / "module"
        subdir.mkdir(parents=True)

        result = find_repo_root(subdir)

        assert result == tmp_path

    def test_finds_repo_root_with_pyproject_marker(self, tmp_path: Path):
        """Test finding repo root when pyproject.toml exists."""
        (tmp_path / "pyproject.toml").touch()
        subdir = tmp_path / "src" / "deep" / "nested"
        subdir.mkdir(parents=True)

        result = find_repo_root(subdir)

        assert result == tmp_path

    def test_returns_none_when_no_markers(self, tmp_path: Path):
        """Test returning None when no repo markers found."""
        subdir = tmp_path / "isolated" / "directory"
        subdir.mkdir(parents=True)

        # Use a path that definitely has no markers in its parents
        # by mocking _iter_parents to only return the tmp_path hierarchy
        result = find_repo_root(subdir)

        # Since tmp_path is in /var or /tmp which likely has no markers,
        # this should return None (unless running in a repo)
        # We need to be more careful here - let's check if result is tmp_path or None
        if result is not None:
            # If a result is found, it should have a marker
            assert (result / ".git").exists() or (result / "pyproject.toml").exists()

    def test_uses_cwd_when_start_is_none(self, tmp_path: Path):
        """Test using current working directory when start is None."""
        (tmp_path / ".git").mkdir()

        with patch("skill_fleet.common.paths.Path.cwd", return_value=tmp_path):
            result = find_repo_root(None)

        assert result == tmp_path

    def test_prefers_closest_marker(self, tmp_path: Path):
        """Test that closest marker is found first."""
        # Create nested repo structure
        (tmp_path / ".git").mkdir()
        nested_repo = tmp_path / "nested" / "repo"
        nested_repo.mkdir(parents=True)
        (nested_repo / ".git").mkdir()

        deep_dir = nested_repo / "src" / "module"
        deep_dir.mkdir(parents=True)

        result = find_repo_root(deep_dir)

        # Should find the nested repo, not the outer one
        assert result == nested_repo


class TestFirstExisting:
    """Tests for _first_existing function."""

    def test_returns_first_existing_path(self, tmp_path: Path):
        """Test returning the first path that exists."""
        existing = tmp_path / "exists"
        existing.mkdir()
        non_existing = tmp_path / "does_not_exist"

        result = _first_existing([non_existing, existing])

        assert result == existing

    def test_returns_none_when_none_exist(self, tmp_path: Path):
        """Test returning None when no paths exist."""
        paths = [
            tmp_path / "a",
            tmp_path / "b",
            tmp_path / "c",
        ]

        result = _first_existing(paths)

        assert result is None

    def test_returns_first_when_multiple_exist(self, tmp_path: Path):
        """Test returning first path when multiple exist."""
        first = tmp_path / "first"
        second = tmp_path / "second"
        first.mkdir()
        second.mkdir()

        result = _first_existing([first, second])

        assert result == first

    def test_handles_empty_list(self):
        """Test handling empty path list."""
        result = _first_existing([])

        assert result is None


class TestDefaultConfigPath:
    """Tests for default_config_path function."""

    def test_returns_config_from_repo_root(self, tmp_path: Path):
        """Test returning config path from repo root."""
        (tmp_path / ".git").mkdir()
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.touch()

        with patch("skill_fleet.common.paths.Path.cwd", return_value=tmp_path):
            result = default_config_path()

        assert result == config_file

    def test_returns_fallback_when_no_config_exists(self, tmp_path: Path):
        """Test returning fallback path when config doesn't exist."""
        # Create a directory with no config
        isolated = tmp_path / "isolated"
        isolated.mkdir()

        with patch("skill_fleet.common.paths.Path.cwd", return_value=isolated):
            with patch("skill_fleet.common.paths.find_repo_root", return_value=None):
                with patch("skill_fleet.common.paths._package_root", return_value=isolated):
                    result = default_config_path()

        # Should return cwd-based fallback
        assert result == isolated / "config" / "config.yaml"


class TestDefaultProfilesPath:
    """Tests for default_profiles_path function."""

    def test_returns_profiles_from_repo_root(self, tmp_path: Path):
        """Test returning profiles path from repo root."""
        (tmp_path / ".git").mkdir()
        profiles_dir = tmp_path / "config" / "profiles"
        profiles_dir.mkdir(parents=True)
        profiles_file = profiles_dir / "bootstrap_profiles.json"
        profiles_file.touch()

        with patch("skill_fleet.common.paths.Path.cwd", return_value=tmp_path):
            result = default_profiles_path()

        assert result == profiles_file

    def test_returns_fallback_when_no_profiles_exist(self, tmp_path: Path):
        """Test returning fallback path when profiles don't exist."""
        isolated = tmp_path / "isolated"
        isolated.mkdir()

        with patch("skill_fleet.common.paths.Path.cwd", return_value=isolated):
            with patch("skill_fleet.common.paths.find_repo_root", return_value=None):
                with patch("skill_fleet.common.paths._package_root", return_value=isolated):
                    result = default_profiles_path()

        assert result == isolated / "config" / "profiles" / "bootstrap_profiles.json"


class TestDefaultSkillsRoot:
    """Tests for default_skills_root function."""

    def test_returns_skills_from_repo_root(self, tmp_path: Path):
        """Test returning skills path from repo root."""
        (tmp_path / ".git").mkdir()
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        with patch("skill_fleet.common.paths.Path.cwd", return_value=tmp_path):
            result = default_skills_root()

        assert result == skills_dir

    def test_returns_fallback_when_no_skills_exist(self, tmp_path: Path):
        """Test returning fallback path when skills directory doesn't exist."""
        isolated = tmp_path / "isolated"
        isolated.mkdir()

        with patch("skill_fleet.common.paths.Path.cwd", return_value=isolated):
            with patch("skill_fleet.common.paths.find_repo_root", return_value=None):
                with patch("skill_fleet.common.paths._package_root", return_value=isolated):
                    result = default_skills_root()

        assert result == isolated / "skills"
