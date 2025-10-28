# DawsOS - AI-Powered Portfolio Management

DawsOS is a comprehensive portfolio management system built with FastAPI and Next.js.

## Quick Start

1. **Setup Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r backend/requirements.txt
   ```

2. **Start Backend**
   ```bash
   ./backend/run_api.sh
   ```

3. **Start Frontend**
   ```bash
   cd dawsos-ui && npm run dev
   ```

4. **Access System**
   - Frontend: http://localhost:3002
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Authentication

- **Email**: michael@dawsos.com
- **Password**: mozzuq-byfqyQ-5tefvu

## Architecture

- **Backend**: FastAPI with PostgreSQL
- **Frontend**: Next.js with TypeScript
- **Authentication**: JWT-based with RBAC
- **Database**: PostgreSQL with TimescaleDB

## Documentation

- [Product Specification](PRODUCT_SPEC.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Development Guide](DEVELOPMENT_GUIDE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Troubleshooting](TROUBLESHOOTING.md)

## License

Proprietary - All rights reserved
