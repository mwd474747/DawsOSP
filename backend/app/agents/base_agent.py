"""
DawsOS Base Agent

Purpose: Abstract base class for all capability-providing agents
Updated: 2025-11-02

Agent Contract:
    1. Declare capabilities via get_capabilities()
    2. Implement capability methods (e.g., ledger_positions for "ledger.positions")
    3. Return results with __metadata__ for traceability
    4. Pure functions: same ctx + inputs → same outputs

Usage:
    class FinancialAnalyst(BaseAgent):
        def get_capabilities(self) -> list[str]:
            return ["ledger.positions", "pricing.apply_pack"]

        async def ledger_positions(self, ctx, state, portfolio_id: str):
            # Implementation
            return result

    agent = FinancialAnalyst("financial_analyst", services)
    runtime.register_agent(agent)
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from app.core.types import (
    RequestCtx,
    PricingPackValidationError,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Agent Metadata
# ============================================================================


@dataclass
class AgentMetadata:
    """
    Metadata attached to capability results.

    Used for tracing, staleness tracking, and reproducibility.
    """

    agent_name: str
    """Agent that produced this result"""

    source: Optional[str] = None
    """Data source (e.g., "ledger", "pricing_pack:20241020_v1", "fmp_api")"""

    asof: Optional[Any] = None
    """As-of date/time for staleness tracking"""

    ttl: Optional[int] = None
    """Time-to-live in seconds (for caching)"""

    confidence: Optional[float] = None
    """Confidence score 0.0-1.0 (for ML/AI results)"""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "agent_name": self.agent_name,
            "source": self.source,
            "asof": str(self.asof) if self.asof else None,
            "ttl": self.ttl,
            "confidence": self.confidence,
        }


# ============================================================================
# Base Agent
# ============================================================================


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    Agents are capability providers that implement specific business logic.
    Each agent declares its capabilities and provides implementations.

    Contract:
        1. Pure functions: deterministic, no side effects
        2. Thread-safe: can execute concurrently
        3. Metadata: attach AgentMetadata to results
        4. Naming: capability "foo.bar" → method foo_bar(ctx, state, **kwargs)
    """

    # Cache TTL constants (in seconds)
    CACHE_TTL_DAY = 86400
    CACHE_TTL_HOUR = 3600
    CACHE_TTL_30MIN = 1800
    CACHE_TTL_5MIN = 300
    CACHE_TTL_NONE = 0

    def __init__(self, name: str, services: Dict[str, Any]):
        """
        Initialize agent.

        Args:
            name: Agent identifier (e.g., "financial_analyst")
            services: Dependency injection dict (db, redis, API clients)
        """
        self.name = name
        self.services = services
        logger.info(f"Initialized agent: {name}")

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of capabilities this agent provides.

        Capabilities use dot notation: "category.operation"

        Examples:
            - "ledger.positions"
            - "pricing.apply_pack"
            - "metrics.compute_twr"
            - "charts.overview"

        Returns:
            List of capability names
        """
        pass

    async def execute(
        self,
        capability: str,
        ctx: RequestCtx,
        state: Dict[str, Any],
        **kwargs,
    ) -> Any:
        """
        Execute a capability with given context and arguments.

        This is the main entry point called by AgentRuntime. It routes
        the capability name to the appropriate method and attaches metadata.

        Args:
            capability: Capability name (e.g., "ledger.positions")
            ctx: Immutable request context
            state: Current pattern execution state
            **kwargs: Capability-specific arguments

        Returns:
            Result with __metadata__ attribute

        Raises:
            ValueError: If capability not supported by this agent
            Exception: If capability execution fails
        """
        # Convert capability name to method name
        # "ledger.positions" → "ledger_positions"
        method_name = capability.replace(".", "_")

        if not hasattr(self, method_name):
            raise ValueError(
                f"Agent {self.name} does not support capability {capability}"
            )

        logger.debug(f"Executing {capability} via {self.name}.{method_name}")

        # Execute capability method
        method = getattr(self, method_name)
        result = await method(ctx, state, **kwargs)

        # Attach metadata if not already present
        if not hasattr(result, "__metadata__") and not isinstance(result, dict):
            try:
                result.__metadata__ = AgentMetadata(agent_name=self.name)
            except (AttributeError, TypeError):
                # Can't set attribute - result probably already has metadata embedded
                pass

        return result

    def _create_metadata(
        self,
        source: Optional[str] = None,
        asof: Optional[Any] = None,
        ttl: Optional[int] = None,
        confidence: Optional[float] = None,
    ) -> AgentMetadata:
        """
        Helper to create metadata for results.

        Args:
            source: Data source identifier
            asof: As-of date/time
            ttl: Cache TTL in seconds
            confidence: Confidence score 0.0-1.0

        Returns:
            AgentMetadata instance
        """
        return AgentMetadata(
            agent_name=self.name,
            source=source,
            asof=asof,
            ttl=ttl,
            confidence=confidence,
        )

    def _attach_metadata(self, result: Any, metadata: AgentMetadata) -> Any:
        """
        Attach metadata to result.

        Args:
            result: Result object (list, dict, dataclass, etc.)
            metadata: Metadata to attach

        Returns:
            Result with metadata embedded (for dicts) or as attribute (for objects)
        """
        # For dicts, add metadata as a key instead of attribute
        if isinstance(result, dict):
            return {
                **result,
                "_metadata": metadata.to_dict()
            }

        # For objects with __dict__, try setting attribute
        try:
            result.__metadata__ = metadata
        except (AttributeError, TypeError):
            # Can't set attribute - wrap in dict instead
            return {
                "value": result,
                "_metadata": metadata.to_dict()
            }

        return result

    def _resolve_asof_date(self, ctx: RequestCtx) -> date:
        """
        Resolve asof_date from context with fallback to today.

        Args:
            ctx: Request context

        Returns:
            As-of date from context or today if not specified
        """
        return ctx.asof_date or date.today()

    def _to_uuid(self, value: Optional[str], param_name: str) -> Optional[UUID]:
        """
        Convert string to UUID with validation.

        Args:
            value: String value to convert to UUID
            param_name: Parameter name for error messages

        Returns:
            UUID object or None if value is empty/None

        Raises:
            ValueError: If string is not a valid UUID format
        """
        if not value:
            return None
        try:
            return UUID(value)
        except ValueError as e:
            raise ValueError(f"Invalid {param_name} format: {value}") from e

    def _resolve_portfolio_id(
        self,
        portfolio_id: Optional[str],
        ctx: RequestCtx,
        capability_name: str
    ) -> UUID:
        """
        Resolve and validate portfolio_id from parameter or context.

        Args:
            portfolio_id: Portfolio ID parameter (may be None)
            ctx: Request context containing fallback portfolio_id
            capability_name: Capability name for error messages

        Returns:
            Validated UUID of the portfolio

        Raises:
            ValueError: If portfolio_id cannot be resolved or is invalid
        """
        if not portfolio_id:
            portfolio_id = str(ctx.portfolio_id) if ctx.portfolio_id else None
        if not portfolio_id:
            raise ValueError(f"portfolio_id required for {capability_name}")

        return self._to_uuid(portfolio_id, "portfolio_id")

    def _require_pricing_pack_id(self, ctx: RequestCtx, capability_name: str) -> str:
        """
        Get pricing_pack_id from context (SACRED - required for reproducibility).

        This pattern is used for optimizer capabilities where pricing_pack_id
        is SACRED and must be explicitly provided in the context for reproducibility.

        Args:
            ctx: Request context
            capability_name: Name of capability requiring pricing_pack_id (for error message)

        Returns:
            Pricing pack ID from context

        Raises:
            ValueError: If pricing_pack_id is not in context
        """
        if not ctx.pricing_pack_id:
            raise ValueError(f"pricing_pack_id required in context for {capability_name}")
        return ctx.pricing_pack_id

    def _resolve_pricing_pack_id(
        self,
        pack_id: Optional[str],
        ctx: RequestCtx,
        default: Optional[str] = None
    ) -> str:
        """
        Resolve pricing_pack_id with fallback chain.

        This pattern is used for non-optimizer capabilities that can fallback
        to a default pricing pack if not explicitly provided.

        Args:
            pack_id: Explicit pricing pack ID (highest priority)
            ctx: Request context (fallback to ctx.pricing_pack_id)
            default: Default value if neither pack_id nor ctx.pricing_pack_id provided

        Returns:
            Resolved pricing pack ID (pack_id > ctx.pricing_pack_id > default)

        Raises:
            PricingPackValidationError: If pricing_pack_id is required but not provided
            PricingPackValidationError: If pricing_pack_id format is invalid
        """
        from app.services.pricing import validate_pack_id
        
        # Resolve from multiple sources (no fallback to "PP_latest")
        resolved = pack_id or ctx.pricing_pack_id or default
        
        if not resolved:
            raise PricingPackValidationError(
                pricing_pack_id="",
                reason="pricing_pack_id is required but not provided. "
                       "Must be set in request context (ctx.pricing_pack_id) or provided as parameter. "
                       "Use get_pricing_service().get_latest_pack() to fetch current pack."
            )
        
        # Validate format using shared validation function
        validate_pack_id(resolved)
        
        return resolved

    def _extract_ratings_from_state(
        self,
        state: Dict[str, Any],
        ratings: Optional[Dict[str, float]] = None
    ) -> Optional[Dict[str, float]]:
        """Extract ratings dict from state if not provided.

        Handles two modes:
        1. Portfolio Ratings Mode: ratings_result["positions"] - Array of position objects
        2. Single Security Ratings Mode: ratings_result["overall_rating"] - Single rating value

        Note:
            - Portfolio mode: Extracts {symbol: rating} from positions array
            - Single mode: Converts overall_rating (0-100) to 0-10 scale (divides by 10)
        """
        if ratings:
            return ratings

        if not state.get("ratings"):
            return None

        ratings_result = state["ratings"]

        # Portfolio ratings mode
        if isinstance(ratings_result, dict) and "positions" in ratings_result:
            return {
                pos["symbol"]: pos.get("rating", 0.0)
                for pos in ratings_result["positions"]
                if pos.get("rating") is not None
            }

        # Single security ratings mode
        elif isinstance(ratings_result, dict) and "overall_rating" in ratings_result:
            symbol = ratings_result.get("symbol")
            if symbol:
                # Convert 0-100 scale to 0-10 scale
                return {symbol: float(ratings_result["overall_rating"]) / 10.0}

        return None

    def _merge_policies_and_constraints(
        self,
        policies: Optional[Union[Dict, List]],
        constraints: Optional[Dict],
        default_policy: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Merge policies and constraints into unified policy dict.

        Handles multiple input formats:
        - policies as dict: Use directly
        - policies as list: Convert list of {type, value} to dict
        - constraints as dict: Merge constraint keys (max_turnover_pct, etc.)
        - default_policy: Apply if no policies provided

        Args:
            policies: Policy dict or list of policy objects
            constraints: Constraints dict (max_turnover_pct, max_te_pct, min_lot_value)
            default_policy: Default policy to use if no policies provided

        Returns:
            Merged policy dict with all constraints applied
        """
        from typing import Union
        
        merged_policy = {}

        # Handle policies
        if policies:
            if isinstance(policies, list):
                # Convert list of policies to dict format
                for policy in policies:
                    if isinstance(policy, dict) and 'type' in policy:
                        policy_type = policy['type']
                        value = policy.get('value', 0.0)

                        if policy_type == 'min_quality_score':
                            merged_policy['min_quality_score'] = value
                        elif policy_type == 'max_single_position':
                            merged_policy['max_single_position_pct'] = value
                        elif policy_type == 'max_sector':
                            merged_policy['max_sector_pct'] = value
                        elif policy_type == 'target_allocation':
                            category = policy.get('category', '')
                            merged_policy[f'target_{category}'] = value
            else:
                # Use policies as base if it's a dict
                merged_policy = policies.copy() if isinstance(policies, dict) else {}

        # Merge constraints if provided
        if constraints and isinstance(constraints, dict):
            if 'max_turnover_pct' in constraints:
                merged_policy['max_turnover_pct'] = constraints['max_turnover_pct']
            if 'max_te_pct' in constraints:
                merged_policy['max_tracking_error_pct'] = constraints['max_te_pct']
            if 'min_lot_value' in constraints:
                merged_policy['min_lot_value'] = constraints['min_lot_value']

        # Apply default policy if provided and no policies merged
        if not merged_policy and default_policy:
            merged_policy = default_policy.copy()

        # Apply standard defaults if still empty
        if not merged_policy:
            merged_policy = {
                "min_quality_score": 0.0,
                "max_single_position_pct": 20.0,
                "max_sector_pct": 30.0,
                "max_turnover_pct": 20.0,
                "max_tracking_error_pct": 3.0,
                "method": "mean_variance",
            }

        return merged_policy

    def _create_error_result(
        self,
        error_message: str,
        ctx: RequestCtx,
        source: Optional[str] = None,
        additional_fields: Optional[Dict[str, Any]] = None,
        include_provenance: bool = True,
    ) -> Dict[str, Any]:
        """
        Create standardized error result dict.

        This helper standardizes error result creation across all agents,
        ensuring consistent error format with metadata and provenance.

        Args:
            error_message: Error message string
            ctx: Request context
            source: Source identifier (e.g., "factor_analysis_service")
            additional_fields: Additional fields to include in error result
            include_provenance: Whether to include _provenance field

        Returns:
            Error result dict with error message and metadata
        """
        error_result = {
            "error": error_message,
        }
        
        if additional_fields:
            error_result.update(additional_fields)
        
        if include_provenance:
            error_result["_provenance"] = {
                "type": "error",
                "source": source or f"{self.name}_service",
                "error": error_message,
            }
        
        # Attach metadata
        metadata = self._create_metadata(
            source=f"{source or self.name}:error",
            asof=self._resolve_asof_date(ctx),
            ttl=self.CACHE_TTL_NONE,  # Don't cache errors
        )
        
        return self._attach_metadata(error_result, metadata)


# ============================================================================
# Result Wrapper (for primitives)
# ============================================================================


class ResultWrapper:
    """
    Wrapper for primitive results that can't have attributes attached.

    Used when a capability returns int, float, str, etc. instead of
    a dict or dataclass.
    """

    def __init__(self, value: Any, metadata: AgentMetadata):
        self.value = value
        self.__metadata__ = metadata

    def __repr__(self):
        return f"ResultWrapper({self.value}, metadata={self.__metadata__})"

    def __str__(self):
        return str(self.value)


# ============================================================================
# Cache Decorator
# ============================================================================


def cache_capability(ttl: int = 300):
    """
    Decorator to cache capability results in Redis.

    Args:
        ttl: Time-to-live in seconds (default 5 minutes)

    Usage:
        @cache_capability(ttl=600)
        async def metrics_compute_twr(self, ctx, state, positions, pack_id):
            # Expensive calculation
            return result
    """
    def decorator(func):
        async def wrapper(self, ctx, state, **kwargs):
            # NOTE: Redis caching can be implemented here when Redis is available in services dict
            # For now, caching is handled at the pattern orchestrator level
            return await func(self, ctx, state, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# Example Agent (for testing)
# ============================================================================


class ExampleAgent(BaseAgent):
    """
    Example agent for testing purposes.

    Provides simple echo capabilities.
    """

    def get_capabilities(self) -> List[str]:
        return ["example.echo", "example.double"]

    async def example_echo(self, ctx: RequestCtx, state: Dict, message: str) -> Dict:
        """Echo back the message."""
        result = {"message": message, "echoed_at": str(ctx.timestamp)}
        result.__metadata__ = self._create_metadata(source="example_agent")
        return result

    async def example_double(self, ctx: RequestCtx, state: Dict, value: int) -> Dict:
        """Double the input value."""
        result = {"value": value, "doubled": value * 2}
        result.__metadata__ = self._create_metadata(source="example_agent")
        return result
