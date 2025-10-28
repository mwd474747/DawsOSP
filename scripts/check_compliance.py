#!/usr/bin/env python3
"""
Trinity Architecture Compliance Checker

AST-based static analysis tool that detects violations of Trinity Architecture principles:
- Direct agent access via runtime.agents[...]
- Direct agent access via runtime.agents.get(...)
- Direct method calls that bypass the registry

Usage:
    python3 scripts/check_compliance.py [--strict] [--exclude PATTERN] [--format {text,json}]
"""

import ast
import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass, asdict


@dataclass
class Violation:
    """Represents a Trinity compliance violation"""
    file_path: str
    line_number: int
    column: int
    violation_type: str
    code_snippet: str
    suggested_fix: str
    severity: str = "error"


class TrinityComplianceChecker(ast.NodeVisitor):
    """AST visitor that detects Trinity compliance violations"""

    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: List[Violation] = []
        self.current_class: Optional[str] = None

        # Track variable assignments to detect indirect access patterns
        self.agent_variables: Set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef):
        """Track current class context for whitelisting"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Subscript(self, node: ast.Subscript):
        """Detect runtime.agents[...] subscript access"""
        # Check if this is runtime.agents[...]
        if self._is_runtime_agents_subscript(node):
            # Check if we're in a whitelisted class
            if not self._is_whitelisted_context():
                violation = self._create_violation(
                    node,
                    "direct_subscript_access",
                    "Direct agent access via subscript",
                    self._suggest_registry_fix(node)
                )
                self.violations.append(violation)

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Detect runtime.agents.get(...) calls"""
        # Check if this is runtime.agents.get(...)
        if self._is_runtime_agents_get_call(node):
            if not self._is_whitelisted_context():
                violation = self._create_violation(
                    node,
                    "direct_get_access",
                    "Direct agent access via .get() method",
                    self._suggest_registry_fix(node)
                )
                self.violations.append(violation)

        # Check for direct agent method calls
        # Look for patterns like: agent.process(...), agent.think(...), agent.analyze(...)
        if self._is_direct_agent_method_call(node):
            if not self._is_whitelisted_context():
                violation = self._create_violation(
                    node,
                    "direct_method_call",
                    "Direct agent method call (bypasses registry)",
                    "Use runtime.exec_via_registry(agent_name, context) instead"
                )
                self.violations.append(violation)

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        """Track variable assignments that might be agents"""
        # Look for patterns like: agent = runtime.agents[...]
        if isinstance(node.value, ast.Subscript):
            if self._is_runtime_agents_subscript(node.value):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.agent_variables.add(target.id)

        # Look for: agent = runtime.agents.get(...)
        if isinstance(node.value, ast.Call):
            if self._is_runtime_agents_get_call(node.value):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.agent_variables.add(target.id)

        self.generic_visit(node)

    def _is_runtime_agents_subscript(self, node: ast.Subscript) -> bool:
        """Check if node is runtime.agents[...]"""
        if not isinstance(node.value, ast.Attribute):
            return False

        # Check for .agents attribute
        if node.value.attr != 'agents':
            return False

        # Check if the object is named 'runtime' (or self.runtime, etc.)
        return self._is_runtime_reference(node.value.value)

    def _is_runtime_agents_get_call(self, node: ast.Call) -> bool:
        """Check if node is runtime.agents.get(...)"""
        if not isinstance(node.func, ast.Attribute):
            return False

        # Check for .get() method
        if node.func.attr != 'get':
            return False

        # Check if called on .agents attribute
        if not isinstance(node.func.value, ast.Attribute):
            return False

        if node.func.value.attr != 'agents':
            return False

        # Check if the object is 'runtime'
        return self._is_runtime_reference(node.func.value.value)

    def _is_runtime_reference(self, node: ast.AST) -> bool:
        """Check if node refers to runtime (runtime, self.runtime, etc.)"""
        if isinstance(node, ast.Name):
            return node.id == 'runtime'
        elif isinstance(node, ast.Attribute):
            # Handle self.runtime, context.runtime, etc.
            return node.attr == 'runtime'
        return False

    def _is_direct_agent_method_call(self, node: ast.Call) -> bool:
        """
        Check if this is a direct agent method call like agent.process(...)
        Only flag if 'agent' was obtained from runtime.agents[...]
        """
        if not isinstance(node.func, ast.Attribute):
            return False

        # Check if method is a known agent method
        agent_methods = {'process', 'think', 'analyze', 'interpret', 'harvest', 'execute'}
        if node.func.attr not in agent_methods:
            return False

        # Check if called on a variable we tracked as an agent
        if isinstance(node.func.value, ast.Name):
            return node.func.value.id in self.agent_variables

        return False

    def _is_whitelisted_context(self) -> bool:
        """Check if current context is whitelisted (allowed to access agents directly)"""
        if not self.current_class:
            return False

        # Whitelist: classes that are allowed to access agents directly
        whitelisted_classes = {
            'AgentRuntime',
            'AgentAdapter',
            'AgentRegistry',
            'TestAgentRuntime',  # Test classes
            'TestTrinityCompliance',
        }

        return self.current_class in whitelisted_classes

    def _create_violation(
        self,
        node: ast.AST,
        violation_type: str,
        description: str,
        suggested_fix: str
    ) -> Violation:
        """Create a Violation object from an AST node"""
        # Get the source code snippet
        line_idx = node.lineno - 1
        if 0 <= line_idx < len(self.source_lines):
            code_snippet = self.source_lines[line_idx].strip()
        else:
            code_snippet = "<source not available>"

        return Violation(
            file_path=self.file_path,
            line_number=node.lineno,
            column=node.col_offset,
            violation_type=violation_type,
            code_snippet=code_snippet,
            suggested_fix=suggested_fix,
            severity="error"
        )

    def _suggest_registry_fix(self, node: ast.AST) -> str:
        """Generate a suggested fix for registry-based execution"""
        # Try to extract agent name if it's a string literal
        agent_name = "agent_name"

        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
            agent_name = f"'{node.slice.value}'"
        elif isinstance(node, ast.Call) and len(node.args) > 0:
            if isinstance(node.args[0], ast.Constant):
                agent_name = f"'{node.args[0].value}'"

        return f"runtime.exec_via_registry({agent_name}, context)"


class ComplianceReport:
    """Generate compliance reports in various formats"""

    def __init__(self, violations: List[Violation], files_checked: int):
        self.violations = violations
        self.files_checked = files_checked

    def to_text(self) -> str:
        """Generate human-readable text report"""
        if not self.violations:
            return (
                f"\n{'='*70}\n"
                f"  TRINITY COMPLIANCE CHECK PASSED\n"
                f"{'='*70}\n\n"
                f"Files checked: {self.files_checked}\n"
                f"Violations found: 0\n\n"
                f"All code is Trinity Architecture compliant!\n"
            )

        lines = [
            f"\n{'='*70}",
            f"  TRINITY COMPLIANCE VIOLATIONS FOUND",
            f"{'='*70}\n"
        ]

        # Group violations by file
        violations_by_file: Dict[str, List[Violation]] = {}
        for v in self.violations:
            if v.file_path not in violations_by_file:
                violations_by_file[v.file_path] = []
            violations_by_file[v.file_path].append(v)

        # Print violations grouped by file
        for file_path, file_violations in sorted(violations_by_file.items()):
            lines.append(f"\n{file_path}:")
            for v in sorted(file_violations, key=lambda x: x.line_number):
                lines.append(f"  Line {v.line_number}:{v.column}")
                lines.append(f"    Type: {v.violation_type}")
                lines.append(f"    Code: {v.code_snippet}")
                lines.append(f"    Fix:  {v.suggested_fix}")
                lines.append("")

        # Summary
        lines.extend([
            f"\n{'='*70}",
            f"SUMMARY",
            f"{'='*70}",
            f"Files checked: {self.files_checked}",
            f"Total violations: {len(self.violations)}",
            f"{'='*70}\n"
        ])

        return "\n".join(lines)

    def to_json(self) -> str:
        """Generate JSON report"""
        report = {
            "files_checked": self.files_checked,
            "total_violations": len(self.violations),
            "violations": [asdict(v) for v in self.violations]
        }
        return json.dumps(report, indent=2)

    def to_github_annotations(self) -> str:
        """Generate GitHub Actions annotations"""
        lines = []
        for v in self.violations:
            # GitHub annotation format:
            # ::error file={name},line={line},col={col}::{message}
            lines.append(
                f"::error file={v.file_path},line={v.line_number},"
                f"col={v.column}::{v.violation_type}: {v.code_snippet}. "
                f"Fix: {v.suggested_fix}"
            )
        return "\n".join(lines)


def should_skip_file(file_path: Path, exclude_patterns: List[str]) -> bool:
    """Check if file should be skipped based on exclusion patterns"""
    file_str = str(file_path)

    # Always skip these
    default_excludes = [
        'venv/',
        '__pycache__/',
        '.git/',
        'archived_legacy/',
        'storage/backups/',
        'backups/',
        'tests/',  # Test files are allowed to access agents directly
    ]

    for pattern in default_excludes + exclude_patterns:
        if pattern in file_str:
            return True

    return False


def check_file(file_path: Path) -> List[Violation]:
    """Check a single Python file for compliance violations"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
            source_lines = source.splitlines()

        # Parse the AST
        tree = ast.parse(source, filename=str(file_path))

        # Run the checker
        checker = TrinityComplianceChecker(str(file_path), source_lines)
        checker.visit(tree)

        return checker.violations

    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error checking {file_path}: {e}", file=sys.stderr)
        return []


def find_python_files(root_dir: Path) -> List[Path]:
    """Find all Python files in the directory tree"""
    python_files = []
    for path in root_dir.rglob('*.py'):
        if path.is_file():
            python_files.append(path)
    return python_files


def main():
    parser = argparse.ArgumentParser(
        description='Check Trinity Architecture compliance in Python code'
    )
    parser.add_argument(
        '--root',
        type=str,
        default='dawsos',
        help='Root directory to scan (default: dawsos)'
    )
    parser.add_argument(
        '--exclude',
        type=str,
        action='append',
        default=[],
        help='Additional patterns to exclude (can be specified multiple times)'
    )
    parser.add_argument(
        '--format',
        choices=['text', 'json', 'github'],
        default='text',
        help='Output format (default: text)'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Exit with error code if violations found'
    )

    args = parser.parse_args()

    # Determine root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    scan_root = project_root / args.root

    if not scan_root.exists():
        print(f"Error: Directory '{scan_root}' does not exist", file=sys.stderr)
        sys.exit(1)

    # Find all Python files
    all_files = find_python_files(scan_root)

    # Filter out excluded files
    files_to_check = []
    for f in all_files:
        try:
            rel_path = f.relative_to(project_root)
            if not should_skip_file(rel_path, args.exclude):
                files_to_check.append(f)
        except ValueError:
            # File is outside project root, skip exclusion check
            if not should_skip_file(f, args.exclude):
                files_to_check.append(f)

    # Check each file
    all_violations = []
    for file_path in files_to_check:
        violations = check_file(file_path)
        all_violations.extend(violations)

    # Generate report
    report = ComplianceReport(all_violations, len(files_to_check))

    if args.format == 'json':
        print(report.to_json())
    elif args.format == 'github':
        print(report.to_github_annotations())
    else:
        print(report.to_text())

    # Exit code
    if args.strict and all_violations:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
