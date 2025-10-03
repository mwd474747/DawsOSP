# Trinity Architecture Compliance Checker

## Overview

The Trinity Compliance Checker is an AST-based static analysis tool that enforces Trinity Architecture principles in DawsOS. It detects violations where code bypasses the agent registry system and directly accesses agents.

## What It Checks

### Violations Detected

1. **Direct Subscript Access** (`runtime.agents[...]`)
   ```python
   # ❌ VIOLATION
   agent = runtime.agents['claude']
   result = agent.process(context)

   # ✅ COMPLIANT
   result = runtime.exec_via_registry('claude', context)
   ```

2. **Direct .get() Access** (`runtime.agents.get(...)`)
   ```python
   # ❌ VIOLATION
   agent = runtime.agents.get('data_harvester')
   if agent:
       result = agent.harvest(request)

   # ✅ COMPLIANT
   result = runtime.exec_via_registry('data_harvester', context)
   ```

3. **Direct Method Calls** (on agents obtained from runtime.agents)
   ```python
   # ❌ VIOLATION
   agent = runtime.agents['pattern_spotter']
   patterns = agent.analyze(data)

   # ✅ COMPLIANT
   result = runtime.exec_via_registry('pattern_spotter', {'data': data})
   patterns = result.get('patterns', [])
   ```

### Whitelisted Contexts

The following classes are **allowed** to access agents directly:

- `AgentRuntime` - Core runtime class
- `AgentAdapter` - Agent wrapper class
- `AgentRegistry` - Registry management
- `TestAgentRuntime` - Test classes
- `TestTrinityCompliance` - Compliance test classes

### Excluded Directories

The checker automatically skips:

- `venv/` - Virtual environment
- `__pycache__/` - Python cache
- `.git/` - Git metadata
- `archived_legacy/` - Archived code
- `storage/backups/` - Backup files
- `archive/` - Archive directory
- `tests/` - Test files (allowed to access agents directly)

## Usage

### Command Line

```bash
# Basic check (text output)
python3 scripts/check_compliance.py

# Strict mode (exit with error if violations found)
python3 scripts/check_compliance.py --strict

# JSON output
python3 scripts/check_compliance.py --format json

# GitHub Actions annotations
python3 scripts/check_compliance.py --format github

# Scan different directory
python3 scripts/check_compliance.py --root dawsos/core

# Exclude additional patterns
python3 scripts/check_compliance.py --exclude "experimental/" --exclude "deprecated/"
```

### Pre-commit Hook

The compliance checker is integrated into pre-commit hooks. Install and configure:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hook scripts
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Run only compliance check
pre-commit run trinity-compliance --all-files
```

### CI/CD Integration

The checker runs automatically on:

- **Pull Requests** to main/develop branches
- **Push** events to main/develop
- **Manual workflow dispatch**

GitHub Actions workflow: `.github/workflows/compliance-check.yml`

## Output Formats

### Text Format (Default)

```
======================================================================
  TRINITY COMPLIANCE VIOLATIONS FOUND
======================================================================

/path/to/file.py:
  Line 42:8
    Type: direct_subscript_access
    Code: agent = runtime.agents['claude']
    Fix:  runtime.exec_via_registry('claude', context)

======================================================================
SUMMARY
======================================================================
Files checked: 59
Total violations: 1
======================================================================
```

### JSON Format

```json
{
  "files_checked": 59,
  "total_violations": 1,
  "violations": [
    {
      "file_path": "/path/to/file.py",
      "line_number": 42,
      "column": 8,
      "violation_type": "direct_subscript_access",
      "code_snippet": "agent = runtime.agents['claude']",
      "suggested_fix": "runtime.exec_via_registry('claude', context)",
      "severity": "error"
    }
  ]
}
```

### GitHub Annotations Format

```
::error file=/path/to/file.py,line=42,col=8::direct_subscript_access: agent = runtime.agents['claude']. Fix: runtime.exec_via_registry('claude', context)
```

## How It Works

### AST Analysis

The checker uses Python's Abstract Syntax Tree (AST) module to:

1. Parse Python source code into an AST
2. Visit each node in the tree
3. Detect specific patterns that violate Trinity Architecture
4. Track variable assignments to detect indirect access
5. Respect whitelisted contexts

### Detection Algorithm

1. **Subscript Detection**: Identifies `runtime.agents[...]` patterns
2. **Method Call Detection**: Identifies `runtime.agents.get(...)` calls
3. **Variable Tracking**: Tracks variables assigned from `runtime.agents`
4. **Method Call Tracking**: Detects agent method calls on tracked variables
5. **Context Awareness**: Skips violations in whitelisted classes

### Example AST Pattern

```python
# Code: runtime.agents['claude']
# AST Structure:
Subscript(
    value=Attribute(
        value=Name(id='runtime'),
        attr='agents'
    ),
    slice=Constant(value='claude')
)
```

## Current Compliance Status

### Latest Scan Results

**Date**: 2025-10-02
**Files Checked**: 59
**Violations Found**: 1

### Violations

1. **`/Users/mdawson/Dawson/DawsOSB/dawsos/core/pattern_engine.py:168`**
   - **Type**: `direct_subscript_access`
   - **Code**: `return self.runtime.agents[agent_name]`
   - **Context**: Fallback path in `_get_agent()` method
   - **Suggested Fix**: `runtime.exec_via_registry(agent_name, context)`
   - **Note**: This is a legacy fallback path in PatternEngine

### Recommended Fixes

#### Pattern Engine (Line 168)

**Current Code**:
```python
def _get_agent(self, agent_name: str):
    """Get agent by name through registry or fallback"""
    if not self.runtime:
        return None

    if hasattr(self.runtime, 'agent_registry'):
        adapter = self.runtime.agent_registry.get_agent(agent_name)
        if adapter:
            return adapter.agent

    if hasattr(self.runtime, 'get_agent_instance'):
        return self.runtime.get_agent_instance(agent_name)

    # Fallback to legacy mapping if exposed
    if hasattr(self.runtime, 'agents') and agent_name in self.runtime.agents:
        return self.runtime.agents[agent_name]  # ❌ VIOLATION

    return None
```

**Recommended Fix** (Option 1 - Remove fallback):
```python
def _get_agent(self, agent_name: str):
    """Get agent by name through registry only"""
    if not self.runtime:
        return None

    if hasattr(self.runtime, 'agent_registry'):
        adapter = self.runtime.agent_registry.get_agent(agent_name)
        if adapter:
            return adapter.agent

    if hasattr(self.runtime, 'get_agent_instance'):
        return self.runtime.get_agent_instance(agent_name)

    # No fallback - enforce registry usage
    return None
```

**Recommended Fix** (Option 2 - Disable warnings):
```python
def _get_agent(self, agent_name: str):
    """Get agent by name through registry or fallback"""
    if not self.runtime:
        return None

    if hasattr(self.runtime, 'agent_registry'):
        adapter = self.runtime.agent_registry.get_agent(agent_name)
        if adapter:
            return adapter.agent

    if hasattr(self.runtime, 'get_agent_instance'):
        return self.runtime.get_agent_instance(agent_name)

    # Fallback with warnings disabled (for migration)
    if hasattr(self.runtime, 'agents') and agent_name in self.runtime.agents:
        if hasattr(self.runtime, 'disable_access_warnings'):
            self.runtime.disable_access_warnings()
        agent = self.runtime.agents.get(agent_name)
        if hasattr(self.runtime, '_access_warnings_enabled'):
            self.runtime._access_warnings_enabled = True
        return agent

    return None
```

## Integration with Development Workflow

### Development Phase

1. Write code following Trinity Architecture
2. Run compliance checker locally: `python3 scripts/check_compliance.py`
3. Fix any violations
4. Commit changes

### Pre-commit Phase

1. Attempt to commit
2. Pre-commit hook runs compliance checker
3. If violations found, commit is blocked
4. Fix violations and retry

### CI/CD Phase

1. Push to remote or create PR
2. GitHub Actions runs compliance checker
3. If violations found:
   - Annotations appear on PR
   - Bot comments with detailed report
   - CI fails, blocking merge
4. Fix violations and push again

## Advanced Usage

### Custom Exclusions

```bash
# Exclude experimental features
python3 scripts/check_compliance.py --exclude "experimental/" --exclude "prototypes/"

# Exclude specific pattern
python3 scripts/check_compliance.py --exclude "legacy_"
```

### Integration in Python Scripts

```python
from pathlib import Path
from check_compliance import check_file, ComplianceReport

# Check a single file
violations = check_file(Path('dawsos/core/agent_runtime.py'))

# Generate report
report = ComplianceReport(violations, 1)
print(report.to_text())
```

### CI/CD Environment Variables

Set these in GitHub Actions:

```yaml
env:
  TRINITY_STRICT_MODE: 'true'  # Enable strict mode in runtime
  PYTHONPATH: ${{ github.workspace }}
```

## Troubleshooting

### False Positives

If the checker flags legitimate code, you can:

1. **Whitelist the class**: Add class name to `whitelisted_classes` in `check_compliance.py`
2. **Exclude the file**: Use `--exclude` flag or add to default excludes
3. **Refactor the code**: Use registry-based access instead

### False Negatives

If code bypasses detection:

1. Report the pattern as an issue
2. Extend the AST visitor to detect it
3. Add test cases to prevent regression

### Common Issues

**Issue**: "No module named 'check_compliance'"
**Solution**: Run from project root: `python3 scripts/check_compliance.py`

**Issue**: "Permission denied"
**Solution**: `chmod +x scripts/check_compliance.py`

**Issue**: Pre-commit hook fails
**Solution**: Ensure pre-commit is installed: `pip install pre-commit && pre-commit install`

## Future Enhancements

- [ ] Support for more complex violation patterns
- [ ] Auto-fix capability (generate patches)
- [ ] IDE integration (VS Code extension)
- [ ] Real-time linting in editor
- [ ] Complexity metrics per file
- [ ] Historical compliance tracking
- [ ] Compliance score dashboard

## References

- [Trinity Architecture Guide](../dawsos/docs/TRINITY_ARCHITECTURE.md)
- [Agent Registry Documentation](../dawsos/docs/AGENT_REGISTRY.md)
- [Python AST Documentation](https://docs.python.org/3/library/ast.html)
- [Pre-commit Framework](https://pre-commit.com/)
