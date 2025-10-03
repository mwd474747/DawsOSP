# Agent Development Guide

This guide explains how to create, register, and maintain agents within the
DawsOS Trinity architecture.

---

## Core Principles

1. **Registry First** – Every agent must be registered with
   `AgentRuntime.register_agent(name, instance, capabilities=...)`.
2. **Capability Metadata** – Capabilities drive routing, dashboards, and lint
   checks. All agents reference their canonical entry in
   `dawsos/core/agent_capabilities.py`.
3. **Registry Execution Only** – Use `runtime.exec_via_registry()` or pattern
   actions like `execute_through_registry`. Direct access to `runtime.agents`
   triggers bypass warnings and is blocked when `TRINITY_STRICT_MODE=true`.
4. **Graph Persistence** – Agents that generate results should call
   `store_result()` or rely on `AgentAdapter`’s auto-storage so outputs land in
   the knowledge graph for future reasoning.

---

## Adding a New Agent

1. **Implement the class** inside `dawsos/agents/`.
   ```python
   class NewAgent(BaseAgent):
       def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
           ...
   ```
2. **Update capability metadata** in
   `dawsos/core/agent_capabilities.py`:
   ```python
   'new_agent': {
       'description': 'Short description',
       'capabilities': ['can_detect_x', 'can_generate_y'],
       'requires': ['requires_knowledge_graph'],
       'provides': ['provides_actionable_signal'],
       'integrates_with': ['pattern_spotter'],
       'stores_results': True,
       'priority': 'medium',
       'category': 'analysis'
   }
   ```
3. **Register the agent** (e.g., in `main.py` or the relevant test fixture):
   ```python
   runtime.register_agent(
       'new_agent',
       NewAgent(graph),
       capabilities=AGENT_CAPABILITIES['new_agent']
   )
   ```
4. **Invoke via registry**:
   ```python
   runtime.exec_via_registry('new_agent', {'task': 'describe'})
   ```
   or from patterns:
   ```json
   {
     "action": "execute_through_registry",
     "params": {
       "agent": "new_agent",
       "context": {"task": "describe"}
     }
   }
   ```

---

## Strict Mode and Bypass Warning

- Set `TRINITY_STRICT_MODE=true` to raise exceptions when legacy access is
  detected. Default mode logs warnings.
- Warnings and strict-mode exceptions include caller information and are stored
  via `AgentRegistry.log_bypass_warning(...)`.
- Dashboard widgets and alert panels surface bypass counts so regressions are
  obvious.

---

## Testing Checklist

- Add unit tests for new agent methods.
- Exercise the registry path (e.g., call `runtime.exec_via_registry`) inside a
  pytest fixture.
- Run `python3 -m pytest dawsos/tests/` and
  `python3 scripts/lint_patterns.py` before submitting changes.
- Ensure new agents do not introduce bare `except` or bypass registry pathways.

---

## Best Practices

- **Keep agents pure**: Accept context dictionaries, return structured, JSON
  serializable data.
- **Store outputs**: Use `store_result(...)` or rely on the adapter to capture
  successful results in the knowledge graph.
- **Document capabilities**: Update the README or capability guide when adding
  new skills so patterns and UI components can consume them.
- **Monitor telemetry**: Use registry metrics and bypass logs to validate that
  the agent is used correctly in production.

