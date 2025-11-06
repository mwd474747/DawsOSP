# DawsOS Troubleshooting Guide

**Last Updated:** January 14, 2025  
**Purpose:** Comprehensive troubleshooting guide for common issues and debugging techniques

---

## 🔍 Quick Diagnosis

### Health Check
```bash
# Check if server is running
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"DawsOS","version":"6.0.1","database":"connected","agents":4,"patterns":"available"}
```

### Common Symptoms → Solutions

| Symptom | Likely Cause | Quick Fix |
|---------|--------------|-----------|
| "Database connection failed" | DATABASE_URL not set or incorrect | Check `echo $DATABASE_URL` |
| "Invalid credentials" | Wrong password or user doesn't exist | Check database: `SELECT * FROM users WHERE email='...'` |
| "Pattern execution failed" | Agent not registered or capability missing | Check `combined_server.py` agent registration |
| "Internal server error" | Check application logs | `tail -f logs/app.log` |
| "Failed to fetch" | Backend not running or CORS issue | Check `python combined_server.py` is running |

---

## 🔐 Authentication Issues

### Problem: "Invalid credentials" error

**Symptoms:**
- Login fails with "Invalid credentials"
- JWT token generation fails

**Diagnosis:**
```bash
# Check if user exists
psql $DATABASE_URL -c "SELECT email, role FROM users WHERE email='michael@dawsos.com';"

# Check password hash format
psql $DATABASE_URL -c "SELECT email, LEFT(password_hash, 20) as hash_preview FROM users;"
```

**Solutions:**
1. **Verify email and password**
   - Default dev: `michael@dawsos.com` / `mozzuq-byfqyQ-5tefvu`
   - Check password length (8+ characters)

2. **Check password hash**
   ```python
   # Generate new password hash
   python3 -c "import bcrypt; print(bcrypt.hashpw(b'YOUR_PASSWORD', bcrypt.gensalt(12)).decode())"
   
   # Update in database
   psql $DATABASE_URL -c "UPDATE users SET password_hash='<new-hash>' WHERE email='michael@dawsos.com';"
   ```

3. **Verify user exists**
   ```sql
   SELECT id, email, role FROM users WHERE email='michael@dawsos.com';
   ```

---

### Problem: "Missing Authorization header" error

**Symptoms:**
- API requests return 401 Unauthorized
- Token validation fails

**Diagnosis:**
```bash
# Check token format
echo $TOKEN | cut -d. -f1 | base64 -d  # Should show JWT header

# Check token expiration
python3 -c "import jwt; token='$TOKEN'; print(jwt.decode(token, options={'verify_signature': False}))"
```

**Solutions:**
1. **Include Authorization header**
   ```bash
   curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/portfolios
   ```

2. **Verify token is valid and not expired**
   - Tokens expire after 24 hours
   - Use `/api/auth/refresh` to get new token

3. **Check token format**
   - Should be: `Bearer <token>`
   - Token should be JWT format (3 parts separated by dots)

4. **Verify AUTH_JWT_SECRET is set**
   ```bash
   echo $AUTH_JWT_SECRET  # Should be 32+ character random string
   ```

---

## 🗄️ Database Issues

### Problem: "Database connection failed"

**Symptoms:**
- Application won't start
- "Connection refused" errors
- Pool registration fails

**Diagnosis:**
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test connection directly
psql $DATABASE_URL -c "SELECT version();"

# Check PostgreSQL is running
pg_isready -h localhost -p 5432
```

**Solutions:**
1. **Check DATABASE_URL environment variable**
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost:5432/dawsos"
   ```

2. **Verify PostgreSQL is running**
   ```bash
   # Local
   pg_isready -h localhost -p 5432
   
   # Docker (if using)
   docker ps | grep postgres
   ```

3. **Check database credentials**
   ```bash
   psql $DATABASE_URL -c "SELECT current_user, current_database();"
   ```

4. **Ensure database exists**
   ```bash
   createdb dawsos  # If doesn't exist
   ```

5. **Check pool registration**
   ```python
   # In Python shell
   from backend.app.db.connection import get_db_pool
   pool = get_db_pool()
   print(f"Pool: {pool}")  # Should not be None
   ```

---

### Problem: "Table does not exist"

**Symptoms:**
- SQL errors: "relation does not exist"
- Migration errors

**Diagnosis:**
```sql
-- Check if table exists
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name = 'portfolios';

-- List all tables
\dt

-- Check migration status
SELECT * FROM schema_migrations ORDER BY version DESC LIMIT 5;
```

**Solutions:**
1. **Run database migrations**
   ```bash
   # Run all migrations
   psql $DATABASE_URL -f backend/db/migrations/001_core_schema.sql
   psql $DATABASE_URL -f backend/db/migrations/002_constraints_indexes.sql
   # ... continue with all migrations
   ```

2. **Check schema files**
   ```bash
   ls -la backend/db/schema/
   ```

3. **Verify database initialization**
   ```bash
   python backend/db/init_database.sh
   ```

---

### Problem: "Pool registration issue"

**Symptoms:**
- Agents can't access database
- `AttributeError: 'NoneType' object has no attribute 'acquire'`
- Module instance separation errors

**Diagnosis:**
```python
# Check pool storage
import sys
storage = sys.modules.get('__dawsos_db_pool_storage__')
print(f"Pool storage: {storage}")
print(f"Pool: {storage.pool if storage else None}")
```

**Solutions:**
1. **Verify pool is registered in combined_server.py**
   ```python
   # Should be in combined_server.py startup
   from backend.app.db.connection import register_external_pool
   register_external_pool(db_pool)
   ```

2. **Check sys.modules storage**
   - Pool should be stored in `sys.modules['__dawsos_db_pool_storage__']`
   - This ensures cross-module access

3. **Restart application**
   - Pool registration happens at startup
   - Restart if pool is None

---

## 🔌 API Issues

### Problem: "Internal server error"

**Symptoms:**
- HTTP 500 errors
- Generic error messages
- Pattern execution fails

**Diagnosis:**
```bash
# Check application logs
tail -f logs/app.log

# Check for specific errors
grep -i "error\|exception\|traceback" logs/app.log | tail -20

# Check server status
curl http://localhost:8000/health
```

**Solutions:**
1. **Check application logs**
   ```bash
   # View recent errors
   tail -100 logs/app.log | grep -i error
   
   # Follow logs in real-time
   tail -f logs/app.log
   ```

2. **Verify all services are running**
   ```bash
   # Check if server is running
   ps aux | grep combined_server.py
   
   # Check port is listening
   lsof -i :8000
   ```

3. **Check database connectivity**
   ```bash
   psql $DATABASE_URL -c "SELECT 1;"
   ```

4. **Review error details**
   - Check traceback in logs
   - Look for specific error messages
   - Check for missing dependencies

---

### Problem: "Pattern execution failed"

**Symptoms:**
- Pattern returns error
- Capability not found
- Agent routing fails

**Diagnosis:**
```bash
# Test pattern execution
curl -X POST http://localhost:8000/api/patterns/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pattern_name":"portfolio_overview","inputs":{"portfolio_id":"..."}}'

# Check pattern file exists
ls -la backend/patterns/portfolio_overview.json

# Validate JSON
python3 -m json.tool backend/patterns/portfolio_overview.json
```

**Solutions:**
1. **Check agent registration in combined_server.py**
   ```python
   # Should register all 4 agents:
   # - FinancialAnalyst
   # - MacroHound
   # - DataHarvester
   # - ClaudeAgent
   ```

2. **Verify capability exists**
   ```python
   # Check if capability is registered
   from backend.app.core.agent_runtime import get_agent_runtime
   runtime = get_agent_runtime()
   agent = runtime.get_agent_for_capability("ledger.positions")
   print(f"Agent: {agent}")  # Should not be None
   ```

3. **Check pattern JSON is valid**
   ```bash
   python3 -m json.tool backend/patterns/portfolio_overview.json
   ```

4. **Verify pattern inputs**
   - Check required inputs are provided
   - Verify input types match pattern definition
   - Check for template substitution errors

---

### Problem: "Capability not found"

**Symptoms:**
- `CapabilityNotFoundError`
- Agent routing fails
- Pattern step fails

**Diagnosis:**
```python
# List all registered capabilities
from backend.app.core.agent_runtime import get_agent_runtime
runtime = get_agent_runtime()
for agent_name, agent in runtime._agents.items():
    print(f"{agent_name}: {agent.get_capabilities()}")
```

**Solutions:**
1. **Check capability naming**
   - Format: `agent.capability` (e.g., `ledger.positions`)
   - Agent name must match registered agent name
   - Capability must exist in agent

2. **Verify agent is registered**
   ```python
   # In combined_server.py
   financial_analyst = FinancialAnalyst("financial_analyst", services)
   _agent_runtime.register_agent(financial_analyst)
   ```

3. **Check capability method exists**
   ```python
   # In agent file
   async def ledger_positions(self, ctx, state, **kwargs):
       # Implementation
   ```

---

## 🎨 Frontend Issues

### Problem: "Failed to fetch" error

**Symptoms:**
- Browser console shows network errors
- API calls fail
- CORS errors

**Diagnosis:**
```javascript
// Check browser console
console.log('API URL:', window.API_BASE_URL);

// Check network tab
// Look for failed requests (red status codes)
```

**Solutions:**
1. **Check backend API is running**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Verify API URL configuration**
   ```javascript
   // In full_ui.html
   const API_BASE_URL = 'http://localhost:8000';
   ```

3. **Check network connectivity**
   - Verify firewall settings
   - Check proxy configuration
   - Test with curl first

4. **Review browser console**
   - Check for CORS errors
   - Look for authentication errors
   - Check for JavaScript errors

---

### Problem: "UI not found" error

**Symptoms:**
- 404 on root path
- `full_ui.html` not served

**Solutions:**
1. **Ensure full_ui.html is in repository root**
   ```bash
   ls -la full_ui.html
   ```

2. **Check combined_server.py serves UI**
   ```python
   # Should have:
   @app.get("/")
   async def serve_ui():
       return FileResponse("full_ui.html")
   ```

---

## 🐛 Debugging Techniques

### Log Analysis

**Enable Debug Logging:**
```python
# In combined_server.py or environment
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Common Log Patterns:**
```bash
# Find errors
grep -i "error\|exception" logs/app.log

# Find pattern executions
grep "pattern.*execute" logs/app.log

# Find database queries
grep "SELECT\|INSERT\|UPDATE" logs/app.log

# Find slow operations
grep "duration\|latency" logs/app.log
```

---

### Pattern Execution Debugging

**Enable Pattern Tracing:**
```python
# Pattern response includes trace
{
  "data": {...},
  "trace": {
    "pattern_id": "portfolio_overview",
    "steps": [...],
    "agents_used": ["financial_analyst"],
    "capabilities_used": ["ledger.positions", "pricing.apply_pack"]
  }
}
```

**Debug Steps:**
1. Check pattern JSON is valid
2. Verify all required inputs are provided
3. Check template substitution works
4. Verify each step executes successfully
5. Check agent routing works

---

### Database Query Debugging

**Enable Query Logging:**
```python
# In connection.py
import logging
logger = logging.getLogger(__name__)

async def execute_query(query, *args):
    logger.debug(f"Query: {query}, Args: {args}")
    # ... execute query
```

**Common Issues:**
- Missing parameters in queries
- Wrong field names (check DATABASE.md for correct names)
- Type mismatches (Decimal vs float)
- Missing indexes (check query performance)

---

### Performance Debugging

**Check Slow Queries:**
```sql
-- Enable query logging
SET log_min_duration_statement = 1000;  -- Log queries > 1 second

-- Check slow queries
SELECT query, duration FROM pg_stat_statements 
ORDER BY duration DESC LIMIT 10;
```

**Common Performance Issues:**
- Missing indexes
- N+1 query problems
- Large result sets
- Inefficient joins

---

## 🔧 Debug Commands

### Database Connection
```bash
# Test connection
python -c "from backend.app.db.connection import init_db_pool; import asyncio; asyncio.run(init_db_pool())"

# Check pool status
python -c "import sys; storage = sys.modules.get('__dawsos_db_pool_storage__'); print(f'Pool: {storage.pool if storage else None}')"
```

### Authentication
```bash
# Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"michael@dawsos.com","password":"mozzuq-byfqyQ-5tefvu"}'

# Check user exists
psql $DATABASE_URL -c "SELECT email, role FROM users;"
```

### API Health
```bash
# Health check
curl http://localhost:8000/health

# Check patterns
curl http://localhost:8000/api/patterns

# Test pattern execution
curl -X POST http://localhost:8000/api/patterns/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pattern_name":"portfolio_overview","inputs":{"portfolio_id":"..."}}'
```

### Log Analysis
```bash
# View recent logs
tail -100 logs/app.log

# Follow logs
tail -f logs/app.log

# Find errors
grep -i error logs/app.log | tail -20

# Find specific pattern
grep "portfolio_overview" logs/app.log
```

---

## 📚 Additional Resources

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - Development guide and patterns
- **[DATABASE.md](DATABASE.md)** - Database schema and operations
- **[API_CONTRACT.md](API_CONTRACT.md)** - API endpoint documentation

---

## 🆘 Getting Help

1. **Check this troubleshooting guide** - Most common issues are covered here
2. **Review application logs** - Check `logs/app.log` for detailed error messages
3. **Check GitHub issues** - Search for similar issues
4. **Review documentation** - See [DOCUMENTATION.md](DOCUMENTATION.md) for complete index
5. **Contact development team** - For issues not covered here

---

**Last Updated:** January 14, 2025
