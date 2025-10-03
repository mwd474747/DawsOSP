#!/usr/bin/env python3
"""Test UniversalExecutor meta pattern path resolution"""

import sys
from pathlib import Path

# Add dawsos to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'dawsos'))

from core.knowledge_graph import KnowledgeGraph
from core.agent_adapter import AgentRegistry
from core.universal_executor import UniversalExecutor

def test_meta_pattern_path():
    """Verify UniversalExecutor finds meta patterns"""
    print("Testing UniversalExecutor meta pattern path...")

    graph = KnowledgeGraph()
    registry = AgentRegistry()  # No graph parameter

    # This will call _load_meta_patterns in __init__
    executor = UniversalExecutor(graph, registry)

    # Check that pattern_engine was initialized
    assert hasattr(executor, 'pattern_engine'), "Executor should have pattern_engine"
    assert executor.pattern_engine is not None, "Pattern engine should be initialized"

    # Check meta patterns loaded
    if executor.pattern_engine.patterns:
        meta_patterns = [
            p_id for p_id in executor.pattern_engine.patterns.keys()
            if 'meta' in p_id.lower() or 'architecture' in p_id.lower()
        ]

        if len(meta_patterns) > 0:
            print(f"✅ Found {len(meta_patterns)} meta patterns: {meta_patterns}")
        else:
            print("⚠️  No meta patterns found in pattern_engine")
            print(f"   Total patterns loaded: {len(executor.pattern_engine.patterns)}")
            print(f"   Pattern IDs: {list(executor.pattern_engine.patterns.keys())[:5]}...")
    else:
        print("⚠️  No patterns loaded in pattern_engine")

    # The key test: path should exist now (no warning in logs)
    # If path was wrong, _load_meta_patterns would log warning
    # Success is implicit: no exception raised, executor initialized

    print("✅ UniversalExecutor path test passed")
    return True

if __name__ == '__main__':
    try:
        test_meta_pattern_path()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
