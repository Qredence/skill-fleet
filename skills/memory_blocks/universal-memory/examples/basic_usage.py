#!/usr/bin/env python3
"""
Basic usage examples for Universal Memory System

Demonstrates the 3-line pattern with different LLM providers.
"""

import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from universal_memory import MemoryContext, learning, learning_async, inject_context, track_conversation


# Mock LLM client for demonstration
class MockLLMClient:
    """Mock LLM client for testing without API keys."""
    
    def __init__(self, name: str):
        self.name = name
        self.call_count = 0
    
    def generate(self, prompt: str) -> str:
        """Mock response generation."""
        self.call_count += 1
        return f"[{self.name}] Response to: {prompt[:50]}..."
    
    def chat(self, messages: list) -> dict:
        """Mock chat completion."""
        self.call_count += 1
        last_msg = messages[-1]['content'] if messages else ""
        return {
            "choices": [{
                "message": {
                    "content": f"[{self.name}] Response to: {last_msg[:50]}..."
                }
            }]
        }


def example_basic_usage():
    """Basic 3-line pattern usage."""
    print("=" * 60)
    print("Example 1: Basic 3-Line Pattern")
    print("=" * 60)
    
    client = MockLLMClient("OpenAI")
    
    with MemoryContext(agent="basic-demo"):
        # First interaction
        response1 = client.chat([{"role": "user", "content": "My name is Alice"}])
        print(f"Response 1: {response1['choices'][0]['message']['content']}")
        
        # Second interaction - memory is automatically injected
        response2 = client.chat([{"role": "user", "content": "What's my name?"}])
        print(f"Response 2: {response2['choices'][0]['message']['content']}")
    
    print()


def example_convenience_function():
    """Using the convenience function."""
    print("=" * 60)
    print("Example 2: Using learning() convenience function")
    print("=" * 60)
    
    client = MockLLMClient("Claude")
    
    with learning(agent="convenience-demo"):
        response = client.generate("Hello, I'm working on a project about AI.")
        print(f"Response: {response}")
    
    print()


def example_async_usage():
    """Async context manager."""
    print("=" * 60)
    print("Example 3: Async Memory Context")
    print("=" * 60)
    
    import asyncio
    
    async def async_chat():
        client = MockLLMClient("Gemini")
        
        async with learning_async(agent="async-demo"):
            response = client.generate("Async message here")
            print(f"Response: {response}")
    
    asyncio.run(async_chat())
    print()


def example_inject_context():
    """Using the inject_context decorator."""
    print("=" * 60)
    print("Example 4: Auto-inject Context with Decorator")
    print("=" * 60)
    
    client = MockLLMClient("OpenAI")
    
    @inject_context
    def chat_with_memory(message: str, agent: str = "demo"):
        return client.chat([{"role": "user", "content": message}])
    
    # First message
    response1 = chat_with_memory("I prefer Python over JavaScript", agent="decorator-demo")
    print(f"Response 1: {response1['choices'][0]['message']['content']}")
    
    # Second message - context automatically injected
    response2 = chat_with_memory("Which language do I prefer?", agent="decorator-demo")
    print(f"Response 2: {response2['choices'][0]['message']['content']}")
    
    print()


def example_capture_only():
    """Capture-only mode for logging."""
    print("=" * 60)
    print("Example 5: Capture-Only Mode (Logging)")
    print("=" * 60)
    
    client = MockLLMClient("Logger")
    
    with MemoryContext(agent="logging-demo", capture_only=True):
        # Conversations saved but no context injected
        response = client.generate("Log this message")
        print(f"Response: {response}")
        print("(Conversation logged, context not injected)")
    
    print()


def example_json_storage():
    """Using JSON storage instead of SQLite."""
    print("=" * 60)
    print("Example 6: JSON Storage")
    print("=" * 60)
    
    client = MockLLMClient("JSON-Client")
    
    with MemoryContext(agent="json-demo", storage_type="json"):
        response = client.generate("Store in JSON format")
        print(f"Response: {response}")
        print("(Stored in ~/.droid/memory/json-demo.json)")
    
    print()


def example_memory_retrieval():
    """Retrieving and searching memory."""
    print("=" * 60)
    print("Example 7: Memory Retrieval")
    print("=" * 60)
    
    from universal_memory import MemoryManager
    
    # Add some conversations
    with MemoryContext(agent="retrieval-demo"):
        client = MockLLMClient("Retrieval-Client")
        client.generate("Python is my favorite programming language")
        client.generate("I work on machine learning projects")
    
    # Retrieve conversations
    manager = MemoryManager(agent="retrieval-demo")
    conversations = manager.get_conversations(limit=10)
    
    print(f"Retrieved {len(conversations)} conversations:")
    for conv in conversations:
        print(f"  - {conv['created_at']}: {conv['messages'][0]['content'][:40]}...")
    
    # Search conversations
    results = manager.search("Python")
    print(f"\nSearch for 'Python': {len(results)} results")
    
    print()


def example_multi_agent():
    """Multiple agents with separate memories."""
    print("=" * 60)
    print("Example 8: Multi-Agent Memory")
    print("=" * 60)
    
    client = MockLLMClient("Multi-Agent")
    
    # Agent 1 - Research Assistant
    with MemoryContext(agent="research-assistant"):
        response = client.generate("Research topic: climate change")
        print(f"Research Agent: {response}")
    
    # Agent 2 - Code Assistant (separate memory)
    with MemoryContext(agent="code-assistant"):
        response = client.generate("Review this Python code")
        print(f"Code Agent: {response}")
    
    print("(Each agent has separate memory)")
    print()


def example_memory_export():
    """Export and import memory."""
    print("=" * 60)
    print("Example 9: Memory Export/Import")
    print("=" * 60)
    
    from universal_memory import MemoryManager
    import tempfile
    
    # Add some conversations
    with MemoryContext(agent="export-demo"):
        client = MockLLMClient("Export-Client")
        client.generate("Important conversation 1")
        client.generate("Important conversation 2")
    
    # Export memory
    manager = MemoryManager(agent="export-demo")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        export_path = f.name
    
    manager.export_memory(export_path)
    print(f"Memory exported to: {export_path}")
    
    # Clear memory
    manager.clear_conversations()
    print("Memory cleared")
    
    # Import memory
    manager.import_memory(export_path)
    print("Memory imported")
    
    conversations = manager.get_conversations()
    print(f"Restored {len(conversations)} conversations")
    
    # Clean up
    os.unlink(export_path)
    
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Universal Memory System - Basic Usage Examples")
    print("=" * 60 + "\n")
    
    example_basic_usage()
    example_convenience_function()
    example_async_usage()
    example_inject_context()
    example_capture_only()
    example_json_storage()
    example_memory_retrieval()
    example_multi_agent()
    example_memory_export()
    
    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
    print(f"\nMemory files stored in: ~/.droid/memory/")
    print("To clean up: delete ~/.droid/memory/ directory")


if __name__ == "__main__":
    main()
