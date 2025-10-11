# Trinity 3.0 - AG-UI Integration: Detailed Execution Plan

**Date**: October 9, 2025
**Analysis Depth**: Deep technical execution flow analysis
**Status**: Production-ready implementation blueprint

---

## Executive Summary

After deep analysis of Trinity 2.0 codebase:
- ✅ **378 files** already use async/await (strong async foundation)
- ✅ **Synchronous execution flow** is primary (Streamlit constraint)
- ✅ **UniversalExecutor** is true single entry point
- ✅ **PatternEngine** coordinates all workflows
- ✅ **Zero breaking changes** possible with proper layering

**Key Insight**: AG-UI integration requires a **parallel async execution path** alongside existing sync flow, not a replacement.

---

## Part 1: Deep Execution Flow Analysis

### **Current Trinity 2.0 Execution** (Synchronous)

```python
# Entry Point: dawsos/main.py (Streamlit)
def main():
    # Initialize components
    graph = KnowledgeGraph()
    registry = AgentRegistry()
    runtime = AgentRuntime()
    executor = UniversalExecutor(graph, registry, runtime)

    # User input from Streamlit
    user_input = st.chat_input("What would you like to know?")

    # SYNCHRONOUS execution
    result = executor.execute({
        'type': 'chat_input',
        'user_input': user_input
    })

    # Display result
    st.markdown(result['response'])

# Flow breakdown:
# 1. executor.execute(request) → Dict
# 2.   └─ pattern_engine.execute_pattern(pattern, context) → Dict
# 3.       └─ For each step in pattern:
# 4.           └─ action_registry.execute(action, params) → Dict
# 5.               └─ runtime.exec_via_registry(agent, context) → Dict
# 6.                   └─ agent_adapter.execute(context) → Dict
# 7.                       └─ agent.process(context) → Dict
# 8.                           └─ graph.add_node(result) → str (node_id)
```

**Key Characteristics**:
- **Blocking**: Each step waits for previous
- **Return values**: All functions return Dict
- **No streaming**: Results returned at end
- **Streamlit constraint**: UI blocks during execution

### **Target Trinity 3.0 with AG-UI** (Dual-Path)

```python
# Path 1: Synchronous (Streamlit - unchanged)
result = executor.execute(request)  # Existing code works

# Path 2: Asynchronous (AG-UI - new)
async for event in executor.execute_streaming(request):
    await emit_agui_event(event)
```

**Critical Requirement**: **Both paths must coexist without conflicts.**

---

## Part 2: Integration Architecture (Refined)

### **Layer 0: Dual Execution Modes** (NEW)

```python
# dawsos/core/execution_mode.py
"""
Execution mode abstraction for sync/async duality.
"""
from enum import Enum
from typing import Dict, Any, Union, AsyncIterator
from dataclasses import dataclass

class ExecutionMode(Enum):
    SYNC = "sync"      # Traditional Streamlit (current)
    ASYNC_STREAM = "async_stream"  # AG-UI streaming

@dataclass
class ExecutionContext:
    """Enhanced context with mode awareness."""
    mode: ExecutionMode
    request: Dict[str, Any]
    event_emitter: Optional['EventEmitter'] = None
    session_id: str = None

    def is_streaming(self) -> bool:
        return self.mode == ExecutionMode.ASYNC_STREAM
```

### **Layer 1: Event Emitter** (NEW - Core Infrastructure)

```python
# dawsos/core/agui/event_emitter.py
"""
Event emitter for AG-UI protocol.
Thread-safe, async-compatible event emission.
"""
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging

class EventEmitter:
    """
    Emit AG-UI events during Trinity execution.

    Design Principles:
    - Non-blocking: Events queued, not blocking execution
    - Safe: Works with both sync and async execution
    - Optional: Can be None (no-op mode)
    """

    def __init__(self):
        self.queue = asyncio.Queue()
        self.listeners = []
        self.logger = logging.getLogger('EventEmitter')

    async def emit(self, event_type: str, data: Dict[str, Any]):
        """Emit an AG-UI event (async)."""
        event = self._create_event(event_type, data)
        await self.queue.put(event)
        self.logger.debug(f"Emitted: {event_type}")

    def emit_sync(self, event_type: str, data: Dict[str, Any]):
        """Emit an AG-UI event (sync wrapper for existing code)."""
        event = self._create_event(event_type, data)
        # Store in thread-safe queue without awaiting
        try:
            self.queue.put_nowait(event)
        except asyncio.QueueFull:
            self.logger.warning(f"Event queue full, dropping: {event_type}")

    def _create_event(self, event_type: str, data: Dict[str, Any]) -> Dict:
        """Create AG-UI compliant event."""
        return {
            'type': event_type,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'agent_id': 'dawsos',
            'data': data
        }

    async def consume(self) -> AsyncIterator[Dict]:
        """Consume events from queue (for SSE/WebSocket)."""
        while True:
            event = await self.queue.get()
            yield event
            self.queue.task_done()


class NullEmitter(EventEmitter):
    """No-op emitter for sync execution (zero overhead)."""

    async def emit(self, event_type: str, data: Dict[str, Any]):
        pass  # No-op

    def emit_sync(self, event_type: str, data: Dict[str, Any]):
        pass  # No-op
```

### **Layer 2: Enhanced UniversalExecutor** (MODIFIED)

```python
# dawsos/core/universal_executor.py (Enhanced)
"""
Universal Executor with dual execution modes.
"""
from typing import Dict, Any, AsyncIterator, Optional
from core.agui.event_emitter import EventEmitter, NullEmitter
from core.agui.execution_mode import ExecutionMode, ExecutionContext

class UniversalExecutor:
    """Single entry point for ALL DawsOS execution (sync & async)."""

    def __init__(self, graph, registry, runtime, auto_save=True):
        # Existing initialization unchanged
        self.graph = graph
        self.registry = registry
        self.runtime = runtime
        self.pattern_engine = PatternEngine(runtime=runtime, graph=graph)
        self.auto_save = auto_save
        self.persistence = PersistenceManager()
        self.metrics = {...}  # Existing metrics

    # ========== EXISTING SYNC PATH (UNCHANGED) ==========
    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous execution (Trinity 2.0 compatible).
        Used by Streamlit and existing code.
        """
        # Existing implementation unchanged
        self.metrics['total_executions'] += 1
        context = self._prepare_context(request)

        if self.pattern_engine.has_pattern('meta_executor'):
            pattern = self.pattern_engine.get_pattern('meta_executor')
            result = self.pattern_engine.execute_pattern(pattern, context)
        else:
            result = self._execute_fallback(context)

        self._store_execution_result(request, result)
        if self.auto_save:
            self._save_graph()

        return result

    # ========== NEW ASYNC PATH (AG-UI) ==========
    async def execute_streaming(
        self,
        request: Dict[str, Any],
        event_emitter: Optional[EventEmitter] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Asynchronous streaming execution (Trinity 3.0 AG-UI).

        Yields AG-UI events during execution while maintaining
        full Trinity compliance.

        Args:
            request: Same format as execute()
            event_emitter: Optional emitter (created if None)

        Yields:
            AG-UI events (agent.thinking, agent.message, agent.ui, etc.)
        """
        # Create emitter if not provided
        emitter = event_emitter or EventEmitter()

        # Create execution context with streaming mode
        exec_context = ExecutionContext(
            mode=ExecutionMode.ASYNC_STREAM,
            request=request,
            event_emitter=emitter
        )

        # Emit start event
        await emitter.emit('agent.thinking', {
            'message': 'Initializing Trinity execution...'
        })

        # Prepare context (same as sync)
        context = self._prepare_context(request)
        context['execution_context'] = exec_context

        # Execute through pattern engine with streaming
        if self.pattern_engine.has_pattern('meta_executor'):
            pattern = self.pattern_engine.get_pattern('meta_executor')

            # NEW: Stream pattern execution
            async for event in self.pattern_engine.execute_pattern_streaming(
                pattern, context, emitter
            ):
                yield event
        else:
            # Fallback streaming
            async for event in self._execute_fallback_streaming(context, emitter):
                yield event

        # Final state event
        await emitter.emit('agent.state', {
            'execution_complete': True,
            'graph_nodes': self.graph.get_stats()['total_nodes']
        })

    async def _execute_fallback_streaming(
        self,
        context: Dict[str, Any],
        emitter: EventEmitter
    ) -> AsyncIterator[Dict]:
        """Fallback streaming execution when meta_executor unavailable."""
        await emitter.emit('agent.thinking', {
            'message': 'Using fallback execution...'
        })

        # Execute sync fallback
        result = self._execute_fallback(context)

        # Convert result to events
        await emitter.emit('agent.message', {
            'text': result.get('response', 'No response'),
            'metadata': result.get('metadata', {})
        })

        yield result
```

### **Layer 3: Enhanced PatternEngine** (MODIFIED)

```python
# dawsos/core/pattern_engine.py (Enhanced)
"""
Pattern Engine with streaming support.
"""
from typing import Dict, Any, AsyncIterator, Optional

class PatternEngine:
    """Execute JSON-defined patterns (sync & async)."""

    def __init__(self, pattern_dir='patterns', runtime=None, graph=None):
        # Existing initialization unchanged
        self.pattern_dir = Path(pattern_dir)
        self.runtime = runtime
        self.graph = graph
        self.patterns = {}
        self.action_registry = ActionRegistry()
        self._register_action_handlers()
        self.load_patterns()

    # ========== EXISTING SYNC METHOD (UNCHANGED) ==========
    def execute_pattern(
        self,
        pattern: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute pattern synchronously (Trinity 2.0).
        Existing implementation unchanged.
        """
        outputs = {}

        for idx, step in enumerate(pattern.get('steps', [])):
            action = step.get('action')
            params = step.get('params', {})

            # Execute action
            result = self.action_registry.execute(action, params, context, outputs)

            # Save output
            save_as = step.get('save_as', f'step_{idx}')
            outputs[save_as] = result

        return self._format_response(pattern, outputs)

    # ========== NEW ASYNC METHOD (AG-UI) ==========
    async def execute_pattern_streaming(
        self,
        pattern: Dict[str, Any],
        context: Dict[str, Any],
        emitter: EventEmitter
    ) -> AsyncIterator[Dict]:
        """
        Execute pattern with AG-UI event streaming (Trinity 3.0).

        Emits events for each step execution while maintaining
        full Trinity compliance.
        """
        outputs = {}
        steps = pattern.get('steps', [])
        total_steps = len(steps)

        # Emit pattern start
        await emitter.emit('agent.thinking', {
            'message': f"Executing pattern: {pattern.get('name', 'Unknown')}",
            'steps': total_steps
        })

        for idx, step in enumerate(steps):
            step_num = idx + 1
            action = step.get('action')
            params = step.get('params', {})
            description = step.get('description', f'Step {step_num}')

            # Emit step start
            await emitter.emit('agent.thinking', {
                'step': step_num,
                'total': total_steps,
                'action': action,
                'description': description
            })

            # Check if action handler supports streaming
            handler = self.action_registry.handlers.get(action)

            if handler and hasattr(handler, 'execute_streaming'):
                # Use streaming handler
                async for event in handler.execute_streaming(
                    params, context, outputs, emitter
                ):
                    yield event

                # Get final result from handler state
                result = handler.last_result
            else:
                # Use sync handler (wrap in async)
                result = await asyncio.to_thread(
                    self.action_registry.execute,
                    action, params, context, outputs
                )

                # Emit result as event
                await emitter.emit('agent.tool.result', {
                    'step': step_num,
                    'action': action,
                    'result': result
                })

            # Save output
            save_as = step.get('save_as', f'step_{idx}')
            outputs[save_as] = result

        # Format final response
        response = self._format_response(pattern, outputs)

        # Emit final message
        await emitter.emit('agent.message', {
            'text': response.get('response', ''),
            'pattern': pattern.get('id'),
            'steps_completed': total_steps
        })

        yield response
```

### **Layer 4: Enhanced Action Handlers** (MODIFIED)

```python
# dawsos/core/actions/__init__.py (Enhanced)
"""
Base action handler with streaming support.
"""
from typing import Dict, Any, AsyncIterator, Optional
from abc import ABC, abstractmethod

class ActionHandler(ABC):
    """Base class for all action handlers (sync & async)."""

    def __init__(self, engine):
        self.engine = engine
        self.runtime = engine.runtime
        self.graph = engine.graph
        self.logger = engine.logger
        self.last_result = None

    @property
    @abstractmethod
    def action_name(self) -> str:
        """Return the action name."""
        pass

    @abstractmethod
    def execute(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any],
        outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute action synchronously (required)."""
        pass

    async def execute_streaming(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any],
        outputs: Dict[str, Any],
        emitter: EventEmitter
    ) -> AsyncIterator[Dict]:
        """
        Execute action with event streaming (optional).

        Default implementation wraps sync execute.
        Override for true streaming support.
        """
        # Emit thinking
        await emitter.emit('agent.thinking', {
            'message': f'Executing {self.action_name}...'
        })

        # Execute sync (in thread pool)
        result = await asyncio.to_thread(
            self.execute, params, context, outputs
        )

        self.last_result = result

        # Emit result
        await emitter.emit('agent.tool.result', {
            'action': self.action_name,
            'result': result
        })

        yield result


# Example: execute_by_capability with streaming
class ExecuteByCapabilityAction(ActionHandler):
    """Execute agent by capability with streaming."""

    @property
    def action_name(self) -> str:
        return "execute_by_capability"

    def execute(self, params, context, outputs) -> Dict:
        """Sync execution (existing)."""
        capability = params.get('capability')
        agent_context = params.get('context', {})

        # Resolve variables
        resolved_context = {}
        for key, value in agent_context.items():
            resolved_context[key] = self._resolve_param(value, context, outputs)

        # Execute through runtime
        result = self.runtime.execute_by_capability(capability, resolved_context)
        return result

    async def execute_streaming(self, params, context, outputs, emitter) -> AsyncIterator[Dict]:
        """Async streaming execution (NEW)."""
        capability = params.get('capability')

        # Emit capability call
        await emitter.emit('agent.tool.call', {
            'capability': capability,
            'action': 'execute_by_capability'
        })

        # Execute (wrap sync runtime call)
        result = await asyncio.to_thread(
            self.execute, params, context, outputs
        )

        self.last_result = result

        # Emit result with metadata
        await emitter.emit('agent.tool.result', {
            'capability': capability,
            'agent': result.get('agent'),
            'success': 'error' not in result
        })

        # Emit UI if present
        if 'ui_component' in result:
            await emitter.emit('agent.ui', result['ui_component'])

        yield result
```

---

## Part 3: AG-UI HTTP Server (Production-Ready)

```python
# dawsos/server/agui_server.py
"""
Production AG-UI server with SSE and WebSocket support.
"""
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
from typing import Dict, Any
import sys
from pathlib import Path

# Add dawsos to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.knowledge_graph import KnowledgeGraph
from core.agent_runtime import AgentRuntime
from core.agent_adapter import AgentRegistry
from core.universal_executor import UniversalExecutor
from core.agui.event_emitter import EventEmitter
from load_env import load_env

# Load environment
load_env()

# Global state (initialized on startup)
executor: UniversalExecutor = None
runtime: AgentRuntime = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DawsOS components on startup."""
    global executor, runtime

    # Initialize Trinity components
    graph = KnowledgeGraph()
    registry = AgentRegistry()
    runtime = AgentRuntime()
    executor = UniversalExecutor(graph, registry, runtime)

    # Register agents (import and register all 15 agents)
    from dawsos.main import _register_all_agents, _init_capabilities
    caps = {}
    _init_capabilities()  # Initialize capabilities
    _register_all_agents(runtime, caps)

    print("✅ DawsOS Trinity 3.0 AG-UI Server Ready")
    yield

    # Cleanup
    print("🛑 Shutting down AG-UI server")

# Create FastAPI app
app = FastAPI(
    title="DawsOS AG-UI Server",
    version="3.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/ag-ui/message")
async def send_message(request: Request):
    """
    Send message and receive SSE stream of AG-UI events.

    Request:
        {"text": "user message", "session_id": "optional"}

    Response:
        SSE stream of AG-UI events
    """
    body = await request.json()
    user_input = body.get('text', '')
    session_id = body.get('session_id', 'default')

    async def event_stream():
        """Generate SSE events."""
        emitter = EventEmitter()

        # Execute with streaming
        async for event in executor.execute_streaming(
            {'type': 'chat_input', 'user_input': user_input},
            event_emitter=emitter
        ):
            # Consume events from emitter
            try:
                queued_event = await asyncio.wait_for(
                    emitter.queue.get(), timeout=0.1
                )
                # Format as SSE
                yield f"data: {json.dumps(queued_event)}\n\n"
            except asyncio.TimeoutError:
                continue

        # Signal completion
        yield f"data: {json.dumps({'type': 'stream.end', 'data': {}})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.websocket("/ag-ui/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for bi-directional AG-UI communication.
    """
    await websocket.accept()
    emitter = EventEmitter()

    try:
        while True:
            # Receive user message
            data = await websocket.receive_json()

            if data.get('type') == 'user.message':
                user_input = data['data']['text']

                # Execute with streaming
                async for event in executor.execute_streaming(
                    {'type': 'chat_input', 'user_input': user_input},
                    event_emitter=emitter
                ):
                    # Send events as they come
                    try:
                        queued_event = await asyncio.wait_for(
                            emitter.queue.get(), timeout=0.1
                        )
                        await websocket.send_json(queued_event)
                    except asyncio.TimeoutError:
                        continue

    except WebSocketDisconnect:
        print(f"WebSocket disconnected")


@app.get("/ag-ui/health")
async def health():
    """Health check."""
    return {
        'status': 'ok',
        'version': '3.0.0',
        'mode': 'streaming',
        'agents': len(runtime._agents) if runtime else 0
    }


@app.get("/ag-ui/agents")
async def list_agents():
    """List available agents and capabilities."""
    from core.agent_capabilities import AGENT_CAPABILITIES

    agents = []
    for name, meta in AGENT_CAPABILITIES.items():
        if runtime.has_agent(name):
            agents.append({
                'id': name,
                'name': name.replace('_', ' ').title(),
                'capabilities': meta.get('capabilities', []),
                'status': 'active'
            })

    return {'agents': agents, 'total': len(agents)}


if __name__ == '__main__':
    import uvicorn
    print("=" * 70)
    print("DawsOS Trinity 3.0 - AG-UI Server")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
```

---

## Part 4: Detailed Migration Phases

### **Phase 1: Foundation (Week 1-2)** ⭐ CRITICAL

**Goal**: Add async execution without breaking sync

#### **Week 1: Core Infrastructure**

**Day 1-2**: Event Emitter & Execution Mode
- Create `dawsos/core/agui/` directory
- Implement `event_emitter.py` (EventEmitter, NullEmitter)
- Implement `execution_mode.py` (ExecutionMode, ExecutionContext)
- Write unit tests for event emitter
- **Deliverable**: Event emission working in isolation

**Day 3-4**: UniversalExecutor Enhancement
- Add `execute_streaming()` method to UniversalExecutor
- Keep existing `execute()` unchanged
- Add mode detection logic
- Write integration tests
- **Deliverable**: Dual execution paths functional

**Day 5**: Testing & Validation
- Run full Trinity 2.0 test suite (ensure no regression)
- Test sync execution (must be identical)
- Test async execution (events emit correctly)
- **Deliverable**: Zero breaking changes confirmed

#### **Week 2: Pattern Engine Streaming**

**Day 1-2**: PatternEngine Enhancement
- Add `execute_pattern_streaming()` method
- Implement step-by-step event emission
- Handle sync action handlers gracefully
- **Deliverable**: Patterns emit events per step

**Day 3-4**: Action Handler Base Class
- Enhance ActionHandler with `execute_streaming()`
- Implement default wrapping behavior
- Add streaming to critical actions (execute_by_capability, execute_through_registry)
- **Deliverable**: Actions support streaming

**Day 5**: Integration Testing
- Test full flow: HTTP → Executor → Pattern → Action → Agent
- Verify events emitted at each layer
- Performance testing (overhead < 5%)
- **Deliverable**: End-to-end streaming works

### **Phase 2: HTTP Server (Week 3)**

**Day 1-2**: FastAPI Server Setup
- Create `dawsos/server/agui_server.py`
- Implement lifespan management (DawsOS initialization)
- Add CORS, error handling
- **Deliverable**: Basic HTTP server running

**Day 3**: SSE Endpoint
- Implement `/ag-ui/message` POST endpoint
- Stream events via Server-Sent Events
- Handle connection management
- **Deliverable**: SSE streaming works with curl

**Day 4**: WebSocket Endpoint
- Implement `/ag-ui/ws` WebSocket endpoint
- Bi-directional event streaming
- Connection pooling
- **Deliverable**: WebSocket chat works

**Day 5**: Production Readiness
- Add authentication/authorization
- Implement rate limiting
- Add monitoring (Prometheus metrics)
- Load testing (100+ concurrent connections)
- **Deliverable**: Production-ready server

### **Phase 3: Frontend (Week 4-5)**

**Week 4: React Frontend**
- Initialize Next.js with AG-UI SDK
- Create chat interface
- Implement component renderer
- Add state management (Zustand/Redux)
- **Deliverable**: Basic chat works

**Week 5: Advanced UI**
- Implement generative UI components
- Add thinking indicators
- Implement graph state viewer
- Add error handling
- **Deliverable**: Full-featured frontend

### **Phase 4: Advanced Features (Week 6-7)**

**Week 6**: Graph State Sync
- Implement bi-directional state sync
- Real-time graph updates in UI
- Conflict resolution
- **Deliverable**: Live graph updates

**Week 7**: Human-in-the-Loop
- Pattern interruption support
- Approval workflows
- Decision modification
- **Deliverable**: Interactive agent oversight

---

## Part 5: Technical Challenges & Solutions

### **Challenge 1: Async/Sync Bridge**

**Problem**: Streamlit is sync-only, AG-UI needs async

**Solution**: Dual execution paths
```python
# Streamlit (sync)
result = executor.execute(request)

# AG-UI (async)
async for event in executor.execute_streaming(request):
    await send_event(event)
```

**Key**: UniversalExecutor supports both without internal conflicts

### **Challenge 2: Event Queue Backpressure**

**Problem**: If events generated faster than consumed, queue grows unbounded

**Solution**: Bounded queue with overflow strategy
```python
self.queue = asyncio.Queue(maxsize=1000)

async def emit(self, event_type, data):
    try:
        await asyncio.wait_for(
            self.queue.put(event),
            timeout=1.0
        )
    except asyncio.TimeoutError:
        self.logger.warning(f"Event dropped: {event_type}")
```

### **Challenge 3: Agent Blocking Calls**

**Problem**: Some agents make blocking I/O calls (network, disk)

**Solution**: Run in thread pool
```python
# In execute_streaming
result = await asyncio.to_thread(
    self.agent.process, context
)
```

### **Challenge 4: Graph Concurrent Access**

**Problem**: KnowledgeGraph not thread-safe

**Solution**: Add async lock
```python
# In KnowledgeGraph
class KnowledgeGraph:
    def __init__(self):
        self._lock = asyncio.Lock()

    async def add_node_async(self, ...):
        async with self._lock:
            return self.add_node(...)
```

### **Challenge 5: Streamlit vs. FastAPI**

**Problem**: Both want to own event loop

**Solution**: Run separately
```bash
# Terminal 1: Streamlit (port 8501)
streamlit run dawsos/main.py

# Terminal 2: AG-UI Server (port 8000)
python dawsos/server/agui_server.py
```

---

## Part 6: Testing Strategy

### **Unit Tests**
```python
# tests/test_event_emitter.py
async def test_event_emission():
    emitter = EventEmitter()

    await emitter.emit('agent.thinking', {'message': 'test'})

    event = await emitter.queue.get()
    assert event['type'] == 'agent.thinking'
    assert event['data']['message'] == 'test'
```

### **Integration Tests**
```python
# tests/test_streaming_execution.py
async def test_full_streaming_flow():
    executor = UniversalExecutor(graph, registry, runtime)

    events = []
    async for event in executor.execute_streaming({
        'type': 'chat_input',
        'user_input': 'Analyze AAPL'
    }):
        events.append(event)

    # Verify event sequence
    assert events[0]['type'] == 'agent.thinking'
    assert any(e['type'] == 'agent.message' for e in events)
    assert any(e['type'] == 'agent.state' for e in events)
```

### **Load Tests**
```python
# tests/load_test.py
async def test_concurrent_connections():
    async with asyncio.TaskGroup() as tg:
        for i in range(100):
            tg.create_task(send_message(f"Test {i}"))

    # Verify: All succeed, response time < 1s
```

---

## Part 7: Rollout Strategy

### **Alpha (Internal)**
- Deploy to staging environment
- Test with sample data
- Performance profiling
- Fix critical bugs

### **Beta (Limited Users)**
- 10-20 early adopters
- Feedback collection
- UI/UX refinement
- Documentation completion

### **Production (Full Rollout)**
- Gradual rollout (10% → 50% → 100%)
- Monitor metrics (latency, errors, events/sec)
- Fallback to sync if issues
- Full documentation

---

## Part 8: Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Event Latency** | < 50ms | Event emit → queue → consumer |
| **Execution Overhead** | < 5% | Async vs. sync execution time |
| **Concurrent Users** | 100+ | Load test with 100 simultaneous connections |
| **Event Throughput** | 1000+ events/sec | Stress test event emission |
| **Zero Regressions** | 100% | All Trinity 2.0 tests pass |
| **Graph Sync Latency** | < 100ms | Node added → UI updated |
| **WebSocket Uptime** | 99.9% | Connection stability |

---

## Conclusion

**Trinity 3.0 AG-UI integration is technically feasible with:**
- ✅ Zero breaking changes (dual execution paths)
- ✅ Strong async foundation (378 files already use async)
- ✅ Clear architecture (event layer is additive)
- ✅ 7-week implementation timeline
- ✅ Production-ready design (robust error handling, testing strategy)

**Next Step**: Begin Phase 1, Week 1 (Event Emitter & Execution Mode)

**Estimated Effort**: 7 weeks, 1 developer
**Risk Level**: Low (incremental, tested, reversible)
**Impact**: Transformative (real-time, interoperable, future-proof)
