# Trinity Execution Flow

This document describes the active execution pipeline for DawsOS after the
Trinity refactor.

```
UI / API Request
        |
        v
+---------------------+
|  UniversalExecutor  |  (meta_executor pattern)
+---------------------+
        |
        v
PatternEngine.execute_pattern()
        |
        v
AgentRuntime.execute() -- AgentRegistry -> AgentAdapter
        |
        v
 KnowledgeGraph (read/write) + Persistence
```

Key guarantees:

- All entry points call `UniversalExecutor.execute(request)`.
- The executor invokes the `meta_executor` pattern when available and falls back
  safely otherwise.
- `PatternEngine` resolves steps and delegates to agents via
  `AgentRuntime.execute`, which enforces registry compliance.
- Specialized agents operate on the shared `KnowledgeGraph`, and results are
  persisted for future requests.

Legacy orchestrators (`core/claude_orchestrator.py`, `core/orchestrator.py`) are
kept only in `archived_legacy/` for historical reference.
