# Corporate Actions: FMP Pro Integration & Pattern-Based Architecture (Revised)

**Date:** November 3, 2025  
**Status:** 📋 **REVISED PLAN - ALIGNED WITH CONSOLIDATED ARCHITECTURE**  
**Purpose:** Complete end-to-end integration of FMP Pro API for corporate actions using pattern-driven architecture, aligned with Phase 3 consolidation patterns

---

## 📊 Executive Summary

This **revised** plan implements corporate actions using FMP Pro API, following the **consolidated architecture** established in Phase 3. The plan aligns with:

- ✅ **Phase 3 Consolidation Patterns** - Uses DataHarvester (core agent, not creating new agent)
- ✅ **BaseAgent Helpers** - Uses standardized helpers (`CACHE_TTL_*`, `_resolve_portfolio_id`, `_to_uuid`)
- ✅ **Established Capability Patterns** - Follows existing capability method signatures
- ✅ **Pattern-Driven Architecture** - UI uses PatternRenderer, not direct API calls
- ✅ **No Anti-Patterns** - Avoids hardcoded values, duplicate patterns, legacy state access

**Key Changes from V1:**
- ✅ Uses DataHarvester (already consolidated, Week 5 complete)
- ✅ Uses BaseAgent helpers (TTL constants, portfolio ID resolution, UUID conversion)
- ✅ Follows established capability method patterns (`capability_name(ctx, state, **kwargs)`)
- ✅ Uses `_attach_metadata()` pattern correctly
- ✅ Aligns with Phase 3 cleanup patterns (no duplication)

---

## 🎯 Architecture Alignment

### Current Architecture (Post-Phase 3)

**Agent Structure:**
- **4 Core Agents** (consolidated from 9):
  1. **FinancialAnalyst** - Portfolio management (ledger, pricing, metrics, ratings, optimization, charts)
  2. **MacroHound** - Macro analysis and alerts
  3. **DataHarvester** - External data fetching and reports ⭐ **USE THIS**
  4. **ClaudeAgent** - AI-powered insights

**BaseAgent Helpers Available:**
- `CACHE_TTL_DAY`, `CACHE_TTL_HOUR`, `CACHE_TTL_30MIN`, `CACHE_TTL_5MIN`, `CACHE_TTL_NONE`
- `_resolve_asof_date(ctx)` - Resolve asof date from context
- `_to_uuid(value, param_name)` - Convert string to UUID with validation
- `_resolve_portfolio_id(portfolio_id, ctx, capability_name)` - Resolve portfolio ID
- `_attach_metadata(result, metadata)` - Attach metadata to results
- `_create_metadata(source, asof, ttl, confidence)` - Create metadata object

**Established Patterns:**
- Capability methods: `async def capability_name(ctx, state, **kwargs)`
- Result wrapping: Use `_attach_metadata()` with `_create_metadata()`
- TTL values: Use `self.CACHE_TTL_*` constants
- Error handling: Return error dict with metadata
- Portfolio ID: Use `_resolve_portfolio_id()` helper

---

## 📋 Revised Implementation Plan

### Phase 1: Extend FMP Provider (4-6 hours)

**Goal:** Add FMP Pro corporate actions endpoints to `FMPProvider`

**FMP Pro API Endpoints:**

#### 1. Dividend Calendar
**Endpoint:** `GET /v3/stock_dividend_calendar`
**Implementation:**
```python
# backend/app/integrations/fmp_provider.py

@rate_limit(requests_per_minute=120)
async def get_dividend_calendar(
    self,
    from_date: date,
    to_date: date
) -> List[Dict]:
    """
    Get dividend calendar for date range.
    
    Args:
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
    
    Returns:
        List of dividend announcements
    
    FMP Response Format:
        [
          {
            "date": "2025-11-07",
            "label": "November 07, 25",
            "adjDividend": 0.24,
            "symbol": "AAPL",
            "dividend": 0.24,
            "recordDate": "2025-11-10",
            "paymentDate": "2025-11-14",
            "declarationDate": "2025-10-28"
          }
        ]
    """
    url = f"{self.config.base_url}/v3/stock_dividend_calendar"
    params = {
        "apikey": self.api_key,
        "from": from_date.isoformat(),
        "to": to_date.isoformat()
    }
    
    response = await self._request("GET", url, params=params)
    return response if isinstance(response, list) else []
```

#### 2. Stock Split Calendar
**Endpoint:** `GET /v3/stock_split_calendar`
```python
@rate_limit(requests_per_minute=120)
async def get_split_calendar(
    self,
    from_date: date,
    to_date: date
) -> List[Dict]:
    """Get stock split calendar for date range."""
    url = f"{self.config.base_url}/v3/stock_split_calendar"
    params = {
        "apikey": self.api_key,
        "from": from_date.isoformat(),
        "to": to_date.isoformat()
    }
    
    response = await self._request("GET", url, params=params)
    return response if isinstance(response, list) else []
```

#### 3. Earnings Calendar
**Endpoint:** `GET /v3/earning_calendar`
```python
@rate_limit(requests_per_minute=120)
async def get_earnings_calendar(
    self,
    from_date: date,
    to_date: date
) -> List[Dict]:
    """Get earnings calendar for date range."""
    url = f"{self.config.base_url}/v3/earning_calendar"
    params = {
        "apikey": self.api_key,
        "from": from_date.isoformat(),
        "to": to_date.isoformat()
    }
    
    response = await self._request("GET", url, params=params)
    return response if isinstance(response, list) else []
```

**Files to Modify:**
- `backend/app/integrations/fmp_provider.py` - Add 3 new methods

**Validation:**
- [ ] Rate limiting works (120 req/min)
- [ ] Error handling for API failures
- [ ] Response format normalization
- [ ] Date range validation

---

### Phase 2: Add DataHarvester Capabilities (6-8 hours)

**Goal:** Add corporate actions capabilities to `DataHarvester` agent (already consolidated)

**Key Principles:**
- ✅ Use DataHarvester (core agent, Week 5 consolidation complete)
- ✅ Use BaseAgent helpers (TTL constants, portfolio ID resolution)
- ✅ Follow established capability method patterns
- ✅ Use `_attach_metadata()` correctly
- ✅ No hardcoded values or duplicate patterns

**New Capabilities:**
```python
# backend/app/agents/data_harvester.py

def get_capabilities(self) -> List[str]:
    return [
        # ... existing capabilities ...
        "corporate_actions.dividends",
        "corporate_actions.splits",
        "corporate_actions.earnings",
        "corporate_actions.upcoming",  # Main capability for pattern
        "corporate_actions.calculate_impact",
    ]
```

**Implementation:**

#### 1. `corporate_actions.dividends`
```python
async def corporate_actions_dividends(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    symbols: Optional[List[str]] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Capability: corporate_actions.dividends
    Fetch dividend calendar from FMP.
    
    Args:
        symbols: Filter by symbols (optional)
        from_date: Start date (YYYY-MM-DD, defaults to today)
        to_date: End date (YYYY-MM-DD, defaults to today + 90 days)
    
    Returns:
        {
            "dividends": [...],
            "count": 5,
            "__metadata__": {...}
        }
    """
    from datetime import date, timedelta
    from app.integrations.fmp_provider import FMPProvider
    
    # Resolve dates using BaseAgent helper
    asof_date = self._resolve_asof_date(ctx)
    
    if from_date:
        from_date_obj = datetime.fromisoformat(from_date).date()
    else:
        from_date_obj = asof_date
    
    if to_date:
        to_date_obj = datetime.fromisoformat(to_date).date()
    else:
        to_date_obj = from_date_obj + timedelta(days=90)
    
    # Get FMP provider
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        error_result = {
            "dividends": [],
            "count": 0,
            "error": "FMP_API_KEY not configured"
        }
        metadata = self._create_metadata(
            source="data_harvester:error",
            asof=asof_date,
            ttl=self.CACHE_TTL_NONE,
            confidence=0.0
        )
        return self._attach_metadata(error_result, metadata)
    
    try:
        provider = FMPProvider(api_key=api_key)
        dividends = await provider.get_dividend_calendar(from_date_obj, to_date_obj)
        
        # Filter by symbols if provided
        if symbols:
            dividends = [d for d in dividends if d.get("symbol") in symbols]
        
        # Normalize format
        normalized = []
        for div in dividends:
            normalized.append({
                "symbol": div.get("symbol"),
                "type": "dividend",
                "ex_date": div.get("date"),  # FMP uses "date" as ex-date
                "payment_date": div.get("paymentDate"),
                "record_date": div.get("recordDate"),
                "declaration_date": div.get("declarationDate"),
                "amount": float(div.get("dividend", 0)),
                "currency": "USD",  # FMP dividends typically USD
                "source": "fmp"
            })
        
        result = {
            "dividends": normalized,
            "count": len(normalized),
            "source": "fmp"
        }
        
        # Attach metadata using BaseAgent helper
        metadata = self._create_metadata(
            source="fmp",
            asof=asof_date,
            ttl=self.CACHE_TTL_HOUR,  # Use BaseAgent constant
            confidence=1.0
        )
        return self._attach_metadata(result, metadata)
        
    except Exception as e:
        logger.error(f"Error fetching dividends from FMP: {e}", exc_info=True)
        error_result = {
            "dividends": [],
            "count": 0,
            "error": f"FMP error: {str(e)}"
        }
        metadata = self._create_metadata(
            source="data_harvester:error",
            asof=asof_date,
            ttl=self.CACHE_TTL_NONE,  # Use BaseAgent constant
            confidence=0.0
        )
        return self._attach_metadata(error_result, metadata)
```

**Key Patterns:**
- ✅ Uses `self._resolve_asof_date(ctx)` - BaseAgent helper
- ✅ Uses `self.CACHE_TTL_HOUR` - BaseAgent constant (not hardcoded)
- ✅ Uses `self._create_metadata()` and `self._attach_metadata()` - BaseAgent helpers
- ✅ Follows established error handling pattern
- ✅ Returns dict with `__metadata__` key (not attribute)

#### 2. `corporate_actions.splits` (Similar pattern)
```python
async def corporate_actions_splits(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    symbols: Optional[List[str]] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> Dict[str, Any]:
    """Capability: corporate_actions.splits - Fetch stock split calendar from FMP."""
    # Similar implementation to dividends
    # Uses BaseAgent helpers, TTL constants, metadata pattern
```

#### 3. `corporate_actions.earnings` (Similar pattern)
```python
async def corporate_actions_earnings(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    symbols: Optional[List[str]] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> Dict[str, Any]:
    """Capability: corporate_actions.earnings - Fetch earnings calendar from FMP."""
    # Similar implementation
```

#### 4. `corporate_actions.upcoming` (Main Pattern Capability)
```python
async def corporate_actions_upcoming(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: Optional[str] = None,
    symbols: Optional[List[str]] = None,
    days_ahead: int = 90
) -> Dict[str, Any]:
    """
    Capability: corporate_actions.upcoming
    Get all upcoming corporate actions for portfolio holdings.
    
    This is the main capability used by the pattern.
    It orchestrates fetching dividends, splits, and earnings,
    then filters by portfolio holdings.
    
    Args:
        portfolio_id: Portfolio UUID (optional, can be resolved from context)
        symbols: List of symbols (optional, will fetch from portfolio if not provided)
        days_ahead: Number of days to look ahead (default 90)
    
    Returns:
        {
            "actions": [...],  # Combined list of all actions
            "summary": {
                "total_actions": 5,
                "dividends_expected": 120.00,
                "splits_pending": 1,
                "earnings_releases": 2
            },
            "__metadata__": {...}
        }
    """
    from datetime import date, timedelta
    
    # Use BaseAgent helper for portfolio ID resolution
    portfolio_uuid = self._resolve_portfolio_id(portfolio_id, ctx, "corporate_actions.upcoming")
    
    # Resolve symbols from portfolio if not provided
    if not symbols:
        # Get holdings from state (should be set by previous step: ledger.positions)
        positions = state.get("positions", {}).get("positions", [])
        symbols = [p.get("symbol") for p in positions if p.get("qty_open", 0) > 0]
    
    if not symbols:
        result = {
            "actions": [],
            "summary": {
                "total_actions": 0,
                "dividends_expected": 0.00,
                "splits_pending": 0,
                "earnings_releases": 0
            }
        }
        metadata = self._create_metadata(
            source="data_harvester",
            asof=self._resolve_asof_date(ctx),
            ttl=self.CACHE_TTL_HOUR,  # Use BaseAgent constant
            confidence=1.0
        )
        return self._attach_metadata(result, metadata)
    
    # Calculate date range
    asof_date = self._resolve_asof_date(ctx)
    from_date = asof_date
    to_date = from_date + timedelta(days=days_ahead)
    
    # Fetch all corporate actions
    all_actions = []
    
    # Fetch dividends
    dividends_result = await self.corporate_actions_dividends(
        ctx, state,
        symbols=symbols,
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat()
    )
    if dividends_result.get("dividends"):
        all_actions.extend(dividends_result["dividends"])
    
    # Fetch splits
    splits_result = await self.corporate_actions_splits(
        ctx, state,
        symbols=symbols,
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat()
    )
    if splits_result.get("splits"):
        all_actions.extend(splits_result["splits"])
    
    # Fetch earnings
    earnings_result = await self.corporate_actions_earnings(
        ctx, state,
        symbols=symbols,
        from_date=from_date.isoformat(),
        to_date=to_date.isoformat()
    )
    if earnings_result.get("earnings"):
        all_actions.extend(earnings_result["earnings"])
    
    # Sort by date
    all_actions.sort(key=lambda x: x.get("ex_date") or x.get("date") or x.get("payment_date"))
    
    # Calculate summary
    dividends_count = sum(1 for a in all_actions if a.get("type") == "dividend")
    dividends_total = sum(
        a.get("amount", 0) for a in all_actions
        if a.get("type") == "dividend"
    )
    splits_count = sum(1 for a in all_actions if a.get("type") == "split")
    earnings_count = sum(1 for a in all_actions if a.get("type") == "earnings")
    
    result = {
        "actions": all_actions,
        "summary": {
            "total_actions": len(all_actions),
            "dividends_expected": dividends_total,
            "splits_pending": splits_count,
            "earnings_releases": earnings_count
        },
        "source": "fmp"
    }
    
    # Attach metadata using BaseAgent helper
    metadata = self._create_metadata(
        source="fmp",
        asof=asof_date,
        ttl=self.CACHE_TTL_30MIN,  # Use BaseAgent constant (shorter TTL for dynamic data)
        confidence=1.0
    )
    return self._attach_metadata(result, metadata)
```

**Key Patterns:**
- ✅ Uses `self._resolve_portfolio_id()` - BaseAgent helper (not hardcoded logic)
- ✅ Uses `self._resolve_asof_date(ctx)` - BaseAgent helper
- ✅ Uses `self.CACHE_TTL_30MIN` - BaseAgent constant (not hardcoded)
- ✅ Uses `self._create_metadata()` and `self._attach_metadata()` - BaseAgent helpers
- ✅ Follows established capability orchestration pattern
- ✅ Reuses other capabilities (dividends, splits, earnings)

#### 5. `corporate_actions.calculate_impact`
```python
async def corporate_actions_calculate_impact(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    actions: List[Dict],
    holdings: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Capability: corporate_actions.calculate_impact
    Calculate portfolio impact for corporate actions.
    
    Args:
        actions: List of corporate actions
        holdings: Dict of {symbol: quantity} (optional, will extract from state if not provided)
    
    Returns:
        {
            "actions": [...],  # Actions with impact calculations
            "total_dividend_impact": 120.00,
            "notifications": {
                "urgent": [...],  # Actions within 7 days
                "informational": [...]
            },
            "__metadata__": {...}
        }
    """
    from datetime import date, timedelta
    
    # Extract holdings from state if not provided
    if not holdings:
        positions = state.get("positions", {}).get("positions", [])
        holdings = {p.get("symbol"): p.get("qty_open", 0) for p in positions}
    
    actions_with_impact = []
    total_dividend_impact = 0.0
    
    for action in actions:
        symbol = action.get("symbol")
        quantity = holdings.get(symbol, 0)
        
        impact = 0.0
        if action.get("type") == "dividend" and quantity > 0:
            amount = action.get("amount", 0)
            impact = amount * quantity
            total_dividend_impact += impact
        
        action_with_impact = {
            **action,
            "portfolio_quantity": quantity,
            "portfolio_impact": impact
        }
        actions_with_impact.append(action_with_impact)
    
    # Calculate notifications (urgent = within 7 days)
    asof_date = self._resolve_asof_date(ctx)
    cutoff_date = asof_date + timedelta(days=7)
    urgent = []
    informational = []
    
    for action in actions_with_impact:
        action_date = action.get("ex_date") or action.get("date") or action.get("payment_date")
        if action_date:
            try:
                action_date_obj = datetime.fromisoformat(action_date).date()
                if action_date_obj <= cutoff_date:
                    urgent.append(action)
                else:
                    informational.append(action)
            except:
                informational.append(action)
        else:
            informational.append(action)
    
    result = {
        "actions": actions_with_impact,
        "total_dividend_impact": total_dividend_impact,
        "notifications": {
            "urgent": urgent,
            "informational": informational
        }
    }
    
    # Attach metadata using BaseAgent helper
    metadata = self._create_metadata(
        source="data_harvester",
        asof=asof_date,
        ttl=self.CACHE_TTL_30MIN,  # Use BaseAgent constant
        confidence=1.0
    )
    return self._attach_metadata(result, metadata)
```

**Files to Modify:**
- `backend/app/agents/data_harvester.py` - Add 5 new methods

**Validation:**
- [ ] Capabilities registered in `get_capabilities()`
- [ ] Methods follow BaseAgent patterns
- [ ] Use BaseAgent helpers (TTL constants, portfolio ID resolution, metadata)
- [ ] Error handling and logging
- [ ] No hardcoded values
- [ ] No duplicate patterns

---

### Phase 3: Create Pattern Definition (2-3 hours)

**Goal:** Create `corporate_actions_upcoming.json` pattern

**Pattern Definition:**
```json
{
  "id": "corporate_actions_upcoming",
  "name": "Upcoming Corporate Actions",
  "description": "Get upcoming corporate actions (dividends, splits, earnings) for portfolio holdings",
  "version": "1.0.0",
  "category": "corporate_actions",
  "tags": ["corporate-actions", "dividends", "splits", "earnings", "holdings"],
  "author": "DawsOS",
  "created": "2025-11-03",
  "inputs": {
    "portfolio_id": {
      "type": "uuid",
      "required": true,
      "description": "Portfolio UUID"
    },
    "days_ahead": {
      "type": "integer",
      "default": 90,
      "description": "Number of days to look ahead (default 90)"
    }
  },
  "outputs": {
    "panels": [
      {
        "id": "actions_table",
        "title": "Upcoming Corporate Actions",
        "type": "table",
        "dataPath": "actions_with_impact.actions"
      },
      {
        "id": "summary_metrics",
        "title": "Summary",
        "type": "metrics_grid",
        "dataPath": "actions_with_impact.summary"
      },
      {
        "id": "notifications_list",
        "title": "Notifications",
        "type": "dual_list",
        "dataPath": "actions_with_impact.notifications"
      }
    ]
  },
  "steps": [
    {
      "capability": "ledger.positions",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}"
      },
      "as": "positions"
    },
    {
      "capability": "corporate_actions.upcoming",
      "args": {
        "portfolio_id": "{{inputs.portfolio_id}}",
        "symbols": "{{positions.positions[*].symbol}}",
        "days_ahead": "{{inputs.days_ahead}}"
      },
      "as": "actions"
    },
    {
      "capability": "corporate_actions.calculate_impact",
      "args": {
        "actions": "{{actions.actions}}",
        "holdings": "{{positions.positions}}"
      },
      "as": "actions_with_impact"
    }
  ],
  "presentation": {
    "summary_metrics": {
      "metrics": [
        {
          "label": "Total Actions",
          "value": "{{actions_with_impact.summary.total_actions}}",
          "format": "number"
        },
        {
          "label": "Dividends Expected",
          "value": "{{actions_with_impact.summary.dividends_expected}}",
          "format": "currency"
        },
        {
          "label": "Splits Pending",
          "value": "{{actions_with_impact.summary.splits_pending}}",
          "format": "number"
        },
        {
          "label": "Earnings Releases",
          "value": "{{actions_with_impact.summary.earnings_releases}}",
          "format": "number"
        }
      ]
    },
    "actions_table": {
      "columns": [
        {"field": "date", "header": "Date", "width": 120},
        {"field": "symbol", "header": "Symbol", "width": 100},
        {"field": "type", "header": "Type", "width": 100},
        {"field": "amount", "header": "Amount", "format": "currency", "width": 120},
        {"field": "portfolio_quantity", "header": "Shares", "format": "number", "width": 100},
        {"field": "portfolio_impact", "header": "Impact", "format": "currency", "width": 120}
      ],
      "data": "{{actions_with_impact.actions}}",
      "sort_by": "date",
      "sort_order": "asc"
    }
  },
  "rights_required": ["portfolio_read"],
  "export_allowed": {
    "pdf": true,
    "csv": true
  },
  "observability": {
    "otel_span_name": "pattern.corporate_actions_upcoming",
    "metrics": [
      "pattern_execution_duration_seconds",
      "corporate_actions_fetched_total",
      "corporate_actions_impact_calculated_total"
    ]
  }
}
```

**Files to Create:**
- `backend/patterns/corporate_actions_upcoming.json`

**Validation:**
- [ ] Pattern loads correctly
- [ ] Steps execute in order
- [ ] Template substitution works (`{{inputs.portfolio_id}}`, `{{positions.positions}}`)
- [ ] Outputs match expected format
- [ ] Follows established pattern structure (see `news_impact_analysis.json`)

---

### Phase 4: Update Pattern Registry (1-2 hours)

**Goal:** Add corporate actions pattern to `patternRegistry` in UI

**Location:** `full_ui.html` lines 2832-3117

**Add Entry:**
```javascript
corporate_actions_upcoming: {
    category: 'corporate_actions',
    name: 'Upcoming Corporate Actions',
    description: 'Track dividends, splits, and earnings for portfolio holdings',
    icon: '📅',
    display: {
        panels: [
            {
                id: 'actions_table',
                title: 'Upcoming Corporate Actions',
                type: 'table',
                dataPath: 'actions_with_impact.actions',
                config: {
                    columns: [
                        { field: 'date', header: 'Date', width: 120 },
                        { field: 'symbol', header: 'Symbol', width: 100 },
                        { field: 'type', header: 'Type', width: 100 },
                        { field: 'amount', header: 'Amount', format: 'currency', width: 120 },
                        { field: 'portfolio_quantity', header: 'Shares', format: 'number', width: 100 },
                        { field: 'portfolio_impact', header: 'Impact', format: 'currency', width: 120 }
                    ],
                    sort_by: 'date',
                    sort_order: 'asc'
                }
            },
            {
                id: 'summary_metrics',
                title: 'Summary',
                type: 'metrics_grid',
                dataPath: 'actions_with_impact.summary',
                config: {
                    columns: 4,
                    metrics: [
                        { key: 'total_actions', label: 'Total Actions', format: 'number' },
                        { key: 'dividends_expected', label: 'Dividends Expected', format: 'currency' },
                        { key: 'splits_pending', label: 'Splits Pending', format: 'number' },
                        { key: 'earnings_releases', label: 'Earnings Releases', format: 'number' }
                    ]
                }
            },
            {
                id: 'notifications_list',
                title: 'Notifications',
                type: 'dual_list',
                dataPath: 'actions_with_impact.notifications',
                config: {
                    urgent_title: 'Urgent (Next 7 Days)',
                    informational_title: 'Upcoming'
                }
            }
        ]
    }
}
```

**Files to Modify:**
- `full_ui.html` - Add to `patternRegistry` object

**Validation:**
- [ ] Pattern entry matches pattern JSON structure
- [ ] Panel configurations correct
- [ ] dataPath values match pattern outputs
- [ ] Follows established registry structure

---

### Phase 5: Refactor UI to Use PatternRenderer (3-4 hours)

**Goal:** Replace direct API calls with PatternRenderer

**Current Implementation:**
```javascript
// Lines 11315-11555: CorporateActionsPage
// Uses: axios.get('/api/corporate-actions')
// Custom state: useState, useEffect
// Custom rendering: manual table rendering
```

**New Implementation:**
```javascript
function CorporateActionsPage() {
    const [filterType, setFilterType] = useState('all');
    const [filterDays, setFilterDays] = useState(90);
    const [patternData, setPatternData] = useState(null);
    
    // Pattern inputs
    const patternInputs = {
        portfolio_id: getCurrentPortfolioId(),
        days_ahead: filterDays
    };
    
    // Handle pattern data
    const handlePatternData = (data) => {
        setPatternData(data);
    };
    
    // Get filtered actions from pattern data
    const filteredActions = useMemo(() => {
        if (!patternData?.actions_with_impact?.actions) return [];
        
        let actions = patternData.actions_with_impact.actions;
        
        // Apply type filter (client-side)
        if (filterType !== 'all') {
            actions = actions.filter(a => a.type?.toLowerCase() === filterType);
        }
        
        return actions;
    }, [patternData, filterType]);
    
    return e('div', null,
        e('div', { className: 'page-header' },
            e('h1', { className: 'page-title' }, 'Corporate Actions'),
            e('p', { className: 'page-description' }, 
                'Track dividends, splits, and other corporate events')
        ),
        
        // Filtering Controls (keep existing filter UI)
        e('div', { className: 'card', style: { marginBottom: '1.5rem' } },
            e('div', { className: 'card-header' },
                e('h3', { className: 'card-title' }, 'Filter Corporate Actions')
            ),
            e('div', { style: { padding: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' } },
                // Action Type Filter
                e('div', { style: { flex: '1 1 200px', minWidth: '150px' } },
                    e('label', { className: 'form-label' }, 'Action Type'),
                    e('select', {
                        className: 'form-input',
                        value: filterType,
                        onChange: (e) => setFilterType(e.target.value)
                    },
                        e('option', { value: 'all' }, 'All Types'),
                        e('option', { value: 'dividend' }, 'Dividends'),
                        e('option', { value: 'split' }, 'Stock Splits'),
                        e('option', { value: 'earnings' }, 'Earnings')
                    )
                ),
                
                // Date Range Filter
                e('div', { style: { flex: '1 1 200px', minWidth: '150px' } },
                    e('label', { className: 'form-label' }, 'Date Range'),
                    e('select', {
                        className: 'form-input',
                        value: filterDays,
                        onChange: (e) => setFilterDays(Number(e.target.value))
                    },
                        e('option', { value: 30 }, 'Next 30 days'),
                        e('option', { value: 90 }, 'Next 90 days'),
                        e('option', { value: 180 }, 'Next 180 days'),
                        e('option', { value: 365 }, 'Next year')
                    )
                )
            )
        ),
        
        // PatternRenderer for main content
        e(PatternRenderer, {
            pattern: 'corporate_actions_upcoming',
            inputs: patternInputs,
            onDataLoaded: handlePatternData
        })
    );
}
```

**Key Changes:**
1. ✅ Remove direct API calls (`axios.get('/api/corporate-actions')`)
2. ✅ Use `PatternRenderer` component
3. ✅ Keep filter controls (client-side filtering)
4. ✅ Use `onDataLoaded` callback for custom filtering
5. ✅ Remove custom table rendering (use PatternRenderer panels)

**Files to Modify:**
- `full_ui.html` - Refactor `CorporateActionsPage` function

**Validation:**
- [ ] PatternRenderer executes pattern
- [ ] Panels render correctly
- [ ] Filters work (client-side)
- [ ] Error handling works
- [ ] Loading states work
- [ ] Follows established PatternRenderer pattern (see `DashboardPage`, `ScenariosPage`)

---

### Phase 6: Testing & Validation (4-6 hours)

**Goal:** Comprehensive testing of end-to-end flow

**Test Cases:**

#### 1. FMP Provider Tests
- [ ] `get_dividend_calendar()` returns correct format
- [ ] `get_split_calendar()` returns correct format
- [ ] `get_earnings_calendar()` returns correct format
- [ ] Rate limiting works (120 req/min)
- [ ] Error handling for API failures
- [ ] Date range validation

#### 2. DataHarvester Capability Tests
- [ ] `corporate_actions.dividends` capability works
- [ ] `corporate_actions.splits` capability works
- [ ] `corporate_actions.earnings` capability works
- [ ] `corporate_actions.upcoming` orchestrates correctly
- [ ] `corporate_actions.calculate_impact` calculates correctly
- [ ] Symbols filtering works
- [ ] Portfolio holdings integration works
- [ ] **Uses BaseAgent helpers** (TTL constants, portfolio ID resolution)
- [ ] **No hardcoded values**
- [ ] **Metadata attached correctly**

#### 3. Pattern Execution Tests
- [ ] Pattern loads from JSON
- [ ] Steps execute in order
- [ ] Template substitution works (`{{inputs.portfolio_id}}`)
- [ ] State passes between steps
- [ ] Outputs match expected format
- [ ] Error handling works

#### 4. UI Integration Tests
- [ ] PatternRenderer executes pattern
- [ ] Panels render correctly
- [ ] Data extraction works (`getDataByPath`)
- [ ] Filters work (client-side)
- [ ] Loading states display
- [ ] Error states display
- [ ] Empty states display

#### 5. End-to-End Tests
- [ ] User opens Corporate Actions page
- [ ] Pattern executes with portfolio ID
- [ ] Holdings fetched correctly
- [ ] FMP API called for dividends/splits/earnings
- [ ] Impact calculated correctly
- [ ] UI displays actions table
- [ ] UI displays summary metrics
- [ ] UI displays notifications
- [ ] Filters work
- [ ] Date range changes trigger re-execution

**Files to Create:**
- `backend/tests/test_corporate_actions_fmp.py`
- `backend/tests/test_corporate_actions_pattern.py`

---

## 🚨 Anti-Pattern Avoidance

### ✅ What We're Doing Right

1. **Using DataHarvester** - Core agent, not creating new agent
2. **Using BaseAgent Helpers** - TTL constants, portfolio ID resolution, metadata
3. **Following Established Patterns** - Capability method signatures, error handling
4. **Pattern-Driven Architecture** - UI uses PatternRenderer, not direct API calls
5. **No Hardcoded Values** - All TTL values use `self.CACHE_TTL_*` constants
6. **No Duplicate Patterns** - Portfolio ID resolution uses `_resolve_portfolio_id()` helper
7. **Proper Metadata** - Uses `_attach_metadata()` and `_create_metadata()` helpers

### ❌ Anti-Patterns We're Avoiding

1. **Hardcoded TTL Values** - ❌ `ttl=3600` → ✅ `ttl=self.CACHE_TTL_HOUR`
2. **Duplicate Portfolio ID Resolution** - ❌ Manual logic → ✅ `_resolve_portfolio_id()`
3. **Hardcoded Date Resolution** - ❌ `ctx.asof_date or date.today()` → ✅ `_resolve_asof_date(ctx)`
4. **Direct API Calls in UI** - ❌ `axios.get('/api/corporate-actions')` → ✅ `PatternRenderer`
5. **Custom State Management** - ❌ Manual state → ✅ PatternRenderer handles state
6. **Legacy State Access** - ❌ `state.get("state", {})` → ✅ Direct state access
7. **Inconsistent Error Handling** - ❌ Various patterns → ✅ Standardized error dict + metadata

---

## 📊 Implementation Timeline

**Total Estimated Time:** 20-30 hours

### Phase 1: FMP Provider Extension (4-6 hours)
- Add 3 methods to `FMPProvider`
- Test rate limiting and error handling

### Phase 2: DataHarvester Capabilities (6-8 hours)
- Add 5 capabilities to `DataHarvester`
- Use BaseAgent helpers (no hardcoded values)
- Test capability routing

### Phase 3: Pattern Definition (2-3 hours)
- Create `corporate_actions_upcoming.json`
- Test pattern execution
- Validate template substitution

### Phase 4: Pattern Registry (1-2 hours)
- Add entry to `patternRegistry`
- Validate panel configurations

### Phase 5: UI Refactoring (3-4 hours)
- Replace direct API calls with PatternRenderer
- Keep filter controls
- Test rendering

### Phase 6: Testing & Validation (4-6 hours)
- Unit tests for provider
- Integration tests for capabilities
- Pattern execution tests
- UI integration tests
- End-to-end tests

---

## ✅ Validation Checklist

### Architecture Alignment
- [ ] Uses DataHarvester (core agent, Week 5 consolidation complete)
- [ ] Uses BaseAgent helpers (TTL constants, portfolio ID resolution, metadata)
- [ ] Follows established capability method patterns
- [ ] No hardcoded values
- [ ] No duplicate patterns
- [ ] Proper metadata attachment

### Provider Layer
- [ ] FMP Provider methods implement correctly
- [ ] Rate limiting enforced (120 req/min)
- [ ] Error handling for API failures
- [ ] Response format normalization
- [ ] Date validation

### Agent Layer
- [ ] Capabilities registered correctly
- [ ] Methods follow BaseAgent patterns
- [ ] **Uses BaseAgent helpers** (TTL constants, portfolio ID resolution, metadata)
- [ ] Error handling and logging
- [ ] **No hardcoded values**
- [ ] **No duplicate patterns**

### Pattern Layer
- [ ] Pattern JSON valid
- [ ] Steps execute in order
- [ ] Template substitution works
- [ ] Outputs match expected format
- [ ] Error handling works
- [ ] Follows established pattern structure

### UI Layer
- [ ] PatternRegistry entry correct
- [ ] PatternRenderer executes pattern
- [ ] Panels render correctly
- [ ] Data extraction works
- [ ] Filters work
- [ ] Error states display
- [ ] Loading states display
- [ ] Follows established PatternRenderer pattern

### End-to-End
- [ ] User flow works from UI to API
- [ ] Data flows correctly through all layers
- [ ] Performance acceptable
- [ ] Error handling graceful
- [ ] User experience smooth

---

## 📚 Related Documentation

- `CORPORATE_ACTIONS_UI_INTEGRATION_AUDIT.md` - Original audit
- `CORPORATE_ACTIONS_FMP_INTEGRATION_PLAN.md` - Previous plan (V1)
- `ARCHITECTURE.md` - Current architecture
- `PHASE_3_CONSOLIDATION_REMAINING_WORK.md` - Consolidation status
- `CODE_REVIEW_REPORT_V2.md` - Anti-patterns identified
- `CLAUDE_CODE_CLEANUP_REVIEW.md` - BaseAgent helpers available
- `backend/patterns/news_impact_analysis.json` - Reference pattern

---

## ✅ Key Differences from V1

### Architecture Alignment
- ✅ **V1:** Created new agent (wrong) → **V2:** Uses DataHarvester (correct)
- ✅ **V1:** Hardcoded TTL values → **V2:** Uses `self.CACHE_TTL_*` constants
- ✅ **V1:** Manual portfolio ID resolution → **V2:** Uses `_resolve_portfolio_id()` helper
- ✅ **V1:** Inconsistent error handling → **V2:** Standardized error dict + metadata

### Pattern Compliance
- ✅ **V1:** Custom capability methods → **V2:** Follows established capability patterns
- ✅ **V1:** Inconsistent metadata → **V2:** Uses `_attach_metadata()` and `_create_metadata()` helpers
- ✅ **V1:** Mixed patterns → **V2:** Consistent with Phase 3 consolidation patterns

### Anti-Pattern Avoidance
- ✅ **V1:** Potential for hardcoded values → **V2:** All values use BaseAgent helpers
- ✅ **V1:** Potential for duplicate patterns → **V2:** All patterns use BaseAgent helpers
- ✅ **V1:** Inconsistent with Phase 3 → **V2:** Aligned with Phase 3 consolidation

---

**Plan Created:** November 3, 2025  
**Status:** ✅ **REVISED & ALIGNED WITH CONSOLIDATED ARCHITECTURE**  
**Estimated Effort:** 20-30 hours  
**Architecture:** Pattern-driven, aligned with Phase 3 consolidation patterns

