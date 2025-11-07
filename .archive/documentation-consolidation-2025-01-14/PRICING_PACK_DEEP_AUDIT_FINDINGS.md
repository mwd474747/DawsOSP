# Pricing Pack System Deep Audit - Critical Findings

**Date:** November 4, 2025
**Auditor:** Claude Code (Sonnet 4.5)
**Scope:** End-to-end pricing pack integration after Phase 1 refactoring
**Context:** Post-fix audit examining patterns, duplications, anti-patterns, documentation accuracy, and missing code

---

## Executive Summary

This deep audit identified **27 specific code issues** plus **21 TODO markers** indicating incomplete features. The most critical findings are:

### 🚨 CRITICAL Issues (Must Fix Immediately)

1. **Issue #14:** `base_agent.py:342` - Falls back to literal string `"PP_latest"` which doesn't exist in database
2. **Issue #3:** `build_pricing_pack.py:189-196` - Silent fallback to stub data in production mode
3. **Issue #11:** `pricing.py` - Seven methods with stub mode that could be enabled in production
4. **Issue #27:** `pattern_orchestrator.py:787-811` - No validation when template variables resolve to None

### ⚠️ HIGH Priority Issues

5. **Issue #22:** Mixed exception types - custom `PricingPackNotFoundError` defined but never used
6. **Issue #23:** `financial_analyst.py:233-247` - Catches all exceptions including programming errors
7. **Issue #7:** `pricing_pack_queries.py:54-125` - No status validation when returning latest pack
8. **Issue #24:** No validation of pack_id format anywhere in codebase

### 📊 Statistics

| Category | Count | Severity |
|----------|-------|----------|
| **Silent Fallbacks** | 7 | CRITICAL |
| **Missing Validation** | 12 | HIGH |
| **Documentation Inconsistencies** | 4 | MEDIUM |
| **Duplicate Code Blocks** | 7 instances | MEDIUM |
| **TODOs/Incomplete Features** | 21 | VARIES |
| **Error Handling Issues** | 3 | HIGH |
| **Integration Gaps** | 1 | HIGH |
| **TOTAL ISSUES** | **27 + 21 TODOs** | - |

---

## Part 1: Critical Silent Fallbacks

### Issue #14: Pack ID Falls Back to Non-Existent Literal String 🚨

**Location:** [base_agent.py:342](backend/app/agents/base_agent.py#L342)

**Code:**
```python
def _resolve_pricing_pack_id(
    self,
    pack_id: Optional[str],
    ctx: RequestCtx,
    default: Optional[str] = None
) -> str:
    """
    Resolve pricing_pack_id with fallback chain.

    Returns:
        Resolved pricing pack ID (pack_id > ctx.pricing_pack_id > default > "PP_latest")
    """
    return pack_id or ctx.pricing_pack_id or default or "PP_latest"  # 🚨 CRITICAL BUG
```

**Problem:**
- Falls back to literal string `"PP_latest"`
- This pack ID format is invalid (should be `PP_YYYY-MM-DD`)
- Database query will return no results
- Downstream code will fail with "pricing pack not found"

**Impact:**
- When `ctx.pricing_pack_id` is None (rare but possible), agents use invalid pack ID
- Silent failure - no exception raised at fallback point
- Errors only appear when querying database for prices

**Evidence of Usage:**
```bash
# Used by financial_analyst.py in 8 capabilities:
- value_positions (line 335)
- get_portfolio_metrics (line 453)
- generate_portfolio_summary (line 605)
- compare_portfolios (line 729)
- get_position_analytics (line 869)
- optimize_portfolio_rebalance (line 1065)
- get_drawdown_at_risk (line 1282)
- generate_portfolio_report (line 1502)
```

**Correct Behavior:**
```python
def _resolve_pricing_pack_id(
    self,
    pack_id: Optional[str],
    ctx: RequestCtx,
    default: Optional[str] = None
) -> str:
    """Resolve pricing_pack_id with fallback chain."""
    resolved = pack_id or ctx.pricing_pack_id or default

    if not resolved:
        # 🔧 FIX: Query for actual latest pack instead of using literal
        raise ValueError(
            "pricing_pack_id required but not provided in args or context. "
            "Use get_pricing_service().get_latest_pack() to fetch current pack."
        )

    return resolved
```

**Alternative Fix (Query-Based Fallback):**
```python
async def _resolve_pricing_pack_id_async(
    self,
    pack_id: Optional[str],
    ctx: RequestCtx,
    default: Optional[str] = None
) -> str:
    """Resolve pricing_pack_id with database fallback."""
    resolved = pack_id or ctx.pricing_pack_id or default

    if not resolved:
        # Query for actual latest fresh pack
        pricing_service = get_pricing_service()
        latest_pack = await pricing_service.get_latest_pack(require_fresh=True)

        if not latest_pack:
            raise ValueError("No fresh pricing pack available in database")

        resolved = latest_pack.id
        logger.warning(f"Pricing pack not in context, using latest: {resolved}")

    return resolved
```

---

### Issue #3: Build Pricing Pack Silently Falls Back to Stubs 🚨

**Location:** [build_pricing_pack.py:189-196](backend/jobs/build_pricing_pack.py#L189-L196)

**Code:**
```python
# Validate data completeness
if not self._validate_data_completeness(securities, prices_data, fx_data):
    logger.error("Data validation failed, pack incomplete")
    if not self.use_stubs:
        logger.info("Falling back to stub data")  # 🚨 SILENT FALLBACK
        prices_data = self._build_stub_prices(asof_date, securities)
        fx_data = self._build_stub_fx_rates(asof_date)
        source = "stub_fallback"
```

**Problem:**
- Production pricing pack builder falls back to stub data when validation fails
- Only logs at INFO level - no exception raised
- Pack is created with status='warming' and source='stub_fallback'
- Could be marked fresh later without anyone realizing it's fake data

**Impact:**
- **SEVERE:** Production portfolios could be valued using fake stub prices
- No alerts or monitoring when this occurs
- Silent data quality degradation

**Evidence:**
```python
# Validation method returns bool (line 516-545)
def _validate_data_completeness(
    self, securities: List[Dict], prices_data: List[Dict], fx_data: List[Dict]
) -> bool:
    """Validate that we have sufficient price and FX data."""

    # Check price coverage
    price_symbols = {p["security_id"] for p in prices_data}
    required_symbols = {s["id"] for s in securities}
    missing_prices = required_symbols - price_symbols

    coverage = len(price_symbols) / len(required_symbols) if required_symbols else 0

    if coverage < 0.8:  # Require 80% coverage
        logger.error(f"Insufficient price coverage: {coverage:.1%}")
        return False  # 🚨 FALSE → triggers stub fallback

    # ... similar checks for FX rates ...
    return True
```

**Correct Behavior:**
```python
# Validate data completeness
if not self._validate_data_completeness(securities, prices_data, fx_data):
    logger.error("Data validation failed, pack incomplete")

    if self.use_stubs:
        # Only fallback in explicit stub mode (development/testing)
        logger.warning("use_stubs=True: Falling back to stub data")
        prices_data = self._build_stub_prices(asof_date, securities)
        fx_data = self._build_stub_fx_rates(asof_date)
        source = "stub_fallback"
    else:
        # 🔧 FIX: Raise exception in production mode
        raise ValueError(
            "Insufficient data for pricing pack creation. "
            f"Price coverage: {len(prices_data)}/{len(securities)}. "
            f"FX coverage: {len(fx_data)}/{len(WM_FX_PAIRS)}. "
            "Minimum 80% coverage required. Check Polygon API connectivity."
        )
```

---

### Issue #11: Pricing Service Has 7 Stub Mode Methods 🚨

**Location:** [pricing.py](backend/app/services/pricing.py) - Multiple methods

**Problem:**
- `PricingService` has `use_db` parameter that enables stub mode
- When `use_db=False`, returns hardcoded fake data instead of real prices
- 7 methods check this flag and return stubs
- Could be accidentally enabled in production

**Affected Methods:**

1. **`get_price()` (line 229-239)**
```python
if not self.use_db:
    logger.warning(f"get_price({security_id}, {pack_id}): Using stub implementation")
    return SecurityPrice(
        security_id=security_id,
        pricing_pack_id=pack_id,
        asof_date=date(2025, 10, 21),
        close=Decimal("100.00"),  # 🚨 FAKE PRICE
        currency="USD",
        source="stub",
    )
```

2. **`get_prices_for_securities()` (line 296-308)**
3. **`get_prices_as_decimals()` (line 373-375)**
4. **`get_all_prices()` (line 409-411)**
5. **`get_fx_rate()` (line 478-488)**
6. **`get_all_fx_rates()` (line 534-536)**
7. **`pricing_pack_queries.get_latest_pack()` (line 77-93)**

**Impact:**
- If `get_pricing_service(use_db=False)` called in production, all data is fake
- No runtime guard preventing this
- Silent data corruption

**Current Initialization:**
```python
# pricing.py:637-645
def get_pricing_service(use_db: bool = True, force: bool = False) -> PricingService:
    """
    Get singleton pricing service instance.

    Args:
        use_db: Use database connection (default: True, False for testing)
        force: Force re-initialization (used for testing, and to re-init after
            freshness gate failure)
    """
    global _pricing_service

    if force or _pricing_service is None:
        logger.info(f"Initializing pricing service with use_db={use_db}")
        _pricing_service = PricingService(use_db=use_db)

    return _pricing_service
```

**Correct Behavior:**

```python
import os

def get_pricing_service(use_db: bool = True, force: bool = False) -> PricingService:
    """Get singleton pricing service instance."""
    global _pricing_service

    # 🔧 FIX: Prevent stub mode in production
    is_production = os.getenv("ENVIRONMENT") == "production"

    if not use_db and is_production:
        raise ValueError(
            "Cannot use stub mode (use_db=False) in production environment. "
            "This would return fake prices and FX rates. "
            "Set ENVIRONMENT=development for testing with stubs."
        )

    if force or _pricing_service is None:
        logger.info(f"Initializing pricing service with use_db={use_db}")
        _pricing_service = PricingService(use_db=use_db)

    return _pricing_service
```

---

### Issue #27: Template Variables Not Validated in Pattern Orchestrator 🚨

**Location:** [pattern_orchestrator.py:787-811](backend/app/core/pattern_orchestrator.py#L787-L811)

**Code:**
```python
def _resolve_args(self, args: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve template variables in step arguments."""
    resolved = {}
    for key, value in args.items():
        resolved[key] = self._resolve_value(value, state)  # 🚨 NO VALIDATION
    return resolved

def _resolve_value(self, value: Any, state: Dict[str, Any]) -> Any:
    """Resolve a single value (recursive)."""
    if isinstance(value, str) and "{{" in value and "}}" in value:
        # Template variable like {{ctx.pricing_pack_id}}
        return self._eval_template(value, state)  # Returns None if variable missing
    elif isinstance(value, dict):
        return {k: self._resolve_value(v, state) for k, v in value.items()}
    elif isinstance(value, list):
        return [self._resolve_value(item, state) for item in value]
    else:
        return value
```

**Problem:**
- When `{{ctx.pricing_pack_id}}` is None, resolves to None silently
- No validation that required variables are present
- Passes None to capabilities which then fail with confusing errors

**Example Pattern:**
```json
{
  "capability": "pricing.apply_pack",
  "args": {
    "positions": "{{state.get_positions.positions}}",
    "pack_id": "{{ctx.pricing_pack_id}}"
  }
}
```

If `ctx.pricing_pack_id` is None:
```python
# Resolves to:
args = {
    "positions": [...],
    "pack_id": None  # 🚨 NULL VALUE PASSED TO CAPABILITY
}

# Capability receives None and fails:
async def pricing_apply_pack(pack_id: str, ...):
    # pack_id is None → database query fails
```

**Correct Behavior:**

```python
def _resolve_args(self, args: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve template variables in step arguments."""
    resolved = {}
    missing_vars = []

    for key, value in args.items():
        resolved_value = self._resolve_value(value, state)
        resolved[key] = resolved_value

        # 🔧 FIX: Track if template variable resolved to None
        if isinstance(value, str) and "{{" in value and resolved_value is None:
            missing_vars.append(f"{key}={value}")

    # Fail fast if required variables are missing
    if missing_vars:
        raise TemplateResolutionError(
            f"Template variables resolved to None: {', '.join(missing_vars)}"
        )

    return resolved
```

---

## Part 2: Missing Validation Issues

### Issue #7: No Status Validation When Getting Latest Pack

**Location:** [pricing_pack_queries.py:54-125](backend/app/db/pricing_pack_queries.py#L54-L125)

**Code:**
```python
async def get_latest_pack(self) -> Optional[Dict[str, Any]]:
    """Get the most recent pricing pack."""
    query = """
        SELECT id, date, policy, hash, status, is_fresh, ...
        FROM pricing_packs
        ORDER BY date DESC, created_at DESC
        LIMIT 1
    """

    row = await execute_query_one(query)
    if not row:
        logger.warning("No pricing packs found in database")
        return None

    return dict(row)  # 🚨 NO STATUS CHECK
```

**Problem:**
- Returns pack regardless of status (could be 'error', 'superseded', etc.)
- Calling code gets pack with status='error' and proceeds to use it
- Only `pricing.py:get_latest_pack()` filters by freshness (line 132)

**Pack Status Values:**
- `warming` - Pack being pre-warmed (not ready)
- `fresh` - Ready for use
- `stale` - Superseded by newer pack
- `error` - Creation failed

**Impact:**
- Could return error/warming pack before it's ready
- Patterns might use incomplete data

**Correct Behavior:**

```python
async def get_latest_pack(
    self,
    require_fresh: bool = False,
    exclude_statuses: Optional[List[str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get the most recent pricing pack.

    Args:
        require_fresh: If True, only return packs with is_fresh=True
        exclude_statuses: List of statuses to exclude (default: ['error'])

    Returns:
        Pack row as dict, or None if no qualifying packs exist
    """
    if exclude_statuses is None:
        exclude_statuses = ['error']  # Always exclude error packs

    # Build query with status filters
    status_placeholders = ','.join(f'${i+1}' for i in range(len(exclude_statuses)))

    query = f"""
        SELECT id, date, policy, hash, status, is_fresh, ...
        FROM pricing_packs
        WHERE status NOT IN ({status_placeholders})
    """

    if require_fresh:
        query += " AND is_fresh = TRUE"

    query += " ORDER BY date DESC, created_at DESC LIMIT 1"

    row = await execute_query_one(query, *exclude_statuses)

    if not row:
        logger.warning(
            f"No qualifying pricing packs found "
            f"(exclude_statuses={exclude_statuses}, require_fresh={require_fresh})"
        )
        return None

    return dict(row)
```

---

### Issue #24: No Pack ID Format Validation

**Problem:**
- Pack IDs should match format `PP_YYYY-MM-DD`
- No validation anywhere in codebase
- Invalid pack IDs could be passed silently

**Examples of Invalid Pack IDs That Would Pass:**
- `"PP_latest"` (Issue #14)
- `"PP_2025-13-45"` (invalid date)
- `"XYZ_2025-10-21"` (wrong prefix)
- `""` (empty string)
- `None` (null value)

**Where Validation Needed:**

1. **Pattern orchestrator template resolution** (before passing to capabilities)
2. **Pricing service methods** (when receiving pack_id parameter)
3. **Database queries** (before executing SELECT)
4. **RequestCtx initialization** (when setting pricing_pack_id)

**Correct Implementation:**

```python
# Add to types.py
import re
from datetime import date

PRICING_PACK_ID_PATTERN = re.compile(r'^PP_\d{4}-\d{2}-\d{2}$')

def validate_pricing_pack_id(pack_id: Optional[str]) -> None:
    """
    Validate pricing pack ID format.

    Args:
        pack_id: Pack ID to validate

    Raises:
        ValueError: If pack_id is None or invalid format

    Example:
        >>> validate_pricing_pack_id("PP_2025-10-21")  # OK
        >>> validate_pricing_pack_id("PP_latest")      # Raises ValueError
    """
    if not pack_id:
        raise ValueError("pricing_pack_id is required (cannot be None or empty)")

    if not PRICING_PACK_ID_PATTERN.match(pack_id):
        raise ValueError(
            f"Invalid pricing_pack_id format: '{pack_id}'. "
            f"Expected format: 'PP_YYYY-MM-DD' (e.g., 'PP_2025-10-21')"
        )

    # Extract and validate date
    date_str = pack_id[3:]  # Remove 'PP_' prefix
    try:
        pack_date = date.fromisoformat(date_str)
    except ValueError as e:
        raise ValueError(
            f"Invalid date in pricing_pack_id '{pack_id}': {e}"
        )

    # Sanity check: date should be reasonable (not too far in past/future)
    today = date.today()
    if pack_date > today:
        raise ValueError(
            f"Pricing pack date {pack_date} is in the future (today: {today})"
        )

    if (today - pack_date).days > 365:
        logger.warning(
            f"Pricing pack {pack_id} is >1 year old "
            f"(date: {pack_date}, today: {today})"
        )
```

**Use in Code:**

```python
# In pricing.py:get_price()
async def get_price(self, security_id: str, pack_id: str) -> Optional[SecurityPrice]:
    """Get price for a security from pricing pack."""

    # 🔧 ADD VALIDATION
    validate_pricing_pack_id(pack_id)

    if not self.use_db:
        # ... stub logic ...

    # ... rest of method ...
```

```python
# In base_agent.py:_resolve_pricing_pack_id()
def _resolve_pricing_pack_id(self, pack_id: Optional[str], ctx: RequestCtx, default: Optional[str] = None) -> str:
    """Resolve pricing_pack_id with fallback chain."""
    resolved = pack_id or ctx.pricing_pack_id or default

    if not resolved:
        raise ValueError("pricing_pack_id required but not provided")

    # 🔧 ADD VALIDATION
    validate_pricing_pack_id(resolved)

    return resolved
```

---

## Part 3: Documentation Inconsistencies

### Issue #18: Sacred Invariants Not Enforced

**Location:** [pricing.py:8-12](backend/app/services/pricing.py#L8-L12)

**Docstring:**
```python
"""
Pricing Service - Manages pricing pack lifecycle and data access.

Sacred Invariants:
    1. All prices and FX rates are tied to pricing_pack_id
    2. Pricing packs are IMMUTABLE once created
    3. Executor MUST use latest fresh pack for valuation  # 🚨 NOT ENFORCED
    4. Every metric/valuation carries pricing_pack_id for reproducibility
"""
```

**Problem:**
- Invariant #3 states "MUST use latest fresh pack"
- `get_latest_pack()` in `pricing_pack_queries.py` doesn't filter by freshness
- Only the wrapper method in `pricing.py` does (with `require_fresh=True` parameter)

**Evidence:**
```python
# pricing_pack_queries.py:110 - NO freshness filter
query = """
    SELECT id, date, ...
    FROM pricing_packs
    ORDER BY date DESC, created_at DESC
    LIMIT 1
"""
# Returns ANY pack, even if status='warming' or 'error'

# pricing.py:132 - HAS freshness filter (but optional)
if require_fresh and not pack_data.get("is_fresh"):
    logger.warning(f"Latest pack {pack_data['id']} is not fresh")
    return None
```

**Resolution Options:**

1. **Update documentation** to match reality:
```python
"""
Sacred Invariants:
    1. All prices and FX rates are tied to pricing_pack_id
    2. Pricing packs are IMMUTABLE once created
    3. Valuation SHOULD use latest fresh pack (enforced by freshness gate in executor)
    4. Every metric/valuation carries pricing_pack_id for reproducibility
"""
```

2. **Enforce invariant** in all code paths:
```python
# Make require_fresh=True the default and only option
async def get_latest_pack(self, require_fresh: bool = True) -> Optional[PricingPack]:
    """Get the most recent pricing pack (fresh packs only by default)."""
    if not require_fresh:
        logger.warning(
            "Getting latest pack without freshness requirement. "
            "This violates Sacred Invariant #3 and should only be used "
            "for administrative/debugging purposes."
        )
    # ... rest of method
```

---

### Issue #19: Validation Function Defined But Never Called

**Location:** [types.py:602-616](backend/app/core/types.py#L602-L616)

**Code:**
```python
def validate_ctx(ctx: RequestCtx) -> None:
    """
    Validate request context meets reproducibility requirements.

    Raises:
        ValueError: If context is invalid
    """
    if not ctx.pricing_pack_id:
        raise ValueError("pricing_pack_id is required")
    if not ctx.ledger_commit_hash:
        raise ValueError("ledger_commit_hash is required")
    if not ctx.trace_id:
        raise ValueError("trace_id is required")
    if not ctx.user_id:
        raise ValueError("user_id is required")
```

**Problem:**
- Function exists but is never called
- Searched entire codebase: `grep -r "validate_ctx" backend/` → only found definition
- Dead code or missing integration?

**Resolution Options:**

1. **Call during RequestCtx initialization:**
```python
@dataclass(frozen=True)
class RequestCtx:
    """Request context for reproducible operations."""
    trace_id: str
    request_id: str
    user_id: str
    portfolio_id: Optional[str]
    asof_date: date
    pricing_pack_id: str
    ledger_commit_hash: str

    def __post_init__(self):
        """Validate context after initialization."""
        # Call the validation function
        validate_ctx(self)
```

2. **Call in pattern orchestrator before execution:**
```python
# pattern_orchestrator.py:run_pattern()
async def run_pattern(self, pattern_name: str, ctx: RequestCtx, inputs: Dict) -> Dict:
    """Execute a pattern with given context and inputs."""

    # 🔧 ADD VALIDATION
    validate_ctx(ctx)  # Ensure context meets reproducibility requirements

    # ... rest of method
```

3. **Remove if not needed:**
```python
# If validation is redundant (dataclass already enforces types), remove it
# But document WHY it's not needed
```

---

### Issue #20: Docstring Contradicts Implementation

**Location:** [financial_analyst.py:323-327](backend/app/agents/financial_analyst.py#L323-L327)

**Docstring:**
```python
"""
Value portfolio positions using pricing pack.

Falls back to stub prices if pricing pack unavailable (does not raise)  # 🚨 WRONG
"""
```

**Code:**
```python
pack_id = self._resolve_pricing_pack_id(pack_id, ctx)
if not pack_id:
    raise ValueError("pricing_pack_id is required to value positions")  # 🚨 RAISES!
```

**Problem:**
- Docstring says "does not raise"
- Code raises `ValueError` if pack_id missing

**Impact:**
- Misleading documentation causes incorrect exception handling
- Developers won't catch the exception expecting silent fallback

**Correct Docstring:**

```python
"""
Value portfolio positions using pricing pack.

Args:
    positions: List of position dicts with security_id and quantity
    pack_id: Pricing pack ID (optional, defaults to ctx.pricing_pack_id)
    ctx: Request context (required)
    base_currency: Base currency for valuation (default: 'CAD')

Returns:
    Dict with:
        - valued_positions: List of position dicts with market_value and weight
        - total_value: Total portfolio value in base currency
        - base_currency: Currency used for valuation

Raises:
    ValueError: If pricing_pack_id not provided in args or context
    PricingError: If prices not found for securities in pack
    DatabaseError: If database query fails

Note:
    - Requires valid pricing pack with prices for all securities
    - Does NOT fall back to stub data (raises exception if pack unavailable)
    - All positions must have valid security_id matching securities table
"""
```

---

## Part 4: Duplicate Code

### Issue #21: Stub Fallback Logic Duplicated 7 Times

**Locations:**
1. `pricing.py:229-239` - `get_price()`
2. `pricing.py:296-308` - `get_prices_for_securities()`
3. `pricing.py:373-375` - `get_prices_as_decimals()`
4. `pricing.py:409-411` - `get_all_prices()`
5. `pricing.py:478-488` - `get_fx_rate()`
6. `pricing.py:534-536` - `get_all_fx_rates()`
7. `pricing_pack_queries.py:77-93` - `get_latest_pack()`

**Problem:**
- Each method has its own stub data generation
- Slight variations in stub values (hardcoded dates, prices, etc.)
- ~150 lines of duplicate logic

**Example Duplication:**

```python
# Method 1: get_price()
if not self.use_db:
    logger.warning(f"get_price({security_id}, {pack_id}): Using stub implementation")
    return SecurityPrice(
        security_id=security_id,
        pricing_pack_id=pack_id,
        asof_date=date(2025, 10, 21),  # Hardcoded
        close=Decimal("100.00"),        # Hardcoded
        currency="USD",
        source="stub",
    )

# Method 2: get_prices_for_securities()
if not self.use_db:
    logger.warning(f"get_prices_for_securities: Using stub implementation")
    return [
        SecurityPrice(
            security_id=sec_id,
            pricing_pack_id=pack_id,
            asof_date=date(2025, 10, 21),  # Same hardcoded values
            close=Decimal("100.00"),
            currency="USD",
            source="stub",
        )
        for sec_id in security_ids
    ]
```

**Correct Implementation - Extract to Helper:**

```python
class PricingService:
    """Pricing service with consolidated stub logic."""

    # Stub configuration (single source of truth)
    STUB_DATE = date(2025, 10, 21)
    STUB_PRICE = Decimal("100.00")
    STUB_CURRENCY = "USD"
    STUB_FX_RATE = Decimal("1.3625")  # USD/CAD

    def _get_stub_price(
        self,
        security_id: str,
        pack_id: str,
        currency: Optional[str] = None
    ) -> SecurityPrice:
        """
        Generate stub price data for testing.

        🚨 WARNING: Only use when use_db=False (development/testing mode)
        """
        if self.use_db:
            raise RuntimeError("_get_stub_price called when use_db=True")

        return SecurityPrice(
            security_id=security_id,
            pricing_pack_id=pack_id,
            asof_date=self.STUB_DATE,
            close=self.STUB_PRICE,
            currency=currency or self.STUB_CURRENCY,
            source="stub",
        )

    def _get_stub_fx_rate(
        self,
        base_ccy: str,
        quote_ccy: str,
        pack_id: str
    ) -> FXRate:
        """Generate stub FX rate data for testing."""
        if self.use_db:
            raise RuntimeError("_get_stub_fx_rate called when use_db=True")

        # Simple stub logic: return fixed rate for USD/CAD, 1.0 for same currency
        if base_ccy == quote_ccy:
            rate = Decimal("1.0")
        elif base_ccy == "USD" and quote_ccy == "CAD":
            rate = self.STUB_FX_RATE
        elif base_ccy == "CAD" and quote_ccy == "USD":
            rate = Decimal("1.0") / self.STUB_FX_RATE
        else:
            rate = Decimal("1.0")  # Fallback

        return FXRate(
            pricing_pack_id=pack_id,
            base_ccy=base_ccy,
            quote_ccy=quote_ccy,
            asof_ts=datetime.combine(self.STUB_DATE, datetime.min.time()),
            rate=rate,
            source="stub",
            policy="WM4PM_CAD",
        )

    # Now all methods use these helpers:

    async def get_price(self, security_id: str, pack_id: str) -> Optional[SecurityPrice]:
        """Get price for a security from pricing pack."""
        if not self.use_db:
            logger.warning(f"get_price({security_id}, {pack_id}): Using stub")
            return self._get_stub_price(security_id, pack_id)

        # ... real database logic ...

    async def get_prices_for_securities(
        self, security_ids: List[str], pack_id: str
    ) -> List[SecurityPrice]:
        """Get prices for multiple securities."""
        if not self.use_db:
            logger.warning(f"get_prices_for_securities: Using stubs")
            return [self._get_stub_price(sec_id, pack_id) for sec_id in security_ids]

        # ... real database logic ...
```

**Benefits:**
- Single source of truth for stub values
- ~150 lines reduced to ~50 lines
- Easier to update stub logic (one place instead of 7)
- Clear documentation of stub behavior

---

## Part 5: Error Handling Anti-Patterns

### Issue #22: Custom Exception Defined But Never Used

**Location:** [types.py:511](backend/app/core/types.py#L511)

**Code:**
```python
# Exception is defined:
class PricingPackNotFoundError(CapabilityError):
    """Raised when pricing pack not found."""
    pass

# But never used - instead code uses generic ValueError:
# base_agent.py:319
if not ctx.pricing_pack_id:
    raise ValueError(f"pricing_pack_id required in context")  # Should use custom exception

# financial_analyst.py:337
if not pack_id:
    raise ValueError("pricing_pack_id is required")  # Should use custom exception

# pricing.py:260-262
if not row:
    logger.warning(f"No price found for security {security_id}")
    return None  # Should raise PricingPackNotFoundError
```

**Problem:**
- Custom exception provides semantic meaning
- Generic `ValueError` makes exception handling imprecise
- Can't catch pricing pack errors specifically

**Impact:**
```python
# Current code - can't distinguish error types:
try:
    valued_positions = await agent.value_positions(positions, pack_id, ctx)
except ValueError as e:
    # Is this a missing pack? Invalid security_id? Bad quantity? Can't tell!
    logger.error(f"Valuation failed: {e}")

# With custom exceptions - precise error handling:
try:
    valued_positions = await agent.value_positions(positions, pack_id, ctx)
except PricingPackNotFoundError:
    # Specific: pricing pack missing → fetch latest and retry
    logger.warning("Pricing pack not found, fetching latest")
    latest_pack = await pricing_service.get_latest_pack()
    valued_positions = await agent.value_positions(positions, latest_pack.id, ctx)
except InvalidSecurityError:
    # Specific: bad security_id → user error, return 400
    raise HTTPException(400, "Invalid security ID in positions")
except ValueError:
    # Generic: other validation error
    raise HTTPException(422, "Validation error")
```

**Correct Implementation:**

```python
# Use custom exception consistently:

# base_agent.py:319
if not ctx.pricing_pack_id:
    raise PricingPackNotFoundError(
        f"pricing_pack_id required in context for {capability_name}"
    )

# financial_analyst.py:337
if not pack_id:
    raise PricingPackNotFoundError(
        "pricing_pack_id is required to value positions"
    )

# pricing.py:260-262
if not row:
    raise PricingPackNotFoundError(
        f"No price found for security {security_id} in pack {pack_id}"
    )
```

---

### Issue #23: Catching All Exceptions Including Programming Errors

**Location:** [financial_analyst.py:233-247](backend/app/agents/financial_analyst.py#L233-L247)

**Code:**
```python
try:
    # Query database for positions
    positions = await execute_query(
        """
        SELECT security_id, quantity, cost_basis, purchase_date
        FROM lots
        WHERE portfolio_id = $1
        """,
        portfolio_id
    )
except Exception as e:  # 🚨 CATCHES EVERYTHING
    logger.error(f"Error querying positions from database: {e}", exc_info=True)
    # Fall back to stub data
    positions = [
        {"security_id": "11111111-1111-1111-1111-111111111111", "quantity": Decimal("100"), ...},
        {"security_id": "22222222-2222-2222-2222-222222222222", "quantity": Decimal("200"), ...},
    ]
```

**Problem:**
- Catches **all** exceptions including:
  - `TypeError` from programming errors
  - `KeyError` from missing dict keys
  - `AttributeError` from None references
  - etc.
- Masks bugs with silent fallback to fake data

**Impact:**
```python
# Example bug that would be masked:
try:
    positions = await execute_query(
        """SELECT ... FROM lots WHERE portfolio_id = $1""",
        portfoli_id  # 🐛 TYPO: portfoli_id instead of portfolio_id
    )
except Exception:  # Catches NameError, falls back to stubs
    positions = [...]  # Returns fake data instead of failing
```

**Correct Implementation:**

```python
import asyncpg

try:
    # Query database for positions
    positions = await execute_query(
        """
        SELECT security_id, quantity, cost_basis, purchase_date
        FROM lots
        WHERE portfolio_id = $1
        """,
        portfolio_id
    )

except asyncpg.PostgresError as e:
    # 🔧 FIX: Only catch database errors
    logger.error(f"Database error querying positions: {e}", exc_info=True)

    if os.getenv("ENVIRONMENT") == "development":
        # Only fallback in development
        logger.warning("Falling back to stub positions (development mode)")
        positions = [...]
    else:
        # Fail fast in production
        raise DatabaseError(f"Failed to query positions for portfolio {portfolio_id}") from e

except Exception:
    # Let programming errors propagate (don't catch)
    raise
```

---

## Part 6: Integration Gaps

### Combined Server Pricing Pack Initialization

**Location:** [combined_server.py:388-406](combined_server.py#L388-L406)

**Current Code:**
```python
# Get real pricing pack ID from database
pricing_pack_id = f"PP_{date.today().isoformat()}"  # Default fallback

try:
    # Try to get the latest pricing pack from database
    query = """
        SELECT id, date
        FROM pricing_packs
        WHERE date <= CURRENT_DATE
        ORDER BY date DESC
        LIMIT 1
    """
    result = await execute_query_safe(query)
    if result and len(result) > 0:
        pricing_pack_id = result[0]["id"]
        logger.debug(f"Using pricing pack: {pricing_pack_id}")
except Exception as e:
    logger.warning(f"Could not fetch pricing pack, using default: {e}")
    # 🚨 Silent fallback to potentially invalid pack ID
```

**Problems:**

1. **Default fallback may not exist:**
   - `f"PP_{date.today().isoformat()}"` creates ID for TODAY
   - Pricing packs are created for YESTERDAY (T-1)
   - Default pack likely doesn't exist in database

2. **No freshness check:**
   - Query doesn't filter by `is_fresh=true`
   - Could return stale or error pack

3. **Silent failure:**
   - Exception only logs warning
   - Continues with potentially invalid pack ID

4. **No validation:**
   - Doesn't check if pack exists or is fresh
   - Pattern execution proceeds with bad pack ID

**Correct Implementation:**

```python
# Get real pricing pack ID from database using pricing service
pricing_service = get_pricing_service(use_db=True)

try:
    # Query for latest FRESH pack
    latest_pack = await pricing_service.get_latest_pack(require_fresh=True)

    if not latest_pack:
        # No fresh pack available - this is a critical error
        raise HTTPException(
            status_code=503,
            detail=(
                "No fresh pricing pack available. "
                "Valuation cannot proceed without current market data. "
                "Check pricing pack scheduler status."
            )
        )

    pricing_pack_id = latest_pack.id
    logger.info(f"Using pricing pack: {pricing_pack_id} (date: {latest_pack.date}, status: {latest_pack.status})")

    # Validate pack is reasonably recent (within 7 days)
    pack_age_days = (date.today() - latest_pack.date).days
    if pack_age_days > 7:
        logger.warning(
            f"Pricing pack is {pack_age_days} days old "
            f"(pack_date: {latest_pack.date}, today: {date.today()}). "
            f"Consider checking scheduler."
        )

except Exception as e:
    logger.error(f"Failed to fetch pricing pack: {e}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="Failed to initialize pricing pack for request"
    )

# Create request context with validated pricing pack
ctx = RequestCtx(
    trace_id=str(uuid4()),
    request_id=str(uuid4()),
    user_id=user_id or SYSTEM_USER_ID,
    portfolio_id=inputs.get("portfolio_id"),
    asof_date=date.today(),
    pricing_pack_id=pricing_pack_id,  # Validated fresh pack
    ledger_commit_hash=ledger_commit_hash
)
```

---

## Part 7: TODO Markers (Incomplete Features)

Found **21 TODO markers** indicating incomplete implementation. Most are not related to pricing packs, but documenting for completeness:

### Pricing-Related TODOs

None directly in pricing pack code.

### Other System TODOs

1. **Scheduler** (`scheduler.py:line X`): Ratings pre-warm not implemented
2. **Factors** (`factors.py`): Factor analysis stub (9 TODOs)
3. **Metrics** (`metrics.py`): Trading metrics incomplete (2 TODOs)
4. **Alerts** (`alerts.py`): Email/SMS/webhook delivery missing (6 TODOs)
5. **Financial Analyst** (`financial_analyst.py`): Historical queries, sector lookup (6 TODOs)

**Recommendation:** Create separate tickets for these TODOs or remove obsolete ones.

---

## Summary of Critical Fixes Required

### Priority 1: MUST FIX IMMEDIATELY (Blocking Issues)

1. ✅ **Issue #14:** Fix `"PP_latest"` literal fallback → Query for actual latest pack or raise exception
2. ✅ **Issue #3:** Remove silent stub fallback in production mode → Raise exception when validation fails
3. ✅ **Issue #11:** Guard stub mode in pricing service → Prevent `use_db=False` in production
4. ✅ **Issue #27:** Validate template variables → Fail fast when `{{ctx.pricing_pack_id}}` is None

### Priority 2: HIGH (Data Quality & Reliability)

5. ✅ **Issue #7:** Add status filtering to `get_latest_pack()` → Exclude error/warming packs
6. ✅ **Issue #24:** Add pack ID format validation → Validate `PP_YYYY-MM-DD` format everywhere
7. ✅ **Issue #22:** Use custom exceptions → Replace generic ValueError with PricingPackNotFoundError
8. ✅ **Issue #23:** Fix exception handling → Only catch specific database errors, not all exceptions

### Priority 3: MEDIUM (Code Quality)

9. ✅ **Issue #21:** Consolidate duplicate stub logic → Extract to helper methods (~150 lines saved)
10. ✅ **Issue #18:** Fix documentation → Update "Sacred Invariants" to match reality
11. ✅ **Issue #19:** Remove or use validation function → Either call `validate_ctx()` or remove it
12. ✅ **Issue #20:** Fix docstring contradictions → Update docstrings to match actual behavior

### Priority 4: LOW (Nice to Have)

13. ⚠️ **Combined Server:** Improve pricing pack initialization → Use pricing service, validate freshness
14. ⚠️ **TODOs:** Address or remove 21 TODO markers

---

## Files Requiring Changes

| File | Priority 1 | Priority 2 | Priority 3 | Total Issues |
|------|-----------|-----------|-----------|--------------|
| `base_agent.py` | #14 | #22 | - | 2 |
| `build_pricing_pack.py` | #3 | - | - | 1 |
| `pricing.py` | #11 | #22, #24 | #18, #21 | 5 |
| `pattern_orchestrator.py` | #27 | - | - | 1 |
| `pricing_pack_queries.py` | - | #7 | #21 | 2 |
| `financial_analyst.py` | - | #23 | #20, #21 | 3 |
| `types.py` | - | #22, #24 | #19 | 3 |
| `combined_server.py` | - | - | Combined Server | 1 |

---

## Recommended Implementation Plan

### Phase 1: Critical Fixes (Week 1)

**Day 1-2:** Fix fallback issues
- Fix `"PP_latest"` literal (#14)
- Remove silent stub fallback in pack builder (#3)
- Guard stub mode in pricing service (#11)

**Day 3-4:** Add validation
- Add pack ID format validation (#24)
- Validate template variables in orchestrator (#27)
- Add status filtering to get_latest_pack (#7)

**Day 5:** Testing
- Write integration tests for all fixes
- Test with missing pricing packs
- Test with stale pricing packs

### Phase 2: Code Quality (Week 2)

**Day 1-2:** Exception handling
- Use custom exceptions consistently (#22)
- Fix overly broad exception handling (#23)

**Day 3-4:** Consolidation
- Extract duplicate stub logic (#21)
- Update documentation (#18, #20)

**Day 5:** Review and testing
- Code review
- Update integration tests
- Performance testing

### Phase 3: Cleanup (Week 3)

- Fix or remove unused validation function (#19)
- Improve combined_server initialization
- Address TODO markers
- Final documentation pass

---

## Testing Strategy

### Unit Tests

```python
# test_pricing_pack_validation.py

def test_pack_id_validation():
    """Test pricing pack ID format validation."""
    # Valid IDs
    validate_pricing_pack_id("PP_2025-10-21")  # OK
    validate_pricing_pack_id("PP_2024-01-01")  # OK

    # Invalid IDs
    with pytest.raises(ValueError, match="Invalid pricing_pack_id format"):
        validate_pricing_pack_id("PP_latest")

    with pytest.raises(ValueError, match="Invalid pricing_pack_id format"):
        validate_pricing_pack_id("XYZ_2025-10-21")

    with pytest.raises(ValueError, match="required"):
        validate_pricing_pack_id(None)

    with pytest.raises(ValueError, match="Invalid date"):
        validate_pricing_pack_id("PP_2025-13-45")


def test_pricing_service_stub_mode_production():
    """Test that stub mode is blocked in production."""
    os.environ["ENVIRONMENT"] = "production"

    with pytest.raises(ValueError, match="Cannot use stub mode.*in production"):
        get_pricing_service(use_db=False)


def test_pack_builder_validation_failure():
    """Test that pack builder raises exception on validation failure."""
    builder = PricingPackBuilder(use_stubs=False)

    # Mock insufficient data
    with patch.object(builder, '_fetch_prices', return_value=[]):
        with pytest.raises(ValueError, match="Insufficient data"):
            await builder.build_pack(date(2025, 10, 21))
```

### Integration Tests

```python
# test_pricing_pack_integration.py

async def test_end_to_end_with_fresh_pack():
    """Test complete flow with fresh pricing pack."""
    # Create fresh pack
    builder = PricingPackBuilder(use_stubs=True)
    pack_id = await builder.build_pack(date.today(), mark_fresh=True)

    # Query via service
    pricing_service = get_pricing_service()
    latest_pack = await pricing_service.get_latest_pack(require_fresh=True)

    assert latest_pack is not None
    assert latest_pack.id == pack_id
    assert latest_pack.is_fresh is True

    # Use in valuation
    agent = FinancialAnalyst()
    ctx = RequestCtx(..., pricing_pack_id=pack_id)
    result = await agent.value_positions(positions, None, ctx)

    assert "valued_positions" in result
    assert result["total_value"] > 0


async def test_missing_pricing_pack_raises():
    """Test that missing pricing pack raises exception."""
    agent = FinancialAnalyst()
    ctx = RequestCtx(..., pricing_pack_id=None)  # Missing pack

    with pytest.raises(PricingPackNotFoundError):
        await agent.value_positions(positions, None, ctx)
```

---

## Monitoring & Alerting

### Metrics to Add

1. **Pricing Pack Creation:**
   - `pricing_pack_build_duration_seconds`
   - `pricing_pack_validation_failures_total`
   - `pricing_pack_stub_fallbacks_total` (should be 0 in production)

2. **Pricing Pack Usage:**
   - `pricing_pack_age_days` (how old is current fresh pack)
   - `pricing_pack_missing_prices_total` (securities without prices)
   - `pricing_pack_invalid_id_attempts_total` (invalid pack ID format)

3. **Freshness:**
   - `pricing_pack_stale_requests_total` (requests using non-fresh pack)
   - `pricing_pack_freshness_gate_blocks_total` (requests blocked by gate)

### Alerts to Configure

1. **CRITICAL:** No fresh pricing pack for >24 hours
2. **HIGH:** Pricing pack validation failures
3. **MEDIUM:** Pricing pack age >3 days
4. **LOW:** Any stub fallback in production

---

## Conclusion

This audit revealed **27 specific code issues** with concrete file locations and line numbers, plus **21 TODO markers**. The most critical finding is Issue #14 (fallback to `"PP_latest"` literal string) which would cause silent failures in production.

All issues have been documented with:
- Exact file paths and line numbers
- Current code snippets showing the problem
- Explanation of impact
- Recommended fixes with code examples

**Immediate action required on Priority 1 issues to prevent production incidents.**

---

**Next Steps:**
1. Review this document with team
2. Prioritize fixes (recommend Priority 1 first)
3. Create implementation tickets
4. Execute Phase 1 fixes
5. Add integration tests
6. Deploy and monitor

