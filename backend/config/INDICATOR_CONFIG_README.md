# Macro Economic Indicators Configuration System

## Overview

The JSON-based configuration system provides centralized management of macro economic indicators used for cycle detection (STDC, LTDC, Empire, Civil).

## Configuration File

**Location:** `backend/config/macro_indicators_defaults.json`

## Key Features

### 1. Structured Organization
- Indicators organized by category (Global, STDC, LTDC, Empire, Civil, Market)
- Each indicator includes comprehensive metadata
- Support for indicator aliases (e.g., "GDP_growth" → "gdp_growth")

### 2. Data Quality Tracking
- **Confidence Levels:** high, medium, low, default
- **Source Attribution:** Where each value comes from
- **Last Updated:** When the value was last verified
- **Notes:** Important context about the indicator

### 3. Validation & Ranges
- Each indicator has defined min/max ranges
- Automatic validation of indicator values
- Fallback to defaults if values are out of range

### 4. Scenario Support
Pre-configured scenarios for testing:
- `current_baseline`: Default economic conditions
- `recession_scenario`: Economic downturn
- `inflation_shock`: High inflation environment
- `debt_crisis`: Sovereign debt crisis

## Usage

### Updating Indicator Values

1. Edit `backend/config/macro_indicators_defaults.json`
2. Update the `value` field for the indicator
3. Update `last_updated` to current date
4. Change `confidence` level if appropriate
5. Add notes about the change if needed

### Adding New Indicators

```json
"new_indicator": {
  "value": 0.05,
  "unit": "decimal",
  "display_unit": "percentage",
  "range": {"min": 0.0, "max": 0.10},
  "source": "Data Source",
  "confidence": "medium",
  "last_updated": "2025-11-02",
  "notes": "Description of the indicator",
  "aliases": ["NEW_IND", "new_ind_alias"]
}
```

### Using in Code

```python
from app.services.indicator_config import IndicatorConfigManager

# Get configuration manager
config_manager = IndicatorConfigManager()

# Get indicator value
gdp_growth = config_manager.get_indicator("gdp_growth")

# Get with metadata
gdp_metadata = config_manager.get_indicator("gdp_growth", with_metadata=True)
print(f"Value: {gdp_metadata.value}")
print(f"Source: {gdp_metadata.source}")
print(f"Confidence: {gdp_metadata.confidence}")

# Apply scenario
recession_indicators = config_manager.get_scenario_indicators("recession_scenario")
```

## Data Flow

1. **Database First:** System checks database for real-time values
2. **Configuration Fallback:** Uses configured defaults if DB value missing
3. **Validation:** Ensures values are within expected ranges
4. **Scaling:** Applies proper scaling rules (percentages to decimals)
5. **Aliases:** Populates all indicator aliases for compatibility

## Scaling Rules

The configuration includes scaling transformations:
- **Percentages:** Converted to decimal form (3.8% → 0.038)
- **Raw Values:** Scaled appropriately (see `scaling_rules` in JSON)
- **Indices:** Kept as-is (VIX, PMI, etc.)

## Maintenance

### Regular Updates
- Review indicator values quarterly
- Update confidence levels based on data source reliability
- Document any manual overrides in notes

### Monitoring
- Check validation warnings in logs
- Review metadata summary for data freshness
- Track which indicators use defaults vs. real data

## Benefits

1. **No Code Changes:** Update indicators without modifying Python code
2. **Transparency:** Clear documentation of data sources and quality
3. **Flexibility:** Easy scenario testing and overrides
4. **Validation:** Automatic range checking prevents bad data
5. **Version Control:** Track changes through git history

## Related Files

- `backend/app/services/indicator_config.py` - Configuration manager
- `backend/app/services/cycles.py` - Uses configuration for cycle detection
- `backend/test_indicator_config.py` - Test script for validation