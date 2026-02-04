"""
Shared utilities for saving skills to draft area.

This module provides utilities used by both v1 API routes and services
for saving completed skills to the draft directory.
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

from skill_fleet.taxonomy.manager import TaxonomyManager

from ...common.security import sanitize_taxonomy_path

if TYPE_CHECKING:
    from pathlib import Path

    from ...core.models import SkillCreationResult

logger = logging.getLogger(__name__)

_FENCE_START_RE = re.compile(r"^\s*```(?P<lang>[a-zA-Z0-9_+-]*)\s*$")
_HEADING_BACKTICK_RE = re.compile(r"^\s{0,3}#{2,6}\s+`(?P<name>[^`]+)`\s*$")


def _safe_single_filename(candidate: str) -> str | None:
    """
    Return a safe single-path filename or None.

    LLM output is untrusted; keep this strict to prevent path traversal.
    """
    name = candidate.strip()
    if not name:
        return None
    if "/" in name or "\\" in name:
        return None
    if name.startswith("."):
        return None
    if not all(c.isalnum() or c in "._-" for c in name):
        return None
    return name


def _extract_named_file_code_blocks(skill_md: str) -> dict[str, str]:
    """
    Extract code blocks that are explicitly labeled with a backticked filename heading.

    Example:
        ### `pytest.ini`
        ```ini
        ...
        ```

    """
    assets: dict[str, str] = {}
    lines = skill_md.splitlines()
    i = 0
    while i < len(lines):
        m = _HEADING_BACKTICK_RE.match(lines[i])
        if not m:
            i += 1
            continue

        raw_name = m.group("name")
        filename = _safe_single_filename(raw_name)
        if not filename:
            i += 1
            continue

        # Scan forward until we find the next fenced block (allow brief prose between).
        j = i + 1
        fence_line = None
        while j < len(lines):
            if lines[j].lstrip().startswith("#"):
                break
            if _FENCE_START_RE.match(lines[j]):
                fence_line = j
                break
            j += 1
        if fence_line is None:
            i += 1
            continue

        j = fence_line + 1
        body: list[str] = []
        while j < len(lines) and not lines[j].strip().startswith("```"):
            body.append(lines[j])
            j += 1

        if j < len(lines) and lines[j].strip().startswith("```"):
            assets[filename] = "\n".join(body).rstrip() + "\n"
            i = j + 1
            continue

        i += 1

    return assets


def _extract_usage_example_code_blocks(skill_md: str) -> dict[str, str]:
    """
    Extract fenced code blocks under the '## Usage Examples' section.

    Writes as simple `example_N.<ext>` files (best-effort).
    """
    lines = skill_md.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == "## Usage Examples":
            start = idx + 1
            break
    if start is None:
        return {}

    end = len(lines)
    for idx in range(start, len(lines)):
        # Stop at the next section at the same/higher level.
        if lines[idx].startswith("#") and lines[idx].lstrip().startswith("## "):
            end = idx
            break

    section = lines[start:end]

    ext_for_lang = {
        "python": "py",
        "py": "py",
        "bash": "sh",
        "sh": "sh",
        "zsh": "sh",
        "shell": "sh",
        "ini": "ini",
        "toml": "toml",
        "yaml": "yml",
        "yml": "yml",
        "json": "json",
    }

    examples: dict[str, str] = {}
    i = 0
    example_idx = 0
    while i < len(section):
        fence = _FENCE_START_RE.match(section[i])
        if not fence:
            i += 1
            continue

        lang = (fence.group("lang") or "").lower()
        i += 1
        body: list[str] = []
        while i < len(section) and not section[i].strip().startswith("```"):
            body.append(section[i])
            i += 1

        if i < len(section) and section[i].strip().startswith("```"):
            example_idx += 1
            ext = ext_for_lang.get(lang, "txt")
            filename = f"example_{example_idx}.{ext}"
            examples[filename] = "\n".join(body).rstrip() + "\n"
            i += 1
            continue

        i += 1

    return examples


def _ensure_draft_root(drafts_root: Path, job_id: str) -> Path:
    """
    Ensure the per-job draft root exists (with its own taxonomy_meta.json).

    Args:
        drafts_root: Base directory for drafts
        job_id: Unique job identifier

    Returns:
        Path to the job-specific draft root

    """
    job_root = drafts_root / job_id
    job_root.mkdir(parents=True, exist_ok=True)
    meta_path = job_root / "taxonomy_meta.json"
    if not meta_path.exists():
        meta_path.write_text(
            json.dumps(
                {
                    "total_skills": 0,
                    "generation_count": 0,
                    "statistics": {"by_type": {}, "by_weight": {}, "by_priority": {}},
                    "last_updated": "",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return job_root


async def save_skill_to_draft(
    *, drafts_root: Path, job_id: str, result: SkillCreationResult
) -> str | None:
    """
    Save a completed skill to the draft area.

    v2 Golden Standard: Also writes subdirectory files if provided in edit_result.

    Args:
        drafts_root: Base directory for drafts
        job_id: Unique job identifier
        result: SkillCreationResult from the workflow

    Returns:
        Path where the draft skill was saved, or None if save failed

    """
    if not result.skill_content or not result.metadata:
        logger.warning("Cannot save skill: missing content or metadata")
        return None

    try:
        draft_root = _ensure_draft_root(drafts_root, job_id)
        manager = TaxonomyManager(draft_root)

        # Extract metadata for registration
        metadata = result.metadata
        taxonomy_path = (
            metadata.taxonomy_path if hasattr(metadata, "taxonomy_path") else metadata.skill_id
        )

        # Use centralized path sanitization to prevent traversal attacks
        safe_taxonomy_path = sanitize_taxonomy_path(taxonomy_path)
        if not safe_taxonomy_path:
            logger.error("Unsafe taxonomy path provided by workflow: %s", taxonomy_path)
            return None

        # Build metadata dict for register_skill.
        #
        # Important: preserve workflow-produced metadata (capabilities, load_priority, etc.)
        # so deterministic validators and downstream tooling see the same intent the DSPy
        # planner produced.
        meta_dict = {
            "skill_id": metadata.skill_id,
            "name": metadata.name,
            "description": metadata.description,
            "version": metadata.version,
            "type": metadata.type,
            "weight": getattr(metadata, "weight", "medium"),
            "load_priority": getattr(metadata, "load_priority", "on_demand"),
            "dependencies": getattr(metadata, "dependencies", []) or [],
            "capabilities": getattr(metadata, "capabilities", []) or [],
            "category": getattr(metadata, "category", ""),
            "keywords": getattr(metadata, "keywords", []) or [],
            "scope": getattr(metadata, "scope", ""),
            "see_also": getattr(metadata, "see_also", []) or [],
            "tags": getattr(metadata, "tags", []) or [],
        }

        # Evolution tracking
        evolution = {
            "created_by": "skill-fleet-api",
            "workflow": "SkillCreationProgram",
            "validation_score": result.validation_report.score
            if result.validation_report
            else None,
        }

        # Register the skill (writes SKILL.md + metadata.json + standard subdirs)
        success = await manager.register_skill(
            path=safe_taxonomy_path,
            metadata=meta_dict,
            content=result.skill_content,
            evolution=evolution,
            extra_files=result.extra_files,
            overwrite=True,
        )

        if success:
            full_path = draft_root / safe_taxonomy_path
            try:
                skill_md_path = full_path / "SKILL.md"
                if skill_md_path.exists():
                    skill_md = skill_md_path.read_text(encoding="utf-8")
                    assets = _extract_named_file_code_blocks(skill_md)
                    examples = _extract_usage_example_code_blocks(skill_md)

                    if assets:
                        assets_dir = full_path / "assets"
                        assets_dir.mkdir(parents=True, exist_ok=True)
                        for filename, content in assets.items():
                            (assets_dir / filename).write_text(content, encoding="utf-8")

                    if examples:
                        examples_dir = full_path / "examples"
                        examples_dir.mkdir(parents=True, exist_ok=True)
                        for filename, content in examples.items():
                            (examples_dir / filename).write_text(content, encoding="utf-8")
            except Exception:
                logger.warning(
                    "Failed to extract skill artifacts (assets/examples) for %s",
                    full_path,
                    exc_info=True,
                )

            # v2 Golden Standard: Write subdirectory files if provided in edit_result
            # Subdirectory files come from the DSPy generation phase
            try:
                if result.edit_result and hasattr(result.edit_result, "subdirectory_files"):
                    subdir_files = result.edit_result.subdirectory_files
                    if subdir_files and isinstance(subdir_files, dict):
                        # Valid subdirectories per v2 standard
                        valid_subdirs = {"references", "guides", "templates", "scripts", "examples"}
                        for subdir_name, files in subdir_files.items():
                            if subdir_name not in valid_subdirs:
                                logger.warning("Skipping invalid subdirectory: %s", subdir_name)
                                continue
                            if not isinstance(files, dict):
                                continue
                            subdir_path = full_path / subdir_name
                            subdir_path.mkdir(parents=True, exist_ok=True)
                            for filename, content in files.items():
                                # Validate filename for safety
                                safe_filename = _safe_single_filename(filename)
                                if safe_filename:
                                    file_path = subdir_path / safe_filename
                                    file_path.write_text(str(content), encoding="utf-8")
                                    logger.debug(
                                        "Wrote subdirectory file: %s/%s",
                                        subdir_name,
                                        safe_filename,
                                    )
            except Exception as e:
                logger.warning(
                    "Failed to write subdirectory files for %s: %s",
                    full_path,
                    e,
                    exc_info=True,
                )

            logger.info("Draft saved successfully to: %s", full_path)
            return str(full_path)
        else:
            logger.error("Failed to register draft skill at path: %s", taxonomy_path)
            return None

    except Exception as e:
        logger.error(f"Error saving skill to draft: {e}", exc_info=True)
        return None
