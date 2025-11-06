"""
DawsOS Core Type Definitions

Purpose: Canonical types for request context, capabilities, and system contracts
Updated: 2025-10-21
Priority: P0 (Critical for reproducibility and type safety)

Usage:
    from app.core.types import RequestCtx, Capability, FactorResult

    # Every request handler receives context
    async def get_portfolio_valuation(ctx: RequestCtx, portfolio_id: UUID) -> ValuationResponse:
        # ctx guarantees reproducibility: pricing_pack_id + ledger_commit_hash
        ...

    # Every capability is a pure function (no side effects)
    class ValuationCapability(Capability[ValuationRequest, ValuationResponse]):
        def execute(self, ctx: RequestCtx, request: ValuationRequest) -> ValuationResponse:
            # Pure function: same inputs → same outputs
            ...
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Protocol,
    TypeVar,
    TypedDict,
    Union,
)
from uuid import UUID

# ============================================================================
# Request Context (Reproducibility Guarantee)
# ============================================================================


@dataclass(frozen=True)
class RequestCtx:
    """
    Immutable request context guaranteeing reproducibility.

    Every result includes:
    - pricing_pack_id: Immutable price snapshot
    - ledger_commit_hash: Exact ledger state
    - trace_id: OpenTelemetry distributed tracing

    Reproducibility guarantee:
        Same ctx + same inputs → byte-for-byte identical outputs
    """

    # Core reproducibility keys
    pricing_pack_id: str
    """Immutable pricing pack ID (e.g., '20241020_v1')"""

    ledger_commit_hash: str
    """Git commit hash of ledger repo at request time"""

    # Execution metadata
    trace_id: str
    """OpenTelemetry trace ID for distributed tracing"""

    user_id: UUID
    """Authenticated user ID (for RLS policies)"""

    request_id: str
    """Unique request identifier (idempotency key)"""

    timestamp: datetime = field(default_factory=datetime.utcnow)
    """Request timestamp (UTC)"""

    # Optional context
    portfolio_id: Optional[UUID] = None
    """Portfolio context (if request is portfolio-scoped)"""

    base_currency: str = "USD"
    """Base currency for multi-currency conversions"""

    rights_profile: Optional[str] = None
    """Data rights profile for usage restrictions"""

    # Phase 2 additions (executor API requirements)
    asof_date: Optional[date] = None
    """As-of date for analysis (None = use pricing pack date)"""

    require_fresh: bool = True
    """If true, block execution when pack not fresh (default: true)"""

    def __post_init__(self):
        """Validate required fields."""
        if not self.pricing_pack_id:
            raise ValueError("pricing_pack_id is required for reproducibility")
        if not self.ledger_commit_hash:
            raise ValueError("ledger_commit_hash is required for reproducibility")
        if not self.trace_id:
            raise ValueError("trace_id is required for observability")

    def with_portfolio(self, portfolio_id: UUID) -> "RequestCtx":
        """Create new context with portfolio_id (immutable update)."""
        return RequestCtx(
            pricing_pack_id=self.pricing_pack_id,
            ledger_commit_hash=self.ledger_commit_hash,
            trace_id=self.trace_id,
            user_id=self.user_id,
            request_id=self.request_id,
            timestamp=self.timestamp,
            portfolio_id=portfolio_id,
            base_currency=self.base_currency,
            rights_profile=self.rights_profile,
            asof_date=self.asof_date,
            require_fresh=self.require_fresh,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict (for JSON responses)."""
        return {
            "pricing_pack_id": self.pricing_pack_id,
            "ledger_commit_hash": self.ledger_commit_hash,
            "trace_id": self.trace_id,
            "user_id": str(self.user_id),
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "portfolio_id": str(self.portfolio_id) if self.portfolio_id else None,
            "base_currency": self.base_currency,
            "rights_profile": self.rights_profile,
            "asof_date": str(self.asof_date) if self.asof_date else None,
            "require_fresh": self.require_fresh,
        }


# ============================================================================
# Capability Protocol (Pure Functions)
# ============================================================================

TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class Capability(Protocol, Generic[TRequest, TResponse]):
    """
    Capability protocol: pure function contract.

    Requirements:
    1. Pure function: same inputs → same outputs (no side effects)
    2. Thread-safe: can execute concurrently
    3. Testable: easy to mock and verify
    4. Composable: capabilities can call other capabilities

    Example:
        class PricingCapability(Capability[PricingRequest, PricingResponse]):
            def execute(self, ctx: RequestCtx, request: PricingRequest) -> PricingResponse:
                # Load immutable pricing pack
                pack = load_pricing_pack(ctx.pricing_pack_id)
                # Pure calculation
                prices = {s: pack.get_price(s) for s in request.symbols}
                return PricingResponse(prices=prices, ctx=ctx)
    """

    def execute(self, ctx: RequestCtx, request: TRequest) -> TResponse:
        """
        Execute capability with given context and request.

        Args:
            ctx: Immutable request context (reproducibility guarantee)
            request: Capability-specific request (validated input)

        Returns:
            Capability-specific response (includes ctx for traceability)

        Raises:
            ValueError: Invalid request
            CapabilityError: Execution failure (retryable or not)
        """
        ...


# ============================================================================
# Standard Requests/Responses
# ============================================================================


@dataclass(frozen=True)
class ValuationRequest:
    """Request for portfolio valuation."""

    portfolio_id: UUID
    asof_date: Optional[date] = None  # None = use pricing_pack date


@dataclass(frozen=True)
class ValuationResponse:
    """Portfolio valuation response."""

    portfolio_id: UUID
    asof_date: date
    total_value: Decimal
    cash_balance: Decimal
    positions: List["PositionValue"]
    ctx: RequestCtx  # Reproducibility: includes pricing_pack_id + ledger_commit_hash


@dataclass(frozen=True)
class PositionValue:
    """Single position valuation."""

    security_id: UUID
    symbol: str
    qty: Decimal
    price: Decimal  # In security's native currency
    fx_rate: Decimal  # To base currency
    value_base: Decimal  # qty × price × fx_rate


# ============================================================================
# Performance Metrics
# ============================================================================


@dataclass(frozen=True)
class TWRRequest:
    """Time-Weighted Return calculation request."""

    portfolio_id: UUID
    start_date: date
    end_date: date
    frequency: Literal["daily", "monthly", "quarterly"] = "daily"


@dataclass(frozen=True)
class TWRResponse:
    """Time-Weighted Return response."""

    portfolio_id: UUID
    start_date: date
    end_date: date
    twr: Decimal  # As decimal (0.10 = 10%)
    periods: List["PeriodReturn"]
    ctx: RequestCtx


@dataclass(frozen=True)
class PeriodReturn:
    """Single period return."""

    date: date
    value_start: Decimal
    value_end: Decimal
    cash_flows: Decimal
    return_pct: Decimal


# ============================================================================
# Attribution Analysis
# ============================================================================


@dataclass(frozen=True)
class AttributionRequest:
    """Brinson-Fachler attribution request."""

    portfolio_id: UUID
    benchmark_id: UUID  # Reference portfolio or index
    start_date: date
    end_date: date


@dataclass(frozen=True)
class AttributionResponse:
    """Attribution analysis response."""

    portfolio_id: UUID
    benchmark_id: UUID
    total_return: Decimal
    benchmark_return: Decimal
    active_return: Decimal  # total - benchmark
    allocation_effect: Decimal
    selection_effect: Decimal
    interaction_effect: Decimal
    sectors: List["SectorAttribution"]
    ctx: RequestCtx


@dataclass(frozen=True)
class SectorAttribution:
    """Sector-level attribution."""

    sector: str
    portfolio_weight: Decimal
    benchmark_weight: Decimal
    portfolio_return: Decimal
    benchmark_return: Decimal
    allocation_effect: Decimal
    selection_effect: Decimal


# ============================================================================
# Dalio Macro Framework
# ============================================================================


@dataclass(frozen=True)
class RegimeRequest:
    """Economic regime detection request."""

    asof_date: date


@dataclass(frozen=True)
class RegimeResponse:
    """Economic regime classification."""

    asof_date: date
    regime: Literal[
        "early_expansion",
        "mid_expansion",
        "late_expansion",
        "early_contraction",
        "deep_contraction",
    ]
    confidence: Decimal  # 0.0 - 1.0
    indicators: Dict[str, Decimal]  # GDP growth, unemployment, inflation, etc.
    ctx: RequestCtx


@dataclass(frozen=True)
class FactorExposureRequest:
    """Factor exposure analysis request."""

    portfolio_id: UUID
    factors: List[str]  # e.g., ["growth", "value", "momentum", "quality"]


@dataclass(frozen=True)
class FactorExposureResponse:
    """Factor exposure analysis."""

    portfolio_id: UUID
    exposures: Dict[str, Decimal]  # factor → exposure (-1.0 to 1.0)
    ctx: RequestCtx


@dataclass(frozen=True)
class ScenarioRequest:
    """Scenario analysis request (DaR - Drawdown at Risk)."""

    portfolio_id: UUID
    scenario: Literal["recession", "inflation_shock", "rate_hike", "custom"]
    custom_shocks: Optional[Dict[str, Decimal]] = None  # asset_class → return shock


@dataclass(frozen=True)
class ScenarioResponse:
    """Scenario analysis response."""

    portfolio_id: UUID
    scenario: str
    expected_return: Decimal
    expected_drawdown: Decimal  # DaR
    confidence_interval: tuple[Decimal, Decimal]  # (5th percentile, 95th percentile)
    position_impacts: List["PositionImpact"]
    ctx: RequestCtx


@dataclass(frozen=True)
class PositionImpact:
    """Position-level scenario impact."""

    security_id: UUID
    symbol: str
    current_value: Decimal
    scenario_value: Decimal
    impact: Decimal  # scenario_value - current_value


# ============================================================================
# Buffett Quality Ratings
# ============================================================================


@dataclass(frozen=True)
class QualityRatingRequest:
    """Buffett quality rating request."""

    symbols: List[str]


@dataclass(frozen=True)
class QualityRatingResponse:
    """Buffett quality ratings."""

    ratings: Dict[str, "QualityScore"]
    ctx: RequestCtx


@dataclass(frozen=True)
class QualityScore:
    """Buffett quality score (0-10 scale)."""

    symbol: str
    moat_strength: Decimal  # 0-10
    dividend_safety: Decimal  # 0-10
    resilience: Decimal  # 0-10
    overall: Decimal  # Average of above
    supporting_metrics: Dict[str, Any]  # ROE, payout ratio, debt/equity, etc.


# ============================================================================
# Pricing & Corporate Actions
# ============================================================================


@dataclass(frozen=True)
class PricingPackInfo:
    """Pricing pack metadata."""

    pricing_pack_id: str
    asof_date: date
    ledger_commit_hash: str
    is_fresh: bool
    supersedes: Optional[str]  # Previous pack ID if restatement
    created_at: datetime


@dataclass(frozen=True)
class DividendRecord:
    """Dividend corporate action."""

    security_id: UUID
    symbol: str
    ex_date: date
    pay_date: date
    amount_per_share: Decimal
    currency: str

    # ADR-specific (optional)
    gross_ccy: Optional[Decimal] = None
    withholding_ccy: Optional[Decimal] = None
    net_ccy: Optional[Decimal] = None
    pay_fx_rate_id: Optional[str] = None  # FX rate at pay_date


@dataclass(frozen=True)
class SplitRecord:
    """Stock split corporate action."""

    security_id: UUID
    symbol: str
    effective_date: date
    ratio: Decimal  # 2.0 = 2:1 split (2 new shares for 1 old)


# ============================================================================
# Alert System
# ============================================================================


@dataclass(frozen=True)
class AlertRule:
    """Alert rule definition."""

    rule_id: UUID
    portfolio_id: UUID
    condition: str  # e.g., "portfolio_value_drop_pct > 5"
    threshold: Decimal
    cooldown_minutes: int = 15
    delivery_methods: List[Literal["email", "webhook", "sms"]] = field(
        default_factory=lambda: ["email"]
    )


@dataclass(frozen=True)
class AlertEvent:
    """Triggered alert event."""

    alert_id: UUID
    rule_id: UUID
    portfolio_id: UUID
    triggered_at: datetime
    condition_value: Decimal
    message: str
    delivered: bool


# ============================================================================
# Error Types
# ============================================================================


class CapabilityError(Exception):
    """Base exception for capability execution failures."""

    def __init__(
        self,
        message: str,
        retryable: bool = False,
        ctx: Optional[RequestCtx] = None,
    ):
        super().__init__(message)
        self.retryable = retryable
        self.ctx = ctx


class PricingPackNotFoundError(CapabilityError):
    """Pricing pack does not exist."""

    def __init__(self, pricing_pack_id: str):
        super().__init__(
            f"Pricing pack not found: {pricing_pack_id}",
            retryable=False,
        )
        self.pricing_pack_id = pricing_pack_id


class PortfolioNotFoundError(CapabilityError):
    """Portfolio does not exist."""

    def __init__(self, portfolio_id: str):
        super().__init__(
            f"Portfolio not found: {portfolio_id}",
            retryable=False,
        )
        self.portfolio_id = portfolio_id


class PricingPackValidationError(CapabilityError):
    """Pricing pack ID format is invalid."""

    def __init__(self, pricing_pack_id: str, reason: str):
        super().__init__(
            f"Invalid pricing pack ID format: {pricing_pack_id}. {reason}",
            retryable=False,
        )
        self.pricing_pack_id = pricing_pack_id
        self.reason = reason


class PricingPackStaleError(CapabilityError):
    """Pricing pack is not fresh (not ready for use)."""

    def __init__(self, pricing_pack_id: str, status: str, is_fresh: bool):
        super().__init__(
            f"Pricing pack {pricing_pack_id} is not fresh (status={status}, is_fresh={is_fresh})",
            retryable=True,  # Retryable because pack might become fresh later
        )
        self.pricing_pack_id = pricing_pack_id
        self.status = status
        self.is_fresh = is_fresh


class LedgerReconciliationError(CapabilityError):
    """Ledger reconciliation failed (discrepancy > ±1bp)."""

    def __init__(self, discrepancies: List[Dict[str, Any]]):
        super().__init__(
            f"Ledger reconciliation failed: {len(discrepancies)} discrepancies",
            retryable=False,
        )
        self.discrepancies = discrepancies


class ProviderTimeoutError(CapabilityError):
    """External provider timeout (circuit breaker should engage)."""

    def __init__(self, provider: str, timeout_seconds: float):
        super().__init__(
            f"Provider timeout: {provider} ({timeout_seconds}s)",
            retryable=True,
        )
        self.provider = provider
        self.timeout_seconds = timeout_seconds


class RightsViolationError(CapabilityError):
    """Data usage rights violation."""

    def __init__(self, action: str, rights_profile: str):
        super().__init__(
            f"Rights violation: action '{action}' not permitted under '{rights_profile}'",
            retryable=False,
        )
        self.action = action
        self.rights_profile = rights_profile


# ============================================================================
# Type Aliases
# ============================================================================

# Currency codes (ISO 4217)
Currency = str  # e.g., "USD", "EUR", "GBP"

# Symbol identifiers
Symbol = str  # e.g., "AAPL", "BMW.DE", "HSBC.L"

# Pricing pack identifiers
PricingPackID = str  # e.g., "20241020_v1"

# Git commit hashes
CommitHash = str  # e.g., "a3b2c1d0"

# OpenTelemetry trace IDs
TraceID = str  # e.g., "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

# ============================================================================
# Constants
# ============================================================================

# Decimal precision (28 digits, 10 decimal places)
DECIMAL_PRECISION = Decimal("0.0000000001")

# Basis point tolerance for reconciliation (±1bp = ±0.0001)
BP_TOLERANCE = Decimal("0.0001")

# Default cooldown for alerts (15 minutes)
DEFAULT_ALERT_COOLDOWN_MINUTES = 15

# SLOs
SLO_WARM_P95_MS = 1200  # 1.2s
SLO_COLD_P95_MS = 2000  # 2.0s
SLO_ALERT_MEDIAN_MS = 60000  # 60s
SLO_PACK_BUILD_DEADLINE_HOUR = 0  # 00:15 local time
SLO_PACK_BUILD_DEADLINE_MINUTE = 15


# ============================================================================
# Validation Helpers
# ============================================================================


def validate_ctx(ctx: RequestCtx) -> None:
    """
    Validate request context meets reproducibility requirements.

    Raises:
        ValueError: If context is invalid
    """
    if not ctx.pricing_pack_id:
        raise ValueError("pricing_pack_id is required")
    if not ctx.ledger_commit_hash:
        raise ValueError("ledger_commit_hash is required")
    if not ctx.trace_id:
        raise ValueError("trace_id is required")
    if not ctx.user_id:
        raise ValueError("user_id is required")


def validate_decimal_precision(value: Decimal, name: str = "value") -> None:
    """
    Validate decimal precision (28 digits, 10 decimal places).

    Raises:
        ValueError: If precision exceeds limits
    """
    if value.as_tuple().exponent < -10:
        raise ValueError(
            f"{name} exceeds decimal precision (max 10 decimal places): {value}"
        )
    if len(value.as_tuple().digits) > 28:
        raise ValueError(f"{name} exceeds decimal precision (max 28 digits): {value}")


def validate_reconciliation_tolerance(
    ledger_value: Decimal,
    db_value: Decimal,
    tolerance: Decimal = BP_TOLERANCE,
) -> bool:
    """
    Validate values match within tolerance (±1bp).

    Returns:
        True if values match within tolerance, False otherwise
    """
    diff = abs(ledger_value - db_value)
    max_value = max(abs(ledger_value), abs(db_value))

    if max_value == 0:
        return diff == 0

    relative_diff = diff / max_value
    return relative_diff <= tolerance


# ============================================================================
# Type Guards
# ============================================================================


def is_fresh_pricing_pack(pack: PricingPackInfo) -> bool:
    """Check if pricing pack is fresh (pre-warming completed)."""
    return pack.is_fresh


def is_retryable_error(error: Exception) -> bool:
    """Check if error is retryable (circuit breaker logic)."""
    if isinstance(error, CapabilityError):
        return error.retryable
    return False


# ============================================================================
# Executor API Types (Phase 2)
# ============================================================================


@dataclass
class ExecReq:
    """Request to executor API."""

    pattern_id: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    require_fresh: bool = True
    asof_date: Optional[date] = None
    portfolio_id: Optional[UUID] = None
    security_id: Optional[UUID] = None


@dataclass
class ExecResp:
    """Response from executor API."""

    result: Any
    metadata: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)
    trace_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "result": self.result,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "trace_id": self.trace_id,
        }


class ErrorCode(str, Enum):
    """Error codes for executor API."""

    # Pack errors
    PACK_WARMING = "pricing_pack_warming"
    PACK_NOT_FOUND = "pricing_pack_not_found"
    PACK_ERROR = "pricing_pack_error"

    # Pattern errors
    PATTERN_NOT_FOUND = "pattern_not_found"
    PATTERN_INVALID = "pattern_invalid"
    PATTERN_EXECUTION_ERROR = "pattern_execution_error"

    # Agent errors
    AGENT_NOT_FOUND = "agent_not_found"
    CAPABILITY_NOT_FOUND = "capability_not_found"
    AGENT_EXECUTION_ERROR = "agent_execution_error"

    # Auth errors
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"

    # System errors
    INTERNAL_ERROR = "internal_error"
    TIMEOUT = "timeout"


@dataclass
class ExecError:
    """Error response from executor API."""

    code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error": self.code.value,
            "message": self.message,
            "details": self.details or {},
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
        }


class PackStatus(str, Enum):
    """Pricing pack status."""

    WARMING = "warming"  # Pack being built/pre-warmed
    FRESH = "fresh"  # Pack ready for use
    ERROR = "error"  # Pack build/reconciliation failed
    STALE = "stale"  # Pack superseded by newer pack


@dataclass
class PackHealth:
    """Pricing pack health status."""

    status: PackStatus
    pack_id: str
    asof_date: date
    is_fresh: bool
    prewarm_done: bool
    reconciliation_passed: bool
    updated_at: datetime
    error_message: Optional[str] = None
    estimated_ready: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "pack_id": self.pack_id,
            "asof_date": str(self.asof_date),
            "is_fresh": self.is_fresh,
            "prewarm_done": self.prewarm_done,
            "reconciliation_passed": self.reconciliation_passed,
            "updated_at": self.updated_at.isoformat(),
            "error_message": self.error_message,
            "estimated_ready": self.estimated_ready.isoformat() if self.estimated_ready else None,
        }


@dataclass
class PatternStep:
    """Single step in pattern execution."""

    id: str
    capability: str
    agent: str
    inputs: Dict[str, Any]
    outputs: List[str]
    condition: Optional[str] = None


@dataclass
class Pattern:
    """Pattern definition."""

    id: str
    version: str
    name: str
    description: str
    steps: List[PatternStep]
    inputs_schema: Optional[Dict[str, Any]] = None
    outputs_schema: Optional[Dict[str, Any]] = None


@dataclass
class CapabilityResult:
    """Result from capability execution."""

    data: Any
    metadata: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)
    trace_id: Optional[str] = None


@dataclass
class AgentCapability:
    """Agent capability definition."""

    capability_id: str
    agent_name: str
    description: str
    inputs_schema: Optional[Dict[str, Any]] = None
    outputs_schema: Optional[Dict[str, Any]] = None


@dataclass
class ExecutionTrace:
    """Execution trace for observability."""

    trace_id: str
    request_id: str
    pattern_id: str
    user_id: UUID
    pricing_pack_id: str
    ledger_commit_hash: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "pattern_id": self.pattern_id,
            "user_id": str(self.user_id),
            "pricing_pack_id": self.pricing_pack_id,
            "ledger_commit_hash": self.ledger_commit_hash,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "steps": self.steps,
            "error": self.error,
        }


# ============================================================================
# Example Usage (Doctest)
# ============================================================================

if __name__ == "__main__":
    import doctest
    from uuid import uuid4

    # Example: Create request context
    ctx = RequestCtx(
        pricing_pack_id="20241020_v1",
        ledger_commit_hash="a3b2c1d0",
        trace_id="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        user_id=uuid4(),
        request_id="req_123",
        portfolio_id=uuid4(),
    )

    print("RequestCtx created:", ctx)
    print("RequestCtx as dict:", ctx.to_dict())

    # Example: Validate decimal precision
    validate_decimal_precision(Decimal("123.4567890123"), "test_value")
    print("Decimal precision validated")

    # Example: Validate reconciliation tolerance
    ledger = Decimal("100.0000")
    db = Decimal("100.0001")
    matches = validate_reconciliation_tolerance(ledger, db)
    print(f"Reconciliation match (±1bp): {matches}")

    doctest.testmod()
