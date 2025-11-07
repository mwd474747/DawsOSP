# RLS Requirement Analysis

**Date:** January 14, 2025  
**Question:** Do we need RLS at this stage of development?

---

## Current State

### ✅ RLS is Already Implemented

**Database Level:**
- Migration 005: RLS enabled on 11 tables
- RLS policies created for multi-tenant isolation
- Policies enforce: `user_id = current_setting('app.user_id')::uuid`

**Application Level:**
- `get_db_connection_with_rls(user_id)` function exists
- 42 API routes already using RLS-aware connections
- `RequestCtx` includes `user_id` field
- User authentication system in place

**Tables with RLS:**
1. `portfolios` - Base isolation
2. `lots` - Holdings
3. `transactions` - Trade history
4. `portfolio_metrics` - Performance metrics
5. `currency_attribution` - Attribution data
6. `factor_exposures` - Risk metrics
7. `alerts` - User alerts
8. `notifications` - User notifications
9. `rebalance_suggestions` - Optimization suggestions
10. `reconciliation_results` - Reconciliation data
11. `ledger_transactions` - Ledger entries

**Tables WITHOUT RLS (Global/System):**
- `pricing_packs` - Global pricing data
- `securities` - Global security master
- `fx_rates` - Global FX rates
- `macro_indicators` - Global macro data
- `rating_rubrics` - System configuration

---

## Do You Need RLS Now?

### Option 1: Keep RLS (Recommended) ✅

**Pros:**
- ✅ **Security by default** - Prevents data leaks even in development
- ✅ **Already implemented** - No additional work needed
- ✅ **Hard to add later** - Easier to have it from the start
- ✅ **Multi-tenant ready** - Can add users anytime
- ✅ **Testing isolation** - Helps catch bugs early
- ✅ **Production-ready** - No refactoring needed later

**Cons:**
- ⚠️ **Slight complexity** - Must use `get_db_connection_with_rls()` for user data
- ⚠️ **Performance overhead** - Minimal (RLS policies are fast with indexes)
- ⚠️ **Development friction** - Must set `user_id` in context

**Recommendation:** ✅ **KEEP RLS** if you plan to:
- Support multiple users (even if not now)
- Deploy to production eventually
- Have any security concerns
- Want to test multi-tenant scenarios

---

### Option 2: Disable RLS (Simpler for Single-User Development)

**Pros:**
- ✅ **Simpler code** - Can use `execute_query*` helper functions everywhere
- ✅ **Less context needed** - No need to pass `user_id` everywhere
- ✅ **Faster development** - One less thing to think about
- ✅ **Easier debugging** - No RLS context to manage

**Cons:**
- ❌ **Security risk** - No data isolation (if you add users later)
- ❌ **Refactoring needed** - Must add RLS back before production
- ❌ **Hard to test** - Can't test multi-tenant scenarios
- ❌ **Breaking change** - Must update all code when re-enabling

**Recommendation:** ⚠️ **ONLY if:**
- You're 100% certain you'll only have 1 user
- You're in very early development (MVP/prototype)
- You're willing to refactor before production

---

## Assessment: What Stage Are You At?

### If You're in Early Development (MVP/Prototype):
**Recommendation:** ⚠️ **Consider disabling RLS temporarily**

**Steps:**
1. Comment out RLS policies in migration 005
2. Use `execute_query*` helper functions everywhere
3. Remove `user_id` from `RequestCtx` (or make optional)
4. Simplify connection patterns

**When to re-enable:**
- Before adding second user
- Before production deployment
- When security becomes a concern

---

### If You're Past MVP (Beta/Production-Ready):
**Recommendation:** ✅ **KEEP RLS**

**Reasons:**
- Already implemented and working
- 42 API routes already using it correctly
- Security is important
- Multi-tenant support is valuable
- Refactoring to remove it is more work than keeping it

---

## Impact on Standardization Plan

### If You Keep RLS (Current Plan):
- **Services:** Use `execute_query*` (system-level, no RLS) ✅
- **Agents:** Use `get_db_connection_with_rls()` (user data, RLS required) ✅
- **API Routes:** Use `get_db_connection_with_rls()` (user data, RLS required) ✅
- **Jobs:** Use `execute_query*` (system-level, no RLS) ✅

**Files to Update:** 5 files (~21 usages)
**Complexity:** Medium (must understand RLS requirements)

---

### If You Disable RLS (Simplified Plan):
- **Everything:** Use `execute_query*` helper functions ✅
- **No RLS context needed** - Remove `user_id` from context
- **Simpler code** - One pattern everywhere

**Files to Update:** 5 files (~21 usages) + remove RLS from database
**Complexity:** Low (one pattern, no RLS to think about)

---

## Recommendation

### ✅ **KEEP RLS** (Recommended)

**Reasons:**
1. **Already implemented** - No additional work
2. **42 API routes already using it** - Most code is correct
3. **Security by default** - Prevents accidental data leaks
4. **Future-proof** - Ready for multi-tenant when needed
5. **Minimal overhead** - RLS policies are fast with indexes

**Standardization Plan:**
- Continue with current plan (RLS-aware for user data)
- Only ~21 usages need updating
- Most code already correct

---

### ⚠️ **DISABLE RLS** (Only if Single-User MVP)

**Only if:**
- You're in very early development
- You're 100% certain you'll only have 1 user
- You want maximum simplicity
- You're willing to refactor later

**Steps to Disable:**
1. Comment out RLS policies in migration 005
2. Update standardization plan to use helper functions everywhere
3. Remove `user_id` requirement from `RequestCtx`
4. Simplify all connection patterns

---

## Decision Matrix

| Factor | Keep RLS | Disable RLS |
|--------|----------|-------------|
| **Current Implementation** | ✅ Already done | ❌ Must remove |
| **Code Complexity** | Medium | Low |
| **Security** | ✅ High | ❌ None |
| **Multi-tenant Ready** | ✅ Yes | ❌ No |
| **Refactoring Needed** | ✅ None | ❌ Must add back later |
| **Development Speed** | Medium | Fast |
| **Production Ready** | ✅ Yes | ❌ No |

---

## My Recommendation

**✅ KEEP RLS** - The infrastructure is already in place, most code is already using it correctly, and it provides security by default. The standardization effort is small (~21 usages) and worth doing properly.

**Exception:** If you're in very early MVP stage with a single user and want maximum simplicity, you could temporarily disable RLS, but plan to re-enable it before production.

---

## Next Steps

1. **If keeping RLS:** Continue with current standardization plan
2. **If disabling RLS:** 
   - Update migration 005 to disable RLS
   - Simplify standardization plan
   - Remove `user_id` from `RequestCtx` (or make optional)

**What's your current stage?** MVP/Prototype or Beta/Production-ready?

