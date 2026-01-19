# Streaming TUI Quick Start Guide

Get real-time streaming responses with thinking/reasoning display in 5 minutes.

## ✅ Prerequisites

- Python 3.12+
- Node.js 18+ (for TUI)
- Skills Fleet API running (`uv run skill-fleet serve`)

## 🚀 Quick Start

### Step 1: Install TUI Dependencies

```bash
cd cli/tui
npm install
npm run build
```

### Step 2: Start the API Server

```bash
# In one terminal
uv run skill-fleet serve
```

### Step 3: Launch the Streaming Chat TUI

```bash
# In another terminal
uv run skill-fleet chat
```

**What you'll see:**
```
┌─────────────────────────────────────────┐
│ 🚀 Skills Fleet TUI                     │
├─────────────────────────────────────────┤
│                                         │
│ Assistant: Welcome to Skills Fleet!    │
│ You can type requests and see my       │
│ thinking process in real-time.         │
│                                         │
│ You: create a JSON parsing skill      │
│                                         │
│ 💭 [thought] Analyzing user message... │
│ 🤔 [reasoning] Looking for keywords... │
│ ⚙️  [internal] Running classification  │
│                                         │
│ > _                                     │
│                                         │
└─────────────────────────────────────────┘
```

## 📝 Examples to Try

### 1. Create a Skill

```
You: create a skill for JSON parsing
```

**Expected Output:**
- Shows thinking process: "Analyzing user message..." → "Looking for keywords..." → "Running classification..."
- Streams response chunks as they're generated
- Shows suggested next steps

### 2. Run Optimization

```
You: /optimize reflection_metrics trainset_v4.json
```

**Expected Output:**
- Thinking: "Setting up Reflection Metrics optimizer..."
- Response: "Starting optimization job... ID: xyz-123"
- Suggested next: "/status xyz-123"

### 3. List Skills

```
You: /list --filter python
```

**Expected Output:**
- Thinking: "Querying skill taxonomy..."
- Response: Tabulated list of Python skills with metadata

## 🎯 Key Features

### Real-Time Thinking Display

Each thinking chunk is labeled with an emoji and type:
- 💭 **thought** - Initial observation
- 🤔 **reasoning** - Logical deduction
- ⚙️ **internal** - Implementation detail
- ▶️ **step** - Multi-step process

### Agentic Suggestions

Based on your message, the assistant suggests next steps:

```
💡 Suggested next steps:
• /list --filter python
• /validate skills/python/async
• /promote <job_id>
```

### Tab Navigation

```
Commands:
- Tab / Ctrl+Tab : Switch tabs
- Alt+1-4 : Jump to specific tab
- ? : Show help
- Ctrl+C : Exit
```

Current tabs:
- **💬 Chat** - Conversational interface with streaming
- **📚 Skills** - Browse and manage skills (coming soon)
- **⚙️ Jobs** - Monitor running optimization jobs (coming soon)
- **🚀 Optimize** - Configure and run optimizers (coming soon)

## 📊 Comparing Stream vs Sync Responses

### Streaming (Real-time)

```bash
# HTTP Request
POST /api/v1/chat/stream
Content-Type: application/json

{"message": "optimize my skill"}

# Response (Server-Sent Events)
event: thinking
data: {"type": "thought", "content": "Analyzing request...", "step": 1}

event: thinking
data: {"type": "reasoning", "content": "User wants to optimize...", "step": 2}

event: response
data: {"type": "response", "content": "I'll help you optimize your skill..."}

event: complete
data:
```

### Synchronous (Fallback)

```bash
# HTTP Request
POST /api/v1/chat/sync
Content-Type: application/json

{"message": "optimize my skill"}

# Response (JSON)
{
  "message": "optimize my skill",
  "thinking": [
    "Analyzing request...",
    "User wants to optimize...",
    "Setting up optimizer..."
  ],
  "response": "I'll help you optimize your skill...",
  "thinking_summary": "Full thinking process shown above"
}
```

## 🔧 Troubleshooting

### TUI doesn't launch

**Solution**: Fall back to simple terminal chat:
```bash
uv run skill-fleet chat --no-tui
```

### Streaming not working

**Check**:
1. API server is running (`uv run skill-fleet serve`)
2. Node.js is installed (`node --version` should be 18+)
3. API URL is correct: `http://localhost:8000`

**Test with curl**:
```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "hello"}'
```

### Slow response

**Likely cause**: LM cold start or network latency

**Check**:
- API logs for errors
- Network connectivity
- Available RAM on API server

## 📚 Advanced Usage

### Custom Context

Pass conversation context for better responses:

```
You: create a skill for my chatbot with context from previous skills
```

The system automatically tracks:
- Previous skills created
- Running jobs
- Training data

### Command Syntax

Explicit commands (override agentic inference):

```
/optimize reflection_metrics trainset_v4.json --fast
/list --filter python --sort recent
/validate skills/python/async
/promote job-xyz-123
/status job-xyz-123
/help
```

### Environment Variables

```bash
# Custom API URL
export SKILL_FLEET_API_URL=http://api.example.com:8000

# Custom user ID
export SKILL_FLEET_USER_ID=john.doe

# Launch TUI
uv run skill-fleet chat
```

## 🎓 Under the Hood

1. **User Message** → Sent to `/api/v1/chat/stream` via HTTP POST
2. **Intent Parsing** → StreamingIntentParser yields thinking chunks
3. **Response Generation** → StreamingAssistant generates response chunks
4. **SSE Streaming** → Events sent as they're generated
5. **TUI Rendering** → Ink.js updates display in real-time

See [STREAMING_ARCHITECTURE.md](./STREAMING_ARCHITECTURE.md) for details.

## 📖 Learn More

- [Streaming Architecture](./STREAMING_ARCHITECTURE.md) - Technical deep-dive
- [DSPy Optimization Guide](./OPTIMIZATION_GUIDE.md) - Optimization workflows
- [API Docs](http://localhost:8000/docs) - Interactive API documentation

## 🐛 Report Issues

Found a bug? Test streaming failing?

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
uv run skill-fleet chat

# Check logs in API server terminal
```

## ✨ What's Next

- [ ] Skills tab: Browse & manage skills
- [ ] Jobs tab: Monitor optimizations
- [ ] Optimization tab: Configure/run optimizers
- [ ] Reflection Metrics: Integration & highlighting
- [ ] Persistent conversation history
- [ ] Theme customization
