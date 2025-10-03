# Trinity Architecture Guide

**The Comprehensive Developer Reference for DawsOS**

**Version:** 1.0
**Last Updated:** October 3, 2025
**Status:** Production-Ready Core

---

## Table of Contents

1. [Overview](#overview)
2. [Execution Flow](#execution-flow)
3. [Core Components](#core-components)
4. [Agent System](#agent-system)
5. [Pattern System](#pattern-system)
6. [Compliance](#compliance)
7. [Knowledge System](#knowledge-system)
8. [Persistence](#persistence)
9. [Development Workflow](#development-workflow)
10. [Code Examples](#code-examples)
11. [Architecture Guarantees](#architecture-guarantees)
12. [Migration Guide](#migration-guide)

---

## Overview

### What is Trinity?

Trinity is DawsOS's core execution architecture that ensures **all operations flow through a unified, compliant path**. It replaces ad-hoc agent calls, direct orchestration, and legacy patterns with a single, pattern-driven execution model.

**Trinity = Pattern Engine + Agent Registry + Knowledge Graph**

### Why Trinity Exists

**Problems Trinity Solves:**
- ❌ **Before:** Agents called directly, bypassing central control
- ❌ **Before:** No consistent data storage or result tracking
- ❌ **Before:** Hard-coded logic scattered across codebase
- ❌ **Before:** No capability-based routing
- ❌ **Before:** Inconsistent error handling and validation

**Trinity Guarantees:**
- ✅ **Single Entry Point:** All execution through UniversalExecutor
- ✅ **Automatic Graph Storage:** Every result stored in KnowledgeGraph
- ✅ **Registry Compliance:** All agents wrapped in AgentAdapter
- ✅ **Pattern-Driven:** Logic defined in JSON, not Python code
- ✅ **Telemetry Built-In:** Track every execution, bypass, and failure

### Current Status

**Core Architecture:** ✅ **100% Complete**
**Pattern Library:** ✅ **45 Patterns, 100% Trinity-Compliant**
**Agent System:** ✅ **19 Agents, All Registry-Wrapped**
**Knowledge System:** ✅ **7 Enriched Datasets, Cached & Validated**
**Compliance:** ✅ **Automated Enforcement, 100% Pattern Compliance**

---

## Execution Flow

### The Trinity Path

```
┌─────────────────┐
│  UI / API       │
│  Request        │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  UniversalExecutor          │  ← Single Entry Point
│  (meta_executor pattern)    │
└─────────┬───────────────────┘
          │
          ▼
┌─────────────────────────────┐
│  PatternEngine              │  ← Load & Execute Patterns
│  - Pattern Matching         │
│  - Step Execution           │
│  - Variable Substitution    │
└─────────┬───────────────────┘
          │
          ▼
┌─────────────────────────────┐
│  AgentRuntime               │  ← Registry-Based Routing
│  → AgentRegistry            │
│    → AgentAdapter           │
└─────────┬───────────────────┘
          │
          ▼
┌─────────────────────────────┐
│  Agent Execution            │  ← Wrapped Agent Call
│  (Financial, Macro, etc.)   │
└─────────┬───────────────────┘
          │
          ▼
┌─────────────────────────────┐
│  KnowledgeGraph             │  ← Auto-Store Results
│  + Persistence              │
└─────────────────────────────┘
```

### Request Journey

1. **Entry:** User submits request via UI/API
2. **UniversalExecutor:** Routes to `meta_executor` pattern
3. **PatternEngine:** Matches pattern, resolves variables
4. **AgentRegistry:** Routes to appropriate agent via adapter
5. **Agent:** Executes logic, returns result
6. **AgentAdapter:** Normalizes response, auto-stores in graph
7. **Response:** Formatted result returned to user

### Key Guarantees

- **No Bypasses:** Direct agent access logged/blocked
- **Automatic Storage:** All results persisted in KnowledgeGraph
- **Consistent Interface:** All agents return standardized dict
- **Telemetry:** Every execution tracked with metadata
- **Fallback:** Graceful degradation if patterns missing

---

## Core Components

### 1. UniversalExecutor

**File:** [dawsos/core/universal_executor.py](../core/universal_executor.py)

**Purpose:** Single entry point for ALL DawsOS execution.

**Key Methods:**
```python
def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
    """Universal execution entry point"""
    # 1. Prepare context with Trinity components
    context = self._prepare_context(request)

    # 2. Route through meta_executor pattern
    pattern = self.pattern_engine.get_pattern('meta_executor')
    result = self.pattern_engine.execute_pattern(pattern, context)

    # 3. Store execution result in graph
    self._store_execution_result(request, result)

    return result
```

**Features:**
- ✅ Loads meta-patterns for self-healing architecture
- ✅ Tracks execution metrics (total, routed, legacy, failures)
- ✅ Injects Trinity components into context
- ✅ Attempts recovery via `architecture_validator` on failure
- ✅ Fallback execution when meta_executor unavailable

**Usage:**
```python
from core.universal_executor import get_executor

executor = get_executor(graph, registry, runtime)
result = executor.execute({'user_input': 'Analyze AAPL'})
```

---

### 2. PatternEngine

**File:** [dawsos/core/pattern_engine.py](../core/pattern_engine.py)

**Purpose:** Load and execute JSON-defined patterns.

**Key Methods:**
```python
def find_pattern(self, user_input: str) -> Optional[Dict]:
    """Match user input to pattern triggers"""

def execute_pattern(self, pattern: Dict, context: Dict) -> Dict:
    """Execute pattern steps sequentially"""

def execute_action(self, action: str, params: Dict, context: Dict, outputs: Dict) -> Dict:
    """Handle special actions (enriched_lookup, calculate, etc.)"""
```

**Supported Actions:**
- `execute_through_registry` - Route to agent (Trinity compliant)
- `enriched_lookup` - Load enriched knowledge datasets
- `knowledge_lookup` - Query KnowledgeGraph
- `calculate` - Perform calculations (DCF, ROIC, etc.)
- `evaluate` - Score moats, cycles, criteria
- `synthesize` - Combine multiple scores
- `fetch_financials` - Get financial data via data_harvester
- `dcf_analysis` - DCF valuation via financial_analyst
- `calculate_confidence` - Dynamic confidence scoring

**Variable Substitution:**
```json
{
  "params": {
    "symbol": "{SYMBOL}",           // Extract from user_input
    "request": "{user_input}",       // Direct context variable
    "price": "{quote_data.price}"    // Nested output reference
  }
}
```

**Pattern Structure:**
```json
{
  "id": "pattern_name",
  "name": "Human-Readable Name",
  "version": "1.0",
  "last_updated": "2025-10-02",
  "triggers": ["keyword1", "keyword2"],
  "steps": [
    {
      "action": "execute_through_registry",
      "params": {
        "agent": "data_harvester",
        "context": {"request": "{user_input}"}
      },
      "outputs": "quote_data"
    }
  ],
  "response_template": "Price: ${quote_data.price}"
}
```

---

### 3. AgentRuntime

**File:** [dawsos/core/agent_runtime.py](../core/agent_runtime.py)

**Purpose:** Execute and coordinate agents with compliance enforcement.

**Key Methods:**
```python
def register_agent(self, name: str, agent: Any, capabilities: Optional[Dict] = None):
    """Register agent with runtime and registry"""

def execute(self, agent_name: str, context: Dict) -> Dict:
    """Execute agent through adapter with tracking"""

def exec_via_registry(self, agent_name: str, context: Dict) -> Dict:
    """Sanctioned path for agent execution (recommended)"""
```

**Trinity Compliance Features:**

**Access Guardrails:**
```python
@property
def agents(self) -> MappingProxyType:
    """
    DEPRECATED: Direct agent access bypasses Trinity.
    Logs warnings and raises errors in strict mode.
    """
    if self._strict_mode:
        raise RuntimeError("Direct access prohibited in TRINITY_STRICT_MODE")
    else:
        self.logger.warning("Use exec_via_registry() instead")

    return MappingProxyType(self._agents)
```

**Strict Mode:**
```bash
export TRINITY_STRICT_MODE=true
```

**Capability-Based Routing:**
```python
result = runtime.execute_by_capability('fetch_data', context)
```

---

### 4. AgentRegistry & AgentAdapter

**File:** [dawsos/core/agent_adapter.py](../core/agent_adapter.py)

**Purpose:** Wrap agents for consistent interface and automatic graph storage.

**AgentAdapter:**
```python
class AgentAdapter:
    def execute(self, context: Dict) -> Dict:
        """Execute agent with method resolution and auto-storage"""
        # Try methods in priority: process, think, analyze, interpret, harvest
        result = method(adapted_params)

        # Add metadata
        result['agent'] = agent.__class__.__name__
        result['timestamp'] = datetime.now().isoformat()

        # AUTO-STORE IN GRAPH
        if hasattr(agent, 'graph') and agent.graph:
            node_id = agent.graph.add_node('agent_result', result)
            result['graph_stored'] = True

        return result
```

**AgentRegistry:**
```python
class AgentRegistry:
    def execute_with_tracking(self, agent_name: str, context: Dict) -> Dict:
        """Execute with telemetry tracking"""
        result = self.agents[agent_name].execute(context)

        # Track metrics
        self.execution_metrics[agent_name]['total_executions'] += 1
        if result.get('graph_stored'):
            self.execution_metrics[agent_name]['last_success'] = now()

        return result
```

**Telemetry:**
- `total_executions` - Count of agent calls
- `graph_stored` - Count of successful graph writes
- `last_success` / `last_failure` - Timestamps
- `failure_reasons` - Last 10 error messages
- `capability_tags` - Agent capabilities

---

### 5. KnowledgeGraph

**File:** [dawsos/core/knowledge_graph.py](../core/knowledge_graph.py)

**Purpose:** Central persistence layer for all knowledge.

**Key Methods:**
```python
def add_node(self, node_type: str, data: dict, node_id: str = None) -> str:
    """Add knowledge node"""

def connect(self, from_id: str, to_id: str, relationship: str, strength: float = 1.0) -> bool:
    """Create edge between nodes"""

def trace_connections(self, start_node: str, max_depth: int = 3) -> List[List[Dict]]:
    """Trace all paths from node"""

def forecast(self, target_node: str, horizon: str = '1d') -> dict:
    """Forecast using all connections"""

def query(self, pattern: dict) -> List[str]:
    """Query nodes matching pattern"""
```

**Helper Methods:**
```python
# Safe access
node = graph.get_node(node_id)
nodes = graph.get_nodes_by_type('stock_analysis')
data = graph.get_node_data(node_id, 'price', default=0)

# Connections
connected = graph.get_connected_nodes(node_id, direction='out')
exists = graph.has_edge(from_id, to_id, 'correlates')
edge = graph.get_edge(from_id, to_id)

# Safe querying
results = graph.safe_query({'type': 'forecast'}, default=[])
```

**Persistence:**
```python
graph.save('storage/graph.json')
graph.load('storage/graph.json')
```

---

## Agent System

### Registered Agents (19)

**Core Agents (8):**
- `claude` - Natural language processing (LLM)
- `data_harvester` - External data (FRED, FMP, News, Crypto)
- `data_digester` - Raw data → graph nodes
- `graph_mind` - Graph operations
- `pattern_spotter` - Pattern detection
- `relationship_hunter` - Correlation analysis
- `forecast_dreamer` - Predictions
- `code_monkey` - Self-modification

**Specialized Agents (5):**
- `equity_agent` - Stock analysis
- `macro_agent` - Economic analysis
- `risk_agent` - Risk assessment
- `financial_analyst` - DCF, ROIC, FCF, owner earnings
- `governance_agent` - Compliance & governance

**Utility Agents (6):**
- `structure_bot` - Code organization
- `refactor_elf` - Code optimization
- `workflow_recorder` - Learning patterns
- `workflow_player` - Automation
- `ui_generator` - Dynamic UI creation
- `base_agent` - Abstract base class

### Agent Registration

**With Explicit Capabilities:**
```python
from core.agent_capabilities import AGENT_CAPABILITIES

runtime.register_agent(
    'financial_analyst',
    FinancialAnalyst(graph),
    capabilities=AGENT_CAPABILITIES['financial_analyst']
)
```

**Capabilities Schema:**
```python
AGENT_CAPABILITIES = {
    'financial_analyst': {
        'can_calculate_dcf': True,
        'can_calculate_roic': True,
        'can_calculate_fcf': True,
        'can_calculate_owner_earnings': True,
        'can_analyze_moat': True,
        'can_project_cash_flows': True,
        'can_calculate_wacc': True,
        'can_value_companies': True,
        'can_analyze_financials': True,
        'requires_financial_data': True,
        'provides_valuations': True
    }
}
```

**File:** [dawsos/core/agent_capabilities.py](../core/agent_capabilities.py)

### Agent Execution

**Trinity-Compliant (Recommended):**
```python
# Through runtime
result = runtime.exec_via_registry('financial_analyst', {
    'symbol': 'AAPL',
    'analysis_type': 'dcf'
})

# Through executor
result = executor.execute({
    'agent': 'financial_analyst',
    'context': {'symbol': 'AAPL'}
})
```

**Anti-Pattern (Logged/Blocked):**
```python
# WRONG - Bypasses registry
agent = runtime.agents['financial_analyst']
result = agent.analyze('AAPL')
```

---

## Pattern System

### Pattern Structure

**Minimal Pattern:**
```json
{
  "id": "pattern_id",
  "name": "Pattern Name",
  "version": "1.0",
  "last_updated": "2025-10-02",
  "triggers": ["keyword"],
  "steps": [
    {
      "action": "execute_through_registry",
      "params": {
        "agent": "agent_name",
        "context": {"key": "value"}
      }
    }
  ]
}
```

**Full Pattern Example:**
```json
{
  "id": "stock_analysis",
  "name": "Stock Analysis Pattern",
  "description": "Comprehensive stock analysis using multiple agents",
  "category": "analysis",
  "version": "1.0",
  "last_updated": "2025-10-02",
  "triggers": [
    "analyze",
    "stock analysis",
    "company analysis"
  ],
  "entities": ["AAPL", "MSFT", "GOOGL"],
  "steps": [
    {
      "description": "Fetch current stock price",
      "action": "execute_through_registry",
      "params": {
        "agent": "data_harvester",
        "context": {
          "request": "stock price for {SYMBOL}"
        }
      },
      "outputs": "price_data"
    },
    {
      "description": "Analyze fundamentals",
      "action": "execute_through_registry",
      "params": {
        "agent": "financial_analyst",
        "context": {
          "symbol": "{SYMBOL}",
          "analysis_type": "fundamental"
        }
      },
      "outputs": "fundamental_analysis"
    },
    {
      "description": "Calculate confidence",
      "action": "calculate_confidence",
      "params": {
        "symbol": "{SYMBOL}",
        "analysis_type": "stock_analysis",
        "factors": [
          "price_data",
          "fundamental_analysis"
        ]
      },
      "outputs": "confidence_score"
    }
  ],
  "response_template": "**{SYMBOL} Analysis**\n\nPrice: ${price_data.price}\nConfidence: {confidence_score.confidence}%\n\n{fundamental_analysis.summary}",
  "response_type": "analysis"
}
```

### Pattern Categories

**45 Patterns across 8 categories:**

1. **Actions (5):** add_to_graph, add_to_portfolio, create_alert, export_data, generate_forecast
2. **Analysis (11):** buffett_checklist, dcf_valuation, dalio_cycle, earnings_analysis, fundamental_analysis, moat_analyzer, owner_earnings, portfolio_analysis, risk_assessment, sentiment_analysis, technical_analysis
3. **Queries (6):** company_analysis, correlation_finder, macro_analysis, market_regime, sector_performance, stock_price
4. **Workflows (4):** deep_dive, morning_briefing, opportunity_scan, portfolio_review
5. **UI (6):** alert_manager, confidence_display, dashboard_generator, dashboard_update, help_guide, watchlist_update
6. **System/Meta (5):** architecture_validator, execution_router, legacy_migrator, meta_executor, self_improve
7. **Governance (6):** audit_everything, compliance_audit, cost_optimization, data_quality_check, governance_template, policy_validation
8. **Root (2):** comprehensive_analysis, sector_rotation

### Variable Substitution

**Context Variables:**
```json
{
  "params": {
    "user_input": "{user_input}",
    "timestamp": "{timestamp}",
    "symbol": "{SYMBOL}"
  }
}
```

**Output References:**
```json
{
  "params": {
    "price": "{price_data.price}",
    "analysis": "{fundamental_analysis}"
  }
}
```

**Symbol Extraction:**
- Automatic extraction from user input
- Company name → ticker symbol mapping
- Alias resolution (e.g., "Apple" → "AAPL")
- Case-insensitive matching

**File:** [dawsos/storage/knowledge/company_database.json](../storage/knowledge/company_database.json)

### Pattern Execution

**Load Pattern:**
```python
pattern = pattern_engine.get_pattern('dcf_valuation')
```

**Execute Pattern:**
```python
context = {
    'user_input': 'DCF analysis for Apple',
    'symbol': 'AAPL'
}
result = pattern_engine.execute_pattern(pattern, context)
```

**Pattern Matching:**
```python
pattern = pattern_engine.find_pattern('Analyze AAPL stock')
# Returns pattern with highest trigger match score
```

---

## Compliance

### What is Compliance?

**Trinity Compliance** = All execution through registry, all results stored in graph.

**Compliant Pattern:**
```json
{
  "action": "execute_through_registry",
  "params": {
    "agent": "financial_analyst",
    "context": {"symbol": "AAPL"}
  }
}
```

**Non-Compliant Pattern (WRONG):**
```json
{
  "agent": "financial_analyst",
  "action": "analyze",
  "params": {"symbol": "AAPL"}
}
```

### Enforcement Mechanisms

#### 1. Runtime Warnings

**Direct Agent Access Detection:**
```python
# This triggers warning
agent = runtime.agents['claude']

# Warning logged:
# "BYPASS WARNING: Direct .agents access from file.py:123. Use exec_via_registry() instead"
```

**Bypass Tracking:**
```python
warnings = runtime.agent_registry.get_bypass_warnings(limit=50)
# Returns list of bypass incidents with caller info
```

#### 2. Strict Mode

**Enable:**
```bash
export TRINITY_STRICT_MODE=true
```

**Effect:**
- Direct agent access raises `RuntimeError`
- Warnings become errors
- Enforces 100% compliance

**Example:**
```python
# In strict mode, this raises error:
agent = runtime.agents['claude']
# RuntimeError: Direct access prohibited in TRINITY_STRICT_MODE
```

#### 3. ComplianceChecker

**File:** [dawsos/core/compliance_checker.py](../core/compliance_checker.py)

**Validation Rules:**

| Rule | Severity | Description |
|------|----------|-------------|
| Missing `id` | Error | Pattern must have unique identifier |
| Missing `version` | Warning | Pattern should have version tracking |
| Missing `last_updated` | Warning | Pattern should have update timestamp |
| Direct agent reference | Error | Must use `execute_through_registry` |
| Invalid agent name | Error | Agent must exist in registry |
| Legacy `action='agent:name'` | Warning | Should migrate to new format |

**Usage:**
```python
from core.compliance_checker import get_compliance_checker

checker = get_compliance_checker(agent_registry)

# Validate pattern
result = checker.check_pattern(pattern)
if not result['compliant']:
    for violation in result['violations']:
        print(violation['message'])

# Generate report
report = checker.get_compliance_report()
print(f"Compliance Rate: {report['overall']['pattern_compliance_rate']}%")
```

**Report Structure:**
```json
{
  "overall": {
    "pattern_compliance_rate": 100.0,
    "agent_access_compliance_rate": 95.0,
    "total_patterns_checked": 45,
    "compliant_patterns": 45
  },
  "violations": {
    "total": 0,
    "by_type": {},
    "by_severity": {"error": 0, "warning": 0}
  },
  "recommendations": [
    "All systems Trinity-compliant!"
  ]
}
```

#### 4. AST Checking

**Static Analysis Script:**
```python
# File: scripts/check_compliance.py

import ast

class AgentAccessChecker(ast.NodeVisitor):
    def visit_Subscript(self, node):
        if isinstance(node.value, ast.Attribute):
            if node.value.attr == 'agents':
                # Found: runtime.agents[...]
                self.violations.append({
                    'line': node.lineno,
                    'message': 'Use runtime.exec_via_registry() instead'
                })
```

**Run:**
```bash
python scripts/check_compliance.py
```

### Integration Points

**PatternEngine:**
```python
def execute_pattern(self, pattern, context):
    # Validate before execution
    compliance = self.compliance_checker.check_pattern(pattern)
    if not compliance['compliant']:
        self.logger.warning(f"Pattern violations: {compliance['violations']}")

    # Execute pattern...
```

**Dashboard:**
```python
# File: dawsos/ui/governance_tab.py

report = checker.get_compliance_report()
st.metric("Pattern Compliance", f"{report['overall']['pattern_compliance_rate']}%")
```

---

## Knowledge System

### KnowledgeLoader

**File:** [dawsos/core/knowledge_loader.py](../core/knowledge_loader.py)

**Purpose:** Centralized, cached access to enriched datasets.

**Features:**
- ✅ 30-minute TTL caching
- ✅ Automatic validation on load
- ✅ Singleton pattern
- ✅ Stale dataset detection
- ✅ Section-based access with dot notation

**Registered Datasets (7):**
```python
datasets = {
    'sector_performance': 'sector_performance.json',
    'economic_cycles': 'economic_cycles.json',
    'sp500_companies': 'sp500_companies.json',
    'sector_correlations': 'sector_correlations.json',
    'relationships': 'relationship_mappings.json',
    'ui_configurations': 'ui_configurations.json',
    'company_database': 'company_database.json'
}
```

**Usage:**
```python
from core.knowledge_loader import get_knowledge_loader

loader = get_knowledge_loader()

# Load dataset
data = loader.get_dataset('sector_performance')

# Load specific section
tech_data = loader.get_dataset_section('sp500_companies', 'Technology.tier1')

# Force reload
data = loader.get_dataset('economic_cycles', force_reload=True)

# List datasets
available = loader.list_datasets()

# Get metadata
info = loader.get_dataset_info('sector_performance')
# Returns: exists, cached, cache_valid, file_size, modified, last_loaded, cache_age_seconds

# Reload all
results = loader.reload_all()
# Returns: {'sector_performance': True, 'economic_cycles': True, ...}

# Check staleness
stale = loader.get_stale_datasets()
# Returns: ['sector_performance', ...] (cached > 30 min ago)
```

**Validation:**
- Schema checks for each dataset type
- Ensures required fields present
- Logs validation errors

**Pattern Integration:**
```python
# In PatternEngine
def execute_action(self, action, params, context, outputs):
    if action == "enriched_lookup":
        data_type = params.get('data_type')
        enriched_data = self.knowledge_loader.get_dataset(data_type)
        return {'data': enriched_data, 'found': True}
```

### Enriched Datasets

**1. sector_performance.json**
- Sector performance by economic cycle
- Historical returns
- Volatility metrics
- Rotation strategies

**2. economic_cycles.json**
- Current economic assessment
- Historical phases
- Indicators mapping
- Cycle transitions

**3. sp500_companies.json**
- S&P 500 companies by sector
- Tiered by market cap
- Industry classifications

**4. sector_correlations.json**
- Correlation matrix
- Relationship strengths
- Time-series correlations

**5. relationship_mappings.json**
- Supply chain relationships
- Competitive dynamics
- Economic dependencies

**6. ui_configurations.json**
- Dashboard layouts
- Widget configurations
- Display preferences

**7. company_database.json**
- Company ticker symbols
- Aliases (e.g., "Apple" → "AAPL")
- Name mappings

**Location:** [dawsos/storage/knowledge/](../storage/knowledge/)

---

## Persistence

### PersistenceManager

**File:** [dawsos/core/persistence.py](../core/persistence.py)

**Purpose:** Manage graph saving/loading with backup rotation and integrity validation.

**Key Features:**
- ✅ Automatic timestamped backups
- ✅ SHA-256 checksum validation
- ✅ 30-day backup rotation (configurable)
- ✅ Metadata tracking (timestamp, node/edge counts)
- ✅ Integrity verification
- ✅ Automatic recovery from corruption

### Backup Management

**Save with Backup:**
```python
from core.persistence import PersistenceManager

pm = PersistenceManager()
result = pm.save_graph_with_backup(graph)

# Returns:
{
    'success': True,
    'graph_path': 'storage/graph.json',
    'backup_path': 'storage/backups/graph_20251003_143022.json',
    'checksum': 'a7f3b8c2...',
    'metadata': {
        'timestamp': '2025-10-03T14:30:22',
        'node_count': 1250,
        'edge_count': 3400
    },
    'backups_removed': 2
}
```

**List Backups:**
```python
backups = pm.list_backups()
for backup in backups:
    print(f"{backup['filename']}: {backup['size']} bytes")
    print(f"  Nodes: {backup['metadata']['node_count']}")
    print(f"  Edges: {backup['metadata']['edge_count']}")
```

**Restore from Backup:**
```python
stats = pm.restore_from_backup('storage/backups/graph_20251003_143022.json', graph)
# Returns:
{
    'success': True,
    'nodes_restored': 1250,
    'edges_restored': 3400,
    'nodes_changed': 50,
    'edges_changed': 120
}
```

### Integrity Validation

**Verify Checksum:**
```python
result = pm.verify_integrity('storage/graph.json')
if result['valid']:
    print(f"Checksum verified: {result['checksum']}")
else:
    print(f"Corruption detected: {result['error']}")
```

**Load with Recovery:**
```python
result = pm.load_graph_with_recovery(graph)

# If primary graph corrupted, automatically recovers from most recent valid backup
if result['source'] == 'backup_recovery':
    print(f"Recovered from {result['backup_used']}")
```

### Backup Rotation

**Automatic Rotation:**
- Runs on every `save_graph_with_backup()`
- Removes backups older than retention period (default: 30 days)
- Preserves metadata files

**Manual Rotation:**
```python
removed = pm._rotate_backups(retention_days=7)
print(f"Removed {removed} old backups")
```

### Metadata Structure

**Saved with every backup:**
```json
{
  "timestamp": "2025-10-03T14:30:22.123456",
  "checksum": "a7f3b8c2d4e5f6...",
  "node_count": 1250,
  "edge_count": 3400,
  "graph_version": "1.0",
  "saved_by": "DawsOS PersistenceManager"
}
```

### Disaster Recovery

**Scenario 1: Corrupted Graph**
```python
# Automatic recovery
result = pm.load_graph_with_recovery(graph)
if not result['success']:
    print(f"Recovery failed: {result['error']}")
```

**Scenario 2: Manual Restore**
```python
# List available backups
backups = pm.list_backups()

# Choose backup to restore
backup_path = backups[0]['path']

# Verify integrity
if pm.verify_integrity(backup_path)['valid']:
    pm.restore_from_backup(backup_path, graph)
```

**Scenario 3: Pattern Migration Rollback**
```bash
# Backup patterns before migration
cp -r dawsos/patterns storage/backups/patterns_pre_migration

# If migration fails, rollback
rm -rf dawsos/patterns
cp -r storage/backups/patterns_pre_migration dawsos/patterns
```

---

## Development Workflow

### How to Add a New Agent

**1. Create Agent Class:**
```python
# File: dawsos/agents/my_agent.py

from agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, graph):
        super().__init__("my_agent")
        self.graph = graph

    def process(self, context):
        # Agent logic here
        result = {
            'success': True,
            'data': 'processed data'
        }

        # Store in graph (auto-handled by AgentAdapter, but can be explicit)
        node_id = self.store_result(result, context)
        result['node_id'] = node_id

        return result
```

**2. Define Capabilities:**
```python
# File: dawsos/core/agent_capabilities.py

AGENT_CAPABILITIES['my_agent'] = {
    'can_process_data': True,
    'can_transform': True,
    'requires_graph': True,
    'provides_insights': True,
    'category': 'data',
    'priority': 'medium'
}
```

**3. Register Agent:**
```python
# File: dawsos/main.py

from agents.my_agent import MyAgent
from core.agent_capabilities import AGENT_CAPABILITIES

runtime.register_agent(
    'my_agent',
    MyAgent(st.session_state.graph),
    capabilities=AGENT_CAPABILITIES['my_agent']
)
```

**4. Test Agent:**
```python
# Via runtime
result = runtime.exec_via_registry('my_agent', {'data': 'test'})

# Via pattern
pattern = {
    "steps": [{
        "action": "execute_through_registry",
        "params": {
            "agent": "my_agent",
            "context": {"data": "test"}
        }
    }]
}
result = pattern_engine.execute_pattern(pattern, {})
```

### How to Create a Pattern

**1. Create Pattern File:**
```json
// File: dawsos/patterns/analysis/my_analysis.json

{
  "id": "my_analysis",
  "name": "My Analysis Pattern",
  "description": "Custom analysis using my_agent",
  "category": "analysis",
  "version": "1.0",
  "last_updated": "2025-10-03",
  "triggers": [
    "my analysis",
    "custom analysis"
  ],
  "steps": [
    {
      "description": "Fetch data",
      "action": "execute_through_registry",
      "params": {
        "agent": "data_harvester",
        "context": {
          "request": "{user_input}"
        }
      },
      "outputs": "raw_data"
    },
    {
      "description": "Process with my_agent",
      "action": "execute_through_registry",
      "params": {
        "agent": "my_agent",
        "context": {
          "data": "{raw_data}"
        }
      },
      "outputs": "processed_data"
    }
  ],
  "response_template": "Analysis Result: {processed_data.result}"
}
```

**2. Test Pattern:**
```python
# Reload patterns
pattern_engine.reload_patterns()

# Find pattern
pattern = pattern_engine.find_pattern('my analysis for AAPL')

# Execute pattern
result = pattern_engine.execute_pattern(pattern, {'user_input': 'my analysis for AAPL'})
```

**3. Validate Compliance:**
```python
from core.compliance_checker import get_compliance_checker

checker = get_compliance_checker(runtime.agent_registry)
result = checker.check_pattern(pattern)

if result['compliant']:
    print("✅ Pattern is Trinity-compliant")
else:
    for violation in result['violations']:
        print(f"❌ {violation['message']}")
```

### How to Test Compliance

**1. Run Compliance Checker:**
```bash
cd dawsos
python tests/test_compliance.py
```

**2. Analyze Existing Patterns:**
```bash
python examples/analyze_existing_patterns.py
```

**3. Check Specific Pattern:**
```python
pattern = pattern_engine.get_pattern('my_pattern')
result = checker.check_pattern(pattern)
```

**4. Generate Report:**
```python
report = checker.get_compliance_report()
checker.export_report('compliance_report.json')
```

**5. Enable Strict Mode:**
```bash
export TRINITY_STRICT_MODE=true
streamlit run dawsos/main.py
```

---

## Code Examples

### Complete Request Flow

```python
# 1. Initialize Trinity components
from core.knowledge_graph import KnowledgeGraph
from core.agent_runtime import AgentRuntime
from core.universal_executor import get_executor
from core.agent_capabilities import AGENT_CAPABILITIES

# Create graph
graph = KnowledgeGraph()

# Create runtime
runtime = AgentRuntime()

# Register agents with capabilities
from agents.financial_analyst import FinancialAnalyst
runtime.register_agent(
    'financial_analyst',
    FinancialAnalyst(graph),
    capabilities=AGENT_CAPABILITIES['financial_analyst']
)

# Create executor
executor = get_executor(graph, runtime.agent_registry, runtime)

# 2. Execute request
request = {
    'user_input': 'DCF analysis for Apple',
    'type': 'analysis'
}

result = executor.execute(request)

# 3. Result is automatically stored in graph
print(f"Node ID: {result.get('node_id')}")
print(f"Graph Stored: {result.get('graph_stored')}")
```

### Pattern Execution with Variable Substitution

```python
# Load pattern
pattern = pattern_engine.get_pattern('dcf_valuation')

# Execute with context
context = {
    'user_input': 'DCF for AAPL',
    'symbol': 'AAPL',
    'growth_assumption': 'conservative'
}

result = pattern_engine.execute_pattern(pattern, context)

# Variables substituted:
# - {symbol} → 'AAPL'
# - {SYMBOL} → 'AAPL' (extracted from user_input)
# - {growth_assumption} → 'conservative'
# - {dcf_analysis.intrinsic_value} → result from step 2

print(result['formatted_response'])
```

### Capability-Based Routing

```python
# Register agent with capabilities
runtime.register_agent(
    'data_harvester',
    DataHarvester(graph),
    capabilities={
        'can_fetch_data': True,
        'can_fetch_stock_quotes': True,
        'can_fetch_economic_data': True,
        'provides_market_data': True
    }
)

# Execute by capability
result = runtime.execute_by_capability('can_fetch_stock_quotes', {
    'symbol': 'AAPL'
})
```

### Compliance Monitoring

```python
# Get compliance metrics
metrics = runtime.get_compliance_metrics()

print(f"Overall Compliance: {metrics['overall_compliance']:.1f}%")
print(f"Total Executions: {metrics['total_executions']}")
print(f"Graph Storage Rate: {metrics['total_stored'] / metrics['total_executions']:.1%}")

# Per-agent metrics
for agent, stats in metrics['agents'].items():
    print(f"{agent}: {stats['compliance_rate']:.1f}% ({stats['executions']} executions)")

# Check bypass warnings
warnings = runtime.agent_registry.get_bypass_warnings(limit=10)
for warning in warnings:
    print(f"⚠️ {warning['caller']} bypassed registry at {warning['timestamp']}")
```

### Knowledge Loader Integration

```python
from core.knowledge_loader import get_knowledge_loader

loader = get_knowledge_loader()

# Load enriched data in pattern
data = loader.get_dataset('sector_performance')

# Use in pattern action
def execute_action(self, action, params, context, outputs):
    if action == "enriched_lookup":
        data_type = params.get('data_type')
        section = params.get('section')

        data = self.knowledge_loader.get_dataset(data_type)
        if section:
            result = self.extract_enriched_section(data, section, params)
            return result

        return {'data': data, 'found': True}
```

### Persistence with Recovery

```python
from core.persistence import PersistenceManager

pm = PersistenceManager()

# Save with automatic backup
result = pm.save_graph_with_backup(graph)
print(f"Saved to {result['graph_path']}")
print(f"Backup at {result['backup_path']}")
print(f"Checksum: {result['checksum']}")

# Load with automatic recovery
load_result = pm.load_graph_with_recovery(graph)

if load_result['source'] == 'backup_recovery':
    print(f"⚠️ Primary graph corrupted, recovered from {load_result['backup_used']}")
else:
    print(f"✅ Loaded from primary graph")

# List backups
backups = pm.list_backups()
print(f"Available backups: {len(backups)}")
for backup in backups[:5]:
    print(f"  {backup['filename']} - {backup['metadata']['node_count']} nodes")
```

---

## Architecture Guarantees

### Trinity Guarantees

1. ✅ **Single Entry Point:** ALL execution through `UniversalExecutor.execute()`
2. ✅ **Pattern-Driven:** Logic defined in JSON patterns, not Python code
3. ✅ **Registry-Based:** All agents wrapped in `AgentAdapter`, routed via `AgentRegistry`
4. ✅ **Automatic Storage:** Every agent result stored in `KnowledgeGraph`
5. ✅ **Compliance Enforcement:** Direct agent access logged/blocked, patterns validated
6. ✅ **Telemetry Built-In:** Track executions, bypasses, failures, graph storage
7. ✅ **Graceful Fallback:** Fallback execution if meta patterns unavailable
8. ✅ **Centralized Knowledge:** All datasets loaded via `KnowledgeLoader` with caching
9. ✅ **Persistence Safety:** Checksums, backups, rotation, integrity verification
10. ✅ **Self-Healing:** Automatic recovery from graph corruption

### What Trinity Prevents

❌ **Direct Agent Access**
```python
# WRONG - Bypasses Trinity
agent = runtime.agents['claude']
result = agent.think(context)
```

❌ **Hard-Coded Logic**
```python
# WRONG - Logic should be in pattern
def analyze_stock(symbol):
    price = get_price(symbol)
    analysis = analyze_fundamentals(symbol)
    return combine(price, analysis)
```

❌ **Inconsistent Results**
```python
# WRONG - Returns raw string instead of dict
def process(self, context):
    return "result string"

# CORRECT - AgentAdapter normalizes
def process(self, context):
    return {'result': 'result string'}
```

❌ **Missing Graph Storage**
```python
# WRONG - Result not stored
result = agent.analyze(symbol)
return result

# CORRECT - AgentAdapter auto-stores
result = runtime.exec_via_registry('agent', context)
# Result automatically stored in graph
```

❌ **Pattern Bypasses**
```json
// WRONG - Direct agent call
{
  "agent": "financial_analyst",
  "action": "analyze",
  "params": {"symbol": "AAPL"}
}

// CORRECT - Registry execution
{
  "action": "execute_through_registry",
  "params": {
    "agent": "financial_analyst",
    "context": {"symbol": "AAPL"}
  }
}
```

### Compliance Levels

**Level 1: Warning Mode (Default)**
- Logs bypass warnings
- Tracks violations
- Allows direct access (with warnings)

**Level 2: Strict Mode**
```bash
export TRINITY_STRICT_MODE=true
```
- Raises errors on bypasses
- Blocks direct agent access
- Enforces 100% compliance

**Level 3: CI/CD Enforcement**
```bash
# AST checking in pipeline
python scripts/check_compliance.py
if [ $? -ne 0 ]; then exit 1; fi

# Pattern validation
python examples/analyze_existing_patterns.py
```

---

## Migration Guide

### Migrating Legacy Code to Trinity

**Before (Legacy Orchestration):**
```python
from core.claude_orchestrator import ClaudeOrchestrator

orchestrator = ClaudeOrchestrator(graph)
result = orchestrator.orchestrate("Analyze AAPL")
```

**After (Trinity):**
```python
from core.universal_executor import get_executor

executor = get_executor(graph, registry, runtime)
result = executor.execute({'user_input': 'Analyze AAPL'})
```

**Before (Direct Agent Access):**
```python
agent = runtime.agents['financial_analyst']
result = agent.process_request('DCF for AAPL', {'symbol': 'AAPL'})
```

**After (Registry Execution):**
```python
result = runtime.exec_via_registry('financial_analyst', {
    'request': 'DCF for AAPL',
    'symbol': 'AAPL'
})
```

**Before (Hard-Coded Pattern):**
```python
def analyze_moat(symbol):
    brand = evaluate_brand(symbol)
    network = evaluate_network(symbol)
    cost = evaluate_cost(symbol)
    switching = evaluate_switching(symbol)

    score = (brand + network + cost + switching) / 4
    rating = "Wide Moat" if score >= 8 else "Narrow Moat"

    return {'rating': rating, 'score': score}
```

**After (JSON Pattern):**
```json
{
  "id": "moat_analyzer",
  "steps": [
    {
      "action": "evaluate",
      "params": {
        "type": "brand_moat",
        "checks": ["premium_pricing_ability", "customer_loyalty"]
      },
      "outputs": "brand_score"
    },
    {
      "action": "evaluate",
      "params": {
        "type": "network_effects",
        "checks": ["value_increases_with_users", "high_switching_costs"]
      },
      "outputs": "network_score"
    },
    {
      "action": "synthesize",
      "params": {
        "scores": ["{brand_score}", "{network_score}", "{cost_score}", "{switching_score}"]
      },
      "outputs": "moat_rating"
    }
  ]
}
```

### Checklist for New Features

**Adding a New Agent:**
- [ ] Inherits from `BaseAgent` or implements standard methods
- [ ] Takes `graph` in constructor
- [ ] Returns `dict` from all execution methods
- [ ] Defined in `AGENT_CAPABILITIES` with explicit capabilities
- [ ] Registered via `runtime.register_agent()` with capabilities
- [ ] Tested via `runtime.exec_via_registry()`
- [ ] Never called directly (no `runtime.agents[name]`)

**Creating a New Pattern:**
- [ ] Has unique `id` field
- [ ] Has `version` field (e.g., "1.0")
- [ ] Has `last_updated` field (YYYY-MM-DD)
- [ ] All steps use `action: "execute_through_registry"`
- [ ] All agent names exist in registry
- [ ] Variables use `{var_name}` syntax
- [ ] Validated with `ComplianceChecker`
- [ ] Tested with `pattern_engine.execute_pattern()`

**Modifying Core Components:**
- [ ] No breaking changes to `UniversalExecutor.execute()` signature
- [ ] Maintains backward compatibility with existing patterns
- [ ] Preserves automatic graph storage in `AgentAdapter`
- [ ] Logs all compliance violations
- [ ] Updates compliance checker rules if needed
- [ ] Regenerates compliance report to verify 100% rate

---

## Appendix: File Reference

### Core Files

- [dawsos/core/universal_executor.py](../core/universal_executor.py) - Universal execution entry point
- [dawsos/core/pattern_engine.py](../core/pattern_engine.py) - Pattern loading and execution
- [dawsos/core/agent_runtime.py](../core/agent_runtime.py) - Agent coordination with compliance
- [dawsos/core/agent_adapter.py](../core/agent_adapter.py) - Agent wrapping and registry
- [dawsos/core/knowledge_graph.py](../core/knowledge_graph.py) - Knowledge persistence layer
- [dawsos/core/knowledge_loader.py](../core/knowledge_loader.py) - Centralized dataset loading
- [dawsos/core/persistence.py](../core/persistence.py) - Backup and recovery management
- [dawsos/core/agent_capabilities.py](../core/agent_capabilities.py) - Agent capability definitions
- [dawsos/core/compliance_checker.py](../core/compliance_checker.py) - Compliance validation

### Pattern Directories

- [dawsos/patterns/](../patterns/) - All patterns (45 total)
- [dawsos/patterns/system/meta/](../patterns/system/meta/) - Meta-patterns (meta_executor, etc.)
- [dawsos/patterns/analysis/](../patterns/analysis/) - Analysis patterns (DCF, moat, etc.)
- [dawsos/patterns/queries/](../patterns/queries/) - Query patterns (stock_price, etc.)
- [dawsos/patterns/workflows/](../patterns/workflows/) - Workflow patterns
- [dawsos/patterns/governance/](../patterns/governance/) - Governance patterns

### Knowledge Files

- [dawsos/storage/knowledge/](../storage/knowledge/) - Enriched datasets (7 total)
- [dawsos/storage/graph.json](../storage/graph.json) - Main knowledge graph
- [dawsos/storage/backups/](../storage/backups/) - Graph backups

### Documentation

- [dawsos/docs/TrinityExecutionFlow.md](TrinityExecutionFlow.md) - Execution flow diagram
- [dawsos/docs/COMPLIANCE_CHECKER_INTEGRATION.md](COMPLIANCE_CHECKER_INTEGRATION.md) - Compliance guide
- [TRINITY_COMPLETION_ROADMAP.md](../../TRINITY_COMPLETION_ROADMAP.md) - Completion roadmap
- [APPLICATION_COMPLETION_STATUS.md](../../APPLICATION_COMPLETION_STATUS.md) - Overall status
- [TRACK_A_WEEK1_COMPLETE.md](../../TRACK_A_WEEK1_COMPLETE.md) - Week 1 completion report

---

## Summary

**Trinity Architecture** is DawsOS's production-ready execution framework with:

✅ **100% Pattern Compliance** - All 45 patterns Trinity-compliant
✅ **19 Registered Agents** - All wrapped in AgentAdapter with capabilities
✅ **Automatic Graph Storage** - Every result persisted
✅ **Compliance Enforcement** - Runtime warnings, strict mode, AST checking
✅ **Centralized Knowledge** - 7 enriched datasets, cached & validated
✅ **Production Persistence** - Backups, checksums, rotation, recovery
✅ **Self-Healing** - Automatic recovery from corruption

**Key Principle:** ALL execution flows through the Trinity path - no bypasses, no exceptions.

**Developer Mantra:** If it's not through the registry, it's not Trinity-compliant.

---

**End of Trinity Architecture Guide**

*For questions or clarifications, see examples in [dawsos/examples/](../examples/) or tests in [dawsos/tests/](../tests/).*
