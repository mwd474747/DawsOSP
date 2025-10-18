# DawsOS - Financial Intelligence System

## Overview
DawsOS is a **pattern-driven financial intelligence system** built with Python and Streamlit. It leverages a "Trinity" architecture (Request → Executor → Pattern → Registry → Agent) to orchestrate 15 specialized AI agents for market analysis, investment frameworks, and data governance. The system aims to provide advanced financial intelligence, including smart pattern analysis, real-time economic dashboards, and systemic risk assessment, making sophisticated financial tools accessible to users.

## User Preferences
I prefer iterative development, where changes are made incrementally, and I am asked for feedback regularly. Please prioritize using clear, concise language in all explanations and avoid overly technical jargon where possible. I value detailed explanations when new features or complex concepts are introduced. Do not make changes to the `dawsos/agents/` folder without explicit approval.

## System Architecture
DawsOS employs a Trinity architecture for orchestrating 15 specialized AI agents. The frontend is a Streamlit web UI, with the backend powered by a Python-based agent system utilizing a knowledge graph for relationship mapping. Data storage is file-based JSON, eliminating the need for an external database. The system supports optional API integrations for real-time data sources like FRED, FMP, and NewsAPI.

**Key Features include:**
- **Smart Patterns System**: Utilizes the `Instructor` library with Pydantic for structured NLU and entity extraction, enabling dynamic analysis based on user intent, depth, timeframe, and preferences. It includes conversational memory for multi-turn context tracking.
- **Systemic Risk Analysis**: Incorporates credit and empire cycle tracking (Ray Dalio's Big Debt Cycle framework) to provide multi-timeframe predictions and adjust confidence based on systemic risk factors.
- **Universal Pattern Rendering System**: Replaces plain markdown output with rich, interactive visualizations for all patterns, including gauge charts, time series charts, allocation pies, comparison bars, metric grids, heatmaps, and candlestick charts.
- **Economic Dashboard**: Features an executive summary with key metrics (GDP Growth, Inflation, Unemployment, Fed Funds Rate), an improved information architecture with collapsible sections for historical trends, regime & cycle analysis, systemic risk analysis, and an economic events calendar.

## External Dependencies
The system can operate without API keys using cached data, but offers enhanced functionality with the following optional integrations:
-   `ANTHROPIC_API_KEY`: For Claude AI live responses.
-   `FRED_API_KEY`: For economic indicators (e.g., GDP, inflation, unemployment, federal funds rate, and systemic risk indicators like debt-to-GDP ratios and delinquency rates).
-   `FMP_API_KEY`: For stock quotes and fundamentals.
-   `NEWSAPI_KEY`: For real-time news headlines.
-   `OPENAI_API_KEY`: Optional fallback for LLM.