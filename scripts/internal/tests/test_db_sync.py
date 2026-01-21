#!/usr/bin/env python3
"""
Test Database Sync Commands

Verifies that export-to-db and import-from-db commands work correctly.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from typer.testing import CliRunner

load_dotenv()

# Import CLI app
from skill_fleet.cli.app import app  # noqa: E402

# Initialize CLI runner
runner = CliRunner()


def test_export_dry_run():
    """Test export with dry-run mode."""
    print("\n" + "=" * 60)
    print("Test 1: Export to DB (Dry Run)")
    print("=" * 60)

    result = runner.invoke(app, ["export-to-db", "--dry-run"])

    if result.exit_code != 0:
        print(f"❌ Test failed with exit code {result.exit_code}")
        print(f"Output: {result.output}")
        return False

    print("✅ Export dry-run successful")
    print(f"Output:\n{result.output}")
    return True


def test_export_to_db():
    """Test actual export to database."""
    print("\n" + "=" * 60)
    print("Test 2: Export to DB (Actual)")
    print("=" * 60)

    result = runner.invoke(app, ["export-to-db", "--force"])

    if result.exit_code != 0:
        print(f"❌ Test failed with exit code {result.exit_code}")
        print(f"Output: {result.output}")
        return False

    print("✅ Export to database successful")
    print(f"Output:\n{result.output}")
    return True


def test_import_from_db():
    """Test import from database."""
    print("\n" + "=" * 60)
    print("Test 3: Import from DB")
    print("=" * 60)

    result = runner.invoke(app, ["import-from-db", "--status", "active"])

    if result.exit_code != 0:
        print(f"❌ Test failed with exit code {result.exit_code}")
        print(f"Output: {result.output}")
        return False

    print("✅ Import from database successful")
    print(f"Output:\n{result.output}")
    return True


def test_import_specific():
    """Test importing specific skill."""
    print("\n" + "=" * 60)
    print("Test 4: Import Specific Skill")
    print("=" * 60)

    result = runner.invoke(app, ["import-from-db", "--skill-path", "development/languages/python"])

    if result.exit_code != 0:
        print(f"❌ Test failed with exit code {result.exit_code}")
        print(f"Output: {result.output}")
        return False

    print("✅ Import specific skill successful")
    print(f"Output:\n{result.output}")
    return True


def test_sync_dry_run():
    """Test bidirectional sync with dry-run."""
    print("\n" + "=" * 60)
    print("Test 5: Sync DB (Dry Run)")
    print("=" * 60)

    result = runner.invoke(app, ["sync-db", "--dry-run"])

    if result.exit_code != 0:
        print(f"❌ Test failed with exit code {result.exit_code}")
        print(f"Output: {result.output}")
        return False

    print("✅ Sync dry-run successful")
    print(f"Output:\n{result.output}")
    return True


def check_environment():
    """Check if environment is properly configured."""
    print("\n" + "=" * 60)
    print("Environment Check")
    print("=" * 60)

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set")
        print("\nPlease set DATABASE_URL in .env or export it:")
        print("export DATABASE_URL='postgresql://...'")
        return False

    print("✅ DATABASE_URL is set")
    print(f"   Database: {db_url.split('@')[1] if '@' in db_url else 'unknown'}")

    # Check if .skills directory exists
    skills_dir = Path(".skills").resolve()
    if not skills_dir.exists():
        print(f"❌ Skills directory not found: {skills_dir}")
        return False

    print(f"✅ Skills directory exists: {skills_dir}")

    # Count skill files
    skill_files = list(skills_dir.rglob("SKILL.md"))
    print(f"   Found {len(skill_files)} skill files")

    return True


def run_all_tests():
    """Run all sync tests."""
    print("\n" + "=" * 60)
    print("Database Sync Commands Test Suite")
    print("=" * 60)

    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed")
        sys.exit(1)

    # Run tests
    tests = [
        ("Export Dry Run", test_export_dry_run),
        ("Export to DB", test_export_to_db),
        ("Import from DB", test_import_from_db),
        ("Import Specific", test_import_specific),
        ("Sync Dry Run", test_sync_dry_run),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Test '{name}' raised exception: {e}")
            import traceback

            traceback.print_exc()
            results.append((name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
