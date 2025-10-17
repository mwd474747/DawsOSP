#!/usr/bin/env python3
"""
Codebase Refactoring Opportunities Analysis
Finds: legacy code, dead code, duplicates, simplification opportunities
"""

import ast
import os
import re
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Set

class RefactoringAnalyzer:
    def __init__(self, base_dir='dawsos'):
        self.base_dir = Path(base_dir)
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)

    def analyze_all(self):
        """Run all analysis checks"""
        print("Analyzing codebase for refactoring opportunities...\n")

        self.find_unused_imports()
        self.find_commented_code()
        self.find_duplicate_functions()
        self.find_legacy_patterns()
        self.find_dead_code()
        self.find_complexity_issues()
        self.find_unused_files()

    def find_unused_imports(self):
        """Find potentially unused imports"""
        for py_file in self.base_dir.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue

            try:
                with open(py_file, 'r') as f:
                    content = f.read()

                # Find imports
                imports = re.findall(r'^import (\w+)', content, re.MULTILINE)
                from_imports = re.findall(r'^from [\w.]+ import ([\w, ]+)', content, re.MULTILINE)

                # Check if used (simple heuristic)
                for imp in imports:
                    if content.count(imp) == 1:  # Only appears in import line
                        self.issues['unused_imports'].append(f"{py_file}: {imp}")

            except Exception:
                pass

    def find_commented_code(self):
        """Find large blocks of commented-out code"""
        for py_file in self.base_dir.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue

            try:
                with open(py_file, 'r') as f:
                    lines = f.readlines()

                comment_block = []
                for i, line in enumerate(lines):
                    if line.strip().startswith('#') and not line.strip().startswith('##'):
                        # Check if it looks like code
                        if any(x in line for x in ['def ', 'class ', 'import ', 'return ', '=']):
                            comment_block.append(i + 1)
                    else:
                        if len(comment_block) >= 5:  # 5+ lines of commented code
                            self.issues['commented_code'].append(
                                f"{py_file}: lines {comment_block[0]}-{comment_block[-1]} ({len(comment_block)} lines)"
                            )
                        comment_block = []

            except Exception:
                pass

    def find_duplicate_functions(self):
        """Find functions with similar names (potential duplicates)"""
        functions = defaultdict(list)

        for py_file in self.base_dir.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue

            try:
                with open(py_file, 'r') as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        functions[node.name].append(str(py_file))

            except Exception:
                pass

        # Find duplicates
        for func_name, files in functions.items():
            if len(files) > 1:
                self.issues['duplicate_function_names'].append(f"{func_name}: {len(files)} files")

    def find_legacy_patterns(self):
        """Find legacy code patterns"""
        legacy_patterns = [
            (r'\.has_key\(', 'has_key (use "in" instead)'),
            (r'execfile\(', 'execfile (use exec(open().read()))'),
            (r'string\.', 'string module (use str methods)'),
            (r'types\.(StringType|IntType)', 'types module (use isinstance)'),
            (r'\.iteritems\(\)', '.iteritems() (use .items())'),
            (r'\.iterkeys\(\)', '.iterkeys() (use .keys())'),
            (r'\.itervalues\(\)', '.itervalues() (use .values())'),
        ]

        for py_file in self.base_dir.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue

            try:
                with open(py_file, 'r') as f:
                    content = f.read()

                for pattern, name in legacy_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        self.issues['legacy_patterns'].append(f"{py_file}: {name}")

            except Exception:
                pass

    def find_dead_code(self):
        """Find potentially unused functions/classes"""
        # Find all definitions
        definitions = {}
        for py_file in self.base_dir.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue

            try:
                with open(py_file, 'r') as f:
                    tree = ast.parse(f.read(), filename=str(py_file))

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        if not node.name.startswith('_'):  # Skip private
                            definitions[node.name] = str(py_file)

            except Exception:
                pass

        # Check usage
        all_content = ""
        for py_file in self.base_dir.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            try:
                with open(py_file, 'r') as f:
                    all_content += f.read() + "\n"
            except Exception:
                pass

        for name, file in definitions.items():
            if all_content.count(name) == 1:  # Only appears in definition
                self.issues['potentially_unused'].append(f"{file}: {name}")

    def find_complexity_issues(self):
        """Find overly complex functions"""
        for py_file in self.base_dir.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue

            try:
                with open(py_file, 'r') as f:
                    lines = f.readlines()
                    tree = ast.parse(''.join(lines), filename=str(py_file))

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Count lines
                        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                            func_lines = node.end_lineno - node.lineno
                            if func_lines > 100:
                                self.issues['long_functions'].append(
                                    f"{py_file}:{node.lineno} {node.name}() - {func_lines} lines"
                                )

                        # Count complexity (nested ifs, loops)
                        complexity = sum(1 for _ in ast.walk(node) if isinstance(_, (ast.If, ast.For, ast.While)))
                        if complexity > 15:
                            self.issues['high_complexity'].append(
                                f"{py_file}:{node.lineno} {node.name}() - complexity {complexity}"
                            )

            except Exception:
                pass

    def find_unused_files(self):
        """Find Python files that might be unused"""
        # Check for files not imported anywhere
        all_imports = set()
        for py_file in self.base_dir.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue

            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    # Extract module names from imports
                    imports = re.findall(r'from [\w.]*([\w]+) import', content)
                    imports += re.findall(r'import [\w.]*([\w]+)', content)
                    all_imports.update(imports)
            except Exception:
                pass

        # Check each file
        for py_file in self.base_dir.rglob('*.py'):
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue

            # Skip main files
            if py_file.name in ['__init__.py', 'main.py', 'setup.py']:
                continue

            # Check if module name appears in imports
            module_name = py_file.stem
            if module_name not in all_imports:
                self.issues['potentially_unused_files'].append(str(py_file))

    def print_report(self):
        """Print comprehensive refactoring report"""
        print("=" * 80)
        print("REFACTORING OPPORTUNITIES REPORT")
        print("=" * 80)
        print()

        categories = [
            ('legacy_patterns', 'LEGACY CODE PATTERNS', 'critical'),
            ('commented_code', 'COMMENTED CODE BLOCKS', 'high'),
            ('long_functions', 'LONG FUNCTIONS (>100 lines)', 'high'),
            ('high_complexity', 'HIGH COMPLEXITY FUNCTIONS', 'high'),
            ('duplicate_function_names', 'DUPLICATE FUNCTION NAMES', 'medium'),
            ('potentially_unused', 'POTENTIALLY UNUSED FUNCTIONS', 'medium'),
            ('potentially_unused_files', 'POTENTIALLY UNUSED FILES', 'medium'),
            ('unused_imports', 'UNUSED IMPORTS', 'low'),
        ]

        for key, title, priority in categories:
            items = self.issues.get(key, [])
            if items:
                emoji = {'critical': '🔴', 'high': '🟡', 'medium': '🟠', 'low': '⚪'}[priority]
                print(f"{emoji} {title} ({len(items)} found)")
                print("-" * 80)
                for item in items[:10]:
                    print(f"  • {item}")
                if len(items) > 10:
                    print(f"  ... and {len(items) - 10} more")
                print()

        # Summary
        total_issues = sum(len(v) for v in self.issues.values())
        print("=" * 80)
        print(f"TOTAL OPPORTUNITIES: {total_issues}")
        print("=" * 80)

def main():
    analyzer = RefactoringAnalyzer()
    analyzer.analyze_all()
    analyzer.print_report()

if __name__ == '__main__':
    main()
