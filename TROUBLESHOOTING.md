# DawsOS Troubleshooting Guide

**Last Updated**: October 6, 2025
**Version**: 2.0

This guide covers common issues and their solutions for the DawsOS Trinity financial intelligence system.

---

## Quick Fixes

### App Won't Start

**Problem**: `streamlit: command not found` or `ModuleNotFoundError`

**Solution**:
```bash
# Recreate virtual environment
rm -rf dawsos/venv
python3 -m venv dawsos/venv
dawsos/venv/bin/pip install -r requirements.txt

# Launch with absolute path
dawsos/venv/bin/streamlit run dawsos/main.py --server.port=8501
```

---

### Port Already in Use

**Problem**: `Port 8501 is already in use`

**Solution**:
```bash
# Kill existing process
lsof -ti:8501 | xargs kill -9

# Or use different port
dawsos/venv/bin/streamlit run dawsos/main.py --server.port=8502
```

---

### Import Errors After Update

**Problem**: `ImportError: cannot import name 'TypeAlias'` or similar

**Solution**:
```bash
# 1. Check Python version (3.10+ required, 3.13+ recommended)
python3 --version

# 2. Recreate venv with correct Python
python3 -m venv dawsos/venv
dawsos/venv/bin/pip install -r requirements.txt

# 3. Verify TypeAlias compatibility shim exists
ls dawsos/core/typing_compat.py  # Should exist
```

**Root Cause**: Python 3.9 doesn't have `TypeAlias`. The codebase includes a compatibility shim at `dawsos/core/typing_compat.py` for Python 3.9 support, but Python 3.13+ is recommended.

---

### Relative Import Errors

**Problem**: `ImportError: attempted relative import beyond top-level package`

**Solution**: Ensure all imports in `dawsos/` use absolute paths:
```python
# ✅ Correct (absolute import)
from core.knowledge_graph import KnowledgeGraph
from agents.base_agent import BaseAgent

# ❌ Wrong (relative import)
from ..core.knowledge_graph import KnowledgeGraph
from .base_agent import BaseAgent
```

**Files to check**: `dawsos/agents/*.py`, `dawsos/agents/analyzers/*.py`

---

### Missing Graph Methods

**Problem**: `AttributeError: 'KnowledgeGraph' object has no attribute 'nodes'` or `'get_all_edges'`

**Solution**: The NetworkX migration changed the API. Use proper methods:
```python
# ✅ Correct
total_nodes = graph.get_stats()['total_nodes']
all_edges = graph.get_all_edges()
node_data = graph.get_node(node_id)

# ❌ Wrong (pre-NetworkX API)
total_nodes = len(graph.nodes)
all_edges = graph.edges
node_data = graph.nodes[node_id]
```

**Verify**: `dawsos/core/knowledge_graph.py` should have:
- `get_stats()` method
- `get_all_edges()` method
- `get_node()` method

---

### Logger Not Defined

**Problem**: `NameError: name 'logger' is not defined`

**Solution**: Use `self.logger` in class methods, or define module-level logger:
```python
# ✅ Class-based logger
class MyClass:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def my_method(self):
        self.logger.info("Message")

# ✅ Module-level logger
import logging
logger = logging.getLogger(__name__)

def my_function():
    logger.info("Message")
```

---

## Environment Issues

### Missing .env File

**Problem**: `FileNotFoundError: .env not found`

**Solution**:
```bash
# Copy template
cp .env.example .env

# App works without API keys (uses cached data)
# Edit .env to add keys for live data (optional)
```

---

### API Keys Not Working

**Problem**: App says "API key not configured" even though keys are in `.env`

**Solution**:
1. Verify `.env` is in **root directory** (not `dawsos/.env`)
2. Check for correct key names:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...
   FRED_API_KEY=...
   FMP_API_KEY=...
   NEWSAPI_KEY=...
   ```
3. Restart the app (environment is loaded at startup)
4. Check quotes: `KEY=value` not `KEY="value"`

---

## Performance Issues

### App Loads Slowly

**Normal behavior**:
- First load: 5-10 seconds (loading 85MB graph with 96k nodes)
- Subsequent loads: 2-3 seconds (cached)

**If slower**:
1. Check graph size: `ls -lh storage/graph.json`
2. Consider pruning old nodes
3. Enable LRU caching (already enabled in v2.0)

---

### High Memory Usage

**Normal**: ~150MB for 96k node graph

**If excessive**:
```bash
# Check graph stats
python3 -c "from dawsos.core.knowledge_graph import KnowledgeGraph; g = KnowledgeGraph(); g.load('storage/graph.json'); print(g.get_stats())"

# Compact graph (removes unreferenced nodes)
python3 scripts/compact_graph.py
```

---

## Pattern & Agent Issues

### Pattern Not Executing

**Problem**: Pattern triggers but doesn't execute

**Checklist**:
1. Pattern JSON is valid: `python scripts/lint_patterns.py`
2. Agent is registered: Check `AGENT_CAPABILITIES` in `dawsos/core/agent_capabilities.py`
3. Action exists: Verify `execute_through_registry` in pattern steps
4. Check logs: Look for "Pattern matched:" in stdout

---

### Agent Not Found

**Problem**: `Agent 'xyz' not found in registry`

**Solution**:
1. Verify agent in `AGENT_CAPABILITIES` dict
2. Check agent registered in `dawsos/main.py`:
   ```python
   runtime.register_agent(
       'agent_name',
       AgentClass(graph),
       capabilities=AGENT_CAPABILITIES['agent_name']
   )
   ```
3. Restart app to reload registry

---

## Data Issues

### Graph Won't Load

**Problem**: `Error loading graph.json`

**Solution**:
```bash
# Check file integrity
python3 -c "import json; json.load(open('storage/graph.json'))"

# If corrupted, restore from backup
ls -lt storage/backups/ | head -5  # Find latest backup
python3 scripts/restore_backup.py storage/backups/graph_20251006_120000.json
```

---

### Dataset Not Found

**Problem**: `Dataset 'xyz' not found in KnowledgeLoader`

**Solution**:
1. Verify file exists: `ls dawsos/storage/knowledge/xyz.json`
2. Check registered in `KnowledgeLoader._datasets`
3. Verify `_meta` header in JSON file:
   ```json
   {
     "_meta": {
       "version": "1.0.0",
       "last_updated": "2025-10-06",
       "source": "..."
     },
     "data": { ... }
   }
   ```

---

## Development Issues

### Tests Failing

**Problem**: Pytest tests fail after changes

**Solution**:
```bash
# Run specific test
pytest dawsos/tests/validation/test_trinity_smoke.py -v

# Run with debug output
pytest dawsos/tests/validation/ -vv --tb=long

# Clear cache and rerun
pytest --cache-clear dawsos/tests/
```

---

### Type Hints Errors

**Problem**: Type checker complains about `TypeAlias`

**Solution**: Use the compatibility shim:
```python
# ✅ Correct
from typing import Dict, List
from core.typing_compat import TypeAlias

NodeID: TypeAlias = str
```

---

## Getting Help

### Debug Mode

Enable detailed logging:
```bash
# Set in .env
TRINITY_STRICT_MODE=true
LOG_LEVEL=DEBUG

# Or inline
TRINITY_STRICT_MODE=true dawsos/venv/bin/streamlit run dawsos/main.py
```

### Check System Health

```bash
# Validate patterns
python scripts/lint_patterns.py

# Check graph integrity
python scripts/verify_graph.py

# Run smoke tests
pytest dawsos/tests/validation/test_trinity_smoke.py -v
```

### Logs Location

```
stdout/stderr:  Console output (Streamlit)
Graph backups:  storage/backups/
Agent memory:   storage/agent_memory/
Alerts:         storage/alerts/
```

---

## Common Error Messages

| Error | Meaning | Fix |
|-------|---------|-----|
| `Port 8501 is already in use` | Another instance running | `lsof -ti:8501 \| xargs kill -9` |
| `ModuleNotFoundError: No module named 'streamlit'` | Dependencies not installed | `pip install -r requirements.txt` |
| `ImportError: cannot import name 'TypeAlias'` | Python < 3.10 or missing shim | Use Python 3.10+ or check `typing_compat.py` |
| `AttributeError: 'KnowledgeGraph' object has no attribute 'nodes'` | Using pre-NetworkX API | Use `get_stats()`, `get_all_edges()` |
| `NameError: name 'logger' is not defined` | Missing logger import | Add `import logging; logger = logging.getLogger(__name__)` |
| `Agent 'xyz' not found` | Agent not registered | Check `AGENT_CAPABILITIES` and `main.py` |
| `Pattern not matched` | No pattern triggers match | Check pattern `triggers` field |

---

## Still Having Issues?

1. **Check recent changes**: `git log -5 --oneline`
2. **Review status docs**: [SYSTEM_STATUS.md](SYSTEM_STATUS.md)
3. **Consult specialists**: [.claude/README.md](.claude/README.md)
4. **Create issue**: Include error traceback, Python version, and steps to reproduce

---

**Note**: Most issues are resolved by recreating the virtual environment with Python 3.13+:
```bash
rm -rf dawsos/venv
python3 -m venv dawsos/venv
dawsos/venv/bin/pip install -r requirements.txt
```
