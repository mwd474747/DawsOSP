"""
DawsOS Client Factory

Purpose: Centralized client initialization to eliminate duplication
Updated: 2025-10-23
Priority: P0 (DRY principle)

This module provides a single source of truth for:
- API client initialization
- Environment configuration
- Mock vs real mode selection

Usage in screens:
    from frontend.ui.client_factory import get_client

    client = get_client()
    result = client.execute("portfolio_overview", ...)

Benefits:
- Eliminates code duplication across 5 screen files
- Single place to change API configuration
- Consistent behavior across all screens
"""

import os
import logging
from typing import Union

from frontend.ui.api_client import DawsOSClient, MockDawsOSClient

logger = logging.getLogger("DawsOS.ClientFactory")

# ============================================================================
# Configuration (Single Source of Truth)
# ============================================================================

# Use real API by default (set USE_MOCK_CLIENT=true for mock data)
USE_MOCK_CLIENT = os.getenv("USE_MOCK_CLIENT", "false").lower() == "true"

# API base URL
API_BASE_URL = os.getenv("EXECUTOR_API_URL", "http://localhost:8000")

# Log configuration on module import
logger.info(
    f"Client factory initialized: "
    f"mock_mode={USE_MOCK_CLIENT}, "
    f"api_url={API_BASE_URL}"
)


# ============================================================================
# Client Factory
# ============================================================================


def get_client() -> Union[DawsOSClient, MockDawsOSClient]:
    """
    Get API client instance (real or mock based on configuration).

    Returns:
        DawsOSClient: Real API client (connects to Executor API)
        MockDawsOSClient: Mock client (returns stub data)

    Environment Variables:
        USE_MOCK_CLIENT: Set to "true" for mock mode (default: false)
        EXECUTOR_API_URL: API base URL (default: http://localhost:8000)

    Examples:
        >>> client = get_client()
        >>> result = client.execute("portfolio_overview", inputs={...})
    """
    if USE_MOCK_CLIENT:
        logger.debug("Creating MockDawsOSClient")
        return MockDawsOSClient(base_url=API_BASE_URL)
    else:
        logger.debug("Creating DawsOSClient")
        return DawsOSClient(base_url=API_BASE_URL)


def is_mock_mode() -> bool:
    """
    Check if running in mock mode.

    Returns:
        bool: True if mock mode, False if real API mode
    """
    return USE_MOCK_CLIENT


def get_api_url() -> str:
    """
    Get configured API base URL.

    Returns:
        str: API base URL
    """
    return API_BASE_URL
