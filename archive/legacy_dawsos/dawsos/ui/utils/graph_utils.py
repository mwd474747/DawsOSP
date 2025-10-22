"""Shared utilities for graph intelligence features"""

import streamlit as st
from typing import Dict, List, Any, Optional
import pandas as pd

def safe_query(graph: Any, pattern: Dict[str, Any], max_results: int = 100) -> List[str]:
    """
    Query graph with result limiting for UI safety

    Args:
        graph: KnowledgeGraph instance
        pattern: Query pattern dict
        max_results: Maximum results to return

    Returns:
        List of node IDs (limited to max_results)
    """
    try:
        results = graph.query(pattern)
        if len(results) > max_results:
            st.warning(f"⚠️ Found {len(results)} results, showing first {max_results}")
            return results[:max_results]
        return results
    except Exception as e:
        st.error(f"Query failed: {str(e)}")
        return []

def format_node_display(node: Dict[str, Any]) -> str:
    """Format node for user-friendly display"""
    node_type = node.get('type', 'unknown')
    node_id = node.get('id', 'N/A')
    created = node.get('created', 'Unknown')

    # Extract key data fields
    data = node.get('data', {})
    if 'symbol' in data:
        return f"📊 {data['symbol']} ({node_type})"
    elif 'name' in data:
        return f"🏷️ {data['name']} ({node_type})"
    else:
        return f"🔹 {node_id} ({node_type})"

def format_path_display(path: List[Dict[str, Any]]) -> str:
    """Format connection path for readable display"""
    if not path:
        return "No path"

    parts = []
    for step in path:
        from_node = step.get('from', '?')
        to_node = step.get('to', '?')
        rel_type = step.get('type', 'connected')
        strength = step.get('strength', 0)

        # Clean up node IDs (remove prefix)
        from_clean = from_node.replace('company_', '').replace('sector_', '').replace('economic_', '')
        to_clean = to_node.replace('company_', '').replace('sector_', '').replace('economic_', '')

        parts.append(f"{from_clean} --[{rel_type} {strength:.2f}]--> {to_clean}")

    return "\n".join(parts)

@st.cache_data(ttl=300)
def get_cached_graph_stats(_graph: Any) -> Dict[str, Any]:
    """Get graph stats with 5-minute caching

    Args:
        _graph: KnowledgeGraph instance (underscore prefix prevents hashing)

    Returns:
        Dictionary with graph statistics
    """
    return _graph.get_stats()

def create_metric_card(label: str, value: Any, delta: Optional[str] = None) -> None:
    """Consistent metric card styling

    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta string (e.g., "+5%")
    """
    st.metric(label, value, delta)

def clean_node_id(node_id: str) -> str:
    """Clean node ID for display

    Args:
        node_id: Raw node ID (e.g., 'company_AAPL', 'sector_Technology')

    Returns:
        Cleaned ID (e.g., 'AAPL', 'Technology')
    """
    # Remove common prefixes
    prefixes = ['company_', 'sector_', 'economic_', 'dcf_analysis_', 'moat_analysis_']
    for prefix in prefixes:
        if node_id.startswith(prefix):
            return node_id[len(prefix):]
    return node_id

def get_node_display_name(node: str) -> str:
    """Convert node ID to human-readable display name

    Args:
        node: Node ID (e.g., 'company_AAPL', 'sector_Technology')

    Returns:
        Human-readable name (e.g., 'AAPL', 'Technology')
    """
    # Remove prefixes and clean up
    name = node.replace('company_', '').replace('sector_', '').replace('economic_', '')
    name = name.replace('dcf_analysis_', '').replace('moat_analysis_', '')
    return name.replace('_', ' ').title()
