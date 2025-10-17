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
- 15 specialized AI agents with 103 capabilities
- 50 pre-defined analysis patterns (Buffett checklist, Dalio cycles, etc.)
- Knowledge graph for relationship mapping
- Economic dashboard and market analysis
- Pattern-based workflow execution

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

## Recent Changes
### Replit Setup (October 17, 2025)
- Installed Python 3.11 and dependencies
- Configured Streamlit for Replit environment (port 5000, headless mode, CORS disabled)
- Removed hardcoded API keys from .env for security
- Set up workflow to run on port 5000 with webview output
- Created .streamlit/config.toml for proper proxy handling

## Known Issues
- FRED API warnings appear in logs when API key not configured (expected behavior - app uses cached data)
- seed_knowledge_graph module import error on first run (benign - graph initializes from JSON files)
- "Error in regime detection" on startup (doesn't affect functionality - uses fallback data)

## Project Structure
```
dawsos/
├── core/                 # Trinity runtime engine
├── agents/              # 15 specialized agents
├── capabilities/        # External API integrations
├── patterns/           # 50 JSON workflow patterns
├── storage/            # Knowledge graph and session data
├── ui/                 # Streamlit dashboard components
├── tests/              # Test suites
└── main.py            # Application entry point
```

## Developer Notes
- The app is designed to run without API keys using cached/fallback data
- All execution flows through the Trinity architecture (no direct agent calls)
- Pattern compliance is validated at 100%
- Streamlit config MUST allow all hosts for Replit proxy to work
