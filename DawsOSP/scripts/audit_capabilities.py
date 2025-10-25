#!/usr/bin/env python3
"""
Capability Audit Script

Creates comprehensive mapping of:
1. All capabilities referenced in pattern files
2. All capabilities declared by agents
3. Gap analysis (missing capabilities)
4. Service method availability check

Output: Markdown report showing what's implemented vs what's needed
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict


def extract_capabilities_from_patterns() -> Dict[str, List[str]]:
    """
    Extract all capabilities referenced in pattern JSON files.

    Returns:
        Dict mapping pattern_id -> list of capabilities
    """
    patterns_dir = Path(__file__).parent.parent / "backend" / "patterns"
    pattern_capabilities = {}

    for pattern_file in patterns_dir.glob("*.json"):
        try:
            with open(pattern_file) as f:
                pattern = json.load(f)

            pattern_id = pattern.get("id") or pattern.get("pattern_id", pattern_file.stem)
            capabilities = []

            # Extract from steps
            for step in pattern.get("steps", []):
                if "capability" in step:
                    capabilities.append(step["capability"])

            pattern_capabilities[pattern_id] = capabilities
        except Exception as e:
            print(f"Warning: Failed to parse {pattern_file}: {e}")

    return pattern_capabilities


def extract_capabilities_from_agents() -> Dict[str, List[str]]:
    """
    Extract all capabilities declared by agents via get_capabilities().

    Returns:
        Dict mapping agent_name -> list of capabilities
    """
    agents_dir = Path(__file__).parent.parent / "backend" / "app" / "agents"
    agent_capabilities = {}

    for agent_file in agents_dir.glob("*.py"):
        if agent_file.name == "base_agent.py":
            continue

        try:
            with open(agent_file) as f:
                content = f.read()

            # Extract agent class name
            class_match = re.search(r'class (\w+)\(BaseAgent\):', content)
            if not class_match:
                continue
            agent_name = class_match.group(1)

            # Extract capabilities from get_capabilities() return statement
            capabilities_match = re.search(
                r'def get_capabilities\(self\).*?return \[(.*?)\]',
                content,
                re.DOTALL
            )

            if capabilities_match:
                caps_text = capabilities_match.group(1)
                # Extract quoted strings
                capabilities = re.findall(r'["\']([^"\']+)["\']', caps_text)
                agent_capabilities[agent_name] = capabilities
            else:
                agent_capabilities[agent_name] = []

        except Exception as e:
            print(f"Warning: Failed to parse {agent_file}: {e}")

    return agent_capabilities


def check_service_methods() -> Dict[str, List[str]]:
    """
    Check which service files exist and what methods they expose.

    Returns:
        Dict mapping service_name -> list of async methods
    """
    services_dir = Path(__file__).parent.parent / "backend" / "app" / "services"
    service_methods = {}

    for service_file in services_dir.glob("*.py"):
        if service_file.name.startswith("__"):
            continue

        try:
            with open(service_file) as f:
                content = f.read()

            service_name = service_file.stem

            # Extract async method names
            methods = re.findall(r'async def (\w+)\(', content)
            service_methods[service_name] = methods

        except Exception as e:
            print(f"Warning: Failed to parse {service_file}: {e}")

    return service_methods


def generate_audit_report():
    """Generate comprehensive capability audit report."""

    print("# DawsOSP Capability Audit Report")
    print()
    print(f"**Generated**: {Path(__file__).parent}")
    print()
    print("---")
    print()

    # Extract data
    pattern_capabilities = extract_capabilities_from_patterns()
    agent_capabilities = extract_capabilities_from_agents()
    service_methods = check_service_methods()

    # Calculate totals
    all_pattern_caps = set()
    for caps in pattern_capabilities.values():
        all_pattern_caps.update(caps)

    all_agent_caps = set()
    for caps in agent_capabilities.values():
        all_agent_caps.update(caps)

    implemented_caps = all_agent_caps
    missing_caps = all_pattern_caps - all_agent_caps

    # Summary
    print("## Executive Summary")
    print()
    print(f"- **Patterns analyzed**: {len(pattern_capabilities)}")
    print(f"- **Agents analyzed**: {len(agent_capabilities)}")
    print(f"- **Services analyzed**: {len(service_methods)}")
    print(f"- **Total unique capabilities in patterns**: {len(all_pattern_caps)}")
    print(f"- **Total unique capabilities implemented**: {len(implemented_caps)}")
    print(f"- **Missing capabilities**: {len(missing_caps)}")
    print(f"- **Coverage**: {len(implemented_caps) / max(len(all_pattern_caps), 1) * 100:.1f}%")
    print()
    print("---")
    print()

    # Pattern-by-Pattern Analysis
    print("## Pattern Coverage Analysis")
    print()
    print("| Pattern ID | Total Caps | Implemented | Missing | Status |")
    print("|------------|------------|-------------|---------|--------|")

    for pattern_id, caps in sorted(pattern_capabilities.items()):
        total = len(caps)
        implemented = sum(1 for c in caps if c in implemented_caps)
        missing = total - implemented

        if missing == 0:
            status = "✅ Complete"
        elif implemented == 0:
            status = "❌ Not Started"
        else:
            status = f"⚠️ Partial ({implemented}/{total})"

        print(f"| {pattern_id} | {total} | {implemented} | {missing} | {status} |")

    print()
    print("---")
    print()

    # Agent-by-Agent Analysis
    print("## Agent Capability Inventory")
    print()

    for agent_name, caps in sorted(agent_capabilities.items()):
        print(f"### {agent_name}")
        print()
        print(f"**Capabilities**: {len(caps)}")
        print()
        if caps:
            for cap in sorted(caps):
                print(f"- `{cap}`")
        else:
            print("- *(No capabilities declared)*")
        print()

    print("---")
    print()

    # Missing Capabilities by Category
    print("## Missing Capabilities")
    print()

    if missing_caps:
        # Group by prefix
        by_category = defaultdict(list)
        for cap in missing_caps:
            prefix = cap.split(".")[0] if "." in cap else "other"
            by_category[prefix].append(cap)

        for category in sorted(by_category.keys()):
            caps = by_category[category]
            print(f"### {category.title()} ({len(caps)} missing)")
            print()
            for cap in sorted(caps):
                # Check if service might exist
                service_name = cap.split(".")[0]
                has_service = service_name in service_methods
                service_indicator = " (service exists)" if has_service else " (no service)"
                print(f"- `{cap}`{service_indicator}")
            print()
    else:
        print("✅ **No missing capabilities** - All pattern capabilities are implemented!")
        print()

    print("---")
    print()

    # Service Method Inventory
    print("## Service Method Inventory")
    print()
    print("Services available with async method counts:")
    print()

    for service_name, methods in sorted(service_methods.items()):
        print(f"### {service_name}.py ({len(methods)} methods)")
        print()
        if methods:
            for method in sorted(methods):
                print(f"- `{method}()`")
        else:
            print("- *(No async methods found)*")
        print()

    print("---")
    print()

    # Recommendations
    print("## Recommendations")
    print()

    if missing_caps:
        print("### Priority Actions")
        print()

        # Check which missing capabilities have services
        with_service = [c for c in missing_caps if c.split(".")[0] in service_methods]
        without_service = [c for c in missing_caps if c.split(".")[0] not in service_methods]

        if with_service:
            print(f"**1. Wire existing services ({len(with_service)} capabilities)**")
            print()
            print("These capabilities likely just need agent methods added:")
            for cap in sorted(with_service):
                service = cap.split(".")[0]
                method = cap.split(".")[1] if "." in cap else cap
                print(f"- `{cap}` → Check if `{service}.py` has `{method}()` method")
            print()

        if without_service:
            print(f"**2. Implement missing services ({len(without_service)} capabilities)**")
            print()
            print("These capabilities need new service files or methods:")

            # Group by service
            by_service = defaultdict(list)
            for cap in without_service:
                service = cap.split(".")[0]
                by_service[service].append(cap)

            for service_name, caps in sorted(by_service.items()):
                print(f"- Create/update `{service_name}.py` ({len(caps)} methods)")
                for cap in sorted(caps):
                    print(f"  - `{cap}`")
            print()
    else:
        print("✅ All pattern capabilities are implemented. Consider:")
        print()
        print("1. End-to-end testing of all patterns")
        print("2. Performance optimization")
        print("3. Additional pattern development")
        print()


if __name__ == "__main__":
    generate_audit_report()
