#!/usr/bin/env python3
"""
Integration test: Demonstrate HITL clarifying questions appearing.
This script will start the server, create a job, and show the clarifying questions.
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

import httpx

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def wait_for_server(timeout=30):
    """Wait for server to be ready."""
    print("⏳ Waiting for server to start...")
    for i in range(timeout):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://127.0.0.1:8000/health", timeout=2.0)
                if response.status_code == 200:
                    print("✅ Server is ready!")
                    return True
        except:
            pass
        await asyncio.sleep(1)
        if i % 5 == 0:
            print(f"   Still waiting... ({i}/{timeout}s)")
    return False


async def create_skill_job(client, task_description):
    """Create a skill job and return job_id."""
    print(f"\n📝 Creating job: '{task_description}'")

    response = await client.post(
        "http://127.0.0.1:8000/api/v1/skills/",
        json={"task_description": task_description, "user_id": "test_user"},
        timeout=120.0,
    )
    response.raise_for_status()
    data = response.json()

    job_id = data.get("job_id")
    status = data.get("status")

    print(f"   ✅ Job created: {job_id}")
    print(f"   📊 Status: {status}")

    if data.get("hitl_context"):
        print(f"   💡 HITL Context present: {bool(data.get('hitl_context'))}")

    return job_id, status


async def poll_for_hitl_prompt(client, job_id, max_attempts=60):
    """Poll for HITL prompt with clarifying questions."""
    print(f"\n🔍 Polling for clarifying questions (Job: {job_id[:8]}...)...")

    for attempt in range(max_attempts):
        try:
            response = await client.get(
                f"http://127.0.0.1:8000/api/v1/hitl/{job_id}/prompt", timeout=10.0
            )
            response.raise_for_status()
            prompt_data = response.json()

            status = prompt_data.get("status")
            hitl_type = prompt_data.get("type")
            questions = prompt_data.get("questions")

            if attempt % 5 == 0:
                print(f"   Attempt {attempt + 1}/{max_attempts}: status={status}, type={hitl_type}")

            # Check if we have reached HITL state with questions
            if status in ["pending_hitl", "pending_user_input"]:
                print(f"\n{'=' * 70}")
                print(f"🎉 SUCCESS! Job reached HITL state!")
                print(f"{'=' * 70}")
                print(f"Status: {status}")
                print(f"Type: {hitl_type}")

                if questions:
                    print(f"\n❓ CLARIFYING QUESTIONS ({len(questions)} found):\n")
                    for i, q in enumerate(questions, 1):
                        print(f"{'─' * 70}")
                        print(f"Question {i}:")
                        text = q.get("text", str(q))
                        print(f"  {text}")

                        if q.get("options"):
                            print(f"\n  Options:")
                            for opt in q["options"]:
                                label = opt.get("label", opt.get("text", str(opt)))
                                print(f"    • {label}")

                        if q.get("rationale"):
                            print(f"\n  Rationale: {q['rationale']}")

                    print(f"{'─' * 70}")
                    return True
                else:
                    print(f"\n⚠️  No questions found in hitl_data!")
                    print(f"Full prompt data:\n{json.dumps(prompt_data, indent=2)}")
                    return False

            if status in ["completed", "failed", "cancelled"]:
                print(f"\n⚠️  Job finished without HITL (status: {status})")
                return False

            await asyncio.sleep(2)

        except Exception as e:
            if attempt % 5 == 0:
                print(f"   Attempt {attempt + 1}: Error - {e}")
            await asyncio.sleep(2)

    print(f"\n❌ Timeout after {max_attempts} attempts")
    return False


async def main():
    """Main test flow."""
    print("=" * 70)
    print("🧪 HITL Clarifying Questions Integration Test")
    print("=" * 70)

    # Start server in background
    print("\n🚀 Starting server...")
    server_process = subprocess.Popen(
        ["uv", "run", "skill-fleet", "serve"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="/Volumes/Samsung-SSD-T7/Workspaces/Github/qredence/agent-framework/v0.5/_WORLD/skills-fleet",
    )

    try:
        # Wait for server
        if not await wait_for_server(timeout=30):
            print("❌ Server failed to start")
            return 1

        # Run test
        async with httpx.AsyncClient() as client:
            # Create job
            job_id, status = await create_skill_job(client, "a skill for design system")

            if not job_id:
                print("❌ Failed to create job")
                return 1

            # Poll for questions
            success = await poll_for_hitl_prompt(client, job_id)

            if success:
                print(f"\n{'=' * 70}")
                print("✅ TEST PASSED: Clarifying questions are working!")
                print("=" * 70)
                return 0
            else:
                print(f"\n{'=' * 70}")
                print("❌ TEST FAILED: Clarifying questions not appearing")
                print("=" * 70)
                return 1

    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except:
            server_process.kill()


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)
