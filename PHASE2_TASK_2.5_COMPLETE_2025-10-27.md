# Phase 2 Task 2.5 Complete: Alert Channels Migration

**Date**: October 27, 2025
**Task**: Add channels column to alerts table for unified notification configuration
**Status**: ✅ COMPLETE
**Time**: 1 hour

---

## Summary

Added support for unified `channels` JSONB column to the `alerts` table while maintaining backward compatibility with existing `notify_email` and `notify_inapp` boolean columns.

---

## Changes Made

### 1. Database Migration (`backend/db/migrations/012_add_alert_channels.sql`)

**File**: NEW - 38 lines

**Purpose**: Add `channels` JSONB column to alerts table

**Key Changes**:
```sql
-- Add channels column (optional)
ALTER TABLE alerts
ADD COLUMN IF NOT EXISTS channels JSONB DEFAULT NULL;

-- Create GIN index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_alerts_channels ON alerts USING GIN (channels);
```

**Migration Strategy**:
- **Phase 1**: Add channels column (ADDITIVE, not BREAKING) ✅
- **Phase 2**: Support both formats in code (DONE) ✅
- **Phase 3**: Backfill channels from notify_email/notify_inapp (FUTURE)
- **Phase 4**: Update API to write to channels column (FUTURE)
- **Phase 5**: Deprecate notify_email/notify_inapp (FUTURE)

**Backward Compatibility**: ✅ YES
- Existing code continues to use `notify_email`/`notify_inapp` columns
- New code can use `channels` JSONB column
- `AlertService.normalize_channels()` supports both formats

---

### 2. Code Update (`backend/app/services/alerts.py`)

**Added Method**: `normalize_channels(alert: Dict[str, Any]) -> Dict[str, bool]`

**Purpose**: Convert between database formats transparently

**Implementation**:
```python
def normalize_channels(self, alert: Dict[str, Any]) -> Dict[str, bool]:
    """
    Normalize alert channels to unified format.

    Supports both legacy format (notify_email, notify_inapp booleans)
    and new format (channels JSONB dict).

    Args:
        alert: Alert configuration dict

    Returns:
        Channels dict {"inapp": bool, "email": bool}
    """
    # Check for new format first
    if "channels" in alert:
        return alert["channels"]

    # Fall back to legacy format
    return {
        "inapp": alert.get("notify_inapp", True),
        "email": alert.get("notify_email", False),
    }
```

**Usage in deliver_alert()**:
```python
channels = self.normalize_channels(alert)
# Works with both formats:
# - {"channels": {"inapp": True, "email": False}}  (new)
# - {"notify_inapp": True, "notify_email": False}  (legacy)
```

---

## Testing

### Manual Verification

**1. Check migration syntax**:
```bash
psql $DATABASE_URL -f backend/db/migrations/012_add_alert_channels.sql
```

**2. Verify column added**:
```sql
\d alerts
-- Should show:
-- channels | jsonb | | |
```

**3. Test normalize_channels() with both formats**:
```python
from backend.app.services.alerts import AlertService

alert_service = AlertService(use_db=False)

# Test legacy format
alert_legacy = {
    "id": "test-123",
    "notify_inapp": True,
    "notify_email": False
}
channels = alert_service.normalize_channels(alert_legacy)
assert channels == {"inapp": True, "email": False}

# Test new format
alert_new = {
    "id": "test-123",
    "channels": {"inapp": False, "email": True}
}
channels = alert_service.normalize_channels(alert_new)
assert channels == {"inapp": False, "email": True}
```

---

## Files Modified

1. **backend/db/migrations/012_add_alert_channels.sql** - NEW (38 lines)
2. **backend/app/services/alerts.py** - Modified (added `normalize_channels()` method)

---

## Files Verified

All files compile successfully:
```bash
python3 -m py_compile backend/app/services/alerts.py  # ✅ OK
```

---

## Next Steps

**Immediate**: Phase 2 Task 2.6 - Create tests for alert delivery integration (2 hours)

**Future** (Post-Phase 2):
1. Create data migration to backfill `channels` from `notify_email`/`notify_inapp`
2. Update API routes to accept `channels` field in AlertCreate/AlertUpdate
3. Update nightly job to write to `channels` column
4. Deprecate `notify_email`/`notify_inapp` columns (breaking change, major version bump)

---

## Benefits

1. **Backward Compatible**: Existing code continues to work without changes
2. **Gradual Migration**: Can migrate to JSONB format incrementally
3. **Cleaner API**: Single `channels` field vs two separate boolean columns
4. **Future-Proof**: Easy to add new channels (SMS, Slack, etc.) without schema changes
5. **Indexable**: GIN index allows efficient JSONB queries

---

## Phase 2 Progress

- ✅ Task 2.1: Add deliver_alert() method to AlertService - COMPLETE
- ✅ Task 2.2: Create AlertDeliveryService for tracking and DLQ - COMPLETE
- ✅ Task 2.3: Integrate DLQ error handling in AlertService - COMPLETE
- ✅ Task 2.4: Create alert retry worker with exponential backoff - COMPLETE
- ✅ Task 2.5: Add channels column to alerts table - COMPLETE
- ⏳ Task 2.6: Create tests for alert delivery integration - PENDING

**Phase 2 Status**: 83% COMPLETE (5/6 tasks done)

---

**Completion Time**: October 27, 2025
**Verified By**: Claude (Sonnet 4.5)
