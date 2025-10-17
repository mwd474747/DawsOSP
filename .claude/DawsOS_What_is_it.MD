# What is DawsOS?

DawsOS is a pattern-driven financial intelligence platform built on the Trinity architecture. The runtime orchestrates 15 specialized agents through a centralized registry, executes 48 JSON patterns, and persists output to a NetworkX-backed knowledge graph for recall and auditing.

## Key Characteristics

- **Trinity Execution Path** – Requests flow through `UniversalExecutor → PatternEngine → AgentRegistry → Agent`, with bypass telemetry and strict-mode enforcement available when needed.
- **Knowledge Graph First** – All insights, datasets, and relationships land in a NetworkX graph managed by the persistence layer with automated backup rotation.
- **Agent Roster (15)** – Dedicated agents cover market data ingestion, macro analysis, governance, UI generation, code improvements, and investment research.
- **Pattern Library** – 48 JSON patterns span analysis, governance, workflows, UI automation, and meta orchestration with capability-based routing.
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
