#!/usr/bin/env python3
"""
Codebase Consistency Tests
Validates technical debt has been properly addressed and prevents regression

Tests ensure:
1. No deprecated Streamlit APIs
2. No legacy agent references in runtime code
3. Documentation consistency (15 agents, not 19)
4. No dead code calling removed agents
"""

import subprocess
import pytest
import json
from pathlib import Path

# Base directory for all tests
BASE_DIR = Path(__file__).parent.parent.parent


def test_no_deprecated_streamlit_apis():
    """Ensure no use_container_width in active codebase (excluding backups)"""
    result = subprocess.run(
        ['grep', '-r', 'use_container_width', 'dawsos', '--include=*.py'],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    # Filter out backup directories and venv
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        non_backup_lines = [l for l in lines if 'backup' not in l.lower()
                           and '/venv/' not in l
                           and 'test_codebase_consistency' not in l]

        assert len(non_backup_lines) == 0, \
            f"Found deprecated Streamlit API in active code:\n" + "\n".join(non_backup_lines)


def test_no_legacy_agent_calls_in_runtime():
    """Ensure no calls to removed agents (equity_agent, macro_agent, risk_agent, pattern_agent)"""
    legacy_agents = ['equity_agent', 'macro_agent', 'risk_agent', 'pattern_agent']

    for agent in legacy_agents:
        result = subprocess.run(
            ['grep', '-r', '-w', agent, 'dawsos/core', '--include=*.py'],
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )

        # Filter for actual calls (not comments or archived code)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            # Exclude comments, archive references, and the test file itself
            code_lines = []
            for l in lines:
                if 'test_codebase_consistency' in l:
                    continue  # Skip the test file itself
                if ':' in l and '#' in l.split(':',1)[1]:
                    continue  # Skip comment lines
                if 'archive' in l.lower() or 'legacy' in l.lower():
                    continue  # Skip archive/legacy mentions
                code_lines.append(l)

            assert len(code_lines) == 0, \
                f"Found legacy agent call '{agent}' in runtime code:\n" + "\n".join(code_lines)


def test_agent_prompts_only_contains_active_agents():
    """Verify agent_prompts.json only references 15 active agents"""
    prompts_file = BASE_DIR / 'dawsos' / 'prompts' / 'agent_prompts.json'

    with open(prompts_file, 'r') as f:
        data = json.load(f)

    # Check that legacy agents are NOT in the file (except in migration docs)
    legacy_agents = ['equity_agent', 'macro_agent', 'risk_agent', 'pattern_agent']
    for agent in legacy_agents:
        # OK if in migration docs, not OK if they have prompts
        if agent in data and agent not in ['_comment', '_reason', '_migration', '_active_agents']:
            assert False, f"Found legacy agent '{agent}' with prompt in agent_prompts.json"

    # Check that active agents count is documented
    if '_active_agents' in data:
        assert len(data['_active_agents']) == 15, \
            f"Expected 15 active agents, found {len(data['_active_agents'])}"


def test_documentation_agent_count_consistency():
    """Check that non-archive docs don't claim 19 agents without consolidation context"""
    result = subprocess.run(
        ['grep', '-r', '-w', '19 agent', '.', '--include=*.md'],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')

        # Filter out acceptable instances
        bad_lines = []
        for line in lines:
            # Skip if in docs/archive directory (moved from root)
            if '/docs/archive/' in line or '/archive/' in line or '/archived/' in line:
                continue
            # Skip if it has consolidation context
            if 'from 19' in line or 'consolidated' in line:
                continue
            # Skip if it's in analysis docs describing the problem
            if any(doc in line for doc in ['ROOT_CAUSE_ANALYSIS', 'CONSOLIDATION_ACTUAL',
                                           'OUTSTANDING_INCONSISTENCIES', 'AGENT_CONSOLIDATION_EVALUATION',
                                           'CONSOLIDATION_VALIDATION_COMPLETE']):
                continue

            bad_lines.append(line)

        assert len(bad_lines) == 0, \
            f"Found '19 agents' without consolidation context:\n" + "\n".join(bad_lines)


def test_no_imports_from_archived_agents():
    """Ensure no imports from archived legacy agents (archive/ directory deleted)"""
    legacy_imports = [
        'from agents.equity_agent',
        'from agents.macro_agent',
        'from agents.risk_agent',
        'from agents.pattern_agent',
        'import equity_agent',
        'import macro_agent',
        'import risk_agent',
        'import pattern_agent'
    ]

    for import_stmt in legacy_imports:
        result = subprocess.run(
            ['grep', '-r', import_stmt, 'dawsos', '--include=*.py'],
            capture_output=True,
            text=True,
            cwd=BASE_DIR
        )

        # Filter out backup references and the test file itself (archive/ deleted)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            active_lines = [l for l in lines if 'backup' not in l.lower()
                           and 'test_codebase_consistency' not in l]

            assert len(active_lines) == 0, \
                f"Found import from archived agent:\n" + "\n".join(active_lines)


def test_active_agents_match_registry():
    """Verify the 15 active agents are properly registered"""
    expected_agents = [
        'graph_mind', 'claude', 'data_harvester', 'data_digester',
        'relationship_hunter', 'pattern_spotter', 'forecast_dreamer',
        'code_monkey', 'structure_bot', 'refactor_elf',
        'workflow_recorder', 'workflow_player', 'ui_generator',
        'financial_analyst', 'governance_agent'
    ]

    prompts_file = BASE_DIR / 'dawsos' / 'prompts' / 'agent_prompts.json'

    with open(prompts_file, 'r') as f:
        data = json.load(f)

    if '_active_agents' in data:
        active_agents = set(data['_active_agents'])
        expected_set = set(expected_agents)

        assert active_agents == expected_set, \
            f"Agent mismatch:\nExpected: {expected_set}\nActual: {active_agents}\n" \
            f"Missing: {expected_set - active_agents}\nExtra: {active_agents - expected_set}"


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v'])
