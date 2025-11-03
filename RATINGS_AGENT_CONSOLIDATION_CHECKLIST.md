# RatingsAgent - Quick Reference & Implementation Checklist

---

## FOUR METHODS AT A GLANCE

```
METHOD                          LINES    PATTERN         RETURNS
────────────────────────────────────────────────────────────────────
ratings_dividend_safety()       61-166   Pass-through    overall: 0-10
ratings_moat_strength()         168-267  Pass-through    overall: 0-10
ratings_resilience()            269-368  Pass-through    overall: 0-10
ratings_aggregate()             370-429  Delegation      overall: 0-100 + grade
  └─ _aggregate_single_rating() 431-509
  └─ _aggregate_portfolio()     511-605
  └─ _rating_to_grade()         607-618
```

---

## EXECUTION FLOW DIAGRAM

```
All 4 Methods Follow This Pattern:

┌─────────────────────────────────────────────────────────────┐
│ ratings_[dividend_safety|moat_strength|resilience]()        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. RESOLVE SYMBOL                                           │
│     param → fundamentals.get("symbol")                       │
│               → state["fundamentals"]["symbol"]              │
│               → "STUB" (if security_id only)                 │
│                                                              │
│  2. RESOLVE FUNDAMENTALS                                     │
│     param → state["fundamentals"]                            │
│     (required - must be present)                             │
│                                                              │
│  3. TRANSFORM IF NEEDED                                      │
│     if "income_statement" in fundamentals:                   │
│        transform_fmp_to_ratings_format()                     │
│                                                              │
│  4. CALL SERVICE                                             │
│     await ratings_service.calculate_dividend_safety(        │
│        symbol, fundamentals, security_id)                   │
│                                                              │
│  5. ATTACH METADATA                                          │
│     _create_metadata(source, asof, ttl=86400)               │
│     _attach_metadata(result, metadata)                       │
│                                                              │
│  6. ERROR HANDLING                                           │
│     try/except → return error_result with ttl=0             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## CODE DUPLICATION MAP

```
PATTERN                          LOCATION                    FREQUENCY
─────────────────────────────────────────────────────────────────────
Symbol resolution                98-110, 199-212, 300-313,   4x IDENTICAL
                                 440-453

Fundamentals resolution          113-119, 215-221, 316-322,  4x IDENTICAL
                                 456-462

FMP transformation check         124-130, 226-232, 327-333,  4x IDENTICAL
                                 467-473

Metadata + success handling      144-150, 246-252, 347-353,  4x IDENTICAL
                                 487-493

Error handling + fallback        161-166, 262-267, 363-368,  4x IDENTICAL
                                 504-509
```

**CONSOLIDATION OPPORTUNITY:** Extract 5 helper methods to eliminate duplication

---

## PARAMETER RESOLUTION CASCADE

```
SYMBOL RESOLUTION:
┌─ Direct parameter: symbol = "AAPL"
├─ From fundamentals: fundamentals.get("symbol")
├─ From state: state["fundamentals"]["symbol"]
├─ From security_id: symbol = "STUB" (WARNING!)
└─ If none: raise ValueError

FUNDAMENTALS RESOLUTION:
┌─ Direct parameter: fundamentals = {...}
├─ From state: state["fundamentals"]
└─ If none: raise ValueError
    "fundamentals required. Run fundamentals.load first."
```

---

## SERVICE DELEGATION PATTERN

All 4 methods use this identical pattern:

```python
# Get service singleton
ratings_service = get_ratings_service()
security_uuid = UUID(security_id) if security_id else None

try:
    # Call appropriate service method
    result = await ratings_service.calculate_dividend_safety(
        symbol=symbol,
        fundamentals=transformed_fundamentals,
        security_id=security_uuid,
    )
    
    # Attach metadata for success case
    metadata = self._create_metadata(
        source=f"ratings_service:v1:{ctx.asof_date}",
        asof=ctx.asof_date or date.today(),
        ttl=86400,
    )
    return self._attach_metadata(result, metadata)
    
except Exception as e:
    # Return error result with fallback score
    error_result = {
        "overall": Decimal("0"),
        "error": str(e),
        "symbol": symbol,
        "security_id": security_id,
    }
    metadata = self._create_metadata(
        source="ratings_service:error",
        asof=ctx.asof_date or date.today(),
        ttl=0,  # Don't cache errors
    )
    return self._attach_metadata(error_result, metadata)
```

---

## RATING SCALES & GRADES

### Individual Ratings (0-10 scale)
- **Dividend Safety:** Payout ratio, FCF coverage, growth streak, net cash
- **Moat Strength:** ROE consistency, gross margin, intangibles, switching costs
- **Resilience:** Debt/equity, interest coverage, current ratio, margin stability

### Aggregate Rating (0-100 scale with weights)
```
Moat Strength:    40%  ┐
Dividend Safety:  30%  ├─→ OVERALL RATING (0-100)
Resilience:       30%  ┘
```

### Letter Grades
```
A: 90-100   Exceptional quality (Buffett's "wonderful")
B: 80-89    Strong quality (Buffett's "good")
C: 70-79    Acceptable quality (requires fair price)
D: 60-69    Below average (avoid unless deeply discounted)
F: <60      Poor quality (stay away)
```

---

## PORTFOLIO AGGREGATION MODE

```
ratings_aggregate(positions=[...]) →

FOR EACH POSITION:
  ├─ Extract: symbol, security_id, value
  ├─ Check: fundamentals available?
  │   └─ If NO: skip, add to unrated_count
  ├─ Call: ratings_service.aggregate()
  ├─ Extract: overall_rating, grade, components
  └─ Accumulate: weighted_rating_sum += rating * value

CALCULATE PORTFOLIO AVERAGE:
  portfolio_avg = weighted_rating_sum / total_value
  portfolio_grade = _rating_to_grade(portfolio_avg)

RETURN:
  {
    "positions": [rated positions],
    "portfolio_avg_rating": float,
    "portfolio_avg_grade": str,
    "rated_count": int,
    "unrated_count": int,
  }
```

---

## HELPER METHODS

### _rating_to_grade(rating: Decimal) → str
```python
def _rating_to_grade(self, rating: Decimal) -> str:
    if rating >= Decimal("90"):
        return "A"
    elif rating >= Decimal("80"):
        return "B"
    elif rating >= Decimal("70"):
        return "C"
    elif rating >= Decimal("60"):
        return "D"
    else:
        return "F"
```
**Used by:** ratings_aggregate(), _aggregate_portfolio_ratings()

### _aggregate_single_rating() [PRIVATE]
- Resolves symbol + fundamentals
- Calls RatingsService.aggregate()
- Returns aggregated result with metadata

### _aggregate_portfolio_ratings() [PRIVATE]
- Iterates positions list
- Rates each position (skips missing fundamentals)
- Calculates weighted portfolio average
- Returns positions + averages with metadata

---

## LOGGING PATTERNS

```
ENTRY:
  INFO: f"ratings.dividend_safety: symbol={symbol}"

TRANSFORMATION:
  INFO: f"Transforming FMP fundamentals for {symbol}"

SUCCESS:
  (No log, implicit success via metadata)

ERROR:
  ERROR: f"Dividend safety calculation failed for {symbol}: {e}"
         exc_info=True
```

---

## CACHING STRATEGY

```
CACHE TTL DECISIONS:

SUCCESS RESULTS:
  ttl=86400 (1 day)
  Rationale: Ratings based on stable fundamentals, safe to cache

ERROR RESULTS:
  ttl=0 (no cache)
  Rationale: Prevent stale error results from being returned repeatedly

SOURCE TRACKING:
  source="ratings_service:v1:{ctx.asof_date}"
  source="ratings_service:error"
```

---

## CONSOLIDATION CHECKLIST FOR WEEK 2

### Phase 1: Direct Method Move
- [ ] Copy `ratings_dividend_safety()` → `financial_analyst_dividend_safety()`
- [ ] Copy `ratings_moat_strength()` → `financial_analyst_moat_strength()`
- [ ] Copy `ratings_resilience()` → `financial_analyst_resilience()`
- [ ] Copy `ratings_aggregate()` → `financial_analyst_aggregate_ratings()`
- [ ] Copy helper methods: `_aggregate_single_rating()`, `_aggregate_portfolio_ratings()`, `_rating_to_grade()`

### Phase 2: Update get_capabilities()
- [ ] Add "financial_analyst.dividend_safety"
- [ ] Add "financial_analyst.moat_strength"
- [ ] Add "financial_analyst.resilience"
- [ ] Add "financial_analyst.aggregate_ratings"

### Phase 3: Code Deduplication (OPTIONAL but RECOMMENDED)
- [ ] Extract `_resolve_symbol()` helper
- [ ] Extract `_resolve_fundamentals()` helper
- [ ] Extract `_transform_if_needed()` helper
- [ ] Update all 4 methods to use helpers
- [ ] Reduce code by ~40%

### Phase 4: Testing
- [ ] Test single security dividend_safety
- [ ] Test single security moat_strength
- [ ] Test single security resilience
- [ ] Test single security aggregate
- [ ] Test portfolio aggregate with all positions rated
- [ ] Test portfolio aggregate with mixed rated/unrated
- [ ] Test error handling for missing fundamentals
- [ ] Test error handling for service exceptions
- [ ] Test grading conversion (A/B/C/D/F)

### Phase 5: Documentation
- [ ] Update FinancialAnalyst module docstring
- [ ] Document new capabilities in method docstring
- [ ] Add usage examples for portfolio aggregation
- [ ] Update README with consolidated capabilities
- [ ] Create migration note for RatingsAgent deprecation

### Phase 6: Backward Compatibility (IF NEEDED)
- [ ] Keep RatingsAgent as thin proxy to FinancialAnalyst
- [ ] OR deprecate RatingsAgent with warning message
- [ ] Update existing patterns that call RatingsAgent

---

## POTENTIAL ISSUES TO WATCH

### 1. Stub Symbol Problem
**Lines:** 104-107, 206-209, 307-310, 447-450
**Risk:** Symbol="STUB" when only security_id provided, breaks ratings
**Fix:** Add security_id → symbol lookup to database

### 2. Missing Fundamentals Keys
**Risk:** Assumes all keys present in fundamentals dict
**Fix:** Add schema validation before service call

### 3. Portfolio with No Ratings
**Risk:** If all positions missing fundamentals, portfolio_avg_rating = 0
**Fix:** Return explicit empty/warning state

### 4. Precision Loss
**Risk:** Decimal → float conversion in portfolio mode
**Fix:** LOW - acceptable for display purposes

---

## KEY DIFFERENCES FROM OTHER AGENTS

### vs OptimizerAgent
- RatingsAgent: Simpler, more consistent patterns
- OptimizerAgent: More complex parameter merging
- RatingsAgent: Higher duplication (easy to extract)
- OptimizerAgent: More varied error handling

### vs DataHarvester
- RatingsAgent: No external API calls
- DataHarvester: Heavy API integration
- RatingsAgent: Delegates to service layer
- DataHarvester: Mixed agent + service logic

### vs ReportsAgent
- RatingsAgent: Data transformation, not aggregation
- ReportsAgent: Aggregation from multiple sources
- RatingsAgent: Simple 4-method set
- ReportsAgent: Complex multi-source merging

---

## PERFORMANCE CONSIDERATIONS

### Service Call Time Estimates
```
calculate_dividend_safety():   ~10-50ms (CPU-only, no DB)
calculate_moat_strength():     ~10-50ms (CPU-only, no DB)
calculate_resilience():        ~10-50ms (CPU-only, no DB)
aggregate():                   ~30-150ms (3x individual calls)
aggregate_portfolio() [10 pos]:~300-1500ms (10 aggregate calls)
```

### Database Load
```
Per-method DB calls:
  - _load_rubrics() (once per service singleton): 1 query (CACHED)
  - Fallback weights: 0 DB calls

Total DB load: MINIMAL (only rubrics table, once cached)
```

---

## FILE REFERENCES

### Key Files to Update
- `backend/app/agents/financial_analyst.py` - Add 4 methods + 3 helpers
- `backend/app/agents/ratings_agent.py` - Can be deprecated or kept as proxy
- `backend/app/services/ratings.py` - No changes (already well-factored)

### Files NOT to Touch
- `backend/app/services/fundamentals_transformer.py` - Works correctly
- `backend/app/services/ratings.py` - Well-designed service layer
- `backend/app/core/types.py` - RequestCtx definition
- Database migrations - rating_rubrics table already exists

---

**Last Updated:** 2025-11-03  
**Consolidation Status:** Ready for Week 2 implementation  
**Effort Estimate:** 1-1.5 hours (including testing + deduplication)
