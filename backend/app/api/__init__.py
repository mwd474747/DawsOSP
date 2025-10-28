"""
DawsOS API Module

Purpose: REST API endpoints for DawsOS
Updated: 2025-10-22
Priority: P0 (Phase 4 Task 1)

Modules:
    - executor: Pattern execution endpoint
    - health: Health check endpoints
    - routes/metrics: Metrics retrieval endpoints
    - routes/attribution: Currency attribution endpoints
    - schemas/metrics: Pydantic response models

Usage:
    from backend.app.api import register_routes
    register_routes(app)
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI


def register_routes(app: "FastAPI") -> None:
    """
    Register all API routes with the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    from .health import router as health_router
    from .executor import router as executor_router

    # Register routers
    app.include_router(health_router)
    app.include_router(executor_router)

    # Register Phase 4 routers (metrics, attribution)
    try:
        from .routes.metrics import router as metrics_router
        from .routes.attribution import router as attribution_router

        app.include_router(metrics_router)
        app.include_router(attribution_router)
    except ImportError:
        # Routes not yet implemented (Phase 4)
        pass

    # Register Sprint 1 routers (UAT readiness)
    try:
        from .routes.portfolios import router as portfolios_router
        from .routes.trades import router as trades_router
        app.include_router(portfolios_router)
        app.include_router(trades_router)
    except ImportError:
        # Routes not yet implemented
        pass

    # Register macro/scenario/risk routers
    try:
        from .routes.macro import router as macro_router
        from .routes.alerts import router as alerts_router
        from .routes.notifications import router as notifications_router
        from .routes.corporate_actions import router as corporate_actions_router

        app.include_router(macro_router)
        app.include_router(alerts_router)
        app.include_router(notifications_router)
        app.include_router(corporate_actions_router)
    except ImportError:
        # Routes not yet implemented
        pass


__all__ = ["register_routes"]
