"""
DawsOS API Routes

Purpose: REST API route modules
Updated: 2025-10-27
Priority: P0 (Phase 4 Task 1)

Modules:
    - auth: Authentication and user management endpoints (NEW)
    - metrics: Metrics retrieval endpoints
    - attribution: Currency attribution endpoints
    - portfolios: Portfolio CRUD endpoints
    - trades: Trade execution endpoints
    - corporate_actions: Corporate actions endpoints
    - alerts: Alert management endpoints
    - notifications: Notification management endpoints
    - macro: Macro regime and scenario analysis endpoints

Usage:
    from app.api.routes.auth import router as auth_router
    from app.api.routes.metrics import router as metrics_router
    from app.api.routes.macro import router as macro_router
    app.include_router(auth_router)
    app.include_router(metrics_router)
    app.include_router(macro_router)
"""

__all__ = ["auth"]
