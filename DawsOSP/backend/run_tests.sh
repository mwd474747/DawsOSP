#!/bin/bash
# DawsOS Test Runner
# Created: 2025-10-27
# Purpose: Run comprehensive test suite with coverage reporting

set -e  # Exit on error

echo "========================================="
echo "DawsOS Test Suite"
echo "========================================="
echo ""

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export DATABASE_URL="${TEST_DATABASE_URL:-postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos_test}"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if test database exists
echo -e "${YELLOW}Checking test database...${NC}"
if ! psql "${DATABASE_URL}" -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Test database not accessible${NC}"
    echo "Please ensure PostgreSQL is running and test database exists:"
    echo "  createdb dawsos_test"
    echo "  psql dawsos_test < backend/db/schema/*.sql"
    exit 1
fi
echo -e "${GREEN}✓ Test database accessible${NC}"
echo ""

# Run unit tests
echo -e "${YELLOW}Running unit tests...${NC}"
pytest backend/tests/unit \
    -v \
    --cov=backend/app \
    --cov-report=term \
    --cov-report=html:backend/htmlcov \
    -m unit \
    || { echo -e "${RED}Unit tests failed${NC}"; exit 1; }

echo -e "${GREEN}✓ Unit tests passed${NC}"
echo ""

# Run integration tests
echo -e "${YELLOW}Running integration tests...${NC}"
pytest backend/tests/integration \
    -v \
    --cov=backend/app \
    --cov-append \
    --cov-report=term \
    --cov-report=html:backend/htmlcov \
    -m integration \
    || { echo -e "${RED}Integration tests failed${NC}"; exit 1; }

echo -e "${GREEN}✓ Integration tests passed${NC}"
echo ""

# Run E2E tests
echo -e "${YELLOW}Running E2E tests...${NC}"
pytest backend/tests/e2e \
    -v \
    --cov=backend/app \
    --cov-append \
    --cov-report=term \
    --cov-report=html:backend/htmlcov \
    -m e2e \
    || { echo -e "${RED}E2E tests failed${NC}"; exit 1; }

echo -e "${GREEN}✓ E2E tests passed${NC}"
echo ""

# Generate coverage report
echo -e "${YELLOW}Generating coverage report...${NC}"
coverage report --fail-under=60 || {
    echo -e "${RED}Coverage below 60% threshold${NC}"
    exit 1
}

echo ""
echo -e "${GREEN}✓ Coverage threshold met (≥60%)${NC}"
echo ""

# Coverage summary
echo "========================================="
echo "Coverage Summary"
echo "========================================="
coverage report --skip-covered

echo ""
echo -e "${GREEN}All tests passed!${NC}"
echo ""
echo "HTML coverage report: backend/htmlcov/index.html"
echo ""
