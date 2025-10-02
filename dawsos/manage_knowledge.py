#!/usr/bin/env python3
"""
Knowledge Graph Management Utility
Safe operations for updating knowledge without impacting system
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional

class KnowledgeManager:
    """Manages knowledge updates with safety checks"""

    def __init__(self):
        self.knowledge_dir = "knowledge"
        self.backup_dir = "storage/knowledge_backups"
        self.patterns_dir = "patterns"

        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)

    def backup_knowledge(self, label: str = None) -> str:
        """Create timestamped backup of all knowledge"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        label = label or "manual"
        backup_name = f"knowledge_{label}_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)

        # Backup knowledge directory
        shutil.copytree(self.knowledge_dir, backup_path)
        print(f"✅ Knowledge backed up to: {backup_path}")

        return backup_path

    def validate_knowledge_file(self, filepath: str) -> Dict[str, Any]:
        """Validate knowledge file structure"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            return {
                'valid': True,
                'file': filepath,
                'keys': len(data.keys()) if isinstance(data, dict) else 0,
                'size': os.path.getsize(filepath)
            }
        except json.JSONDecodeError as e:
            return {
                'valid': False,
                'file': filepath,
                'error': f"Invalid JSON: {e}"
            }
        except Exception as e:
            return {
                'valid': False,
                'file': filepath,
                'error': str(e)
            }

    def validate_all_knowledge(self) -> Dict[str, Any]:
        """Validate all knowledge files"""
        results = {
            'valid_files': [],
            'invalid_files': [],
            'total_files': 0
        }

        # Check all JSON files in knowledge directory
        for root, dirs, files in os.walk(self.knowledge_dir):
            for file in files:
                if file.endswith('.json'):
                    filepath = os.path.join(root, file)
                    validation = self.validate_knowledge_file(filepath)
                    results['total_files'] += 1

                    if validation['valid']:
                        results['valid_files'].append(filepath)
                    else:
                        results['invalid_files'].append(validation)

        return results

    def safe_update_knowledge(self, filepath: str, updates: Dict[str, Any]) -> bool:
        """Safely update knowledge file with automatic backup"""
        # Validate target file exists
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return False

        # Create backup first
        backup_path = self.backup_knowledge("pre_update")

        try:
            # Load existing data
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Apply updates (merge, don't replace)
            if isinstance(data, dict):
                data.update(updates)
            else:
                print(f"⚠️ File is not a dict, replacing entirely")
                data = updates

            # Validate new structure
            test_validation = json.dumps(data)  # Test if serializable

            # Write updated data
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"✅ Updated: {filepath}")
            return True

        except Exception as e:
            print(f"❌ Update failed: {e}")
            print(f"🔄 Restoring from backup: {backup_path}")
            # Restore from backup
            shutil.rmtree(self.knowledge_dir)
            shutil.copytree(backup_path, self.knowledge_dir)
            return False

    def list_backups(self) -> list:
        """List available knowledge backups"""
        backups = []
        if os.path.exists(self.backup_dir):
            for item in os.listdir(self.backup_dir):
                if item.startswith("knowledge_"):
                    backups.append(item)
        return sorted(backups, reverse=True)

    def restore_backup(self, backup_name: str) -> bool:
        """Restore knowledge from backup"""
        backup_path = os.path.join(self.backup_dir, backup_name)

        if not os.path.exists(backup_path):
            print(f"❌ Backup not found: {backup_name}")
            return False

        try:
            # Create current state backup first
            self.backup_knowledge("pre_restore")

            # Clear current knowledge
            shutil.rmtree(self.knowledge_dir)

            # Restore from backup
            shutil.copytree(backup_path, self.knowledge_dir)

            print(f"✅ Restored from: {backup_name}")
            return True

        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False

    def check_knowledge_health(self) -> Dict[str, Any]:
        """Check overall knowledge health"""
        from core.knowledge_graph import KnowledgeGraph
        from core.graph_governance import GraphGovernance

        graph = KnowledgeGraph()
        governance = GraphGovernance(graph)

        # Run comprehensive check
        health = governance.comprehensive_governance_check()

        # Add validation results
        validation = self.validate_all_knowledge()

        return {
            'graph_health': health,
            'file_validation': validation,
            'recommendation': self._get_health_recommendation(health, validation)
        }

    def _get_health_recommendation(self, health: Dict, validation: Dict) -> str:
        """Generate health recommendation"""
        if validation['invalid_files']:
            return "⚠️ Fix invalid JSON files first"
        elif health.get('overall_health', 0) < 0.5:
            return "⚠️ Run self-improvement to enhance quality"
        elif health.get('quality_issues', []):
            return "🔄 Some nodes need refresh"
        else:
            return "✅ Knowledge is healthy"

    def create_knowledge_snapshot(self) -> str:
        """Create full snapshot including graph state"""
        from core.knowledge_graph import KnowledgeGraph

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = f"storage/graph_snapshots/full_snapshot_{timestamp}.json"

        # Initialize graph
        graph = KnowledgeGraph()

        # Save complete state
        graph.save_graph(snapshot_path)

        print(f"✅ Snapshot created: {snapshot_path}")
        return snapshot_path


def main():
    """Interactive knowledge management CLI"""
    manager = KnowledgeManager()

    print("🧠 DawsOS Knowledge Manager")
    print("=" * 40)

    while True:
        print("\nOptions:")
        print("1. Validate all knowledge files")
        print("2. Backup current knowledge")
        print("3. List available backups")
        print("4. Restore from backup")
        print("5. Check knowledge health")
        print("6. Create full snapshot")
        print("7. Exit")

        choice = input("\nSelect option: ")

        if choice == "1":
            results = manager.validate_all_knowledge()
            print(f"\n✅ Valid files: {len(results['valid_files'])}")
            if results['invalid_files']:
                print(f"❌ Invalid files: {len(results['invalid_files'])}")
                for invalid in results['invalid_files']:
                    print(f"  - {invalid['file']}: {invalid['error']}")

        elif choice == "2":
            label = input("Backup label (optional): ") or None
            manager.backup_knowledge(label)

        elif choice == "3":
            backups = manager.list_backups()
            print(f"\n📦 Available backups ({len(backups)}):")
            for backup in backups[:10]:  # Show recent 10
                print(f"  - {backup}")

        elif choice == "4":
            backups = manager.list_backups()
            if not backups:
                print("No backups available")
                continue
            print("\nRecent backups:")
            for i, backup in enumerate(backups[:5]):
                print(f"{i+1}. {backup}")
            idx = input("Select backup number: ")
            try:
                selected = backups[int(idx)-1]
                manager.restore_backup(selected)
            except:
                print("Invalid selection")

        elif choice == "5":
            print("\n🔍 Checking knowledge health...")
            health = manager.check_knowledge_health()
            print(f"Overall Health: {health['graph_health'].get('overall_health', 0):.0%}")
            print(f"Recommendation: {health['recommendation']}")

        elif choice == "6":
            manager.create_knowledge_snapshot()

        elif choice == "7":
            print("Goodbye! 👋")
            break

        else:
            print("Invalid option")


if __name__ == "__main__":
    main()