# DawsOS – Trinity Architecture Build

DawsOS is a knowledge-graph intelligence system that now runs entirely through
its **Trinity** execution pipeline:

```
Request → UniversalExecutor → PatternEngine → AgentRuntime/AgentRegistry → KnowledgeGraph
```

Patterns coordinate agents, agents operate through the registry/adapter layer,
and all results are persisted in the shared knowledge graph. This README
summarises the current state, how to get the system running, and where to find
the restored documentation.

---

## Quick Start

1. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure API keys** (all optional, but recommended)
   ```bash
   cp .env.example .env
   # then edit .env and add FMP_API_KEY, NEWSAPI_KEY, etc.
   ```
4. **Launch the Streamlit UI**
   ```bash
   streamlit run dawsos/main.py
   ```
5. **Run tests**
   After installing `pytest` locally (`python3 -m pip install pytest`), run:
   ```bash
   python3 -m pytest dawsos/tests/validation/test_trinity_smoke.py
   ```
   Add additional suites as you expand coverage.

---

## Architecture Snapshot

- `core/universal_executor.py` – single entry point. Routes every request to the
  `meta_executor` pattern and falls back safely when missing.
- `core/pattern_engine.py` – executes JSON-defined workflows. All agent access
  now flows through registry helpers (`_get_agent`, `_iter_agents`).
- `core/agent_runtime.py` – maintains the registry-backed agent catalogue and
  executes requests through adapters. `orchestrate` now defers to the executor.
- `core/knowledge_graph.py` – shared persistence layer with helper APIs
  (`get_node`, `get_nodes_by_type`, `safe_query`, etc.).
- `ui/` – Streamlit surfaces that now read agent data via the registry.

For diagrams and a deeper explanation, see
[`docs/TrinityExecutionFlow.md`](docs/TrinityExecutionFlow.md).

---

## Repository Layout

```
dawsos/
├── core/                 # Graph, runtime, executor, pattern engine
├── agents/               # Specialised agents (registered via runtime)
├── capabilities/         # External data integrations (FRED, FMP, etc.)
├── patterns/             # JSON pattern library (including system/meta)
├── storage/              # Persisted graph, sessions, knowledge bases
├── ui/                   # Streamlit components (chat, dashboards)
├── docs/
│   ├── TrinityExecutionFlow.md
│   ├── PHASE3_ENRICHMENT_PLAN.md
│   ├── ...
│   └── archive/          # Historical plans/status reports
└── tests/                # Validation and smoke suites
```

`archived_legacy/` retains the original Claude-based orchestrators for
historical reference only.

---

## Documentation

All Markdown files now live under `dawsos/docs/`. Recent highlights:

- `docs/TrinityExecutionFlow.md` – canonical execution flow.
- `docs/PHASE3_ENRICHMENT_PLAN.md` & `docs/PHASE3_DATA_MAP.md` – enrichment
  roadmaps.
- `docs/archive/` – historical plans, assessments, and reports from previous
  phases.

---

## Current Status

- ✅ Single execution entry point (UniversalExecutor) with meta-pattern routing.
- ✅ PatternEngine + AgentRegistry integration; direct `runtime.agents[...]`
  access removed from active code paths.
- ✅ Streamlit UI components query agent metadata via the registry.
- 🚧 Additional validation suites should be converted to `pytest` once available
  in your environment.

---

## Contributing & Next Steps

1. Ensure any new UI or workflow calls `UniversalExecutor.execute()` rather than
   invoking agents directly.
2. Add or update JSON patterns in `dawsos/patterns/`; accompany changes with
   smoke tests under `dawsos/tests/validation/`.
3. Keep documentation under `docs/` so the README remains the single entry point
   for newcomers.

Enjoy building with the Trinity stack!
