"""Tests for common security utilities.

Tests path sanitization and validation functions that protect against
path traversal attacks and ensure paths remain within expected boundaries.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from skill_fleet.common.security import (
    is_safe_path_component,
    resolve_path_within_root,
    sanitize_relative_file_path,
    sanitize_taxonomy_path,
)


class TestSanitizeTaxonomyPath:
    """Tests for sanitize_taxonomy_path function."""

    def test_accepts_valid_taxonomy_path(self):
        """Test that valid taxonomy paths are accepted."""
        assert (
            sanitize_taxonomy_path("technical_skills/programming/python")
            == "technical_skills/programming/python"
        )
        assert sanitize_taxonomy_path("general/testing") == "general/testing"
        assert sanitize_taxonomy_path("business/analytics") == "business/analytics"

    def test_rejects_absolute_path(self):
        """Test that absolute paths are rejected."""
        assert sanitize_taxonomy_path("/absolute/path") is None
        assert sanitize_taxonomy_path("/etc/passwd") is None

    def test_rejects_parent_directory_traversal(self):
        """Test that parent directory traversal is rejected."""
        assert sanitize_taxonomy_path("../traversal") is None
        assert sanitize_taxonomy_path("path/../up") is None
        assert sanitize_taxonomy_path("../../etc/passwd") is None

    def test_rejects_windows_separators(self):
        """Test that Windows path separators are rejected."""
        assert sanitize_taxonomy_path("path\\to\\file") is None
        assert sanitize_taxonomy_path("C:\\Windows\\System32") is None

    def test_rejects_empty_path(self):
        """Test that empty paths are rejected."""
        assert sanitize_taxonomy_path("") is None
        assert sanitize_taxonomy_path("   ") is None

    def test_rejects_special_characters(self):
        """Test that paths with special characters are rejected."""
        assert sanitize_taxonomy_path("path/with spaces") is None
        assert sanitize_taxonomy_path("path/with@symbol") is None
        assert sanitize_taxonomy_path("path/with!exclamation") is None

    def test_normalizes_path_segments(self):
        """Test that path segments are normalized."""
        # Removes empty segments and dots
        assert sanitize_taxonomy_path("path//double/slash") == "path/double/slash"
        assert sanitize_taxonomy_path("./current/path") == "current/path"
        assert sanitize_taxonomy_path("path/./middle") == "path/middle"

    def test_accepts_hyphens_and_underscores(self):
        """Test that hyphens and underscores are accepted."""
        assert (
            sanitize_taxonomy_path("python-advanced/web_development")
            == "python-advanced/web_development"
        )
        assert (
            sanitize_taxonomy_path("data-science/machine_learning")
            == "data-science/machine_learning"
        )


class TestSanitizeRelativeFilePath:
    """Tests for sanitize_relative_file_path function."""

    def test_accepts_valid_relative_path(self):
        """Test that valid relative paths are accepted."""
        assert sanitize_relative_file_path("path/to/file.txt") == "path/to/file.txt"
        assert sanitize_relative_file_path("subdir/file.py") == "subdir/file.py"

    def test_rejects_absolute_path(self):
        """Test that absolute paths are rejected."""
        assert sanitize_relative_file_path("/absolute/path") is None
        assert sanitize_relative_file_path("/etc/passwd") is None

    def test_rejects_parent_directory_traversal(self):
        """Test that parent directory traversal is rejected."""
        assert sanitize_relative_file_path("../file.txt") is None
        assert sanitize_relative_file_path("path/../../escape") is None

    def test_rejects_windows_separators(self):
        """Test that Windows separators are rejected."""
        assert sanitize_relative_file_path("path\\to\\file") is None

    def test_rejects_null_bytes(self):
        """Test that null bytes are rejected."""
        assert sanitize_relative_file_path("path\x00file") is None

    def test_rejects_empty_path(self):
        """Test that empty paths are rejected."""
        assert sanitize_relative_file_path("") is None

    def test_accepts_dots_in_filenames(self):
        """Test that dots in filenames are accepted."""
        assert sanitize_relative_file_path("file.name.txt") == "file.name.txt"
        assert sanitize_relative_file_path("path/to/.hidden") == "path/to/.hidden"

    def test_normalizes_path_segments(self):
        """Test that path segments are normalized."""
        # Removes empty segments and single dots
        assert sanitize_relative_file_path("path//double") == "path/double"
        assert sanitize_relative_file_path("./path/file") == "path/file"


class TestResolvePathWithinRoot:
    """Tests for resolve_path_within_root function."""

    def test_resolves_valid_path_within_root(self, tmp_path: Path):
        """Test that valid paths within root are resolved correctly."""
        root = tmp_path / "root"
        root.mkdir()

        # Create a subdirectory
        subdir = root / "subdir"
        subdir.mkdir()

        result = resolve_path_within_root(root, "subdir")
        assert result == subdir.resolve()

    def test_rejects_path_escaping_root_via_parent_reference(self, tmp_path: Path):
        """Test that paths escaping root via .. are rejected."""
        root = tmp_path / "root"
        root.mkdir()

        with pytest.raises(ValueError, match="Invalid relative path"):
            resolve_path_within_root(root, "../escape")

    def test_rejects_absolute_path(self, tmp_path: Path):
        """Test that absolute paths are rejected."""
        root = tmp_path / "root"
        root.mkdir()

        with pytest.raises(ValueError, match="Invalid relative path"):
            resolve_path_within_root(root, "/etc/passwd")

    def test_handles_nested_paths(self, tmp_path: Path):
        """Test that nested paths within root are handled correctly."""
        root = tmp_path / "root"
        root.mkdir()

        # Create nested structure
        nested = root / "a" / "b" / "c"
        nested.mkdir(parents=True)

        result = resolve_path_within_root(root, "a/b/c")
        assert result == nested.resolve()

    def test_rejects_symlink_escape(self, tmp_path: Path):
        """Test that symlinks escaping root are detected."""
        root = tmp_path / "root"
        root.mkdir()

        # Create directory outside root
        outside = tmp_path / "outside"
        outside.mkdir()

        # Create symlink from inside root to outside
        symlink = root / "symlink"
        try:
            symlink.symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        # The symlink itself exists within root, but resolves outside
        with pytest.raises(ValueError, match="Path escapes root"):
            resolve_path_within_root(root, "symlink")

    def test_rejects_empty_path(self, tmp_path: Path):
        """Test that empty paths are rejected."""
        root = tmp_path / "root"
        root.mkdir()

        with pytest.raises(ValueError, match="Invalid relative path"):
            resolve_path_within_root(root, "")

    def test_rejects_windows_separators(self, tmp_path: Path):
        """Test that Windows separators are rejected."""
        root = tmp_path / "root"
        root.mkdir()

        with pytest.raises(ValueError, match="Invalid relative path"):
            resolve_path_within_root(root, "path\\to\\file")


class TestIsSafePathComponent:
    """Tests for is_safe_path_component function."""

    def test_accepts_valid_filename(self):
        """Test that valid filenames are accepted."""
        assert is_safe_path_component("file.txt") is True
        assert is_safe_path_component("my-file_name.py") is True
        assert is_safe_path_component("data.json") is True

    def test_accepts_alphanumeric(self):
        """Test that alphanumeric characters are accepted."""
        assert is_safe_path_component("abc123") is True
        assert is_safe_path_component("Test123") is True

    def test_accepts_dots_hyphens_underscores(self):
        """Test that dots, hyphens, and underscores are accepted."""
        assert is_safe_path_component("file.name.txt") is True
        assert is_safe_path_component("my-file") is True
        assert is_safe_path_component("my_file") is True
        assert is_safe_path_component("file-name_v1.2.txt") is True

    def test_rejects_empty_string(self):
        """Test that empty strings are rejected."""
        assert is_safe_path_component("") is False

    def test_rejects_dot(self):
        """Test that single dot is rejected."""
        assert is_safe_path_component(".") is False

    def test_rejects_double_dot(self):
        """Test that double dot is rejected."""
        assert is_safe_path_component("..") is False

    def test_rejects_component_with_double_dot(self):
        """Test that components containing .. are rejected."""
        assert is_safe_path_component("file..txt") is False
        assert is_safe_path_component("..file") is False
        assert is_safe_path_component("file..") is False

    def test_rejects_path_separators(self):
        """Test that path separators are rejected."""
        assert is_safe_path_component("path/to/file") is False
        assert is_safe_path_component("path\\to\\file") is False

    def test_rejects_null_bytes(self):
        """Test that null bytes are rejected."""
        assert is_safe_path_component("file\x00name") is False

    def test_rejects_special_characters(self):
        """Test that special characters are rejected."""
        assert is_safe_path_component("file@name") is False
        assert is_safe_path_component("file!name") is False
        assert is_safe_path_component("file name") is False  # space


class TestSecurityEdgeCases:
    """Tests for edge cases and attack vectors."""

    def test_unicode_normalization_attack(self, tmp_path: Path):
        """Test that Unicode normalization doesn't allow escapes."""
        root = tmp_path / "root"
        root.mkdir()

        # Try various Unicode representations that might normalize to ..
        # Most should be rejected by the character validation
        with pytest.raises(ValueError):
            resolve_path_within_root(root, "path/\u2024\u2024/escape")

    def test_null_byte_injection(self, tmp_path: Path):
        """Test that null byte injection is prevented."""
        root = tmp_path / "root"
        root.mkdir()

        with pytest.raises(ValueError):
            resolve_path_within_root(root, "safe\x00../../../etc/passwd")

    def test_mixed_separators(self, tmp_path: Path):
        """Test that mixed separators don't bypass validation."""
        root = tmp_path / "root"
        root.mkdir()

        with pytest.raises(ValueError):
            resolve_path_within_root(root, "path\\..\\escape")

    def test_url_encoding_attack(self, tmp_path: Path):
        """Test that URL-encoded traversal is rejected."""
        root = tmp_path / "root"
        root.mkdir()

        # %2e%2e should not work
        with pytest.raises(ValueError):
            resolve_path_within_root(root, "%2e%2e/escape")

    def test_very_long_path(self, tmp_path: Path):
        """Test that very long paths are handled safely."""
        root = tmp_path / "root"
        root.mkdir()

        # Create a very long but valid path
        long_segment = "a" * 255  # Max filename length on most systems
        # This should work or raise an OS error, not a security error
        try:
            result = resolve_path_within_root(root, long_segment)
            # If it succeeds, verify it's still within root
            assert result.parent == root.resolve()
        except ValueError:
            # Acceptable if validation rejects it
            pass
        except OSError:
            # Acceptable if OS rejects it
            pass
