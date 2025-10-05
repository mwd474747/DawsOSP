# DawsOS Developer Setup Guide

**Last Updated:** October 4, 2025
**DawsOS Version:** 1.0 (15-agent Trinity architecture)

---

## Quick Start (5 minutes)

```bash
# 1. Clone and navigate
cd /path/to/DawsOSB

# 2. Create virtual environment
python3 -m venv dawsos/venv
source dawsos/venv/bin/activate  # On Windows: dawsos\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up credentials (see below)
cp .env.example .env
# Edit .env with your API keys

# 5. Run the application
streamlit run dawsos/main.py
```

---

## Prerequisites

### Required
- **Python 3.9+** (tested on 3.13.2)
- **pip** package manager
- **Git** for version control

### Optional
- **FRED API Key** - For economic data (free from [https://fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html))
- **Anthropic API Key** - For Claude LLM features (from [https://console.anthropic.com/](https://console.anthropic.com/))

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd DawsOSB
```

### 2. Create Virtual Environment

```bash
# Create venv
python3 -m venv dawsos/venv

# Activate (macOS/Linux)
source dawsos/venv/bin/activate

# Activate (Windows)
dawsos\venv\Scripts\activate

# Verify activation
which python  # Should show path inside dawsos/venv
```

### 3. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Verify key packages
python -c "import streamlit; import networkx; import anthropic; print('✅ All packages installed')"
```

**Core Dependencies:**
- `streamlit` - Web UI framework
- `networkx` - Knowledge graph
- `anthropic` - Claude API (optional but recommended)
- `pandas`, `numpy` - Data processing
- `plotly` - Visualizations
- `python-dotenv` - Environment management

### 4. Configure Credentials

DawsOS uses a `.env` file for API keys and credentials.

```bash
# Create .env file
cp .env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

**Required .env Contents:**

```bash
# Anthropic (Claude) API Key - Required for LLM features
ANTHROPIC_API_KEY=sk-ant-api03-...

# FRED API Key - Optional, for economic data
# Get free key from: https://fred.stlouisfed.org/docs/api/api_key.html
FRED_API_KEY=your_fred_api_key_here

# Optional: Trinity strict mode (fails on direct agent access)
TRINITY_STRICT_MODE=false
```

**Security Notes:**
- ⚠️ **Never commit .env to git** - It's in `.gitignore` by default
- 🔒 Store production keys in environment variables or secret manager
- 📝 Use `.env.example` as template for team onboarding

### 5. Verify Setup

```bash
# Test Python imports
python3 -c "
import dawsos.core.universal_executor as ue
import dawsos.core.pattern_engine as pe
import dawsos.core.knowledge_graph as kg
print('✅ Core modules import successfully')
"

# Test credentials
python3 -c "
from dawsos.core.credentials import get_credential_manager
creds = get_credential_manager()
print(f'✅ ANTHROPIC_API_KEY: {'SET' if creds.get('ANTHROPIC_API_KEY') else 'MISSING'}')
print(f'✅ FRED_API_KEY: {'SET' if creds.get('FRED_API_KEY') else 'MISSING (optional)'}')
"
```

---

## Running the Application

### Development Mode

```bash
# Activate venv
source dawsos/venv/bin/activate

# Run Streamlit with hot reload
streamlit run dawsos/main.py
```

**Application will open at:** [http://localhost:8501](http://localhost:8501)

### Production Mode

```bash
# Run without hot reload
streamlit run dawsos/main.py --server.runOnSave=false

# Run on specific port
streamlit run dawsos/main.py --server.port=8080

# Run with external access
streamlit run dawsos/main.py --server.address=0.0.0.0
```

### Docker (Alternative)

```bash
# Build image
docker build -t dawsos:latest .

# Run container
docker run -p 8501:8501 --env-file .env dawsos:latest
```

---

## Project Structure

```
DawsOSB/
├── dawsos/                      # Main application package
│   ├── core/                    # Trinity architecture core
│   │   ├── universal_executor.py   # Single entry point
│   │   ├── pattern_engine.py       # Pattern routing
│   │   ├── agent_runtime.py        # Agent management
│   │   ├── knowledge_graph.py      # Graph storage
│   │   ├── llm_client.py          # Claude API wrapper
│   │   └── credentials.py         # Credential management
│   ├── agents/                  # 15 active agents
│   │   ├── claude.py              # LLM orchestrator
│   │   ├── data_harvester.py      # Data collection
│   │   ├── pattern_spotter.py     # Pattern detection
│   │   ├── financial_analyst.py   # Financial analysis (consolidated)
│   │   └── ...                    # 11 more agents
│   ├── capabilities/            # Shared capabilities
│   │   ├── fred_data.py          # FRED economic data
│   │   └── ...
│   ├── patterns/                # 45+ patterns
│   │   └── workflow_patterns.json
│   ├── ui/                      # Streamlit UI components
│   │   ├── trinity_ui_components.py
│   │   ├── trinity_dashboard_tabs.py
│   │   └── ...
│   ├── tests/                   # Test suite
│   │   ├── test_codebase_consistency.py  # Validation tests
│   │   └── validation/          # Integration tests
│   ├── storage/                 # Persistent data
│   │   ├── knowledge_base.json  # Graph data
│   │   └── checksums.json       # Integrity checks
│   ├── main.py                  # Streamlit entry point
│   └── venv/                    # Virtual environment
├── docs/                        # Documentation
│   ├── DEVELOPER_SETUP.md       # This file
│   ├── reports/                 # Status reports
│   └── archive/                 # Historical docs
├── archive/                     # Archived legacy code
├── .env                         # Credentials (DO NOT COMMIT)
├── .env.example                 # Template for .env
├── requirements.txt             # Python dependencies
└── README.md                    # Project overview
```

---

## Development Workflow

### Making Changes

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** following Trinity architecture:
   - User requests go through `UniversalExecutor`
   - Patterns route to appropriate agents
   - All results stored in `KnowledgeGraph`

3. **Run tests**
   ```bash
   # Run validation tests
   pytest dawsos/tests/test_codebase_consistency.py -v

   # Run specific test
   pytest dawsos/tests/test_codebase_consistency.py::test_no_deprecated_streamlit_apis
   ```

4. **Verify application runs**
   ```bash
   streamlit run dawsos/main.py
   ```

5. **Commit with descriptive message**
   ```bash
   git add .
   git commit -m "feat: Add new pattern for X"
   ```

### Code Style

- **Python:** Follow PEP 8
- **Imports:** Absolute imports from `dawsos` package root
- **Type hints:** Use where helpful (gradual typing)
- **Logging:** Use Python `logging` module, not `print()`

**Example:**
```python
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def my_function(param: str) -> Dict[str, Any]:
    """Clear docstring describing function"""
    logger.info(f"Processing {param}")
    return {'result': 'success'}
```

### Testing

**Run all tests:**
```bash
pytest dawsos/tests/ -v
```

**Run with coverage:**
```bash
pytest --cov=dawsos --cov-report=html
```

**Key test files:**
- `test_codebase_consistency.py` - Prevents regressions (Streamlit APIs, agent refs, docs)
- `test_trinity_smoke.py` - Trinity architecture smoke tests
- `test_integration.py` - Integration tests

---

## Common Issues & Solutions

### Issue: `ModuleNotFoundError: No module named 'core'`

**Solution:** Use absolute imports from `dawsos` root:
```python
# ❌ Wrong
from core import universal_executor

# ✅ Correct
from dawsos.core import universal_executor
```

### Issue: `anthropic not found` error

**Solution:**
```bash
# Activate venv first
source dawsos/venv/bin/activate

# Install anthropic
pip install anthropic
```

### Issue: Streamlit shows "connection error"

**Solution:**
```bash
# Kill existing Streamlit processes
pkill -f streamlit

# Restart
streamlit run dawsos/main.py
```

### Issue: FRED data returns errors

**Check:**
1. API key set in `.env`
2. API key valid (test at [fred.stlouisfed.org](https://fred.stlouisfed.org))
3. Check health status:
   ```python
   from dawsos.capabilities.fred_data import FredDataCapability
   fred = FredDataCapability()
   print(fred.get_health_status())
   ```

### Issue: Knowledge graph too large (96K+ nodes)

**Solutions:**
- Clear cache: Delete `dawsos/storage/knowledge_base.json`
- Implement sampling (see TECHNICAL_DEBT_STATUS.md)

---

## Architecture Overview

### Trinity Architecture

```
Request → UniversalExecutor → PatternEngine → AgentRuntime → Agent → KnowledgeGraph
                                    ↓
                            (45+ Patterns)
                                    ↓
                            (15 Active Agents)
```

**Key Principles:**
1. **Single Entry Point:** All requests go through `UniversalExecutor`
2. **Pattern-Driven:** Patterns determine agent routing
3. **Knowledge Storage:** All results stored in graph
4. **No Direct Agent Access:** Bypass detection warns developers

### 15 Active Agents

| Agent | Purpose |
|-------|---------|
| `graph_mind` | Knowledge graph operations |
| `claude` | LLM orchestration |
| `data_harvester` | Data collection |
| `data_digester` | Data processing |
| `relationship_hunter` | Graph relationships |
| `pattern_spotter` | Pattern detection |
| `forecast_dreamer` | Predictions |
| `code_monkey` | Code generation |
| `structure_bot` | Structure analysis |
| `refactor_elf` | Code refactoring |
| `workflow_recorder` | Workflow capture |
| `workflow_player` | Workflow execution |
| `ui_generator` | UI components |
| `financial_analyst` | Financial analysis (consolidated from 3 legacy agents) |
| `governance_agent` | System governance |

**Legacy agents** (archived 10/2025):
- `equity_agent`, `macro_agent`, `risk_agent` → Consolidated into `financial_analyst`
- `pattern_agent` → Use `pattern_spotter`

---

## API Keys & External Services

### FRED API (Federal Reserve Economic Data)

**Purpose:** Economic indicators (GDP, CPI, unemployment, etc.)
**Cost:** Free
**Get Key:** [https://fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)

**Features:**
- 800,000+ time series
- 24-hour cache TTL
- Automatic fallback to expired cache on API failure
- Rate limit: 1000 requests/minute (generous)

### Anthropic API (Claude)

**Purpose:** LLM features for agents
**Cost:** Pay-per-token (see [anthropic.com/pricing](https://www.anthropic.com/pricing))
**Get Key:** [https://console.anthropic.com/](https://console.anthropic.com/)

**Default Model:** `claude-3-haiku-20240307` (fast, cost-effective)

---

## Contributing

### Before Submitting PR

1. ✅ Run tests: `pytest dawsos/tests/ -v`
2. ✅ Verify application starts: `streamlit run dawsos/main.py`
3. ✅ Check no deprecated APIs: `rg "use_container_width" dawsos --type py | grep -v backup`
4. ✅ Update documentation if needed

### PR Guidelines

- Clear title: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
- Description of changes
- Link to issue if applicable
- Screenshots for UI changes

---

## Getting Help

**Documentation:**
- [TECHNICAL_DEBT_STATUS.md](../TECHNICAL_DEBT_STATUS.md) - Current status
- [CONSOLIDATION_VALIDATION_COMPLETE.md](../CONSOLIDATION_VALIDATION_COMPLETE.md) - Agent consolidation
- [ROOT_CAUSE_ANALYSIS.md](../ROOT_CAUSE_ANALYSIS.md) - Process improvements

**Common Commands:**
```bash
# View logs
tail -f dawsos/logs/PatternEngine_$(date +%Y%m%d).log

# Check knowledge graph size
ls -lh dawsos/storage/knowledge_base.json

# View FRED cache stats
python3 -c "
from dawsos.capabilities.fred_data import FredDataCapability
fred = FredDataCapability()
print(fred.get_cache_stats())
"

# Health check
python3 -c "
from dawsos.capabilities.fred_data import FredDataCapability
fred = FredDataCapability()
import json
print(json.dumps(fred.get_health_status(), indent=2))
"
```

---

## Next Steps

1. ✅ Complete this setup guide
2. 🚀 Run the application and explore the UI
3. 📖 Read [TECHNICAL_DEBT_STATUS.md](../TECHNICAL_DEBT_STATUS.md) for current status
4. 🛠️ Make your first contribution!

**Happy coding!** 🎉
