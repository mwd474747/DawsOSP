# OptimizerAgent Consolidation Analysis Report
**Date:** 2025-11-03  
**Thoroughness Level:** MEDIUM  
**Scope:** Analysis of 4 methods to be consolidated into FinancialAnalyst  

---

## Executive Summary

The OptimizerAgent provides portfolio optimization and rebalancing capabilities through 4 main methods that will be consolidated into the FinancialAnalyst agent. The implementation follows a clean agent/service pattern with minimal coupling, using Riskfolio-Lib for optimization math. All 4 methods are thin wrappers around corresponding OptimizerService methods, handling primarily argument resolution and metadata attachment.

**Key Finding:** The consolidation will be straightforward - all 4 methods have similar patterns:
1. Resolve portfolio_id from context
2. Handle pattern compatibility for multiple input formats
3. Call corresponding OptimizerService method
4. Attach metadata and return result

---

## Method 1: optimizer_propose_trades()

### Method Signature
```python
async def optimizer_propose_trades(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
    policy_json: Optional[Dict[str, Any]] = None,
    policies: Optional[Dict[str, Any]] = None,  # Pattern compatibility
    constraints: Optional[Dict[str, Any]] = None,  # Pattern compatibility
    positions: Optional[List[Dict[str, Any]]] = None,
    ratings: Optional[Dict[str, float]] = None,
    **kwargs,
) -> Dict[str, Any]:
```

### Location
**File:** `/Users/mdawson/Documents/GitHub/DawsOSP/backend/app/agents/optimizer_agent.py`  
**Lines:** 63-233 (171 lines total)

### Service Dependencies
- **Primary:** `get_optimizer_service()` (line 194)
  - Calls: `optimizer_service.propose_trades()`
- No direct database access - delegates to service

### Input Validation
1. **Portfolio ID Resolution (lines 110-116):**
   - Validates `portfolio_id` parameter or falls back to `ctx.portfolio_id`
   - Raises `ValueError` if neither available
   - Converts to `UUID` for type safety

2. **Policy Parameter Handling (lines 118-152):**
   - Handles multiple input formats for backward compatibility:
     - `policy_json` (dict format)
     - `policies` (list or dict format with policy type mappings)
     - `constraints` (dict format with constraint-specific keys)
   - Maps policy types to dict keys (e.g., "min_quality_score", "max_single_position")
   - Merges constraints into unified policy dict

3. **Default Policy (lines 154-163):**
   ```python
   {
       "min_quality_score": 0.0,
       "max_single_position_pct": 20.0,
       "max_sector_pct": 30.0,
       "max_turnover_pct": 20.0,
       "max_tracking_error_pct": 3.0,
       "method": "mean_variance",
   }
   ```

4. **Context Validation (lines 165-168):**
   - Requires `ctx.pricing_pack_id` (SACRED for reproducibility)
   - Raises `ValueError` if missing

5. **Ratings Parameter Handling (lines 170-185):**
   - Extracts ratings from state if not provided
   - Supports two rating result formats:
     - Portfolio ratings mode: Dict with "positions" key
     - Single security mode: Dict with "overall_rating" key

### Database Queries
**No direct queries** - OptimizerService.propose_trades() makes these queries:
- Query positions from `lots` table (join with `prices`)
- Query historical prices for covariance estimation
- Query pricing pack metadata

### Return Structure
```python
Dict[str, Any] with keys:
{
    "trades": List[Dict] - Trade proposals with:
        - symbol: str
        - action: "BUY"|"SELL"|"HOLD"
        - quantity: int (shares to trade)
        - current_shares: int
        - target_shares: int
        - current_weight_pct: float
        - target_weight_pct: float
        - current_price: float
        - trade_value: float
        - estimated_cost: float
        - rationale: str
    
    "trade_count": int
    "total_turnover": Decimal
    "turnover_pct": float
    "estimated_costs": Decimal
    "cost_bps": float (basis points)
    "method": str (optimization method used)
    "constraints_met": bool
    "warnings": List[str]
    "_metadata": Dict with agent metadata
}
```

### Error Handling
**Try/Except Pattern (lines 196-233):**
```python
try:
    result = await optimizer_service.propose_trades(...)
    metadata = self._create_metadata(...)
    return self._attach_metadata(result, metadata)
except Exception as e:
    logger.error(f"Trade proposal generation failed: {e}", exc_info=True)
    # Return error result with empty trades
    error_result = {
        "trades": [],
        "trade_count": 0,
        "total_turnover": Decimal("0"),
        "turnover_pct": 0.0,
        "estimated_costs": Decimal("0"),
        "cost_bps": 0.0,
        "error": str(e),
        "constraints_met": False,
        "warnings": [f"Optimization failed: {str(e)}"],
    }
    # Still attaches metadata even on error
    return self._attach_metadata(error_result, metadata)
```

### Business Logic Flow

1. **Portfolio Resolution:** Extract portfolio UUID from parameter or context
2. **Policy Consolidation:** Merge multiple policy/constraint input formats into unified dict
3. **Pricing Pack Validation:** Verify pricing_pack_id in context (reproducibility requirement)
4. **Ratings Resolution:** Extract quality scores from state or direct parameter
5. **Service Call:** Delegate to OptimizerService.propose_trades() which:
   - Loads current positions from database
   - Filters by quality rating if provided
   - Fetches historical prices (252-day lookback default)
   - Runs Riskfolio-Lib optimization (mean-variance, risk parity, max Sharpe, or CVaR)
   - Generates trade proposals from target weights
   - Validates constraints (turnover, costs)
6. **Metadata Attachment:** Attach traceability metadata (source, asof_date, TTL=0 for no caching)
7. **Error Recovery:** Return empty trades array with error message if optimization fails

### Dependencies on Other Capabilities
- **Implicit dependency:** ratings from RatingsAgent (passed via state or parameter)
- **Implicit dependency:** positions from FinancialAnalyst.ledger_positions (can be passed via state)

### External API Calls
- **Riskfolio-Lib:** Called asynchronously via `asyncio.to_thread` for optimization
  - Supports: Mean-Variance, Risk Parity, Max Sharpe, CVaR methods
  - Uses 252-day historical lookback for covariance estimation

### Key Patterns
- **Pattern Compatibility:** Handles `policies` and `constraints` parameters for workflow pattern integration
- **State Resolution:** Extracts ratings from state if not provided as parameter
- **Caller-Supplied Data:** Can accept pre-fetched positions to avoid DB queries
- **Metadata TTL:** TTL=0 means no caching (always fresh trade proposals)
- **Logging:** Info level for execution flow, Error level with traceback on failures

---

## Method 2: optimizer_analyze_impact()

### Method Signature
```python
async def optimizer_analyze_impact(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
    proposed_trades: Optional[List[Dict[str, Any]]] = None,
    current_positions: Optional[List[Dict[str, Any]]] = None,
    **kwargs,
) -> Dict[str, Any]:
```

### Location
**File:** `/Users/mdawson/Documents/GitHub/DawsOSP/backend/app/agents/optimizer_agent.py`  
**Lines:** 235-349 (115 lines total)

### Service Dependencies
- **Primary:** `get_optimizer_service()` (line 318)
  - Calls: `optimizer_service.analyze_impact()`
- No direct database access

### Input Validation
1. **Portfolio ID Resolution (lines 283-289):**
   - Same pattern as propose_trades
   - Validates from parameter or `ctx.portfolio_id`
   - Converts to `UUID`

2. **Proposed Trades Resolution (lines 291-304):**
   - Multi-location resolution hierarchy:
     1. Direct parameter `proposed_trades`
     2. `state["proposed_trades"]`
     3. `state["rebalance_result"]["trades"]`
   - **Critical:** Requires proposed_trades (cannot be empty)
   - Raises `ValueError` with helpful message if missing

3. **Context Validation (lines 306-309):**
   - Requires `ctx.pricing_pack_id`

### Database Queries
**None** - OptimizerService.analyze_impact() queries:
- Current positions from `lots` table
- Applies trade simulations (no DB writes)

### Return Structure
```python
Dict[str, Any] with keys:
{
    "current_value": Decimal
    "post_rebalance_value": Decimal
    "value_delta": Decimal
    
    "current_div_safety": float (optional)
    "post_div_safety": float (optional)
    "div_safety_delta": float (optional)
    
    "current_moat": float (optional)
    "post_moat": float (optional)
    "moat_delta": float (optional)
    
    "current_concentration": float (% in top 10)
    "post_concentration": float (% in top 10)
    "concentration_delta": float
    
    "te_delta": float (tracking error delta, optional)
    
    "_metadata": Dict with agent metadata
}
```

### Error Handling
**Try/Except Pattern (lines 320-349):**
- Same structure as propose_trades
- Returns minimal error result with zeros on failure
- Always attaches metadata

### Business Logic Flow

1. **Portfolio & Pricing Resolution:** Same as propose_trades
2. **Proposed Trades Resolution:** Extract from multiple possible locations in state
3. **Service Call:** OptimizerService.analyze_impact() which:
   - Loads current positions from database
   - Simulates trades to get post-rebalance positions
   - Calculates concentration metrics (top 10 holdings)
   - Computes value deltas
   - **TODO items noted in source:** Expected return, volatility, Sharpe, max drawdown calculations pending historical data integration
4. **Metadata:** TTL=0 (no caching, impact analysis always fresh)
5. **Error Recovery:** Returns zero values with error message

### Dependencies on Other Capabilities
- **Explicit dependency:** optimizer.propose_trades output (proposed_trades parameter)
- **Implicit dependency:** FinancialAnalyst.ledger_positions (for current positions)

### External API Calls
- None (pure data transformation)

### Key Patterns
- **Smart state extraction:** Searches multiple paths in state dict for proposed_trades
- **Before/After paradigm:** Compares portfolio metrics pre- and post-rebalance
- **Concentration focus:** Top 10 holdings metric is primary indicator
- **Extensibility:** TODO marks show this is incomplete (Sharpe, return, volatility pending)

---

## Method 3: optimizer_suggest_hedges()

### Method Signature
```python
async def optimizer_suggest_hedges(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
    scenario_id: Optional[str] = None,
    scenario_result: Optional[Dict[str, Any]] = None,  # Pattern compatibility
    max_cost_bps: float = 20.0,
    **kwargs,
) -> Dict[str, Any]:
```

### Location
**File:** `/Users/mdawson/Documents/GitHub/DawsOSP/backend/app/agents/optimizer_agent.py`  
**Lines:** 351-456 (106 lines total)

### Service Dependencies
- **Primary:** `get_optimizer_service()` (line 424)
  - Calls: `optimizer_service.suggest_hedges()`
- **Secondary (in service):** `get_scenario_service()` - OptimizerService internally calls:
  - `scenario_service.apply_scenario()`
  - `scenario_service.suggest_hedges()`

### Input Validation
1. **Portfolio ID Resolution (lines 393-399):**
   - Same pattern as other methods

2. **Scenario ID Resolution (lines 401-410):**
   - Handles `scenario_result` parameter (from pattern)
   - Extracts `scenario_id` from dict keys: "scenario_id", "id", "scenario_type", "name"
   - Falls back to `scenario_id` parameter
   - **Critical:** Either `scenario_id` or `scenario_result` required

3. **Context Validation (lines 412-415):**
   - Requires `ctx.pricing_pack_id`

### Database Queries
**None in agent** - OptimizerService.suggest_hedges() calls ScenarioService which may query databases for:
- Current positions
- Historical returns for scenario application

### Return Structure
```python
Dict[str, Any] with keys:
{
    "hedges": List[Dict] with structure:
        {
            "instrument": str (symbol or description)
            "instrument_type": str ("equity", "option", "futures", "etf")
            "action": "BUY"|"SELL"
            "notional": Decimal (dollar notional)
            "hedge_ratio": float (0-1)
            "rationale": str
            "expected_offset_pct": float (% of loss offset)
        }
    
    "total_notional": Decimal
    "expected_offset_pct": float
    "scenario_id": str
    "_metadata": Dict with agent metadata
}
```

### Error Handling
**Try/Except Pattern (lines 426-456):**
- Catches exceptions from scenario service
- Returns empty hedges with error message
- Logs error with traceback

### Business Logic Flow

1. **Portfolio & Pricing Resolution:** Standard validation
2. **Scenario ID Extraction:** From `scenario_result` dict or direct parameter
3. **Service Call:** OptimizerService.suggest_hedges() which:
   - Maps scenario_id to ShockType enum (rates_up, equity_selloff, usd_up, credit_spread_widening)
   - Calls ScenarioService.apply_scenario() to identify losers
   - Calls ScenarioService.suggest_hedges() to get recommendations
   - Formats recommendations into hedge dicts
   - Calculates total notional and expected offset percentage
4. **Metadata:** TTL=3600 seconds (1 hour cache - scenario hedges are relatively stable)
5. **Error Recovery:** Returns empty hedges with error

### Dependencies on Other Capabilities
- **ScenarioService dependency:** For scenario application and hedge recommendations
- **Pattern integration:** Works with scenario_result from prior pattern steps

### External API Calls
- None in agent layer (delegated to services)

### Key Patterns
- **Scenario Mapping:** 10+ scenario types mapped to ShockType enum (rates_up, equity_selloff, usd_up, etc.)
- **Intelligent Extraction:** Can extract scenario_id from multiple dict formats
- **Caching Strategy:** Unlike trade proposals, hedges can be cached (1 hour)
- **Instrument Types:** Supports equities, options, futures, ETFs

### Supported Scenarios
From service code (optimizer.py:634-646):
```python
"rates_up" → ShockType.RATES_UP
"rates_down" → ShockType.RATES_DOWN
"usd_up" → ShockType.USD_UP
"usd_down" → ShockType.USD_DOWN
"inflation"/"cpi_surprise" → ShockType.CPI_SURPRISE
"credit_spread_widening" → ShockType.CREDIT_SPREAD_WIDENING
"equity_selloff" → ShockType.EQUITY_SELLOFF
"equity_rally" → ShockType.EQUITY_RALLY
"late_cycle_rates_up" → ShockType.RATES_UP
"recession_mild" → ShockType.EQUITY_SELLOFF
```

---

## Method 4: optimizer_suggest_deleveraging_hedges()

### Method Signature
```python
async def optimizer_suggest_deleveraging_hedges(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
    regime: Optional[str] = None,
    scenarios: Optional[Dict[str, Any]] = None,  # Pattern compatibility
    ltdc_phase: Optional[str] = None,  # Pattern compatibility
    **kwargs,
) -> Dict[str, Any]:
```

### Location
**File:** `/Users/mdawson/Documents/GitHub/DawsOSP/backend/app/agents/optimizer_agent.py`  
**Lines:** 458-593 (136 lines total)

### Service Dependencies
- **Primary:** `get_optimizer_service()` (line 561)
  - Calls: `optimizer_service.suggest_deleveraging_hedges()`
- No external service dependencies beyond DB

### Input Validation
1. **Portfolio ID Resolution (lines 502-508):**
   - Standard pattern

2. **Regime Resolution (lines 510-547):**
   - Multi-source resolution with priority:
     1. Direct `regime` parameter
     2. Extract from `ltdc_phase` via mapping:
        ```python
        "Phase 1" → "LATE_EXPANSION"
        "Phase 2" → "DELEVERAGING"
        "Phase 3" → "DEPRESSION"
        "Phase 4" → "EARLY_EXPANSION"
        ```
     3. Infer from `scenarios` dict - find most severe scenario impact
     4. Get from state["regime"] (from macro.detect_regime)
   - **Critical:** One of these sources must provide regime

3. **Context Validation (lines 549-552):**
   - Requires `ctx.pricing_pack_id`

### Database Queries
**None in agent** - OptimizerService.suggest_deleveraging_hedges() queries:
- Current positions from `lots` table

### Return Structure
```python
Dict[str, Any] with keys:
{
    "recommendations": List[Dict] with structure:
        {
            "action": str (e.g., "reduce_equity_exposure", "increase_safe_havens")
            "instruments": List[str] (symbols or descriptions)
            "rationale": str
            "target_reduction_pct": float (only for reduction actions)
            "target_allocation_pct": float (only for allocation actions)
        }
    
    "regime": str
    "total_reduction_pct": float
    "total_allocation_pct": float
    "_metadata": Dict with agent metadata
}
```

### Error Handling
**Try/Except Pattern (lines 563-593):**
- Same as other methods
- Returns empty recommendations on error
- Logs with traceback

### Business Logic Flow

1. **Portfolio & Pricing Resolution:** Standard
2. **Regime Determination:** Multi-source resolution with hierarchy
   - Direct parameter → LTDC phase mapping → Scenario inference → State extraction
3. **Service Call:** OptimizerService.suggest_deleveraging_hedges() which:
   - Loads current positions
   - Gets regime-specific recommendations via `_get_deleveraging_recommendations()`
   - Returns list of action dicts
4. **Metadata:** TTL=3600 seconds (1 hour cache)
5. **Error Recovery:** Empty recommendations with error message

### Dependencies on Other Capabilities
- **Implicit:** Macro.detect_regime (regime passed via state)
- **Pattern integration:** Works with LTDC phase or scenario results from prior steps

### External API Calls
- None in agent (delegated to service)

### Key Patterns
- **Dalio Deleveraging Framework:** Three main regimes with specific playbooks:
  
  **DELEVERAGING/DEPRESSION** (Aggressive):
  - Reduce equity 40%
  - Increase safe havens (GLD, TLT, CASH) to 30%
  - Exit high-yield credit 100% (HYG, JNK)
  
  **LATE_EXPANSION** (Moderate):
  - Reduce equity 20%
  - Increase defensive sectors 15% (XLU, XLP, VNQ)
  
  **REFLATION** (Inflation protection):
  - Reduce long-duration bonds 50% (TLT, IEF)
  - Increase inflation hedges 20% (GLD, TIP, DBC)

- **Multi-source regime input:** Can accept regime directly, infer from LTDC phase, or derive from scenario severity

---

## Helper Methods & Utilities (OptimizerService)

### Private Methods Used by the 4 Agents

#### `_parse_policy()` (Line 836)
- **Purpose:** Convert policy JSON dict to PolicyConstraints dataclass
- **Used by:** propose_trades
- **Returns:** PolicyConstraints with typed fields

#### `_fetch_current_positions()` (Line 853)
- **Purpose:** Load portfolio positions from `lots` table
- **Used by:** propose_trades, analyze_impact, suggest_deleveraging_hedges
- **Query:** Joins lots with prices table, groups by security, ordered by value DESC
- **Returns:** List[Dict] with symbol, security_id, quantity, price, value, currency

#### `_filter_by_quality()` (Line 910)
- **Purpose:** Filter positions by minimum quality rating
- **Used by:** propose_trades
- **Returns:** Filtered position list, logs excluded positions

#### `_fetch_price_history()` (Line 930)
- **Purpose:** Fetch historical prices for covariance estimation
- **Used by:** propose_trades
- **Lookback:** 252 days default (configurable)
- **Query:** Returns historical prices from `prices` table
- **Returns:** pandas DataFrame with dates as index, symbols as columns
- **Data Handling:** Forward fill then backward fill for missing values

#### `_run_optimization()` (Line 993)
- **Purpose:** Execute Riskfolio-Lib optimization
- **Used by:** propose_trades
- **Methods Supported:**
  - `mean_variance` (default) - Markowitz optimization
  - `risk_parity` - Equal risk contribution
  - `max_sharpe` - Maximum Sharpe ratio
  - `cvar` - Conditional Value at Risk (CVaR)
- **Threading:** Wrapped in asyncio.to_thread (Riskfolio is synchronous)
- **Returns:** pd.Series of target weights

#### `_optimize_sync()` (Line 1025)
- **Purpose:** Synchronous Riskfolio optimization kernel
- **Used by:** _run_optimization (via asyncio.to_thread)
- **Constraints Enforced:**
  - min_position_pct: Minimum weight to avoid dust
  - max_single_position_pct: Maximum position size
- **Covariance:** Historical method
- **Returns:** Normalized pd.Series weights

#### `_equal_weight_fallback()` (Line 1087)
- **Purpose:** Fallback when optimization fails (insufficient data)
- **Returns:** Equal weights across all positions

#### `_generate_trade_proposals()` (Line 1097)
- **Purpose:** Convert target weights to actual trade proposals
- **Used by:** propose_trades
- **Logic:**
  1. For each position, calculate current and target values
  2. Determine target shares from target weight
  3. Skip negligible trades (< 1 share or < $100)
  4. Classify as BUY or SELL
  5. Calculate trade costs (commission + market impact)
- **Returns:** List[Dict] of trade proposals

#### `_estimate_trade_cost()` (Line 1167)
- **Purpose:** Estimate commission + market impact
- **Calculation:**
  - Flat commission per trade
  - Market impact: trade_value × (market_impact_bps / 10000)
- **Returns:** Decimal total cost

#### `_scale_trades_to_turnover_limit()` (Line 1192)
- **Purpose:** Reduce trades if they exceed turnover constraint
- **Used by:** propose_trades when turnover > max_turnover_pct
- **Method:** Proportionally scale all trades by scale_factor
- **Returns:** Reduced trade proposals

#### `_simulate_trades()` (Line 1241)
- **Purpose:** Apply proposed trades to current positions
- **Used by:** analyze_impact
- **Returns:** Post-rebalance position list

#### `_calculate_concentration_top10()` (Line 1261)
- **Purpose:** Calculate concentration metric (% in top 10 holdings)
- **Used by:** analyze_impact
- **Returns:** float percentage

#### `_get_scenario_hedges()` (Line 1281)
- **Purpose:** Get hedge recommendations for specific scenario
- **Used by:** suggest_hedges (internal to service)
- **Scenarios:**
  - `rates_up`: Long TLT (long-duration treasuries)
  - `equity_selloff`: VIX calls + SPY puts
  - `usd_up`: Short UUP (USD ETF)
  - `credit_spread_widening`: LQD puts (IG credit)
- **Returns:** List[HedgeRecommendation]

#### `_get_deleveraging_recommendations()` (Line 1368)
- **Purpose:** Get regime-specific deleveraging playbook
- **Used by:** suggest_deleveraging_hedges
- **Regimes:** DELEVERAGING/DEPRESSION, LATE_EXPANSION, REFLATION
- **Returns:** List[Dict] with action, instruments, targets, rationale

#### `_get_pack_date()` (Line 1446)
- **Purpose:** Get asof_date from pricing pack
- **Returns:** date object

#### `_dataclass_to_dict()` (Line 1457)
- **Purpose:** Convert dataclass instances to dicts
- **Handles:** Decimal → float, date/datetime → ISO string, nested dataclasses
- **Returns:** Dict

#### `_empty_rebalance_result()` (Line 1479)
- **Purpose:** Return empty rebalance (no trades scenario)
- **Returns:** RebalanceResult dict with trade_count=0

#### `_stub_rebalance_result()` (Line 1505)
- **Purpose:** Return stub when Riskfolio not installed
- **Returns:** RebalanceResult dict with warning about missing library

#### `_empty_impact_analysis()` (Line 1533)
- **Purpose:** Return empty impact analysis
- **Returns:** ImpactAnalysis dict with zeros

#### `_mock_execute_query()`, `_mock_execute_query_one()`, `_mock_execute_statement()` (Lines 278-347)
- **Purpose:** Mock database methods for testing
- **Used when:** use_db=False in OptimizerService init
- **Returns:** Stub data for testing without database

---

## Shared State & Class Variables

### OptimizerService Instance Variables
```python
self.use_db: bool              # Whether to use real database
self.riskfolio_available: bool # Whether Riskfolio-Lib is installed
self.execute_query: callable   # Database query executor
self.execute_query_one: callable # Database single-row executor
self.execute_statement: callable # Database statement executor
```

### No Shared State Across Requests
- All operations are request-scoped (no cross-request state)
- Service is stateless (pure functions)
- Database connections obtained per-request

---

## Logging Patterns

### Log Levels Used
- **INFO:** Execution flow, operation start/completion
  ```python
  logger.info(f"optimizer.propose_trades: portfolio_id={portfolio_id}, ...")
  logger.info(f"Generated {len(trades)} trade proposals, turnover={turnover_pct:.1f}%")
  ```

- **WARNING:** Data issues, constraint violations, missing libraries
  ```python
  logger.warning(f"Riskfolio-Lib not available. Optimizer will return stub data.")
  logger.warning(f"Turnover {turnover_pct:.1f}% exceeds limit...")
  ```

- **ERROR:** Exceptions with traceback
  ```python
  logger.error(f"Trade proposal generation failed: {e}", exc_info=True)
  ```

### Logging Context
- Consistent use of agent name prefix: "DawsOS.OptimizerAgent"
- Operation names included in log messages
- Performance metrics included (turnover %, costs)

---

## Data Flow Diagram

```
Pattern Request
    ↓
OptimizerAgent Method (agent layer)
    ├─ Resolve parameters from multiple sources
    ├─ Validate context (portfolio_id, pricing_pack_id)
    └─ Call OptimizerService
        ↓
OptimizerService Method (service layer)
    ├─ For propose_trades:
    │   ├─ Parse policy constraints
    │   ├─ Fetch positions from DB (or use caller-supplied)
    │   ├─ Filter by quality rating
    │   ├─ Fetch price history (252 days)
    │   ├─ Run Riskfolio-Lib optimization
    │   ├─ Generate trade proposals
    │   └─ Validate constraints
    │
    ├─ For analyze_impact:
    │   ├─ Fetch current positions
    │   ├─ Simulate proposed trades
    │   └─ Calculate metrics (concentration, value delta)
    │
    ├─ For suggest_hedges:
    │   ├─ Map scenario_id to ShockType
    │   ├─ Call ScenarioService.apply_scenario()
    │   └─ Call ScenarioService.suggest_hedges()
    │
    └─ For suggest_deleveraging_hedges:
        ├─ Fetch positions
        └─ Return regime-specific playbook
        ↓
Result Dict
    ↓
Agent attaches metadata
    ↓
Return to pattern/client
```

---

## Critical Dependencies for Consolidation

### Database Tables Required
1. **lots** - Portfolio positions
   - Columns: portfolio_id, security_id, symbol, quantity, is_open, currency
2. **prices** - Security prices by date
   - Columns: security_id, pricing_pack_id, close, asof_date, currency
3. **pricing_packs** - Pack metadata
   - Columns: id, date, is_fresh

### Service Dependencies (when consolidated into FinancialAnalyst)
1. **OptimizerService** - Core optimization logic (already exists)
2. **ScenarioService** - For hedge suggestions (in suggest_hedges)
3. **RatingsService** - For quality filtering (passed via ratings param)

### Input Dependencies
1. **ratings** - Quality scores from RatingsAgent (can be in state or param)
2. **positions** - Can accept pre-fetched from FinancialAnalyst (or fetch from DB)
3. **pricing_pack_id** - SACRED - required in RequestCtx

---

## Key Consolidation Considerations

### 1. Method Naming After Consolidation
Current (agent):
- `optimizer_propose_trades()`
- `optimizer_analyze_impact()`
- `optimizer_suggest_hedges()`
- `optimizer_suggest_deleveraging_hedges()`

Proposed consolidation names in FinancialAnalyst:
- `financial_analyst_propose_trades()` or keep as dual-registration
- `financial_analyst_analyze_impact()`
- `financial_analyst_suggest_hedges()`
- `financial_analyst_suggest_deleveraging_hedges()`

Or support both:
- `optimizer_propose_trades()` (backward compat)
- `financial_analyst_propose_trades()` (new)

### 2. Capability Registration
FinancialAnalyst already declares consolidated capabilities (lines 82-87):
```python
"financial_analyst.propose_trades",
"financial_analyst.analyze_impact",
"financial_analyst.suggest_hedges",
"financial_analyst.suggest_deleveraging_hedges",
```

These can be registered with fallback to original OptimizerAgent names for backward compatibility.

### 3. Pattern Compatibility
All 4 methods use pattern-compatible parameter names:
- `policies` and `constraints` (policy.propose_trades pattern)
- `scenario_result` (scenarios.apply_scenario pattern)
- `ltdc_phase` (cycles.detect_phase pattern)

These should be preserved in FinancialAnalyst to maintain pattern compatibility.

### 4. Metadata Handling
Current pattern:
```python
metadata = self._create_metadata(
    source=f"optimizer_service:{ctx.pricing_pack_id}",
    asof=ctx.asof_date or date.today(),
    ttl=0,  # No caching for proposals
)
return self._attach_metadata(result, metadata)
```

All methods use TTL=0 for proposals (always fresh), TTL=3600 for hedges (1 hour cache).

### 5. Error Handling Strategy
All methods use same pattern:
1. Try service call
2. On exception: Log error with traceback
3. Return empty/zero result with error string
4. Always attach metadata even on error

This is consistent and should be preserved.

### 6. Service Layer Interactions
- All methods delegate to OptimizerService
- OptimizerService is stateless (can be shared)
- No modification needed to OptimizerService for consolidation

---

## Potential Issues & Attention Points

### 1. Riskfolio-Lib Dependency
**Issue:** suggest_hedges calls ScenarioService which may have its own dependencies  
**Mitigation:** Verify ScenarioService is available and working

### 2. Insufficient Price History
**Issue:** Less than 30 days of price data causes fallback to equal-weight  
**Behavior:** Method logs warning and returns zero-trade result  
**Consideration:** May need to increase minimum lookback or adjust expectations

### 3. Constraint Violations
**Issue:** If optimization results exceed turnover limit, trades are scaled down  
**Behavior:** Trades are proportionally reduced, warning added  
**Consideration:** Final weights may not achieve optimization target

### 4. Quality Filtering
**Issue:** If all positions filtered out by quality score, returns empty trades  
**Behavior:** Logs info about excluded positions  
**Consideration:** May leave portfolio unoptimized if quality standards too strict

### 5. Pattern State Integration
**Issue:** Methods search state dict multiple places for required params  
**Consideration:** State dict structure must be consistent with pattern execution order

### 6. Async/Await Patterns
**Issue:** Uses asyncio.to_thread for Riskfolio synchronous code  
**Consideration:** Could be performance bottleneck with large portfolios (requires thread pool)

### 7. TODO Items in analyze_impact
**Issue:** Service code has TODO for Sharpe, volatility, max DD calculations  
**Status:** Currently not implemented, would return None for these fields  
**Impact:** Impact analysis is incomplete compared to full capability

---

## Summary Table

| Method | Lines | Service Call | DB Queries | Cacheable | Error Recovery |
|--------|-------|--------------|-----------|-----------|-----------------|
| propose_trades | 171 | propose_trades | Via service | No (TTL=0) | Empty trades list |
| analyze_impact | 115 | analyze_impact | Via service | No (TTL=0) | Zero values |
| suggest_hedges | 106 | suggest_hedges | Via service + ScenarioService | 1hr (TTL=3600) | Empty hedges |
| suggest_deleveraging_hedges | 136 | suggest_deleveraging_hedges | Via service | 1hr (TTL=3600) | Empty recommendations |

---

## Consolidation Checklist

- [ ] Add 4 methods to FinancialAnalyst class
- [ ] Update get_capabilities() to register new capability names
- [ ] Ensure OptimizerService is available as service dependency
- [ ] Update capability registry for dual registration (backward compat)
- [ ] Test pattern compatibility (policies, constraints, scenario_result)
- [ ] Verify state dict parameter extraction works correctly
- [ ] Test with missing optional parameters (ratings, positions)
- [ ] Verify error handling and empty result generation
- [ ] Update logging (agent name prefix may change)
- [ ] Document new capabilities in FinancialAnalyst docstring
- [ ] Consider deprecation timeline for OptimizerAgent

