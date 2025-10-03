#!/usr/bin/env python3
"""
Test Validation Script
Validates test structure and counts tests without running them
"""

import sys
import ast
from pathlib import Path
from collections import defaultdict

def count_tests_in_file(file_path):
    """Count test methods in a Python test file"""
    try:
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        test_count = 0
        class_count = 0
        test_classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Count test classes (those starting with Test)
                if node.name.startswith('Test'):
                    class_count += 1
                    test_classes.append(node.name)

                    # Count test methods in this class
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if item.name.startswith('test_'):
                                test_count += 1

        return {
            'test_count': test_count,
            'class_count': class_count,
            'test_classes': test_classes,
            'file_path': file_path
        }
    except Exception as e:
        return {
            'error': str(e),
            'file_path': file_path
        }

def main():
    """Main validation function"""
    test_dir = Path('dawsos/tests')

    print("=" * 80)
    print("DawsOS Test Suite Validation")
    print("=" * 80)
    print()

    # Find all test files
    test_files = {
        'regression': list((test_dir / 'regression').glob('test_*.py')),
        'integration': list((test_dir / 'integration').glob('test_*.py')),
        'unit': list((test_dir / 'unit').glob('test_*.py')),
        'validation': list((test_dir / 'validation').glob('test_*.py')),
    }

    total_tests = 0
    total_classes = 0
    results = defaultdict(list)

    for category, files in test_files.items():
        if not files:
            continue

        print(f"\n{category.upper()} TESTS")
        print("-" * 80)

        for file_path in sorted(files):
            info = count_tests_in_file(file_path)

            if 'error' in info:
                print(f"❌ {file_path.name}: ERROR - {info['error']}")
                continue

            test_count = info['test_count']
            class_count = info['class_count']

            total_tests += test_count
            total_classes += class_count
            results[category].append(info)

            print(f"✓ {file_path.name}")
            print(f"  Tests: {test_count}, Classes: {class_count}")
            if info['test_classes']:
                print(f"  Test Classes: {', '.join(info['test_classes'][:3])}", end='')
                if len(info['test_classes']) > 3:
                    print(f" ... ({len(info['test_classes'])} total)")
                else:
                    print()

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for category, infos in results.items():
        category_tests = sum(info['test_count'] for info in infos)
        category_classes = sum(info['class_count'] for info in infos)
        print(f"{category.upper()}: {len(infos)} files, {category_tests} tests, {category_classes} classes")

    print()
    print(f"TOTAL: {total_tests} tests across {total_classes} test classes")
    print()

    # Check for specific regression test files
    print("=" * 80)
    print("REGRESSION TEST COVERAGE")
    print("=" * 80)

    required_files = [
        'test_agent_compliance.py',
        'test_pattern_execution.py',
        'test_knowledge_system.py'
    ]

    regression_dir = test_dir / 'regression'
    for filename in required_files:
        file_path = regression_dir / filename
        if file_path.exists():
            info = count_tests_in_file(file_path)
            print(f"✓ {filename}: {info['test_count']} tests")
        else:
            print(f"❌ {filename}: NOT FOUND")

    # Check for integration test
    print()
    print("=" * 80)
    print("INTEGRATION TEST COVERAGE")
    print("=" * 80)

    integration_file = test_dir / 'integration' / 'test_trinity_flow.py'
    if integration_file.exists():
        info = count_tests_in_file(integration_file)
        print(f"✓ test_trinity_flow.py: {info['test_count']} tests")
    else:
        print("❌ test_trinity_flow.py: NOT FOUND")

    print()
    print("=" * 80)
    print("Validation Complete!")
    print("=" * 80)

    return 0 if total_tests > 0 else 1

if __name__ == '__main__':
    sys.exit(main())
