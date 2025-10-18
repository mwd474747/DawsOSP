# DawsOS - Financial Intelligence Platform

**Status**: ✅ Operational (A- Grade - 92/100) - Technical debt documented  
**Version**: 3.0 (Trinity Architecture)  
**Last Updated**: October 17, 2025

---

## Overview

DawsOS is a **pattern-driven financial intelligence system** that orchestrates 15 specialized AI agents through a centralized registry, executing 50 pre-defined patterns for market analysis, investment frameworks, and real-time financial insights.

### Core Architecture
```
User Request → UniversalExecutor → PatternEngine → AgentRegistry → Specialized Agents → KnowledgeGraph
```

---

## Quick Start

```bash
# 1. Clone repository
git clone <your-repo-url>
cd DawsOSB

# 2. Create virtual environment (Python 3.10+ required)
python3 -m venv dawsos/venv
source dawsos/venv/bin/activate  # Windows: dawsos\venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
streamlit run dawsos/main.py --server.port=5000

# 5. Open browser at http://localhost:5000
```

**Quick Launch**:
```bash
./start.sh  # Handles everything automatically
```

---

## API Configuration (Optional)

DawsOS works fully **without API keys** using cached data and enriched datasets. API keys enable real-time data and live AI analysis.

### Setup Environment Variables

```bash
# Copy example template
cp .env.example .env

# Add your API keys (all optional)
nano .env
```

### Available APIs

| API | Purpose | Free Tier | Get Key |
|-----|---------|-----------|---------|
| `ANTHROPIC_API_KEY` | AI-powered analysis | Pay-as-you-go | [console.anthropic.com](https://console.anthropic.com/) |
| `FRED_API_KEY` | Economic indicators | Unlimited | [fred.stlouisfed.org/docs/api](https://fred.stlouisfed.org/docs/api/api_key.html) |
| `FMP_API_KEY` | Stock data | 250/day | [financialmodelingprep.com](https://financialmodelingprep.com/developer/docs/) |
| `NEWSAPI_KEY` | Financial news | 100/day | [newsapi.org](https://newsapi.org/register) |

---

## Key Features

### 🏛️ Trinity Architecture
- **50 JSON patterns** define financial workflows
- **15 specialized agents** with 103 capabilities
- **Capability-based routing** for flexible execution
- **Centralized registry** ensures architecture compliance

### 📊 Financial Intelligence
- **Investment Frameworks**: Buffett, Dalio, factor analysis
- **Real-time Market Data**: FRED, FMP, NewsAPI integration
- **AI-Powered Analysis**: Claude-based insights
- **Options Flow Analysis**: Unusual activity detection

### 🧠 Knowledge Management
- **27 enriched datasets** with 30-minute cache
- **NetworkX graph** (96K+ nodes, 10x performance)
- **Automatic persistence** with 30-day backup rotation
- **Data quality scoring** and governance

### 📈 Analysis Capabilities
- DCF Valuation & Moat Analysis
- Economic Regime Detection
- Portfolio Risk Assessment
- Sector Correlation & Rotation
- Options Greeks & IV Analysis

---

## System Metrics

| Metric | Value |
|--------|-------|
| **Overall Grade** | A- (92/100) |
| **Agents** | 15 registered |
| **Capabilities** | 103 unique |
| **Patterns** | 50 executable |
| **Datasets** | 27 (100% coverage) |
| **Graph Nodes** | 96,000+ |
| **Type Coverage** | 85%+ |

---

## Documentation

### Getting Started
- [Quick Start](#quick-start) - Installation and setup
- [API Configuration](#api-configuration-optional) - External API setup
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues & fixes

### Development
- [CLAUDE.md](CLAUDE.md) - Development memory (AI sessions)
- [SYSTEM_STATUS.md](SYSTEM_STATUS.md) - Current system status
- [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md) - 103 capabilities reference
- [docs/DEVELOPER_SETUP.md](docs/DEVELOPER_SETUP.md) - Developer onboarding
- [docs/AgentDevelopmentGuide.md](docs/AgentDevelopmentGuide.md) - Building agents
- [docs/KnowledgeMaintenance.md](docs/KnowledgeMaintenance.md) - Dataset management

### Architecture & Specialists
- [.claude/trinity_architect.md](.claude/trinity_architect.md) - Architecture expert
- [.claude/pattern_specialist.md](.claude/pattern_specialist.md) - Pattern expert
- [.claude/knowledge_curator.md](.claude/knowledge_curator.md) - Knowledge graph expert
- [.claude/agent_orchestrator.md](.claude/agent_orchestrator.md) - Agent system expert

### Historical Documentation
- [archive/legacy/INDEX.md](archive/legacy/INDEX.md) - Master index
- [archive/legacy/sessions/](archive/legacy/sessions/) - Development session reports
- [archive/legacy/fixes/](archive/legacy/fixes/) - Bug fixes & root cause analyses
- [archive/legacy/refactoring/](archive/legacy/refactoring/) - Architecture evolution

---

## Repository Structure

```
DawsOSB/
├── dawsos/                    # Application root
│   ├── main.py               # Streamlit entry point
│   ├── core/                 # Trinity runtime (8 core modules)
│   ├── agents/               # 15 specialized agents
│   ├── patterns/             # 48 JSON workflow patterns
│   ├── capabilities/         # External API integrations
│   ├── storage/knowledge/    # 27 enriched datasets
│   ├── ui/                   # Streamlit dashboards
│   └── tests/                # Test suites
├── .claude/                  # Specialist agent documentation
├── docs/                     # Development guides
├── archive/legacy/           # Historical documentation
│   ├── sessions/            # Session completion reports
│   ├── fixes/               # Bug fix documentation
│   └── refactoring/         # Architecture evolution
├── README.md                 # This file
├── CLAUDE.md                 # AI development memory
└── SYSTEM_STATUS.md          # Current system status
```

---

## Agent Capabilities

### Data Pipeline
- **data_harvester** - Market data, economic indicators, news
- **data_digester** - Transform raw data into graph nodes
- **relationship_hunter** - Correlation and relationship analysis

### Analysis
- **financial_analyst** - DCF, ROIC, moat analysis, portfolio risk
- **pattern_spotter** - Pattern recognition and trend detection
- **forecast_dreamer** - Predictive modeling and forecasts

### Governance
- **governance_agent** - Data quality, compliance, lineage tracking

**Full Capability List**: [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md)

---

## Pattern Library

### 50 Executable Patterns (0 Errors)

**Categories**:
- **Analysis** (15) - Buffett checklist, DCF, moat, sector rotation
- **Workflows** (5) - Deep dive, morning briefing, portfolio review
- **Governance** (6) - Policy validation, quality audits, compliance
- **Queries** (6) - Company analysis, market regime, sector performance
- **UI** (6) - Dashboard updates, alerts, watchlists
- **System** (5) - Meta-execution, architecture validation

**Validation**:
```bash
python scripts/lint_patterns.py
# Output: 50 patterns checked, 0 errors ✅
```

---

## Capability-Based Routing

Execute agents by **what they can do** rather than by name:

```python
# Traditional name-based routing
result = runtime.exec_via_registry('financial_analyst', context)

# Modern capability-based routing (Trinity 2.0+)
result = runtime.execute_by_capability('can_calculate_dcf', context)
```

**Benefits**: Flexible agent swapping, better discoverability, graceful degradation

---

## Monitoring & Health

### Health Check
```bash
curl http://localhost:5000/_stcore/health
# Response: ok ✅
```

### System Dashboard
Access at http://localhost:5000:
- **Overview** - Agent status, pattern execution
- **Compliance** - Registry bypass tracking
- **Governance** - Data quality metrics
- **Graph** - Node health and relationships

---

## Development

### Code Standards
- Follow Trinity architecture (UniversalExecutor → Pattern → Registry → Agent)
- Use `execute_through_registry` for agent calls
- Load datasets via `KnowledgeLoader` (no ad-hoc file reads)
- Run pattern linter before commits

### Validation
```bash
# Pattern validation
python scripts/lint_patterns.py

# Test suite
pytest dawsos/tests/validation/
```

### Contributing
1. Create feature branch
2. Follow Trinity patterns (see [CLAUDE.md](CLAUDE.md))
3. Run validation suite
4. Update documentation
5. Submit PR (CI auto-validates)

---

## Troubleshooting

### Common Issues

**Port already in use**:
```bash
lsof -ti:5000 | xargs kill -9
```

**Knowledge loader errors**:
```bash
python -c "from dawsos.core.knowledge_loader import KnowledgeLoader; print(len(KnowledgeLoader().datasets))"
# Expected: 27
```

**Import errors**:
- Ensure virtual environment is activated
- Reinstall: `pip install -r requirements.txt`

**More help**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## Production Deployment

### Prerequisites
- Python 3.10+
- Virtual environment configured
- (Optional) API keys for real-time data

### Production Checklist
- [ ] Set `TRINITY_STRICT_MODE=true` (optional enforcement)
- [ ] Configure API keys (optional)
- [ ] Review backup rotation settings
- [ ] Monitor bypass telemetry
- [ ] Check pattern execution logs

### Health Verification
```bash
# Agent registration
python -c "from dawsos.main import runtime; print(f'Agents: {len(runtime._agents)}')"
# Expected: 15

# Dataset coverage
python -c "from dawsos.core.knowledge_loader import KnowledgeLoader; print(f'Datasets: {len(KnowledgeLoader().datasets)}')"
# Expected: 27
```

---

## Support

- **Documentation**: See guides above
- **Issues**: Use GitHub issues
- **System Status**: [SYSTEM_STATUS.md](SYSTEM_STATUS.md)
- **Health**: http://localhost:5000

---

## Built With

- **Trinity Architecture** - Pattern-driven execution framework
- **Streamlit** - Interactive UI framework
- **NetworkX** - High-performance graph backend
- **Anthropic Claude** - AI-powered analysis
- **Python 3.10+** - Core language

---

**Status**: ✅ Operational - Technical debt documented  
**Grade**: A- (92/100)  
**App**: http://localhost:5000  
**Version**: 3.0 (October 2025)
