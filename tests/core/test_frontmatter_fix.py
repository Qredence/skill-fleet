"""Test for frontmatter canonicalization fix."""

import pytest
import yaml

from skill_fleet.core.dspy.modules.phase3_validation import _canonicalize_skill_md_frontmatter


class TestFrontmatterCanonicalization:
    """Test that _canonicalize_skill_md_frontmatter correctly handles multi-line descriptions."""

    def test_single_line_description(self):
        """Single-line description should use plain YAML."""
        metadata = {
            "name": "test-skill",
            "description": "A single-line description for testing.",
        }

        content = "# Test Skill\n\nSome content..."
        result = _canonicalize_skill_md_frontmatter(content, metadata)

        # Parse frontmatter
        frontmatter_part = result.split("---")[1].split("---")[0]
        parsed = yaml.safe_load(frontmatter_part)

        assert parsed["name"] == "test-skill"
        assert parsed["description"] == "A single-line description for testing."
        # Should use plain description, not folded scalar
        assert "description: >" not in result

    def test_multiline_description_uses_folded_scalar(self):
        """Multi-line description should use folded scalar."""
        long_desc = "Use when building FastAPI apps with async database operations, connection pool issues, or partial update bugs. Apply for production-ready applications."
        metadata = {
            "name": "fastapi-patterns",
            "description": long_desc,
        }

        content = "# Test Skill\n\nSome content..."
        result = _canonicalize_skill_md_frontmatter(content, metadata)

        # Parse frontmatter
        frontmatter_part = result.split("---")[1].split("---")[0]
        parsed = yaml.safe_load(frontmatter_part)

        assert parsed["name"] == "fastapi-patterns"
        # Folded scalar adds trailing newline - normalize comparison
        assert parsed["description"].strip() == long_desc
        # Should use folded scalar syntax
        assert "description: >" in result

    def test_long_description_truncation(self):
        """Descriptions over 1024 chars should be truncated."""
        # Create description that exceeds 1024 chars
        long_desc = "A description that is definitely way too long for the description field." * 50
        assert len(long_desc) > 1024, "Test setup: description must exceed 1024 chars"
        
        metadata = {
            "name": "test-skill",
            "description": long_desc,
        }

        content = "# Test Skill\n\nSome content..."
        result = _canonicalize_skill_md_frontmatter(content, metadata)

        # Parse frontmatter
        frontmatter_part = result.split("---")[1].split("---")[0]
        parsed = yaml.safe_load(frontmatter_part)

        # Original truncation should be <= 1024 chars
        # YAML folded scalar may add trailing whitespace/newlines
        assert len(parsed["description"].strip()) <= 1024

    def test_invalid_yaml_frontmatter_stripping(self):
        """Existing invalid frontmatter should be stripped and fixed."""
        # Simulating broken frontmatter with incorrect multi-line indentation
        broken_frontmatter = """---
name: test-skill
description: Use when Python Docker images are excessively large (>800MB), build times
  are slow due to redundant dependency installation...
---
# Content
"""

        metadata = {
            "name": "test-skill",
            "description": "Use when Python Docker images are excessively large (>800MB), build times are slow due to redundant dependency installation.",
        }

        result = _canonicalize_skill_md_frontmatter(broken_frontmatter, metadata)

        # Frontmatter should be fixed
        frontmatter_part = result.split("---")[1].split("---")[0]
        parsed = yaml.safe_load(frontmatter_part)

        # Folded scalar adds trailing newline - normalize
        assert parsed["description"].strip() == metadata["description"]
        # Should use folded scalar
        assert "description: >" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
