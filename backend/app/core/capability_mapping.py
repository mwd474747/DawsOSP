"""
DawsOS Capability Consolidation Mapping

Purpose: Maps capabilities from individual agents to consolidated agents for Phase 3
Created: 2025-11-03
Priority: P1 (Critical for agent consolidation)

This module defines how capabilities will be consolidated from 8+ agents down to 3 agents:
  - FinancialAnalyst: Core portfolio management (metrics, ratings, optimization, charts)
  - MacroHound: Macro analysis and alerts
  - DataHarvester: External data and reports

Features:
    - Forward mapping (old → new capabilities)
    - Reverse mapping (new → old for backward compatibility)
    - Consolidation metadata (priority, risk level, dependencies)
    - Agent mapping (which old agent → which new agent)
    
Usage:
    from app.core.capability_mapping import get_consolidated_capability, get_target_agent
    
    new_capability = get_consolidated_capability("optimizer.propose_trades")
    # Returns: "financial_analyst.propose_trades"
    
    target_agent = get_target_agent("optimizer.propose_trades") 
    # Returns: "financial_analyst"
"""

import logging
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ============================================================================
# Capability Consolidation Map
# ============================================================================

CAPABILITY_CONSOLIDATION_MAP = {
    # --------------------------------------------------------------------------
    # OptimizerAgent → FinancialAnalyst
    # --------------------------------------------------------------------------
    "optimizer.propose_trades": {
        "target": "financial_analyst.propose_trades",
        "target_agent": "financial_analyst",
        "priority": 1,  # Core functionality, high priority
        "risk_level": "high",  # Trading decisions require careful migration
        "dependencies": ["ledger.positions", "pricing.apply_pack"],
    },
    "optimizer.analyze_impact": {
        "target": "financial_analyst.analyze_impact",
        "target_agent": "financial_analyst",
        "priority": 1,
        "risk_level": "medium",
        "dependencies": ["ledger.positions"],
    },
    "optimizer.suggest_hedges": {
        "target": "financial_analyst.suggest_hedges",
        "target_agent": "financial_analyst",
        "priority": 2,
        "risk_level": "medium",
        "dependencies": ["macro.run_scenario"],
    },
    "optimizer.suggest_deleveraging_hedges": {
        "target": "financial_analyst.suggest_deleveraging_hedges",
        "target_agent": "financial_analyst",
        "priority": 2,
        "risk_level": "medium",
        "dependencies": ["macro.detect_regime"],
    },

    # --------------------------------------------------------------------------
    # RatingsAgent → FinancialAnalyst
    # --------------------------------------------------------------------------
    "ratings.dividend_safety": {
        "target": "financial_analyst.dividend_safety",
        "target_agent": "financial_analyst",
        "priority": 1,
        "risk_level": "low",
        "dependencies": ["provider.fetch_fundamentals"],
    },
    "ratings.moat_strength": {
        "target": "financial_analyst.moat_strength",
        "target_agent": "financial_analyst",
        "priority": 1,
        "risk_level": "low",
        "dependencies": ["provider.fetch_fundamentals"],
    },
    "ratings.resilience": {
        "target": "financial_analyst.resilience",
        "target_agent": "financial_analyst",
        "priority": 1,
        "risk_level": "low",
        "dependencies": ["provider.fetch_fundamentals"],
    },
    "ratings.aggregate": {
        "target": "financial_analyst.aggregate_ratings",
        "target_agent": "financial_analyst",
        "priority": 1,
        "risk_level": "low",
        "dependencies": ["ratings.dividend_safety", "ratings.moat_strength", "ratings.resilience"],
    },

    # --------------------------------------------------------------------------
    # ChartsAgent → FinancialAnalyst
    # --------------------------------------------------------------------------
    "charts.macro_overview": {
        "target": "financial_analyst.macro_overview_charts",
        "target_agent": "financial_analyst",
        "priority": 2,
        "risk_level": "low",
        "dependencies": ["macro.detect_regime"],
    },
    "charts.scenario_deltas": {
        "target": "financial_analyst.scenario_charts",
        "target_agent": "financial_analyst",
        "priority": 2,
        "risk_level": "low",
        "dependencies": ["macro.run_scenario"],
    },

    # --------------------------------------------------------------------------
    # AlertsAgent → MacroHound
    # --------------------------------------------------------------------------
    "alerts.suggest_presets": {
        "target": "macro_hound.suggest_alerts",
        "target_agent": "macro_hound",
        "priority": 2,
        "risk_level": "medium",
        "dependencies": ["macro.detect_trend_shifts"],
    },
    "alerts.create_if_threshold": {
        "target": "macro_hound.create_alert",
        "target_agent": "macro_hound",
        "priority": 2,
        "risk_level": "medium",
        "dependencies": ["news.compute_portfolio_impact"],
    },

    # --------------------------------------------------------------------------
    # ReportsAgent → DataHarvester
    # --------------------------------------------------------------------------
    "reports.render_pdf": {
        "target": "data_harvester.render_pdf",
        "target_agent": "data_harvester",
        "priority": 1,
        "risk_level": "low",
        "dependencies": [],
    },
    "reports.export_csv": {
        "target": "data_harvester.export_csv",
        "target_agent": "data_harvester",
        "priority": 1,
        "risk_level": "low",
        "dependencies": [],
    },
    "reports.export_excel": {
        "target": "data_harvester.export_excel",
        "target_agent": "data_harvester",
        "priority": 3,
        "risk_level": "low",
        "dependencies": [],
    },

    # --------------------------------------------------------------------------
    # Existing capabilities that remain unchanged (already in target agent)
    # --------------------------------------------------------------------------
    # FinancialAnalyst capabilities remain as-is
    "ledger.positions": {
        "target": "ledger.positions",
        "target_agent": "financial_analyst",
        "priority": 0,  # Already in target agent
        "risk_level": "none",
        "dependencies": [],
    },
    "pricing.apply_pack": {
        "target": "pricing.apply_pack",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "metrics.compute": {
        "target": "metrics.compute",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "metrics.compute_twr": {
        "target": "metrics.compute_twr",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "metrics.compute_sharpe": {
        "target": "metrics.compute_sharpe",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "attribution.currency": {
        "target": "attribution.currency",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "charts.overview": {
        "target": "charts.overview",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "risk.compute_factor_exposures": {
        "target": "risk.compute_factor_exposures",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "risk.get_factor_exposure_history": {
        "target": "risk.get_factor_exposure_history",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "risk.overlay_cycle_phases": {
        "target": "risk.overlay_cycle_phases",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "get_position_details": {
        "target": "get_position_details",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "compute_position_return": {
        "target": "compute_position_return",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "compute_portfolio_contribution": {
        "target": "compute_portfolio_contribution",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "compute_position_currency_attribution": {
        "target": "compute_position_currency_attribution",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "compute_position_risk": {
        "target": "compute_position_risk",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "get_transaction_history": {
        "target": "get_transaction_history",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "get_security_fundamentals": {
        "target": "get_security_fundamentals",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "get_comparable_positions": {
        "target": "get_comparable_positions",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "portfolio.sector_allocation": {
        "target": "portfolio.sector_allocation",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "portfolio.historical_nav": {
        "target": "portfolio.historical_nav",
        "target_agent": "financial_analyst",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },

    # MacroHound capabilities remain as-is
    "macro.detect_regime": {
        "target": "macro.detect_regime",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "macro.compute_cycles": {
        "target": "macro.compute_cycles",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "macro.get_indicators": {
        "target": "macro.get_indicators",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "macro.run_scenario": {
        "target": "macro.run_scenario",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "macro.compute_dar": {
        "target": "macro.compute_dar",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "macro.get_regime_history": {
        "target": "macro.get_regime_history",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "macro.detect_trend_shifts": {
        "target": "macro.detect_trend_shifts",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "cycles.compute_short_term": {
        "target": "cycles.compute_short_term",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "cycles.compute_long_term": {
        "target": "cycles.compute_long_term",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "cycles.compute_empire": {
        "target": "cycles.compute_empire",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "cycles.compute_civil": {
        "target": "cycles.compute_civil",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "cycles.aggregate_overview": {
        "target": "cycles.aggregate_overview",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "scenarios.deleveraging_austerity": {
        "target": "scenarios.deleveraging_austerity",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "scenarios.deleveraging_default": {
        "target": "scenarios.deleveraging_default",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "scenarios.deleveraging_money_printing": {
        "target": "scenarios.deleveraging_money_printing",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "scenarios.macro_aware_apply": {
        "target": "scenarios.macro_aware_apply",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "scenarios.macro_aware_rank": {
        "target": "scenarios.macro_aware_rank",
        "target_agent": "macro_hound",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },

    # DataHarvester capabilities remain as-is
    "provider.fetch_quote": {
        "target": "provider.fetch_quote",
        "target_agent": "data_harvester",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "provider.fetch_fundamentals": {
        "target": "provider.fetch_fundamentals",
        "target_agent": "data_harvester",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "provider.fetch_news": {
        "target": "provider.fetch_news",
        "target_agent": "data_harvester",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "provider.fetch_macro": {
        "target": "provider.fetch_macro",
        "target_agent": "data_harvester",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "provider.fetch_ratios": {
        "target": "provider.fetch_ratios",
        "target_agent": "data_harvester",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "fundamentals.load": {
        "target": "fundamentals.load",
        "target_agent": "data_harvester",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "news.search": {
        "target": "news.search",
        "target_agent": "data_harvester",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
    "news.compute_portfolio_impact": {
        "target": "news.compute_portfolio_impact",
        "target_agent": "data_harvester",
        "priority": 0,
        "risk_level": "none",
        "dependencies": [],
    },
}

# ============================================================================
# Reverse Mapping (New → Old for backward compatibility)
# ============================================================================

REVERSE_CONSOLIDATION_MAP = {}

def _build_reverse_mapping():
    """Build reverse mapping from new capabilities to old."""
    global REVERSE_CONSOLIDATION_MAP
    for old_capability, mapping in CAPABILITY_CONSOLIDATION_MAP.items():
        new_capability = mapping["target"]
        if new_capability not in REVERSE_CONSOLIDATION_MAP:
            REVERSE_CONSOLIDATION_MAP[new_capability] = []
        REVERSE_CONSOLIDATION_MAP[new_capability].append(old_capability)

# Build reverse mapping on module import
_build_reverse_mapping()

# ============================================================================
# Agent Consolidation Mapping
# ============================================================================

AGENT_CONSOLIDATION_MAP = {
    # Agents being consolidated away
    "optimizer": "financial_analyst",
    "ratings": "financial_analyst",
    "charts": "financial_analyst",
    "alerts": "macro_hound",
    "reports": "data_harvester",
    
    # Agents that remain as-is
    "financial_analyst": "financial_analyst",
    "macro_hound": "macro_hound",
    "data_harvester": "data_harvester",
}

# ============================================================================
# Helper Functions
# ============================================================================

def get_consolidated_capability(old_capability: str) -> str:
    """
    Get the consolidated (new) capability name for an old capability.
    
    Args:
        old_capability: Original capability name (e.g., "optimizer.propose_trades")
        
    Returns:
        New consolidated capability name (e.g., "financial_analyst.propose_trades")
    """
    if old_capability in CAPABILITY_CONSOLIDATION_MAP:
        return CAPABILITY_CONSOLIDATION_MAP[old_capability]["target"]
    return old_capability  # No consolidation needed

def get_target_agent(capability: str) -> str:
    """
    Get the target agent for a capability after consolidation.
    
    Args:
        capability: Capability name (old or new)
        
    Returns:
        Target agent name (e.g., "financial_analyst")
    """
    if capability in CAPABILITY_CONSOLIDATION_MAP:
        return CAPABILITY_CONSOLIDATION_MAP[capability]["target_agent"]
    
    # Try to extract agent from capability name
    if "." in capability:
        agent_prefix = capability.split(".")[0]
        if agent_prefix in AGENT_CONSOLIDATION_MAP:
            return AGENT_CONSOLIDATION_MAP[agent_prefix]
    
    # Default to extracting agent from capability name
    if "." in capability:
        return capability.split(".")[0]
    
    return "unknown"

def get_original_capabilities(new_capability: str) -> List[str]:
    """
    Get the original capabilities that map to a new consolidated capability.
    
    Args:
        new_capability: New consolidated capability name
        
    Returns:
        List of original capability names that map to this new capability
    """
    return REVERSE_CONSOLIDATION_MAP.get(new_capability, [new_capability])

def get_consolidation_info(capability: str) -> Dict[str, any]:
    """
    Get complete consolidation information for a capability.
    
    Args:
        capability: Capability name (old or new)
        
    Returns:
        Dict with consolidation metadata (priority, risk_level, dependencies, etc.)
    """
    if capability in CAPABILITY_CONSOLIDATION_MAP:
        return CAPABILITY_CONSOLIDATION_MAP[capability].copy()
    
    # Check if this is a new capability that has old mappings
    if capability in REVERSE_CONSOLIDATION_MAP:
        old_capabilities = REVERSE_CONSOLIDATION_MAP[capability]
        if old_capabilities:
            # Return info from the first old capability
            return CAPABILITY_CONSOLIDATION_MAP.get(old_capabilities[0], {})
    
    return {}

def get_capabilities_by_priority(priority: int) -> List[str]:
    """
    Get all capabilities with a specific consolidation priority.
    
    Args:
        priority: Priority level (0=already in target, 1=high, 2=medium, 3=low)
        
    Returns:
        List of capability names with the specified priority
    """
    capabilities = []
    for capability, info in CAPABILITY_CONSOLIDATION_MAP.items():
        if info.get("priority") == priority:
            capabilities.append(capability)
    return capabilities

def get_capabilities_by_risk(risk_level: str) -> List[str]:
    """
    Get all capabilities with a specific risk level.
    
    Args:
        risk_level: Risk level ("none", "low", "medium", "high")
        
    Returns:
        List of capability names with the specified risk level
    """
    capabilities = []
    for capability, info in CAPABILITY_CONSOLIDATION_MAP.items():
        if info.get("risk_level") == risk_level:
            capabilities.append(capability)
    return capabilities

def get_agent_capabilities(agent_name: str) -> Tuple[List[str], List[str]]:
    """
    Get all capabilities for an agent (both current and after consolidation).
    
    Args:
        agent_name: Agent name (e.g., "financial_analyst")
        
    Returns:
        Tuple of (current_capabilities, future_capabilities)
    """
    current = []
    future = []
    
    for capability, info in CAPABILITY_CONSOLIDATION_MAP.items():
        # Current capabilities
        if capability.startswith(f"{agent_name}."):
            current.append(capability)
        
        # Future capabilities (after consolidation)
        if info["target_agent"] == agent_name:
            future.append(info["target"])
    
    return current, future

def get_consolidation_stats() -> Dict[str, any]:
    """
    Get statistics about the consolidation mapping.
    
    Returns:
        Dict with consolidation statistics
    """
    total_capabilities = len(CAPABILITY_CONSOLIDATION_MAP)
    
    # Count by priority
    priority_counts = {}
    for i in range(4):
        priority_counts[i] = len(get_capabilities_by_priority(i))
    
    # Count by risk
    risk_counts = {
        "none": len(get_capabilities_by_risk("none")),
        "low": len(get_capabilities_by_risk("low")),
        "medium": len(get_capabilities_by_risk("medium")),
        "high": len(get_capabilities_by_risk("high")),
    }
    
    # Count by target agent
    agent_counts = {}
    for info in CAPABILITY_CONSOLIDATION_MAP.values():
        agent = info["target_agent"]
        agent_counts[agent] = agent_counts.get(agent, 0) + 1
    
    # Count consolidations needed
    consolidations_needed = sum(
        1 for info in CAPABILITY_CONSOLIDATION_MAP.values()
        if info["priority"] > 0
    )
    
    return {
        "total_capabilities": total_capabilities,
        "consolidations_needed": consolidations_needed,
        "priority_counts": priority_counts,
        "risk_counts": risk_counts,
        "agent_counts": agent_counts,
    }

def validate_consolidation_map() -> List[str]:
    """
    Validate the consolidation map for consistency issues.
    
    Returns:
        List of validation warnings/errors
    """
    issues = []
    
    # Check for duplicate target capabilities
    targets_seen = {}
    for old_cap, info in CAPABILITY_CONSOLIDATION_MAP.items():
        target = info["target"]
        if target in targets_seen and target != old_cap:
            # Multiple old capabilities mapping to same new capability is OK
            # but log it for awareness
            if info["priority"] > 0:  # Only if it's an actual consolidation
                logger.debug(f"Multiple capabilities map to {target}: {targets_seen[target]}, {old_cap}")
        targets_seen[target] = old_cap
    
    # Check for missing dependencies
    all_capabilities = set(CAPABILITY_CONSOLIDATION_MAP.keys())
    for cap, info in CAPABILITY_CONSOLIDATION_MAP.items():
        for dep in info.get("dependencies", []):
            if dep not in all_capabilities:
                issues.append(f"Capability '{cap}' has unknown dependency '{dep}'")
    
    # Check for circular dependencies
    def has_circular_dep(cap, visited=None):
        if visited is None:
            visited = set()
        if cap in visited:
            return True
        visited.add(cap)
        for dep in CAPABILITY_CONSOLIDATION_MAP.get(cap, {}).get("dependencies", []):
            if has_circular_dep(dep, visited.copy()):
                return True
        return False
    
    for cap in CAPABILITY_CONSOLIDATION_MAP:
        if has_circular_dep(cap):
            issues.append(f"Capability '{cap}' has circular dependencies")
    
    return issues

# Log consolidation stats on module import
stats = get_consolidation_stats()
logger.info(f"Capability consolidation map loaded: {stats['consolidations_needed']} consolidations needed")
logger.info(f"Target agent distribution: {stats['agent_counts']}")

# Validate the map and log any issues
validation_issues = validate_consolidation_map()
if validation_issues:
    for issue in validation_issues:
        logger.warning(f"Consolidation map validation issue: {issue}")