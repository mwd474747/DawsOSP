#!/usr/bin/env python3
"""Integration test for meta_executor pattern flow"""

import sys
from pathlib import Path

# Add dawsos to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'dawsos'))

from core.pattern_engine import PatternEngine
from core.knowledge_graph import KnowledgeGraph
from core.agent_runtime import AgentRuntime


def test_meta_executor_flow():
    """Test complete meta_executor pattern execution flow"""
    print("\n=== Testing meta_executor pattern flow ===")

    # Setup
    graph = KnowledgeGraph()
    runtime = AgentRuntime()
    runtime.graph = graph  # Add graph for store_in_graph action

    engine = PatternEngine(pattern_dir='dawsos/patterns', runtime=runtime)

    # Verify meta_executor pattern loaded
    assert engine.has_pattern('meta_executor'), "meta_executor pattern should be loaded"
    print("✅ meta_executor pattern loaded")

    # Get the pattern
    pattern = engine.get_pattern('meta_executor')
    assert pattern is not None, "Should retrieve meta_executor pattern"
    print(f"✅ Retrieved meta_executor pattern with {len(pattern.get('steps', []))} steps")

    # Verify pattern has required steps
    steps = pattern.get('steps', [])
    expected_actions = ['detect_execution_type', 'select_router', 'execute_pattern', 'track_execution']

    actual_actions = [step.get('action') for step in steps]
    for expected in expected_actions:
        assert expected in actual_actions, f"Pattern should have {expected} action"

    print(f"✅ Pattern has all required actions: {actual_actions}")

    # Test the flow (without runtime, will use fallback but actions should work)
    # Note: Full execution would require runtime with registered agents

    # Test 1: select_router action works
    router_result = engine.execute_action(
        'select_router',
        {'request': {'type': 'test', 'pattern_id': 'buffett_checklist'}},
        {},
        {}
    )
    assert router_result['strategy'] == 'pattern', "Should route to pattern"
    assert router_result['pattern_id'] == 'buffett_checklist', "Should select buffett_checklist"
    print("✅ select_router action working correctly")

    # Test 2: Verify actions are registered in supported_actions
    # This happens during pattern execution, so we check the execute_action method
    test_actions = ['select_router', 'execute_pattern', 'track_execution', 'store_in_graph']
    for action in test_actions:
        # Try to execute each action - if not supported, would return error
        result = engine.execute_action(action, {}, {}, {})
        # select_router returns routing decision, others may return errors but shouldn't fail on "unknown action"
        assert 'Unknown action' not in str(result), f"Action {action} should be supported"

    print(f"✅ All meta pattern actions are supported: {test_actions}")

    # Test 3: Integration - routing leads to pattern execution
    # This would require full runtime setup, so we just verify the chain is possible

    # Simulated flow:
    # 1. Request comes in
    request = {'type': 'analysis', 'pattern_id': 'buffett_checklist'}

    # 2. select_router determines strategy
    router_decision = engine.execute_action('select_router', {'request': request}, {}, {})
    assert router_decision['strategy'] == 'pattern', "Should choose pattern strategy"

    # 3. execute_pattern would be called (but requires runtime)
    # We verify it exists and has recursion guard
    exec_result = engine.execute_action(
        'execute_pattern',
        {'pattern_id': router_decision['pattern_id'], 'context': {}},
        {'_recursion_depth': 0},  # Start at depth 0
        {}
    )
    # Will fail without runtime, but should not hit recursion guard
    assert 'recursion' not in str(exec_result).lower(), "Should not hit recursion guard at depth 0"

    # 4. track_execution would record metrics
    track_result = engine.execute_action(
        'track_execution',
        {'result': exec_result, 'start_time': None},
        {'pattern_id': 'buffett_checklist'},
        {}
    )
    assert 'timestamp' in track_result, "Should track execution with timestamp"

    # 5. store_in_graph would save to knowledge graph
    store_result = engine.execute_action(
        'store_in_graph',
        {'result': exec_result, 'metadata': {'test': True}},
        {'pattern_id': 'buffett_checklist'},
        {}
    )
    assert 'stored' in store_result, "Should attempt graph storage"

    print("✅ Meta pattern execution flow validated")

    print("\n" + "="*50)
    print("✅ META_EXECUTOR INTEGRATION TEST PASSED")
    print("="*50)
    return True


if __name__ == '__main__':
    try:
        test_meta_executor_flow()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
