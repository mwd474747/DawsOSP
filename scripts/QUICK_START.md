# Trinity Compliance Checker - Quick Start Guide

## 🚀 Installation

```bash
# 1. Make scripts executable
chmod +x scripts/check_compliance.py
chmod +x scripts/test_compliance_checker.py

# 2. Install pre-commit (optional but recommended)
pip install pre-commit
pre-commit install
```

## 📋 Common Commands

### Check Compliance

```bash
# Basic check
python3 scripts/check_compliance.py

# Strict mode (exit with error on violations)
python3 scripts/check_compliance.py --strict

# JSON output
python3 scripts/check_compliance.py --format json

# Check specific directory
python3 scripts/check_compliance.py --root dawsos/ui
```

### Run Tests

```bash
# Test the compliance checker
python3 scripts/test_compliance_checker.py

# Run with pytest
pytest scripts/test_compliance_checker.py -v
```

### Pre-commit Hooks

```bash
# Run all hooks
pre-commit run --all-files

# Run only compliance check
pre-commit run trinity-compliance --all-files

# Skip hooks (emergency only)
git commit --no-verify
```

## ❌ Violations Detected

### 1. Direct Subscript Access

```python
# ❌ WRONG
agent = runtime.agents['claude']
result = agent.process(context)

# ✅ CORRECT
result = runtime.exec_via_registry('claude', context)
```

### 2. Direct .get() Access

```python
# ❌ WRONG
agent = runtime.agents.get('data_harvester')
if agent:
    result = agent.harvest(request)

# ✅ CORRECT
result = runtime.exec_via_registry('data_harvester', {'request': request})
```

### 3. Direct Method Calls

```python
# ❌ WRONG
agent = runtime.agents['pattern_spotter']
patterns = agent.analyze(data)

# ✅ CORRECT
result = runtime.exec_via_registry('pattern_spotter', {'data': data})
patterns = result.get('patterns', [])
```

## ✅ Whitelisted Classes

These classes CAN access agents directly:
- `AgentRuntime`
- `AgentAdapter`
- `AgentRegistry`
- `TestAgentRuntime`
- `TestTrinityCompliance`

## 📁 Excluded Directories

Automatically skipped:
- `venv/`
- `tests/`
- `__pycache__/`
- `archived_legacy/`
- `storage/backups/`
- `archive/`

## 🔧 Quick Fixes

### Fix Pattern 1: Simple Execution

```python
# Before
agent = runtime.agents['agent_name']
result = agent.process(context)

# After
result = runtime.exec_via_registry('agent_name', context)
```

### Fix Pattern 2: Conditional Execution

```python
# Before
agent = runtime.agents.get('agent_name')
if agent:
    result = agent.process(context)
else:
    result = {'error': 'Agent not found'}

# After
result = runtime.exec_via_registry('agent_name', context)
# Registry handles missing agents automatically
```

### Fix Pattern 3: Method Call Chain

```python
# Before
agent = runtime.agents['data_harvester']
data = agent.fetch('url')
processed = agent.transform(data)

# After
fetch_result = runtime.exec_via_registry('data_harvester', {
    'action': 'fetch',
    'url': 'url'
})
process_result = runtime.exec_via_registry('data_harvester', {
    'action': 'transform',
    'data': fetch_result.get('data')
})
```

## 📊 Output Formats

### Text (Default)

```
======================================================================
  TRINITY COMPLIANCE VIOLATIONS FOUND
======================================================================

/path/to/file.py:
  Line 42:8
    Type: direct_subscript_access
    Code: agent = runtime.agents['claude']
    Fix:  runtime.exec_via_registry('claude', context)
```

### JSON

```json
{
  "files_checked": 59,
  "total_violations": 1,
  "violations": [
    {
      "file_path": "/path/to/file.py",
      "line_number": 42,
      "violation_type": "direct_subscript_access",
      "code_snippet": "agent = runtime.agents['claude']",
      "suggested_fix": "runtime.exec_via_registry('claude', context)"
    }
  ]
}
```

### GitHub Annotations

```
::error file=/path/to/file.py,line=42::direct_subscript_access: agent = runtime.agents['claude']. Fix: runtime.exec_via_registry('claude', context)
```

## 🔍 Current Status

**Last Scan**: October 2, 2025
- **Files Checked**: 59
- **Violations**: 1
- **Compliance**: 98.3%

### Active Violation

**File**: `dawsos/core/pattern_engine.py:168`
```python
# Line 168
return self.runtime.agents[agent_name]  # Legacy fallback

# Suggested Fix
return self.runtime.get_agent_instance(agent_name)
```

## 🛠️ Troubleshooting

### Issue: "No module named 'check_compliance'"
**Solution**: Run from project root
```bash
cd /Users/mdawson/Dawson/DawsOSB
python3 scripts/check_compliance.py
```

### Issue: "Permission denied"
**Solution**: Make executable
```bash
chmod +x scripts/check_compliance.py
```

### Issue: Pre-commit hook fails
**Solution**: Install pre-commit
```bash
pip install pre-commit
pre-commit install
```

### Issue: False positive
**Solution**: Add class to whitelist in `check_compliance.py`
```python
whitelisted_classes = {
    'AgentRuntime',
    'AgentAdapter',
    'AgentRegistry',
    'YourClassName',  # Add here
}
```

## 📚 Resources

- **Full Documentation**: `scripts/README_COMPLIANCE.md`
- **Implementation Report**: `COMPLIANCE_REPORT.md`
- **Test Suite**: `scripts/test_compliance_checker.py`
- **CI/CD Workflow**: `.github/workflows/compliance-check.yml`
- **Pre-commit Config**: `.pre-commit-config.yaml`

## 🎯 Best Practices

1. **Always use registry**: `runtime.exec_via_registry(agent_name, context)`
2. **Run before commit**: `python3 scripts/check_compliance.py`
3. **Install pre-commit**: Catch violations automatically
4. **Fix immediately**: Don't accumulate violations
5. **Test changes**: Run test suite after fixes

## 📞 Support

For issues or questions:
1. Check `scripts/README_COMPLIANCE.md`
2. Review `COMPLIANCE_REPORT.md`
3. Run test suite to validate
4. Check GitHub Actions logs for CI failures
