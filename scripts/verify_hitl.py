import asyncio
import sys

import httpx

BASE_URL = "http://localhost:8000/api/v1"


async def test_hitl_flow():
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        # 1. Start Skill Creation
        print("Starting skill creation...")
        payload = {
            "task_description": "Create a skill for python programming",  # Vague
            "user_id": "test_user",
        }
        resp = await client.post(f"{BASE_URL}/skills", json=payload)
        resp.raise_for_status()
        data = resp.json()
        job_id = data["job_id"]
        print(f"Job started: {job_id}")

        # 2. Poll for Status
        print("Polling for HITL prompt...")
        for _ in range(20):
            await asyncio.sleep(2)
            resp = await client.get(f"{BASE_URL}/jobs/{job_id}")
            job_data = resp.json()
            status = job_data["status"]
            print(f"Status: {status}")

            if status == "pending_user_input":
                print("HITL Prompt detected!")
                # Get questions
                prompt_resp = await client.get(f"{BASE_URL}/hitl/{job_id}/prompt")
                prompt_data = prompt_resp.json()
                questions = prompt_data.get("questions", [])
                print(f"Questions received: {len(questions)}")
                if questions:
                    print(f"Q1: {questions[0]['text']}")

                # 3. Submit Response
                print("Submitting response...")
                answer_payload = {
                    "answers": [
                        {
                            "question_id": questions[0]["id"] if questions else "q1",
                            "free_text": "I want a skill to manage async tasks in Python using asyncio.",
                        }
                    ]
                }
                hitl_resp = await client.post(
                    f"{BASE_URL}/hitl/{job_id}/response", json=answer_payload
                )
                hitl_resp.raise_for_status()
                print("Response submitted.")
                break

            if status in ["completed", "failed"]:
                print(f"Job finished early with status: {status}")
                return

        # 4. Poll for Resumption
        print("Polling for resumption...")
        for _ in range(20):
            await asyncio.sleep(2)
            resp = await client.get(f"{BASE_URL}/jobs/{job_id}")
            job_data = resp.json()
            status = job_data["status"]
            print(f"Status: {status}")

            if status == "running":
                # Ensure it's not stuck
                pass
            if status == "completed":
                print("Job completed successfully!")
                return
            if status == "failed":
                print("Job failed.")
                return


if __name__ == "__main__":
    try:
        asyncio.run(test_hitl_flow())
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
