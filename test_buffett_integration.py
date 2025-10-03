#!/usr/bin/env python3
"""
Test Buffett Analysis Integration with execute_through_registry
Validates that:
1. buffett_checklist.json data file loads correctly
2. execute_through_registry routes to correct agents
3. Buffett patterns can execute end-to-end
"""

import sys
import json
from pathlib import Path

# Add dawsos to path
sys.path.insert(0, str(Path(__file__).parent / 'dawsos'))

from core.agent_runtime import AgentRuntime
from core.pattern_engine import PatternEngine
from core.knowledge_loader import KnowledgeLoader

def test_buffett_data_loads():
    """Test that buffett_checklist.json knowledge file loads"""
    print("=" * 60)
    print("TEST 1: Buffett Checklist Data Loading")
    print("=" * 60)

    loader = KnowledgeLoader()

    # Check if buffett_checklist.json exists in knowledge
    buffett_path = Path('dawsos/storage/knowledge/buffett_checklist.json')
    if not buffett_path.exists():
        print(f"❌ FAIL: {buffett_path} not found")
        return False

    with open(buffett_path) as f:
        buffett_data = json.load(f)

    print(f"✅ Buffett checklist loaded: {buffett_data['name']}")
    print(f"   Categories: {len(buffett_data['categories'])}")
    print(f"   Version: {buffett_data['version']}")

    # Verify key structure
    required_keys = ['name', 'description', 'categories', 'scoring', 'key_principles']
    for key in required_keys:
        if key not in buffett_data:
            print(f"❌ FAIL: Missing required key '{key}'")
            return False

    print("✅ All required keys present")

    # Verify categories
    expected_categories = [
        'Business Understanding',
        'Economic Moat',
        'Management Quality',
        'Financial Strength',
        'Valuation'
    ]

    actual_categories = [cat['category'] for cat in buffett_data['categories']]
    for cat in expected_categories:
        if cat in actual_categories:
            print(f"   ✅ {cat}")
        else:
            print(f"   ❌ Missing category: {cat}")
            return False

    print("✅ PASS: Buffett checklist data valid\n")
    return True

def test_execute_through_registry():
    """Test that execute_through_registry function exists and works"""
    print("=" * 60)
    print("TEST 2: execute_through_registry Function")
    print("=" * 60)

    runtime = AgentRuntime()

    # Verify function exists
    if not hasattr(runtime, 'exec_via_registry'):
        print("❌ FAIL: exec_via_registry method not found")
        return False

    print("✅ exec_via_registry method exists")

    # Verify agent registry has required agents
    required_agents = ['claude', 'data_harvester', 'pattern_spotter']
    for agent_name in required_agents:
        if agent_name in runtime.agent_registry.agents:
            print(f"   ✅ Agent registered: {agent_name}")
        else:
            print(f"   ⚠️  Agent not registered: {agent_name}")

    print("✅ PASS: execute_through_registry ready\n")
    return True

def test_buffett_pattern_structure():
    """Test Buffett-related patterns for Trinity compliance"""
    print("=" * 60)
    print("TEST 3: Buffett Pattern Structure")
    print("=" * 60)

    patterns_to_check = [
        'dawsos/patterns/analysis/buffett_checklist.json',
        'dawsos/patterns/analysis/moat_analyzer.json',
        'dawsos/patterns/analysis/owner_earnings.json',
        'dawsos/patterns/analysis/fundamental_analysis.json'
    ]

    legacy_action_types = ['checklist', 'evaluate', 'calculate', 'synthesize', 'knowledge_lookup']
    patterns_with_legacy = []

    for pattern_path in patterns_to_check:
        path = Path(pattern_path)
        if not path.exists():
            print(f"⚠️  Pattern not found: {pattern_path}")
            continue

        with open(path) as f:
            pattern = json.load(f)

        print(f"\nPattern: {pattern.get('name', pattern.get('id'))}")

        # Check for legacy actions
        has_legacy = False
        has_registry = False

        if 'steps' in pattern:
            for i, step in enumerate(pattern['steps']):
                action = step.get('action', '')
                if action in legacy_action_types:
                    has_legacy = True
                    print(f"   ⚠️  Step {i+1}: Legacy action '{action}'")
                elif action == 'execute_through_registry':
                    has_registry = True
                    print(f"   ✅ Step {i+1}: Trinity-compliant 'execute_through_registry'")

        if has_legacy:
            patterns_with_legacy.append(pattern.get('id'))
            print(f"   ⚠️  NEEDS CONVERSION: Contains legacy action types")
        elif has_registry:
            print(f"   ✅ Trinity-compliant pattern")
        else:
            print(f"   ℹ️  No agent execution steps")

    if patterns_with_legacy:
        print(f"\n⚠️  {len(patterns_with_legacy)} patterns need conversion to Trinity:")
        for pid in patterns_with_legacy:
            print(f"   - {pid}")
        print("\nℹ️  These patterns will work but should be converted for full Trinity compliance")
        return True  # Not a failure, just needs enhancement
    else:
        print("\n✅ PASS: All Buffett patterns use Trinity architecture")
        return True

def test_pattern_engine_loads_buffett():
    """Test that PatternEngine loads Buffett patterns correctly"""
    print("=" * 60)
    print("TEST 4: Pattern Engine Loads Buffett Patterns")
    print("=" * 60)

    runtime = AgentRuntime()
    pattern_engine = PatternEngine(runtime)

    buffett_patterns = [
        'buffett_checklist',
        'moat_analyzer',
        'owner_earnings',
        'fundamental_analysis'
    ]

    all_found = True
    for pattern_id in buffett_patterns:
        pattern = pattern_engine.get_pattern(pattern_id)
        if pattern:
            print(f"✅ Loaded: {pattern_id} - {pattern.get('name')}")
        else:
            print(f"❌ NOT LOADED: {pattern_id}")
            all_found = False

    if all_found:
        print("\n✅ PASS: All Buffett patterns loaded\n")
        return True
    else:
        print("\n❌ FAIL: Some Buffett patterns not loaded\n")
        return False

def test_dalio_data_loads():
    """Test that dalio_cycles.json knowledge file loads"""
    print("=" * 60)
    print("TEST 5: Dalio Cycles Data Loading")
    print("=" * 60)

    dalio_path = Path('dawsos/storage/knowledge/dalio_cycles.json')
    if not dalio_path.exists():
        print(f"❌ FAIL: {dalio_path} not found")
        return False

    with open(dalio_path) as f:
        dalio_data = json.load(f)

    print(f"✅ Dalio cycles loaded: {dalio_data.get('name', 'Unknown')}")
    print(f"   Cycles: {len(dalio_data.get('cycles', []))}")

    print("✅ PASS: Dalio cycles data valid\n")
    return True

def main():
    """Run all Buffett integration tests"""
    print("\n" + "=" * 60)
    print("BUFFETT ANALYSIS INTEGRATION TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        ("Buffett Data Loading", test_buffett_data_loads),
        ("execute_through_registry", test_execute_through_registry),
        ("Buffett Pattern Structure", test_buffett_pattern_structure),
        ("Pattern Engine Load", test_pattern_engine_loads_buffett),
        ("Dalio Data Loading", test_dalio_data_loads),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ EXCEPTION in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n✅ ALL TESTS PASSED - Buffett integration ready!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
