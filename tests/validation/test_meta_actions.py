#!/usr/bin/env python3
"""Unit tests for meta pattern action handlers"""

import sys
from pathlib import Path
from datetime import datetime

# Add dawsos to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'dawsos'))

from core.pattern_engine import PatternEngine
from core.knowledge_graph import KnowledgeGraph
from core.agent_runtime import AgentRuntime


def test_select_router():
    """Test select_router action"""
    print("\n=== Testing select_router ===")
    engine = PatternEngine(pattern_dir='dawsos/patterns', runtime=None)

    # Test 1: Explicit agent request
    result = engine.execute_action(
        'select_router',
        {'request': {'type': 'test', 'agent': 'claude'}},
        {},
        {}
    )
    assert result['strategy'] == 'agent', f"Expected agent strategy, got {result['strategy']}"
    assert result['agent_name'] == 'claude', f"Expected claude agent, got {result.get('agent_name')}"
    print("✅ Test 1: Explicit agent request - PASSED")

    # Test 2: Pattern ID request
    result = engine.execute_action(
        'select_router',
        {'request': {'type': 'analysis', 'pattern_id': 'buffett_analysis'}},
        {},
        {}
    )
    assert result['strategy'] == 'pattern', f"Expected pattern strategy, got {result['strategy']}"
    assert result['pattern_id'] == 'buffett_analysis', f"Expected buffett_analysis, got {result.get('pattern_id')}"
    print("✅ Test 2: Pattern ID request - PASSED")

    # Test 3: User input (no match)
    result = engine.execute_action(
        'select_router',
        {'request': {'user_input': 'random question that does not match any pattern'}},
        {},
        {}
    )
    assert result['strategy'] == 'agent', f"Expected agent strategy for no match, got {result['strategy']}"
    assert result['agent_name'] == 'claude', f"Expected claude fallback, got {result.get('agent_name')}"
    print("✅ Test 3: User input (no match) - PASSED")

    print("✅ select_router: All tests passed")
    return True


def test_execute_pattern():
    """Test execute_pattern action"""
    print("\n=== Testing execute_pattern ===")
    engine = PatternEngine(pattern_dir='dawsos/patterns', runtime=None)

    # Test 1: Pattern not found
    result = engine.execute_action(
        'execute_pattern',
        {'pattern_id': 'nonexistent_pattern', 'context': {}},
        {},
        {}
    )
    assert 'error' in result, "Should return error for missing pattern"
    assert result['error'] == 'Pattern not found', f"Wrong error message: {result.get('error')}"
    print("✅ Test 1: Pattern not found - PASSED")

    # Test 2: Recursion guard
    result = engine.execute_action(
        'execute_pattern',
        {'pattern_id': 'meta_executor', 'context': {}},  # Use existing pattern
        {'_recursion_depth': 6},  # Already at depth 6 - THIS IS THE CONTEXT PARAM
        {}  # outputs
    )
    assert 'error' in result, "Should return error for max recursion"
    assert 'recursion' in result['error'].lower(), f"Wrong error message: {result.get('error')}"
    print("✅ Test 2: Recursion guard - PASSED")

    # Test 3: Valid pattern (with runtime returning fallback error)
    result = engine.execute_action(
        'execute_pattern',
        {'pattern_id': 'meta_executor', 'context': {'test': 'data'}},
        {},
        {}
    )
    # Without runtime, expect fallback error
    assert 'error' in result or 'No runtime' in str(result), "Should handle missing runtime gracefully"
    print("✅ Test 3: Valid pattern (no runtime) - PASSED")

    print("✅ execute_pattern: All tests passed")
    return True


def test_track_execution():
    """Test track_execution action"""
    print("\n=== Testing track_execution ===")
    engine = PatternEngine(pattern_dir='dawsos/patterns', runtime=None)

    # Test 1: Basic tracking without runtime
    start_time = datetime.now().isoformat()
    result = engine.execute_action(
        'track_execution',
        {
            'result': {'success': True, 'agent': 'test_agent'},
            'start_time': start_time
        },
        {'pattern_id': 'test_pattern'},  # context (3rd param)
        {}  # outputs (4th param)
    )
    assert result['success'] == True, "Should preserve success status"
    assert result['pattern_id'] == 'test_pattern', "Should track pattern ID"
    assert result['agent_used'] == 'test_agent', "Should track agent used"
    assert 'duration_ms' in result, "Should calculate duration"
    assert result['duration_ms'] is not None, "Duration should be calculated"
    print(f"✅ Test 1: Basic tracking - PASSED (duration: {result['duration_ms']:.1f}ms)")

    # Test 2: Error tracking
    result = engine.execute_action(
        'track_execution',
        {
            'result': {'success': False, 'error': 'Test error'},
            'start_time': datetime.now().isoformat()
        },
        {'pattern_id': 'error_pattern'},  # context
        {}  # outputs
    )
    assert result['success'] == False, "Should preserve error status"
    assert result['error'] == 'Test error', "Should track error message"
    print("✅ Test 2: Error tracking - PASSED")

    # Test 3: No start time (duration should be None)
    result = engine.execute_action(
        'track_execution',
        {'result': {'success': True}},
        {},
        {}
    )
    assert result['duration_ms'] is None, "Duration should be None without start_time"
    print("✅ Test 3: No start time - PASSED")

    print("✅ track_execution: All tests passed")
    return True


def test_store_in_graph():
    """Test store_in_graph action"""
    print("\n=== Testing store_in_graph ===")

    # Test 1: No graph available (no runtime)
    engine = PatternEngine(pattern_dir='dawsos/patterns', runtime=None)
    result = engine.execute_action(
        'store_in_graph',
        {'result': {'success': True}, 'metadata': {'source': 'test'}},
        {},
        {'pattern_id': 'test_pattern'}
    )
    assert result['stored'] == False, "Should return stored=False when no graph"
    assert result['reason'] == 'No graph available', "Should explain why not stored"
    print("✅ Test 1: No graph available - PASSED")

    # Test 2: With graph available
    graph = KnowledgeGraph()
    runtime = AgentRuntime()
    runtime.graph = graph  # Manually add graph to runtime for testing
    engine = PatternEngine(pattern_dir='dawsos/patterns', runtime=runtime)

    result = engine.execute_action(
        'store_in_graph',
        {
            'result': {'success': True, 'data': 'test_data'},
            'metadata': {'source': 'test'}
        },
        {'pattern_id': 'test_pattern'},  # context (3rd param)
        {}  # outputs (4th param)
    )
    assert result['stored'] == True, f"Should store successfully, got: {result}"
    assert 'node_id' in result, "Should return node_id"
    assert 'timestamp' in result, "Should return timestamp"
    print(f"✅ Test 2: Graph storage - PASSED (node_id: {result['node_id']})")

    # Test 3: Verify node was created
    node = graph.get_node(result['node_id'])
    assert node is not None, "Node should exist in graph"
    assert node['type'] == 'execution_result', f"Wrong node type: {node.get('type')}"
    assert node['data']['metadata']['pattern_id'] == 'test_pattern', "Should store pattern_id"
    print("✅ Test 3: Node verification - PASSED")

    print("✅ store_in_graph: All tests passed")
    return True


if __name__ == '__main__':
    try:
        print("Starting meta pattern action handler tests...")

        test_select_router()
        test_execute_pattern()
        test_track_execution()
        test_store_in_graph()

        print("\n" + "="*50)
        print("✅ ALL META ACTION TESTS PASSED")
        print("="*50)
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
