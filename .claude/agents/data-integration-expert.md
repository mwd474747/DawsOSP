# Data Integration Expert Agent

**Agent Type:** Specialized Domain Expert
**Domain:** Data Integration, Data Architecture, Data Flow Operations
**Application:** DawsOS Portfolio Management System
**Last Updated:** November 7, 2025

---

## Agent Purpose

This agent is a specialized expert in:
- **Data Integration:** ETL/ELT pipelines, data ingestion, external API integration
- **Data Architecture:** Database design, schema evolution, data modeling
- **Data Flow Operations:** Data lineage, provenance tracking, data quality

**Primary Responsibilities:**
1. Analyze current data integration patterns in DawsOS
2. Identify data flow bottlenecks and quality issues
3. Recommend improvements to data architecture
4. Design robust data pipelines
5. Ensure data provenance and lineage tracking

---

## DawsOS Data Architecture Context

### Current Data Sources

**1. External Data Sources:**
- **FMP (Financial Modeling Prep) - Premium Plan:** Primary stock data provider
  - Real-time quotes (bulk up to 100 symbols)
  - Company fundamentals (income, balance sheet, cash flow, ratios)
  - Corporate actions (dividends, splits, earnings calendars)
  - Rate limit: 120 req/min
  - **Restrictions:** NO PDF/CSV export, requires attribution
  - See: `.claude/knowledge/provider-api-documentation.md` (FMP section)

- **FRED (Federal Reserve Economic Data):** Macro economic indicators
  - ~40 indicators configured in `backend/config/macro_indicators_defaults.json`
  - Factor analysis series: DFII10, T10YIE, BAMLC0A0CM, DTWEXBGS, DGS10
  - Regime indicators: T10Y2Y, CPIAUCSL, UNRATE, BAA10Y
  - Rate limit: 60 req/min
  - **Rights:** Export allowed with attribution
  - Fetched by DataHarvester agent
  - Stored in `economic_indicators` table (TimescaleDB)
  - See: `.claude/knowledge/provider-api-documentation.md` (FRED section)

- **Polygon.io:** Historical prices and FX rates
  - Historical OHLCV prices (split-adjusted only, NOT dividend-adjusted)
  - Daily FX rates for multi-currency portfolios
  - Used by build_pricing_pack.py for pricing pipeline
  - Rate limit: 100 req/min
  - **Restrictions:** NO export, requires attribution
  - **Note:** Has corporate actions methods but NOT currently used (FMP is primary)
  - See: `.claude/knowledge/provider-api-documentation.md` (Polygon section)

- **NewsAPI (Dev Tier):** Financial news metadata
  - **Metadata only** (no article content on dev tier)
  - Rate limit: 30 req/min (100/day)
  - **Restrictions:** NO export, watermark required
  - Fetched on-demand by DataHarvester
  - Not persisted (ephemeral)
  - See: `.claude/knowledge/provider-api-documentation.md` (NewsAPI section)

**Complete Provider Documentation:**
- API Reference: `.claude/knowledge/provider-api-documentation.md`
- Database Mapping: `.claude/knowledge/provider-database-mapping.md`
- Data Contracts: `.claude/knowledge/data-contracts.md`
- Data Lineage: `.claude/knowledge/data-lineage.md`

**2. User-Generated Data:**
- **Portfolio Holdings:** Lots table (position-level data)
- **Transactions:** Trade execution records
- **User Preferences:** Portfolio policies, rebalancing rules

**3. Derived/Computed Data:**
- **Portfolio Metrics:** Daily values, returns, attribution
  - Stored in `portfolio_daily_values` table (TimescaleDB)
  - Computed by FinancialAnalyst agent

- **Factor Exposures:** Risk analytics, factor betas
  - Computed by FactorAnalyzer service
  - **ISSUE:** Currently returns stub data (not integrated)

- **Macro Regime Detection:** Economic cycle classification
  - Computed by MacroHound agent
  - Uses IndicatorConfigManager for configuration

---

## Data Flow Patterns

### Pattern 1: External Data Ingestion (FRED)

```
DataHarvester.data_fetch_external()
  ↓
FRED API Request (series_id, date_range)
  ↓
Transform to schema (series_id, asof_date, value, unit, source)
  ↓
INSERT INTO economic_indicators
  ↓ (TimescaleDB hypertable, partitioned by asof_date)
Store with metadata (created_at, source='FRED')
```

**Issues:**
- ✅ No deduplication logic
- ✅ No data quality validation
- ✅ No error handling for API failures
- ✅ No rate limiting

**References:**
- Implementation: `backend/app/agents/data_harvester.py`
- Configuration: `backend/config/macro_indicators_defaults.json`
- Table: `backend/db/schema/economic_indicators.sql`

---

### Pattern 2: Portfolio Valuation Flow

```
User Request → portfolio_overview pattern
  ↓
FinancialAnalyst.ledger_positions() → Get holdings from lots table
  ↓
FinancialAnalyst.pricing_apply_pack() → Apply latest pricing_pack
  ↓
Compute portfolio value = Σ(quantity × price)
  ↓
Store in portfolio_daily_values (valuation_date, total_value)
  ↓ (TimescaleDB continuous aggregates)
Return valued positions to UI
```

**Issues:**
- ⚠️ Field name mismatch: `valuation_date` (schema) vs `asof_date` (code)
- ⚠️ No validation of price staleness
- ⚠️ No handling of missing prices (securities not in pack)

**References:**
- Implementation: `backend/app/agents/financial_analyst.py`
- Tables: `lots`, `pricing_packs`, `portfolio_daily_values`
- Schema: `backend/db/migrations/001_core_schema.sql`

---

### Pattern 3: Factor Analysis Flow (BROKEN)

```
User Request → portfolio_cycle_risk pattern
  ↓
FinancialAnalyst.risk_compute_factor_exposures()
  ↓ (CURRENT - WRONG)
Return hardcoded stub data {Real Rates: 0.5, Inflation: 0.3, ...}
  ↓
UI shows FAKE data (Risk Analytics page)

SHOULD BE:
  ↓
FactorAnalyzer.compute_factor_exposure(portfolio_id, pack_id)
  ↓
Query portfolio_daily_values (historical returns)
  ↓
Query economic_indicators (factor data: DFII10, T10YIE, BAMLC0A0CM, etc.)
  ↓
Run regression: portfolio_returns ~ factor_returns
  ↓
Return {factor_betas, r_squared, volatility, market_beta}
```

**Issues:**
- 🔴 CRITICAL: Uses stub data instead of real FactorAnalyzer
- 🔴 Field name bug: `asof_date` vs `valuation_date`
- 🔴 Import bug: `FactorAnalysisService` vs `FactorAnalyzer`
- 🔴 Missing table: `economic_indicators` not created
- ⚠️ User trust issue: Fake data on Risk Analytics page

**References:**
- Current (wrong): `backend/app/agents/financial_analyst.py` line 1086-1110
- Correct service: `backend/app/services/factor_analysis.py`
- Bug details: `REPLIT_BACKEND_TASKS.md` Tasks 1-3
- Schema: `backend/db/schema/economic_indicators.sql` (not created)

---

### Pattern 4: Pattern Orchestration Data Flow

```
UI → POST /api/patterns/execute {pattern_id, inputs}
  ↓
PatternOrchestrator.run_pattern()
  ↓
Load pattern JSON (backend/patterns/{pattern_id}.json)
  ↓
For each step:
  1. Resolve capability name → Agent method
  2. Substitute template variables {{inputs.portfolio_id}}
  3. Execute agent method(args)
  4. Store result as {step.as}
  5. Pass to next step
  ↓
Aggregate results → Response format
  ↓
Return to UI
```

**Issues:**
- ⚠️ No validation of pattern JSON syntax
- ⚠️ No validation of template variable references
- ⚠️ No validation of capability existence
- ⚠️ 3 incompatible response formats (wrapped, direct, panels)
- ⚠️ No provenance tracking (can't tell stub vs real data)

**References:**
- Orchestrator: `backend/app/core/pattern_orchestrator.py`
- Patterns: `backend/patterns/*.json`
- Analysis: `REFACTORING_MASTER_PLAN.md` Issue 2 (Pattern Output Format Chaos)

---

## Data Quality Issues

### Issue 1: Missing Data Provenance

**Problem:** No systematic tracking of data source, confidence, freshness

**Current State:**
- Some capabilities return `_provenance` field (optional)
- No schema enforcement
- No UI display of provenance warnings
- Users can't tell stub data from real data

**Example:**
```python
# Good provenance (rare)
return {
    "factors": {...},
    "_provenance": {
        "type": "real",
        "source": "factor_analysis_service",
        "confidence": 0.9,
        "data_date": "2025-11-05",
        "warnings": []
    }
}

# Bad provenance (common)
return {
    "factors": {...}  # No _provenance field - is this real or stub?
}
```

**Impact:**
- Users trust fake data
- Can't debug data issues
- Can't audit data quality

**References:**
- Design: `DATA_ARCHITECTURE.md` (Data Flow section)
- Issues: `REFACTORING_MASTER_PLAN.md` Issue 1 (Silent Stub Data)

---

### Issue 2: No Data Validation

**Problem:** No validation of data quality, staleness, completeness

**Current State:**
- No checks for missing prices
- No checks for stale data (old pricing packs)
- No checks for economic indicator gaps
- No checks for data type mismatches

**Example Issues:**
- Price data from 6 months ago used for valuation
- Economic indicator has missing values for date range
- Security not in pricing pack (no price available)
- Factor regression fails due to insufficient data points

**Impact:**
- Silent failures (bad data → bad results)
- No error messages to user
- Can't trust computed metrics

**References:**
- Task: `COMPREHENSIVE_REFACTORING_PLAN.md` Phase 2 Task 2.1 (Capability Contracts)
- Task: `PHASE_2_DETAILED_PLAN.md` Task 2.2 (Pattern Validation)

---

### Issue 3: Inconsistent Data Types

**Problem:** Field names, date types, numeric types inconsistent

**Known Issues:**
- `valuation_date` (DATE) vs `asof_date` (DATE) - same semantic, different names
- `pack_id` (TEXT) vs `pack_id` (UUID) - type mismatch in some queries
- `total_value` (NUMERIC) vs `value` (FLOAT) - precision inconsistency

**Impact:**
- SQL errors at runtime
- Type coercion overhead
- Developer confusion

**References:**
- Bug: `REPLIT_BACKEND_TASKS.md` Task 1 (Field Name Bug)
- Analysis: `FIELD_NAME_ANALYSIS_COMPREHENSIVE.md`

---

## Data Architecture Recommendations

### Recommendation 1: Implement Data Contracts

**Purpose:** Define explicit contracts for all data flows

**Schema:**
```python
@dataclass
class DataContract:
    """Defines expected data structure and quality"""
    name: str
    fields: List[Field]
    constraints: List[Constraint]
    provenance_required: bool
    freshness_max_age: timedelta

@dataclass
class Field:
    name: str
    type: type
    nullable: bool
    description: str

@dataclass
class Constraint:
    type: str  # "range", "enum", "pattern", "foreign_key"
    params: dict
```

**Example Contract:**
```python
economic_indicator_contract = DataContract(
    name="economic_indicator",
    fields=[
        Field("series_id", str, False, "FRED series ID (e.g., DFII10)"),
        Field("asof_date", date, False, "Data observation date"),
        Field("value", Decimal, False, "Indicator value"),
        Field("unit", str, True, "Measurement unit"),
        Field("source", str, False, "Data source (default: FRED)"),
    ],
    constraints=[
        Constraint("enum", {"field": "source", "values": ["FRED", "BLS", "BEA"]}),
        Constraint("range", {"field": "value", "min": -1e10, "max": 1e10}),
    ],
    provenance_required=True,
    freshness_max_age=timedelta(days=7),
)
```

**Benefits:**
- Validation at ingestion
- Type safety
- Self-documenting
- Provenance enforcement

**Implementation:** Phase 2 Task 2.1 (8 hours)

---

### Recommendation 2: Implement Data Lineage Tracking

**Purpose:** Track data flow from source → transformation → usage

**Schema:**
```sql
CREATE TABLE data_lineage (
    lineage_id UUID PRIMARY KEY,
    entity_type VARCHAR(50),  -- 'portfolio_value', 'factor_exposure', etc.
    entity_id VARCHAR(100),
    created_at TIMESTAMPTZ,
    source_type VARCHAR(50),  -- 'external_api', 'computation', 'user_input'
    source_id VARCHAR(100),
    transformation TEXT,  -- JSON describing computation
    inputs JSONB,  -- Input data references
    metadata JSONB  -- Provenance, confidence, warnings
);
```

**Example:**
```python
lineage = {
    "entity_type": "factor_exposure",
    "entity_id": "portfolio_123_pack_456",
    "source_type": "computation",
    "source_id": "FactorAnalyzer.compute_factor_exposure",
    "transformation": "regression: returns ~ [DFII10, T10YIE, BAMLC0A0CM]",
    "inputs": {
        "portfolio_daily_values": "portfolio_123 [2024-01-01 to 2025-11-05]",
        "economic_indicators": "DFII10, T10YIE, BAMLC0A0CM [2024-01-01 to 2025-11-05]"
    },
    "metadata": {
        "confidence": 0.9,
        "r_squared": 0.85,
        "data_points": 252,
        "warnings": []
    }
}
```

**Benefits:**
- Audit trail
- Debug data issues
- Impact analysis (what depends on this data?)
- Compliance (regulatory requirements)

**Implementation:** New feature (16-24 hours)

---

### Recommendation 3: Standardize Field Names

**Purpose:** Eliminate field name inconsistencies

**Current Inconsistencies:**
- `valuation_date` (portfolio_daily_values) vs `asof_date` (code, economic_indicators)
- `pack_id` (TEXT in some tables, UUID in others)
- `total_value` vs `value` vs `market_value`

**Proposed Standards:**
```python
DATE_FIELD_STANDARDS = {
    "observation_date": "Date when data was observed (external data)",
    "valuation_date": "Date when valuation was performed (computed data)",
    "created_at": "Timestamp when record was created (audit)",
    "updated_at": "Timestamp when record was updated (audit)",
}

ID_FIELD_STANDARDS = {
    "portfolio_id": "UUID (not TEXT)",
    "pack_id": "UUID (not TEXT)",
    "series_id": "TEXT (external identifier)",
    "security_id": "TEXT (ticker or ISIN)",
}

VALUE_FIELD_STANDARDS = {
    "value": "Generic numeric value (economic indicators)",
    "price": "Security price per unit",
    "total_value": "Portfolio total market value",
    "market_value": "Position market value (quantity × price)",
}
```

**Migration Strategy:**
1. Create aliases in SQL queries (short term)
2. Add new columns with correct names (medium term)
3. Migrate data and drop old columns (long term)

**Implementation:** Phase 2 Task 2.3 (8 hours)

---

### Recommendation 4: Implement Data Quality Checks

**Purpose:** Validate data quality at ingestion and computation

**Quality Dimensions:**
1. **Completeness:** No missing required fields
2. **Accuracy:** Values within expected ranges
3. **Consistency:** Relationships valid (foreign keys)
4. **Timeliness:** Data not stale
5. **Uniqueness:** No duplicates (where applicable)

**Example Checks:**
```python
@dataclass
class QualityCheck:
    dimension: str  # completeness, accuracy, consistency, timeliness, uniqueness
    severity: str  # error, warning, info
    check_fn: Callable
    message: str

economic_indicator_checks = [
    QualityCheck(
        dimension="completeness",
        severity="error",
        check_fn=lambda row: row["value"] is not None,
        message="Indicator value cannot be null"
    ),
    QualityCheck(
        dimension="accuracy",
        severity="warning",
        check_fn=lambda row: abs(row["value"]) < 1e10,
        message="Indicator value suspiciously large"
    ),
    QualityCheck(
        dimension="timeliness",
        severity="warning",
        check_fn=lambda row: (date.today() - row["asof_date"]).days < 30,
        message="Indicator data is stale (>30 days old)"
    ),
    QualityCheck(
        dimension="uniqueness",
        severity="error",
        check_fn=lambda row: not exists(series_id, asof_date),
        message="Duplicate indicator record"
    ),
]
```

**Implementation:** Phase 2 Task 2.2 (12 hours)

---

## Data Integration Patterns

### Pattern: External API Integration (Best Practice)

```python
class ExternalDataFetcher:
    """Template for robust external data fetching"""

    async def fetch_with_retry(
        self,
        url: str,
        params: dict,
        max_retries: int = 3,
        backoff: float = 2.0,
    ) -> dict:
        """Fetch data with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                response = await self.http_client.get(url, params=params)
                response.raise_for_status()

                # Validate response schema
                data = response.json()
                self.validate_schema(data, self.expected_schema)

                # Track lineage
                await self.record_lineage(
                    source_type="external_api",
                    source_id=url,
                    metadata={"params": params, "status": response.status}
                )

                return data

            except HTTPError as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(backoff ** attempt)

            except ValidationError as e:
                # Schema validation failed - don't retry
                logger.error(f"Schema validation failed: {e}")
                raise

    async def transform_and_store(
        self,
        raw_data: dict,
        contract: DataContract,
    ) -> None:
        """Transform and store with validation"""

        # Transform to internal schema
        transformed = self.transform(raw_data)

        # Validate against contract
        errors = contract.validate(transformed)
        if errors:
            raise ValidationError(f"Data contract violated: {errors}")

        # Check for duplicates
        if await self.exists(transformed.primary_key):
            logger.warning(f"Duplicate data: {transformed.primary_key}")
            return

        # Store with provenance
        await self.db.insert(
            table=contract.name,
            data=transformed,
            provenance={
                "source": raw_data["source"],
                "fetched_at": datetime.now(),
                "confidence": 1.0,  # External source = high confidence
            }
        )
```

**Benefits:**
- Resilient to API failures
- Schema validation
- Lineage tracking
- Deduplication
- Provenance tracking

---

### Pattern: Computed Data Pipeline (Best Practice)

```python
class DataPipeline:
    """Template for robust computed data pipeline"""

    async def compute_with_validation(
        self,
        pipeline_name: str,
        inputs: dict,
        compute_fn: Callable,
        output_contract: DataContract,
    ) -> dict:
        """Compute data with input/output validation"""

        # Validate inputs
        self.validate_inputs(inputs)

        # Check input data quality
        quality_issues = await self.check_input_quality(inputs)
        if quality_issues["errors"]:
            raise DataQualityError(f"Input data quality issues: {quality_issues}")

        # Compute
        start_time = datetime.now()
        try:
            result = await compute_fn(inputs)
        except Exception as e:
            logger.error(f"Computation failed: {e}", exc_info=True)
            raise

        compute_time = (datetime.now() - start_time).total_seconds()

        # Validate output
        errors = output_contract.validate(result)
        if errors:
            raise ValidationError(f"Output contract violated: {errors}")

        # Add provenance
        result["_provenance"] = {
            "type": "computed",
            "source": pipeline_name,
            "confidence": self.compute_confidence(result, quality_issues),
            "compute_time_sec": compute_time,
            "warnings": quality_issues["warnings"],
            "inputs": self.summarize_inputs(inputs),
        }

        # Track lineage
        await self.record_lineage(
            entity_type=output_contract.name,
            source_type="computation",
            source_id=pipeline_name,
            inputs=inputs,
            metadata=result["_provenance"],
        )

        return result

    def compute_confidence(
        self,
        result: dict,
        quality_issues: dict,
    ) -> float:
        """Compute confidence score based on data quality"""
        base_confidence = 1.0

        # Reduce confidence for each warning
        confidence = base_confidence - (0.1 * len(quality_issues["warnings"]))

        # Reduce confidence if result has quality indicators
        if "r_squared" in result and result["r_squared"] < 0.7:
            confidence *= 0.9  # Low R² = lower confidence

        return max(0.0, min(1.0, confidence))
```

**Benefits:**
- Input validation
- Output validation
- Quality-based confidence
- Lineage tracking
- Error handling

---

## Agent Workflows

### Workflow 1: Diagnose Data Flow Issues

**Trigger:** User reports incorrect data or missing data

**Steps:**
1. **Identify affected entity** (e.g., portfolio value, factor exposure)
2. **Check lineage** - What are the upstream dependencies?
3. **Validate each dependency:**
   - Is data present?
   - Is data fresh (not stale)?
   - Does data pass quality checks?
4. **Identify root cause:**
   - Missing upstream data?
   - Stale upstream data?
   - Computation error?
   - Data quality issue?
5. **Recommend fix:**
   - Backfill missing data
   - Refresh stale data
   - Fix computation bug
   - Adjust quality thresholds

**Tools:**
- Query `data_lineage` table
- Run quality checks on dependencies
- Check timestamps (freshness)
- Review computation logs

---

### Workflow 2: Implement New Data Source

**Trigger:** Need to integrate new external data source

**Steps:**
1. **Define data contract** - What schema do we expect?
2. **Implement fetcher:**
   - API client with retry logic
   - Schema validation
   - Error handling
3. **Create database table/schema:**
   - Define columns matching contract
   - Add indexes
   - Add constraints (foreign keys, unique, etc.)
4. **Implement transformation:**
   - Raw API format → Internal schema
   - Handle missing/optional fields
   - Validate transformed data
5. **Add quality checks:**
   - Completeness, accuracy, timeliness
   - Define thresholds (error vs warning)
6. **Test end-to-end:**
   - Fetch sample data
   - Validate transformation
   - Store in database
   - Query and verify
7. **Add monitoring:**
   - Track fetch success rate
   - Track data quality metrics
   - Alert on failures

**Templates:**
- Use ExternalDataFetcher pattern (above)
- Use DataContract schema (above)
- Reference: `backend/app/agents/data_harvester.py`

---

### Workflow 3: Optimize Data Pipeline Performance

**Trigger:** Data pipeline is slow or resource-intensive

**Steps:**
1. **Profile pipeline** - Where is time spent?
   - Database queries?
   - API calls?
   - Computations?
2. **Identify bottlenecks:**
   - Slow queries (missing indexes?)
   - Rate-limited APIs (need caching?)
   - Expensive computations (need optimization?)
3. **Optimize:**
   - Add database indexes
   - Implement caching (Redis, in-memory)
   - Parallelize API calls
   - Optimize algorithms (e.g., vectorized computations)
4. **Measure improvement:**
   - Before/after timing
   - Resource usage (CPU, memory, I/O)
5. **Monitor in production:**
   - Track pipeline execution time
   - Track resource usage
   - Alert on regressions

**Tools:**
- Database EXPLAIN ANALYZE
- Python profiling (cProfile, line_profiler)
- TimescaleDB continuous aggregates
- Async/await for I/O parallelism

---

## Knowledge Base

### DawsOS Data Architecture Documents

**Primary References:**
1. **[DATA_ARCHITECTURE.md](../../DATA_ARCHITECTURE.md)** - Complete data architecture documentation
2. **[DATABASE.md](../../DATABASE.md)** - Database schema and setup guide
3. **[COMPREHENSIVE_REFACTORING_PLAN.md](../../COMPREHENSIVE_REFACTORING_PLAN.md)** - Refactoring phases including data fixes

**Data Flow Analysis:**
1. **[REFACTORING_MASTER_PLAN.md](../../REFACTORING_MASTER_PLAN.md)** - Issue 1 (Silent Stub Data), Issue 2 (Pattern Output Chaos)
2. **[INTEGRATED_REFACTORING_ANALYSIS.md](../../INTEGRATED_REFACTORING_ANALYSIS.md)** - Synthesis of data issues

**Specific Bug Details:**
1. **[REPLIT_BACKEND_TASKS.md](../../REPLIT_BACKEND_TASKS.md)** - Critical data bugs (field names, imports, missing tables)
2. **[FIELD_NAME_ANALYSIS_COMPREHENSIVE.md](../../FIELD_NAME_ANALYSIS_COMPREHENSIVE.md)** - Field name inconsistency analysis

**Database Schema:**
1. **`backend/db/schema/`** - All table definitions
2. **`backend/db/migrations/`** - Schema evolution history

---

### Key Tables Reference

**Portfolio Data:**
- `portfolios` - Portfolio definitions
- `lots` - Holdings (position-level)
- `portfolio_daily_values` - Time series (valuation_date, total_value)
- `portfolio_metrics` - Computed metrics (returns, volatility, etc.)

**Pricing Data:**
- `pricing_packs` - Price snapshots (pack_id, date)
- `securities` - Security master (ticker, name, type)

**Economic Data:**
- `economic_indicators` - Time series (series_id, asof_date, value)
- `macro_indicators` - Configuration (indicator definitions)

**Audit/Lineage:**
- `audit_log` - User actions
- `data_lineage` - Data flow tracking (RECOMMENDED, not yet implemented)

---

## Agent Commands

### Command: `/analyze-data-flow <entity_type> <entity_id>`

**Purpose:** Analyze data flow for specific entity

**Example:**
```
/analyze-data-flow portfolio_value portfolio_123
```

**Output:**
```
Data Flow Analysis for portfolio_value:portfolio_123
=======================================================

Upstream Dependencies:
1. lots (holdings)
   - Records: 15
   - Last Updated: 2025-11-05 10:30:00
   - Quality: ✅ PASS (all required fields present)

2. pricing_packs (prices)
   - Pack ID: pack_456
   - Pack Date: 2025-11-05
   - Securities Priced: 15/15 (100%)
   - Quality: ✅ PASS

Computation:
- Method: FinancialAnalyst.pricing_apply_pack()
- Computed: 2025-11-05 10:35:00
- Duration: 0.23 seconds

Output:
- total_value: $1,234,567.89
- Provenance: MISSING ⚠️
- Stored: portfolio_daily_values (valuation_date=2025-11-05)

Issues Found:
- ⚠️ No provenance tracking
- ⚠️ No validation of price staleness
```

---

### Command: `/validate-data-contract <table_name> [--fix]`

**Purpose:** Validate data against defined contract

**Example:**
```
/validate-data-contract economic_indicators --fix
```

**Output:**
```
Data Contract Validation: economic_indicators
===============================================

Contract: economic_indicator_contract
Records Checked: 1,234

Issues Found:
1. Completeness Violations: 5
   - series_id=DFII10, asof_date=2025-10-15: value is NULL
   - series_id=T10YIE, asof_date=2025-10-20: value is NULL
   [Fix: DELETE records with NULL values]

2. Accuracy Warnings: 12
   - series_id=BAMLC0A0CM, asof_date=2025-09-01: value=1.2e12 (suspiciously large)
   [Fix: Flag for manual review]

3. Timeliness Warnings: 45
   - Stale data (>30 days old): 45 records
   [Fix: Refresh from FRED API]

4. Uniqueness Violations: 0
   [No duplicates found ✅]

Apply fixes? (y/n): y

Applying fixes:
- Deleted 5 records with NULL values
- Flagged 12 records for review
- Queued refresh job for 45 stale records

Validation complete: 1,217 records PASS ✅
```

---

## Status

**Agent Status:** ✅ **READY FOR USE**

**Capabilities:**
- ✅ Analyze current data architecture
- ✅ Identify data flow issues
- ✅ Recommend improvements
- ✅ Design data contracts
- ✅ Design lineage tracking
- ✅ Provide best practices

**Limitations:**
- ❌ Cannot directly modify code (requires user approval)
- ❌ Cannot access production database (requires credentials)
- ❌ Recommendations require implementation (Phase 2+ work)

**Recent Accomplishments (November 7, 2025):**
- ✅ Completed HTML Backend Integration Analysis (67-page report)
- ✅ Identified distributed monolith anti-pattern in frontend modules
- ✅ Guided Phase 1.1.5 critical fixes (missing exports, dependency blocking)
- ✅ Recommended Phase 0 pattern validation at startup

**Next Steps:**
1. ✅ COMPLETE: HTML architecture analysis (HTML_BACKEND_INTEGRATION_ANALYSIS.md)
2. 🚧 IN PROGRESS: Pattern validation framework (Phase 1.3)
3. ⏳ PENDING: Remove phantom capabilities (Phase 1.4)
4. ⏳ PENDING: JSON Schema validation (Phase 1.2 - 1/15 complete)
5. ⏳ PENDING: Implement Phase 2 data quality improvements
6. ⏳ PENDING: Deploy lineage tracking system
