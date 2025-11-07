# Agent Shared Memory - DawsOS Project

## Last Updated: November 5, 2025 by Replit Agent

## Critical Fixes Applied After Remote Sync

### Context for Claude Agent

**Issue Origin**: The November 4, 2025 remote sync introduced security fixes that broke scenario analysis functionality.

### What Was Broken

1. **Scenario Analysis Service** (`backend/app/services/scenarios.py`)
   - Line 752 was hardcoding `pack_id = "PP_latest"`
   - This caused validation errors and crashes since `PP_latest` was removed as part of security fixes
   - All scenario-based risk analysis patterns were failing

2. **Outdated Documentation**
   - FinancialAnalyst agent still documented fallback to "PP_latest"
   - This was misleading developers about expected behavior

### Fixes Applied by Replit Agent

1. **Scenario Service Fix** (`backend/app/services/scenarios.py` lines 751-770)
   ```python
   # OLD (broken):
   if not pack_id:
       pack_id = "PP_latest"
   
   # NEW (fixed):
   if not pack_id:
       from app.services.pricing import get_pricing_service
       pricing_service = get_pricing_service()
       latest_pack = await pricing_service.get_latest_pack()
       if latest_pack:
           pack_id = latest_pack.id
       else:
           # Return error if no pricing pack available
   ```

2. **Documentation Update** (`backend/app/agents/financial_analyst.py` lines 302-307)
   - Removed: "Falls back to PP_latest if not specified"
   - Added: "Must be provided either directly or via context - no automatic fallback"

### Important Notes

- **Never reintroduce `PP_latest`** - It was intentionally removed as a security fix
- Always use `get_pricing_service().get_latest_pack()` for dynamic pack lookup
- Pricing pack IDs must be in format `PP_YYYY-MM-DD` or valid UUID

### Current System State

✅ All patterns working correctly:
- portfolio_overview
- portfolio_summary  
- portfolio_holdings
- portfolio_scenario_analysis

✅ Portfolio data is coherent:
- Total value: ~$687K
- Cash: $359K (52%)
- Securities: $328K (48%)
- Total contributions: $605K
- 1-year return: 9.29%

✅ Authentication working:
- Username: michael@dawsos.com
- Password: admin123

### Remaining Known Issues

1. **TWR Calculation Bug** (not fixed yet)
   - `backend/app/services/metrics.py` line 142 uses wrong denominator
   - Should divide by `v_prev` not `v_prev + cf`
   - This overstates returns when deposits occur

2. **Missing Metrics**
   - MWR/IRR function exists but not exposed in API
   - Max drawdown calculated but not returned in responses
   - Current drawdown not calculated

### Database Schema Notes

- Use `TRANSFER_IN` for deposits (not `DEPOSIT` which doesn't exist)
- Portfolio cash flows use `DEPOSIT` type (different from transactions)
- Pricing packs require explicit IDs - no automatic fallback