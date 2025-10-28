"""
Portfolio Management API Routes

Purpose: CRUD operations for portfolios
Created: 2025-10-23 (Sprint 1 - UAT readiness)
Priority: P0 (UAT-001, UAT-002)

Endpoints:
    POST   /v1/portfolios              - Create new portfolio
    GET    /v1/portfolios              - List portfolios (RLS filtered)
    GET    /v1/portfolios/{id}         - Get single portfolio
    PATCH  /v1/portfolios/{id}         - Update portfolio
    DELETE /v1/portfolios/{id}         - Soft delete portfolio

UAT Coverage:
    - UAT-001: Create portfolio with valid user_id
    - UAT-002: Verify RLS policy isolates portfolios
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field

from app.db.connection import get_db_connection_with_rls
from app.middleware.auth_middleware import verify_token
from app.services.auth import get_auth_service

logger = logging.getLogger("DawsOS.API.Portfolios")

router = APIRouter(prefix="/v1/portfolios", tags=["portfolios"])


# ============================================================================
# Request/Response Models
# ============================================================================


class PortfolioCreate(BaseModel):
    """Portfolio creation request."""
    name: str = Field(..., min_length=1, max_length=255, description="Portfolio name")
    description: Optional[str] = Field(None, max_length=1000, description="Portfolio description")
    base_currency: str = Field(default="USD", pattern="^[A-Z]{3}$", description="ISO 4217 currency code")
    benchmark_id: Optional[str] = Field(None, description="Benchmark security ID")


class PortfolioUpdate(BaseModel):
    """Portfolio update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    benchmark_id: Optional[str] = None
    is_active: Optional[bool] = None


class PortfolioResponse(BaseModel):
    """Portfolio response model."""
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str]
    base_currency: str
    benchmark_id: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Dependency: Get User ID from JWT Claims
# ============================================================================


def get_user_id_from_claims(claims: dict) -> UUID:
    """
    Extract user_id from JWT claims and convert to UUID.

    Args:
        claims: JWT claims dict from verify_token dependency

    Returns:
        User UUID

    Raises:
        HTTPException: If user_id is invalid
    """
    user_id_str = claims.get("user_id")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT token missing user_id claim"
        )

    try:
        return UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id format in JWT token (must be UUID)"
        )


# ============================================================================
# Endpoints
# ============================================================================


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio: PortfolioCreate,
    claims: dict = Depends(verify_token)
) -> PortfolioResponse:
    """
    Create new portfolio.

    UAT Coverage: UAT-001

    Steps:
        1. Validate input
        2. Generate portfolio_id (UUID)
        3. Insert into portfolios table with RLS context
        4. Initialize Beancount ledger file (future: Phase 2B)

    Args:
        portfolio: Portfolio creation data
        claims: JWT claims (user_id, email, role)

    Returns:
        Created portfolio

    Raises:
        HTTPException: If creation fails
    """
    user_id = get_user_id_from_claims(claims)
    user_role = claims.get("role", "USER")
    
    # RBAC: Check permission to manage portfolios
    auth_service = get_auth_service()
    if not auth_service.check_permission(user_role, "manage_portfolios"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create portfolios"
        )
    
    portfolio_id = uuid4()

    logger.info(
        f"Creating portfolio: name={portfolio.name}, "
        f"user_id={user_id}, portfolio_id={portfolio_id}, role={user_role}"
    )

    try:
        # Use RLS-enabled connection
        async with get_db_connection_with_rls(str(user_id)) as conn:
            # Insert portfolio (RLS ensures user_id is set correctly)
            row = await conn.fetchrow(
                """
                INSERT INTO portfolios (
                    id, user_id, name, description, base_currency, benchmark_id
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, user_id, name, description, base_currency,
                          benchmark_id, is_active, created_at, updated_at
                """,
                portfolio_id,
                user_id,
                portfolio.name,
                portfolio.description,
                portfolio.base_currency,
                portfolio.benchmark_id,
            )

        logger.info(f"Portfolio created successfully: {portfolio_id}")

        return PortfolioResponse(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            description=row["description"],
            base_currency=row["base_currency"],
            benchmark_id=row["benchmark_id"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    except Exception as e:
        logger.error(f"Failed to create portfolio: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create portfolio: {str(e)}"
        )


@router.get("", response_model=List[PortfolioResponse])
async def list_portfolios(
    claims: dict = Depends(verify_token),
    is_active: Optional[bool] = None
) -> List[PortfolioResponse]:
    """
    List portfolios for current user.

    UAT Coverage: UAT-002 (RLS filtering)

    RLS ensures users only see their own portfolios.

    Args:
        claims: JWT claims (user_id, email, role)
        is_active: Optional filter for active portfolios

    Returns:
        List of portfolios (RLS filtered)
    """
    user_id = get_user_id_from_claims(claims)
    logger.info(f"Listing portfolios for user: {user_id}")

    try:
        # Use RLS-enabled connection (automatically filters by user_id)
        async with get_db_connection_with_rls(str(user_id)) as conn:
            if is_active is not None:
                rows = await conn.fetch(
                    """
                    SELECT id, user_id, name, description, base_currency,
                           benchmark_id, is_active, created_at, updated_at
                    FROM portfolios
                    WHERE is_active = $1
                    ORDER BY created_at DESC
                    """,
                    is_active
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, user_id, name, description, base_currency,
                           benchmark_id, is_active, created_at, updated_at
                    FROM portfolios
                    ORDER BY created_at DESC
                    """
                )

        portfolios = [
            PortfolioResponse(
                id=row["id"],
                user_id=row["user_id"],
                name=row["name"],
                description=row["description"],
                base_currency=row["base_currency"],
                benchmark_id=row["benchmark_id"],
                is_active=row["is_active"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

        logger.info(f"Found {len(portfolios)} portfolios for user {user_id}")
        return portfolios

    except Exception as e:
        logger.error(f"Failed to list portfolios: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list portfolios: {str(e)}"
        )


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: UUID,
    claims: dict = Depends(verify_token)
) -> PortfolioResponse:
    """
    Get single portfolio by ID.

    UAT Coverage: UAT-002 (RLS ensures user can only access own portfolios)

    Args:
        portfolio_id: Portfolio UUID
        claims: JWT claims (user_id, email, role)

    Returns:
        Portfolio details

    Raises:
        HTTPException: If portfolio not found or access denied (RLS)
    """
    user_id = get_user_id_from_claims(claims)
    logger.info(f"Getting portfolio: {portfolio_id} for user: {user_id}")

    try:
        # Use RLS-enabled connection
        async with get_db_connection_with_rls(str(user_id)) as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, name, description, base_currency,
                       benchmark_id, is_active, created_at, updated_at
                FROM portfolios
                WHERE id = $1
                """,
                portfolio_id
            )

        if not row:
            # RLS filtered it out (user doesn't own it) or doesn't exist
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found or access denied"
            )

        return PortfolioResponse(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            description=row["description"],
            base_currency=row["base_currency"],
            benchmark_id=row["benchmark_id"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get portfolio: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get portfolio: {str(e)}"
        )


@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: UUID,
    updates: PortfolioUpdate,
    claims: dict = Depends(verify_token)
) -> PortfolioResponse:
    """
    Update portfolio.

    Args:
        portfolio_id: Portfolio UUID
        updates: Fields to update
        claims: JWT claims (user_id, email, role)

    Returns:
        Updated portfolio

    Raises:
        HTTPException: If portfolio not found or access denied
    """
    user_id = get_user_id_from_claims(claims)
    user_role = claims.get("role", "USER")
    
    # RBAC: Check permission to manage portfolios
    auth_service = get_auth_service()
    if not auth_service.check_permission(user_role, "manage_portfolios"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update portfolios"
        )
    
    logger.info(f"Updating portfolio: {portfolio_id} for user: {user_id}, role: {user_role}")

    # Build dynamic UPDATE query based on provided fields
    update_fields = []
    values = []
    param_idx = 1

    if updates.name is not None:
        update_fields.append(f"name = ${param_idx}")
        values.append(updates.name)
        param_idx += 1

    if updates.description is not None:
        update_fields.append(f"description = ${param_idx}")
        values.append(updates.description)
        param_idx += 1

    if updates.benchmark_id is not None:
        update_fields.append(f"benchmark_id = ${param_idx}")
        values.append(updates.benchmark_id)
        param_idx += 1

    if updates.is_active is not None:
        update_fields.append(f"is_active = ${param_idx}")
        values.append(updates.is_active)
        param_idx += 1

    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )

    # Add portfolio_id to values
    values.append(portfolio_id)

    query = f"""
        UPDATE portfolios
        SET {', '.join(update_fields)}
        WHERE id = ${param_idx}
        RETURNING id, user_id, name, description, base_currency,
                  benchmark_id, is_active, created_at, updated_at
    """

    try:
        async with get_db_connection_with_rls(str(user_id)) as conn:
            row = await conn.fetchrow(query, *values)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found or access denied"
            )

        logger.info(f"Portfolio updated successfully: {portfolio_id}")

        return PortfolioResponse(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            description=row["description"],
            base_currency=row["base_currency"],
            benchmark_id=row["benchmark_id"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update portfolio: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update portfolio: {str(e)}"
        )


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: UUID,
    claims: dict = Depends(verify_token)
) -> None:
    """
    Soft delete portfolio (set is_active = false).

    Args:
        portfolio_id: Portfolio UUID
        claims: JWT claims (user_id, email, role)

    Raises:
        HTTPException: If portfolio not found or access denied
    """
    user_id = get_user_id_from_claims(claims)
    user_role = claims.get("role", "USER")
    
    # RBAC: Check permission to manage portfolios
    auth_service = get_auth_service()
    if not auth_service.check_permission(user_role, "manage_portfolios"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete portfolios"
        )
    
    logger.info(f"Deleting portfolio: {portfolio_id} for user: {user_id}, role: {user_role}")

    try:
        async with get_db_connection_with_rls(str(user_id)) as conn:
            result = await conn.execute(
                """
                UPDATE portfolios
                SET is_active = false
                WHERE id = $1
                """,
                portfolio_id
            )

        # Check if any row was updated
        if result == "UPDATE 0":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio {portfolio_id} not found or access denied"
            )

        logger.info(f"Portfolio deleted successfully: {portfolio_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete portfolio: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete portfolio: {str(e)}"
        )
