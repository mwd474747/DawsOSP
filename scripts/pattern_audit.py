#!/usr/bin/env python3
"""
Trinity 3.0 Pattern Compliance Audit
Checks all patterns for compliance with Trinity 3.0 standards
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Emoji detection regex
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE
)

# Knowledge loading capabilities (should use enriched_lookup instead)
KNOWLEDGE_CAPABILITIES = {
    'can_fetch_economic_data',  # FRED API, not for knowledge loading
    'can_fetch_fundamentals',   # Real-time API, not static data
    'can_fetch_stock_quotes',   # Real-time API
}

# Correct knowledge loading action
KNOWLEDGE_ACTION = 'enriched_lookup'

# Required fields for Trinity 3.0
REQUIRED_FIELDS = ['id', 'name', 'description', 'category', 'steps', 'version']

# Professional standards
PROFESSIONAL_STANDARDS = {
    'no_emojis': True,
    'use_registry': True,
    'proper_capabilities': True,
    'has_version': True,
}


def find_emojis(text: str) -> List[str]:
    """Find all emojis in text"""
    return EMOJI_PATTERN.findall(text)


def check_pattern_compliance(pattern_path: Path) -> Dict:
    """Comprehensive compliance check for a single pattern"""

    with open(pattern_path, 'r') as f:
        pattern = json.load(f)

    issues = []
    warnings = []

    # 1. Check required fields
    missing_fields = [f for f in REQUIRED_FIELDS if f not in pattern]
    if missing_fields:
        issues.append(f"Missing required fields: {', '.join(missing_fields)}")

    # 2. Check for emojis in template
    template = pattern.get('template', '')
    emojis_found = find_emojis(template)
    if emojis_found:
        issues.append(f"Found {len(emojis_found)} emojis in template: {' '.join(set(emojis_found))}")

    # 3. Check steps for compliance
    steps = pattern.get('steps', [])
    for i, step in enumerate(steps):
        step_num = i + 1
        action = step.get('action', '')

        # Check for direct agent calls
        if 'agent' in step and action != 'execute_through_registry':
            issues.append(f"Step {step_num}: Direct agent call '{step.get('agent')}' (should use execute_through_registry)")

        # Check for wrong capability usage
        if action == 'execute_through_registry':
            capability = step.get('params', {}).get('capability', '')

            # Check if using API capability for knowledge loading
            if capability in KNOWLEDGE_CAPABILITIES:
                # Check context to see if it's loading knowledge
                context = step.get('params', {}).get('context', {})
                if 'dataset_name' in str(context) or 'knowledge' in step.get('description', '').lower():
                    warnings.append(
                        f"Step {step_num}: Using '{capability}' for knowledge loading "
                        f"(should use '{KNOWLEDGE_ACTION}' action instead)"
                    )

        # Check for load_knowledge action (deprecated)
        if action == 'load_knowledge':
            warnings.append(f"Step {step_num}: Using deprecated 'load_knowledge' (use '{KNOWLEDGE_ACTION}' instead)")

    # 4. Check version field
    version = pattern.get('version', None)
    if not version:
        warnings.append("Missing 'version' field")
    elif version not in ['2.0', '3.0']:
        warnings.append(f"Version '{version}' should be '3.0' for Trinity 3.0")

    # 5. Check for nested template fields (potential fragility)
    nested_fields = re.findall(r'\{(\w+\.\w+(?:\.\w+)*)\}', template)
    if nested_fields:
        warnings.append(f"Template uses {len(nested_fields)} nested fields (fragile): {', '.join(set(nested_fields))}")

    # Calculate compliance score
    total_checks = 5
    issues_count = len([i for i in issues if 'emoji' in i.lower() or 'direct agent' in i.lower() or 'missing required' in i.lower()])
    compliance_score = max(0, 100 - (issues_count * 20) - (len(warnings) * 5))

    return {
        'pattern': pattern_path.name,
        'category': pattern_path.parent.name,
        'id': pattern.get('id', 'UNKNOWN'),
        'version': version,
        'issues': issues,
        'warnings': warnings,
        'compliance_score': compliance_score,
        'compliant': len(issues) == 0
    }


def audit_all_patterns() -> Tuple[List[Dict], Dict]:
    """Audit all patterns in patterns/ directory"""

    patterns_dir = Path('patterns')
    pattern_files = list(patterns_dir.glob('**/*.json'))

    results = []
    summary = {
        'total_patterns': len(pattern_files),
        'compliant': 0,
        'non_compliant': 0,
        'total_issues': 0,
        'total_warnings': 0,
        'avg_compliance': 0,
    }

    for pattern_file in sorted(pattern_files):
        result = check_pattern_compliance(pattern_file)
        results.append(result)

        if result['compliant']:
            summary['compliant'] += 1
        else:
            summary['non_compliant'] += 1

        summary['total_issues'] += len(result['issues'])
        summary['total_warnings'] += len(result['warnings'])

    if results:
        summary['avg_compliance'] = sum(r['compliance_score'] for r in results) / len(results)

    return results, summary


def print_audit_report(results: List[Dict], summary: Dict):
    """Print formatted audit report"""

    print("=" * 80)
    print("TRINITY 3.0 PATTERN COMPLIANCE AUDIT")
    print("=" * 80)
    print()

    # Summary
    print("SUMMARY")
    print("-" * 80)
    print(f"Total Patterns:       {summary['total_patterns']}")
    print(f"Compliant:            {summary['compliant']} ({summary['compliant']/summary['total_patterns']*100:.1f}%)")
    print(f"Non-Compliant:        {summary['non_compliant']} ({summary['non_compliant']/summary['total_patterns']*100:.1f}%)")
    print(f"Total Issues:         {summary['total_issues']}")
    print(f"Total Warnings:       {summary['total_warnings']}")
    print(f"Avg Compliance Score: {summary['avg_compliance']:.1f}/100")
    print()

    # Non-compliant patterns
    non_compliant = [r for r in results if not r['compliant']]
    if non_compliant:
        print("NON-COMPLIANT PATTERNS")
        print("-" * 80)
        for result in non_compliant:
            print(f"\n❌ {result['pattern']} ({result['category']}/)")
            print(f"   ID: {result['id']}")
            print(f"   Version: {result['version']}")
            print(f"   Compliance Score: {result['compliance_score']}/100")

            if result['issues']:
                print(f"   Issues ({len(result['issues'])}):")
                for issue in result['issues']:
                    print(f"      - {issue}")

            if result['warnings']:
                print(f"   Warnings ({len(result['warnings'])}):")
                for warning in result['warnings']:
                    print(f"      - {warning}")

    # Compliant patterns
    compliant = [r for r in results if r['compliant']]
    if compliant:
        print("\n✅ COMPLIANT PATTERNS")
        print("-" * 80)
        for result in compliant:
            warnings_str = f" ({len(result['warnings'])} warnings)" if result['warnings'] else ""
            print(f"   {result['pattern']} - {result['compliance_score']}/100{warnings_str}")

    print("\n" + "=" * 80)

    # Recommendations
    if summary['non_compliant'] > 0:
        print("\nRECOMMENDED ACTIONS")
        print("-" * 80)

        emoji_count = sum(1 for r in results if any('emoji' in i.lower() for i in r['issues']))
        if emoji_count > 0:
            print(f"1. Remove emojis from {emoji_count} pattern templates (professional standard)")

        direct_agent_count = sum(1 for r in results if any('direct agent' in i.lower() for i in r['issues']))
        if direct_agent_count > 0:
            print(f"2. Fix {direct_agent_count} patterns using direct agent calls (use execute_through_registry)")

        capability_count = sum(1 for r in results if any('capability' in w.lower() for w in r['warnings']))
        if capability_count > 0:
            print(f"3. Review {capability_count} patterns with capability warnings")

        print()


if __name__ == '__main__':
    results, summary = audit_all_patterns()
    print_audit_report(results, summary)

    # Exit with non-zero if non-compliant patterns found
    exit(0 if summary['non_compliant'] == 0 else 1)
