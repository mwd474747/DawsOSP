# Economic Data Debug Instructions

**Date**: October 11, 2025
**Status**: Diagnostic logging added, awaiting real app trigger
**Server**: http://localhost:8501

---

## ✅ What's Been Done

1. **Diagnostic logging added** to `dawsos/core/pattern_engine.py` (lines 1883-1901)
2. **Server running** with the new logging code
3. **.env file loading fixed** - API keys properly set
4. **FRED API verified working** when called directly

---

## 🔍 How to View Diagnostic Output

The diagnostic logging will appear when the app tries to fetch economic data. Here's how to see it:

### Method 1: Check App Logs in Real-Time

1. **Open the app** at http://localhost:8501
2. **Navigate to a tab** that uses economic data:
   - Dashboard tab
   - Economic Dashboard
   - Macro Analysis
   - Any pattern that fetches indicators

3. **Look for 🔍 emoji** in the terminal where Streamlit is running

The diagnostic output will show:
```
🔍 Calling execute_by_capability with context: {'indicators': ['GDP', 'CPIAUCSL', ...], ...}
🔍 Got result type: <class 'dict'>, keys: [...]
🔍 Result has 'series': YES/NO
🔍 Result has 'error': YES - error message / NO
🔍 series_data has N series: ['GDP', 'CPIAUCSL']
```

---

### Method 2: Trigger Manually via Python

```bash
cd /Users/mdawson/Dawson/DawsOSB

# Run test that triggers the diagnostic logging
dawsos/venv/bin/python3 <<'EOF'
import sys
sys.path.insert(0, 'dawsos')
from load_env import load_env
load_env()

# Full imports from main.py
from core.knowledge_graph import KnowledgeGraph
from core.agent_runtime import AgentRuntime
from core.pattern_engine import PatternEngine

# Initialize like Streamlit does
graph = KnowledgeGraph()
runtime = AgentRuntime()
engine = PatternEngine(runtime=runtime, graph=graph)

# Trigger the method (it's private, so we access internals)
try:
    result = engine._get_macro_economic_data({})
    print(f"Success! Got {result.get('indicators_count', 0)} indicators")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
EOF
```

Look for the 🔍 emoji in the output!

---

## 📋 What the Diagnostic Logging Will Reveal

Based on the output, here's what to do:

### Scenario A: "Result has 'error': YES"
```
🔍 Result has 'error': YES - No agent found with capability: can_fetch_economic_data
```
**Problem**: Capability routing failed
**Fix**: Check `AGENT_CAPABILITIES` registration for `can_fetch_economic_data`

### Scenario B: "Result has 'series': NO"
```
🔍 Result has 'series': NO
🔍 Got result type: <class 'dict'>, keys: ['response']
```
**Problem**: DataHarvester returned wrong format
**Fix**: DataHarvester.fetch_economic_data() not returning `{'series': {...}}`

### Scenario C: "series_data has 0 series"
```
🔍 Result has 'series': YES
🔍 series_data has 0 series: []
```
**Problem**: FredDataCapability returned empty series
**Fix**: Check FRED API key, API limits, or network issues

### Scenario D: No diagnostic output at all
**Problem**: `_get_macro_economic_data()` never gets called
**Fix**: Check what triggers it (should be dashboard initialization)

---

## 🔧 Current Known Issues

### Issue 1: Method is Private
The method `_get_macro_economic_data()` is private (starts with `_`), so it's only called internally by:
- `execute_pattern()` at line 1502
- When rendering dashboard/economic tabs

### Issue 2: Multiple Background Processes
There are ~18 zombie Streamlit processes that might interfere. To clean up:
```bash
bash scripts/manage_streamlit.sh cleanup
killall -9 streamlit python
sleep 3
./start.sh
```

### Issue 3: Logs Go to stderr
The diagnostic output goes to stderr, not stdout. When running in terminal:
- stdout shows: "You can now view your Streamlit app..."
- stderr shows: INFO/WARNING/ERROR messages with 🔍 emoji

---

## ✅ Quick Verification

To verify the diagnostic logging is active:

```bash
# Check that the logging code exists
grep "🔍" dawsos/core/pattern_engine.py

# Should show 4-5 lines with magnifying glass emoji
```

Expected output:
```python
self.logger.info(f"🔍 Calling execute_by_capability with context: {context}")
self.logger.info(f"🔍 Got result type: {type(result)}, keys: ...")
self.logger.info(f"🔍 Result has 'series': {'YES' if 'series' in result else 'NO'}")
self.logger.info(f"🔍 Result has 'error': {'YES - ' + str(result.get('error')) if 'error' in result else 'NO'}")
self.logger.info(f"🔍 series_data has {len(series_data)} series: {list(series_data.keys())}")
```

---

## 📊 What We Know So Far

✅ **API Keys**: Loaded correctly (`FRED_API_KEY`, `FMP_API_KEY`)
✅ **FRED API**: Works when called directly (2 series fetched)
✅ **.env Loading**: Fixed to work from multiple locations
✅ **Pattern Routing**: 28+ patterns fixed with detect_patterns() method
✅ **Server**: Running on port 8501

⚠️ **Integration**: Something breaks in capability routing chain
⚠️ **Diagnostic Logging**: Added but needs real trigger to see output

---

## 🎯 Next Steps

1. **Open the app** at http://localhost:8501
2. **Click on Dashboard** or Economic Dashboard tab
3. **Watch the terminal** where Streamlit is running
4. **Look for 🔍 emoji** in the log output
5. **Report what you see** - that will tell us exactly where it's failing

Alternatively, if you prefer offline mode:
- The system works with 27 enriched datasets
- Economic data is static but functional
- All features work without API calls

---

## 📞 Related Documents

- [API_INTEGRATION_STATUS.md](API_INTEGRATION_STATUS.md) - Full troubleshooting guide
- [CRITICAL_FIXES_COMPLETE.md](CRITICAL_FIXES_COMPLETE.md) - 28-pattern fix summary
- [SAFE_REFACTORING_SUMMARY.md](SAFE_REFACTORING_SUMMARY.md) - Refactoring opportunities

---

**The diagnostic logging is ready - it just needs you to trigger it by using the app!**
