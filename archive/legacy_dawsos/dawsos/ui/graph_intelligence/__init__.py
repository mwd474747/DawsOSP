"""
Graph Intelligence Module
Exposes Knowledge Graph capabilities to users through interactive UI components

Phase 1 Features (Complete):
- Live Stats Dashboard: Real-time graph health metrics
- Connection Tracer: Show causal chains through the graph
- Impact Forecaster: AI-powered predictions based on relationships
- Related Suggestions: Discover connected investment opportunities

Phase 2 Features (Complete):
- Sector Correlations: Heatmap of sector relationships ✅
- Query Builder: SQL-like graph queries for power users ✅
- Comparative Analysis: Side-by-side stock comparison ✅

Phase 3 Features (In Progress):
- Analysis History: Timeline of valuations over time ✅
- Interactive Graph Visualizer: Network diagram with zoom/filter
- Pattern Discovery: Show auto-discovered patterns
"""

# Phase 1 imports
from .live_stats import render_live_stats
from .connection_tracer import render_connection_tracer
from .impact_forecaster import render_impact_forecaster
from .related_suggestions import render_related_suggestions

# Phase 2 imports
from .sector_correlations import render_sector_correlations
from .query_builder import render_query_builder
from .comparative_analysis import render_comparative_analysis

# Phase 3 imports
from .analysis_history import render_analysis_history

__all__ = [
    # Phase 1
    'render_live_stats',
    'render_connection_tracer',
    'render_impact_forecaster',
    'render_related_suggestions',
    # Phase 2
    'render_sector_correlations',
    'render_query_builder',
    'render_comparative_analysis',
    # Phase 3
    'render_analysis_history',
]

# Module version
__version__ = '3.0.0'
