---
name: universal-memory
description: Local persistent memory system for LLM agents that works without cloud dependencies. Provides the 3-line pattern for adding memory to any LLM agent (OpenAI, Anthropic, Gemini, etc.) using local storage.
---

# Universal Memory System

## Overview
A universal, cloud-free memory system for LLM agents that provides persistent memory across sessions using local storage. Works with any LLM provider without requiring API keys for external memory services.

## When to Use
Use this skill when:
- Building LLM agents that need memory across sessions
- Working in environments without external cloud dependencies
- Implementing conversation history persistence with local storage
- Creating agents for offline or air-gapped environments
- Adding context-aware capabilities to existing agents
- Working with any LLM provider (OpenAI, Anthropic, Gemini, local models)

## Core Integration Pattern

### Basic 3-Line Integration
```python
from universal_memory import MemoryContext

# Wrap LLM SDK calls to enable memory
with MemoryContext(agent="my-agent"):
    response = openai.chat.completions.create(...)
```

### Async Integration
```python
from universal_memory import AsyncMemoryContext

# For async LLM SDK usage
async with AsyncMemoryContext(agent="my-agent"):
    response = await claude.messages.create(...)
```

## Provider-Specific Examples

### OpenAI Integration
```python
from openai import OpenAI
from universal_memory import MemoryContext

client = OpenAI()

def chat(message: str, model: str = "gpt-4"):
    with MemoryContext(agent="openai-demo"):
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": message}]
        )
        return response.choices[0].message.content

# Memory persists across calls
chat("My name is Alice.")
chat("What's my name?")  # Returns "Alice"
```

### Claude Integration
```python
from anthropic import Anthropic
from universal_memory import MemoryContext

client = Anthropic()

def chat(message: str, model: str = "claude-3-5-sonnet-20241022"):
    with MemoryContext(agent="claude-demo"):
        response = client.messages.create(
            model=model,
            max_tokens=1000,
            messages=[{"role": "user", "content": message}]
        )
        return response.content[0].text

# Memory works with Claude
chat("I prefer Python over JavaScript.")
chat("Which programming language do I prefer?")
```

### Gemini Integration
```python
import google.generativeai as genai
from universal_memory import MemoryContext

genai.configure(api_key="your-key")
model = genai.GenerativeModel('gemini-pro')

def chat(message: str):
    with MemoryContext(agent="gemini-demo"):
        response = model.generate_content(message)
        return response.text
```

### Local Models (Ollama, vLLM, etc.)
```python
import requests
from universal_memory import MemoryContext

def chat_local(message: str, model: str = "llama2"):
    with MemoryContext(agent="local-demo"):
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": message}
        )
        return response.json()["response"]
```

## Advanced Patterns

### Capture-Only Mode
```python
# Save conversations without injecting memory (logging only)
with MemoryContext(agent="research-agent", capture_only=True):
    # Conversation saved but no memory injected
    response = llm_call(...)
```

### Custom Memory Blocks
```python
# Define custom memory blocks for specific context
memory_blocks = [
    {"label": "project_context", "description": "Current project details"},
    {"label": "user_preferences", "description": "User's working preferences"}
]

with MemoryContext(agent="my-agent", memory=memory_blocks):
    response = llm_call(...)
```

### Multi-Agent Memory Sharing
```python
# Multiple agents can share memory by using the same agent name
with MemoryContext(agent="shared-agent"):
    response1 = agent1.chat("Research topic X")

with MemoryContext(agent="shared-agent"):
    response2 = agent2.chat("Summarize our research")
```

### Memory Retrieval
```python
from universal_memory import MemoryManager

# Retrieve conversation history
manager = MemoryManager(agent="my-agent")
conversations = manager.get_conversations(limit=10)

# Search conversations
results = manager.search("project requirements")
```

## Memory Storage Options

### SQLite (Default)
```python
# Default: SQLite in ~/.droid/memory/
with MemoryContext(agent="my-agent"):
    # Stores in SQLite database
    response = llm_call(...)
```

### JSON Storage
```python
from universal_memory import MemoryContext

# Use JSON file storage
with MemoryContext(agent="my-agent", storage_type="json"):
    response = llm_call(...)
    # Stores in ~/.droid/memory/my-agent.json
```

### Custom Storage Path
```python
from universal_memory import MemoryContext

# Specify custom storage location
with MemoryContext(agent="my-agent", storage_path="/custom/path/memory.db"):
    response = llm_call(...)
```

## Best Practices

### 1. Agent Naming
- Use descriptive agent names that reflect their purpose
- For related functionality, use consistent naming patterns
- Example: `email-processor`, `research-assistant`, `code-reviewer`

### 2. Memory Management
```python
from universal_memory import MemoryManager

manager = MemoryManager(agent="my-agent")

# Clear old conversations
manager.clear_conversations(older_than_days=30)

# Clear all memory
manager.clear_all()

# Export memory
manager.export_memory("backup.json")

# Import memory
manager.import_memory("backup.json")
```

### 3. Error Handling
```python
def robust_llm_call(message: str):
    try:
        with MemoryContext(agent="my-agent"):
            return llm_sdk_call(...)
    except Exception as e:
        # Fallback without memory
        return llm_sdk_call(...)
```

## Memory Architecture

### Storage Format
- **SQLite**: Single database with tables for conversations, messages, and metadata
- **JSON**: Hierarchical structure with conversations as top-level keys
- **Memory limit**: Configurable per agent (default: 10000 characters)

### Retrieval Strategy
- **Recent context**: Last N conversations within context window
- **Keyword search**: Simple keyword matching for relevant memories
- **Semantic search**: Optional with sentence-transformers (requires installation)

### Conversation Structure
```python
{
  "agent": "agent-name",
  "created_at": "2026-01-08T10:00:00Z",
  "messages": [
    {"role": "user", "content": "...", "timestamp": "..."},
    {"role": "assistant", "content": "...", "timestamp": "..."}
  ],
  "metadata": {
    "model": "gpt-4",
    "tokens_used": 1234
  }
}
```

## Installation

### Basic Setup
```bash
# Clone or copy the universal-memory skill to your project
# No additional installation required - uses Python standard library

# Optional: Install for semantic search
pip install sentence-transformers
```

### Configuration
```python
# Configure memory storage (optional)
import os
os.environ["FLEET_MEMORY_PATH"] = "/custom/memory/path"
os.environ["FLEET_MEMORY_LIMIT"] = "20000"  # characters
```

## Integration Examples

### Universal Research Agent
```python
from universal_memory import MemoryContext

class UniversalResearchAgent:
    def __init__(self, provider: str):
        self.provider = provider
        self.client = self._initialize_client(provider)

    def _initialize_client(self, provider: str):
        # Initialize different provider clients
        if provider == "openai":
            from openai import OpenAI
            return OpenAI()
        elif provider == "claude":
            from anthropic import Anthropic
            return Anthropic()
        elif provider == "ollama":
            import requests
            return requests

    def research(self, topic: str):
        with MemoryContext(agent="universal-researcher"):
            prompt = f"Research the topic: {topic}. Consider previous research context."
            return self._make_llm_call(prompt)
```

### Multi-Provider Code Review Assistant
```python
from universal_memory import MemoryContext

class CodeReviewAssistant:
    def __init__(self, providers: list):
        self.providers = providers

    def review_with_multiple_perspectives(self, code: str):
        reviews = {}
        
        for provider_name, client in self.providers.items():
            with MemoryContext(agent=f"code-reviewer-{provider_name}"):
                prompt = f"Review this code from {provider_name} perspective: {code}"
                reviews[provider_name] = self._make_llm_call(client, prompt)
        
        return self._synthesize_reviews(reviews)
```

## Memory Persistence

### Automatic Persistence
```python
# All conversations are automatically saved
with MemoryContext(agent="my-agent"):
    response = llm_call(...)
    # Conversation automatically saved to storage
```

### Manual Persistence
```python
from universal_memory import MemoryManager

manager = MemoryManager(agent="my-agent")

# Manually save conversation
manager.save_conversation([
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
])
```

## Testing

### Unit Test Pattern
```python
import pytest
from universal_memory import MemoryContext

def test_memory_integration():
    with MemoryContext(agent="test-agent"):
        # Test that memory is working
        response = mock_llm_call("Remember this test")
        
        # Verify memory was captured
        manager = MemoryManager(agent="test-agent")
        conversations = manager.get_conversations()
        assert len(conversations) > 0

@pytest.mark.parametrize("provider", ["openai", "claude", "ollama"])
def test_provider_memory_integration(provider):
    # Test memory works with each provider
    agent = create_agent(provider)
    response = agent.chat("Test message")
    assert response is not None
```

## Troubleshooting

### Common Issues
1. **Memory not appearing**: Ensure agent name is consistent across calls
2. **Storage errors**: Check write permissions for memory directory
3. **Performance issues**: Use `capture_only=True` for logging-only scenarios
4. **Context overflow**: Regularly clear memory for long-running sessions
5. **Storage location**: Default is `~/.droid/memory/`

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging to see memory operations
with MemoryContext(agent="debug-agent"):
    # Memory operations will be logged
    response = llm_call(...)
```

## Security Considerations

### Local Storage
- All data stored locally (no cloud transmission)
- SQLite databases can be encrypted with standard tools
- JSON files can be encrypted if needed

### Memory Sanitization
```python
# Sanitize sensitive data before storage
import re

def sanitize_message(message: str) -> str:
    # Remove common sensitive patterns
    message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED]', message)
    message = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED]', message)
    return message
```

## Performance Optimization

### Memory Limits
```python
# Set per-agent memory limits
with MemoryContext(agent="my-agent", memory_limit=5000):
    response = llm_call(...)
```

### Conversation Cleanup
```python
from universal_memory import MemoryManager

manager = MemoryManager(agent="my-agent")

# Keep only recent conversations
manager.cleanup(keep_last_n=50)

# Compress old conversations
manager.compress_old_conversations()
```

## References

- `scripts/memory_manager.py` - Core memory management implementation
- `scripts/universal_memory.py` - 3-line pattern API
- `examples/` - Provider-specific integration examples
- `references/` - Detailed documentation

## License

MIT - Use freely in any project
