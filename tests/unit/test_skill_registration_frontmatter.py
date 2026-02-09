import yaml

from skill_fleet.taxonomy.skill_registration import generate_skill_md_with_frontmatter


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    assert content.startswith("---")
    end_marker = content.find("---", 3)
    assert end_marker != -1
    yaml_content = content[3:end_marker].strip()
    frontmatter = yaml.safe_load(yaml_content) or {}
    body = content[end_marker + 3 :].lstrip("\n")
    return frontmatter, body


def test_generate_skill_md_preserves_frontmatter_and_normalizes_allowed_tools() -> None:
    content = """---
name: old-name
description: old desc
model: claude-3-5
allowed-tools:
  - Read
  - Write
hooks:
  - name: pre
    command: echo hi
metadata:
  custom: keep
unknown-key: keep
---

# Title
Body line
"""

    metadata = {
        "skill_id": "practices/rlm",
        "version": "1.0.0",
        "type": "technical",
        "weight": "medium",
        "allowed_tools": ["Read", "Write", "Bash"],
    }

    output = generate_skill_md_with_frontmatter(
        name="new-name",
        description="new desc",
        metadata=metadata,
        content=content,
    )

    frontmatter, body = _parse_frontmatter(output)

    assert frontmatter["name"] == "new-name"
    assert frontmatter["description"] == "new desc"
    assert frontmatter["model"] == "claude-3-5"
    assert frontmatter["unknown-key"] == "keep"
    assert frontmatter["hooks"] == [{"name": "pre", "command": "echo hi"}]
    assert frontmatter["allowed-tools"] == "Read Write Bash"

    assert isinstance(frontmatter.get("metadata"), dict)
    assert frontmatter["metadata"]["custom"] == "keep"
    assert frontmatter["metadata"]["skill_id"] == "practices/rlm"

    assert body == "# Title\nBody line\n"
