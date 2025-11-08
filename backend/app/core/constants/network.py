"""
Network Configuration Constants

Domain: Server ports, host bindings
Sources: Standard port assignments, application architecture
Identified by: Analysis of run_backend.py, combined_server.py + Constants audit 2025-11-07

This module contains constants used for:
- Server port numbers
- Host bindings

Cleanup History:
- 2025-11-07: Removed 9 unused constants (75% waste)
  - Removed: POSTGRES_DEFAULT_PORT, REDIS_DEFAULT_PORT (unused)
  - Removed: All connection pool constants (DEFAULT_DB_POOL_*) (unused)
  - Removed: All timeout constants except DEFAULT_CONNECTION_TIMEOUT
  - Removed: LOCALHOST (unused)
  - Removed: DEFAULT_DB_QUERY_TIMEOUT, LONG_RUNNING_QUERY_TIMEOUT (unused)
  - Note: DEFAULT_CONNECTION_TIMEOUT kept as canonical (was duplicate in integration.py)
"""

# =============================================================================
# SERVER PORTS
# =============================================================================

# HTTP/API server ports
DEFAULT_API_PORT = 8000  # FastAPI/Uvicorn default port
DEFAULT_COMBINED_SERVER_PORT = 5000  # Combined frontend+backend server

# =============================================================================
# CONNECTION TIMEOUTS
# =============================================================================

# Connection establishment timeouts
DEFAULT_CONNECTION_TIMEOUT = 10  # Time to establish connection (canonical source)

# =============================================================================
# HOST CONFIGURATION
# =============================================================================

# Host bindings
ALL_INTERFACES = "0.0.0.0"  # Listen on all network interfaces

# =============================================================================
# MODULE METADATA
# =============================================================================

__all__ = [
    # Server ports
    "DEFAULT_API_PORT",
    "DEFAULT_COMBINED_SERVER_PORT",
    # Timeouts
    "DEFAULT_CONNECTION_TIMEOUT",
    # Hosts
    "ALL_INTERFACES",
]
