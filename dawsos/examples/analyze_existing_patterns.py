#!/usr/bin/env python3
"""
Analyze Existing Patterns - Check compliance of all patterns in the system

This script scans all patterns in the patterns directory and generates
a comprehensive compliance report showing which patterns need migration
to Trinity Architecture.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
from pathlib import Path
from core.compliance_checker import ComplianceChecker
from core.agent_adapter import AgentRegistry


def load_all_patterns(pattern_dir='patterns'):
    """Load all pattern files from directory"""
    patterns = []
    pattern_path = Path(pattern_dir)

    if not pattern_path.exists():
        print(f"Pattern directory not found: {pattern_dir}")
        return patterns

    for pattern_file in pattern_path.rglob('*.json'):
        # Skip schema files
        if pattern_file.name == 'schema.json':
            continue

        try:
            with open(pattern_file, 'r') as f:
                pattern = json.load(f)

                # Skip if it's a JSON schema
                if '$schema' in pattern:
                    continue

                patterns.append({
                    'pattern': pattern,
                    'file': str(pattern_file),
                    'relative_path': str(pattern_file.relative_to(pattern_path))
                })
        except json.JSONDecodeError as e:
            print(f"Error loading {pattern_file}: {e}")
        except Exception as e:
            print(f"Error processing {pattern_file}: {e}")

    return patterns


def analyze_patterns(patterns, checker):
    """Analyze all patterns for compliance"""
    results = {
        'compliant': [],
        'non_compliant': [],
        'warnings': []
    }

    for pattern_info in patterns:
        pattern = pattern_info['pattern']
        result = checker.check_pattern(pattern)

        pattern_summary = {
            'id': pattern.get('id', 'unknown'),
            'name': pattern.get('name', 'Unknown'),
            'file': pattern_info['relative_path'],
            'result': result
        }

        if result['compliant']:
            if result['warnings']:
                results['warnings'].append(pattern_summary)
            else:
                results['compliant'].append(pattern_summary)
        else:
            results['non_compliant'].append(pattern_summary)

    return results


def print_analysis_summary(results):
    """Print analysis summary"""
    total = len(results['compliant']) + len(results['non_compliant']) + len(results['warnings'])

    print("\n" + "=" * 80)
    print("PATTERN COMPLIANCE ANALYSIS SUMMARY")
    print("=" * 80)

    print(f"\nTotal Patterns Analyzed: {total}")
    print(f"  Fully Compliant: {len(results['compliant'])}")
    print(f"  Compliant with Warnings: {len(results['warnings'])}")
    print(f"  Non-Compliant: {len(results['non_compliant'])}")

    compliance_rate = (len(results['compliant']) / total * 100) if total > 0 else 0
    print(f"\nCompliance Rate: {compliance_rate:.1f}%")

    # Show non-compliant patterns
    if results['non_compliant']:
        print("\n" + "-" * 80)
        print("NON-COMPLIANT PATTERNS (Need Migration)")
        print("-" * 80)

        for pattern in results['non_compliant']:
            print(f"\n  Pattern: {pattern['id']}")
            print(f"  File: {pattern['file']}")
            print(f"  Violations:")

            for v in pattern['result']['violations']:
                print(f"    - [{v['severity'].upper()}] {v['type']}: {v['message']}")

    # Show patterns with warnings
    if results['warnings']:
        print("\n" + "-" * 80)
        print("PATTERNS WITH WARNINGS (Should Update)")
        print("-" * 80)

        for pattern in results['warnings']:
            print(f"\n  Pattern: {pattern['id']}")
            print(f"  File: {pattern['file']}")
            print(f"  Warnings:")

            for v in pattern['result']['violations']:
                if v['severity'] == 'warning':
                    print(f"    - {v['message']}")

    # Show compliant patterns
    print("\n" + "-" * 80)
    print(f"FULLY COMPLIANT PATTERNS ({len(results['compliant'])})")
    print("-" * 80)

    for pattern in results['compliant'][:10]:  # Show first 10
        print(f"  ✓ {pattern['id']} ({pattern['file']})")

    if len(results['compliant']) > 10:
        print(f"  ... and {len(results['compliant']) - 10} more")


def main():
    """Main analysis function"""
    print("\n" + "=" * 80)
    print("DawsOS Trinity Architecture - Pattern Compliance Analysis")
    print("=" * 80)

    # Setup (we don't have actual agents, so use empty registry)
    # In production, this would use the actual AgentRegistry
    registry = AgentRegistry()

    # Register placeholder agents that are commonly referenced
    # This prevents false positives for valid agent references
    class PlaceholderAgent:
        def process(self, context):
            return {}

    common_agents = [
        'data_harvester',
        'financial_analyst',
        'macro_agent',
        'equity_agent',
        'pattern_spotter',
        'relationship_hunter',
        'forecast_dreamer',
        'data_digester',
        'claude'
    ]

    for agent_name in common_agents:
        registry.register(agent_name, PlaceholderAgent())

    checker = ComplianceChecker(agent_registry=registry, strict_mode=False)

    # Load patterns
    print("\nLoading patterns...")
    patterns = load_all_patterns('patterns')
    print(f"Found {len(patterns)} patterns")

    if not patterns:
        print("No patterns found. Make sure you're running from the dawsos directory.")
        return

    # Analyze patterns
    print("\nAnalyzing compliance...")
    results = analyze_patterns(patterns, checker)

    # Print summary
    print_analysis_summary(results)

    # Generate full report
    print("\n" + "=" * 80)
    report = checker.get_compliance_report()

    print("\nRECOMMENDATIONS:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"  {i}. {rec}")

    # Export report
    report_file = 'pattern_compliance_analysis.json'
    checker.export_report(report_file)
    print(f"\nFull compliance report exported to: {report_file}")

    print("\n" + "=" * 80)
    print("Analysis Complete!")
    print("=" * 80)

    # Return exit code based on compliance
    if results['non_compliant']:
        print("\nWARNING: Non-compliant patterns found. Migration recommended.")
        return 1
    else:
        print("\nSUCCESS: All patterns are Trinity-compliant!")
        return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
