#!/usr/bin/env python3
"""
Agent Capabilities Schema
Comprehensive capability metadata for all DawsOS agents
Defines explicit capabilities, requirements, and outputs for each agent
"""

from typing import Dict, List, Any

# Complete capability definitions for all 15 agents
AGENT_CAPABILITIES: Dict[str, Dict[str, Any]] = {

    # === CORE ORCHESTRATION AGENTS ===

    'claude': {
        'description': 'General-purpose conversational AI agent and primary orchestrator',
        'capabilities': [
            'can_orchestrate_requests',
            'can_natural_language_understanding',
            'can_generate_responses',
            'can_delegate_to_agents',
            'can_synthesize_information',
            'can_explain_reasoning'
        ],
        'requires': [
            'requires_llm_client',
            'requires_knowledge_graph'
        ],
        'provides': [
            'provides_conversational_interface',
            'provides_request_routing',
            'provides_response_formatting'
        ],
        'integrates_with': ['all_agents'],
        'stores_results': True,
        'priority': 'critical',
        'category': 'orchestration'
    },

    'graph_mind': {
        'description': 'Knowledge graph specialist managing graph operations and queries',
        'capabilities': [
            'can_manage_graph_structure',
            'can_query_relationships',
            'can_add_nodes',
            'can_connect_nodes',
            'can_traverse_graph',
            'can_analyze_graph_topology',
            'can_find_paths'
        ],
        'requires': [
            'requires_knowledge_graph'
        ],
        'provides': [
            'provides_graph_operations',
            'provides_relationship_data',
            'provides_graph_insights'
        ],
        'integrates_with': ['all_agents'],
        'stores_results': True,
        'priority': 'critical',
        'category': 'core'
    },

    # === DATA AGENTS ===

    'data_harvester': {
        'description': 'Fetches data from external sources (market, economic, news, options)',
        'capabilities': [
            'can_fetch_stock_quotes',
            'can_fetch_economic_data',
            'can_fetch_news',
            'can_fetch_fundamentals',
            'can_fetch_market_movers',
            'can_fetch_crypto_data',
            'can_calculate_correlations',
            'can_fetch_options_flow',
            'can_fetch_unusual_options'
        ],
        'requires': [
            'requires_market_capability',
            'requires_fred_capability',
            'requires_news_capability',
            'requires_fundamentals_capability',
            'requires_polygon_capability'
        ],
        'provides': [
            'provides_market_data',
            'provides_economic_indicators',
            'provides_news_data',
            'provides_financial_data'
        ],
        'integrates_with': [
            'data_digester',
            'financial_analyst',
            'pattern_spotter',
            'relationship_hunter'
        ],
        'stores_results': True,
        'priority': 'high',
        'category': 'data'
    },

    'data_digester': {
        'description': 'Processes and enriches raw data into knowledge',
        'capabilities': [
            'can_normalize_data',
            'can_enrich_data',
            'can_validate_data',
            'can_calculate_metrics',
            'can_aggregate_data',
            'can_transform_data'
        ],
        'requires': [
            'requires_knowledge_graph',
            'requires_raw_data'
        ],
        'provides': [
            'provides_enriched_data',
            'provides_validated_data',
            'provides_calculated_metrics'
        ],
        'integrates_with': [
            'data_harvester',
            'financial_analyst',
            'pattern_spotter'
        ],
        'stores_results': True,
        'priority': 'high',
        'category': 'data'
    },

    # === ANALYSIS AGENTS ===

    'relationship_hunter': {
        'description': 'Discovers and analyzes relationships between entities',
        'capabilities': [
            'can_find_correlations',
            'can_detect_causality',
            'can_analyze_connections',
            'can_identify_relationships',
            'can_calculate_correlation_coefficients',
            'can_map_dependencies'
        ],
        'requires': [
            'requires_knowledge_graph',
            'requires_market_capability',
            'requires_enriched_data'
        ],
        'provides': [
            'provides_correlation_data',
            'provides_relationship_insights',
            'provides_dependency_maps'
        ],
        'integrates_with': [
            'pattern_spotter',
            'data_harvester',
            'graph_mind'
        ],
        'stores_results': True,
        'priority': 'high',
        'category': 'analysis'
    },

    'pattern_spotter': {
        'description': 'Identifies patterns, trends, and anomalies in data',
        'capabilities': [
            'can_detect_patterns',
            'can_analyze_trends',
            'can_find_anomalies',
            'can_detect_sequences',
            'can_find_cycles',
            'can_identify_triggers',
            'can_analyze_macro_trends',
            'can_detect_market_regime'
        ],
        'requires': [
            'requires_knowledge_graph',
            'requires_historical_data'
        ],
        'provides': [
            'provides_pattern_insights',
            'provides_trend_analysis',
            'provides_anomaly_detection',
            'provides_regime_detection'
        ],
        'integrates_with': [
            'relationship_hunter',
            'forecast_dreamer',
            'data_harvester'
        ],
        'stores_results': True,
        'priority': 'high',
        'category': 'analysis'
    },

    'forecast_dreamer': {
        'description': 'Makes predictions and forecasts based on patterns',
        'capabilities': [
            'can_generate_forecasts',
            'can_project_trends',
            'can_estimate_probabilities',
            'can_predict_outcomes',
            'can_calculate_confidence',
            'can_model_scenarios'
        ],
        'requires': [
            'requires_knowledge_graph',
            'requires_pattern_data',
            'requires_historical_data'
        ],
        'provides': [
            'provides_forecasts',
            'provides_predictions',
            'provides_probability_estimates',
            'provides_scenario_analysis'
        ],
        'integrates_with': [
            'pattern_spotter',
            'financial_analyst',
            'relationship_hunter'
        ],
        'stores_results': True,
        'priority': 'medium',
        'category': 'analysis'
    },

    'financial_analyst': {
        'description': 'Specialized financial analysis, valuation, and options analysis agent',
        'capabilities': [
            'can_calculate_dcf',
            'can_calculate_roic',
            'can_calculate_fcf',
            'can_calculate_owner_earnings',
            'can_analyze_moat',
            'can_project_cash_flows',
            'can_calculate_wacc',
            'can_value_companies',
            'can_analyze_financials',
            'can_analyze_greeks',
            'can_analyze_options_flow',
            'can_detect_unusual_activity',
            'can_calculate_iv_rank'
        ],
        'requires': [
            'requires_knowledge_graph',
            'requires_market_capability',
            'requires_financial_data',
            'requires_polygon_capability'
        ],
        'provides': [
            'provides_dcf_valuations',
            'provides_financial_metrics',
            'provides_investment_analysis',
            'provides_moat_analysis'
        ],
        'integrates_with': [
            'data_harvester',
            'data_digester',
            'pattern_spotter'
        ],
        'stores_results': True,
        'priority': 'high',
        'category': 'financial'
    },

    # === CODE AGENTS ===

    'code_monkey': {
        'description': 'Writes and modifies code',
        'capabilities': [
            'can_write_functions',
            'can_fix_bugs',
            'can_simplify_code',
            'can_generate_code',
            'can_write_to_files',
            'can_read_files'
        ],
        'requires': [
            'requires_file_system_access',
            'requires_llm_client'
        ],
        'provides': [
            'provides_code_generation',
            'provides_bug_fixes',
            'provides_code_simplification'
        ],
        'integrates_with': [
            'structure_bot',
            'refactor_elf'
        ],
        'stores_results': False,
        'priority': 'medium',
        'category': 'development'
    },

    'structure_bot': {
        'description': 'Analyzes and improves code structure',
        'capabilities': [
            'can_analyze_structure',
            'can_suggest_improvements',
            'can_organize_code',
            'can_design_architecture',
            'can_create_modules',
            'can_refactor_structure'
        ],
        'requires': [
            'requires_file_system_access',
            'requires_code_analysis'
        ],
        'provides': [
            'provides_structure_analysis',
            'provides_architecture_recommendations',
            'provides_organization_improvements'
        ],
        'integrates_with': [
            'code_monkey',
            'refactor_elf'
        ],
        'stores_results': False,
        'priority': 'medium',
        'category': 'development'
    },

    'refactor_elf': {
        'description': 'Refactors and optimizes existing code',
        'capabilities': [
            'can_refactor_code',
            'can_optimize_performance',
            'can_improve_readability',
            'can_extract_patterns',
            'can_eliminate_duplication',
            'can_modernize_code'
        ],
        'requires': [
            'requires_file_system_access',
            'requires_code_analysis'
        ],
        'provides': [
            'provides_refactored_code',
            'provides_performance_improvements',
            'provides_code_quality_enhancements'
        ],
        'integrates_with': [
            'code_monkey',
            'structure_bot'
        ],
        'stores_results': False,
        'priority': 'medium',
        'category': 'development'
    },

    # === WORKFLOW AGENTS ===

    'workflow_recorder': {
        'description': 'Records successful interaction patterns for reuse',
        'capabilities': [
            'can_record_workflows',
            'can_identify_patterns',
            'can_extract_templates',
            'can_save_patterns',
            'can_find_similar_workflows',
            'can_judge_success'
        ],
        'requires': [
            'requires_knowledge_graph',
            'requires_interaction_history'
        ],
        'provides': [
            'provides_workflow_templates',
            'provides_pattern_library',
            'provides_reusable_workflows'
        ],
        'integrates_with': [
            'workflow_player',
            'pattern_spotter'
        ],
        'stores_results': True,
        'priority': 'medium',
        'category': 'workflow'
    },

    'workflow_player': {
        'description': 'Executes recorded workflows and patterns',
        'capabilities': [
            'can_execute_workflows',
            'can_replay_patterns',
            'can_adapt_workflows',
            'can_parameterize_execution',
            'can_chain_workflows',
            'can_handle_errors'
        ],
        'requires': [
            'requires_workflow_templates',
            'requires_agent_runtime'
        ],
        'provides': [
            'provides_workflow_execution',
            'provides_pattern_replay',
            'provides_automated_processes'
        ],
        'integrates_with': [
            'workflow_recorder',
            'all_agents'
        ],
        'stores_results': True,
        'priority': 'medium',
        'category': 'workflow'
    },

    # === UI AND PRESENTATION AGENTS ===

    'ui_generator': {
        'description': 'Generates UI components and visualizations',
        'capabilities': [
            'can_generate_ui_components',
            'can_create_visualizations',
            'can_generate_charts',
            'can_create_dashboards',
            'can_generate_html',
            'can_style_components',
            'can_create_confidence_meters',
            'can_create_alert_feeds',
            'can_create_risk_radars'
        ],
        'requires': [
            'requires_streamlit',
            'requires_plotly',
            'requires_data_to_visualize'
        ],
        'provides': [
            'provides_ui_components',
            'provides_visualizations',
            'provides_interactive_dashboards'
        ],
        'integrates_with': [
            'pattern_spotter',
            'financial_analyst',
            'data_harvester'
        ],
        'stores_results': False,
        'priority': 'medium',
        'category': 'presentation'
    },

    # === GOVERNANCE AGENTS ===

    'governance_agent': {
        'description': 'Manages data quality, compliance, and system governance',
        'capabilities': [
            'can_check_data_quality',
            'can_audit_compliance',
            'can_trace_lineage',
            'can_assess_security',
            'can_optimize_costs',
            'can_tune_performance',
            'can_validate_agent_compliance',
            'can_suggest_improvements',
            'can_enforce_policies',
            'can_auto_remediate'
        ],
        'requires': [
            'requires_knowledge_graph',
            'requires_graph_governance',
            'requires_agent_runtime'
        ],
        'provides': [
            'provides_governance_reports',
            'provides_compliance_audits',
            'provides_quality_scores',
            'provides_policy_enforcement',
            'provides_improvement_suggestions'
        ],
        'integrates_with': [
            'all_agents',
            'graph_mind',
            'pattern_spotter'
        ],
        'stores_results': True,
        'priority': 'high',
        'category': 'governance'
    }
}


# Capability categories for organization
CAPABILITY_CATEGORIES = {
    'orchestration': ['claude'],
    'core': ['graph_mind'],
    'data': ['data_harvester', 'data_digester'],
    'analysis': ['relationship_hunter', 'pattern_spotter', 'forecast_dreamer'],
    'financial': ['financial_analyst'],
    'development': ['code_monkey', 'structure_bot', 'refactor_elf'],
    'workflow': ['workflow_recorder', 'workflow_player'],
    'presentation': ['ui_generator'],
    'governance': ['governance_agent']
}


# Capability dependencies - which capabilities are required by which
CAPABILITY_DEPENDENCIES = {
    'market_data': ['data_harvester', 'financial_analyst', 'relationship_hunter'],
    'economic_data': ['data_harvester', 'pattern_spotter'],
    'knowledge_graph': [
        'claude', 'graph_mind', 'data_digester', 'relationship_hunter',
        'pattern_spotter', 'forecast_dreamer', 'financial_analyst',
        'workflow_recorder', 'workflow_player', 'governance_agent'
    ],
    'llm_client': ['claude', 'code_monkey'],
    'pattern_engine': ['workflow_player', 'governance_agent']
}


# Integration matrix - which agents commonly work together
AGENT_INTEGRATION_MATRIX = {
    'data_harvester': ['data_digester', 'financial_analyst', 'pattern_spotter'],
    'data_digester': ['data_harvester', 'financial_analyst', 'pattern_spotter'],
    'relationship_hunter': ['pattern_spotter', 'data_harvester', 'graph_mind'],
    'pattern_spotter': ['relationship_hunter', 'forecast_dreamer', 'data_harvester'],
    'forecast_dreamer': ['pattern_spotter', 'financial_analyst', 'relationship_hunter'],
    'financial_analyst': ['data_harvester', 'data_digester', 'pattern_spotter'],
    'workflow_recorder': ['workflow_player', 'pattern_spotter'],
    'workflow_player': ['workflow_recorder', 'all_agents'],
    'governance_agent': ['all_agents', 'graph_mind', 'pattern_spotter']
}


def get_agent_capabilities(agent_name: str) -> Dict[str, Any]:
    """Get capabilities for a specific agent"""
    return AGENT_CAPABILITIES.get(agent_name, {})


def get_agents_by_capability(capability: str) -> List[str]:
    """Get all agents that have a specific capability"""
    agents = []
    for agent_name, config in AGENT_CAPABILITIES.items():
        if capability in config.get('capabilities', []):
            agents.append(agent_name)
    return agents


def get_agents_by_category(category: str) -> List[str]:
    """Get all agents in a specific category"""
    return CAPABILITY_CATEGORIES.get(category, [])


def validate_agent_requirements(agent_name: str, available_capabilities: List[str]) -> Dict[str, Any]:
    """Check if agent requirements are met"""
    config = AGENT_CAPABILITIES.get(agent_name, {})
    requirements = config.get('requires', [])

    missing = []
    for req in requirements:
        # Strip 'requires_' prefix for matching
        req_name = req.replace('requires_', '')
        if req_name not in available_capabilities:
            missing.append(req)

    return {
        'agent': agent_name,
        'satisfied': len(missing) == 0,
        'missing': missing,
        'requirements': requirements
    }


def get_capability_summary() -> Dict[str, Any]:
    """Get summary of all agent capabilities"""
    return {
        'total_agents': len(AGENT_CAPABILITIES),
        'categories': list(CAPABILITY_CATEGORIES.keys()),
        'agents_by_category': {
            category: len(agents)
            for category, agents in CAPABILITY_CATEGORIES.items()
        },
        'total_capabilities': sum(
            len(config.get('capabilities', []))
            for config in AGENT_CAPABILITIES.values()
        )
    }


if __name__ == '__main__':
    # Print capability summary
    summary = get_capability_summary()
    print("\n=== DawsOS Agent Capability Summary ===\n")
    print(f"Total Agents: {summary['total_agents']}")
    print(f"Total Capabilities: {summary['total_capabilities']}")
    print("\nAgents by Category:")
    for category, count in summary['agents_by_category'].items():
        print(f"  {category}: {count} agents")

    print("\n=== Agent Details ===\n")
    for agent_name, config in AGENT_CAPABILITIES.items():
        print(f"{agent_name}:")
        print(f"  Description: {config['description']}")
        print(f"  Capabilities: {len(config['capabilities'])}")
        print(f"  Category: {config['category']}")
        print(f"  Stores Results: {config['stores_results']}")
        print()
