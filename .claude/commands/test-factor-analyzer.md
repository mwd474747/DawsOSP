---
description: Test FactorAnalyzer service with real data (Phase 0 critical decision)
---

Test FactorAnalyzer to determine if we can use it or must reimplement:

**This is a CRITICAL DECISION POINT:**
- If works: Save 40 hours (skip Phase 3 implementation)
- If needs data: Add 8 hours (populate tables)
- If broken: Proceed with library/scratch implementation (40h)

**Test Script:**
```python
import asyncio
from app.services.factor_analysis import FactorAnalyzer
from app.db.connection import get_db_pool

async def test_factor_analyzer():
    db = await get_db_pool()
    analyzer = FactorAnalyzer(db)

    # Get real portfolio_id and pack_id
    portfolio_row = await db.fetchrow("SELECT portfolio_id FROM portfolios LIMIT 1")
    pack_row = await db.fetchrow("SELECT pack_id FROM pricing_packs ORDER BY date DESC LIMIT 1")

    result = await analyzer.compute_factor_exposure(
        portfolio_id=str(portfolio_row["portfolio_id"]),
        pack_id=str(pack_row["pack_id"]),
        lookback_days=252
    )

    if "error" in result:
        print(f"⚠️  FactorAnalyzer returned error: {result['error']}")
        print("Check if portfolio_daily_values and economic_indicators tables populated")
    else:
        print(f"✅ FactorAnalyzer works! R² = {result.get('r_squared', 0):.2%}")
        print("Can use this instead of stub, save 40 hours")

asyncio.run(test_factor_analyzer())
```

**Decision Tree:**
- ✅ Works → Wire up in Phase 1, skip Phase 3 implementation
- ⚠️ Missing data → Populate tables (8h), then wire up
- ❌ Broken → Implement from scratch (40h)

See: COMPREHENSIVE_REFACTORING_PLAN.md Phase 0 Task 0.5
