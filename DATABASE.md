# Database Documentation

**Version:** 1.0
**Last Updated:** November 3, 2025
**Purpose:** Comprehensive database reference for DawsOSP

---

## Overview

DawsOSP uses PostgreSQL 14+ with TimescaleDB extension for portfolio and time-series data storage.

**Key Components:**
- **Connection Pooling:** Cross-module pool using `sys.modules` storage
- **Schema:** 15+ core tables with RLS (Row Level Security)
- **Migrations:** Sequential SQL migration files in `backend/db/migrations/`
- **Seeding:** Development and production seed data

---

## Database Setup

### Prerequisites

**Required Software:**
- PostgreSQL 14+
- TimescaleDB extension
- psql command-line tool

### Installation

**macOS:**
```bash
# Install PostgreSQL and TimescaleDB
brew install postgresql@14
brew install timescaledb

# Start PostgreSQL
brew services start postgresql@14

# Enable TimescaleDB
timescaledb-tune --quiet --yes
```

**Ubuntu/Debian:**
```bash
# Add PostgreSQL repository
sudo apt-get install -y postgresql-common
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh

# Install PostgreSQL and TimescaleDB
sudo apt-get install -y postgresql-14 timescaledb-2-postgresql-14

# Enable and start PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### Database Creation

**Step 1: Create Database**
```bash
# Create database (as postgres user or your user)
createdb dawsos

# Or via psql:
psql -c "CREATE DATABASE dawsos;"
```

**Step 2: Enable TimescaleDB Extension**
```bash
psql -d dawsos -c "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"
```

**Step 3: Verify Installation**
```bash
psql -d dawsos -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';"
```

Expected output:
```
   extname   | extversion
-------------+------------
 timescaledb | 2.x.x
```

### Running Migrations

**IMPORTANT**: Migrations must be run in order.

**Core Migrations (REQUIRED):**
```bash
# 1. Core schema
psql -d dawsos < backend/db/migrations/001_core_schema.sql

# 2. Seed reference data
psql -d dawsos < backend/db/migrations/002_seed_data.sql

# 3. TimescaleDB hypertables (portfolio metrics)
psql -d dawsos < backend/db/migrations/003_create_portfolio_metrics.sql

# 4. Currency attribution support
psql -d dawsos < backend/db/migrations/004_create_currency_attribution.sql
```

**Authentication Setup (REQUIRED):**
```bash
# Note: Some migration files have .sql.disabled extension
# Rename to .sql to enable, or run directly:

# Create users table and audit log
psql -d dawsos < backend/db/migrations/010_add_users_and_audit_log.sql.disabled
```

**Optional Migrations:**
```bash
# Row-level security policies (if needed)
psql -d dawsos < backend/db/migrations/005_create_rls_policies.sql.disabled

# Advanced lot quantity tracking
psql -d dawsos < backend/db/migrations/007_add_lot_qty_tracking.sql.disabled

# Alert delivery system
psql -d dawsos < backend/db/migrations/011_alert_delivery_system.sql.disabled
```

### Verify Setup

**Check Tables:**
```bash
psql -d dawsos -c "\\dt"
```

Expected tables: portfolios, lots, transactions, securities, pricing_packs, prices, users, etc.

**Check Users:**
```bash
psql -d dawsos -c "SELECT email, role FROM users;"
```

Should show at least one user (michael@dawsos.com or similar).

**Check Application Connection:**
```bash
export DATABASE_URL="postgresql://localhost/dawsos"
python3 -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql://localhost/dawsos'))" && echo "✅ Connection successful"
```

### Troubleshooting Setup

**Error: "database does not exist"**
```bash
createdb dawsos
```

**Error: "role does not exist"**
```bash
# Create PostgreSQL user (if needed)
createuser -s $USER  # Create superuser with your username
```

**Error: "extension timescaledb not found"**
```bash
# macOS
brew install timescaledb
timescaledb-tune --quiet --yes

# Ubuntu
sudo apt-get install timescaledb-2-postgresql-14
```

**Error: "permission denied"**
```bash
# Grant permissions (as postgres user)
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE dawsos TO $USER;"
```

---

## Connection Architecture

### Pool Management

**Implementation:** `backend/app/db/connection.py`

**Pattern:** Cross-module pool storage using `sys.modules['__dawsos_db_pool_storage__']`

```python
# Register pool (in combined_server.py)
from backend.app.db.connection import register_external_pool
register_external_pool(pool)

# Access pool (in any module)
from backend.app.db.connection import get_db_pool
pool = get_db_pool()  # Returns same pool across all modules
```

**Why:** Python creates separate module instances on import. Module-level variables don't persist across imports. Solution: Store pool reference in `sys.modules` which is shared globally.

**Historical Context:** See `.archive/investigations/REMAINING_FIXES_ANALYSIS.md` for full explanation of database pool fix (commits 4d15246, e54da93).

### Connection Priorities

**PRIORITY_1:** Schema operations (migrations, DDL)
**PRIORITY_2:** Application queries (default for most operations)
**PRIORITY_3:** Background jobs (async tasks)

---

## Schema Overview

### Core Tables (13 tables actively used)

#### Authentication & Users
- **users** - User accounts, authentication, default portfolio
- **audit_log** - User action audit trail

#### Portfolio Management
- **portfolios** - Portfolio metadata (user_id, currency, name)
- **securities** - Security master data (symbol, name, sector)
- **lots** - Position holdings (portfolio_id, security_id, quantity, cost basis)
- **transactions** - Trade history (buy, sell, dividend, fees)

#### Pricing & Valuation
- **pricing_packs** - Pricing context (asof_date, reproducibility)
- **prices** - Security prices (security_id, pack_id, price)
- **fx_rates** - Currency exchange rates (from_currency, to_currency, rate)

#### Time-Series Data
- **portfolio_metrics** - Daily metrics (TWR, MWR, Sharpe, etc.) - TimescaleDB hypertable
- **portfolio_daily_values** - Daily NAV tracking - TimescaleDB hypertable
- **portfolio_cash_flows** - Cash flow events for IRR calculation

#### Configuration
- **rating_rubrics** - Quality rating configuration (dividend safety, moat strength, resilience)
- **alerts** - Alert definitions and thresholds

#### Macro/Economic
- **macro_indicators** - Economic indicators (unemployment, yield curve, GDP)
- **regime_history** - Macro regime classification history

---

## Data Requirements

### Minimum Required Data

**For Authentication:**
- ✅ At least 1 user in `users` table

**For Portfolio Operations:**
- ✅ At least 1 portfolio in `portfolios` table
- ✅ At least 1 security in `securities` table
- ✅ At least 1 lot in `lots` table (positions)
- ✅ At least 1 pricing pack in `pricing_packs` table
- ✅ Prices for all securities in `prices` table

**Critical:** All 11 portfolio patterns require portfolio_id, which requires above data to exist.

### Detailed Requirements

See archived documentation for comprehensive data requirements:
- `.archive/deprecated/DATABASE_DATA_REQUIREMENTS.md` - Full table requirements
- `.archive/deprecated/DATABASE_SEEDING_PLAN.md` - Seeding strategy

---

## Database Seeding

### Development Fixtures

**Existing Seed Data:**
```sql
-- Users (from 010_add_users_and_audit_log.sql)
admin@dawsos.com (ADMIN role, password: admin123)
user@dawsos.com (USER role, password: user123)
michael@dawsos.com (ADMIN role)

-- Securities (from seed_portfolio_data.sql)
BRK.B, CNR, BAM, BBUC, BTI, EVO, NKE, PYPL, HHC

-- Portfolios
1 portfolio per user with sample holdings
```

### Seeding Process

**Quick Start:**
```bash
# Ensure PostgreSQL is running
psql -d dawsos < backend/db/schema/001_core_tables.sql
psql -d dawsos < backend/db/seeds/seed_portfolio_data.sql
```

**Production Setup:**
1. Run migrations in order (`001_*.sql`, `002_*.sql`, etc.)
2. Load seed data (`backend/db/seeds/*.sql`)
3. Verify with health check: `curl http://localhost:8000/health`

### Comprehensive Seeding Plan

For detailed seeding strategy including:
- Dependency chain analysis
- Business-contextual test data
- Multi-currency portfolios
- Macro economic data

See: `.archive/deprecated/DATABASE_SEEDING_PLAN.md` (1,000 lines, comprehensive)

---

## Database Operations

### Common Queries

**Get Portfolio Positions:**
```sql
SELECT
    s.symbol,
    l.quantity,
    p.price,
    l.quantity * p.price as market_value
FROM lots l
JOIN securities s ON l.security_id = s.id
JOIN prices p ON s.id = p.security_id
WHERE l.portfolio_id = $1
  AND p.pack_id = $2;
```

**Get Performance Metrics:**
```sql
SELECT
    asof_date,
    twr,
    mwr,
    sharpe_ratio
FROM portfolio_metrics
WHERE portfolio_id = $1
ORDER BY asof_date DESC
LIMIT 30;
```

### Performance Optimization

**TimescaleDB Hypertables:**
- `portfolio_metrics` - Partitioned by time for fast time-series queries
- `portfolio_daily_values` - Optimized for historical NAV lookups

**Indexes:**
- Portfolio lookups: `(portfolio_id, asof_date)`
- Security prices: `(security_id, pack_id)`
- Transaction history: `(portfolio_id, transaction_date)`

---

## Migrations

### Migration Files

**Location:** `backend/db/migrations/`

**Naming:** Sequential numbered files:
- `001_core_schema.sql` - Core tables
- `002_seed_data.sql` - Reference data
- `003_create_portfolio_metrics.sql` - TimescaleDB setup
- etc.

**Status:** Several migrations disabled (`.sql.disabled` extension):
- `005_create_rls_policies.sql.disabled` - RLS policies (not used in alpha)
- `007_add_lot_qty_tracking.sql.disabled` - Advanced lot tracking
- `009_jwt_auth.sql.disabled` - JWT migration (handled in code)
- etc.

### Running Migrations

**Manual:**
```bash
psql -d dawsos < backend/db/migrations/001_core_schema.sql
psql -d dawsos < backend/db/migrations/002_seed_data.sql
```

**Future:** Migration manager planned (see `backend/app/db/migration_manager.py`)

---

## Monitoring & Maintenance

### Health Checks

**Application Health:**
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "agents": 9,
  "patterns": "available"
}
```

### Database Monitoring

**Check Connections:**
```sql
SELECT count(*) FROM pg_stat_activity WHERE datname = 'dawsos';
```

**Check Table Sizes:**
```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Troubleshooting

### Connection Issues

**"Database connection failed"**

**Solution:**
1. Check DATABASE_URL environment variable
2. Verify PostgreSQL is running
3. Check connection pool registration

```bash
export DATABASE_URL="postgresql://user:pass@localhost/dawsos"
```

### Pool Registration Issues

**"'NoneType' object has no attribute 'get_pool'"**

**Solution:** Pool registration issue. Ensure pool is registered in `combined_server.py`:

```python
from backend.app.db.connection import register_external_pool
register_external_pool(db_pool)
```

**Historical Context:** See `.archive/investigations/REMAINING_FIXES_ANALYSIS.md` for full fix details.

### Migration Issues

**"Table already exists"**

**Solution:** Migration already run. Check existing tables:
```sql
\dt
```

**"Missing table"**

**Solution:** Run migrations in order (001, 002, 003...)

---

## Best Practices

### Development

1. ✅ **Use transactions** for multi-statement operations
2. ✅ **Test with realistic data** (use seed files)
3. ✅ **Verify RLS isolation** (users only see their data)
4. ✅ **Use prepared statements** (prevent SQL injection)

### Production

1. ✅ **Regular backups** (pg_dump)
2. ✅ **Monitor connection pool** (prevent leaks)
3. ✅ **Index maintenance** (VACUUM, ANALYZE)
4. ✅ **Change default passwords** (admin123, user123)

---

## References

**Code:**
- [backend/app/db/connection.py](backend/app/db/connection.py) - Connection pooling
- [backend/db/migrations/](backend/db/migrations/) - Migration files
- [backend/db/seeds/](backend/db/seeds/) - Seed data

**Archived Documentation:**
- [.archive/deprecated/DATABASE_DATA_REQUIREMENTS.md](.archive/deprecated/DATABASE_DATA_REQUIREMENTS.md) - Detailed requirements (840 lines)
- [.archive/deprecated/DATABASE_SEEDING_PLAN.md](.archive/deprecated/DATABASE_SEEDING_PLAN.md) - Comprehensive seeding plan (1,000 lines)
- [.archive/deprecated/DATABASE_OPERATIONS_VALIDATION.md](.archive/deprecated/DATABASE_OPERATIONS_VALIDATION.md) - Operations analysis (504 lines)

---

**Last Updated:** November 3, 2025
