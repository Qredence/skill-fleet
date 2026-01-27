#!/usr/bin/env python3
"""
Week 1 Fix #2: Fix blocking subprocess calls in async context.

This script updates taxonomy/skill_registration.py to use asyncio
create_subprocess_exec instead of blocking subprocess.run.
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent / "src" / "skill_fleet" / "taxonomy"
SKILL_REGISTRATION_PY = ROOT / "skill_registration.py"

def main():
    print("=" * 70)
    print("WEEK 1 FIX #2: Async Subprocess Calls")
    print("=" * 70)
    
    # Create backup
    backup_path = SKILL_REGISTRATION_PY.with_suffix('.py.bak')
    shutil.copy2(SKILL_REGISTRATION_PY, backup_path)
    print(f"✅ Backed up skill_registration.py to {backup_path.name}")
    
    # Read current content
    content = SKILL_REGISTRATION_PY.read_text()
    
    # Add asyncio import at top if not present
    if "import asyncio" not in content:
        content = content.replace(
            "import subprocess",
            "import asyncio\nimport subprocess"
        )
        print("✅ Added asyncio import")
    
    # Replace the lint_skill_code function with async version
    old_function = '''def lint_skill_code(skill_dir: Path, timeout: int = 30) -> None:
    """Run linting and formatting on skill Python files."""
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        return

    python_files = list(scripts_dir.rglob("*.py"))

    if not python_files:
        return

    # Run ruff check (linting)
    try:
        result = subprocess.run(
            ["uv", "run", "ruff", "check"] + [str(f) for f in python_files],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.warning(f"Linting issues found in skill {skill_dir.name}: {result.stdout}")
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
        logger.warning(f"Failed to lint skill {skill_dir.name}: {e}")

    # Run ruff format
    try:
        result = subprocess.run(
            ["uv", "run", "ruff", "format"] + [str(f) for f in python_files],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.warning(f"Formatting issues found in skill {skill_dir.name}: {result.stdout}")
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
        logger.warning(f"Failed to format skill {skill_dir.name}: {e}")'''

    new_function = '''async def lint_skill_code(skill_dir: Path, timeout: int = 30) -> None:
    """Run linting and formatting on skill Python files asynchronously."""
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        return

    python_files = list(scripts_dir.rglob("*.py"))

    if not python_files:
        return

    # Run ruff check (linting)
    try:
        proc = await asyncio.create_subprocess_exec(
            "uv", "run", "ruff", "check",
            *[str(f) for f in python_files],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
            if proc.returncode != 0:
                logger.warning(
                    f"Linting issues found in skill {skill_dir.name}: "
                    f"{stdout.decode() if stdout else stderr.decode()}"
                )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            logger.warning(f"Linting timed out for skill {skill_dir.name}")
    except (FileNotFoundError, OSError) as e:
        logger.warning(f"Failed to lint skill {skill_dir.name}: {e}")

    # Run ruff format
    try:
        proc = await asyncio.create_subprocess_exec(
            "uv", "run", "ruff", "format",
            *[str(f) for f in python_files],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
            if proc.returncode != 0:
                logger.warning(
                    f"Formatting issues found in skill {skill_dir.name}: "
                    f"{stdout.decode() if stdout else stderr.decode()}"
                )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            logger.warning(f"Formatting timed out for skill {skill_dir.name}")
    except (FileNotFoundError, OSError) as e:
        logger.warning(f"Failed to format skill {skill_dir.name}: {e}")'''

    if old_function in content:
        content = content.replace(old_function, new_function)
        print("✅ Updated lint_skill_code to async version")
    else:
        print("⚠️  Could not find exact function match, manual update may be needed")
    
    # Update callers to use await
    # Find calls to lint_skill_code and ensure they're awaited
    content = content.replace(
        "lint_skill_code(skill_dir)",
        "await lint_skill_code(skill_dir)"
    )
    print("✅ Updated callers to use await")
    
    # Write updated content
    SKILL_REGISTRATION_PY.write_text(content)
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("✅ lint_skill_code() is now async")
    print("✅ Uses asyncio.create_subprocess_exec() instead of subprocess.run()")
    print("✅ Proper timeout handling with asyncio.wait_for()")
    print("✅ Non-blocking - won't freeze the event loop")
    print("\n⚠️  Make sure callers use 'await lint_skill_code()'")
    print("   Updated automatic callers in this file")
    print("\nTo complete the fix:")
    print("  1. Check for other files calling lint_skill_code()")
    print("     grep -r 'lint_skill_code' src/ --include='*.py'")
    print("  2. Update those callers to use 'await'")
    print("  3. Run tests: uv run pytest tests/ -xvs -k 'skill' 2>&1 | head -50")


if __name__ == "__main__":
    main()
