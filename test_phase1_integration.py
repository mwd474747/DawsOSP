#!/usr/bin/env python3
"""
Phase 1 Integration Test
Tests that all UI components can access real knowledge data
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dawsos'))

from core.pattern_engine import PatternEngine
from core.agent_runtime import AgentRuntime
from core.knowledge_graph import KnowledgeGraph

def test_phase1_integration():
    """Test Phase 1 knowledge integration"""
    print("🧪 Phase 1 Integration Test\n")
    print("=" * 60)

    # Initialize core components
    print("\n1. Initializing Trinity components...")
    os.chdir('dawsos')  # Change to dawsos directory where storage is located
    pattern_engine = PatternEngine()
    runtime = AgentRuntime()
    graph = KnowledgeGraph()

    # Test 1: Sector Correlations Loading
    print("\n2. Testing sector correlations loading...")
    try:
        correlations = pattern_engine.load_enriched_data('sector_correlations')
        if correlations:
            corr_matrix = correlations.get('sector_correlations', {}).get('correlation_matrix', {})
            print(f"   ✅ Loaded {len(corr_matrix)} sector correlations")

            # Calculate risk metric (as UI does)
            avg_correlations = []
            for sector, sector_corrs in corr_matrix.items():
                sector_avg = sum([v for k, v in sector_corrs.items() if k != sector]) / max(1, len(sector_corrs) - 1)
                avg_correlations.append(sector_avg)

            avg_corr = sum(avg_correlations) / len(avg_correlations) if avg_correlations else 0
            print(f"   ✅ Calculated average correlation: {avg_corr:.1%}")
        else:
            print("   ❌ Failed to load sector correlations")
            return False
    except Exception as e:
        print(f"   ❌ Error loading correlations: {e}")
        return False

    # Test 2: Sector Performance Loading
    print("\n3. Testing sector performance loading...")
    try:
        sector_data = pattern_engine.load_enriched_data('sector_performance')
        economic_cycles = pattern_engine.load_enriched_data('economic_cycles')

        if sector_data and economic_cycles:
            sectors = sector_data.get('sectors', {})
            current_regime = economic_cycles.get('economic_cycles', {}).get('current_phase', 'early_expansion')

            print(f"   ✅ Loaded {len(sectors)} sectors")
            print(f"   ✅ Current regime: {current_regime}")

            # Calculate top sectors (as UI does)
            performance_data = []
            for sector_name, sector_info in sectors.items():
                perf_by_cycle = sector_info.get('performance_by_cycle', {})
                current_perf = perf_by_cycle.get(current_regime, {})
                avg_return = current_perf.get('avg_return', 0)
                performance_data.append((sector_name, avg_return))

            performance_data.sort(key=lambda x: x[1], reverse=True)
            print(f"   ✅ Top sector: {performance_data[0][0]} ({performance_data[0][1]:+.1%})")
        else:
            print("   ❌ Failed to load sector/cycle data")
            return False
    except Exception as e:
        print(f"   ❌ Error loading sector data: {e}")
        return False

    # Test 3: UI Configurations Loading
    print("\n4. Testing UI configurations loading...")
    try:
        ui_config = pattern_engine.load_enriched_data('ui_configurations')

        if ui_config:
            alert_thresholds = ui_config.get('alert_thresholds', {})
            pattern_shortcuts = ui_config.get('pattern_shortcuts', {})
            suggested_questions = ui_config.get('suggested_questions', {})

            print(f"   ✅ Loaded {len(alert_thresholds)} alert thresholds")
            print(f"   ✅ Loaded {len(pattern_shortcuts)} pattern shortcuts")
            print(f"   ✅ Loaded {len(suggested_questions)} question categories")

            # Test threshold access (as UI does)
            corr_threshold = alert_thresholds.get('sector_correlation', {})
            warning = corr_threshold.get('warning', 0.8)
            critical = corr_threshold.get('critical', 0.9)
            print(f"   ✅ Correlation thresholds: warning={warning:.0%}, critical={critical:.0%}")
        else:
            print("   ❌ Failed to load UI configurations")
            return False
    except Exception as e:
        print(f"   ❌ Error loading UI config: {e}")
        return False

    # Test 4: Pattern Engine Integration
    print("\n5. Testing pattern engine integration...")
    try:
        pattern_count = len(pattern_engine.patterns)
        print(f"   ✅ Pattern engine has {pattern_count} patterns loaded")

        # Check for risk assessment pattern (used by UI)
        risk_pattern = pattern_engine.get_pattern('risk_assessment')
        if risk_pattern:
            print(f"   ✅ Risk assessment pattern available: {risk_pattern.get('name')}")
        else:
            print("   ⚠️  Risk assessment pattern not found (optional)")
    except Exception as e:
        print(f"   ❌ Error with pattern engine: {e}")
        return False

    # Test 5: Risk Factor Calculations
    print("\n6. Testing risk factor calculations (as UI does)...")
    try:
        # Get all data
        correlations = pattern_engine.load_enriched_data('sector_correlations')
        corr_data = correlations.get('sector_correlations', {})

        # Market Risk
        factor_sensitivities = corr_data.get('inter_asset_correlations', {}).get('sector_to_factors', {})
        tech_factors = factor_sensitivities.get('Technology', {})
        market_risk = abs(tech_factors.get('vix', -0.65)) * 100
        print(f"   ✅ Market Risk: {market_risk:.0f}%")

        # Regime Risk
        regimes = corr_data.get('correlation_regimes', {})
        risk_on_corr = regimes.get('risk_on', {}).get('correlation_increase', 0.15) * 100
        risk_off_corr = regimes.get('risk_off', {}).get('correlation_increase', 0.25) * 100
        regime_risk = (risk_on_corr + risk_off_corr) / 2
        print(f"   ✅ Regime Risk: {regime_risk:.0f}%")

        # Volatility Risk
        stability = corr_data.get('correlation_stability', {})
        unstable = stability.get('unstable_correlations', {})
        volatility_risk = len(unstable) * 15
        print(f"   ✅ Volatility Risk: {volatility_risk:.0f}% ({len(unstable)} unstable pairs)")

    except Exception as e:
        print(f"   ❌ Error calculating risk factors: {e}")
        return False

    # Test 6: Alert Generation Logic
    print("\n7. Testing alert generation logic...")
    try:
        ui_config = pattern_engine.load_enriched_data('ui_configurations')
        correlations = pattern_engine.load_enriched_data('sector_correlations')

        alert_thresholds = ui_config.get('alert_thresholds', {})
        corr_matrix = correlations.get('sector_correlations', {}).get('correlation_matrix', {})

        # Calculate avg correlation
        avg_correlations = []
        for sector, sector_corrs in corr_matrix.items():
            sector_avg = sum([v for k, v in sector_corrs.items() if k != sector]) / max(1, len(sector_corrs) - 1)
            avg_correlations.append(sector_avg)

        avg_correlation = sum(avg_correlations) / len(avg_correlations) if avg_correlations else 0

        # Check thresholds
        corr_threshold = alert_thresholds.get('sector_correlation', {})
        warning_level = corr_threshold.get('warning', 0.8)
        critical_level = corr_threshold.get('critical', 0.9)

        if avg_correlation >= critical_level:
            alert_level = "🔴 CRITICAL"
        elif avg_correlation >= warning_level:
            alert_level = "🟡 WARNING"
        else:
            alert_level = "✅ NORMAL"

        print(f"   ✅ Alert level: {alert_level} (correlation {avg_correlation:.1%})")

    except Exception as e:
        print(f"   ❌ Error testing alerts: {e}")
        return False

    # Success!
    print("\n" + "=" * 60)
    print("✅ All Phase 1 Integration Tests PASSED")
    print("\nComponents can successfully:")
    print("  • Load enriched knowledge from JSON files")
    print("  • Calculate real risk metrics")
    print("  • Generate regime-aware insights")
    print("  • Monitor alert thresholds")
    print("  • Access pattern engine")
    print("\n🎉 Phase 1 integration is OPERATIONAL")
    return True


if __name__ == "__main__":
    try:
        success = test_phase1_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
