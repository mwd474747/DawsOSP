#!/usr/bin/env python3
"""Run the DawsOS backend API server."""
import uvicorn
import os

if __name__ == "__main__":
    # Ensure database URL is available
    if not os.environ.get('DATABASE_URL'):
        print("WARNING: DATABASE_URL not set, using Replit PostgreSQL")
    
    # Run the FastAPI application
    uvicorn.run(
        "app.api.executor:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )