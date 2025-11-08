# DawsOS - AI-Powered Portfolio Management

AI-powered portfolio intelligence platform with macro economic analysis, risk assessment, and scenario testing.

**Version**: 6.0.1 | **Status**: Production Ready ✅

---

## 🚀 Quick Start

```bash
# 1. Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost/dawsos"
export ANTHROPIC_API_KEY="your-api-key"  # Optional for AI features

# 2. Activate virtual environment (if needed)
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 3. Start the application
python combined_server.py

# 4. Open browser
# Visit: http://localhost:8000/
# Login: michael@dawsos.com / admin123
```

**That's it!** The application serves everything from a single server.

---

## ✨ Features

- ✅ **Portfolio Dashboard**: Real-time metrics, attribution, performance tracking
- ✅ **Macro Analysis**: 4 economic cycles (STDC, LTDC, Empire, Civil)
- ✅ **AI Analysis**: Claude-powered insights and explanations
- ✅ **Buffett Ratings**: Quality assessment for all holdings (A-F grades)
- ✅ **Risk Management**: Stress testing and scenario analysis
- ✅ **Transaction History**: Complete audit trail with pagination
- ✅ **Alerts System**: Real-time monitoring and notifications
- ✅ **PDF Reports**: Professional report generation
- ✅ **18 Complete UI Pages**: Fully functional React SPA

---

## 🏗️ Architecture

**Current Production Stack**:
- **UI**: `full_ui.html` - Single-page React application (11,594 lines, no build step)
- **Server**: `combined_server.py` - FastAPI server (6,043 lines, 53 endpoints)
- **Database**: PostgreSQL + TimescaleDB
- **Agents**: 4 agents providing ~70 capabilities
  - **FinancialAnalyst**: Portfolio management, pricing, metrics, ratings, charts, optimization
  - **MacroHound**: Macro economic cycles, scenarios, alerts, regime detection
  - **DataHarvester**: External data, news, reports, corporate actions
  - **ClaudeAgent**: AI-powered explanations and insights
  - **Note:** V3 refactoring ~70% complete (January 15, 2025):
    - Phase -1: Critical bugs fixed ✅ COMPLETE
    - Phase 0: Browser infrastructure ✅ COMPLETE
    - Phase 1: Exception handling (85%) ✅ MOSTLY COMPLETE
    - Phase 2: Singleton removal → DI container (95%) ✅ MOSTLY COMPLETE
    - Phase 3: Code duplication extraction ✅ COMPLETE
    - Phase 4: Legacy code removal ✅ COMPLETE
- **Patterns**: 13 pattern definitions for orchestration

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.

---

## 📦 Technology Stack

- **Backend**: FastAPI + Python 3.11+
- **Frontend**: React 18 (UMD builds - no npm/build step)
- **Database**: PostgreSQL 14+ with TimescaleDB extension
- **AI**: Anthropic Claude API (claude-3-sonnet)
- **Charts**: Chart.js
- **Design**: IBM Plex fonts, professional dark theme

---

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 14+ with TimescaleDB extension
- (Optional) Anthropic API key for AI features
- (Optional) FRED API key for economic data

---

## 🔧 Installation

### 1. Clone Repository

```bash
git clone https://github.com/mwd474747/DawsOSP.git
cd DawsOSP
```

### 2. Set Up Python Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

### 3. Configure Database

```bash
# Create database
createdb dawsos

# Set environment variable
export DATABASE_URL="postgresql://localhost/dawsos"
```

### 4. Set Environment Variables

**⚠️ REQUIRED Variables:**
```bash
# Database connection (REQUIRED)
export DATABASE_URL="postgresql://localhost/dawsos"

# JWT secret for authentication (REQUIRED - generate securely!)
export AUTH_JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

**Optional Variables:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."  # For AI insights (claude.* capabilities)
export FRED_API_KEY="..."              # For economic data (macro indicators)
```

**⚠️ CRITICAL**: Never use `AUTH_JWT_SECRET="your-secret"` in production! Generate a secure random key using the command above.

### 5. Start Application

```bash
# Start server
python combined_server.py

# Server starts on http://localhost:8000/
```

### 6. Access Application

- **UI**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🎮 Default Login

**Development Only:**
- **Email**: michael@dawsos.com
- **Password**: mozzuq-byfqyQ-5tefvu

## 🔒 SECURITY WARNING

**⚠️ BEFORE PRODUCTION DEPLOYMENT:**

1. **Change Default Password**:
   ```sql
   -- Generate new password hash
   python3 -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_NEW_PASSWORD', bcrypt.gensalt(12)).decode())"

   -- Update in database
   UPDATE users SET password_hash = '<new-hash>' WHERE email = 'michael@dawsos.com';
   ```

2. **Delete Test Users**:
   ```sql
   DELETE FROM users WHERE email IN ('admin@dawsos.com', 'user@dawsos.com');
   ```

3. **Generate Secure AUTH_JWT_SECRET** (see environment variables section above)

4. **Enable HTTPS/TLS** for all connections

5. **Review CORS Settings** in combined_server.py (never use `allow_origins=["*"]`)

---

## 📁 Project Structure

```
DawsOSP/
├── combined_server.py            # ⭐ PRIMARY SERVER (FastAPI entry point)
├── full_ui.html                  # ⭐ PRIMARY UI (React SPA)
├── test_ratings_parse.html       # Buffett ratings testing utility
├── backend/
│   ├── app/
│   │   ├── agents/               # 4 agents (financial_analyst, macro_hound, data_harvester, portfolio)
│   │   ├── api/
│   │   │   ├── executor.py       # Alternative entry point (not used in production)
│   │   │   └── routes/           # Modular API routes (imported by combined_server)
│   │   ├── core/                 # AgentRuntime, PatternOrchestrator
│   │   ├── services/             # Business logic
│   │   └── db/                   # Database layer
│   ├── patterns/                 # 13 pattern definitions (JSON)
│   ├── db/
│   │   ├── schema/               # Database schema files
│   │   └── seeds/                # Seed data
│   └── requirements.txt
├── frontend/
│   └── api-client.js             # API client module for full_ui.html
├── scripts/                      # Utility scripts
├── .legacy/                      # Legacy Streamlit UI (archived)
└── .archive/                     # Archived components
```

---

## 🚦 API Endpoints

### Core

- `GET /` - Serves full_ui.html
- `GET /health` - Health check
- `POST /api/patterns/execute` - Execute pattern (main endpoint)

### Authentication

- `POST /api/auth/login` - Login (JWT)
- `POST /api/auth/refresh` - Refresh token

### Portfolio

- `GET /api/portfolios` - List portfolios
- `GET /api/portfolios/{id}` - Get portfolio details
- `POST /api/portfolios` - Create portfolio

### Analysis

- `GET /api/metrics/{portfolio_id}` - Performance metrics
- `GET /api/macro` - Macro economic data
- `GET /api/alerts` - Alert list

See `/docs` endpoint for complete API documentation.

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# API tests
curl http://localhost:8000/health

# UI tests
# Open browser: http://localhost:8000/
# Test all 18 pages manually
```

---

## 🚀 Deployment (Replit)

DawsOS is deployed on Replit. To run locally:

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@host:5432/dawsos"
export ANTHROPIC_API_KEY="your-key"
export AUTH_JWT_SECRET="your-secret"

# Run the server
python combined_server.py
```

The server will start on `http://localhost:8000/`

---

## 📚 Documentation

### Essential Guides
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - Development guide and patterns
- **[BEST_PRACTICES.md](BEST_PRACTICES.md)** - Development best practices
- **[DATABASE.md](DATABASE.md)** - Database reference and operations
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment instructions
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Comprehensive troubleshooting guide

### Reference Documentation
- **[PATTERNS_REFERENCE.md](docs/reference/PATTERNS_REFERENCE.md)** - Pattern system reference
- **[API_CONTRACT.md](API_CONTRACT.md)** - API endpoint documentation
- **[PRODUCT_SPEC.md](PRODUCT_SPEC.md)** - Product specifications
- **API Docs**: http://localhost:8000/docs (when running)

### Complete Documentation Index
- **[DOCUMENTATION.md](DOCUMENTATION.md)** - Complete documentation index

---

## 🔄 Alternative Entry Points

The application includes a modular backend structure in `backend/app/` that can be used as an alternative entry point:

```bash
# Alternative: Use modular backend (experimental)
cd backend
uvicorn app.api.executor:executor_app --reload --port 8001

# Note: This is NOT the production entry point
# Use combined_server.py for production
```

---

## 🛠️ Development

### Adding New Features

**Recommended Flow:**
1. **Create Pattern** (if needed) - Define JSON pattern in `backend/patterns/`
2. **Add Capability** - Add capability to appropriate agent in `backend/app/agents/`
3. **Register Agent** - Ensure agent is registered in `combined_server.py`
4. **Update UI** - Update `full_ui.html` to use new pattern (if needed)
5. **Test** - Test pattern execution and UI integration

**Example: Adding a New Capability**
```python
# 1. Add capability to agent
@capability(inputs={"portfolio_id": "uuid"}, outputs={"result": "dict"})
async def my_new_capability(self, ctx: RequestCtx, state: Dict, portfolio_id: str, **kwargs):
    # Implementation
    return {"result": "data"}

# 2. Update get_capabilities()
def get_capabilities(self) -> List[str]:
    return [..., "my.new_capability"]

# 3. Use in pattern
{
  "capability": "my.new_capability",
  "args": {"portfolio_id": "{{inputs.portfolio_id}}"},
  "as": "my_result"
}
```

**For detailed development guide, see [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)**

### Code Style

```bash
# Format code
black backend/
isort backend/

# Lint
flake8 backend/
pylint backend/

# Type checking (if using mypy)
mypy backend/
```

**Best Practices:**
- ✅ Use type hints for all functions
- ✅ Use specific exceptions (not broad `Exception`)
- ✅ Use parameterized database queries
- ✅ Use structured logging (not `print()`)
- ✅ Follow naming conventions (see [BEST_PRACTICES.md](BEST_PRACTICES.md))

**For comprehensive best practices, see [BEST_PRACTICES.md](BEST_PRACTICES.md)**

---

## 📊 System Status

Check system health:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "DawsOS",
  "version": "6.0.1",
  "database": "connected",
  "agents": 4,
  "patterns": "available"
}
```

---

## 🔐 Security

- **Authentication**: JWT tokens with 24-hour expiration
- **Authorization**: Role-based access control (ADMIN, MANAGER, USER, VIEWER)
- **Data Protection**: Password hashing (bcrypt), input validation
- **Network Security**: Configure CORS appropriately for production

**Important**: Change default credentials and JWT secret in production!

---

## 🐛 Troubleshooting

**Quick Fixes:**

| Issue | Quick Fix |
|-------|-----------|
| "UI not found" | Ensure `full_ui.html` is in repository root |
| "Database connection failed" | Check `DATABASE_URL` environment variable |
| "Pattern execution failed" | Check agent registration in `combined_server.py` |
| "Invalid credentials" | Verify user exists: `psql $DATABASE_URL -c "SELECT * FROM users;"` |
| "Application won't start" | Check Python version: `python --version` (should be 3.11+) |

**Common Solutions:**

### Database Connection Issues
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT version();"

# Verify PostgreSQL is running
pg_isready -h localhost -p 5432
```

### Pattern Execution Issues
```bash
# Check pattern JSON is valid
python3 -m json.tool backend/patterns/portfolio_overview.json

# Test pattern execution
curl -X POST http://localhost:8000/api/patterns/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pattern_name":"portfolio_overview","inputs":{"portfolio_id":"..."}}'
```

**For comprehensive troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📜 License

Proprietary - All rights reserved

---

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **React** - UI library
- **Anthropic Claude** - AI analysis
- **PostgreSQL + TimescaleDB** - Database
- **Chart.js** - Visualizations

---

## 📞 Support

For issues or questions:
- **Issues**: https://github.com/mwd474747/DawsOSP/issues
- **Documentation**: See [DOCUMENTATION.md](DOCUMENTATION.md) for complete documentation index

---

**DawsOS** - Portfolio Intelligence Platform | Version 6.0.1 | 2025
