#!/bin/bash

#
# Integration Test Runner for DawsOS
#
# Purpose: Run all integration tests with proper database setup
# Created: 2025-10-23
# Priority: P0 (Critical for CI/CD)
#
# Usage:
#   ./backend/run_integration_tests.sh              # Run all tests
#   ./backend/run_integration_tests.sh --uat        # Run only UAT tests
#   ./backend/run_integration_tests.sh --security   # Run only security tests
#   ./backend/run_integration_tests.sh --coverage   # Run with coverage report
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
TEST_DATABASE_URL="${TEST_DATABASE_URL:-postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos_test}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Parse arguments
RUN_UAT=false
RUN_SECURITY=false
RUN_PERFORMANCE=false
RUN_PATTERNS=false
RUN_PROVIDERS=false
RUN_COVERAGE=false
RUN_VERBOSE=false

for arg in "$@"; do
    case $arg in
        --uat)
            RUN_UAT=true
            ;;
        --security)
            RUN_SECURITY=true
            ;;
        --performance)
            RUN_PERFORMANCE=true
            ;;
        --patterns)
            RUN_PATTERNS=true
            ;;
        --providers)
            RUN_PROVIDERS=true
            ;;
        --coverage)
            RUN_COVERAGE=true
            ;;
        -v|--verbose)
            RUN_VERBOSE=true
            ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            echo "Usage: $0 [--uat] [--security] [--performance] [--patterns] [--providers] [--coverage] [-v]"
            exit 1
            ;;
    esac
done

# If no specific test suite selected, run all
if [ "$RUN_UAT" = false ] && [ "$RUN_SECURITY" = false ] && [ "$RUN_PERFORMANCE" = false ] && [ "$RUN_PATTERNS" = false ] && [ "$RUN_PROVIDERS" = false ]; then
    RUN_ALL=true
else
    RUN_ALL=false
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DawsOS Integration Test Runner${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Step 1: Verify database connection
echo -e "${YELLOW}[1/6] Verifying database connection...${NC}"

if ! psql "$TEST_DATABASE_URL" -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Cannot connect to test database${NC}"
    echo -e "${RED}Database URL: $TEST_DATABASE_URL${NC}"
    echo ""
    echo "Please ensure PostgreSQL is running and test database exists:"
    echo "  psql -U postgres -c \"CREATE DATABASE dawsos_test;\""
    echo "  psql -U postgres -c \"CREATE USER dawsos_app WITH PASSWORD 'dawsos_app_pass';\""
    echo "  psql -U postgres -c \"GRANT ALL PRIVILEGES ON DATABASE dawsos_test TO dawsos_app;\""
    exit 1
fi

echo -e "${GREEN}✓ Database connection OK${NC}"
echo ""

# Step 2: Apply migrations
echo -e "${YELLOW}[2/6] Applying database migrations...${NC}"

# Check if migrations directory exists
if [ ! -d "$PROJECT_ROOT/backend/db/schema" ]; then
    echo -e "${RED}ERROR: Migrations directory not found${NC}"
    echo -e "${RED}Expected: $PROJECT_ROOT/backend/db/schema${NC}"
    exit 1
fi

# Apply each migration
for migration in "$PROJECT_ROOT/backend/db/schema"/*.sql; do
    if [ -f "$migration" ]; then
        filename=$(basename "$migration")
        echo "  Applying: $filename"

        if ! psql "$TEST_DATABASE_URL" -f "$migration" > /dev/null 2>&1; then
            echo -e "${YELLOW}  Warning: Migration $filename may have already been applied${NC}"
        fi
    fi
done

echo -e "${GREEN}✓ Migrations applied${NC}"
echo ""

# Step 3: Verify schema
echo -e "${YELLOW}[3/6] Verifying database schema...${NC}"

REQUIRED_TABLES=("portfolios" "lots" "transactions" "portfolio_metrics" "pricing_packs")

for table in "${REQUIRED_TABLES[@]}"; do
    if ! psql "$TEST_DATABASE_URL" -c "SELECT 1 FROM $table LIMIT 1" > /dev/null 2>&1; then
        echo -e "${RED}ERROR: Required table '$table' not found${NC}"
        exit 1
    fi
    echo "  ✓ Table '$table' exists"
done

echo -e "${GREEN}✓ Schema verified${NC}"
echo ""

# Step 4: Setup Python environment
echo -e "${YELLOW}[4/6] Setting up Python environment...${NC}"

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
    echo "  ✓ Virtual environment activated"
elif [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo "  ✓ Virtual environment activated"
else
    echo -e "${YELLOW}  Warning: No virtual environment found, using system Python${NC}"
fi

# Install test dependencies (if requirements-test.txt exists)
if [ -f "$PROJECT_ROOT/backend/requirements-test.txt" ]; then
    pip install -q -r "$PROJECT_ROOT/backend/requirements-test.txt"
    echo "  ✓ Test dependencies installed"
fi

echo -e "${GREEN}✓ Python environment ready${NC}"
echo ""

# Step 5: Run tests
echo -e "${YELLOW}[5/6] Running integration tests...${NC}"
echo ""

# Build pytest command
PYTEST_CMD="pytest $PROJECT_ROOT/backend/tests/integration"

# Add markers based on selection
MARKERS=""

if [ "$RUN_ALL" = true ]; then
    MARKERS="-m integration"
else
    MARKER_LIST=""

    if [ "$RUN_UAT" = true ]; then
        MARKER_LIST="${MARKER_LIST}uat or "
    fi

    if [ "$RUN_SECURITY" = true ]; then
        MARKER_LIST="${MARKER_LIST}rls or "
    fi

    if [ "$RUN_PERFORMANCE" = true ]; then
        MARKER_LIST="${MARKER_LIST}slow or "
    fi

    if [ "$RUN_PATTERNS" = true ]; then
        MARKER_LIST="${MARKER_LIST}integration or "
    fi

    if [ "$RUN_PROVIDERS" = true ]; then
        MARKER_LIST="${MARKER_LIST}integration or "
    fi

    # Remove trailing " or "
    MARKER_LIST="${MARKER_LIST% or }"

    if [ -n "$MARKER_LIST" ]; then
        MARKERS="-m \"$MARKER_LIST\""
    fi
fi

# Add coverage if requested
if [ "$RUN_COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=html --cov-report=term-missing"
fi

# Add verbose if requested
if [ "$RUN_VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v -s"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add markers
if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD $MARKERS"
fi

# Set environment variables
export TEST_DATABASE_URL="$TEST_DATABASE_URL"
export PYTHONPATH="$PROJECT_ROOT/backend:$PYTHONPATH"

# Run tests
echo "Running: $PYTEST_CMD"
echo ""

if eval "$PYTEST_CMD"; then
    TEST_RESULT=0
else
    TEST_RESULT=$?
fi

echo ""

# Step 6: Generate report
echo -e "${YELLOW}[6/6] Generating test report...${NC}"

if [ "$TEST_RESULT" -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo -e "${GREEN}========================================${NC}"

    if [ "$RUN_COVERAGE" = true ]; then
        echo ""
        echo -e "${GREEN}Coverage report generated: htmlcov/index.html${NC}"
    fi
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo -e "${RED}========================================${NC}"
fi

echo ""

# Cleanup (optional - comment out if you want to inspect test database)
# echo -e "${YELLOW}Cleaning up test database...${NC}"
# psql "$TEST_DATABASE_URL" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" > /dev/null 2>&1
# echo -e "${GREEN}✓ Cleanup complete${NC}"

exit $TEST_RESULT
