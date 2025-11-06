"""
Pattern Linter CLI Tool

Purpose: Validate all patterns before deployment
Created: January 14, 2025
Priority: P1 (Foundation for Phase 2)

Features:
    - Validate single pattern or all patterns
    - Check dependencies, contracts, formats
    - Output clear errors and warnings
    - CI/CD friendly (exit codes)

Usage:
    # Validate single pattern
    python -m app.core.pattern_linter --pattern portfolio_cycle_risk

    # Validate all patterns
    python -m app.core.pattern_linter --all

    # Validate and output JSON
    python -m app.core.pattern_linter --all --json

    # Exit with error code if validation fails
    python -m app.core.pattern_linter --all --strict
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

from app.core.pattern_orchestrator import PatternOrchestrator
from app.db.connection import get_db_pool


class PatternLinter:
    """Pattern linter for validation."""
    
    def __init__(self, orchestrator: PatternOrchestrator):
        self.orchestrator = orchestrator
    
    def lint_pattern(self, pattern_id: str) -> Dict[str, Any]:
        """
        Lint a single pattern.
        
        Args:
            pattern_id: Pattern ID to lint
        
        Returns:
            Dict with validation results
        """
        results = {
            "pattern_id": pattern_id,
            "valid": True,
            "errors": [],
            "warnings": [],
            "checks": {}
        }
        
        # Check if pattern exists
        if pattern_id not in self.orchestrator.patterns:
            results["valid"] = False
            results["errors"].append(f"Pattern '{pattern_id}' not found")
            return results
        
        spec = self.orchestrator.patterns[pattern_id]
        
        # Check 1: Dependency validation
        validation_result = self.orchestrator.validate_pattern_dependencies(pattern_id)
        results["checks"]["dependencies"] = validation_result
        if not validation_result["valid"]:
            results["valid"] = False
            results["errors"].extend(validation_result["errors"])
        results["warnings"].extend(validation_result["warnings"])
        
        # Check 2: Output format validation
        outputs = spec.get("outputs", [])
        if not isinstance(outputs, list):
            results["valid"] = False
            results["errors"].append(
                f"Outputs must be a list, got {type(outputs).__name__}"
            )
        else:
            results["checks"]["output_format"] = {"valid": True, "format": "list"}
        
        # Check 3: Step "as" keys match output keys
        steps = spec.get("steps", [])
        step_keys = {step.get("as") for step in steps if step.get("as")}
        output_keys = set(outputs)
        
        missing_in_outputs = step_keys - output_keys
        missing_in_steps = output_keys - step_keys
        
        if missing_in_outputs:
            results["valid"] = False
            results["errors"].append(
                f"Step 'as' keys not in outputs: {sorted(missing_in_outputs)}"
            )
        
        if missing_in_steps:
            results["warnings"].append(
                f"Output keys not in step 'as' keys: {sorted(missing_in_steps)}"
            )
        
        results["checks"]["step_output_match"] = {
            "valid": len(missing_in_outputs) == 0,
            "missing_in_outputs": list(missing_in_outputs),
            "missing_in_steps": list(missing_in_steps),
        }
        
        # Check 4: Capability validation
        capabilities = [step.get("capability") for step in steps if step.get("capability")]
        missing_capabilities = []
        for capability in capabilities:
            if capability not in self.orchestrator.agent_runtime.capability_map:
                missing_capabilities.append(capability)
        
        if missing_capabilities:
            results["valid"] = False
            results["errors"].append(
                f"Capabilities not found: {missing_capabilities}"
            )
        
        results["checks"]["capabilities"] = {
            "valid": len(missing_capabilities) == 0,
            "missing": missing_capabilities,
        }
        
        return results
    
    def lint_all(self) -> Dict[str, Any]:
        """
        Lint all patterns.
        
        Returns:
            Dict with validation results for all patterns
        """
        all_results = {
            "valid": True,
            "patterns": {},
            "summary": {
                "total": 0,
                "valid": 0,
                "invalid": 0,
                "errors": 0,
                "warnings": 0,
            }
        }
        
        for pattern_id in self.orchestrator.patterns.keys():
            result = self.lint_pattern(pattern_id)
            all_results["patterns"][pattern_id] = result
            
            all_results["summary"]["total"] += 1
            if result["valid"]:
                all_results["summary"]["valid"] += 1
            else:
                all_results["summary"]["invalid"] += 1
                all_results["valid"] = False
            
            all_results["summary"]["errors"] += len(result["errors"])
            all_results["summary"]["warnings"] += len(result["warnings"])
        
        return all_results


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Pattern linter")
    parser.add_argument("--pattern", help="Pattern ID to validate")
    parser.add_argument("--all", action="store_true", help="Validate all patterns")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--strict", action="store_true", help="Exit with error code if validation fails")
    
    args = parser.parse_args()
    
    # Initialize orchestrator (requires agent runtime and db)
    # Import here to avoid circular dependencies
    try:
        from combined_server import get_agent_runtime
        agent_runtime = get_agent_runtime()
        db_pool = get_db_pool()
        
        orchestrator = PatternOrchestrator(agent_runtime, db_pool)
        linter = PatternLinter(orchestrator)
        
        if args.pattern:
            result = linter.lint_pattern(args.pattern)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"Pattern: {result['pattern_id']}")
                print(f"Valid: {result['valid']}")
                if result['errors']:
                    print("\nErrors:")
                    for error in result['errors']:
                        print(f"  - {error}")
                if result['warnings']:
                    print("\nWarnings:")
                    for warning in result['warnings']:
                        print(f"  - {warning}")
            
            if args.strict and not result['valid']:
                sys.exit(1)
        
        elif args.all:
            results = linter.lint_all()
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print(f"Total patterns: {results['summary']['total']}")
                print(f"Valid: {results['summary']['valid']}")
                print(f"Invalid: {results['summary']['invalid']}")
                print(f"Errors: {results['summary']['errors']}")
                print(f"Warnings: {results['summary']['warnings']}")
                
                for pattern_id, result in results['patterns'].items():
                    if not result['valid']:
                        print(f"\n{pattern_id}:")
                        for error in result['errors']:
                            print(f"  ERROR: {error}")
            
            if args.strict and not results['valid']:
                sys.exit(1)
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error initializing pattern linter: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

