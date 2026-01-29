#!/usr/bin/env python3
"""Check job status and HITL data directly."""

import asyncio
import sys

sys.path.insert(
    0,
    "/Volumes/Samsung-SSD-T7/Workspaces/Github/qredence/agent-framework/v0.5/_WORLD/skills-fleet/src",
)

from skill_fleet.api.services.job_manager import get_job_manager


async def check_job(job_id):
    manager = get_job_manager()
    job = manager.get_job(job_id)

    if not job:
        print(f"❌ Job {job_id} not found")
        return

    print(f"✅ Job found: {job_id}")
    print(f"   Status: {job.status}")
    print(f"   HITL Type: {job.hitl_type}")
    print(f"   HITL Data: {job.hitl_data}")
    print(f"   Questions: {job.hitl_data.get('questions') if job.hitl_data else None}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_job.py <job_id>")
        sys.exit(1)

    job_id = sys.argv[1]
    asyncio.run(check_job(job_id))
