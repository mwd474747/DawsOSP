#!/usr/bin/env python3
"""Test PatternEngine graph reference (Phase 4)"""

import sys
from pathlib import Path

# Add dawsos to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'dawsos'))

from core.pattern_engine import PatternEngine
from core.knowledge_graph import KnowledgeGraph
from core.agent_runtime import AgentRuntime


def test_pattern_engine_graph_reference():
    """Test that PatternEngine receives graph reference correctly"""
    print("\n=== Testing PatternEngine Graph Reference ===")

    graph = KnowledgeGraph()
    runtime = AgentRuntime()
    runtime.graph = graph  # Add graph to runtime

    # Test 1: Pattern engine with explicit graph parameter
    engine = PatternEngine(
        pattern_dir='dawsos/patterns',
        runtime=runtime,
        graph=graph
    )

    assert hasattr(engine, 'graph'), "PatternEngine should have graph attribute"
    assert engine.graph is not None, "Graph should not be None"
    assert engine.graph is graph, "Graph should be the one we passed"
    print("✅ Test 1: Explicit graph parameter - PASSED")

    # Test 2: Pattern engine gets graph from runtime
    engine2 = PatternEngine(
        pattern_dir='dawsos/patterns',
        runtime=runtime,
        graph=None  # Don't pass graph explicitly
    )

    assert hasattr(engine2, 'graph'), "PatternEngine should have graph attribute"
    assert engine2.graph is not None, "Graph should be inferred from runtime"
    assert engine2.graph is graph, "Graph should be runtime.graph"
    print("✅ Test 2: Graph inferred from runtime - PASSED")

    # Test 3: Pattern engine with no graph (fallback)
    runtime_no_graph = AgentRuntime()
    engine3 = PatternEngine(
        pattern_dir='dawsos/patterns',
        runtime=runtime_no_graph,
        graph=None
    )

    assert hasattr(engine3, 'graph'), "PatternEngine should have graph attribute"
    assert engine3.graph is None, "Graph should be None when not provided"
    print("✅ Test 3: No graph (fallback) - PASSED")

    print("\n" + "="*50)
    print("✅ ALL GRAPH REFERENCE TESTS PASSED")
    print("="*50)
    return True


if __name__ == '__main__':
    try:
        test_pattern_engine_graph_reference()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
