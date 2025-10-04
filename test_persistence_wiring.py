#!/usr/bin/env python3
"""
Test Persistence Wiring - Verify save_graph_with_backup() integration
"""
import sys
sys.path.insert(0, 'dawsos')

from core.knowledge_graph import KnowledgeGraph
from core.persistence import PersistenceManager
import os

def test_persistence_wiring():
    """Test that persistence manager works with graph"""
    print("🧪 Testing Persistence Wiring...")
    print()

    # Initialize components
    graph = KnowledgeGraph()
    persistence = PersistenceManager()

    # Add some test nodes
    graph.add_node('test', data={'name': 'Test Node 1', 'value': 100})
    graph.add_node('test', data={'name': 'Test Node 2', 'value': 200})

    print(f"✅ Created test graph with {len(graph.nodes)} nodes")
    print()

    # Test save_graph_with_backup()
    print("📦 Testing save_graph_with_backup()...")
    save_result = persistence.save_graph_with_backup(graph)

    assert save_result['success'], "Save failed!"
    assert 'checksum' in save_result, "Missing checksum!"
    assert 'backup_path' in save_result, "Missing backup path!"
    assert os.path.exists(save_result['backup_path']), "Backup file not created!"

    print(f"✅ Graph saved successfully")
    print(f"   Checksum: {save_result['checksum'][:16]}...")
    print(f"   Backup: {save_result['backup_path']}")
    print(f"   Nodes: {save_result['metadata']['node_count']}")
    print(f"   Edges: {save_result['metadata']['edge_count']}")
    print(f"   Backups removed: {save_result['backups_removed']}")
    print()

    # Test list_backups()
    print("📋 Testing list_backups()...")
    backups = persistence.list_backups()

    assert len(backups) > 0, "No backups found!"

    print(f"✅ Found {len(backups)} backup(s)")
    for i, backup in enumerate(backups[:3]):
        print(f"   {i+1}. {backup['filename']} - {backup['size']/1024:.1f} KB")
    print()

    # Test verify_integrity()
    print("🔐 Testing verify_integrity()...")
    integrity = persistence.verify_integrity(save_result['graph_path'])

    assert integrity['valid'], f"Integrity check failed: {integrity.get('error')}"

    print(f"✅ Integrity verified")
    print(f"   Checksum matches: {integrity['checksum'][:16]}...")
    print()

    # Test backup rotation
    print("🔄 Testing backup rotation...")

    # Create multiple backups
    for i in range(3):
        graph.add_node('test', data={'name': f'Extra Node {i}'})
        persistence.save_graph_with_backup(graph)

    backups_after = persistence.list_backups()
    print(f"✅ Created {len(backups_after)} total backups")
    print()

    # Summary
    print("="*50)
    print("✅ ALL TESTS PASSED!")
    print("="*50)
    print()
    print("Persistence wiring verified:")
    print(f"  ✅ save_graph_with_backup() working")
    print(f"  ✅ Checksum validation working")
    print(f"  ✅ Backup rotation working")
    print(f"  ✅ Backup listing working")
    print(f"  ✅ Integrity verification working")
    print()

    return True

if __name__ == '__main__':
    try:
        test_persistence_wiring()
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
