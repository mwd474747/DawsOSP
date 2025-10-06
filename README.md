# DawsOS - Trinity Architecture Financial Intelligence System

**Status**: ✅ Production Ready (A+ Grade - 98/100)
**Version**: 2.0
**Architecture**: Trinity (Request → Executor → Pattern → Registry → Agent)

---

## Quick Start

```bash
# 1. Clone repository
git clone <your-repo-url>
cd DawsOSB

# 2. Create virtual environment
python3 -m venv dawsos/venv
source dawsos/venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate knowledge graph (first run only, ~30 seconds)
python scripts/seed_minimal_graph.py

# 5. Run the application
streamlit run dawsos/main.py

# 6. Open browser
# http://localhost:8502
```

### Environment Configuration (Optional)

DawsOS works with sensible defaults but can be enhanced with API keys.

**Setup `.env` file** (optional):
```bash
# Copy example
cp .env.example .env

# Edit with your keys
nano .env
```

**Optional API Keys**:
- `ANTHROPIC_API_KEY` - Enables live Claude AI analysis (cached responses used if not set)
- `FRED_API_KEY` - Economic data API from Federal Reserve (generous free tier)

**Note**: The system is fully functional without API keys. They unlock real-time AI insights and fresh economic data.

---

## System Overview

DawsOS is a **pattern-driven financial intelligence system** built on Trinity architecture principles. It orchestrates 15 specialized agents through a centralized registry, executing 45 pre-defined patterns for market analysis, investment frameworks, and data governance.

### Core Architecture

```
User Request
    ↓
UniversalExecutor (main.py)
    ↓
PatternEngine (core/pattern_engine.py)
    ↓
AgentRegistry (core/agent_adapter.py)
    ↓
Specialized Agents (agents/)
    ↓
KnowledgeGraph (core/relationships.py)
```

---

## Key Features

### ✅ Trinity Architecture
- **Pattern-driven execution**: 45 JSON patterns define workflows
- **Agent registry**: Centralized capability-based routing
- **Bypass telemetry**: Tracks compliance violations
- **Strict mode**: `TRINITY_STRICT_MODE=true` for enforcement

### ✅ Knowledge Management
- **Centralized loader**: 26 datasets cached and validated (100% coverage)
- **Investment frameworks**: Buffett, Dalio, factor analysis
- **Market data**: Sectors, correlations, economic cycles
- **30-minute cache TTL**: Optimized performance

### ✅ Data Governance
- **Graph-based quality scoring**: Node validation and health
- **Compliance monitoring**: Policy enforcement
- **Lineage tracking**: Data provenance
- **Real-time alerts**: Quality issues and violations

### ✅ Persistence & Recovery
- **Automatic backup rotation**: 30-day retention
- **Decisions file rotation**: 5MB threshold
- **Checksum validation**: Data integrity
- **Timestamped archives**: Full audit trail

---

## Documentation

### Essential Guides
- [README.md](README.md) - Quick start and system overview
- [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md) - Capability-based routing walkthrough
- [CORE_INFRASTRUCTURE_STABILIZATION.md](CORE_INFRASTRUCTURE_STABILIZATION.md) - Core architecture upgrades
- [docs/AgentDevelopmentGuide.md](docs/AgentDevelopmentGuide.md) - How to build and register agents
- [docs/KnowledgeMaintenance.md](docs/KnowledgeMaintenance.md) - Dataset formats and refresh cadence
- [docs/DisasterRecovery.md](docs/DisasterRecovery.md) - Backup and restore procedures

### Assessment Reports
- [FINAL_ROADMAP_COMPLIANCE.md](FINAL_ROADMAP_COMPLIANCE.md) - Complete compliance (A grade - 94/100)
- [QUICK_WINS_COMPLETE.md](QUICK_WINS_COMPLETE.md) - Final improvements summary (A+ - 98/100)

### Additional Documentation
- [docs/reports/](docs/reports/) - Interim progress reports (4 files)
- [dawsos/docs/archive/](dawsos/docs/archive/) - Historical documentation

---

## Key Metrics

| Metric | Value |
|--------|-------|
| **Overall Grade** | A+ (98/100) |
| **Agents** | 15 registered |
| **Patterns** | 45 (0 errors) |
| **Knowledge Datasets** | 26 (100% coverage) |
| **Pattern Compliance** | 100% Trinity |
| **Error Handling** | Professional (0 bare pass) |
| **Repository** | Clean (5 essential docs) |

---

## System Status

### ✅ Production Ready

**Core Systems**:
- Trinity architecture enforced end-to-end
- Pattern compliance validated (0 errors)
- Knowledge loader operational (26/26 datasets)
- Backup/recovery automated
- CI/CD pipeline active
- Error handling professional

**Health Check**:
```bash
curl http://localhost:8502/_stcore/health
# Response: ok ✅
```

---

## Recent Improvements (October 3, 2025)

### Quick Wins Completed ✅
1. **Knowledge Registry**: 100% coverage (26/26 datasets registered)
2. **Error Handling**: Zero bare pass statements
3. **Repository Hygiene**: Clean structure (5 essential docs in root)
4. **Capability Routing**: Complete documentation and examples
5. **Test Organization**: Automated (pytest) vs manual (diagnostics) clarified
6. **Documentation**: Aligned and consolidated

### Grade Progression
- Initial: C+ (75/100)
- After Cleanup: A- (92/100)
- After Phase 1: A (94/100)
- **Final: A+ (98/100)** 🎉

---

## Repository Structure

```
DawsOSB/
├── README.md                           # Quick start
├── CAPABILITY_ROUTING_GUIDE.md        # Capability routing
├── CORE_INFRASTRUCTURE_STABILIZATION.md # Architecture
├── FINAL_ROADMAP_COMPLIANCE.md        # Compliance (A)
├── QUICK_WINS_COMPLETE.md             # Final improvements (A+)
├── dawsos/                            # Application
│   ├── core/                          # Trinity runtime
│   ├── agents/                        # 15 specialized agents
│   ├── patterns/                      # 45 workflow patterns
│   ├── storage/knowledge/             # 26 enriched datasets
│   ├── ui/                            # Streamlit dashboards
│   └── tests/
│       ├── validation/                # Automated pytest tests
│       └── manual/                    # Diagnostic scripts
├── docs/
│   ├── reports/                       # Progress reports
│   └── archive/                       # Historical docs
├── examples/archive/                  # Demo scripts
└── scripts/                           # Lint and validation tools
```

---

## Agent Capabilities

### 15 Agents with 50+ Capabilities

**Data Pipeline**:
- `data_harvester` - Market data, economic indicators, news
- `data_digester` - Raw data to graph nodes
- `relationship_hunter` - Correlation analysis

**Analysis**:
- `financial_analyst` - DCF, Buffett framework, valuations
- `pattern_spotter` - Pattern recognition
- `forecast_dreamer` - Predictive modeling

**Governance**:
- `governance_agent` - Data quality, compliance, lineage

**Development**:
- `code_monkey` - Code generation
- `refactor_elf` - Code improvements
- `structure_bot` - Architecture design

**Full list**: See [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md)

---

## Pattern Library

### 45 Patterns (0 Errors)

**Categories**:
- **Analysis** (14): Buffett checklist, Dalio cycles, sector rotation
- **System** (8): Architecture validation, capability checks
- **Governance** (6): Policy validation, quality audits
- **Macro** (5): Economic regime detection
- **Others** (12): Market overview, correlation analysis

**Validation**:
```bash
python3 scripts/lint_patterns.py
# Output: 45 patterns checked, 0 errors ✅
```

---

## Capability-Based Routing

### New in Version 2.0

Execute agents by **what they can do** rather than by name:

```python
# Traditional name-based
result = runtime.exec_via_registry('financial_analyst', context)

# New capability-based
result = runtime.execute_by_capability('can_calculate_dcf', context)
```

**Benefits**:
- More flexible agent swapping
- Better discoverability
- Graceful degradation

**Documentation**: [CAPABILITY_ROUTING_GUIDE.md](CAPABILITY_ROUTING_GUIDE.md)

---

## Deployment

### Prerequisites
- Python 3.10+
- Virtual environment with dependencies
- (Optional) API keys for external data

### Steps

See [Quick Start](#quick-start) section above for complete setup instructions.

### Production Checklist
- [ ] Set `TRINITY_STRICT_MODE=true` (optional)
- [ ] Configure API keys (optional)
- [ ] Review backup rotation settings
- [ ] Monitor bypass telemetry
- [ ] Check pattern execution logs

---

## Monitoring

### Health Check
```bash
curl http://localhost:8502/_stcore/health
```

### System Metrics
Access Trinity Dashboard at http://localhost:8502:
- **Overview**: Agent status, pattern execution
- **Compliance**: Registry bypass tracking
- **Governance**: Data quality metrics
- **Graph**: Node health and relationships

### Key Metrics
- Pattern compliance: 100%
- Knowledge coverage: 100% (26/26)
- Error handling: Professional
- CI/CD: Fully operational

---

## CI/CD Pipeline

### GitHub Actions Workflow
`.github/workflows/compliance-check.yml` includes:

1. **Trinity Compliance Check** - Validates architecture compliance
2. **Pattern Linting** - Validates all 45 patterns
3. **Test Suite** - Runs integration and unit tests
4. **Security Scan** - Bandit security analysis
5. **Compliance Summary** - Generates PR reports

**Status**: ✅ Fully operational

---

## Troubleshooting

### Common Issues

**Pattern execution fails**:
```bash
python3 scripts/lint_patterns.py  # Check patterns
```

**Knowledge loader errors**:
```bash
cd dawsos && python3 -c "from core.knowledge_loader import KnowledgeLoader; print(len(KnowledgeLoader().datasets))"
# Should output: 26
```

**Graph quality issues**:
- Check governance dashboard at http://localhost:8502
- Review data quality metrics
- Validate node connections

---

## Contributing

### Code Standards
- Follow Trinity architecture principles
- Use `execute_through_registry` for agent calls
- Run pattern linter before commits
- Update knowledge registry for new datasets

### Pull Request Process
1. Create feature branch
2. Make changes following Trinity patterns
3. Run `python3 scripts/lint_patterns.py`
4. Update documentation
5. Submit PR (CI will auto-validate)

---

## Support

- **Documentation**: See guides above
- **Issues**: Use GitHub issues
- **Health**: http://localhost:8502

---

## Acknowledgments

Built with:
- Trinity Architecture (Request → Executor → Pattern → Registry → Agent)
- Streamlit (UI framework)
- Python 3.10+ (Core language)

---

**Last Updated**: October 3, 2025
**Status**: ✅ Production Ready (A+ Grade - 98/100)
**App**: Running at http://localhost:8502
**Deployment**: Ready for immediate production use
