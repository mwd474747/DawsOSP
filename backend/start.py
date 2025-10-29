#!/usr/bin/env python3
"""
Unified Backend Startup Script
Purpose: Single entry point with comprehensive validation

This replaces all previous startup mechanisms and ensures:
- Consistent PYTHONPATH configuration
- Environment validation
- Proper module imports
- Standardized startup process
"""
import sys
import os
from pathlib import Path

# Set PYTHONPATH before any imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ["PYTHONPATH"] = str(PROJECT_ROOT)

# Validate environment before importing
if not (PROJECT_ROOT / "backend" / "app" / "api" / "executor.py").exists():
    print(f"❌ Error: Must run from project root. Current: {PROJECT_ROOT}")
    sys.exit(1)

# Validate virtual environment
if not (PROJECT_ROOT / "venv").exists():
    print(f"❌ Error: Virtual environment not found at {PROJECT_ROOT / 'venv'}")
    sys.exit(1)

# Now import and run
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting DawsOS Backend API...")
    print(f"📁 Project root: {PROJECT_ROOT}")
    print(f"🐍 Python path: {PROJECT_ROOT}")
    print("")
    
    uvicorn.run(
        "backend.app.api.executor:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False  # No reload - prevents module reloading issues
    )
