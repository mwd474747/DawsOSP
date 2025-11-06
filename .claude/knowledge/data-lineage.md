# Data Lineage Tracking Knowledge Base

**Purpose:** Track data flow from source → transformation → usage for audit, debugging, and impact analysis
**Last Updated:** November 5, 2025

---

## What is Data Lineage?

**Data lineage** is a record of:
- **Where data comes from** (source: API, user input, computation)
- **How data is transformed** (operations applied)
- **Where data is used** (downstream dependencies)
- **When data was created/updated** (timestamps)
- **Quality metadata** (confidence, warnings, validation results)

**Benefits:**
- **Audit trail:** Regulatory compliance, data governance
- **Debugging:** Trace errors back to source
- **Impact analysis:** What depends on this data?
- **Data quality:** Track quality metrics over time
- **Reproducibility:** Recreate computations

---

## Lineage Schema

### Database Table

```sql
CREATE TABLE data_lineage (
    lineage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Entity being tracked
    entity_type VARCHAR(50) NOT NULL,  -- 'portfolio_value', 'factor_exposure', etc.
    entity_id VARCHAR(100) NOT NULL,   -- Unique identifier for entity instance

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ,  -- NULL = still valid

    -- Source information
    source_type VARCHAR(50) NOT NULL,  -- 'external_api', 'computation', 'user_input'
    source_id VARCHAR(100) NOT NULL,   -- API endpoint, function name, user_id

    -- Transformation details
    transformation TEXT,  -- Description of transformation
    transformation_config JSONB,  -- Configuration parameters

    -- Input dependencies
    inputs JSONB,  -- References to upstream data

    -- Quality metadata
    metadata JSONB,  -- Provenance, confidence, warnings, etc.

    -- Indexes for queries
    INDEX idx_lineage_entity (entity_type, entity_id),
    INDEX idx_lineage_created (created_at DESC),
    INDEX idx_lineage_source (source_type, source_id)
);

-- Convert to hypertable for time-series queries
SELECT create_hypertable(
    'data_lineage',
    'created_at',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 month'
);
```

---

## Lineage Patterns

### Pattern 1: External API Data

**Example:** Fetching economic indicators from FRED

```python
lineage_record = {
    "entity_type": "economic_indicator",
    "entity_id": "DFII10_2025-11-05",
    "source_type": "external_api",
    "source_id": "https://api.stlouisfed.org/fred/series/observations",
    "transformation": "FRED API response → economic_indicators schema",
    "transformation_config": {
        "series_id": "DFII10",
        "observation_start": "2025-11-05",
        "observation_end": "2025-11-05",
        "units": "lin"  # Linear (no transformation)
    },
    "inputs": {
        "api_request": {
            "url": "https://api.stlouisfed.org/fred/series/observations",
            "params": {
                "series_id": "DFII10",
                "api_key": "<redacted>",
                "file_type": "json"
            },
            "response_status": 200
        }
    },
    "metadata": {
        "provenance": {
            "type": "external",
            "source": "FRED",
            "confidence": 1.0,  # Direct from source = high confidence
            "data_date": "2025-11-05",
            "fetch_timestamp": "2025-11-05T10:30:00Z"
        },
        "quality": {
            "completeness": 1.0,  # All fields present
            "validation_passed": True,
            "warnings": []
        }
    }
}
```

---

### Pattern 2: Computed Data (Factor Exposure)

**Example:** Computing factor exposure from regression

```python
lineage_record = {
    "entity_type": "factor_exposure",
    "entity_id": "portfolio_123_pack_456",
    "source_type": "computation",
    "source_id": "FactorAnalyzer.compute_factor_exposure",
    "transformation": "Regression: portfolio_returns ~ factor_returns",
    "transformation_config": {
        "model": "OLS",
        "lookback_days": 252,
        "factors": ["DFII10", "T10YIE", "BAMLC0A0CM", "DTWEXBGS", "SP500"]
    },
    "inputs": {
        "portfolio_daily_values": {
            "entity_type": "portfolio_daily_value",
            "portfolio_id": "portfolio_123",
            "date_range": ["2024-11-05", "2025-11-05"],
            "records_count": 252,
            "lineage_id": "lineage_abc123"  # Reference to upstream lineage
        },
        "economic_indicators": {
            "entity_type": "economic_indicator",
            "series_ids": ["DFII10", "T10YIE", "BAMLC0A0CM", "DTWEXBGS", "SP500"],
            "date_range": ["2024-11-05", "2025-11-05"],
            "records_count": 1260,  # 252 days × 5 indicators
            "lineage_ids": ["lineage_def456", "lineage_ghi789", ...]
        }
    },
    "metadata": {
        "provenance": {
            "type": "computed",
            "source": "factor_analysis_service",
            "confidence": 0.9,  # High confidence (good R²)
            "compute_timestamp": "2025-11-05T14:25:00Z",
            "compute_duration_sec": 2.3
        },
        "quality": {
            "r_squared": 0.85,  # Good model fit
            "data_points": 252,
            "missing_values": 0,
            "validation_passed": True,
            "warnings": []
        },
        "results": {
            "factor_betas": {
                "Real Rates": 0.52,
                "Inflation": 0.31,
                "Credit": 0.73,
                "USD": -0.15,
                "Equity": 1.18
            },
            "market_beta": 1.18,
            "portfolio_volatility": 0.15
        }
    }
}
```

---

### Pattern 3: User Input Data

**Example:** User creating a portfolio holding

```python
lineage_record = {
    "entity_type": "portfolio_lot",
    "entity_id": "lot_789",
    "source_type": "user_input",
    "source_id": "user_456",
    "transformation": "User-provided trade execution → lot record",
    "transformation_config": {
        "input_method": "web_ui",
        "page": "portfolio_holdings",
        "action": "add_position"
    },
    "inputs": {
        "user_input": {
            "portfolio_id": "portfolio_123",
            "security_id": "AAPL",
            "quantity": 100,
            "price": 175.50,
            "trade_date": "2025-11-05",
            "settlement_date": "2025-11-07"
        }
    },
    "metadata": {
        "provenance": {
            "type": "user_input",
            "source": "web_ui",
            "user_id": "user_456",
            "confidence": 1.0,  # Direct user input = trusted
            "input_timestamp": "2025-11-05T09:15:00Z"
        },
        "quality": {
            "validation_passed": True,
            "warnings": []
        },
        "audit": {
            "ip_address": "192.168.1.100",
            "session_id": "session_xyz"
        }
    }
}
```

---

## Lineage Tracking Implementation

### Lineage Tracker Class

```python
class LineageTracker:
    """Track data lineage for audit and debugging"""

    def __init__(self, db: Database):
        self.db = db

    async def record_lineage(
        self,
        entity_type: str,
        entity_id: str,
        source_type: str,
        source_id: str,
        transformation: str = None,
        transformation_config: dict = None,
        inputs: dict = None,
        metadata: dict = None,
    ) -> UUID:
        """Record lineage for a data entity"""

        lineage_record = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "source_type": source_type,
            "source_id": source_id,
            "transformation": transformation,
            "transformation_config": transformation_config or {},
            "inputs": inputs or {},
            "metadata": metadata or {},
        }

        # Insert into lineage table
        lineage_id = await self.db.insert_returning(
            "data_lineage",
            lineage_record,
            returning="lineage_id"
        )

        logger.info(
            f"Recorded lineage: {entity_type}:{entity_id} "
            f"from {source_type}:{source_id} (lineage_id={lineage_id})"
        )

        return lineage_id

    async def get_lineage(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 10
    ) -> List[dict]:
        """Get lineage history for entity"""

        query = """
            SELECT *
            FROM data_lineage
            WHERE entity_type = $1 AND entity_id = $2
            ORDER BY created_at DESC
            LIMIT $3
        """

        return await self.db.fetch(query, entity_type, entity_id, limit)

    async def get_upstream_dependencies(
        self,
        entity_type: str,
        entity_id: str
    ) -> List[dict]:
        """Get upstream data dependencies (what this depends on)"""

        lineage = await self.get_lineage(entity_type, entity_id, limit=1)
        if not lineage:
            return []

        inputs = lineage[0].get("inputs", {})
        dependencies = []

        # Extract upstream entity references
        for input_name, input_data in inputs.items():
            if "lineage_id" in input_data:
                # Single upstream dependency
                upstream = await self.db.fetchrow(
                    "SELECT * FROM data_lineage WHERE lineage_id = $1",
                    input_data["lineage_id"]
                )
                dependencies.append(upstream)

            elif "lineage_ids" in input_data:
                # Multiple upstream dependencies
                upstream_list = await self.db.fetch(
                    "SELECT * FROM data_lineage WHERE lineage_id = ANY($1)",
                    input_data["lineage_ids"]
                )
                dependencies.extend(upstream_list)

        return dependencies

    async def get_downstream_dependents(
        self,
        entity_type: str,
        entity_id: str
    ) -> List[dict]:
        """Get downstream dependents (what depends on this)"""

        # Find all lineage records that reference this entity in inputs
        query = """
            SELECT *
            FROM data_lineage
            WHERE inputs::text LIKE $1
            ORDER BY created_at DESC
        """

        search_pattern = f'%"{entity_type}:{entity_id}"%'
        return await self.db.fetch(query, search_pattern)

    async def trace_lineage_graph(
        self,
        entity_type: str,
        entity_id: str,
        max_depth: int = 5
    ) -> dict:
        """Build complete lineage graph (upstream and downstream)"""

        graph = {
            "entity": {"type": entity_type, "id": entity_id},
            "upstream": await self._trace_upstream(entity_type, entity_id, max_depth),
            "downstream": await self._trace_downstream(entity_type, entity_id, max_depth),
        }

        return graph

    async def _trace_upstream(
        self,
        entity_type: str,
        entity_id: str,
        max_depth: int,
        current_depth: int = 0
    ) -> List[dict]:
        """Recursively trace upstream dependencies"""

        if current_depth >= max_depth:
            return []

        dependencies = await self.get_upstream_dependencies(entity_type, entity_id)

        for dep in dependencies:
            dep["upstream"] = await self._trace_upstream(
                dep["entity_type"],
                dep["entity_id"],
                max_depth,
                current_depth + 1
            )

        return dependencies
```

---

## Usage Patterns

### Pattern 1: Track External Data Ingestion

```python
async def fetch_and_store_fred_data(
    series_id: str,
    start_date: date,
    end_date: date
) -> None:
    """Fetch FRED data with lineage tracking"""

    # Fetch from API
    raw_data = await fred_client.get_series(series_id, start_date, end_date)

    # Transform to internal schema
    transformed = transform_fred_data(raw_data)

    # Store in database
    for obs in transformed:
        await db.insert("economic_indicators", obs)

        # Track lineage
        await lineage_tracker.record_lineage(
            entity_type="economic_indicator",
            entity_id=f"{obs['series_id']}_{obs['asof_date']}",
            source_type="external_api",
            source_id="https://api.stlouisfed.org/fred/series/observations",
            transformation="FRED API response → economic_indicators schema",
            transformation_config={
                "series_id": series_id,
                "observation_start": str(start_date),
                "observation_end": str(end_date),
            },
            inputs={
                "api_request": {
                    "url": fred_client.base_url,
                    "params": {"series_id": series_id},
                    "response_status": 200,
                }
            },
            metadata={
                "provenance": {
                    "type": "external",
                    "source": "FRED",
                    "confidence": 1.0,
                    "data_date": str(obs["asof_date"]),
                }
            }
        )
```

### Pattern 2: Track Computation with Dependencies

```python
async def compute_factor_exposure_with_lineage(
    portfolio_id: str,
    pack_id: str,
    lookback_days: int = 252
) -> dict:
    """Compute factor exposure with full lineage tracking"""

    # Get input data
    portfolio_values = await get_portfolio_daily_values(portfolio_id, lookback_days)
    economic_data = await get_economic_indicators(FACTOR_SERIES, lookback_days)

    # Get lineage IDs for inputs
    portfolio_lineage_ids = [
        await get_lineage_id("portfolio_daily_value", f"{portfolio_id}_{v['valuation_date']}")
        for v in portfolio_values
    ]

    indicator_lineage_ids = [
        await get_lineage_id("economic_indicator", f"{i['series_id']}_{i['asof_date']}")
        for i in economic_data
    ]

    # Compute factor exposure
    result = await factor_analyzer.compute_factor_exposure(
        portfolio_id=portfolio_id,
        pack_id=pack_id,
        lookback_days=lookback_days
    )

    # Track lineage
    lineage_id = await lineage_tracker.record_lineage(
        entity_type="factor_exposure",
        entity_id=f"{portfolio_id}_{pack_id}",
        source_type="computation",
        source_id="FactorAnalyzer.compute_factor_exposure",
        transformation="Regression: portfolio_returns ~ factor_returns",
        transformation_config={
            "model": "OLS",
            "lookback_days": lookback_days,
            "factors": FACTOR_SERIES,
        },
        inputs={
            "portfolio_daily_values": {
                "portfolio_id": portfolio_id,
                "records_count": len(portfolio_values),
                "lineage_ids": portfolio_lineage_ids,
            },
            "economic_indicators": {
                "series_ids": FACTOR_SERIES,
                "records_count": len(economic_data),
                "lineage_ids": indicator_lineage_ids,
            },
        },
        metadata={
            "provenance": {
                "type": "computed",
                "source": "factor_analysis_service",
                "confidence": min(0.9, result["r_squared"]),
            },
            "quality": {
                "r_squared": result["r_squared"],
                "data_points": lookback_days,
            },
            "results": result,
        }
    )

    # Add lineage ID to result
    result["lineage_id"] = lineage_id

    return result
```

---

## Lineage Visualization

### ASCII Lineage Graph

```
Factor Exposure (portfolio_123, 2025-11-05)
├── Source: FactorAnalyzer.compute_factor_exposure
├── Confidence: 0.9
└── Upstream Dependencies:
    ├── Portfolio Daily Values (portfolio_123, 2024-11-05 to 2025-11-05)
    │   ├── Source: FinancialAnalyst.pricing_apply_pack
    │   ├── Records: 252
    │   └── Upstream Dependencies:
    │       ├── Lots (portfolio_123)
    │       │   └── Source: User Input (user_456)
    │       └── Pricing Pack (pack_456, 2025-11-05)
    │           └── Source: Bloomberg API
    └── Economic Indicators (2024-11-05 to 2025-11-05)
        ├── DFII10 (Real Rates) - 252 records
        │   └── Source: FRED API
        ├── T10YIE (Inflation) - 252 records
        │   └── Source: FRED API
        ├── BAMLC0A0CM (Credit) - 252 records
        │   └── Source: FRED API
        ├── DTWEXBGS (USD) - 252 records
        │   └── Source: FRED API
        └── SP500 (Equity) - 252 records
            └── Source: FRED API
```

---

## Impact Analysis

### Example: "What depends on FRED data?"

```python
# Find all downstream dependents of a FRED series
fred_lineage = await lineage_tracker.get_lineage(
    entity_type="economic_indicator",
    entity_id="DFII10_2025-11-05"
)

downstream = await lineage_tracker.get_downstream_dependents(
    entity_type="economic_indicator",
    entity_id="DFII10_2025-11-05"
)

print(f"Impact Analysis: DFII10_2025-11-05")
print(f"Downstream Dependents: {len(downstream)}")
for dep in downstream:
    print(f"  - {dep['entity_type']}:{dep['entity_id']}")
    print(f"    Source: {dep['source_id']}")
    print(f"    Created: {dep['created_at']}")
```

**Output:**
```
Impact Analysis: DFII10_2025-11-05
Downstream Dependents: 15
  - factor_exposure:portfolio_123_pack_456
    Source: FactorAnalyzer.compute_factor_exposure
    Created: 2025-11-05 14:25:00

  - factor_exposure:portfolio_789_pack_456
    Source: FactorAnalyzer.compute_factor_exposure
    Created: 2025-11-05 14:30:00

  ...
```

---

## Status

**Lineage Tracking Status:**
- ✅ Schema designed
- ✅ Implementation patterns defined
- ✅ Visualization approach defined
- ❌ NOT YET IMPLEMENTED (requires new feature)

**Next Steps:**
1. Create data_lineage table (migration)
2. Implement LineageTracker class
3. Add lineage tracking to all data ingestion points
4. Add lineage tracking to all computation pipelines
5. Build lineage visualization UI

**Implementation Effort:** 16-24 hours (new feature)

**Priority:** Medium (not in Phase 0-4, but valuable for debugging and audit)
