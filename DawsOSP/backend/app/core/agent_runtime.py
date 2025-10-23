"""
DawsOS Agent Runtime

Purpose: Agent registration, capability routing, circuit breaker management, and rights enforcement
Updated: 2025-10-22
Priority: P0 (Critical for execution architecture)

Features:
    - Agent registration with capability mapping
    - Capability routing to correct agent
    - Dependency injection (services, DB, Redis)
    - Circuit breaker for agent failures
    - Result metadata preservation
    - Capability discovery
    - Rights validation and attribution (NEW)

Usage:
    runtime = AgentRuntime(services)
    runtime.register_agent(FinancialAnalyst("financial_analyst", services))
    result = await runtime.execute_capability("ledger.positions", ctx, state, portfolio_id="...")
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseAgent
from app.core.types import RequestCtx
from backend.compliance.attribution import get_attribution_manager
from backend.compliance.rights_registry import get_rights_registry

logger = logging.getLogger(__name__)


# ============================================================================
# Circuit Breaker
# ============================================================================


class CircuitBreaker:
    """
    Circuit breaker for agent failure management.

    Prevents cascading failures by opening circuit after threshold
    failures, then attempting recovery after timeout.

    States:
        - CLOSED: Normal operation, requests pass through
        - OPEN: Too many failures, requests blocked
        - HALF_OPEN: Testing recovery, limited requests allowed
    """

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures: Dict[str, int] = {}
        self.open_until: Dict[str, datetime] = {}

    def is_open(self, agent_name: str) -> bool:
        """
        Check if circuit is open for agent.

        Args:
            agent_name: Agent identifier

        Returns:
            True if circuit is open (requests blocked)
        """
        if agent_name in self.open_until:
            if datetime.now() < self.open_until[agent_name]:
                return True
            else:
                # Timeout expired, move to half-open
                logger.info(f"Circuit breaker for {agent_name}: OPEN → HALF_OPEN")
                del self.open_until[agent_name]
                self.failures[agent_name] = 0

        return False

    def record_failure(self, agent_name: str):
        """
        Record agent failure.

        Opens circuit if threshold exceeded.

        Args:
            agent_name: Agent identifier
        """
        self.failures[agent_name] = self.failures.get(agent_name, 0) + 1
        failure_count = self.failures[agent_name]

        logger.warning(
            f"Agent {agent_name} failure recorded "
            f"({failure_count}/{self.failure_threshold})"
        )

        if failure_count >= self.failure_threshold:
            self.open_until[agent_name] = datetime.now() + timedelta(
                seconds=self.timeout
            )
            logger.error(
                f"Circuit breaker OPENED for {agent_name} "
                f"(timeout: {self.timeout}s)"
            )

    def record_success(self, agent_name: str):
        """
        Record agent success.

        Closes circuit and resets failure count.

        Args:
            agent_name: Agent identifier
        """
        if agent_name in self.failures and self.failures[agent_name] > 0:
            logger.info(f"Circuit breaker for {agent_name}: resetting failure count")
            self.failures[agent_name] = 0

        if agent_name in self.open_until:
            logger.info(f"Circuit breaker for {agent_name}: HALF_OPEN → CLOSED")
            del self.open_until[agent_name]

    def get_status(self, agent_name: str) -> Dict[str, Any]:
        """
        Get circuit breaker status for agent.

        Args:
            agent_name: Agent identifier

        Returns:
            Dict with state, failures, and open_until (if applicable)
        """
        is_open = self.is_open(agent_name)
        return {
            "agent_name": agent_name,
            "state": "OPEN" if is_open else "CLOSED",
            "failures": self.failures.get(agent_name, 0),
            "open_until": (
                self.open_until[agent_name].isoformat()
                if agent_name in self.open_until
                else None
            ),
        }


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
        4. Manage circuit breakers for fault tolerance
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
        self.circuit_breaker = CircuitBreaker()

        # Rights enforcement
        self.enable_rights_enforcement = enable_rights_enforcement
        if enable_rights_enforcement:
            self._attribution_manager = get_attribution_manager()
            self._rights_registry = get_rights_registry()
            logger.info("AgentRuntime initialized with rights enforcement enabled")
        else:
            self._attribution_manager = None
            self._rights_registry = None
            logger.info("AgentRuntime initialized (rights enforcement disabled)")

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
                "circuit_breaker": self.circuit_breaker.get_status(agent.name),
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
        Route capability to correct agent and execute.

        Args:
            capability: Capability name (e.g., "ledger.positions")
            ctx: Immutable request context
            state: Pattern execution state
            **kwargs: Capability-specific arguments

        Returns:
            Result with __metadata__ attribute and __attributions__ (if rights enforcement enabled)

        Raises:
            ValueError: If capability not registered
            HTTPException: If circuit breaker is open (503)
            Exception: If capability execution fails
        """
        agent_name = self.capability_map.get(capability)
        if not agent_name:
            available = ", ".join(sorted(self.capability_map.keys()))
            raise ValueError(
                f"No agent registered for capability {capability}. "
                f"Available: {available}"
            )

        agent = self.agents[agent_name]

        # Check circuit breaker
        if self.circuit_breaker.is_open(agent_name):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "CIRCUIT_BREAKER_OPEN",
                    "message": f"Agent {agent_name} circuit breaker is open",
                    "agent": agent_name,
                    "capability": capability,
                },
            )

        # Execute capability
        try:
            logger.debug(
                f"Routing {capability} to {agent_name} "
                f"(ctx.pricing_pack_id={ctx.pricing_pack_id})"
            )

            result = await agent.execute(capability, ctx, state, **kwargs)

            # Add attributions if rights enforcement enabled
            if self.enable_rights_enforcement and self._attribution_manager:
                result = self._add_attributions(result)

            self.circuit_breaker.record_success(agent_name)
            return result

        except Exception as e:
            self.circuit_breaker.record_failure(agent_name)
            logger.error(
                f"Capability {capability} failed in {agent_name}: {e}",
                exc_info=True,
            )
            raise

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

    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get circuit breaker status for all agents.

        Returns:
            Dict of agent_name → status
        """
        return {
            agent_name: self.circuit_breaker.get_status(agent_name)
            for agent_name in self.agents.keys()
        }


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

    # TODO: Import and register actual agents as they're implemented
    # from app.agents.financial_analyst import FinancialAnalyst
    # from app.agents.macro_hound import MacroHound
    # from app.agents.data_harvester import DataHarvester

    # runtime.register_agent(FinancialAnalyst("financial_analyst", services))
    # runtime.register_agent(MacroHound("macro_hound", services))
    # runtime.register_agent(DataHarvester("data_harvester", services))

    # Register example agent for testing
    from app.agents.base_agent import ExampleAgent
    runtime.register_agent(ExampleAgent("example_agent", services))

    logger.info(f"Runtime initialized with {len(runtime.agents)} agents")
    return runtime
