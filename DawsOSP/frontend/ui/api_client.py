"""
DawsOS API Client

Purpose: HTTP client for calling DawsOS Executor API
Updated: 2025-10-22 (Phase 4 Task 3)
Priority: P0 (Critical for UI)

Features:
    - Call /v1/execute endpoint
    - Handle authentication (stub for now)
    - Parse responses with provenance metadata
    - Error handling and retries

Usage:
    from ui.api_client import DawsOSClient

    client = DawsOSClient(base_url="http://localhost:8000")
    result = client.execute("portfolio_overview", {"portfolio_id": "123"})
"""

import logging
import os
from datetime import date
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests

logger = logging.getLogger("DawsOS.APIClient")


class DawsOSClient:
    """
    HTTP client for DawsOS Executor API.

    Provides convenience methods for calling the /v1/execute endpoint
    with proper authentication and error handling.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize API client.

        Args:
            base_url: Base URL for API (default: from EXECUTOR_API_URL env or localhost:8000)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv("EXECUTOR_API_URL", "http://localhost:8000")
        self.timeout = timeout

        # Remove trailing slash
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

        logger.info(f"DawsOSClient initialized with base_url={self.base_url}")

    def execute(
        self,
        pattern_id: str,
        inputs: Dict[str, Any] = None,
        portfolio_id: Optional[str] = None,
        asof_date: Optional[date] = None,
        require_fresh: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute a pattern via /v1/execute endpoint.

        Args:
            pattern_id: Pattern identifier (e.g., "portfolio_overview")
            inputs: Pattern inputs (optional)
            portfolio_id: Portfolio ID (optional)
            asof_date: As-of date (optional, defaults to today)
            require_fresh: Require fresh pricing pack (default: True)

        Returns:
            Dict with:
            {
                "data": {...},  # Pattern execution result
                "metadata": {
                    "pattern_id": "portfolio_overview",
                    "request_id": "req-123",
                    "pricing_pack_id": "20251022_v1",
                    "ledger_commit_hash": "abc123",
                    "execution_time_ms": 245.2,
                },
                "trace": {...}  # Execution trace (for explain drawer)
            }

        Raises:
            requests.HTTPError: If API returns error status
            requests.Timeout: If request times out
            requests.RequestException: For other request errors
        """
        url = urljoin(self.base_url, "/v1/execute")

        # Build request payload
        payload = {
            "pattern_id": pattern_id,
            "inputs": inputs or {},
            "require_fresh": require_fresh,
        }

        if portfolio_id:
            payload["portfolio_id"] = portfolio_id

        if asof_date:
            payload["asof_date"] = asof_date.isoformat() if isinstance(asof_date, date) else asof_date

        logger.info(f"Executing pattern: {pattern_id}, portfolio_id={portfolio_id}")

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    # TODO: Add authentication headers when auth is implemented
                    # "Authorization": f"Bearer {self.api_token}",
                },
            )

            # Raise for HTTP errors (4xx, 5xx)
            response.raise_for_status()

            result = response.json()

            logger.info(
                f"Pattern executed successfully: {pattern_id}, "
                f"request_id={result.get('request_id', 'unknown')}"
            )

            return result

        except requests.Timeout:
            logger.error(f"Request timeout after {self.timeout}s for pattern {pattern_id}")
            raise

        except requests.HTTPError as e:
            # Parse error detail from response if available
            try:
                error_detail = e.response.json()
                logger.error(
                    f"API error for pattern {pattern_id}: "
                    f"status={e.response.status_code}, detail={error_detail}"
                )
            except Exception:
                logger.error(
                    f"API error for pattern {pattern_id}: status={e.response.status_code}"
                )
            raise

        except requests.RequestException as e:
            logger.error(f"Request error for pattern {pattern_id}: {e}")
            raise

    def get_portfolio_metrics(
        self,
        portfolio_id: str,
        asof_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get portfolio metrics (convenience method).

        Args:
            portfolio_id: Portfolio ID
            asof_date: As-of date (optional, defaults to latest)

        Returns:
            Dict with metrics
        """
        url = urljoin(self.base_url, f"/api/v1/portfolios/{portfolio_id}/metrics")

        params = {}
        if asof_date:
            params["asof_date"] = asof_date.isoformat() if isinstance(asof_date, date) else asof_date

        logger.info(f"Fetching metrics for portfolio {portfolio_id}")

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Metrics fetched successfully for portfolio {portfolio_id}")

            return result

        except requests.RequestException as e:
            logger.error(f"Error fetching metrics for portfolio {portfolio_id}: {e}")
            raise

    def get_currency_attribution(
        self,
        portfolio_id: str,
        asof_date: Optional[date] = None,
        base_currency: str = "CAD",
    ) -> Dict[str, Any]:
        """
        Get currency attribution (convenience method).

        Args:
            portfolio_id: Portfolio ID
            asof_date: As-of date (optional, defaults to latest)
            base_currency: Base currency (default: CAD)

        Returns:
            Dict with attribution breakdown
        """
        url = urljoin(self.base_url, f"/api/v1/portfolios/{portfolio_id}/attribution/currency")

        params = {"base_currency": base_currency}
        if asof_date:
            params["asof_date"] = asof_date.isoformat() if isinstance(asof_date, date) else asof_date

        logger.info(f"Fetching currency attribution for portfolio {portfolio_id}")

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Attribution fetched successfully for portfolio {portfolio_id}")

            return result

        except requests.RequestException as e:
            logger.error(f"Error fetching attribution for portfolio {portfolio_id}: {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """
        Check API health.

        Returns:
            Dict with health status
        """
        url = urljoin(self.base_url, "/health")

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}


# ============================================================================
# Mock Client (for development/testing without API)
# ============================================================================


class MockDawsOSClient(DawsOSClient):
    """
    Mock client that returns fake data without calling real API.

    Useful for UI development and testing when API is not available.
    """

    def execute(
        self,
        pattern_id: str,
        inputs: Dict[str, Any] = None,
        portfolio_id: Optional[str] = None,
        asof_date: Optional[date] = None,
        require_fresh: bool = True,
    ) -> Dict[str, Any]:
        """Return mock execution result."""
        logger.info(f"[MOCK] Executing pattern: {pattern_id}")

        return {
            "data": {
                "portfolio_name": "Test Portfolio",
                "total_value": 1245678.90,
                "currency": "CAD",
            },
            "metadata": {
                "pattern_id": pattern_id,
                "request_id": "mock-req-123",
                "pricing_pack_id": "20251022_v1",
                "ledger_commit_hash": "abc123def",
                "execution_time_ms": 125.5,
            },
            "trace": {
                "steps": [
                    {"name": "fetch_metrics", "duration_ms": 45.2},
                    {"name": "compute_attribution", "duration_ms": 80.3},
                ],
            },
        }

    def get_portfolio_metrics(
        self,
        portfolio_id: str,
        asof_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Return mock metrics."""
        logger.info(f"[MOCK] Fetching metrics for portfolio {portfolio_id}")

        return {
            "portfolio_id": portfolio_id,
            "asof_date": "2025-10-22",
            "pricing_pack_id": "20251022_v1",
            "twr_1d": 0.0125,
            "twr_mtd": 0.0234,
            "twr_ytd": 0.0850,
            "twr_1y": 0.1240,
            "sharpe_30d": 1.45,
            "sharpe_1y": 1.28,
            "volatility_30d": 0.1520,
            "max_drawdown_1y": -0.1234,
        }

    def get_currency_attribution(
        self,
        portfolio_id: str,
        asof_date: Optional[date] = None,
        base_currency: str = "CAD",
    ) -> Dict[str, Any]:
        """Return mock attribution."""
        logger.info(f"[MOCK] Fetching attribution for portfolio {portfolio_id}")

        return {
            "portfolio_id": portfolio_id,
            "asof_date": "2025-10-22",
            "pricing_pack_id": "20251022_v1",
            "base_currency": base_currency,
            "local_return": 0.0850,
            "fx_return": -0.0120,
            "interaction_return": -0.0010,
            "total_return": 0.0720,
            "error_bps": 0.05,
        }
