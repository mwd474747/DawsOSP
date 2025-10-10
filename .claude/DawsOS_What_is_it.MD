# What is DawsOS?

DawsOS is a pattern-driven financial intelligence platform built on the Trinity architecture. The system orchestrates 15 specialized agents through a centralized registry, executes 45 JSON patterns, and persists everything to a NetworkX-backed knowledge graph.

## Key Characteristics

- **Trinity Execution Path** – Requests flow through `UniversalExecutor → PatternEngine → AgentRegistry → Agent`. Every agent call is routed through the registry for telemetry and compliance.
- **Knowledge Graph First** – A NetworkX graph stores all nodes, relationships, and derived analyses. Persistence is handled by `PersistenceManager` with rotating backups.
- **Agent Roster (15)** – Core agents cover data harvesting, enrichment, forecasting, governance, UI generation, and financial analysis. Legacy adapters (macro/equity/risk) were retired in Oct 2025.
- **Pattern Library** – 45 JSON patterns span actions, analysis, governance, queries, workflows, and meta orchestration.
- **Fallback Transparency** – A centralized `fallback_tracker` records when cached/placeholder data is used and surfaces warnings in the UI and API Health dashboard.

## Current Capabilities

- Natural-language query handling via the Claude agent
- Live market, economic, news, crypto, and fundamentals ingestion (with cached fallbacks)
- Automated pattern execution for financial analysis, governance checks, and UI updates
- Telemetry dashboards for agent compliance, fallback events, and API health
- Workflow recording and replay through `WorkflowRecorder` / `WorkflowPlayer`

## Development Status (Oct 2025)

- Trinity 2.0 migration complete; legacy 19-agent architecture archived
- NetworkX integration with Graph utilities and backward-compatible APIs
- Streamlit UI with dashboards, chat interface, data integrity and API health tabs
- Comprehensive unit/integration tests plus consistency checks that guard against legacy regressions

## Roadmap Highlights

- Prune/generate the large `graph.json` to keep the repo lean
- Convert remaining print-based validation scripts to pytest modules
- Tighten type hints in `AgentRuntime` / adapters for stronger contracts
- Continue enhancing fallback transparency and API instrumentation

DawsOS is designed to be transparent, auditable, and extensible—a modern knowledge-graph intelligence layer for financial analysis.
