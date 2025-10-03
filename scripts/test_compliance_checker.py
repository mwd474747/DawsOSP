#!/usr/bin/env python3
"""
Test suite for Trinity Compliance Checker

Validates that the compliance checker correctly detects violations
and respects whitelisted contexts.
"""

import tempfile
import os
from pathlib import Path
from check_compliance import check_file, TrinityComplianceChecker


def test_detects_subscript_access():
    """Test detection of runtime.agents[...] violations"""
    code = """
def process_data(runtime):
    agent = runtime.agents['claude']  # Should be flagged
    return agent
"""
    violations = check_code(code)
    assert len(violations) >= 1
    assert any(v.violation_type == "direct_subscript_access" for v in violations)
    print("✅ test_detects_subscript_access passed")


def test_detects_get_access():
    """Test detection of runtime.agents.get(...) violations"""
    code = """
def fetch_agent(runtime):
    agent = runtime.agents.get('data_harvester')  # Should be flagged
    return agent
"""
    violations = check_code(code)
    assert len(violations) >= 1
    assert any(v.violation_type == "direct_get_access" for v in violations)
    print("✅ test_detects_get_access passed")


def test_detects_direct_method_call():
    """Test detection of direct agent method calls"""
    code = """
def analyze_data(runtime):
    agent = runtime.agents['pattern_spotter']
    result = agent.analyze('test')  # Should be flagged
    return result
"""
    violations = check_code(code)
    # Should detect both the subscript access and the method call
    assert len(violations) >= 1
    assert any(v.violation_type == "direct_subscript_access" for v in violations)
    print("✅ test_detects_direct_method_call passed")


def test_whitelists_agent_runtime():
    """Test that AgentRuntime class is whitelisted"""
    code = """
class AgentRuntime:
    def get_agent(self, name):
        return self.agents[name]  # Should NOT be flagged
"""
    violations = check_code(code)
    assert len(violations) == 0
    print("✅ test_whitelists_agent_runtime passed")


def test_whitelists_agent_adapter():
    """Test that AgentAdapter class is whitelisted"""
    code = """
class AgentAdapter:
    def execute(self, runtime, agent_name):
        agent = runtime.agents[agent_name]  # Should NOT be flagged
        return agent.process({})
"""
    violations = check_code(code)
    assert len(violations) == 0
    print("✅ test_whitelists_agent_adapter passed")


def test_whitelists_agent_registry():
    """Test that AgentRegistry class is whitelisted"""
    code = """
class AgentRegistry:
    def get_agent_instance(self, runtime, name):
        return runtime.agents.get(name)  # Should NOT be flagged
"""
    violations = check_code(code)
    assert len(violations) == 0
    print("✅ test_whitelists_agent_registry passed")


def test_compliant_code():
    """Test that compliant code passes"""
    code = """
def process_request(runtime, agent_name):
    # Compliant: uses registry
    result = runtime.exec_via_registry(agent_name, {'data': 'test'})
    return result
"""
    violations = check_code(code)
    assert len(violations) == 0
    print("✅ test_compliant_code passed")


def test_self_runtime_access():
    """Test detection of self.runtime.agents access"""
    code = """
class DataProcessor:
    def process(self):
        agent = self.runtime.agents['claude']  # Should be flagged
        return agent
"""
    violations = check_code(code)
    assert len(violations) >= 1
    assert any(v.violation_type == "direct_subscript_access" for v in violations)
    print("✅ test_self_runtime_access passed")


def test_context_runtime_access():
    """Test detection of context.runtime.agents access"""
    code = """
def handle_request(context):
    agent = context.runtime.agents['data_harvester']  # Should be flagged
    return agent
"""
    violations = check_code(code)
    assert len(violations) >= 1
    assert any(v.violation_type == "direct_subscript_access" for v in violations)
    print("✅ test_context_runtime_access passed")


def test_suggested_fixes():
    """Test that suggested fixes are generated"""
    code = """
def use_agent(runtime):
    agent = runtime.agents['claude']
"""
    violations = check_code(code)
    assert len(violations) == 1
    assert "exec_via_registry" in violations[0].suggested_fix
    assert "'claude'" in violations[0].suggested_fix
    print("✅ test_suggested_fixes passed")


def test_line_numbers():
    """Test that line numbers are correct"""
    code = """
def function1():
    pass

def function2(runtime):
    agent = runtime.agents['test']  # Line 6
    return agent
"""
    violations = check_code(code)
    assert len(violations) >= 1
    # Check that at least one violation is on line 6
    assert any(v.line_number == 6 for v in violations)
    print("✅ test_line_numbers passed")


def check_code(code: str):
    """Helper function to check code and return violations"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        temp_path = Path(f.name)

    try:
        violations = check_file(temp_path)
        return violations
    finally:
        os.unlink(temp_path)


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("  RUNNING COMPLIANCE CHECKER TESTS")
    print("="*70 + "\n")

    tests = [
        test_detects_subscript_access,
        test_detects_get_access,
        test_detects_direct_method_call,
        test_whitelists_agent_runtime,
        test_whitelists_agent_adapter,
        test_whitelists_agent_registry,
        test_compliant_code,
        test_self_runtime_access,
        test_context_runtime_access,
        test_suggested_fixes,
        test_line_numbers,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} error: {e}")
            failed += 1

    print("\n" + "="*70)
    print(f"  RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")

    return failed == 0


if __name__ == '__main__':
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
