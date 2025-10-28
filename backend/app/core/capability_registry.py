"""
DawsOS Capability Registry

Purpose: Centralized capability discovery and documentation
Updated: 2025-10-21
Priority: P0 (Critical for capability routing)

Features:
    - List all registered capabilities
    - Get agent providing a capability
    - Validate capability availability
    - Generate capability documentation
    - Category-based capability grouping

Usage:
    registry = CapabilityRegistry(agent_runtime)
    capabilities = registry.list_capabilities()
    agent = registry.get_agent_for_capability("ledger.positions")
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.agent_runtime import AgentRuntime

logger = logging.getLogger(__name__)


# ============================================================================
# Capability Categories
# ============================================================================

CAPABILITY_CATEGORIES = {
    "ledger": "Ledger and position management",
    "pricing": "Pricing and market data",
    "metrics": "Performance metrics and calculations",
    "attribution": "Return attribution analysis",
    "regime": "Economic regime detection",
    "factor": "Factor exposure analysis",
    "scenario": "Scenario analysis and stress testing",
    "quality": "Quality ratings (Buffett framework)",
    "charts": "Chart generation for UI",
    "export": "Data export and reports",
}


# ============================================================================
# Capability Registry
# ============================================================================


class CapabilityRegistry:
    """
    Capability registry: discovery and documentation.

    Wraps AgentRuntime to provide capability-centric view rather than
    agent-centric view. Useful for UI capability pickers, documentation
    generation, and validation.
    """

    def __init__(self, agent_runtime: AgentRuntime):
        """
        Initialize capability registry.

        Args:
            agent_runtime: AgentRuntime with registered agents
        """
        self.runtime = agent_runtime
        self._capability_cache: Optional[List[Dict[str, Any]]] = None
        logger.info("CapabilityRegistry initialized")

    def list_capabilities(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all registered capabilities with metadata.

        Args:
            category: Optional category filter (e.g., "ledger", "pricing")

        Returns:
            List of capability info dicts:
            [
                {
                    "name": "ledger.positions",
                    "category": "ledger",
                    "agent": "financial_analyst",
                    "description": "Get current positions from lots table"
                },
                ...
            ]
        """
        if self._capability_cache is None:
            self._build_cache()

        capabilities = self._capability_cache or []

        if category:
            capabilities = [c for c in capabilities if c["category"] == category]

        return capabilities

    def get_capability_info(self, capability: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific capability.

        Args:
            capability: Capability name

        Returns:
            Capability info dict or None if not found
        """
        capabilities = self.list_capabilities()
        for cap in capabilities:
            if cap["name"] == capability:
                return cap
        return None

    def get_agent_for_capability(self, capability: str) -> Optional[str]:
        """
        Get agent name providing a capability.

        Args:
            capability: Capability name

        Returns:
            Agent name or None if capability not registered
        """
        capability_map = self.runtime.list_capabilities()
        return capability_map.get(capability)

    def is_capability_available(self, capability: str) -> bool:
        """
        Check if capability is registered and available.

        Args:
            capability: Capability name

        Returns:
            True if capability is available
        """
        return capability in self.runtime.list_capabilities()

    def validate_capabilities(self, capabilities: List[str]) -> Dict[str, Any]:
        """
        Validate that all capabilities in list are available.

        Args:
            capabilities: List of capability names to validate

        Returns:
            Dict with:
            {
                "valid": True/False,
                "available": [...],  # List of available capabilities
                "missing": [...]     # List of missing capabilities
            }
        """
        available_caps = set(self.runtime.list_capabilities().keys())
        requested_caps = set(capabilities)

        missing = requested_caps - available_caps
        available = requested_caps & available_caps

        return {
            "valid": len(missing) == 0,
            "available": sorted(list(available)),
            "missing": sorted(list(missing)),
        }

    def get_capabilities_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group capabilities by category.

        Returns:
            Dict of category → list of capabilities
        """
        capabilities = self.list_capabilities()
        grouped: Dict[str, List[Dict[str, Any]]] = {}

        for cap in capabilities:
            category = cap["category"]
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(cap)

        return grouped

    def generate_documentation(self) -> str:
        """
        Generate markdown documentation for all capabilities.

        Returns:
            Markdown string with capability reference
        """
        lines = ["# DawsOS Capability Reference\n"]
        lines.append(
            "This document lists all registered capabilities in the DawsOS execution architecture.\n"
        )

        grouped = self.get_capabilities_by_category()

        for category in sorted(grouped.keys()):
            category_desc = CAPABILITY_CATEGORIES.get(
                category, "No description"
            )
            lines.append(f"## {category.capitalize()}\n")
            lines.append(f"{category_desc}\n")

            for cap in sorted(grouped[category], key=lambda c: c["name"]):
                lines.append(f"### `{cap['name']}`\n")
                lines.append(f"**Agent**: {cap['agent']}\n")
                if cap.get("description"):
                    lines.append(f"{cap['description']}\n")
                lines.append("")

        return "\n".join(lines)

    def _build_cache(self):
        """
        Build capability cache from runtime.

        Extracts capability metadata from agents and caches it.
        """
        capabilities = []
        capability_map = self.runtime.list_capabilities()

        for cap_name, agent_name in capability_map.items():
            # Extract category from capability name (e.g., "ledger.positions" → "ledger")
            category = cap_name.split(".")[0] if "." in cap_name else "unknown"

            # Get agent
            agent = self.runtime.get_agent(agent_name)

            # Try to extract description from method docstring
            description = ""
            if agent:
                method_name = cap_name.replace(".", "_")
                if hasattr(agent, method_name):
                    method = getattr(agent, method_name)
                    if method.__doc__:
                        # Take first line of docstring
                        description = method.__doc__.strip().split("\n")[0]

            capabilities.append({
                "name": cap_name,
                "category": category,
                "agent": agent_name,
                "description": description,
            })

        self._capability_cache = capabilities
        logger.info(f"Built capability cache with {len(capabilities)} capabilities")

    def invalidate_cache(self):
        """
        Invalidate capability cache.

        Call this if agents are registered after registry creation.
        """
        self._capability_cache = None
        logger.debug("Capability cache invalidated")


# ============================================================================
# Helper Functions
# ============================================================================


def create_registry(agent_runtime: AgentRuntime) -> CapabilityRegistry:
    """
    Create capability registry from agent runtime.

    Args:
        agent_runtime: AgentRuntime with registered agents

    Returns:
        CapabilityRegistry instance
    """
    return CapabilityRegistry(agent_runtime)


def validate_pattern_capabilities(
    registry: CapabilityRegistry, pattern: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate that pattern's capabilities are all available.

    Args:
        registry: CapabilityRegistry instance
        pattern: Pattern specification dict

    Returns:
        Validation result dict with valid, available, missing
    """
    steps = pattern.get("steps", [])
    capabilities = [step["capability"] for step in steps]
    return registry.validate_capabilities(capabilities)
