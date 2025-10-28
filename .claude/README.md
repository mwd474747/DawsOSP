# Trinity 3.0 Specialist Agents

This directory contains specialist agent context files for AI assistants working on Trinity 3.0.

## Product Vision

**[DawsOS_What_is_it.MD](DawsOS_What_is_it.MD)** - Complete product vision and architecture overview

Trinity 3.0 is a Bloomberg-quality financial intelligence platform combining natural language understanding with pattern-driven analysis. **Read this file first** to understand the system.

## Specialist Agents

When making changes to Trinity 3.0, consult the relevant specialist:

### Core System Specialists

**[trinity_architect.md](trinity_architect.md)** - Architecture & Execution Flow
- UniversalExecutor → PatternEngine → AgentRuntime → KnowledgeGraph
- Validates architecture compliance
- Ensures proper execution flow
- **Consult before**: Architectural changes, new components, execution flow modifications

**[pattern_specialist.md](pattern_specialist.md)** - Pattern System Expert
- 12 JSON patterns (currently operational in backend/patterns/)
- Pattern creation & debugging
- Template field resolution
- **Consult before**: Creating patterns, debugging pattern execution, template issues

**[knowledge_curator.md](knowledge_curator.md)** - Knowledge Graph & Datasets
- 27 enriched datasets in storage/knowledge/
- NetworkX graph operations
- Knowledge loader caching (30-min TTL)
- **Consult before**: Adding datasets, modifying graph structure, knowledge queries

**[agent_orchestrator.md](agent_orchestrator.md)** - Agent System & Capabilities
- 9 agents registered (financial_analyst, macro_hound, data_harvester, claude, ratings, optimizer, reports, alerts, charts)
- 57 total capabilities (capability-based routing)
- Agent registration & runtime
- **Consult before**: Creating agents, adding capabilities, routing logic

## Usage Guidelines

1. **Read Product Vision First**: [DawsOS_What_is_it.MD](DawsOS_What_is_it.MD) describes Trinity 3.0 architecture and goals
2. **Consult Specialists**: Before making architectural, pattern, knowledge, or agent changes
3. **Follow Architecture**: UniversalExecutor → PatternEngine → AgentRuntime (no shortcuts)
4. **Update MASTER_TASK_LIST.md**: Single source of truth for all gaps/TODOs

## Critical Principles

- **Real Data Only**: Zero mock services, all data from OpenBB/FRED/FMP
- **Pattern-Driven**: All workflows defined in JSON patterns
- **Capability-Based Routing**: Use `execute_by_capability()` not direct agent calls
- **Bloomberg Aesthetic**: Professional UI, NO emojis
- **Full Transparency**: Entity extraction, intent confidence, execution time visible

## System Architecture (Trinity 3.0)

```
User Query → EnhancedChatProcessor → EntityExtraction
                 ↓
        UniversalExecutor
                 ↓
          PatternEngine (12 patterns)
                 ↓
     AgentRuntime (9 agents, 57 capabilities)
                 ↓
          KnowledgeGraph (27 datasets)
```

## Key Components

**Patterns** (12 total - verified 2025-10-27):
- Located in backend/patterns/
- All patterns operational and tested

**Agents** (9 total - verified 2025-10-27):
- All registered in backend/app/api/executor.py
- financial_analyst, macro_hound, data_harvester, claude, ratings, optimizer, reports, alerts, charts

**Knowledge** (27 datasets):
- Core (7), Investment Frameworks (4), Financial Data (4)
- Factor/Alt Data (4), Market Indicators (6), System Metadata (2)

**Data Sources**:
- OpenBB Platform (equity quotes, fundamentals, options)
- FRED API (GDP, CPI, unemployment, yield curve)
- FMP (insider trading, analyst ratings, earnings)

## Documentation Structure

- `/` - Core documentation (README.md, CLAUDE.md, ARCHITECTURE.md, etc.)
- `/.claude/` - Specialist agent context (this directory)
- See [../MASTER_TASK_LIST.md](../MASTER_TASK_LIST.md) for current status and todos

---

**These specialists work together to maintain the integrity, performance, and evolution of Trinity 3.0.**
