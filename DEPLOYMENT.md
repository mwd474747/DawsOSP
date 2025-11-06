# DawsOS Deployment Guide

**Last Updated:** January 14, 2025  
**CI/CD:** Handled by Replit (GitHub Actions workflows archived - see `.archive/ci-cd/`)  
**Status:** ✅ Production Ready

---

## 🚀 Deployment Overview

DawsOS is deployed on Replit. This guide covers deployment on Replit and local development.

**Note:** GitHub Actions workflows have been archived (January 14, 2025) as they were incompatible with the current application structure. CI/CD is handled by Replit's deployment system. Workflows can be restored/updated from `.archive/ci-cd/github-workflows/` if needed in the future.

---

## 📋 Prerequisites

### Required
- Replit account (for production) OR local Python 3.11+ environment
- PostgreSQL 14+ with TimescaleDB extension
- Git repository access

### Optional (for full functionality)
- API keys for data providers:
  - FMP API key (for fundamentals)
  - Polygon API key (for prices)
  - FRED API key (for economic data)
  - Anthropic API key (for AI insights)

---

## 🔧 Environment Variables

### Required Variables

**⚠️ CRITICAL: These must be set for the application to start**

```bash
# Database connection (REQUIRED)
DATABASE_URL=postgresql://user:password@host:5432/dawsos

# JWT authentication secret (REQUIRED - generate securely!)
# Generate with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
AUTH_JWT_SECRET=<generated-secure-random-key>
```

### Optional Variables

```bash
# AI-powered insights (optional)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Economic data (optional)
FRED_API_KEY=your-fred-api-key

# Market data (optional)
FMP_API_KEY=your-fmp-key
POLYGON_API_KEY=your-polygon-key

# CORS allowed origins (comma-separated)
CORS_ORIGINS=http://localhost:8000,https://yourdomain.com

# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Environment (development, production)
ENVIRONMENT=production
```

---

## 🚀 Replit Deployment

### Step 1: Push Code to Replit

**Option A: Import Repository**
1. Go to Replit
2. Click "Import from GitHub"
3. Enter repository URL: `https://github.com/mwd474747/DawsOSP.git`
4. Click "Import"

**Option B: Push to Replit Git**
```bash
# Add Replit remote
git remote add replit https://replit.com/github/mwd474747/DawsOSP

# Push to Replit
git push replit main
```

---

### Step 2: Set Environment Variables

1. **Go to Secrets tab** in Replit
2. **Add all required environment variables:**
   - `DATABASE_URL` - PostgreSQL connection string
   - `AUTH_JWT_SECRET` - Secure JWT secret (generate with command above)
   - Optional: API keys for data providers

**⚠️ SECURITY WARNING:**
- Never commit secrets to Git
- Use Replit Secrets tab for all sensitive values
- Generate secure random keys (don't use "your-secret")

---

### Step 3: Install Dependencies

```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Verify installation
python -c "import fastapi; print('FastAPI installed')"
```

---

### Step 4: Initialize Database

```bash
# Run database initialization script
python backend/db/init_database.sh

# Or run migrations manually
psql $DATABASE_URL -f backend/db/schema/001_portfolios_lots_transactions.sql
psql $DATABASE_URL -f backend/db/schema/002_pricing.sql
# ... continue with all schema files
```

**Verify Database:**
```bash
# Check tables exist
psql $DATABASE_URL -c "\dt"

# Check TimescaleDB extension
psql $DATABASE_URL -c "SELECT * FROM pg_extension WHERE extname='timescaledb';"
```

---

### Step 5: Start the Server

**Replit will automatically run:**
```bash
python combined_server.py
```

**Or set run command manually:**
1. Go to Replit settings
2. Set run command: `python combined_server.py`
3. Click "Run"

**Verify Server:**
```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"DawsOS","version":"6.0.1","database":"connected","agents":4,"patterns":"available"}
```

---

## 💻 Local Development

### Step 1: Clone Repository

```bash
git clone https://github.com/mwd474747/DawsOSP.git
cd DawsOSP
```

---

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

---

### Step 3: Set Up Database

```bash
# Create database
createdb dawsos

# Enable TimescaleDB extension
psql -d dawsos -c "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"

# Run initialization script
./backend/db/init_database.sh
```

---

### Step 4: Set Environment Variables

```bash
# Create .env file (optional - can use export instead)
cat > .env << EOF
DATABASE_URL=postgresql://localhost/dawsos
AUTH_JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
ANTHROPIC_API_KEY=sk-ant-...  # Optional
FRED_API_KEY=...  # Optional
EOF

# Or export directly
export DATABASE_URL="postgresql://localhost/dawsos"
export AUTH_JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

---

### Step 5: Start Development Server

```bash
# Start server
python combined_server.py

# Server starts on http://localhost:8000/
```

**Verify:**
- Open browser: http://localhost:8000/
- Login: michael@dawsos.com / mozzuq-byfqyQ-5tefvu
- Check health: http://localhost:8000/health

---

## 📊 Monitoring

### Health Checks

**Application Health:**
```bash
# Check server status
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "service": "DawsOS",
  "version": "6.0.1",
  "database": "connected",
  "agents": 4,
  "patterns": "available"
}
```

**Database Health:**
```bash
# Check database connection
psql $DATABASE_URL -c "SELECT version();"

# Check active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE datname='dawsos';"
```

---

### Application Logs

**View Logs:**
```bash
# Follow logs in real-time
tail -f logs/app.log

# View recent errors
tail -100 logs/app.log | grep -i error

# View pattern executions
grep "pattern.*execute" logs/app.log
```

**Log Levels:**
- `DEBUG` - Detailed debugging information
- `INFO` - General informational messages
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical errors

**Set Log Level:**
```bash
export LOG_LEVEL=DEBUG  # For detailed debugging
export LOG_LEVEL=INFO   # For production (default)
```

---

### Performance Monitoring

**API Response Times:**
```bash
# Time API requests
time curl http://localhost:8000/health

# Check slow queries
psql $DATABASE_URL -c "SELECT query, duration FROM pg_stat_statements ORDER BY duration DESC LIMIT 10;"
```

**Database Performance:**
```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## 💾 Backup Strategy

### Database Backups

**Automated Daily Backups:**
```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="/backups/dawsos"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/dawsos_backup_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
pg_dump $DATABASE_URL > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup created: $BACKUP_FILE.gz"
```

**Manual Backup:**
```bash
# Create backup
pg_dump $DATABASE_URL > dawsos_backup_$(date +%Y%m%d).sql

# Restore backup
psql $DATABASE_URL < dawsos_backup_20250114.sql
```

---

### Code Backups

**Git-based backups:**
- All code is version controlled in Git
- Regular commits ensure code history
- Use tags for releases: `git tag -a v6.0.1 -m "Release 6.0.1"`

---

### Configuration Backups

**Backup Environment Variables:**
```bash
# Export all environment variables
env | grep -E "DATABASE_URL|AUTH_JWT_SECRET|.*_API_KEY" > .env.backup

# Restore (carefully - don't commit to Git!)
source .env.backup
```

**⚠️ SECURITY: Never commit .env files to Git!**

---

## 🔄 Rollback Procedures

### Code Rollback

**Git Rollback:**
```bash
# View recent commits
git log --oneline -10

# Rollback to previous commit
git reset --hard <previous-commit-hash>

# Force push (if needed - be careful!)
git push origin main --force
```

**Replit Rollback:**
1. Go to Replit version history
2. Select previous working version
3. Restore that version

---

### Database Rollback

**Migration Rollback:**
```bash
# Check migration status
psql $DATABASE_URL -c "SELECT * FROM schema_migrations ORDER BY version DESC LIMIT 5;"

# Rollback specific migration (if migration supports it)
# Note: Most migrations don't support rollback - restore from backup instead
```

**Restore from Backup:**
```bash
# Stop application
pkill -f combined_server.py

# Restore database
psql $DATABASE_URL < dawsos_backup_20250114.sql

# Restart application
python combined_server.py
```

---

## ✅ Production Checklist

### Before Deployment

- [ ] All environment variables set (DATABASE_URL, AUTH_JWT_SECRET)
- [ ] Database initialized and migrations run
- [ ] Default credentials changed (if applicable)
- [ ] Secure JWT secret generated (not "your-secret")
- [ ] API keys configured (if using external data)
- [ ] CORS settings configured appropriately
- [ ] Logging level set to INFO or WARNING (not DEBUG)
- [ ] Health check endpoint working
- [ ] All patterns execute successfully
- [ ] Database backups configured

### After Deployment

- [ ] Health check returns healthy status
- [ ] Login works with production credentials
- [ ] All 13 patterns execute successfully
- [ ] Database queries perform well
- [ ] Error logs are clean (no unexpected errors)
- [ ] Monitoring is set up
- [ ] Backups are running
- [ ] Documentation is up to date

---

## 🚨 Disaster Recovery

### Database Corruption

**Symptoms:**
- Database queries fail
- Data inconsistencies
- Application errors

**Recovery:**
1. Stop application
2. Restore from most recent backup
3. Verify data integrity
4. Restart application

---

### Application Failure

**Symptoms:**
- Server won't start
- 500 errors
- Pattern execution fails

**Recovery:**
1. Check application logs
2. Verify environment variables
3. Check database connectivity
4. Rollback to previous working version if needed

---

### Data Loss

**Symptoms:**
- Missing data
- Incomplete records
- Corrupted data

**Recovery:**
1. Stop application immediately
2. Restore from most recent backup
3. Verify data integrity
4. Investigate root cause
5. Implement prevention measures

---

## 📚 Additional Resources

- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[DATABASE.md](DATABASE.md)** - Database operations
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - Development guide

---

**Last Updated:** January 14, 2025
