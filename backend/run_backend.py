#!/usr/bin/env python3
"""Run the DawsOS backend API server."""
import uvicorn
import os
from app.core.constants.network import DEFAULT_API_PORT, ALL_INTERFACES

if __name__ == "__main__":
    # Ensure database URL is available
    if not os.environ.get('DATABASE_URL'):
        print("WARNING: DATABASE_URL not set, using Replit PostgreSQL")
    
    # Run the FastAPI application
    uvicorn.run(
        "app.api.executor:app",
        host=ALL_INTERFACES,
        port=DEFAULT_API_PORT,
        reload=True,
        log_level="info"
    )