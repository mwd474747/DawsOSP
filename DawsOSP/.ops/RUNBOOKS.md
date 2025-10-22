# DawsOS Operational Runbooks

**Version**: 1.0
**Date**: 2025-10-21
**Owner**: Operations Team
**Last Updated**: 2025-10-21

---

## Overview

This document contains **6 critical runbooks** (RB-01 through RB-06) for responding to operational incidents in the DawsOS Portfolio Intelligence Platform. Each runbook provides:

- **Symptoms**: How to identify the incident
- **Steps**: Ordered response procedures
- **Rollback**: How to revert if needed
- **Post-incident**: Review and prevention tasks

**On-call rotation**: See [ONCALL_SCHEDULE.md](ONCALL_SCHEDULE.md)
**Escalation**: See [ESCALATION_POLICY.md](ESCALATION_POLICY.md)

---

## RB-01: Pricing Pack Build Failure

**Severity**: P1 (High)
**Impact**: 503 errors on `/execute`; users cannot get fresh valuations
**SLO**: Pack must be ready by 00:15 local time

### Symptoms

- 503 "Pricing pack warming in progress" errors persisting > 15 minutes past 00:15
- UI shows "Pack build in progress" banner indefinitely
- Metrics dashboard shows `pack_build_duration_seconds` > 600

### Root Causes (Common)

1. **Provider outage**: Polygon/FMP API unavailable
2. **DB performance**: Slow inserts into `prices`/`fx_rates` tables
3. **Symbol mapping**: New symbols without FIGI/CUSIP mappings
4. **Job failure**: Scheduler crashed mid-build

### Steps

#### 1. Check Nightly Job Status

```bash
# Kubernetes
kubectl logs -l app=scheduler -n prod --tail=200 | grep "build_pack"

# Docker Compose
docker-compose logs scheduler | grep "build_pack"
```

**Look for**:
- Error messages (exceptions, API timeouts)
- Last successful step (prices fetched, FX rates fetched, hash computed)

---

#### 2. Check Provider Health

```bash
# Polygon
curl https://api.polygon.io/v1/status
# Expected: {"status": "ok"}

# FMP
curl "https://financialmodelingprep.com/api/v3/quote/AAPL?apikey=$FMP_KEY"
# Expected: [{...price data...}]

# FRED
curl "https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key=$FRED_KEY"
# Expected: {...observations...}
```

**If providers are down**:
- See [RB-02: Provider Outage](#rb-02-provider-outage)
- Serve last-good pack (step 4 below)

---

#### 3. Check Database Health

```bash
psql $DATABASE_URL -c "
  SELECT id, date, is_fresh, created_at
  FROM pricing_pack
  ORDER BY date DESC
  LIMIT 5;
"
```

**Expected**:
- Latest pack has `is_fresh = TRUE`
- Previous packs have `is_fresh = FALSE`

**If slow**:
```sql
-- Check long-running queries
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND query NOT LIKE '%pg_stat_activity%'
ORDER BY duration DESC;

-- Kill if stuck
SELECT pg_terminate_backend(pid) WHERE ...;
```

---

#### 4. Serve Last-Good Pack (Temporary Mitigation)

```sql
-- Mark yesterday's pack as fresh (temporary)
UPDATE pricing_pack
SET is_fresh = TRUE
WHERE id = 'PP-2025-10-20';  -- Adjust date

-- Verify
SELECT id, date, is_fresh FROM pricing_pack WHERE is_fresh = TRUE;
```

**Result**: Users can now execute patterns (using yesterday's prices)

**UI Impact**: No banner shown (pack is marked fresh)

---

#### 5. Rerun Pack Build Manually

```bash
# Kubernetes
kubectl exec -it deployment/scheduler -n prod -- \
  python -m jobs.build_pack --date 2025-10-21 --force

# Docker Compose
docker-compose exec scheduler python -m jobs.build_pack --date 2025-10-21 --force
```

**Monitor**:
```bash
# Watch logs in real-time
kubectl logs -f deployment/scheduler -n prod
```

**Expected duration**: 5-10 minutes for 500 securities

---

#### 6. Mark Pack Fresh (After Successful Build)

```sql
-- Unmark old pack
UPDATE pricing_pack SET is_fresh = FALSE WHERE date < '2025-10-21';

-- Mark new pack
UPDATE pricing_pack SET is_fresh = TRUE WHERE id = 'PP-2025-10-21';
```

---

#### 7. Verify Freshness Gate

```bash
# Test /execute endpoint
curl -X POST https://dawsos.com/execute \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern_id": "portfolio_overview",
    "portfolio_id": "test-portfolio-uuid",
    "inputs": {}
  }'

# Expected: 200 OK (not 503)
```

---

### Post-Incident

1. **Root cause analysis**: Document why build failed
2. **Update monitoring**: Add alert if missing (e.g., provider timeout threshold)
3. **Review SLO**: Did we meet pack-ready-by-00:15 SLO? If not, investigate bottleneck
4. **Symbol mapping**: If new symbols failed, add to `symbol_mapping` table

---

## RB-02: Provider Outage

**Severity**: P2 (Medium)
**Impact**: Stale data; circuit breaker open; some patterns degraded
**SLO**: Graceful degradation; no crashes

### Symptoms

- UI panels show "Data as of [yesterday] (stale)" chips
- Logs show `CircuitBreakerOpen` errors
- Metrics dashboard shows provider error rate > 10%

### Root Causes

1. **Provider API down**: Maintenance, outage, rate limit exceeded
2. **Network issue**: Connectivity to provider blocked
3. **Auth issue**: API key revoked/expired

### Steps

#### 1. Identify Affected Provider

```bash
kubectl logs -l app=api -n prod --tail=500 | grep "CircuitBreakerOpen"
# Example output:
# CircuitBreakerOpen: PolygonService - 5 consecutive failures
```

**Common providers**:
- `PolygonService`: Prices, corporate actions
- `FMPService`: Fundamentals, ratios
- `FREDService`: Macro indicators
- `NewsService`: News impact

---

#### 2. Verify Provider Status

Check provider status pages:
- Polygon: https://status.polygon.io
- FMP: https://financialmodelingprep.com/status
- FRED: https://fred.stlouisfed.org/docs/api/api_status.html

**If confirmed outage**: Proceed to step 3

---

#### 3. Pause Dependent Alerts

```sql
-- Disable alerts that rely on affected provider
UPDATE alerts
SET active = FALSE
WHERE condition_json->>'provider' = 'polygon';

-- Example: VIX alert requires live market data
UPDATE alerts
SET active = FALSE
WHERE condition_json->>'entity' = 'VIX';
```

**Result**: Prevents alert storm during outage

---

#### 4. Serve Last-Good Data

**No action needed** - Circuit breaker automatically:
- Prevents new pack build (uses last pack)
- Returns cached data (with stale TTL shown)

**Verify cache hits**:
```bash
# Check Redis cache
redis-cli -h $REDIS_HOST get "fundamentals:AAPL"
# Should return cached data
```

---

#### 5. Monitor Provider Recovery

**Set up watch**:
```bash
watch -n 60 'curl -s https://api.polygon.io/v1/status | jq .status'
```

**Or use status page notifications** (subscribe to provider status page)

---

#### 6. Replay DLQ Jobs (After Recovery)

Once provider recovers:

```bash
# Kubernetes
kubectl exec -it deployment/worker -n prod -- \
  python -m jobs.replay_dlq --provider polygon --max-retries 3

# Docker Compose
docker-compose exec worker python -m jobs.replay_dlq --provider polygon --max-retries 3
```

**What this does**:
- Retries failed jobs from Dead Letter Queue
- Re-fetches prices/fundamentals that failed during outage
- Updates pack if needed

---

#### 7. Re-enable Alerts

```sql
UPDATE alerts
SET active = TRUE
WHERE condition_json->>'provider' = 'polygon';
```

---

### Post-Incident

1. **Review circuit breaker thresholds**: Did it trip too early/late?
2. **Update provider failover**: Consider adding backup provider (e.g., yfinance if Polygon down)
3. **Alert SLA review**: Did users get notified of degraded service?

---

## RB-03: Alert Storm

**Severity**: P1 (High)
**Impact**: > 1000 notifications in < 5 minutes; email/SMS quota exhausted
**SLO**: Alert median latency < 60s

### Symptoms

- Notification queue depth > 1000
- Email service quota exceeded
- Users report spam (100s of identical alerts)
- Metrics dashboard shows `notifications_per_minute` > 200

### Root Causes

1. **Faulty alert rule**: Condition fires on every execution
2. **Market volatility**: VIX spike triggers many alerts
3. **Dedupe failure**: Unique constraint not enforcing

### Steps

#### 1. Enable Global Cooldown

```sql
-- Set all alerts to 60-minute cooldown (emergency brake)
UPDATE alerts
SET cooldown_minutes = 60
WHERE cooldown_minutes < 60;
```

**Result**: Max 1 notification per alert per hour

---

#### 2. Inspect Firing Rules

```sql
-- Top 10 alerts by notification count (last 5 minutes)
SELECT a.id, a.name, a.condition_json, COUNT(*) as notification_count
FROM notifications n
JOIN alerts a ON n.alert_id = a.id
WHERE n.created_at > NOW() - INTERVAL '5 minutes'
GROUP BY a.id, a.name, a.condition_json
ORDER BY notification_count DESC
LIMIT 10;
```

**Example output**:
```
alert_id | name           | condition_json                     | notification_count
---------|----------------|------------------------------------|---------
abc-123  | VIX Spike      | {"entity":"VIX","op":">","val":30} | 487
def-456  | Portfolio Loss | {"portfolio_pl":"<","val":-0.05}   | 203
```

---

#### 3. Disable Top Offenders

```sql
-- Temporarily disable top 3 offending alerts
UPDATE alerts
SET active = FALSE
WHERE id IN ('abc-123', 'def-456', 'ghi-789');
```

---

#### 4. Verify Dedupe Logic

```sql
-- Check for duplicate notifications (should return 0 rows)
SELECT user_id, alert_id, date_trunc('day', created_at) AS day, COUNT(*)
FROM notifications
GROUP BY user_id, alert_id, day
HAVING COUNT(*) > 1;
```

**If duplicates found**:
```sql
-- Manually dedupe (emergency)
DELETE FROM notifications
WHERE id NOT IN (
  SELECT MIN(id)
  FROM notifications
  GROUP BY user_id, alert_id, date_trunc('day', created_at)
);
```

**Root cause**: Unique index missing or disabled. Check:
```sql
\d notifications
-- Should show: uq_notify_user_alert_day UNIQUE
```

---

#### 5. Throttle Evaluator (Temporary)

```bash
# Stop alert evaluator job
kubectl scale deployment/scheduler -n prod --replicas=0

# Fix alert rules, then scale back up
kubectl scale deployment/scheduler -n prod --replicas=1
```

---

#### 6. Review Alert Rules

**Faulty rule example**:
```json
{"type":"portfolio","metric":"value","op":">","value":0}
```
**Problem**: Fires on every portfolio (always true)

**Fix**:
```sql
UPDATE alerts
SET condition_json = '{"type":"portfolio","metric":"value","op":">","value":1000000}'::jsonb
WHERE condition_json->>'value' = '0';
```

---

### Post-Incident

1. **Review alert design**: Add rate limits per alert definition
2. **Update dedupe tests**: Ensure unique constraint tested in CI
3. **Email quota**: Increase quota or implement batching

---

## RB-04: Rights Registry Violation

**Severity**: P1 (High - Compliance Risk)
**Impact**: Exported PDF contains restricted data without license
**SLO**: Zero unauthorized exports

### Symptoms

- User reports PDF contains FMP data without FMP license
- Audit log shows `rights_block` events bypassed
- Legal/compliance notification

### Root Causes

1. **Registry misconfiguration**: Provider marked as `allow` instead of `restricted`
2. **License check bypass**: User entitlements not checked
3. **Export path bypass**: UI→PDF without going through rights gate

### Steps

#### 1. Inspect Rights Registry

```bash
cat .ops/RIGHTS_REGISTRY.yaml | grep -A5 "FMP:"
```

**Expected**:
```yaml
FMP:
  export: restricted
  require_license: true
  attribution: "Financial data © Financial Modeling Prep"
```

**If `export: allow`**: Change to `restricted`

---

#### 2. Check User License Entitlements

```sql
SELECT * FROM user_licenses
WHERE user_id = 'reported-user-uuid' AND provider = 'FMP';
```

**If no rows**: User has no FMP license

---

#### 3. Block Exports Immediately

```sql
-- Block all FMP exports until audit complete
UPDATE provider_rights
SET export = 'restricted', require_license = TRUE
WHERE provider = 'FMP';
```

---

#### 4. Audit Recent Exports

```sql
-- All PDF exports in last 7 days
SELECT user_id, created_at, payload_json
FROM analytics_events
WHERE event_type = 'export_pdf'
  AND created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

**Cross-reference** with `user_licenses` to find violations

---

#### 5. Revoke Unauthorized PDFs (If Needed)

**If PDFs stored in S3**:
```bash
aws s3 rm s3://dawsos-exports-prod/user-uuid/export-id.pdf
```

**Notify user**:
```sql
INSERT INTO notifications (user_id, alert_id, payload_json)
VALUES (
  'user-uuid',
  'rights-violation-alert-id',
  '{"message": "Your export has been revoked due to licensing restrictions"}'::jsonb
);
```

---

#### 6. Add Missing License (If Legitimate)

```sql
-- Grant FMP license to user
INSERT INTO user_licenses (user_id, provider, license_type, granted_at)
VALUES ('user-uuid', 'FMP', 'export', NOW());
```

---

### Post-Incident

1. **Review rights enforcement**: Ensure all export paths go through `rights.ensure_allowed()`
2. **Add license check tests**: CI test for each provider
3. **Compliance report**: Document incident for legal/compliance team

---

## RB-05: Database Incident

**Severity**: P0 (Critical)
**Impact**: Slow queries, failover, connection errors
**SLO**: RTO < 2h, RPO < 15 min

### Symptoms

- API returns 500 errors (DB connection timeout)
- Query latency > 5s
- RDS dashboard shows CPU > 90% or IOPS maxed
- Failover in progress

### Root Causes

1. **Slow queries**: Missing index, full table scan
2. **Connection pool exhausted**: Too many concurrent connections
3. **Hardware failure**: DB instance failure
4. **Lock contention**: Long-running transactions blocking writes

### Steps

#### 1. Check RDS/Managed DB Status

```bash
# AWS RDS
aws rds describe-db-instances \
  --db-instance-identifier dawsos-prod

# Azure
az postgres server show --resource-group dawsos-prod --name dawsos-db-prod
```

**Look for**:
- `DBInstanceStatus`: Should be `available`
- `PendingModifiedValues`: Any in-progress changes

---

#### 2. Failover to Standby (If Primary Down)

```bash
# AWS RDS (Multi-AZ)
aws rds failover-db-cluster \
  --db-cluster-identifier dawsos-prod-cluster

# Azure (Replica promotion)
az postgres server replica promote \
  --resource-group dawsos-prod \
  --name dawsos-db-prod-replica
```

**Expected duration**: 1-3 minutes

---

#### 3. Identify Slow Queries

```sql
-- Top 10 slowest queries (requires pg_stat_statements extension)
SELECT
  query,
  calls,
  mean_exec_time,
  total_exec_time,
  rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

**Example slow query**:
```sql
-- BAD: No index on portfolio_id
SELECT * FROM portfolio_metrics WHERE twr > 0.05;
```

**Fix**: Add index or rewrite query (see SCHEMA_SPECIALIST.md for patterns)

---

#### 4. Kill Long-Running Queries

```sql
-- Queries running > 30 seconds
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active'
  AND query NOT LIKE '%pg_stat_activity%'
  AND now() - query_start > INTERVAL '30 seconds'
ORDER BY duration DESC;

-- Kill if blocking critical operations
SELECT pg_terminate_backend(pid) WHERE pid = 12345;
```

---

#### 5. Scale Up (If Resource-Constrained)

```bash
# AWS RDS (vertical scaling)
aws rds modify-db-instance \
  --db-instance-identifier dawsos-prod \
  --db-instance-class db.r6g.2xlarge \
  --apply-immediately

# Azure
az postgres server update \
  --resource-group dawsos-prod \
  --name dawsos-db-prod \
  --sku-name GP_Gen5_4
```

**Downtime**: 5-15 minutes (multi-AZ reduces downtime)

---

#### 6. Restore from PITR (Worst Case)

**Only if data corruption detected**:

```bash
# AWS RDS (Point-in-Time Restore)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier dawsos-prod \
  --target-db-instance-identifier dawsos-prod-restore \
  --restore-time 2025-10-21T12:00:00Z

# Verify restored data
psql $RESTORE_DATABASE_URL -c "SELECT COUNT(*) FROM portfolios;"

# Switch connection string to restored instance
kubectl set env deployment/api -n prod DATABASE_URL=$RESTORE_DATABASE_URL
```

---

### Post-Incident

1. **Query audit**: Review all slow queries; add missing indexes
2. **Connection pool tuning**: Increase max connections if needed
3. **PITR drill**: Schedule monthly restore test
4. **RDS parameter group**: Review settings (shared_buffers, work_mem, etc.)

---

## RB-06: Security Incident

**Severity**: P0 (Critical)
**Impact**: JWT token leaked, unauthorized access, data breach
**SLO**: Contain within 1 hour

### Symptoms

- JWT token found in public GitHub repo
- Suspicious access patterns (100s of requests from single IP)
- WAF alerts (SQL injection, XSS attempts)
- RLS bypass detected (user accessed another user's portfolio)

### Root Causes

1. **Token leak**: JWT in logs, committed to Git
2. **Brute force**: Password/token guessing
3. **SQL injection**: Unsanitized input
4. **RLS policy gap**: Missing or incorrect policy

### Steps

#### 1. Rotate JWT Secret (Forces Re-Authentication)

```bash
# Generate new secret
NEW_SECRET=$(openssl rand -base64 32)

# Kubernetes
kubectl create secret generic jwt-secret \
  --from-literal=JWT_SECRET=$NEW_SECRET \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart API (picks up new secret)
kubectl rollout restart deployment/api -n prod

# Docker Compose
echo "AUTH_JWT_SECRET=$NEW_SECRET" >> .env
docker-compose restart api
```

**Result**: All existing tokens invalid; users must re-authenticate

---

#### 2. Investigate WAF Logs

```bash
# AWS WAF
aws wafv2 get-sampled-requests \
  --web-acl-id $WAF_ACL_ID \
  --rule-metric-name $RULE_NAME \
  --scope REGIONAL \
  --time-window StartTime=$(date -d '1 hour ago' +%s),EndTime=$(date +%s)

# Look for:
# - High request rates from single IP
# - SQL injection patterns ('; DROP TABLE)
# - XSS attempts (<script>)
```

---

#### 3. Validate RLS Logs

```sql
-- Check for RLS bypass attempts (should be 0 or very few)
SELECT user_id, portfolio_id, action, meta_json, ts
FROM audit_log
WHERE action = '403_idor'
  AND ts > NOW() - INTERVAL '24 hours'
ORDER BY ts DESC
LIMIT 100;
```

**If many rows**: RLS policy may be missing or incorrect

**Verify RLS policies**:
```sql
-- All portfolio-scoped tables should have policies
SELECT tablename FROM pg_tables
WHERE schemaname = 'public'
  AND tablename LIKE '%portfolio%'
  AND tablename NOT IN (
    SELECT tablename FROM pg_policies WHERE schemaname = 'public'
  );
-- Should return 0 rows
```

---

#### 4. Block Malicious IP

```bash
# AWS WAF (add IP to block list)
aws wafv2 update-ip-set \
  --name dawsos-blocked-ips \
  --id $IP_SET_ID \
  --scope REGIONAL \
  --addresses 192.0.2.1/32

# Or use temporary rate limit
aws wafv2 create-rate-based-rule ...
```

---

#### 5. Review Compromised Accounts

```sql
-- Recent logins from suspicious IP
SELECT user_id, created_at, meta_json->>'ip_address' AS ip
FROM analytics_events
WHERE event_type = 'login'
  AND meta_json->>'ip_address' = '192.0.2.1'
  AND created_at > NOW() - INTERVAL '7 days';

-- Force password reset for affected users
UPDATE users
SET password_reset_required = TRUE
WHERE id IN (...);
```

---

#### 6. Notify Affected Users

```sql
-- Create notification
INSERT INTO notifications (user_id, alert_id, payload_json)
SELECT user_id, 'security-incident-alert-id', '{"message": "Security incident detected. Please reset your password."}'::jsonb
FROM users
WHERE id IN (...);
```

**Email template**: See `.ops/SECURITY_INCIDENT_EMAIL.md`

---

### Post-Incident

1. **Security audit**: Full review of RLS policies, WAF rules, secrets management
2. **Update RLS tests**: Add test case for detected bypass
3. **Pentest**: Schedule external penetration test
4. **Compliance report**: Notify legal/compliance team; GDPR/CCPA requirements

---

## Emergency Contacts

| Role | Name | Email | Phone |
|------|------|-------|-------|
| On-call Engineer | TBD | oncall@dawsos.com | (555) 123-4567 |
| Database Admin | TBD | dba@dawsos.com | (555) 234-5678 |
| Security Lead | TBD | security@dawsos.com | (555) 345-6789 |
| Product Owner | Mike | mike@dawsos.com | (555) 456-7890 |

---

## Related Documents

- [SLO Dashboards](SLO_DASHBOARDS.md) - Metrics and alert thresholds
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Canary, rollback procedures
- [Rights Registry Process](RIGHTS_PROCESS.md) - License management
- [Escalation Policy](ESCALATION_POLICY.md) - When to escalate

---

**Last Updated**: 2025-10-21
**Next Review**: 2026-01-21 (quarterly)
