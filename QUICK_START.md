# DawsOS - Quick Start

**Status**: ✅ **READY TO LAUNCH**

---

## 🚀 Launch in 30 Seconds

### Option 1: Development Mode (Recommended)

```bash
# Terminal 1 - Backend
cd /Users/mdawson/Documents/GitHub/DawsOSP
source activate.sh
./backend/run_api.sh

# Terminal 2 - Frontend
cd /Users/mdawson/Documents/GitHub/DawsOSP
source activate.sh
./frontend/run_ui.sh

# Browser
open http://localhost:8501
```

---

### Option 2: Docker (Full Stack + Observability)

```bash
cd /Users/mdawson/Documents/GitHub/DawsOSP
docker compose --profile observability up -d

# Wait 30 seconds, then access:
open http://localhost:8501      # Frontend
open http://localhost:3000      # Grafana (admin/admin)
```

---

## 📊 Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:8501 | - |
| **Backend API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **Grafana** | http://localhost:3000 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |
| **Jaeger** | http://localhost:16686 | - |

---

## ✅ What's Configured

- ✅ Virtual environment (Python 3.13.2, 151 packages)
- ✅ Database services (PostgreSQL + Redis running)
- ✅ API keys (5 providers configured)
- ✅ Observability stack (Prometheus, Grafana, Jaeger, OTel)
- ✅ Tests (602+ tests ready)

---

## 🔑 API Providers Ready

- ✅ **FMP** - Fundamentals data (Premium - Unlimited)
- ✅ **Polygon** - Real-time prices (Paid - 100 req/min)
- ✅ **FRED** - Macro indicators (Free - 60 req/min)
- ✅ **NewsAPI** - News sentiment (Developer - 100 req/day)
- ✅ **Anthropic** - AI analysis (Pay-as-you-go)

---

## 🧪 Quick Test

```bash
# Verify everything ready
./verify_ready.sh

# Test backend health
curl http://localhost:8000/health

# Run tests
source venv/bin/activate
pytest backend/tests/unit/test_alert_delivery.py -v
```

---

## 📚 Full Documentation

- **[READY_TO_LAUNCH.md](READY_TO_LAUNCH.md)** - Complete launch guide
- **[LAUNCH_GUIDE.md](LAUNCH_GUIDE.md)** - Detailed instructions
- **[API_KEYS_CONFIGURED.md](API_KEYS_CONFIGURED.md)** - API setup
- **[OBSERVABILITY_QUICKSTART.md](OBSERVABILITY_QUICKSTART.md)** - Monitoring guide

---

## 🛠️ Troubleshooting

### Backend won't start?
```bash
lsof -ti:8000 | xargs kill -9  # Kill any process on port 8000
source activate.sh
./backend/run_api.sh
```

### Frontend can't connect?
```bash
# Verify backend is running
curl http://localhost:8000/health

# Set API URL and restart
export EXECUTOR_API_URL="http://localhost:8000"
./frontend/run_ui.sh
```

### Database not running?
```bash
docker compose -f docker-compose.simple.yml up -d
sleep 5  # Wait for startup
docker ps | grep dawsos
```

---

## 🎯 Next Steps After Launch

1. ✅ Create user account (via API or frontend)
2. ✅ Load seed data: `python scripts/seed_loader.py --all`
3. ✅ Create your first alert
4. ✅ Explore Grafana dashboards
5. ✅ Run full test suite: `pytest backend/tests/ -v`

---

## 📊 What You'll See

### Backend (Terminal 1)
```
✅ Virtual environment activated
✅ Dependencies installed
✅ Database connection verified

API Provider Status:
  FMP (Fundamentals): ✅ Configured
  Polygon (Prices): ✅ Configured
  FRED (Macro): ✅ Configured
  NewsAPI: ✅ Configured
  Anthropic (AI): ✅ Configured

Starting Executor API on http://localhost:8000
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Frontend (Terminal 2)
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
```

### Browser
DawsOS dashboard with navigation:
- Portfolio Overview
- Markets
- Economics
- Alerts
- Settings

---

**Ready to launch?** Just run the commands above! 🚀

---

**Last Updated**: October 28, 2025
**Status**: ✅ Production Ready
**Repository**: [DawsOSP](https://github.com/mwd474747/DawsOSP)
