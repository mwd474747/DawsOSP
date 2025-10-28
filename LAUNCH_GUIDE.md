# DawsOS Launch Guide

**Date**: October 27, 2025
**Purpose**: Complete guide to launch DawsOS locally for development
**Time to Complete**: 10-15 minutes

---

## Prerequisites

### Required Software
- **Python 3.11+** (Python 3.13 works)
- **Docker Desktop** (for PostgreSQL and Redis)
- **Git** (to clone repository)

### Optional Software
- **Make** (for Makefile commands)
- **PostgreSQL Client** (psql) for database inspection

---

## Quick Start (5 minutes)

### Step 1: Clone Repository (if not already done)

```bash
git clone https://github.com/mwd474747/DawsOSP.git
cd DawsOSP
```

### Step 2: Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
pip install -r frontend/requirements.txt
```

**Note**: Installation takes ~5 minutes (downloads ~500MB of packages)

### Step 3: Start Database Services

```bash
# Start PostgreSQL and Redis only (lightweight)
docker compose -f docker-compose.simple.yml up -d

# Verify services are running
docker compose -f docker-compose.simple.yml ps

# Should show:
# dawsos-dev-postgres    running    0.0.0.0:5432->5432/tcp
# dawsos-dev-redis       running    0.0.0.0:6379->6379/tcp
```

### Step 4: Configure API Keys (Optional)

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys (optional - app works without them)
nano .env

# Required API keys for full functionality:
# - ANTHROPIC_API_KEY (for AI explanations)
# - FMP_API_KEY (for fundamentals data)
# - POLYGON_API_KEY (for real-time prices)
# - FRED_API_KEY (for macro/economic data)
```

**Without API Keys**: Application runs in "stub mode" with sample/mock data.

### Step 5: Apply Database Schema

```bash
# Create database schema
# Note: This step is optional for first run as the app auto-creates tables
# But it's recommended to ensure all migrations are applied

# Option 1: Using psql (if installed)
psql postgresql://dawsos:dawsos@localhost:5432/dawsos -f backend/db/schema/01_users_and_auth.sql
psql postgresql://dawsos:dawsos@localhost:5432/dawsos -f backend/db/schema/02_ledger.sql
psql postgresql://dawsos:dawsos@localhost:5432/dawsos -f backend/db/schema/03_patterns.sql
psql postgresql://dawsos:dawsos@localhost:5432/dawsos -f backend/db/schema/04_alerts_notifications.sql

# Option 2: Using Docker (no psql required)
docker compose -f docker-compose.simple.yml exec postgres psql -U dawsos -d dawsos -f /docker-entrypoint-initdb.d/01_users_and_auth.sql
```

### Step 6: Start Backend API

```bash
# Option 1: Using startup script (recommended)
chmod +x backend/run_api.sh
./backend/run_api.sh

# Option 2: Using uvicorn directly
source venv/bin/activate
export PYTHONPATH=$(pwd)
cd backend
uvicorn app.api.executor:app --host 0.0.0.0 --port 8000
```

**Backend URL**: http://localhost:8000

**Health Check**: http://localhost:8000/health

### Step 7: Start Frontend UI (New Terminal)

```bash
# Open new terminal window
cd DawsOSP

# Option 1: Using startup script (recommended)
chmod +x frontend/run_ui.sh
./frontend/run_ui.sh

# Option 2: Using streamlit directly
source venv/bin/activate
export PYTHONPATH=$(pwd)
streamlit run frontend/main.py --server.port 8501
```

**Frontend URL**: http://localhost:8501

---

## Verification

### Check Backend is Running

```bash
# Health check
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","timestamp":"2025-10-27T..."}

# List available patterns
curl http://localhost:8000/patterns

# Metrics endpoint (Prometheus format)
curl http://localhost:8000/metrics
```

### Check Frontend is Running

Open browser: http://localhost:8501

You should see the DawsOS dashboard with navigation:
- Portfolio Overview
- Markets
- Economics
- Alerts
- Settings

### Check Database Connection

```bash
# Using Docker exec
docker compose -f docker-compose.simple.yml exec postgres psql -U dawsos -d dawsos -c "SELECT version();"

# Should show PostgreSQL version with TimescaleDB
```

---

## Full Stack Launch (with Observability)

### Start All Services (Development)

```bash
# Start full stack (backend, frontend, database, observability)
docker compose up -d

# OR with observability profile
docker compose --profile observability up -d
```

**Services Started**:
- **PostgreSQL** (port 5432) - Database
- **Redis** (port 6379) - Cache
- **Backend** (port 8000) - FastAPI
- **Frontend** (port 8501) - Streamlit
- **Worker** (background) - Jobs
- **Prometheus** (port 9090) - Metrics (with --profile observability)
- **Grafana** (port 3000) - Dashboards (with --profile observability)
- **Jaeger** (port 16686) - Traces (with --profile observability)
- **OTel Collector** (ports 4317, 8888) - Telemetry (with --profile observability)

### Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:8501 | - |
| **Backend API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Jaeger** | http://localhost:16686 | - |

---

## Environment Variables

### Backend Environment Variables

```bash
# Database
export DATABASE_URL="postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos"
export REDIS_URL="redis://localhost:6379/0"

# API Keys (optional - stub mode without them)
export ANTHROPIC_API_KEY="sk-..."
export FMP_API_KEY="..."
export POLYGON_API_KEY="..."
export FRED_API_KEY="..."
export NEWSAPI_KEY="..."

# Application Settings
export ENVIRONMENT="development"
export LOG_LEVEL="INFO"
export PYTHONPATH="$(pwd)"

# Observability (optional)
export OTLP_ENDPOINT="http://jaeger:4317"  # If using Docker observability
export SENTRY_DSN="https://..."  # Optional error tracking

# Security
export AUTH_JWT_SECRET="your-secret-key-here"  # Change in production!

# Feature Flags
export USE_MOCK_DATA="false"  # Set to "true" for testing without API keys
```

### Frontend Environment Variables

```bash
# Backend API URL
export EXECUTOR_API_URL="http://localhost:8000"

# Mock Mode (for testing UI without backend)
export USE_MOCK_CLIENT="false"  # Set to "true" for UI-only development

export PYTHONPATH="$(pwd)"
```

---

## Development Workflow

### Day-to-Day Development

1. **Start Database** (once per day):
   ```bash
   docker compose -f docker-compose.simple.yml up -d
   ```

2. **Start Backend** (each coding session):
   ```bash
   source venv/bin/activate
   ./backend/run_api.sh
   ```

3. **Start Frontend** (new terminal):
   ```bash
   source venv/bin/activate
   ./frontend/run_ui.sh
   ```

4. **Make Code Changes**:
   - Backend changes: Restart `run_api.sh` (no auto-reload for stability)
   - Frontend changes: Streamlit auto-reloads

5. **Run Tests**:
   ```bash
   source venv/bin/activate
   pytest backend/tests/
   ```

### Stop Services

```bash
# Stop backend/frontend
Ctrl+C in terminal

# Stop database
docker compose -f docker-compose.simple.yml down

# Stop full stack
docker compose down
```

---

## Testing

### Run Full Test Suite

```bash
source venv/bin/activate

# Run all tests
pytest backend/tests/ -v

# Run specific test file
pytest backend/tests/unit/test_alert_delivery.py -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
# OR
xdg-open htmlcov/index.html  # Linux
```

### Test Results

**Expected**: 602+ tests collected, all passing

```
===================== 602 passed in 45.23s ======================
```

---

## Troubleshooting

### Issue: Port Already in Use

**Error**: `Address already in use: port 8000`

**Solution**:
```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
kill -9 $(lsof -ti:8000)

# Or restart backend script (it auto-kills)
./backend/run_api.sh
```

### Issue: Database Connection Failed

**Error**: `Connection refused` or `database "dawsos" does not exist`

**Solution**:
```bash
# Check Docker is running
docker ps

# Start database if not running
docker compose -f docker-compose.simple.yml up -d

# Wait for database to be ready
docker compose -f docker-compose.simple.yml logs postgres | grep "ready"

# Recreate database if needed
docker compose -f docker-compose.simple.yml down -v
docker compose -f docker-compose.simple.yml up -d
```

### Issue: Import Errors

**Error**: `ModuleNotFoundError: No module named 'backend'`

**Solution**:
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=$(pwd)

# Verify you're in project root
pwd  # Should end in DawsOSP

# Reinstall dependencies
pip install -r backend/requirements.txt
```

### Issue: Virtual Environment Issues

**Error**: `bad interpreter: no such file or directory`

**Solution**:
```bash
# Remove and recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### Issue: API Keys Not Working

**Error**: `Using stub mode` warnings in logs

**Solution**:
```bash
# Verify .env file exists
ls -la .env

# Verify keys are exported (DO NOT print actual keys!)
env | grep -E "FMP_API_KEY|POLYGON_API_KEY" | wc -l
# Should show 2 (or number of keys you've set)

# Reload environment
source .env  # If using shell
# OR restart run_api.sh (it sources .env automatically)
```

### Issue: Frontend Not Connecting to Backend

**Error**: Frontend shows "Connection Error"

**Solution**:
```bash
# 1. Verify backend is running
curl http://localhost:8000/health

# 2. Check EXECUTOR_API_URL
echo $EXECUTOR_API_URL
# Should be: http://localhost:8000

# 3. Restart frontend with correct env
export EXECUTOR_API_URL="http://localhost:8000"
./frontend/run_ui.sh
```

---

## Production Deployment

### Using Docker Compose (Recommended)

```bash
# Set production environment variables
export ENVIRONMENT=production
export AUTH_JWT_SECRET=$(openssl rand -base64 32)
export GRAFANA_PASSWORD=$(openssl rand -base64 16)

# Set API keys in .env file
nano .env

# Start services
docker compose --profile observability up -d

# Verify all healthy
docker compose ps
docker compose logs -f

# Apply database migrations
docker compose exec postgres psql -U dawsos -d dawsos -f /docker-entrypoint-initdb.d/01_users_and_auth.sql
# ... (repeat for other schema files)

# Schedule alert retry worker
# See PHASE2_ALERT_DELIVERY_COMPLETE_2025-10-27.md for systemd timer setup
```

### Environment-Specific Settings

**Development**:
- `ENVIRONMENT=development`
- `LOG_LEVEL=INFO`
- `USE_MOCK_DATA=false` (if you have API keys)
- Trace sampling: 100%
- Prometheus retention: 30 days

**Production**:
- `ENVIRONMENT=production`
- `LOG_LEVEL=WARNING`
- `USE_MOCK_DATA=false`
- Trace sampling: 10% (configure in `observability/otel/otel-collector-config.yml`)
- Prometheus retention: 15 days
- Add resource limits in docker-compose.yml
- Use external secrets manager for API keys

---

## API Endpoints Reference

### Backend API (http://localhost:8000)

**Core Endpoints**:
```
GET  /health                 - Health check
GET  /metrics                - Prometheus metrics
GET  /patterns               - List available patterns
POST /v1/execute             - Execute pattern
GET  /docs                   - Interactive API docs (Swagger UI)
GET  /redoc                  - Alternative API docs (ReDoc)
```

**Authentication**:
```
POST /v1/auth/register       - Register new user
POST /v1/auth/login          - Login (get JWT token)
POST /v1/auth/refresh        - Refresh JWT token
GET  /v1/auth/me             - Get current user
```

**Alerts**:
```
GET  /v1/alerts              - List user's alerts
POST /v1/alerts              - Create alert
GET  /v1/alerts/{id}         - Get alert details
PATCH /v1/alerts/{id}        - Update alert
DELETE /v1/alerts/{id}       - Delete alert
POST /v1/alerts/{id}/test    - Test alert (dry run)
```

**Reports**:
```
POST /v1/reports/portfolio   - Generate portfolio PDF report
```

---

## Useful Commands

### Database Management

```bash
# Connect to database
docker compose -f docker-compose.simple.yml exec postgres psql -U dawsos -d dawsos

# Run SQL query
docker compose -f docker-compose.simple.yml exec postgres \
  psql -U dawsos -d dawsos -c "SELECT COUNT(*) FROM users;"

# Backup database
docker compose -f docker-compose.simple.yml exec postgres \
  pg_dump -U dawsos dawsos > backup.sql

# Restore database
cat backup.sql | docker compose -f docker-compose.simple.yml exec -T postgres \
  psql -U dawsos -d dawsos
```

### Docker Management

```bash
# View logs
docker compose logs backend
docker compose logs frontend
docker compose logs postgres

# Follow logs
docker compose logs -f backend

# Restart service
docker compose restart backend

# Rebuild service after code changes
docker compose up -d --build backend

# Stop all services
docker compose down

# Stop all services and remove volumes (WARNING: deletes data)
docker compose down -v
```

### Development Helpers

```bash
# Format code with ruff
./venv/bin/ruff format backend/

# Lint code
./venv/bin/ruff check backend/

# Type check
./venv/bin/mypy backend/app

# Run specific test
pytest backend/tests/unit/test_alert_delivery.py::TestDeliverAlert::test_deliver_alert_success -v

# Watch mode for tests (requires pytest-watch)
pip install pytest-watch
ptw backend/tests/
```

---

## Next Steps

### After Successful Launch

1. ✅ **Explore Frontend**: http://localhost:8501
   - Navigate through Portfolio, Markets, Economics tabs
   - Create an alert
   - View dashboards

2. ✅ **Try API**: http://localhost:8000/docs
   - Test execute endpoint with sample pattern
   - View metrics endpoint

3. ✅ **View Observability** (if started with --profile observability):
   - Grafana: http://localhost:3000 (admin/admin)
   - Prometheus: http://localhost:9090
   - Jaeger: http://localhost:16686

4. ✅ **Run Tests**:
   ```bash
   pytest backend/tests/ -v
   ```

5. ✅ **Read Documentation**:
   - [OBSERVABILITY_QUICKSTART.md](OBSERVABILITY_QUICKSTART.md) - Observability guide
   - [PRODUCT_SPEC.md](PRODUCT_SPEC.md) - Product specification
   - [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Development workflow

### Development Tasks

- [ ] Add your API keys to `.env` for real data
- [ ] Load seed data (ledger transactions)
- [ ] Create custom patterns
- [ ] Add custom agents
- [ ] Create custom dashboards

---

## Support

### Documentation
- **Quick Start**: This file (LAUNCH_GUIDE.md)
- **Observability**: [OBSERVABILITY_QUICKSTART.md](OBSERVABILITY_QUICKSTART.md)
- **Product Spec**: [PRODUCT_SPEC.md](PRODUCT_SPEC.md)
- **Architecture**: [CLAUDE.md](CLAUDE.md)

### Troubleshooting
- Check [Troubleshooting](#troubleshooting) section above
- Review logs: `docker compose logs -f backend`
- Check health: `curl http://localhost:8000/health`

### GitHub
- **Repository**: https://github.com/mwd474747/DawsOSP
- **Issues**: https://github.com/mwd474747/DawsOSP/issues

---

**Last Updated**: October 27, 2025
**Tested On**: macOS (Apple Silicon), Python 3.13
**Status**: ✅ Production Ready
