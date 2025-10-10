# AG-UI Quick Start Prototype - Weekend Project

**Goal**: Proof-of-concept AG-UI integration in 1-2 days
**Scope**: Minimal viable integration to test the concept

---

## What We'll Build

A minimal AG-UI middleware that:
1. ✅ Receives user messages
2. ✅ Executes through Trinity
3. ✅ Emits AG-UI events via SSE
4. ✅ Works with existing DawsOS

**No Frontend Required**: Test with curl/browser EventSource

---

## Step 1: Create Minimal AG-UI Middleware (1 hour)

```python
# dawsos/server/agui_minimal.py
"""
Minimal AG-UI Protocol implementation for DawsOS.
Single-file proof of concept.
"""

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import asyncio
from typing import AsyncIterator

# Import DawsOS components
import sys
sys.path.insert(0, '/Users/mdawson/Dawson/DawsOSB/dawsos')

from core.agent_runtime import AgentRuntime
from core.universal_executor import UniversalExecutor
from core.knowledge_graph import KnowledgeGraph
from core.agent_adapter import AgentRegistry

# Create FastAPI app
app = FastAPI(title="DawsOS AG-UI Server")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DawsOS components
graph = KnowledgeGraph()
registry = AgentRegistry()
runtime = AgentRuntime()
executor = UniversalExecutor(graph, registry, runtime)


def create_agui_event(event_type: str, data: dict) -> str:
    """Create AG-UI compliant SSE event."""
    event = {
        'type': event_type,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'agent_id': 'dawsos',
        'data': data
    }
    return f"data: {json.dumps(event)}\n\n"


async def process_message_stream(user_input: str) -> AsyncIterator[str]:
    """
    Process user message and yield AG-UI events.

    Yields SSE-formatted events.
    """
    # Event 1: Agent thinking
    yield create_agui_event('agent.thinking', {
        'message': 'Processing through Trinity Pattern Engine...'
    })

    await asyncio.sleep(0.1)  # Simulate processing

    # Event 2: Execute through Trinity
    try:
        result = executor.execute({
            'type': 'chat_input',
            'user_input': user_input
        })

        # Event 3: Agent message
        yield create_agui_event('agent.message', {
            'text': result.get('response', 'No response'),
            'metadata': {
                'pattern_used': result.get('pattern_id'),
                'execution_time_ms': result.get('execution_time', 0)
            }
        })

        # Event 4: Agent state (if graph updated)
        if result.get('graph_stored'):
            yield create_agui_event('agent.state', {
                'graph_updated': True,
                'node_id': result.get('node_id')
            })

        # Event 5: Agent UI (if components generated)
        if 'ui_component' in result:
            yield create_agui_event('agent.ui', {
                'component': result['ui_component']['type'],
                'props': result['ui_component']['props']
            })

    except Exception as e:
        # Event: Agent error
        yield create_agui_event('agent.error', {
            'error': str(e),
            'message': 'Execution failed'
        })


@app.post("/ag-ui/message")
async def send_message(request: Request):
    """
    Receive user message and return SSE stream of AG-UI events.

    Usage:
        curl -X POST http://localhost:8000/ag-ui/message \\
             -H "Content-Type: application/json" \\
             -d '{"text": "Analyze AAPL stock"}'
    """
    body = await request.json()
    user_input = body.get('text', '')

    return StreamingResponse(
        process_message_stream(user_input),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/ag-ui/health")
async def health():
    """Health check endpoint."""
    return {
        'status': 'ok',
        'service': 'DawsOS AG-UI Server',
        'version': '3.0-prototype',
        'agents': len(runtime._agents),
        'trinity_compliant': True
    }


@app.get("/ag-ui/agents")
async def list_agents():
    """List available agents and their capabilities."""
    from core.agent_capabilities import AGENT_CAPABILITIES

    agents_info = []
    for agent_name, metadata in AGENT_CAPABILITIES.items():
        if runtime.has_agent(agent_name):
            agents_info.append({
                'id': agent_name,
                'name': agent_name.replace('_', ' ').title(),
                'capabilities': metadata.get('capabilities', []),
                'status': 'active'
            })

    return {
        'agents': agents_info,
        'total': len(agents_info)
    }


if __name__ == '__main__':
    import uvicorn
    print("=" * 70)
    print("DawsOS AG-UI Server (Prototype)")
    print("=" * 70)
    print("Starting on http://localhost:8000")
    print()
    print("Test endpoints:")
    print("  Health:  GET  http://localhost:8000/ag-ui/health")
    print("  Agents:  GET  http://localhost:8000/ag-ui/agents")
    print("  Message: POST http://localhost:8000/ag-ui/message")
    print()
    print("Test with curl:")
    print('  curl -X POST http://localhost:8000/ag-ui/message \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"text": "What is the market regime?"}\'')
    print("=" * 70)

    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Step 2: Test with curl (5 minutes)

### **Start Server**:
```bash
cd /Users/mdawson/Dawson/DawsOSB
python dawsos/server/agui_minimal.py
```

### **Test Health**:
```bash
curl http://localhost:8000/ag-ui/health
```

**Expected**:
```json
{
  "status": "ok",
  "service": "DawsOS AG-UI Server",
  "version": "3.0-prototype",
  "agents": 15,
  "trinity_compliant": true
}
```

### **List Agents**:
```bash
curl http://localhost:8000/ag-ui/agents
```

**Expected**:
```json
{
  "agents": [
    {
      "id": "financial_analyst",
      "name": "Financial Analyst",
      "capabilities": ["can_calculate_dcf", "can_analyze_moat"],
      "status": "active"
    },
    ...
  ],
  "total": 15
}
```

### **Send Message** (See Events Stream):
```bash
curl -X POST http://localhost:8000/ag-ui/message \
     -H "Content-Type: application/json" \
     -d '{"text": "What is the market regime?"}'
```

**Expected SSE Stream**:
```
data: {"type":"agent.thinking","timestamp":"2025-10-09T12:00:00Z","agent_id":"dawsos","data":{"message":"Processing through Trinity Pattern Engine..."}}

data: {"type":"agent.message","timestamp":"2025-10-09T12:00:01Z","agent_id":"dawsos","data":{"text":"Current market regime is...","metadata":{"pattern_used":"market_regime"}}}

data: {"type":"agent.state","timestamp":"2025-10-09T12:00:01Z","agent_id":"dawsos","data":{"graph_updated":true,"node_id":"node_123"}}
```

---

## Step 3: Test with Browser (10 minutes)

Create a minimal HTML test page:

```html
<!-- test_agui.html -->
<!DOCTYPE html>
<html>
<head>
    <title>DawsOS AG-UI Test</title>
    <style>
        body { font-family: monospace; padding: 20px; background: #1e1e1e; color: #d4d4d4; }
        #events {
            border: 1px solid #444;
            padding: 10px;
            height: 400px;
            overflow-y: scroll;
            background: #252526;
            margin: 10px 0;
        }
        .event {
            margin: 5px 0;
            padding: 5px;
            background: #2d2d30;
            border-left: 3px solid #007acc;
        }
        .thinking { border-left-color: #f0ad4e; }
        .message { border-left-color: #5cb85c; }
        .error { border-left-color: #d9534f; }
        input {
            width: 70%;
            padding: 10px;
            background: #3c3c3c;
            border: 1px solid #555;
            color: #d4d4d4;
        }
        button {
            padding: 10px 20px;
            background: #007acc;
            border: none;
            color: white;
            cursor: pointer;
        }
        button:hover { background: #005a9e; }
    </style>
</head>
<body>
    <h1>🤖 DawsOS AG-UI Protocol Test</h1>

    <div>
        <input type="text" id="userInput" placeholder="Enter message (e.g., 'Analyze AAPL')" />
        <button onclick="sendMessage()">Send</button>
        <button onclick="clearEvents()">Clear</button>
    </div>

    <h3>Events Stream:</h3>
    <div id="events"></div>

    <script>
        const eventsDiv = document.getElementById('events');
        let eventSource = null;

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();

            if (!text) return;

            // Close previous connection
            if (eventSource) {
                eventSource.close();
            }

            // Add user message to display
            addEvent('user', 'user.message', { text });

            // Send message and listen to events
            try {
                const response = await fetch('http://localhost:8000/ag-ui/message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });

                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const eventData = JSON.parse(line.slice(6));
                            addEvent('agent', eventData.type, eventData.data);
                        }
                    }
                }
            } catch (error) {
                addEvent('error', 'connection.error', { error: error.message });
            }

            input.value = '';
        }

        function addEvent(source, type, data) {
            const eventDiv = document.createElement('div');
            eventDiv.className = 'event ' + type.split('.')[1];

            const timestamp = new Date().toLocaleTimeString();
            const eventType = type.replace('agent.', '').replace('user.', '');

            eventDiv.innerHTML = `
                <strong>[${timestamp}]</strong>
                <span style="color: ${source === 'user' ? '#569cd6' : '#4ec9b0'}">${source}</span>
                <span style="color: #dcdcaa">${eventType}</span>:
                ${JSON.stringify(data, null, 2)}
            `;

            eventsDiv.appendChild(eventDiv);
            eventsDiv.scrollTop = eventsDiv.scrollHeight;
        }

        function clearEvents() {
            eventsDiv.innerHTML = '';
        }

        // Allow Enter key to send
        document.getElementById('userInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
```

**Open in browser**: `file:///path/to/test_agui.html`

**Try queries**:
- "What is the market regime?"
- "Analyze AAPL stock"
- "Show sector performance"

---

## Step 4: Verify Trinity Compliance (5 minutes)

The prototype maintains 100% Trinity compliance:

```python
# Verify execution flow
result = executor.execute({
    'type': 'chat_input',
    'user_input': user_input
})
```

**Flow**:
```
HTTP Request
    ↓
FastAPI Endpoint
    ↓
AG-UI Middleware (events emitted)
    ↓
UniversalExecutor.execute()  ← Trinity entry point
    ↓
PatternEngine → AgentRuntime → Agents → KnowledgeGraph
    ↓
Result → Converted to AG-UI events
    ↓
SSE Stream to client
```

**Trinity Compliance Checklist**:
- ✅ All execution through UniversalExecutor
- ✅ Pattern-driven workflow
- ✅ Registry-based agent routing
- ✅ Results stored in KnowledgeGraph
- ✅ No registry bypasses

---

## Expected Results

### **What Works**:
✅ HTTP server starts on port 8000
✅ Health check returns status
✅ Agents list shows 15 registered agents
✅ Message endpoint accepts POST requests
✅ SSE events stream in real-time
✅ Trinity execution flows correctly
✅ Events include thinking/message/state

### **What's Missing** (Full Implementation):
⏸️ WebSocket support (SSE only)
⏸️ Agent UI components (no generative UI yet)
⏸️ Pattern step-by-step events (only final result)
⏸️ Human-in-the-loop interrupts
⏸️ Full event validation
⏸️ Authentication/authorization

---

## Next Steps After Prototype

### **If Successful** ✅:
1. Add async execution to PatternEngine
2. Emit events for each pattern step
3. Add UI component generation
4. Create proper event queue
5. Add WebSocket transport
6. Build React frontend

### **Incremental Improvements**:
1. Add `agent.tool.call` events for capabilities
2. Emit pattern step progress
3. Add error handling events
4. Implement event backpressure
5. Add connection management

---

## Troubleshooting

### **Port 8000 in use**:
```bash
# Change port in script
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### **Module import errors**:
```bash
# Ensure running from correct directory
cd /Users/mdawson/Dawson/DawsOSB
python dawsos/server/agui_minimal.py
```

### **No events streaming**:
- Check browser console for CORS errors
- Verify server is running
- Test with curl first

### **Trinity execution fails**:
- Verify agents are registered
- Check pattern directory path
- Review server logs

---

## Success Criteria

**✅ Prototype Success** if you can:
1. Start AG-UI server
2. Send message via curl
3. Receive SSE event stream
4. See events in browser HTML
5. Verify Trinity execution works
6. Get agent.thinking + agent.message events

**Time**: 1-2 hours for full prototype

---

## Cleanup

```bash
# Stop server
Ctrl+C

# Remove prototype file (optional)
rm dawsos/server/agui_minimal.py
```

---

## Conclusion

This minimal prototype demonstrates:
✅ AG-UI Protocol feasibility
✅ Trinity Architecture compatibility
✅ Event streaming via SSE
✅ Real-time agent communication
✅ Zero breaking changes

**Next**: If successful, proceed with full Trinity 3.0 integration plan.

**Time Investment**: 1-2 hours
**Risk**: Low (single file, easily removed)
**Value**: High (validates entire Trinity 3.0 strategy)
