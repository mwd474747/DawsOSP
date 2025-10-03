# DawsOS Claude Agent Specialists

This directory contains specialized Claude .mdc agent configurations designed to deeply understand and maintain the DawsOS Trinity Architecture system.

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
- Understands all 46+ patterns across 6 categories
- Knows supported actions (knowledge_lookup, enriched_lookup, evaluate, etc.)
- Debugs variable substitution issues
- Validates against schema with linter
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
- Understands 7 enriched datasets and their structures
- Knows all graph helper methods (get_node, safe_query, etc.)
- Manages KnowledgeLoader caching
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
- Knows all 19 registered agents and their methods
- Understands AgentAdapter normalization
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
│  - Loads 46+ JSON patterns                               │
│  - Executes steps sequentially                           │
│  - Resolves variables                                    │
│  - Integrates enriched knowledge                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         AgentRuntime/AgentRegistry                       │
│  - 19 registered agents                                  │
│  - AgentAdapter normalization                            │
│  - Capability-based routing                              │
│  - Execution telemetry                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              KnowledgeGraph                              │
│  - Nodes, edges, patterns, forecasts                     │
│  - 7 enriched datasets (cached)                          │
│  - Graph queries and traversals                          │
│  - Persistence to storage/                               │
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
- Architecture: `dawsos/README.md`
- Trinity Flow: `dawsos/docs/TrinityExecutionFlow.md`
- Phase 3 Data: `dawsos/docs/PHASE3_DATA_MAP.md`
- Assessments: `dawsos/docs/archive/`

---

**These specialists work together to maintain the integrity, performance, and evolution of the DawsOS Trinity Architecture.**
