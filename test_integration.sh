#!/bin/bash

# DawsOS Integration Test Script
# Purpose: Verify end-to-end integration (Database → API → UI)
# Updated: 2025-10-23

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DawsOS Integration Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print test result
test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        ((TESTS_FAILED++))
    fi
}

# Function to test API endpoint
test_api() {
    local url=$1
    local description=$2
    local expected_status=${3:-200}

    echo -e "${YELLOW}Testing:${NC} $description"

    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo "000")
    status_code=$(echo "$response" | tail -n1)

    if [ "$status_code" = "$expected_status" ]; then
        test_result 0 "$description (HTTP $status_code)"
    else
        test_result 1 "$description (Expected HTTP $expected_status, got $status_code)"
    fi
}

# Function to test API POST endpoint
test_api_post() {
    local url=$1
    local data=$2
    local description=$3
    local expected_status=${4:-200}

    echo -e "${YELLOW}Testing:${NC} $description"

    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "$data" \
        "$url" 2>/dev/null || echo "000")
    status_code=$(echo "$response" | tail -n1)

    if [ "$status_code" = "$expected_status" ]; then
        test_result 0 "$description (HTTP $status_code)"
        # Print first 200 chars of response body
        body=$(echo "$response" | head -n-1 | head -c 200)
        echo -e "${BLUE}   Response:${NC} $body..."
    else
        test_result 1 "$description (Expected HTTP $expected_status, got $status_code)"
    fi
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 1: Infrastructure Checks${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Test 1: Check Database Connection
echo -e "${YELLOW}Checking database connection...${NC}"

DB_USER="dawsos_app"
DB_NAME="dawsos"
DATABASE_URL="${DATABASE_URL:-postgresql://localhost/dawsos}"

# Try to connect to database
if python3 -c "import asyncpg; import os; import asyncio; async def test(): conn = await asyncpg.connect(os.getenv('DATABASE_URL', '$DATABASE_URL')); await conn.close(); asyncio.run(test())" 2>/dev/null; then
    test_result 0 "Database connection successful"
else
    test_result 1 "Database connection failed (check DATABASE_URL environment variable)"
fi

echo ""

# Test 2: Check database connectivity
echo -e "${YELLOW}Checking database connectivity...${NC}"
if python3 -c "import asyncpg; import os; import asyncio; async def test(): conn = await asyncpg.connect(os.getenv('DATABASE_URL', '$DATABASE_URL')); await conn.execute('SELECT 1'); await conn.close(); asyncio.run(test())" 2>/dev/null; then
    test_result 0 "Database connection successful"
else
    test_result 1 "Database connection failed"
fi

echo ""

# Test 3: Check database tables
echo -e "${YELLOW}Checking database schema...${NC}"
table_count=$(python3 -c "import asyncpg; import os; import asyncio; async def test(): conn = await asyncpg.connect(os.getenv('DATABASE_URL', '$DATABASE_URL')); count = await conn.fetchval(\"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'\"); await conn.close(); print(count); asyncio.run(test())" 2>/dev/null | tr -d ' ')
table_count=${table_count:-0}

if [ "$table_count" -ge 10 ]; then
    test_result 0 "Database schema exists ($table_count tables)"
else
    test_result 1 "Database schema incomplete (only $table_count tables)"
fi

echo ""

# Test 4: Check seed data
echo -e "${YELLOW}Checking seed data...${NC}"
portfolio_count=$(python3 -c "import asyncpg; import os; import asyncio; async def test(): conn = await asyncpg.connect(os.getenv('DATABASE_URL', '$DATABASE_URL')); count = await conn.fetchval('SELECT COUNT(*) FROM portfolios'); await conn.close(); print(count); asyncio.run(test())" 2>/dev/null | tr -d ' ')
portfolio_count=${portfolio_count:-0}

if [ "$portfolio_count" -ge 1 ]; then
    test_result 0 "Seed data exists ($portfolio_count portfolios)"
else
    test_result 1 "No seed data found"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 2: Backend API Checks${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if API is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Backend API not running on port 8000${NC}"
    echo -e "${YELLOW}Skipping API tests. Start the API with:${NC}"
    echo "  ./backend/run_api.sh"
    echo ""
    API_RUNNING=0
else
    API_RUNNING=1
fi

if [ $API_RUNNING -eq 1 ]; then
    # Test 5: Health check endpoint
    test_api "http://localhost:8000/health" "Health check endpoint"

    echo ""

    # Test 6: Patterns list endpoint
    test_api "http://localhost:8000/patterns" "Patterns list endpoint"

    echo ""

    # Test 7: Metrics endpoint
    test_api "http://localhost:8000/metrics" "Prometheus metrics endpoint"

    echo ""

    # Test 8: Execute pattern (portfolio_overview)
    echo -e "${YELLOW}Testing pattern execution...${NC}"

    # Get portfolio ID from database
    portfolio_id=$(python3 -c "import asyncpg; import os; import asyncio; async def test(): conn = await asyncpg.connect(os.getenv('DATABASE_URL', '$DATABASE_URL')); pid = await conn.fetchval('SELECT id FROM portfolios LIMIT 1'); await conn.close(); print(pid if pid else ''); asyncio.run(test())" 2>/dev/null | tr -d ' ')

    if [ -n "$portfolio_id" ]; then
        test_api_post "http://localhost:8000/v1/execute" \
            "{\"pattern_id\": \"portfolio_overview\", \"inputs\": {\"portfolio_id\": \"$portfolio_id\"}, \"require_fresh\": false}" \
            "Execute portfolio_overview pattern"
    else
        echo -e "${RED}Cannot test pattern execution: no portfolios in database${NC}"
        ((TESTS_FAILED++))
    fi

    echo ""
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 3: Frontend UI Checks${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Streamlit is running
if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    test_result 0 "Streamlit UI running on port 8501"
    UI_RUNNING=1
else
    echo -e "${YELLOW}Warning: Streamlit UI not running on port 8501${NC}"
    echo -e "${YELLOW}Start the UI with:${NC}"
    echo "  ./frontend/run_ui.sh"
    echo ""
    test_result 1 "Streamlit UI not running"
    UI_RUNNING=0
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Step 4: End-to-End Integration${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ $API_RUNNING -eq 1 ] && [ $UI_RUNNING -eq 1 ]; then
    echo -e "${GREEN}✅ Full stack is running!${NC}"
    echo ""
    echo -e "${YELLOW}Testing workflow:${NC}"
    echo "  1. UI calls DawsOS API Client"
    echo "  2. Client sends POST to http://localhost:8000/v1/execute"
    echo "  3. Executor API calls Pattern Orchestrator"
    echo "  4. Pattern Orchestrator calls Agent Runtime"
    echo "  5. Agents query database"
    echo "  6. Results returned to UI"
    echo ""

    test_result 0 "End-to-end stack operational"
else
    echo -e "${RED}❌ Full stack not running${NC}"
    echo ""

    if [ $API_RUNNING -eq 0 ]; then
        echo -e "${YELLOW}Missing: Backend API${NC}"
        echo "  Start with: ./backend/run_api.sh"
    fi

    if [ $UI_RUNNING -eq 0 ]; then
        echo -e "${YELLOW}Missing: Frontend UI${NC}"
        echo "  Start with: ./frontend/run_ui.sh"
    fi

    test_result 1 "End-to-end stack not operational"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
PASS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))

echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo -e "Pass Rate: $PASS_RATE%"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${GREEN}✅ DawsOS is fully operational!${NC}"
    echo ""
    echo "Access the application:"
    echo -e "  UI:  ${BLUE}http://localhost:8501${NC}"
    echo -e "  API: ${BLUE}http://localhost:8000${NC}"
    echo ""
    echo "Try these user scenarios:"
    echo "  1. Portfolio Overview - View metrics and holdings"
    echo "  2. Holdings Deep-Dive - Select a holding for analysis"
    echo "  3. Macro Dashboard - View current regime and cycles"
    echo "  4. Scenarios - Run stress tests (rates_up, equity_crash, etc.)"
    echo ""
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Please fix the failing tests before proceeding."
    echo ""
    echo "Common issues:"
    echo "  1. Database not accessible: Check DATABASE_URL environment variable"
    echo "  2. Backend API not started: ./backend/run_api.sh"
    echo "  3. Frontend UI not started: ./frontend/run_ui.sh"
    echo "  4. Database schema not applied: see backend/db/init_database.sh"
    echo ""
    exit 1
fi
