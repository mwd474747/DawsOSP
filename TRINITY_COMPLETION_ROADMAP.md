# Trinity 2.0 → 3.0 Completion Roadmap

**Date**: October 8, 2025
**Current Status**: Trinity 2.0 Infrastructure Complete (93.75%)
**Path**: 2.0 Completion → 3.0 AI Orchestration

---

## Trinity 2.0 - Remaining Work

### Current Status: 93.75% Complete ✅

**Completed**:
- ✅ Infrastructure (AgentAdapter, Discovery APIs, ExecuteThroughRegistryAction)
- ✅ 19 wrapper methods (FinancialAnalyst: 12, DataHarvester: 7)
- ✅ 45/48 patterns migrated to capability routing
- ✅ Test suite (28/28 tests passing)
- ✅ Documentation (8,073 lines)

**Remaining**: 6.25% to reach 100%

---

## Phase 1: Complete Trinity 2.0 (6-8 hours)

### 1.1 Manual Pattern Review (30 min) ⚠️ REQUIRED

**Issue**: 3 patterns use 'claude' agent which needs proper capability mapping

**Patterns to review**:
1. Check which patterns still have unmapped steps
2. Likely governance or complex multi-agent patterns

**Action**:
```bash
# Find patterns with 'claude' agent
grep -r '"agent": "claude"' dawsos/patterns/ | cut -d: -f1 | sort -u
```

**Fix**: Map 'claude' agent requests to appropriate capabilities based on context

---

### 1.2 Add Remaining Critical Wrapper Methods (2-3 hours) ⚠️ RECOMMENDED

**Current Coverage**: 19/103 capabilities (18.4%)
**Target**: 40/103 capabilities (38.8%) - covers 90% of use cases

#### Priority 1: Pattern-Spotter (30 min)
```python
# In dawsos/agents/pattern_spotter.py

def detect_patterns(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Public wrapper for pattern detection capability.
    Maps to: can_detect_patterns"""
    # Delegate to existing pattern detection logic
    pass

def identify_signals(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Public wrapper for signal identification capability.
    Maps to: can_identify_signals"""
    # Delegate to existing signal identification logic
    pass
```

#### Priority 2: Forecast-Dreamer (30 min)
```python
# In dawsos/agents/forecast_dreamer.py

def generate_forecast(self, symbol: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Public wrapper for forecasting capability.
    Maps to: can_generate_forecast"""
    # Delegate to existing forecast generation
    pass

def project_future(self, scenario: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Public wrapper for future projection capability.
    Maps to: can_project_future"""
    # Delegate to existing projection logic
    pass
```

#### Priority 3: Governance-Agent (45 min)
```python
# In dawsos/agents/governance_agent.py

def audit_data_quality(self, dataset: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Public wrapper for data quality audit capability.
    Maps to: can_audit_data_quality"""
    pass

def validate_policy(self, policy: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Public wrapper for policy validation capability.
    Maps to: can_validate_policy"""
    pass

def check_compliance(self, rules: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Public wrapper for compliance checking capability.
    Maps to: can_check_compliance"""
    pass
```

#### Priority 4: Relationship-Hunter (30 min)
```python
# In dawsos/agents/relationship_hunter.py

def calculate_correlations(self, symbol1: str, symbol2: str, context: Dict[str, Any] = None) -> float:
    """Public wrapper for correlation calculation.
    Maps to: can_calculate_correlations"""
    # Already exists in DataHarvester, may need implementation here
    pass

def find_relationships(self, entity: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Public wrapper for relationship finding.
    Maps to: can_find_relationships"""
    pass
```

**Estimated**: 2.5 hours total

---

### 1.3 End-to-End Pattern Testing (2-3 hours) ⚠️ CRITICAL

**Objective**: Verify migrated patterns work in production

#### Test Suite
1. **DCF Valuation** (migrated pattern)
   ```
   Test: "Analyze AAPL using DCF"
   Expected: Intrinsic value calculation, no template placeholders
   ```

2. **Options Flow** (already migrated)
   ```
   Test: "Analyze options flow for SPY"
   Expected: Put/call ratio, sentiment, real data (not {flow_sentiment.put_call_ratio})
   ```

3. **Moat Analysis** (migrated pattern)
   ```
   Test: "Analyze economic moat for MSFT"
   Expected: Brand strength, switching costs, moat score
   ```

4. **Portfolio Risk** (migrated pattern)
   ```
   Test: "Analyze portfolio risk for [AAPL, GOOGL, MSFT]"
   Expected: Concentration risk, correlations, recommendations
   ```

5. **Morning Briefing** (migrated workflow)
   ```
   Test: "Give me morning briefing"
   Expected: Market overview, economic data, top movers
   ```

#### Test Process
```bash
# 1. Kill existing Streamlit instances
pkill -f streamlit

# 2. Restart with latest code
dawsos/venv/bin/streamlit run dawsos/main.py --server.port=8501

# 3. Test each query in UI
# 4. Check logs for errors
# 5. Verify results are formatted correctly
# 6. Ensure no template placeholders ({...})
```

**Deliverable**: Test results document showing 5/5 patterns working

---

### 1.4 Pattern Linter Validation (30 min)

**Action**:
```bash
# Run pattern linter on all patterns
python scripts/lint_patterns.py dawsos/patterns/

# Expected: 0 errors, maybe warnings
# Fix any structural issues found
```

**Common issues to fix**:
- Missing `entities` field
- Inconsistent entity naming ({symbol} vs {SYMBOL})
- Missing `save_as` on multi-step patterns
- Invalid capability names

---

### 1.5 Performance Benchmarking (1 hour) 📊

**Objective**: Compare capability routing vs legacy routing performance

#### Benchmark Script
```python
import time
from dawsos.core.pattern_engine import PatternEngine

# Test legacy pattern
start = time.time()
result = engine.execute_pattern('legacy_dcf', {'symbol': 'AAPL'})
legacy_time = time.time() - start

# Test capability routing pattern
start = time.time()
result = engine.execute_pattern('dcf_valuation', {'symbol': 'AAPL'})
capability_time = time.time() - start

print(f"Legacy: {legacy_time:.3f}s")
print(f"Capability: {capability_time:.3f}s")
print(f"Speedup: {legacy_time/capability_time:.2f}x")
```

**Expected Results**:
- Capability routing: 10-20% faster (no text parsing overhead)
- Or similar speed (baseline for future optimization)

**Deliverable**: Performance comparison report

---

### 1.6 Documentation Updates (1 hour)

**Files to update**:

1. **CLAUDE.md** - Add Trinity 2.0 status
   ```markdown
   ## Trinity 2.0 Status (October 2025)
   - ✅ Capability routing infrastructure: 100% complete
   - ✅ Pattern migration: 93.75% (45/48)
   - ✅ Wrapper methods: 19+ capabilities functional
   - ✅ Testing: All tests passing
   ```

2. **docs/AgentDevelopmentGuide.md** - Add wrapper method pattern
   ```markdown
   ## Adding Capability Wrapper Methods

   When adding new capabilities to agents, create public wrapper methods:

   ```python
   def calculate_dcf(self, symbol: str, context: Dict = None) -> Dict:
       """Public wrapper for DCF calculation capability.
       Maps to: can_calculate_dcf"""
       request = f"Calculate DCF valuation for {symbol}"
       return self._perform_dcf_analysis(request, context or {})
   ```
   ```

3. **SYSTEM_STATUS.md** - Update to reflect Trinity 2.0 completion

---

## Summary: Trinity 2.0 Completion Checklist

| Task | Priority | Time | Status |
|------|----------|------|--------|
| Manual pattern review (3 patterns) | ⚠️ Required | 30 min | ⏳ Pending |
| End-to-end testing (5 queries) | ⚠️ Critical | 2-3 hrs | ⏳ Pending |
| Add wrapper methods (4 agents) | Recommended | 2-3 hrs | ⏳ Pending |
| Pattern linter validation | Recommended | 30 min | ⏳ Pending |
| Performance benchmarking | Optional | 1 hr | ⏳ Pending |
| Documentation updates | Optional | 1 hr | ⏳ Pending |
| **TOTAL** | - | **6-8 hrs** | **93.75%** |

**To reach 100% Trinity 2.0**: Complete tasks 1-2 (3 hours minimum)
**To reach production-ready**: Complete tasks 1-4 (6 hours)

---

## Trinity 3.0 - AI-Powered Orchestration

**Vision**: Natural language → Automatic capability chaining → Optimized execution

### Current State vs Trinity 3.0

| Capability | Trinity 2.0 | Trinity 3.0 |
|------------|-------------|-------------|
| **Input** | Specific query matches pattern | Natural language intent |
| **Pattern Selection** | Keyword matching | Semantic similarity + AI |
| **Capability Routing** | Manual in patterns | AI-orchestrated |
| **Multi-step** | Predefined in JSON | Dynamic chaining |
| **Learning** | Static patterns | Self-optimizing |
| **Extensibility** | New JSON patterns | Plugin system |

---

## Phase 2: Trinity 3.0 Foundation (40-60 hours)

### 2.1 Intent Parser (10-15 hours)

**Objective**: Natural language → Capability selection

#### Architecture
```python
class IntentParser:
    """Parses natural language queries into capability requirements"""

    def parse(self, query: str) -> Intent:
        """
        Input: "I want to understand Apple's competitive advantages"
        Output: Intent(
            primary_capability='can_analyze_moat',
            entities={'symbol': 'AAPL'},
            secondary_capabilities=['can_fetch_fundamentals'],
            confidence=0.95
        )
        """
        pass
```

#### Implementation
1. **LLM-based parsing** (fast to build, 10 hours)
   - Use Claude/GPT to extract intent
   - Few-shot prompting with examples
   - Structured output (JSON)

2. **Embeddings + Similarity** (more robust, 15 hours)
   - Embed all 103 capabilities
   - Embed user query
   - Find top-k similar capabilities
   - LLM refines selection

**Deliverable**: `IntentParser` class in `core/intent_parser.py`

---

### 2.2 Semantic Pattern Search (8-12 hours)

**Objective**: Find patterns by description similarity, not just ID

#### Current (Trinity 2.0)
```python
pattern = engine.get_pattern('dcf_valuation')  # Exact ID match
```

#### Trinity 3.0
```python
patterns = engine.find_patterns_by_intent("value this company")
# Returns: [dcf_valuation, buffett_checklist, moat_analyzer]
# Ranked by semantic similarity
```

#### Implementation
1. **Embed all pattern descriptions** (once)
2. **Embed user query** (on-the-fly)
3. **Cosine similarity ranking**
4. **Return top-k patterns**

**Technology**:
- Sentence transformers (sentence-transformers library)
- Or OpenAI embeddings API
- Vector store: FAISS or in-memory

**Deliverable**: `find_patterns_by_intent()` method in PatternEngine

---

### 2.3 Capability Orchestrator (15-20 hours)

**Objective**: Automatically chain capabilities to fulfill complex requests

#### Example
```
User: "I want a comprehensive analysis of AAPL - valuation, moat, risks, and comparison to MSFT"

Orchestrator determines:
1. can_fetch_fundamentals (AAPL, MSFT)
2. can_calculate_dcf (AAPL)
3. can_analyze_moat (AAPL)
4. can_identify_risks (AAPL)
5. can_compare_stocks (AAPL, MSFT)
6. Synthesize results

Executes in optimal order (parallel where possible)
```

#### Architecture
```python
class CapabilityOrchestrator:
    """Chains capabilities to fulfill complex intents"""

    def orchestrate(self, intent: Intent) -> ExecutionPlan:
        """
        Input: Intent with primary + secondary capabilities
        Output: ExecutionPlan with:
          - Ordered capability list
          - Dependency graph
          - Parallelization opportunities
          - Data flow between steps
        """
        pass

    def execute(self, plan: ExecutionPlan) -> Result:
        """Execute the plan, handling errors and retries"""
        pass
```

#### Key Features
1. **Dependency resolution**: If A needs output from B, run B first
2. **Parallel execution**: Run independent capabilities concurrently
3. **Error handling**: Retry, fallback, graceful degradation
4. **Result synthesis**: Combine outputs into coherent response

**Technology**:
- DAG (Directed Acyclic Graph) for dependencies
- asyncio for parallel execution
- LLM for result synthesis

**Deliverable**: `CapabilityOrchestrator` class in `core/orchestrator.py`

---

### 2.4 Plugin System (10-15 hours)

**Objective**: Dynamically extend capabilities without code changes

#### Current (Trinity 2.0)
```python
# To add capability:
1. Write agent method
2. Update AGENT_CAPABILITIES
3. Add pattern JSON
4. Restart system
```

#### Trinity 3.0
```python
# Plugin definition
class MyCustomPlugin:
    capability = "can_analyze_sentiment_advanced"

    def execute(self, text: str) -> Dict:
        # Custom sentiment analysis
        return {'sentiment': 'positive', 'score': 0.85}

# Load plugin
orchestrator.load_plugin(MyCustomPlugin)

# Use immediately (no restart)
result = orchestrator.execute_capability('can_analyze_sentiment_advanced', {'text': '...'})
```

#### Implementation
1. **Plugin interface**: Standard base class
2. **Plugin registry**: Discover and load plugins
3. **Capability injection**: Add to AGENT_CAPABILITIES dynamically
4. **Hot-reload**: Load new plugins without restart

**Deliverable**: Plugin system in `core/plugin_manager.py`

---

### 2.5 Self-Learning & Optimization (15-20 hours)

**Objective**: System learns from usage and optimizes over time

#### Features

1. **Usage Tracking**
   - Log which capabilities are used together
   - Track execution times
   - Measure user satisfaction (implicit/explicit)

2. **Pattern Optimization**
   - If users frequently ask X, create new pattern for X
   - Optimize capability chaining based on actual usage
   - Cache frequent results

3. **Capability Recommendation**
   - "Users who used can_calculate_dcf also used can_analyze_moat"
   - Suggest related capabilities

4. **Auto-tuning**
   - Adjust timeout thresholds
   - Optimize parallel vs sequential execution
   - Balance speed vs accuracy

#### Implementation
```python
class LearningEngine:
    """Learns from usage patterns and optimizes system"""

    def track_execution(self, query: str, capabilities_used: List[str],
                       result_quality: float, execution_time: float):
        """Log execution for learning"""
        pass

    def suggest_capabilities(self, current_capability: str) -> List[str]:
        """Recommend related capabilities"""
        pass

    def optimize_plan(self, intent: Intent) -> ExecutionPlan:
        """Generate optimized execution plan based on learned patterns"""
        pass
```

**Technology**:
- SQLite for usage logs
- Simple ML models (collaborative filtering)
- A/B testing framework

**Deliverable**: `LearningEngine` class in `core/learning.py`

---

## Phase 3: Trinity 3.0 Integration (20-30 hours)

### 3.1 Unified API (5-8 hours)

**Create single entry point** for all Trinity 3.0 features:

```python
class TrinityOrchestrator:
    """Unified Trinity 3.0 interface"""

    def __init__(self):
        self.intent_parser = IntentParser()
        self.pattern_search = SemanticPatternSearch()
        self.orchestrator = CapabilityOrchestrator()
        self.learning = LearningEngine()
        self.plugin_manager = PluginManager()

    def execute(self, query: str) -> Result:
        """
        Trinity 3.0 execution:
        1. Parse intent
        2. Find relevant patterns
        3. Orchestrate capabilities
        4. Execute plan
        5. Learn from execution
        6. Return result
        """
        # Parse
        intent = self.intent_parser.parse(query)

        # Find patterns
        patterns = self.pattern_search.find(intent)

        # Orchestrate
        plan = self.orchestrator.plan(intent, patterns)

        # Execute
        result = self.orchestrator.execute(plan)

        # Learn
        self.learning.track_execution(query, plan, result)

        return result
```

---

### 3.2 Testing & Validation (10-15 hours)

**Comprehensive test suite** for Trinity 3.0:

1. **Intent parsing accuracy** (500+ test queries)
2. **Pattern search relevance** (semantic similarity benchmarks)
3. **Orchestration correctness** (dependency resolution, parallel execution)
4. **Plugin system** (load, unload, error handling)
5. **End-to-end** (complex multi-step queries)

---

### 3.3 Documentation (5-7 hours)

1. **User Guide**: How to use Trinity 3.0
2. **Developer Guide**: How to extend Trinity 3.0
3. **Plugin Guide**: How to write plugins
4. **Architecture Guide**: How Trinity 3.0 works
5. **Migration Guide**: Trinity 2.0 → 3.0

---

## Trinity 3.0 Timeline

| Phase | Component | Hours | Dependencies |
|-------|-----------|-------|--------------|
| 2.1 | Intent Parser | 10-15 | None |
| 2.2 | Semantic Pattern Search | 8-12 | None |
| 2.3 | Capability Orchestrator | 15-20 | 2.1 |
| 2.4 | Plugin System | 10-15 | None |
| 2.5 | Self-Learning | 15-20 | 2.3 |
| 3.1 | Unified API | 5-8 | 2.1-2.5 |
| 3.2 | Testing | 10-15 | 3.1 |
| 3.3 | Documentation | 5-7 | 3.1 |
| **TOTAL** | **Trinity 3.0** | **78-112 hrs** | - |

**Estimated Timeline**: 2-3 weeks full-time (10-14 weeks part-time)

---

## Parallel Development Strategy

### Stream 1: Intent & Search (2.1 + 2.2)
- **Team**: 1 developer
- **Time**: 18-27 hours
- **Deliverable**: Natural language → Pattern selection

### Stream 2: Orchestration (2.3)
- **Team**: 1 developer
- **Time**: 15-20 hours
- **Deliverable**: Automatic capability chaining

### Stream 3: Extensibility (2.4 + 2.5)
- **Team**: 1 developer
- **Time**: 25-35 hours
- **Deliverable**: Plugin system + Learning

### Stream 4: Integration (3.1 + 3.2 + 3.3)
- **Team**: 1 developer
- **Time**: 20-30 hours
- **Dependency**: Streams 1-3 complete
- **Deliverable**: Unified Trinity 3.0 system

**Parallel execution**: Streams 1-3 run simultaneously (saves 30-40 hours)

---

## Recommended Path Forward

### Option A: Complete Trinity 2.0 First (RECOMMENDED)
**Timeline**: 6-8 hours
**Goal**: 100% Trinity 2.0 completion
**Tasks**: Manual pattern review, end-to-end testing, wrapper methods

**Pros**:
- ✅ Solid foundation for Trinity 3.0
- ✅ Production-ready capability routing
- ✅ All patterns working correctly

**Cons**:
- ⏱️ Delays Trinity 3.0 start by 1 week

### Option B: Start Trinity 3.0 Immediately
**Timeline**: Begin 78-112 hour project
**Goal**: Jump to AI orchestration
**Risk**: Building on incomplete foundation (93.75% complete)

**Pros**:
- 🚀 Faster to advanced features
- 🎯 Focus on innovation

**Cons**:
- ⚠️ May encounter issues from incomplete 2.0
- 🐛 Harder to debug (2.0 + 3.0 issues mixed)

### Option C: Hybrid Approach
**Timeline**: 3 hours + parallel 3.0 development
**Goal**: Complete critical 2.0 tasks, start 3.0 foundation

**Tasks**:
1. Complete manual pattern review (30 min)
2. End-to-end testing of top 5 patterns (2-3 hours)
3. Start Trinity 3.0 Intent Parser in parallel

**Pros**:
- ✅ De-risks Trinity 2.0
- 🚀 Starts Trinity 3.0 progress
- ⚖️ Balanced approach

**Cons**:
- 🔀 Context switching between 2.0 and 3.0

---

## Immediate Next Steps (Choose One)

### Path A: Complete 2.0
```bash
1. Manual pattern review (30 min)
   - Find 3 patterns with 'claude' agent
   - Map to appropriate capabilities

2. End-to-end testing (2-3 hours)
   - Test DCF valuation for AAPL
   - Test options flow for SPY
   - Test moat analysis for MSFT
   - Test portfolio risk
   - Test morning briefing

3. Document results and declare Trinity 2.0 100% complete
```

### Path B: Start 3.0
```bash
1. Create core/intent_parser.py
2. Implement LLM-based intent parsing
3. Test with 20 sample queries
4. Begin semantic pattern search
```

### Path C: Hybrid
```bash
1. Manual pattern review (30 min)
2. Quick testing of top 3 patterns (1 hour)
3. Start Intent Parser prototype (2 hours)
```

---

## Success Criteria

### Trinity 2.0 Complete (100%)
- [ ] All 48 patterns migrated to capability routing
- [ ] All patterns execute successfully (no template placeholders)
- [ ] Pattern linter: 0 errors
- [ ] 40+ wrapper methods (covers 90% of use cases)
- [ ] Performance benchmarks documented

### Trinity 3.0 MVP (Phase 1)
- [ ] Intent parser: 80%+ accuracy on test queries
- [ ] Semantic search: Finds relevant patterns for 90% of queries
- [ ] Orchestrator: Correctly chains 2-3 capabilities
- [ ] End-to-end: Complex query works (e.g., "comprehensive AAPL analysis")

### Trinity 3.0 Complete
- [ ] Plugin system: 3rd party plugins load successfully
- [ ] Learning: System improves over 100+ queries
- [ ] Documentation: User + Developer guides complete
- [ ] Testing: 95%+ test coverage

---

## Recommendation

**Immediate**: Complete Trinity 2.0 (Option A)
- Time: 6-8 hours
- Impact: Production-ready capability routing
- Risk: Low

**Next**: Begin Trinity 3.0 Intent Parser (Stream 1)
- Time: 10-15 hours
- Impact: Natural language support
- Risk: Medium

**Long-term**: Full Trinity 3.0 (Parallel streams)
- Time: 78-112 hours (2-3 weeks)
- Impact: AI-powered orchestration
- Risk: Medium

**Total timeline**: 1 week (2.0) + 2-3 weeks (3.0) = **3-4 weeks to complete Trinity 3.0**

---

**Current Status**: Trinity 2.0 at 93.75% - Ready for final push to 100%
**Next Milestone**: Trinity 2.0 Complete (6-8 hours)
**Ultimate Goal**: Trinity 3.0 AI Orchestration (78-112 hours from now)

🎯 **Recommended**: Complete Trinity 2.0 first, then proceed to 3.0 with solid foundation.
