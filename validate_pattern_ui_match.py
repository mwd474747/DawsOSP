#!/usr/bin/env python3
"""
Pattern-UI DataPath Validation Script
Verifies that UI dataPaths match actual pattern outputs
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Define the UI dataPath expectations from patternRegistry
UI_DATAPATHS = {
    'portfolio_overview': {
        'performance_strip': 'perf_metrics',
        'nav_chart': 'historical_nav',
        'currency_attr': 'currency_attr',
        'sector_alloc': 'sector_allocation',
        'holdings_table': 'valued_positions.positions'  # Potentially problematic
    },
    'portfolio_scenario_analysis': {
        'scenario_impact': 'scenario_result',
        'position_deltas': 'scenario_result.position_deltas',
        'winners_losers': 'scenario_result',
        'hedge_cards': 'hedge_suggestions.suggestions'
    },
    'portfolio_cycle_risk': {
        'cycle_risk_summary': 'risk_summary',  # Missing in pattern
        'vulnerabilities': 'vulnerabilities'    # Missing in pattern
    },
    'news_impact_analysis': {
        'news_summary': 'summary',  # Should be 'impact_analysis'
        'news_items': 'news_items'
    },
    'buffett_checklist': {
        'quality_score': 'moat_strength',
        'moat_analysis': 'moat_strength',
        'dividend_safety': 'dividend_safety',
        'resilience': 'resilience'
    },
    'policy_rebalance': {
        'rebalance_summary': 'summary',  # Should be 'rebalance_result'
        'trade_proposals': 'trades'      # Should be 'rebalance_result.trades'
    },
    'macro_cycles_overview': {
        'stdc_panel': 'stdc',
        'ltdc_panel': 'ltdc',
        'empire_panel': 'empire',
        'civil_panel': 'civil'
    },
    'macro_trend_monitor': {
        'trends_grid': 'trends',        # Missing in pattern
        'indicators_chart': 'indicators' # Missing in pattern
    },
    'holding_deep_dive': {
        'holding_metrics': 'metrics',    # Missing in pattern
        'fundamentals': 'fundamentals'
    }
}

def extract_pattern_outputs(pattern_file: Path) -> Tuple[Set[str], Dict]:
    """Extract outputs from pattern JSON file"""
    with open(pattern_file) as f:
        pattern = json.load(f)
    
    outputs = set()
    step_outputs = {}
    
    # Get explicitly declared outputs
    if 'outputs' in pattern:
        if isinstance(pattern['outputs'], list):
            outputs.update(pattern['outputs'])
        elif isinstance(pattern['outputs'], dict):
            # Handle structured outputs
            for key in pattern['outputs']:
                if key not in ['panels']:  # Skip display metadata
                    outputs.add(key)
    
    # Extract outputs from steps
    for step in pattern.get('steps', []):
        output_name = step.get('as')
        if output_name:
            outputs.add(output_name)
            step_outputs[output_name] = {
                'capability': step.get('capability'),
                'args': step.get('args', {}),
                'condition': step.get('condition')
            }
    
    return outputs, step_outputs

def validate_datapath(datapath: str, outputs: Set[str]) -> Tuple[bool, str]:
    """Check if a datapath can be resolved from available outputs"""
    parts = datapath.split('.')
    root = parts[0]
    
    if root not in outputs:
        return False, f"Root '{root}' not found in pattern outputs"
    
    if len(parts) > 1:
        # Nested path - would need runtime validation
        return True, f"Nested path '{datapath}' - requires runtime validation"
    
    return True, "Direct match"

def analyze_pattern(pattern_name: str, pattern_file: Path) -> Dict:
    """Analyze a single pattern for UI compatibility"""
    if not pattern_file.exists():
        return {
            'status': 'ERROR',
            'message': f'Pattern file not found: {pattern_file}'
        }
    
    outputs, step_outputs = extract_pattern_outputs(pattern_file)
    ui_expectations = UI_DATAPATHS.get(pattern_name, {})
    
    results = {
        'pattern': pattern_name,
        'file': str(pattern_file),
        'outputs': sorted(outputs),
        'ui_expectations': ui_expectations,
        'mismatches': [],
        'warnings': [],
        'status': 'OK'
    }
    
    for panel, datapath in ui_expectations.items():
        is_valid, message = validate_datapath(datapath, outputs)
        
        if not is_valid:
            results['mismatches'].append({
                'panel': panel,
                'expected': datapath,
                'issue': message,
                'severity': 'HIGH'
            })
            results['status'] = 'MISMATCH'
        elif 'requires runtime validation' in message:
            results['warnings'].append({
                'panel': panel,
                'datapath': datapath,
                'note': message
            })
    
    return results

def generate_fix_recommendations(results: List[Dict]) -> List[Dict]:
    """Generate specific fix recommendations"""
    fixes = []
    
    for result in results:
        if result.get('status') == 'MISMATCH':
            pattern = result['pattern']
            
            for mismatch in result.get('mismatches', []):
                if pattern == 'portfolio_cycle_risk':
                    if mismatch['expected'] == 'risk_summary':
                        fixes.append({
                            'pattern': pattern,
                            'type': 'ADD_AGGREGATION',
                            'description': 'Add risk_summary aggregation step',
                            'solution': 'Create aggregation from cycle_risk_map data'
                        })
                    elif mismatch['expected'] == 'vulnerabilities':
                        fixes.append({
                            'pattern': pattern,
                            'type': 'ADD_COMPUTATION',
                            'description': 'Add vulnerabilities analysis',
                            'solution': 'Compute from factor_exposures and dar'
                        })
                
                elif pattern == 'news_impact_analysis':
                    if mismatch['expected'] == 'summary':
                        fixes.append({
                            'pattern': pattern,
                            'type': 'UI_PATH_CHANGE',
                            'description': "Change UI dataPath from 'summary' to 'impact_analysis'",
                            'file': 'full_ui.html',
                            'line': '~2997'
                        })
                
                elif pattern == 'policy_rebalance':
                    if mismatch['expected'] == 'summary':
                        fixes.append({
                            'pattern': pattern,
                            'type': 'UI_PATH_CHANGE',
                            'description': "Change UI dataPath from 'summary' to 'rebalance_result'",
                            'file': 'full_ui.html',
                            'line': '~3043'
                        })
                    elif mismatch['expected'] == 'trades':
                        fixes.append({
                            'pattern': pattern,
                            'type': 'UI_PATH_CHANGE',
                            'description': "Change UI dataPath from 'trades' to 'rebalance_result.trades'",
                            'file': 'full_ui.html',
                            'line': '~3049'
                        })
    
    return fixes

def main():
    """Run the validation"""
    patterns_dir = Path('backend/patterns')
    
    print("=" * 80)
    print("PATTERN-UI DATAPATH VALIDATION REPORT")
    print("=" * 80)
    print()
    
    all_results = []
    
    for pattern_name in UI_DATAPATHS.keys():
        pattern_file = patterns_dir / f"{pattern_name}.json"
        result = analyze_pattern(pattern_name, pattern_file)
        all_results.append(result)
        
        print(f"\n{'='*60}")
        print(f"Pattern: {pattern_name}")
        print(f"File: {pattern_file}")
        print(f"Status: {result['status']}")
        
        if result['status'] == 'OK':
            print("✅ All dataPaths match")
        else:
            print(f"Outputs found: {', '.join(result['outputs'])}")
            
            if result['mismatches']:
                print("\n❌ MISMATCHES:")
                for m in result['mismatches']:
                    print(f"  - Panel '{m['panel']}' expects '{m['expected']}'")
                    print(f"    Issue: {m['issue']}")
            
            if result['warnings']:
                print("\n⚠️  WARNINGS:")
                for w in result['warnings']:
                    print(f"  - {w['datapath']}: {w['note']}")
    
    # Generate summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    total = len(all_results)
    ok_count = sum(1 for r in all_results if r['status'] == 'OK')
    mismatch_count = sum(1 for r in all_results if r['status'] == 'MISMATCH')
    error_count = sum(1 for r in all_results if r['status'] == 'ERROR')
    
    print(f"Total patterns checked: {total}")
    print(f"✅ OK: {ok_count}")
    print(f"❌ Mismatches: {mismatch_count}")
    print(f"🔥 Errors: {error_count}")
    
    # Generate fixes
    fixes = generate_fix_recommendations(all_results)
    if fixes:
        print(f"\n{'='*80}")
        print("RECOMMENDED FIXES")
        print(f"{'='*80}")
        
        for i, fix in enumerate(fixes, 1):
            print(f"\n{i}. Pattern: {fix['pattern']}")
            print(f"   Type: {fix['type']}")
            print(f"   Description: {fix['description']}")
            if 'file' in fix:
                print(f"   File: {fix['file']}, Line: {fix['line']}")
            if 'solution' in fix:
                print(f"   Solution: {fix['solution']}")
    
    # Save results to JSON
    output_file = 'pattern_ui_validation_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'results': all_results,
            'summary': {
                'total': total,
                'ok': ok_count,
                'mismatches': mismatch_count,
                'errors': error_count
            },
            'fixes': fixes
        }, f, indent=2)
    
    print(f"\n📄 Full results saved to: {output_file}")
    
    # Return exit code based on results
    return 0 if mismatch_count == 0 and error_count == 0 else 1

if __name__ == '__main__':
    exit(main())