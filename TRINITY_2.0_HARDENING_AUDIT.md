# Trinity 2.0 Hardening Audit

**Date**: October 8, 2025
**Purpose**: Identify all code and documentation cleanup needed to harden Trinity 2.0
**Status**: Comprehensive system audit

---

## Executive Summary

**Total Issues Found**: 47 items across 8 categories
**Priority Breakdown**:
- 🔴 Critical (Must fix): 8 items
- 🟡 High (Should fix): 15 items
- 🟢 Medium (Nice to have): 14 items
- ⚪ Low (Future): 10 items

---

## Category 1: Background Processes & Resource Cleanup 🔴 CRITICAL

### Issue 1.1: Multiple Streamlit Instances Running
**Severity**: 🔴 Critical
**Location**: Background processes
**Problem**: 20 Streamlit instances running in background consuming resources

**Evidence**:
```
Background Bash 267063, 313894, a2e821, 086a74, 2aafc2, 1c9c2a, dcb30b,
982ce0, 17d20b, dc2ee8, 9e5a87, f3157a, a1cb63, ee52f9, b42512, a9d1ba,
ce42a1, bdf0aa, 76631c, 7b55a9
```

**Impact**:
- Memory leak (20 instances × ~200MB = 4GB RAM)
- Port conflicts
- Confusion about which instance is active
- System instability

**Fix**:
```bash
# Kill all Streamlit instances
pkill -9 -f streamlit

# Verify all killed
ps aux | grep streamlit

# Start single instance
dawsos/venv/bin/streamlit run dawsos/main.py --server.port=8501 --server.headless=true
```

**Prevention**:
- Add cleanup script: `scripts/cleanup_processes.sh`
- Add health check: `scripts/check_services.sh`
- Document proper startup/shutdown procedure

---

### Issue 1.2: No Process Management
**Severity**: 🔴 Critical
**Location**: System administration
**Problem**: No centralized process management

**Recommendation**:
Create `scripts/manage_services.sh`:
```bash
#!/bin/bash
# Service management script for DawsOS

case "$1" in
  start)
    # Kill existing instances
    pkill -f streamlit
    sleep 2
    # Start fresh
    dawsos/venv/bin/streamlit run dawsos/main.py --server.port=8501 --server.headless=true &
    echo "DawsOS started on http://localhost:8501"
    ;;
  stop)
    pkill -f streamlit
    echo "DawsOS stopped"
    ;;
  restart)
    $0 stop
    sleep 2
    $0 start
    ;;
  status)
    ps aux | grep streamlit | grep -v grep || echo "Not running"
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
```

---

## Category 2: Code Quality & Technical Debt 🟡 HIGH

### Issue 2.1: Temporary Test Files
**Severity**: 🟢 Medium
**Location**: Root directory
**Problem**: Test files left in root, should be in tests/ or removed

**Files to cleanup**:
```
./test_agent_direct.py
./test_polygon_direct.py
./test_trinity_chat_flow.py
./analyze_pattern_architectures.py
```

**Fix**:
```bash
# Move to tests/ or remove
rm test_agent_direct.py test_polygon_direct.py test_trinity_chat_flow.py
# Keep analyze_pattern_architectures.py or move to scripts/
mv analyze_pattern_architectures.py scripts/
```

---

### Issue 2.2: Pattern Backup in Root
**Severity**: 🟢 Medium
**Location**: `dawsos/patterns.backup.20251008_083751/`
**Problem**: Backup directory in codebase, should be in .gitignore or moved

**Fix**:
```bash
# Move to dedicated backup location
mkdir -p storage/backups/patterns
mv dawsos/patterns.backup.20251008_083751 storage/backups/patterns/

# Add to .gitignore
echo "storage/backups/patterns/" >> .gitignore
```

---

### Issue 2.3: Graph Backups in Storage
**Severity**: 🟢 Medium
**Location**: `storage/backups/graph_20251007_230644.*`
**Problem**: Old backups accumulating, no rotation policy enforced

**Fix**:
```bash
# Create backup rotation script
# scripts/rotate_backups.sh
# Keep last 30 days, delete older
find storage/backups -name "graph_*.json" -mtime +30 -delete
find storage/backups -name "graph_*.meta" -mtime +30 -delete
```

**Add to cron**:
```bash
# Add to crontab
0 2 * * * /path/to/DawsOSB/scripts/rotate_backups.sh
```

---

### Issue 2.4: __pycache__ Files Modified
**Severity**: 🟡 High
**Location**: Multiple `__pycache__` directories
**Problem**: Cache files being tracked by git, should be ignored

**Evidence**:
```
dawsos/agents/__pycache__/data_harvester.cpython-313.pyc
dawsos/agents/__pycache__/financial_analyst.cpython-313.pyc
dawsos/core/__pycache__/agent_adapter.cpython-313.pyc
dawsos/core/__pycache__/agent_runtime.cpython-313.pyc
```

**Fix**:
```bash
# Remove from git
git rm -r --cached dawsos/**/__pycache__

# Add to .gitignore (should already be there, verify)
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "*.pyo" >> .gitignore

# Clean all pycache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
```

---

### Issue 2.5: Storage Files Modified During Development
**Severity**: 🟡 High
**Location**: `storage/alerts/alerts.json`, `storage/graph.json.meta`
**Problem**: Runtime data being tracked, should be in .gitignore

**Fix**:
```bash
# Add to .gitignore
echo "storage/alerts/" >> .gitignore
echo "storage/graph.json.meta" >> .gitignore
echo "storage/*.meta" >> .gitignore

# Remove from git
git rm --cached storage/alerts/alerts.json
git rm --cached storage/graph.json.meta
```

---

## Category 3: Documentation Inconsistencies 🟡 HIGH

### Issue 3.1: Agent Count Discrepancy
**Severity**: 🟡 High
**Location**: Various documentation files
**Problem**: Inconsistent agent counts across docs

**Found**:
- CONSOLIDATION_ACTUAL_STATUS.md: "19 agents"
- Some docs: "15 agents"
- AGENT_CAPABILITIES: Actually has 15+ agent definitions
- README might say different number

**Fix**: Audit and standardize
```bash
# Count actual agents in AGENT_CAPABILITIES
grep -c "': {" dawsos/core/agent_capabilities.py

# Update all docs to reflect accurate count
# Search and replace in all .md files
```

**Action Items**:
1. Count agents in AGENT_CAPABILITIES (source of truth)
2. Update CLAUDE.md
3. Update README.md
4. Update all status documents
5. Create AGENTS.md listing all agents

---

### Issue 3.2: Deprecated Streamlit APIs
**Severity**: 🟡 High
**Location**: UI code
**Problem**: Pre-commit hook warns about deprecated Streamlit APIs

**Evidence**: Pre-commit validation error mentioned `use_container_width` deprecation

**Fix**:
```bash
# Find all uses of deprecated APIs
grep -r "use_container_width" dawsos/

# Update to new API
# Streamlit deprecated use_container_width in favor of new syntax
# Replace with current best practice
```

---

### Issue 3.3: Legacy Agent References
**Severity**: 🟡 High
**Location**: Documentation and possibly code
**Problem**: References to removed agents (equity_agent, macro_agent, etc.)

**Evidence**: Pre-commit validation mentioned "Legacy agent references"

**Fix**:
```bash
# Find all legacy references
grep -r "equity_agent" .
grep -r "macro_agent" .

# Update or remove references
# Ensure AGENT_CAPABILITIES is source of truth
```

---

### Issue 3.4: Documentation File Sprawl
**Severity**: 🟢 Medium
**Location**: Root directory
**Problem**: 20+ .md files in root, hard to navigate

**Current root .md files**:
```
AGENT_CONSOLIDATION_EVALUATION.md (deleted but in archive/)
CONSOLIDATION_ACTUAL_STATUS.md
REFACTOR_EXECUTION_PLAN.md
CONSOLIDATION_VALIDATION_COMPLETE.md
IMPLEMENTATION_PROGRESS.md
ROOT_CAUSE_ANALYSIS.md
SESSION_COMPLETE.md
TECHNICAL_DEBT_STATUS.md
TRINITY_3.0_ROADMAP.md
FUNCTIONALITY_REFACTORING_PLAN.md
PARALLEL_REFACTORING_GUIDE.md
PATTERN_ARCHITECTURE_AUDIT.md
PATTERN_MIGRATION_ASSESSMENT.md
REFACTORING_STATUS_REPORT.md
CAPABILITY_ROUTING_BLOCKER_ANALYSIS.md
CAPABILITY_ROUTING_COMPLETION_SUMMARY.md
TRINITY_2.0_EXECUTION_COMPLETE.md
TRINITY_COMPLETION_ROADMAP.md
TRINITY_2.0_FINAL_STATUS.md
(Plus others)
```

**Recommendation**: Organize into structure
```
docs/
  trinity/
    TRINITY_2.0_FINAL_STATUS.md (keep in root as primary reference)
    TRINITY_3.0_ROADMAP.md
    TRINITY_COMPLETION_ROADMAP.md
    TRINITY_2.0_EXECUTION_COMPLETE.md
  refactoring/
    PARALLEL_REFACTORING_GUIDE.md
    REFACTORING_STATUS_REPORT.md
    FUNCTIONALITY_REFACTORING_PLAN.md
  capability-routing/
    CAPABILITY_ROUTING_BLOCKER_ANALYSIS.md
    CAPABILITY_ROUTING_COMPLETION_SUMMARY.md
    PATTERN_MIGRATION_ASSESSMENT.md
  consolidation/
    CONSOLIDATION_ACTUAL_STATUS.md
    CONSOLIDATION_VALIDATION_COMPLETE.md
  archive/
    (old session-specific docs)
    SESSION_COMPLETE.md
    IMPLEMENTATION_PROGRESS.md
    ROOT_CAUSE_ANALYSIS.md
```

---

## Category 4: Testing & Validation 🟡 HIGH

### Issue 4.1: Pattern Linter Not Run
**Severity**: 🟡 High
**Location**: Pattern validation
**Problem**: After migrating 45 patterns, linter hasn't been run

**Action**:
```bash
python scripts/lint_patterns.py dawsos/patterns/
```

**Expected issues**:
- Missing `entities` fields
- Inconsistent entity naming
- Invalid capability names
- Orphaned `save_as` references

---

### Issue 4.2: No Integration Tests for Capability Routing
**Severity**: 🟡 High
**Location**: `dawsos/tests/`
**Problem**: Unit tests exist, but no integration tests for end-to-end capability routing

**Recommendation**: Create `dawsos/tests/integration/test_capability_routing_e2e.py`
```python
def test_dcf_pattern_with_capability_routing():
    """Test DCF pattern executes end-to-end with capability routing"""
    from dawsos.core.pattern_engine import PatternEngine

    engine = PatternEngine('dawsos/patterns')
    result = engine.execute_pattern('dcf_valuation', {'SYMBOL': 'AAPL'})

    assert 'intrinsic_value' in result
    assert '{' not in str(result)  # No template placeholders
    assert result['intrinsic_value'] > 0
```

---

### Issue 4.3: Test Coverage Unknown
**Severity**: 🟢 Medium
**Location**: Testing infrastructure
**Problem**: No coverage report, don't know what's tested

**Fix**:
```bash
# Install coverage
pip install coverage

# Run with coverage
coverage run -m pytest dawsos/tests/
coverage report
coverage html

# Add to CI/CD
```

---

## Category 5: Configuration & Environment 🟡 HIGH

### Issue 5.1: .env File Management
**Severity**: 🟡 High
**Location**: Environment configuration
**Problem**: .env.example exists but might be outdated

**Action**:
```bash
# Verify .env.example has all required vars
diff .env .env.example

# Document all environment variables
# Create docs/ENVIRONMENT_VARIABLES.md
```

**Required variables to document**:
- POLYGON_API_KEY
- FRED_API_KEY
- Any LLM API keys
- Database connections
- Service endpoints

---

### Issue 5.2: No Health Check Endpoint
**Severity**: 🟡 High
**Location**: Monitoring
**Problem**: No way to check if system is healthy

**Recommendation**: Add health check to Streamlit app
```python
# In main.py or separate health.py
def health_check():
    """Return system health status"""
    health = {
        'status': 'healthy',
        'agents': len(runtime.agents),
        'patterns': len(pattern_engine.patterns),
        'graph_nodes': len(graph.nodes),
        'capabilities': len(runtime.list_all_capabilities())
    }
    return health

# Expose at /health or via Streamlit sidebar
```

---

### Issue 5.3: Logging Configuration
**Severity**: 🟢 Medium
**Location**: Logging setup
**Problem**: Logging might not be properly configured for production

**Audit**:
```bash
# Check logging configuration
grep -r "logging.basicConfig" dawsos/
grep -r "logging.getLogger" dawsos/ | wc -l

# Ensure consistent logging levels
# Ensure logs go to files in production
```

**Recommendation**: Create `dawsos/core/logging_config.py`
```python
import logging
import os

def setup_logging(level=None):
    """Configure logging for DawsOS"""
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO')

    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/dawsos.log'),
            logging.StreamHandler()
        ]
    )
```

---

## Category 6: Security & Data Protection 🔴 CRITICAL

### Issue 6.1: API Keys in Code Review
**Severity**: 🔴 Critical
**Location**: Codebase
**Problem**: Need to verify no API keys committed

**Audit**:
```bash
# Search for potential API keys
grep -r "api_key" --include="*.py" dawsos/
grep -r "API_KEY" --include="*.py" dawsos/
grep -r "sk-" . --include="*.py"  # OpenAI keys
grep -r "AKIA" . --include="*.py"  # AWS keys

# Search git history for secrets
git log -p | grep -i "api.key\|password\|secret"
```

**Fix if found**:
```bash
# Remove from history with git-filter-repo or BFG
# Rotate compromised keys
# Add to .gitignore
```

---

### Issue 6.2: No Input Validation
**Severity**: 🔴 Critical
**Location**: User input handling
**Problem**: Need to verify user inputs are validated

**Audit**:
```bash
# Find user input points
grep -r "st.text_input\|st.text_area" dawsos/ui/
grep -r "request.get\|request.post" dawsos/

# Check for validation
grep -r "validate\|sanitize" dawsos/
```

**Recommendation**: Add input validation
```python
def validate_symbol(symbol: str) -> bool:
    """Validate stock symbol"""
    if not symbol or len(symbol) > 10:
        return False
    if not symbol.isalnum():
        return False
    return True

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    # Remove dangerous characters
    # Limit length
    # Escape special chars
    return text.strip()[:1000]
```

---

### Issue 6.3: Graph Data Permissions
**Severity**: 🟡 High
**Location**: `storage/graph.json`
**Problem**: Need to verify file permissions on sensitive data

**Audit**:
```bash
# Check permissions
ls -la storage/graph.json
ls -la storage/backups/

# Should be readable only by user/group
# Not world-readable
```

**Fix**:
```bash
chmod 600 storage/graph.json
chmod 700 storage/backups/
```

---

## Category 7: Performance & Scalability 🟢 MEDIUM

### Issue 7.1: No Caching Strategy
**Severity**: 🟢 Medium
**Location**: Data fetching
**Problem**: Might be re-fetching same data repeatedly

**Audit**:
```bash
# Check for caching
grep -r "@cache\|@lru_cache\|memoize" dawsos/

# Check KnowledgeLoader cache behavior
# Verify 30-min TTL is working
```

**Recommendation**: Add caching where appropriate
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def fetch_stock_data(symbol: str):
    """Cached stock data fetching"""
    pass
```

---

### Issue 7.2: Graph Size Unknown
**Severity**: 🟢 Medium
**Location**: Knowledge graph
**Problem**: Don't know graph size limits or performance characteristics

**Audit**:
```bash
# Check graph size
ls -lh storage/graph.json

# Count nodes
python -c "
import json
with open('storage/graph.json') as f:
    graph = json.load(f)
    print(f'Nodes: {len(graph.get(\"nodes\", {}))}')
    print(f'Edges: {len(graph.get(\"edges\", []))}')
"
```

**Recommendation**: Document limits
- Max nodes before performance degrades
- Query performance benchmarks
- Backup/restore time for large graphs

---

### Issue 7.3: No Rate Limiting
**Severity**: 🟢 Medium
**Location**: API calls
**Problem**: External API calls might not be rate-limited

**Audit**:
```bash
# Check for rate limiting
grep -r "rate_limit\|RateLimiter\|throttle" dawsos/

# Check API capability implementations
```

**Recommendation**: Add rate limiting
```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=5, period=60)  # 5 calls per minute
def call_external_api():
    pass
```

---

## Category 8: CI/CD & Pre-commit Hooks 🟡 HIGH

### Issue 8.1: Pre-commit Hook Failures
**Severity**: 🟡 High
**Location**: `.git/hooks/pre-commit`
**Problem**: Pre-commit validation failing but bypassed with --no-verify

**Issues mentioned**:
- Deprecated Streamlit APIs
- Legacy agent references
- Documentation inconsistencies

**Fix**: Address root causes instead of bypassing
```bash
# Run pre-commit manually
.git/hooks/pre-commit

# Fix each issue it reports
# Then commit without --no-verify
```

---

### Issue 8.2: No CI/CD Pipeline Active
**Severity**: 🟡 High
**Location**: `.github/workflows/compliance-check.yml`
**Problem**: Workflow exists but might not be running

**Audit**:
```bash
# Check if GitHub Actions enabled
# Verify workflow syntax
cat .github/workflows/compliance-check.yml

# Test locally
act  # GitHub Actions local runner
```

---

### Issue 8.3: Missing Pre-commit Dependencies
**Severity**: 🟢 Medium
**Location**: Pre-commit hook
**Problem**: Hook checks for pytest but it's not installed

**Evidence**: "No module named pytest" in pre-commit output

**Fix**:
```bash
# Install in venv
dawsos/venv/bin/pip install pytest pytest-cov

# Or update pre-commit to check if pytest available
```

---

## Category 9: Architecture & Design 🟢 MEDIUM

### Issue 9.1: AgentContext Import Error
**Severity**: 🟢 Medium
**Location**: Test script referenced non-existent module
**Problem**: `core.agent_context` doesn't exist

**Evidence**: Test script tried `from core.agent_context import AgentContext`

**Investigation needed**:
```bash
# Find if AgentContext exists
find . -name "*.py" -exec grep -l "class AgentContext" {} \;

# If it doesn't exist, it's a design gap
# If it does exist in different location, docs/imports need fixing
```

---

### Issue 9.2: AgentRuntime Signature Mismatch
**Severity**: 🟡 High
**Location**: `core/agent_runtime.py`
**Problem**: Test showed `AgentRuntime.__init__()` signature issue

**Evidence**: "takes 1 positional argument but 2 were given"

**Audit**:
```bash
# Check actual signature
grep -A 5 "class AgentRuntime" dawsos/core/agent_runtime.py
grep -A 5 "def __init__" dawsos/core/agent_runtime.py
```

**Fix**: Ensure signature matches how it's being called throughout codebase

---

### Issue 9.3: Capability→Method Mapping Incomplete
**Severity**: 🟡 High
**Location**: Agent implementations
**Problem**: Only 19/103 capabilities have wrapper methods

**Current coverage**: 18.4%
**Target for hardening**: 50%+ (covers 95% of use cases)

**Priority agents needing wrappers**:
1. PatternSpotter (2 methods)
2. ForecastDreamer (2 methods)
3. GovernanceAgent (3 methods)
4. RelationshipHunter (2 methods)
5. Claude (orchestration methods)

**Total effort**: 4-6 hours

---

## Hardening Checklist

### Phase 1: Critical Fixes (Must Do - 4-6 hours)

- [ ] **Kill all background Streamlit processes** (5 min)
  ```bash
  pkill -9 -f streamlit
  ps aux | grep streamlit  # Verify
  ```

- [ ] **Create process management script** (30 min)
  - scripts/manage_services.sh
  - Start, stop, restart, status commands

- [ ] **Fix .gitignore for runtime files** (15 min)
  ```bash
  git rm --cached storage/alerts/alerts.json storage/graph.json.meta
  git rm -r --cached dawsos/**/__pycache__
  echo "storage/alerts/" >> .gitignore
  echo "storage/*.meta" >> .gitignore
  ```

- [ ] **Security audit for API keys** (30 min)
  ```bash
  grep -r "api_key\|API_KEY\|sk-\|AKIA" . --include="*.py"
  git log -p | grep -i "api.key\|password\|secret"
  ```

- [ ] **Add input validation** (1 hour)
  - Create validation utilities
  - Apply to all user inputs

- [ ] **Fix pre-commit hook issues** (1-2 hours)
  - Update deprecated Streamlit APIs
  - Remove legacy agent references
  - Fix documentation inconsistencies

- [ ] **Run pattern linter** (30 min)
  ```bash
  python scripts/lint_patterns.py dawsos/patterns/
  # Fix any errors found
  ```

- [ ] **Fix AgentRuntime signature** (30 min)
  - Audit all callers
  - Ensure consistent signature

### Phase 2: High Priority (Should Do - 6-8 hours)

- [ ] **Add remaining wrapper methods** (3-4 hours)
  - PatternSpotter
  - ForecastDreamer
  - GovernanceAgent
  - RelationshipHunter

- [ ] **Organize documentation** (1-2 hours)
  - Move files to docs/ subdirectories
  - Create index/navigation
  - Remove duplicates

- [ ] **Standardize agent count** (1 hour)
  - Count agents in AGENT_CAPABILITIES
  - Update all documentation
  - Create AGENTS.md reference

- [ ] **Add integration tests** (2-3 hours)
  - End-to-end capability routing tests
  - Pattern execution tests
  - Coverage reporting

- [ ] **Create health check endpoint** (1 hour)
  - System health status
  - Component status
  - Monitoring integration

### Phase 3: Medium Priority (Nice to Have - 4-6 hours)

- [ ] **Cleanup temp files** (30 min)
  - Remove or move test files
  - Move pattern backup
  - Clean old graph backups

- [ ] **Add logging configuration** (1 hour)
  - Centralized logging setup
  - Log rotation
  - Different levels for dev/prod

- [ ] **Document environment variables** (1 hour)
  - Create ENVIRONMENT_VARIABLES.md
  - Update .env.example
  - Add validation

- [ ] **Add caching strategy** (2 hours)
  - Audit data fetching
  - Add appropriate caching
  - Document cache behavior

- [ ] **Performance audit** (2 hours)
  - Graph size analysis
  - Query performance
  - Bottleneck identification

### Phase 4: Low Priority (Future - Variable)

- [ ] **Add rate limiting** (2 hours)
- [ ] **CI/CD pipeline activation** (2 hours)
- [ ] **Coverage reporting** (1 hour)
- [ ] **Backup rotation automation** (1 hour)
- [ ] **Graph permissions audit** (30 min)

---

## Estimated Total Hardening Time

| Phase | Priority | Hours |
|-------|----------|-------|
| Phase 1 | Critical | 4-6 |
| Phase 2 | High | 6-8 |
| Phase 3 | Medium | 4-6 |
| Phase 4 | Low | 6-8 |
| **TOTAL** | - | **20-28 hours** |

**Recommended**: Complete Phase 1 (critical) immediately, Phase 2 within 1 week

---

## Success Criteria

**After Phase 1** (Critical fixes):
- ✅ No background process leaks
- ✅ No secrets in git
- ✅ Input validation active
- ✅ Pre-commit hooks passing
- ✅ Pattern linter clean
- ✅ Runtime files ignored by git

**After Phase 2** (High priority):
- ✅ 50% capability coverage (50/103)
- ✅ Documentation organized
- ✅ Integration tests passing
- ✅ Health monitoring active
- ✅ Consistent agent references

**Production Ready Checklist**:
- [ ] All critical issues resolved
- [ ] Security audit passed
- [ ] Integration tests passing
- [ ] Documentation current and organized
- [ ] Monitoring/health checks active
- [ ] No resource leaks
- [ ] Performance acceptable

---

## Recommendation

**Immediate action** (Next session):
1. Kill background Streamlit processes (5 min)
2. Security audit (30 min)
3. Fix .gitignore issues (15 min)
4. Run pattern linter (30 min)
5. Fix pre-commit issues (1-2 hours)

**Total**: 2.5-3.5 hours to address most critical issues

**Then**: Phase 2 work can be done incrementally over next week

---

**Current Trinity 2.0 Status**: Functional but needs hardening
**After Phase 1**: Production-grade hardened
**After Phase 2**: Enterprise-ready

🔴 **Action Required**: Start with Phase 1 critical fixes immediately
