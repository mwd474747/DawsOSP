#!/usr/bin/env python3
"""
Demo script to showcase new backup rotation, checksum validation, and recovery features
"""
import sys
import json
import time
import shutil
import os

# Add dawsos to path
sys.path.insert(0, 'dawsos')

from core.persistence import PersistenceManager
from core.knowledge_graph import KnowledgeGraph

print("=" * 80)
print("DAWSOS BACKUP & RECOVERY FEATURE DEMONSTRATION")
print("=" * 80)

# Clean up any existing test data
if os.path.exists('storage/demo_backup'):
    shutil.rmtree('storage/demo_backup')

# Initialize test persistence manager
persistence = PersistenceManager('storage/demo_backup')
print("\n✅ Initialized PersistenceManager")

print("\n1. SAVE GRAPH WITH BACKUP AND CHECKSUM")
print("-" * 40)

# Create test graph
graph = KnowledgeGraph()
graph.add_node('stock', {'symbol': 'AAPL', 'price': 175.50}, 'AAPL')
graph.add_node('stock', {'symbol': 'GOOGL', 'price': 140.25}, 'GOOGL')
graph.add_node('indicator', {'name': 'GDP', 'value': 27000}, 'GDP')
graph.connect('GDP', 'AAPL', 'influences', 0.7)
graph.connect('GDP', 'GOOGL', 'influences', 0.65)

print("Created graph with:")
print(f"  - {len(graph.nodes)} nodes")
print(f"  - {len(graph.edges)} edges")

# Save with backup
save_result = persistence.save_graph_with_backup(graph)

print(f"\n✅ Graph saved with backup:")
print(f"  - Main: {save_result['graph_path']}")
print(f"  - Backup: {save_result['backup_path']}")
print(f"  - Checksum: {save_result['checksum'][:16]}...")
print(f"  - Nodes: {save_result['metadata']['node_count']}")
print(f"  - Edges: {save_result['metadata']['edge_count']}")

print("\n2. METADATA FILE STRUCTURE")
print("-" * 40)

meta_path = f"{save_result['graph_path']}.meta"
with open(meta_path, 'r') as f:
    metadata = json.load(f)

print("\nMetadata contents:")
print(json.dumps(metadata, indent=2))

print("\n3. INTEGRITY VERIFICATION")
print("-" * 40)

# Verify integrity
integrity = persistence.verify_integrity(save_result['graph_path'])
if integrity['valid']:
    print("✅ Integrity check PASSED")
    print(f"  - Checksum verified: {integrity['checksum'][:16]}...")
else:
    print(f"❌ Integrity check FAILED: {integrity['error']}")

print("\n4. CREATING MULTIPLE BACKUPS")
print("-" * 40)

# Create several backups
for i in range(5):
    # Modify graph slightly
    graph.add_node('test', {'iteration': i}, f'TEST_{i}')
    result = persistence.save_graph_with_backup(graph)
    print(f"  Backup {i+1}: {os.path.basename(result['backup_path'])}")
    time.sleep(0.2)  # Small delay for different timestamps

print("\n5. LIST ALL BACKUPS")
print("-" * 40)

backups = persistence.list_backups()
print(f"\nFound {len(backups)} backups:")

for i, backup in enumerate(backups[:5], 1):
    print(f"\n  {i}. {backup['filename']}")
    print(f"     Size: {backup['size']:,} bytes")
    print(f"     Modified: {backup['modified']}")
    if 'metadata' in backup:
        print(f"     Nodes: {backup['metadata']['node_count']}")
        print(f"     Edges: {backup['metadata']['edge_count']}")

print("\n6. BACKUP ROTATION")
print("-" * 40)

print(f"\nBackups before rotation: {len(backups)}")

# Rotate with 0 days retention (removes all old backups)
removed = persistence._rotate_backups(retention_days=0)

backups_after = persistence.list_backups()
print(f"Backups after rotation: {len(backups_after)}")
print(f"Backups removed: {removed}")

# Create fresh backups for next tests
for i in range(3):
    graph.add_node('fresh', {'value': i}, f'FRESH_{i}')
    persistence.save_graph_with_backup(graph)
    time.sleep(0.1)

print("\n7. RESTORE FROM BACKUP")
print("-" * 40)

# Get most recent backup
backups = persistence.list_backups()
latest_backup = backups[0]['path']

print(f"\nRestoring from: {os.path.basename(latest_backup)}")

# Create new graph and restore
restored_graph = KnowledgeGraph()
restore_stats = persistence.restore_from_backup(latest_backup, restored_graph)

print(f"\n✅ Restore complete:")
print(f"  - Nodes restored: {restore_stats['nodes_restored']}")
print(f"  - Edges restored: {restore_stats['edges_restored']}")

# Verify some data
if 'AAPL' in restored_graph.nodes:
    print(f"  - Verified node 'AAPL': {restored_graph.nodes['AAPL']['data']}")

print("\n8. CORRUPTION DETECTION")
print("-" * 40)

# Create corrupted file for testing
corrupted_path = 'storage/demo_backup/corrupted_test.json'
with open(corrupted_path, 'w') as f:
    f.write('{"corrupted": "data", "invalid": "content"}')

# Copy metadata from good file to make it look legitimate
shutil.copy(f"{save_result['graph_path']}.meta", f"{corrupted_path}.meta")

print("\nCreated corrupted file with valid metadata")

# Try to verify
corrupt_check = persistence.verify_integrity(corrupted_path)

if not corrupt_check['valid']:
    print(f"\n✅ Corruption DETECTED: {corrupt_check['error']}")
    if 'expected' in corrupt_check and 'actual' in corrupt_check:
        print(f"  - Expected checksum: {corrupt_check['expected'][:16]}...")
        print(f"  - Actual checksum:   {corrupt_check['actual'][:16]}...")
else:
    print("\n❌ Failed to detect corruption")

print("\n9. AUTOMATIC RECOVERY")
print("-" * 40)

# Corrupt the main graph file
main_graph_path = 'storage/demo_backup/graph.json'
print("\nCorrupting main graph file...")

with open(main_graph_path, 'w') as f:
    f.write('{"corrupted": true}')

# Try to load with automatic recovery
recovery_graph = KnowledgeGraph()
recovery_result = persistence.load_graph_with_recovery(recovery_graph)

if recovery_result['success']:
    if recovery_result['source'] == 'backup_recovery':
        print(f"\n✅ AUTOMATIC RECOVERY SUCCESS!")
        print(f"  - Source: Backup recovery")
        print(f"  - Backup used: {recovery_result['backup_used']}")
        print(f"  - Nodes recovered: {recovery_result['recovery_stats']['nodes_restored']}")
        print(f"  - Edges recovered: {recovery_result['recovery_stats']['edges_restored']}")
    else:
        print(f"\n✅ Loaded from primary (no recovery needed)")
else:
    print(f"\n❌ Recovery failed: {recovery_result.get('error', 'Unknown error')}")

print("\n10. BACKUP DIRECTORY STRUCTURE")
print("-" * 40)

print("\nFinal directory structure:")
print("\nstorage/demo_backup/")
print("├── graph.json              # Primary graph")
print("├── graph.json.meta         # Primary metadata (checksum, counts)")
print("└── backups/")

backups = persistence.list_backups()
for backup in backups[:5]:
    filename = backup['filename']
    print(f"    ├── {filename}")
    print(f"    └── {filename}.meta")

print("\n" + "=" * 80)
print("FEATURE SUMMARY")
print("=" * 80)

print("""
✅ save_graph_with_backup() - Automatic timestamped backups
✅ _rotate_backups() - Remove backups older than retention period
✅ list_backups() - List all backups with metadata
✅ restore_from_backup() - Restore graph from specific backup
✅ _calculate_checksum() - SHA-256 checksum validation
✅ _save_with_metadata() - Save metadata alongside data files
✅ verify_integrity() - Verify file against checksum
✅ load_graph_with_recovery() - Auto-recovery from corruption
✅ _recover_from_backup() - Automatic fallback to valid backup

Production Features:
- SHA-256 checksum validation on all saves
- Automatic backup rotation (30-day default retention)
- Metadata files with timestamp, checksum, node/edge counts
- Automatic corruption detection and recovery
- Detailed logging of all operations
- Recovery statistics (nodes/edges restored)

Metadata Format:
{
  "timestamp": "2025-10-02T23:30:00",
  "checksum": "abc123...",
  "node_count": 150,
  "edge_count": 320,
  "graph_version": "1.0",
  "saved_by": "DawsOS PersistenceManager"
}

See dawsos/docs/DISASTER_RECOVERY.md for complete recovery procedures.
""")

print("\n📊 Storage Statistics:")
total_size = 0
for file in os.listdir('storage/demo_backup'):
    filepath = os.path.join('storage/demo_backup', file)
    if os.path.isfile(filepath):
        total_size += os.path.getsize(filepath)

backup_count = len(persistence.list_backups())
print(f"  - Total backups: {backup_count}")
print(f"  - Storage used: {total_size / 1024:.2f} KB")

print("\n✨ Demo complete!")
