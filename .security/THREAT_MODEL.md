# DawsOS Portfolio Intelligence Platform — Threat Model

**Version**: 1.0
**Date**: 2025-10-21
**Framework**: STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)
**Scope**: Production deployment (staging + production environments)

---

## Executive Summary

This threat model identifies security risks across the DawsOS Portfolio Intelligence Platform using the STRIDE framework. The platform processes sensitive financial data (portfolio holdings, transactions, personal financial information) and integrates with third-party data providers (FMP, Polygon, FRED, NewsAPI).

**Critical Assets**:
1. **Portfolio data** (holdings, transactions, P&L) — User-specific financial information
2. **Beancount ledger** — Source of truth for transactions and positions
3. **Pricing Pack** — Immutable daily snapshot of prices/FX rates
4. **API credentials** — Third-party provider keys (FMP, Polygon, FRED, NewsAPI)
5. **User authentication tokens** — OAuth tokens, JWT bearer tokens
6. **Audit logs** — Complete record of all mutations and access

**Compliance Requirements**:
- Row-Level Security (RLS) on all portfolio-scoped tables
- No cross-user data access (IDOR prevention)
- Secrets management (vault/env only, never in code)
- Audit trail for all mutations
- Rights registry enforcement (export licensing)

---

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
│                    (React/Next.js or Streamlit)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Executor API (FastAPI)                      │
│              OAuth → JWT → RLS context → Orchestrator            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Pattern Orchestrator + Agents                  │
│        (financial_analyst, macro_hound, data_harvester)          │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
    ┌─────────────────────┐     ┌─────────────────────┐
    │  Postgres/Timescale │     │  External Providers  │
    │  (RLS-protected)    │     │ (FMP/Polygon/FRED)   │
    └─────────────────────┘     └─────────────────────┘
                ▼
    ┌─────────────────────┐
    │  Beancount Ledger   │
    │  (Git repo, local)  │
    └─────────────────────┘
```

---

## STRIDE Analysis by Component

### 1. User Browser / UI

#### Spoofing
- **Threat**: Attacker impersonates legitimate user via stolen session token
- **Mitigation**:
  - OAuth with Google/GitHub (trusted identity providers)
  - Short-lived JWT tokens (15-minute expiry)
  - Secure cookie flags (`HttpOnly`, `Secure`, `SameSite=Strict`)
  - Logout revokes server-side session

#### Tampering
- **Threat**: Man-in-the-middle (MITM) attack modifies API requests/responses
- **Mitigation**:
  - HTTPS/TLS 1.3 only (enforce in load balancer)
  - HSTS headers (`Strict-Transport-Security: max-age=31536000`)
  - Certificate pinning for critical endpoints (optional)

#### Information Disclosure
- **Threat**: Browser cache/local storage leaks sensitive data
- **Mitigation**:
  - No sensitive data in `localStorage` (portfolio values, holdings)
  - Session tokens in `HttpOnly` cookies only
  - Cache-Control headers for sensitive responses (`no-store`)

#### Denial of Service
- **Threat**: Client-side infinite loops or memory exhaustion
- **Mitigation**:
  - Rate limiting on client-side API calls (max 10 req/sec)
  - Timeout for long-running requests (30s UI timeout)

---

### 2. Executor API (FastAPI)

#### Spoofing
- **Threat**: Forged JWT tokens bypass authentication
- **Mitigation**:
  - Verify JWT signature with public key from OAuth provider
  - Check `iss` (issuer), `aud` (audience), `exp` (expiry) claims
  - Reject tokens from untrusted issuers

#### Tampering
- **Threat**: Attacker modifies request payloads (e.g., change `portfolio_id`)
- **Mitigation**:
  - RLS enforces user ownership of portfolio (DB-level check)
  - Request validation with Pydantic schemas (type checking)
  - IDOR fuzzing in CI (100 cross-portfolio access attempts → 100 403s)

#### Repudiation
- **Threat**: User denies performing portfolio mutation (add transaction, delete holding)
- **Mitigation**:
  - Audit log for all mutations (user_id, timestamp, action, payload)
  - Structured JSON logs with trace correlation
  - Immutable audit log (append-only, no deletes)

#### Information Disclosure
- **Threat**: Error messages leak sensitive data (portfolio values, holdings)
- **Mitigation**:
  - Generic error bodies for 403/404 (no portfolio names/values)
  - Sentry redacts PII from error payloads
  - No stack traces in production responses

#### Denial of Service
- **Threat**: Excessive requests exhaust API resources
- **Mitigation**:
  - Rate limiting (100 req/min per user, 1000 req/min globally)
  - Pack freshness gate (503 when warming, prevents stampede)
  - Request timeouts (30s for `/execute`, 5s for `/health`)
  - Circuit breakers for downstream services

#### Elevation of Privilege
- **Threat**: User accesses another user's portfolio via IDOR
- **Mitigation**:
  - RLS policies on 14 portfolio-scoped tables
  - `SET app.user_id = '<user_id>'` before every query
  - IDOR fuzz tests in CI (cross-user access → 403)
  - Minimal error bodies (no leakage)

---

### 3. Pattern Orchestrator + Agents

#### Tampering
- **Threat**: Malicious pattern modifies pricing pack or ledger
- **Mitigation**:
  - Pricing pack immutability enforced (no mutations allowed)
  - Ledger is read-only for API (writes via external Beancount CLI only)
  - Property tests ensure pack immutability

#### Information Disclosure
- **Threat**: Agent logs leak sensitive data (portfolio holdings, values)
- **Mitigation**:
  - Structured JSON logs with redaction rules
  - No portfolio values in log messages
  - Trace IDs for correlation (no PII in traces)

#### Elevation of Privilege
- **Threat**: Agent bypasses RLS to access cross-user data
- **Mitigation**:
  - Agents use same DB connection pool with RLS context set
  - No direct SQL (ORM only, inherits RLS)
  - Integration tests verify RLS enforcement

---

### 4. Postgres/Timescale Database

#### Spoofing
- **Threat**: Unauthorized access to database via stolen credentials
- **Mitigation**:
  - Database credentials in secrets manager (AWS Secrets Manager, Vault)
  - No credentials in code or config files
  - Rotate credentials quarterly
  - IP allowlist for DB access (API servers only)

#### Tampering
- **Threat**: Direct DB access modifies audit log or portfolio data
- **Mitigation**:
  - Audit log is append-only (no UPDATE/DELETE permissions)
  - Foreign key constraints enforce referential integrity
  - Nightly ledger reconciliation detects tampering (±1bp tolerance)

#### Information Disclosure
- **Threat**: Database backup leaks sensitive data
- **Mitigation**:
  - Encrypted backups (AES-256)
  - Backup storage in private S3 bucket (no public access)
  - Restore drill monthly (verify backup integrity)

#### Denial of Service
- **Threat**: Expensive queries exhaust DB resources
- **Mitigation**:
  - Query timeout (10s max for `/execute` queries)
  - Connection pooling (max 50 connections)
  - TimescaleDB continuous aggregates (pre-computed rolling stats)

#### Elevation of Privilege
- **Threat**: RLS bypass via direct SQL or ORM bug
- **Mitigation**:
  - RLS enabled at DB level (not just ORM)
  - Unit tests for RLS policies (100% coverage)
  - IDOR fuzz tests in CI

---

### 5. External Providers (FMP, Polygon, FRED, NewsAPI)

#### Spoofing
- **Threat**: Attacker impersonates provider API (DNS hijacking, MITM)
- **Mitigation**:
  - TLS certificate validation (reject self-signed certs)
  - Hardcoded provider domains (no user-supplied URLs)
  - Certificate pinning for critical providers (optional)

#### Tampering
- **Threat**: Provider response modified in transit
- **Mitigation**:
  - HTTPS/TLS 1.3 for all provider calls
  - Response validation (schema checks, sanity checks)
  - Golden tests detect data drift

#### Information Disclosure
- **Threat**: API keys leak in logs or error messages
- **Mitigation**:
  - API keys stored in secrets manager (not code/config)
  - Redact API keys from logs (structured logging with filters)
  - Sentry redacts secrets from error payloads

#### Denial of Service
- **Threat**: Provider outage cascades to platform failure
- **Mitigation**:
  - Circuit breakers (3 failures → OPEN for 60s)
  - Fallback to last-good data (stale panel markers)
  - DLQ for failed requests (replay after recovery)
  - Rate limiting (token bucket, jittered backoff)

#### Elevation of Privilege
- **Threat**: Provider over-provisioning exposes more data than licensed
- **Mitigation**:
  - Rights registry enforces export restrictions
  - Block or watermark restricted data in PDF exports
  - Staging enforcement from S1-W2 onward

---

### 6. Beancount Ledger (Git Repo)

#### Tampering
- **Threat**: Unauthorized ledger modification (add/delete transactions)
- **Mitigation**:
  - Git commit signatures (GPG signed commits)
  - Ledger repo access restricted (SSH key-based auth)
  - Nightly reconciliation detects drift (±1bp tolerance)
  - Alert on reconciliation failure

#### Repudiation
- **Threat**: User denies ledger transaction
- **Mitigation**:
  - Git history is immutable (commit hashes)
  - Every API result includes `ledger_commit_hash`
  - Audit log links API actions to ledger commits

#### Information Disclosure
- **Threat**: Ledger repo leak exposes full transaction history
- **Mitigation**:
  - Ledger repo encrypted at rest (LUKS or dm-crypt)
  - Git remote mirror in private repo (no public access)
  - Access logs for ledger repo

---

## Attack Scenarios & Mitigations

### Scenario 1: Cross-User Data Access (IDOR)

**Attack**:
1. User A obtains User B's `portfolio_id` (e.g., via URL parameter)
2. User A sends request to `/execute` with User B's `portfolio_id`

**Mitigation**:
- RLS policy on `portfolios` table: `WHERE user_id = current_setting('app.user_id')::uuid`
- Executor sets `app.user_id` before every query
- Query returns 0 rows for User B's portfolio (User A sees 403)
- IDOR fuzz tests in CI (100 attempts → 100 failures)

**Test**:
```python
def test_idor_fuzz():
    for i in range(100):
        user_a = create_user()
        user_b = create_user()
        portfolio_b = create_portfolio(user_b)

        resp = client.post("/execute",
            json={"pattern_id": "portfolio_overview", "portfolio_id": portfolio_b.id},
            headers={"Authorization": f"Bearer {user_a.token}"}
        )
        assert resp.status_code == 403
        assert "portfolio" not in resp.json()  # No leakage
```

---

### Scenario 2: Pricing Pack Tampering

**Attack**:
1. Attacker modifies pricing pack to inflate portfolio values
2. User makes investment decision based on false valuations

**Mitigation**:
- Pricing pack immutability enforced (no UPDATE permission)
- Pack hash computed on creation (SHA-256 of all prices/FX)
- Every API result includes `pricing_pack_id` (audit trail)
- Property tests ensure immutability

**Test**:
```python
def test_pack_immutability():
    pack = create_pack()
    with pytest.raises(ImmutabilityError):
        pack.prices[0].close = 999.99
        db.session.commit()
```

---

### Scenario 3: API Key Leakage

**Attack**:
1. API key leaked in error message or log
2. Attacker uses key to exhaust provider quota

**Mitigation**:
- Secrets in vault/env only (never code/config)
- Structured logging with redaction rules
- Sentry redacts secrets from error payloads
- FMP bandwidth alarms (70%/85%/95% of quota)

**Test**:
```python
def test_no_secrets_in_logs(caplog):
    os.environ["FMP_API_KEY"] = "secret123"
    with caplog.at_level(logging.ERROR):
        fetch_fundamentals("AAPL")
    assert "secret123" not in caplog.text
```

---

### Scenario 4: Provider Outage DoS

**Attack**:
1. FMP API goes down
2. All portfolio requests fail (cascade failure)

**Mitigation**:
- Circuit breaker (3 failures → OPEN for 60s)
- Fallback to last-good data (stale panel markers)
- DLQ for failed requests (replay after recovery)
- Chaos tests (provider outage → no crashes)

**Test**:
```python
def test_provider_outage_chaos():
    mock_fmp_down()
    resp = client.post("/execute", json={"pattern_id": "portfolio_overview"})
    assert resp.status_code == 200
    assert resp.json()["fundamentals"]["stale"] is True
    assert "FMP unavailable" in resp.json()["fundamentals"]["message"]
```

---

### Scenario 5: Rights Registry Bypass

**Attack**:
1. User exports PDF with NewsAPI data (not licensed for export)
2. Violates provider terms of service

**Mitigation**:
- Rights registry enforced in staging from S1-W2
- Block export or apply watermark per provider license
- Rights drills in CI (NewsAPI export → blocked)

**Test**:
```python
def test_rights_newsapi_blocked():
    portfolio = create_portfolio_with_news()
    with pytest.raises(RightsViolationError):
        generate_portfolio_pdf(portfolio.id)
```

---

## Security Testing Requirements

### Phase 0 (Foundation)
- [ ] SAST/SCA CI job green (no High/Critical vulns, no copyleft)
- [ ] `.security/THREAT_MODEL.md` reviewed by team
- [ ] Secret scanning enabled (GitHub Advanced Security or gitleaks)

### Sprint 1 Week 1 (Truth Spine)
- [ ] RLS unit tests 100% coverage (14 portfolio-scoped tables)
- [ ] IDOR fuzz tests (100 cross-user attempts → 100 failures)
- [ ] Pricing pack immutability property tests

### Sprint 1 Week 2 (Observability + Rights)
- [ ] Rights gate blocks NewsAPI export (staging)
- [ ] Sentry initialized (no PII in error bodies)
- [ ] Audit log for all mutations

### Sprint 3 Week 6 (Alerts + DLQ)
- [ ] Chaos test: Redis outage → DLQ replay (no dupes)
- [ ] Chaos test: Provider outage → circuit breaker engages

### Sprint 4 Week 8 (Final)
- [ ] Penetration test (external security audit)
- [ ] Rights drills (FMP-only/NewsAPI blocked)
- [ ] Load test (200 concurrent users → no DoS)

---

## Compliance Checklist

**Authentication & Authorization**:
- [x] OAuth with trusted providers (Google/GitHub)
- [x] Short-lived JWT tokens (15-minute expiry)
- [x] RLS on all portfolio-scoped tables
- [x] IDOR prevention (fuzz tests in CI)

**Data Protection**:
- [x] Encrypted backups (AES-256)
- [x] Secrets in vault/env (never code)
- [x] TLS 1.3 for all external calls
- [x] No PII in logs or error bodies

**Audit & Logging**:
- [x] Audit log for all mutations (append-only)
- [x] Structured JSON logs with trace correlation
- [x] Every result includes `pricing_pack_id` + `ledger_commit_hash`

**Provider Compliance**:
- [x] Rights registry enforced (export licensing)
- [x] FMP bandwidth alarms (quota monitoring)
- [x] Circuit breakers (3 failures → OPEN)

**Incident Response**:
- [x] Sentry for error tracking
- [x] Prometheus alerts → PagerDuty
- [x] Monthly restore drill (backup integrity)

---

## Open Risks & Mitigations

| Risk | Severity | Mitigation | Status |
|------|----------|------------|--------|
| RLS bypass via ORM bug | High | Unit tests + IDOR fuzz | ✅ Covered |
| Pricing pack tampering | High | Immutability + hash verification | ✅ Covered |
| API key leakage | High | Secrets manager + log redaction | ✅ Covered |
| Provider outage DoS | Medium | Circuit breakers + DLQ | ✅ Covered |
| Rights registry bypass | Medium | Staging enforcement + drills | ✅ Covered (S1-W2) |
| Session fixation | Low | Secure cookie flags + logout | ✅ Covered |
| SQL injection | Low | ORM only (no raw SQL) | ✅ Covered |
| XSS (stored) | Low | React escapes by default | ✅ Covered |

---

## Review & Updates

**Review Schedule**: Quarterly or after major architecture changes
**Next Review**: 2025-01-21
**Owner**: Security Team + Build Architect
**Approvers**: Engineering Lead, Product Owner

**Change Log**:
- 2025-10-21: Initial threat model (v1.0)

---

**Signed**: Security Architect
**Date**: 2025-10-21
