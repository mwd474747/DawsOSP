#!/usr/bin/env python3
"""
Pattern Linter - Validates pattern JSON files for Trinity Architecture compliance

This script checks all patterns for:
- Schema compliance (required fields)
- Valid agent references
- Knowledge dependency validation
- Versioning metadata
- Duplicate pattern IDs
- Orphaned or deprecated references
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any
from datetime import datetime


class PatternLinter:
    """Validates pattern files for compliance and best practices"""

    def __init__(self, pattern_dir: str = 'dawsos/patterns', agent_list: List[str] = None):
        """
        Initialize the pattern linter.

        Args:
            pattern_dir: Directory containing pattern JSON files
            agent_list: List of valid agent names (if None, will skip agent validation)
        """
        self.pattern_dir = Path(pattern_dir)
        self.agent_list = set(agent_list) if agent_list else None
        self.errors = []
        self.warnings = []
        self.patterns_checked = 0

    def lint_all_patterns(self) -> Tuple[List[str], List[str]]:
        """
        Lint all pattern files in the directory.

        Returns:
            Tuple of (errors, warnings)
        """
        if not self.pattern_dir.exists():
            self.errors.append(f"Pattern directory not found: {self.pattern_dir}")
            return self.errors, self.warnings

        pattern_ids = set()

        # Recursively find all JSON files
        for pattern_file in self.pattern_dir.rglob('*.json'):
            # Skip schema files
            if pattern_file.name == 'schema.json':
                continue

            self.lint_pattern_file(pattern_file, pattern_ids)

        return self.errors, self.warnings

    def lint_pattern_file(self, filepath: Path, pattern_ids: Set[str]):
        """Lint a single pattern file"""
        try:
            with open(filepath, 'r') as f:
                pattern = json.load(f)

            # Skip if it's a JSON schema
            if '$schema' in pattern:
                return

            self.patterns_checked += 1
            relative_path = filepath.relative_to(self.pattern_dir)

            # Check required fields
            self._check_required_fields(pattern, relative_path)

            # Check for duplicate IDs
            self._check_duplicate_id(pattern, pattern_ids, relative_path)

            # Check versioning metadata
            self._check_versioning(pattern, relative_path)

            # Check steps/workflow structure
            self._check_steps(pattern, relative_path)

            # Check agent references
            self._check_agent_references(pattern, relative_path)

            # Check for deprecated fields
            self._check_deprecated_fields(pattern, relative_path)

        except json.JSONDecodeError as e:
            self.errors.append(f"{filepath}: Invalid JSON - {e}")
        except Exception as e:
            self.errors.append(f"{filepath}: Error during linting - {e}")

    def _check_required_fields(self, pattern: Dict, filepath: Path):
        """Check for required fields in pattern"""
        required = ['id', 'name', 'description']

        for field in required:
            if field not in pattern:
                self.errors.append(f"{filepath}: Missing required field '{field}'")

        # Check for either 'steps' or 'workflow'
        if 'steps' not in pattern and 'workflow' not in pattern:
            self.errors.append(f"{filepath}: Missing 'steps' or 'workflow' field")

    def _check_duplicate_id(self, pattern: Dict, pattern_ids: Set[str], filepath: Path):
        """Check for duplicate pattern IDs"""
        pattern_id = pattern.get('id')
        if not pattern_id:
            return

        if pattern_id in pattern_ids:
            self.errors.append(f"{filepath}: Duplicate pattern ID '{pattern_id}'")
        else:
            pattern_ids.add(pattern_id)

    def _check_versioning(self, pattern: Dict, filepath: Path):
        """Check for versioning metadata"""
        if 'version' not in pattern:
            self.warnings.append(f"{filepath}: Missing 'version' field")

        if 'last_updated' not in pattern:
            self.warnings.append(f"{filepath}: Missing 'last_updated' field")

        # Validate version format if present
        if 'version' in pattern:
            version = pattern['version']
            if not isinstance(version, (str, int, float)):
                self.errors.append(f"{filepath}: Invalid version format (should be string or number)")

    def _check_steps(self, pattern: Dict, filepath: Path):
        """Check steps/workflow structure"""
        steps = pattern.get('steps', pattern.get('workflow', []))

        if not isinstance(steps, list):
            self.errors.append(f"{filepath}: 'steps'/'workflow' must be a list")
            return

        if len(steps) == 0:
            self.warnings.append(f"{filepath}: Empty steps/workflow")

        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                self.errors.append(f"{filepath}: Step {i} is not a dictionary")
                continue

            # Each step should have either 'agent' or 'action'
            if 'agent' not in step and 'action' not in step:
                self.errors.append(f"{filepath}: Step {i} missing 'agent' or 'action' field")

            # Check for unknown fields (common typos)
            known_fields = {'agent', 'action', 'params', 'parameters', 'outputs', 'output', 'save_as', 'description'}
            unknown_fields = set(step.keys()) - known_fields

            if unknown_fields:
                self.warnings.append(f"{filepath}: Step {i} has unknown fields: {unknown_fields}")

    def _check_agent_references(self, pattern: Dict, filepath: Path):
        """Check that referenced agents exist"""
        if not self.agent_list:
            return  # Skip if no agent list provided

        steps = pattern.get('steps', pattern.get('workflow', []))

        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                continue

            agent_name = step.get('agent')
            if agent_name and agent_name not in self.agent_list:
                self.errors.append(
                    f"{filepath}: Step {i} references unknown agent '{agent_name}'"
                )

            # Check action-based agent references (e.g., "agent:financial_analyst")
            action = step.get('action', '')
            if isinstance(action, str) and action.startswith('agent:'):
                agent_name = action.replace('agent:', '')
                if agent_name not in self.agent_list:
                    self.errors.append(
                        f"{filepath}: Step {i} action references unknown agent '{agent_name}'"
                    )

    def _check_deprecated_fields(self, pattern: Dict, filepath: Path):
        """Check for deprecated or legacy fields"""
        deprecated = {
            'claude_orchestrator': 'Use runtime.execute() instead',
            'orchestrator': 'Use runtime.execute() instead',
            'direct_call': 'All calls should go through registry'
        }

        # Check in main pattern
        for field, message in deprecated.items():
            if field in pattern:
                self.warnings.append(f"{filepath}: Deprecated field '{field}' - {message}")

        # Check in steps
        steps = pattern.get('steps', pattern.get('workflow', []))
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                continue

            for field, message in deprecated.items():
                if field in step:
                    self.warnings.append(
                        f"{filepath}: Step {i} uses deprecated field '{field}' - {message}"
                    )

    def print_report(self):
        """Print linting report"""
        print(f"\n{'='*60}")
        print(f"Pattern Linting Report")
        print(f"{'='*60}")
        print(f"Patterns checked: {self.patterns_checked}")
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"{'='*60}\n")

        if self.errors:
            print(f"ERRORS ({len(self.errors)}):")
            print("-" * 60)
            for error in self.errors:
                print(f"  ❌ {error}")
            print()

        if self.warnings:
            print(f"WARNINGS ({len(self.warnings)}):")
            print("-" * 60)
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
            print()

        if not self.errors and not self.warnings:
            print("✅ All patterns are valid!")

        return len(self.errors) == 0


def get_registered_agents() -> List[str]:
    """Get list of registered agent names from main.py"""
    # This is a simple parser - in production, you'd want to import and inspect the runtime
    agents = [
        'graph_mind',
        'claude',
        'data_harvester',
        'data_digester',
        'relationship_hunter',
        'pattern_spotter',
        'forecast_dreamer',
        'code_monkey',
        'structure_bot',
        'refactor_elf',
        'workflow_recorder',
        'workflow_player',
        'ui_generator',
        'financial_analyst',
        'governance_agent'
    ]
    return agents


def main():
    """Main entry point"""
    print("DawsOS Pattern Linter")
    print("=" * 60)

    # Get registered agents
    agents = get_registered_agents()
    print(f"Checking patterns against {len(agents)} registered agents\n")

    # Run linter
    linter = PatternLinter(agent_list=agents)
    errors, warnings = linter.lint_all_patterns()

    # Print report
    success = linter.print_report()

    # Exit with appropriate code
    if errors:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
