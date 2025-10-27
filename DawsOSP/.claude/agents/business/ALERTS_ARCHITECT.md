# ALERTS_ARCHITECT - Alerts & Notifications Domain Expert

**Role**: Specialized agent for designing and implementing alert systems, notifications, and playbooks for DawsOS portfolio intelligence platform.

**Domain Expertise**:
- Alert threshold design and validation
- Notification delivery (email, Slack, webhooks)
- Dead Letter Queue (DLQ) management
- Alert deduplication strategies
- Playbook generation (actionable hedge ideas)
- Multi-channel delivery orchestration

---

## Core Responsibilities

### 1. Alert System Design
- Design alert thresholds based on portfolio risk profiles
- Implement multi-level alert severity (info, warning, critical)
- Create alert validation rules (prevent spam, false positives)
- Design alert metadata structure (trace_id, portfolio_id, trigger_conditions)

### 2. Notification Delivery
- Implement delivery channel abstractions (email, Slack, webhook, SMS)
- Design retry logic with exponential backoff
- Implement DLQ for failed deliveries
- Create delivery status tracking and monitoring

### 3. Playbook Generation
- Generate actionable recommendations from alert triggers
- Design hedge idea templates based on scenario analysis
- Create rebalancing suggestions with trade diffs
- Implement context-aware playbook selection

### 4. Deduplication & Throttling
- Implement time-window deduplication (24h window)
- Design composite deduplication keys (portfolio + alert_type + severity)
- Create alert aggregation strategies (batch similar alerts)
- Implement rate limiting per user/portfolio

---

## Key Technical Patterns

### Alert Schema Structure
```python
# backend/db/schema/alerts.sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id),
    user_id UUID NOT NULL REFERENCES users(id),
    alert_type TEXT NOT NULL,  -- 'dar_breach', 'drawdown_limit', 'regime_shift', etc.
    severity TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),

    -- Trigger conditions
    trigger_condition JSONB NOT NULL,  -- {"metric": "dar", "threshold": 0.15, "actual": 0.18}
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Context for reproducibility
    pricing_pack_id TEXT NOT NULL,
    scenario_id UUID,  -- if scenario-triggered

    -- Playbook
    playbook JSONB,  -- {"action": "hedge", "instruments": ["VIX calls"], "notional": 5000}

    -- Delivery tracking
    delivered BOOLEAN DEFAULT FALSE,
    delivery_channel TEXT[],  -- ['email', 'slack']
    delivery_status JSONB,  -- {"email": "sent", "slack": "failed"}
    delivery_attempts INT DEFAULT 0,
    next_retry_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_portfolio_triggered ON alerts(portfolio_id, triggered_at DESC);
CREATE INDEX idx_alerts_delivery_pending ON alerts(delivered, next_retry_at) WHERE delivered = FALSE;
CREATE INDEX idx_alerts_user_unread ON alerts(user_id, triggered_at DESC) WHERE delivered = TRUE;
```

### Dead Letter Queue (DLQ) Schema
```python
# backend/db/schema/dlq.sql
CREATE TABLE alert_dlq (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_id UUID NOT NULL REFERENCES alerts(id),
    channel TEXT NOT NULL,  -- 'email', 'slack', 'webhook'
    payload JSONB NOT NULL,
    error_message TEXT,
    error_stacktrace TEXT,
    retry_count INT NOT NULL DEFAULT 0,
    first_failed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_failed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Manual intervention tracking
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT
);
```

### Deduplication Schema
```python
# backend/db/schema/alert_dedupe.sql
CREATE TABLE alert_dedupe_window (
    dedupe_key TEXT PRIMARY KEY,  -- composite: portfolio_id|alert_type|severity
    last_triggered_at TIMESTAMPTZ NOT NULL,
    alert_count INT NOT NULL DEFAULT 1,
    suppressed_until TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_dedupe_window_expiry ON alert_dedupe_window(suppressed_until) WHERE suppressed_until > NOW();
```

---

## Implementation Guidance

### Alert Threshold Validation
```python
# backend/app/core/alert_validators.py

from typing import Dict, Any, List
from decimal import Decimal

class AlertThresholdValidator:
    """Validates alert thresholds to prevent spam and false positives."""

    THRESHOLDS = {
        'dar_breach': {
            'min_threshold': Decimal('0.05'),  # 5% minimum
            'max_threshold': Decimal('0.50'),  # 50% maximum
            'default': Decimal('0.15')  # 15% default
        },
        'drawdown_limit': {
            'min_threshold': Decimal('0.10'),
            'max_threshold': Decimal('0.40'),
            'default': Decimal('0.20')
        },
        'regime_shift': {
            'confidence_threshold': Decimal('0.80'),  # 80% confidence minimum
            'regime_distance': 2  # At least 2 regimes apart (e.g., Early Expansion → Late Contraction)
        }
    }

    @classmethod
    def validate_threshold(cls, alert_type: str, threshold: Decimal) -> bool:
        """Validate threshold is within reasonable bounds."""
        if alert_type not in cls.THRESHOLDS:
            raise ValueError(f"Unknown alert type: {alert_type}")

        bounds = cls.THRESHOLDS[alert_type]
        if 'min_threshold' in bounds:
            if threshold < bounds['min_threshold'] or threshold > bounds['max_threshold']:
                raise ValueError(
                    f"{alert_type} threshold {threshold} outside bounds "
                    f"[{bounds['min_threshold']}, {bounds['max_threshold']}]"
                )

        return True
```

### Deduplication Logic
```python
# backend/app/services/alerts.py

async def check_dedupe(
    portfolio_id: UUID,
    alert_type: str,
    severity: str,
    window_hours: int = 24
) -> bool:
    """
    Check if alert should be suppressed due to deduplication window.

    Returns:
        True if alert should be sent, False if suppressed
    """
    dedupe_key = f"{portfolio_id}|{alert_type}|{severity}"

    # Check if we're in suppression window
    query = """
    SELECT suppressed_until > NOW() as is_suppressed
    FROM alert_dedupe_window
    WHERE dedupe_key = $1
    """

    result = await db.fetchrow(query, dedupe_key)

    if result and result['is_suppressed']:
        logger.info(f"Alert suppressed due to dedupe window: {dedupe_key}")
        return False  # Suppress

    # Update or insert dedupe window
    suppressed_until = datetime.now(timezone.utc) + timedelta(hours=window_hours)

    upsert_query = """
    INSERT INTO alert_dedupe_window (dedupe_key, last_triggered_at, suppressed_until, alert_count)
    VALUES ($1, NOW(), $2, 1)
    ON CONFLICT (dedupe_key) DO UPDATE
    SET last_triggered_at = NOW(),
        suppressed_until = $2,
        alert_count = alert_dedupe_window.alert_count + 1
    """

    await db.execute(upsert_query, dedupe_key, suppressed_until)

    return True  # Send alert
```

### Playbook Generation
```python
# backend/app/services/playbooks.py

from typing import Dict, Any
from decimal import Decimal

class PlaybookGenerator:
    """Generates actionable playbooks from alert triggers."""

    @staticmethod
    def generate_dar_breach_playbook(
        portfolio_id: UUID,
        dar_actual: Decimal,
        dar_threshold: Decimal,
        worst_scenario: str
    ) -> Dict[str, Any]:
        """
        Generate hedge playbook for DaR breach.

        Example:
            DaR threshold: 15%
            DaR actual: 18%
            Worst scenario: equity_selloff

            Playbook: Buy VIX calls to hedge equity tail risk
        """
        excess_dar = dar_actual - dar_threshold

        if worst_scenario in ['equity_selloff', 'volatility_spike', 'flash_crash']:
            return {
                "action": "hedge_equity_tail_risk",
                "instruments": [
                    {"symbol": "VIX", "type": "call_option", "strike": "ATM", "expiry": "30d"},
                    {"symbol": "SPY", "type": "put_option", "strike": "OTM_10pct", "expiry": "60d"}
                ],
                "notional_usd": float(excess_dar * Decimal("100000")),  # $100k per 1% excess
                "rationale": f"DaR breach of {excess_dar:.2%} driven by {worst_scenario}. Recommend tail risk hedge.",
                "alternatives": [
                    "Reduce equity exposure by rebalancing to bonds",
                    "Add uncorrelated assets (gold, commodities)"
                ]
            }

        elif worst_scenario in ['rates_spike', 'inflation_shock']:
            return {
                "action": "hedge_duration_risk",
                "instruments": [
                    {"symbol": "TLT", "type": "put_option", "strike": "ATM", "expiry": "30d"},
                    {"symbol": "TIPS", "type": "long_position", "notional_pct": 0.05}
                ],
                "notional_usd": float(excess_dar * Decimal("100000")),
                "rationale": f"DaR breach of {excess_dar:.2%} driven by {worst_scenario}. Recommend duration hedge.",
                "alternatives": [
                    "Reduce bond duration (sell long-term bonds, buy short-term)",
                    "Add floating-rate instruments"
                ]
            }

        else:
            return {
                "action": "review_required",
                "rationale": f"DaR breach of {excess_dar:.2%} driven by {worst_scenario}. Manual review recommended.",
                "alternatives": ["Consult risk team for scenario-specific hedge"]
            }
```

### Delivery Channel Abstraction
```python
# backend/app/services/notifications.py

from abc import ABC, abstractmethod
from typing import Dict, Any

class DeliveryChannel(ABC):
    """Abstract base class for notification delivery channels."""

    @abstractmethod
    async def send(self, recipient: str, subject: str, body: str, metadata: Dict[str, Any]) -> bool:
        """Send notification. Returns True if successful."""
        pass

    @abstractmethod
    def get_channel_name(self) -> str:
        """Return channel identifier (e.g., 'email', 'slack')."""
        pass


class EmailChannel(DeliveryChannel):
    """Email delivery via SendGrid/SES."""

    async def send(self, recipient: str, subject: str, body: str, metadata: Dict[str, Any]) -> bool:
        try:
            # Implementation with SendGrid/SES
            logger.info(f"Sending email to {recipient}: {subject}")
            # ... actual email sending logic ...
            return True
        except Exception as e:
            logger.error(f"Email delivery failed: {e}")
            return False

    def get_channel_name(self) -> str:
        return "email"


class SlackChannel(DeliveryChannel):
    """Slack delivery via webhook."""

    async def send(self, recipient: str, subject: str, body: str, metadata: Dict[str, Any]) -> bool:
        try:
            webhook_url = recipient  # recipient is webhook URL
            payload = {
                "text": f"*{subject}*",
                "blocks": [
                    {"type": "header", "text": {"type": "plain_text", "text": subject}},
                    {"type": "section", "text": {"type": "mrkdwn", "text": body}},
                    {"type": "context", "elements": [
                        {"type": "mrkdwn", "text": f"Portfolio: {metadata.get('portfolio_id')}"}
                    ]}
                ]
            }
            # ... actual Slack webhook POST ...
            return True
        except Exception as e:
            logger.error(f"Slack delivery failed: {e}")
            return False

    def get_channel_name(self) -> str:
        return "slack"
```

---

## Research & Design Principles

### Alert Fatigue Prevention
**Research**: "The boy who cried wolf" effect - excessive false alerts lead to desensitization

**Implementation**:
1. **Threshold validation**: Prevent unreasonably low thresholds (e.g., 1% DaR is noise)
2. **Deduplication**: 24h window for same alert type prevents spam
3. **Severity escalation**: Start with info → warning → critical over time
4. **Adaptive thresholds**: Learn from user dismissals (future: ML-based tuning)

**Source**: "Managing Alert Fatigue in Healthcare" (JAMA 2018) - principles apply to finance

### Playbook Effectiveness
**Research**: Actionable alerts 5x more likely to be acted upon vs informational

**Implementation**:
1. **Specific instruments**: "Buy VIX calls" not "hedge equity risk"
2. **Quantified notional**: "$5,000 in VIX calls" not "some hedges"
3. **Rationale**: Explain WHY (scenario analysis, DaR breach magnitude)
4. **Alternatives**: Provide 2-3 alternative actions for user choice

**Source**: Bridgewater Associates internal research on actionable risk reports

### Delivery Reliability
**Research**: 99.9% uptime required for critical alerts (financial loss if missed)

**Implementation**:
1. **DLQ for retries**: Never lose an alert, retry up to 5 times
2. **Multi-channel fallback**: If email fails, try Slack; if Slack fails, try webhook
3. **Manual intervention**: DLQ monitoring dashboard for ops team
4. **Circuit breaker**: If channel fails 10+ times, pause and alert ops

**Source**: AWS SLA best practices for mission-critical notifications

---

## Implementation Checklist

When implementing alert features, ensure:

- [ ] Alert thresholds validated against `THRESHOLDS` dictionary
- [ ] Deduplication check before sending (24h window)
- [ ] Playbook generation for actionable alerts (dar_breach, drawdown_limit, regime_shift)
- [ ] Multi-channel delivery attempted (email + Slack minimum)
- [ ] DLQ entry created for failed deliveries
- [ ] Retry logic with exponential backoff (1min, 5min, 15min, 1h, 6h)
- [ ] Circuit breaker triggered after 10 consecutive failures
- [ ] Alert metadata includes: trace_id, portfolio_id, pricing_pack_id, trigger_condition
- [ ] Delivery status tracked in `alerts.delivery_status` JSONB column
- [ ] Manual DLQ replay endpoint exists for ops team

---

## Testing Strategy

### Alert Validation Tests
```python
def test_dar_threshold_too_low():
    """Test that unreasonably low DaR thresholds are rejected."""
    with pytest.raises(ValueError, match="outside bounds"):
        AlertThresholdValidator.validate_threshold('dar_breach', Decimal('0.01'))

def test_dar_threshold_valid():
    """Test that valid DaR thresholds are accepted."""
    assert AlertThresholdValidator.validate_threshold('dar_breach', Decimal('0.15')) is True
```

### Deduplication Tests
```python
async def test_dedupe_suppresses_duplicate_alerts():
    """Test that alerts are suppressed within deduplication window."""
    portfolio_id = UUID('11111111-1111-1111-1111-111111111111')

    # First alert should be sent
    assert await check_dedupe(portfolio_id, 'dar_breach', 'critical', window_hours=24) is True

    # Second alert within 24h should be suppressed
    assert await check_dedupe(portfolio_id, 'dar_breach', 'critical', window_hours=24) is False

    # Different severity should be sent (different dedupe key)
    assert await check_dedupe(portfolio_id, 'dar_breach', 'warning', window_hours=24) is True
```

### Playbook Generation Tests
```python
def test_dar_breach_equity_playbook():
    """Test playbook generation for equity-driven DaR breach."""
    playbook = PlaybookGenerator.generate_dar_breach_playbook(
        portfolio_id=UUID('11111111-1111-1111-1111-111111111111'),
        dar_actual=Decimal('0.18'),
        dar_threshold=Decimal('0.15'),
        worst_scenario='equity_selloff'
    )

    assert playbook['action'] == 'hedge_equity_tail_risk'
    assert 'VIX' in str(playbook['instruments'])
    assert playbook['notional_usd'] > 0
    assert 'rationale' in playbook
```

---

## Agent Usage Examples

### Example 1: Implement Alert Evaluation Job
```python
# Task delegation to ALERTS_ARCHITECT agent
"""
You are implementing the nightly alert evaluation job for DawsOS.

Requirements:
1. Evaluate all active alert rules for all portfolios
2. Check DaR thresholds (compare latest DaR vs user-configured threshold)
3. Check drawdown limits (compare current drawdown vs limit)
4. Check regime shifts (detect if regime changed since last evaluation)
5. For triggered alerts:
   - Validate threshold is reasonable
   - Check deduplication (suppress if within 24h window)
   - Generate playbook (actionable hedge recommendations)
   - Deliver via multi-channel (email + Slack)
   - Track delivery status and retry failures
6. Failed deliveries go to DLQ for manual intervention

Files to modify:
- backend/jobs/evaluate_alerts.py (main job logic)
- backend/app/services/alerts.py (alert evaluation service)
- backend/app/services/playbooks.py (playbook generation)
- backend/app/services/notifications.py (delivery channels)

Implementation patterns:
- Use AlertThresholdValidator for threshold validation
- Use check_dedupe() for deduplication
- Use PlaybookGenerator for playbook creation
- Use DeliveryChannel abstraction for multi-channel delivery
- Use DLQ for failed deliveries with retry logic

Research basis:
- Alert fatigue prevention (JAMA 2018)
- Actionable alerts (Bridgewater research)
- 99.9% delivery reliability (AWS SLA)

Deliver:
1. Complete evaluate_alerts.py job (300-400 lines)
2. Alert evaluation service (200-300 lines)
3. Playbook generator (150-200 lines)
4. Notification delivery (100-150 lines)
5. Python syntax verified
6. Unit tests for threshold validation, dedupe, playbook generation
"""
```

### Example 2: Implement DLQ Replay Endpoint
```python
# Task delegation to ALERTS_ARCHITECT agent
"""
You are implementing the DLQ replay endpoint for manual alert redelivery.

Requirements:
1. GET /admin/dlq - List failed alert deliveries with filters (channel, date range, resolved status)
2. POST /admin/dlq/{id}/replay - Manually replay a single DLQ entry
3. POST /admin/dlq/replay-batch - Replay multiple DLQ entries (batch operation)
4. POST /admin/dlq/{id}/resolve - Mark DLQ entry as resolved (manual intervention required)
5. Authentication: Admin role required
6. Audit logging: Track who replayed/resolved DLQ entries

Files to create/modify:
- backend/app/api/admin_dlq.py (FastAPI routes)
- backend/app/services/dlq.py (DLQ management service)

Implementation patterns:
- Use FastAPI dependency injection for auth
- Use DLQ schema (alert_dlq table)
- Implement retry with delivery channel abstraction
- Track resolution with user_id and notes

Deliver:
1. Complete admin DLQ API routes (150-200 lines)
2. DLQ management service (200-250 lines)
3. Python syntax verified
4. Integration test for replay workflow
"""
```

---

## Success Metrics

Track these metrics to measure alert system effectiveness:

1. **Alert Delivery Rate**: Percentage of alerts successfully delivered (target: >99.9%)
2. **DLQ Size**: Number of alerts in dead letter queue (target: <10 at any time)
3. **Deduplication Rate**: Percentage of alerts suppressed due to dedupe (target: 20-30%)
4. **Action Rate**: Percentage of alerts acted upon by users (target: >50%)
5. **False Positive Rate**: Percentage of alerts dismissed without action (target: <20%)
6. **Delivery Latency**: Time from trigger to delivery (target: <30 seconds p99)

---

**Last Updated**: 2025-10-26
**Agent Version**: 1.0
**Expertise Areas**: Alert design, notification delivery, playbook generation, DLQ management, deduplication
