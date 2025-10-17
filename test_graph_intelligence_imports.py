#!/usr/bin/env python3
"""Test script to verify graph_intelligence imports work correctly"""

import sys
import os

# Add dawsos to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing Graph Intelligence Module Imports")
print("=" * 60)

# Test 1: Import graph_utils
print("\n1. Testing import from dawsos.ui.utils.graph_utils...")
try:
    from dawsos.ui.utils.graph_utils import get_node_display_name, safe_query, get_cached_graph_stats
    print("   ✅ SUCCESS: graph_utils imports work")
    print(f"   - get_node_display_name: {get_node_display_name}")
    print(f"   - safe_query: {safe_query}")
    print(f"   - get_cached_graph_stats: {get_cached_graph_stats}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    sys.exit(1)

# Test 2: Import individual graph intelligence features
print("\n2. Testing graph intelligence feature imports...")
features = [
    'live_stats',
    'connection_tracer',
    'impact_forecaster',
    'related_suggestions',
    'sector_correlations',
    'query_builder',
    'comparative_analysis',
    'analysis_history'
]

for feature in features:
    try:
        module_name = f"dawsos.ui.graph_intelligence.{feature}"
        module = __import__(module_name, fromlist=[f'render_{feature}'])
        render_func = getattr(module, f'render_{feature}')
        print(f"   ✅ {feature}: {render_func}")
    except Exception as e:
        print(f"   ❌ {feature}: {e}")
        sys.exit(1)

# Test 3: Import from __init__.py
print("\n3. Testing graph_intelligence __init__.py exports...")
try:
    from dawsos.ui.graph_intelligence import (
        render_live_stats,
        render_connection_tracer,
        render_impact_forecaster,
        render_related_suggestions,
        render_sector_correlations,
        render_query_builder,
        render_comparative_analysis,
        render_analysis_history
    )
    print("   ✅ SUCCESS: All exports from __init__.py work")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    sys.exit(1)

# Test 4: Verify function existence
print("\n4. Testing get_node_display_name function...")
try:
    test_node = "company_AAPL"
    result = get_node_display_name(test_node)
    print(f"   ✅ get_node_display_name('{test_node}') = '{result}'")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - Imports are working correctly!")
print("=" * 60)
