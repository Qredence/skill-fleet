"""Sync packaged runtime resources into `src/skill_fleet/`.

Skill Fleet ships a small set of runtime defaults inside the Python package so
the wheel works out-of-the-box (no repo checkout required):
- `src/skill_fleet/config/**` (config.yaml, templates, training data)
- `src/skill_fleet/_seed/skills/**` (minimal skills taxonomy bootstrap)

In-repo development uses the top-level `config/` and `skills/` directories as
the source of truth. Run this script after updating those directories.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from shutil import copy2


def _iter_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file()]


def _sync_tree(*, src_root: Path, dst_root: Path, exclude: set[str]) -> None:
    src_root = src_root.resolve()
    dst_root = dst_root.resolve()
    dst_root.mkdir(parents=True, exist_ok=True)

    src_files: set[Path] = set()
    for src_path in _iter_files(src_root):
        rel = src_path.relative_to(src_root)
        rel_str = rel.as_posix()
        if rel_str in exclude:
            continue

        src_files.add(rel)
        dst_path = dst_root / rel
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        copy2(src_path, dst_path)

    # Delete files in dst that no longer exist in src (excluding the excluded set).
    for dst_path in _iter_files(dst_root):
        rel = dst_path.relative_to(dst_root)
        rel_str = rel.as_posix()
        if rel_str in exclude:
            continue
        if rel not in src_files:
            dst_path.unlink()


def main(argv: list[str] | None = None) -> int:
    """Sync top-level `config/` + `skills/` into `src/skill_fleet/` resources."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repo root (defaults to the parent of this script's directory)",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root or Path(__file__).resolve().parents[1]

    src_config = repo_root / "config"
    dst_config = repo_root / "src" / "skill_fleet" / "config"
    if not src_config.is_dir():
        print(f"error: missing source config dir: {src_config}", file=sys.stderr)
        return 2

    _sync_tree(
        src_root=src_config,
        dst_root=dst_config,
        exclude={
            # Binary: keep it repo-only unless we explicitly decide to ship it.
            "optimized/miprov2/program.pkl",
        },
    )

    # Seed skills (minimal bootstrap files only)
    src_skills = repo_root / "skills"
    dst_seed = repo_root / "src" / "skill_fleet" / "_seed" / "skills"
    dst_seed_templates = dst_seed / "_templates"
    dst_seed_templates.mkdir(parents=True, exist_ok=True)

    for rel in (
        Path("taxonomy_index.json"),
        Path("taxonomy_meta.json"),
        Path("_templates") / "skill_template.json",
    ):
        src_path = src_skills / rel
        dst_path = dst_seed / rel
        if not src_path.exists():
            print(f"error: missing seed file: {src_path}", file=sys.stderr)
            return 2
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        copy2(src_path, dst_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
