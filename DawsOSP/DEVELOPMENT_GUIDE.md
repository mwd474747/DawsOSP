# DawsOS / Trinity 3.0 Development Guide

> ⚠️ **Note**: This document originated from the legacy Trinity 3.0 stack. Some references (e.g., `MASTER_TASK_LIST.md`, `UniversalExecutor`) no longer exist in the DawsOSP repo. Use this guide for environment setup basics, but rely on:
> - `README.md` for the authoritative quick start
> - `.ops/TASK_INVENTORY_2025-10-24.md` for the live backlog
> - `PRODUCT_SPEC.md` for architecture guardrails

---

## Quick Setup

```bash
# 1. Clone repository (monorepo root)
git clone <repo-url>
cd DawsOSB/DawsOSP

# 2. Create virtual environment (Python 3.11 required)
python3.11 -m venv venv

# 3. Install dependencies
venv/bin/pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Edit .env with your API keys

# 5. Launch backend + frontend
docker compose up -d --build  # spins up Postgres, Redis, backend, frontend
# or, for local dev:
#   ./backend/run_api.sh
#   ./frontend/run_ui.sh

# (Optional) Seed demo data and rating rubrics
python scripts/seed_loader.py --all  # symbols, portfolios, prices, macro, cycles, ratings
```

---

## Project Structure

```
./
├── main.py                  # Streamlit UI application
├── agents/                  # 7 intelligence agents
├── core/                    # 13 core modules
├── patterns/                # 16 JSON pattern definitions
├── storage/knowledge/       # 27 knowledge datasets
├── services/                # 8 data services
├── intelligence/            # 3 chat/NLP modules
├── ui/                      # 7 UI component files
├── config/                  # API configuration
└── .env.example             # API key template
```

---

## Development Workflow

### Making Changes

1. **Review `.ops/TASK_INVENTORY_2025-10-24.md`** - Check current tasks/gaps
2. **Follow architecture** - Use UniversalExecutor → PatternEngine → AgentRuntime
3. **Test locally** - Verify changes work
4. **Update `.ops/TASK_INVENTORY_*`** - Mark complete, add new discoveries
5. **Update documentation** - If changing architecture/API

### Coding Standards

**Python Style**:
- PEP 8 compliant
- Type hints where appropriate
- Docstrings for all public methods
- Max line length: 100 characters

**Imports**:
```python
# Always absolute imports (not relative)
from core.knowledge_graph import KnowledgeGraph  # ✅ Correct
from ..core.knowledge_graph import KnowledgeGraph  # ❌ Wrong
```

**Logging**:
```python
# Always use self.logger in class methods
class MyAgent(BaseAgent):
    def process(self, context):
        self.logger.info("Processing request")  # ✅ Correct
        logger.info("Processing")  # ❌ Wrong (not scoped)
```

---

## Adding New Components

### Add New Agent

**1. Create agent file** in `agents/`:
```python
from agents.base_agent import BaseAgent

class MyNewAgent(BaseAgent):
    def __init__(self, graph=None, llm_client=None):
        super().__init__(
            name="my_new_agent",
            description="What this agent does",
            graph=graph,
            llm_client=llm_client
        )
        self.capabilities = ['can_do_something']  # From agent_capabilities.py
    
    def process(self, context: Dict) -> Dict:
        """Main processing method"""
        # Your logic here
        return {"result": "success"}
```

**2. Register in main.py**:
```python
def initialize_trinity(self):
    # ... existing code ...
    
    # Add your agent
    my_agent = MyNewAgent(graph=self.graph, llm_client=self.llm_client)
    self.runtime.register_agent('my_new_agent', my_agent, {
        'capabilities': my_agent.capabilities,
        'priority': 5
    })
```

**3. Update `.ops/TASK_INVENTORY_*`** with completed tasks

### Add New Pattern

**1. Create JSON** in `patterns/<category>/`:
```json
{
  "id": "my_new_pattern",
  "name": "My Analysis Pattern",
  "description": "What this pattern does",
  "version": "1.0.0",
  "triggers": ["keyword1", "keyword2"],
  "steps": [
    {
      "id": "step_1",
      "action": "execute_by_capability",
      "capability": "can_do_something",
      "params": {
        "input": "{SYMBOL}"
      }
    }
  ],
  "template": "Analysis for {SYMBOL}: {step_1}"
}
```

**2. See [PATTERN_AUTHORING_GUIDE.md](PATTERN_AUTHORING_GUIDE.md)** for full spec

### Add New Knowledge Dataset

**1. Create JSON** in `storage/knowledge/`:
```json
{
  "_meta": {
    "version": "1.0.0",
    "last_updated": "2025-10-21",
    "source": "Your data source",
    "description": "What this dataset contains"
  },
  "data": [
    {"key": "value"}
  ]
}
```

**2. Auto-discovered** by KnowledgeLoader (no code changes needed)

---

## Architecture Compliance

### ALWAYS Use These Patterns

**For Execution**:
```python
# ✅ Correct - Use UniversalExecutor
result = self.executor.execute(pattern_id="my_pattern", context={"SYMBOL": "AAPL"})

# ❌ Wrong - Direct agent call
agent = self.runtime.agents['financial_analyst']
result = agent.process(context)
```

**For Knowledge Loading**:
```python
# ✅ Correct - Use KnowledgeLoader
from core.knowledge_loader import get_knowledge_loader
loader = get_knowledge_loader()
data = loader.get_dataset('sector_performance')

# ❌ Wrong - Direct file load
with open('storage/knowledge/sector_performance.json') as f:
    data = json.load(f)
```

**For Agent Capabilities**:
```python
# ✅ Correct - Use capability routing
result = runtime.execute_by_capability('can_analyze_dcf', context)

# ⚠️ OK but not preferred - Name-based routing
result = runtime.exec_via_registry('financial_analyst', context)
```

### NEVER Do These

1. **Direct agent instantiation** - Always use AgentRuntime registry
2. **Bypass pattern engine** - Always route through UniversalExecutor
3. **Hardcode paths** - Use config values or KnowledgeLoader
4. **Direct graph access** - Use safe methods: `get_node()`, `safe_query()`
5. **Skip error handling** - Always wrap external calls in try/except

---

## Testing

### Manual Testing

```bash
# 1. Start application
./start.sh

# 2. Test market data
# Navigate to Market Overview, verify SPY/QQQ/VIX show real prices

# 3. Test query processing
# Enter query in chat: "What is SPY?"

# 4. Test knowledge loading
# Check Economic Dashboard, verify data loads
```

### Automated Testing

**Current Status**: No test suite (see `.ops/TASK_INVENTORY_*` P3 task)

**Recommended**:
```bash
# Run tests (when created)
venv/bin/pytest tests/

# Run with coverage
venv/bin/pytest --cov=core --cov=agents tests/
```

---

## Common Tasks

### Fix Knowledge Loader Path

**Issue**: Default path `./dawsos/storage/knowledge` (wrong)  
**Fix**: Edit `core/knowledge_loader.py:__init__`
```python
def __init__(self, base_path: str = "./storage/knowledge"):  # Fixed
    self.base_path = Path(base_path)
```

### Register Missing Agents

**Issue**: Only 2/7 agents registered  
**Fix**: Add to `main.py:initialize_trinity()`
```python
# Add these 5 agents
dh = DataHarvester(graph=self.graph)
self.runtime.register_agent('data_harvester', dh, {'capabilities': dh.capabilities})

fd = ForecastDreamer(graph=self.graph)
self.runtime.register_agent('forecast_dreamer', fd, {'capabilities': fd.capabilities})

# ... etc for graph_mind, pattern_spotter
```

### Connect UI to Pattern Engine

**Issue**: UI bypasses execution stack  
**Current**:
```python
def render_sector_performance(self):
    with open('storage/knowledge/sector_performance.json') as f:
        data = json.load(f)
```

**Fix**:
```python
def render_sector_performance(self):
    # Use pattern engine
    result = self.executor.execute(
        pattern_id="sector_performance_analysis",
        context={}
    )
    data = result['data']
```

---

## Debugging

### Enable Debug Logging

Edit `.env`:
```
LOG_LEVEL=DEBUG
```

Restart application.

### Common Errors

**ImportError: No module named 'X'**
```bash
venv/bin/pip install -r requirements.txt
```

**API key errors**
```bash
# Verify .env file exists
ls -la .env

# Check keys loaded
venv/bin/python -c "from config.api_config import APIConfig; print(APIConfig.get_status())"
```

**Market data not loading**
```bash
# Test OpenBBService
venv/bin/python -c "
from services.openbb_service import OpenBBService
service = OpenBBService()
print(service.get_equity_quote('SPY'))
"
```

---

## API Integration

### Configure Minimum Keys

For full functionality:
```
ANTHROPIC_API_KEY=sk-ant-...  # Required for AI analysis
FRED_API_KEY=...              # Required for economic data (FREE)
```

See [CONFIGURATION.md](CONFIGURATION.md) for all 10 providers

### Test API Connection

```bash
venv/bin/python scripts/test_api_integration.py
```

---

## References

- [.ops/TASK_INVENTORY_2025-10-24.md](.ops/TASK_INVENTORY_2025-10-24.md) - Current tasks and gaps
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [CONFIGURATION.md](CONFIGURATION.md) - API setup
- [PATTERN_AUTHORING_GUIDE.md](PATTERN_AUTHORING_GUIDE.md) - Pattern creation
- [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md) - All 103 capabilities
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

---

**Document Status**: ✅ Verified against code October 21, 2025
# Observability toggle (optional)
# Enable Jaeger/Sentry by setting these in .env
# ENABLE_OBSERVABILITY=true
# JAEGER_ENDPOINT=http://localhost:14268/api/traces
# SENTRY_DSN=<dsn>
