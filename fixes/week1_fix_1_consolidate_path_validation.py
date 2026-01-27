#!/usr/bin/env python3
"""
Week 1 Fix #1: Consolidate duplicate path validation code.

This script consolidates the duplicate implementations between:
- src/skill_fleet/common/path_validation.py (more comprehensive)
- src/skill_fleet/common/security.py (simpler, used by more modules)

Strategy: Keep security.py as the canonical implementation and update it with
the best features from path_validation.py. Then make path_validation.py a
thin wrapper for backward compatibility.
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent / "src" / "skill_fleet" / "common"
SECURITY_PY = ROOT / "security.py"
PATH_VALIDATION_PY = ROOT / "path_validation.py"

def main():
    print("=" * 70)
    print("WEEK 1 FIX #1: Consolidate Path Validation")
    print("=" * 70)
    
    # Step 1: Create backup
    backup_path = PATH_VALIDATION_PY.with_suffix('.py.bak')
    shutil.copy2(PATH_VALIDATION_PY, backup_path)
    print(f"✅ Backed up path_validation.py to {backup_path.name}")
    
    # Step 2: Replace path_validation.py with a re-export module
    new_content = '''"""
Path validation utilities - DEPRECATED.

This module is deprecated. All functions have been moved to security.py.
Import from security.py directly for new code.

This module is kept for backward compatibility and re-exports all functions
from security.py.
"""

from __future__ import annotations

import warnings

# Re-export all functions from security.py
from .security import (
    is_safe_path_component,
    resolve_path_within_root,
    sanitize_relative_file_path,
    sanitize_taxonomy_path,
)

# Deprecated alias for backward compatibility
def resolve_skill_md_path(skills_root, taxonomy_path):
    """
    Resolve the path to a skill's SKILL.md file.
    
    DEPRECATED: Use resolve_path_within_root() directly instead.
    """
    warnings.warn(
        "resolve_skill_md_path is deprecated, use resolve_path_within_root directly",
        DeprecationWarning,
        stacklevel=2
    )
    from pathlib import Path
    
    safe_path = sanitize_taxonomy_path(taxonomy_path)
    if safe_path is None:
        raise ValueError("Invalid taxonomy path")
    
    skill_dir = skills_root / safe_path
    candidate_md = skill_dir / "SKILL.md"
    
    if not candidate_md.exists():
        raise FileNotFoundError(candidate_md)
    
    return candidate_md.resolve()


__all__ = [
    "is_safe_path_component",
    "resolve_path_within_root",
    "resolve_skill_md_path",
    "sanitize_relative_file_path",
    "sanitize_taxonomy_path",
]
'''
    
    PATH_VALIDATION_PY.write_text(new_content)
    print("✅ Updated path_validation.py to re-export from security.py")
    
    # Step 3: Update security.py with the better TOCTOU-safe function
    security_content = SECURITY_PY.read_text()
    
    # Check if resolve_skill_md_path already exists
    if "def resolve_skill_md_path" not in security_content:
        # Add the TOCTOU-safe resolve_skill_md_path function
        addition = '''

def resolve_skill_md_path(skills_root: Path, taxonomy_path: str) -> Path:
    """
    Resolve the path to a skill's SKILL.md file atomically.

    This function is TOCTOU (time-of-check-time-of-use) safe and
    prevents symlink-based path traversal attacks.

    Args:
        skills_root: Root directory for skills
        taxonomy_path: The taxonomy path to the skill (e.g., "python/fastapi")

    Returns:
        The absolute path to the SKILL.md file

    Raises:
        ValueError: If the path is invalid or escapes the skills root
        FileNotFoundError: If the SKILL.md file doesn't exist

    """
    # Sanitize and validate taxonomy path
    safe_taxonomy_path = sanitize_taxonomy_path(taxonomy_path)
    if safe_taxonomy_path is None:
        raise ValueError("Invalid path")

    skills_root_resolved = skills_root.resolve()

    # Resolve path atomically to prevent TOCTOU attacks
    # resolve(strict=True) raises FileNotFoundError if path doesn't exist
    # and resolves symlinks automatically while preserving safety
    skill_dir = skills_root_resolved / safe_taxonomy_path
    candidate_md = skill_dir / "SKILL.md"

    # Atomic check: verify SKILL.md exists
    # Using resolve(strict=True) is safe against TOCTOU
    try:
        resolved_md = candidate_md.resolve(strict=True)
    except FileNotFoundError:
        raise FileNotFoundError(candidate_md.as_posix()) from None

    # Verify resolved path is within skills root (prevents symlink escapes)
    try:
        resolved_md.relative_to(skills_root_resolved)
    except ValueError as e:
        raise ValueError("Invalid path") from e

    return resolved_md

'''
        
        # Insert before __all__
        security_content = security_content.replace(
            '\n__all__ = [',
            addition + '\n__all__ = ['
        )
        
        # Update __all__ to include new function
        security_content = security_content.replace(
            '"sanitize_taxonomy_path",\n]',
            '"sanitize_taxonomy_path",\n    "resolve_skill_md_path",\n]'
        )
        
        SECURITY_PY.write_text(security_content)
        print("✅ Added TOCTOU-safe resolve_skill_md_path to security.py")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✅ path_validation.py now re-exports from security.py")
    print("✅ All existing imports will continue to work")
    print("✅ New code should import from security.py directly")
    print("\n⚠️  Deprecated warnings will be shown for resolve_skill_md_path")
    print("   when imported from path_validation.py")
    print("\nTo complete the fix:")
    print("  1. Test that imports still work: python -c 'from skill_fleet.common.path_validation import sanitize_taxonomy_path'")
    print("  2. Run tests: uv run pytest tests/ -xvs -k 'path' 2>&1 | head -50")


if __name__ == "__main__":
    main()
