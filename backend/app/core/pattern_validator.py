"""
Pattern Output Validation Utility

Purpose: Validate pattern outputs against orchestrator state
Created: 2025-11-06
Priority: P1 (Improves pattern development experience)

Features:
    - Validates panel ID → step result mapping
    - Detects orphaned panel IDs (no matching state key)
    - Detects ambiguous matches (multiple state keys match)
    - Validates dataPath root keys exist
    - Supports all three output formats (list, dict, panels)

Usage:
    from app.core.pattern_validator import validate_pattern_outputs

    warnings = validate_pattern_outputs(spec, state)
    if warnings:
        for warning in warnings:
            logger.warning(f"Pattern validation: {warning}")
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def validate_pattern_outputs(spec: Dict[str, Any], state: Dict[str, Any]) -> List[str]:
    """
    Validate pattern outputs against orchestrator state.

    Checks:
    - Format 1 (list): All keys exist in state
    - Format 2 (dict): All keys exist in state
    - Format 3 (panels): Panel IDs match state keys, dataPaths are valid

    Args:
        spec: Pattern specification dict
        state: Orchestrator state dict (step results)

    Returns:
        List of warning messages (empty if valid)

    Examples:
        >>> spec = {"outputs": ["key1", "key2"]}
        >>> state = {"key1": {...}, "key2": {...}}
        >>> validate_pattern_outputs(spec, state)
        []

        >>> spec = {"outputs": ["missing_key"]}
        >>> state = {"key1": {...}}
        >>> validate_pattern_outputs(spec, state)
        ["Output key 'missing_key' not found in state (available: key1)"]

        >>> spec = {"outputs": {"panels": [{"id": "risk_map", "dataPath": "cycle_risk_map"}]}}
        >>> state = {"cycle_risk_map": {...}}
        >>> validate_pattern_outputs(spec, state)
        []  # Fuzzy match: risk_map → cycle_risk_map
    """
    warnings = []
    outputs_spec = spec.get("outputs", {})

    if isinstance(outputs_spec, list):
        # Format 1: List of keys ["key1", "key2"]
        warnings.extend(_validate_list_format(outputs_spec, state))

    elif isinstance(outputs_spec, dict):
        if "panels" in outputs_spec:
            # Format 3: Panels with dataPath
            warnings.extend(_validate_panels_format(outputs_spec["panels"], state))
        else:
            # Format 2: Dict with keys {"key1": {...}, "key2": {...}}
            warnings.extend(_validate_dict_format(outputs_spec, state))

    else:
        # Unknown format
        warnings.append(f"Unexpected outputs format: {type(outputs_spec).__name__} (expected list or dict)")

    return warnings


def _validate_list_format(outputs_spec: List[str], state: Dict[str, Any]) -> List[str]:
    """
    Validate Format 1: Simple list of output keys.

    Args:
        outputs_spec: List of output keys
        state: Orchestrator state

    Returns:
        List of warnings
    """
    warnings = []

    for key in outputs_spec:
        if key not in state:
            available_keys = ", ".join(sorted(state.keys()))
            warnings.append(f"Output key '{key}' not found in state (available: {available_keys})")

    return warnings


def _validate_dict_format(outputs_spec: Dict[str, Any], state: Dict[str, Any]) -> List[str]:
    """
    Validate Format 2: Dict with keys.

    Args:
        outputs_spec: Dict of output keys
        state: Orchestrator state

    Returns:
        List of warnings
    """
    warnings = []

    for key in outputs_spec.keys():
        if key not in state:
            available_keys = ", ".join(sorted(state.keys()))
            warnings.append(f"Output key '{key}' not found in state (available: {available_keys})")

    return warnings


def _validate_panels_format(panels: List[Dict[str, Any]], state: Dict[str, Any]) -> List[str]:
    """
    Validate Format 3: Panels with dataPath.

    Checks:
    - Panel IDs have at least one matching state key (fuzzy matching)
    - Panel IDs don't match multiple state keys (ambiguous)
    - dataPath root keys exist in state

    Args:
        panels: List of panel dicts
        state: Orchestrator state

    Returns:
        List of warnings
    """
    warnings = []

    for panel in panels:
        if not isinstance(panel, dict):
            warnings.append(f"Panel is not a dict: {panel}")
            continue

        panel_id = panel.get("id")
        data_path = panel.get("dataPath")

        if not panel_id:
            warnings.append(f"Panel missing 'id' field: {panel}")
            continue

        # Check for fuzzy matches (same logic as orchestrator)
        matches = _find_fuzzy_matches(panel_id, state)

        if len(matches) == 0:
            # No matches - orphaned panel ID
            available_keys = ", ".join(sorted(state.keys()))
            warnings.append(
                f"Panel '{panel_id}' has no matching state key. "
                f"Available keys: {available_keys}. "
                f"Fuzzy matching rules: exact match, prefix match (key_*), suffix match (*_key)"
            )
        elif len(matches) > 1:
            # Multiple matches - ambiguous
            warnings.append(
                f"Panel '{panel_id}' matches multiple state keys: {', '.join(matches)}. "
                f"This is ambiguous. Use more specific panel ID or exact match."
            )

        # Validate dataPath if present
        if data_path:
            warnings.extend(_validate_data_path(panel_id, data_path, state))

    return warnings


def _find_fuzzy_matches(panel_id: str, state: Dict[str, Any]) -> List[str]:
    """
    Find state keys that fuzzy match panel ID.

    Matching rules (same as orchestrator):
    1. Exact match: panel_id == state_key
    2. Suffix match: state_key.endswith(f"_{panel_id}")
    3. Prefix match: state_key.startswith(f"{panel_id}_")

    Args:
        panel_id: Panel ID to match
        state: Orchestrator state

    Returns:
        List of matching state keys
    """
    matches = []

    for state_key in state.keys():
        if (state_key == panel_id or
            state_key.endswith(f"_{panel_id}") or
            state_key.startswith(f"{panel_id}_")):
            matches.append(state_key)

    return matches


def _validate_data_path(panel_id: str, data_path: str, state: Dict[str, Any]) -> List[str]:
    """
    Validate dataPath is resolvable.

    Checks:
    - dataPath root key exists in state
    - If dataPath is nested, root key is dict (can be drilled into)

    Args:
        panel_id: Panel ID (for error messages)
        data_path: Data path (e.g., "cycle_risk_map" or "analysis.scenarios")
        state: Orchestrator state

    Returns:
        List of warnings
    """
    warnings = []

    # Extract root key (before first dot)
    parts = data_path.split('.')
    root_key = parts[0]

    # Check root key exists
    if root_key not in state:
        available_keys = ", ".join(sorted(state.keys()))
        warnings.append(
            f"Panel '{panel_id}' dataPath root '{root_key}' not found in state. "
            f"Available keys: {available_keys}"
        )
        return warnings

    # If nested path, check root is dict
    if len(parts) > 1:
        root_value = state[root_key]
        if not isinstance(root_value, dict):
            warnings.append(
                f"Panel '{panel_id}' dataPath '{data_path}' has nested path, "
                f"but root key '{root_key}' is {type(root_value).__name__}, not dict. "
                f"Nested paths require dict structure."
            )

    return warnings


def validate_all_patterns(patterns_dir: str = "backend/patterns") -> Dict[str, List[str]]:
    """
    Validate all patterns in directory.

    NOTE: This function can't actually validate against state because
    state is only available at runtime. It validates pattern structure only.

    Args:
        patterns_dir: Directory containing pattern JSON files

    Returns:
        Dict mapping pattern_id → list of structural warnings
    """
    import os
    import json

    results = {}

    for filename in os.listdir(patterns_dir):
        if not filename.endswith(".json"):
            continue

        pattern_path = os.path.join(patterns_dir, filename)
        pattern_id = filename.replace(".json", "")

        try:
            with open(pattern_path, "r") as f:
                spec = json.load(f)

            # Structural validation only (no state available)
            warnings = _validate_pattern_structure(spec)
            if warnings:
                results[pattern_id] = warnings

        except (ValueError, TypeError, KeyError, AttributeError) as e:
            # Programming errors - should not happen, log and record
            results[pattern_id] = [f"Programming error loading pattern: {str(e)}"]
        except Exception as e:
            # Pattern loading errors - record
            results[pattern_id] = [f"Failed to load pattern: {str(e)}"]

    return results


def _validate_pattern_structure(spec: Dict[str, Any]) -> List[str]:
    """
    Validate pattern structure (without runtime state).

    Checks:
    - outputs field exists
    - outputs format is valid (list, dict, or panels)
    - panels have required fields (id, dataPath)

    Args:
        spec: Pattern specification

    Returns:
        List of structural warnings
    """
    warnings = []

    if "outputs" not in spec:
        warnings.append("Pattern missing 'outputs' field")
        return warnings

    outputs_spec = spec["outputs"]

    if isinstance(outputs_spec, list):
        # Format 1: Valid
        if not outputs_spec:
            warnings.append("Outputs list is empty")

    elif isinstance(outputs_spec, dict):
        if "panels" in outputs_spec:
            # Format 3: Validate panel structure
            panels = outputs_spec["panels"]
            if not isinstance(panels, list):
                warnings.append(f"'panels' field must be list, got {type(panels).__name__}")
            else:
                for i, panel in enumerate(panels):
                    if not isinstance(panel, dict):
                        warnings.append(f"Panel {i} is not a dict: {panel}")
                        continue

                    if "id" not in panel:
                        warnings.append(f"Panel {i} missing 'id' field")

                    if "dataPath" not in panel:
                        warnings.append(f"Panel {i} missing 'dataPath' field (recommended for Format 3)")
        else:
            # Format 2: Valid
            if not outputs_spec:
                warnings.append("Outputs dict is empty")

    else:
        warnings.append(f"Unexpected outputs format: {type(outputs_spec).__name__} (expected list or dict)")

    return warnings
