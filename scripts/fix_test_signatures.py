#!/usr/bin/env python3
"""
Fix test signatures for Phase 6.2 (Option A)

Automatically converts test files to use correct Trinity 2.0 signatures:
1. execute_pattern(pattern: Dict, context: Dict) - pattern must be dict not string
2. add_node(node_type: str, data: dict) - separate node_type from data

Run: python3 scripts/fix_test_signatures.py
"""

import re
import sys
from pathlib import Path

def fix_execute_pattern_calls(content: str) -> tuple[str, int]:
    """
    Fix execute_pattern calls to use correct signature.

    Before: engine.execute_pattern('pattern_id', context)
    After:  pattern = engine.get_pattern('pattern_id')
            engine.execute_pattern(pattern, context)
    """
    fixes = 0

    # Pattern for old-style calls
    pattern = r"(\s+)(\w+)\.execute_pattern\(['\"](\w+)['\"]\s*,\s*([^)]+)\)"

    def replace_call(match):
        nonlocal fixes
        fixes += 1
        indent = match.group(1)
        engine = match.group(2)
        pattern_id = match.group(3)
        context = match.group(4)

        return (
            f"{indent}pattern = {engine}.get_pattern('{pattern_id}')\n"
            f"{indent}if pattern:\n"
            f"{indent}    result = {engine}.execute_pattern(pattern, {context})"
        )

    content = re.sub(pattern, replace_call, content)
    return content, fixes

def fix_add_node_calls(content: str) -> tuple[str, int]:
    """
    Fix add_node calls to use correct signature.

    Before: graph.add_node('test', {...})
    After:  graph.add_node(node_type='test', data={...})

    Before: graph.add_node('test_id', 'test', {...})
    After:  graph.add_node(node_type='test', data={...}, node_id='test_id')
    """
    fixes = 0

    # Pattern 1: add_node('type', {...}) - most common case
    pattern1 = r"\.add_node\(['\"](\w+)['\"]\s*,\s*(\{[^}]*\})\)"

    def replace_positional(match):
        nonlocal fixes
        fixes += 1
        node_type = match.group(1)
        data = match.group(2)
        return f".add_node(node_type='{node_type}', data={data})"

    content = re.sub(pattern1, replace_positional, content)

    # Pattern 2: add_node('node_id', 'type', {...})
    pattern2 = r"\.add_node\(['\"](\w+)['\"]\s*,\s*['\"](\w+)['\"]\s*,\s*(\{[^}]*\})\)"

    def replace_with_id(match):
        nonlocal fixes
        fixes += 1
        node_id = match.group(1)
        node_type = match.group(2)
        data = match.group(3)
        return f".add_node(node_type='{node_type}', data={data}, node_id='{node_id}')"

    content = re.sub(pattern2, replace_with_id, content)

    return content, fixes

def process_file(filepath: Path) -> dict:
    """Process a single test file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        original = content
        execute_fixes = 0
        add_node_fixes = 0

        # Fix execute_pattern calls
        content, execute_fixes = fix_execute_pattern_calls(content)

        # Fix add_node calls
        content, add_node_fixes = fix_add_node_calls(content)

        total_fixes = execute_fixes + add_node_fixes

        if total_fixes > 0:
            # Backup original
            backup = filepath.with_suffix(filepath.suffix + '.bak')
            with open(backup, 'w') as f:
                f.write(original)

            # Write fixed version
            with open(filepath, 'w') as f:
                f.write(content)

            return {
                'status': 'fixed',
                'execute_pattern': execute_fixes,
                'add_node': add_node_fixes,
                'total': total_fixes
            }
        else:
            return {'status': 'ok', 'total': 0}

    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def main():
    """Process all test files."""
    tests_dir = Path('dawsos/tests')

    if not tests_dir.exists():
        print(f"❌ Tests directory not found: {tests_dir}")
        return 1

    # Find all test files
    test_files = list(tests_dir.rglob('*.py'))

    print(f"🔍 Found {len(test_files)} test files\n")

    results = {
        'fixed': [],
        'ok': [],
        'error': []
    }

    total_fixes = 0

    for filepath in sorted(test_files):
        rel_path = filepath.relative_to('dawsos')
        result = process_file(filepath)

        status = result['status']
        results[status].append((rel_path, result))

        if status == 'fixed':
            fixes = result['total']
            total_fixes += fixes
            print(f"✅ {rel_path}: {fixes} fixes")
            if result['execute_pattern'] > 0:
                print(f"   - execute_pattern: {result['execute_pattern']}")
            if result['add_node'] > 0:
                print(f"   - add_node: {result['add_node']}")
        elif status == 'error':
            print(f"❌ {rel_path}: {result['error']}")

    print(f"\n{'='*60}")
    print(f"📊 Summary:")
    print(f"   Fixed: {len(results['fixed'])} files ({total_fixes} total fixes)")
    print(f"   Already OK: {len(results['ok'])} files")
    print(f"   Errors: {len(results['error'])} files")

    if results['error']:
        print(f"\n⚠️  Files with errors:")
        for path, result in results['error']:
            print(f"   - {path}: {result['error']}")
        return 1

    print(f"\n✨ Phase 6.2 signature conversion complete!")
    print(f"   Backups saved with .bak extension")

    return 0

if __name__ == '__main__':
    sys.exit(main())
