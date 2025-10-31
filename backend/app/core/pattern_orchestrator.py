"""
DawsOS Pattern Orchestrator

Purpose: Load and execute JSON patterns with template substitution and tracing
Updated: 2025-10-21
Priority: P0 (Critical for pattern-driven execution)

Features:
    - Load patterns from patterns/ directory
    - Execute DAG steps sequentially (parallel support in S2)
    - Template substitution ({{state.foo}}, {{ctx.bar}}, {{inputs.baz}})
    - Build execution trace with agents_used, capabilities_used, sources
    - Per-panel staleness tracking
    - Conditional step execution
    - Redis caching for intermediate results

Usage:
    orchestrator = PatternOrchestrator(agent_runtime, db, redis)
    result = await orchestrator.run_pattern("portfolio_overview", ctx, inputs)
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.types import RequestCtx
from observability.metrics import get_metrics

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

        # Extract metadata from result if available
        if hasattr(result, "__metadata__"):
            meta = result.__metadata__
            if hasattr(meta, "agent_name") and meta.agent_name:
                self.agents_used.add(meta.agent_name)
            if hasattr(meta, "source") and meta.source:
                self.sources.add(meta.source)
            if hasattr(meta, "asof") and meta.asof:
                self.per_panel_staleness.append({
                    "capability": capability,
                    "asof": str(meta.asof),
                    "ttl": getattr(meta, "ttl", None),
                })

        self.steps.append({
            "capability": capability,
            "args": args,
            "success": True,
            "duration_seconds": duration_seconds,
        })

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
            Dict with pattern_id, pricing_pack_id, ledger_commit_hash, agents, capabilities, sources, steps, cache_stats
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
        4. Resolve template arguments ({{state.foo}}, {{ctx.bar}})
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

                self.patterns[spec["id"]] = spec
                pattern_count += 1
                logger.debug(f"Loaded pattern: {spec['id']} from {pattern_file}")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse pattern {pattern_file}: {e}")
            except Exception as e:
                logger.error(f"Failed to load pattern {pattern_file}: {e}")

        logger.info(f"Loaded {pattern_count} patterns from {patterns_dir}")

    def list_patterns(self) -> List[Dict[str, Any]]:
        """
        Get list of all loaded patterns.

        Returns:
            List of pattern metadata dicts
        """
        return [
            {
                "id": spec["id"],
                "name": spec["name"],
                "description": spec.get("description", ""),
                "category": spec.get("category", "unknown"),
            }
            for spec in self.patterns.values()
        ]

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
                    state[result_key] = result
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
        # Handle outputs as either dict (keys) or list (backward compatibility)
        outputs_spec = spec.get("outputs", {})
        if isinstance(outputs_spec, dict):
            output_keys = list(outputs_spec.keys())
        else:
            output_keys = outputs_spec
        
        # Debug logging for macro pattern issue
        if pattern_id == "macro_cycles_overview":
            logger.info(f"DEBUG: outputs_spec type: {type(outputs_spec)}, value: {outputs_spec}")
            logger.info(f"DEBUG: output_keys: {output_keys}")
            logger.info(f"DEBUG: state keys: {list(state.keys())}")
            
        for output_key in output_keys:
            if output_key in state:
                outputs[output_key] = state[output_key]
                if pattern_id == "macro_cycles_overview":
                    logger.info(f"DEBUG: Added {output_key} to outputs")
            else:
                logger.warning(
                    f"Output {output_key} not found in state for pattern {pattern_id}"
                )

        # Special handling for charts (common output key)
        charts = state.get("charts", [])

        logger.info(f"Pattern {pattern_id} completed successfully")

        # Get trace with cache stats before cleanup
        trace_data = trace.serialize()

        # Cleanup request cache after pattern execution
        self.agent_runtime.clear_request_cache(ctx.request_id)

        return {
            "data": outputs,
            "charts": charts,
            "trace": trace_data,
        }

    def _resolve_args(self, args: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve template arguments.

        Templates:
            {{state.foo}} - Access state variable
            {{ctx.pricing_pack_id}} - Access context field
            {{inputs.symbol}} - Access user input

        Args:
            args: Raw arguments with templates
            state: Current execution state

        Returns:
            Resolved arguments dict

        Example:
            args = {"positions": "{{state.positions}}", "pack_id": "{{ctx.pricing_pack_id}}"}
            state = {"positions": [...], "ctx": {"pricing_pack_id": "20241020_v1"}}
            → {"positions": [...], "pack_id": "20241020_v1"}
        """
        resolved = {}
        for key, value in args.items():
            resolved[key] = self._resolve_value(value, state)
        return resolved

    def _resolve_value(self, value: Any, state: Dict[str, Any]) -> Any:
        """
        Recursively resolve a single value (supports nested dicts/lists).

        Args:
            value: Value to resolve (may contain templates)
            state: Current execution state

        Returns:
            Resolved value
        """
        # Handle string templates
        if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
            # Extract path: {{state.positions}} → ["state", "positions"]
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
                if result is None:
                    raise ValueError(f"Template path {value} resolved to None")
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
        Evaluate simple boolean conditions.

        Supported conditions:
            - "state.positions.length > 0"
            - "inputs.include_charts == true"
            - "ctx.portfolio_id != null"

        Args:
            condition: Condition string
            state: Current execution state

        Returns:
            True if condition met, False otherwise

        Note:
            For S1, we use simple eval(). In production, use a safe expression
            evaluator like simpleeval or ast.literal_eval with restricted namespace.
        """
        try:
            # Replace template syntax for eval
            # {{state.foo}} → state["foo"]
            safe_condition = re.sub(
                r'\{\{(\w+)\.(\w+)\}\}',
                r'\1["\2"]',
                condition
            )

            # Simple eval (TODO: Replace with safe evaluator in production)
            result = eval(safe_condition, {"__builtins__": {}}, state)
            return bool(result)
        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False


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
                "positions": "{{state.positions}}",
                "pack_id": "{{ctx.pricing_pack_id}}"
            }
        },
        {
            "capability": "metrics.compute_twr",
            "as": "perf_metrics",
            "args": {
                "positions": "{{state.valued_positions}}",
                "pack_id": "{{ctx.pricing_pack_id}}"
            }
        },
        {
            "capability": "charts.overview",
            "as": "charts",
            "args": {
                "positions": "{{state.valued_positions}}",
                "metrics": "{{state.perf_metrics}}"
            }
        }
    ],
    "outputs": ["perf_metrics", "valued_positions", "charts"]
}
