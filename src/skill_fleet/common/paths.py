"""Path resolution helpers for skill_fleet defaults.

These helpers avoid assuming a checked-out repo and prefer packaged defaults
when running from an installed wheel.

Separately, some resources (like a seed skills taxonomy) are bundled for
bootstrapping new working directories without requiring the repo to be cloned.
"""

from __future__ import annotations

import json
from pathlib import Path
from shutil import copy2

_REPO_MARKERS = (".git", "pyproject.toml")


def _iter_parents(start: Path) -> list[Path]:
    start_dir = start if start.is_dir() else start.parent
    return [start_dir, *start_dir.parents]


def find_repo_root(start: Path | None = None) -> Path | None:
    """Find a repo root by walking parents for common markers."""
    for parent in _iter_parents((start or Path.cwd()).resolve()):
        if any((parent / marker).exists() for marker in _REPO_MARKERS):
            return parent
    return None


def _package_root() -> Path:
    # skill_fleet/common/paths.py -> skill_fleet/
    return Path(__file__).resolve().parents[1]


def _seed_skills_root() -> Path:
    return _package_root() / "_seed" / "skills"


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def default_config_path() -> Path:
    """Resolve the default fleet config path with safe fallbacks."""
    candidates: list[Path] = []

    for root in (find_repo_root(Path.cwd()), find_repo_root(Path(__file__).resolve())):
        if root:
            candidates.append(root / "config" / "config.yaml")

    candidates.append(_package_root() / "config" / "config.yaml")

    return _first_existing(candidates) or (Path.cwd() / "config" / "config.yaml")


def default_config_root() -> Path:
    """Resolve the default fleet config directory (the parent of config.yaml)."""
    return default_config_path().parent


def resolve_repo_relative_path(path: str | Path, *, config_path: Path | None = None) -> Path:
    """Resolve a repo-style relative path with fallbacks for installed wheels.

    This is primarily for paths like `config/training/trainset.json` referenced in
    code/config. Resolution order:
    1) Current working directory relative path (if it exists)
    2) Repo root relative path (if in a checkout)
    3) Packaged config directory (for `config/...` paths)
    4) Return the original relative path (best-effort)
    """
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate

    if candidate.exists():
        return candidate

    repo_root = find_repo_root(Path.cwd())
    if repo_root:
        repo_candidate = repo_root / candidate
        if repo_candidate.exists():
            return repo_candidate

    parts = candidate.parts
    if parts and parts[0] == "config":
        base = (config_path or default_config_path()).parent
        packaged_candidate = base.joinpath(*parts[1:])
        if packaged_candidate.exists():
            return packaged_candidate

    return candidate


def default_profiles_path() -> Path:
    """Resolve the default onboarding profiles path with safe fallbacks."""
    candidates: list[Path] = []

    for root in (find_repo_root(Path.cwd()), find_repo_root(Path(__file__).resolve())):
        if root:
            candidates.append(root / "config" / "profiles" / "bootstrap_profiles.json")

    candidates.append(_package_root() / "config" / "profiles" / "bootstrap_profiles.json")

    return _first_existing(candidates) or (
        Path.cwd() / "config" / "profiles" / "bootstrap_profiles.json"
    )


def default_skills_root() -> Path:
    """Resolve the default skills root path with safe fallbacks."""
    candidates: list[Path] = []

    for root in (find_repo_root(Path.cwd()), find_repo_root(Path(__file__).resolve())):
        if root:
            candidates.append(root / "skills")

    # Prefer a writable local skills directory when running from an installed wheel.
    candidates.append(Path.cwd() / "skills")

    return _first_existing(candidates) or (Path.cwd() / "skills")


def ensure_skills_root_initialized(skills_root: Path) -> Path:
    """Ensure a skills_root exists and has the minimal required files.

    This is primarily for first-run UX when installed from PyPI: users shouldn't
    need to clone the repo just to get `taxonomy_meta.json`, `taxonomy_index.json`,
    and the default `_templates/skill_template.json`.
    """
    root_path = Path(skills_root)
    if root_path.exists():
        if root_path.is_symlink():
            raise ValueError("skills_root must not be a symlink")
        resolved = root_path.resolve(strict=True)
        if not resolved.is_dir():
            raise ValueError("skills_root must be a directory")
    else:
        root_path.mkdir(parents=True, exist_ok=True)
        resolved = root_path.resolve(strict=True)

    seed_root = _seed_skills_root()

    # taxonomy_meta.json (required by TaxonomyManager)
    meta_path = resolved / "taxonomy_meta.json"
    if not meta_path.exists():
        if meta_path.is_symlink():
            raise ValueError("taxonomy_meta.json must not be a symlink")
        seed_meta = seed_root / "taxonomy_meta.json"
        if seed_meta.exists():
            copy2(seed_meta, meta_path)
        else:
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

    # taxonomy_index.json (optional but expected by migration + alias resolution)
    index_path = resolved / "taxonomy_index.json"
    if not index_path.exists():
        if index_path.is_symlink():
            raise ValueError("taxonomy_index.json must not be a symlink")
        seed_index = seed_root / "taxonomy_index.json"
        if seed_index.exists():
            copy2(seed_index, index_path)
        else:
            index_path.write_text(
                json.dumps({"version": "0.1", "skills": {}}, indent=2) + "\n",
                encoding="utf-8",
            )

    # _templates/skill_template.json (optional, used by SkillValidator overrides)
    template_path = resolved / "_templates" / "skill_template.json"
    if not template_path.exists():
        if template_path.is_symlink():
            raise ValueError("skill_template.json must not be a symlink")
        template_path.parent.mkdir(parents=True, exist_ok=True)
        if template_path.parent.is_symlink():
            raise ValueError("_templates must not be a symlink")
        seed_template = seed_root / "_templates" / "skill_template.json"
        if seed_template.exists():
            copy2(seed_template, template_path)

    return resolved


__all__ = [
    "find_repo_root",
    "default_config_path",
    "default_config_root",
    "resolve_repo_relative_path",
    "default_profiles_path",
    "default_skills_root",
    "ensure_skills_root_initialized",
]
