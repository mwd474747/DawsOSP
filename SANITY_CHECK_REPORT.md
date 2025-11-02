# Sanity Check Report: Cleanup Plans
**Generated:** 2025-01-26  
**Purpose:** Identify gaps, missing dependencies, and critical issues before executing cleanup plans

---

## Executive Summary

🔴 **CRITICAL ISSUES FOUND:** Several removals will break imports and dependencies  
⚠️ **MEDIUM RISK:** Scripts and configuration files need updates  
✅ **LOW RISK:** Some removals are safe but need careful execution

---

## 1. CRITICAL: Agent Runtime Dependencies (Will Break)

### 🔴 Issue: `agent_runtime.py` imports compliance and observability

**Location:** `backend/app/core/agent_runtime.py`

**Current Imports:**
```python
from compliance.attribution import get_attribution_manager
from compliance.rights_registry import get_rights_registry
from observability.metrics import get_metrics
```

**Usage:**
- Line 193-194: Initializes `_attribution_manager` and `_rights_registry` in `__init__`
- Line 442: Calls `get_metrics()` in `execute_capability()`
- Line 456: Uses `_attribution_manager` to add attributions
- Line 465-468: Records circuit breaker state in metrics

**Impact:**
- ❌ **Will break** if compliance module removed (ImportError)
- ❌ **Will break** if observability removed (ImportError)
- ❌ **Will break** circuit breaker metrics recording

**Required Fix:**
1. Make imports optional (try/except)
2. Make compliance/observability gracefully degrade
3. OR: Keep modules but disable features

**Recommendation:**
- ⚠️ **Don't delete** compliance/observability modules yet
- ✅ **Make imports optional** first (try/except pattern)
- ✅ **Disable features** instead of removing modules
- ✅ **Then remove** modules after imports are optional

---

### 🔴 Issue: Pattern Orchestrator imports observability

**Location:** `backend/app/core/pattern_orchestrator.py`

**Current Import:**
```python
from observability.metrics import get_metrics
```

**Usage:**
- Likely used for metrics tracking in pattern execution

**Impact:**
- ❌ **Will break** if observability removed (ImportError)

**Required Fix:**
- Make import optional (try/except)
- Gracefully degrade if metrics unavailable

---

## 2. CRITICAL: Circuit Breaker Actually Used (Can't Remove)

### 🔴 Issue: Circuit Breaker is used in production code

**Location:** `backend/app/core/agent_runtime.py`

**Current Usage:**
- Line 183: `self.circuit_breaker = CircuitBreaker()` - Initialized
- Line 419: `if self.circuit_breaker.is_open(agent_name)` - Checked in execute
- Line 462: `self.circuit_breaker.record_success(agent_name)` - Success recorded
- Line 474: `self.circuit_breaker.record_failure(agent_name)` - Failure recorded
- Line 465-468: Circuit breaker state recorded in metrics

**Impact:**
- ❌ **Will break** if CircuitBreaker removed (NameError)
- ❌ Circuit breaker is actually functional, not just dead code

**Required Fix:**
- ⚠️ **Don't remove** CircuitBreaker class
- ✅ **Simplify** CircuitBreaker implementation (remove complex states)
- ✅ **OR:** Make circuit breaker optional (allow disabling)

**Recommendation:**
- Keep CircuitBreaker but simplify (remove OPEN/HALF_OPEN states)
- Make circuit breaker optional (disable if not needed)
- Don't remove entirely - it's used in production code

---

## 3. CRITICAL: Docker Compose Dependencies (Will Break Startup)

### 🔴 Issue: `docker-compose.yml` has Redis dependencies

**Location:** `docker-compose.yml`

**Current Dependencies:**
```yaml
backend:
  depends_on:
    redis:
      condition: service_healthy
  
worker:
  depends_on:
    redis:
      condition: service_healthy

redis:
  image: redis:7-alpine
  # ... full Redis service definition
```

**Impact:**
- ❌ **Will break** if Redis service removed from docker-compose
- ❌ `depends_on: redis` will cause Docker Compose errors
- ❌ Backend and worker won't start (missing dependency)

**Required Fix:**
1. Remove `depends_on: redis` from backend and worker services
2. Remove Redis service definition
3. Remove `REDIS_URL` environment variables
4. Remove Redis health checks

**Files to Update:**
- `docker-compose.yml` - Remove Redis service and dependencies
- `docker-compose.prod.yml` (if exists) - Same updates
- `docker-compose.test.yml` (if exists) - Same updates

---

## 4. MEDIUM RISK: Scripts Reference Removed Features

### ⚠️ Issue: `start.sh` starts Redis

**Location:** `start.sh`

**Current Code:**
```bash
# Line 29: Starts Redis
docker compose up -d postgres redis
```

**Impact:**
- ⚠️ Script will fail if Redis removed from docker-compose
- ⚠️ Will try to start non-existent service

**Required Fix:**
- Update `start.sh` to only start postgres (remove redis)

---

### ⚠️ Issue: `deploy.sh` references observability

**Location:** `deploy.sh`

**Current Code:**
```bash
# Lines 48-49: References observability mode
elif [ "$MODE" = "observability" ]; then
    COMPOSE_FILE="docker-compose.observability.yml"

# Lines 76-79: Lists observability services
if [ "$MODE" = "observability" ]; then
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3001"
    echo "  Jaeger: http://localhost:16686"
fi
```

**Impact:**
- ⚠️ Script references observability mode
- ⚠️ Will fail if `docker-compose.observability.yml` removed

**Required Fix:**
- Remove observability mode handling from `deploy.sh`
- OR: Keep observability mode but make it optional

---

### ⚠️ Issue: `run_api.sh` sets REDIS_URL

**Location:** `backend/run_api.sh`

**Current Code:**
```bash
# Line 100: Sets REDIS_URL
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"

# Line 110: Displays Redis URL
echo "  Redis URL: ${REDIS_URL}"
```

**Impact:**
- ⚠️ Script sets Redis environment variable
- ⚠️ May cause confusion if Redis not available

**Required Fix:**
- Remove `REDIS_URL` from `run_api.sh`
- OR: Keep but make it optional (not required)

---

## 5. MEDIUM RISK: Requirements.txt Dependencies

### ⚠️ Issue: `requirements.txt` has observability packages

**Location:** `backend/requirements.txt`

**Current Dependencies:**
```
prometheus-client>=0.18.0
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-exporter-jaeger>=1.21.0
opentelemetry-instrumentation-fastapi>=0.42b0
sentry-sdk[fastapi]>=1.38.0
```

**Impact:**
- ⚠️ Packages installed but may not be used
- ⚠️ Wasteful but won't break anything if removed
- ⚠️ If removed, imports will fail (already covered above)

**Required Fix:**
- Remove observability packages from `requirements.txt`
- BUT: Only after making imports optional

---

### ⚠️ Issue: `requirements.txt` may have Redis package

**Location:** `backend/requirements.txt`

**Check:**
- Search for `redis>=` in requirements.txt

**Impact:**
- ⚠️ Redis package may be listed but unused
- ⚠️ Won't break if removed (if not imported)

**Required Fix:**
- Remove Redis package if present
- BUT: Check if `redis_pool_coordinator.py` imports it first

---

## 6. LOW RISK: Documentation References

### ✅ Issue: Documentation mentions removed features

**Locations:**
- `README.md` - May mention Redis/observability
- `DEPLOYMENT_GUIDE.md` - May mention Redis
- `ARCHITECTURE.md` - May mention removed features
- Various other docs

**Impact:**
- ✅ Won't break code
- ⚠️ May cause confusion

**Required Fix:**
- Update documentation to reflect removals
- Not critical, but good practice

---

## 7. LOW RISK: Environment Variables

### ✅ Issue: Environment variables reference removed features

**Locations:**
- `docker-compose.yml` - `REDIS_URL`, `OTLP_ENDPOINT`, `SENTRY_DSN`
- `.env` files (if exist) - May have Redis/observability vars

**Impact:**
- ✅ Won't break code (env vars can be unused)
- ⚠️ May cause confusion

**Required Fix:**
- Remove unused environment variables
- Not critical, but good cleanup

---

## 8. CRITICAL: Redis Pool Coordinator Usage

### 🔴 Issue: `db/connection.py` imports Redis coordinator

**Location:** `backend/app/db/connection.py`

**Current Code:**
```python
# Line 64-69: Tries to register with Redis coordinator
try:
    if hasattr(coordinator, '_local_pool'):
        coordinator._local_pool = pool
        logger.info(f"✅ Pool registered in Redis coordinator")
except Exception as e:
    logger.warning(f"Could not register pool in Redis coordinator: {e}")
```

**Impact:**
- ⚠️ Already has try/except - won't break
- ✅ Gracefully degrades if Redis coordinator unavailable
- ⚠️ BUT: Import of `redis_pool_coordinator` will fail if module removed

**Check:**
- Verify if `redis_pool_coordinator` is imported (need to check)

**Required Fix:**
- Make Redis coordinator import optional (try/except)
- OR: Remove Redis coordinator code entirely

---

## 9. Execution Order Issues

### ⚠️ Issue: Dependencies must be removed in correct order

**Critical Path:**
1. **First:** Make imports optional in `agent_runtime.py` and `pattern_orchestrator.py`
2. **Then:** Remove compliance/observability modules
3. **Then:** Update docker-compose.yml
4. **Then:** Update scripts
5. **Then:** Update requirements.txt

**Impact:**
- ⚠️ Wrong order will cause ImportErrors
- ⚠️ Must make code resilient BEFORE removing modules

**Required Fix:**
- Follow correct execution order
- Test after each step

---

## 10. Summary of Critical Issues

### 🔴 Must Fix Before Removal:

1. **Agent Runtime imports** - Make optional (try/except)
2. **Pattern Orchestrator imports** - Make optional (try/except)
3. **Circuit Breaker usage** - Simplify, don't remove
4. **Docker Compose dependencies** - Remove Redis service and depends_on
5. **Redis Pool Coordinator import** - Make optional or remove entirely

### ⚠️ Should Fix Before Removal:

6. **Scripts** - Update `start.sh`, `deploy.sh`, `run_api.sh`
7. **Requirements.txt** - Remove observability packages (after making imports optional)
8. **Documentation** - Update to reflect removals

### ✅ Low Risk (Can Fix Later):

9. **Environment variables** - Clean up unused vars
10. **Documentation** - Update docs to reflect changes

---

## 11. Recommended Fix Sequence

### Phase 0: Make Code Resilient (CRITICAL - Do First)

1. **Update `agent_runtime.py`:**
   ```python
   # Make imports optional
   try:
       from compliance.attribution import get_attribution_manager
       from compliance.rights_registry import get_rights_registry
   except ImportError:
       get_attribution_manager = None
       get_rights_registry = None
   
   try:
       from observability.metrics import get_metrics
   except ImportError:
       def get_metrics():
           return None
   ```

2. **Update `pattern_orchestrator.py`:**
   ```python
   # Make import optional
   try:
       from observability.metrics import get_metrics
   except ImportError:
       def get_metrics():
           return None
   ```

3. **Update `db/connection.py`:**
   ```python
   # Make Redis coordinator optional
   try:
       from app.db.redis_pool_coordinator import coordinator
   except ImportError:
       coordinator = None
   ```

### Phase 1: Remove Modules (After Phase 0)

4. Delete `backend/compliance/` (archive instead)
5. Delete `backend/observability/`
6. Delete `backend/app/db/redis_pool_coordinator.py`

### Phase 2: Update Configuration (After Phase 1)

7. Update `docker-compose.yml` (remove Redis service and depends_on)
8. Update `start.sh` (remove redis from docker compose)
9. Update `deploy.sh` (remove observability mode)
10. Update `run_api.sh` (remove REDIS_URL)

### Phase 3: Clean Up (After Phase 2)

11. Update `requirements.txt` (remove observability packages)
12. Update documentation
13. Simplify CircuitBreaker (optional)

---

## 12. Risk Assessment Summary

| Issue | Risk Level | Breakage Impact | Fix Complexity |
|-------|-----------|-----------------|----------------|
| Agent Runtime imports | 🔴 Critical | ImportError on startup | Medium (try/except) |
| Pattern Orchestrator imports | 🔴 Critical | ImportError on startup | Medium (try/except) |
| Circuit Breaker usage | 🔴 Critical | NameError at runtime | Medium (simplify) |
| Docker Compose Redis | 🔴 Critical | Service won't start | Low (remove service) |
| Redis Pool Coordinator | ⚠️ Medium | ImportError if not optional | Low (make optional) |
| Scripts | ⚠️ Medium | Script failures | Low (update scripts) |
| Requirements.txt | ⚠️ Medium | Package conflicts | Low (remove packages) |
| Documentation | ✅ Low | Confusion only | Low (update docs) |

---

## 13. Conclusion

### Critical Gaps Found:

1. ❌ **Import errors** will break if modules removed before making imports optional
2. ❌ **Docker Compose** will fail if Redis removed without updating dependencies
3. ❌ **Circuit Breaker** is actually used - can't just remove it
4. ⚠️ **Scripts** will fail if not updated
5. ⚠️ **Requirements** should be cleaned up but after imports are optional

### Required Actions:

1. **MUST DO FIRST:** Make all imports optional (try/except pattern)
2. **THEN:** Remove modules safely
3. **THEN:** Update docker-compose and scripts
4. **THEN:** Clean up requirements.txt
5. **OPTIONAL:** Simplify CircuitBreaker (don't remove)

### Recommendation:

✅ **Plans are sound** but need execution order fix  
⚠️ **Don't remove modules** until imports are optional  
🔴 **Don't remove CircuitBreaker** - simplify instead  
✅ **Proceed with caution** - test after each phase

---

## 14. Missing from Plans

### Not Covered:

1. ❌ **Import error handling** - Plans don't mention making imports optional first
2. ❌ **Circuit Breaker is actually used** - Plans say "remove" but it's functional
3. ❌ **Docker Compose dependencies** - Plans don't mention updating depends_on
4. ❌ **Script updates** - Plans don't mention updating start.sh, deploy.sh
5. ⚠️ **Redis Pool Coordinator** - Plans mention removing but not import handling

### Should Add to Plans:

1. **Phase 0:** Make imports optional (try/except)
2. **Phase 1:** Remove modules (after Phase 0)
3. **Phase 2:** Update docker-compose.yml dependencies
4. **Phase 3:** Update scripts (start.sh, deploy.sh, run_api.sh)
5. **Phase 4:** Simplify CircuitBreaker (don't remove)

