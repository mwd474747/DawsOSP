#!/usr/bin/env python3
"""
Comprehensive Pattern Analysis
Checks for: completeness, anti-patterns, orphaned code, capability mapping
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class PatternAnalyzer:
    def __init__(self, pattern_dir: str = 'dawsos/patterns'):
        self.pattern_dir = Path(pattern_dir)
        self.patterns = []
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)

    def load_patterns(self):
        """Load all pattern files"""
        for pattern_file in self.pattern_dir.rglob('*.json'):
            if pattern_file.name == 'schema.json':
                continue

            try:
                with open(pattern_file, 'r') as f:
                    pattern = json.load(f)
                    if '$schema' not in pattern:  # Skip schema files
                        pattern['_filepath'] = str(pattern_file.relative_to(self.pattern_dir))
                        self.patterns.append(pattern)
            except Exception as e:
                self.issues['load_errors'].append(f"{pattern_file}: {e}")

        self.stats['total_patterns'] = len(self.patterns)

    def check_anti_patterns(self):
        """Check for anti-patterns in pattern structure"""

        for pattern in self.patterns:
            filepath = pattern.get('_filepath', 'unknown')
            steps = pattern.get('steps', pattern.get('workflow', []))

            # Anti-pattern 1: Direct agent calls (bypass registry)
            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    continue

                # Check for old agent-based routing
                if 'agent' in step.get('params', {}):
                    agent_name = step['params'].get('agent')
                    # Allow 'claude' agent (intentional for LLM orchestration)
                    if agent_name != 'claude':
                        self.issues['legacy_agent_routing'].append(
                            f"{filepath} step {i}: Uses legacy 'agent' param instead of 'capability'"
                        )

            # Anti-pattern 2: Missing version/last_updated
            if 'version' not in pattern:
                self.issues['missing_version'].append(f"{filepath}: No version field")
            elif pattern.get('version') not in ['2.0', 2.0, '2', 2]:
                self.issues['wrong_version'].append(
                    f"{filepath}: Version {pattern.get('version')} (should be 2.0)"
                )

            if 'last_updated' not in pattern:
                self.issues['missing_last_updated'].append(f"{filepath}: No last_updated field")

            # Anti-pattern 3: Empty or missing triggers
            triggers = pattern.get('triggers', [])
            if not triggers:
                self.issues['missing_triggers'].append(f"{filepath}: No triggers defined")
            elif len(triggers) < 2:
                self.issues['insufficient_triggers'].append(
                    f"{filepath}: Only {len(triggers)} trigger (recommend 3+ for coverage)"
                )

            # Anti-pattern 4: No template for user output
            if 'template' not in pattern:
                self.issues['missing_template'].append(f"{filepath}: No output template")

            # Anti-pattern 5: Steps using both 'params' and 'parameters'
            for i, step in enumerate(steps):
                if isinstance(step, dict):
                    if 'params' in step and 'parameters' in step:
                        self.issues['duplicate_params'].append(
                            f"{filepath} step {i}: Has both 'params' and 'parameters'"
                        )

    def check_capability_mapping(self):
        """Check if all capability references are valid"""
        # Known capabilities from AGENT_CAPABILITIES
        valid_capabilities = {
            'can_calculate_dcf', 'can_calculate_roic', 'can_analyze_moat',
            'can_analyze_stock', 'can_calculate_fcf', 'can_analyze_fundamentals',
            'can_analyze_greeks', 'can_calculate_iv_rank', 'can_detect_unusual_activity',
            'can_analyze_options_flow', 'can_fetch_stock_quotes', 'can_fetch_fundamentals',
            'can_fetch_market_data', 'can_fetch_economic_data', 'can_fetch_sentiment',
            'can_fetch_news', 'can_fetch_options_data', 'can_analyze_text',
            'can_synthesize_insights', 'can_orchestrate_agents', 'can_generate_ui'
        }

        for pattern in self.patterns:
            filepath = pattern.get('_filepath', 'unknown')
            steps = pattern.get('steps', pattern.get('workflow', []))

            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    continue

                capability = step.get('params', {}).get('capability')
                if capability and capability not in valid_capabilities:
                    # Check if it's a valid action instead
                    action = step.get('action', '')
                    if action != 'execute_through_registry':
                        continue  # Not a capability call

                    self.issues['unknown_capability'].append(
                        f"{filepath} step {i}: Unknown capability '{capability}'"
                    )

    def check_trigger_coverage(self):
        """Check for duplicate/overlapping triggers"""
        trigger_map = defaultdict(list)

        for pattern in self.patterns:
            pattern_id = pattern.get('id', 'unknown')
            triggers = pattern.get('triggers', [])

            for trigger in triggers:
                if isinstance(trigger, str):
                    trigger_map[trigger.lower()].append(pattern_id)

        # Find duplicates
        for trigger, pattern_ids in trigger_map.items():
            if len(pattern_ids) > 1:
                self.issues['duplicate_triggers'].append(
                    f"'{trigger}' → {', '.join(pattern_ids)}"
                )

        self.stats['unique_triggers'] = len(trigger_map)
        self.stats['total_triggers'] = sum(len(p.get('triggers', [])) for p in self.patterns)

    def find_orphaned_patterns(self):
        """Find patterns that are never referenced"""
        # Patterns that extend others
        extended = set()
        for pattern in self.patterns:
            if 'extends' in pattern:
                extended.add(pattern['extends'])

        # Check system/meta patterns
        meta_patterns = [p for p in self.patterns if 'system/meta' in p.get('_filepath', '')]

        if len(meta_patterns) > 0:
            self.issues['meta_patterns'].append(
                f"Found {len(meta_patterns)} meta patterns (may be for internal use only)"
            )

        self.stats['extended_patterns'] = len(extended)

    def check_completeness(self):
        """Check pattern coverage by category"""
        categories = defaultdict(int)

        for pattern in self.patterns:
            category = pattern.get('category', 'uncategorized')
            categories[category] += 1

        self.stats['categories'] = dict(categories)

        # Check for missing essential categories
        essential = ['analysis', 'queries', 'actions', 'workflows']
        for cat in essential:
            if cat not in categories:
                self.issues['missing_category'].append(f"No patterns in '{cat}' category")

    def analyze(self):
        """Run all analyses"""
        print("Loading patterns...")
        self.load_patterns()

        print(f"Analyzing {len(self.patterns)} patterns...\n")

        self.check_completeness()
        self.check_anti_patterns()
        self.check_capability_mapping()
        self.check_trigger_coverage()
        self.find_orphaned_patterns()

    def print_report(self):
        """Print comprehensive analysis report"""
        print("=" * 80)
        print("PATTERN ANALYSIS REPORT")
        print("=" * 80)

        print(f"\n📊 STATISTICS")
        print("-" * 80)
        print(f"Total patterns: {self.stats['total_patterns']}")
        print(f"Extended patterns: {self.stats['extended_patterns']}")
        print(f"Total triggers: {self.stats['total_triggers']}")
        print(f"Unique triggers: {self.stats['unique_triggers']}")

        print(f"\n📁 CATEGORIES")
        print("-" * 80)
        for cat, count in sorted(self.stats.get('categories', {}).items()):
            print(f"  {cat:20s}: {count:2d} patterns")

        # Issues
        critical_issues = ['legacy_agent_routing', 'unknown_capability', 'load_errors']
        high_issues = ['missing_version', 'wrong_version', 'missing_triggers']
        medium_issues = ['missing_template', 'insufficient_triggers', 'duplicate_params']
        low_issues = ['missing_last_updated', 'duplicate_triggers', 'missing_category']

        has_issues = False

        # Critical
        critical_found = []
        for issue_type in critical_issues:
            if issue_type in self.issues and self.issues[issue_type]:
                critical_found.extend(self.issues[issue_type])

        if critical_found:
            has_issues = True
            print(f"\n🔴 CRITICAL ISSUES ({len(critical_found)})")
            print("-" * 80)
            for issue in critical_found[:20]:
                print(f"  ❌ {issue}")
            if len(critical_found) > 20:
                print(f"  ... and {len(critical_found) - 20} more")

        # High
        high_found = []
        for issue_type in high_issues:
            if issue_type in self.issues and self.issues[issue_type]:
                high_found.extend(self.issues[issue_type])

        if high_found:
            has_issues = True
            print(f"\n🟡 HIGH PRIORITY ({len(high_found)})")
            print("-" * 80)
            for issue in high_found[:20]:
                print(f"  ⚠️  {issue}")
            if len(high_found) > 20:
                print(f"  ... and {len(high_found) - 20} more")

        # Medium
        medium_found = []
        for issue_type in medium_issues:
            if issue_type in self.issues and self.issues[issue_type]:
                medium_found.extend(self.issues[issue_type])

        if medium_found:
            has_issues = True
            print(f"\n🟠 MEDIUM PRIORITY ({len(medium_found)})")
            print("-" * 80)
            for issue in medium_found[:15]:
                print(f"  💡 {issue}")
            if len(medium_found) > 15:
                print(f"  ... and {len(medium_found) - 15} more")

        # Low
        low_found = []
        for issue_type in low_issues:
            if issue_type in self.issues and self.issues[issue_type]:
                low_found.extend(self.issues[issue_type])

        if low_found:
            print(f"\n⚪ LOW PRIORITY ({len(low_found)})")
            print("-" * 80)
            for issue in low_found[:10]:
                print(f"  ℹ️  {issue}")
            if len(low_found) > 10:
                print(f"  ... and {len(low_found) - 10} more")

        if not has_issues:
            print(f"\n✅ NO ISSUES FOUND")
            print("-" * 80)
            print("All patterns are well-structured and complete!")

        print("\n" + "=" * 80)

        # Return counts
        return {
            'critical': len(critical_found),
            'high': len(high_found),
            'medium': len(medium_found),
            'low': len(low_found)
        }

def main():
    analyzer = PatternAnalyzer()
    analyzer.analyze()
    issue_counts = analyzer.print_report()

    # Exit code based on issues
    if issue_counts['critical'] > 0:
        sys.exit(2)
    elif issue_counts['high'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
