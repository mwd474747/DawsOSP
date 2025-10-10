# DawsOS Deployment Checklist

**System Version**: 2.0 (Trinity Architecture)
**Status**: Production Ready (A+ Grade - 98/100)
**Last Updated**: October 9, 2025

---

## Pre-Deployment Checklist

### ✅ System Validation

#### Code Quality
- [ ] All tests passing: `pytest dawsos/tests/validation/`
- [ ] Pattern linter: 0 errors: `python3 scripts/lint_patterns.py`
- [ ] No syntax errors: `python3 -m py_compile dawsos/**/*.py`
- [ ] Type hints validated (optional): `mypy dawsos/` (if using mypy)

#### Security
- [ ] No secrets in codebase: `git grep -i "api_key\|password\|secret" | grep -v ".env.example"`
- [ ] `.env.example` sanitized (no real keys)
- [ ] `.gitignore` includes `.env`, `storage/`, `*.pyc`, `__pycache__/`
- [ ] Input validation active (check `core/universal_executor.py`)
- [ ] Secret detection enabled (check `core/pattern_engine.py`)

#### Architecture
- [ ] Trinity compliance: 100% (verify with compliance dashboard)
- [ ] Registry bypass warnings: 0 (check telemetry)
- [ ] All 15 agents registered: `python3 -c "from dawsos.main import runtime; print(len(runtime._agents))"`
- [ ] All 26 datasets loaded: `python3 -c "from dawsos.core.knowledge_loader import KnowledgeLoader; print(len(KnowledgeLoader().datasets))"`

#### Documentation
- [ ] README.md accurate and up-to-date
- [ ] SYSTEM_STATUS.md reflects current state
- [ ] CLAUDE.md has latest metrics
- [ ] API keys documented in .env.example
- [ ] Troubleshooting guide complete

#### Dependencies
- [ ] `requirements.txt` up-to-date
- [ ] Python version documented (3.10+, 3.13+ recommended)
- [ ] No deprecated dependencies: `pip list --outdated`

---

## Deployment Steps

### Step 1: Environment Setup

#### 1.1 Server Requirements
- [ ] Python 3.10+ installed (check: `python3 --version`)
- [ ] Sufficient disk space (minimum 500MB for app + storage)
- [ ] Network access for API calls (if using live data)
- [ ] Port 8501 available (or configure alternative)

#### 1.2 Clone Repository
```bash
git clone <your-repo-url>
cd DawsOSB
```

#### 1.3 Create Virtual Environment
```bash
python3 -m venv dawsos/venv
source dawsos/venv/bin/activate  # On Windows: dawsos\venv\Scripts\activate
```

#### 1.4 Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 1.5 Environment Variables (Optional)
```bash
# Copy example template
cp .env.example .env

# Edit with your API keys (ONLY if using live data)
nano .env

# Recommended variables:
# ANTHROPIC_API_KEY=<your_key>    # For live Claude responses
# FRED_API_KEY=<your_key>         # For economic data (free, unlimited)
# FMP_API_KEY=<your_key>          # For stock quotes (250/day free)
# NEWSAPI_KEY=<your_key>          # For news (100/day free)
# TRINITY_STRICT_MODE=true        # (Optional) Enforce strict compliance
```

**Note**: System works fully without API keys using cached data.

---

### Step 2: Pre-Launch Validation

#### 2.1 Verify Installation
```bash
# Check Python environment
which python3
python3 --version  # Should be 3.10+

# Check dependencies
pip list | grep -E "streamlit|anthropic|networkx|requests"

# Verify file structure
ls -l dawsos/
# Should see: agents/, core/, patterns/, storage/, ui/, main.py
```

#### 2.2 Test Core Systems
```bash
# Test pattern linter
python3 scripts/lint_patterns.py
# Expected: 48 patterns, 0 errors, 1 warning

# Test knowledge loader
python3 -c "
from dawsos.core.knowledge_loader import KnowledgeLoader
loader = KnowledgeLoader()
print(f'Datasets loaded: {len(loader.datasets)}')
"
# Expected: Datasets loaded: 26

# Test agent registration
python3 -c "
from dawsos.core.agent_runtime import AgentRuntime
runtime = AgentRuntime()
print(f'Agents registered: {len(runtime._agents)}')
"
# Expected: Agents registered: 15
```

#### 2.3 Syntax Validation
```bash
# Check critical files for syntax errors
python3 -m py_compile dawsos/main.py
python3 -m py_compile dawsos/core/universal_executor.py
python3 -m py_compile dawsos/core/pattern_engine.py
python3 -m py_compile dawsos/core/agent_runtime.py
# Should complete with no output (success)
```

---

### Step 3: Launch Application

#### 3.1 Start Streamlit (Quick Launch)
```bash
# Using launch script (recommended)
./start.sh

# Or manual launch
dawsos/venv/bin/streamlit run dawsos/main.py --server.port=8501
```

#### 3.2 Verify Launch
```bash
# Check if process is running
ps aux | grep streamlit

# Check port binding
lsof -i:8501
# Should show streamlit process
```

#### 3.3 Access Application
- Open browser: http://localhost:8501
- Expected: DawsOS Trinity Dashboard loads

---

### Step 4: Initial Testing

#### 4.1 UI Functionality
- [ ] Trinity Dashboard tab loads
- [ ] Chat interface responds
- [ ] Pattern library visible
- [ ] Quick actions work
- [ ] Sidebar renders correctly

#### 4.2 Pattern Execution
- [ ] Test simple query: "What is the market regime?"
- [ ] Verify response appears
- [ ] Check execution logs (no errors)
- [ ] Test pattern with template output

#### 4.3 Data Access
- [ ] Navigate to Knowledge Graph tab
- [ ] Verify graph statistics show (96K+ nodes)
- [ ] Test graph search/query
- [ ] Check dataset loading (no errors)

#### 4.4 API Health (if using API keys)
- [ ] Navigate to API Health tab
- [ ] Verify API status (green = configured, yellow = fallback)
- [ ] Check fallback statistics
- [ ] Test API refresh

---

## Post-Deployment Checklist

### ✅ System Health

#### Monitor Application
- [ ] No error messages in terminal
- [ ] No warnings in Streamlit UI
- [ ] Response times <5 seconds (typical queries)
- [ ] Memory usage stable (<500MB typical)

#### Verify Core Systems
```bash
# Health check
curl http://localhost:8501/_stcore/health
# Expected: ok

# Check logs (if logging to file)
tail -f dawsos/storage/logs/*.log
# Look for: No ERROR messages, INFO/WARNING acceptable
```

#### Test Key Features
- [ ] Pattern matching works (try 5 different queries)
- [ ] Agent execution successful (check registry telemetry)
- [ ] Knowledge graph queries work
- [ ] Governance dashboard loads
- [ ] Trinity compliance dashboard shows 100%

---

### ✅ Monitoring Setup

#### Application Monitoring
- [ ] Set up process monitoring (systemd, supervisor, or PM2)
- [ ] Configure auto-restart on failure
- [ ] Set up log rotation (if not using default)
- [ ] Monitor disk space (storage/ directory grows with backups)

#### Performance Metrics
- [ ] Track pattern execution success rate (Goal: >95%)
- [ ] Monitor registry bypass warnings (Goal: 0)
- [ ] Check API fallback counts (Goal: minimize)
- [ ] Measure response times (Goal: <5s)

#### Alerts (Optional)
- [ ] Error rate threshold alert
- [ ] Disk space alert (when storage/ >80%)
- [ ] API quota alerts (if using paid APIs)
- [ ] Uptime monitoring

---

### ✅ Backup Configuration

#### Automated Backups
- [ ] Verify graph backup rotation (30-day)
  - Check: `ls -lh dawsos/storage/backups/`
  - Should see dated backup files

- [ ] Verify decisions file rotation (5MB threshold)
  - Check: `ls -lh dawsos/storage/agent_memory/archive/`

#### Manual Backup Schedule
```bash
# Create weekly full backup (recommended)
# Add to cron: 0 2 * * 0 /path/to/backup.sh

#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d)
tar -czf /backups/dawsos-backup-$DATE.tar.gz /path/to/DawsOSB/dawsos/storage/
find /backups/ -name "dawsos-backup-*.tar.gz" -mtime +30 -delete
```

#### Test Restore Procedure
```bash
# Test restore from backup (dry run)
tar -tzf dawsos-backup-20251009.tar.gz | head -20
# Verify files look correct

# Actual restore (if needed)
tar -xzf dawsos-backup-20251009.tar.gz -C /path/to/restore/
```

---

### ✅ Documentation

#### Update Documentation
- [ ] Document server details (hostname, port, credentials)
- [ ] Create runbook for common operations
- [ ] Document backup/restore procedures
- [ ] Create incident response guide

#### Share Access
- [ ] Provide URL to users: http://<server>:8501
- [ ] Share user guide (README.md Quick Start)
- [ ] Provide support contact information
- [ ] Share troubleshooting guide

---

## Production Maintenance

### Daily Tasks
- [ ] Check application status (is it running?)
- [ ] Review error logs (any critical issues?)
- [ ] Monitor disk space (storage/ directory)

### Weekly Tasks
- [ ] Review pattern execution metrics
- [ ] Check API usage (if using paid APIs)
- [ ] Verify backups are running
- [ ] Test key functionality (5-10 test queries)

### Monthly Tasks
- [ ] Full system backup (manual)
- [ ] Review and archive old backups
- [ ] Update dependencies: `pip list --outdated`
- [ ] Review and update patterns (if needed)
- [ ] Update knowledge datasets (if needed)

### Quarterly Tasks
- [ ] Security review (check for vulnerabilities)
- [ ] Performance optimization (if needed)
- [ ] Documentation update
- [ ] User feedback review

---

## Rollback Procedure

### If Deployment Fails

#### Quick Rollback
```bash
# Stop current application
pkill -f streamlit

# Switch to previous version
git checkout <previous-commit-hash>

# Reinstall dependencies (if changed)
pip install -r requirements.txt

# Restart application
./start.sh
```

#### Full Rollback
```bash
# Stop application
pkill -f streamlit

# Remove new deployment
rm -rf DawsOSB/

# Restore from backup
tar -xzf dawsos-backup-<date>.tar.gz

# Navigate to restored directory
cd DawsOSB/

# Activate venv and restart
source dawsos/venv/bin/activate
./start.sh
```

---

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check Python version
python3 --version  # Must be 3.10+

# Check dependencies
pip install -r requirements.txt

# Check port availability
lsof -i:8501
# If occupied: lsof -ti:8501 | xargs kill -9

# Check for syntax errors
python3 -m py_compile dawsos/main.py
```

#### Import Errors
```bash
# Verify venv is activated
which python3
# Should point to dawsos/venv/bin/python3

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check PYTHONPATH (should not be set)
echo $PYTHONPATH
# Should be empty or not set
```

#### Pattern Execution Fails
```bash
# Run pattern linter
python3 scripts/lint_patterns.py

# Check logs
tail -f dawsos/storage/logs/*.log

# Verify knowledge loader
python3 -c "from dawsos.core.knowledge_loader import KnowledgeLoader; print(len(KnowledgeLoader().datasets))"
```

#### Memory Issues
```bash
# Check memory usage
free -h  # Linux
top -l 1 | grep PhysMem  # macOS

# Restart application (clears cache)
pkill -f streamlit
./start.sh
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more details.

---

## Support

### Resources
- **Documentation**: See README.md and docs/ directory
- **Troubleshooting**: TROUBLESHOOTING.md
- **System Status**: SYSTEM_STATUS.md
- **Completion Report**: COMPLETION_FINAL.md

### Monitoring Dashboards
- **Trinity Dashboard**: http://localhost:8501 (Overview, Compliance)
- **Governance**: http://localhost:8501 (Data Quality, Policy)
- **API Health**: http://localhost:8501 (API Status, Fallbacks)

### Health Checks
```bash
# Application health
curl http://localhost:8501/_stcore/health

# Pattern validation
python3 scripts/lint_patterns.py

# Knowledge loader
python3 -c "from dawsos.core.knowledge_loader import KnowledgeLoader; print(f'Datasets: {len(KnowledgeLoader().datasets)}')"

# Agent registration
python3 -c "from dawsos.main import runtime; print(f'Agents: {len(runtime._agents)}')"
```

---

## Deployment Completion

### Final Verification

- [ ] Application running and accessible
- [ ] All tests passing
- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] Documentation complete
- [ ] Users notified
- [ ] Support plan in place

**Deployment Status**: ✅ COMPLETE

---

**Document Version**: 1.0
**Status**: Production Ready
**Last Updated**: October 9, 2025
**Prepared By**: Agent 6 (Documentation Finalizer)
