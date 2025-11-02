# Developer Setup

Complete setup guide for DawsOS development.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ with TimescaleDB extension
- (Optional) Anthropic API key for AI features
- (Optional) FRED API key for economic data

**Note:** Node.js is NOT required - the frontend uses React UMD builds from CDN (no build step).

## Quick Start

1. **Clone repository**
   ```bash
   git clone https://github.com/mwd474747/DawsOSP.git
   cd DawsOSP
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r backend/requirements.txt
   ```

3. **Configure database**
   ```bash
   createdb dawsos
   export DATABASE_URL="postgresql://localhost/dawsos"
   ```

4. **Set environment variables** (optional)
   ```bash
   export ANTHROPIC_API_KEY="your-api-key"  # For AI features
   export FRED_API_KEY="your-fred-key"      # For economic data
   export AUTH_JWT_SECRET="dev-secret"      # For authentication
   ```

5. **Start the application**
   ```bash
   python combined_server.py
   ```

6. **Access the application**
   - UI: http://localhost:8000/
   - API Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

See main [README.md](../README.md) for detailed instructions.
