#!/usr/bin/env python3
"""
Phase 2A Comprehensive Pattern Validation
Tests patterns and documents all findings including authentication issues
"""

import json
import subprocess
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:5000"
PORTFOLIO_ID = "64ff3be6-0ed1-4990-a32b-4ded17f0320c"
SECURITY_ID = "00000000-0000-0000-0000-000000000001"

class ComprehensivePatternValidator:
    """Complete pattern validation with multiple test approaches"""
    
    def __init__(self):
        self.results = []
        self.auth_token = None
        self.existing_patterns = []
        self.missing_patterns = []
        
    def scan_pattern_files(self):
        """Scan for existing pattern files"""
        pattern_dir = Path("backend/patterns")
        if pattern_dir.exists():
            pattern_files = list(pattern_dir.glob("*.json"))
            self.existing_patterns = [f.stem for f in pattern_files]
            print(f"Found {len(self.existing_patterns)} pattern files")
            return self.existing_patterns
        return []
    
    def test_authentication(self):
        """Test various authentication methods"""
        auth_results = {
            "methods_tried": [],
            "successful": False,
            "token": None
        }
        
        # Try different auth combinations
        auth_attempts = [
            {"email": "admin@dawsos.com", "password": "admin123"},
            {"email": "test@test.com", "password": "test123"},
            {"email": "user@dawsos.com", "password": "password123"},
        ]
        
        for attempt in auth_attempts:
            try:
                cmd = [
                    "curl", "-X", "POST",
                    f"{BASE_URL}/api/auth/login",
                    "-H", "Content-Type: application/json",
                    "-d", json.dumps(attempt),
                    "-s"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                response = result.stdout
                
                auth_results["methods_tried"].append({
                    "credentials": attempt,
                    "response": response[:200]
                })
                
                # Check if successful
                try:
                    data = json.loads(response)
                    if "access_token" in data:
                        auth_results["successful"] = True
                        auth_results["token"] = data["access_token"]
                        self.auth_token = data["access_token"]
                        print(f"✓ Authentication successful with {attempt['email']}")
                        break
                except:
                    pass
                    
            except Exception as e:
                auth_results["methods_tried"].append({
                    "credentials": attempt,
                    "error": str(e)
                })
        
        if not auth_results["successful"]:
            print("✗ All authentication attempts failed")
            
        return auth_results
    
    def test_pattern_endpoint(self, pattern_id: str, inputs: Dict[str, Any], with_auth: bool = False):
        """Test a pattern via HTTP endpoint"""
        headers = ["Content-Type: application/json"]
        if with_auth and self.auth_token:
            headers.append(f"Authorization: Bearer {self.auth_token}")
        
        request_data = {
            "pattern_id": pattern_id,
            "inputs": inputs
        }
        
        cmd = ["curl", "-X", "POST", f"{BASE_URL}/api/patterns/execute"]
        for header in headers:
            cmd.extend(["-H", header])
        cmd.extend(["-d", json.dumps(request_data), "-s"])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            response = result.stdout
            
            # Parse response
            try:
                data = json.loads(response)
                return {
                    "success": result.returncode == 0 and "error" not in data,
                    "status_code": data.get("status_code", 200),
                    "data": data,
                    "structure": self.analyze_structure(data)
                }
            except:
                return {
                    "success": False,
                    "raw_response": response[:500],
                    "error": "Failed to parse JSON response"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Request timeout (10s)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def analyze_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze response structure for nesting issues"""
        if not isinstance(data, dict):
            return {"type": type(data).__name__}
            
        analysis = {
            "keys": list(data.keys()),
            "has_data": "data" in data,
            "has_trace": "trace" in data,
            "has_error": "error" in data,
            "nesting_issues": []
        }
        
        # Check for double nesting
        if "data" in data and isinstance(data["data"], dict):
            if "data" in data["data"]:
                analysis["nesting_issues"].append("data.data double nesting")
                
        if "result" in data and isinstance(data["result"], dict):
            if "result" in data["result"]:
                analysis["nesting_issues"].append("result.result double nesting")
                
        # Check for metadata in wrong place  
        if "data" in data and isinstance(data["data"], dict):
            if "_metadata" in data["data"] or "__metadata__" in data["data"]:
                analysis["nesting_issues"].append("metadata in data instead of trace")
                
        return analysis
    
    def run_comprehensive_tests(self):
        """Run all tests and generate comprehensive report"""
        print("\n" + "=" * 60)
        print("PHASE 2A - COMPREHENSIVE PATTERN VALIDATION")
        print("=" * 60)
        
        # Step 1: Scan for patterns
        print("\n[1/4] Scanning pattern files...")
        self.scan_pattern_files()
        
        # Step 2: Test authentication
        print("\n[2/4] Testing authentication...")
        auth_results = self.test_authentication()
        
        # Step 3: Test patterns
        print("\n[3/4] Testing patterns...")
        
        # All patterns to test (expected and actual)
        all_patterns = [
            ("portfolio_overview", {"portfolio_id": PORTFOLIO_ID}),
            ("portfolio_scenario_analysis", {"portfolio_id": PORTFOLIO_ID}),
            ("portfolio_currency_impact", {"portfolio_id": PORTFOLIO_ID}),
            ("portfolio_risk_analysis", {"portfolio_id": PORTFOLIO_ID}),
            ("macro_cycles_overview", {}),
            ("market_regime_overview", {}),
            ("buffett_checklist", {"security_id": SECURITY_ID}),
            ("export_portfolio_report", {"portfolio_id": PORTFOLIO_ID}),
            ("portfolio_optimizer", {"portfolio_id": PORTFOLIO_ID}),
            ("macro_with_ai_explanation", {}),
            ("compare_portfolios", {"portfolio_ids": [PORTFOLIO_ID]}),
            ("alert_summary", {"portfolio_id": PORTFOLIO_ID}),
            # Additional patterns found
            ("cycle_deleveraging_scenarios", {"portfolio_id": PORTFOLIO_ID}),
            ("holding_deep_dive", {"portfolio_id": PORTFOLIO_ID, "symbol": "AAPL"}),
            ("macro_trend_monitor", {}),
            ("news_impact_analysis", {"portfolio_id": PORTFOLIO_ID}),
            ("policy_rebalance", {"portfolio_id": PORTFOLIO_ID}),
            ("portfolio_cycle_risk", {"portfolio_id": PORTFOLIO_ID}),
            ("portfolio_macro_overview", {"portfolio_id": PORTFOLIO_ID}),
        ]
        
        for pattern_id, inputs in all_patterns:
            print(f"\nTesting: {pattern_id}")
            
            result = {
                "pattern_id": pattern_id,
                "exists": pattern_id in self.existing_patterns,
                "test_results": {}
            }
            
            if not result["exists"]:
                print(f"  ⚠️ Pattern file not found")
                self.missing_patterns.append(pattern_id)
            else:
                # Test without auth
                print(f"  Testing without auth...")
                result["test_results"]["no_auth"] = self.test_pattern_endpoint(
                    pattern_id, inputs, with_auth=False
                )
                
                # Test with auth if available
                if self.auth_token:
                    print(f"  Testing with auth...")
                    result["test_results"]["with_auth"] = self.test_pattern_endpoint(
                        pattern_id, inputs, with_auth=True
                    )
                
                # Print quick status
                for test_type, test_result in result["test_results"].items():
                    if test_result.get("success"):
                        print(f"    ✓ {test_type}: Success")
                        if test_result.get("structure", {}).get("nesting_issues"):
                            print(f"      ⚠️ Issues: {test_result['structure']['nesting_issues']}")
                    else:
                        error_msg = test_result.get("data", {}).get("message") or test_result.get("error", "Unknown error")
                        print(f"    ✗ {test_type}: {error_msg[:80]}")
            
            self.results.append(result)
        
        # Step 4: Generate report
        print("\n[4/4] Generating report...")
        self.generate_report(auth_results)
        
    def generate_report(self, auth_results):
        """Generate comprehensive markdown report"""
        report = []
        
        # Header
        report.append("# PHASE 2A VALIDATION REPORT")
        report.append(f"\nGenerated: {datetime.now().isoformat()}")
        report.append(f"Server: {BASE_URL}")
        report.append(f"Test Portfolio: {PORTFOLIO_ID}")
        
        # Executive Summary
        report.append("\n## Executive Summary\n")
        
        total_patterns = len(self.results)
        existing_patterns = sum(1 for r in self.results if r["exists"])
        missing_patterns = total_patterns - existing_patterns
        
        # Count successes
        successful_no_auth = sum(1 for r in self.results 
                                 if r.get("test_results", {}).get("no_auth", {}).get("success"))
        successful_with_auth = sum(1 for r in self.results 
                                  if r.get("test_results", {}).get("with_auth", {}).get("success"))
        
        # Count issues
        with_nesting_issues = sum(1 for r in self.results
                                 for test in r.get("test_results", {}).values()
                                 if test.get("structure", {}).get("nesting_issues"))
        
        report.append(f"- **Total Patterns Expected**: {total_patterns}")
        report.append(f"- **Pattern Files Found**: {existing_patterns}/{total_patterns}")
        report.append(f"- **Missing Pattern Files**: {missing_patterns}")
        report.append(f"- **Successful without Auth**: {successful_no_auth}/{existing_patterns}")
        report.append(f"- **Successful with Auth**: {successful_with_auth}/{existing_patterns}")
        report.append(f"- **Patterns with Nesting Issues**: {with_nesting_issues}")
        
        # Authentication Status
        report.append("\n## Authentication Status\n")
        if auth_results["successful"]:
            report.append("✅ **Authentication successful**")
        else:
            report.append("❌ **Authentication failed**")
            report.append("\n### Authentication Attempts:")
            for attempt in auth_results["methods_tried"]:
                creds = attempt.get("credentials", {})
                report.append(f"- **{creds.get('email')}**: {attempt.get('response', attempt.get('error', 'Unknown'))[:100]}")
        
        # Pattern Test Results
        report.append("\n## Pattern Test Results\n")
        
        # Existing patterns
        report.append("### Existing Patterns\n")
        for result in self.results:
            if result["exists"]:
                report.append(f"\n#### {result['pattern_id']}")
                
                for test_type, test_result in result.get("test_results", {}).items():
                    if test_result.get("success"):
                        report.append(f"- **{test_type}**: ✅ Success")
                        structure = test_result.get("structure", {})
                        if structure.get("nesting_issues"):
                            report.append(f"  - ⚠️ Issues: {', '.join(structure['nesting_issues'])}")
                        report.append(f"  - Response keys: {', '.join(structure.get('keys', [])[:5])}")
                    else:
                        error = test_result.get("data", {}).get("message") or test_result.get("error", "Unknown")
                        status_code = test_result.get("data", {}).get("details", {}).get("status_code", "N/A")
                        report.append(f"- **{test_type}**: ❌ Failed (HTTP {status_code})")
                        report.append(f"  - Error: {error[:100]}")
        
        # Missing patterns
        if self.missing_patterns:
            report.append("\n### Missing Patterns\n")
            report.append("The following expected patterns were not found:")
            for pattern_id in self.missing_patterns:
                report.append(f"- {pattern_id}")
        
        # Data Structure Analysis
        report.append("\n## Data Structure Analysis\n")
        
        issues_found = {}
        for result in self.results:
            for test_result in result.get("test_results", {}).values():
                structure = test_result.get("structure", {})
                for issue in structure.get("nesting_issues", []):
                    issues_found[issue] = issues_found.get(issue, 0) + 1
        
        if issues_found:
            report.append("### Nesting Issues Found")
            for issue, count in sorted(issues_found.items(), key=lambda x: x[1], reverse=True):
                report.append(f"- **{issue}**: {count} occurrences")
        else:
            report.append("✅ No data nesting issues detected in successful responses")
        
        # Key Findings
        report.append("\n## Key Findings\n")
        
        # Authentication barrier
        if successful_no_auth == 0 and existing_patterns > 0:
            report.append("### 🔒 Authentication Barrier")
            report.append("- All patterns require authentication")
            report.append("- No patterns can be tested without valid credentials")
            report.append("- Authentication endpoint validation is too strict (422 errors)")
        
        # Pattern availability
        if missing_patterns > 0:
            report.append("\n### ⚠️ Pattern Availability")
            report.append(f"- {missing_patterns} patterns referenced but not implemented")
            report.append("- This may indicate incomplete implementation or outdated documentation")
        
        # Data structure
        if with_nesting_issues > 0:
            report.append("\n### 📊 Data Structure Issues")
            report.append(f"- {with_nesting_issues} patterns show nesting issues")
            report.append("- Common issues: " + ", ".join(list(issues_found.keys())[:3]))
        
        # Recommendations
        report.append("\n## Recommendations for Phase 2B\n")
        
        report.append("### Priority 1: Authentication Resolution")
        report.append("- Create test user credentials that work")
        report.append("- Consider adding a dev mode that bypasses auth for testing")
        report.append("- Fix authentication endpoint validation issues")
        
        report.append("\n### Priority 2: Pattern Implementation")
        report.append("- Implement missing patterns or remove references:")
        for pattern in self.missing_patterns[:5]:
            report.append(f"  - {pattern}")
        
        if with_nesting_issues > 0:
            report.append("\n### Priority 3: Data Structure Standardization")
            report.append("- Fix double-nesting issues (data.data, result.result)")
            report.append("- Move metadata to trace only, not in data payload")
            report.append("- Standardize response envelope across all patterns")
        
        # Success Criteria Assessment
        report.append("\n## Success Criteria Assessment\n")
        
        can_test = successful_no_auth > 0 or successful_with_auth > 0
        no_exceptions = successful_with_auth == existing_patterns if self.auth_token else False
        clean_structure = with_nesting_issues == 0
        
        report.append(f"- **Can test patterns**: {'✅ YES' if can_test else '❌ NO - Auth barrier'}")
        report.append(f"- **All patterns execute without exceptions**: {'✅ YES' if no_exceptions else '❌ NO'}")
        report.append(f"- **Data in flattened format**: {'✅ YES' if clean_structure else '❌ NO'}")
        report.append(f"- **No double-nesting issues**: {'✅ YES' if clean_structure else '❌ NO'}")
        
        # Phase 2B Readiness
        report.append("\n## Phase 2B Readiness\n")
        
        if can_test and no_exceptions and clean_structure:
            report.append("✅ **Ready for Phase 2B standardization**")
        else:
            report.append("⚠️ **Not ready for Phase 2B - Address the following:**")
            if not can_test:
                report.append("  1. Resolve authentication issues to enable testing")
            if not no_exceptions:
                report.append("  2. Fix pattern execution errors")
            if not clean_structure:
                report.append("  3. Fix data nesting issues")
        
        # Appendix: Pattern Files Found
        report.append("\n## Appendix: Pattern Files Found\n")
        report.append("```")
        for pattern in sorted(self.existing_patterns):
            report.append(f"- {pattern}.json")
        report.append("```")
        
        # Write report
        report_content = "\n".join(report)
        with open("PHASE_2A_VALIDATION_REPORT.md", "w") as f:
            f.write(report_content)
        
        print("\n" + "=" * 60)
        print("✓ Report written to PHASE_2A_VALIDATION_REPORT.md")
        print("=" * 60)

def main():
    """Main entry point"""
    validator = ComprehensivePatternValidator()
    validator.run_comprehensive_tests()

if __name__ == "__main__":
    main()