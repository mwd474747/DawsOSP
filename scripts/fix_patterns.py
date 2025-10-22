#!/usr/bin/env python3
"""
Trinity 3.0 Pattern Compliance Fixer
Automatically fixes common compliance issues in patterns
"""

import json
import re
from pathlib import Path
from typing import Dict, List

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


def remove_emojis(text: str) -> str:
    """Remove all emojis from text"""
    return EMOJI_PATTERN.sub('', text).strip()


def fix_pattern(pattern_path: Path, dry_run: bool = False) -> Dict:
    """Fix a single pattern for Trinity 3.0 compliance"""

    with open(pattern_path, 'r') as f:
        pattern = json.load(f)

    changes = []
    modified = False

    # 1. Remove emojis from template
    if 'template' in pattern:
        original = pattern['template']
        cleaned = remove_emojis(original)
        if cleaned != original:
            pattern['template'] = cleaned
            emoji_count = len(EMOJI_PATTERN.findall(original))
            changes.append(f"Removed {emoji_count} emojis from template")
            modified = True

    # 2. Update version to 3.0
    if pattern.get('version') in ['1.0', '2.0', None]:
        old_version = pattern.get('version', 'None')
        pattern['version'] = '3.0'
        pattern['last_updated'] = '2025-10-21'
        changes.append(f"Updated version: {old_version} → 3.0")
        modified = True

    # 3. Fix deprecated load_knowledge action
    steps = pattern.get('steps', [])
    for i, step in enumerate(steps):
        if step.get('action') == 'load_knowledge':
            step['action'] = 'enriched_lookup'
            # Move dataset_name to params if needed
            if 'dataset_name' in step and 'params' not in step:
                step['params'] = {'dataset_name': step.pop('dataset_name')}
            changes.append(f"Step {i+1}: Fixed deprecated 'load_knowledge' → 'enriched_lookup'")
            modified = True

    # 4. Write back if modified
    if modified and not dry_run:
        with open(pattern_path, 'w') as f:
            json.dump(pattern, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Add trailing newline

    return {
        'pattern': pattern_path.name,
        'modified': modified,
        'changes': changes
    }


def fix_all_patterns(dry_run: bool = False) -> List[Dict]:
    """Fix all patterns in patterns/ directory"""

    patterns_dir = Path('patterns')
    pattern_files = list(patterns_dir.glob('**/*.json'))

    results = []
    for pattern_file in sorted(pattern_files):
        result = fix_pattern(pattern_file, dry_run=dry_run)
        if result['modified'] or result['changes']:
            results.append(result)

    return results


def print_fix_report(results: List[Dict], dry_run: bool = False):
    """Print formatted fix report"""

    mode = "DRY RUN" if dry_run else "APPLIED"

    print("=" * 80)
    print(f"TRINITY 3.0 PATTERN COMPLIANCE FIXER - {mode}")
    print("=" * 80)
    print()

    if not results:
        print("✅ No patterns need fixing - all compliant!")
        return

    print(f"FIXED {len(results)} PATTERNS")
    print("-" * 80)

    for result in results:
        print(f"\n{'🔧' if not dry_run else '🔍'} {result['pattern']}")
        for change in result['changes']:
            print(f"   ✓ {change}")

    print("\n" + "=" * 80)

    if dry_run:
        print("\n⚠️  This was a DRY RUN - no files were modified")
        print("Run with --apply to make actual changes")
    else:
        print(f"\n✅ Successfully fixed {len(results)} patterns")


if __name__ == '__main__':
    import sys

    dry_run = '--apply' not in sys.argv

    results = fix_all_patterns(dry_run=dry_run)
    print_fix_report(results, dry_run=dry_run)

    if dry_run and results:
        print("\nTo apply these fixes, run: python3 scripts/fix_patterns.py --apply")
