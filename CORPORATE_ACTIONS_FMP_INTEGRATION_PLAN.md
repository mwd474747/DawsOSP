# Corporate Actions: FMP Pro Integration & Pattern-Based Architecture

**Date:** November 3, 2025  
**Status:** 📋 **COMPREHENSIVE PLAN - READY FOR IMPLEMENTATION**  
**Purpose:** Complete end-to-end integration of FMP Pro API for corporate actions using pattern-driven architecture

---

## 📊 Executive Summary

This plan implements a **complete, pattern-driven corporate actions feature** using FMP Pro API, following the established DawsOS architecture. The implementation extends the existing pattern system, properly integrates with DataHarvester agent, and refactors the UI to use PatternRenderer for consistency.

**Key Principles:**
- ✅ **No shortcuts** - Full pattern integration, not direct API calls
- ✅ **Extend properly** - Follow existing patterns (news_impact_analysis, portfolio_overview)
- ✅ **FMP Pro** - Leverage comprehensive FMP Pro API capabilities
- ✅ **Pattern-driven** - UI uses PatternRenderer, not custom API calls

---

## 🎯 Architecture Overview

### Current State

**UI Component:**
- ✅ Fully functional `CorporateActionsPage` component
- ❌ Uses direct API calls (`/api/corporate-actions`)
- ❌ Not integrated with pattern system
- ❌ Custom state management

**Backend:**
- ✅ `FMPProvider` exists with rate limiting, circuit breaker
- ❌ Missing corporate actions methods
- ❌ No `corporate_actions.*` capabilities
- ❌ No `corporate_actions_upcoming` pattern

**Pattern System:**
- ✅ PatternOrchestrator executes JSON patterns
- ✅ PatternRenderer renders panels in UI
- ✅ 12 patterns registered, working end-to-end
- ❌ No corporate actions pattern

### Target State

**Pattern-Driven Architecture:**
```
User → CorporateActionsPage
  → PatternRenderer(pattern="corporate_actions_upcoming", inputs={portfolio_id, days_ahead})
  → apiClient.executePattern()
  → POST /api/patterns/execute
  → PatternOrchestrator.run_pattern("corporate_actions_upcoming")
  → Steps:
      1. ledger.positions (get holdings)
      2. corporate_actions.upcoming (fetch from FMP)
      3. corporate_actions.calculate_impact (portfolio impact)
  → Returns: { actions, summary, notifications }
  → PatternRenderer extracts panels from patternRegistry
  → PanelRenderer renders: actions_table, summary_metrics, notifications_list
```

---

## 📋 Implementation Plan

### Phase 1: Extend FMP Provider (4-6 hours)

**Goal:** Add FMP Pro corporate actions endpoints to `FMPProvider`

**FMP Pro API Endpoints (Pro Access):**

#### 1. Dividend Calendar
**Endpoint:** `GET /v3/stock_dividend_calendar`
**Query Params:** `from=YYYY-MM-DD&to=YYYY-MM-DD&apikey=...`

**Response Format:**
```json
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
```

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
    """
    url = f"{self.config.base_url}/v3/stock_dividend_calendar"
    params = {
        "apikey": self.api_key,
        "from": from_date.isoformat(),
        "to": to_date.isoformat()
    }
    
    response = await self._request("GET", url, params=params)
    return response if isinstance(response, list) else []

@rate_limit(requests_per_minute=120)
async def get_historical_dividends(
    self,
    symbol: str
) -> List[Dict]:
    """
    Get historical dividends for symbol.
    
    Endpoint: GET /v3/historical-price-full/stock_dividend/{symbol}
    """
    url = f"{self.config.base_url}/v3/historical-price-full/stock_dividend/{symbol}"
    params = {"apikey": self.api_key}
    
    response = await self._request("GET", url, params=params)
    
    # FMP returns { "symbol": "AAPL", "historical": [...] }
    if isinstance(response, dict) and "historical" in response:
        return response["historical"]
    return []
```

#### 2. Stock Split Calendar
**Endpoint:** `GET /v3/stock_split_calendar`

**Implementation:**
```python
@rate_limit(requests_per_minute=120)
async def get_split_calendar(
    self,
    from_date: date,
    to_date: date
) -> List[Dict]:
    """
    Get stock split calendar for date range.
    """
    url = f"{self.config.base_url}/v3/stock_split_calendar"
    params = {
        "apikey": self.api_key,
        "from": from_date.isoformat(),
        "to": to_date.isoformat()
    }
    
    response = await self._request("GET", url, params=params)
    return response if isinstance(response, list) else []

@rate_limit(requests_per_minute=120)
async def get_historical_splits(
    self,
    symbol: str
) -> List[Dict]:
    """
    Get historical stock splits for symbol.
    
    Endpoint: GET /v3/historical-price-full/stock_split/{symbol}
    """
    url = f"{self.config.base_url}/v3/historical-price-full/stock_split/{symbol}"
    params = {"apikey": self.api_key}
    
    response = await self._request("GET", url, params=params)
    
    if isinstance(response, dict) and "historical" in response:
        return response["historical"]
    return []
```

#### 3. Earnings Calendar
**Endpoint:** `GET /v3/earning_calendar`

**Implementation:**
```python
@rate_limit(requests_per_minute=120)
async def get_earnings_calendar(
    self,
    from_date: date,
    to_date: date
) -> List[Dict]:
    """
    Get earnings calendar for date range.
    
    Response Format:
    [
      {
        "date": "2025-11-15",
        "symbol": "MSFT",
        "eps": 2.85,
        "epsEstimated": 2.80,
        "time": "amc",
        "revenue": 56100000000,
        "revenueEstimated": 55800000000,
        "fiscalDateEnding": "2025-09-30",
        "updatedFromDate": "2025-10-01"
      }
    ]
    """
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
- `backend/app/integrations/fmp_provider.py` - Add 5 new methods

**Validation:**
- [ ] Rate limiting works (120 req/min)
- [ ] Error handling for API failures
- [ ] Response format normalization
- [ ] Date range validation

---

### Phase 2: Add DataHarvester Capabilities (6-8 hours)

**Goal:** Add corporate actions capabilities to `DataHarvester` agent

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
        "corporate_actions.calculate_impact",  # Portfolio impact calculation
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
        symbols: Filter by symbols (optional, if None fetches all)
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
    
    Returns:
        {
            "dividends": [...],
            "source": "fmp",
            "__metadata__": {...}
        }
    """
    from datetime import date
    from app.integrations.fmp_provider import FMPProvider
    
    # Resolve dates
    if from_date:
        from_date_obj = datetime.fromisoformat(from_date).date()
    else:
        from_date_obj = date.today()
    
    if to_date:
        to_date_obj = datetime.fromisoformat(to_date).date()
    else:
        to_date_obj = from_date_obj + timedelta(days=90)
    
    # Get FMP provider
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        return self._wrap_error("FMP_API_KEY not configured")
    
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
        
        return self._wrap_result({
            "dividends": normalized,
            "source": "fmp",
            "count": len(normalized)
        }, source="fmp", ttl=self.CACHE_TTL_HOUR)
        
    except Exception as e:
        logger.error(f"Error fetching dividends from FMP: {e}", exc_info=True)
        return self._wrap_error(f"FMP error: {str(e)}")
```

#### 2. `corporate_actions.splits`
```python
async def corporate_actions_splits(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    symbols: Optional[List[str]] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Capability: corporate_actions.splits
    Fetch stock split calendar from FMP.
    """
    # Similar implementation to dividends
    # ...
```

#### 3. `corporate_actions.earnings`
```python
async def corporate_actions_earnings(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    symbols: Optional[List[str]] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Capability: corporate_actions.earnings
    Fetch earnings calendar from FMP.
    """
    # Similar implementation
    # ...
```

#### 4. `corporate_actions.upcoming` (Main Pattern Capability)
```python
async def corporate_actions_upcoming(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    portfolio_id: str,
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
        portfolio_id: Portfolio UUID
        symbols: List of symbols (if None, will fetch from portfolio)
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
            "source": "fmp"
        }
    """
    from datetime import date, timedelta
    
    # Resolve symbols from portfolio if not provided
    if not symbols:
        # Get holdings from state (should be set by previous step)
        positions = state.get("positions", {}).get("positions", [])
        symbols = [p.get("symbol") for p in positions if p.get("qty_open", 0) > 0]
    
    if not symbols:
        return self._wrap_result({
            "actions": [],
            "summary": {
                "total_actions": 0,
                "dividends_expected": 0.00,
                "splits_pending": 0,
                "earnings_releases": 0
            }
        }, source="fmp", ttl=self.CACHE_TTL_HOUR)
    
    # Calculate date range
    from_date = date.today()
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
    
    return self._wrap_result({
        "actions": all_actions,
        "summary": {
            "total_actions": len(all_actions),
            "dividends_expected": dividends_total,
            "splits_pending": splits_count,
            "earnings_releases": earnings_count
        },
        "source": "fmp"
    }, source="fmp", ttl=self.CACHE_TTL_30MIN)
```

#### 5. `corporate_actions.calculate_impact`
```python
async def corporate_actions_calculate_impact(
    self,
    ctx: RequestCtx,
    state: Dict[str, Any],
    actions: List[Dict],
    holdings: Dict[str, float]  # {symbol: quantity}
) -> Dict[str, Any]:
    """
    Capability: corporate_actions.calculate_impact
    Calculate portfolio impact for corporate actions.
    
    Args:
        actions: List of corporate actions
        holdings: Dict of {symbol: quantity} for portfolio holdings
    
    Returns:
        {
            "actions": [...],  # Actions with impact calculations
            "total_dividend_impact": 120.00,
            "notifications": {
                "urgent": [...],  # Actions within 7 days
                "informational": [...]
            }
        }
    """
    from datetime import date, timedelta
    
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
    cutoff_date = date.today() + timedelta(days=7)
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
    
    return self._wrap_result({
        "actions": actions_with_impact,
        "total_dividend_impact": total_dividend_impact,
        "notifications": {
            "urgent": urgent,
            "informational": informational
        }
    }, source="fmp", ttl=self.CACHE_TTL_30MIN)
```

**Files to Modify:**
- `backend/app/agents/data_harvester.py` - Add 5 new methods

**Validation:**
- [ ] Capabilities registered in `get_capabilities()`
- [ ] Methods follow BaseAgent patterns
- [ ] Error handling and logging
- [ ] TTL values appropriate
- [ ] Metadata attached correctly

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
        "dataPath": "actions_with_impact"
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
        },
        {
          "label": "Total Dividend Impact",
          "value": "{{actions_with_impact.total_dividend_impact}}",
          "format": "currency",
          "color_condition": "sign"
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
        {"field": "portfolio_impact", "header": "Impact", "format": "currency", "width": 120, "color_condition": "sign"}
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
- [ ] Template substitution works
- [ ] Outputs match expected format

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
        
        // Apply type filter
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
            // ... existing filter controls ...
        ),
        
        // PatternRenderer for main content
        e(PatternRenderer, {
            pattern: 'corporate_actions_upcoming',
            inputs: patternInputs,
            onDataLoaded: handlePatternData,
            config: {
                // Custom config if needed
            }
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

## 📊 Implementation Timeline

**Total Estimated Time:** 20-30 hours

### Phase 1: FMP Provider Extension (4-6 hours)
- Add 5 methods to `FMPProvider`
- Test rate limiting and error handling

### Phase 2: DataHarvester Capabilities (6-8 hours)
- Add 5 capabilities to `DataHarvester`
- Implement orchestration logic
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

## 🚨 Critical Considerations

### 1. FMP Pro API Requirements

**Rate Limits:**
- Basic: 3,000 calls/day ($29/month)
- Professional: 10,000 calls/day ($79/month)
- Enterprise: 100,000 calls/day ($299/month)

**Recommendation:** Start with Basic ($29/month) for alpha

**API Key:**
- Must be set in environment: `FMP_API_KEY`
- Provider validates key on initialization

### 2. Pattern Template Substitution

**Complex Template:**
```json
"symbols": "{{positions.positions[*].symbol}}"
```

**Implementation:**
- PatternOrchestrator must extract symbols from positions array
- May need custom template resolver for array extraction
- Fallback: Pass full positions array, extract in capability

### 3. Portfolio Holdings Integration

**Step 1 Pattern:**
```json
{
  "capability": "ledger.positions",
  "args": {
    "portfolio_id": "{{inputs.portfolio_id}}"
  },
  "as": "positions"
}
```

**Step 2 Usage:**
```json
{
  "capability": "corporate_actions.upcoming",
  "args": {
    "symbols": "{{positions.positions[*].symbol}}"
  }
}
```

**Challenge:** Array extraction in templates
**Solution:** Extract symbols in capability if template fails

### 4. Date Handling

**FMP API:**
- Requires `YYYY-MM-DD` format
- Returns ISO format dates
- Must handle timezone conversions

**Implementation:**
- Use `date.today()` for current date
- Use `timedelta` for date ranges
- Convert to ISO format for API calls

### 5. Error Handling

**Provider Errors:**
- API rate limit exceeded
- Invalid API key
- Network failures
- Invalid date ranges

**Capability Errors:**
- Missing portfolio holdings
- Empty symbols list
- FMP API failures

**Pattern Errors:**
- Step execution failures
- Template resolution failures
- State access failures

**UI Errors:**
- Pattern execution failures
- Data extraction failures
- Panel rendering failures

**All errors must be handled gracefully with user-friendly messages.**

---

## ✅ Validation Checklist

### Provider Layer
- [ ] FMP Provider methods implement correctly
- [ ] Rate limiting enforced (120 req/min)
- [ ] Error handling for API failures
- [ ] Response format normalization
- [ ] Date validation

### Agent Layer
- [ ] Capabilities registered correctly
- [ ] Methods follow BaseAgent patterns
- [ ] Error handling and logging
- [ ] TTL values appropriate
- [ ] Metadata attached correctly

### Pattern Layer
- [ ] Pattern JSON valid
- [ ] Steps execute in order
- [ ] Template substitution works
- [ ] Outputs match expected format
- [ ] Error handling works

### UI Layer
- [ ] PatternRegistry entry correct
- [ ] PatternRenderer executes pattern
- [ ] Panels render correctly
- [ ] Data extraction works
- [ ] Filters work
- [ ] Error states display
- [ ] Loading states display

### End-to-End
- [ ] User flow works from UI to API
- [ ] Data flows correctly through all layers
- [ ] Performance acceptable
- [ ] Error handling graceful
- [ ] User experience smooth

---

## 📚 Related Documentation

- `CORPORATE_ACTIONS_UI_INTEGRATION_AUDIT.md` - Original audit
- `CORPORATE_ACTIONS_GUIDE.md` - Feature guide
- `.archive/corporate-actions/FMP_CORPORATE_ACTIONS_CONTEXT.md` - FMP API context
- `backend/patterns/news_impact_analysis.json` - Reference pattern
- `backend/patterns/portfolio_overview.json` - Reference pattern

---

## ✅ Next Steps

1. **Review this plan** - Ensure all aspects covered
2. **Set up FMP Pro API key** - Configure environment variable
3. **Begin Phase 1** - Extend FMP Provider
4. **Continue through phases** - Implement systematically
5. **Test thoroughly** - Validate each phase
6. **Deploy and monitor** - Watch for errors and performance

---

**Plan Created:** November 3, 2025  
**Status:** ✅ **READY FOR IMPLEMENTATION**  
**Estimated Effort:** 20-30 hours  
**Architecture:** Pattern-driven, following existing patterns

