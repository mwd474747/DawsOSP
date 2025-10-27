#!/bin/bash
#
# Database Initialization Script
# Purpose: Initialize TimescaleDB with DawsOS schema
# Created: 2025-10-23
# Priority: P0 (Critical for UAT foundation)
#
# Usage:
#   ./backend/db/init_database.sh
#
# Prerequisites:
#   - Docker installed
#   - DATABASE_URL environment variable set
#   - PostgreSQL/TimescaleDB running (or use ./start-db.sh)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DawsOS Database Initialization${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_URL not set${NC}"
    echo ""
    echo "Please set DATABASE_URL environment variable:"
    echo "  export DATABASE_URL='postgresql://user:pass@localhost:5432/dawsos'"
    echo ""
    echo "Or use the docker-compose setup:"
    echo "  cd backend/db"
    echo "  docker-compose up -d"
    echo "  export DATABASE_URL='postgresql://dawsos:dawsos@localhost:5432/dawsos'"
    exit 1
fi

echo -e "${GREEN}✓${NC} DATABASE_URL is set"
echo ""

# Check if database is reachable
echo -e "${YELLOW}Checking database connection...${NC}"
if psql "$DATABASE_URL" -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Database connection successful"
else
    echo -e "${RED}ERROR: Cannot connect to database${NC}"
    echo ""
    echo "Make sure the database is running:"
    echo "  cd backend/db"
    echo "  docker-compose up -d"
    exit 1
fi
echo ""

# Apply schemas in order
echo -e "${YELLOW}Applying database schemas...${NC}"

schemas=(
    "backend/db/schema/000_roles.sql"
    "backend/db/schema/001_portfolios_lots_transactions.sql"
    "backend/db/schema/ledger.sql"
    "backend/db/schema/pricing_packs.sql"
    "backend/db/schema/rating_rubrics.sql"
    "backend/db/schema/portfolio_metrics.sql"
    "backend/db/schema/macro_indicators.sql"
    "backend/db/schema/alerts_notifications.sql"
)

for schema in "${schemas[@]}"; do
    if [ -f "$schema" ]; then
        echo -e "  ${YELLOW}→${NC} Applying $(basename "$schema")"
        psql "$DATABASE_URL" -f "$schema" > /dev/null 2>&1 || {
            echo -e "${RED}ERROR: Failed to apply $schema${NC}"
            exit 1
        }
        echo -e "  ${GREEN}✓${NC} Applied $(basename "$schema")"
    else
        echo -e "${RED}WARNING: Schema file not found: $schema${NC}"
    fi
done
echo ""

# Apply migrations
echo -e "${YELLOW}Applying migrations...${NC}"

migrations=(
    "backend/db/migrations/005_create_rls_policies.sql"
)

for migration in "${migrations[@]}"; do
    if [ -f "$migration" ]; then
        echo -e "  ${YELLOW}→${NC} Applying $(basename "$migration")"
        psql "$DATABASE_URL" -f "$migration" > /dev/null 2>&1 || {
            echo -e "${RED}ERROR: Failed to apply $migration${NC}"
            exit 1
        }
        echo -e "  ${GREEN}✓${NC} Applied $(basename "$migration")"
    else
        echo -e "${RED}WARNING: Migration file not found: $migration${NC}"
    fi
done
echo ""

# Verify schema
echo -e "${YELLOW}Verifying schema...${NC}"

# Check tables
tables=$(psql "$DATABASE_URL" -t -c "
    SELECT COUNT(*)
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('portfolios', 'lots', 'transactions', 'portfolio_metrics', 'pricing_packs', 'rating_rubrics', 'ledger_snapshots')
" | xargs)

if [ "$tables" -ge 7 ]; then
    echo -e "  ${GREEN}✓${NC} Core tables created ($tables/7+)"
else
    echo -e "  ${RED}✗${NC} Expected 7+ tables, found $tables"
    exit 1
fi

# Check RLS policies
rls_policies=$(psql "$DATABASE_URL" -t -c "
    SELECT COUNT(*)
    FROM pg_policies
    WHERE schemaname = 'public'
    AND policyname LIKE '%isolation%'
" | xargs)

if [ "$rls_policies" -ge 3 ]; then
    echo -e "  ${GREEN}✓${NC} RLS policies created ($rls_policies/3+)"
else
    echo -e "  ${RED}✗${NC} Expected 3+ RLS policies, found $rls_policies"
    exit 1
fi

# Check indexes
indexes=$(psql "$DATABASE_URL" -t -c "
    SELECT COUNT(*)
    FROM pg_indexes
    WHERE schemaname = 'public'
    AND tablename IN ('portfolios', 'lots', 'transactions')
" | xargs)

if [ "$indexes" -ge 5 ]; then
    echo -e "  ${GREEN}✓${NC} Indexes created ($indexes/5+)"
else
    echo -e "  ${YELLOW}⚠${NC} Expected 5+ indexes, found $indexes"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Database initialization complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Run tests: pytest backend/tests/test_database_schema.py -v"
echo "  2. Load seed data: python scripts/seed_loader.py --all"
echo "  3. Verify with: psql \$DATABASE_URL -c 'SELECT COUNT(*) FROM portfolios;'"
echo ""
