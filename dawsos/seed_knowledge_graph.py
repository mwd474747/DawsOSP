#!/usr/bin/env python3
"""
Seed the knowledge graph with fundamental analysis frameworks
"""
from load_env import load_env
load_env()

import json
from core.knowledge_graph import KnowledgeGraph

def seed_buffett_framework(graph):
    """Seed Buffett investment principles into the graph"""
    print("Seeding Buffett framework...")

    # Load framework
    with open('storage/knowledge/buffett_framework.json', 'r') as f:
        buffett = json.load(f)

    # Create main Buffett entity
    buffett_id = graph.add_node('framework', {
        'name': 'Buffett Investment Framework',
        'type': 'investment_philosophy',
        'creator': 'Warren Buffett',
        'core_principle': 'Buy wonderful companies at fair prices'
    })

    # Add Circle of Competence
    coc_id = graph.add_node('concept', {
        'name': 'Circle of Competence',
        'rule': buffett['buffett_principles']['circle_of_competence']['rule'],
        'questions': buffett['buffett_principles']['circle_of_competence']['questions']
    })
    graph.connect(buffett_id, coc_id, 'includes_concept', metadata={'importance': 'critical'})

    # Add Economic Moat types
    moat_data = buffett['buffett_principles']['economic_moat']
    moat_id = graph.add_node('concept', {
        'name': 'Economic Moat',
        'definition': moat_data['definition']
    })
    graph.connect(buffett_id, moat_id, 'includes_concept', metadata={'importance': 'critical'})

    # Add each moat type
    for moat_type, details in moat_data['types'].items():
        type_id = graph.add_node('moat_type', {
            'name': moat_type.replace('_', ' ').title(),
            'indicators': details['indicators'],
            'examples': details['examples'],
            'metrics': details.get('metrics', []),
            'durability_test': details['durability_test']
        })
        graph.connect(moat_id, type_id, 'has_type', metadata={'category': moat_type})

    # Add Management Quality criteria
    mgmt_data = buffett['buffett_principles']['management_quality']
    mgmt_id = graph.add_node('concept', {
        'name': 'Management Quality',
        'aspects': ['integrity', 'capital_allocation']
    })
    graph.connect(buffett_id, mgmt_id, 'evaluates', metadata={'importance': 'high'})

    # Add Intrinsic Value calculation methods
    value_data = buffett['buffett_principles']['intrinsic_value']
    value_id = graph.add_node('concept', {
        'name': 'Intrinsic Value',
        'methods': list(value_data['valuation_methods'].keys())
    })
    graph.connect(buffett_id, value_id, 'calculates', metadata={'purpose': 'investment_decision'})

    # Add Owner Earnings formula
    owner_earnings_id = graph.add_node('formula', {
        'name': 'Owner Earnings',
        'formula': value_data['owner_earnings']['formula'],
        'adjustments': value_data['owner_earnings']['adjustments'],
        'quality_check': value_data['owner_earnings']['quality_check']
    })
    graph.connect(value_id, owner_earnings_id, 'uses_formula', metadata={'preferred': True})

    print(f"✅ Added Buffett framework with {graph.get_stats()['total_nodes']} nodes")

def seed_dalio_framework(graph):
    """Seed Dalio economic principles into the graph"""
    print("Seeding Dalio framework...")

    # Load framework
    with open('storage/knowledge/dalio_framework.json', 'r') as f:
        dalio = json.load(f)

    # Create main Dalio entity
    dalio_id = graph.add_node('framework', {
        'name': 'Dalio Economic Machine',
        'type': 'economic_framework',
        'creator': 'Ray Dalio',
        'core_principle': 'Economy works like a machine with predictable cycles'
    })

    # Add Three Forces
    forces = dalio['dalio_principles']['economic_machine']['three_forces']

    # Productivity Growth
    prod_id = graph.add_node('economic_force', {
        'name': 'Productivity Growth',
        'driver': forces['productivity_growth']['driver'],
        'growth_rate': forces['productivity_growth']['characteristics']['growth_rate'],
        'investment_implications': forces['productivity_growth']['investment_implications']
    })
    graph.connect(dalio_id, prod_id, 'driven_by', metadata={'type': 'long_term'})

    # Short-term Debt Cycle
    short_cycle = forces['short_term_debt_cycle']
    short_id = graph.add_node('cycle', {
        'name': 'Short-term Debt Cycle',
        'duration': short_cycle['duration'],
        'driver': short_cycle['driver'],
        'phases': list(short_cycle['phases'].keys())
    })
    graph.connect(dalio_id, short_id, 'includes_cycle', metadata={'timeframe': 'short'})

    # Add cycle phases
    for phase_name, phase_data in short_cycle['phases'].items():
        phase_id = graph.add_node('cycle_phase', {
            'name': phase_name,
            'characteristics': phase_data['characteristics'],
            'indicators': phase_data['indicators'],
            'portfolio_positioning': phase_data['portfolio_positioning']
        })
        graph.connect(short_id, phase_id, 'has_phase', metadata={'sequence': phase_name})

    # Long-term Debt Cycle
    long_cycle = forces['long_term_debt_cycle']
    long_id = graph.add_node('cycle', {
        'name': 'Long-term Debt Cycle',
        'duration': long_cycle['duration'],
        'driver': long_cycle['driver'],
        'phases': list(long_cycle['phases'].keys())
    })
    graph.connect(dalio_id, long_id, 'includes_cycle', metadata={'timeframe': 'long'})

    # All-Weather Portfolio
    all_weather = dalio['dalio_principles']['all_weather_portfolio']
    aw_id = graph.add_node('portfolio', {
        'name': 'All-Weather Portfolio',
        'philosophy': all_weather['philosophy'],
        'standard_allocation': all_weather['standard_implementation']
    })
    graph.connect(dalio_id, aw_id, 'recommends_portfolio', metadata={'purpose': 'all_environments'})

    # Add Four Quadrants
    for quadrant_name, quadrant_data in all_weather['four_quadrants'].items():
        quad_id = graph.add_node('market_environment', {
            'name': quadrant_name.replace('_', ' ').title(),
            'environment': quadrant_data['environment'],
            'winners': quadrant_data['winners'],
            'losers': quadrant_data['losers']
        })
        graph.connect(aw_id, quad_id, 'handles_environment', metadata={'risk_allocation': '25%'})

    # Paradigm Shifts
    paradigms = dalio['dalio_principles']['paradigm_shifts']
    paradigm_id = graph.add_node('concept', {
        'name': 'Paradigm Shifts',
        'concept': paradigms['concept'],
        'identification_signals': paradigms['identification_signals']
    })
    graph.connect(dalio_id, paradigm_id, 'recognizes', metadata={'importance': 'critical'})

    print(f"✅ Added Dalio framework, total nodes: {graph.get_stats()['total_nodes']}")

def seed_financial_calculations(graph):
    """Seed financial calculation formulas into the graph"""
    print("Seeding financial calculations...")

    # Load calculations
    with open('storage/knowledge/financial_calculations.json', 'r') as f:
        calcs = json.load(f)

    # Create main calculations entity
    calc_id = graph.add_node('knowledge_base', {
        'name': 'Financial Calculations',
        'type': 'formulas_and_methods',
        'categories': ['buffett_calculations', 'dalio_calculations', 'combined_framework']
    })

    # Add Buffett calculations
    buffett_calcs = calcs['buffett_calculations']

    # Owner Earnings
    owner_id = graph.add_node('calculation', {
        'name': 'Owner Earnings',
        'concept': buffett_calcs['owner_earnings']['concept'],
        'formula': buffett_calcs['owner_earnings']['formula'],
        'steps': buffett_calcs['owner_earnings']['steps'],
        'quality_checks': buffett_calcs['owner_earnings']['quality_checks']
    })
    graph.connect(calc_id, owner_id, 'contains_calculation', metadata={'framework': 'buffett'})

    # Moat Quantification
    moat_calc_id = graph.add_node('calculation', {
        'name': 'Moat Quantification',
        'roic_formula': buffett_calcs['moat_quantification']['roic_calculation']['formula'],
        'roic_vs_wacc': buffett_calcs['moat_quantification']['roic_vs_wacc_spread'],
        'gross_margin_stability': buffett_calcs['moat_quantification']['gross_margin_stability']
    })
    graph.connect(calc_id, moat_calc_id, 'contains_calculation', metadata={'framework': 'buffett'})

    # Intrinsic Value Methods
    iv_methods = buffett_calcs['intrinsic_value_calculations']
    iv_id = graph.add_node('calculation', {
        'name': 'Intrinsic Value Methods',
        'dcf_two_stage': iv_methods['dcf_two_stage'],
        'earnings_power_value': iv_methods['earnings_power_value'],
        'graham_number': iv_methods['graham_number']
    })
    graph.connect(calc_id, iv_id, 'contains_calculation', metadata={'framework': 'buffett'})

    # Add Dalio calculations
    dalio_calcs = calcs['dalio_calculations']

    # Debt Cycle Position
    cycle_calc_id = graph.add_node('calculation', {
        'name': 'Debt Cycle Position',
        'short_term_score': dalio_calcs['debt_cycle_position']['short_term_cycle_score'],
        'long_term_score': dalio_calcs['debt_cycle_position']['long_term_cycle_score']
    })
    graph.connect(calc_id, cycle_calc_id, 'contains_calculation', metadata={'framework': 'dalio'})

    # All-Weather Weights
    aw_calc_id = graph.add_node('calculation', {
        'name': 'All-Weather Risk Parity',
        'risk_parity': dalio_calcs['all_weather_weights']['risk_parity_calculation'],
        'simple_implementation': dalio_calcs['all_weather_weights']['simple_implementation']
    })
    graph.connect(calc_id, aw_calc_id, 'contains_calculation', metadata={'framework': 'dalio'})

    # Combined Framework
    combined = calcs['combined_framework_calculations']

    # Quality-Value Matrix
    matrix_id = graph.add_node('framework', {
        'name': 'Quality-Value Matrix',
        'concept': 'Combine Buffett quality with value investing',
        'quadrants': combined['quality_value_matrix']['quadrants']
    })
    graph.connect(calc_id, matrix_id, 'contains_framework', metadata={'type': 'combined'})

    print(f"✅ Added financial calculations, total nodes: {graph.get_stats()['total_nodes']}")

def seed_investment_examples(graph):
    """Seed example companies and analyses"""
    print("Seeding investment examples...")

    # Add example companies with moat assessments
    examples = [
        {
            'symbol': 'AAPL',
            'name': 'Apple Inc.',
            'moat_type': 'brand_moat',
            'moat_score': 9,
            'owner_earnings_quality': 'Excellent',
            'cycle_sensitivity': 'Moderate'
        },
        {
            'symbol': 'BRK.B',
            'name': 'Berkshire Hathaway',
            'moat_type': 'multiple',
            'moat_score': 10,
            'owner_earnings_quality': 'Excellent',
            'cycle_sensitivity': 'Low'
        },
        {
            'symbol': 'V',
            'name': 'Visa Inc.',
            'moat_type': 'network_effects',
            'moat_score': 10,
            'owner_earnings_quality': 'Excellent',
            'cycle_sensitivity': 'Moderate'
        },
        {
            'symbol': 'COST',
            'name': 'Costco',
            'moat_type': 'cost_advantages',
            'moat_score': 8,
            'owner_earnings_quality': 'Good',
            'cycle_sensitivity': 'Low'
        },
        {
            'symbol': 'MSFT',
            'name': 'Microsoft',
            'moat_type': 'switching_costs',
            'moat_score': 9,
            'owner_earnings_quality': 'Excellent',
            'cycle_sensitivity': 'Moderate'
        }
    ]

    for company in examples:
        company_id = graph.add_node('company', company)

        # Link to moat type
        moat_query = f"moat analysis for {company['symbol']}"
        graph.add_node('analysis_query', {
            'query': moat_query,
            'symbol': company['symbol'],
            'analysis_type': 'moat'
        })

    print(f"✅ Added example companies, total nodes: {graph.get_stats()['total_nodes']}")

def main():
    """Main seeding function"""
    print("=" * 80)
    print("SEEDING KNOWLEDGE GRAPH WITH FUNDAMENTAL ANALYSIS FRAMEWORKS")
    print("=" * 80)

    # Initialize knowledge graph
    graph = KnowledgeGraph()

    # Seed each framework
    seed_buffett_framework(graph)
    seed_dalio_framework(graph)
    seed_financial_calculations(graph)
    seed_investment_examples(graph)

    # Display final stats
    stats = graph.get_stats()
    print("\n" + "=" * 80)
    print("KNOWLEDGE GRAPH SEEDED SUCCESSFULLY")
    print("=" * 80)
    print("\nFinal Statistics:")
    print(f"• Total Nodes: {stats['total_nodes']}")
    print(f"• Total Edges: {stats['total_edges']}")
    print(f"• Node Types: {stats['node_types']}")
    print(f"• Edge Types: {stats.get('edge_types', {})}")

    print("\n📚 Available Knowledge:")
    print("• Buffett Investment Framework")
    print("• Dalio Economic Machine")
    print("• Economic Moat Analysis")
    print("• Owner Earnings Calculations")
    print("• Debt Cycle Analysis")
    print("• All-Weather Portfolio")
    print("• Intrinsic Value Methods")
    print("• Quality-Value Matrix")

    print("\n🎯 Ready for fundamental analysis queries!")

    # Note: KnowledgeGraph doesn't have a save method, but we can persist the instance
    print("\n💾 Graph seeded and ready for use!")

if __name__ == "__main__":
    main()