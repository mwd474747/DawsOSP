# DawsOS - Financial Intelligence System

## Overview
DawsOS is a **pattern-driven financial intelligence system** built with Python and Streamlit. It leverages a "Trinity" architecture (Request → Executor → Pattern → Registry → Agent) to orchestrate 15 specialized AI agents for market analysis, investment frameworks, and data governance. The system provides Bloomberg Terminal-quality financial intelligence with 64 analysis patterns, including smart pattern analysis, real-time economic dashboards, and systemic risk assessment.

## User Preferences
I prefer iterative development, where changes are made incrementally, and I am asked for feedback regularly. Please prioritize using clear, concise language in all explanations and avoid overly technical jargon where possible. I value detailed explanations when new features or complex concepts are introduced. Do not make changes to the `dawsos/agents/` folder without explicit approval.

## Design Guidelines
- **NO ICONS/EMOJIS**: The interface should maintain a professional Bloomberg Terminal aesthetic. Never use emojis, icons, or decorative symbols in titles, headers, or UI elements. This includes but is not limited to: 📊, 📈, 📉, 💰, ⚠️, 🎯, etc.
- **Modern Professional Theme**: Purple-pink-blue gradient banner with glass morphism effects on a dark background
- **Typography**: Clean, minimal text without decorative elements
- **Visual Hierarchy**: Use color, size, and spacing rather than icons to establish importance

## System Architecture
DawsOS employs a Trinity architecture for orchestrating 15 specialized AI agents. The frontend is a Streamlit web UI, with the backend powered by a Python-based agent system utilizing a knowledge graph for relationship mapping. Data storage is file-based JSON, eliminating the need for an external database. The system supports optional API integrations for real-time data sources like FRED, FMP, and NewsAPI.

**Key Features include:**
- **Smart Patterns System** (64 total patterns): Utilizes the `Instructor` library with Pydantic for structured NLU and entity extraction, enabling dynamic analysis based on user intent, depth, timeframe, and preferences. Includes conversational memory for multi-turn context tracking.
- **Advanced Macro Analysis Patterns** (6 Bloomberg-quality deep dives):
  - Recession Risk Dashboard: Multi-indicator probability analysis with scenario forecasting
  - Macro-Aware Sector Allocation: Regime-driven sector rotation strategy
  - Multi-Timeframe Economic Outlook: Short/medium/long-term scenario planning
  - Fed Policy Impact Analyzer: Transmission mechanism analysis across all channels
  - Housing Market & Credit Cycle: Real estate analysis integrated with debt cycle framework
  - Labor Market Deep Dive: Comprehensive employment analysis with systemic implications
- **Systemic Risk Analysis**: Incorporates credit and empire cycle tracking (Ray Dalio's Big Debt Cycle framework) to provide multi-timeframe predictions and adjust confidence based on systemic risk factors.
- **Universal Pattern Rendering System**: Rich, interactive visualizations for all patterns, including gauge charts, time series charts, allocation pies, comparison bars, metric grids, heatmaps, and candlestick charts.
- **Economic Dashboard**: Executive summary with key metrics (GDP Growth, Inflation, Unemployment, Fed Funds Rate), collapsible sections for historical trends, regime & cycle analysis, systemic risk analysis, and economic events calendar.

## External Dependencies
The system can operate without API keys using cached data, but offers enhanced functionality with the following optional integrations:
-   `ANTHROPIC_API_KEY`: For Claude AI live responses.
-   `FRED_API_KEY`: For economic indicators (e.g., GDP, inflation, unemployment, federal funds rate, and systemic risk indicators like debt-to-GDP ratios and delinquency rates).
-   `FMP_API_KEY`: For stock quotes and fundamentals.
-   `NEWSAPI_KEY`: For real-time news headlines.
-   `OPENAI_API_KEY`: Optional fallback for LLM.