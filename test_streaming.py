#!/usr/bin/env python3
"""Quick test script to debug streaming endpoint 500 error."""

import asyncio
import json
import os

import dspy
from src.skill_fleet.core.dspy.streaming import StreamingAssistant
from src.skill_fleet.llm.dspy_config import configure_dspy


async def test_streaming():
    """Test StreamingAssistant directly."""

    # Check API key
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not set!")
        print("   Export it: export GOOGLE_API_KEY='your-key'")
        return

    print("✅ GOOGLE_API_KEY found")
    print()

    # Configure DSPy
    try:
        configure_dspy()
        print("✅ DSPy configured successfully")
        print(f"   LM: {dspy.settings.lm}")
        print()
    except Exception as e:
        print(f"❌ DSPy configuration failed: {e}")
        return

    # Test StreamingAssistant
    try:
        assistant = StreamingAssistant()
        print("✅ StreamingAssistant initialized")
        print()

        print("Testing with message: 'hello'")
        print("─" * 50)

        async for event in assistant.forward_streaming(user_message="hello"):
            event_type = event.get("type", "unknown")
            data = event.get("data", "")

            if event_type == "thinking":
                parsed = json.loads(data) if isinstance(data, str) else data
                print(f"💭 Thinking: {parsed.get('content', '')}")
            elif event_type == "response":
                parsed = json.loads(data) if isinstance(data, str) else data
                print(f"💬 Response: {parsed.get('content', '')}")
            elif event_type == "complete":
                print("✅ Complete")
            elif event_type == "error":
                print(f"❌ Error: {data}")

        print("─" * 50)
        print("\n✅ Streaming test successful!")

    except Exception as e:
        print(f"❌ StreamingAssistant failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_streaming())
