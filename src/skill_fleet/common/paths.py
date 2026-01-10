"""Path resolution helpers for skill_fleet defaults.

These helpers avoid assuming a checked-out repo and prefer packaged defaults
when running from an installed wheel.
"""

from __future__ import annotations

from pathlib import Path


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

    candidates.append(_package_root() / "skills")

    return _first_existing(candidates) or (Path.cwd() / "skills")

