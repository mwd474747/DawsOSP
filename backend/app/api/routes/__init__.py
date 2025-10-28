"""
DawsOS API Routes

Purpose: REST API route modules with JWT authentication
Updated: 2025-10-27
Priority: P0 (Phase 4 Task 1)

Authentication:
    All routes require JWT authentication via Authorization header:
    Authorization: Bearer <jwt_token>

Modules:
    - auth: Authentication and user management endpoints
    - metrics: Metrics retrieval endpoints
    - attribution: Currency attribution endpoints
    - portfolios: Portfolio CRUD endpoints (JWT + RBAC)
    - trades: Trade execution endpoints (JWT + RBAC)
    - corporate_actions: Corporate actions endpoints (JWT + RBAC)
    - alerts: Alert management endpoints (JWT + RBAC)
    - notifications: Notification management endpoints (JWT + RBAC)
    - macro: Macro regime and scenario analysis endpoints (JWT + RBAC)

Usage:
    from app.api.routes.auth import router as auth_router
    from app.api.routes.metrics import router as metrics_router
    from app.api.routes.macro import router as macro_router
    app.include_router(auth_router)
    app.include_router(metrics_router)
    app.include_router(macro_router)
"""

__all__ = ["auth"]
