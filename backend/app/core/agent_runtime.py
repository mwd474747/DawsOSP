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

# Compliance modules not used in current deployment
# Attribution and rights management are handled by the pattern orchestrator
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

# Import feature flags for capability routing
try:
    from app.core.feature_flags import get_feature_flags
    FEATURE_FLAGS_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Feature flags module not available - using default routing")
    get_feature_flags = None
    FEATURE_FLAGS_AVAILABLE = False

# Import capability mapping for consolidation routing
try:
    from app.core.capability_mapping import (
        get_consolidated_capability,
        get_target_agent,
        get_consolidation_info,
        AGENT_CONSOLIDATION_MAP
    )
    CAPABILITY_MAPPING_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Capability mapping module not available - using direct routing")
    get_consolidated_capability = None
    get_target_agent = None
    get_consolidation_info = None
    AGENT_CONSOLIDATION_MAP = {}
    CAPABILITY_MAPPING_AVAILABLE = False

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
        self.capability_map: Dict[str, str] = {}  # capability → primary agent_name
        
        # Support for dual registration (multiple agents for same capability)
        # Format: {capability: [(agent_name, priority), ...]}
        self.capability_registry: Dict[str, List[Tuple[str, int]]] = {}
        
        # Request-level capability cache
        # Format: {request_id: {cache_key: result}}
        self._request_caches: Dict[str, Dict[str, Any]] = {}
        self._cache_stats: Dict[str, Dict[str, int]] = {}  # {request_id: {hits: N, misses: N}}
        
        # Routing decision log for monitoring
        self._routing_decisions: List[Dict[str, Any]] = []
        self._max_routing_log = 1000  # Keep last N routing decisions

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

    def register_agent(self, agent: BaseAgent, priority: int = 100, allow_dual_registration: bool = True):
        """
        Register an agent and its capabilities.
        
        Supports dual registration where multiple agents can provide the same capability
        for safe consolidation rollout.

        Args:
            agent: Agent instance to register
            priority: Priority for capability routing (lower = higher priority, default 100)
            allow_dual_registration: Allow multiple agents to handle same capability

        Raises:
            ValueError: If capability conflict and dual registration not allowed
        """
        agent_name = agent.name

        if agent_name in self.agents:
            logger.warning(
                f"Agent {agent_name} already registered, replacing with new instance"
            )

        self.agents[agent_name] = agent

        # Map capabilities to agent with support for dual registration
        capabilities = agent.get_capabilities()
        conflicts = []
        
        for cap in capabilities:
            # Check for existing registration
            if cap in self.capability_map and not allow_dual_registration:
                existing_agent = self.capability_map[cap]
                conflicts.append(f"{cap} (already in {existing_agent})")
                continue
                
            # Initialize registry entry if needed
            if cap not in self.capability_registry:
                self.capability_registry[cap] = []
            
            # Add agent to registry with priority
            self.capability_registry[cap].append((agent_name, priority))
            # Sort by priority (ascending)
            self.capability_registry[cap].sort(key=lambda x: x[1])
            
            # Update primary mapping (agent with highest priority)
            if not self.capability_map.get(cap) or priority < self.capability_registry[cap][0][1]:
                self.capability_map[cap] = agent_name
        
        if conflicts and not allow_dual_registration:
            raise ValueError(
                f"Capability conflicts for {agent_name}: {', '.join(conflicts)}. "
                f"Set allow_dual_registration=True to enable consolidation mode."
            )

        logger.info(
            f"Registered agent {agent_name} with {len(capabilities)} capabilities "
            f"(priority={priority}, dual_reg={allow_dual_registration}): "
            f"{', '.join(capabilities[:5])}{'...' if len(capabilities) > 5 else ''}"
        )
        
        # Log any dual registrations for monitoring
        for cap in capabilities:
            if len(self.capability_registry.get(cap, [])) > 1:
                agents = [a for a, _ in self.capability_registry[cap]]
                logger.debug(f"Capability '{cap}' now handled by multiple agents: {agents}")

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

    def _log_routing_decision(self, decision: Dict[str, Any]):
        """
        Log a routing decision for monitoring.
        
        Args:
            decision: Routing decision details
        """
        import datetime
        decision["timestamp"] = datetime.datetime.now().isoformat()
        
        # Keep only last N decisions
        self._routing_decisions.append(decision)
        if len(self._routing_decisions) > self._max_routing_log:
            self._routing_decisions.pop(0)
            
    def get_routing_decisions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent routing decisions for monitoring.
        
        Args:
            limit: Maximum number of decisions to return
            
        Returns:
            List of recent routing decisions
        """
        return self._routing_decisions[-limit:]

    def _get_capability_routing_override(
        self, 
        capability: str, 
        original_agent: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Check if capability routing should be overridden by feature flags and capability mapping.
        
        Uses both feature flags and capability mapping for intelligent routing during consolidation.
        
        Args:
            capability: Capability name (e.g., "optimizer.propose_trades")
            original_agent: Original agent that handles this capability
            context: Context for percentage rollout decisions (user_id, request_id, etc.)
            
        Returns:
            Override agent name or None to use original routing
        """
        routing_decision = {
            "capability": capability,
            "original_agent": original_agent,
            "override_agent": None,
            "reason": None,
            "context": context
        }
        
        # First check capability mapping if available
        if CAPABILITY_MAPPING_AVAILABLE and get_target_agent is not None:
            # Get consolidation info for this capability
            consolidation_info = get_consolidation_info(capability) if get_consolidation_info else {}
            target_agent = consolidation_info.get("target_agent")
            
            if target_agent and target_agent != original_agent:
                # This capability should be consolidated
                # Now check if feature flags allow it
                if FEATURE_FLAGS_AVAILABLE and get_feature_flags is not None:
                    try:
                        flags = get_feature_flags()
                        
                        # Build flag name from agent consolidation
                        # e.g., "optimizer" → "agent_consolidation.optimizer_to_financial"
                        agent_prefix = capability.split(".")[0] if "." in capability else original_agent
                        
                        # Check consolidation flags
                        flag_mappings = {
                            "optimizer": "agent_consolidation.optimizer_to_financial",
                            "ratings": "agent_consolidation.ratings_to_financial",
                            "charts": "agent_consolidation.charts_to_financial",
                            "reports": "agent_consolidation.reports_to_financial",
                            "alerts": "agent_consolidation.alerts_to_macro",
                        }
                        
                        flag_name = flag_mappings.get(agent_prefix)
                        
                        # Check unified consolidation flag first
                        if flags.is_enabled("agent_consolidation.unified_consolidation", context):
                            # Unified consolidation enabled - check if target agent exists
                            if target_agent in self.agents:
                                # Check if agent can handle this (priority-based)
                                agents_for_cap = self.capability_registry.get(capability, [])
                                if any(a[0] == target_agent for a in agents_for_cap):
                                    routing_decision["override_agent"] = target_agent
                                    routing_decision["reason"] = "unified_consolidation_flag"
                                    logger.info(
                                        f"Routing {capability}: {original_agent} → {target_agent} "
                                        f"(unified consolidation, priority={consolidation_info.get('priority', 'unknown')})"
                                    )
                                    self._log_routing_decision(routing_decision)
                                    return target_agent
                        
                        # Check specific consolidation flag
                        elif flag_name and flags.is_enabled(flag_name, context):
                            # Specific consolidation enabled
                            if target_agent in self.agents:
                                # Check if agent can handle this
                                agents_for_cap = self.capability_registry.get(capability, [])
                                if any(a[0] == target_agent for a in agents_for_cap):
                                    routing_decision["override_agent"] = target_agent
                                    routing_decision["reason"] = f"flag:{flag_name}"
                                    logger.info(
                                        f"Routing {capability}: {original_agent} → {target_agent} "
                                        f"(flag: {flag_name}, risk: {consolidation_info.get('risk_level', 'unknown')})"
                                    )
                                    self._log_routing_decision(routing_decision)
                                    return target_agent
                    
                    except Exception as e:
                        logger.error(f"Error checking feature flags for {capability}: {e}")
                        routing_decision["reason"] = f"error:{str(e)}"
        
        # No override - use original routing
        routing_decision["reason"] = "no_override"
        self._log_routing_decision(routing_decision)
        return None

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

        # Check for feature flag routing overrides
        # Build context for feature flag decisions
        flag_context = {
            "request_id": ctx.request_id,
            "portfolio_id": getattr(ctx, "portfolio_id", None),
            "user_id": getattr(ctx, "user_id", None),
        }
        
        # Check if routing should be overridden
        override_agent = self._get_capability_routing_override(
            capability, agent_name, flag_context
        )
        
        if override_agent:
            logger.info(
                f"Feature flag override: Routing {capability} from {agent_name} to {override_agent}"
            )
            agent_name = override_agent
        
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