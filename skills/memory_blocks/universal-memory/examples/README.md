# Universal Memory Examples

This directory contains practical examples demonstrating the Universal Memory System.

## Running Examples

### Basic Examples
```bash
python examples/basic_usage.py
```

This runs all basic examples showing:
- 3-line pattern usage
- Convenience functions
- Async context management
- Auto-injection decorators
- Capture-only mode
- JSON storage
- Memory retrieval
- Multi-agent scenarios
- Export/import functionality

## Provider-Specific Examples

### OpenAI
```python
from openai import OpenAI
from universal_memory import learning

client = OpenAI()

with learning(agent="openai-demo"):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(response.choices[0].message.content)
```

### Claude (Anthropic)
```python
from anthropic import Anthropic
from universal_memory import learning

client = Anthropic()

with learning(agent="claude-demo"):
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print(message.content[0].text)
```

### Gemini
```python
import google.generativeai as genai
from universal_memory import learning

genai.configure(api_key="your-api-key")
model = genai.GenerativeModel('gemini-pro')

with learning(agent="gemini-demo"):
    response = model.generate_content("Hello!")
    print(response.text)
```

### Local Models (Ollama)
```python
import requests
from universal_memory import learning

with learning(agent="ollama-demo"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama2",
            "prompt": "Hello!"
        }
    )
    print(response.json()["response"])
```

## Advanced Patterns

### Auto-Inject Decorator
```python
from universal_memory import inject_context

@inject_context
def chat(message: str, agent: str = "my-agent"):
    return openai_client.chat.completions.create(
        messages=[{"role": "user", "content": message}]
    )

# Context automatically injected
response = chat("Hello!", agent="my-agent")
```

### Memory Search
```python
from universal_memory import MemoryManager

manager = MemoryManager(agent="my-agent")

# Search conversations
results = manager.search("project requirements")

# Get recent context
context = manager.get_context(limit=5)

# Export memory
manager.export_memory("backup.json")
```

### Custom Memory Blocks
```python
from universal_memory import MemoryContext

memory_blocks = [
    {"label": "project_context", "description": "Current project details"},
    {"label": "user_preferences", "description": "User's working preferences"}
]

with MemoryContext(agent="my-agent", memory=memory_blocks):
    response = llm_call(...)
```

## Memory Management

### Clear Old Conversations
```python
from universal_memory import MemoryManager

manager = MemoryManager(agent="my-agent")

# Clear conversations older than 30 days
manager.clear_conversations(older_than_days=30)

# Clear all conversations
manager.clear_conversations()
```

### Backup and Restore
```python
# Backup
manager.export_memory("backup.json")

# Restore to different agent
new_manager = MemoryManager(agent="restored-agent")
new_manager.import_memory("backup.json")
```

## Testing Examples

### Unit Test Pattern
```python
import pytest
from universal_memory import MemoryContext

def test_memory_persistence():
    with MemoryContext(agent="test-agent"):
        # Make LLM call
        response = mock_llm_call("Test message")
    
    # Verify memory was saved
    manager = MemoryManager(agent="test-agent")
    conversations = manager.get_conversations()
    assert len(conversations) > 0
```

## Error Handling

### Fallback Without Memory
```python
def robust_llm_call(message: str):
    try:
        with MemoryContext(agent="my-agent"):
            return llm_sdk_call(message)
    except Exception as e:
        # Fallback without memory if storage fails
        print(f"Memory error: {e}, using fallback")
        return llm_sdk_call(message)
```

## Memory Storage Locations

### Default Locations
- **SQLite**: `~/.droid/memory/<agent-name>.db`
- **JSON**: `~/.droid/memory/<agent-name>.json`

### Custom Storage Path
```python
import os
os.environ["DROID_MEMORY_PATH"] = "/custom/memory/path"

with MemoryContext(agent="my-agent"):
    # Uses custom path
    response = llm_call(...)
```

## Configuration

### Environment Variables
```bash
# Set custom memory path
export DROID_MEMORY_PATH="/custom/path"

# Set default memory limit (characters)
export DROID_MEMORY_LIMIT="20000"
```

### Code Configuration
```python
from universal_memory import MemoryContext

with MemoryContext(
    agent="my-agent",
    storage_type="json",  # or "sqlite"
    storage_path="/custom/path",
    memory_limit=5000
):
    response = llm_call(...)
```

## Performance Tips

1. **Use capture_only for logging**: When you only want to log conversations
2. **Set memory limits**: Prevent excessive storage with `memory_limit`
3. **Regular cleanup**: Clear old conversations periodically
4. **Choose storage wisely**: SQLite for many conversations, JSON for few

## Troubleshooting

### Memory Not Persisting
- Check write permissions for `~/.droid/memory/`
- Verify agent name is consistent across calls
- Check for errors in logs

### Context Not Injecting
- Ensure you're not using `capture_only=True`
- Check that conversations exist in memory
- Verify agent name matches between calls

### Performance Issues
- Use `memory_limit` to cap storage
- Clear old conversations regularly
- Consider JSON storage for fewer conversations

## Further Reading

- Main documentation: `../SKILL.md`
- Memory manager implementation: `../scripts/memory_manager.py`
- Universal memory API: `../scripts/universal_memory.py`
