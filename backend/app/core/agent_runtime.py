"""
DawsOS Agent Runtime

Purpose: Agent registration, capability routing, retry management, and rights enforcement
Updated: 2025-11-02
Priority: P0 (Critical for execution architecture)

Features:
    - Agent registration with capability mapping
    - Capability routing to correct agent
    - Dependency injection (services, DB, Redis)
    - Simple retry mechanism with exponential backoff (3 retries, 1s/2s/4s delays)
    - Request-level capability result caching
    - Result metadata preservation
    - Capability discovery
    - Rights validation and attribution (optional)

Usage:
    runtime = AgentRuntime(services)
    runtime.register_agent(FinancialAnalyst("financial_analyst", services))
    result = await runtime.execute_capability("ledger.positions", ctx, state, portfolio_id="...")

Retry Logic:
    - Max 3 retries with exponential backoff (1s, 2s, 4s)
    - No circuit breaker (removed for simplicity)
    - Failures are logged and metrics recorded
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseAgent
from app.core.types import RequestCtx

# Compliance modules archived (Phase 0-5 cleanup), not available
# See: .archive/compliance-archived-20251102/
get_attribution_manager = None
get_rights_registry = None

try:
    from observability.metrics import get_metrics
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Observability metrics module not available - metrics disabled")
    def get_metrics():
        """Fallback metrics function when observability not available"""
        return None

logger = logging.getLogger(__name__)


# ============================================================================
# Agent Runtime
# ============================================================================


class AgentRuntime:
    """
    Agent runtime: registration, routing, execution, and rights enforcement.

    Responsibilities:
        1. Register agents and build capability map
        2. Route capability requests to correct agent
        3. Inject dependencies (services, DB, Redis)
        4. Manage retries with exponential backoff for fault tolerance
        5. Preserve result metadata for tracing
        6. Enforce rights and add attributions (NEW)
    """

    def __init__(self, services: Dict[str, Any], enable_rights_enforcement: bool = True):
        """
        Initialize agent runtime.

        Args:
            services: Dependency injection dict (db, redis, API clients)
            enable_rights_enforcement: Enable rights validation and attribution (default: True)
        """
        self.services = services
        self.agents: Dict[str, BaseAgent] = {}
        self.capability_map: Dict[str, str] = {}  # capability → agent_name

        # Request-level capability cache
        # Format: {request_id: {cache_key: result}}
        self._request_caches: Dict[str, Dict[str, Any]] = {}
        self._cache_stats: Dict[str, Dict[str, int]] = {}  # {request_id: {hits: N, misses: N}}

        # Retry configuration
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s

        # Rights enforcement
        self.enable_rights_enforcement = enable_rights_enforcement
        if enable_rights_enforcement and get_attribution_manager is not None:
            self._attribution_manager = get_attribution_manager()
            self._rights_registry = get_rights_registry()
            logger.info("AgentRuntime initialized with rights enforcement enabled")
        else:
            self._attribution_manager = None
            self._rights_registry = None
            if enable_rights_enforcement:
                logger.warning("Rights enforcement requested but compliance modules not available")
            logger.info("AgentRuntime initialized (rights enforcement disabled)")

    def _get_cache_key(self, capability: str, kwargs: Dict[str, Any]) -> str:
        """
        Generate cache key for capability + arguments.

        Args:
            capability: Capability name
            kwargs: Capability arguments

        Returns:
            MD5 hash of capability + sorted args
        """
        import hashlib
        import json

        # Sort kwargs for consistent hashing
        sorted_args = json.dumps(kwargs, sort_keys=True, default=str)
        key_str = f"{capability}:{sorted_args}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def _get_cached_result(self, request_id: str, cache_key: str) -> Optional[Any]:
        """
        Get cached result if exists.

        Args:
            request_id: Request identifier
            cache_key: Cache key

        Returns:
            Cached result or None
        """
        request_cache = self._request_caches.get(request_id, {})
        if cache_key in request_cache:
            # Update stats
            if request_id not in self._cache_stats:
                self._cache_stats[request_id] = {"hits": 0, "misses": 0}
            self._cache_stats[request_id]["hits"] += 1
            logger.debug(f"Cache HIT: request={request_id[:8]}, key={cache_key[:8]}")
            return request_cache[cache_key]

        # Cache miss
        if request_id not in self._cache_stats:
            self._cache_stats[request_id] = {"hits": 0, "misses": 0}
        self._cache_stats[request_id]["misses"] += 1
        logger.debug(f"Cache MISS: request={request_id[:8]}, key={cache_key[:8]}")
        return None

    def _set_cached_result(self, request_id: str, cache_key: str, result: Any):
        """
        Cache capability result.

        Args:
            request_id: Request identifier
            cache_key: Cache key
            result: Result to cache
        """
        if request_id not in self._request_caches:
            self._request_caches[request_id] = {}
        self._request_caches[request_id][cache_key] = result
        logger.debug(f"Cache SET: request={request_id[:8]}, key={cache_key[:8]}")

    def get_cache_stats(self, request_id: str) -> Dict[str, Any]:
        """
        Get cache statistics for request.

        Args:
            request_id: Request identifier

        Returns:
            Dict with hits, misses, hit_rate
        """
        stats = self._cache_stats.get(request_id, {"hits": 0, "misses": 0})
        total = stats["hits"] + stats["misses"]
        hit_rate = stats["hits"] / total if total > 0 else 0.0

        return {
            "hits": stats["hits"],
            "misses": stats["misses"],
            "total": total,
            "hit_rate": hit_rate,
        }

    def clear_request_cache(self, request_id: str):
        """
        Clear cache for specific request (cleanup after request completes).

        Args:
            request_id: Request identifier
        """
        if request_id in self._request_caches:
            cache_size = len(self._request_caches[request_id])
            del self._request_caches[request_id]
            logger.debug(f"Cleared cache for request {request_id[:8]} ({cache_size} entries)")

        if request_id in self._cache_stats:
            del self._cache_stats[request_id]

    def register_agent(self, agent: BaseAgent):
        """
        Register an agent and its capabilities.

        Args:
            agent: Agent instance to register

        Raises:
            ValueError: If capability already registered by another agent
        """
        agent_name = agent.name

        if agent_name in self.agents:
            logger.warning(
                f"Agent {agent_name} already registered, replacing with new instance"
            )

        self.agents[agent_name] = agent

        # Map capabilities to agent
        capabilities = agent.get_capabilities()
        for cap in capabilities:
            if cap in self.capability_map:
                existing_agent = self.capability_map[cap]
                raise ValueError(
                    f"Capability {cap} already registered by {existing_agent}, "
                    f"cannot register for {agent_name}"
                )
            self.capability_map[cap] = agent_name

        logger.info(
            f"Registered agent {agent_name} with {len(capabilities)} capabilities: "
            f"{', '.join(capabilities)}"
        )

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """
        Get agent by name.

        Args:
            agent_name: Agent identifier

        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(agent_name)

    def get_agent_for_capability(self, capability: str) -> Optional[BaseAgent]:
        """
        Get agent that provides a capability.

        Args:
            capability: Capability name

        Returns:
            Agent instance or None if capability not registered
        """
        agent_name = self.capability_map.get(capability)
        if not agent_name:
            return None
        return self.agents.get(agent_name)

    def list_agents(self) -> List[Dict[str, Any]]:
        """
        Get list of all registered agents.

        Returns:
            List of agent info dicts
        """
        return [
            {
                "name": agent.name,
                "capabilities": agent.get_capabilities(),
            }
            for agent in self.agents.values()
        ]

    def list_capabilities(self) -> Dict[str, str]:
        """
        Get capability → agent mapping.

        Returns:
            Dict of capability names to agent names
        """
        return self.capability_map.copy()

    async def execute_capability(
        self,
        capability: str,
        ctx: RequestCtx,
        state: Dict[str, Any],
        **kwargs,
    ) -> Any:
        """
        Route capability to correct agent and execute with retry logic.

        Implements simple retry mechanism with exponential backoff:
        - 3 retries maximum
        - Exponential backoff: 1s, 2s, 4s
        - If all retries fail, raises the last exception

        Args:
            capability: Capability name (e.g., "ledger.positions")
            ctx: Immutable request context
            state: Pattern execution state
            **kwargs: Capability-specific arguments

        Returns:
            Result with __metadata__ attribute and __attributions__ (if rights enforcement enabled)

        Raises:
            ValueError: If capability not registered
            Exception: If capability execution fails after all retries
        """
        agent_name = self.capability_map.get(capability)
        if not agent_name:
            available = ", ".join(sorted(self.capability_map.keys()))
            raise ValueError(
                f"No agent registered for capability {capability}. "
                f"Available: {available}"
            )

        agent = self.agents[agent_name]

        # Check cache first
        cache_key = self._get_cache_key(capability, kwargs)
        cached_result = self._get_cached_result(ctx.request_id, cache_key)
        if cached_result is not None:
            logger.debug(
                f"Cache HIT for {capability} in {agent_name} "
                f"(request_id={ctx.request_id[:8]})"
            )
            return cached_result

        # Execute capability with retry logic
        metrics = get_metrics()

        last_exception = None
        for attempt in range(self.max_retries + 1):
            agent_start_time = time.time()
            agent_status = "success"

            try:
                if attempt > 0:
                    logger.info(
                        f"Retry attempt {attempt}/{self.max_retries} for {capability} "
                        f"in {agent_name}"
                    )
                else:
                    logger.debug(
                        f"Routing {capability} to {agent_name} "
                        f"(ctx.pricing_pack_id={ctx.pricing_pack_id})"
                    )

                result = await agent.execute(capability, ctx, state, **kwargs)

                # Add attributions if rights enforcement enabled
                if self.enable_rights_enforcement and self._attribution_manager:
                    result = self._add_attributions(result)

                # Cache the result
                self._set_cached_result(ctx.request_id, cache_key, result)

                # Record success metrics
                if metrics:
                    agent_duration = time.time() - agent_start_time
                    metrics.agent_invocations.labels(
                        agent_name=agent_name,
                        capability=capability,
                        status=agent_status,
                    ).inc()

                    metrics.agent_latency.labels(
                        agent_name=agent_name,
                        capability=capability,
                    ).observe(agent_duration)

                return result

            except Exception as e:
                agent_status = "error"
                last_exception = e

                # Log the error with appropriate severity based on attempt
                if attempt < self.max_retries:
                    logger.warning(
                        f"Capability {capability} failed in {agent_name} "
                        f"(attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                    )
                else:
                    logger.error(
                        f"Capability {capability} failed in {agent_name} "
                        f"after {self.max_retries + 1} attempts: {e}",
                        exc_info=True,
                    )

                # Record failure metrics
                if metrics:
                    agent_duration = time.time() - agent_start_time
                    metrics.agent_invocations.labels(
                        agent_name=agent_name,
                        capability=capability,
                        status=agent_status,
                    ).inc()

                    metrics.agent_latency.labels(
                        agent_name=agent_name,
                        capability=capability,
                    ).observe(agent_duration)

                # If this is not the last attempt, wait before retrying
                if attempt < self.max_retries:
                    delay = self.retry_delays[attempt]
                    logger.info(
                        f"Waiting {delay}s before retry for {capability} in {agent_name}"
                    )
                    await asyncio.sleep(delay)
                    continue

                # If all retries failed, raise the last exception
                raise

        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(f"Unexpected error in retry logic for {capability}")

    def _add_attributions(self, result: Any) -> Any:
        """
        Add attributions to capability result.

        Extracts data sources from result metadata and adds __attributions__ field.

        Args:
            result: Capability result

        Returns:
            Result with attributions added
        """
        if not isinstance(result, dict):
            # Can't add attributions to non-dict results
            return result

        try:
            # Extract sources from result metadata
            sources = self._attribution_manager.extract_sources(result)

            if sources:
                # Add attributions
                result = self._attribution_manager.attach_attributions(
                    result, sources=sources
                )

        except Exception as e:
            logger.warning(f"Failed to add attributions: {e}", exc_info=True)

        return result


# ============================================================================
# Helper Functions
# ============================================================================


def create_runtime_with_agents(services: Dict[str, Any]) -> AgentRuntime:
    """
    Create agent runtime and register all available agents.

    Args:
        services: Dependency injection dict

    Returns:
        AgentRuntime with all agents registered
    """
    runtime = AgentRuntime(services)

    # Register production agents
    from app.agents.macro_hound import MacroHound

    try:
        from app.agents.financial_analyst import FinancialAnalyst
        runtime.register_agent(FinancialAnalyst("financial_analyst", services))
    except ImportError as e:
        logger.warning(f"FinancialAnalyst not available: {e}")

    try:
        runtime.register_agent(MacroHound("macro_hound", services))
    except ImportError as e:
        logger.warning(f"MacroHound not available: {e}")

    try:
        from app.agents.data_harvester import DataHarvester
        runtime.register_agent(DataHarvester("data_harvester", services))
    except ImportError as e:
        logger.warning(f"DataHarvester not available: {e}")

    # Register example agent for testing
    from app.agents.base_agent import ExampleAgent
    runtime.register_agent(ExampleAgent("example_agent", services))

    logger.info(f"Runtime initialized with {len(runtime.agents)} agents")
    return runtime