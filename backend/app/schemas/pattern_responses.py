"""
Pattern Response Schemas

Pydantic models for validating pattern execution responses.
Ensures backend responses match UI expectations (field names, types).

Created: November 4, 2025
Purpose: Phase 2 of pattern system refactoring
"""

from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Dict, Any, Optional, Union
from decimal import Decimal
from datetime import date, datetime
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class Position(BaseModel):
    """
    Standard position model.

    Matches expected fields in pattern JSON files and UI patternRegistry.
    Critical: Field names MUST match UI expectations (quantity, market_value).
    """
    security_id: UUID
    symbol: str
    name: Optional[str] = None
    quantity: Decimal = Field(..., description="Position quantity (must be positive)")
    market_value: Decimal = Field(..., description="Market value in portfolio currency")
    cost_basis: Decimal = Field(..., ge=0, description="Total cost basis")
    unrealized_pnl: Decimal = Field(..., description="Unrealized P&L (can be negative)")
    weight: Optional[Decimal] = Field(None, ge=0, le=1, description="Portfolio weight (0-1)")

    # Optional rating fields
    dividend_safety: Optional[str] = None
    moat_strength: Optional[str] = None
    resilience: Optional[str] = None

    # Optional sector/classification
    sector: Optional[str] = None
    asset_class: Optional[str] = None
    currency: Optional[str] = None

    @validator('quantity')
    def quantity_positive(cls, v):
        """Quantity must be positive for open positions."""
        if v <= 0:
            raise ValueError('quantity must be positive')
        return v

    @validator('symbol')
    def symbol_uppercase(cls, v):
        """Symbols should be uppercase."""
        return v.upper() if v else v

    class Config:
        """Pydantic config."""
        # Allow extra fields (for flexibility)
        extra = "allow"
        # Use Decimal for numeric types
        json_encoders = {
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v),
        }


class PerformanceMetrics(BaseModel):
    """Performance metrics structure."""
    twr_1y: Optional[Decimal] = Field(None, description="Time-weighted return (1 year)")
    twr_ytd: Optional[Decimal] = None
    twr_mtd: Optional[Decimal] = None
    volatility: Optional[Decimal] = Field(None, ge=0)
    sharpe_ratio: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = Field(None, le=0)

    class Config:
        extra = "allow"


class CurrencyAttribution(BaseModel):
    """Currency attribution structure."""
    local_return: Decimal
    fx_return: Decimal
    interaction: Decimal
    total_return: Optional[Decimal] = None

    class Config:
        extra = "allow"


class SectorAllocation(BaseModel):
    """Sector allocation structure."""
    sectors: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        extra = "allow"


class HistoricalNAV(BaseModel):
    """Historical NAV data structure."""
    dates: List[date] = Field(default_factory=list)
    values: List[Decimal] = Field(default_factory=list)

    @validator('values')
    def values_length_matches_dates(cls, v, values):
        """Ensure values and dates have same length."""
        dates = values.get('dates', [])
        if len(v) != len(dates):
            raise ValueError(f'values length ({len(v)}) must match dates length ({len(dates)})')
        return v

    class Config:
        extra = "allow"


class ValuedPositions(BaseModel):
    """Valued positions structure from pricing.apply_pack."""
    positions: List[Position]
    total_value: Decimal = Field(..., ge=0)
    base_currency: Optional[str] = None

    class Config:
        extra = "allow"


class PatternMetadata(BaseModel):
    """Standard pattern execution metadata."""
    pattern_id: str
    execution_time_ms: Optional[int] = None
    cached: Optional[bool] = False
    cache_hit: Optional[bool] = False
    validation_warning: Optional[str] = None

    class Config:
        extra = "allow"


class PatternTrace(BaseModel):
    """Standard pattern execution trace."""
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    duration_ms: Optional[int] = None
    errors: List[str] = Field(default_factory=list)

    class Config:
        extra = "allow"


class PortfolioOverviewResponse(BaseModel):
    """
    Response schema for portfolio_overview pattern.

    Validates the complete response structure including:
    - Performance metrics
    - Valued positions
    - Currency attribution
    - Sector allocation
    - Historical NAV
    - Metadata and trace
    """
    perf_metrics: PerformanceMetrics
    valued_positions: ValuedPositions
    currency_attr: Optional[CurrencyAttribution] = None
    sector_allocation: Optional[SectorAllocation] = None
    historical_nav: Optional[HistoricalNAV] = None

    # Standard pattern response fields
    _metadata: PatternMetadata
    _trace: Optional[PatternTrace] = None

    class Config:
        extra = "allow"


class HoldingDeepDiveResponse(BaseModel):
    """Response schema for holding_deep_dive pattern."""
    position: Position
    historical_prices: Optional[List[Dict[str, Any]]] = None
    dividend_history: Optional[List[Dict[str, Any]]] = None
    transaction_history: Optional[List[Dict[str, Any]]] = None
    ratings: Optional[Dict[str, Any]] = None

    _metadata: PatternMetadata
    _trace: Optional[PatternTrace] = None

    class Config:
        extra = "allow"


class PatternResponseValidator:
    """
    Pattern response validator.

    Validates pattern execution results against expected schemas.
    Non-blocking: logs warnings but doesn't fail execution.
    """

    # Map pattern IDs to their response schemas
    SCHEMA_MAP: Dict[str, type[BaseModel]] = {
        "portfolio_overview": PortfolioOverviewResponse,
        "holding_deep_dive": HoldingDeepDiveResponse,
        # Add more patterns as needed
    }

    @classmethod
    def validate(cls, pattern_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a pattern execution result.

        Args:
            pattern_id: Pattern identifier
            result: Pattern execution result

        Returns:
            Validated result (same as input, possibly with validation_warning)

        Note:
            This method is NON-BLOCKING. It logs validation errors but
            returns the original result to avoid breaking execution.
        """
        # Get schema for this pattern
        schema_class = cls.SCHEMA_MAP.get(pattern_id)

        if not schema_class:
            logger.debug(f"No validation schema defined for pattern: {pattern_id}")
            return result

        # Attempt validation
        try:
            # Parse and validate
            validated = schema_class(**result)
            logger.debug(f"Pattern {pattern_id} validation: PASSED")
            return result

        except Exception as e:
            # Log validation error but don't block execution
            logger.warning(
                f"Pattern {pattern_id} validation failed: {e}",
                extra={
                    "pattern_id": pattern_id,
                    "validation_error": str(e),
                }
            )

            # Add validation warning to metadata
            if "_metadata" in result:
                result["_metadata"]["validation_warning"] = str(e)
            else:
                result["_metadata"] = {"validation_warning": str(e)}

            return result

    @classmethod
    def check_deprecated_fields(cls, data: Any, path: str = "root") -> List[str]:
        """
        Recursively check for deprecated field names.

        Args:
            data: Data structure to check
            path: Current path in data structure (for error messages)

        Returns:
            List of warnings about deprecated fields found
        """
        warnings = []

        if isinstance(data, dict):
            for key, value in data.items():
                # Check for deprecated field names
                if key in ('qty', 'value') and key not in ('total_value', 'market_value'):
                    warnings.append(f"Found deprecated field '{key}' at {path}.{key}")

                # Check for old naming patterns
                if 'qty_' in key and key not in ('quantity_open', 'quantity_original'):
                    warnings.append(f"Found old naming pattern '{key}' at {path}.{key}")

                # Recurse into nested structures
                warnings.extend(cls.check_deprecated_fields(value, f"{path}.{key}"))

        elif isinstance(data, list):
            for idx, item in enumerate(data):
                warnings.extend(cls.check_deprecated_fields(item, f"{path}[{idx}]"))

        return warnings


# Example usage:
#
# from app.schemas.pattern_responses import PatternResponseValidator
#
# async def run_pattern(self, pattern_id, ctx, inputs):
#     # ... execute pattern ...
#     result = {...}
#
#     # Validate response (non-blocking)
#     validated_result = PatternResponseValidator.validate(pattern_id, result)
#
#     # Check for deprecated fields
#     warnings = PatternResponseValidator.check_deprecated_fields(validated_result)
#     if warnings:
#         logger.warning(f"Pattern {pattern_id} contains deprecated fields: {warnings}")
#
#     return validated_result
