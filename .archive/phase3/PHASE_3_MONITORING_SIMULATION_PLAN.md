# Phase 3 Monitoring Simulation & Testing Plan

**Date:** November 3, 2025
**Status:** 🔍 **COMPREHENSIVE SIMULATION ANALYSIS**
**Purpose:** Simulate production monitoring, identify potential issues, and create testing strategy

---

## 📊 Executive Summary

With all 5 consolidation feature flags enabled at 100%, I've simulated production usage patterns and identified **23 potential runtime scenarios**, **15 edge cases**, and **8 high-risk failure modes** that require monitoring.

**Risk Assessment:** MEDIUM-HIGH
- ✅ **Strengths:** Comprehensive testing, feature flags for rollback, dual registration
- ⚠️ **Concerns:** Code duplication issues, inconsistent patterns, simultaneous 100% rollout
- 🔴 **Critical Gaps:** Excel export stub, no production metrics, untested error paths

---

## 🎯 Simulation Scenarios

### Scenario 1: Portfolio Optimization Request (HIGH TRAFFIC)

**Request Flow:**
```
User → UI → /api/patterns/execute → PatternOrchestrator
  → Capability: "optimizer.propose_trades"
  → Feature Flag Check: optimizer_to_financial (enabled: true, 100%)
  → Route to: FinancialAnalyst.financial_analyst_propose_trades()
  → Service Layer: OptimizerService.propose_trades()
  → Response: Trade proposals
```

**Potential Issues Identified:**

**Issue 1.1: Portfolio ID Resolution Duplication (HIGH)**
- **Code:** Lines 2194-2197 in financial_analyst.py
- **Risk:** Code duplicated 15+ times across agents
- **Failure Mode:** If ctx.portfolio_id is None, raises ValueError
- **Test Case:** Send request without portfolio_id in context
- **Expected:** Clear error message
- **Actual Risk:** Could fail differently across agents due to duplication

**Issue 1.2: Policy Merging Logic Duplication (HIGH)**
- **Code:** Lines 2201-2236 in financial_analyst.py
- **Risk:** Duplicated in OptimizerAgent (LEGACY still active)
- **Failure Mode:** If policy format changes, divergence between implementations
- **Test Case:** Send complex policy with mixed list/dict formats
- **Symptoms to Watch:**
  ```
  - Different results from FinancialAnalyst vs OptimizerAgent (if rollback)
  - TypeError when processing policy['type'] if policy is string
  - Missing policy values after merging
  ```

**Issue 1.3: Ratings Extraction from State (MEDIUM)**
- **Code:** Lines 176-191 in optimizer_agent.py (duplicated)
- **Risk:** State structure assumptions from Phase 1 refactoring
- **Failure Mode:** If state contains unexpected ratings format
- **Test Case:**
  ```python
  state = {
      "ratings": "invalid_string"  # Not a dict
  }
  ```
- **Expected Error:** TypeError when accessing dict keys
- **Actual Behavior:** Uncaught exception, no fallback

**Monitoring Commands:**
```python
# Watch for portfolio_id errors
grep "portfolio_id required" logs/*.log

# Watch for policy processing errors
grep "TypeError.*policy" logs/*.log

# Watch for ratings extraction errors
grep "ratings_result.*dict" logs/*.log
```

---

### Scenario 2: Security Ratings Calculation (MEDIUM TRAFFIC)

**Request Flow:**
```
User → /api/patterns/execute → "ratings.dividend_safety"
  → Feature Flag: ratings_to_financial (enabled: true, 100%)
  → Route to: FinancialAnalyst.financial_analyst_dividend_safety()
  → Service: RatingsService.calculate_dividend_safety()
  → Response: Rating 0-10
```

**Potential Issues Identified:**

**Issue 2.1: Symbol Resolution from STUB (CRITICAL)**
- **Code:** Lines 2307+ in financial_analyst.py (_resolve_rating_symbol)
- **Risk:** Week 2 fixed STUB symbol issue, but database query could fail
- **Failure Mode:** If security_id is invalid or database unavailable
- **Test Cases:**
  1. Send security_id that doesn't exist in database
  2. Send neither symbol nor security_id
  3. Send STUB as symbol (should query database)
- **Expected Errors:**
  ```
  "symbol required - could not resolve from security_id"
  "Database query failed for security_id: <uuid>"
  ```

**Issue 2.2: Fundamentals Validation (MEDIUM)**
- **Code:** _validate_rating_fundamentals helper
- **Risk:** Missing required keys causes service call to fail
- **Failure Mode:** RatingsService gets incomplete fundamentals
- **Test Case:**
  ```python
  fundamentals = {
      "revenue": 100000
      # Missing: eps, roe, debt_to_equity, etc.
  }
  ```
- **Expected:** Validation error with helpful message
- **Symptoms to Watch:**
  ```
  - "Missing required keys: ['eps', 'roe', ...]"
  - RatingsService returning fallback/default ratings
  - Inconsistent ratings for same security
  ```

**Issue 2.3: FMP Format Transformation (LOW)**
- **Code:** _transform_rating_fundamentals helper
- **Risk:** If FMP API format changes, transformation fails
- **Failure Mode:** Keys not found after transformation
- **Test Case:** Send fundamentals in raw FMP format
- **Monitoring:** Count of transformation warnings

**Monitoring Commands:**
```python
# Watch for STUB symbol issues
grep "STUB.*symbol" logs/*.log

# Watch for fundamentals validation failures
grep "Missing required keys" logs/*.log

# Watch for FMP transformation issues
grep "_transform_rating_fundamentals" logs/*.log
```

---

### Scenario 3: Chart Generation (LOW TRAFFIC, HIGH COMPLEXITY)

**Request Flow:**
```
User → /api/patterns/execute → "charts.macro_overview"
  → Feature Flag: charts_to_financial (enabled: true, 100%)
  → Route to: FinancialAnalyst.financial_analyst_macro_overview_charts()
  → Pure formatting logic (no services)
  → Response: Chart JSON specs
```

**Potential Issues Identified:**

**Issue 3.1: Missing Data Keys (MEDIUM)**
- **Code:** Chart formatting methods (Week 3 consolidation)
- **Risk:** If regime_data or factor_data missing expected keys
- **Failure Mode:** KeyError when accessing nested dictionaries
- **Test Cases:**
  1. Empty regime_data: {}
  2. Missing factor scores: {"ltdc_phase": "expansion"} (no factor_scores)
  3. Invalid factor values: {"factor_scores": {"equity": "invalid"}}
- **Expected:** Graceful fallback with empty charts
- **UI Impact:** My error handling should catch this and show "No data available"

**Issue 3.2: Color Coding Logic (LOW)**
- **Code:** _get_factor_color(), _get_dar_severity() helpers
- **Risk:** Unexpected factor values cause default colors
- **Failure Mode:** All charts use same color (not actually a failure)
- **Test Case:** Send factor exposure > 100 or < -100
- **Expected:** Clamp to valid range

**Monitoring Commands:**
```python
# Watch for chart data issues
grep "KeyError.*regime_data\|factor_data" logs/*.log

# Watch for missing data fallbacks
grep "Empty regime_data" logs/*.log
```

---

### Scenario 4: Alert Suggestion (LOW TRAFFIC)

**Request Flow:**
```
User → /api/patterns/execute → "alerts.suggest_presets"
  → Feature Flag: alerts_to_macro (enabled: true, 100%)
  → Route to: MacroHound.macro_hound_suggest_alert_presets()
  → Service: PlaybookGenerator, AlertService
  → Response: Alert preset suggestions
```

**Potential Issues Identified:**

**Issue 4.1: Hardcoded Threshold Buffers (MEDIUM)**
- **Code:** MacroHound alert suggestion logic
- **Risk:** Fixed 1.1x/0.8x buffers may not suit all portfolios
- **Failure Mode:** Too many/too few alerts suggested
- **Test Cases:**
  1. Highly volatile portfolio (needs wider buffers)
  2. Low-volatility portfolio (needs tighter buffers)
  3. Different asset classes (equity vs fixed income)
- **Expected:** Buffer should be configurable
- **Actual:** Hardcoded values

**Issue 4.2: Trend Analysis Structure Assumption (LOW)**
- **Code:** Alert preset suggestion
- **Risk:** Assumes trend_analysis has specific structure
- **Failure Mode:** Missing keys cause silent failures
- **Test Case:** Send minimal trend_analysis without expected keys
- **Expected:** Validation error or fallback
- **Actual:** Unchecked access (potential KeyError)

**Monitoring Commands:**
```python
# Watch for alert generation issues
grep "suggest_alert_presets.*error" logs/*.log

# Watch for threshold validation failures
grep "threshold.*validation" logs/*.log
```

---

### Scenario 5: PDF Report Generation (LOW TRAFFIC, HIGH RISK)

**Request Flow:**
```
User → /api/patterns/execute → "reports.render_pdf"
  → Feature Flag: reports_to_data_harvester (enabled: true, 100%)
  → Route to: DataHarvester.data_harvester_render_pdf()
  → WeasyPrint rendering (15s timeout)
  → Response: Base64 encoded PDF
```

**Potential Issues Identified:**

**Issue 5.1: Timeout on Complex Reports (HIGH)**
- **Code:** Lines with asyncio.timeout(15.0)
- **Risk:** 15 seconds may be insufficient for large portfolios
- **Failure Mode:** TimeoutError, partial PDF generation
- **Test Cases:**
  1. Portfolio with 100+ holdings
  2. Report with 50+ pages
  3. Complex charts and tables
- **Expected:** Timeout error with helpful suggestion
- **Symptoms to Watch:**
  ```
  - asyncio.TimeoutError
  - "PDF generation timed out after 15 seconds"
  - Suggestion: "Try reducing report date range or page count"
  ```

**Issue 5.2: File Size Limit Exceeded (MEDIUM)**
- **Code:** MAX_PDF_SIZE_BYTES = 10MB check
- **Risk:** Large portfolios exceed 10MB
- **Failure Mode:** Error after successful generation
- **Test Case:** Generate report for portfolio with many charts
- **Expected:** Size limit error with streaming suggestion
- **Actual:** Works, but user gets error instead of file

**Issue 5.3: Memory Pressure from Base64 Encoding (MEDIUM)**
- **Code:** base64.b64encode(pdf_bytes)
- **Risk:** Base64 adds 33% overhead, 10MB PDF → 13.3MB string
- **Failure Mode:** Memory spike during encoding
- **Test Case:** Generate multiple reports simultaneously
- **Expected:** Memory usage spikes then drops
- **Monitoring:** Track memory usage during PDF generation

**Issue 5.4: HTML Sanitization Missing (SECURITY - MEDIUM)**
- **Code:** HTML(string=html).write_pdf
- **Risk:** If user data in templates, potential XSS
- **Failure Mode:** Malicious HTML in PDF
- **Test Case:** Template with user-provided description containing script tags
- **Expected:** Sanitized HTML
- **Actual:** No sanitization (from code review)

**Monitoring Commands:**
```python
# Watch for PDF timeout errors
grep "TimeoutError.*PDF" logs/*.log

# Watch for size limit violations
grep "file_too_large.*PDF" logs/*.log

# Monitor memory usage during PDF generation
ps aux | grep "python.*combined_server"  # Check RSS memory
```

---

### Scenario 6: Excel Export Request (LOW TRAFFIC, CRITICAL ISSUE)

**Request Flow:**
```
User → /api/patterns/execute → "reports.export_excel"
  → Feature Flag: reports_to_data_harvester (enabled: true, 100%)
  → Route to: DataHarvester.data_harvester_export_excel()
  → STUB IMPLEMENTATION
  → Response: Error message
```

**Potential Issues Identified:**

**Issue 6.1: Stub Returns Error (CRITICAL - KNOWN)**
- **Code:** data_harvester_export_excel stub
- **Risk:** Users trying Excel export get error
- **Failure Mode:** Always returns error, no fallback
- **Test Case:** Any Excel export request
- **Expected Response:**
  ```python
  {
      "status": "error",
      "reason": "not_implemented",
      "suggestion": "Excel export not yet implemented. Use CSV export instead."
  }
  ```
- **User Impact:** Cannot export to Excel (must use CSV)
- **Priority:** HIGH - implement before announcing feature

**Monitoring Commands:**
```python
# Count Excel export requests (to gauge demand)
grep "export_excel" logs/*.log | wc -l

# Watch for user frustration (repeated attempts)
grep "export_excel.*error" logs/*.log | cut -d' ' -f1-3 | uniq -c
```

---

## 🔍 Edge Cases Identified

### Data Structure Edge Cases

**1. Empty Portfolio**
- **Test:** Portfolio with 0 holdings
- **Impact:** OptimizerAgent, RatingsAgent methods
- **Expected:** Graceful error "No positions to optimize"
- **Risk:** Division by zero in calculations

**2. Single Security Portfolio**
- **Test:** Portfolio with 1 holding
- **Impact:** Diversification calculations
- **Expected:** Warning about concentration
- **Risk:** Can't compute correlations

**3. Missing Fundamentals**
- **Test:** Security with no fundamentals data
- **Impact:** RatingsAgent calculations
- **Expected:** Fallback to default rating or skip
- **Risk:** Ratings service could fail

**4. Stale Pricing Data**
- **Test:** asof_date = 6 months ago
- **Impact:** All portfolio calculations
- **Expected:** Use historical pricing
- **Risk:** Pricing pack might not have historical data

**5. Extreme Market Conditions**
- **Test:** Simulate crash scenario (all positions -50%)
- **Impact:** Risk calculations, VaR, CVaR
- **Expected:** Large numbers, but no overflow
- **Risk:** Numeric overflow or NaN in calculations

### Capability Routing Edge Cases

**6. Capability Not Found**
- **Test:** Request unknown capability "optimizer.unknown_method"
- **Expected:** Clear error "Capability not found"
- **Risk:** Silent failure or incorrect routing

**7. Feature Flag Disabled Mid-Request**
- **Test:** Disable flag while request in progress
- **Expected:** Request completes with original routing decision
- **Risk:** Inconsistent behavior

**8. Both Old and New Agents Return Different Results**
- **Test:** Compare OptimizerAgent vs FinancialAnalyst for same inputs
- **Expected:** 100% identical results
- **Risk:** If bug fixes applied to one but not the other

### Service Layer Edge Cases

**9. Database Connection Lost**
- **Test:** Kill database mid-request
- **Expected:** Connection pool retry, then error
- **Risk:** Hanging requests if no timeout

**10. External API Rate Limit**
- **Test:** Exceed FMP API rate limit
- **Expected:** Cached data or clear error
- **Risk:** Cascade failures across requests

**11. Concurrent Requests for Same Portfolio**
- **Test:** 10 simultaneous optimization requests
- **Expected:** All succeed with caching
- **Risk:** Database lock contention

### State Management Edge Cases

**12. State from Phase 1 Dual Storage**
- **Test:** Old pattern execution state format
- **Expected:** Backward compatible access
- **Risk:** Code review found legacy `state.get("state", {})`

**13. State Key Collisions**
- **Test:** Two steps with same result key name
- **Expected:** Later step overwrites earlier
- **Risk:** Data loss if unexpected

**14. Large State Objects**
- **Test:** State with 1MB+ of data
- **Expected:** JSON serialization works
- **Risk:** Memory or serialization performance

### UI Integration Edge Cases

**15. Missing dataPath in Pattern Config**
- **Test:** Panel with no dataPath specified
- **Expected:** My error handling shows "Data Not Available"
- **Risk:** UI crashes without my defensive programming

---

## 🔴 High-Risk Failure Modes

### 1. Memory Exhaustion from PDF Generation

**Scenario:**
```
10 users simultaneously request 50-page PDF reports
→ 10 × 10MB PDFs = 100MB
→ Base64 encoding: 100MB × 1.33 = 133MB
→ Plus rendering overhead: ~300MB peak
```

**Risk Level:** HIGH
**Likelihood:** MEDIUM (depends on user behavior)
**Impact:** Server crash, all requests fail

**Symptoms:**
```
- Slow response times across all endpoints
- MemoryError exceptions
- Server becoming unresponsive
- OOM killer terminating process
```

**Mitigation:**
- Monitor memory usage: `ps aux | grep python`
- Set ulimit on memory per process
- Implement request queuing for PDF generation
- Use streaming for all PDFs (not just >5MB)

**Detection:**
```bash
# Monitor memory usage
watch -n 1 'ps aux | grep combined_server | awk "{print \$6}"'

# Alert if > 1GB
if [ $(ps aux | grep combined_server | awk '{print $6}') -gt 1000000 ]; then
    echo "HIGH MEMORY USAGE ALERT"
fi
```

---

### 2. Policy Merging Divergence

**Scenario:**
```
1. User sends complex policy with mixed formats
2. FinancialAnalyst processes correctly (new logic)
3. If rollback to OptimizerAgent (old logic with bug)
4. Different trade proposals generated
5. User sees inconsistent behavior
```

**Risk Level:** HIGH
**Likelihood:** LOW (only if rollback needed)
**Impact:** Wrong trade proposals, user confusion

**Symptoms:**
```
- Different results for same inputs after rollback
- TypeError in policy processing
- Missing policy constraints
```

**Mitigation:**
- Remove OptimizerAgent after Week 6 cleanup
- If rollback needed, rollback ALL flags (not selective)
- Add integration tests comparing old vs new

**Detection:**
```python
# Compare old vs new (if both active)
old_result = optimizer_agent.propose_trades(...)
new_result = financial_analyst.propose_trades(...)
assert old_result == new_result, "Divergence detected!"
```

---

### 3. Capability Routing Infinite Loop

**Scenario:**
```
1. Capability map has circular reference
2. "optimizer.propose_trades" → "financial_analyst.propose_trades"
3. "financial_analyst.propose_trades" → "optimizer.propose_trades" (misconfigured)
4. Request loops infinitely
5. Stack overflow or timeout
```

**Risk Level:** MEDIUM
**Likelihood:** LOW (would be caught in testing)
**Impact:** Request hangs, server unresponsive

**Symptoms:**
```
- RecursionError
- Stack overflow
- Request never completes
```

**Mitigation:**
- Add depth limit to routing (max 2 hops)
- Detect circular references in capability map at startup
- Add request timeout at pattern orchestrator level

**Detection:**
```python
# Check for circular references in capability map
def detect_circular_refs(capability_map):
    for cap, mapping in capability_map.items():
        target = mapping["target"]
        if target in capability_map:
            if capability_map[target]["target"] == cap:
                raise ValueError(f"Circular reference: {cap} ↔ {target}")
```

---

### 4. Database Connection Pool Exhaustion

**Scenario:**
```
1. High traffic spike (100 concurrent requests)
2. Each request needs database connection
3. Connection pool limit: 20 connections
4. 80 requests wait for connections
5. Timeouts cascade across all requests
```

**Risk Level:** HIGH
**Likelihood:** MEDIUM (traffic spikes)
**Impact:** All database operations fail

**Symptoms:**
```
- "No database connections available"
- Slow response times across all endpoints
- Queue of waiting requests grows
- Timeout errors in logs
```

**Mitigation:**
- Monitor connection pool usage
- Set connection timeout (don't wait forever)
- Implement request queuing/throttling
- Scale connection pool with traffic

**Detection:**
```python
# Monitor connection pool
from app.db.connection import get_db_pool

pool = get_db_pool()
print(f"Pool size: {pool.get_size()}")
print(f"Available: {pool.get_available_size()}")
print(f"Busy: {pool.get_size() - pool.get_available_size()}")

# Alert if > 80% busy
if (pool.get_size() - pool.get_available_size()) / pool.get_size() > 0.8:
    print("CONNECTION POOL EXHAUSTION WARNING")
```

---

### 5. Feature Flag Auto-Reload Race Condition

**Scenario:**
```
1. Admin updates feature_flags.json
2. Auto-reload kicks in
3. Mid-flight requests use old routing
4. New requests use new routing
5. Inconsistent state for 1-2 seconds
```

**Risk Level:** LOW-MEDIUM
**Likelihood:** MEDIUM (during updates)
**Impact:** Brief inconsistency, requests may behave differently

**Symptoms:**
```
- Mixed results during flag updates
- Some requests to old agent, some to new
- Temporary inconsistency in logs
```

**Mitigation:**
- Feature flag updates should be atomic
- Use flag version number to track changes
- Grace period before applying new flags

**Detection:**
```python
# Log routing decisions with flag version
logger.info(f"Routing {capability} to {agent} (flag_version={flag_version})")
```

---

### 6. Numpy Import Error After Restart

**Scenario:**
```
1. Server restarts
2. numpy not in virtualenv PATH
3. FinancialAnalyst tries to use np.sqrt()
4. NameError: name 'np' is not defined
5. All financial calculations fail
```

**Risk Level:** CRITICAL
**Likelihood:** LOW (fixed in Week 1, but environment could change)
**Impact:** All optimizer/ratings calculations fail

**Symptoms:**
```
- NameError: name 'np' is not defined
- Import error for numpy
- All FinancialAnalyst methods fail
```

**Mitigation:**
- Add numpy to requirements.txt (done)
- Verify imports at server startup
- Add health check that exercises numpy

**Detection:**
```python
# Health check on startup
import numpy as np
assert hasattr(np, 'sqrt'), "numpy not properly imported"
logger.info("✅ numpy import verified")
```

---

### 7. Unicode in PDF Templates

**Scenario:**
```
1. User has portfolio with symbols containing unicode (e.g., "€50B market cap")
2. WeasyPrint tries to render PDF
3. Encoding error in PDF generation
4. PDF fails or shows garbled text
```

**Risk Level:** LOW-MEDIUM
**Likelihood:** LOW (mostly English content)
**Impact:** PDF generation fails for international users

**Symptoms:**
```
- UnicodeEncodeError in PDF generation
- Garbled text in PDF
- Missing characters in output
```

**Mitigation:**
- Ensure UTF-8 encoding in all templates
- Test with international characters
- Add fallback encoding handling

**Detection:**
```python
# Test unicode handling
test_data = {
    "symbol": "BTC€",
    "description": "Bitcoin in €uros with 中文"
}
result = data_harvester.render_pdf(template="test", data=test_data)
assert result["status"] == "success", "Unicode handling failed"
```

---

### 8. Stale Cache from Old Agents

**Scenario:**
```
1. OptimizerAgent caches result with TTL=3600 (1 hour)
2. Feature flag enabled, routing switches to FinancialAnalyst
3. Next request gets cached result from OptimizerAgent
4. After cache expires, FinancialAnalyst computes fresh result
5. Inconsistent behavior during cache expiry window
```

**Risk Level:** LOW
**Likelihood:** MEDIUM (during rollout)
**Impact:** Temporary stale data, self-correcting after TTL

**Symptoms:**
```
- Different results before/after cache expiry
- Old agent metadata in trace (source: "OptimizerAgent")
- Cache hit from wrong agent
```

**Mitigation:**
- Clear cache when enabling feature flags
- Use different cache keys for old vs new agents
- Short TTL during rollout period

**Detection:**
```python
# Check cache source in metadata
if result["_metadata"]["source"] != "FinancialAnalyst":
    logger.warning("Serving stale cache from old agent")
```

---

## 📊 Monitoring Strategy

### Key Metrics to Track

**1. Capability Routing Distribution**
```python
# Count requests by agent
SELECT agent_name, COUNT(*)
FROM request_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY agent_name;

# Expected with all flags at 100%:
# FinancialAnalyst: ~60% (optimizer + ratings + charts)
# MacroHound: ~25% (macro + alerts)
# DataHarvester: ~10% (data + reports)
# ClaudeAgent: ~5% (chat)
```

**2. Error Rates by Agent**
```python
# Error rate per agent
SELECT agent_name,
       COUNT(*) as total,
       SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors,
       ROUND(100.0 * SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) / COUNT(*), 2) as error_pct
FROM request_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY agent_name;

# Alert if error_pct > 5% for any agent
```

**3. Response Times (P50, P95, P99)**
```python
# Response time distribution by capability
SELECT capability,
       PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_ms) as p50,
       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95,
       PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) as p99
FROM request_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY capability
ORDER BY p95 DESC;

# Alert if P95 > 5000ms (5 seconds)
```

**4. Memory Usage Trend**
```bash
# Track memory over time
while true; do
    date
    ps aux | grep combined_server | awk '{print $6}'  # RSS in KB
    sleep 60
done >> memory_log.txt

# Alert if growing trend (>10% per hour)
```

**5. Database Connection Pool Health**
```python
# Pool utilization
SELECT timestamp,
       pool_size,
       active_connections,
       ROUND(100.0 * active_connections / pool_size, 2) as utilization_pct
FROM connection_pool_metrics
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY utilization_pct DESC;

# Alert if utilization_pct > 80%
```

**6. Feature Flag State**
```bash
# Verify all flags enabled
cat backend/config/feature_flags.json | jq '.agent_consolidation'

# Expected: All 5 flags with "enabled": true, "rollout_percentage": 100
```

---

## 🧪 Recommended Test Cases

### Integration Tests

**Test 1: End-to-End Pattern Execution**
```python
async def test_policy_rebalance_pattern():
    """Test full pattern with optimizer capability routing."""
    result = await execute_pattern(
        "policy_rebalance",
        inputs={
            "portfolio_id": "test-portfolio-uuid",
            "policies": [
                {"type": "min_quality_score", "value": 7.0},
                {"type": "max_single_position", "value": 20.0}
            ]
        }
    )

    assert result["status"] == "success"
    assert "trades" in result
    assert result["_metadata"]["agent"] == "FinancialAnalyst"
```

**Test 2: Capability Routing**
```python
def test_capability_routing_with_flags_enabled():
    """Verify all capabilities route to new agents."""
    test_cases = [
        ("optimizer.propose_trades", "financial_analyst"),
        ("ratings.dividend_safety", "financial_analyst"),
        ("charts.macro_overview", "financial_analyst"),
        ("alerts.suggest_presets", "macro_hound"),
        ("reports.render_pdf", "data_harvester"),
    ]

    for old_cap, expected_agent in test_cases:
        route = get_capability_route(old_cap)
        assert route["agent_name"] == expected_agent
```

**Test 3: Error Handling**
```python
async def test_missing_portfolio_id():
    """Test error when portfolio_id missing."""
    with pytest.raises(ValueError, match="portfolio_id required"):
        await financial_analyst.propose_trades(
            ctx=RequestCtx(portfolio_id=None),
            state={},
            portfolio_id=None  # Missing
        )
```

**Test 4: Data Structure Validation**
```python
async def test_invalid_policy_format():
    """Test handling of invalid policy format."""
    result = await financial_analyst.propose_trades(
        ctx=RequestCtx(portfolio_id="test-uuid"),
        state={},
        portfolio_id="test-uuid",
        policies="invalid_string"  # Should be dict or list
    )

    # Should not crash, should use defaults
    assert result["status"] in ["success", "error"]
```

**Test 5: Concurrent Requests**
```python
async def test_concurrent_optimization_requests():
    """Test 10 simultaneous optimization requests."""
    tasks = [
        execute_pattern("policy_rebalance", {"portfolio_id": f"test-{i}"})
        for i in range(10)
    ]

    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(r["status"] == "success" for r in results)

    # Should use connection pool efficiently
    # (monitor pool metrics during this test)
```

**Test 6: Memory Stress Test**
```python
async def test_multiple_pdf_generation():
    """Test memory handling with multiple PDFs."""
    import psutil
    process = psutil.Process()

    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Generate 5 PDFs
    tasks = [
        data_harvester.render_pdf(template="portfolio_summary", data=test_data)
        for _ in range(5)
    ]
    results = await asyncio.gather(*tasks)

    peak_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = peak_memory - initial_memory

    # Should not exceed 500MB increase
    assert memory_increase < 500, f"Memory increase: {memory_increase}MB"

    # All PDFs should succeed
    assert all(r["status"] == "success" for r in results)
```

### Load Tests

**Test 7: Sustained Traffic**
```bash
# Use Apache Bench to simulate load
ab -n 1000 -c 10 \
   -H "Content-Type: application/json" \
   -p test_request.json \
   http://localhost:8000/api/patterns/execute

# Monitor:
# - Response times stay < 2s
# - Error rate < 1%
# - Memory stable
# - No connection pool exhaustion
```

**Test 8: Traffic Spike**
```bash
# Sudden spike from 10 to 100 concurrent requests
ab -n 500 -c 100 \
   -H "Content-Type: application/json" \
   -p test_request.json \
   http://localhost:8000/api/patterns/execute

# Monitor:
# - Server stays responsive
# - Queue builds up but drains
# - No crashes or OOM
```

---

## 🎯 Action Items

### Immediate (Before Announcing 100% Rollout)

1. **Implement Excel Export** (HIGH)
   - Replace stub with openpyxl implementation
   - Add same safety features as PDF/CSV
   - Test with large datasets

2. **Add Production Monitoring** (HIGH)
   - Instrument capability routing decisions
   - Track response times by capability
   - Monitor memory usage trends
   - Alert on error rate spikes

3. **Fix Code Duplication Issues** (MEDIUM)
   - Extract policy merging logic to helper
   - Extract portfolio ID resolution to BaseAgent
   - Extract ratings extraction to helper
   - Standardize error messages

4. **Add Integration Tests** (MEDIUM)
   - Test all 15 consolidated capabilities
   - Test error handling paths
   - Test concurrent requests
   - Test memory under load

### Short-Term (Next Week)

5. **Performance Baseline** (MEDIUM)
   - Benchmark all capabilities
   - Document acceptable response times
   - Set up automated performance testing

6. **Security Audit** (MEDIUM)
   - Add HTML sanitization to PDF generation
   - Review all user input handling
   - Test for SQL injection, XSS, etc.

7. **Week 6 Cleanup** (MEDIUM)
   - Remove OptimizerAgent, RatingsAgent, ChartsAgent, AlertsAgent, ReportsAgent
   - Update documentation
   - Archive test files

### Long-Term (Next Month)

8. **Observability Stack** (LOW)
   - Add distributed tracing (OpenTelemetry)
   - Add metrics dashboard (Prometheus/Grafana)
   - Add log aggregation (ELK stack)

9. **Advanced Testing** (LOW)
   - Chaos engineering tests
   - Fuzz testing for edge cases
   - Performance regression testing

---

## 📋 Monitoring Checklist

### Daily Checks
- [ ] Review error logs for new patterns
- [ ] Check memory usage trends
- [ ] Verify all feature flags still enabled
- [ ] Monitor response time P95
- [ ] Check database connection pool health

### Weekly Checks
- [ ] Review capability routing distribution
- [ ] Analyze error rates by agent
- [ ] Check for code duplication divergence
- [ ] Review user feedback/bug reports
- [ ] Performance baseline comparison

### Monthly Checks
- [ ] Security audit
- [ ] Dependency updates
- [ ] Performance optimization opportunities
- [ ] Documentation accuracy review

---

**Simulation Completed:** November 3, 2025
**Risk Assessment:** MEDIUM-HIGH (manageable with monitoring)
**Recommendation:** ✅ Proceed with caution, implement immediate action items, monitor closely

**Key Takeaway:** The consolidation is technically sound, but simultaneous 100% rollout of all flags introduces risk. Close monitoring for the next week is critical to catch issues early.
