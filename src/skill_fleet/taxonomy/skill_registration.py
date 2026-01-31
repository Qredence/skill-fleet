"""
Skill registration utilities for taxonomy management.

Handles registering new skills to the taxonomy, including:
- Creating directory structure
- Writing metadata.json and SKILL.md
- agentskills.io compliance (YAML frontmatter)
- Populating extra files and subdirectories
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import yaml

from ..common.security import (
    is_safe_path_component,
    resolve_path_within_root,
    sanitize_relative_file_path,
    sanitize_taxonomy_path,
)
from .metadata import SkillMetadata
from .naming import skill_id_to_name

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def register_skill(
    skills_root: Path,
    path: str,
    metadata: dict[str, Any],
    content: str,
    evolution: dict[str, Any],
    extra_files: dict[str, Any] | None = None,
    overwrite: bool = False,
) -> SkillMetadata:
    """
    Register a new skill in the taxonomy.

    Creates an agentskills.io compliant skill with YAML frontmatter in SKILL.md
    and extended metadata in metadata.json.

    Args:
        skills_root: Root directory of the taxonomy
        path: Taxonomy path for the skill
        metadata: Skill metadata dictionary
        content: SKILL.md content (markdown)
        evolution: Evolution/tracking metadata
        extra_files: Optional dict of additional files to create
        overwrite: Whether to overwrite existing skill

    Returns:
        SkillMetadata object for the registered skill

    Raises:
        ValueError: If path is invalid or skill exists and overwrite=False

    """
    import re

    safe_path = sanitize_taxonomy_path(path)
    if safe_path is None:
        raise ValueError(f"Invalid taxonomy path: {path}")

    skill_dir = resolve_path_within_root(skills_root, safe_path)
    if (skill_dir / "metadata.json").exists() and not overwrite:
        raise ValueError(f"Skill already exists at {path}")
    skill_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(tz=UTC).isoformat()

    # Ensure skill_id is set
    metadata.setdefault("skill_id", safe_path)
    skill_id = metadata["skill_id"]

    # Ensure metadata.json contains required taxonomy fields
    metadata.setdefault("version", "1.0.0")
    metadata.setdefault("type", "technical")
    metadata.setdefault("weight", "medium")
    metadata.setdefault("load_priority", "on_demand")

    if not isinstance(metadata.get("dependencies"), list):
        metadata["dependencies"] = []
    if not isinstance(metadata.get("capabilities"), list):
        metadata["capabilities"] = []
    if not isinstance(metadata.get("tags"), list):
        metadata["tags"] = []
    if not metadata.get("category") and "/" in path:
        metadata["category"] = "/".join(path.split("/")[:-1])

    # Generate agentskills.io compliant name
    name = metadata.get("name") or skill_id_to_name(skill_id)
    metadata["name"] = name

    # Ensure description exists
    description = metadata.get("description", "")
    if not description:
        # Try to extract from content if it looks like markdown
        first_para = content.split("\n\n")[0] if content else ""
        # Strip markdown headers
        description = re.sub(r"^#.*\n?", "", first_para).strip()[:1024]
        metadata["description"] = description

    metadata["created_at"] = metadata.get("created_at", now)
    metadata["last_modified"] = now
    metadata["evolution"] = evolution

    # Write extended metadata to metadata.json
    metadata_path = skill_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    # Generate SKILL.md with agentskills.io compliant YAML frontmatter
    skill_md_content = generate_skill_md_with_frontmatter(
        name=name,
        description=description,
        metadata=metadata,
        content=content,
    )
    (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")

    # Populate extra files if provided
    if extra_files:
        write_extra_files(skill_dir, extra_files)

    # Create SkillMetadata object
    skill_metadata = SkillMetadata(
        skill_id=skill_id,
        version=metadata.get("version", "1.0.0"),
        type=metadata.get("type", "technical"),
        weight=metadata.get("weight", "medium"),
        load_priority=metadata.get("load_priority", "on_demand"),
        dependencies=list(metadata.get("dependencies", [])),
        capabilities=list(metadata.get("capabilities", [])),
        path=metadata_path,
        always_loaded=bool(metadata.get("always_loaded", False)),
        name=name,
        description=description,
    )

    return skill_metadata


def generate_skill_md_with_frontmatter(
    name: str,
    description: str,
    metadata: dict[str, Any],
    content: str,
) -> str:
    """
    Generate SKILL.md content with agentskills.io compliant YAML frontmatter.

    Args:
        name: Kebab-case skill name
        description: Skill description (1-1024 chars)
        metadata: Extended metadata dict
        content: Original markdown content (may or may not have frontmatter)

    Returns:
        Complete SKILL.md content with proper frontmatter

    """
    # Strip existing frontmatter from content if present
    body_content = content
    if content.startswith("---"):
        end_marker = content.find("---", 3)
        if end_marker != -1:
            body_content = content[end_marker + 3 :].lstrip("\n")

    # Build frontmatter
    frontmatter = {
        "name": name,
        "description": description[:1024],  # Enforce max length
    }

    # Add optional extended metadata
    extended_meta = {}
    if metadata.get("skill_id"):
        extended_meta["skill_id"] = metadata["skill_id"]
    if metadata.get("version"):
        extended_meta["version"] = metadata["version"]
    if metadata.get("type"):
        extended_meta["type"] = metadata["type"]
    if metadata.get("weight"):
        extended_meta["weight"] = metadata["weight"]

    if extended_meta:
        frontmatter["metadata"] = extended_meta

    # Generate YAML frontmatter
    yaml_content = yaml.dump(
        frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False
    )

    return f"---\n{yaml_content}---\n\n{body_content}"


def write_extra_files(skill_dir: Path, extra_files: dict[str, Any]) -> None:
    """
    Populate skill subdirectories with additional content.

    Only creates directories when there is actual content to write.

    Args:
        skill_dir: Path to the skill directory
        extra_files: Dictionary mapping file categories to content

    """
    # Handle capability implementations
    if "capability_implementations" in extra_files:
        caps = extra_files["capability_implementations"]
        if isinstance(caps, str) and caps.strip().startswith(("{", "[")):
            try:
                caps = json.loads(caps)
            except json.JSONDecodeError:
                pass

        if isinstance(caps, dict):
            caps_dir = skill_dir / "references" / "capability-implementations"
            caps_dir.mkdir(parents=True, exist_ok=True)
            for cap_id, cap_content in caps.items():
                raw_name = f"{str(cap_id).replace('/', '_')}.md"
                filename = raw_name if is_safe_path_component(raw_name) else "implementation.md"
                (caps_dir / filename).write_text(str(cap_content), encoding="utf-8")
        else:
            refs_dir = skill_dir / "references"
            refs_dir.mkdir(exist_ok=True)
            (refs_dir / "capability-implementations.md").write_text(str(caps), encoding="utf-8")

    # Handle usage examples
    if "usage_examples" in extra_files:
        examples = extra_files["usage_examples"]
        if isinstance(examples, str) and examples.strip().startswith(("{", "[")):
            try:
                examples = json.loads(examples)
            except json.JSONDecodeError:
                pass

        if isinstance(examples, list):
            examples_dir = skill_dir / "examples"
            examples_dir.mkdir(exist_ok=True)
            for i, example in enumerate(examples):
                if isinstance(example, dict):
                    content = example.get("code") or example.get("content")
                    if content:
                        ext = ".py" if "code" in example else ".md"
                        suggested = str(example.get("filename", "")).strip()
                        default_name = f"example_{i + 1}{ext}"
                        filename = (
                            suggested
                            if suggested and is_safe_path_component(suggested)
                            else default_name
                        )
                    else:
                        suggested = str(example.get("filename", "")).strip()
                        default_name = f"example_{i + 1}.json"
                        filename = (
                            suggested
                            if suggested and is_safe_path_component(suggested)
                            else default_name
                        )
                        content = json.dumps(example, indent=2)
                else:
                    filename = f"example_{i + 1}.md"
                    content = str(example)
                (examples_dir / filename).write_text(content, encoding="utf-8")
        else:
            examples_dir = skill_dir / "examples"
            examples_dir.mkdir(exist_ok=True)
            (examples_dir / "examples.md").write_text(str(examples), encoding="utf-8")

    # Handle tests
    if "integration_tests" in extra_files:
        tests = extra_files["integration_tests"]
        if isinstance(tests, str) and tests.strip().startswith(("{", "[")):
            try:
                tests = json.loads(tests)
            except json.JSONDecodeError:
                pass

        if isinstance(tests, list):
            tests_dir = skill_dir / "tests"
            tests_dir.mkdir(exist_ok=True)
            for i, test in enumerate(tests):
                if isinstance(test, dict):
                    content = test.get("code") or test.get("content")
                    if content:
                        ext = ".py" if "code" in test else ".md"
                        suggested = str(test.get("filename", "")).strip()
                        default_name = f"test_{i + 1}{ext}"
                        filename = (
                            suggested
                            if suggested and is_safe_path_component(suggested)
                            else default_name
                        )
                    else:
                        suggested = str(test.get("filename", "")).strip()
                        default_name = f"test_{i + 1}.json"
                        filename = (
                            suggested
                            if suggested and is_safe_path_component(suggested)
                            else default_name
                        )
                        content = json.dumps(test, indent=2)
                else:
                    filename = f"test_{i + 1}.py"
                    content = str(test)
                (tests_dir / filename).write_text(content, encoding="utf-8")
        else:
            tests_dir = skill_dir / "tests"
            tests_dir.mkdir(exist_ok=True)
            (tests_dir / "test_skill.py").write_text(str(tests), encoding="utf-8")

    # Handle best practices
    if "best_practices" in extra_files and extra_files["best_practices"]:
        bp = extra_files["best_practices"]
        if isinstance(bp, str) and bp.strip().startswith("["):
            try:
                bp_list = json.loads(bp)
                content = "## Best Practices\n\n" + "\n".join([f"- {item}" for item in bp_list])
            except (json.JSONDecodeError, TypeError):
                content = str(bp)
        else:
            content = str(bp)
        (skill_dir / "best_practices.md").write_text(content, encoding="utf-8")

    # Handle integration guide
    if "integration_guide" in extra_files and extra_files["integration_guide"]:
        guide = extra_files["integration_guide"]
        (skill_dir / "integration.md").write_text(str(guide), encoding="utf-8")

    # Handle resource requirements
    if "resource_requirements" in extra_files and extra_files["resource_requirements"]:
        res = extra_files["resource_requirements"]
        guides_dir = skill_dir / "guides"
        guides_dir.mkdir(exist_ok=True)
        filename = (
            "requirements.json"
            if isinstance(res, dict | list)
            or (isinstance(res, str) and res.strip().startswith(("{", "[")))
            else "requirements.md"
        )
        (guides_dir / filename).write_text(str(res), encoding="utf-8")

    # Handle bundled resources
    for category in ["scripts", "assets", "resources"]:
        if category in extra_files:
            items = extra_files[category]
            if isinstance(items, dict):
                target_dir = skill_dir / ("guides" if category == "resources" else category)
                target_dir.mkdir(parents=True, exist_ok=True)
                for filename, content in items.items():
                    sanitized = sanitize_relative_file_path(str(filename))
                    if sanitized is None:
                        continue
                    file_path = resolve_path_within_root(target_dir, sanitized)
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    if isinstance(content, bytes):
                        file_path.write_bytes(content)
                    else:
                        file_path.write_text(str(content), encoding="utf-8")


def create_skill_subdirectories(skill_dir: Path, skill_name: str) -> None:
    """
    Create standard skill subdirectories with README.md files.

    Creates the following structure (v2 Golden Standard format):
    - references/README.md, quick-start.md, common-patterns.md, api-reference.md, troubleshooting.md
    - guides/README.md (formerly resources/)
    - templates/README.md
    - scripts/README.md
    - examples/README.md
    - tests/README.md
    - assets/README.md

    Legacy directories (capabilities/, resources/) are created for backward compatibility
    but new skills should use references/ and guides/ instead.

    Args:
        skill_dir: Path to the skill directory
        skill_name: Name of the skill (for README content)

    """
    # Define subdirectories and their README content
    subdirs = {
        "capabilities": f"# Capabilities (Legacy)\n\n**Note:** This directory is deprecated. Use `references/` instead for new skills.\n\nCapability implementations for `{skill_name}`.\n\nEach file in this directory documents a specific capability provided by this skill.\n",
        "resources": f"# Resources (Legacy)\n\n**Note:** This directory is deprecated. Use `guides/` instead for new skills.\n\nResource files for `{skill_name}`.\n\nIncludes configuration files, data files, and other resources needed by the skill.\n",
        "examples": f"# Examples\n\nUsage examples for `{skill_name}`.\n\nEach file demonstrates a specific use case or pattern.\n",
        "tests": f"# Tests\n\nIntegration tests for `{skill_name}`.\n\nThese tests verify the skill's capabilities work as expected.\n",
        "guides": f"# Guides\n\nHow-to guides and tutorials for `{skill_name}`.\n\nStep-by-step instructions for common tasks and workflows.\n",
        "references": f"# References\n\nReference documentation for `{skill_name}`.\n\n## Contents\n\n- [Quick Start](quick-start.md) - Get started quickly\n- [Common Patterns](common-patterns.md) - Frequently used patterns\n- [API Reference](api-reference.md) - Detailed API documentation\n- [Troubleshooting](troubleshooting.md) - Common issues and solutions\n",
        "scripts": f"# Scripts\n\nUtility scripts for `{skill_name}`.\n\nThese scripts help with setup, maintenance, or automation tasks.\n",
        "assets": f"# Assets\n\nStatic assets for `{skill_name}`.\n\nIncludes images, diagrams, and other static files.\n",
    }

    # Create each subdirectory with README.md
    for subdir, readme_content in subdirs.items():
        subdir_path = skill_dir / subdir
        subdir_path.mkdir(exist_ok=True)
        readme_path = subdir_path / "README.md"
        if not readme_path.exists():
            readme_path.write_text(readme_content, encoding="utf-8")

    # Create reference documentation templates
    references_dir = skill_dir / "references"

    quick_start_content = f"""# Quick Start Guide

Get started with `{skill_name}` in minutes.

## Prerequisites

- List prerequisites here

## Installation

```bash
# Installation steps
```

## Basic Usage

```python
# Basic usage example
```

## Next Steps

- See [Common Patterns](common-patterns.md) for more examples
- Check [API Reference](api-reference.md) for detailed documentation
"""

    common_patterns_content = f"""# Common Patterns

Frequently used patterns with `{skill_name}`.

## Pattern 1: Basic Usage

Description of the pattern.

```python
# Example code
```

## Pattern 2: Advanced Usage

Description of the pattern.

```python
# Example code
```

## Anti-Patterns

Things to avoid when using this skill.
"""

    api_reference_content = f"""# API Reference

Detailed API documentation for `{skill_name}`.

## Core Functions

### function_name

```python
def function_name(param1: type, param2: type) -> return_type:
    \"\"\"Description of the function.\"\"\"
```

**Parameters:**
- `param1`: Description
- `param2`: Description

**Returns:** Description of return value

**Example:**
```python
# Usage example
```

## Classes

### ClassName

Description of the class.

#### Methods

- `method_name()`: Description
"""

    troubleshooting_content = f"""# Troubleshooting

Common issues and solutions for `{skill_name}`.

## Common Issues

### Issue 1: Description

**Symptoms:** What you might see

**Cause:** Why this happens

**Solution:** How to fix it

```python
# Fix example
```

### Issue 2: Description

**Symptoms:** What you might see

**Cause:** Why this happens

**Solution:** How to fix it

## Getting Help

If you encounter issues not covered here:
1. Check the [API Reference](api-reference.md)
2. Review [Common Patterns](common-patterns.md)
3. Search existing issues
"""

    # Write reference documentation files if they don't exist
    ref_files = {
        "quick-start.md": quick_start_content,
        "common-patterns.md": common_patterns_content,
        "api-reference.md": api_reference_content,
        "troubleshooting.md": troubleshooting_content,
    }

    for filename, content in ref_files.items():
        file_path = references_dir / filename
        if not file_path.exists():
            file_path.write_text(content, encoding="utf-8")


async def lint_and_format_skill(skill_dir: Path) -> None:
    """
    Lint and format Python files in generated skill directory asynchronously.

    Runs ruff linting and formatting on all Python files in the skill's
    examples/ and scripts/ subdirectories to ensure code quality.

    Args:
        skill_dir: Path to skill directory

    """
    python_files = []
    examples_dir = skill_dir / "examples"
    scripts_dir = skill_dir / "scripts"

    # Collect Python files from examples/
    if examples_dir.exists():
        python_files.extend(examples_dir.rglob("*.py"))

    # Collect Python files from scripts/
    if scripts_dir.exists():
        python_files.extend(scripts_dir.rglob("*.py"))

    if not python_files:
        return

    # Run ruff check (linting)
    try:
        proc = await asyncio.create_subprocess_exec(
            "uv",
            "run",
            "ruff",
            "check",
            *[str(f) for f in python_files],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            if proc.returncode != 0:
                logger.warning(
                    f"Linting issues in skill {skill_dir.name}: "
                    f"{stdout.decode() if stdout else stderr.decode()}"
                )
        except TimeoutError:
            proc.kill()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except TimeoutError:
                logger.error(f"Failed to terminate linting process for {skill_dir.name}")
            logger.warning(f"Linting timed out for skill {skill_dir.name}")
    except (FileNotFoundError, OSError) as e:
        logger.warning(f"Failed to lint skill {skill_dir.name}: {e}")

    # Run ruff format
    try:
        proc = await asyncio.create_subprocess_exec(
            "uv",
            "run",
            "ruff",
            "format",
            *[str(f) for f in python_files],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            if proc.returncode != 0:
                logger.warning(
                    f"Formatting issues in skill {skill_dir.name}: "
                    f"{stdout.decode() if stdout else stderr.decode()}"
                )
        except TimeoutError:
            proc.kill()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except TimeoutError:
                logger.error(f"Failed to terminate formatting process for {skill_dir.name}")
            logger.warning(f"Formatting timed out for skill {skill_dir.name}")
    except (FileNotFoundError, OSError) as e:
        logger.warning(f"Failed to format skill {skill_dir.name}: {e}")
