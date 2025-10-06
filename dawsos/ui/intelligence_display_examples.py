#!/usr/bin/env python3
"""
Intelligence Display Integration Examples

This file demonstrates how to integrate the intelligence_display.py component
into various parts of the DawsOS Trinity architecture.

Phase 3.1: Comprehensive type hints added
"""

import streamlit as st
from typing import Any
from ui.intelligence_display import IntelligenceDisplay, create_intelligence_display
from ui.intelligence_display import quick_confidence_display, quick_thinking_trace


# ============================================================================
# EXAMPLE 1: Integration with Pattern Execution
# ============================================================================

def example_pattern_execution_with_intelligence() -> None:
    """Show how to display intelligence after a pattern execution."""
    st.markdown("## Example 1: Pattern Execution Intelligence")

    # Assuming you have these from your Trinity setup
    # graph = runtime.graph
    # registry = runtime.agent_registry
    # pattern_engine = runtime.pattern_engine

    # Create intelligence display
    # display = create_intelligence_display(graph, registry, runtime)

    # Execute a pattern
    user_input = st.text_input("Enter query:", "Analyze Apple stock")

    if st.button("Execute Pattern"):
        with st.spinner("Executing pattern..."):
            # This would be your actual pattern execution
            # result = pattern_engine.execute_pattern_by_trigger(user_input)

            # For demonstration, use sample result
            result = {
                'confidence': 87,
                'execution_history': [
                    {
                        'agent': 'PatternEngine',
                        'action': 'match_pattern',
                        'duration_ms': 120,
                        'result': {'pattern_matched': 'analyze_stock'}
                    }
                ],
                'agents_used': ['PatternEngine', 'DataHarvester', 'PatternDetector'],
                'reasoning': ['Matched stock analysis pattern', 'Retrieved market data'],
                'node_id': 'result_123'
            }

            # Display intelligence
            # display.render_intelligence_summary(result, show_all_sections=False)

            st.success("Pattern executed! Intelligence displayed below.")


# ============================================================================
# EXAMPLE 2: Standalone Confidence Display
# ============================================================================

def example_standalone_confidence() -> None:
    """Show confidence for a prediction or analysis."""
    st.markdown("## Example 2: Standalone Confidence Display")

    # Quick confidence display without full setup
    st.markdown("### Quick Confidence Gauge")
    quick_confidence_display(85.5, "Prediction Confidence")

    # Multiple confidence scores
    st.markdown("### Multiple Confidence Scores")
    display = IntelligenceDisplay()
    display.render_multi_confidence({
        'Data Quality': 92,
        'Model Accuracy': 88,
        'Historical Success': 76,
        'Overall': 85
    })


# ============================================================================
# EXAMPLE 3: Integration with Agent Results
# ============================================================================

def example_agent_result_intelligence(runtime: Any) -> None:
    """Display intelligence for any agent execution result.

    Args:
        runtime: AgentRuntime instance
    """
    st.markdown("## Example 3: Agent Result Intelligence")

    # Create display with Trinity components
    display = create_intelligence_display(
        graph=runtime.graph,
        registry=runtime.agent_registry,
        runtime=runtime
    )

    # After executing an agent
    agent_name = st.selectbox("Select Agent", ["DataHarvester", "PatternDetector", "GraphMind"])

    if st.button("Execute Agent"):
        # Execute agent through registry
        context = {'user_input': 'Test query'}
        result = runtime.agent_registry.execute_with_tracking(agent_name, context)

        # Show result with intelligence
        st.markdown("### Agent Result")
        st.json(result)

        st.markdown("### Intelligence Analysis")
        display.render_intelligence_summary(result)


# ============================================================================
# EXAMPLE 4: System Health Dashboard Integration
# ============================================================================

def example_system_health_tab(runtime: Any) -> None:
    """Integration example for a system health dashboard tab.

    Args:
        runtime: AgentRuntime instance
    """
    st.markdown("## System Intelligence Health")

    display = create_intelligence_display(
        graph=runtime.graph,
        registry=runtime.agent_registry,
        runtime=runtime
    )

    # Show system-wide intelligence metrics
    display.render_system_intelligence()

    # Show Trinity architecture
    st.markdown("---")
    display.render_trinity_architecture_flow()


# ============================================================================
# EXAMPLE 5: Decision Provenance Deep Dive
# ============================================================================

def example_decision_provenance(graph: Any) -> None:
    """Deep dive into a specific decision's provenance.

    Args:
        graph: KnowledgeGraph instance
    """
    st.markdown("## Example 5: Decision Provenance")

    display = create_intelligence_display(graph=graph)

    # Get a decision node from the graph
    # In practice, you'd query the graph for decision nodes
    decision_node = {
        'type': 'analysis_result',
        'timestamp': '2025-10-03T10:30:00',
        'agent': 'PatternDetector',
        'reasoning': [
            'Analyzed 100 data points for AAPL',
            'Identified strong uptrend pattern',
            'Pattern confidence: 85%',
            'Historical success rate: 78%'
        ],
        'factors': {
            'trend_strength': 0.85,
            'volume_confirmation': 0.78,
            'momentum': 0.82,
            'volatility': 0.65
        },
        'sources': [
            {'type': 'market_data', 'id': 'AAPL_2025-10-03'},
            {'type': 'historical_pattern', 'id': 'uptrend_pattern_v2'}
        ],
        'node_id': 'decision_abc123'
    }

    display.render_decision_provenance(decision_node, show_data_sources=True)


# ============================================================================
# EXAMPLE 6: Execution Trace for Debugging
# ============================================================================

def example_execution_trace_debug() -> None:
    """Use thinking trace for debugging agent execution."""
    st.markdown("## Example 6: Execution Trace Debugging")

    # Sample execution history with an error
    execution_history = [
        {
            'agent': 'UniversalExecutor',
            'action': 'route_request',
            'duration_ms': 45,
            'timestamp': '2025-10-03T10:30:00.000',
            'result': {'status': 'routed', 'pattern': 'analyze_stock'}
        },
        {
            'agent': 'PatternEngine',
            'action': 'match_pattern',
            'duration_ms': 120,
            'timestamp': '2025-10-03T10:30:00.045',
            'result': {'pattern_id': 'analyze_stock', 'confidence': 0.95}
        },
        {
            'agent': 'DataHarvester',
            'action': 'fetch_data',
            'duration_ms': 350,
            'timestamp': '2025-10-03T10:30:00.165',
            'result': {'error': 'API rate limit exceeded'}
        },
        {
            'agent': 'PatternEngine',
            'action': 'retry_with_cache',
            'duration_ms': 80,
            'timestamp': '2025-10-03T10:30:00.515',
            'result': {'cache_hit': True, 'data_points': 95}
        }
    ]

    quick_thinking_trace(execution_history)

    st.info("Notice the error in step 3 and the automatic retry in step 4")


# ============================================================================
# EXAMPLE 7: Agent Flow Visualization
# ============================================================================

def example_agent_flow_visualization():
    """
    Visualize complex agent execution flows
    """
    st.markdown("## Example 7: Agent Flow Visualization")

    display = IntelligenceDisplay()

    # Example 1: Simple sequential flow
    st.markdown("### Sequential Flow")
    agents_used = ['UniversalExecutor', 'PatternEngine', 'DataHarvester', 'PatternDetector']
    display.render_agent_flow_diagram(agents_used)

    # Example 2: Complex flow with explicit paths
    st.markdown("### Complex Flow with Branching")
    execution_path = [
        ("User Input", "UniversalExecutor"),
        ("UniversalExecutor", "PatternEngine"),
        ("PatternEngine", "AgentRegistry"),
        ("AgentRegistry", "DataHarvester"),
        ("AgentRegistry", "PatternDetector"),
        ("AgentRegistry", "GraphMind"),
        ("DataHarvester", "KnowledgeGraph"),
        ("PatternDetector", "KnowledgeGraph"),
        ("GraphMind", "KnowledgeGraph"),
        ("KnowledgeGraph", "Response")
    ]
    display.render_agent_flow_diagram([], execution_path)


# ============================================================================
# EXAMPLE 8: Confidence with Historical Trend
# ============================================================================

def example_confidence_with_history(runtime):
    """
    Show confidence gauge with historical trend

    Args:
        runtime: AgentRuntime with execution_history
    """
    st.markdown("## Example 8: Confidence with Historical Trend")

    display = create_intelligence_display(runtime=runtime)

    # Current confidence
    current_confidence = 85.5

    # Render with history
    display.render_confidence_gauge(
        confidence=current_confidence,
        label="Current Prediction Confidence",
        show_history=True
    )


# ============================================================================
# EXAMPLE 9: Embedding in Pattern Browser
# ============================================================================

def example_pattern_browser_integration(pattern_engine, runtime):
    """
    Show how to embed intelligence display in pattern browser

    Args:
        pattern_engine: PatternEngine instance
        runtime: AgentRuntime instance
    """
    st.markdown("## Example 9: Pattern Browser with Intelligence")

    # Pattern selection
    pattern_ids = list(pattern_engine.patterns.keys())
    selected_pattern = st.selectbox("Select Pattern", pattern_ids)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Pattern Details")
        if selected_pattern:
            pattern = pattern_engine.get_pattern(selected_pattern)
            st.json(pattern)

    with col2:
        st.markdown("### Execute with Intelligence")
        if st.button("Execute and Analyze"):
            with st.spinner("Executing..."):
                # Execute pattern
                result = pattern_engine.execute_pattern(
                    pattern,
                    {'user_input': 'Test execution'}
                )

                # Show intelligence
                display = create_intelligence_display(
                    graph=runtime.graph,
                    registry=runtime.agent_registry,
                    runtime=runtime
                )

                display.render_intelligence_summary(result, show_all_sections=True)


# ============================================================================
# EXAMPLE 10: Custom Intelligence Tab
# ============================================================================

def create_intelligence_tab(runtime):
    """
    Create a dedicated intelligence tab for the dashboard

    Args:
        runtime: AgentRuntime instance
    """
    st.title("🧠 Intelligence Center")

    display = create_intelligence_display(
        graph=runtime.graph,
        registry=runtime.agent_registry,
        runtime=runtime
    )

    # Tab layout
    tab1, tab2, tab3, tab4 = st.tabs([
        "System Health",
        "Recent Executions",
        "Decision History",
        "Architecture"
    ])

    with tab1:
        display.render_system_intelligence()

    with tab2:
        if hasattr(runtime, 'execution_history'):
            st.markdown("### Recent Executions")
            for idx, execution in enumerate(runtime.execution_history[-5:]):
                with st.expander(f"Execution {idx + 1}"):
                    display.render_intelligence_summary(execution, show_all_sections=False)

    with tab3:
        st.markdown("### Decision History")
        # Query graph for decision nodes
        if runtime.graph:
            decision_nodes = runtime.graph.get_nodes_by_type('decision')
            for node_id, node_data in list(decision_nodes.items())[:5]:
                with st.expander(f"Decision: {node_id}"):
                    display.render_decision_provenance(node_data)

    with tab4:
        display.render_trinity_architecture_flow()


# ============================================================================
# MAIN DEMO
# ============================================================================

def main():
    """
    Main demo showing all examples
    """
    st.set_page_config(
        page_title="Intelligence Display Examples",
        page_icon="🧠",
        layout="wide"
    )

    st.title("🧠 Intelligence Display Component Examples")

    st.markdown("""
    This demo shows various ways to integrate the `intelligence_display.py` component
    into your DawsOS Trinity architecture.

    **Key Features:**
    - 📊 Confidence scores with visual gauges
    - 🧠 Thinking traces showing step-by-step execution
    - 🔄 Agent flow diagrams
    - 🔍 Decision provenance
    - 🏥 System health intelligence
    """)

    # Select example
    example = st.sidebar.selectbox(
        "Choose Example",
        [
            "1. Pattern Execution",
            "2. Standalone Confidence",
            "3. Agent Result",
            "4. System Health",
            "5. Decision Provenance",
            "6. Execution Trace",
            "7. Agent Flow",
            "8. Confidence History",
            "9. Pattern Browser",
            "10. Intelligence Tab"
        ]
    )

    st.markdown("---")

    # Run selected example
    if example.startswith("1"):
        example_pattern_execution_with_intelligence()
    elif example.startswith("2"):
        example_standalone_confidence()
    elif example.startswith("6"):
        example_execution_trace_debug()
    elif example.startswith("7"):
        example_agent_flow_visualization()
    else:
        st.info(f"Example {example} requires runtime setup. See source code for integration.")


if __name__ == "__main__":
    main()
