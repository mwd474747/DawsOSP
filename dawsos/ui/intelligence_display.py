#!/usr/bin/env python3
"""
Intelligence Display Component for DawsOS Trinity Architecture

This module visualizes agent intelligence, decision-making, and execution flows:
- Confidence scores with visual gauges
- Thinking traces showing step-by-step agent execution
- Agent flow diagrams illustrating the execution path
- Decision provenance explaining reasoning and data sources

All components integrate with the Trinity architecture (UniversalExecutor -> PatternEngine -> AgentRegistry -> Agents -> KnowledgeGraph)

Phase 3.1: Comprehensive type hints added
"""

import streamlit as st
from typing import Dict, List, Optional, Tuple, Any
from core.typing_compat import TypeAlias
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# Type aliases for clarity
ResultDict: TypeAlias = Dict[str, Any]
ExecutionHistory: TypeAlias = List[Dict[str, Any]]
NodeDict: TypeAlias = Dict[str, Any]


class IntelligenceDisplay:
    """Visualize agent intelligence and decision-making processes"""

    def __init__(self, graph: Optional[Any] = None, registry: Optional[Any] = None, runtime: Optional[Any] = None) -> None:
        """Initialize intelligence display with Trinity components.

        Args:
            graph: KnowledgeGraph instance for decision nodes
            registry: AgentRegistry for agent tracking
            runtime: AgentRuntime for execution metrics
        """
        self.graph: Optional[Any] = graph
        self.registry: Optional[Any] = registry
        self.runtime: Optional[Any] = runtime

    # ========================================================================
    # A. CONFIDENCE SCORE DISPLAY
    # ========================================================================

    def render_confidence_gauge(self, confidence: float, label: str = "Confidence",
                                show_history: bool = False) -> None:
        """
        Render visual confidence indicator with color coding

        Args:
            confidence: Confidence score (0-100)
            label: Label for the gauge
            show_history: Whether to show historical trend
        """
        # Determine color based on confidence level
        if confidence >= 80:
            color = "#00C851"  # Green
            status = "High"
        elif confidence >= 50:
            color = "#FFB300"  # Yellow
            status = "Medium"
        else:
            color = "#FF4444"  # Red
            status = "Low"

        # Create gauge chart using Plotly
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=confidence,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"{label}<br><span style='font-size:0.8em;color:gray'>{status} Confidence</span>"},
            delta={'reference': 70, 'increasing': {'color': "green"}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkgray"},
                'bar': {'color': color},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': '#FFE6E6'},
                    {'range': [50, 80], 'color': '#FFF9E6'},
                    {'range': [80, 100], 'color': '#E6F7E6'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))

        fig.update_layout(
            height=250,
            margin=dict(l=20, r=20, t=60, b=20),
            font={'size': 14}
        )

        st.plotly_chart(fig, width="stretch")

        # Show historical trend if requested
        if show_history and self.runtime:
            self._render_confidence_history()

    def _render_confidence_history(self) -> None:
        """Render historical confidence trend chart"""
        # Extract confidence from execution history
        if not hasattr(self.runtime, 'execution_history'):
            return

        history = []
        for idx, execution in enumerate(self.runtime.execution_history[-20:]):  # Last 20 executions
            result = execution.get('result', {})
            confidence = result.get('confidence', 0.75)  # Default to 75%
            timestamp = execution.get('timestamp', '')

            history.append({
                'execution': idx + 1,
                'confidence': confidence * 100 if confidence <= 1 else confidence,
                'timestamp': timestamp
            })

        if history:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[h['execution'] for h in history],
                y=[h['confidence'] for h in history],
                mode='lines+markers',
                name='Confidence',
                line=dict(color='#4285F4', width=2),
                marker=dict(size=8)
            ))

            fig.update_layout(
                title="Confidence Trend (Last 20 Executions)",
                xaxis_title="Execution #",
                yaxis_title="Confidence %",
                height=200,
                margin=dict(l=40, r=20, t=40, b=40),
                showlegend=False
            )

            st.plotly_chart(fig, width="stretch")

    def render_multi_confidence(self, scores: Dict[str, float]) -> None:
        """
        Render multiple confidence scores side-by-side

        Args:
            scores: Dictionary of {label: confidence_score}
        """
        cols = st.columns(len(scores))

        for idx, (label, confidence) in enumerate(scores.items()):
            with cols[idx]:
                self._render_mini_gauge(confidence, label)

    def _render_mini_gauge(self, confidence: float, label: str) -> None:
        """Render a compact confidence gauge"""
        # Determine color
        if confidence >= 80:
            color = "#00C851"
        elif confidence >= 50:
            color = "#FFB300"
        else:
            color = "#FF4444"

        # Use st.metric for compact display
        st.metric(
            label=label,
            value=f"{confidence:.1f}%",
            delta=f"{confidence - 70:.1f}%" if confidence != 70 else None,
            delta_color="normal"
        )

        # Add a simple progress bar
        st.progress(min(confidence / 100, 1.0))

    # ========================================================================
    # B. THINKING TRACE VISUALIZER
    # ========================================================================

    def render_thinking_trace(self, execution_history: List[Dict],
                             expand_by_default: bool = False) -> None:
        """
        Show step-by-step agent execution as a timeline

        Args:
            execution_history: List of execution steps
            expand_by_default: Whether to expand all steps by default
        """
        st.markdown("### 🧠 Thinking Trace")
        st.caption("Step-by-step agent execution flow")

        if not execution_history:
            st.info("No execution history available")
            return

        # Calculate total execution time
        total_time = 0
        for step in execution_history:
            total_time += step.get('duration_ms', 0)

        st.markdown(f"**Total Execution Time:** {total_time:.0f}ms | **Steps:** {len(execution_history)}")

        # Render each step
        for idx, step in enumerate(execution_history):
            self._render_execution_step(idx, step, expand_by_default)

    def _render_execution_step(self, idx: int, step: Dict, expand: bool) -> None:
        """Render a single execution step"""
        agent_name = step.get('agent', 'Unknown')
        action = step.get('action', step.get('method_used', 'execute'))
        result = step.get('result', {})
        duration = step.get('duration_ms', 0)
        timestamp = step.get('timestamp', '')

        # Determine success/failure
        success = 'error' not in result
        status_icon = "✅" if success else "❌"
        status_color = "green" if success else "red"

        # Create expandable section
        with st.expander(
            f"{status_icon} **Step {idx + 1}:** {agent_name} → {action} ({duration:.0f}ms)",
            expanded=expand
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Agent:** {agent_name}")
                st.markdown(f"**Action:** {action}")
                st.markdown(f"**Status:** :{status_color}[{'Success' if success else 'Failed'}]")

                # Show result summary
                if isinstance(result, dict):
                    if 'response' in result:
                        st.markdown(f"**Response:** {result['response'][:200]}...")
                    elif 'error' in result:
                        st.error(f"**Error:** {result['error']}")
                    else:
                        st.markdown(f"**Result Keys:** {', '.join(result.keys())}")

            with col2:
                st.metric("Duration", f"{duration:.0f}ms")
                if timestamp:
                    st.caption(f"Time: {timestamp}")

            # Show full result in JSON
            with st.expander("📄 Full Result"):
                st.json(result)

    def render_execution_timeline(self, execution_history: List[Dict]) -> None:
        """
        Render execution as a visual timeline using Plotly

        Args:
            execution_history: List of execution steps
        """
        if not execution_history:
            return

        # Prepare data for Gantt chart
        timeline_data = []
        start_time = 0

        for idx, step in enumerate(execution_history):
            agent_name = step.get('agent', 'Unknown')
            action = step.get('action', step.get('method_used', 'execute'))
            duration = step.get('duration_ms', 100)
            success = 'error' not in step.get('result', {})

            timeline_data.append({
                'Task': f"{agent_name}",
                'Start': start_time,
                'Finish': start_time + duration,
                'Resource': action,
                'Status': 'Success' if success else 'Failed'
            })

            start_time += duration

        # Create Gantt chart
        fig = px.timeline(
            timeline_data,
            x_start='Start',
            x_end='Finish',
            y='Task',
            color='Status',
            hover_data=['Resource'],
            color_discrete_map={'Success': '#00C851', 'Failed': '#FF4444'}
        )

        fig.update_layout(
            title="Execution Timeline",
            xaxis_title="Time (ms)",
            yaxis_title="Agent",
            height=max(200, len(timeline_data) * 40),
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, width="stretch")

    # ========================================================================
    # C. AGENT FLOW DIAGRAM
    # ========================================================================

    def render_agent_flow_diagram(self, agents_used: List[str],
                                  execution_path: Optional[List[Tuple[str, str]]] = None) -> None:
        """
        Visual flowchart of agent execution through Trinity architecture

        Args:
            agents_used: List of agent names involved
            execution_path: Optional list of (from_agent, to_agent) tuples
        """
        st.markdown("### 🔄 Agent Execution Flow")

        # If no execution path provided, infer sequential flow
        if not execution_path and agents_used:
            execution_path = []
            # Always start with UniversalExecutor
            execution_path.append(("User Input", "UniversalExecutor"))
            execution_path.append(("UniversalExecutor", "PatternEngine"))

            # Add agent registry routing
            if agents_used:
                execution_path.append(("PatternEngine", "AgentRegistry"))

                # Add agent executions
                for agent in agents_used:
                    execution_path.append(("AgentRegistry", agent))
                    execution_path.append((agent, "KnowledgeGraph"))

        # Render using Mermaid diagram
        self._render_mermaid_flow(execution_path)

        # Show agent details
        if agents_used:
            st.markdown("#### Agents Involved")
            cols = st.columns(min(len(agents_used), 4))

            for idx, agent_name in enumerate(agents_used):
                with cols[idx % 4]:
                    self._render_agent_card(agent_name)

    def _render_mermaid_flow(self, execution_path: List[Tuple[str, str]]) -> None:
        """Render execution flow using Mermaid diagram"""
        if not execution_path:
            return

        # Build Mermaid diagram
        mermaid_code = "graph TD\n"

        # Create unique node IDs
        node_ids = {}
        counter = 0

        for from_node, to_node in execution_path:
            if from_node not in node_ids:
                node_ids[from_node] = f"N{counter}"
                counter += 1
            if to_node not in node_ids:
                node_ids[to_node] = f"N{counter}"
                counter += 1

        # Add node definitions with styling
        for node_name, node_id in node_ids.items():
            # Style based on node type
            if node_name == "User Input":
                mermaid_code += f"    {node_id}[{node_name}]:::input\n"
            elif node_name in ["UniversalExecutor", "PatternEngine", "AgentRegistry"]:
                mermaid_code += f"    {node_id}[{node_name}]:::core\n"
            elif node_name == "KnowledgeGraph":
                mermaid_code += f"    {node_id}[({node_name})]:::graph\n"
            else:
                mermaid_code += f"    {node_id}[{node_name}]:::agent\n"

        # Add edges
        for from_node, to_node in execution_path:
            mermaid_code += f"    {node_ids[from_node]} --> {node_ids[to_node]}\n"

        # Add styles
        mermaid_code += """
    classDef input fill:#4285F4,stroke:#1967D2,stroke-width:2px,color:#fff
    classDef core fill:#0F9D58,stroke:#0B8043,stroke-width:2px,color:#fff
    classDef agent fill:#F4B400,stroke:#F29900,stroke-width:2px,color:#000
    classDef graph fill:#DB4437,stroke:#C5221F,stroke-width:2px,color:#fff
"""

        # Render using Mermaid component
        st.markdown(f"""
```mermaid
{mermaid_code}
```
        """)

    def _render_agent_card(self, agent_name: str) -> None:
        """Render a compact agent information card"""
        # Get agent capabilities if available
        capabilities = []
        if self.registry:
            agent = self.registry.get_agent(agent_name)
            if agent:
                caps = agent.get_capabilities()
                capabilities = caps.get('methods', [])

        st.markdown(f"""
**{agent_name}**
- Methods: {', '.join(capabilities[:3]) if capabilities else 'N/A'}
        """)

    def render_trinity_architecture_flow(self) -> None:
        """Render the complete Trinity architecture flow"""
        st.markdown("### 🏛️ Trinity Architecture")

        st.markdown("""
```mermaid
graph TD
    A[User Request] --> B[UniversalExecutor]
    B --> C[PatternEngine]
    C --> D[Pattern Matching]
    D --> E[AgentRegistry]
    E --> F1[Agent 1]
    E --> F2[Agent 2]
    E --> F3[Agent N]
    F1 --> G[KnowledgeGraph]
    F2 --> G
    F3 --> G
    G --> H[Results]
    H --> I[UI Display]

    classDef input fill:#4285F4,stroke:#1967D2,stroke-width:2px,color:#fff
    classDef core fill:#0F9D58,stroke:#0B8043,stroke-width:2px,color:#fff
    classDef agent fill:#F4B400,stroke:#F29900,stroke-width:2px,color:#000
    classDef graph fill:#DB4437,stroke:#C5221F,stroke-width:2px,color:#fff

    class A,I input
    class B,C,D,E core
    class F1,F2,F3 agent
    class G graph
```
        """)

    # ========================================================================
    # D. DECISION PROVENANCE
    # ========================================================================

    def render_decision_provenance(self, decision_node: Dict,
                                   show_data_sources: bool = True) -> None:
        """
        Show reasoning behind a decision with contributing factors

        Args:
            decision_node: Decision node from knowledge graph or execution result
            show_data_sources: Whether to show data sources
        """
        st.markdown("### 🔍 Decision Provenance")
        st.caption("Understanding the reasoning behind this result")

        # Extract decision information
        decision_type = decision_node.get('type', 'decision')
        timestamp = decision_node.get('timestamp', datetime.now().isoformat())
        agent = decision_node.get('agent', 'Unknown')

        # Display decision header
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Decision Type", decision_type)
        with col2:
            st.metric("Agent", agent)
        with col3:
            st.metric("Timestamp", timestamp[:19])

        # Show reasoning steps
        reasoning = decision_node.get('reasoning', [])
        if reasoning and isinstance(reasoning, list):
            st.markdown("#### 🤔 Reasoning Steps")
            for idx, step in enumerate(reasoning):
                st.markdown(f"{idx + 1}. {step}")

        # Show contributing factors
        factors = decision_node.get('factors', decision_node.get('data', {}))
        if factors:
            st.markdown("#### 📊 Contributing Factors")

            # If factors is a dict, display as metrics
            if isinstance(factors, dict):
                factor_cols = st.columns(min(len(factors), 3))
                for idx, (key, value) in enumerate(factors.items()):
                    with factor_cols[idx % 3]:
                        st.metric(key.replace('_', ' ').title(), str(value))
            else:
                st.json(factors)

        # Show data sources
        if show_data_sources:
            self._render_data_sources(decision_node)

        # Show knowledge graph connections
        if self.graph and 'node_id' in decision_node:
            self._render_graph_connections(decision_node['node_id'])

    def _render_data_sources(self, decision_node: Dict) -> None:
        """Render data sources used in the decision"""
        sources = decision_node.get('sources', [])

        if not sources and self.graph and 'node_id' in decision_node:
            # Try to get sources from graph connections
            node_id = decision_node['node_id']
            connected_nodes = self.graph.get_connected_nodes(node_id, direction='in')

            sources = []
            for node_id in connected_nodes[:5]:  # Limit to 5 sources
                node = self.graph.get_node(node_id)
                if node:
                    sources.append({
                        'type': node.get('type', 'unknown'),
                        'id': node_id,
                        'timestamp': node.get('created', '')
                    })

        if sources:
            st.markdown("#### 📚 Data Sources")
            for source in sources:
                if isinstance(source, dict):
                    source_type = source.get('type', 'Unknown')
                    source_id = source.get('id', 'N/A')
                    st.markdown(f"- **{source_type}**: `{source_id}`")
                else:
                    st.markdown(f"- {source}")

    def _render_graph_connections(self, node_id: str) -> None:
        """Render knowledge graph connections for a node"""
        if not self.graph:
            return

        with st.expander("🕸️ Knowledge Graph Connections"):
            # Get incoming and outgoing connections
            incoming = self.graph.get_connected_nodes(node_id, direction='in')
            outgoing = self.graph.get_connected_nodes(node_id, direction='out')

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Incoming:** {len(incoming)}")
                for conn_id in incoming[:5]:
                    node = self.graph.get_node(conn_id)
                    if node:
                        st.caption(f"← {node.get('type', 'unknown')}")

            with col2:
                st.markdown(f"**Outgoing:** {len(outgoing)}")
                for conn_id in outgoing[:5]:
                    node = self.graph.get_node(conn_id)
                    if node:
                        st.caption(f"→ {node.get('type', 'unknown')}")

    # ========================================================================
    # E. MAIN INTELLIGENCE SUMMARY
    # ========================================================================

    def render_intelligence_summary(self, result: Dict,
                                    show_all_sections: bool = False) -> None:
        """
        Main function to display all intelligence for a result

        Args:
            result: Execution result dictionary
            show_all_sections: Whether to show all sections expanded
        """
        st.markdown("## 🧠 Intelligence Analysis")

        # Section 1: Confidence Scores
        with st.expander("📊 Confidence Scores", expanded=show_all_sections):
            # Extract confidence from result
            confidence = result.get('confidence', 0.75)
            if confidence <= 1:
                confidence *= 100

            # Get component confidences if available
            scores = result.get('confidence_breakdown', {
                'Overall': confidence,
                'Data Quality': result.get('data_quality', 85),
                'Analysis': result.get('analysis_confidence', 80),
                'Prediction': result.get('prediction_confidence', 75)
            })

            self.render_multi_confidence(scores)

        # Section 2: Execution Trace
        execution_history = result.get('execution_history', [])
        if execution_history:
            with st.expander(f"🧠 Thinking Trace ({len(execution_history)} steps)",
                           expanded=show_all_sections):
                self.render_thinking_trace(execution_history, expand_by_default=False)

                # Add timeline view
                st.markdown("#### Timeline View")
                self.render_execution_timeline(execution_history)

        # Section 3: Agent Flow
        agents_used = result.get('agents_used', [])
        if not agents_used and execution_history:
            agents_used = [step.get('agent', 'Unknown') for step in execution_history]
            agents_used = list(dict.fromkeys(agents_used))  # Remove duplicates, preserve order

        if agents_used:
            with st.expander(f"🔄 Agent Flow ({len(agents_used)} agents)",
                           expanded=show_all_sections):
                self.render_agent_flow_diagram(agents_used)

        # Section 4: Decision Provenance
        with st.expander("🔍 Decision Provenance", expanded=show_all_sections):
            self.render_decision_provenance(result)

        # Section 5: Raw Result
        with st.expander("📄 Raw Result Data"):
            st.json(result)

    # ========================================================================
    # F. SYSTEM HEALTH INTELLIGENCE
    # ========================================================================

    def render_system_intelligence(self) -> None:
        """Render overall system intelligence metrics"""
        st.markdown("## 🏥 System Intelligence Health")

        # Get registry metrics
        if self.registry:
            metrics = self.registry.get_compliance_metrics()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Overall Compliance",
                    f"{metrics.get('overall_compliance', 0):.1f}%"
                )

            with col2:
                st.metric(
                    "Total Executions",
                    metrics.get('total_executions', 0)
                )

            with col3:
                st.metric(
                    "Graph Storage Rate",
                    f"{metrics.get('total_stored', 0)}/{metrics.get('total_executions', 0)}"
                )

            with col4:
                agent_count = len(metrics.get('agents', {}))
                st.metric(
                    "Active Agents",
                    agent_count
                )

            # Show per-agent metrics
            st.markdown("### Agent Performance")

            agent_metrics = metrics.get('agents', {})
            if agent_metrics:
                # Create DataFrame for better display
                agent_data = []
                for agent_name, agent_stats in agent_metrics.items():
                    agent_data.append({
                        'Agent': agent_name,
                        'Executions': agent_stats['executions'],
                        'Stored': agent_stats['stored'],
                        'Compliance': f"{agent_stats['compliance_rate']:.1f}%",
                        'Failures': agent_stats['failures']
                    })

                st.dataframe(agent_data, width="stretch")

        # Get graph statistics
        if self.graph:
            st.markdown("### Knowledge Graph Intelligence")

            stats = self.graph.get_stats()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Nodes", stats.get('total_nodes', 0))

            with col2:
                st.metric("Total Edges", stats.get('total_edges', 0))

            with col3:
                st.metric("Patterns", stats.get('total_patterns', 0))

            with col4:
                st.metric("Avg Connections", f"{stats.get('avg_connections', 0):.2f}")

            # Show node type distribution
            node_types = stats.get('node_types', {})
            if node_types:
                st.markdown("#### Node Type Distribution")

                fig = go.Figure(data=[go.Pie(
                    labels=list(node_types.keys()),
                    values=list(node_types.values()),
                    hole=0.3
                )])

                fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, width="stretch")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_intelligence_display(graph: Optional[Any] = None, registry: Optional[Any] = None, runtime: Optional[Any] = None) -> IntelligenceDisplay:
    """Factory function to create IntelligenceDisplay with Trinity components.

    Args:
        graph: KnowledgeGraph instance
        registry: AgentRegistry instance
        runtime: AgentRuntime instance

    Returns:
        Configured IntelligenceDisplay instance
    """
    return IntelligenceDisplay(graph=graph, registry=registry, runtime=runtime)


def quick_confidence_display(confidence: float, label: str = "Confidence") -> None:
    """Quick helper to display a confidence gauge without full setup.

    Args:
        confidence: Confidence score (0-100)
        label: Label for the gauge
    """
    display = IntelligenceDisplay()
    display.render_confidence_gauge(confidence, label)


def quick_thinking_trace(execution_history: ExecutionHistory) -> None:
    """Quick helper to display thinking trace without full setup.

    Args:
        execution_history: List of execution steps
    """
    display = IntelligenceDisplay()
    display.render_thinking_trace(execution_history)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example usage for testing

    # Create sample execution result
    sample_result = {
        'confidence': 0.85,
        'confidence_breakdown': {
            'Overall': 85,
            'Data Quality': 92,
            'Analysis': 88,
            'Prediction': 76
        },
        'execution_history': [
            {
                'agent': 'UniversalExecutor',
                'action': 'route_request',
                'duration_ms': 50,
                'timestamp': '2025-10-03T10:30:00',
                'result': {'status': 'routed', 'pattern': 'analyze_stock'}
            },
            {
                'agent': 'PatternEngine',
                'action': 'match_pattern',
                'duration_ms': 120,
                'timestamp': '2025-10-03T10:30:00',
                'result': {'pattern_id': 'analyze_stock', 'confidence': 0.95}
            },
            {
                'agent': 'DataHarvester',
                'action': 'fetch_data',
                'duration_ms': 350,
                'timestamp': '2025-10-03T10:30:00',
                'result': {'symbol': 'AAPL', 'data_points': 100}
            },
            {
                'agent': 'PatternDetector',
                'action': 'detect_patterns',
                'duration_ms': 280,
                'timestamp': '2025-10-03T10:30:01',
                'result': {'patterns_found': 3, 'strongest': 'uptrend'}
            }
        ],
        'agents_used': ['UniversalExecutor', 'PatternEngine', 'DataHarvester', 'PatternDetector'],
        'reasoning': [
            'Analyzed stock price data for AAPL',
            'Detected strong uptrend pattern with 85% confidence',
            'Historical success rate for this pattern is 78%',
            'Recommend monitoring for continuation'
        ],
        'factors': {
            'trend_strength': 0.85,
            'volume_confirmation': 0.78,
            'historical_accuracy': 0.82
        },
        'node_id': 'decision_abc123'
    }

    # Display intelligence summary
    display = IntelligenceDisplay()
    display.render_intelligence_summary(sample_result, show_all_sections=False)
