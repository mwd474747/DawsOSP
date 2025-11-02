# DawsOS Deployment Guide

## Replit Deployment

DawsOS is deployed on Replit. This guide covers deployment on Replit.

### Prerequisites
- Replit account
- PostgreSQL database (provided by Replit or external)
- API keys for data providers (optional)

### Environment Variables
Set these in Replit's Secrets tab:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dawsos

# Authentication
AUTH_JWT_SECRET=your-secure-jwt-secret

# API Keys (Optional - for real data)
FMP_API_KEY=your-fmp-key
POLYGON_API_KEY=your-polygon-key
FRED_API_KEY=your-fred-key
NEWS_API_KEY=your-news-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### Deployment Steps

1. **Push code to Replit**
   - Import repository or push to Replit Git

2. **Set environment variables**
   - Go to Secrets tab
   - Add all required environment variables

3. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Run migrations** (if needed)
   ```bash
   python backend/init_db.py
   ```

5. **Start the server**
   - Replit will automatically run `combined_server.py`
   - Or set run command: `python combined_server.py`

### Local Development

For local development:

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://localhost/dawsos"
export AUTH_JWT_SECRET="dev-secret"

# Run server
python combined_server.py
```

## Monitoring

- Application logs
- Database performance
- API response times
- Error rates
- User activity

## Backup Strategy

- Database backups (daily)
- Code backups (via Git)
- Configuration backups
- Disaster recovery procedures
