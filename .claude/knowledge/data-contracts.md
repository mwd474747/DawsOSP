# Data Contracts Knowledge Base

**Purpose:** Define expected data structures, quality requirements, and validation rules for all data flows in DawsOS
**Last Updated:** November 5, 2025

---

## What is a Data Contract?

A **data contract** is an explicit agreement about:
- **Schema:** What fields exist, what types they have
- **Constraints:** What values are valid
- **Quality:** What quality standards must be met
- **Provenance:** Where data comes from, how fresh it is

**Benefits:**
- Catch errors early (at ingestion, not computation)
- Self-documenting (schema is code)
- Type safety (prevent type errors)
- Quality enforcement (prevent bad data)

---

## Contract Schema

```python
@dataclass
class DataContract:
    """Defines expected data structure and quality"""
    name: str  # Entity name (e.g., "economic_indicator")
    description: str  # Human-readable description
    fields: List[Field]  # Schema fields
    constraints: List[Constraint]  # Validation rules
    provenance_required: bool  # Must track provenance?
    freshness_max_age: timedelta  # Maximum data age
    version: str  # Contract version (for evolution)

@dataclass
class Field:
    """Single field in data contract"""
    name: str  # Field name
    type: type  # Python type (str, int, Decimal, date, etc.)
    nullable: bool  # Can be NULL?
    description: str  # Human-readable description
    default: Any = None  # Default value if not provided

@dataclass
class Constraint:
    """Validation rule for data"""
    type: str  # Constraint type
    field: str  # Field to validate
    params: dict  # Constraint parameters
    severity: str  # "error" or "warning"
    message: str  # Error message

# Constraint types:
# - "range": {min, max} - Value must be in range
# - "enum": {values: []} - Value must be in list
# - "pattern": {regex: ""} - Value must match regex
# - "length": {min, max} - String length must be in range
# - "foreign_key": {table, column} - Value must exist in other table
# - "unique": {columns: []} - Combination must be unique
# - "not_null": {} - Value cannot be NULL
```

---

## DawsOS Data Contracts

### Contract 1: Economic Indicator

**Entity:** Economic indicator data from FRED API

```python
economic_indicator_contract = DataContract(
    name="economic_indicator",
    description="Economic indicator time series from FRED",
    version="1.0",
    fields=[
        Field(
            name="series_id",
            type=str,
            nullable=False,
            description="FRED series identifier (e.g., DFII10, T10YIE)"
        ),
        Field(
            name="asof_date",
            type=date,
            nullable=False,
            description="Observation date for indicator value"
        ),
        Field(
            name="value",
            type=Decimal,
            nullable=False,
            description="Indicator value (units vary by series)"
        ),
        Field(
            name="unit",
            type=str,
            nullable=True,
            description="Measurement unit (%, basis points, index, etc.)"
        ),
        Field(
            name="source",
            type=str,
            nullable=False,
            description="Data source (FRED, BLS, BEA, etc.)",
            default="FRED"
        ),
        Field(
            name="created_at",
            type=datetime,
            nullable=False,
            description="Timestamp when record was created",
            default=datetime.now
        ),
    ],
    constraints=[
        Constraint(
            type="enum",
            field="source",
            params={"values": ["FRED", "BLS", "BEA", "Bloomberg"]},
            severity="error",
            message="Source must be one of: FRED, BLS, BEA, Bloomberg"
        ),
        Constraint(
            type="range",
            field="value",
            params={"min": -1e10, "max": 1e10},
            severity="warning",
            message="Indicator value suspiciously large/small"
        ),
        Constraint(
            type="unique",
            field="",
            params={"columns": ["series_id", "asof_date"]},
            severity="error",
            message="Duplicate indicator record (series_id + asof_date must be unique)"
        ),
        Constraint(
            type="pattern",
            field="series_id",
            params={"regex": r"^[A-Z0-9]+$"},
            severity="error",
            message="Series ID must be alphanumeric uppercase"
        ),
    ],
    provenance_required=True,
    freshness_max_age=timedelta(days=7),
)
```

**Usage:**
```python
# Validate data before insertion
errors = economic_indicator_contract.validate(indicator_data)
if errors:
    raise ValidationError(f"Data contract violated: {errors}")

# Insert with confidence
await db.insert("economic_indicators", indicator_data)
```

---

### Contract 2: Portfolio Daily Value

**Entity:** Daily portfolio valuation (time series)

```python
portfolio_daily_value_contract = DataContract(
    name="portfolio_daily_value",
    description="Daily portfolio valuation time series",
    version="1.0",
    fields=[
        Field(
            name="portfolio_id",
            type=UUID,
            nullable=False,
            description="Portfolio identifier"
        ),
        Field(
            name="valuation_date",
            type=date,
            nullable=False,
            description="Date of valuation"
        ),
        Field(
            name="total_value",
            type=Decimal,
            nullable=False,
            description="Total market value of portfolio in base currency"
        ),
        Field(
            name="cash",
            type=Decimal,
            nullable=True,
            description="Cash balance in base currency",
            default=Decimal(0)
        ),
        Field(
            name="returns_1d",
            type=Decimal,
            nullable=True,
            description="1-day return (percentage)"
        ),
        Field(
            name="created_at",
            type=datetime,
            nullable=False,
            description="Timestamp when record was created",
            default=datetime.now
        ),
    ],
    constraints=[
        Constraint(
            type="range",
            field="total_value",
            params={"min": 0, "max": 1e12},
            severity="error",
            message="Portfolio value must be positive and < $1T"
        ),
        Constraint(
            type="range",
            field="returns_1d",
            params={"min": -0.50, "max": 0.50},
            severity="warning",
            message="Daily return >50% is suspicious"
        ),
        Constraint(
            type="foreign_key",
            field="portfolio_id",
            params={"table": "portfolios", "column": "portfolio_id"},
            severity="error",
            message="Portfolio must exist"
        ),
        Constraint(
            type="unique",
            field="",
            params={"columns": ["portfolio_id", "valuation_date"]},
            severity="error",
            message="Duplicate valuation (portfolio_id + valuation_date must be unique)"
        ),
    ],
    provenance_required=True,
    freshness_max_age=timedelta(days=1),
)
```

---

### Contract 3: Factor Exposure

**Entity:** Factor exposure computation result

```python
factor_exposure_contract = DataContract(
    name="factor_exposure",
    description="Factor exposure from regression analysis",
    version="1.0",
    fields=[
        Field(
            name="portfolio_id",
            type=UUID,
            nullable=False,
            description="Portfolio identifier"
        ),
        Field(
            name="pack_id",
            type=UUID,
            nullable=False,
            description="Pricing pack identifier"
        ),
        Field(
            name="factor_betas",
            type=dict,
            nullable=False,
            description="Factor beta coefficients {factor_name: beta_value}"
        ),
        Field(
            name="r_squared",
            type=Decimal,
            nullable=False,
            description="R-squared of regression model (0-1)"
        ),
        Field(
            name="portfolio_volatility",
            type=Decimal,
            nullable=False,
            description="Portfolio volatility (annualized)"
        ),
        Field(
            name="market_beta",
            type=Decimal,
            nullable=False,
            description="Market beta coefficient"
        ),
        Field(
            name="lookback_days",
            type=int,
            nullable=False,
            description="Number of days used for regression"
        ),
        Field(
            name="computed_at",
            type=datetime,
            nullable=False,
            description="Timestamp when factor exposure was computed",
            default=datetime.now
        ),
    ],
    constraints=[
        Constraint(
            type="range",
            field="r_squared",
            params={"min": 0.0, "max": 1.0},
            severity="error",
            message="R-squared must be between 0 and 1"
        ),
        Constraint(
            type="range",
            field="r_squared",
            params={"min": 0.5, "max": 1.0},
            severity="warning",
            message="R-squared < 0.5 indicates poor model fit"
        ),
        Constraint(
            type="range",
            field="portfolio_volatility",
            params={"min": 0.0, "max": 1.0},
            severity="warning",
            message="Volatility > 100% is suspicious"
        ),
        Constraint(
            type="range",
            field="market_beta",
            params={"min": -5.0, "max": 5.0},
            severity="warning",
            message="Market beta outside [-5, 5] is suspicious"
        ),
        Constraint(
            type="range",
            field="lookback_days",
            params={"min": 30, "max": 1000},
            severity="error",
            message="Lookback days must be between 30 and 1000"
        ),
        Constraint(
            type="foreign_key",
            field="portfolio_id",
            params={"table": "portfolios", "column": "portfolio_id"},
            severity="error",
            message="Portfolio must exist"
        ),
        Constraint(
            type="foreign_key",
            field="pack_id",
            params={"table": "pricing_packs", "column": "pack_id"},
            severity="error",
            message="Pricing pack must exist"
        ),
    ],
    provenance_required=True,
    freshness_max_age=timedelta(hours=24),
)
```

**Additional Validation:**
```python
# Validate factor_betas structure
def validate_factor_betas(factor_betas: dict) -> List[str]:
    """Validate factor_betas dictionary"""
    errors = []

    required_factors = ["Real Rates", "Inflation", "Credit", "USD", "Equity"]
    for factor in required_factors:
        if factor not in factor_betas:
            errors.append(f"Missing required factor: {factor}")

    for factor, beta in factor_betas.items():
        if not isinstance(beta, (int, float, Decimal)):
            errors.append(f"Factor {factor} beta must be numeric, got {type(beta)}")
        if abs(beta) > 10:
            errors.append(f"Factor {factor} beta {beta} suspiciously large")

    return errors
```

---

### Contract 4: Pricing Pack

**Entity:** Snapshot of security prices

```python
pricing_pack_contract = DataContract(
    name="pricing_pack",
    description="Snapshot of security prices at a point in time",
    version="1.0",
    fields=[
        Field(
            name="pack_id",
            type=UUID,
            nullable=False,
            description="Pricing pack identifier"
        ),
        Field(
            name="date",
            type=date,
            nullable=False,
            description="Date of pricing snapshot"
        ),
        Field(
            name="source",
            type=str,
            nullable=False,
            description="Data source (Bloomberg, Yahoo, etc.)"
        ),
        Field(
            name="securities_count",
            type=int,
            nullable=False,
            description="Number of securities in pack"
        ),
        Field(
            name="created_at",
            type=datetime,
            nullable=False,
            description="Timestamp when pack was created",
            default=datetime.now
        ),
    ],
    constraints=[
        Constraint(
            type="enum",
            field="source",
            params={"values": ["Bloomberg", "Yahoo", "Manual"]},
            severity="error",
            message="Source must be Bloomberg, Yahoo, or Manual"
        ),
        Constraint(
            type="range",
            field="securities_count",
            params={"min": 1, "max": 10000},
            severity="error",
            message="Pack must have 1-10000 securities"
        ),
        Constraint(
            type="unique",
            field="pack_id",
            params={},
            severity="error",
            message="Pack ID must be unique"
        ),
    ],
    provenance_required=True,
    freshness_max_age=timedelta(days=7),
)
```

---

## Contract Validation Implementation

### Validator Class

```python
class DataContractValidator:
    """Validates data against defined contracts"""

    def __init__(self, contract: DataContract):
        self.contract = contract

    def validate(self, data: dict) -> List[ValidationError]:
        """Validate data against contract"""
        errors = []

        # Check required fields
        for field in self.contract.fields:
            if not field.nullable and field.name not in data:
                errors.append(
                    ValidationError(
                        field=field.name,
                        constraint="not_null",
                        message=f"Required field {field.name} is missing",
                        severity="error"
                    )
                )

        # Check field types
        for field_name, value in data.items():
            field = self._get_field(field_name)
            if field and not isinstance(value, field.type):
                errors.append(
                    ValidationError(
                        field=field_name,
                        constraint="type",
                        message=f"Field {field_name} must be {field.type}, got {type(value)}",
                        severity="error"
                    )
                )

        # Check constraints
        for constraint in self.contract.constraints:
            constraint_errors = self._validate_constraint(data, constraint)
            errors.extend(constraint_errors)

        return errors

    def _validate_constraint(
        self,
        data: dict,
        constraint: Constraint
    ) -> List[ValidationError]:
        """Validate single constraint"""
        if constraint.type == "range":
            return self._validate_range(data, constraint)
        elif constraint.type == "enum":
            return self._validate_enum(data, constraint)
        elif constraint.type == "pattern":
            return self._validate_pattern(data, constraint)
        # ... other constraint types

    def _validate_range(
        self,
        data: dict,
        constraint: Constraint
    ) -> List[ValidationError]:
        """Validate range constraint"""
        value = data.get(constraint.field)
        if value is None:
            return []

        min_val = constraint.params.get("min")
        max_val = constraint.params.get("max")

        errors = []
        if min_val is not None and value < min_val:
            errors.append(
                ValidationError(
                    field=constraint.field,
                    constraint="range",
                    message=f"{constraint.message}: {value} < {min_val}",
                    severity=constraint.severity
                )
            )

        if max_val is not None and value > max_val:
            errors.append(
                ValidationError(
                    field=constraint.field,
                    constraint="range",
                    message=f"{constraint.message}: {value} > {max_val}",
                    severity=constraint.severity
                )
            )

        return errors
```

---

## Usage Patterns

### Pattern 1: Validate Before Insert

```python
async def insert_economic_indicator(
    db: Database,
    indicator_data: dict
) -> None:
    """Insert economic indicator with validation"""

    # Validate against contract
    validator = DataContractValidator(economic_indicator_contract)
    errors = validator.validate(indicator_data)

    # Filter errors by severity
    critical_errors = [e for e in errors if e.severity == "error"]
    warnings = [e for e in errors if e.severity == "warning"]

    # Log warnings
    for warning in warnings:
        logger.warning(f"Data quality warning: {warning.message}")

    # Raise if critical errors
    if critical_errors:
        raise ValidationError(f"Data contract violated: {critical_errors}")

    # Insert with confidence
    await db.insert("economic_indicators", indicator_data)
```

### Pattern 2: Validate API Response

```python
async def fetch_fred_data(
    series_id: str,
    start_date: date,
    end_date: date
) -> List[dict]:
    """Fetch FRED data with validation"""

    # Fetch from API
    raw_data = await fred_client.get_series(series_id, start_date, end_date)

    # Transform to internal schema
    transformed = [
        {
            "series_id": series_id,
            "asof_date": obs["date"],
            "value": Decimal(obs["value"]),
            "unit": raw_data["units"],
            "source": "FRED",
        }
        for obs in raw_data["observations"]
    ]

    # Validate each observation
    validator = DataContractValidator(economic_indicator_contract)
    validated = []

    for obs in transformed:
        errors = validator.validate(obs)
        critical_errors = [e for e in errors if e.severity == "error"]

        if critical_errors:
            logger.error(f"Skipping invalid observation: {critical_errors}")
            continue

        validated.append(obs)

    return validated
```

---

## Status

**Contract Status:**
- ✅ Schema defined for 4 key entities
- ✅ Validation logic designed
- ❌ NOT YET IMPLEMENTED (requires Phase 2 Task 2.1)

**Next Steps:**
1. Implement DataContractValidator class
2. Define contracts for all entities
3. Add validation to all data ingestion points
4. Add validation to all computation pipelines
5. Monitor validation errors/warnings

**Implementation Effort:** 8 hours (Phase 2 Task 2.1)
