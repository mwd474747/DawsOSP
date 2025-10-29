"""
DawsOS Base Agent

Purpose: Abstract base class for all capability-providing agents
Updated: 2025-10-21
Priority: P0 (Critical for agent architecture)

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

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from backend.app.core.types import RequestCtx

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
                "data": result,
                "_metadata": metadata.to_dict()
            }

        return result


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
            # Implement Redis caching
            cache_key = f"{self.__class__.__name__}:{func.__name__}:{hash(str(kwargs))}"
            try:
                # Try to get from cache first
                cached_result = await self.redis.get(cache_key)
                if cached_result:
                    return json.loads(cached_result)
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")
            
            # Execute function and cache result
            result = await func(self, ctx, state, **kwargs)
            try:
                await self.redis.setex(cache_key, ttl, json.dumps(result, default=str))
            except Exception as e:
                logger.warning(f"Cache write failed: {e}")
            
            return result
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
