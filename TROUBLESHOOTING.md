# Trinity 3.0 - Troubleshooting

**Last Updated**: October 21, 2025

---

## Quick Diagnostics

```bash
# 1. Verify Python version
python --version  # Should be 3.11.x

# 2. Verify dependencies
venv/bin/pip list | grep -E "streamlit|openbb|anthropic"

# 3. Check API configuration
venv/bin/python -c "from config.api_config import APIConfig; print(APIConfig.get_status())"

# 4. Test market data
venv/bin/python -c "from services.openbb_service import OpenBBService; s=OpenBBService(); print(s.get_equity_quote('SPY'))"

# 5. Check application files
ls -1 agents/*.py core/*.py patterns/*/*.json | wc -l  # Should be ~40
```

---

## Common Issues

### Application Won't Start

**Symptom**: `./start.sh` fails or Streamlit errors

**Causes**:
1. Python version wrong (need 3.11)
2. Dependencies not installed
3. Port 8501 already in use

**Solutions**:
```bash
# Check Python version
python3.11 --version || echo "Python 3.11 not found"

# Reinstall dependencies
venv/bin/pip install -r requirements.txt --upgrade

# Kill existing Streamlit
pkill -9 -f streamlit

# Restart
./start.sh
```

### No API Keys / Free Mode

**Symptom**: "0/10 APIs configured", no AI analysis

**Cause**: No .env file or empty API keys

**Solution**:
```bash
# 1. Create .env
cp .env.example .env

# 2. Edit .env (add minimum keys)
ANTHROPIC_API_KEY=sk-ant-your-key-here
FRED_API_KEY=your-fred-key-here

# 3. Restart
pkill -9 -f streamlit && ./start.sh

# 4. Verify
venv/bin/python -c "from config.api_config import APIConfig; print(APIConfig.validate())"
```

See [CONFIGURATION.md](CONFIGURATION.md) for API signup links

### Market Data Not Loading

**Symptom**: "Market data loading..." stuck

**Cause**: OpenBB 4.5.0 bug (known issue)

**Status**: Fixed via yfinance workaround

**Verification**:
```bash
venv/bin/python -c "from services.openbb_service import OpenBBService; s=OpenBBService(); print(s.get_equity_quote('SPY')['results'][0]['price'])"
# Should print: Real price like 672.63
```

**If Still Fails**:
```bash
# Check yfinance installed
venv/bin/pip show yfinance

# Reinstall
venv/bin/pip install --upgrade yfinance
```

### Knowledge Data Not Loading

**Symptom**: Economic dashboard shows "No data"

**Causes**:
1. Knowledge loader default path wrong
2. Files missing

**Solutions**:
```bash
# 1. Verify files exist
ls -1 storage/knowledge/*.json | wc -l  # Should be 27

# 2. Test loader
venv/bin/python -c "
from core.knowledge_loader import get_knowledge_loader
loader = get_knowledge_loader(base_path='./storage/knowledge')
data = loader.get_dataset('sector_performance')
print('✅ Loaded' if data else '❌ Failed')
"

# 3. Fix default path (if needed)
# Edit core/knowledge_loader.py line ~30
# Change: "./dawsos/storage/knowledge" → "./storage/knowledge"
```

### Patterns Not Executing

**Symptom**: UI buttons don't trigger analysis

**Cause**: UI bypasses pattern engine (known issue - see MASTER_TASK_LIST.md P1)

**Status**: Architecture exists but not connected to UI

**Workaround**: Direct execution via Python:
```python
from core.universal_executor import UniversalExecutor
from core.agent_runtime import AgentRuntime
from core.knowledge_graph import KnowledgeGraph

graph = KnowledgeGraph()
runtime = AgentRuntime()
executor = UniversalExecutor(graph=graph, runtime=runtime)

result = executor.execute(pattern_id="smart_stock_analysis", context={"SYMBOL": "AAPL"})
print(result)
```

---

## Error Messages

### ImportError: cannot import name 'OBBject_EquityInfo'

**Cause**: OpenBB 4.5.0 package builder bug

**Status**: Known upstream issue (GitHub #7113)

**Fix**: Already implemented (yfinance workaround)

**Verify**:
```bash
venv/bin/python scripts/diagnose_openbb_fmp.py
# Should show: "❌ OBBject_EquityInfo NOT FOUND" but market data works via yfinance
```

### Module not found: dotenv

**Cause**: python-dotenv not installed

**Fix**:
```bash
venv/bin/pip install python-dotenv
```

### KeyError: 'results' (market data)

**Cause**: API call failed, no data returned

**Debug**:
```bash
venv/bin/python -c "
from services.openbb_service import OpenBBService
import traceback
try:
    s = OpenBBService()
    result = s.get_equity_quote('INVALID_SYMBOL')
    print(result)
except Exception as e:
    traceback.print_exc()
"
```

### Streamlit stuck on "Please wait..."

**Cause**: Long-running operation or error

**Solutions**:
1. Check browser console for errors (F12)
2. Check terminal for Python errors
3. Restart Streamlit
4. Clear browser cache

---

## Performance Issues

### Slow Dashboard Loading

**Causes**:
1. Knowledge loader cache expired (30min TTL)
2. First load (no cache)
3. Large datasets

**Solutions**:
```python
# Increase cache TTL
# Edit core/knowledge_loader.py
self.cache_ttl = 3600  # 1 hour instead of 30 min
```

### High Memory Usage

**Cause**: Large knowledge graph in memory

**Monitor**:
```bash
# Check memory
top -p $(pgrep -f streamlit)
```

**Solutions**:
1. Restart application periodically
2. Reduce knowledge dataset size
3. Implement Redis caching (optional)

---

## Known Issues

See [MASTER_TASK_LIST.md](MASTER_TASK_LIST.md) for full list:

1. **P1: Pattern engine disconnected from UI**
2. **P1: Only 2/7 agents registered**
3. **P1: Knowledge loader default path wrong**
4. **P2: Query processing bypasses UniversalExecutor**
5. **P2: OpenBB 4.5.0 bug** (workaround in place)

---

## Getting Help

1. Check [MASTER_TASK_LIST.md](MASTER_TASK_LIST.md) for known issues
2. Run diagnostics (top of this file)
3. Check logs in terminal
4. Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
5. See [CONFIGURATION.md](CONFIGURATION.md) for API setup

---

**Document Status**: ✅ Verified October 21, 2025
