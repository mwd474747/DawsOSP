# FRED Data Scaling Documentation

## Overview
This document describes the scaling transformations applied to raw FRED (Federal Reserve Economic Data) values to convert them into standardized decimal/percentage formats suitable for macro economic cycle analysis in DawsOS.

## Problem Statement
Raw FRED data comes in various units and formats:
- Index values (e.g., CPI at 324.368 for base 1982-84=100)
- Billions/Trillions (e.g., Federal Debt at 36,211,469 million)
- Percentages as whole numbers (e.g., 4.08 for 4.08%)
- Index levels that need YoY conversion (e.g., INDPRO at 103.9)

These raw values must be transformed to consistent decimal/ratio formats for proper cycle calculations.

## Implementation
The transformation logic is implemented in:
- `backend/app/services/fred_transformation.py` - Core transformation service
- `backend/jobs/compute_macro.py` - Integration with FRED data loader
- `combined_server.py` - Database storage with transformations

## Transformation Rules by Indicator

### Interest Rates and Yields
| Indicator | FRED Series | Raw Format | Transformation | Expected Range |
|-----------|-------------|------------|----------------|----------------|
| interest_rate | DFF | Percent (4.08) | ÷100 → 0.0408 | 0.00-0.20 |
| treasury_10y | DGS10 | Percent | ÷100 | 0.00-0.20 |
| treasury_2y | DGS2 | Percent | ÷100 | 0.00-0.20 |
| yield_curve | T10Y2Y | Percent (0.5) | ÷100 → 0.005 | -0.03-0.03 |
| fed_funds_rate | FEDFUNDS | Percent | ÷100 | 0.00-0.20 |

### Inflation and Prices
| Indicator | FRED Series | Raw Format | Transformation | Expected Range |
|-----------|-------------|------------|----------------|----------------|
| inflation | CPIAUCSL | Index (324.368) | YoY % change → 0.0324 | -0.02-0.20 |
| core_inflation | CPILFESL | Index | YoY % change | -0.02-0.20 |

### Employment
| Indicator | FRED Series | Raw Format | Transformation | Expected Range |
|-----------|-------------|------------|----------------|----------------|
| unemployment | UNRATE | Percent (4.3) | ÷100 → 0.043 | 0.02-0.15 |
| payroll_growth | PAYEMS | Level | YoY % change | -0.05-0.05 |

### Debt and Credit
| Indicator | FRED Series | Raw Format | Transformation | Expected Range |
|-----------|-------------|------------|----------------|----------------|
| debt_to_gdp | GFDEGDQ188S | Percent | ÷100 → 1.32 | 0.30-3.00 |
| federal_debt | GFDEBTN | Millions | ÷GDP → ratio | 0.30-3.00 |
| debt_service_ratio | TDSP | Percent | ÷100 → 0.1477 | 0.08-0.20 |
| credit_growth | TOTBKCR | Level | YoY % change → 0.104 | -0.10-0.30 |
| credit_spreads | BAA10Y | Percent | ÷100 → 0.0161 | 0.005-0.10 |

### Fiscal Policy
| Indicator | FRED Series | Raw Format | Transformation | Expected Range |
|-----------|-------------|------------|----------------|----------------|
| fiscal_deficit | FYFSGDA188S | % of GDP | ÷100 → -0.062 | -0.20-0.05 |
| trade_balance | NETEXP | Billions | ÷GDP → -0.032 | -0.10-0.05 |

### Production and Business
| Indicator | FRED Series | Raw Format | Transformation | Expected Range |
|-----------|-------------|------------|----------------|----------------|
| industrial_production | INDPRO | Index (103.9) | YoY % → 0.021 | -0.20-0.20 |
| manufacturing_pmi | NAPM | Index (50.7) | Keep as-is | 30-70 |
| capacity_utilization | CAPUTL | Percent | ÷100 | 0.60-0.85 |

### Growth Indicators
| Indicator | FRED Series | Raw Format | Transformation | Expected Range |
|-----------|-------------|------------|----------------|----------------|
| gdp_growth | A191RL1Q225SBEA | Percent | ÷100 → 0.038 | -0.10-0.15 |
| productivity_growth | PRS85006092 | Level | YoY % → 0.033 | -0.02-0.05 |
| retail_sales | RSXFS | Level | YoY % → 0.032 | -0.15-0.15 |
| m2_money_supply | M2SL | Level | YoY % → 0.025 | -0.10-0.25 |

### Market Indicators
| Indicator | FRED Series | Raw Format | Transformation | Expected Range |
|-----------|-------------|------------|----------------|----------------|
| vix | VIXCLS | Index | Keep as-is (16.92) | 10-80 |
| sp500 | SP500 | Index | YoY % change | -0.40-0.40 |
| consumer_confidence | UMCSENT | Index | Keep as-is (98.5) | 50-150 |
| housing_starts | HOUST | Thousands | Keep as-is (1,425,000) | 500K-2.5M |

## Transformation Types

### 1. percent_to_decimal
- **Description**: Convert percentage to decimal (5% → 0.05)
- **Formula**: value ÷ 100
- **Used for**: Interest rates, unemployment, yields

### 2. index_to_yoy_change
- **Description**: Calculate year-over-year percentage change from index
- **Formula**: (current - year_ago) ÷ year_ago
- **Used for**: CPI (inflation), Industrial Production, S&P 500
- **Requires**: Historical data (365 days back)

### 3. level_to_yoy_change
- **Description**: Calculate YoY change from level data
- **Formula**: (current - year_ago) ÷ year_ago
- **Used for**: M2 money supply, credit growth, retail sales
- **Requires**: Historical data

### 4. millions_to_gdp_ratio
- **Description**: Convert millions to ratio of GDP
- **Formula**: value ÷ GDP_in_millions
- **Used for**: Federal debt (GFDEBTN)
- **Note**: Uses approximate US GDP of $27 trillion if not provided

### 5. billions_to_gdp_ratio_signed
- **Description**: Convert billions to ratio of GDP, preserving sign
- **Formula**: value ÷ GDP_in_billions
- **Used for**: Trade balance (NETEXP)

### 6. index_keep
- **Description**: Keep index value as-is
- **Used for**: PMI, Consumer Sentiment, VIX
- **Note**: These indices already have meaningful scales

### 7. thousands_keep
- **Description**: Keep in thousands
- **Used for**: Housing starts, jobless claims
- **Note**: Absolute values are meaningful

## Testing and Validation

### Test Commands
```bash
# Test the transformation service
cd backend && python -c "
from app.services.fred_transformation import get_transformation_service
service = get_transformation_service()

# Test key transformations
print('Interest Rate:', service.transform_fred_value('DFF', 4.08, '2025-11-02'))
print('Yield Curve:', service.transform_fred_value('T10Y2Y', 0.5, '2025-11-02'))
print('Fiscal Deficit:', service.transform_fred_value('FYFSGDA188S', -6.20107, '2025-11-02'))
"

# Run the macro data loader
cd backend && python -m backend.jobs.compute_macro --asof-date 2025-11-02
```

### Validation Query
```sql
-- Check that transformed values are within expected ranges
SELECT 
    indicator_id,
    value,
    CASE 
        WHEN indicator_id = 'interest_rate' AND value BETWEEN 0.00 AND 0.20 THEN 'PASS'
        WHEN indicator_id = 'yield_curve' AND value BETWEEN -0.03 AND 0.03 THEN 'PASS'
        WHEN indicator_id = 'debt_to_gdp' AND value BETWEEN 0.30 AND 3.00 THEN 'PASS'
        WHEN indicator_id = 'inflation' AND value BETWEEN -0.02 AND 0.20 THEN 'PASS'
        WHEN indicator_id = 'unemployment' AND value BETWEEN 0.02 AND 0.15 THEN 'PASS'
        WHEN indicator_id = 'industrial_production' AND value BETWEEN -0.20 AND 0.20 THEN 'PASS'
        WHEN indicator_id = 'manufacturing_pmi' AND value BETWEEN 30 AND 70 THEN 'PASS'
        ELSE 'FAIL'
    END as validation
FROM macro_indicators
WHERE date = CURRENT_DATE;
```

## Integration Points

### 1. Data Loading (`backend/jobs/compute_macro.py`)
- Fetches raw FRED data via API
- Applies transformations before storing
- Logs transformation details

### 2. Database Storage (`combined_server.py`)
- `store_macro_indicators()` function applies basic transformations
- Maps indicator names to FRED series IDs
- Handles both raw and pre-transformed data

### 3. Cycle Calculations (`backend/app/services/cycles.py`)
- Expects transformed decimal values
- Validates indicators against expected ranges
- Logs warnings for out-of-range values

## Troubleshooting

### Common Issues
1. **Values still out of range**: Check if transformation is defined for the series
2. **YoY calculations failing**: Ensure sufficient historical data (365+ days)
3. **GDP ratios incorrect**: Verify GDP value is current and in correct units
4. **PMI values wrong**: Some PMI series are sub-indices (use NAPM for headline)

### Debug Logging
Enable debug logging to see transformation details:
```python
logger.setLevel(logging.DEBUG)
```

## Maintenance

### Adding New Indicators
1. Add transformation rule to `SERIES_TRANSFORMATIONS` dict
2. Map indicator name to FRED series in `series_mapping`
3. Define expected range in configuration
4. Test transformation with sample data
5. Update this documentation

### Updating Transformations
1. Modify transformation logic in `transform_fred_value()`
2. Test with historical data
3. Re-run macro calculations to verify
4. Document any breaking changes

## References
- FRED API Documentation: https://fred.stlouisfed.org/docs/api/
- Series Units Reference: Each FRED series page shows units
- Macro Indicators Config: `backend/config/macro_indicators_defaults.json`
- Cycle Detection Logic: `backend/app/services/cycles.py`