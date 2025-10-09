#!/usr/bin/env python3
"""
Automated Pattern Migration Script
Migrates patterns from legacy agent+request format to Trinity 2.0 capability routing
Based on .claude/pattern_migration_specialist.md guidance
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional

# Agent→Capability mapping from AGENT_CAPABILITIES
CAPABILITY_MAPPING = {
    # FinancialAnalyst capabilities
    'financial_analyst': {
        'dcf': 'can_calculate_dcf',
        'discounted cash flow': 'can_calculate_dcf',
        'intrinsic value': 'can_calculate_dcf',
        'roic': 'can_calculate_roic',
        'return on invested capital': 'can_calculate_roic',
        'moat': 'can_analyze_moat',
        'competitive advantage': 'can_analyze_moat',
        'owner earnings': 'can_calculate_owner_earnings',
        'buffett earnings': 'can_calculate_owner_earnings',
        'free cash flow': 'can_calculate_fcf',
        'fcf': 'can_calculate_fcf',
        'economy': 'can_analyze_economy',
        'economic': 'can_analyze_economy',
        'portfolio': 'can_analyze_portfolio_risk',
        'fundamental': 'can_analyze_fundamentals',
        'comprehensive': 'can_analyze_stock',
        'greeks': 'can_analyze_greeks',
        'options greeks': 'can_analyze_greeks',
        'options flow': 'can_analyze_options_flow',
        'unusual': 'can_detect_unusual_activity',
        'iv rank': 'can_calculate_iv_rank',
    },
    # DataHarvester capabilities
    'data_harvester': {
        'stock': 'can_fetch_stock_quotes',
        'quote': 'can_fetch_stock_quotes',
        'economic': 'can_fetch_economic_data',
        'fred': 'can_fetch_economic_data',
        'news': 'can_fetch_news',
        'fundamental': 'can_fetch_fundamentals',
        'financial': 'can_fetch_fundamentals',
        'market movers': 'can_fetch_market_movers',
        'crypto': 'can_fetch_crypto_data',
        'options flow': 'can_fetch_options_flow',
        'unusual options': 'can_fetch_unusual_options',
    },
    # Other agents
    'pattern_spotter': {
        'pattern': 'can_detect_patterns',
        'signal': 'can_identify_signals',
    },
    'forecast_dreamer': {
        'forecast': 'can_generate_forecast',
        'predict': 'can_generate_forecast',
        'project': 'can_project_future',
    },
    'governance_agent': {
        'audit': 'can_audit_data_quality',
        'validate': 'can_validate_policy',
        'compliance': 'can_check_compliance',
    },
    'relationship_hunter': {
        'correlation': 'can_calculate_correlations',
        'relationship': 'can_find_relationships',
    }
}


def infer_capability(agent: str, request: str, description: str = "") -> Optional[str]:
    """
    Infer capability from agent name and request text
    Uses keyword matching against CAPABILITY_MAPPING
    """
    if agent not in CAPABILITY_MAPPING:
        return None

    # Combine request and description for better matching
    text = (request + " " + description).lower()

    # Find matching capability
    for keyword, capability in CAPABILITY_MAPPING[agent].items():
        if keyword in text:
            return capability

    return None


def extract_entity_from_context(context: Dict[str, Any]) -> Optional[str]:
    """Extract entity placeholder from context parameters"""
    for key, value in context.items():
        if isinstance(value, str):
            if '{symbol}' in value.lower() or '{ticker}' in value.lower():
                return 'SYMBOL'
            if '{symbols}' in value.lower() or '{tickers}' in value.lower():
                return 'SYMBOLS'
    return None


def migrate_step(step: Dict[str, Any], pattern_description: str = "") -> Dict[str, Any]:
    """
    Migrate a single pattern step from legacy to capability routing
    """
    # Skip if already using capability routing
    if 'params' in step and 'capability' in step.get('params', {}):
        print(f"    ✓ Step already uses capability routing")
        return step

    # Legacy format check
    if 'params' not in step or 'agent' not in step.get('params', {}):
        print(f"    ⚠️  Step doesn't have agent parameter, skipping")
        return step

    agent = step['params'].get('agent')
    old_context = step['params'].get('context', {})
    request = old_context.get('request', '')

    # Infer capability
    capability = infer_capability(agent, request, step.get('description', '') + " " + pattern_description)

    if not capability:
        print(f"    ⚠️  Could not infer capability for agent '{agent}' with request '{request[:50]}...'")
        return step

    # Build new context (remove 'request', keep other params)
    new_context = {k: v for k, v in old_context.items() if k != 'request'}

    # Extract structured parameters from request
    # Convert {symbol} to {SYMBOL}, {ticker} to {SYMBOL}, etc.
    if 'symbol' in request.lower() or 'ticker' in request.lower():
        if '{symbol}' in request.lower():
            new_context['symbol'] = '{SYMBOL}'
        elif '{ticker}' in request.lower():
            new_context['symbol'] = '{SYMBOL}'

    if 'symbols' in request.lower() or 'tickers' in request.lower():
        if '{symbols}' in request.lower():
            new_context['symbols'] = '{SYMBOLS}'
        elif '{tickers}' in request.lower():
            new_context['symbols'] = '{SYMBOLS}'

    # Also check parameters field if it exists
    if 'parameters' in step:
        for key, value in step['parameters'].items():
            if key not in new_context:
                # Convert lowercase entity refs to uppercase
                if isinstance(value, str):
                    value = value.replace('{symbol}', '{SYMBOL}')
                    value = value.replace('{ticker}', '{SYMBOL}')
                    value = value.replace('{symbols}', '{SYMBOLS}')
                    value = value.replace('{tickers}', '{SYMBOLS}')
                new_context[key] = value

    # Create migrated step
    migrated = {
        'description': step.get('description', ''),
        'action': 'execute_through_registry',
        'params': {
            'capability': capability,
            'context': new_context
        }
    }

    # Preserve save_as if it exists
    if 'save_as' in step:
        migrated['save_as'] = step['save_as']

    # Preserve outputs if it exists
    if 'outputs' in step:
        migrated['outputs'] = step['outputs']

    print(f"    ✓ Migrated: agent '{agent}' → capability '{capability}'")
    return migrated


def migrate_pattern_file(filepath: str, dry_run: bool = False) -> bool:
    """
    Migrate a single pattern file to capability routing
    Returns True if migration was successful
    """
    try:
        with open(filepath, 'r') as f:
            pattern = json.load(f)

        print(f"\n📄 Migrating: {os.path.basename(filepath)}")
        print(f"   ID: {pattern.get('id', 'unknown')}")
        print(f"   Steps: {len(pattern.get('steps', []))}")

        # Check if already migrated
        if any('capability' in step.get('params', {}) for step in pattern.get('steps', [])):
            print(f"   ✓ Already uses capability routing, skipping")
            return True

        # Extract entities for proper capitalization
        entities = []
        for step in pattern.get('steps', []):
            entity = extract_entity_from_context(step.get('params', {}).get('context', {}))
            if entity and entity not in entities:
                entities.append(entity)

        # Migrate each step
        migrated_steps = []
        for i, step in enumerate(pattern.get('steps', [])):
            print(f"   Step {i+1}:")
            migrated_step = migrate_step(step, pattern.get('description', ''))
            migrated_steps.append(migrated_step)

        # Update pattern
        pattern['steps'] = migrated_steps
        pattern['version'] = '2.0'
        pattern['last_updated'] = '2025-10-08'

        # Add entities if found
        if entities and 'entities' not in pattern:
            pattern['entities'] = entities

        # Update description to mention Trinity 2.0
        if 'Trinity 2.0' not in pattern.get('description', ''):
            pattern['description'] = pattern.get('description', '').replace(
                'Trinity architecture',
                'Trinity 2.0 capability routing'
            )
            if 'Trinity' not in pattern.get('description', ''):
                pattern['description'] += ' (Trinity 2.0 capability routing)'

        # Update response template to use uppercase entities
        if 'template' in pattern:
            pattern['template'] = pattern['template'].replace('{symbol}', '{SYMBOL}')
            pattern['template'] = pattern['template'].replace('{ticker}', '{SYMBOL}')
            pattern['template'] = pattern['template'].replace('{symbols}', '{SYMBOLS}')
            pattern['template'] = pattern['template'].replace('{tickers}', '{SYMBOLS}')

        # Write back
        if not dry_run:
            with open(filepath, 'w') as f:
                json.dump(pattern, f, indent=2)
            print(f"   ✅ Migrated successfully")
        else:
            print(f"   ✅ Migration validated (dry run)")

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Main migration script"""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate patterns to Trinity 2.0 capability routing')
    parser.add_argument('--dry-run', action='store_true', help='Validate migration without writing files')
    parser.add_argument('--pattern', type=str, help='Migrate specific pattern file')
    parser.add_argument('--batch', type=str, choices=['analysis', 'query', 'workflow', 'action', 'governance', 'system', 'ui', 'all'],
                       default='all', help='Migrate specific batch of patterns')

    args = parser.parse_args()

    print("=" * 70)
    print("PATTERN MIGRATION TO TRINITY 2.0 CAPABILITY ROUTING")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE MIGRATION'}")
    print(f"Batch: {args.batch}")
    print()

    # Find patterns to migrate
    patterns_dir = 'dawsos/patterns'

    if args.pattern:
        patterns = [args.pattern]
    else:
        # Find all pattern files
        patterns = []
        for root, dirs, files in os.walk(patterns_dir):
            for file in files:
                if file.endswith('.json') and file != 'schema.json':
                    filepath = os.path.join(root, file)

                    # Filter by batch
                    if args.batch != 'all':
                        if args.batch not in filepath:
                            continue

                    patterns.append(filepath)

    print(f"Found {len(patterns)} patterns to migrate\n")

    # Migrate patterns
    success_count = 0
    skip_count = 0
    fail_count = 0

    for pattern in sorted(patterns):
        result = migrate_pattern_file(pattern, dry_run=args.dry_run)
        if result:
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print("\n" + "=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)
    print(f"✅ Successfully migrated: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"📊 Total processed: {success_count + fail_count}")
    print()

    if not args.dry_run and success_count > 0:
        print("✅ Pattern migration complete!")
        print("Next steps:")
        print("  1. Run pattern linter: python scripts/lint_patterns.py")
        print("  2. Test patterns with sample queries")
        print("  3. Commit changes: git add dawsos/patterns/ && git commit")

    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
