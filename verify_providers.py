#!/usr/bin/env python3
"""
Provider Integration Verification Script

Purpose: Verify that all provider components are properly installed
Updated: 2025-10-23
"""

import sys
import os
from pathlib import Path

def check_file(path, min_lines=0):
    """Check if file exists and has minimum lines."""
    if not os.path.exists(path):
        return False, "Missing"
    
    with open(path, 'r') as f:
        lines = len(f.readlines())
    
    if min_lines > 0 and lines < min_lines:
        return False, f"Too short ({lines} lines)"
    
    return True, f"OK ({lines} lines)"

def main():
    """Verify all provider integration files."""
    print("=" * 80)
    print("PROVIDER INTEGRATION VERIFICATION")
    print("=" * 80)
    print()
    
    repo_root = Path(__file__).resolve().parent

    files = [
        ("backend/app/core/circuit_breaker.py", 400),
        ("backend/app/core/rate_limiter.py", 350),
        ("backend/app/providers/__init__.py", 10),
        ("backend/app/providers/fmp_client.py", 450),
        ("backend/app/providers/polygon_client.py", 400),
        ("backend/app/providers/fred_client.py", 450),
        ("backend/app/services/providers.py", 550),
        ("backend/jobs/build_pricing_pack.py", 600),
        (".ops/RIGHTS_REGISTRY.yaml", 100),
        ("backend/tests/test_providers.py", 500),
        ("PROVIDER_INTEGRATION_GUIDE.md", 500),
        ("PROVIDER_INTEGRATION_COMPLETE.md", 300),
    ]
    
    all_ok = True
    for file_path, min_lines in files:
        full_path = repo_root / file_path
        ok, status = check_file(full_path, min_lines)
        
        symbol = "✅" if ok else "❌"
        print(f"{symbol} {file_path:<50} {status}")
        
        if not ok:
            all_ok = False
    
    print()
    print("=" * 80)
    
    if all_ok:
        print("✅ ALL FILES VERIFIED")
        print()
        print("Next steps:")
        print("1. Set environment variables (FMP_API_KEY, POLYGON_API_KEY, FRED_API_KEY)")
        print("2. Run tests: pytest backend/tests/test_providers.py -v")
        print("3. Build pricing pack: python backend/jobs/build_pricing_pack.py --use-stubs")
        print()
        return 0
    else:
        print("❌ VERIFICATION FAILED - Some files are missing or incomplete")
        return 1

if __name__ == "__main__":
    sys.exit(main())
