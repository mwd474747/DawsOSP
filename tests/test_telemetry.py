#!/usr/bin/env python3
"""
Pytest tests for AgentRuntime telemetry tracking.
Converted from scripts/test_telemetry.py
"""
import pytest
import sys
import os
from datetime import datetime

# Add dawsos to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dawsos'))

from core.agent_runtime import AgentRuntime


class TestTelemetryTracking:
    """Test suite for AgentRuntime telemetry functionality"""

    @pytest.fixture
    def runtime(self):
        """Create fresh AgentRuntime instance for each test"""
        return AgentRuntime()

    @pytest.fixture
    def sample_metrics(self):
        """Sample execution metrics for testing"""
        return [
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

    def test_initial_telemetry_state(self, runtime):
        """Test that runtime starts with empty telemetry"""
        summary = runtime.get_telemetry_summary()

        assert summary['total_executions'] == 0, "Should start with 0 executions"
        assert summary['success_rate'] == 0, "Should start with 0% success rate"
        assert summary['avg_duration_ms'] == 0, "Should start with 0ms average duration"
        assert len(summary['executions_by_agent']) == 0, "Should have no agent tracking"
        assert len(summary['executions_by_pattern']) == 0, "Should have no pattern tracking"
        assert summary['last_execution_time'] is None, "Should have no last execution time"

    def test_track_single_execution(self, runtime):
        """Test tracking a single execution"""
        metrics = {
            'success': True,
            'duration_ms': 125.5,
            'timestamp': datetime.now().isoformat(),
            'pattern_id': 'test_pattern',
            'agent_used': 'test_agent',
            'graph_stored': True
        }

        runtime.track_execution(metrics)
        summary = runtime.get_telemetry_summary()

        assert summary['total_executions'] == 1
        assert summary['success_rate'] == 100.0
        assert summary['avg_duration_ms'] == 125.5
        assert 'test_agent' in summary['executions_by_agent']
        assert 'test_pattern' in summary['executions_by_pattern']
        assert summary['last_execution_time'] is not None

    def test_track_multiple_executions(self, runtime, sample_metrics):
        """Test tracking multiple executions"""
        for metrics in sample_metrics:
            runtime.track_execution(metrics)

        summary = runtime.get_telemetry_summary()

        assert summary['total_executions'] == 5
        assert summary['success_rate'] == 80.0  # 4 success, 1 failure

        # Expected average: (125.5 + 89.3 + 5000.0 + 42.1 + 167.8) / 5 = 1084.94
        expected_avg = round((125.5 + 89.3 + 5000.0 + 42.1 + 167.8) / 5, 2)
        assert summary['avg_duration_ms'] == expected_avg

    def test_agent_tracking(self, runtime, sample_metrics):
        """Test that agents are tracked correctly"""
        for metrics in sample_metrics:
            runtime.track_execution(metrics)

        summary = runtime.get_telemetry_summary()

        assert 'data_harvester' in summary['executions_by_agent']
        assert summary['executions_by_agent']['data_harvester'] == 2
        assert summary['executions_by_agent']['pattern_spotter'] == 2
        assert summary['executions_by_agent']['relationship_hunter'] == 1

    def test_pattern_tracking(self, runtime, sample_metrics):
        """Test that patterns are tracked correctly"""
        for metrics in sample_metrics:
            runtime.track_execution(metrics)

        summary = runtime.get_telemetry_summary()

        assert 'pattern_001' in summary['executions_by_pattern']
        assert summary['executions_by_pattern']['pattern_001'] == 2
        assert summary['executions_by_pattern']['pattern_002'] == 2
        assert summary['executions_by_pattern']['pattern_003'] == 1

    def test_telemetry_list_size(self, runtime):
        """Test that telemetry list is bounded to 1000 entries"""
        # Track more than 1000 executions
        for i in range(1050):
            runtime.track_execution({
                'success': True,
                'duration_ms': 100.0,
                'timestamp': datetime.now().isoformat(),
                'pattern_id': f'pattern_{i}',
                'agent_used': 'test_agent',
                'graph_stored': True
            })

        # Should be trimmed to 1000
        assert len(runtime.telemetry) == 1000, "Telemetry should be trimmed to 1000 entries"

        summary = runtime.get_telemetry_summary()
        assert summary['total_executions'] == 1050, "Total count should still be accurate"

    def test_last_execution_timestamp(self, runtime, sample_metrics):
        """Test that last execution time is updated"""
        for metrics in sample_metrics:
            runtime.track_execution(metrics)

        summary = runtime.get_telemetry_summary()
        assert summary['last_execution_time'] is not None

        # Should be the timestamp from the last execution
        last_timestamp = sample_metrics[-1]['timestamp']
        assert summary['last_execution_time'] == last_timestamp

    def test_success_rate_calculation(self, runtime):
        """Test success rate is calculated correctly"""
        # Track 3 success, 1 failure
        for success in [True, True, True, False]:
            runtime.track_execution({
                'success': success,
                'duration_ms': 100.0,
                'timestamp': datetime.now().isoformat(),
                'pattern_id': 'test',
                'agent_used': 'test',
                'graph_stored': True
            })

        summary = runtime.get_telemetry_summary()
        assert summary['success_rate'] == 75.0  # 3/4 = 75%

    def test_telemetry_with_missing_fields(self, runtime):
        """Test telemetry handles missing optional fields gracefully"""
        metrics = {
            'success': True,
            'timestamp': datetime.now().isoformat()
            # Missing: duration_ms, pattern_id, agent_used, graph_stored
        }

        runtime.track_execution(metrics)
        summary = runtime.get_telemetry_summary()

        assert summary['total_executions'] == 1
        # Should not crash even with missing fields
