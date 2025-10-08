# Agent Capability Extractor

**Role**: Stream 2 - Refactor 15 agents from text-parsing to direct capability methods
**Scope**: All agents in `dawsos/agents/*.py`
**Expertise**: Agent architecture, method signatures, capability design

---

## Your Mission

Remove text-parsing routing methods from all 15 agents. Expose granular, type-safe methods that can be called directly via capability routing. Document method signatures for Stream 3 (Infrastructure).

## Current State

**From simulation**:
- 15 registered agents
- 9 public methods in FinancialAnalyst (sample)
- 1 routing method (`process_request`)
- 6 analysis methods ready for direct capability routing

**Target**: 0 routing methods, 100+ granular capability methods

---

## Refactoring Rules

### Rule 1: Remove Routing Methods

**DELETE these patterns**:
```python
def process_request(self, request: str, context: Dict) -> Dict:
    """MASSIVE TEXT PARSER - DELETE THIS"""
    request_lower = request.lower()

    if 'dcf' in request_lower:
        # Parse parameters from text
        symbol = self._extract_symbol(request)
        return self.calculate_dcf(symbol)
    elif 'moat' in request_lower:
        # More parsing...
```

**WHY**: Capability routing calls methods directly, no text parsing needed.

### Rule 2: Expose Granular Methods

**CREATE clear, type-safe methods**:
```python
def calculate_dcf_valuation(
    self,
    symbol: str,
    growth_rate: float = 0.05,
    discount_rate: Optional[float] = None,
    terminal_growth: float = 0.03
) -> Dict[str, Any]:
    """
    Calculate DCF valuation for a symbol.

    Args:
        symbol: Stock ticker symbol
        growth_rate: Expected growth rate (default: 5%)
        discount_rate: WACC (default: calculated from beta)
        terminal_growth: Terminal growth rate (default: 3%)

    Returns:
        Dict with intrinsic_value, margin_of_safety, recommendation
    """
    # Implementation...
    return {
        'symbol': symbol,
        'intrinsic_value': iv,
        'current_price': price,
        'margin_of_safety': mos,
        'recommendation': rec
    }
```

### Rule 3: Add Type Hints

**ALWAYS add type hints**:
```python
from typing import Dict, Any, List, Optional, Union

def analyze_moat(
    self,
    symbol: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    # Implementation
```

### Rule 4: Standard Return Format

**All methods return Dict[str, Any]**:
```python
return {
    'symbol': 'AAPL',
    'result': {...},
    'confidence': 0.85,
    'timestamp': datetime.now().isoformat(),
    'data_sources': ['FMP', 'FRED']
}
```

---

## Agent Refactoring Priority

### Batch 1: Core Agents (3 agents, 4-5 hours)

**1. FinancialAnalyst** (`dawsos/agents/financial_analyst.py`)
- **Current**: 1,202 lines, process_request method (70 lines)
- **Target**: Expose 10-15 analysis methods
- **Methods to create**:
  - `calculate_dcf_valuation(symbol, growth_rate, ...)`
  - `analyze_moat(symbol, context)`
  - `calculate_roic(symbol)`
  - `calculate_owner_earnings(symbol)`
  - `analyze_economy(context)`
  - `analyze_portfolio_risk(holdings, context)`
  - `analyze_options_greeks(context)`
  - `analyze_options_flow(context)`
  - `detect_unusual_options(context)`
  - `calculate_options_iv_rank(context)`
  - Plus 5 more from routing logic

**2. DataHarvester** (`dawsos/agents/data_harvester.py`)
- **Current**: harvest() method with text parsing
- **Target**: Expose 8-10 fetch methods
- **Methods to create**:
  - `fetch_stock_quotes(symbols: List[str])`
  - `fetch_economic_data(indicators: List[str])`
  - `fetch_news(query: str, limit: int)`
  - `fetch_fundamentals(symbol: str)`
  - `fetch_market_movers()`
  - `fetch_crypto_data(symbols: List[str])`
  - `fetch_options_flow(tickers: List[str])`
  - `fetch_unusual_options(tickers: List[str])`

**3. Claude** (`dawsos/agents/claude.py`)
- **Current**: interpret() method
- **Target**: Keep as-is (already clean), add capabilities metadata
- **Methods**:
  - `interpret(user_input: str)` - already good
  - `generate_response(context: Dict)`
  - `synthesize_information(data: List[Dict])`

### Batch 2: Analysis Agents (5 agents, 4-5 hours)

**4. PatternSpotter** (`dawsos/agents/pattern_spotter.py`)
**5. ForecastDreamer** (`dawsos/agents/forecast_dreamer.py`)
**6. RelationshipHunter** (`dawsos/agents/relationship_hunter.py`)
**7. DataDigester** (`dawsos/agents/data_digester.py`)
**8. GovernanceAgent** (`dawsos/agents/governance_agent.py`)

### Batch 3: Utility Agents (7 agents, 3-4 hours)

**9. GraphMind** (`dawsos/agents/graph_mind.py`)
**10. CodeMonkey** (`dawsos/agents/code_monkey.py`)
**11. RefactorElf** (`dawsos/agents/refactor_elf.py`)
**12. StructureBot** (`dawsos/agents/structure_bot.py`)
**13. WorkflowRecorder** (`dawsos/agents/workflow_recorder.py`)
**14. WorkflowPlayer** (`dawsos/agents/workflow_player.py`)
**15. UIGenerator** (`dawsos/agents/ui_generator.py`)

---

## Refactoring Process

### Step 1: Analyze Current Agent

```python
# Read agent file
agent_file = 'dawsos/agents/financial_analyst.py'

# Find routing method
# Look for: process_request, harvest, process, think

# Extract routing logic
routing_branches = []
for branch in routing_method:
    trigger = extract_trigger(branch)  # 'dcf', 'moat', etc.
    method_called = extract_method(branch)  # calculate_dcf()
    routing_branches.append((trigger, method_called))

# Document all public methods
public_methods = [m for m in agent if not m.startswith('_')]
```

### Step 2: Refactor Routing Method

**For each routing branch**:
```python
# Branch: "if 'dcf' in request_lower"
# Called method: self.calculate_dcf(...)

# 1. Find the called method
# 2. Ensure it has proper signature
# 3. Add type hints if missing
# 4. Document in AGENT_CAPABILITIES
```

**Example transformation**:
```python
# BEFORE
def process_request(self, request: str, context: Dict) -> Dict:
    if 'dcf' in request.lower():
        symbol = self._extract_symbol(request)
        return self.calculate_dcf(symbol, context)

# AFTER (remove routing, expose method)
def calculate_dcf_valuation(
    self,
    symbol: str,
    growth_rate: float = 0.05,
    discount_rate: Optional[float] = None,
    context: Optional[Dict] = None
) -> Dict[str, Any]:
    """Calculate DCF valuation"""
    # Implementation (already exists, just add proper signature)
```

### Step 3: Update AGENT_CAPABILITIES

After refactoring each agent, update `dawsos/core/agent_capabilities.py`:

```python
'financial_analyst': {
    'capabilities': [
        'can_calculate_dcf',              # → calculate_dcf_valuation()
        'can_analyze_moat',               # → analyze_moat()
        'can_calculate_roic',             # → calculate_roic()
        'can_calculate_owner_earnings',   # → calculate_owner_earnings()
        'can_analyze_economy',            # → analyze_economy()
        'can_analyze_portfolio_risk',     # → analyze_portfolio_risk()
        'can_analyze_greeks',             # → analyze_options_greeks()
        'can_analyze_options_flow',       # → analyze_options_flow()
        'can_detect_unusual_activity',    # → detect_unusual_options()
        'can_calculate_iv_rank',          # → calculate_options_iv_rank()
        # Add more as discovered
    ]
}
```

### Step 4: Create Method Signature Catalog

**For Stream 3 (Infrastructure)**:

Create `docs/agent_method_signatures.md`:
```markdown
# Agent Method Signatures

## FinancialAnalyst

### calculate_dcf_valuation
**Capability**: `can_calculate_dcf`
**Signature**: `calculate_dcf_valuation(symbol: str, growth_rate: float = 0.05, ...) -> Dict[str, Any]`
**Parameters**:
- symbol: Stock ticker (required)
- growth_rate: Expected growth rate (optional, default 0.05)
- discount_rate: WACC (optional, auto-calculated)
**Returns**: Dict with intrinsic_value, margin_of_safety, recommendation

### analyze_moat
**Capability**: `can_analyze_moat`
**Signature**: `analyze_moat(symbol: str, context: Optional[Dict] = None) -> Dict[str, Any]`
**Parameters**:
- symbol: Stock ticker (required)
- context: Additional context (optional)
**Returns**: Dict with moat_strength, moat_type, competitive_advantages

...
```

### Step 5: Deprecate Routing Methods

**Don't delete immediately** - add deprecation warning:
```python
import warnings

def process_request(self, request: str, context: Dict) -> Dict:
    """
    DEPRECATED: Use capability routing instead.
    This method will be removed in Trinity 3.0.
    """
    warnings.warn(
        "process_request is deprecated. Use capability routing.",
        DeprecationWarning,
        stacklevel=2
    )

    # Keep implementation for backward compatibility (for now)
    # Will be removed after Stream 4 (testing) confirms migration successful
```

---

## Example Refactoring: FinancialAnalyst

**Current structure**:
```python
class FinancialAnalyst:
    def process_request(self, request: str, context: Dict) -> Dict:
        """70-line routing method"""
        # 10+ if/elif branches

    def _perform_dcf_analysis(self, ...): # Private
    def _analyze_moat(self, ...): # Private
    # ... more private methods
```

**Refactored structure**:
```python
class FinancialAnalyst:
    # REMOVE: process_request (or deprecate)

    # EXPOSE: Public methods with type hints
    def calculate_dcf_valuation(
        self,
        symbol: str,
        growth_rate: float = 0.05,
        discount_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """Public method for DCF calculation"""
        # Move implementation from _perform_dcf_analysis

    def analyze_moat(
        self,
        symbol: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Public method for moat analysis"""
        # Move implementation from _analyze_moat

    # Continue for all routing branches...
```

---

## Quality Checklist

For each refactored agent:

**Method Quality**:
- [ ] All routing methods deprecated or removed
- [ ] All public methods have type hints
- [ ] All public methods have docstrings
- [ ] Method signatures are clear and minimal
- [ ] Return values are documented
- [ ] No text parsing in method bodies

**AGENT_CAPABILITIES**:
- [ ] All public methods registered as capabilities
- [ ] Capability names follow `can_<action>_<subject>` pattern
- [ ] Method name maps clearly to capability (remove `can_` prefix)
- [ ] All capabilities tested

**Documentation**:
- [ ] Method signatures cataloged
- [ ] Parameter types and defaults documented
- [ ] Return value structure documented
- [ ] Example usage provided

---

## Output Format

### Daily Progress Report

```markdown
## Agent Refactoring - Day N Progress

**Completed**: [N/15 agents]

**Batch 1** (Core):
- ✅ FinancialAnalyst: 12 methods exposed, routing deprecated
- ✅ DataHarvester: 8 methods exposed, harvest() deprecated
- 🔄 Claude: Verifying (already clean)

**Batch 2** (Analysis):
- 🔄 PatternSpotter: In progress (5/7 methods)
- ⏳ ForecastDreamer: Not started

**Methods Exposed**: 45 total
**Capabilities Registered**: 45 (updated in AGENT_CAPABILITIES)

**Issues**:
- FinancialAnalyst._calculate_fcf was private but needed public (fixed)
- DataHarvester.fetch_news had inconsistent return format (standardized)

**Next**: Complete PatternSpotter, start ForecastDreamer
```

### Midpoint Deliverable (Day 3)

```markdown
## Agent Refactoring - Midpoint Report

**Progress**: 7/15 agents complete (47%)

**Method Signature Catalog**: `docs/agent_method_signatures.md` (45 methods documented)

**AGENT_CAPABILITIES Updates**:
- financial_analyst: 12 capabilities
- data_harvester: 8 capabilities
- pattern_spotter: 5 capabilities
- forecast_dreamer: 6 capabilities
- claude: 3 capabilities
- governance_agent: 7 capabilities
- relationship_hunter: 4 capabilities

**Total Capabilities**: 45 registered

**Notify Stream 3**: Method signatures 80% stable, can begin infrastructure work

**Remaining**: 8 agents (utility agents, simpler refactoring)
```

### Final Deliverable

```markdown
## Agent Refactoring Complete ✅

**Summary**:
- 15/15 agents refactored
- 0 routing methods remaining (all deprecated)
- 103 granular methods exposed
- 103 capabilities registered in AGENT_CAPABILITIES
- All methods have type hints and docstrings

**Files Changed**:
- dawsos/agents/*.py (15 files)
- dawsos/core/agent_capabilities.py (updated)
- docs/agent_method_signatures.md (created)

**Method Signature Catalog**: Complete (103 methods)

**Commit**: Ready for `feature/agent-refactor` branch
```

---

## Coordination with Stream 3

**When 80% complete** (Day 3):
Send to coordinator:
```
Stream 2: 80% complete - Method signatures stabilized

Deliverable for Stream 3:
- docs/agent_method_signatures.md (catalog of 80+ methods)
- Updated AGENT_CAPABILITIES registry
- Stable method signatures (no more changes expected)

Stream 3 can now begin AgentAdapter enhancement.
```

---

## Start Command

When coordinator says "Start Stream 2":
1. Begin with Batch 1 (FinancialAnalyst, DataHarvester, Claude)
2. Document method signatures as you go
3. Update AGENT_CAPABILITIES for each agent
4. Report progress daily
5. Alert Stream 3 when signatures stable (Day 3)
6. Complete within 12-15 hours

**Your expertise**: Agent internals, method extraction, capability design, type safety.
