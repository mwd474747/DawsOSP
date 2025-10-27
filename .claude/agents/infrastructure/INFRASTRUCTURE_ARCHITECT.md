# Infrastructure Architect Agent

**Role**: Foundation infrastructure for DawsOS Portfolio Platform
**Reports to**: [ORCHESTRATOR](../ORCHESTRATOR.md)
**Status**: ✅ Compose stack + Postgres/Redis baseline operational; OAuth/RLS hardening tracked in `.ops/TASK_INVENTORY_2025-10-24.md` P1 items
**Priority**: P0

---

## Scope

Build and validate the complete infrastructure foundation:
1. **Database**: Postgres + Timescale with RLS
2. **Containers**: Docker Compose orchestration
3. **Security**: OAuth/JWT authentication, RLS policies, IDOR protection
4. **Seed Data**: Demo portfolios, symbol master
5. **Configuration**: Secrets management, CORS, environment

---

## Sub-Agents

### DATABASE_BUILDER
**File**: `DATABASE_BUILDER.md`
**Responsibilities**:
- Postgres 15+ with Timescale extension
- Schema migrations (Alembic)
- RLS policies on all portfolio-scoped tables
- Hypertables for metrics, currency_attribution, factor_exposures
- Continuous aggregates for rolling statistics
- Backup strategy (daily dumps + ledger mirror)

**Deliverables**:
```sql
-- migrations/001_foundation.sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    name TEXT NOT NULL,
    base_ccy CHAR(3) NOT NULL,
    benchmark_id TEXT,
    settings_json JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
CREATE POLICY portfolio_user_isolation ON portfolios
    USING (user_id = current_setting('app.user_id')::UUID);

-- Hypertable for metrics
CREATE TABLE portfolio_metrics (
    portfolio_id UUID REFERENCES portfolios(id),
    asof_date DATE NOT NULL,
    pricing_pack_id UUID NOT NULL,
    twr NUMERIC(10,6),
    mwr NUMERIC(10,6),
    vol NUMERIC(10,6),
    sharpe NUMERIC(10,4),
    max_dd NUMERIC(10,6),
    beta NUMERIC(10,4),
    base_ccy CHAR(3),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (portfolio_id, asof_date)
);

SELECT create_hypertable('portfolio_metrics', 'asof_date');

-- Continuous aggregate (30-day rolling vol)
CREATE MATERIALIZED VIEW portfolio_metrics_rolling_30d
WITH (timescaledb.continuous) AS
SELECT portfolio_id, time_bucket('1 day', asof_date) AS bucket,
       STDDEV(twr) * SQRT(252) AS vol_30d_annualized
FROM portfolio_metrics
GROUP BY portfolio_id, bucket;
```

**Tests**:
- RLS isolation: User A cannot query User B's portfolios
- Hypertable ingestion: 1M metric rows insert < 5s
- Migration rollback: Down migrations leave clean state
- Continuous aggregate: Refresh completes < 1s for 10k rows

---

### DOCKER_COMPOSER
**File**: `DOCKER_COMPOSER.md`
**Responsibilities**:
- Multi-service compose stack
- Service health checks
- Volume mounts for ledger repo
- Network isolation
- Local dev vs production configs

**Deliverables**:
```yaml
# docker-compose.yml
version: '3.9'

services:
  db:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_DB: dawsos
      POSTGRES_USER: dawsos
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dawsos"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    environment:
      DATABASE_URL: postgresql://dawsos:${DB_PASSWORD}@db:5432/dawsos
      REDIS_URL: redis://redis:6379/0
      FMP_API_KEY: ${FMP_API_KEY}
      POLYGON_API_KEY: ${POLYGON_API_KEY}
      FRED_API_KEY: ${FRED_API_KEY}
      NEWS_API_KEY: ${NEWS_API_KEY}
      AUTH_JWT_SECRET: ${JWT_SECRET}
      PRICING_POLICY: WM4PM_CAD
      CORS_ORIGINS: ${CORS_ORIGINS}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./ledger:/app/ledger
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000

  worker:
    build:
      context: .
      dockerfile: Dockerfile.api
    environment:
      DATABASE_URL: postgresql://dawsos:${DB_PASSWORD}@db:5432/dawsos
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./ledger:/app/ledger
    command: rq worker -u redis://redis:6379/0

  scheduler:
    build:
      context: .
      dockerfile: Dockerfile.api
    environment:
      DATABASE_URL: postgresql://dawsos:${DB_PASSWORD}@db:5432/dawsos
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./ledger:/app/ledger
    command: python -m scheduler.main

  ui:
    build:
      context: .
      dockerfile: Dockerfile.ui
    environment:
      EXECUTOR_API_URL: http://api:8000
    ports:
      - "8501:8501"
    depends_on:
      - api
    command: streamlit run ui/main.py --server.port=8501

volumes:
  db_data:
```

**Tests**:
- `docker-compose up` → all services healthy < 30s
- `docker-compose down -v` → clean teardown
- Health checks pass before dependents start
- Volume persistence: db data survives container restart

---

### AUTH_SECURITY
**File**: `AUTH_SECURITY.md`
**Responsibilities**:
- OAuth integration (Google/GitHub)
- JWT token generation/validation
- RLS context setting (`app.user_id`)
- IDOR fuzz testing
- Secrets management (Vault/AWS Secrets Manager)

**Deliverables**:
```python
# api/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("AUTH_JWT_SECRET")
ALGORITHM = "HS256"

security = HTTPBearer()

def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return {"user_id": user_id, "email": payload.get("email")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# RLS context setter
async def set_rls_context(db, user_id: str):
    await db.execute(f"SET LOCAL app.user_id = '{user_id}'")

# api/main.py
@app.post("/execute")
async def execute(
    req: ExecRequest,
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    await set_rls_context(db, user["user_id"])
    # ... rest of execution
```

**IDOR Fuzz Tests**:
```python
# tests/security/test_idor.py
import pytest
from hypothesis import given, strategies as st

@given(
    victim_portfolio_id=st.uuids(),
    attacker_user_id=st.uuids()
)
def test_portfolio_access_isolation(victim_portfolio_id, attacker_user_id, client):
    """Attacker should never access victim's portfolio"""
    # Create victim portfolio
    victim_user = create_user()
    create_portfolio(victim_user.id, portfolio_id=victim_portfolio_id)

    # Attempt access as attacker
    attacker_token = create_access_token(str(attacker_user_id), "attacker@example.com")
    response = client.get(
        f"/portfolios/{victim_portfolio_id}",
        headers={"Authorization": f"Bearer {attacker_token}"}
    )

    # Must return 404 (not 403 to avoid enumeration)
    assert response.status_code == 404

@pytest.mark.parametrize("endpoint", [
    "/portfolios/{portfolio_id}",
    "/portfolios/{portfolio_id}/positions",
    "/portfolios/{portfolio_id}/metrics",
    "/execute"  # with portfolio_id in payload
])
def test_all_endpoints_enforce_rls(endpoint, client):
    """Every portfolio-scoped endpoint must enforce RLS"""
    # Create two users with portfolios
    user_a = create_user()
    user_b = create_user()
    portfolio_a = create_portfolio(user_a.id)

    token_b = create_access_token(str(user_b.id), user_b.email)

    # User B attempts to access User A's portfolio
    response = client.get(
        endpoint.format(portfolio_id=portfolio_a.id),
        headers={"Authorization": f"Bearer {token_b}"}
    )

    assert response.status_code == 404
```

**Secrets Management**:
```python
# config/secrets.py
import os
from typing import Optional

class SecretsManager:
    """Abstract secrets provider (can swap Vault/AWS/local)"""

    @staticmethod
    def get_secret(key: str, default: Optional[str] = None) -> str:
        # For now: env vars; later: Vault/AWS Secrets Manager
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"Required secret {key} not found")
        return value

# .env.example (committed)
DATABASE_URL=postgresql://dawsos:CHANGE_ME@localhost:5432/dawsos
REDIS_URL=redis://localhost:6379/0
FMP_API_KEY=your_fmp_key
POLYGON_API_KEY=your_polygon_key
FRED_API_KEY=your_fred_key
NEWS_API_KEY=your_news_key
AUTH_JWT_SECRET=CHANGE_ME_LONG_RANDOM_STRING
PRICING_POLICY=WM4PM_CAD
CORS_ORIGINS=http://localhost:8501,http://localhost:3000

# .env (gitignored, actual secrets)
```

---

## Symbol Master

**Table**:
```sql
CREATE TABLE securities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol TEXT NOT NULL,
    figi TEXT,
    cusip TEXT,
    name TEXT,
    trading_currency CHAR(3) NOT NULL,
    dividend_currency CHAR(3),
    domicile_country CHAR(2),
    type TEXT CHECK (type IN ('STOCK', 'ETF', 'BOND', 'CRYPTO')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, trading_currency)
);

CREATE INDEX idx_securities_figi ON securities(figi) WHERE figi IS NOT NULL;
CREATE INDEX idx_securities_cusip ON securities(cusip) WHERE cusip IS NOT NULL;
```

**Seed Script**:
```python
# scripts/seed_symbol_master.py
import pandas as pd
from sqlalchemy import create_engine

# Load S&P 500 constituents
sp500 = pd.read_csv("seed_data/sp500_constituents.csv")

# Example row: AAPL, US0378331005, BBG000B9XRY4, Apple Inc., USD, USD, US, STOCK
for _, row in sp500.iterrows():
    insert_security(
        symbol=row['symbol'],
        cusip=row['cusip'],
        figi=row['figi'],
        name=row['name'],
        trading_currency=row['trading_ccy'],
        dividend_currency=row['div_ccy'],
        domicile_country=row['domicile'],
        type='STOCK'
    )
```

---

## Demo Seed Data

**Script**:
```python
# scripts/seed_demo_portfolio.py
from decimal import Decimal
from datetime import date

# Create demo user
user = create_user(email="demo@dawsos.com")

# Create portfolio
portfolio = create_portfolio(
    user_id=user.id,
    name="Demo Portfolio",
    base_ccy="CAD",
    benchmark_id="SPY"
)

# Add positions
positions = [
    {"symbol": "AAPL", "qty": 100, "cost_base": Decimal("15000.00"), "trade_date": date(2024, 1, 15)},
    {"symbol": "MSFT", "qty": 50, "cost_base": Decimal("20000.00"), "trade_date": date(2024, 2, 1)},
    {"symbol": "GOOGL", "qty": 30, "cost_base": Decimal("4500.00"), "trade_date": date(2024, 3, 10)},
    {"symbol": "TD.TO", "qty": 200, "cost_base": Decimal("16000.00"), "trade_date": date(2024, 1, 20)},  # CAD stock
]

for p in positions:
    create_lot(portfolio_id=portfolio.id, **p)
```

---

## Rights Registry

**File**: `config/rights_registry.yaml`
```yaml
providers:
  FMP:
    export: restricted
    require_license: true
    attribution: "Financial data © Financial Modeling Prep"
    watermark_text: "For authorized use only"

  Polygon:
    export: restricted
    require_license: true
    attribution: "Market data © Polygon.io"

  FRED:
    export: allow
    require_license: false
    attribution: "Economic data: Federal Reserve Bank of St. Louis, FRED®"

  NewsAPI:
    export: restricted
    require_license: true
    attribution: "News metadata via NewsAPI.org"
    metadata_only: true  # Cannot redistribute full article text

export_types:
  pdf:
    requires_all_licenses: true
    include_attributions: true

  csv:
    requires_all_licenses: true
    include_attributions: true

  api:
    requires_all_licenses: false
    include_attributions: true
```

**Stub Enforcer**:
```python
# services/rights_registry.py
import yaml
from pathlib import Path

class RightsRegistry:
    def __init__(self):
        with open("config/rights_registry.yaml") as f:
            self.config = yaml.safe_load(f)

    def check_export(self, providers: list[str], export_type: str) -> dict:
        """
        Returns {"allowed": bool, "attributions": list[str], "watermark": str | None}
        """
        export_cfg = self.config["export_types"][export_type]

        # Collect provider configs
        provider_cfgs = [self.config["providers"][p] for p in providers]

        # Check if all required licenses present
        if export_cfg["requires_all_licenses"]:
            restricted = [p for p in provider_cfgs if p["export"] == "restricted"]
            if restricted and not self._has_licenses(restricted):
                return {
                    "allowed": False,
                    "reason": "Export requires licenses for: " + ", ".join([p["attribution"] for p in restricted])
                }

        # Collect attributions
        attributions = [p["attribution"] for p in provider_cfgs if export_cfg["include_attributions"]]

        # Watermark if any provider requires it
        watermark = next((p.get("watermark_text") for p in provider_cfgs if p.get("watermark_text")), None)

        return {"allowed": True, "attributions": attributions, "watermark": watermark}

    def _has_licenses(self, providers: list[dict]) -> bool:
        # TODO: Check user's license entitlements in DB
        # For now: allow if env var set
        return os.getenv("EXPORT_LICENSES_ACTIVE") == "true"
```

---

## CORS Configuration

**FastAPI Setup**:
```python
# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="DawsOS Executor API")

# CORS
origins = os.getenv("CORS_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Acceptance Criteria (Week 0.5 Gate)

- [ ] `docker-compose up` → all services healthy
- [ ] Can authenticate via OAuth (Google/GitHub) → receive JWT
- [ ] RLS policies enforce isolation (IDOR tests pass)
- [ ] Symbol master has 500+ securities (S&P 500)
- [ ] Demo portfolio seeded with 4 positions
- [ ] Rights registry stub blocks exports with restricted providers (configurable)
- [ ] CORS allows configured origins
- [ ] Alembic migrations can up/down cleanly
- [ ] Backup script creates dump + ledger mirror

---

## Blockers & Dependencies

**Blockers**:
- None (foundational layer)

**Dependencies**:
- `.env` file with valid secrets (dev team responsibility)
- OAuth app credentials (Google/GitHub developer consoles)

---

## Handoff

Upon completion, deliver:
1. **Runbook**: Docker compose ops, backup/restore procedures
2. **Migration guide**: How to add new tables/columns with RLS
3. **Security checklist**: RLS policy template, IDOR test template
4. **Seed data**: Instructions to regenerate symbol master/demo portfolios
