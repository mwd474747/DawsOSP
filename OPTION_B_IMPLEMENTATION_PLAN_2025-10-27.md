# Option B Implementation Plan: Complete P0 (Metrics + Alerts)
**Date**: October 27, 2025
**Scope**: Phase 1 (Metrics Recording) + Phase 2 (Alert Delivery Integration)
**Estimated Effort**: 17 hours (~2 days)
**Priority**: P0 (Critical for production readiness)

---

## Executive Summary

This document provides a detailed, code-level implementation plan for completing P0 observability and alerting work. Based on deep-dive analysis, we discovered that **NotificationService is fully implemented**, reducing Phase 2 effort significantly.

**Goal**: Enable full observability and complete end-to-end alerting in 17 hours.

**Phases**:
1. **Phase 1**: Complete Metrics Recording (5 hours)
2. **Phase 2**: Alert Delivery Integration (12 hours)

---

## Phase 1: Complete Metrics Recording (5 hours)

### Overview

**Current State**: Metrics infrastructure exists but recording calls are missing
**Goal**: Add metrics recording at pattern and agent level
**Effort**: 5 hours

**Files to Modify**:
- `backend/app/core/pattern_orchestrator.py` (add pattern metrics)
- `backend/app/core/agent_runtime.py` (add agent metrics)
- `backend/tests/unit/test_metrics_recording.py` (new file)

---

### Task 1.1: Pattern Orchestrator Metrics (2 hours)

**File**: `backend/app/core/pattern_orchestrator.py`

#### Integration Points

**Location 1: Pattern execution start/end** (lines 252-369)
```python
async def run_pattern(
    self,
    pattern_id: str,
    ctx: RequestCtx,
    inputs: Dict[str, Any],
) -> Dict[str, Any]:
```

**Changes Required**:
1. Import metrics at top of file:
   ```python
   from backend.observability.metrics import get_metrics
   ```

2. Get metrics registry at start of `run_pattern()`:
   ```python
   # Get metrics registry
   metrics = get_metrics()
   ```

3. Wrap pattern execution with metrics:
   ```python
   # Start metrics tracking
   import time
   pattern_start = time.time()
   pattern_status = "success"

   try:
       # ... existing pattern execution code ...

   except Exception as e:
       pattern_status = "error"
       raise
   finally:
       # Record pattern execution
       if metrics:
           pattern_duration = time.time() - pattern_start
           metrics.record_pattern_execution(pattern_id, pattern_status)

           # Record total pattern latency
           metrics.api_latency.labels(
               pattern_id=pattern_id,
               status=pattern_status,
           ).observe(pattern_duration)
   ```

**Location 2: Pattern step execution** (lines 312-342)

**Current Code**:
```python
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

    # ... store result in state ...

    trace.add_step(capability, result, args, duration)
```

**Add After** `duration = time.time() - start_time`:
```python
    # Record step duration metrics
    if metrics:
        metrics.pattern_step_duration.labels(
            pattern_id=pattern_id,
            step_index=str(step_idx),
            capability=capability,
        ).observe(duration)
```

**Complete Implementation**:
```python
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
    metrics = get_metrics()
    if metrics:
        metrics.pattern_step_duration.labels(
            pattern_id=pattern_id,
            step_index=str(step_idx),
            capability=capability,
        ).observe(duration)

    # Store result in state
    result_key = step.get("as", "last")
    logger.info(f"📦 Storing result from {capability} in state['{result_key}']")
    state[result_key] = result

    trace.add_step(capability, result, args, duration)
    logger.debug(
        f"Completed {capability} in {duration:.3f}s → {result_key}"
    )

except Exception as e:
    error_msg = f"Capability {capability} failed: {e}"
    logger.error(error_msg, exc_info=True)
    trace.add_error(capability, error_msg)
    raise
```

**Verification**:
```bash
# After implementation, verify metrics are recorded
curl http://localhost:8000/metrics | grep pattern_executions
curl http://localhost:8000/metrics | grep pattern_step_duration
```

---

### Task 1.2: Agent Runtime Metrics (2 hours)

**File**: `backend/app/core/agent_runtime.py`

#### Integration Points

**Location 1: Agent capability execution** (lines 410-465)

**Current Code**:
```python
async def execute_capability(
    self,
    capability: str,
    ctx: RequestCtx,
    state: Dict[str, Any],
    **kwargs,
) -> Any:
    # ... agent selection logic ...

    agent = self.agents[agent_name]

    # ... circuit breaker check ...
    # ... cache check ...

    # Execute capability (cache miss)
    try:
        result = await agent.execute(capability, ctx, state, **kwargs)

        # Cache the result
        self._set_cached_result(ctx.request_id, cache_key, result)

        self.circuit_breaker.record_success(agent_name)
        return result

    except Exception as e:
        self.circuit_breaker.record_failure(agent_name)
        logger.error(...)
        raise
```

**Changes Required**:

1. Import metrics at top of file:
   ```python
   from backend.observability.metrics import get_metrics
   ```

2. Wrap agent execution with metrics timing:
   ```python
   # Execute capability (cache miss)
   metrics = get_metrics()

   try:
       logger.debug(
           f"Routing {capability} to {agent_name} "
           f"(ctx.pricing_pack_id={ctx.pricing_pack_id})"
       )

       # Time agent execution
       import time
       agent_start = time.time()
       agent_status = "success"

       try:
           result = await agent.execute(capability, ctx, state, **kwargs)
       except Exception as e:
           agent_status = "error"
           raise
       finally:
           # Record agent metrics
           agent_duration = time.time() - agent_start
           if metrics:
               metrics.agent_invocations.labels(
                   agent_name=agent_name,
                   capability=capability,
                   status=agent_status,
               ).inc()

               metrics.agent_latency.labels(
                   agent_name=agent_name,
                   capability=capability,
               ).observe(agent_duration)

       # Add attributions if rights enforcement enabled
       if self.enable_rights_enforcement and self._attribution_manager:
           result = self._add_attributions(result)

       # Cache the result
       self._set_cached_result(ctx.request_id, cache_key, result)

       self.circuit_breaker.record_success(agent_name)
       return result

   except Exception as e:
       self.circuit_breaker.record_failure(agent_name)
       logger.error(
           f"Capability {capability} failed in {agent_name}: {e}",
           exc_info=True,
       )
       raise
   ```

**Location 2: Circuit Breaker State Changes** (lines 456, 460)

**Current Code**:
```python
self.circuit_breaker.record_success(agent_name)
# ...
self.circuit_breaker.record_failure(agent_name)
```

**Add After** each circuit breaker state change:
```python
# Record success
self.circuit_breaker.record_success(agent_name)

# Record circuit breaker state in metrics
metrics = get_metrics()
if metrics:
    cb_status = self.circuit_breaker.get_status(agent_name)
    state = cb_status.get("state", "CLOSED")
    metrics.record_circuit_breaker_state(agent_name, state)
```

```python
# Record failure
self.circuit_breaker.record_failure(agent_name)

# Record circuit breaker state in metrics
metrics = get_metrics()
if metrics:
    cb_status = self.circuit_breaker.get_status(agent_name)
    state = cb_status.get("state", "CLOSED")
    metrics.record_circuit_breaker_state(agent_name, state)
```

**Verification**:
```bash
# After implementation, verify metrics are recorded
curl http://localhost:8000/metrics | grep agent_invocations
curl http://localhost:8000/metrics | grep agent_latency
curl http://localhost:8000/metrics | grep circuit_breaker_state
```

---

### Task 1.3: Testing (1 hour)

**File**: `backend/tests/unit/test_metrics_recording.py` (new)

**Test Cases**:

```python
"""
Unit tests for metrics recording in pattern orchestrator and agent runtime.

Purpose: Verify metrics are correctly recorded during pattern execution
Updated: 2025-10-27
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from backend.app.core.pattern_orchestrator import PatternOrchestrator
from backend.app.core.agent_runtime import AgentRuntime
from backend.app.core.types import RequestCtx
from backend.observability.metrics import MetricsRegistry


@pytest.fixture
def mock_metrics():
    """Mock metrics registry."""
    metrics = Mock(spec=MetricsRegistry)
    metrics.pattern_executions = Mock()
    metrics.pattern_executions.labels = Mock(return_value=Mock(inc=Mock()))
    metrics.pattern_step_duration = Mock()
    metrics.pattern_step_duration.labels = Mock(return_value=Mock(observe=Mock()))
    metrics.agent_invocations = Mock()
    metrics.agent_invocations.labels = Mock(return_value=Mock(inc=Mock()))
    metrics.agent_latency = Mock()
    metrics.agent_latency.labels = Mock(return_value=Mock(observe=Mock()))
    metrics.api_latency = Mock()
    metrics.api_latency.labels = Mock(return_value=Mock(observe=Mock()))
    metrics.record_pattern_execution = Mock()
    metrics.record_circuit_breaker_state = Mock()
    return metrics


@pytest.mark.asyncio
async def test_pattern_execution_metrics_recorded(mock_metrics):
    """Test that pattern execution metrics are recorded."""
    # Setup
    with patch('backend.observability.metrics.get_metrics', return_value=mock_metrics):
        orchestrator = PatternOrchestrator(agent_runtime=Mock())

        # Mock pattern
        orchestrator.patterns = {
            "test_pattern": {
                "id": "test_pattern",
                "steps": [
                    {"capability": "test.capability", "args": {}, "as": "result"}
                ],
                "outputs": ["result"],
            }
        }

        # Mock agent runtime
        orchestrator.agent_runtime.execute_capability = AsyncMock(return_value={"data": "test"})
        orchestrator.agent_runtime.get_cache_stats = Mock(return_value={"hits": 0, "misses": 1})
        orchestrator.agent_runtime.clear_request_cache = Mock()

        # Execute pattern
        ctx = RequestCtx(
            request_id="test-request",
            user_id="test-user",
            user_role="user",
            portfolio_id="test-portfolio",
            pricing_pack_id="PP_2025-10-21",
            ledger_commit_hash="abc123",
            trace_id="trace-123",
        )

        result = await orchestrator.run_pattern("test_pattern", ctx, {})

        # Verify metrics recorded
        assert mock_metrics.record_pattern_execution.called
        assert mock_metrics.api_latency.labels.called
        assert mock_metrics.pattern_step_duration.labels.called


@pytest.mark.asyncio
async def test_pattern_step_duration_recorded(mock_metrics):
    """Test that individual step durations are recorded."""
    with patch('backend.observability.metrics.get_metrics', return_value=mock_metrics):
        orchestrator = PatternOrchestrator(agent_runtime=Mock())

        # Mock multi-step pattern
        orchestrator.patterns = {
            "multi_step": {
                "id": "multi_step",
                "steps": [
                    {"capability": "step1", "args": {}, "as": "result1"},
                    {"capability": "step2", "args": {}, "as": "result2"},
                ],
                "outputs": ["result1", "result2"],
            }
        }

        orchestrator.agent_runtime.execute_capability = AsyncMock(return_value={"data": "test"})
        orchestrator.agent_runtime.get_cache_stats = Mock(return_value={"hits": 0, "misses": 2})
        orchestrator.agent_runtime.clear_request_cache = Mock()

        ctx = RequestCtx(
            request_id="test-request",
            user_id="test-user",
            user_role="user",
            portfolio_id="test-portfolio",
            pricing_pack_id="PP_2025-10-21",
            ledger_commit_hash="abc123",
            trace_id="trace-123",
        )

        result = await orchestrator.run_pattern("multi_step", ctx, {})

        # Verify step duration recorded for each step
        assert mock_metrics.pattern_step_duration.labels.call_count == 2

        # Verify labels include pattern_id, step_index, capability
        calls = mock_metrics.pattern_step_duration.labels.call_args_list
        assert calls[0][1]["pattern_id"] == "multi_step"
        assert calls[0][1]["step_index"] == "0"
        assert calls[0][1]["capability"] == "step1"
        assert calls[1][1]["step_index"] == "1"
        assert calls[1][1]["capability"] == "step2"


@pytest.mark.asyncio
async def test_agent_invocation_metrics_recorded(mock_metrics):
    """Test that agent invocation metrics are recorded."""
    with patch('backend.observability.metrics.get_metrics', return_value=mock_metrics):
        # Setup agent runtime
        runtime = AgentRuntime()

        # Register mock agent
        mock_agent = Mock()
        mock_agent.get_capabilities = Mock(return_value=["test.capability"])
        mock_agent.execute = AsyncMock(return_value={"data": "test"})
        runtime.register_agent("test_agent", mock_agent)

        # Execute capability
        ctx = RequestCtx(
            request_id="test-request",
            user_id="test-user",
            user_role="user",
            portfolio_id="test-portfolio",
            pricing_pack_id="PP_2025-10-21",
            ledger_commit_hash="abc123",
            trace_id="trace-123",
        )

        result = await runtime.execute_capability("test.capability", ctx, {})

        # Verify agent invocation metrics recorded
        assert mock_metrics.agent_invocations.labels.called
        assert mock_metrics.agent_latency.labels.called

        # Verify labels
        invocation_call = mock_metrics.agent_invocations.labels.call_args
        assert invocation_call[1]["agent_name"] == "test_agent"
        assert invocation_call[1]["capability"] == "test.capability"
        assert invocation_call[1]["status"] == "success"


@pytest.mark.asyncio
async def test_circuit_breaker_state_metrics_recorded(mock_metrics):
    """Test that circuit breaker state changes are recorded in metrics."""
    with patch('backend.observability.metrics.get_metrics', return_value=mock_metrics):
        runtime = AgentRuntime()

        # Register failing agent
        mock_agent = Mock()
        mock_agent.get_capabilities = Mock(return_value=["fail.capability"])
        mock_agent.execute = AsyncMock(side_effect=Exception("Agent failure"))
        runtime.register_agent("fail_agent", mock_agent)

        ctx = RequestCtx(
            request_id="test-request",
            user_id="test-user",
            user_role="user",
            portfolio_id="test-portfolio",
            pricing_pack_id="PP_2025-10-21",
            ledger_commit_hash="abc123",
            trace_id="trace-123",
        )

        # Attempt to execute (will fail)
        with pytest.raises(Exception):
            await runtime.execute_capability("fail.capability", ctx, {})

        # Verify circuit breaker state metric recorded
        assert mock_metrics.record_circuit_breaker_state.called
        call_args = mock_metrics.record_circuit_breaker_state.call_args
        assert call_args[0][0] == "fail_agent"  # agent_name


@pytest.mark.asyncio
async def test_pattern_error_metrics_recorded(mock_metrics):
    """Test that pattern errors are recorded with error status."""
    with patch('backend.observability.metrics.get_metrics', return_value=mock_metrics):
        orchestrator = PatternOrchestrator(agent_runtime=Mock())

        orchestrator.patterns = {
            "error_pattern": {
                "id": "error_pattern",
                "steps": [
                    {"capability": "fail.capability", "args": {}, "as": "result"}
                ],
                "outputs": ["result"],
            }
        }

        # Mock failing capability
        orchestrator.agent_runtime.execute_capability = AsyncMock(
            side_effect=Exception("Capability failed")
        )
        orchestrator.agent_runtime.get_cache_stats = Mock(return_value={"hits": 0, "misses": 0})
        orchestrator.agent_runtime.clear_request_cache = Mock()

        ctx = RequestCtx(
            request_id="test-request",
            user_id="test-user",
            user_role="user",
            portfolio_id="test-portfolio",
            pricing_pack_id="PP_2025-10-21",
            ledger_commit_hash="abc123",
            trace_id="trace-123",
        )

        # Execute pattern (will fail)
        with pytest.raises(Exception):
            await orchestrator.run_pattern("error_pattern", ctx, {})

        # Verify error status recorded
        assert mock_metrics.record_pattern_execution.called
        call_args = mock_metrics.record_pattern_execution.call_args
        assert call_args[0][0] == "error_pattern"  # pattern_id
        assert call_args[0][1] == "error"  # status
```

**Run Tests**:
```bash
pytest backend/tests/unit/test_metrics_recording.py -v
```

**Expected Output**:
```
test_metrics_recording.py::test_pattern_execution_metrics_recorded PASSED
test_metrics_recording.py::test_pattern_step_duration_recorded PASSED
test_metrics_recording.py::test_agent_invocation_metrics_recorded PASSED
test_metrics_recording.py::test_circuit_breaker_state_metrics_recorded PASSED
test_metrics_recording.py::test_pattern_error_metrics_recorded PASSED

============================== 5 passed in 0.5s ==============================
```

---

### Phase 1 Summary

**Deliverables**:
- ✅ Pattern execution metrics recorded (pattern_executions, api_latency)
- ✅ Pattern step metrics recorded (pattern_step_duration)
- ✅ Agent invocation metrics recorded (agent_invocations, agent_latency)
- ✅ Circuit breaker metrics recorded (circuit_breaker_state)
- ✅ 5 unit tests passing

**Verification Checklist**:
- [ ] `/metrics` endpoint includes `pattern_executions_total`
- [ ] `/metrics` endpoint includes `pattern_step_duration_seconds`
- [ ] `/metrics` endpoint includes `agent_invocations_total`
- [ ] `/metrics` endpoint includes `agent_latency_seconds`
- [ ] `/metrics` endpoint includes `circuit_breaker_state`
- [ ] All 5 unit tests passing
- [ ] Pattern execution records success/error status
- [ ] Step duration includes pattern_id, step_index, capability labels
- [ ] Agent metrics include agent_name, capability, status labels

**Time Estimate**: 5 hours
- Task 1.1: 2 hours
- Task 1.2: 2 hours
- Task 1.3: 1 hour

---

## Phase 2: Alert Delivery Integration (12 hours)

### Overview

**Current State**: AlertService and NotificationService both exist but not wired together
**Goal**: Complete end-to-end alerting (evaluate → deliver → notification)
**Effort**: 12 hours

**Key Discovery**: NotificationService is FULLY IMPLEMENTED!
- ✅ Email delivery (SMTP + AWS SES)
- ✅ In-app notification creation
- ✅ Deduplication logic
- ✅ User email lookup

**Files to Modify**:
- `backend/app/services/alerts.py` (add delivery integration)
- `backend/app/services/alert_delivery.py` (new - DLQ/retry wrapper)
- `backend/jobs/alert_retry_worker.py` (new - retry scheduler)
- `backend/db/schema/alerts.sql` (add channels column)
- `backend/tests/unit/test_alert_delivery.py` (new)
- `backend/tests/integration/test_alerts_e2e.py` (new)

---

### Task 2.1: AlertService Delivery Integration (2 hours)

**File**: `backend/app/services/alerts.py`

**Goal**: Add `deliver_alert()` method that calls NotificationService

#### Implementation

**Add Import** at top of file:
```python
from backend.app.services.notifications import NotificationService
```

**Add Method** to `AlertService` class (after `should_trigger` method):

```python
async def deliver_alert(
    self,
    alert: Dict[str, Any],
    user_id: str,
    message: str,
) -> bool:
    """
    Deliver alert to user via configured channels.

    Args:
        alert: Alert configuration dict (includes id, name, condition, channels)
        user_id: User UUID
        message: Alert message to deliver

    Returns:
        True if delivery succeeded, False otherwise

    Raises:
        Exception: If delivery fails (caller should handle DLQ)
    """
    alert_id = alert.get("id")
    alert_name = alert.get("name", "Alert")
    channels = alert.get("channels", {"inapp": True, "email": False})

    logger.info(
        f"Delivering alert {alert_id} to user {user_id} "
        f"(channels: {channels})"
    )

    # Get notification service
    notification_service = NotificationService(use_db=self.use_db)

    # Send notification
    try:
        success = await notification_service.send_notification(
            user_id=user_id,
            alert_id=alert_id,
            message=message,
            channels=channels,
            alert_name=alert_name,
        )

        if success:
            logger.info(f"Alert {alert_id} delivered successfully to user {user_id}")
        else:
            logger.warning(
                f"Alert {alert_id} not delivered (deduplication or channel unavailable)"
            )

        return success

    except Exception as e:
        logger.error(f"Failed to deliver alert {alert_id}: {e}", exc_info=True)
        raise
```

**Update `should_trigger` Method** to include delivery hint (optional):

Add to docstring:
```python
"""
Check if alert should trigger.

After this returns True, caller should:
1. Call deliver_alert() to send notification
2. Update last_fired_at timestamp in database
3. Handle DLQ if delivery fails

...
"""
```

**Usage Example**:
```python
# In alert evaluation loop
alert = {"id": "alert-123", "name": "VIX Alert", "condition_json": {...}, ...}
ctx = {"asof_date": date.today()}

# Evaluate condition
if await alert_service.evaluate_condition(alert["condition_json"], ctx):
    # Check cooldown
    if await alert_service.should_trigger(alert, ctx):
        # Deliver alert
        message = "VIX exceeded 30 (current: 32.5)"
        try:
            success = await alert_service.deliver_alert(alert, user_id, message)
            if success:
                # Update last_fired_at in database
                await update_alert_last_fired(alert["id"], datetime.utcnow())
        except Exception as e:
            # Push to DLQ for retry
            await push_to_dlq(alert, error=str(e))
```

---

### Task 2.2: Alert Delivery Tracking (2 hours)

**File**: `backend/app/services/alert_delivery.py` (new)

**Goal**: Track deliveries in `alert_deliveries` table for additional dedup layer

#### Implementation

```python
"""
Alert Delivery Tracking Service

Purpose: Track alert deliveries and manage DLQ for failed alerts
Updated: 2025-10-27
Priority: P0 (Phase 2 Task 2)

Features:
    - Delivery tracking (alert_deliveries table)
    - Content-based deduplication (MD5 hash)
    - DLQ insertion for failed deliveries
    - Retry scheduling

Usage:
    from backend.app.services.alert_delivery import AlertDeliveryService

    delivery_svc = AlertDeliveryService()

    # Track successful delivery
    await delivery_svc.track_delivery(
        alert_id="alert-123",
        alert_data={"condition": {...}, "message": "..."},
        delivery_methods=["inapp", "email"],
    )

    # Push to DLQ on failure
    await delivery_svc.push_to_dlq(
        alert_id="alert-123",
        alert_data={"condition": {...}},
        error_message="SMTP connection failed",
    )
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

logger = logging.getLogger("DawsOS.AlertDelivery")


class AlertDeliveryService:
    """
    Alert delivery tracking service.

    Tracks successful deliveries and manages DLQ for failures.
    """

    def __init__(self, use_db: bool = True):
        """
        Initialize alert delivery service.

        Args:
            use_db: If True, use real database. If False, use stubs for testing.
        """
        self.use_db = use_db

        if use_db:
            try:
                from backend.app.db.connection import execute_query_one, execute_statement

                self.execute_query_one = execute_query_one
                self.execute_statement = execute_statement
                logger.info("AlertDeliveryService initialized with database integration")

            except Exception as e:
                logger.warning(
                    f"Failed to initialize database connections: {e}. "
                    "Falling back to stub mode."
                )
                self.use_db = False
        else:
            logger.info("AlertDeliveryService initialized in stub mode")

    def compute_content_hash(self, alert_data: Dict[str, Any]) -> str:
        """
        Compute MD5 hash of alert content for deduplication.

        Args:
            alert_data: Alert data dict

        Returns:
            MD5 hash (hex string)
        """
        # Sort keys for consistent hashing
        content_json = json.dumps(alert_data, sort_keys=True, default=str)
        return hashlib.md5(content_json.encode()).hexdigest()

    async def check_duplicate_delivery(
        self,
        alert_id: str,
        content_hash: str,
        lookback_hours: int = 24,
    ) -> bool:
        """
        Check if alert with same content was recently delivered.

        Args:
            alert_id: Alert ID
            content_hash: Content hash (MD5)
            lookback_hours: How far back to check (default: 24 hours)

        Returns:
            True if duplicate found, False otherwise
        """
        if not self.use_db:
            return False  # Stub: no duplicates

        query = """
            SELECT id
            FROM alert_deliveries
            WHERE alert_id = $1
              AND content_hash = $2
              AND delivered_at > NOW() - INTERVAL '%s hours'
            LIMIT 1
        """ % lookback_hours

        try:
            row = await self.execute_query_one(query, alert_id, content_hash)
            if row:
                logger.debug(
                    f"Duplicate delivery detected for alert {alert_id} "
                    f"(content_hash: {content_hash})"
                )
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to check duplicate delivery: {e}")
            # On error, allow delivery (fail open)
            return False

    async def track_delivery(
        self,
        alert_id: str,
        alert_data: Dict[str, Any],
        delivery_methods: List[str],
    ) -> str:
        """
        Track successful alert delivery.

        Args:
            alert_id: Alert ID
            alert_data: Alert data (condition, message, etc.)
            delivery_methods: List of delivery methods used (e.g., ["inapp", "email"])

        Returns:
            Delivery record ID
        """
        if not self.use_db:
            return "stub-delivery-id"

        # Compute content hash
        content_hash = self.compute_content_hash(alert_data)

        # Insert into alert_deliveries
        query = """
            INSERT INTO alert_deliveries (
                alert_id,
                content_hash,
                delivery_methods,
                delivered_at
            ) VALUES (
                $1,
                $2,
                $3::jsonb,
                NOW()
            )
            RETURNING id
        """

        try:
            row = await self.execute_query_one(
                query,
                alert_id,
                content_hash,
                json.dumps(delivery_methods),
            )

            delivery_id = str(row["id"])
            logger.info(
                f"Tracked delivery for alert {alert_id} "
                f"(delivery_id: {delivery_id}, methods: {delivery_methods})"
            )
            return delivery_id

        except Exception as e:
            logger.error(f"Failed to track delivery: {e}")
            raise

    async def push_to_dlq(
        self,
        alert_id: str,
        alert_data: Dict[str, Any],
        error_message: str,
    ) -> str:
        """
        Push failed alert to Dead Letter Queue.

        Args:
            alert_id: Alert ID
            alert_data: Alert data (condition, message, etc.)
            error_message: Error that caused failure

        Returns:
            DLQ record ID
        """
        if not self.use_db:
            logger.warning(f"DLQ (stub): alert {alert_id} failed: {error_message}")
            return "stub-dlq-id"

        # Insert into alert_dlq
        query = """
            INSERT INTO alert_dlq (
                alert_id,
                alert_data,
                error_message,
                retry_count,
                created_at
            ) VALUES (
                $1,
                $2::jsonb,
                $3,
                0,
                NOW()
            )
            RETURNING id
        """

        try:
            row = await self.execute_query_one(
                query,
                alert_id,
                json.dumps(alert_data),
                error_message,
            )

            dlq_id = str(row["id"])
            logger.warning(
                f"Alert {alert_id} pushed to DLQ "
                f"(dlq_id: {dlq_id}, error: {error_message})"
            )
            return dlq_id

        except Exception as e:
            logger.error(f"Failed to push to DLQ: {e}")
            raise

    async def get_failed_alerts(
        self,
        max_retry_count: int = 5,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get failed alerts from DLQ that need retry.

        Args:
            max_retry_count: Maximum retry attempts
            limit: Maximum alerts to return

        Returns:
            List of DLQ records
        """
        if not self.use_db:
            return []

        query = """
            SELECT
                id,
                alert_id,
                alert_data,
                error_message,
                retry_count,
                created_at,
                last_retry_at
            FROM alert_dlq
            WHERE retry_count < $1
            ORDER BY created_at ASC
            LIMIT $2
        """

        try:
            from backend.app.db.connection import execute_query

            rows = await execute_query(query, max_retry_count, limit)

            return [
                {
                    "id": str(row["id"]),
                    "alert_id": row["alert_id"],
                    "alert_data": row["alert_data"],
                    "error_message": row["error_message"],
                    "retry_count": row["retry_count"],
                    "created_at": row["created_at"],
                    "last_retry_at": row["last_retry_at"],
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Failed to get failed alerts: {e}")
            return []

    async def increment_retry_count(
        self,
        dlq_id: str,
    ) -> None:
        """
        Increment retry count for DLQ record.

        Args:
            dlq_id: DLQ record ID
        """
        if not self.use_db:
            return

        query = """
            UPDATE alert_dlq
            SET retry_count = retry_count + 1,
                last_retry_at = NOW()
            WHERE id = $1::uuid
        """

        try:
            await self.execute_statement(query, dlq_id)
            logger.debug(f"Incremented retry count for DLQ record {dlq_id}")

        except Exception as e:
            logger.error(f"Failed to increment retry count: {e}")

    async def remove_from_dlq(
        self,
        dlq_id: str,
    ) -> None:
        """
        Remove alert from DLQ after successful delivery.

        Args:
            dlq_id: DLQ record ID
        """
        if not self.use_db:
            return

        query = """
            DELETE FROM alert_dlq
            WHERE id = $1::uuid
        """

        try:
            await self.execute_statement(query, dlq_id)
            logger.info(f"Removed DLQ record {dlq_id} after successful retry")

        except Exception as e:
            logger.error(f"Failed to remove from DLQ: {e}")
```

---

### Task 2.3: DLQ Integration in AlertService (2 hours)

**File**: `backend/app/services/alerts.py`

**Goal**: Wrap `deliver_alert()` with DLQ error handling

#### Implementation

**Update Import**:
```python
from backend.app.services.alert_delivery import AlertDeliveryService
```

**Update `deliver_alert` Method**:

```python
async def deliver_alert(
    self,
    alert: Dict[str, Any],
    user_id: str,
    message: str,
) -> bool:
    """
    Deliver alert to user via configured channels.

    Includes delivery tracking and DLQ integration.

    Args:
        alert: Alert configuration dict (includes id, name, condition, channels)
        user_id: User UUID
        message: Alert message to deliver

    Returns:
        True if delivery succeeded, False otherwise
    """
    alert_id = alert.get("id")
    alert_name = alert.get("name", "Alert")
    channels = alert.get("channels", {"inapp": True, "email": False})

    logger.info(
        f"Delivering alert {alert_id} to user {user_id} "
        f"(channels: {channels})"
    )

    # Get delivery service
    delivery_service = AlertDeliveryService(use_db=self.use_db)

    # Check for duplicate delivery (content-based)
    alert_data = {
        "condition": alert.get("condition_json"),
        "message": message,
        "user_id": user_id,
    }
    content_hash = delivery_service.compute_content_hash(alert_data)

    is_duplicate = await delivery_service.check_duplicate_delivery(
        alert_id=alert_id,
        content_hash=content_hash,
        lookback_hours=24,
    )

    if is_duplicate:
        logger.warning(
            f"Alert {alert_id} already delivered recently "
            "(content-based deduplication)"
        )
        return False

    # Get notification service
    notification_service = NotificationService(use_db=self.use_db)

    # Send notification
    try:
        success = await notification_service.send_notification(
            user_id=user_id,
            alert_id=alert_id,
            message=message,
            channels=channels,
            alert_name=alert_name,
        )

        if success:
            # Track successful delivery
            await delivery_service.track_delivery(
                alert_id=alert_id,
                alert_data=alert_data,
                delivery_methods=[k for k, v in channels.items() if v],
            )
            logger.info(f"Alert {alert_id} delivered successfully to user {user_id}")
        else:
            logger.warning(
                f"Alert {alert_id} not delivered (deduplication or channel unavailable)"
            )

        return success

    except Exception as e:
        # Push to DLQ for retry
        logger.error(f"Failed to deliver alert {alert_id}: {e}", exc_info=True)

        await delivery_service.push_to_dlq(
            alert_id=alert_id,
            alert_data=alert_data,
            error_message=str(e),
        )

        # Re-raise for caller to handle
        raise
```

---

### Task 2.4: Retry Worker (3 hours)

**File**: `backend/jobs/alert_retry_worker.py` (new)

**Goal**: Periodic job to retry failed alerts from DLQ

#### Implementation

```python
"""
Alert Retry Worker

Purpose: Retry failed alert deliveries from DLQ with exponential backoff
Updated: 2025-10-27
Priority: P0 (Phase 2 Task 4)

Features:
    - Exponential backoff: 5min, 30min, 2hr, 12hr
    - Max 5 retry attempts
    - Remove from DLQ after successful delivery
    - Metrics for retry attempts

Usage:
    # Run as scheduled job (cron/systemd)
    python backend/jobs/alert_retry_worker.py

    # Or import and run programmatically
    from backend.jobs.alert_retry_worker import retry_failed_alerts
    await retry_failed_alerts()
"""

import asyncio
import logging
from datetime import datetime, timedelta

from backend.app.services.alert_delivery import AlertDeliveryService
from backend.app.services.alerts import AlertService
from backend.app.services.notifications import NotificationService
from backend.observability.metrics import get_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("DawsOS.AlertRetryWorker")

# Retry schedule (exponential backoff)
RETRY_SCHEDULE = [
    timedelta(minutes=5),    # Retry 1: 5 minutes
    timedelta(minutes=30),   # Retry 2: 30 minutes
    timedelta(hours=2),      # Retry 3: 2 hours
    timedelta(hours=12),     # Retry 4: 12 hours
    timedelta(hours=24),     # Retry 5: 24 hours
]

MAX_RETRIES = len(RETRY_SCHEDULE)


async def retry_failed_alerts():
    """
    Retry failed alert deliveries from DLQ.

    Fetches failed alerts from DLQ and retries delivery with exponential backoff.
    """
    logger.info("Starting alert retry worker")

    # Initialize services
    delivery_service = AlertDeliveryService(use_db=True)
    notification_service = NotificationService(use_db=True)
    metrics = get_metrics()

    # Get failed alerts
    failed_alerts = await delivery_service.get_failed_alerts(
        max_retry_count=MAX_RETRIES,
        limit=100,
    )

    if not failed_alerts:
        logger.info("No failed alerts to retry")
        return

    logger.info(f"Found {len(failed_alerts)} failed alerts to retry")

    # Retry each alert
    retried_count = 0
    success_count = 0
    skipped_count = 0

    for dlq_record in failed_alerts:
        dlq_id = dlq_record["id"]
        alert_id = dlq_record["alert_id"]
        alert_data = dlq_record["alert_data"]
        retry_count = dlq_record["retry_count"]
        last_retry_at = dlq_record["last_retry_at"]

        # Check if enough time has passed since last retry
        if last_retry_at:
            now = datetime.utcnow()
            time_since_retry = now - last_retry_at.replace(tzinfo=None)
            required_wait = RETRY_SCHEDULE[min(retry_count, len(RETRY_SCHEDULE) - 1)]

            if time_since_retry < required_wait:
                logger.debug(
                    f"Skipping alert {alert_id} (retry {retry_count + 1}): "
                    f"waiting {required_wait - time_since_retry} more"
                )
                skipped_count += 1
                continue

        # Retry delivery
        logger.info(
            f"Retrying alert {alert_id} (attempt {retry_count + 1}/{MAX_RETRIES})"
        )

        try:
            # Extract delivery info
            user_id = alert_data.get("user_id")
            message = alert_data.get("message")
            channels = alert_data.get("channels", {"inapp": True, "email": False})
            alert_name = alert_data.get("name", "Alert")

            # Attempt delivery
            success = await notification_service.send_notification(
                user_id=user_id,
                alert_id=alert_id,
                message=message,
                channels=channels,
                alert_name=alert_name,
            )

            if success:
                # Track successful delivery
                await delivery_service.track_delivery(
                    alert_id=alert_id,
                    alert_data=alert_data,
                    delivery_methods=[k for k, v in channels.items() if v],
                )

                # Remove from DLQ
                await delivery_service.remove_from_dlq(dlq_id)

                logger.info(f"Alert {alert_id} delivered successfully on retry")
                success_count += 1

                # Record metrics
                if metrics:
                    metrics.agent_invocations.labels(
                        agent_name="alert_retry_worker",
                        capability="retry_delivery",
                        status="success",
                    ).inc()

            else:
                # Delivery failed (likely deduplication)
                logger.warning(f"Alert {alert_id} not delivered on retry")

                # Increment retry count
                await delivery_service.increment_retry_count(dlq_id)
                retried_count += 1

        except Exception as e:
            logger.error(f"Failed to retry alert {alert_id}: {e}", exc_info=True)

            # Increment retry count
            await delivery_service.increment_retry_count(dlq_id)
            retried_count += 1

            # Record metrics
            if metrics:
                metrics.agent_invocations.labels(
                    agent_name="alert_retry_worker",
                    capability="retry_delivery",
                    status="error",
                ).inc()

    logger.info(
        f"Alert retry worker finished: "
        f"{success_count} succeeded, {retried_count} retried, {skipped_count} skipped"
    )


if __name__ == "__main__":
    asyncio.run(retry_failed_alerts())
```

**Cron Schedule** (run every 5 minutes):
```bash
# Add to crontab
*/5 * * * * /path/to/venv/bin/python /path/to/backend/jobs/alert_retry_worker.py >> /var/log/dawsos/alert_retry.log 2>&1
```

**Systemd Timer** (alternative):
```ini
# /etc/systemd/system/dawsos-alert-retry.service
[Unit]
Description=DawsOS Alert Retry Worker
After=network.target

[Service]
Type=oneshot
User=dawsos
WorkingDirectory=/opt/dawsos
Environment="DATABASE_URL=postgresql://..."
ExecStart=/opt/dawsos/venv/bin/python /opt/dawsos/backend/jobs/alert_retry_worker.py

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/dawsos-alert-retry.timer
[Unit]
Description=Run DawsOS Alert Retry Worker every 5 minutes
Requires=dawsos-alert-retry.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
Unit=dawsos-alert-retry.service

[Install]
WantedBy=timers.target
```

**Enable Timer**:
```bash
sudo systemctl enable dawsos-alert-retry.timer
sudo systemctl start dawsos-alert-retry.timer
```

---

### Task 2.5: User Alert Preferences (1 hour)

**File**: `backend/db/schema/alerts.sql`

**Goal**: Add `channels` column to alerts table for user preferences

#### Database Migration

**Create Migration**: `backend/db/migrations/012_add_alert_channels.sql`

```sql
-- Migration: Add channels column to alerts table
-- Date: 2025-10-27
-- Purpose: Support user-configurable delivery channels (email, in-app)

-- Add channels column (JSONB)
ALTER TABLE alerts
ADD COLUMN IF NOT EXISTS channels JSONB DEFAULT '{"inapp": true, "email": false}'::jsonb;

-- Add comment
COMMENT ON COLUMN alerts.channels IS 'Delivery channels for alert (JSON: {"inapp": bool, "email": bool})';

-- Example values:
-- '{"inapp": true, "email": false}' - In-app only (default)
-- '{"inapp": true, "email": true}' - Both channels
-- '{"inapp": false, "email": true}' - Email only
```

**Run Migration**:
```bash
psql $DATABASE_URL < backend/db/migrations/012_add_alert_channels.sql
```

**Verify**:
```sql
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'alerts' AND column_name = 'channels';
```

---

### Task 2.6: Testing (2 hours)

**File 1**: `backend/tests/unit/test_alert_delivery.py` (new)

```python
"""
Unit tests for alert delivery tracking.

Purpose: Verify delivery tracking, DLQ, and deduplication
Updated: 2025-10-27
"""

import pytest
from datetime import datetime
from backend.app.services.alert_delivery import AlertDeliveryService


@pytest.mark.asyncio
async def test_content_hash_computation():
    """Test that content hash is computed consistently."""
    service = AlertDeliveryService(use_db=False)

    # Same content → same hash
    data1 = {"condition": {"type": "macro"}, "message": "Test alert"}
    data2 = {"message": "Test alert", "condition": {"type": "macro"}}  # Different order

    hash1 = service.compute_content_hash(data1)
    hash2 = service.compute_content_hash(data2)

    assert hash1 == hash2, "Content hash should be consistent regardless of key order"


@pytest.mark.asyncio
async def test_track_delivery_creates_record():
    """Test that track_delivery creates a record in alert_deliveries."""
    # TODO: Implement with real database or mock
    pass


@pytest.mark.asyncio
async def test_push_to_dlq_creates_record():
    """Test that push_to_dlq creates a record in alert_dlq."""
    # TODO: Implement with real database or mock
    pass


@pytest.mark.asyncio
async def test_duplicate_delivery_detection():
    """Test that duplicate deliveries are detected."""
    # TODO: Implement with real database or mock
    pass


@pytest.mark.asyncio
async def test_retry_count_increment():
    """Test that retry count is incremented correctly."""
    # TODO: Implement with real database or mock
    pass
```

**File 2**: `backend/tests/integration/test_alerts_e2e.py` (new)

```python
"""
End-to-end integration tests for alerting system.

Purpose: Verify full alert flow (evaluate → deliver → notification)
Updated: 2025-10-27
"""

import pytest
from datetime import date
from backend.app.services.alerts import AlertService
from backend.app.services.notifications import NotificationService


@pytest.mark.asyncio
async def test_alert_evaluation_and_delivery_e2e():
    """
    Test end-to-end alert flow:
    1. Evaluate condition
    2. Check cooldown
    3. Deliver notification
    4. Track delivery
    """
    # Initialize services
    alert_service = AlertService(use_db=True)  # Use real DB

    # Define alert
    alert = {
        "id": "test-alert-123",
        "name": "VIX Alert",
        "condition_json": {
            "type": "macro",
            "entity": "VIX",
            "metric": "level",
            "op": ">",
            "value": 30,
        },
        "cooldown_hours": 24,
        "last_fired_at": None,
        "channels": {"inapp": True, "email": False},
    }

    user_id = "11111111-1111-1111-1111-111111111111"  # Test user
    ctx = {"asof_date": date.today()}

    # Step 1: Evaluate condition
    should_fire = await alert_service.evaluate_condition(alert["condition_json"], ctx)

    if should_fire:
        # Step 2: Check cooldown
        should_deliver = await alert_service.should_trigger(alert, ctx)

        if should_deliver:
            # Step 3: Deliver alert
            message = "VIX exceeded 30 (current level triggered alert)"

            try:
                success = await alert_service.deliver_alert(alert, user_id, message)
                assert success, "Alert delivery should succeed"

                # Step 4: Verify notification was created
                notification_service = NotificationService(use_db=True)
                notifications = await notification_service.get_user_notifications(
                    user_id=user_id,
                    limit=10,
                    unread_only=True,
                )

                # Check that notification exists
                alert_notifications = [
                    n for n in notifications if n["alert_id"] == alert["id"]
                ]
                assert len(alert_notifications) > 0, "Notification should be created"

            except Exception as e:
                pytest.fail(f"Alert delivery failed: {e}")
```

**Run Tests**:
```bash
pytest backend/tests/unit/test_alert_delivery.py -v
pytest backend/tests/integration/test_alerts_e2e.py -v
```

---

### Phase 2 Summary

**Deliverables**:
- ✅ AlertService.deliver_alert() method implemented
- ✅ AlertDeliveryService for tracking and DLQ
- ✅ DLQ integration in AlertService
- ✅ Retry worker with exponential backoff
- ✅ Alert channels configuration (database migration)
- ✅ Unit tests for delivery tracking
- ✅ End-to-end integration test

**Verification Checklist**:
- [ ] AlertService.deliver_alert() calls NotificationService
- [ ] Successful deliveries tracked in alert_deliveries table
- [ ] Failed deliveries pushed to alert_dlq table
- [ ] Retry worker scheduled (cron or systemd timer)
- [ ] Duplicate deliveries prevented (content-based + time-based)
- [ ] Channels column added to alerts table
- [ ] End-to-end test passing (evaluate → deliver → notification created)

**Time Estimate**: 12 hours
- Task 2.1: 2 hours
- Task 2.2: 2 hours
- Task 2.3: 2 hours
- Task 2.4: 3 hours
- Task 2.5: 1 hour
- Task 2.6: 2 hours

---

## Implementation Sequence

**Recommended Order**:
1. Phase 1 (Metrics Recording) - 5 hours
2. Phase 2 (Alert Delivery Integration) - 12 hours

**Total Time**: 17 hours (~2 days)

**Parallelization Opportunity**:
- Phase 1 and Phase 2 are independent
- Can be implemented by 2 developers in parallel
- Total time with 2 devs: ~12 hours (1.5 days)

---

## Testing Strategy

**Unit Tests** (8 tests total):
- 5 tests for metrics recording
- 3 tests for alert delivery tracking

**Integration Tests** (1 test):
- End-to-end alert flow (evaluate → deliver → notification)

**Manual Testing**:
1. Start API: `./backend/run_api.sh`
2. Execute pattern: `curl -X POST http://localhost:8000/v1/execute ...`
3. Check metrics: `curl http://localhost:8000/metrics`
4. Verify pattern metrics present
5. Verify agent metrics present
6. Create test alert and trigger evaluation
7. Verify in-app notification created
8. Check alert_deliveries table
9. Simulate delivery failure → verify DLQ insertion
10. Run retry worker → verify failed alert retried

---

## Deployment Checklist

**Phase 1 Deployment**:
- [ ] Code changes merged to main
- [ ] Unit tests passing (5/5)
- [ ] API restarted
- [ ] `/metrics` endpoint verified
- [ ] Grafana dashboards updated (optional, Phase 3)

**Phase 2 Deployment**:
- [ ] Database migration run (012_add_alert_channels.sql)
- [ ] Code changes merged to main
- [ ] Unit tests passing (3/3)
- [ ] Integration test passing (1/1)
- [ ] API restarted
- [ ] Retry worker scheduled (cron or systemd timer)
- [ ] Email SMTP configuration verified (if email delivery needed)
- [ ] Test alert created and verified

---

## Environment Variables

**Metrics (Already Configured)**:
```bash
ENABLE_OBSERVABILITY=true
JAEGER_ENDPOINT=http://localhost:4318/v1/traces
SENTRY_DSN=https://your-sentry-dsn
```

**Email Delivery (Optional)**:
```bash
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@dawsos.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=DawsOS Alerts <alerts@dawsos.com>

# AWS SES (Alternative)
USE_AWS_SES=false
AWS_REGION=us-east-1
AWS_SES_FROM=alerts@dawsos.com
```

**Database**:
```bash
DATABASE_URL=postgresql://dawsos_app:dawsos_app_pass@localhost:5432/dawsos
```

---

## Success Metrics

**Phase 1 Success**:
- `/metrics` endpoint returns pattern_executions_total counter
- `/metrics` endpoint returns pattern_step_duration_seconds histogram
- `/metrics` endpoint returns agent_invocations_total counter
- `/metrics` endpoint returns agent_latency_seconds histogram
- `/metrics` endpoint returns circuit_breaker_state gauge
- All 5 unit tests passing

**Phase 2 Success**:
- Alert evaluation triggers delivery
- In-app notification created in database
- Email sent (if SMTP configured)
- Duplicate delivery prevented
- Failed delivery pushed to DLQ
- Retry worker successfully retries failed alerts
- All 4 tests passing (3 unit + 1 integration)

---

## Risk Assessment

**Phase 1 Risks**:
- **LOW**: Metrics recording is additive (no breaking changes)
- **LOW**: Metrics module already tested and working
- **LOW**: Changes are isolated to pattern orchestrator and agent runtime

**Phase 2 Risks**:
- **MEDIUM**: Email delivery requires SMTP configuration (can start with in-app only)
- **LOW**: NotificationService already implemented and tested
- **LOW**: DLQ tables already defined (just need to use them)
- **MEDIUM**: Retry worker needs scheduling (cron or systemd timer)

**Mitigation**:
- Start with in-app notifications only (defer email to Phase 3)
- Test DLQ insertion before implementing retry worker
- Use stub mode for testing (use_db=False)

---

## Next Steps After Option B

**Phase 3: Observability Enablement** (10 hours) - P1
- Docker Compose integration (Jaeger, Prometheus, Grafana)
- Grafana dashboards (5 dashboards)
- Documentation and setup guides

**Phase 4: Nightly Job Integration** (11 hours) - P1
- Instrument nightly jobs
- Alert evaluation scheduler
- Wire retry worker into nightly jobs

---

**Last Updated**: October 27, 2025
**Author**: Claude (AI Assistant)
**Status**: Ready for implementation
**Estimated Effort**: 17 hours (~2 days)
