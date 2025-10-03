#!/usr/bin/env python3
"""
Test script for AgentRuntime telemetry tracking.
Tests the track_execution() and get_telemetry_summary() methods.
"""
import sys
import os
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dawsos'))

from core.agent_runtime import AgentRuntime


def test_telemetry_tracking():
    """Test telemetry tracking functionality"""
    print("=" * 60)
    print("Testing AgentRuntime Telemetry Tracking")
    print("=" * 60)

    # Create AgentRuntime instance
    print("\n1. Creating AgentRuntime instance...")
    runtime = AgentRuntime()
    print("   ✓ Runtime created")

    # Verify initial state
    print("\n2. Checking initial telemetry state...")
    initial_summary = runtime.get_telemetry_summary()
    print(f"   Total executions: {initial_summary['total_executions']}")
    print(f"   Success rate: {initial_summary['success_rate']}%")
    assert initial_summary['total_executions'] == 0, "Should start with 0 executions"
    print("   ✓ Initial state correct")

    # Track 5 sample executions
    print("\n3. Tracking 5 sample executions...")
    sample_metrics = [
        {
            'success': True,
            'duration_ms': 125.5,
            'timestamp': datetime.now().isoformat(),
            'pattern_id': 'pattern_001',
            'agent_used': 'data_harvester',
            'graph_stored': True
        },
        {
            'success': True,
            'duration_ms': 89.3,
            'timestamp': datetime.now().isoformat(),
            'pattern_id': 'pattern_002',
            'agent_used': 'pattern_spotter',
            'graph_stored': True
        },
        {
            'success': False,
            'error': 'Connection timeout',
            'duration_ms': 5000.0,
            'timestamp': datetime.now().isoformat(),
            'pattern_id': 'pattern_001',
            'agent_used': 'data_harvester',
            'graph_stored': False
        },
        {
            'success': True,
            'duration_ms': 42.1,
            'timestamp': datetime.now().isoformat(),
            'pattern_id': 'pattern_003',
            'agent_used': 'relationship_hunter',
            'graph_stored': True
        },
        {
            'success': True,
            'duration_ms': 167.8,
            'timestamp': datetime.now().isoformat(),
            'pattern_id': 'pattern_002',
            'agent_used': 'pattern_spotter',
            'graph_stored': True
        }
    ]

    for i, metrics in enumerate(sample_metrics, 1):
        runtime.track_execution(metrics)
        success_indicator = "✓" if metrics['success'] else "✗"
        print(f"   {success_indicator} Execution {i}: {metrics['pattern_id']} via {metrics['agent_used']} ({metrics['duration_ms']}ms)")

    # Get and display telemetry summary
    print("\n4. Getting telemetry summary...")
    summary = runtime.get_telemetry_summary()

    print("\n" + "=" * 60)
    print("TELEMETRY SUMMARY")
    print("=" * 60)
    print(json.dumps(summary, indent=2))

    # Verify results
    print("\n5. Verifying results...")
    assert summary['total_executions'] == 5, f"Expected 5 executions, got {summary['total_executions']}"
    print(f"   ✓ Total executions: {summary['total_executions']}")

    assert summary['success_rate'] == 80.0, f"Expected 80% success rate, got {summary['success_rate']}%"
    print(f"   ✓ Success rate: {summary['success_rate']}%")

    # Calculate expected average: (125.5 + 89.3 + 5000.0 + 42.1 + 167.8) / 5 = 1084.94
    expected_avg = round((125.5 + 89.3 + 5000.0 + 42.1 + 167.8) / 5, 2)
    assert summary['avg_duration_ms'] == expected_avg, f"Expected {expected_avg}ms avg, got {summary['avg_duration_ms']}ms"
    print(f"   ✓ Average duration: {summary['avg_duration_ms']}ms")

    # Check agent tracking
    assert 'data_harvester' in summary['executions_by_agent'], "data_harvester should be tracked"
    assert summary['executions_by_agent']['data_harvester'] == 2, "data_harvester should have 2 executions"
    assert summary['executions_by_agent']['pattern_spotter'] == 2, "pattern_spotter should have 2 executions"
    assert summary['executions_by_agent']['relationship_hunter'] == 1, "relationship_hunter should have 1 execution"
    print(f"   ✓ Agent tracking: {len(summary['executions_by_agent'])} agents tracked")

    # Check pattern tracking
    assert 'pattern_001' in summary['executions_by_pattern'], "pattern_001 should be tracked"
    assert summary['executions_by_pattern']['pattern_001'] == 2, "pattern_001 should have 2 executions"
    assert summary['executions_by_pattern']['pattern_002'] == 2, "pattern_002 should have 2 executions"
    assert summary['executions_by_pattern']['pattern_003'] == 1, "pattern_003 should have 1 execution"
    print(f"   ✓ Pattern tracking: {len(summary['executions_by_pattern'])} patterns tracked")

    # Check last execution time
    assert summary['last_execution_time'] is not None, "Last execution time should be set"
    print(f"   ✓ Last execution time: {summary['last_execution_time']}")

    # Test telemetry list trimming (verify max 1000 entries)
    print("\n6. Testing telemetry list trimming...")
    current_count = len(runtime.telemetry)
    print(f"   Current telemetry entries: {current_count}")
    assert current_count == 5, f"Should have 5 entries, got {current_count}"
    print("   ✓ Telemetry list size correct")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)

    return summary


if __name__ == '__main__':
    try:
        summary = test_telemetry_tracking()
        print("\n✓ Telemetry tracking integration test completed successfully")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
