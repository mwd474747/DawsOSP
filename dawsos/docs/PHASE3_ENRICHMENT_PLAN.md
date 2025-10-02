# Phase 3: Data Enrichment Implementation Plan

## Current State vs Target State

### 📊 Data Coverage Comparison

| Category | Current | Target | Improvement |
|----------|---------|--------|-------------|
| **Companies** | 30 | 500+ | 16x increase |
| **Sectors** | 11 basic | 11 detailed | Deep sector data |
| **Financial Metrics** | Formulas only | Live calculations | Real-time metrics |
| **Historical Data** | None | 5 years | Trend analysis |
| **Relationships** | ~50 edges | 500+ edges | 10x connections |
| **Economic Cycles** | Concepts | Historical data | Backtesting capable |

## Priority 1: Immediate High-Impact Enrichments

### 1. Sector Performance Database
```json
{
  "sectors": {
    "Technology": {
      "performance_by_cycle": {
        "expansion": {"avg_return": 18.5, "win_rate": 0.72},
        "peak": {"avg_return": 8.2, "win_rate": 0.58},
        "recession": {"avg_return": -12.3, "win_rate": 0.35},
        "recovery": {"avg_return": 25.8, "win_rate": 0.81}
      },
      "correlations": {
        "SPY": 0.92,
        "QQQ": 0.95,
        "interest_rates": -0.45,
        "dollar_index": -0.32
      },
      "key_drivers": [
        "innovation_cycle",
        "capital_availability",
        "consumer_spending"
      ]
    }
  }
}
```
**Files to create:**
- `storage/knowledge/sector_performance.json`
- `storage/knowledge/sector_correlations.json`

### 2. Economic Cycle Historical Data
```json
{
  "cycles": [
    {
      "phase": "expansion",
      "start": "2009-06",
      "end": "2020-02",
      "duration_months": 128,
      "characteristics": {
        "gdp_growth": 2.3,
        "unemployment": 5.0,
        "inflation": 1.8,
        "fed_funds": 1.0
      },
      "best_sectors": ["Technology", "Consumer Discretionary"],
      "worst_sectors": ["Utilities", "Consumer Staples"]
    }
  ]
}
```
**Files to create:**
- `storage/knowledge/economic_cycles.json`
- `storage/knowledge/cycle_indicators.json`

### 3. Enhanced Company Database
Expand from 30 to 500 companies with:
- Market cap tiers (mega, large, mid, small)
- Financial metrics (P/E, P/B, ROE, Debt/Equity)
- Growth metrics (Revenue growth, EPS growth)
- Dividend data (Yield, payout ratio)

## Priority 2: Relationship Mappings

### Supply Chain Relationships
```json
{
  "supply_chains": {
    "AAPL": {
      "suppliers": ["QCOM", "TSM", "SWKS", "AVGO"],
      "customers": ["consumers", "enterprise"],
      "impact_factors": {
        "chip_shortage": "high",
        "china_relations": "high",
        "consumer_spending": "high"
      }
    }
  }
}
```

### Inter-Sector Dependencies
```json
{
  "dependencies": {
    "Energy → Airlines": {
      "relationship": "input_cost",
      "correlation": -0.65,
      "lag_days": 30
    },
    "Financials → Real Estate": {
      "relationship": "lending_rates",
      "correlation": 0.72,
      "lag_days": 90
    }
  }
}
```

## Priority 3: Calculation Integration

### Connect Formulas to Live Data
1. **Valuation Calculations**
   - P/E using real EPS
   - PEG using actual growth rates
   - DCF using real cash flows

2. **Risk Calculations**
   - Beta using price history
   - Sharpe using actual returns
   - Correlation using real data

3. **Performance Metrics**
   - Actual vs expected returns
   - Sector relative performance
   - Risk-adjusted returns

## Implementation Schedule

### Week 1: Foundation
- [ ] Create sector_performance.json (Day 1-2)
- [ ] Create economic_cycles.json (Day 2-3)
- [ ] Expand company_database.json (Day 3-5)

### Week 2: Relationships
- [ ] Create supply_chain_map.json (Day 1-2)
- [ ] Create sector_dependencies.json (Day 2-3)
- [ ] Create correlation_matrices.json (Day 3-5)

### Week 3: Integration
- [ ] Update patterns to use new data (Day 1-2)
- [ ] Connect calculations to real data (Day 2-4)
- [ ] Test and validate enrichments (Day 4-5)

## File Structure

```
storage/
└── knowledge/
    ├── existing/
    │   ├── company_database.json (expand)
    │   ├── financial_formulas.json
    │   └── agent_capabilities.json
    ├── new_core/
    │   ├── sector_performance.json
    │   ├── economic_cycles.json
    │   └── sector_correlations.json
    └── new_relationships/
        ├── supply_chains.json
        ├── sector_dependencies.json
        └── correlation_matrices.json
```

## Success Criteria

### Quantitative Metrics
- ✅ 500+ companies with complete data
- ✅ All 11 sectors with performance history
- ✅ 50+ economic cycle phases mapped
- ✅ 100+ supply chain relationships
- ✅ Correlation data for top 100 symbols

### Qualitative Metrics
- ✅ Patterns can access historical performance
- ✅ Calculations use real data not mocks
- ✅ Sector rotation strategies work
- ✅ Risk assessments are accurate
- ✅ Cycle detection is reliable

## Quick Start Commands

```python
# 1. Create sector data
python3 -c "
from scripts.enrich_sectors import create_sector_database
create_sector_database()
"

# 2. Expand companies
python3 -c "
from scripts.enrich_companies import expand_to_sp500
expand_to_sp500()
"

# 3. Map relationships
python3 -c "
from scripts.map_relationships import create_all_mappings
create_all_mappings()
"

# 4. Test enrichments
python3 test_phase3_enrichments.py
```

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Data size growth | Implement lazy loading |
| API rate limits | Cache aggressively |
| Data freshness | Scheduled updates |
| Calculation accuracy | Validate against sources |
| Breaking changes | Backward compatibility |

## Next Actions

1. **Immediate**: Create sector_performance.json with historical data
2. **Today**: Design S&P 500 company data structure
3. **Tomorrow**: Implement economic cycle mappings
4. **This Week**: Complete Priority 1 enrichments
5. **Next Week**: Build relationship networks

This plan provides 10-20x more data while maintaining the simple JSON-based knowledge architecture.