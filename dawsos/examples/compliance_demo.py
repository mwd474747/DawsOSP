#!/usr/bin/env python3
"""
Compliance Checker Demo - Shows ComplianceChecker in action

This script demonstrates:
1. Pattern validation with compliant and non-compliant examples
2. Agent access monitoring
3. Compliance report generation
4. Integration with Trinity Architecture
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.compliance_checker import ComplianceChecker
from core.agent_adapter import AgentRegistry
import json


class DemoAgent:
    """Simple demo agent"""
    def __init__(self, name):
        self.name = name

    def process(self, context):
        return {'response': f'Demo response from {self.name}'}


def setup_demo_environment():
    """Set up demo environment with registry and agents"""
    print("Setting up demo environment...")

    # Create agent registry
    registry = AgentRegistry()

    # Register demo agents
    registry.register('data_harvester', DemoAgent('data_harvester'))
    registry.register('financial_analyst', DemoAgent('financial_analyst'))
    registry.register('macro_agent', DemoAgent('macro_agent'))
    registry.register('claude', DemoAgent('claude'))

    # Create compliance checker
    checker = ComplianceChecker(agent_registry=registry, strict_mode=False)

    print(f"  Registered {len(registry.agents)} agents")
    print(f"  ComplianceChecker initialized (strict_mode={checker.strict_mode})")

    return checker, registry


def demo_compliant_pattern(checker):
    """Demonstrate a fully compliant pattern"""
    print("\n" + "=" * 80)
    print("DEMO 1: Trinity-Compliant Pattern")
    print("=" * 80)

    pattern = {
        'id': 'compliant_moat_analysis',
        'name': 'Compliant Moat Analysis Pattern',
        'description': 'Properly structured pattern using execute_through_registry',
        'version': '1.0',
        'last_updated': '2025-10-02',
        'steps': [
            {
                'action': 'knowledge_lookup',
                'params': {
                    'knowledge_file': 'buffett_framework.json',
                    'section': 'economic_moat'
                },
                'outputs': ['moat_knowledge']
            },
            {
                'agent': 'financial_analyst',
                'action': 'execute_through_registry',
                'params': {
                    'analysis_type': 'moat_evaluation',
                    'context': '{moat_knowledge}'
                },
                'outputs': ['moat_score']
            },
            {
                'action': 'synthesize',
                'params': {
                    'scores': ['{moat_score}']
                },
                'outputs': ['final_rating']
            }
        ]
    }

    print("\nPattern Structure:")
    print(json.dumps(pattern, indent=2))

    result = checker.check_pattern(pattern)

    print(f"\n{'SUCCESS' if result['compliant'] else 'FAILED'}: Compliance Check")
    print(f"  Compliant: {result['compliant']}")
    print(f"  Violations: {len(result['violations'])}")
    print(f"  Warnings: {len(result['warnings'])}")

    if result['violations']:
        print("\n  Violations found:")
        for v in result['violations']:
            print(f"    - [{v['severity'].upper()}] {v['type']}: {v['message']}")


def demo_non_compliant_pattern(checker):
    """Demonstrate a non-compliant pattern with direct agent reference"""
    print("\n" + "=" * 80)
    print("DEMO 2: Non-Compliant Pattern (Direct Agent Reference)")
    print("=" * 80)

    pattern = {
        'id': 'non_compliant_analysis',
        'name': 'Non-Compliant Analysis Pattern',
        'description': 'Legacy pattern with direct agent reference',
        'version': '1.0',
        'last_updated': '2025-10-02',
        'steps': [
            {
                'agent': 'data_harvester',
                'action': 'harvest',  # VIOLATION: Should use execute_through_registry
                'params': {
                    'request': 'get stock data'
                }
            },
            {
                'agent': 'financial_analyst',
                'action': 'analyze',  # VIOLATION: Should use execute_through_registry
                'params': {
                    'data': '{step_0}'
                }
            }
        ]
    }

    print("\nPattern Structure:")
    print(json.dumps(pattern, indent=2))

    result = checker.check_pattern(pattern)

    print(f"\n{'SUCCESS' if result['compliant'] else 'FAILED'}: Compliance Check")
    print(f"  Compliant: {result['compliant']}")
    print(f"  Violations: {len(result['violations'])}")

    if result['violations']:
        print("\n  Violations found:")
        for v in result['violations']:
            print(f"    - [{v['severity'].upper()}] {v['type']}: {v['message']}")

    print("\n  Migration Path:")
    print("    Change 'action' to 'execute_through_registry' for all agent steps")


def demo_missing_metadata(checker):
    """Demonstrate pattern with missing metadata"""
    print("\n" + "=" * 80)
    print("DEMO 3: Pattern Missing Metadata")
    print("=" * 80)

    pattern = {
        'id': 'missing_metadata_pattern',
        'name': 'Pattern Without Metadata',
        # Missing: version, last_updated
        'steps': [
            {
                'action': 'knowledge_lookup',
                'params': {
                    'section': 'test'
                }
            }
        ]
    }

    print("\nPattern Structure:")
    print(json.dumps(pattern, indent=2))

    result = checker.check_pattern(pattern)

    print(f"\n{'SUCCESS' if result['compliant'] else 'FAILED'}: Compliance Check")
    print(f"  Compliant: {result['compliant']}")
    print(f"  Violations: {len(result['violations'])}")

    if result['violations']:
        print("\n  Violations found:")
        for v in result['violations']:
            print(f"    - [{v['severity'].upper()}] {v['type']}: {v['message']}")


def demo_invalid_agent_reference(checker):
    """Demonstrate pattern referencing unknown agent"""
    print("\n" + "=" * 80)
    print("DEMO 4: Pattern with Invalid Agent Reference")
    print("=" * 80)

    pattern = {
        'id': 'invalid_agent_pattern',
        'name': 'Pattern with Unknown Agent',
        'version': '1.0',
        'last_updated': '2025-10-02',
        'steps': [
            {
                'agent': 'nonexistent_agent',
                'action': 'execute_through_registry',
                'params': {
                    'query': 'test'
                }
            }
        ]
    }

    print("\nPattern Structure:")
    print(json.dumps(pattern, indent=2))

    result = checker.check_pattern(pattern)

    print(f"\n{'SUCCESS' if result['compliant'] else 'FAILED'}: Compliance Check")
    print(f"  Compliant: {result['compliant']}")
    print(f"  Violations: {len(result['violations'])}")

    if result['violations']:
        print("\n  Violations found:")
        for v in result['violations']:
            print(f"    - [{v['severity'].upper()}] {v['type']}: {v['message']}")


def demo_agent_access_monitoring(checker):
    """Demonstrate agent access monitoring"""
    print("\n" + "=" * 80)
    print("DEMO 5: Agent Access Monitoring")
    print("=" * 80)

    print("\nMonitoring agent access from different modules:")

    # Authorized access
    result1 = checker.check_agent_access('agent_runtime', 'data_harvester')
    print(f"\n  Access from 'agent_runtime':")
    print(f"    Compliant: {result1['compliant']}")
    if result1['warning']:
        print(f"    Warning: {result1['warning']}")

    # Unauthorized access
    result2 = checker.check_agent_access('ui.dashboard', 'financial_analyst')
    print(f"\n  Access from 'ui.dashboard':")
    print(f"    Compliant: {result2['compliant']}")
    if result2['warning']:
        print(f"    Warning: {result2['warning']}")

    result3 = checker.check_agent_access('random_module', 'claude')
    print(f"\n  Access from 'random_module':")
    print(f"    Compliant: {result3['compliant']}")
    if result3['warning']:
        print(f"    Warning: {result3['warning']}")


def generate_compliance_report(checker):
    """Generate and display comprehensive compliance report"""
    print("\n" + "=" * 80)
    print("COMPLIANCE REPORT")
    print("=" * 80)

    report = checker.get_compliance_report()

    print(f"\nGenerated: {report['generated_at']}")
    print(f"Strict Mode: {report['strict_mode']}")

    # Overall metrics
    print("\nOVERALL COMPLIANCE:")
    overall = report['overall']
    print(f"  Pattern Compliance Rate: {overall['pattern_compliance_rate']}%")
    print(f"  Agent Access Compliance Rate: {overall['agent_access_compliance_rate']}%")
    print(f"  Total Patterns Checked: {overall['total_patterns_checked']}")
    print(f"  Compliant Patterns: {overall['compliant_patterns']}")
    print(f"  Non-Compliant Patterns: {overall['non_compliant_patterns']}")

    # Violations
    print("\nVIOLATIONS:")
    violations = report['violations']
    print(f"  Total Violations: {violations['total']}")

    if violations['by_type']:
        print("\n  By Type:")
        for violation_type, count in violations['by_type'].items():
            print(f"    - {violation_type}: {count}")

    if violations['by_severity']:
        print("\n  By Severity:")
        for severity, count in violations['by_severity'].items():
            print(f"    - {severity.upper()}: {count}")

    # Recommendations
    print("\nRECOMMENDATIONS:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"  {i}. {rec}")

    # Export to file
    report_file = 'compliance_report_demo.json'
    checker.export_report(report_file)
    print(f"\nFull report exported to: {report_file}")


def main():
    """Run all compliance demos"""
    print("\n" + "=" * 80)
    print("DawsOS Trinity Architecture - Compliance Checker Demo")
    print("=" * 80)

    # Setup
    checker, registry = setup_demo_environment()

    # Run demos
    demo_compliant_pattern(checker)
    demo_non_compliant_pattern(checker)
    demo_missing_metadata(checker)
    demo_invalid_agent_reference(checker)
    demo_agent_access_monitoring(checker)

    # Generate report
    generate_compliance_report(checker)

    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  1. Use action='execute_through_registry' for all agent steps")
    print("  2. Include version and last_updated in all patterns")
    print("  3. Verify all agent names exist in registry")
    print("  4. Access agents through AgentRuntime.execute(), not directly")
    print("  5. Monitor compliance reports regularly")
    print("\nFor strict enforcement, set TRINITY_STRICT_MODE=true")


if __name__ == '__main__':
    main()
