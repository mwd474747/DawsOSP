"""
Capability Contract System

Purpose: Document and validate capability contracts
Created: January 14, 2025
Priority: P1 (Foundation for Phase 2)

Features:
    - Capability decorator for documenting contracts
    - Self-documenting code
    - Clear expectations (inputs, outputs, behavior)
    - Stub identification (mark stub vs real implementations)

Usage:
    from app.core.capability_contract import capability

    @capability(
        name="risk.compute_factor_exposures",
        inputs={"portfolio_id": str, "pack_id": str},
        outputs={"factors": dict, "r_squared": float, "_provenance": dict},
        fetches_positions=False,
        implementation_status="stub",
        description="Compute portfolio factor exposures (currently stub implementation)",
        dependencies=["ledger.positions", "pricing.apply_pack"],
    )
    async def risk_compute_factor_exposures(...):
        ...
"""

from typing import Dict, Any, Optional, Callable, Type
from functools import wraps
import inspect
import logging

logger = logging.getLogger(__name__)


def capability(
    name: str,
    inputs: Dict[str, Type],
    outputs: Dict[str, Type],
    fetches_positions: bool = False,
    implementation_status: str = "real",  # "real" | "stub" | "partial"
    description: Optional[str] = None,
    dependencies: Optional[list] = None,
):
    """
    Decorator to document capability contracts.
    
    Args:
        name: Capability name (e.g., "risk.compute_factor_exposures")
        inputs: Dict of input parameter names and types
        outputs: Dict of output field names and types
        fetches_positions: Whether capability fetches positions internally
        implementation_status: "real" | "stub" | "partial"
        description: Human-readable description
        dependencies: List of capability dependencies
    
    Returns:
        Decorated function with contract metadata attached
    
    Example:
        @capability(
            name="risk.compute_factor_exposures",
            inputs={"portfolio_id": str, "pack_id": str},
            outputs={"factors": dict, "_provenance": dict},
            implementation_status="stub",
            description="Compute portfolio factor exposures (stub implementation)",
        )
        async def risk_compute_factor_exposures(self, ctx, state, portfolio_id, pack_id):
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Store contract metadata
        contract = {
            "name": name,
            "inputs": inputs,
            "outputs": outputs,
            "fetches_positions": fetches_positions,
            "implementation_status": implementation_status,
            "description": description or "",
            "dependencies": dependencies or [],
        }
        
        # Attach to function
        func.__capability_contract__ = contract
        
        # Preserve original function metadata
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        # Copy contract to wrapper
        wrapper.__capability_contract__ = contract
        
        # Copy other attributes
        if hasattr(func, '__doc__'):
            wrapper.__doc__ = func.__doc__
        
        return wrapper
    
    return decorator


def get_capability_contract(func: Callable) -> Optional[Dict[str, Any]]:
    """
    Get capability contract from function.
    
    Args:
        func: Function to get contract from
    
    Returns:
        Contract dict or None if not found
    """
    return getattr(func, '__capability_contract__', None)


def extract_all_contracts(agent_class) -> Dict[str, Dict[str, Any]]:
    """
    Extract all capability contracts from an agent class.
    
    Args:
        agent_class: Agent class to extract contracts from
    
    Returns:
        Dict mapping capability names to contracts
    """
    contracts = {}
    
    for name, method in inspect.getmembers(agent_class, inspect.ismethod):
        contract = get_capability_contract(method)
        if contract:
            contracts[contract['name']] = contract
    
    # Also check functions (for module-level capabilities)
    for name, method in inspect.getmembers(agent_class, inspect.isfunction):
        contract = get_capability_contract(method)
        if contract:
            contracts[contract['name']] = contract
    
    return contracts


def validate_contract(func: Callable, contract: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate function signature matches contract.
    
    Args:
        func: Function to validate
        contract: Contract dict
    
    Returns:
        Validation result with errors and warnings
    """
    errors = []
    warnings = []
    
    # Get function signature
    sig = inspect.signature(func)
    params = sig.parameters
    
    # Check inputs
    contract_inputs = contract.get("inputs", {})
    for param_name, param_type in contract_inputs.items():
        if param_name not in params:
            # Skip special parameters (self, ctx, state)
            if param_name not in ['self', 'ctx', 'state']:
                warnings.append(
                    f"Contract specifies input '{param_name}' but function doesn't have it"
                )
    
    # Check for extra parameters
    for param_name, param in params.items():
        if param_name in ['self', 'ctx', 'state']:
            continue
        if param_name not in contract_inputs:
            warnings.append(
                f"Function has parameter '{param_name}' but contract doesn't specify it"
            )
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }

