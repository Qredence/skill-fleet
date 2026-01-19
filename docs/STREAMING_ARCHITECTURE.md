# Streaming Architecture: Real-Time Thinking & Response Output

This document explains the streaming architecture for Skills Fleet, enabling real-time display of:
- **Thinking/Reasoning Content** - Shows the AI's step-by-step reasoning
- **Intermediate Steps** - Displays progress as computations happen
- **Response Chunks** - Streams response text as it's generated
- **Signatures & Thought Process** - Full visibility into LM behavior

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Ink TUI (TypeScript/React)                  │
│                                                                 │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Chat Tab      │  │ Skills Tab   │  │ Jobs Monitor    │   │
│  │                │  │              │  │                 │   │
│  │ • Input field  │  │ • Skill list │  │ • Progress bar  │   │
│  │ • Messages     │  │ • Search     │  │ • Job status    │   │
│  │ • Thinking     │  │ • Validate   │  │ • Results       │   │
│  │ • Suggestions  │  │ • Promote    │  │                 │   │
│  └────────────────┘  └──────────────┘  └─────────────────┘   │
│         │                                                       │
│         │ fetch() POST /api/v1/chat/stream                     │
└─────────┼───────────────────────────────────────────────────────┘
          │
          │ HTTP/1.1 Server-Sent Events (SSE)
          │
┌─────────▼───────────────────────────────────────────────────────┐
│              FastAPI Backend (Python/DSPy)                      │
│                                                                 │
│  POST /api/v1/chat/stream                                      │
│  │                                                              │
│  ├─► StreamingAssistant (DSPy Module)                         │
│  │   │                                                         │
│  │   ├─ StreamingIntentParser                                │
│  │   │  └─ Yields thinking steps as LM analyzes intent       │
│  │   │                                                         │
│  │   └─ DSPy ChainOfThought                                  │
│  │      └─ Yields thinking + response chunks                 │
│  │                                                             │
│  └─► Streams ServerSentEvents (SSE)                          │
│      │                                                         │
│      ├─ event: thinking                                       │
│      │  data: {"type": "thought", "content": "...", ...}    │
│      │                                                         │
│      ├─ event: response                                       │
│      │  data: {"type": "response", "content": "..."}         │
│      │                                                         │
│      └─ event: complete                                       │
│         data:                                                 │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Python Backend: Streaming DSPy Module

**File**: `src/skill_fleet/core/dspy/streaming.py`

```python
class StreamingModule(dspy.Module):
    """Base class for streaming modules."""
    
    def yield_thinking(self, content: str, thinking_type: str) -> ThinkingChunk:
        """Yield a thinking chunk (thought, reasoning, internal step, etc.)"""
        return ThinkingChunk(type=thinking_type, content=content, step=...)

class StreamingIntentParser(StreamingModule):
    """Parse user intent with streaming reasoning."""
    
    async def forward_streaming(self, user_message: str):
        """Yield thinking steps, then final intent classification."""
        yield thinking_chunk_1  # "Analyzing user message..."
        yield thinking_chunk_2  # "Looking for keywords..."
        yield thinking_chunk_3  # "Running LM classification..."
        yield response_chunk    # Final classification result

class StreamingAssistant(StreamingModule):
    """Main assistant that streams full conversation."""
    
    async def forward_streaming(self, user_message: str, context: dict):
        """Full thinking + response streaming."""
        # Step 1: Parse intent (with thinking)
        async for event in self.intent_parser.forward_streaming(user_message):
            yield event
        
        # Step 2: Generate response (with thinking)
        yield thinking_chunk_4  # "Generating response..."
        # Stream response in chunks...
        for chunk in response_chunks:
            yield ResponseChunk(content=chunk)
        
        yield complete_event
```

### 2. FastAPI Streaming Endpoint

**File**: `src/skill_fleet/api/routes/chat_streaming.py`

```python
@router.post("/chat/stream")
async def chat_stream(request: ChatMessageRequest):
    """
    Stream real-time chat response with thinking process.
    
    Returns Server-Sent Events with:
    - thinking: Intermediate reasoning steps
    - response: Generated response chunks
    - error: Any errors
    - complete: Stream finished
    """
    assistant = StreamingAssistant()
    
    async def event_generator():
        async for event in assistant.forward_streaming(
            user_message=request.message,
            context=request.context
        ):
            yield event
    
    return stream_events_to_sse(event_generator())
```

### 3. TypeScript Streaming Client

**File**: `cli/tui/src/streaming-client.ts`

```typescript
class StreamingClient {
    async streamChat(options: StreamingOptions) {
        // Connect to SSE endpoint
        const response = await fetch('/api/v1/chat/stream', {
            method: 'POST',
            body: JSON.stringify({ message, context })
        });
        
        // Parse SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            // Parse SSE format: "event: type\ndata: {...}\n\n"
            const line = decoder.decode(value);
            
            if (line.startsWith('event: thinking')) {
                options.onThinking(JSON.parse(data));
            } else if (line.startsWith('event: response')) {
                options.onResponse(JSON.parse(data));
            } else if (line.startsWith('event: complete')) {
                options.onComplete();
            }
        }
    }
}
```

### 4. Ink TUI Chat Component

**File**: `cli/tui/src/tabs/chat-tab.tsx`

```typescript
export const ChatTab: React.FC<ChatTabProps> = ({ apiUrl, isActive }) => {
    const [messages, setMessages] = useState<Message[]>([]);
    const streamingClient = new StreamingClient();

    const handleSubmit = async (message: string) => {
        // Add user message
        setMessages(prev => [...prev, { role: 'user', content: message }]);

        // Stream assistant response
        await streamingClient.streamChat({
            apiUrl,
            message,
            onThinking: (chunk) => {
                // Display thinking chunk (colored)
                setMessages(prev => [...prev, {
                    role: 'thinking',
                    content: formatThinking(chunk),
                    thinking_type: chunk.type
                }]);
            },
            onResponse: (chunk) => {
                // Accumulate and update response
                setMessages(prev => {
                    const last = prev[prev.length - 1];
                    if (last?.role === 'assistant') {
                        last.content += chunk.content;
                    }
                    return prev;
                });
            },
            onComplete: () => {
                // Generate suggestions
                generateSuggestions(message);
            }
        });
    };

    return (
        <Box flexDirection="column">
            {/* Display messages with thinking/response separation */}
            {messages.map(msg => (
                <Text color={msg.role === 'thinking' ? 'gray' : 'green'}>
                    {msg.role === 'thinking' ? `💭 ${msg.content}` : msg.content}
                </Text>
            ))}
            
            {/* Input field */}
            <TextInput value={input} onChange={setInput} onSubmit={handleSubmit} />
        </Box>
    );
};
```

## Event Types & Formats

### Thinking Event

```json
{
  "type": "thinking",
  "data": {
    "type": "thought|reasoning|internal|step",
    "content": "What the AI is thinking about",
    "step": 1
  }
}
```

**Types**:
- `thought` (💭): Initial observation or idea
- `reasoning` (🤔): Logical deduction or analysis
- `internal` (⚙️): System/implementation detail
- `step` (▶️): Step in a multi-step process

### Response Event

```json
{
  "type": "response",
  "data": {
    "type": "response|complete",
    "content": "Chunk of text being generated"
  }
}
```

### Complete Event

```
event: complete
data:

```

Empty data signals end of stream.

### Error Event

```json
{
  "type": "error",
  "data": "Error message string"
}
```

## Usage Examples

### JavaScript/TypeScript

```typescript
const client = new StreamingClient();

await client.streamChat({
    apiUrl: "http://localhost:8000",
    message: "Create a skill for JSON parsing",
    
    onThinking: (chunk) => {
        console.log(`[${chunk.type}] ${chunk.content}`);
    },
    
    onResponse: (chunk) => {
        process.stdout.write(chunk.content);
    },
    
    onError: (error) => {
        console.error("Error:", error);
    },
    
    onComplete: () => {
        console.log("\n\nDone!");
    }
});
```

### Python (for testing)

```python
import httpx
import asyncio
import json

async def stream_chat():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/api/v1/chat/stream",
            json={"message": "optimize my skill"},
            headers={"Accept": "text/event-stream"}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    event_type = line.split(":", 1)[1].strip()
                elif line.startswith("data:"):
                    data_str = line.split(":", 1)[1].strip()
                    if data_str:
                        data = json.loads(data_str)
                        print(f"[{event_type}] {data}")

asyncio.run(stream_chat())
```

## Benefits

1. **Real-time Visibility**: See the AI's thinking process as it happens
2. **Better UX**: Responsive interface with streaming chunks instead of waiting
3. **Transparency**: Understand how intent is parsed and responses are generated
4. **Debugging**: Trace through signature + reasoning for troubleshooting
5. **Educational**: Learn how LMs work by observing thinking steps
6. **Agentic**: Show suggestions based on intermediate thinking

## Performance Considerations

- **Small chunks**: Stream events are small (50-200 bytes typically)
- **Low latency**: SSE events are sent as soon as generated
- **Network efficient**: HTTP/1.1 with keep-alive
- **Memory efficient**: No buffering of full responses

## Fallback: Synchronous Mode

If streaming is unavailable:

```python
@router.post("/chat/sync")
async def chat_sync(request: ChatMessageRequest):
    """Non-streaming response (collects all events first)."""
    assistant = StreamingAssistant()
    
    thinking_steps = []
    responses = []
    
    async for event in assistant.forward_streaming(...):
        if event["type"] == "thinking":
            thinking_steps.append(...)
        elif event["type"] == "response":
            responses.append(...)
    
    return {
        "thinking": thinking_steps,
        "response": "".join(responses),
        "thinking_summary": assistant.get_thinking_summary()
    }
```

## Testing Streaming

```bash
# 1. Start the API server
uv run skill-fleet serve

# 2. In another terminal, test streaming with curl
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "create a skill for JSON validation"}'

# 3. Or test with the Ink TUI
cd cli/tui && npm install && npm run build
SKILL_FLEET_API_URL=http://localhost:8000 npm start
```

## Future Enhancements

- [ ] Support for structured outputs (JSON schema)
- [ ] Partial error recovery (continue on validation error)
- [ ] Thinking caching (avoid re-parsing for similar inputs)
- [ ] Custom thinking prompts per module
- [ ] Visualization of DSPy module flow
