"""
DawsOS Pattern Orchestrator

Purpose: Load and execute JSON patterns with template substitution and tracing
Updated: 2025-01-14
Priority: P0 (Critical for pattern-driven execution)

Features:
    - Load patterns from patterns/ directory
    - Execute DAG steps sequentially (parallel support in Phase 2)
    - Template substitution ({{foo}}, {{ctx.bar}}, {{inputs.baz}})
    - Build execution trace with agents_used, capabilities_used, sources
    - Per-panel staleness tracking
    - Conditional step execution
    - Redis caching for intermediate results
    - Pattern contract validation (Phase 3)

Usage:
    orchestrator = PatternOrchestrator(agent_runtime, db, redis)
    result = await orchestrator.run_pattern("portfolio_overview", ctx, inputs)
"""

import inspect
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.types import RequestCtx

# Optional import for observability (graceful degradation)
try:
    from observability.metrics import get_metrics
except ImportError:
    def get_metrics():
        """Fallback metrics function when observability not available"""
        return None

# Optional import for pattern response validation (graceful degradation)
try:
    from app.schemas.pattern_responses import PatternResponseValidator
except ImportError:
    # Fallback if schemas not available
    class PatternResponseValidator:
        @classmethod
        def validate(cls, pattern_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
            """Fallback validator when schemas not available"""
            return result

        @classmethod
        def check_deprecated_fields(cls, data: Any, path: str = "root") -> List[str]:
            """Fallback deprecated field checker"""
            return []

logger = logging.getLogger(__name__)


# ============================================================================
# Execution Trace
# ============================================================================


class Trace:
    """
    Execution trace builder.

    Tracks all steps, agents, capabilities, and data sources used during
    pattern execution for full reproducibility and debugging.
    """

    def __init__(self, pattern_id: str, ctx: RequestCtx, agent_runtime=None):
        self.pattern_id = pattern_id
        self.pricing_pack_id = ctx.pricing_pack_id
        self.ledger_commit_hash = ctx.ledger_commit_hash
        self.trace_id = ctx.trace_id
        self.request_id = ctx.request_id
        self.steps: List[Dict[str, Any]] = []
        self.agents_used: set[str] = set()
        self.capabilities_used: set[str] = set()
        self.sources: set[str] = set()
        self.per_panel_staleness: List[Dict[str, Any]] = []
        self.agent_runtime = agent_runtime  # For cache stats

    def add_step(
        self,
        capability: str,
        result: Any,
        args: Dict[str, Any],
        duration_seconds: float,
    ):
        """
        Add successful step to trace.

        Args:
            capability: Capability name (e.g., "ledger.positions")
            result: Result returned by capability
            args: Arguments passed to capability
            duration_seconds: Execution time in seconds
        """
        self.capabilities_used.add(capability)

        # Extract metadata from result if available (Phase 1: Move metadata to trace only)
        # Support both __metadata__ attribute and _metadata key in dicts
        metadata = None
        if hasattr(result, "__metadata__"):
            metadata = result.__metadata__
        elif isinstance(result, dict) and "_metadata" in result:
            # Extract metadata dict and convert to object-like structure for compatibility
            metadata_dict = result["_metadata"]
            class MetadataObj:
                def __init__(self, d):
                    self.agent_name = d.get("agent_name")
                    self.source = d.get("source")
                    self.asof = d.get("asof")
                    self.ttl = d.get("ttl")
                    self.confidence = d.get("confidence")
            metadata = MetadataObj(metadata_dict)
        
        if metadata:
            if hasattr(metadata, "agent_name") and metadata.agent_name:
                self.agents_used.add(metadata.agent_name)
            if hasattr(metadata, "source") and metadata.source:
                self.sources.add(metadata.source)
            if hasattr(metadata, "asof") and metadata.asof:
                self.per_panel_staleness.append({
                    "capability": capability,
                    "asof": str(metadata.asof),
                    "ttl": getattr(metadata, "ttl", None),
                })
        
        # Extract provenance information if available
        provenance = None
        if isinstance(result, dict) and "_provenance" in result:
            provenance = result["_provenance"]

        step_data = {
            "capability": capability,
            "args": args,
            "success": True,
            "duration_seconds": duration_seconds,
        }
        
        # Add provenance to step if available
        if provenance:
            step_data["provenance"] = provenance

        self.steps.append(step_data)

    def add_error(self, capability: str, error: str):
        """
        Add failed step to trace.

        Args:
            capability: Capability that failed
            error: Error message
        """
        self.steps.append({
            "capability": capability,
            "success": False,
            "error": error,
        })

    def skip_step(self, capability: str, reason: str = "condition_not_met"):
        """
        Add skipped step to trace.

        Args:
            capability: Capability that was skipped
            reason: Why step was skipped
        """
        self.steps.append({
            "capability": capability,
            "skipped": True,
            "reason": reason,
        })

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize trace to dict for API response.

        Returns:
            Dict with pattern_id, pricing_pack_id, ledger_commit_hash, agents, capabilities, sources, steps, cache_stats, and provenance
        """
        trace_dict = {
            "pattern_id": self.pattern_id,
            "pricing_pack_id": self.pricing_pack_id,
            "ledger_commit_hash": self.ledger_commit_hash,
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "agents_used": sorted(list(self.agents_used)),
            "capabilities_used": sorted(list(self.capabilities_used)),
            "sources": sorted(list(self.sources)),
            "per_panel_staleness": self.per_panel_staleness,
            "steps": self.steps,
        }

        # Add cache stats if agent_runtime available
        if self.agent_runtime:
            cache_stats = self.agent_runtime.get_cache_stats(self.request_id)
            trace_dict["cache_stats"] = cache_stats
        
        # Aggregate provenance information from steps
        provenance_types = set()
        all_warnings = []
        for step in self.steps:
            if "provenance" in step:
                prov_info = step["provenance"]
                if "type" in prov_info:
                    provenance_types.add(prov_info["type"])
                if "warnings" in prov_info:
                    all_warnings.extend(prov_info["warnings"])
        
        # Determine overall provenance
        overall_provenance = "unknown"
        if "stub" in provenance_types:
            overall_provenance = "mixed" if len(provenance_types) > 1 else "stub"
        elif "real" in provenance_types:
            overall_provenance = "real"
        elif "cached" in provenance_types:
            overall_provenance = "cached"
        elif "computed" in provenance_types:
            overall_provenance = "computed"
        
        trace_dict["data_provenance"] = {
            "overall": overall_provenance,
            "types_used": sorted(list(provenance_types)),
            "warnings": list(set(all_warnings))  # Deduplicate warnings
        }

        return trace_dict


# ============================================================================
# Pattern Orchestrator
# ============================================================================


class PatternOrchestrator:
    """
    Pattern orchestrator: load and execute JSON patterns.

    Responsibilities:
        1. Load pattern definitions from patterns/ directory
        2. Validate pattern structure against schema
        3. Execute steps in order (sequential for S1, parallel in S2)
        4. Resolve template arguments ({{foo}}, {{ctx.bar}}, {{inputs.baz}})
        5. Route capabilities to agent runtime
        6. Build execution trace for reproducibility
        7. Cache intermediate results in Redis
    """

    def __init__(self, agent_runtime, db, redis=None):
        """
        Initialize pattern orchestrator.

        Args:
            agent_runtime: AgentRuntime instance for capability routing
            db: Database connection pool
            redis: Redis connection pool (optional, for caching)
        """
        self.agent_runtime = agent_runtime
        self.db = db
        self.redis = redis
        self.patterns: Dict[str, Dict[str, Any]] = {}
        self._load_patterns()

    def _load_patterns(self):
        """
        Load all pattern JSON files from backend/patterns/ directory.

        Pattern files must have structure:
        {
            "id": "pattern_name",
            "name": "Human Readable Name",
            "description": "What this pattern does",
            "category": "analysis|workflow|action|governance",
            "inputs": {...},
            "steps": [...],
            "outputs": [...]
        }
        """
        # GOVERNANCE FIX #2: Use correct pattern directory path
        # backend/app/core/pattern_orchestrator.py -> parent.parent.parent = backend/ -> patterns/
        patterns_dir = Path(__file__).parent.parent.parent / "patterns"
        if not patterns_dir.exists():
            logger.warning(f"Patterns directory not found: {patterns_dir}")
            return

        pattern_count = 0
        for pattern_file in patterns_dir.rglob("*.json"):
            try:
                spec = json.loads(pattern_file.read_text())

                # Validate required fields
                required = ["id", "name", "steps", "outputs"]
                missing = [f for f in required if f not in spec]
                if missing:
                    logger.error(
                        f"Pattern {pattern_file} missing required fields: {missing}"
                    )
                    continue

                pattern_id = spec["id"]
                self.patterns[pattern_id] = spec
                
                # PHASE 2: Validate pattern dependencies during loading
                validation_result = self.validate_pattern_dependencies(pattern_id)
                if not validation_result["valid"]:
                    logger.error(
                        f"Pattern {pattern_id} failed dependency validation:\n"
                        + "\n".join(validation_result["errors"])
                    )
                    # Still load pattern, but log error
                elif validation_result["warnings"]:
                    for warning in validation_result["warnings"]:
                        logger.warning(f"Pattern {pattern_id}: {warning}")
                
                pattern_count += 1
                logger.debug(f"Loaded pattern: {pattern_id} from {pattern_file}")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse pattern {pattern_file}: {e}")
            except Exception as e:
                logger.error(f"Failed to load pattern {pattern_file}: {e}")

        logger.info(f"Loaded {pattern_count} patterns from {patterns_dir}")

    def list_patterns(self) -> List[Dict[str, Any]]:
        """
        Get list of all loaded patterns with metadata.

        Returns:
            List of pattern metadata dicts including display configuration
        """
        return [
            {
                "id": spec["id"],
                "name": spec["name"],
                "description": spec.get("description", ""),
                "category": spec.get("category", "unknown"),
                "display": spec.get("display", {}),  # Display configuration for frontend
                "inputs": spec.get("inputs", {}),    # Input schema
            }
            for spec in self.patterns.values()
        ]

    def get_pattern_metadata(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed metadata for a specific pattern.

        Args:
            pattern_id: Pattern identifier

        Returns:
            Pattern metadata dict or None if not found
        """
        spec = self.patterns.get(pattern_id)
        if not spec:
            return None

        return {
            "id": spec["id"],
            "name": spec["name"],
            "description": spec.get("description", ""),
            "category": spec.get("category", "unknown"),
            "display": spec.get("display", {}),
            "inputs": spec.get("inputs", {}),
            "outputs": spec.get("outputs", []),
            "steps_count": len(spec.get("steps", [])),
        }

    def _apply_pattern_defaults(
        self, 
        spec: Dict[str, Any], 
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply default values from pattern spec to inputs.
        
        Args:
            spec: Pattern specification
            inputs: User-provided inputs
            
        Returns:
            Merged inputs with defaults applied
        """
        # Start with a copy of user inputs
        merged = inputs.copy()
        
        # Get the inputs spec from the pattern
        inputs_spec = spec.get("inputs", {})
        
        # Apply defaults for any missing optional inputs
        for input_name, input_config in inputs_spec.items():
            # Skip if already provided by user
            if input_name in merged:
                continue
                
            # Skip required inputs without defaults
            if input_config.get("required", False) and "default" not in input_config:
                continue
                
            # Apply default if available
            if "default" in input_config:
                default_value = input_config["default"]
                merged[input_name] = default_value
                logger.info(f"Applied default for {input_name}: {default_value}")
                
        return merged

    def validate_pattern(
        self, 
        pattern_id: str,
        inputs: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Validate that a pattern's capabilities exist and have matching parameters.
        
        This method performs contract validation to ensure:
        1. All capabilities referenced in the pattern exist in the agent runtime
        2. Required parameters for each capability are available
        3. Parameter types match the agent method signatures
        
        Args:
            pattern_id: Pattern ID to validate
            inputs: Optional inputs to validate against pattern requirements
            
        Returns:
            Dict with validation results:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str],
                "capabilities": {
                    "capability_name": {
                        "exists": bool,
                        "agent": str,
                        "required_params": List[str],
                        "missing_params": List[str],
                        "errors": List[str]
                    }
                }
            }
        """
        errors = []
        warnings = []
        capability_details = {}
        
        # Check if pattern exists
        spec = self.patterns.get(pattern_id)
        if not spec:
            return {
                "valid": False,
                "errors": [f"Pattern '{pattern_id}' not found"],
                "warnings": [],
                "capabilities": {}
            }
        
        # Validate inputs if provided
        if inputs is None:
            inputs = {}
        
        pattern_inputs_spec = spec.get("inputs", {})
        
        # Check required inputs
        for input_name, input_config in pattern_inputs_spec.items():
            if input_config.get("required", False):
                if input_name not in inputs and "default" not in input_config:
                    errors.append(f"Required input '{input_name}' is missing")
        
        # Validate each step's capability
        for step_idx, step in enumerate(spec.get("steps", [])):
            capability = step.get("capability")
            if not capability:
                errors.append(f"Step {step_idx} missing capability definition")
                continue
            
            # Check if capability exists in agent runtime
            agent_name = self.agent_runtime.capability_map.get(capability)
            exists = agent_name is not None
            
            capability_detail = {
                "exists": exists,
                "agent": agent_name,
                "required_params": [],
                "missing_params": [],
                "errors": []
            }
            
            if not exists:
                errors.append(f"Capability '{capability}' not found in any agent")
                capability_detail["errors"].append("Capability not registered")
            else:
                # Get the agent and method
                agent = self.agent_runtime.agents.get(agent_name)
                if agent:
                    # Convert capability name to method name
                    method_name = capability.replace(".", "_")
                    
                    if hasattr(agent, method_name):
                        method = getattr(agent, method_name)
                        
                        # Inspect method signature
                        try:
                            sig = inspect.signature(method)
                            params = sig.parameters
                            
                            # Get required parameters (excluding self, ctx, state)
                            required_params = []
                            for param_name, param in params.items():
                                if param_name in ['self', 'ctx', 'state']:
                                    continue
                                
                                # Check if parameter has no default value (required)
                                if param.default == inspect.Parameter.empty:
                                    required_params.append(param_name)
                                    capability_detail["required_params"].append(param_name)
                            
                            # Check if step provides required parameters
                            step_args = step.get("args", {})
                            
                            # Create a mock state to test argument resolution
                            mock_state = {
                                "ctx": {"portfolio_id": "test", "pricing_pack_id": "test"},
                                "inputs": inputs,
                                "state": {}
                            }
                            
                            # Check each required parameter
                            for param_name in required_params:
                                # Check if parameter is in step args
                                if param_name not in step_args:
                                    # Special cases for common parameters
                                    if param_name == "portfolio_id":
                                        # Could come from ctx or inputs
                                        if "portfolio_id" not in step_args:
                                            warnings.append(
                                                f"Step {step_idx} ({capability}): "
                                                f"parameter '{param_name}' not explicitly provided "
                                                "(uses ctx.portfolio_id or inputs.portfolio_id if available)"
                                            )
                                    else:
                                        capability_detail["missing_params"].append(param_name)
                                        errors.append(
                                            f"Step {step_idx} ({capability}): "
                                            f"required parameter '{param_name}' not provided"
                                        )
                                else:
                                    # Check if the argument references exist
                                    arg_value = step_args[param_name]
                                    if isinstance(arg_value, str) and "{{" in arg_value:
                                        # It's a template reference, validate it
                                        try:
                                            # Extract the reference path
                                            if arg_value.startswith("{{") and arg_value.endswith("}}"):
                                                path = arg_value[2:-2].strip()
                                                parts = path.split(".")
                                                
                                                # Check if it references a previous step result
                                                if parts[0] not in ["ctx", "inputs", "state"]:
                                                    # It's a direct state reference
                                                    # Check if this is from a previous step
                                                    prev_steps = spec["steps"][:step_idx]
                                                    prev_results = [s.get("as", "last") for s in prev_steps]
                                                    if parts[0] not in prev_results:
                                                        warnings.append(
                                                            f"Step {step_idx} ({capability}): "
                                                            f"references '{parts[0]}' which may not be available"
                                                        )
                                        except Exception as e:
                                            warnings.append(
                                                f"Step {step_idx} ({capability}): "
                                                f"could not validate template '{arg_value}': {e}"
                                            )
                        except Exception as e:
                            warnings.append(
                                f"Could not inspect signature for {capability}: {e}"
                            )
                    else:
                        errors.append(
                            f"Agent '{agent_name}' has no method for capability '{capability}'"
                        )
                else:
                    errors.append(f"Agent '{agent_name}' not found in runtime")
            
            capability_details[capability] = capability_detail
        
        # Determine overall validity
        valid = len(errors) == 0
        
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "capabilities": capability_details,
            "pattern": {
                "id": pattern_id,
                "name": spec.get("name", "Unknown"),
                "description": spec.get("description", ""),
                "steps": len(spec.get("steps", []))
            }
        }

    async def run_pattern(
        self,
        pattern_id: str,
        ctx: RequestCtx,
        inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a pattern with given context and inputs.

        Args:
            pattern_id: Pattern ID to execute
            ctx: Immutable request context (reproducibility guarantee)
            inputs: User-provided inputs for pattern

        Returns:
            Dict with data, charts, and trace:
            {
                "data": {...},  # Pattern outputs
                "charts": [...],  # Chart configurations
                "trace": {...}  # Execution trace
            }

        Raises:
            ValueError: If pattern not found or validation fails
            Exception: If capability execution fails
        """
        spec = self.patterns.get(pattern_id)
        if not spec:
            raise ValueError(f"Pattern not found: {pattern_id}")

        logger.info(f"Executing pattern: {pattern_id}")
        logger.info(f"Initial inputs: {inputs}")

        # Perform pre-flight validation (non-blocking, informative only)
        validation_result = self.validate_pattern(pattern_id, inputs)
        if not validation_result["valid"]:
            logger.warning(f"Pattern '{pattern_id}' validation failed (continuing anyway):")
            for error in validation_result["errors"]:
                logger.error(f"  ERROR: {error}")
            for warning in validation_result["warnings"]:
                logger.warning(f"  WARNING: {warning}")
        else:
            logger.info(f"Pattern '{pattern_id}' passed validation")
            if validation_result["warnings"]:
                for warning in validation_result["warnings"]:
                    logger.warning(f"  WARNING: {warning}")

        # Apply defaults from pattern spec
        inputs = self._apply_pattern_defaults(spec, inputs)
        logger.info(f"Inputs after applying defaults: {inputs}")

        # PHASE 2: Validate pattern dependencies before execution
        validation_result = self.validate_pattern_dependencies(pattern_id)
        if not validation_result["valid"]:
            error_msg = "Pattern dependency validation failed:\n" + "\n".join(validation_result["errors"])
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if validation_result["warnings"]:
            for warning in validation_result["warnings"]:
                logger.warning(f"Pattern {pattern_id} validation warning: {warning}")

        # Get metrics registry for pattern-level tracking
        metrics = get_metrics()

        # Start pattern timing
        import time
        pattern_start_time = time.time()
        pattern_status = "success"

        # Initialize execution state
        state = {
            "ctx": ctx.to_dict(),  # Context accessible via {{ctx.foo}}
            "inputs": inputs,       # Inputs accessible via {{inputs.foo}}
        }
        trace = Trace(pattern_id, ctx, agent_runtime=self.agent_runtime)

        # Execute steps with metrics tracking
        try:
            for step_idx, step in enumerate(spec["steps"]):
                capability = step["capability"]
                logger.debug(f"Step {step_idx}: {capability}")

                # Evaluate condition if present
                if "condition" in step:
                    if not self._eval_condition(step["condition"], state):
                        trace.skip_step(capability, "condition_not_met")
                        logger.debug(f"Skipped {capability}: condition not met")
                        continue

                # Resolve template arguments
                try:
                    args = self._resolve_args(step.get("args", {}), state)
                except Exception as e:
                    error_msg = f"Failed to resolve args for {capability}: {e}"
                    logger.error(error_msg)
                    trace.add_error(capability, error_msg)
                    raise ValueError(error_msg)

                # Execute capability
                try:
                    import time
                    start_time = time.time()

                    result = await self.agent_runtime.execute_capability(
                        capability,
                        ctx=ctx,
                        state=state,
                        **args,
                    )

                    duration = time.time() - start_time

                    # Record step duration metrics
                    if metrics:
                        metrics.pattern_step_duration.labels(
                            pattern_id=pattern_id,
                            step_index=str(step_idx),
                            capability=capability,
                        ).observe(duration)

                    # Store result in state
                    result_key = step.get("as", "last")
                    logger.info(f"📦 Storing result from {capability} in state['{result_key}']")
                    logger.info(f"Result type: {type(result)}, is None: {result is None}")
                    
                    # Phase 1: Remove metadata from results (metadata moved to trace only)
                    # Strip _metadata key from dict results before storing
                    cleaned_result = result
                    if isinstance(result, dict) and "_metadata" in result:
                        cleaned_result = {k: v for k, v in result.items() if k != "_metadata"}
                        logger.debug(f"Removed _metadata from {result_key} result (moved to trace)")
                    
                    # Store result directly without smart unwrapping to avoid nested access patterns
                    # Each pattern should explicitly reference the data structure it needs
                    # This prevents double-nesting issues (result.result.data)
                    state[result_key] = cleaned_result
                    
                    logger.info(f"State after storing: keys={list(state.keys())}, '{result_key}' is None: {state.get(result_key) is None}")

                    trace.add_step(capability, result, args, duration)
                    logger.debug(
                        f"Completed {capability} in {duration:.3f}s → {result_key}"
                    )

                except Exception as e:
                    error_msg = f"Capability {capability} failed: {e}"
                    logger.error(error_msg, exc_info=True)
                    trace.add_error(capability, error_msg)
                    raise

        except Exception as e:
            # Pattern failed - record error status
            pattern_status = "error"
            error_msg = f"Pattern execution failed: {e}"
            logger.error(error_msg, exc_info=True)
            trace.add_error("pattern_execution", error_msg)
            raise
        finally:
            # Record pattern-level metrics
            pattern_duration = time.time() - pattern_start_time
            if metrics:
                metrics.record_pattern_execution(pattern_id, pattern_status)
                metrics.api_latency.labels(
                    pattern_id=pattern_id,
                    status=pattern_status,
                ).observe(pattern_duration)

        # Extract outputs
        outputs = {}
        # PHASE 1 FIX: Handle multiple output formats
        # Format 1: List of keys ["perf_metrics", "currency_attr", ...]
        # Format 2: Dict with keys {"perf_metrics": {...}, ...}
        # Format 3: Dict with panels {"panels": [...]} - extract panel IDs and map to step results
        outputs_spec = spec.get("outputs", {})
        
        if isinstance(outputs_spec, list):
            # Format 1: List of keys
            output_keys = outputs_spec
        elif isinstance(outputs_spec, dict):
            if "panels" in outputs_spec:
                # Format 3: Dict with panels - extract panel IDs and map to step results
                # Panels are UI metadata, actual data comes from step results
                # Map panel IDs to step result keys (e.g., "risk_map" -> "cycle_risk_map")
                panels = outputs_spec["panels"]
                output_keys = []
                # Extract panel IDs and try to find corresponding step results
                for panel in panels:
                    panel_id = panel.get("id") if isinstance(panel, dict) else panel
                    if panel_id:
                        # Try panel_id first, then try common variations
                        if panel_id in state:
                            output_keys.append(panel_id)
                        else:
                            # Try to find step result that matches panel
                            # Common pattern: panel_id might be a prefix or suffix of step result
                            for state_key in state.keys():
                                if state_key == panel_id or state_key.endswith(f"_{panel_id}") or state_key.startswith(f"{panel_id}_"):
                                    output_keys.append(state_key)
                                    break
                            else:
                                logger.warning(
                                    f"Panel {panel_id} not found in state for pattern {pattern_id}, "
                                    f"available keys: {list(state.keys())}"
                                )
            else:
                # Format 2: Dict with keys
                output_keys = list(outputs_spec.keys())
        else:
            # Fallback: empty list
            output_keys = []
            logger.warning(
                f"Unexpected outputs format for pattern {pattern_id}: {type(outputs_spec)}"
            )
        
        # Extract outputs from state
        for output_key in output_keys:
            if output_key in state:
                outputs[output_key] = state[output_key]
                logger.debug(f"Added {output_key} to outputs for pattern {pattern_id}")
            else:
                logger.warning(
                    f"Output {output_key} not found in state for pattern {pattern_id}, "
                    f"available keys: {list(state.keys())}"
                )
                # PHASE 1 FIX: Set missing output to None instead of skipping
                # This prevents "No data" errors in UI
                outputs[output_key] = None

        # Special handling for charts (common output key)
        charts = state.get("charts", [])

        logger.info(f"Pattern {pattern_id} completed successfully")

        # Get trace with cache stats before cleanup
        trace_data = trace.serialize()

        # Cleanup request cache after pattern execution
        self.agent_runtime.clear_request_cache(ctx.request_id)

        # Build result
        result = {
            "data": outputs,
            "charts": charts,
            "trace": trace_data,
        }

        # Validate response (Phase 2: Pattern System Refactoring)
        # Non-blocking validation - logs warnings but doesn't fail execution
        try:
            # Flatten outputs for validation (validator expects flat structure)
            validation_data = {**outputs, "_metadata": {"pattern_id": pattern_id}, "_trace": trace_data}
            validated = PatternResponseValidator.validate(pattern_id, validation_data)

            # Check for deprecated field names
            deprecated_warnings = PatternResponseValidator.check_deprecated_fields(outputs)
            if deprecated_warnings:
                logger.warning(
                    f"Pattern {pattern_id} contains deprecated fields:",
                    extra={"warnings": deprecated_warnings}
                )
                for warning in deprecated_warnings:
                    logger.warning(f"  - {warning}")

        except Exception as e:
            # Validation itself should never break execution
            logger.error(f"Pattern validation error (non-blocking): {e}", exc_info=True)

        return result

    def _resolve_args(self, args: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve template arguments.

        Templates:
            {{foo}} - Access state variable (from previous step's "as" key)
            {{ctx.pricing_pack_id}} - Access context field
            {{inputs.symbol}} - Access user input

        Args:
            args: Raw arguments with templates
            state: Current execution state

        Returns:
            Resolved arguments dict
            
        Raises:
            ValueError: If required template variable (e.g., ctx.pricing_pack_id) resolves to None

        Example:
            args = {"positions": "{{positions.positions}}", "pack_id": "{{ctx.pricing_pack_id}}"}
            state = {"positions": {...}, "ctx": {"pricing_pack_id": "20241020_v1"}}
            → {"positions": {...}, "pack_id": "20241020_v1"}
        """
        resolved = {}
        for key, value in args.items():
            resolved_value = self._resolve_value(value, state)
            
            # Validate required template variables (especially ctx.pricing_pack_id)
            if resolved_value is None and isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                template_path = value[2:-2].strip()
                
                # Check if this is a required context variable
                if template_path.startswith("ctx."):
                    # Required context variables that cannot be None
                    required_ctx_vars = ["ctx.pricing_pack_id", "ctx.ledger_commit_hash"]
                    if template_path in required_ctx_vars:
                        raise ValueError(
                            f"Required template variable '{template_path}' resolved to None. "
                            f"Context: pricing_pack_id={state.get('ctx', {}).get('pricing_pack_id')}, "
                            f"ledger_commit_hash={state.get('ctx', {}).get('ledger_commit_hash')}. "
                            f"Must be set in request context before pattern execution."
                        )
            
            resolved[key] = resolved_value
        return resolved

    def _resolve_value(self, value: Any, state: Dict[str, Any]) -> Any:
        """
        Recursively resolve a single value (supports nested dicts/lists).

        Args:
            value: Value to resolve (supports template variables {{...}})
            state: Current execution state

        Returns:
            Resolved value
        """
        # Handle string templates
        if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
            # Extract path: {{positions}} → ["positions"] or {{positions.positions}} → ["positions", "positions"]
            path = value[2:-2].strip().split(".")
            result = state
            for part in path:
                if isinstance(result, dict):
                    result = result.get(part)
                elif hasattr(result, part):
                    result = getattr(result, part)
                else:
                    raise ValueError(
                        f"Cannot resolve template path {value}: {part} not found"
                    )
                # Allow None for optional parameters
                # Don't raise ValueError if result is None - just return None
                # This allows optional fields like custom_shocks to be None
            return result

        # Handle nested dicts
        elif isinstance(value, dict):
            return {k: self._resolve_value(v, state) for k, v in value.items()}

        # Handle lists
        elif isinstance(value, list):
            return [self._resolve_value(item, state) for item in value]

        # Return primitive values as-is
        else:
            return value

    def _eval_condition(self, condition: str, state: Dict[str, Any]) -> bool:
        """
        Safely evaluate simple boolean conditions without using eval().

        Supported conditions:
            - "positions.length > 0" (where positions is a step result key)
            - "inputs.include_charts == true"
            - "ctx.portfolio_id != null"
            - "value >= 100"
            - "status == 'active' and count > 0"

        Args:
            condition: Condition string
            state: Current execution state

        Returns:
            True if condition met, False otherwise
        """
        try:
            # First handle template variables {{...}}
            safe_condition = self._resolve_template_vars(condition, state)
            
            # Now evaluate the resolved condition safely
            return self._safe_evaluate(safe_condition, state)
            
        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False
    
    def _safe_evaluate(self, condition: str, state: Dict[str, Any]) -> bool:
        """
        Safely evaluate boolean conditions without using eval().
        
        Supports operators: ==, !=, <, >, <=, >=, and, or, not, is, in
        Supports literals: true, false, null, numeric values, quoted strings
        Supports path access: positions.length, inputs.portfolio_id, ctx.asof_date
        
        Args:
            condition: Condition string to evaluate
            state: Current execution state containing step results and context
            
        Returns:
            True if condition evaluates to true, False otherwise
            
        Example:
            >>> state = {"positions": [1, 2, 3], "inputs": {"include_charts": True}}
            >>> _safe_evaluate("positions.length > 0", state)
            True
            >>> _safe_evaluate("inputs.include_charts == true", state)
            True
        """
        import operator
        from ast import literal_eval
        
        # Handle simple boolean keywords
        condition = condition.strip()
        if condition.lower() == 'true':
            return True
        if condition.lower() == 'false':
            return False
        
        # Handle 'and' and 'or' operators
        if ' and ' in condition:
            parts = condition.split(' and ')
            return all(self._safe_evaluate(part.strip(), state) for part in parts)
        
        if ' or ' in condition:
            parts = condition.split(' or ')
            return any(self._safe_evaluate(part.strip(), state) for part in parts)
        
        # Handle 'not' operator
        if condition.startswith('not '):
            return not self._safe_evaluate(condition[4:].strip(), state)
        
        # Handle comparison operators
        ops = {
            '==': operator.eq,
            '!=': operator.ne,
            '<=': operator.le,
            '>=': operator.ge,
            '<': operator.lt,
            '>': operator.gt,
            ' is ': operator.is_,
            ' in ': lambda x, y: x in y
        }
        
        for op_str, op_func in ops.items():
            if op_str in condition:
                parts = condition.split(op_str, 1)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    
                    # Get values
                    left_val = self._get_value(left, state)
                    right_val = self._get_value(right, state)
                    
                    # Special handling for null/None comparisons
                    if right_val == 'null' or right_val == 'None':
                        right_val = None
                    
                    try:
                        return op_func(left_val, right_val)
                    except:
                        return False
        
        # If no operator found, try to evaluate as a simple path
        val = self._get_value(condition, state)
        return bool(val)
    
    def _get_value(self, expr: str, state: Dict[str, Any]) -> Any:
        """Get value from expression, handling paths and literals."""
        expr = expr.strip()
        
        # Handle string literals
        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]
        
        # Handle numeric literals
        try:
            if '.' in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass
        
        # Handle boolean literals
        if expr.lower() == 'true':
            return True
        if expr.lower() == 'false':
            return False
        if expr.lower() in ('null', 'none'):
            return None
        
        # Handle paths like "positions.length" or "inputs.portfolio_id"
        if '.' in expr:
            parts = expr.split('.')
            obj = state
            for part in parts:
                # Handle list length
                if part == 'length' and isinstance(obj, list):
                    return len(obj)
                # Handle dictionary access
                elif isinstance(obj, dict):
                    obj = obj.get(part)
                    if obj is None:
                        return None
                else:
                    return None
            return obj
        
        # Simple key lookup
        return state.get(expr)
    
    def _extract_template_references(self, text: str) -> List[str]:
        """
        Extract template references from text.
        
        Args:
            text: Text containing template variables in {{...}} format
        
        Returns:
            List of template reference paths (e.g., ["ctx.portfolio_id", "positions.positions"])
        """
        import re
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, text)
        return [match.strip() for match in matches]
    
    def _validate_template_reference(self, ref: str, defined_outputs: set) -> bool:
        """
        Validate template reference exists in defined outputs.
        
        Args:
            ref: Template reference (e.g., "positions.positions" or "ctx.portfolio_id")
            defined_outputs: Set of defined output keys (e.g., {"ctx", "inputs", "positions"})
        
        Returns:
            True if reference is valid, False otherwise
        """
        # Handle nested references (e.g., "positions.positions")
        parts = ref.split(".")
        first_part = parts[0]
        
        # Special cases: ctx and inputs are always available
        if first_part in ["ctx", "inputs"]:
            return True
        
        # Check if first part exists in defined outputs
        if first_part not in defined_outputs:
            return False
        
        # If nested, basic validation (full validation would require actual state)
        # For now, we just check if the first part exists
        return True
    
    def validate_pattern_dependencies(self, pattern_id: str) -> Dict[str, Any]:
        """
        Validate pattern step dependencies.
        
        Validates that:
        1. All referenced steps exist
        2. No forward references (steps can only reference previous steps)
        3. Template variables resolve correctly
        
        Args:
            pattern_id: Pattern ID to validate
        
        Returns:
            Dict with validation results:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str]
            }
        """
        spec = self.patterns.get(pattern_id)
        if not spec:
            return {
                "valid": False,
                "errors": [f"Pattern '{pattern_id}' not found"],
                "warnings": []
            }
        
        errors = []
        warnings = []
        steps = spec.get("steps", [])
        defined_outputs = set(["ctx", "inputs"])  # Always available
        
        for i, step in enumerate(steps):
            step_name = step.get("as", f"step_{i}")
            capability = step.get("capability", "unknown")
            
            # Track defined outputs (step "as" keys)
            defined_outputs.add(step_name)
            
            # Check template references in args
            args = step.get("args", {})
            for key, value in args.items():
                if isinstance(value, str) and "{{" in value:
                    # Extract template references
                    template_refs = self._extract_template_references(value)
                    for ref in template_refs:
                        # Check if reference exists
                        if not self._validate_template_reference(ref, defined_outputs):
                            errors.append(
                                f"Step {i} ({capability}): "
                                f"Template reference '{{{{ {ref} }}}}' not found. "
                                f"Available: {sorted(list(defined_outputs))}"
                            )
            
            # Check condition template references
            if "condition" in step:
                condition = step["condition"]
                template_refs = self._extract_template_references(condition)
                for ref in template_refs:
                    if not self._validate_template_reference(ref, defined_outputs):
                        errors.append(
                            f"Step {i} condition ({capability}): "
                            f"Template reference '{{{{ {ref} }}}}' not found. "
                            f"Available: {sorted(list(defined_outputs))}"
                        )
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _resolve_template_vars(self, text: str, state: Dict[str, Any]) -> str:
        """
        Replace template variables {{var}} with actual values from execution state.
        
        Supports template syntax: {{path.to.value}}
        - Paths can reference step results: {{positions.positions}}
        - Paths can reference context: {{ctx.portfolio_id}}
        - Paths can reference inputs: {{inputs.asof_date}}
        - Paths can reference nested structures: {{valued_positions.positions[0].symbol}}
        
        Args:
            text: Text containing template variables in {{...}} format
            state: Current execution state containing step results, context, and inputs
            
        Returns:
            Text with template variables replaced by their actual values
            
        Example:
            >>> state = {
            ...     "positions": {"positions": [{"symbol": "AAPL"}]},
            ...     "ctx": {"portfolio_id": "abc-123"},
            ...     "inputs": {"asof_date": "2025-01-01"}
            ... }
            >>> _resolve_template_vars("Portfolio {{ctx.portfolio_id}} on {{inputs.asof_date}}", state)
            'Portfolio abc-123 on 2025-01-01'
        """
        import re
        
        def replace_template(match):
            var_path = match.group(1)
            val = self._get_value(var_path, state)
            # Return the value as a string representation
            if val is None:
                return 'null'
            elif isinstance(val, bool):
                return 'true' if val else 'false'
            elif isinstance(val, str):
                return f'"{val}"'
            else:
                return str(val)
        
        # Replace {{path.to.value}} with resolved values
        return re.sub(r'\{\{([\w.]+)\}\}', replace_template, text)


# ============================================================================
# Example Pattern (for testing)
# ============================================================================

EXAMPLE_PATTERN = {
    "id": "portfolio_overview",
    "name": "Portfolio Overview",
    "description": "Comprehensive portfolio snapshot with performance and attribution",
    "category": "analysis",
    "inputs": {
        "portfolio_id": {"type": "uuid", "required": True}
    },
    "steps": [
        {
            "capability": "ledger.positions",
            "as": "positions",
            "args": {"portfolio_id": "{{inputs.portfolio_id}}"}
        },
        {
            "capability": "pricing.apply_pack",
            "as": "valued_positions",
            "args": {
                "positions": "{{positions.positions}}",
                "pack_id": "{{ctx.pricing_pack_id}}"
            }
        },
        {
            "capability": "metrics.compute_twr",
            "as": "perf_metrics",
            "args": {
                "positions": "{{valued_positions.positions}}",
                "pack_id": "{{ctx.pricing_pack_id}}"
            }
        },
        {
            "capability": "charts.overview",
            "as": "charts",
            "args": {
                "positions": "{{valued_positions.positions}}",
                "metrics": "{{perf_metrics}}"
            }
        }
    ],
    "outputs": ["perf_metrics", "valued_positions", "charts"]
}
