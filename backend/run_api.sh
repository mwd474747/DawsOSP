#!/bin/bash

# DawsOS Backend API Launcher
# Purpose: Start the Executor API on port 8000
# Updated: 2025-11-02
#
# NOTE: This script is OPTIONAL for Replit deployment.
# On Replit, use `python combined_server.py` directly.
# This script is for local development with Docker.

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DawsOS Executor API Launcher${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if we're in the correct directory
if [ ! -f "backend/app/api/executor.py" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    echo "Current directory: $(pwd)"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not found at ./venv${NC}"
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if required packages are installed
echo -e "${GREEN}Checking dependencies...${NC}"
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    pip install -r backend/requirements.txt
fi

# Check if database is running
echo -e "${GREEN}Checking database connection...${NC}"
if ! docker ps --format '{{.Names}}' | grep -q '^dawsos-postgres$' && \
   ! docker ps --format '{{.Names}}' | grep -q '^dawsos-dev-postgres$'; then
    echo -e "${YELLOW}Warning: PostgreSQL container not running${NC}"
    echo "Starting Docker services..."

    if [ -f "docker-compose.simple.yml" ]; then
        docker-compose -f docker-compose.simple.yml up -d
        echo "Waiting for database to be ready..."
        sleep 5
    else
        echo -e "${RED}Error: docker-compose.simple.yml not found${NC}"
        echo "Please start the database manually:"
        echo "  docker-compose -f docker-compose.simple.yml up -d"
        exit 1
    fi
fi

# Set environment variables
echo -e "${GREEN}Setting environment variables...${NC}"

# Load .env file if it exists (contains API keys)
if [ -f ".env" ]; then
    echo -e "${GREEN}Loading API keys from .env file...${NC}"
    set -a  # Automatically export all variables
    source .env
    set +a
else
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "API providers will run in stub mode (no real data)"
    echo "To enable real data, create .env file:"
    echo "  cp .env.example .env"
    echo "  # Edit .env and add your API keys"
    echo ""
fi

# Load database config (can override .env)
if [ -f ".env.database" ]; then
    source .env.database
    export DATABASE_URL
else
    # Use default if not in .env or .env.database
    if [ -z "$DATABASE_URL" ]; then
        export DATABASE_URL="postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos"
    fi
fi

# Executor API URL (for self-reference)
export EXECUTOR_API_URL="${EXECUTOR_API_URL:-http://localhost:8000}"

# CORS origins (allow frontend on 8501)
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:8501,http://127.0.0.1:8501}"

# Environment
export ENVIRONMENT="${ENVIRONMENT:-development}"

echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  Database URL: ${DATABASE_URL}"
echo "  API URL: ${EXECUTOR_API_URL}"
echo "  CORS Origins: ${CORS_ORIGINS}"
echo "  Environment: ${ENVIRONMENT}"

# Show API provider status (without exposing keys)
echo ""
echo -e "${GREEN}API Provider Status:${NC}"
if [ -n "$FMP_API_KEY" ]; then
    echo "  FMP (Fundamentals): ✅ Configured"
else
    echo "  FMP (Fundamentals): ⚠️  Not configured (stub mode)"
fi

if [ -n "$POLYGON_API_KEY" ]; then
    echo "  Polygon (Prices): ✅ Configured"
else
    echo "  Polygon (Prices): ⚠️  Not configured (stub mode)"
fi

if [ -n "$FRED_API_KEY" ]; then
    echo "  FRED (Macro): ✅ Configured"
else
    echo "  FRED (Macro): ⚠️  Not configured (stub mode)"
fi

if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "  Anthropic (AI): ✅ Configured"
else
    echo "  Anthropic (AI): ⚠️  Not configured (stub mode)"
fi
echo ""

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Port 8000 is already in use${NC}"
    echo "Killing existing process..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start the API
echo -e "${GREEN}Starting Executor API on http://localhost:8000${NC}"
echo ""
echo -e "${YELLOW}Available endpoints:${NC}"
echo "  POST http://localhost:8000/v1/execute     - Execute patterns"
echo "  GET  http://localhost:8000/health         - Health check"
echo "  GET  http://localhost:8000/patterns       - List patterns"
echo "  GET  http://localhost:8000/metrics        - Prometheus metrics"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""
echo "=========================================="
echo ""

# Run uvicorn with the executor API
# Note: The app is defined in backend/app/api/executor.py
# Set PYTHONPATH to project root so imports work correctly
export PYTHONPATH="$(pwd):$PYTHONPATH"
cd backend
uvicorn app.api.executor:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info \
    --access-log

# Note: --reload has been REMOVED to fix database pool access issue
# This prevents module reloading which breaks global pool initialization
# Manual restart required for code changes in development
