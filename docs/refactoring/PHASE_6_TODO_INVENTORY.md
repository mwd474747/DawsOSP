# Phase 6: Fix TODOs - Inventory

**Date:** January 15, 2025  
**Status:** 🚧 IN PROGRESS  
**Current Step:** Inventory and categorize all TODOs

---

## Summary

**Total TODOs Found:** 52 (51 backend + 1 frontend)

---

## TODO Inventory

### P1 (Critical) - Must Fix Before Production

#### 1. Database Schema TODOs
- **Location:** `backend/app/services/alerts.py:675`
  - **TODO:** Create security_ratings table in schema
  - **Impact:** HIGH - Alert system cannot function without this table
  - **Fix:** Add migration to create table

- **Location:** `backend/app/services/alerts.py:885`
  - **TODO:** Create news_sentiment table in schema
  - **Impact:** HIGH - News-based alerts cannot function
  - **Fix:** Add migration to create table

- **Location:** `backend/db/migrations/011_alert_delivery_system.sql:62,66,70`
  - **TODO:** Add proper user isolation when alert ownership is defined
  - **Impact:** HIGH - Security issue, RLS not properly configured
  - **Fix:** Update RLS policies when user ownership is added

#### 2. Security TODOs
- **Location:** `backend/app/services/reports.py:699-700`
  - **TODO:** Get real IP from request context
  - **TODO:** Get real user agent
  - **Impact:** HIGH - Audit trail incomplete
  - **Fix:** Extract from request context

#### 3. Placeholder Values
- **Location:** `backend/app/services/alerts.py:550,632,968,1071`
  - **TODO:** Replace "xxx" placeholder values
  - **Impact:** HIGH - Example code may be executed
  - **Fix:** Remove or document as examples

- **Location:** `backend/app/services/notifications.py:24,38`
  - **TODO:** Replace "xxx" placeholder values
  - **Impact:** HIGH - Configuration incomplete
  - **Fix:** Use environment variables

- **Location:** `backend/app/services/dlq.py:34`
  - **TODO:** Replace "xxx" placeholder values
  - **Impact:** HIGH - DLQ system incomplete
  - **Fix:** Use proper values

- **Location:** `backend/app/core/alert_validators.py:228,283`
  - **TODO:** Replace "xxx" placeholder values
  - **Impact:** HIGH - Validation incomplete
  - **Fix:** Use proper values

---

### P2 (High) - Should Fix Soon

#### 4. Missing Functionality
- **Location:** `backend/app/services/optimizer.py:619,680`
  - **TODO:** Add expected return, volatility, Sharpe, max DD calculations
  - **Impact:** MEDIUM - Incomplete optimization results
  - **Fix:** Implement calculations or document limitations

- **Location:** `backend/app/agents/macro_hound.py:799`
  - **TODO:** Implement cycle-adjusted DaR if cycle_adjusted=True
  - **Impact:** MEDIUM - Feature incomplete
  - **Fix:** Implement or document limitation

- **Location:** `backend/app/agents/data_harvester.py:1172`
  - **TODO:** Implement sector-based lookup for switching costs
  - **Impact:** MEDIUM - Feature incomplete
  - **Fix:** Implement or document limitation

- **Location:** `backend/app/services/currency_attribution.py:426`
  - **TODO:** Check for FX hedge positions
  - **Impact:** MEDIUM - Attribution incomplete
  - **Fix:** Implement FX hedge detection

- **Location:** `backend/app/services/risk.py:332`
  - **TODO:** Add asset class classification
  - **Impact:** MEDIUM - Risk analysis incomplete
  - **Fix:** Implement asset class classification

#### 5. Integration TODOs
- **Location:** `backend/app/services/alerts.py:1431`
  - **TODO:** Integrate with email service (SendGrid, SES, etc.)
  - **Impact:** MEDIUM - Email alerts not functional
  - **Fix:** Implement email integration

- **Location:** `backend/app/services/alerts.py:1460`
  - **TODO:** Integrate with SMS service (Twilio, etc.)
  - **Impact:** MEDIUM - SMS alerts not functional
  - **Fix:** Implement SMS integration

- **Location:** `backend/app/services/alerts.py:1488`
  - **TODO:** Implement webhook delivery
  - **Impact:** MEDIUM - Webhook alerts not functional
  - **Fix:** Implement webhook delivery

- **Location:** `backend/app/services/alerts.py:1543`
  - **TODO:** Implement retry scheduling (Redis, Celery, etc.)
  - **Impact:** MEDIUM - Alert retries not functional
  - **Fix:** Implement retry mechanism

#### 6. Configuration TODOs
- **Location:** `backend/app/services/metrics.py:190`
  - **TODO:** Make configurable via environment variable or database setting
  - **Impact:** MEDIUM - Hardcoded configuration
  - **Fix:** Add configuration option

- **Location:** `backend/app/db/continuous_aggregate_manager.py:180`
  - **TODO:** Check if job is enabled
  - **Impact:** MEDIUM - Jobs may run when disabled
  - **Fix:** Add enabled check

---

### P3 (Medium) - Nice to Have

#### 7. Enhancement TODOs
- **Location:** `backend/app/agents/data_harvester.py:762`
  - **TODO:** Enhance transformer to use ratios data for more accurate metrics
  - **Impact:** LOW - Enhancement, current functionality works
  - **Fix:** Implement enhancement or document limitation

- **Location:** `backend/app/agents/base_agent.py:574`
  - **TODO:** Implement Redis caching
  - **Impact:** LOW - Performance optimization
  - **Fix:** Implement Redis caching

- **Location:** `backend/app/core/service_initializer.py:177`
  - **TODO:** Update agents to accept services as constructor parameters
  - **Impact:** LOW - Architecture improvement
  - **Fix:** Refactor agent constructors

- **Location:** `backend/app/core/service_initializer.py:243`
  - **TODO:** Wire real Redis when needed
  - **Impact:** LOW - Feature not yet needed
  - **Fix:** Implement when needed

- **Location:** `backend/jobs/compute_macro.py:352`
  - **TODO:** Send alert notification
  - **Impact:** LOW - Feature enhancement
  - **Fix:** Implement alert notification

- **Location:** `backend/jobs/scheduler.py:463`
  - **TODO:** Implement ratings pre-warm
  - **Impact:** LOW - Performance optimization
  - **Fix:** Implement pre-warming

- **Location:** `backend/jobs/scheduler.py:472`
  - **TODO:** Status "TODO" - likely placeholder
  - **Impact:** LOW - Status tracking incomplete
  - **Fix:** Update status

- **Location:** `backend/app/services/corporate_actions_sync.py:310`
  - **TODO:** Add withholding tax logic
  - **Impact:** LOW - Feature enhancement
  - **Fix:** Implement withholding tax logic

- **Location:** `backend/jobs/metrics.py:281`
  - **TODO:** Get portfolio positions and FX rates from database
  - **Impact:** LOW - Feature enhancement
  - **Fix:** Implement database queries

- **Location:** `backend/jobs/metrics.py:925`
  - **TODO:** Implement trading metrics
  - **Impact:** LOW - Feature enhancement
  - **Fix:** Implement trading metrics

- **Location:** `backend/jobs/metrics.py:1007`
  - **TODO:** Get from portfolio config
  - **Impact:** LOW - Configuration improvement
  - **Fix:** Get from portfolio config

- **Location:** `backend/jobs/backfill_rehearsal.py:298`
  - **TODO:** Insert into audit_log table (if exists)
  - **Impact:** LOW - Audit trail incomplete
  - **Fix:** Add audit logging

- **Location:** `backend/app/db/continuous_aggregate_manager.py:210`
  - **TODO:** Implement full PostgreSQL interval parsing
  - **Impact:** LOW - Feature enhancement
  - **Fix:** Implement full parsing

- **Location:** `frontend/utils.js:443`
  - **TODO:** Read from trace if data source display is needed
  - **Impact:** LOW - Feature enhancement
  - **Fix:** Implement trace reading

---

### P4 (Low) - Future Enhancement / Stub Implementation

#### 8. Stub Implementation TODOs
- **Location:** `backend/jobs/factors.py:268,283,312,326,349,377,398,420,434,498`
  - **Multiple TODOs:** Factor analysis implementation stubs
  - **Impact:** LOW - Feature not yet implemented
  - **Fix:** Implement when feature is prioritized

---

## Summary by Priority

| Priority | Count | Files |
|----------|-------|-------|
| **P1 (Critical)** | 13 | 6 files |
| **P2 (High)** | 12 | 8 files |
| **P3 (Medium)** | 17 | 12 files |
| **P4 (Low)** | 10 | 1 file |
| **Total** | 52 | 27 files |

---

## Next Steps

1. ✅ Inventory complete
2. ⏳ Fix P1 TODOs (Critical)
3. ⏳ Fix P2 TODOs (High)
4. ⏳ Fix P3 TODOs (Medium - optional)
5. ⏳ Document P4 TODOs (Future work)

---

**Status:** 🚧 IN PROGRESS  
**Last Updated:** January 15, 2025

