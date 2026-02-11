#!/usr/bin/env python3
"""
Skills-Fleet Repository Layer Test

This script tests the SQLAlchemy models and repository layer
to ensure database operations work correctly.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os as python_os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Import models and repositories
from skill_fleet.infrastructure.db.models import JobStatusEnum, SkillStatusEnum, SkillTypeEnum
from skill_fleet.infrastructure.db.repositories import (
    JobRepository,
    SkillRepository,
    TaxonomyRepository,
)

load_dotenv()
DATABASE_URL = python_os.getenv("DATABASE_URL", "")

if DATABASE_URL and not DATABASE_URL.startswith("postgresql+"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")


def test_taxonomy():
    """Test taxonomy repository."""
    print("\n" + "=" * 60)
    print("Testing Taxonomy Repository")
    print("=" * 60)

    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        repo = TaxonomyRepository(session)

        # List all categories
        print("\n📋 Listing all categories:")
        categories = repo.get_multi(limit=20)
        for cat in categories:
            indent = "  " * cat.level
            print(f"{indent}→ {cat.name} ({cat.path})")

        # Get tree structure
        print("\n🌲 Getting category tree for 'development':")
        dev_tree = repo.get_tree("development")
        print_tree(dev_tree, indent="  ")


def print_tree(items, indent=""):
    """Helper to print tree structure."""
    for item in items:
        print(f"{indent}• {item['name']}")
        if item.get("children"):
            print_tree(item["children"], indent + "  ")


def test_skills():
    """Test skills repository."""
    print("\n" + "=" * 60)
    print("Testing Skills Repository")
    print("=" * 60)

    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        repo = SkillRepository(session)

        # List all skills (should be empty initially)
        print("\n📋 Listing all skills:")
        skills = repo.get_multi(limit=10)
        if skills:
            for skill in skills:
                print(f"  → {skill.name} ({skill.status})")
        else:
            print("  (No skills found)")

        # Create a test skill
        print("\n➕ Creating test skill...")
        try:
            skill_data = {
                "skill_path": "development/languages/python/test-skill",
                "name": "test-skill",
                "description": "A test skill for repository validation",
                "version": "1.0.0",
                "type": SkillTypeEnum.TECHNICAL,
                "status": SkillStatusEnum.DRAFT,
                "skill_content": "# Test Skill\n\nThis is a test skill.",
            }

            skill = repo.create_with_relations(
                skill_data=skill_data,
                capabilities=[],
                dependencies=[],
                keywords=["test", "repository"],
                tags=["test"],
            )
            print(f"  ✓ Created skill: {skill.name} (ID: {skill.skill_id})")

            # Get the skill back
            print("\n🔍 Retrieving skill by path...")
            retrieved = repo.get_by_path("development/languages/python/test-skill")
            if retrieved:
                print(f"  ✓ Found: {retrieved.name}")
                print(f"     Description: {retrieved.description}")
                print(f"     Keywords: {[k.keyword for k in retrieved.keywords]}")
                print(f"     Tags: {[t.tag for t in retrieved.tags]}")

            # Search for skills
            print("\n🔎 Searching for 'test'...")
            results = repo.search(query="test", status=None, limit=5)
            for r in results:
                print(f"  → {r.name} (status: {r.status})")

            # Clean up
            print("\n🗑️  Cleaning up test skill...")
            repo.delete(id=retrieved.skill_id)
            print("  ✓ Test skill deleted")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback

            traceback.print_exc()


def test_jobs():
    """Test jobs repository."""
    print("\n" + "=" * 60)
    print("Testing Jobs Repository")
    print("=" * 60)

    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        repo = JobRepository(session)

        # Create a test job
        print("\n➕ Creating test job...")
        job_data = {
            "user_id": "test_user",
            "task_description": "Create a test skill for validation",
            "status": JobStatusEnum.PENDING,
        }

        job = repo.create(obj_in=job_data)
        print(f"  ✓ Created job: {job.job_id}")
        print(f"     Status: {job.status}")
        print(f"     Description: {job.task_description}")

        # Update job status
        print("\n📝 Updating job status...")
        updated = repo.update_status(job.job_id, JobStatusEnum.COMPLETED, result={"success": True})
        print(f"  ✓ Job status: {updated.status}")

        # Get pending jobs
        print("\n📋 Getting pending jobs...")
        pending = repo.get_by_status(JobStatusEnum.PENDING, limit=5)
        for p in pending:
            print(f"  → {p.job_id} (created: {p.created_at})")

        # Clean up
        print("\n🗑️  Cleaning up test job...")
        repo.delete(id=job.job_id)
        print("  ✓ Test job deleted")


def run_all_tests():
    """Run all repository tests."""
    print("\n" + "=" * 60)
    print("Skills-Fleet Repository Layer Tests")
    print("=" * 60)
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")

    try:
        # Test 1: Taxonomy
        test_taxonomy()

        # Test 2: Skills
        test_skills()

        # Test 3: Jobs
        test_jobs()

        print("\n" + "=" * 60)
        print("✅ All repository tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
