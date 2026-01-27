#!/usr/bin/env python3
"""
Week 1 Critical Fixes - Master Script

This script applies all Week 1 critical fixes:
1. Consolidate duplicate path validation code
2. Fix blocking subprocess calls in async context
3. Add job store eviction to prevent memory leaks
4. Implement TODO stubs

Usage:
    python fixes/week1_apply_all.py [--dry-run]
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_fix(script_name: str, dry_run: bool = False) -> bool:
    """Run a single fix script."""
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        print(f"❌ Fix script not found: {script_path}")
        return False
    
    print(f"\n{'='*70}")
    print(f"Running: {script_name}")
    print('='*70)
    
    if dry_run:
        print(f"[DRY RUN] Would execute: {script_path}")
        return True
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Fix failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Error running fix: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Apply Week 1 critical fixes")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--fix",
        choices=["1", "2", "3", "4", "all"],
        default="all",
        help="Apply specific fix (1-4) or all"
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("WEEK 1 CRITICAL FIXES")
    print("=" * 70)
    
    if args.dry_run:
        print("[DRY RUN MODE - No changes will be made]")
    
    fixes = {
        "1": ("week1_fix_1_consolidate_path_validation.py", "Consolidate path validation"),
        "2": ("week1_fix_2_async_subprocess.py", "Async subprocess calls"),
        "3": ("week1_fix_3_job_store_eviction.py", "Job store eviction"),
        "4": ("week1_fix_4_todo_implementations.py", "TODO implementations"),
    }
    
    results = []
    
    if args.fix == "all":
        for num in ["1", "2", "3", "4"]:
            script, desc = fixes[num]
            success = run_fix(script, args.dry_run)
            results.append((num, desc, success))
    else:
        script, desc = fixes[args.fix]
        success = run_fix(script, args.dry_run)
        results.append((args.fix, desc, success))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for num, desc, success in results:
        status = "✅" if success else "❌"
        print(f"{status} Fix #{num}: {desc}")
    
    all_success = all(r[2] for r in results)
    
    if not args.dry_run and all_success:
        print("\n" + "=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        print("1. Review the changes:")
        print("   git diff --stat")
        print("\n2. Run tests:")
        print("   uv run pytest tests/ -x 2>&1 | tail -20")
        print("\n3. If tests pass, commit the changes:")
        print("   git add -A")
        print('   git commit -m "Apply Week 1 critical fixes"')
    
    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
