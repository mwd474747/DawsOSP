# DawsOS Launch Guide

## Quick Launch (5 minutes)

### 1. Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Node.js 18+

### 2. Setup
```bash
# Clone and setup
git clone <repository-url>
cd DawsOSP

# Backend setup
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Frontend setup
cd dawsos-ui
npm install
cd ..
```

### 3. Start Services
```bash
# Terminal 1: Backend
./backend/run_api.sh

# Terminal 2: Frontend
cd dawsos-ui && npm run dev
```

### 4. Access System
- **Frontend**: http://localhost:3002
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 5. Login
- **Email**: michael@dawsos.com
- **Password**: mozzuq-byfqyQ-5tefvu

## What's Next?

1. **Explore the UI** - Navigate through different sections
2. **Test APIs** - Use the API documentation at /docs
3. **Create Data** - Add portfolios and test features
4. **Customize** - Modify settings and preferences

## Need Help?

- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Development Guide](DEVELOPMENT_GUIDE.md)
- [Architecture Guide](ARCHITECTURE.md)
