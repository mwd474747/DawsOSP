"""
Network Configuration Constants

Domain: Server ports, connection pools, timeouts
Sources: Standard port assignments, application architecture
Identified by: Analysis of run_backend.py, combined_server.py, connection configs

This module contains constants used for:
- Server port numbers
- Database connection settings
- Network timeouts
- Connection pool sizes
"""

# =============================================================================
# SERVER PORTS
# =============================================================================

# HTTP/API server ports
DEFAULT_API_PORT = 8000  # FastAPI/Uvicorn default port
DEFAULT_COMBINED_SERVER_PORT = 5000  # Combined frontend+backend server

# Common service ports (for reference)
POSTGRES_DEFAULT_PORT = 5432  # PostgreSQL database
REDIS_DEFAULT_PORT = 6379  # Redis cache

# =============================================================================
# DATABASE CONNECTION POOLS
# =============================================================================

# Connection pool sizes
DEFAULT_DB_POOL_MIN_SIZE = 2  # Minimum connections in pool
DEFAULT_DB_POOL_MAX_SIZE = 10  # Maximum connections in pool

# Connection pool timeouts (seconds)
DEFAULT_DB_POOL_TIMEOUT = 30  # Timeout waiting for connection from pool

# =============================================================================
# NETWORK TIMEOUTS
# =============================================================================

# Database query timeouts (seconds)
DEFAULT_DB_QUERY_TIMEOUT = 30  # General query timeout
LONG_RUNNING_QUERY_TIMEOUT = 60  # For complex aggregations

# Connection establishment timeouts
DEFAULT_CONNECTION_TIMEOUT = 10  # Time to establish connection

# =============================================================================
# HOST CONFIGURATION
# =============================================================================

# Host bindings
LOCALHOST = "127.0.0.1"
ALL_INTERFACES = "0.0.0.0"  # Listen on all network interfaces

# =============================================================================
# MODULE METADATA
# =============================================================================

__all__ = [
    # Server ports
    "DEFAULT_API_PORT",
    "DEFAULT_COMBINED_SERVER_PORT",
    "POSTGRES_DEFAULT_PORT",
    "REDIS_DEFAULT_PORT",
    # Connection pools
    "DEFAULT_DB_POOL_MIN_SIZE",
    "DEFAULT_DB_POOL_MAX_SIZE",
    "DEFAULT_DB_POOL_TIMEOUT",
    # Timeouts
    "DEFAULT_DB_QUERY_TIMEOUT",
    "LONG_RUNNING_QUERY_TIMEOUT",
    "DEFAULT_CONNECTION_TIMEOUT",
    # Hosts
    "LOCALHOST",
    "ALL_INTERFACES",
]
