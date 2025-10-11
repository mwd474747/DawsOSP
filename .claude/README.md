# DawsOS Claude Agent Specialists

**System Version**: 3.0 (Trinity Architecture + Pydantic Validation)
**Grade**: D- → A (Remediation in Progress)
**Last Updated**: October 10, 2025

This directory contains specialized Claude agent configurations designed to deeply understand and maintain the DawsOS Trinity Architecture system.

## 🚨 CRITICAL CONTEXT (October 2025)

**System Status**: Economic data system 100% broken since Trinity 3.0 deployment
**Root Cause**: Zero integration tests, double normalization anti-pattern, 0% API validation
**Remediation**: 6-week Pydantic migration + comprehensive integration testing

**Key Documents**:
- [TRINITY_3.0_FORENSIC_FAILURE_ANALYSIS.md](../TRINITY_3.0_FORENSIC_FAILURE_ANALYSIS.md)
- [COMPREHENSIVE_REMEDIATION_PLAN.md](../COMPREHENSIVE_REMEDIATION_PLAN.md)
- [API_SYSTEMS_INTEGRATION_MATRIX.md](../API_SYSTEMS_INTEGRATION_MATRIX.md)

---

## Agent Specialists

### 🏛️ [Trinity Architect](trinity_architect.md)
**Primary Role**: Architecture governance and compliance

**Expertise**:
- Trinity execution flow validation
- Registry bypass detection
- Architectural compliance reviews
- Component interaction analysis
- Pattern-driven execution oversight

**When to use**:
- Reviewing code changes for Trinity compliance
- Understanding how components interact
- Validating execution paths
- Identifying architectural violations
- Planning new features within Trinity constraints

**Key Skills**:
- Traces execution through UniversalExecutor → Pattern → Registry → Graph
- Detects direct agent calls that bypass registry
- Suggests Trinity-compliant alternatives
- References specific files and line numbers
- Maintains architectural purity

---

### 🎯 [Pattern Specialist](pattern_specialist.md)
**Primary Role**: Pattern creation, validation, and optimization

**Expertise**:
- JSON pattern structure and schema
- Pattern execution flow
- Variable substitution and templating
- Enriched knowledge integration
- Pattern linting and debugging

**When to use**:
- Creating new patterns
- Debugging pattern execution failures
- Optimizing trigger matching
- Integrating enriched datasets
- Validating pattern library health

**Key Skills**:
- Understands all 45 patterns (0 errors) across 6 categories
- Knows supported actions (execute_through_registry, enriched_lookup, evaluate, etc.)
- Debugs variable substitution issues
- Validates against schema with linter (CI/CD integrated)
- Optimizes pattern performance

---

### 📚 [Knowledge Curator](knowledge_curator.md)
**Primary Role**: Knowledge graph and enriched dataset management

**Expertise**:
- Knowledge graph structure and relationships
- Node types and edge relationships
- Enriched dataset loading and validation
- Graph queries and traversals
- Data persistence and integrity

**When to use**:
- Designing graph structures
- Creating meaningful relationships
- Loading and validating enriched data
- Optimizing graph queries
- Ensuring data freshness and quality
- Tracking data lineage

**Key Skills**:
- Understands 26 enriched datasets (100% coverage) and their structures
- Knows all graph helper methods (get_node, safe_query, etc.)
- Manages KnowledgeLoader caching (30-min TTL)
- Tracks confidence and metadata
- Monitors graph health metrics

---

### 🤖 [Agent Orchestrator](agent_orchestrator.md)
**Primary Role**: Agent system architecture and coordination

**Expertise**:
- Agent registration and lifecycle
- Registry compliance and governance
- AgentAdapter interface design
- Capability-based routing
- Execution telemetry
- Multi-agent workflows

**When to use**:
- Creating new agents
- Implementing capability-based routing
- Tracking execution metrics
- Coordinating multi-agent workflows
- Detecting bypass violations
- Optimizing agent performance

**Key Skills**:
- Knows all 15 registered agents and their 50+ capabilities
- Understands AgentAdapter normalization
- Implements capability-based routing (Trinity 2.0)
- Tracks compliance metrics (last_success, failures, etc.)
- Detects registry bypasses
- Coordinates sequential and parallel execution

---

## How to Use These Agents

### 1. Architecture Review
Ask the **Trinity Architect** to review your code:
```
Review this code for Trinity compliance:
[paste code]
```

### 2. Pattern Development
Ask the **Pattern Specialist** to help create a pattern:
```
Help me create a pattern that:
1. Fetches company financials
2. Calculates DCF valuation
3. Stores result in graph
```

### 3. Knowledge Management
Ask the **Knowledge Curator** to design a graph structure:
```
How should I structure nodes and relationships for:
- Supply chain relationships
- Sector correlations
- Risk factors
```

### 4. Agent Development
Ask the **Agent Orchestrator** to design an agent:
```
Help me create an agent that:
- Fetches news sentiment
- Analyzes tone
- Stores in graph with confidence scores
```

## Team Coordination

For complex tasks, engage multiple specialists:

**Example: Building a New Analysis Workflow**

1. **Trinity Architect**: "Is this workflow Trinity-compliant?"
2. **Pattern Specialist**: "Create the JSON pattern structure"
3. **Agent Orchestrator**: "Which agents do we need?"
4. **Knowledge Curator**: "How should we store the results?"

## DawsOS System Overview

All specialists understand this core architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    User Request                          │
│              (UI, API, CLI, Pattern)                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              UniversalExecutor                           │
│  - Routes to meta_executor pattern                       │
│  - Tracks metrics and compliance                         │
│  - Handles fallback                                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              PatternEngine                               │
│  - Loads 45 JSON patterns (0 errors)                     │
│  - Executes steps sequentially                           │
│  - Resolves variables                                    │
│  - Integrates enriched knowledge via KnowledgeLoader     │
│  - Primary action: execute_through_registry              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         AgentRuntime/AgentRegistry                       │
│  - 15 registered agents with 50+ capabilities            │
│  - AgentAdapter normalization                            │
│  - Capability-based routing (Trinity 2.0)                │
│  - Execution telemetry & bypass detection                │
│  - AGENT_CAPABILITIES metadata                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              KnowledgeGraph                              │
│  - Nodes, edges, patterns, forecasts                     │
│  - 26 enriched datasets (100% coverage, 30-min TTL)      │
│  - Graph queries and traversals                          │
│  - Persistence to storage/ (auto-rotation)               │
└─────────────────────────────────────────────────────────┘
```

## Key Principles

All specialists enforce these Trinity principles:

1. **Single Entry Point**: All execution through UniversalExecutor
2. **Registry Compliance**: All agent calls through AgentRegistry
3. **Graph Storage**: All results persisted in KnowledgeGraph
4. **Centralized Knowledge**: All data via KnowledgeLoader
5. **Pattern-Driven**: Workflows defined in JSON patterns
6. **Telemetry**: All executions tracked with metrics

## Common Tasks

### Task: Add a New Feature
1. **Architect**: Design Trinity-compliant flow
2. **Pattern**: Create JSON pattern definition
3. **Agent**: Implement or reuse existing agents
4. **Curator**: Define graph storage structure

### Task: Debug an Execution Failure
1. **Architect**: Trace execution path
2. **Pattern**: Validate pattern structure
3. **Agent**: Check agent implementation
4. **Curator**: Verify graph connectivity

### Task: Optimize Performance
1. **Architect**: Identify bottlenecks in flow
2. **Pattern**: Optimize trigger matching
3. **Agent**: Improve agent efficiency
4. **Curator**: Add caching and indexes

## Validation Tools

All specialists can use these tools:

- **Pattern Linter**: `python scripts/lint_patterns.py`
- **Smoke Tests**: `python -m pytest dawsos/tests/validation/test_trinity_smoke.py`
- **Integration Tests**: `python -m pytest dawsos/tests/validation/test_integration.py`
- **Full Suite**: `python -m pytest dawsos/tests/validation/`

## Quick Reference

### File Locations
- Patterns: `dawsos/patterns/`
- Agents: `dawsos/agents/`
- Core: `dawsos/core/`
- Knowledge: `dawsos/storage/knowledge/`
- Tests: `dawsos/tests/`
- Scripts: `scripts/`

### Key Files
- Main entry: `dawsos/main.py`
- Universal Executor: `dawsos/core/universal_executor.py`
- Pattern Engine: `dawsos/core/pattern_engine.py`
- Agent Runtime: `dawsos/core/agent_runtime.py`
- Agent Adapter: `dawsos/core/agent_adapter.py`
- Knowledge Graph: `dawsos/core/knowledge_graph.py`
- Knowledge Loader: `dawsos/core/knowledge_loader.py`

### Documentation

**Essential Guides** (Trinity 2.0):
- [README.md](../README.md) - Quick start and system overview
- [CAPABILITY_ROUTING_GUIDE.md](../CAPABILITY_ROUTING_GUIDE.md) - Capability-based routing
- [CORE_INFRASTRUCTURE_STABILIZATION.md](../CORE_INFRASTRUCTURE_STABILIZATION.md) - Architecture upgrades
- [SYSTEM_STATUS.md](../SYSTEM_STATUS.md) - Current system state (A+ grade)
- [QUICK_WINS_COMPLETE.md](../QUICK_WINS_COMPLETE.md) - Final improvements summary

**Development Guides**:
- [docs/AgentDevelopmentGuide.md](../docs/AgentDevelopmentGuide.md) - Agent implementation and registration
- [docs/KnowledgeMaintenance.md](../docs/KnowledgeMaintenance.md) - Dataset formats and refresh
- [docs/DisasterRecovery.md](../docs/DisasterRecovery.md) - Backup and restore procedures

**Assessment Reports**:
- [FINAL_ROADMAP_COMPLIANCE.md](../FINAL_ROADMAP_COMPLIANCE.md) - Complete compliance (A grade)
- [docs/reports/](../docs/reports/) - Interim progress reports
- [dawsos/docs/archive/](../dawsos/docs/archive/) - Historical documentation

---

**These specialists work together to maintain the integrity, performance, and evolution of the DawsOS Trinity Architecture.**
