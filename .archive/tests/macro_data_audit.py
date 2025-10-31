#!/usr/bin/env python3
"""
Comprehensive Macro Dashboard Data Audit Tool
Tests all data points and analyzes data flow
"""

import json
import requests
from datetime import datetime
from typing import Dict, Any, Tuple

def login() -> str:
    """Login and get JWT token"""
    response = requests.post(
        "http://localhost:5000/auth/login",
        json={"email": "michael@dawsos.com", "password": "admin123"}
    )
    return response.json().get("access_token", "")

def fetch_macro_data(token: str) -> Dict[str, Any]:
    """Fetch macro cycles overview data"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        "http://localhost:5000/execute",
        json={"pattern": "macro_cycles_overview", "inputs": {}},
        headers=headers
    )
    return response.json()

def audit_stdc_data(data: Dict[str, Any]) -> Tuple[int, int]:
    """Audit Short-Term Debt Cycle data"""
    print("\n═══════════════════════════════════════════════════════")
    print("  SHORT-TERM DEBT CYCLE (5-8 YEARS)")
    print("═══════════════════════════════════════════════════════")
    
    result = data.get("result", {})
    stdc_metrics = result.get("stdc_metrics", {})
    indicators = result.get("indicators", {})
    
    # Merge both sources of data
    stdc_data = {**indicators, **stdc_metrics}
    
    fields = {
        "gdp_growth": "GDP Growth",
        "interest_rate": "Interest Rate", 
        "inflation": "Inflation Rate",
        "unemployment": "Unemployment",
        "vix": "Market Volatility (VIX)",
        "dollar_index": "Dollar Index"
    }
    
    populated = 0
    total = len(fields)
    
    for field, label in fields.items():
        value = stdc_data.get(field)
        if value is not None:
            populated += 1
            if field in ["gdp_growth", "interest_rate", "inflation", "unemployment"]:
                print(f"  ✅ {label:25s}: {value:6.2f}%")
            else:
                print(f"  ✅ {label:25s}: {value:6.2f}")
        else:
            print(f"  ❌ {label:25s}: MISSING")
    
    phase = result.get("stdc_phase", "UNKNOWN")
    print(f"  📍 Current Phase: {phase}")
    
    return populated, total

def audit_ltdc_data(data: Dict[str, Any]) -> Tuple[int, int]:
    """Audit Long-Term Debt Cycle data"""
    print("\n═══════════════════════════════════════════════════════")
    print("  LONG-TERM DEBT CYCLE (75-100 YEARS)")
    print("═══════════════════════════════════════════════════════")
    
    result = data.get("result", {})
    debt_metrics = result.get("debt_metrics", {})
    
    fields = {
        "debt_to_gdp": "Total Debt/GDP",
        "credit_growth": "Credit Growth",
        "credit_impulse": "Credit Impulse",
        "real_rates": "Real Interest Rates",
        "productivity_growth": "Productivity Growth",
        "interest_burden": "Interest Burden"
    }
    
    populated = 0
    total = len(fields)
    
    for field, label in fields.items():
        value = debt_metrics.get(field)
        if value is not None:
            populated += 1
            if field == "debt_to_gdp":
                print(f"  ✅ {label:25s}: {value:6.1f}%")
            else:
                print(f"  ✅ {label:25s}: {value:6.2f}%")
        else:
            print(f"  ❌ {label:25s}: MISSING")
    
    phase = result.get("ltdc_phase", "UNKNOWN")
    deleveraging = result.get("deleveraging_score")
    
    print(f"  📍 Current Phase: {phase}")
    if deleveraging:
        print(f"  🏦 Deleveraging Score: {deleveraging}")
    
    return populated, total

def audit_empire_data(data: Dict[str, Any]) -> Tuple[int, int]:
    """Audit Empire Cycle data"""
    print("\n═══════════════════════════════════════════════════════")
    print("  EMPIRE CYCLE (250 YEARS)")
    print("═══════════════════════════════════════════════════════")
    
    result = data.get("result", {})
    empire_indicators = result.get("empire_indicators", {})
    
    fields = {
        "education_score": "Education Score",
        "innovation_score": "Innovation Score",
        "competitiveness_score": "Competitiveness",
        "economic_output_share": "Global GDP Share",
        "world_trade_share": "Trade Share",
        "military_strength": "Military Strength",
        "financial_center_score": "Financial Hub Score",
        "reserve_currency_share": "Reserve Currency"
    }
    
    populated = 0
    total = len(fields)
    
    for field, label in fields.items():
        value = empire_indicators.get(field)
        if value is not None:
            populated += 1
            if field.endswith("_share"):
                print(f"  ✅ {label:25s}: {value:6.2f}%")
            else:
                print(f"  ✅ {label:25s}: {value:6.1f}")
        else:
            print(f"  ❌ {label:25s}: MISSING")
    
    phase = result.get("empire_phase", "UNKNOWN")
    score = result.get("empire_score")
    
    print(f"  📍 Current Phase: {phase}")
    if score:
        print(f"  📊 Empire Score: {score:.1f}")
    
    return populated, total

def audit_internal_data(data: Dict[str, Any]) -> Tuple[int, int]:
    """Audit Internal Order/Disorder Cycle data"""
    print("\n═══════════════════════════════════════════════════════")
    print("  INTERNAL ORDER/DISORDER CYCLE")
    print("═══════════════════════════════════════════════════════")
    
    result = data.get("result", {})
    
    fields = {
        "wealth_gap": ("Wealth Gap (Gini)", "gini"),
        "political_polarization": ("Political Polarization", "score"),
        "social_unrest": ("Social Unrest Score", "score"),
        "fiscal_deficit": ("Fiscal Deficit", "deficit"),
        "civil_war_probability": ("Civil War Risk", "percent")
    }
    
    populated = 0
    total = len(fields)
    
    for field, (label, fmt) in fields.items():
        value = result.get(field)
        if value is not None:
            populated += 1
            if fmt == "gini":
                print(f"  ✅ {label:25s}: {value:.3f}")
            elif fmt == "deficit":
                print(f"  ✅ {label:25s}: {value:6.2f}% GDP")
            elif fmt == "percent":
                print(f"  ✅ {label:25s}: {value:6.1f}%")
            else:
                print(f"  ✅ {label:25s}: {value:6.1f}/100")
        else:
            print(f"  ❌ {label:25s}: MISSING")
    
    stage = result.get("internal_stage_name", "UNKNOWN")
    print(f"  📍 Current Stage: {stage}")
    
    return populated, total

def analyze_data_flow(data: Dict[str, Any]) -> None:
    """Analyze overall data flow and quality"""
    print("\n═══════════════════════════════════════════════════════")
    print("  DATA FLOW ANALYSIS")
    print("═══════════════════════════════════════════════════════")
    
    result = data.get("result", {})
    
    # Check key components
    components = {
        "indicators": "Core Indicators",
        "stdc_metrics": "STDC Metrics",
        "debt_metrics": "Debt Metrics",
        "empire_indicators": "Empire Indicators",
        "recommendations": "AI Recommendations",
        "portfolio_risk_assessment": "Risk Assessment"
    }
    
    for key, label in components.items():
        if key in result and result[key]:
            count = len(result[key]) if isinstance(result[key], (dict, list)) else 1
            print(f"  ✅ {label:25s}: Present ({count} items)")
        else:
            print(f"  ❌ {label:25s}: Missing")
    
    # Check regime detection
    print("\n  🎯 Regime Detection:")
    print(f"    • Overall Regime: {result.get('regime', 'UNKNOWN')}")
    print(f"    • Risk Level: {result.get('risk_level', 'UNKNOWN')}")
    print(f"    • Trend: {result.get('trend', 'UNKNOWN')}")

def main():
    """Run comprehensive audit"""
    print("\n" + "="*60)
    print("    COMPREHENSIVE MACRO DASHBOARD DATA AUDIT")
    print("="*60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Login
    token = login()
    if not token:
        print("\n❌ Authentication failed!")
        return
    
    print("\n✅ Authentication successful")
    
    # Fetch data
    print("📊 Fetching macro cycles data...")
    data = fetch_macro_data(token)
    
    if data.get("status") != "success":
        print("\n❌ Failed to fetch data!")
        print(f"Error: {data}")
        return
    
    # Audit each cycle
    stdc_pop, stdc_total = audit_stdc_data(data)
    ltdc_pop, ltdc_total = audit_ltdc_data(data)
    empire_pop, empire_total = audit_empire_data(data)
    internal_pop, internal_total = audit_internal_data(data)
    
    # Analyze data flow
    analyze_data_flow(data)
    
    # Summary
    print("\n═══════════════════════════════════════════════════════")
    print("  DATA QUALITY SUMMARY")
    print("═══════════════════════════════════════════════════════")
    
    total_populated = stdc_pop + ltdc_pop + empire_pop + internal_pop
    total_fields = stdc_total + ltdc_total + empire_total + internal_total
    coverage = (total_populated / total_fields * 100) if total_fields > 0 else 0
    
    print(f"\n  📊 Coverage by Cycle:")
    print(f"    • Short-Term Debt: {stdc_pop}/{stdc_total} ({stdc_pop/stdc_total*100:.1f}%)")
    print(f"    • Long-Term Debt: {ltdc_pop}/{ltdc_total} ({ltdc_pop/ltdc_total*100:.1f}%)")
    print(f"    • Empire Cycle: {empire_pop}/{empire_total} ({empire_pop/empire_total*100:.1f}%)")
    print(f"    • Internal Cycle: {internal_pop}/{internal_total} ({internal_pop/internal_total*100:.1f}%)")
    
    print(f"\n  📈 Overall:")
    print(f"    • Total Fields: {total_fields}")
    print(f"    • Populated: {total_populated}")
    print(f"    • Missing: {total_fields - total_populated}")
    print(f"    • Coverage: {coverage:.1f}%")
    
    if coverage >= 90:
        print(f"\n  ✅ Status: EXCELLENT - All systems operational")
    elif coverage >= 75:
        print(f"\n  ⚠️  Status: GOOD - Minor data gaps")
    else:
        print(f"\n  ❌ Status: NEEDS ATTENTION - Significant data missing")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()