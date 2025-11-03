#!/usr/bin/env python3
"""
Phase 2 Validation Script
Tests all critical changes from Phase 2 refactoring

Purpose: Validate pattern orchestrator fix, agent stability, and corporate actions
Created: 2025-11-03
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:5000"
PORTFOLIO_ID = "64ff3be6-0ed1-4990-a32b-4ded17f0320c"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTAwMSIsImVtYWlsIjoibWljaGFlbEBkYXdzb3MuY29tIiwiZXhwIjoxNzQzNzA0MTExfQ.rC3hP8WlBxs3BaJUxIztNJL-q0H_VDYhXd6XjKexBL8"

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_result(test_name: str, status: str, details: str = ""):
    """Log test result with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    icon = "✅" if status == "passed" else "❌" if status == "failed" else "⚠️"
    print(f"[{timestamp}] {icon} {test_name}: {details}")
    
    if status == "passed":
        test_results["passed"].append(test_name)
    elif status == "failed":
        test_results["failed"].append((test_name, details))
    else:
        test_results["warnings"].append((test_name, details))


async def test_pattern_execution(client: httpx.AsyncClient, pattern_name: str, inputs: Dict[str, Any]) -> bool:
    """Test a single pattern execution."""
    try:
        response = await client.post(
            f"{BASE_URL}/api/patterns/execute",
            json={
                "pattern": pattern_name,
                "inputs": inputs
            },
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            timeout=30.0
        )
        
        if response.status_code != 200:
            log_result(f"Pattern: {pattern_name}", "failed", f"Status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check for nested storage bug (result.result.data)
        def check_nesting(obj, path=""):
            """Recursively check for double-nested structures."""
            if isinstance(obj, dict):
                if "result" in obj and isinstance(obj["result"], dict):
                    if "result" in obj["result"]:
                        return False, f"Double nesting found at {path}.result.result"
                for key, value in obj.items():
                    valid, msg = check_nesting(value, f"{path}.{key}" if path else key)
                    if not valid:
                        return False, msg
            return True, ""
        
        valid, nesting_msg = check_nesting(data)
        if not valid:
            log_result(f"Pattern: {pattern_name}", "failed", f"Nested storage bug: {nesting_msg}")
            return False
        
        # Check for required fields based on pattern
        if pattern_name == "portfolio_overview":
            result_data = data.get("data", {})
            required = ["historical_nav", "sector_allocation", "currency_attr"]
            missing = [field for field in required if field not in result_data]
            if missing:
                log_result(f"Pattern: {pattern_name}", "warning", f"Missing fields: {missing}")
                return False
        
        log_result(f"Pattern: {pattern_name}", "passed", "Executed successfully")
        return True
        
    except Exception as e:
        log_result(f"Pattern: {pattern_name}", "failed", str(e))
        return False


async def test_critical_patterns():
    """Test the most affected patterns from nested storage fix."""
    print("\n" + "="*60)
    print("TESTING CRITICAL PATTERNS")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        # Test portfolio_overview - most affected pattern
        success = await test_pattern_execution(
            client,
            "portfolio_overview",
            {"portfolio_id": PORTFOLIO_ID, "lookback_days": 252}
        )
        
        # Test holding_deep_dive if we have a security_id
        # Note: This requires a valid security_id from the portfolio
        
        # Test export_portfolio_report
        success = await test_pattern_execution(
            client,
            "export_portfolio_report",
            {
                "portfolio_id": PORTFOLIO_ID,
                "include_holdings": True,
                "include_performance": True,
                "include_macro": False
            }
        )


async def test_all_patterns():
    """Quick smoke test of all patterns."""
    print("\n" + "="*60)
    print("TESTING ALL PATTERNS (SMOKE TEST)")
    print("="*60)
    
    patterns = [
        ("buffett_checklist", {"portfolio_id": PORTFOLIO_ID}),
        ("cycle_deleveraging_scenarios", {"portfolio_id": PORTFOLIO_ID}),
        ("macro_cycles_overview", {}),
        ("macro_trend_monitor", {}),
        ("news_impact_analysis", {"portfolio_id": PORTFOLIO_ID, "days_back": 7}),
        ("policy_rebalance", {
            "portfolio_id": PORTFOLIO_ID,
            "policies": [{"type": "target_allocation", "category": "risk", "value": 0.3}],
            "constraints": {"max_te_pct": 2.0, "max_turnover_pct": 10.0}
        }),
        ("portfolio_cycle_risk", {"portfolio_id": PORTFOLIO_ID}),
        ("portfolio_macro_overview", {"portfolio_id": PORTFOLIO_ID}),
        ("portfolio_scenario_analysis", {
            "portfolio_id": PORTFOLIO_ID,
            "scenario": "RATE_HIKE"
        }),
    ]
    
    async with httpx.AsyncClient() as client:
        for pattern_name, inputs in patterns:
            await test_pattern_execution(client, pattern_name, inputs)


async def test_corporate_actions():
    """Test corporate actions endpoint validation."""
    print("\n" + "="*60)
    print("TESTING CORPORATE ACTIONS ENDPOINT")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Without portfolio_id (should fail with 422)
        try:
            response = await client.get(
                f"{BASE_URL}/api/corporate-actions",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
            )
            if response.status_code == 422:
                log_result("Corporate Actions: Missing portfolio_id", "passed", "Returns 422 as expected")
            else:
                log_result("Corporate Actions: Missing portfolio_id", "failed", f"Expected 422, got {response.status_code}")
        except Exception as e:
            log_result("Corporate Actions: Missing portfolio_id", "failed", str(e))
        
        # Test 2: With invalid portfolio_id (should fail with 400)
        try:
            response = await client.get(
                f"{BASE_URL}/api/corporate-actions",
                params={"portfolio_id": "invalid-uuid"},
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
            )
            if response.status_code == 400:
                log_result("Corporate Actions: Invalid UUID", "passed", "Returns 400 as expected")
            else:
                log_result("Corporate Actions: Invalid UUID", "failed", f"Expected 400, got {response.status_code}")
        except Exception as e:
            log_result("Corporate Actions: Invalid UUID", "failed", str(e))
        
        # Test 3: With valid portfolio_id (should return empty array)
        try:
            response = await client.get(
                f"{BASE_URL}/api/corporate-actions",
                params={"portfolio_id": PORTFOLIO_ID},
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
            )
            if response.status_code == 200:
                data = response.json()["data"]
                if len(data.get("actions", [])) == 0 and "metadata" in data:
                    log_result("Corporate Actions: Valid request", "passed", "Returns empty array with metadata")
                else:
                    log_result("Corporate Actions: Valid request", "warning", "Unexpected response structure")
            else:
                log_result("Corporate Actions: Valid request", "failed", f"Status {response.status_code}")
        except Exception as e:
            log_result("Corporate Actions: Valid request", "failed", str(e))


async def check_server_health():
    """Check if server is running and agents initialized properly."""
    print("\n" + "="*60)
    print("CHECKING SERVER HEALTH")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            # Check root endpoint
            response = await client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                log_result("Server Health", "passed", "Server is running")
            else:
                log_result("Server Health", "failed", f"Status {response.status_code}")
                return False
            
            # Check if we can authenticate
            response = await client.get(
                f"{BASE_URL}/api/portfolios",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
            )
            if response.status_code in [200, 404]:  # 404 is ok if no portfolios
                log_result("Authentication", "passed", "Auth token valid")
            else:
                log_result("Authentication", "failed", f"Status {response.status_code}")
                
        except Exception as e:
            log_result("Server Health", "failed", str(e))
            return False
    
    return True


async def main():
    """Run all validation tests."""
    print("="*60)
    print("PHASE 2 VALIDATION SUITE")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Server: {BASE_URL}")
    print(f"Portfolio: {PORTFOLIO_ID}")
    
    # Check server health first
    if not await check_server_health():
        print("\n❌ Server is not healthy. Please ensure DawsOS is running.")
        return 1
    
    # Run test suites
    await test_critical_patterns()
    await test_corporate_actions()
    await test_all_patterns()
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    print(f"⚠️  Warnings: {len(test_results['warnings'])}")
    
    if test_results["failed"]:
        print("\nFailed Tests:")
        for test_name, details in test_results["failed"]:
            print(f"  - {test_name}: {details}")
    
    if test_results["warnings"]:
        print("\nWarnings:")
        for test_name, details in test_results["warnings"]:
            print(f"  - {test_name}: {details}")
    
    # Return exit code
    return 0 if len(test_results["failed"]) == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)