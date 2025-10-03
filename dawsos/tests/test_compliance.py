#!/usr/bin/env python3
"""
Test suite for ComplianceChecker

Tests Trinity Architecture compliance validation:
- Pattern validation
- Agent access monitoring
- Compliance reporting
"""

import unittest
import os
from datetime import datetime
from core.compliance_checker import ComplianceChecker, ComplianceViolation, get_compliance_checker
from core.agent_adapter import AgentRegistry


class MockAgent:
    """Mock agent for testing"""

    def __init__(self, name):
        self.name = name

    def process(self, context):
        return {'response': f'Mock response from {self.name}'}


class TestComplianceChecker(unittest.TestCase):
    """Test ComplianceChecker functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Create registry with mock agents
        self.registry = AgentRegistry()
        self.registry.register('data_harvester', MockAgent('data_harvester'))
        self.registry.register('pattern_spotter', MockAgent('pattern_spotter'))
        self.registry.register('claude', MockAgent('claude'))

        # Create checker
        self.checker = ComplianceChecker(
            agent_registry=self.registry,
            strict_mode=False
        )

    def tearDown(self):
        """Clean up after tests"""
        self.checker.reset_stats()

    def test_compliant_pattern_with_execute_through_registry(self):
        """Test that patterns using execute_through_registry pass validation"""
        pattern = {
            'id': 'test_compliant_pattern',
            'name': 'Test Compliant Pattern',
            'version': '1.0',
            'last_updated': '2025-10-02',
            'steps': [
                {
                    'agent': 'data_harvester',
                    'action': 'execute_through_registry',
                    'params': {
                        'request': 'test'
                    }
                }
            ]
        }

        result = self.checker.check_pattern(pattern)

        self.assertTrue(result['compliant'])
        self.assertEqual(result['pattern_id'], 'test_compliant_pattern')
        self.assertEqual(len(result['violations']), 0)

    def test_non_compliant_pattern_with_direct_agent_reference(self):
        """Test that direct agent references are caught"""
        pattern = {
            'id': 'test_non_compliant_pattern',
            'name': 'Test Non-Compliant Pattern',
            'version': '1.0',
            'last_updated': '2025-10-02',
            'steps': [
                {
                    'agent': 'data_harvester',
                    'action': 'harvest',  # Should be execute_through_registry
                    'params': {
                        'request': 'test'
                    }
                }
            ]
        }

        result = self.checker.check_pattern(pattern)

        # In non-strict mode, this is a warning
        self.assertFalse(result['compliant'])
        self.assertGreater(len(result['violations']), 0)

        # Check violation details
        violation = result['violations'][0]
        self.assertEqual(violation['type'], 'direct_agent_reference')
        self.assertIn('execute_through_registry', violation['message'])

    def test_strict_mode_warnings_as_errors(self):
        """Test that strict mode treats warnings as non-compliant"""
        strict_checker = ComplianceChecker(
            agent_registry=self.registry,
            strict_mode=True
        )

        # Pattern with only warnings (missing metadata)
        pattern = {
            'id': 'test_strict_pattern',
            'name': 'Test Strict Pattern',
            # Missing version and last_updated - normally just warnings
            'steps': [
                {
                    'action': 'knowledge_lookup',
                    'params': {}
                }
            ]
        }

        result = strict_checker.check_pattern(pattern)

        # In strict mode, warnings make the pattern non-compliant
        self.assertFalse(result['compliant'])

    def test_pattern_missing_metadata(self):
        """Test that missing version/last_updated generates warnings"""
        pattern = {
            'id': 'test_missing_metadata',
            'name': 'Test Pattern',
            # Missing version and last_updated
            'steps': []
        }

        result = self.checker.check_pattern(pattern)

        # Should have warnings for missing metadata
        violations = [v for v in result['violations'] if v['type'] == 'missing_metadata']
        self.assertGreaterEqual(len(violations), 2)  # version and last_updated

    def test_pattern_with_invalid_agent_reference(self):
        """Test that unknown agent names are caught"""
        pattern = {
            'id': 'test_invalid_agent',
            'name': 'Test Invalid Agent',
            'version': '1.0',
            'last_updated': '2025-10-02',
            'steps': [
                {
                    'agent': 'nonexistent_agent',
                    'action': 'execute_through_registry',
                    'params': {}
                }
            ]
        }

        result = self.checker.check_pattern(pattern)

        self.assertFalse(result['compliant'])

        # Should have violation for invalid agent
        invalid_agent_violations = [
            v for v in result['violations']
            if v['type'] == 'invalid_agent_reference'
        ]
        self.assertGreater(len(invalid_agent_violations), 0)

    def test_validate_individual_step(self):
        """Test validation of individual step"""
        # Compliant step
        compliant_step = {
            'agent': 'data_harvester',
            'action': 'execute_through_registry',
            'params': {'request': 'test'}
        }

        violations, warnings = self.checker.validate_step(compliant_step, 0)
        self.assertEqual(len(violations), 0)

        # Non-compliant step
        non_compliant_step = {
            'agent': 'claude',
            'action': 'interpret',  # Should use execute_through_registry
            'params': {'user_input': 'test'}
        }

        violations, warnings = self.checker.validate_step(non_compliant_step, 0)
        self.assertGreater(len(violations), 0)

    def test_legacy_action_format_warning(self):
        """Test that legacy action formats generate warnings"""
        pattern = {
            'id': 'test_legacy_pattern',
            'name': 'Test Legacy Pattern',
            'version': '1.0',
            'last_updated': '2025-10-02',
            'steps': [
                {
                    'action': 'agent:data_harvester',  # Legacy format
                    'params': {'request': 'test'}
                }
            ]
        }

        result = self.checker.check_pattern(pattern)

        # Should have warnings about legacy format
        self.assertGreater(len(result['warnings']), 0)
        self.assertTrue(
            any('legacy' in w.lower() for w in result['warnings'])
        )

    def test_agent_access_monitoring(self):
        """Test agent access monitoring"""
        # Authorized access
        result1 = self.checker.check_agent_access('agent_runtime', 'data_harvester')
        self.assertTrue(result1['compliant'])

        # Unauthorized access
        result2 = self.checker.check_agent_access('ui.dashboard', 'claude')
        self.assertFalse(result2['compliant'])
        self.assertIsNotNone(result2['warning'])

    def test_compliance_report_generation(self):
        """Test compliance report generation"""
        # Check several patterns
        patterns = [
            {
                'id': 'pattern_1',
                'name': 'Pattern 1',
                'version': '1.0',
                'last_updated': '2025-10-02',
                'steps': [
                    {
                        'agent': 'data_harvester',
                        'action': 'execute_through_registry',
                        'params': {}
                    }
                ]
            },
            {
                'id': 'pattern_2',
                'name': 'Pattern 2',
                'version': '1.0',
                'last_updated': '2025-10-02',
                'steps': [
                    {
                        'agent': 'claude',
                        'action': 'interpret',  # Non-compliant
                        'params': {}
                    }
                ]
            }
        ]

        for pattern in patterns:
            self.checker.check_pattern(pattern)

        # Generate report
        report = self.checker.get_compliance_report()

        # Verify report structure
        self.assertIn('overall', report)
        self.assertIn('violations', report)
        self.assertIn('pattern_details', report)
        self.assertIn('recommendations', report)

        # Verify statistics
        self.assertEqual(report['overall']['total_patterns_checked'], 2)
        self.assertGreater(report['overall']['pattern_compliance_rate'], 0)

    def test_pattern_compliance_status_lookup(self):
        """Test retrieving compliance status for specific pattern"""
        pattern = {
            'id': 'lookup_test_pattern',
            'name': 'Lookup Test',
            'version': '1.0',
            'last_updated': '2025-10-02',
            'steps': []
        }

        self.checker.check_pattern(pattern)

        # Lookup pattern status
        status = self.checker.get_pattern_compliance_status('lookup_test_pattern')

        self.assertIsNotNone(status)
        self.assertEqual(status['pattern_id'], 'lookup_test_pattern')
        self.assertTrue(status['compliant'])

        # Lookup non-existent pattern
        missing_status = self.checker.get_pattern_compliance_status('does_not_exist')
        self.assertIsNone(missing_status)

    def test_statistics_tracking(self):
        """Test that statistics are properly tracked"""
        # Initial state
        self.assertEqual(self.checker.stats['patterns_checked'], 0)

        # Check a compliant pattern
        compliant_pattern = {
            'id': 'stats_test_1',
            'name': 'Stats Test 1',
            'version': '1.0',
            'last_updated': '2025-10-02',
            'steps': [
                {
                    'agent': 'data_harvester',
                    'action': 'execute_through_registry',
                    'params': {}
                }
            ]
        }

        self.checker.check_pattern(compliant_pattern)

        self.assertEqual(self.checker.stats['patterns_checked'], 1)
        self.assertEqual(self.checker.stats['patterns_compliant'], 1)

        # Check a non-compliant pattern
        non_compliant_pattern = {
            'id': 'stats_test_2',
            'name': 'Stats Test 2',
            # Missing metadata
            'steps': [
                {
                    'agent': 'claude',
                    'action': 'interpret',
                    'params': {}
                }
            ]
        }

        self.checker.check_pattern(non_compliant_pattern)

        self.assertEqual(self.checker.stats['patterns_checked'], 2)
        self.assertEqual(self.checker.stats['patterns_non_compliant'], 1)

    def test_reset_stats(self):
        """Test resetting statistics"""
        # Generate some data with a non-compliant pattern
        pattern = {
            'id': 'reset_test',
            'name': 'Reset Test',
            # Missing version - will generate violation
            'steps': [
                {
                    'agent': 'unknown_agent',  # Invalid agent
                    'action': 'execute_through_registry',
                    'params': {}
                }
            ]
        }

        self.checker.check_pattern(pattern)
        self.checker.check_agent_access('test_module', 'test_agent')

        # Verify data exists
        self.assertGreater(self.checker.stats['patterns_checked'], 0)
        self.assertGreater(len(self.checker.violations), 0)  # Should have violations now

        # Reset
        self.checker.reset_stats()

        # Verify reset
        self.assertEqual(self.checker.stats['patterns_checked'], 0)
        self.assertEqual(len(self.checker.violations), 0)
        self.assertEqual(len(self.checker.pattern_checks), 0)
        self.assertEqual(len(self.checker.agent_access_log), 0)

    def test_export_report(self):
        """Test exporting compliance report to file"""
        import tempfile
        import json

        # Generate some compliance data
        pattern = {
            'id': 'export_test',
            'name': 'Export Test',
            'version': '1.0',
            'last_updated': '2025-10-02',
            'steps': []
        }

        self.checker.check_pattern(pattern)

        # Export to temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            self.checker.export_report(temp_path)

            # Verify file exists and contains valid JSON
            self.assertTrue(os.path.exists(temp_path))

            with open(temp_path, 'r') as f:
                report_data = json.load(f)

            self.assertIn('overall', report_data)
            self.assertIn('violations', report_data)

        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_get_compliance_checker_singleton(self):
        """Test singleton pattern for global compliance checker"""
        checker1 = get_compliance_checker(self.registry)
        checker2 = get_compliance_checker()

        # Should return the same instance
        self.assertIs(checker1, checker2)

    def test_compliance_violation_to_dict(self):
        """Test ComplianceViolation serialization"""
        violation = ComplianceViolation(
            violation_type='test_violation',
            severity='warning',
            message='Test message',
            context={'key': 'value'}
        )

        violation_dict = violation.to_dict()

        self.assertEqual(violation_dict['type'], 'test_violation')
        self.assertEqual(violation_dict['severity'], 'warning')
        self.assertEqual(violation_dict['message'], 'Test message')
        self.assertEqual(violation_dict['context']['key'], 'value')
        self.assertIn('timestamp', violation_dict)

    def test_recommendations_generation(self):
        """Test that recommendations are generated based on violations"""
        # Create patterns with different violation types
        patterns = [
            {
                'id': 'rec_test_1',
                'name': 'Rec Test 1',
                # Missing metadata
                'steps': [
                    {
                        'agent': 'data_harvester',
                        'action': 'harvest',  # Direct reference
                        'params': {}
                    }
                ]
            },
            {
                'id': 'rec_test_2',
                'name': 'Rec Test 2',
                'version': '1.0',
                'last_updated': '2025-10-02',
                'steps': [
                    {
                        'agent': 'unknown_agent',  # Invalid agent
                        'action': 'execute_through_registry',
                        'params': {}
                    }
                ]
            }
        ]

        for pattern in patterns:
            self.checker.check_pattern(pattern)

        report = self.checker.get_compliance_report()
        recommendations = report['recommendations']

        # Should have recommendations for the violations
        self.assertGreater(len(recommendations), 0)

        # Check for specific recommendations
        recommendation_text = ' '.join(recommendations).lower()
        self.assertTrue(
            'execute_through_registry' in recommendation_text or
            'metadata' in recommendation_text or
            'agent' in recommendation_text
        )


class TestComplianceIntegration(unittest.TestCase):
    """Integration tests for ComplianceChecker with real patterns"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.registry = AgentRegistry()
        self.registry.register('data_harvester', MockAgent('data_harvester'))
        self.registry.register('financial_analyst', MockAgent('financial_analyst'))
        self.registry.register('macro_agent', MockAgent('macro_agent'))

        self.checker = ComplianceChecker(self.registry, strict_mode=False)

    def test_moat_analyzer_pattern_structure(self):
        """Test compliance of a pattern similar to moat_analyzer"""
        moat_pattern = {
            'id': 'moat_analyzer',
            'name': 'Economic Moat Analyzer',
            'version': '1.0',
            'last_updated': '2025-10-02',
            'steps': [
                {
                    'action': 'knowledge_lookup',
                    'params': {
                        'knowledge_file': 'buffett_framework.json',
                        'section': 'economic_moat'
                    }
                },
                {
                    'action': 'evaluate',
                    'outputs': ['brand_score'],
                    'params': {
                        'type': 'brand_moat',
                        'checks': ['premium_pricing_ability']
                    }
                },
                {
                    'action': 'synthesize',
                    'outputs': ['moat_rating'],
                    'params': {
                        'scores': ['{brand_score}']
                    }
                }
            ]
        }

        result = self.checker.check_pattern(moat_pattern)

        # Pattern should be compliant (no agent references)
        self.assertTrue(result['compliant'])
        self.assertEqual(len(result['violations']), 0)


def run_tests():
    """Run all compliance tests"""
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run_tests()
