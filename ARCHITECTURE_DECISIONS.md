# Architecture Decision Records (ADR) - Database Pool Refactoring

## ADR-001: Unified Database Pool Management

### Status
Proposed (October 30, 2025)

### Context
The DawsOS application has evolved with multiple disconnected database initialization patterns:
1. `combined_server.py` creates its own asyncpg pool directly
2. Backend agents expect `get_db_pool()` from RedisPoolCoordinator pattern
3. Redis is unavailable in deployment (connection errors)
4. Agents are failing with "Database pool not initialized" errors
5. Circuit breakers are opening, causing cascading failures

The application architecture follows: Pattern Orchestrator → Agent Runtime → Services → Database

### Decision
We will implement the "Share the Pool" approach:
- Bridge the `combined_server.py` pool to the backend PoolManager singleton
- Remove Redis dependency for pool coordination (not needed for monolithic deployment)
- Maintain single pool instance shared across all components

### Rationale

#### Why "Share the Pool" Over Alternatives

**Option 1: Share the Pool (CHOSEN)**
- ✅ Minimal code changes (15-30 minutes implementation)
- ✅ Preserves pattern orchestrator architecture
- ✅ Matches monolithic deployment reality
- ✅ No new dependencies required

**Option 2: Complete Migration to Backend Pattern**
- ❌ Requires rewriting all database functions in combined_server.py
- ❌ High risk of introducing new bugs
- ❌ Time consuming (days of work)
- ❌ Disrupts working functionality

**Option 3: Add Redis and Use Coordinator**
- ❌ Adds unnecessary infrastructure dependency
- ❌ Redis coordination designed for microservices, not monolith
- ❌ Increases operational complexity
- ❌ Redis currently failing in deployment

### Consequences

#### Positive
- Immediate fix for production errors
- All 52 agent capabilities become functional
- Circuit breakers can be reset
- Pattern orchestrator can execute with real data
- Simpler architecture without Redis dependency

#### Negative
- Temporary coupling between combined_server and backend patterns
- Need to ensure import order is correct
- Pool configuration must be consistent

#### Risks
- Pool exhaustion if connection limits too low (mitigated by current settings)
- Thread safety concerns (mitigated by asyncpg's thread-safe design)

---

## ADR-002: Monolithic vs Microservices Architecture

### Status
Accepted (Implicit in current deployment)

### Context
The application was designed with microservices patterns (Redis coordination, separate pools per module) but is deployed as a monolith (single Python process).

### Decision
Acknowledge monolithic deployment reality and optimize for it:
- Single shared database pool
- Direct function calls instead of network hops
- Simplified error handling
- No inter-service authentication needed

### Rationale
- Simpler to deploy and operate
- Lower latency (no network calls between services)
- Easier debugging (single process)
- Appropriate for current scale and team size

### Consequences
- Cannot scale services independently
- All components share same resource limits
- Deployment affects entire application
- Future microservices migration will require refactoring

---

## ADR-003: Pattern Orchestrator as Central Coordinator

### Status
Accepted (October 2025)

### Context
Business logic can be embedded in code or externalized as configuration. The application uses 12 JSON workflow patterns to define business logic.

### Decision
All API endpoints route through Pattern Orchestrator:
- Business logic defined in JSON patterns
- Agents execute capabilities as directed by patterns
- Services provide low-level functionality

### Rationale
- Business logic changes don't require code changes
- Consistent execution model
- Easier to test and validate
- Clear separation of concerns

### Consequences
- Additional abstraction layer
- Need to maintain pattern definitions
- Debugging requires understanding pattern flow
- Performance overhead from orchestration

---

## ADR-004: Error Handling Strategy

### Status
Accepted with modifications

### Context
The application has multiple error handling approaches:
- Circuit breakers in agent runtime
- Try-catch with fallbacks in combined_server
- Mock data fallbacks when database unavailable

### Decision
Implement consistent error handling:
1. Database errors: Log and return structured error response
2. Agent failures: Circuit breaker after 5 failures, 60s timeout
3. Pattern failures: Return partial results with error details
4. API errors: Structured error responses with correlation IDs

### Rationale
- Predictable error behavior
- Prevents cascading failures
- Maintains partial functionality during outages
- Better debugging with structured errors

### Consequences
- Need to maintain circuit breaker state
- Partial results may confuse users
- Error recovery logic adds complexity

---

## ADR-005: Database Schema Evolution

### Status
Under Review

### Context
Multiple schema definitions exist:
- DATA_ARCHITECTURE.md documentation
- Actual PostgreSQL schema
- Code expectations (missing tables)
- Seed data requirements

Missing tables identified:
- portfolio_daily_values
- portfolio_metrics
- currency_attribution
- factor_exposures
- notifications
- scenario_shocks
- position_factor_betas
- dar_history

### Decision
Implement schema reconciliation:
1. Audit actual database schema
2. Create missing tables based on code requirements
3. Update DATA_ARCHITECTURE.md to match reality
4. Implement proper migration strategy

### Rationale
- Code expects these tables to exist
- Features are failing due to missing tables
- Documentation should match implementation

### Consequences
- Need careful migration planning
- Potential data loss if not handled properly
- Downtime during migration

---

## Implementation Priority

### Phase 1: Immediate (Today)
1. Implement pool sharing bridge
2. Reset circuit breakers
3. Test core functionality

### Phase 2: Short-term (This Week)
1. Remove Redis dependency
2. Consolidate database functions
3. Update documentation

### Phase 3: Medium-term (Next Month)
1. Schema reconciliation
2. Complete seed data
3. Performance optimization

### Phase 4: Long-term (Next Quarter)
1. Consider microservices if scale demands
2. Implement proper service mesh
3. Add distributed tracing

---

## Lessons Learned

### What Went Wrong
1. **Evolution without coordination**: Different parts of the system evolved independently
2. **Pattern mismatch**: Microservices patterns in monolithic deployment
3. **Missing integration tests**: Pool initialization issues not caught
4. **Documentation drift**: Implementation diverged from documentation

### What to Improve
1. **Regular architecture reviews**: Ensure components stay aligned
2. **Integration testing**: Test complete flow, not just units
3. **Documentation as code**: Keep docs next to implementation
4. **Deployment matching design**: Either go microservices or simplify to monolith

### Best Practices Going Forward
1. **One source of truth**: Single place for each concern
2. **Fail fast**: Detect issues early in startup
3. **Explicit dependencies**: Clear service initialization order
4. **Monitoring first**: Know when things break

---

## Decision Log

| Date | Decision | Rationale | Impact |
|------|----------|-----------|--------|
| Oct 22, 2025 | Add PoolManager singleton | Ensure single pool instance | Medium |
| Oct 24, 2025 | Add RedisPoolCoordinator | Fix module instance issues | High |
| Oct 29, 2025 | Create combined_server.py | Unified entry point | High |
| Oct 30, 2025 | Share the Pool refactoring | Fix production errors | Critical |

---

## References
- [AsyncPG Documentation](https://magicstack.github.io/asyncpg/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Database Connection Pooling Best Practices](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [Monolith First](https://martinfowler.com/bliki/MonolithFirst.html)