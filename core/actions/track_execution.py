#!/usr/bin/env python3
"""
Track Execution Action - Track execution metrics for telemetry

Records execution metrics including timing, success status, and agent usage.
Stores metrics in runtime for observability and analysis.

Priority: 📊 Telemetry - Execution tracking and observability
"""

from datetime import datetime
from . import ActionHandler, ParamsDict, ContextDict, OutputsDict, ResultDict


class TrackExecutionAction(ActionHandler):
    """
    Track execution metrics for telemetry.

    Records:
    - Success status
    - Duration (if start_time provided)
    - Pattern ID
    - Agent used
    - Errors
    - Graph storage status

    Stores metrics in runtime.track_execution() if available.

    Pattern Example:
        {
            "action": "track_execution",
            "result": "{final_result}",
            "start_time": "2025-10-06T15:00:00"
        }
    """

    @property
    def action_name(self) -> str:
        return "track_execution"

    def execute(self, params: ParamsDict, context: ContextDict, outputs: OutputsDict) -> ResultDict:
        """
        Track execution metrics.

        Args:
            params: Must contain 'result', optional 'start_time'
            context: Current execution context (contains pattern_id)
            outputs: Previous step outputs

        Returns:
            Metrics dictionary with success, duration, timestamp, etc.
        """
        result = params.get('result', {})
        start_time = params.get('start_time')

        # Calculate duration
        end_time = datetime.now()
        duration_ms = None

        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time)
                duration_ms = (end_time - start_dt).total_seconds() * 1000
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Could not calculate duration: {e}")

        # Build metrics
        metrics = {
            'success': result.get('success', True) if isinstance(result, dict) else True,
            'error': result.get('error') if isinstance(result, dict) else None,
            'duration_ms': duration_ms,
            'timestamp': end_time.isoformat(),
            'pattern_id': context.get('pattern_id'),
            'agent_used': result.get('agent') if isinstance(result, dict) else None,
            'graph_stored': result.get('graph_stored', False) if isinstance(result, dict) else False
        }

        # Store in runtime if available
        if self.runtime and hasattr(self.runtime, 'track_execution'):
            try:
                self.runtime.track_execution(metrics)
                self.logger.debug("Metrics stored in runtime")
            except Exception as e:
                self.logger.warning(f"Could not store metrics in runtime: {e}")

        # Log for observability
        if duration_ms is not None:
            self.logger.info(
                f"Execution tracked: {metrics['pattern_id']} "
                f"({duration_ms:.1f}ms, success={metrics['success']})"
            )
        else:
            self.logger.info(
                f"Execution tracked: {metrics['pattern_id']} "
                f"(success={metrics['success']})"
            )

        return metrics
