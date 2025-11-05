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
  - **Note:** Phase 3 consolidation complete (November 3, 2025):
    - Week 1: OptimizerAgent → FinancialAnalyst ✅ COMPLETE
    - Week 2: RatingsAgent → FinancialAnalyst ✅ COMPLETE
    - Week 3: ChartsAgent → FinancialAnalyst ✅ COMPLETE
    - Week 4: AlertsAgent → MacroHound ✅ COMPLETE
    - Week 5: ReportsAgent → DataHarvester ✅ COMPLETE
    - Week 6: Legacy agent cleanup ✅ COMPLETE
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
│   │   ├── agents/               # 9 agents (financial_analyst, macro_hound, etc.)
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

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[PRODUCT_SPEC.md](PRODUCT_SPEC.md)** - Product specifications
- **[DATABASE.md](DATABASE.md)** - Database reference and operations
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - Development guide
- **[PATTERNS_REFERENCE.md](docs/reference/PATTERNS_REFERENCE.md)** - Pattern system reference
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment instructions
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **API Docs**: http://localhost:8000/docs (when running)

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

1. **Backend API**: Add route to `backend/app/api/routes/` or `combined_server.py`
2. **Business Logic**: Add to appropriate agent in `backend/app/agents/`
3. **UI**: Update `full_ui.html` (React components)
4. **Pattern**: Define new pattern in `backend/patterns/` if needed

### Code Style

```bash
# Format code
black backend/
isort backend/

# Lint
flake8 backend/
pylint backend/
```

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

### "UI not found" error

**Solution**: Ensure `full_ui.html` is in repository root

### "Database connection failed"

**Solution**: Check `DATABASE_URL` environment variable

```bash
export DATABASE_URL="postgresql://user:pass@localhost/dawsos"
```

### "Pattern execution failed"

**Solution**: Check agent registration in `combined_server.py`

### Application won't start

**Solution**: Check Python version and dependencies

```bash
python --version  # Should be 3.11+
pip install -r backend/requirements.txt
```

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
