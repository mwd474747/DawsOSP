"""
Service Initializer

Purpose: Initialize all services in dependency order using DI container
Updated: 2025-01-15
Priority: P0 (Critical for Phase 2)

Features:
    - Service registration in dependency order
    - Automatic dependency resolution
    - Initialization sequence management

Usage:
    container = get_container()
    initialize_services(container, db_pool, fred_provider, news_provider)
"""

import logging
import os
from typing import Optional, Dict, Any
import asyncpg

from app.core.di_container import DIContainer, get_container
from app.db.connection import get_db_pool

logger = logging.getLogger(__name__)


def initialize_services(
    container: Optional[DIContainer] = None,
    db_pool: Optional[asyncpg.Pool] = None,
    fred_provider: Optional[Any] = None,
    news_provider: Optional[Any] = None,
) -> DIContainer:
    """
    Initialize all services in dependency order.
    
    Args:
        container: DI container (optional, creates new if not provided)
        db_pool: Database connection pool (optional, uses get_db_pool() if not provided)
        fred_provider: FRED API provider (optional, creates if not provided)
        news_provider: News API provider (optional, creates if not provided)
    
    Returns:
        Initialized DI container
    """
    if container is None:
        container = get_container()
    
    # Step 1: Register infrastructure services
    if db_pool is None:
        try:
            db_pool = get_db_pool()
        except RuntimeError:
            logger.warning("Database pool not initialized, some services may not work")
            db_pool = None
    
    container.register("db_pool", db_pool)
    
    # Register FRED provider if not provided
    if fred_provider is None:
        from app.integrations.fred_provider import FREDProvider
        api_key = os.getenv("FRED_API_KEY")
        if api_key:
            fred_provider = FREDProvider(api_key=api_key)
            container.register("fred_provider", fred_provider)
        else:
            logger.warning("FRED_API_KEY not set, macro services may not work")
    
    # Register News provider if not provided
    if news_provider is None:
        from app.integrations.news_provider import NewsAPIProvider
        api_key = os.getenv("NEWSAPI_KEY")
        if api_key:
            tier = os.getenv("NEWSAPI_TIER", "dev")
            news_provider = NewsAPIProvider(api_key=api_key, tier=tier)
            container.register("news_provider", news_provider)
        else:
            logger.warning("NEWSAPI_KEY not set, news services may not work")
    
    # Step 2: Register core services (no dependencies)
    from app.services.fred_transformation import FREDTransformationService
    from app.services.indicator_config import IndicatorConfigManager
    from app.services.rights_registry import RightsRegistry
    from app.services.alert_delivery import AlertDeliveryService
    from app.services.playbooks import PlaybookGenerator
    from app.services.auth import AuthService
    
    container.register_service("fred_transformation", FREDTransformationService)
    container.register_service("indicator_config", IndicatorConfigManager)
    container.register_service("rights_registry", RightsRegistry)
    container.register_service("alert_delivery", AlertDeliveryService)
    container.register_service("playbooks", PlaybookGenerator)
    container.register_service("auth", AuthService)
    
    # Step 3: Register core services (infrastructure dependencies only)
    from app.services.pricing import PricingService
    from app.services.ratings import RatingsService
    from app.services.optimizer import OptimizerService
    from app.services.notifications import NotificationService
    from app.services.audit import AuditService
    
    container.register_service("pricing", PricingService, db_pool="db_pool")
    container.register_service("ratings", RatingsService, db_pool="db_pool")
    container.register_service("optimizer", OptimizerService, db_pool="db_pool")
    container.register_service("notifications", NotificationService, db_pool="db_pool")
    container.register_service("audit", AuditService, db_pool="db_pool")
    
    # Step 4: Register core services (service dependencies)
    from app.services.macro import MacroService
    from app.services.scenarios import ScenarioService
    from app.services.metrics import PerformanceCalculator
    from app.services.currency_attribution import CurrencyAttributor
    from app.services.risk_metrics import RiskMetricsService
    from app.services.factor_analysis import FactorAnalysisService
    from app.services.benchmarks import BenchmarkService
    from app.services.alerts import AlertService
    from app.services.cycles import CyclesService
    from app.services.reports import ReportService
    
    container.register_service(
        "macro",
        MacroService,
        fred_client="fred_provider",
        db_pool="db_pool",
    )
    container.register_service(
        "scenarios",
        ScenarioService,
        db_pool="db_pool",
        pricing_service="pricing",
    )
    container.register_service("metrics", PerformanceCalculator, pricing_service="pricing")
    container.register_service("currency_attribution", CurrencyAttributor, pricing_service="pricing")
    container.register_service("risk_metrics", RiskMetricsService, pricing_service="pricing")
    container.register_service("factor_analysis", FactorAnalysisService, pricing_service="pricing")
    container.register_service("benchmarks", BenchmarkService, pricing_service="pricing")
    container.register_service(
        "alerts",
        AlertService,
        db_pool="db_pool",
        notifications_service="notifications",
        alert_delivery_service="alert_delivery",
    )
    container.register_service("cycles", CyclesService, indicator_config="indicator_config")
    container.register_service("reports", ReportService, rights_registry="rights_registry")
    
    # Step 5: Register composite services
    from app.services.macro_aware_scenarios import MacroAwareScenarioService
    
    container.register_service(
        "macro_aware_scenarios",
        MacroAwareScenarioService,
        scenarios_service="scenarios",
        macro_service="macro",
        db_pool="db_pool",
    )
    
    # Step 6: Register agents
    # Note: Agents currently create their own services in __init__
    # For now, we'll pass services through the services dict
    # TODO: Update agents to accept services as constructor parameters
    
    from app.agents.macro_hound import MacroHound
    from app.agents.financial_analyst import FinancialAnalyst
    from app.agents.data_harvester import DataHarvester
    from app.agents.claude_agent import ClaudeAgent
    
    def create_macro_hound() -> MacroHound:
        """Create MacroHound with services from container."""
        services = {
            "db": container.resolve("db_pool"),
            "redis": None,
            # Pass resolved services for agents that need them
            "macro_service": container.resolve("macro"),
            "scenarios_service": container.resolve("scenarios"),
            "macro_aware_service": container.resolve("macro_aware_scenarios"),
            "alerts_service": container.resolve("alerts"),
            "cycles_service": container.resolve("cycles"),
            "playbooks_service": container.resolve("playbooks"),
        }
        return MacroHound("macro_hound", services)
    
    def create_financial_analyst() -> FinancialAnalyst:
        """Create FinancialAnalyst with services from container."""
        services = {
            "db": container.resolve("db_pool"),
            "redis": None,
            # Pass resolved services for agents that need them
            "pricing_service": container.resolve("pricing"),
            "optimizer_service": container.resolve("optimizer"),
            "ratings_service": container.resolve("ratings"),
            "currency_attribution_service": container.resolve("currency_attribution"),
        }
        return FinancialAnalyst("financial_analyst", services)
    
    def create_data_harvester() -> DataHarvester:
        """Create DataHarvester with services from container."""
        services = {
            "db": container.resolve("db_pool"),
            "redis": None,
        }
        return DataHarvester("data_harvester", services)
    
    def create_claude_agent() -> ClaudeAgent:
        """Create ClaudeAgent with services from container."""
        services = {
            "db": container.resolve("db_pool"),
            "redis": None,
        }
        return ClaudeAgent("claude", services)
    
    # Register agents with factory functions (no dependencies since they resolve internally)
    container.register_service("macro_hound", MacroHound, factory=create_macro_hound, dependencies={})
    container.register_service("financial_analyst", FinancialAnalyst, factory=create_financial_analyst, dependencies={})
    container.register_service("data_harvester", DataHarvester, factory=create_data_harvester, dependencies={})
    container.register_service("claude_agent", ClaudeAgent, factory=create_claude_agent, dependencies={})
    
    # Step 7: Register runtime
    from app.core.agent_runtime import AgentRuntime
    from app.core.pattern_orchestrator import PatternOrchestrator
    
    # Agent Runtime needs all agents
    # We'll register it with a factory function that resolves agents
    def create_agent_runtime() -> AgentRuntime:
        services = {
            "db": container.resolve("db_pool"),
            "redis": None,  # TODO: Wire real Redis when needed
        }
        runtime = AgentRuntime(services)
        
        # Register all agents
        runtime.register_agent(container.resolve("financial_analyst"))
        runtime.register_agent(container.resolve("macro_hound"))
        runtime.register_agent(container.resolve("data_harvester"))
        runtime.register_agent(container.resolve("claude_agent"))
        
        return runtime
    
    # Register runtime with factory function (no dependencies since it resolves internally)
    container.register_service("agent_runtime", AgentRuntime, factory=create_agent_runtime, dependencies={})
    
    # Pattern Orchestrator needs agent runtime
    def create_pattern_orchestrator() -> PatternOrchestrator:
        runtime = container.resolve("agent_runtime")
        return PatternOrchestrator(runtime)
    
    container.register_service("pattern_orchestrator", PatternOrchestrator, factory=create_pattern_orchestrator, dependencies={})
    
    # Initialize all services in dependency order
    dependency_order = [
        # Infrastructure
        "db_pool",
        "fred_provider",
        "news_provider",
        # Core services (no dependencies)
        "fred_transformation",
        "indicator_config",
        "rights_registry",
        "alert_delivery",
        "playbooks",
        "auth",
        # Core services (infrastructure dependencies)
        "pricing",
        "ratings",
        "optimizer",
        "notifications",
        "audit",
        # Core services (service dependencies)
        "macro",
        "scenarios",
        "metrics",
        "currency_attribution",
        "risk_metrics",
        "factor_analysis",
        "benchmarks",
        "alerts",
        "cycles",
        "reports",
        # Composite services
        "macro_aware_scenarios",
        # Agents
        "macro_hound",
        "financial_analyst",
        "data_harvester",
        "claude_agent",
        # Runtime
        "agent_runtime",
        "pattern_orchestrator",
    ]
    
    container.initialize_services(dependency_order)
    
    logger.info(f"Initialized {len(container._instances)} services in dependency order")
    
    return container

