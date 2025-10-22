# What is DawsOS (Trinity 3.0 Architecture)?

> **NAMING NOTE**:
> - **DawsOS** = The application (what users see)
> - **Trinity 3.0** = The architecture version (how it works internally)
> - These are NOT separate systems - Trinity 3.0 is DawsOS's execution framework
>
> Like "React 18" is the framework version for a React app, "Trinity 3.0" is the framework version for DawsOS.

> **IMPORTANT**: This document contains ASPIRATIONAL descriptions alongside current state.
>
> **CURRENT STATE** (October 2025):
> - ✅ 16 patterns (economy: 6, smart: 7, workflows: 3)
> - ✅ 6 agents registered (financial_analyst, claude, data_harvester, forecast_dreamer, graph_mind, pattern_spotter)
> - ✅ 27 knowledge datasets
> - ✅ 103 capabilities
>
> See [../MASTER_TASK_LIST.md](../MASTER_TASK_LIST.md) for verified current state.

DawsOS is a pattern-driven financial intelligence platform built on the Trinity 3.0 architecture. The runtime orchestrates agents through a centralized registry, executes JSON patterns, and persists output to a NetworkX-backed knowledge graph for recall and auditing.

## Key Characteristics

- **Trinity Execution Path** – Requests flow through `UniversalExecutor → PatternEngine → AgentRegistry → Agent`, with bypass telemetry and strict-mode enforcement available when needed.
- **Knowledge Graph First** – All insights, datasets, and relationships land in a NetworkX graph managed by the persistence layer with automated backup rotation.
- **Agent Files (12)** – Current: 2 registered (financial_analyst, claude). Available: 10 more (data_harvester, forecast_dreamer, graph_mind, pattern_spotter, code_monkey, data_digester, governance_agent, relationship_hunter, workflow_player, base_agent)
- **Pattern Library (16)** – Current patterns span economy (6), smart analysis (7), and workflows (3) with capability-based routing.
- **Fallback Transparency** – Centralized tracking highlights when cached or stale data substitutes for live API responses, surfacing warnings in the UI and telemetry dashboards.

## Current Capabilities

- Natural-language requests via the conversational agent with pattern-driven follow-up analysis
- Market, economic, news, and fundamentals ingestion with cached fallbacks and enrichment
- Automated playbooks for company deep-dives, macro context, portfolio hygiene, and governance checks
- Streamlit dashboards for compliance, API health, and knowledge graph status
- Workflow capture and replay through `WorkflowRecorder` / `WorkflowPlayer`

## 2025 Development Snapshot

- Trinity 2.0 migration completed with capability routing, NetworkX graph adoption, and decomposed UI helpers
- Trinity 3.0 GDP refresh work introduced direct capability routing in the economic dashboard and expanded datasets to 27, while remediation continues on capability discovery and telemetry gaps
- Extensive documentation covers agents, patterns, remediation logs, and planned AG‑UI protocol integration for future streaming interfaces
- Test suites cover many validation scenarios, though several legacy CLI scripts and capability-routing tests still need conversion to automated pytest coverage

## Active Improvement Themes

- Finalize Trinity 3.0 fixes: ensure registry capability lookups and telemetry operate without manual workarounds
- Standardize external API integrations with Pydantic models and broader integration-test coverage
- Retire or consolidate overlapping remediation docs to keep onboarding material current and focused
- Harden security by moving secrets out of tracked `.env` defaults and tightening credential storage

DawsOS aims to give investors and builders a transparent, auditable intelligence layer—pulling live and curated data into guided playbooks that surface what’s moving, why it matters, and what to watch next.
