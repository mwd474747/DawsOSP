"""DawsOS Agents (Trinity 3.0 Architecture) - Production Ready

6 agents registered in main.py:
- financial_analyst: DCF, stock analysis, portfolio risk
- claude: General intelligence, text processing
- data_harvester: Fetch stock quotes, economic data, news
- forecast_dreamer: Generate forecasts, project trends
- graph_mind: Manage graph structure, query relationships
- pattern_spotter: Detect patterns, analyze trends, find anomalies
"""

# Core DawsOS agents
from .base_agent import BaseAgent
from .claude import Claude
from .financial_analyst import FinancialAnalyst
from .data_harvester import DataHarvester
from .forecast_dreamer import ForecastDreamer
from .pattern_spotter import PatternSpotter
from .graph_mind import GraphMind

__all__ = [
    'BaseAgent',
    'Claude',
    'FinancialAnalyst',
    'DataHarvester',
    'ForecastDreamer',
    'PatternSpotter',
    'GraphMind'
]
