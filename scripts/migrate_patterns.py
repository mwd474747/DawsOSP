#!/usr/bin/env python3
"""
Pattern Migration Script - Trinity Compliance

Migrates patterns from direct agent calls to Trinity-compliant registry execution.

Usage:
    python scripts/migrate_patterns.py                    # Migrate all
    python scripts/migrate_patterns.py --dry-run          # Preview changes
    python scripts/migrate_patterns.py --category analysis # Migrate specific category
    python scripts/migrate_patterns.py --verbose          # Detailed output
"""

import json
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime
import argparse


class PatternMigrator:
    """Migrates patterns to Trinity-compliant structure"""

    def __init__(self, pattern_dir: str = 'dawsos/patterns', dry_run: bool = False, verbose: bool = False):
        self.pattern_dir = Path(pattern_dir)
        self.dry_run = dry_run
        self.verbose = verbose
        self.backup_dir = Path('storage/backups/patterns_pre_migration')
        self.changes = []
        self.errors = []
        self.skipped = []

    def migrate_all(self, category: str = None) -> Dict[str, int]:
        """Migrate all patterns or specific category"""
        print(f"\n{'='*60}")
        print(f"Pattern Migration to Trinity Compliance")
        print(f"{'='*60}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE MIGRATION'}")
        print(f"Directory: {self.pattern_dir}")
        if category:
            print(f"Category: {category}")
        print(f"{'='*60}\n")

        # Create backup
        if not self.dry_run:
            self._create_backup()

        # Find patterns
        pattern_files = self._find_patterns(category)
        print(f"Found {len(pattern_files)} patterns to process\n")

        # Migrate each pattern
        stats = {
            'processed': 0,
            'migrated': 0,
            'skipped': 0,
            'errors': 0
        }

        for pattern_file in pattern_files:
            try:
                result = self._migrate_pattern_file(pattern_file)
                stats['processed'] += 1

                if result == 'migrated':
                    stats['migrated'] += 1
                elif result == 'skipped':
                    stats['skipped'] += 1

            except Exception as e:
                stats['errors'] += 1
                self.errors.append(f"{pattern_file}: {e}")
                print(f"  ❌ ERROR: {pattern_file.name} - {e}")

        # Print summary
        self._print_summary(stats)

        return stats

    def _find_patterns(self, category: str = None) -> List[Path]:
        """Find pattern files to migrate"""
        if category:
            # Specific category
            category_dir = self.pattern_dir / category
            if not category_dir.exists():
                print(f"Warning: Category '{category}' not found")
                return []
            pattern_files = list(category_dir.glob('*.json'))
        else:
            # All patterns recursively
            pattern_files = list(self.pattern_dir.rglob('*.json'))

        # Filter out schema files
        pattern_files = [f for f in pattern_files if f.name != 'schema.json']

        return sorted(pattern_files)

    def _create_backup(self):
        """Create backup of patterns before migration"""
        if self.backup_dir.exists():
            # Append timestamp to avoid overwriting
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = Path(f"{self.backup_dir}_{timestamp}")
        else:
            backup_dir = self.backup_dir

        print(f"Creating backup: {backup_dir}")
        shutil.copytree(self.pattern_dir, backup_dir)
        print(f"✓ Backup created\n")

    def _migrate_pattern_file(self, filepath: Path) -> str:
        """Migrate a single pattern file"""
        relative_path = filepath.relative_to(self.pattern_dir)

        try:
            with open(filepath, 'r') as f:
                pattern = json.load(f)

            # Skip if it's a schema
            if '$schema' in pattern:
                return 'skipped'

            # Check if already migrated
            if self._is_already_migrated(pattern):
                if self.verbose:
                    print(f"  ⏭️  SKIP: {relative_path} (already migrated)")
                self.skipped.append(str(relative_path))
                return 'skipped'

            # Migrate pattern
            changes = self._migrate_pattern(pattern, filepath)

            if not changes:
                if self.verbose:
                    print(f"  ⏭️  SKIP: {relative_path} (no changes needed)")
                self.skipped.append(str(relative_path))
                return 'skipped'

            # Save migrated pattern
            if not self.dry_run:
                with open(filepath, 'w') as f:
                    json.dump(pattern, f, indent=2)

            # Report changes
            print(f"  ✅ MIGRATED: {relative_path}")
            if self.verbose:
                for change in changes:
                    print(f"      - {change}")

            self.changes.extend([f"{relative_path}: {c}" for c in changes])

            return 'migrated'

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

    def _is_already_migrated(self, pattern: Dict) -> bool:
        """Check if pattern already migrated"""
        # Has version metadata
        has_version = 'version' in pattern

        # All steps use actions or execute_through_registry
        steps = pattern.get('steps', pattern.get('workflow', []))
        has_direct_agent_calls = any(
            'agent' in step and step.get('action') != 'execute_through_registry'
            for step in steps
            if isinstance(step, dict)
        )

        return has_version and not has_direct_agent_calls

    def _migrate_pattern(self, pattern: Dict, filepath: Path) -> List[str]:
        """Migrate pattern structure"""
        changes = []

        # 1. Add versioning
        if 'version' not in pattern:
            pattern['version'] = '1.0'
            changes.append("Added version: 1.0")

        if 'last_updated' not in pattern:
            pattern['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            changes.append(f"Added last_updated: {pattern['last_updated']}")

        # 2. Normalize workflow → steps
        if 'workflow' in pattern and 'steps' not in pattern:
            pattern['steps'] = pattern.pop('workflow')
            changes.append("Renamed 'workflow' → 'steps'")

        # 3. Migrate steps
        steps = pattern.get('steps', [])
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                continue

            step_changes = self._migrate_step(step, i)
            changes.extend(step_changes)

        return changes

    def _migrate_step(self, step: Dict, index: int) -> List[str]:
        """Migrate a single step"""
        changes = []

        # Convert agent call to registry action
        if 'agent' in step and step.get('action') != 'execute_through_registry':
            agent_name = step.pop('agent')

            # Wrap params in context
            params = step.pop('params', {})

            step['action'] = 'execute_through_registry'
            step['params'] = {
                'agent': agent_name,
                'context': params
            }

            changes.append(f"Step {index}: Converted agent '{agent_name}' → execute_through_registry")

        # Remove deprecated 'method' field
        if 'method' in step:
            method = step.pop('method')
            changes.append(f"Step {index}: Removed 'method' field ('{method}')")

        # Remove 'step' field (just description)
        if 'step' in step:
            step_desc = step.pop('step')
            if self.verbose:
                changes.append(f"Step {index}: Removed 'step' field ('{step_desc}')")

        # Remove 'order' field
        if 'order' in step:
            step.pop('order')
            changes.append(f"Step {index}: Removed 'order' field")

        # Normalize output → save_as
        if 'output' in step and 'save_as' not in step:
            step['save_as'] = step.pop('output')
            changes.append(f"Step {index}: Renamed 'output' → 'save_as'")

        # Normalize parameters → params
        if 'parameters' in step and 'params' not in step:
            step['params'] = step.pop('parameters')
            changes.append(f"Step {index}: Renamed 'parameters' → 'params'")

        return changes

    def _print_summary(self, stats: Dict[str, int]):
        """Print migration summary"""
        print(f"\n{'='*60}")
        print(f"Migration Summary")
        print(f"{'='*60}")
        print(f"Processed:  {stats['processed']}")
        print(f"Migrated:   {stats['migrated']}")
        print(f"Skipped:    {stats['skipped']}")
        print(f"Errors:     {stats['errors']}")
        print(f"{'='*60}")

        if self.dry_run:
            print(f"\n⚠️  DRY RUN MODE - No files were modified")
            print(f"Run without --dry-run to apply changes\n")

        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  - {error}")

        if self.changes and self.verbose:
            print(f"\n✅ CHANGES MADE ({len(self.changes)}):")
            for change in self.changes[:20]:  # Show first 20
                print(f"  - {change}")
            if len(self.changes) > 20:
                print(f"  ... and {len(self.changes) - 20} more")

        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Migrate patterns to Trinity-compliant structure'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )
    parser.add_argument(
        '--category',
        type=str,
        help='Migrate specific category (e.g., analysis, queries, ui)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output'
    )
    parser.add_argument(
        '--pattern-dir',
        type=str,
        default='dawsos/patterns',
        help='Pattern directory (default: dawsos/patterns)'
    )

    args = parser.parse_args()

    # Run migration
    migrator = PatternMigrator(
        pattern_dir=args.pattern_dir,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    stats = migrator.migrate_all(category=args.category)

    # Exit code
    if stats['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
