# Phase 6: Fix TODOs - Priority Fixes Plan

**Date:** January 15, 2025  
**Status:** 🚧 IN PROGRESS  
**Current Step:** Starting with P1 (Critical) fixes

---

## P1 (Critical) Fixes - Starting Now

### 1. Database Schema TODOs

#### Fix 1.1: Create security_ratings table migration
**File:** `backend/app/services/alerts.py:675`  
**Priority:** P1 (Critical)  
**Impact:** Alert system cannot function without this table

**Action:** Create migration file to add security_ratings table

---

#### Fix 1.2: Create news_sentiment table migration
**File:** `backend/app/services/alerts.py:885`  
**Priority:** P1 (Critical)  
**Impact:** News-based alerts cannot function

**Action:** Create migration file to add news_sentiment table

---

#### Fix 1.3: Update RLS policies for user isolation
**File:** `backend/db/migrations/011_alert_delivery_system.sql:62,66,70`  
**Priority:** P1 (Critical)  
**Impact:** Security issue, RLS not properly configured

**Action:** Update RLS policies to use proper user isolation

---

### 2. Security TODOs

#### Fix 2.1: Extract real IP and user agent from request
**File:** `backend/app/services/reports.py:699-700`  
**Priority:** P1 (Critical)  
**Impact:** Audit trail incomplete

**Action:** Extract from request context (FastAPI request object)

---

### 3. Placeholder Values

#### Fix 3.1: Replace placeholder values in notifications.py
**File:** `backend/app/services/notifications.py:24,38`  
**Priority:** P1 (Critical)  
**Impact:** Configuration incomplete

**Action:** Use environment variables

---

#### Fix 3.2: Replace placeholder values in dlq.py
**File:** `backend/app/services/dlq.py:34`  
**Priority:** P1 (Critical)  
**Impact:** DLQ system incomplete

**Action:** Use proper values or environment variables

---

#### Fix 3.3: Replace placeholder values in alert_validators.py
**File:** `backend/app/core/alert_validators.py:228,283`  
**Priority:** P1 (Critical)  
**Impact:** Validation incomplete

**Action:** Use proper values or remove if examples

---

**Note:** The "xxx" values in `alerts.py` are in example docstrings, not actual code. These are fine as examples.

---

## Execution Plan

1. ✅ Inventory complete
2. ⏳ Fix database schema TODOs (1.1, 1.2, 1.3)
3. ⏳ Fix security TODOs (2.1)
4. ⏳ Fix placeholder values (3.1, 3.2, 3.3)
5. ⏳ Move to P2 TODOs

---

**Status:** 🚧 IN PROGRESS  
**Last Updated:** January 15, 2025

