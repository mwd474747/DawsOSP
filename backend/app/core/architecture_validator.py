"""
Architecture Validation Utilities

Purpose: Validate codebase against architecture principles
Created: 2025-01-15
Priority: P3 (Prevents anti-patterns)

This module provides validation functions to ensure the codebase follows
architectural patterns and prevents anti-patterns from being introduced.
"""

import ast
import os
import logging
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)


def validate_no_singleton_factories(root_dir: str = "backend/app") -> List[Tuple[str, str, int]]:
    """
    Check that no singleton factory functions exist.
    
    Returns:
        List of (file_path, function_name, line_number) violations
    """
    violations = []
    
    for root, dirs, files in os.walk(root_dir):
        # Skip test files
        if "test" in root or "__pycache__" in root:
            continue
            
        for file in files:
            if not file.endswith(".py"):
                continue
                
            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, 'r') as f:
                    tree = ast.parse(f.read(), filename=file_path)
                    
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check for get_*_service or get_*_agent patterns
                        if (node.name.startswith("get_") and 
                            (node.name.endswith("_service") or node.name.endswith("_agent"))):
                            # Skip if it's a comment explaining removal
                            # Check if function body is just a comment/docstring
                            violations.append((file_path, node.name, node.lineno))
                            
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")
    
    return violations


def validate_imports_use_classes(root_dir: str = "backend") -> List[Tuple[str, str, int]]:
    """
    Check that imports use classes, not factory functions.
    
    Returns:
        List of (file_path, import_statement, line_number) violations
    """
    violations = []
    
    for root, dirs, files in os.walk(root_dir):
        if "test" in root or "__pycache__" in root:
            continue
            
        for file in files:
            if not file.endswith(".py"):
                continue
                
            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines, 1):
                    # Check for imports of get_*_service or get_*_agent
                    if "import" in line and ("get_" in line and ("_service" in line or "_agent" in line)):
                        # Skip if it's a comment
                        if line.strip().startswith("#"):
                            continue
                        # Skip if it's in a migration comment
                        if "Migration:" in line or "OLD:" in line or "DEPRECATED" in line:
                            continue
                        violations.append((file_path, line.strip(), i))
                        
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
    
    return violations


def run_architecture_validation() -> dict:
    """
    Run all architecture validation checks.
    
    Returns:
        Dictionary with validation results
    """
    results = {
        "singleton_factories": validate_no_singleton_factories(),
        "factory_imports": validate_imports_use_classes(),
        "valid": True
    }
    
    if results["singleton_factories"] or results["factory_imports"]:
        results["valid"] = False
        logger.error("Architecture validation failed!")
        logger.error(f"Found {len(results['singleton_factories'])} singleton factory functions")
        logger.error(f"Found {len(results['factory_imports'])} factory function imports")
    
    return results


if __name__ == "__main__":
    """Run validation and print results."""
    results = run_architecture_validation()
    
    if not results["valid"]:
        print("❌ Architecture validation failed!")
        print("\nSingleton Factory Functions:")
        for file, func, line in results["singleton_factories"]:
            print(f"  {file}:{line} - {func}")
        print("\nFactory Function Imports:")
        for file, import_stmt, line in results["factory_imports"]:
            print(f"  {file}:{line} - {import_stmt}")
        exit(1)
    else:
        print("✅ Architecture validation passed!")
        exit(0)

