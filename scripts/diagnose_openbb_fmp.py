#!/usr/bin/env python3
"""
Deep diagnostic of OpenBB + FMP integration
Find root cause of import failure
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*60)
print("OpenBB + FMP Integration Diagnostic")
print("="*60)
print()

# Step 1: Check OpenBB installation
print("1. Checking OpenBB installation...")
try:
    import openbb
    version = getattr(openbb, '__version__', 'unknown')
    print(f"   ✅ openbb version: {version}")
except ImportError as e:
    print(f"   ❌ OpenBB not installed: {e}")
    sys.exit(1)

# Step 2: Check openbb-core
print("\n2. Checking openbb-core...")
try:
    import openbb_core
    version = getattr(openbb_core, '__version__', 'unknown')
    print(f"   ✅ openbb-core version: {version}")
except ImportError as e:
    print(f"   ❌ openbb-core not installed: {e}")
    sys.exit(1)

# Step 3: Check provider_interface module
print("\n3. Checking provider_interface module...")
try:
    from openbb_core.app import provider_interface
    print(f"   ✅ provider_interface module found")
    print(f"   Available attributes:")
    attrs = [a for a in dir(provider_interface) if not a.startswith('_')]
    for attr in attrs[:20]:  # First 20
        print(f"      - {attr}")
    if len(attrs) > 20:
        print(f"      ... and {len(attrs) - 20} more")
except ImportError as e:
    print(f"   ❌ provider_interface import failed: {e}")

# Step 4: Check for OBBject_EquityInfo
print("\n4. Checking for OBBject_EquityInfo...")
try:
    from openbb_core.app.provider_interface import OBBject_EquityInfo
    print(f"   ✅ OBBject_EquityInfo found: {OBBject_EquityInfo}")
except ImportError as e:
    print(f"   ❌ OBBject_EquityInfo NOT FOUND: {e}")
    print(f"   This is the root cause!")

# Step 5: Check OpenBB equity module
print("\n5. Checking OpenBB equity module...")
try:
    from openbb import obb
    print(f"   ✅ obb instance created")
    print(f"   obb.equity exists: {hasattr(obb, 'equity')}")
    if hasattr(obb, 'equity'):
        print(f"   obb.equity.price exists: {hasattr(obb.equity, 'price')}")
        if hasattr(obb.equity, 'price'):
            print(f"   obb.equity.price.quote exists: {hasattr(obb.equity.price, 'quote')}")
except Exception as e:
    print(f"   ❌ Error accessing obb.equity: {e}")

# Step 6: Try actual FMP quote
print("\n6. Attempting FMP quote (will likely fail)...")
try:
    from openbb import obb
    result = obb.equity.price.quote('AAPL', provider='yfinance')
    print(f"   ✅ yfinance quote succeeded!")
    print(f"   Result type: {type(result)}")
except Exception as e:
    print(f"   ❌ Quote failed: {e}")
    print(f"   Error type: {type(e).__name__}")

# Step 7: Check what's actually in provider_interface
print("\n7. Detailed provider_interface inspection...")
try:
    from openbb_core.app import provider_interface

    # Look for OBBject classes
    obbject_classes = [a for a in dir(provider_interface) if 'OBBject' in a or 'Obbject' in a]
    if obbject_classes:
        print(f"   Found OBBject classes: {obbject_classes}")
    else:
        print(f"   ❌ No OBBject classes found")

    # Look for any equity-related classes
    equity_classes = [a for a in dir(provider_interface) if 'equity' in a.lower() or 'quote' in a.lower()]
    if equity_classes:
        print(f"   Found equity-related classes: {equity_classes}")
    else:
        print(f"   No equity-related classes found")

except Exception as e:
    print(f"   ❌ Error: {e}")

# Step 8: Check openbb-yfinance specifically
print("\n8. Checking openbb-yfinance provider...")
try:
    import openbb_yfinance
    version = getattr(openbb_yfinance, '__version__', 'unknown')
    print(f"   ✅ openbb-yfinance version: {version}")
except ImportError as e:
    print(f"   ❌ openbb-yfinance not installed: {e}")

# Step 9: Check openbb-fmp specifically
print("\n9. Checking openbb-fmp provider...")
try:
    import openbb_fmp
    version = getattr(openbb_fmp, '__version__', 'unknown')
    print(f"   ✅ openbb-fmp version: {version}")
except ImportError as e:
    print(f"   ❌ openbb-fmp not installed: {e}")

print()
print("="*60)
print("Diagnostic Complete")
print("="*60)
