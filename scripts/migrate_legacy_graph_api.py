#!/usr/bin/env python3
"""
Automated migration script to replace legacy graph.nodes/graph.edges usage
with NetworkX native API calls.

This script handles the common migration patterns identified in the specialist guide.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


class GraphAPIMigrator:
    """Migrates legacy graph API usage to NetworkX native API"""

    def __init__(self):
        self.changes_made = []
        self.files_modified = []

    def migrate_file(self, filepath: Path) -> Tuple[bool, List[str]]:
        """
        Migrate a single file.

        Returns:
            (modified: bool, changes: List[str])
        """
        try:
            with open(filepath, 'r') as f:
                content = f.read()

            original_content = content
            file_changes = []

            # Pattern 1: graph.nodes.items() -> graph._graph.nodes(data=True)
            pattern1 = r'(\w+)\.nodes\.items\(\)'
            replacement1 = r'\1._graph.nodes(data=True)'
            if re.search(pattern1, content):
                content = re.sub(pattern1, replacement1, content)
                count = len(re.findall(pattern1, original_content))
                file_changes.append(f"  - Migrated {count} .nodes.items() calls")

            # Pattern 2: graph.nodes[id] -> graph.get_node(id) OR graph._graph.nodes[id]
            # This is context-dependent, so we use a conservative approach
            # We can't automate this perfectly without AST analysis

            # Pattern 3: if id in graph.nodes -> if graph._graph.has_node(id)
            pattern3 = r'if\s+(\w+)\s+in\s+(\w+)\.nodes:'
            replacement3 = r'if \2._graph.has_node(\1):'
            if re.search(pattern3, content):
                content = re.sub(pattern3, replacement3, content)
                count = len(re.findall(pattern3, original_content))
                file_changes.append(f"  - Migrated {count} 'in nodes' checks")

            # Pattern 3b: elif/while variants
            pattern3b = r'(elif|while)\s+(\w+)\s+in\s+(\w+)\.nodes:'
            replacement3b = r'\1 \3._graph.has_node(\2):'
            if re.search(pattern3b, content):
                content = re.sub(pattern3b, replacement3b, content)
                count = len(re.findall(pattern3b, original_content))
                file_changes.append(f"  - Migrated {count} 'elif/while in nodes' checks")

            # Pattern 4: for edge in graph.edges: -> for u, v, attrs in graph._graph.edges(data=True):
            pattern4 = r'for\s+(\w+)\s+in\s+(\w+)\.edges:'
            replacement4 = r'for u, v, attrs in \2._graph.edges(data=True):'
            if re.search(pattern4, content):
                content = re.sub(pattern4, replacement4, content)
                count = len(re.findall(pattern4, original_content))
                file_changes.append(f"  - Migrated {count} 'for edge in edges' loops")

            # Pattern 5: len(graph.nodes) -> graph._graph.number_of_nodes()
            pattern5 = r'len\((\w+)\.nodes\)'
            replacement5 = r'\1._graph.number_of_nodes()'
            if re.search(pattern5, content):
                content = re.sub(pattern5, replacement5, content)
                count = len(re.findall(pattern5, original_content))
                file_changes.append(f"  - Migrated {count} len(nodes) calls")

            # Pattern 6: len(graph.edges) -> graph._graph.number_of_edges()
            pattern6 = r'len\((\w+)\.edges\)'
            replacement6 = r'\1._graph.number_of_edges()'
            if re.search(pattern6, content):
                content = re.sub(pattern6, replacement6, content)
                count = len(re.findall(pattern6, original_content))
                file_changes.append(f"  - Migrated {count} len(edges) calls")

            # Pattern 7: graph.nodes.keys() -> graph._graph.nodes()
            pattern7 = r'(\w+)\.nodes\.keys\(\)'
            replacement7 = r'list(\1._graph.nodes())'
            if re.search(pattern7, content):
                content = re.sub(pattern7, replacement7, content)
                count = len(re.findall(pattern7, original_content))
                file_changes.append(f"  - Migrated {count} .nodes.keys() calls")

            # Pattern 8: graph.nodes.values() -> (attrs for _, attrs in graph._graph.nodes(data=True))
            # This one is complex, skip for now - needs manual migration

            # Write back if modified
            if content != original_content:
                with open(filepath, 'w') as f:
                    f.write(content)
                return True, file_changes

            return False, []

        except Exception as e:
            print(f"Error migrating {filepath}: {e}")
            return False, []

    def migrate_directory(self, directory: Path, recursive: bool = True) -> dict:
        """Migrate all Python files in a directory"""
        results = {
            'files_scanned': 0,
            'files_modified': 0,
            'total_changes': 0,
            'details': []
        }

        pattern = '**/*.py' if recursive else '*.py'

        for filepath in directory.glob(pattern):
            if '__pycache__' in str(filepath):
                continue

            results['files_scanned'] += 1
            modified, changes = self.migrate_file(filepath)

            if modified:
                results['files_modified'] += 1
                results['total_changes'] += len(changes)
                results['details'].append({
                    'file': str(filepath),
                    'changes': changes
                })

        return results


def main():
    """Main migration execution"""
    print("=" * 70)
    print("AUTOMATED LEGACY GRAPH API MIGRATION")
    print("=" * 70)
    print()

    migrator = GraphAPIMigrator()

    # Get base directory
    base_dir = Path(__file__).parent.parent / 'dawsos'

    if not base_dir.exists():
        print(f"Error: {base_dir} not found")
        return 1

    # Migrate in priority order
    priorities = [
        ('agents', base_dir / 'agents'),
        ('capabilities', base_dir / 'capabilities'),
        ('ui', base_dir / 'ui'),
        ('core (remaining)', base_dir / 'core'),
        ('tests', base_dir / 'tests'),
    ]

    total_files_modified = 0
    total_changes = 0

    for name, directory in priorities:
        if not directory.exists():
            continue

        print(f"Migrating: {name}")
        print("-" * 70)

        results = migrator.migrate_directory(directory, recursive=True)

        print(f"  Files scanned: {results['files_scanned']}")
        print(f"  Files modified: {results['files_modified']}")
        print(f"  Total changes: {results['total_changes']}")

        if results['details']:
            for detail in results['details']:
                print(f"    {detail['file']}")
                for change in detail['changes']:
                    print(f"      {change}")

        print()

        total_files_modified += results['files_modified']
        total_changes += results['total_changes']

    print("=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)
    print(f"Total files modified: {total_files_modified}")
    print(f"Total changes applied: {total_changes}")
    print()
    print("Next steps:")
    print("1. Review changes with: git diff")
    print("2. Test compilation: python3 -m py_compile dawsos/**/*.py")
    print("3. Run tests: pytest dawsos/tests/")
    print("4. If all passes, remove legacy @property methods from knowledge_graph.py")

    return 0


if __name__ == '__main__':
    sys.exit(main())
