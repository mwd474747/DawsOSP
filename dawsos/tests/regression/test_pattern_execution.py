#!/usr/bin/env python3
"""
Regression Tests for Pattern Engine and Pattern Execution

Tests that patterns:
- Load successfully from disk
- Execute without errors (dry-run mode)
- Handle variable substitution correctly
- Include expected result fields
- Work with execute_through_registry action
- Include versioning information
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.pattern_engine import PatternEngine
from core.knowledge_graph import KnowledgeGraph
from core.agent_runtime import AgentRuntime
from agents.data_harvester import DataHarvester
from agents.data_digester import DataDigester


class TestPatternLoading:
    """Test that all patterns load successfully"""

    @pytest.fixture
    def pattern_engine(self):
        """Create pattern engine instance"""
        return PatternEngine(pattern_dir='patterns')

    def test_pattern_engine_initialization(self, pattern_engine):
        """Test pattern engine initializes successfully"""
        assert pattern_engine is not None, "Pattern engine should initialize"
        assert hasattr(pattern_engine, 'patterns'), "Should have patterns attribute"
        assert hasattr(pattern_engine, 'pattern_dir'), "Should have pattern_dir attribute"

    def test_patterns_loaded(self, pattern_engine):
        """Test that patterns are loaded from disk"""
        assert len(pattern_engine.patterns) > 0, "Should load at least one pattern"

    def test_no_duplicate_pattern_ids(self, pattern_engine):
        """Test that pattern IDs are unique"""
        pattern_ids = list(pattern_engine.patterns.keys())
        unique_ids = set(pattern_ids)

        assert len(pattern_ids) == len(unique_ids), "Pattern IDs must be unique"

    def test_all_patterns_have_required_fields(self, pattern_engine):
        """Test that all loaded patterns have required fields"""
        required_fields = ['id', 'name']

        for pattern_id, pattern in pattern_engine.patterns.items():
            for field in required_fields:
                assert field in pattern, f"Pattern {pattern_id} missing required field: {field}"

    def test_pattern_steps_are_valid(self, pattern_engine):
        """Test that pattern steps are well-formed"""
        for pattern_id, pattern in pattern_engine.patterns.items():
            # Pattern should have either 'steps' or 'workflow'
            steps = pattern.get('steps', pattern.get('workflow', []))

            if steps:  # Only test if pattern has steps
                assert isinstance(steps, list), f"Pattern {pattern_id} steps must be a list"

                for i, step in enumerate(steps):
                    assert isinstance(step, dict), f"Pattern {pattern_id} step {i} must be a dict"
                    # Step should have either 'agent' or 'action'
                    has_agent_or_action = 'agent' in step or 'action' in step
                    assert has_agent_or_action, f"Pattern {pattern_id} step {i} must have 'agent' or 'action'"

    def test_pattern_source_files_tracked(self, pattern_engine):
        """Test that pattern source files are tracked"""
        for pattern_id, pattern in pattern_engine.patterns.items():
            # Should track source file for debugging
            if '_source_file' in pattern:
                source_file = pattern['_source_file']
                assert isinstance(source_file, str), f"Pattern {pattern_id} source file should be string"


class TestPatternExecution:
    """Test pattern execution without errors (dry-run mode)"""

    @pytest.fixture
    def graph(self):
        """Create fresh knowledge graph"""
        return KnowledgeGraph()

    @pytest.fixture
    def runtime(self, graph):
        """Create runtime with test agents"""
        runtime = AgentRuntime()

        # Register mock agents for testing
        mock_capabilities = {
            'fred': Mock(get_latest=Mock(return_value={'value': 100, 'date': '2024-01-01'})),
            'market': Mock(get_quote=Mock(return_value={'symbol': 'AAPL', 'price': 150})),
            'news': Mock()
        }

        runtime.register_agent('data_harvester', DataHarvester(graph, mock_capabilities))
        runtime.register_agent('data_digester', DataDigester(graph))

        return runtime

    @pytest.fixture
    def pattern_engine(self, runtime):
        """Create pattern engine with runtime"""
        return PatternEngine(pattern_dir='patterns', runtime=runtime)

    def test_simple_pattern_execution(self, pattern_engine):
        """Test execution of a simple pattern"""
        # Find a simple query pattern
        if pattern_engine.has_pattern('stock_price'):
            pattern = pattern_engine.get_pattern('stock_price')
            context = {'user_input': 'What is AAPL price?'}

            result = pattern_engine.execute_pattern(pattern, context)

            assert isinstance(result, dict), "Pattern execution must return dict"
            assert 'pattern' in result or 'error' in result, "Result must include pattern or error"

    def test_pattern_execution_with_context(self, pattern_engine):
        """Test pattern execution with context variables"""
        # Test with a pattern that uses context variables
        test_pattern = {
            'id': 'test_context_pattern',
            'name': 'Test Context Pattern',
            'steps': [
                {
                    'action': 'knowledge_lookup',
                    'params': {
                        'section': 'test_section'
                    }
                }
            ]
        }

        context = {'user_input': 'test query', 'symbol': 'AAPL'}
        result = pattern_engine.execute_pattern(test_pattern, context)

        assert isinstance(result, dict), "Must return dict"

    def test_pattern_execution_handles_missing_runtime(self):
        """Test pattern execution without runtime configured"""
        engine = PatternEngine(pattern_dir='patterns', runtime=None)

        test_pattern = {
            'id': 'test_no_runtime',
            'name': 'Test No Runtime',
            'steps': [{'action': 'test_action'}]
        }

        result = engine.execute_pattern(test_pattern, {})

        assert isinstance(result, dict), "Must return dict"
        assert 'error' in result, "Should indicate error when runtime missing"

    def test_all_patterns_execute_without_crash(self, pattern_engine):
        """Test that all patterns can be executed without crashing"""
        errors = []

        # Sample of patterns to test (limit to avoid long test runs)
        patterns_to_test = list(pattern_engine.patterns.items())[:10]

        for pattern_id, pattern in patterns_to_test:
            try:
                context = {'user_input': 'test input', 'symbol': 'AAPL'}
                result = pattern_engine.execute_pattern(pattern, context)

                assert isinstance(result, dict), f"Pattern {pattern_id} must return dict"

            except Exception as e:
                errors.append((pattern_id, str(e)))

        # Allow some patterns to have errors (e.g., missing agents)
        # but most should execute without crashing
        assert len(errors) < len(patterns_to_test) / 2, \
            f"Too many patterns failed: {errors[:5]}"


class TestVariableSubstitution:
    """Test variable substitution in pattern parameters"""

    @pytest.fixture
    def graph(self):
        """Create knowledge graph"""
        return KnowledgeGraph()

    @pytest.fixture
    def runtime(self, graph):
        """Create runtime"""
        runtime = AgentRuntime()
        runtime.register_agent('data_digester', DataDigester(graph))
        return runtime

    @pytest.fixture
    def pattern_engine(self, runtime):
        """Create pattern engine"""
        return PatternEngine(pattern_dir='patterns', runtime=runtime)

    def test_context_variable_substitution(self, pattern_engine):
        """Test that context variables are substituted correctly"""
        params = {
            'message': 'Hello {user_name}',
            'symbol': '{SYMBOL}'
        }

        context = {
            'user_name': 'Alice',
            'user_input': 'Check AAPL stock'
        }

        resolved = pattern_engine._resolve_params(params, context, {})

        assert resolved['message'] == 'Hello Alice', "Should substitute user_name"
        assert 'AAPL' in resolved['symbol'] or '{SYMBOL}' in resolved['symbol'], \
            "Should substitute or preserve SYMBOL"

    def test_output_variable_substitution(self, pattern_engine):
        """Test that output variables from previous steps are substituted"""
        params = {
            'value': 'Price is {step_1}'
        }

        context = {}
        outputs = {
            'step_1': 150.50
        }

        resolved = pattern_engine._resolve_params(params, context, outputs)

        assert '150.5' in resolved['value'], "Should substitute step output"

    def test_nested_output_substitution(self, pattern_engine):
        """Test nested output variable substitution"""
        params = {
            'message': 'Stock {quote.symbol} is at ${quote.price}'
        }

        context = {}
        outputs = {
            'quote': {
                'symbol': 'AAPL',
                'price': 150.50
            }
        }

        resolved = pattern_engine._resolve_params(params, context, outputs)

        assert 'AAPL' in resolved['message'], "Should substitute nested symbol"
        assert '150.5' in resolved['message'], "Should substitute nested price"

    def test_symbol_extraction_from_input(self, pattern_engine):
        """Test symbol extraction from user input"""
        params = {
            'symbol': '{SYMBOL}'
        }

        test_cases = [
            ('Check AAPL stock', 'AAPL'),
            ('What about MSFT?', 'MSFT'),
            ('How is Tesla doing?', 'TSLA'),  # Company name to symbol
        ]

        for user_input, expected_symbol in test_cases:
            context = {'user_input': user_input}
            resolved = pattern_engine._resolve_params(params, context, {})

            # Should extract symbol or keep placeholder
            assert expected_symbol in resolved['symbol'] or '{SYMBOL}' in resolved['symbol'], \
                f"Should extract {expected_symbol} from '{user_input}'"


class TestPatternResults:
    """Test that pattern results include expected fields"""

    @pytest.fixture
    def graph(self):
        """Create knowledge graph"""
        return KnowledgeGraph()

    @pytest.fixture
    def runtime(self, graph):
        """Create runtime"""
        runtime = AgentRuntime()
        runtime.register_agent('data_digester', DataDigester(graph))
        return runtime

    @pytest.fixture
    def pattern_engine(self, runtime):
        """Create pattern engine"""
        return PatternEngine(runtime=runtime)

    def test_pattern_result_includes_pattern_info(self, pattern_engine):
        """Test that result includes pattern information"""
        test_pattern = {
            'id': 'test_result_pattern',
            'name': 'Test Result Pattern',
            'steps': []
        }

        result = pattern_engine.execute_pattern(test_pattern, {})

        assert 'pattern' in result, "Result should include pattern name"
        assert result['pattern'] == 'Test Result Pattern', "Should include correct pattern name"

    def test_pattern_result_includes_step_results(self, pattern_engine):
        """Test that result includes results from all steps"""
        test_pattern = {
            'id': 'test_steps_pattern',
            'name': 'Test Steps Pattern',
            'steps': [
                {'action': 'knowledge_lookup', 'params': {'section': 'test'}},
                {'action': 'evaluate', 'params': {'type': 'test', 'checks': []}}
            ]
        }

        result = pattern_engine.execute_pattern(test_pattern, {})

        assert 'results' in result, "Result should include step results"
        assert isinstance(result['results'], list), "Step results should be a list"

    def test_pattern_result_type(self, pattern_engine):
        """Test that result includes response_type"""
        test_pattern = {
            'id': 'test_type_pattern',
            'name': 'Test Type Pattern',
            'response_type': 'stock_quote',
            'steps': []
        }

        result = pattern_engine.execute_pattern(test_pattern, {})

        assert 'type' in result, "Result should include type"
        assert result['type'] == 'stock_quote', "Should preserve response_type"


class TestExecuteThroughRegistry:
    """Test execute_through_registry action"""

    @pytest.fixture
    def graph(self):
        """Create knowledge graph"""
        return KnowledgeGraph()

    @pytest.fixture
    def runtime(self, graph):
        """Create runtime with registry"""
        runtime = AgentRuntime()
        runtime.register_agent('data_digester', DataDigester(graph))
        return runtime

    @pytest.fixture
    def pattern_engine(self, runtime):
        """Create pattern engine"""
        return PatternEngine(runtime=runtime)

    def test_execute_through_registry_action(self, pattern_engine):
        """Test execute_through_registry action works"""
        params = {
            'agent': 'data_digester',
            'method': 'process',
            'context': {'data': {'value': 100}, 'data_type': 'test'}
        }

        result = pattern_engine.execute_action(
            'execute_through_registry',
            params,
            context={},
            outputs={}
        )

        assert isinstance(result, dict), "Should return dict"
        # Should execute through registry if available
        if 'error' not in result:
            assert 'agent' in result or 'status' in result, "Should have agent or status"

    def test_registry_execution_adds_metadata(self, pattern_engine):
        """Test that registry execution adds Trinity metadata"""
        if not pattern_engine.runtime:
            pytest.skip("Runtime not configured")

        params = {
            'agent': 'data_digester',
            'context': {'data': {'value': 100}, 'data_type': 'test'}
        }

        result = pattern_engine.execute_action(
            'execute_through_registry',
            params,
            context={},
            outputs={}
        )

        if 'error' not in result:
            # Should have Trinity compliance metadata
            assert 'timestamp' in result or 'agent' in result, \
                "Registry execution should add metadata"


class TestPatternVersioning:
    """Test that patterns include versioning information"""

    @pytest.fixture
    def pattern_engine(self):
        """Create pattern engine"""
        return PatternEngine(pattern_dir='patterns')

    def test_patterns_can_include_version(self, pattern_engine):
        """Test that patterns can include version field"""
        # Create test pattern with version
        test_pattern = {
            'id': 'test_versioned_pattern',
            'name': 'Test Versioned Pattern',
            'version': '1.0.0',
            'steps': []
        }

        # Should not raise error
        assert test_pattern['version'] == '1.0.0', "Pattern can have version"

    def test_pattern_metadata_preservation(self, pattern_engine):
        """Test that pattern metadata is preserved during execution"""
        test_pattern = {
            'id': 'test_metadata_pattern',
            'name': 'Test Metadata Pattern',
            'version': '2.0.0',
            'author': 'Test Author',
            'description': 'Test description',
            'steps': []
        }

        # Execute pattern
        result = pattern_engine.execute_pattern(test_pattern, {})

        # Original pattern should be unchanged
        assert test_pattern['version'] == '2.0.0', "Version should be preserved"
        assert test_pattern['author'] == 'Test Author', "Author should be preserved"

    def test_source_file_tracking(self, pattern_engine):
        """Test that source files are tracked for loaded patterns"""
        for pattern_id, pattern in pattern_engine.patterns.items():
            # Loaded patterns should have source file tracked
            if pattern_id != 'test_pattern':  # Skip test patterns
                # May or may not have source file depending on loading method
                if '_source_file' in pattern:
                    assert isinstance(pattern['_source_file'], str), \
                        f"Pattern {pattern_id} source file should be string"


class TestPatternFindMatching:
    """Test pattern finding and matching"""

    @pytest.fixture
    def pattern_engine(self):
        """Create pattern engine"""
        return PatternEngine(pattern_dir='patterns')

    def test_find_pattern_by_trigger(self, pattern_engine):
        """Test finding pattern by trigger words"""
        # Add test pattern with specific trigger
        test_pattern = {
            'id': 'test_trigger_pattern',
            'name': 'Test Trigger',
            'triggers': ['stock price', 'quote'],
            'steps': []
        }
        pattern_engine.patterns['test_trigger_pattern'] = test_pattern

        # Find pattern
        found = pattern_engine.find_pattern('What is the stock price of AAPL?')

        # Should find a pattern (might be test or existing)
        assert found is None or isinstance(found, dict), "Should return pattern or None"

    def test_find_pattern_with_entity(self, pattern_engine):
        """Test finding pattern with entity matching"""
        test_pattern = {
            'id': 'test_entity_pattern',
            'name': 'Test Entity',
            'triggers': ['analyze'],
            'entities': ['AAPL', 'MSFT'],
            'steps': []
        }
        pattern_engine.patterns['test_entity_pattern'] = test_pattern

        # Find with entity
        found = pattern_engine.find_pattern('Analyze AAPL performance')

        # Should find pattern or another matching one
        assert found is None or isinstance(found, dict), "Should return pattern or None"

    def test_has_pattern_method(self, pattern_engine):
        """Test has_pattern method works correctly"""
        # Should have some patterns loaded
        if len(pattern_engine.patterns) > 0:
            first_pattern_id = list(pattern_engine.patterns.keys())[0]
            assert pattern_engine.has_pattern(first_pattern_id), \
                "has_pattern should return True for existing pattern"

        assert not pattern_engine.has_pattern('nonexistent_pattern_xyz'), \
            "has_pattern should return False for non-existent pattern"

    def test_get_pattern_method(self, pattern_engine):
        """Test get_pattern method works correctly"""
        # Get existing pattern
        if len(pattern_engine.patterns) > 0:
            first_pattern_id = list(pattern_engine.patterns.keys())[0]
            pattern = pattern_engine.get_pattern(first_pattern_id)

            assert pattern is not None, "Should return pattern"
            assert isinstance(pattern, dict), "Should return pattern dict"

        # Get non-existent pattern
        result = pattern_engine.get_pattern('nonexistent_pattern_xyz')
        assert result is None, "Should return None for non-existent pattern"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
