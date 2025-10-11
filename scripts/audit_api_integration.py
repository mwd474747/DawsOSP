#!/usr/bin/env python3
"""Comprehensive API Integration Audit Script

Audits all API capabilities and patterns for:
1. API key loading consistency
2. Error handling patterns
3. Pattern-to-API integration
4. Credential management
5. Validation integration

Identifies issues causing "constant API issues"
"""
import sys
import json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, 'dawsos')

# Results tracking
results = {
    'capabilities': {},
    'patterns_with_api_calls': [],
    'issues': [],
    'summary': {}
}

print("=" * 80)
print("DawsOS API Integration Audit")
print("=" * 80)

# ============================================================================
# PHASE 1: Audit All API Capabilities
# ============================================================================
print("\n📡 PHASE 1: Auditing API Capabilities...")
print("-" * 80)

capabilities = [
    ('fred_data', 'FredDataCapability', 'FRED_API_KEY'),
    ('market_data', 'MarketDataCapability', 'FMP_API_KEY'),
    ('fundamentals', 'FundamentalsCapability', 'FMP_API_KEY'),
    ('news', 'NewsCapability', 'NEWSAPI_KEY'),
    ('crypto', 'CryptoCapability', None),  # No key required
    ('polygon_options', 'PolygonOptionsCapability', 'POLYGON_API_KEY'),
]

for module_name, class_name, key_name in capabilities:
    print(f"\n🔍 Checking {class_name}...")

    try:
        module = __import__(f'capabilities.{module_name}', fromlist=[class_name])
        cls = getattr(module, class_name)

        # Check initialization
        cap_info = {
            'module': module_name,
            'class': class_name,
            'key_required': key_name,
            'issues': []
        }

        # Read source to check patterns
        source_file = Path(f'dawsos/capabilities/{module_name}.py')
        if source_file.exists():
            source = source_file.read_text()

            # Check for credential loading
            if 'get_credential_manager' in source:
                cap_info['uses_credential_manager'] = True
            elif 'os.getenv' in source:
                cap_info['uses_os_getenv'] = True
            else:
                cap_info['uses_credential_manager'] = False
                cap_info['issues'].append('No credential loading found')

            # Check for validation
            if '_validate_' in source or 'ValidationError' in source:
                cap_info['has_validation'] = True
            else:
                cap_info['has_validation'] = False
                cap_info['issues'].append('No Pydantic validation')

            # Check error handling
            if 'try:' in source and 'except' in source:
                cap_info['has_error_handling'] = True
            else:
                cap_info['has_error_handling'] = False
                cap_info['issues'].append('Missing error handling')

        results['capabilities'][module_name] = cap_info

        if cap_info['issues']:
            print(f"  ⚠️  Issues: {', '.join(cap_info['issues'])}")
        else:
            print(f"  ✓ OK")

    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        results['issues'].append(f"{class_name}: {e}")

# ============================================================================
# PHASE 2: Audit All Patterns for API Calls
# ============================================================================
print("\n\n📋 PHASE 2: Auditing Patterns for API Integration...")
print("-" * 80)

pattern_dir = Path('dawsos/patterns')
pattern_files = list(pattern_dir.rglob('*.json'))
pattern_files = [f for f in pattern_files if f.name != 'schema.json']

api_capabilities = [
    'can_fetch_economic_data',
    'can_fetch_stock_data',
    'can_fetch_news',
    'can_fetch_fundamentals',
    'can_fetch_crypto_price',
    'can_fetch_options_data'
]

for pattern_file in pattern_files:
    try:
        with open(pattern_file) as f:
            pattern = json.load(f)

        # Check if pattern uses API capabilities
        pattern_info = {
            'file': str(pattern_file.relative_to('dawsos/patterns')),
            'id': pattern.get('id', 'unknown'),
            'api_steps': []
        }

        for i, step in enumerate(pattern.get('steps', [])):
            capability = step.get('capability', '')

            # Check if this step involves API calls
            if any(api_cap in capability for api_cap in api_capabilities):
                pattern_info['api_steps'].append({
                    'step': i,
                    'capability': capability,
                    'action': step.get('action', 'unknown')
                })

        if pattern_info['api_steps']:
            results['patterns_with_api_calls'].append(pattern_info)

    except Exception as e:
        print(f"  ❌ Error reading {pattern_file.name}: {e}")
        results['issues'].append(f"Pattern {pattern_file.name}: {e}")

print(f"\nFound {len(results['patterns_with_api_calls'])} patterns with API calls")

# ============================================================================
# PHASE 3: Check Credential Manager Integration
# ============================================================================
print("\n\n🔑 PHASE 3: Checking Credential Manager...")
print("-" * 80)

try:
    from core.credentials import CredentialManager, get_credential_manager

    cred_mgr = get_credential_manager()

    print(f"\nSupported Keys:")
    for key_name in cred_mgr.SUPPORTED_KEYS:
        key_info = cred_mgr.SUPPORTED_KEYS[key_name]
        has_key = bool(cred_mgr.get(key_name, required=False))
        status = "✓ SET" if has_key else "✗ NOT SET"
        print(f"  {status} {key_name}: {key_info['description']}")

except Exception as e:
    print(f"❌ Credential Manager Error: {e}")
    results['issues'].append(f"Credential Manager: {e}")

# ============================================================================
# PHASE 4: Generate Summary Report
# ============================================================================
print("\n\n" + "=" * 80)
print("AUDIT SUMMARY")
print("=" * 80)

print(f"\n📊 Capabilities Audited: {len(results['capabilities'])}")
validation_count = sum(1 for c in results['capabilities'].values() if c.get('has_validation', False))
print(f"   - With Pydantic validation: {validation_count}/{len(results['capabilities'])}")

cred_mgr_count = sum(1 for c in results['capabilities'].values() if c.get('uses_credential_manager', False))
print(f"   - Using credential manager: {cred_mgr_count}/{len(results['capabilities'])}")

issue_count = sum(len(c.get('issues', [])) for c in results['capabilities'].values())
print(f"   - Total issues found: {issue_count}")

print(f"\n📋 Patterns with API Calls: {len(results['patterns_with_api_calls'])}")

print(f"\n🔴 Critical Issues: {len(results['issues'])}")
for issue in results['issues']:
    print(f"   - {issue}")

# ============================================================================
# PHASE 5: Specific Issue Detection
# ============================================================================
print("\n\n🔍 PHASE 5: Detecting Common API Issues...")
print("-" * 80)

issues_found = []

# Issue 1: Check if .env file exists
env_file = Path('dawsos/.env')
if not env_file.exists():
    issues_found.append("CRITICAL: dawsos/.env file does not exist")
    print("❌ CRITICAL: dawsos/.env file does not exist")
else:
    print("✓ dawsos/.env file exists")

    # Check if keys are populated
    env_content = env_file.read_text()
    if 'FRED_API_KEY=' in env_content and 'FRED_API_KEY=\n' in env_content:
        issues_found.append("WARNING: FRED_API_KEY is empty in .env")
        print("⚠️  WARNING: FRED_API_KEY is empty in .env")

# Issue 2: Check for inconsistent API key loading
inconsistent_loading = []
for name, info in results['capabilities'].items():
    if info.get('key_required') and not info.get('uses_credential_manager'):
        inconsistent_loading.append(name)

if inconsistent_loading:
    issues_found.append(f"Inconsistent credential loading in: {', '.join(inconsistent_loading)}")
    print(f"⚠️  WARNING: Inconsistent credential loading in: {', '.join(inconsistent_loading)}")

# Issue 3: Check for missing validation
missing_validation = [name for name, info in results['capabilities'].items()
                      if not info.get('has_validation', False)]
if missing_validation:
    issues_found.append(f"Missing validation in: {', '.join(missing_validation)}")
    print(f"⚠️  WARNING: Missing Pydantic validation in: {', '.join(missing_validation)}")

# ============================================================================
# FINAL RECOMMENDATIONS
# ============================================================================
print("\n\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

if not env_file.exists():
    print("\n1. CREATE .env FILE:")
    print("   cp .env.example dawsos/.env")
    print("   # Then add your API keys to dawsos/.env")

if 'FRED_API_KEY is empty' in str(issues_found):
    print("\n2. ADD API KEYS to dawsos/.env:")
    print("   FRED_API_KEY=your_key_here")
    print("   FMP_API_KEY=your_key_here")
    print("   NEWSAPI_KEY=your_key_here")

if inconsistent_loading:
    print("\n3. STANDARDIZE CREDENTIAL LOADING:")
    print("   All capabilities should use get_credential_manager()")

if missing_validation:
    print("\n4. ADD PYDANTIC VALIDATION:")
    print(f"   Capabilities missing validation: {', '.join(missing_validation)}")

print("\n" + "=" * 80)
print(f"Audit complete. Found {len(issues_found)} issues.")
print("=" * 80)
