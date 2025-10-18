# DawsOS - Financial Intelligence System

## Project Overview
DawsOS is a **pattern-driven financial intelligence system** built with Python and Streamlit. It uses a Trinity architecture (Request → Executor → Pattern → Registry → Agent) to orchestrate 15 specialized agents for market analysis, investment frameworks, and data governance.

## Current State
- **Status**: Running successfully on Replit
- **URL**: Port 5000 (webview configured)
- **Python Version**: 3.11
- **Framework**: Streamlit 1.50.0+

## Architecture
- **Frontend**: Streamlit web UI on port 5000
- **Backend**: Python-based agent system with knowledge graph
- **Database**: File-based JSON storage (no external DB required)
- **API Integration**: Optional APIs for real-time data (FRED, FMP, NewsAPI, etc.)

## Key Features
- 15 specialized AI agents with 104 capabilities (NEW: `can_analyze_systemic_risk`)
- 51 pre-defined analysis patterns (NEW: deep_macro_analysis with systemic risk)
- Knowledge graph for relationship mapping
- Economic dashboard and market analysis
- Pattern-based workflow execution
- **Systemic Risk Analysis** (October 2025):
  - Credit cycle tracking (expansion/peak/contraction phases)
  - Empire cycle analysis (Ray Dalio's Big Debt Cycle framework)
  - Multi-timeframe predictions (near-term + long-term structural outlook)
  - Confidence adjustment based on systemic risk factors

## Configuration
### Required Files
- `.streamlit/config.toml` - Streamlit server configuration (port 5000, headless mode)
- `dawsos/.env` - Environment variables (API keys - all optional)

### Environment Variables (All Optional)
The system works fully without API keys using cached data:
- `ANTHROPIC_API_KEY` - Claude AI for live responses
- `FRED_API_KEY` - Economic indicators (GDP, inflation)
- `FMP_API_KEY` - Stock quotes and fundamentals
- `NEWSAPI_KEY` - Real-time news headlines
- `OPENAI_API_KEY` - Optional fallback LLM
- `TRINITY_STRICT_MODE` - Architecture compliance enforcement (default: false)

### FRED Economic Data Series
**Base Indicators** (used by all patterns):
- `GDP` - Gross Domestic Product (quarterly growth)
- `CPIAUCSL` - Consumer Price Index (inflation)
- `UNRATE` - Unemployment Rate
- `DFF` - Federal Funds Effective Rate

**Systemic Risk Indicators** (used by deep_macro_analysis pattern):
- `GFDEGDQ188S` - Federal Debt as % of GDP (debt sustainability)
- `SIPOVGINIUSA` - Gini Coefficient (income inequality, 0-1 scale)
- `HDTGPDUSQ163N` - Household Debt as % of GDP (consumer leverage)
- `TDSP` - Household Debt Service Payments as % of Disposable Income
- `DRCCLACBS` - Delinquency Rate on Credit Card Loans (credit stress)
- `EPUSOVDEBT` - Economic Policy Uncertainty Index: Sovereign Debt/Currency Crises

**Interpretation Guide**:
- **Credit Cycle Phases**:
  - Expansion: Debt/GDP < 90%, low delinquency, rising credit growth
  - Peak: Debt/GDP 90-110%, elevated delinquency (>3%), slowing credit growth
  - Contraction: Debt/GDP > 110%, high delinquency (>4%), negative credit growth
  - Trough: Deleveraging complete, low debt levels, credit growth resuming

- **Empire Cycle Stages** (Ray Dalio Framework):
  - Rising Empire: Debt/GDP < 80%, Gini < 0.40, low policy uncertainty
  - Peak Empire: Debt/GDP 80-100%, Gini 0.40-0.45, moderate uncertainty
  - Declining Empire: Debt/GDP > 100%, Gini > 0.45, high uncertainty
  - Crisis: Debt/GDP > 120%, Gini > 0.50, extreme uncertainty

- **Systemic Risk Score** (0-100 scale):
  - 0-30: Low risk - Normal economic conditions
  - 31-50: Moderate risk - Some vulnerabilities present
  - 51-70: Elevated risk - Multiple warning signals active
  - 71-100: High risk - Crisis conditions likely within 1-3 years

## Recent Changes
### Systemic Risk Analysis Enhancement (October 18, 2025)
- **NEW Pattern**: `deep_macro_analysis.json` - Comprehensive macroeconomic analysis with systemic risk overlay
- **NEW Capability**: `can_analyze_systemic_risk` - FinancialAnalyst method for credit/empire cycle analysis
- **NEW Methods**: 5 systemic risk analysis methods in FinancialAnalyst:
  - `_analyze_credit_cycle()` - Tracks debt leverage and credit stress indicators
  - `_analyze_empire_cycle()` - Ray Dalio's framework with debt/GDP, inequality, sovereignty proxies
  - `_calculate_systemic_risk_score()` - Composite 0-100 risk score
  - `_adjust_forecast_confidence()` - Reduces confidence when systemic risks are elevated
  - `analyze_systemic_risk()` - Public capability routing method
- **NEW FRED Series**: 6 additional indicators (GFDEGDQ188S, SIPOVGINIUSA, HDTGPDUSQ163N, TDSP, DRCCLACBS, EPUSOVDEBT)
- **Backward Compatible**: Existing patterns continue using base 4 indicators (GDP, CPI, Unemployment, Fed Funds)
- **Pattern Count**: 51 patterns total (was 50)
- **Capability Count**: 104 total (was 103)

### Documentation Consolidation (October 18, 2025)
- **Created PROJECT_ROADMAP.md**: Comprehensive roadmap consolidating all TODOs, plans, and phases
- **Validated system metrics**: Confirmed 51 patterns, 27 datasets, 15 agents, 104 capabilities
- **Updated documentation consistency**: All core docs now reflect accurate facts (A- grade, 51 patterns, 27 datasets)
- **Created pattern inventory**: Detailed breakdown of patterns with issues and priorities
- **Documented remediation plan**: 3-phase plan (Weeks 1-3) to address 6 categories of technical debt

### Replit Setup (October 17, 2025)
- Installed Python 3.11 and dependencies
- Configured Streamlit for Replit environment (port 5000, headless mode, CORS disabled)
- Removed hardcoded API keys from .env for security
- Set up workflow to run on port 5000 with webview output
- Created .streamlit/config.toml for proper proxy handling
- **Fixed API key integration**: Modified `load_env.py` to preserve Replit secrets (doesn't overwrite existing env vars)
- **Verified working**: FRED API, FMP API, Anthropic Claude API all operational

## System Grade
**A- (92/100)** - Operational with documented technical debt

**Key Metrics**:
- ✅ 51 patterns operational (NEW: deep_macro_analysis with systemic risk)
- ✅ 27 datasets in knowledge graph (96K+ nodes)
- ✅ 15 agents with 104 capabilities (NEW: can_analyze_systemic_risk)
- ⚠️ 6 categories of technical debt documented (template fragility, capability misuse, hybrid routing, etc.)

**See**: PROJECT_ROADMAP.md for complete remediation plan

## Known Issues (Non-Critical)
- FRED API warnings appear in logs when API key not configured (expected behavior - app uses cached data)
- seed_knowledge_graph module import error on first run (benign - graph initializes from JSON files)
- "Error in regime detection" on startup (doesn't affect functionality - uses fallback data)

For technical debt and pattern-specific issues, see:
- **PROJECT_ROADMAP.md** - Complete roadmap of TODOs, plans, and phases
- **KNOWN_PATTERN_ISSUES.md** - Detailed pattern-by-pattern analysis
- **SYSTEM_STATUS.md** - Known issues and technical debt

## Project Structure
```
dawsos/
├── core/                 # Trinity runtime engine
├── agents/              # 15 specialized agents
├── capabilities/        # External API integrations
├── patterns/           # 51 JSON workflow patterns
├── storage/            # Knowledge graph and session data
├── ui/                 # Streamlit dashboard components
├── tests/              # Test suites
└── main.py            # Application entry point
```

## Developer Notes
- The app is designed to run without API keys using cached/fallback data
- All execution flows through the Trinity architecture (no direct agent calls)
- Pattern compliance: ~85% capability routing (~40% patterns have hybrid agent calls)
- Streamlit config MUST allow all hosts for Replit proxy to work

## Documentation
- **PROJECT_ROADMAP.md** - Master roadmap: completed phases, active technical debt, remediation plan
- **SYSTEM_STATUS.md** - Current system status, metrics, known issues
- **KNOWN_PATTERN_ISSUES.md** - Pattern-by-pattern analysis, remediation priorities
- **PATTERN_AUTHORING_GUIDE.md** - Best practices for creating/editing patterns
- **CAPABILITY_ROUTING_GUIDE.md** - Capability selection matrix, common mistakes
- **TROUBLESHOOTING.md** - Pattern-specific troubleshooting, error handling
- **CLAUDE.md** - Trinity architecture primer, development guidelines
