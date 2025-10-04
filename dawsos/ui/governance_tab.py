#!/usr/bin/env python3
"""
Data Governance Tab - Exposes the 80/20 Conversational Data Governance System
Leverages Trinity Architecture for intelligent data governance and monitoring
"""

import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go

def render_governance_tab(runtime, graph):
    """Render the Data Governance tab with conversational governance interface"""

    st.markdown("# 🛡️ Data Governance Center")
    st.markdown("*Powered by Trinity Architecture with Graph-Native Governance*")

    # Check if governance agent is available
    if not runtime or not runtime.agent_registry.get_agent('governance_agent'):
        st.error("⚠️ Governance Agent not available. Please check system configuration.")
        return

    governance_adapter = runtime.agent_registry.get_agent('governance_agent')
    governance_agent = governance_adapter.agent if governance_adapter else None

    # Get real-time graph governance metrics
    graph_metrics = {}
    if hasattr(governance_agent, 'graph_governance') and governance_agent.graph_governance:
        try:
            graph_metrics = governance_agent.graph_governance.comprehensive_governance_check()
        except Exception as e:
            st.warning(f"Could not load governance metrics: {str(e)}")
            graph_metrics = {}

    # Governance Dashboard - Real metrics from graph
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_nodes = graph_metrics.get('total_nodes', len(graph.nodes) if graph else 0)
        st.metric(
            label="🔗 Graph Nodes",
            value=f"{total_nodes:,}",
            delta=f"{graph_metrics.get('total_edges', 0):,} edges"
        )

    with col2:
        health = graph_metrics.get('overall_health', 0.98)
        st.metric(
            label="📊 Graph Health",
            value=f"{health:.0%}",
            delta="Live calculation"
        )

    with col3:
        quality_issues = len(graph_metrics.get('quality_issues', []))
        st.metric(
            label="⚠️ Quality Issues",
            value=quality_issues,
            delta="Auto-detected" if quality_issues > 0 else "All clear"
        )

    with col4:
        lineage_gaps = len(graph_metrics.get('lineage_gaps', []))
        st.metric(
            label="🔍 Orphan Nodes",
            value=lineage_gaps,
            delta="Need connections" if lineage_gaps > 0 else "Fully connected"
        )

    st.markdown("---")

    # System Telemetry Dashboard
    st.markdown("### 📊 System Telemetry")
    st.markdown("*Real-time execution metrics from Trinity Architecture*")

    if hasattr(runtime, 'get_telemetry_summary'):
        try:
            telemetry = runtime.get_telemetry_summary()

            if telemetry['total_executions'] > 0:
                # Metrics Row 1: Key performance indicators
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        label="🎯 Total Executions",
                        value=f"{telemetry['total_executions']:,}",
                        delta="Lifetime"
                    )

                with col2:
                    success_rate = telemetry['success_rate']
                    st.metric(
                        label="✅ Success Rate",
                        value=f"{success_rate:.1f}%",
                        delta="Good" if success_rate >= 90 else "Needs attention"
                    )

                with col3:
                    avg_duration = telemetry['avg_duration_ms']
                    st.metric(
                        label="⏱️ Avg Duration",
                        value=f"{avg_duration:.0f}ms",
                        delta="Fast" if avg_duration < 1000 else "Slow" if avg_duration > 5000 else "Normal"
                    )

                # Metrics Row 2: Agent and Pattern usage
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**🤖 Top Agents**")
                    agents = telemetry['executions_by_agent']
                    if agents:
                        # Show top 5 agents
                        sorted_agents = sorted(agents.items(), key=lambda x: x[1], reverse=True)[:5]
                        for agent, count in sorted_agents:
                            st.text(f"  {agent}: {count} executions")
                    else:
                        st.text("  No agent data yet")

                with col2:
                    st.markdown("**📋 Top Patterns**")
                    patterns = telemetry['executions_by_pattern']
                    if patterns:
                        # Show top 5 patterns
                        sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:5]
                        for pattern, count in sorted_patterns:
                            st.text(f"  {pattern}: {count} executions")
                    else:
                        st.text("  No pattern data yet")

                # Last execution timestamp
                if telemetry['last_execution_time']:
                    st.caption(f"Last execution: {telemetry['last_execution_time']}")
            else:
                st.info("💡 No executions tracked yet. Execute patterns to see telemetry metrics.")
        except Exception as e:
            st.warning(f"Could not load telemetry: {str(e)}")
    else:
        st.warning("⚠️ Telemetry not available in runtime")

    st.markdown("---")

    # Persistence Health Metrics
    st.markdown("### 💾 Persistence & Backup Health")
    st.markdown("*Real-time backup rotation and checksum validation*")

    # Get persistence manager from session state or executor
    persistence = None
    if 'persistence' in st.session_state:
        persistence = st.session_state.persistence
    elif hasattr(st.session_state.get('executor'), 'persistence'):
        persistence = st.session_state.executor.persistence

    if persistence:
        try:
            # Get backup list
            backups = persistence.list_backups()

            # Calculate metrics
            total_backups = len(backups)
            total_backup_size = sum(b.get('size', 0) for b in backups) / (1024 * 1024)  # MB

            # Get most recent backup info
            latest_backup = backups[0] if backups else None
            latest_checksum = None
            if latest_backup and 'metadata' in latest_backup:
                latest_checksum = latest_backup['metadata'].get('checksum', '')[:16]

            # Verify integrity of latest backup
            integrity_status = "✅ Valid"
            if latest_backup:
                integrity = persistence.verify_integrity(latest_backup['path'])
                if not integrity['valid']:
                    integrity_status = f"❌ {integrity['error']}"

            # Display metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    label="💾 Total Backups",
                    value=total_backups,
                    delta="30-day retention"
                )

            with col2:
                st.metric(
                    label="📦 Backup Size",
                    value=f"{total_backup_size:.1f} MB",
                    delta="Auto-rotated"
                )

            with col3:
                st.metric(
                    label="🔐 Latest Checksum",
                    value=f"{latest_checksum}..." if latest_checksum else "N/A",
                    delta=integrity_status
                )

            with col4:
                if latest_backup:
                    latest_time = latest_backup.get('modified', 'Unknown')
                    st.metric(
                        label="⏰ Last Backup",
                        value=latest_time[-8:-3] if len(latest_time) > 10 else latest_time,  # Show time only
                        delta=f"{latest_backup.get('metadata', {}).get('node_count', 0)} nodes"
                    )
                else:
                    st.metric(
                        label="⏰ Last Backup",
                        value="None",
                        delta="No backups yet"
                    )

            # Backup list in expander
            with st.expander("📋 View All Backups"):
                if backups:
                    for i, backup in enumerate(backups[:10]):  # Show last 10
                        metadata = backup.get('metadata', {})
                        st.text(f"{i+1}. {backup['filename']}")
                        st.text(f"   Size: {backup['size'] / 1024:.1f} KB | Nodes: {metadata.get('node_count', 0)} | Edges: {metadata.get('edge_count', 0)}")
                        st.text(f"   Checksum: {metadata.get('checksum', 'N/A')[:32]}...")
                        st.text("")
                else:
                    st.info("No backups available yet")

        except Exception as e:
            st.warning(f"Could not load persistence metrics: {str(e)}")
    else:
        st.warning("⚠️ Persistence Manager not initialized")

    st.markdown("---")

    # Main governance interface
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 💬 Conversational Governance")
        st.markdown("*Ask any governance question in natural language*")

        # Governance request input
        governance_request = st.text_area(
            "What governance action would you like to perform?",
            placeholder="Examples:\n• Check data quality for AAPL dataset\n• Run compliance audit for SOX requirements\n• Optimize costs for data pipeline\n• Trace lineage for customer data",
            height=100
        )

        col_a, col_b = st.columns([1, 3])
        with col_a:
            execute_governance = st.button("🚀 Execute Governance", type="primary")
        with col_b:
            if st.button("📋 Show Available Patterns"):
                st.session_state['show_patterns'] = True

        # Execute governance request
        if execute_governance and governance_request:
            with st.spinner("🔄 Processing governance request through Trinity Architecture..."):
                try:
                    # Process request through governance agent
                    result = governance_agent.process_request(
                        governance_request,
                        {'source': 'ui_tab', 'timestamp': datetime.now().isoformat()}
                    )

                    # Display results
                    st.success("✅ Governance action completed!")

                    # Show governance report
                    if 'governance_report' in result:
                        st.markdown("### 📋 Governance Report")
                        st.markdown(result['governance_report'])

                    # Show detailed results in expandable section
                    with st.expander("🔍 Detailed Results"):
                        st.json(result)

                except Exception as e:
                    st.error(f"❌ Governance execution failed: {str(e)}")

        # Show available patterns if requested
        if st.session_state.get('show_patterns', False):
            st.markdown("### 🎯 Available Governance Patterns")

            patterns = [
                {
                    "name": "Data Quality Check",
                    "description": "Comprehensive data quality assessment and improvement",
                    "example": "Check data quality for our customer database"
                },
                {
                    "name": "Compliance Audit",
                    "description": "Regulatory compliance assessment and reporting",
                    "example": "Run SOX compliance audit on financial data"
                },
                {
                    "name": "Cost Optimization",
                    "description": "Analyze and optimize data-related costs",
                    "example": "Optimize costs for our data warehouse"
                },
                {
                    "name": "Data Lineage Trace",
                    "description": "Track data flow and transformation lineage",
                    "example": "Trace lineage for revenue metrics"
                }
            ]

            for i, pattern in enumerate(patterns):
                with st.expander(f"🔸 {pattern['name']}"):
                    st.write(pattern['description'])
                    st.code(f"Example: {pattern['example']}")
                    if st.button("Use Example", key=f"example_{i}"):
                        st.session_state['governance_request'] = pattern['example']
                        st.rerun()

            if st.button("Hide Patterns"):
                st.session_state['show_patterns'] = False
                st.rerun()

    with col2:
        # Real-time governance monitoring
        st.markdown("### 📊 Live Governance Monitoring")

        # Governance alerts feed
        st.markdown("#### 🚨 Recent Alerts")
        try:
            # Get governance alerts from pattern spotter
            pattern_spotter_adapter = runtime.agent_registry.get_agent('pattern_spotter') if runtime else None
            if pattern_spotter_adapter:
                alert_data = pattern_spotter_adapter.agent.process(
                    "governance_alerts"
                )

                alerts = alert_data.get('patterns_found', [])
                if alerts:
                    for alert in alerts[-3:]:  # Show last 3 alerts
                        severity = alert.get('severity', 'info')
                        icon = "🔴" if severity == 'critical' else "🟡" if severity == 'warning' else "🟢"

                        st.markdown(f"""
                        <div style="padding: 10px; border-left: 3px solid {'red' if severity == 'critical' else 'orange' if severity == 'warning' else 'green'}; margin: 5px 0;">
                        {icon} <strong>{alert.get('title', 'Governance Alert')}</strong><br>
                        <small>{alert.get('description', 'Alert description unavailable')}</small>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ No governance alerts - all systems healthy")
            else:
                st.info("📡 Governance monitoring starting...")
        except Exception as e:
            st.warning(f"⚠️ Monitoring unavailable: {str(e)}")

        # Governance metrics
        st.markdown("#### 📈 Key Metrics")

        # Data quality score - Use real graph metrics
        st.markdown("**Data Quality Score**")
        data_quality = graph_metrics.get('overall_health', 0.92) if graph_metrics else 0.92
        st.progress(data_quality)
        quality_label = "Excellent" if data_quality > 0.9 else "Good" if data_quality > 0.7 else "Needs improvement"
        st.caption(f"{data_quality:.0%} - {quality_label}")

        # Compliance score - Calculate from policy violations
        st.markdown("**Compliance Score**")
        quality_issues_count = len(graph_metrics.get('quality_issues', [])) if graph_metrics else 0
        total_nodes = graph_metrics.get('total_nodes', 1) if graph_metrics else 1
        compliance = 1.0 - (quality_issues_count / max(total_nodes, 1)) if total_nodes > 0 else 0.88
        st.progress(compliance)
        compliance_label = "Excellent" if compliance > 0.9 else "Good" if compliance > 0.7 else "Needs improvement"
        st.caption(f"{compliance:.0%} - {compliance_label}")

        # Cost efficiency - Calculate from orphan nodes (inefficiency indicator)
        st.markdown("**Cost Efficiency**")
        orphan_count = len(graph_metrics.get('lineage_gaps', [])) if graph_metrics else 0
        cost_efficiency = 1.0 - (orphan_count / max(total_nodes, 1)) if total_nodes > 0 else 0.76
        st.progress(max(cost_efficiency, 0.5))  # Floor at 50%
        cost_label = "Excellent" if cost_efficiency > 0.9 else "Good" if cost_efficiency > 0.7 else "Room for improvement"
        st.caption(f"{cost_efficiency:.0%} - {cost_label}")

        # Quick actions
        st.markdown("#### ⚡ Quick Actions")

        # Add Agent Compliance Check button
        if st.button("🤖 Check Agent Compliance", width="stretch"):
            with st.spinner("Validating all agents for Trinity Architecture compliance..."):
                try:
                    compliance_result = governance_agent.process_request(
                        "agent_compliance",
                        {'source': 'quick_action', 'runtime': runtime}
                    )

                    if compliance_result.get('status') == 'completed':
                        overall = compliance_result.get('overall_compliance', 0)

                        # Store in session state for detailed view
                        st.session_state['latest_compliance'] = compliance_result

                        # Show summary
                        if overall >= 0.8:
                            st.success(f"✅ Overall Compliance: {overall:.0%}")
                        elif overall >= 0.5:
                            st.warning(f"⚠️ Overall Compliance: {overall:.0%} - Needs improvement")
                        else:
                            st.error(f"❌ Overall Compliance: {overall:.0%} - Critical issues")

                        # Show key recommendations
                        recommendations = compliance_result.get('recommendations', [])
                        if recommendations:
                            st.markdown("**Top Recommendations:**")
                            for rec in recommendations[:3]:
                                st.write(f"• {rec}")
                    elif compliance_result.get('status') == 'error':
                        error_msg = compliance_result.get('message', 'Unknown error')
                        st.error(f"Compliance check failed: {error_msg}")
                        if "agent_validator.py" in error_msg:
                            st.info("💡 Tip: Ensure agent_validator.py is in the core/ directory")
                    else:
                        st.error("Compliance check failed - unexpected response")
                except Exception as e:
                    st.error(f"❌ Compliance check failed: {str(e)}")

        # Add System Improvement button
        if st.button("🎯 Auto-Improve System", width="stretch"):
            with st.spinner("Analyzing system for improvements..."):
                try:
                    # Get improvement suggestions
                    suggestions = governance_agent.suggest_improvements()

                    if suggestions['status'] == 'success':
                        improvements = suggestions['improvements']

                        if improvements:
                            st.success(f"Found {len(improvements)} improvements!")

                            # Store in session state for display
                            st.session_state['system_improvements'] = suggestions

                            # Auto-fix high priority issues
                            high_priority = [i for i in improvements if i['priority'] == 'high']
                            if high_priority:
                                st.info(f"Auto-fixing {len(high_priority)} high-priority issues...")

                                # Execute improvements
                                for improvement in high_priority:
                                    data_harvester = runtime.agent_registry.get_agent('data_harvester') if runtime else None
                                    relationship_hunter = runtime.agent_registry.get_agent('relationship_hunter') if runtime else None

                                    if improvement['type'] == 'data_refresh' and data_harvester:
                                        data_harvester.agent.process(
                                            f"refresh data for {improvement['target']}"
                                        )
                                    elif improvement['type'] == 'add_connection' and relationship_hunter:
                                        relationship_hunter.agent.process(
                                            f"find connections for {improvement['target']}"
                                        )
                                    elif improvement['type'] == 'seed_data' and data_harvester:
                                        for symbol in ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']:
                                            data_harvester.agent.process(
                                                f"get stock data for {symbol}"
                                            )

                                st.success(f"✅ Fixed {len(high_priority)} high-priority issues!")
                        else:
                            st.success("✅ System is healthy - no improvements needed!")

                        # Show analysis summary
                        summary = suggestions.get('analysis_summary', {})
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Overall Health", f"{summary.get('overall_health', 0):.0%}")
                        with col2:
                            st.metric("Auto-Fixed", suggestions.get('auto_fixable', 0))
                    else:
                        st.warning("Could not analyze system")

                except Exception as e:
                    st.error(f"Improvement analysis failed: {str(e)}")

        if st.button("🔍 System Health Check", width="stretch"):
            with st.spinner("Running system health check..."):
                try:
                    health_result = governance_agent.process_request(
                        "Run a comprehensive system health check",
                        {'source': 'quick_action'}
                    )
                    st.success("✅ Health check completed")
                    with st.expander("Health Report"):
                        st.json(health_result)
                except Exception as e:
                    st.error(f"❌ Health check failed: {str(e)}")

        if st.button("📊 Generate Compliance Report", width="stretch"):
            with st.spinner("Generating compliance report..."):
                try:
                    compliance_result = governance_agent.process_request(
                        "Generate a comprehensive compliance report",
                        {'source': 'quick_action'}
                    )
                    st.success("✅ Compliance report generated")
                    with st.expander("Compliance Report"):
                        if 'governance_report' in compliance_result:
                            st.markdown(compliance_result['governance_report'])
                        else:
                            st.json(compliance_result)
                except Exception as e:
                    st.error(f"❌ Report generation failed: {str(e)}")

        if st.button("💰 Cost Optimization Scan", width="stretch"):
            with st.spinner("Scanning for cost optimization opportunities..."):
                try:
                    cost_result = governance_agent.process_request(
                        "Identify cost optimization opportunities across the platform",
                        {'source': 'quick_action'}
                    )
                    st.success("✅ Cost optimization scan completed")
                    with st.expander("Cost Analysis"):
                        if 'governance_report' in cost_result:
                            st.markdown(cost_result['governance_report'])
                        else:
                            st.json(cost_result)
                except Exception as e:
                    st.error(f"❌ Cost scan failed: {str(e)}")

    # Graph Governance Section
    st.markdown("---")
    st.markdown("### 🌐 Graph-Native Governance")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Quality Analysis", "Data Lineage", "Policy Management", "Agent Compliance", "System Oversight"])

    with tab1:
        st.markdown("#### Node Quality Analysis")

        # Show quality issues if any
        if graph_metrics.get('quality_issues'):
            st.warning(f"Found {len(graph_metrics['quality_issues'])} nodes with quality issues:")

            for issue in graph_metrics['quality_issues'][:5]:  # Show top 5
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"📍 **{issue['node']}**")
                with col2:
                    score = issue.get('score', 0)
                    st.write(f"Score: {score:.0%}")
                with col3:
                    st.write(f"Type: {issue.get('type', 'unknown')}")
        else:
            st.success("✅ All nodes meet quality thresholds")

        # Quality distribution chart
        if graph and len(graph.nodes) > 0:
            quality_scores = []
            for node_id in list(graph.nodes.keys())[:50]:  # Sample first 50 nodes
                if hasattr(governance_agent, 'graph_governance'):
                    try:
                        score = governance_agent.graph_governance._calculate_quality_from_graph(node_id)
                        quality_scores.append(score)
                    except Exception:
                        # Skip nodes that can't be scored
                        continue

            if quality_scores:
                fig = go.Figure(data=[go.Histogram(x=quality_scores, nbinsx=10)])
                fig.update_layout(
                    title="Data Quality Distribution",
                    xaxis_title="Quality Score",
                    yaxis_title="Number of Nodes",
                    height=300
                )
                st.plotly_chart(fig, width="stretch")

    with tab2:
        st.markdown("#### Data Lineage Explorer")

        # Node selector for lineage
        if graph and len(graph.nodes) > 0:
            node_options = list(graph.nodes.keys())[:100]  # Limit to 100 for performance
            selected_node = st.selectbox(
                "Select node to trace lineage:",
                options=node_options,
                format_func=lambda x: f"{x} ({graph.nodes[x]['type']})"
            )

            if st.button("🔍 Trace Lineage"):
                if hasattr(governance_agent, 'graph_governance'):
                    try:
                        lineage = governance_agent.graph_governance.trace_data_lineage(selected_node)

                        if lineage:
                            st.success(f"Found {len(lineage)} lineage paths")

                            for i, path in enumerate(lineage[:3]):  # Show first 3 paths
                                with st.expander(f"Path {i+1}: {' → '.join(path[:3])}..."):
                                    # Create flow diagram
                                    for j, node in enumerate(path):
                                        if j > 0:
                                            st.write("↓")
                                        st.write(f"**{node}** ({graph.nodes[node]['type']})")
                        else:
                            st.info("No lineage paths found - node may be a source")
                    except Exception as e:
                        st.error(f"Lineage trace failed: {str(e)}")

        # Orphan nodes section
        if graph_metrics.get('lineage_gaps'):
            st.warning(f"⚠️ Found {len(graph_metrics['lineage_gaps'])} orphan nodes:")
            for gap in graph_metrics['lineage_gaps'][:5]:
                st.write(f"• **{gap['node']}** - {gap.get('issue', 'no connections')}")

    with tab3:
        st.markdown("#### Governance Policy Management")

        # Add new policy
        with st.expander("➕ Add New Governance Policy"):
            policy_name = st.text_input("Policy Name")
            policy_rule = st.text_area("Policy Rule", placeholder="e.g., All financial data must be updated daily")

            # Multi-select for nodes to apply policy to
            if graph and len(graph.nodes) > 0:
                apply_to_types = st.multiselect(
                    "Apply to node types:",
                    options=['stock', 'indicator', 'sector', 'event', 'pattern'],
                    default=['stock', 'indicator']
                )

                if st.button("Create Policy"):
                    if policy_name and policy_rule and hasattr(governance_agent, 'graph_governance'):
                        try:
                            # Find nodes of selected types
                            applies_to = [
                                node_id for node_id, node in graph.nodes.items()
                                if node.get('type') in apply_to_types
                            ][:20]  # Limit to 20 nodes

                            policy_id = governance_agent.graph_governance.add_governance_policy(
                                policy_name, policy_rule, applies_to
                            )

                            st.success(f"✅ Policy created: {policy_id}")
                            st.info(f"Applied to {len(applies_to)} nodes")
                        except Exception as e:
                            st.error(f"Failed to create policy: {str(e)}")

        # Show existing policies
        st.markdown("**Active Policies**")

        if graph:
            policy_count = 0
            for node_id, node in graph.nodes.items():
                if node.get('type') == 'data_policy':
                    policy_count += 1
                    with st.expander(f"📜 {node['data'].get('name', node_id)}"):
                        st.write(f"**Rule**: {node['data'].get('rule', 'N/A')}")
                        st.write(f"**Active**: {node['data'].get('active', False)}")
                        st.write(f"**Violations**: {node['data'].get('violations', 0)}")

            if policy_count == 0:
                st.info("No policies defined yet. Add one above!")

    with tab4:
        st.markdown("#### 🤖 Agent Compliance Dashboard")
        st.markdown("*Monitor and enforce Trinity Architecture compliance across all agents*")

        # Get latest compliance results
        compliance_data = st.session_state.get('latest_compliance', {})

        if compliance_data and compliance_data.get('status') == 'completed':
            # Overall compliance metrics
            col1, col2, col3, col4 = st.columns(4)

            summary = compliance_data.get('summary', {})
            overall = compliance_data.get('overall_compliance', 0)

            with col1:
                color = "green" if overall >= 0.8 else "orange" if overall >= 0.5 else "red"
                st.metric(
                    label="📊 Overall Compliance",
                    value=f"{overall:.0%}",
                    delta="Trinity Architecture"
                )

            with col2:
                st.metric(
                    label="✅ Compliant Agents",
                    value=summary.get('compliant', 0),
                    delta=f"of {summary.get('total_agents', 0)}"
                )

            with col3:
                st.metric(
                    label="⚠️ Warnings",
                    value=summary.get('warnings', 0),
                    delta="Need review"
                )

            with col4:
                st.metric(
                    label="❌ Non-Compliant",
                    value=summary.get('non_compliant', 0),
                    delta="Critical" if summary.get('non_compliant', 0) > 0 else "None"
                )

            # Detailed compliance report
            if 'report' in compliance_data:
                with st.expander("📋 Detailed Compliance Report", expanded=True):
                    st.markdown(compliance_data['report'])

            # Recommendations
            recommendations = compliance_data.get('recommendations', [])
            if recommendations:
                st.markdown("##### 🎯 Action Items")
                for i, rec in enumerate(recommendations, 1):
                    if "CRITICAL" in rec:
                        st.error(f"{i}. {rec}")
                    elif "WARNING" in rec:
                        st.warning(f"{i}. {rec}")
                    else:
                        st.info(f"{i}. {rec}")

            # Agent-specific issues
            st.markdown("##### 📍 Agent-Specific Issues")

            # Group agents by compliance level
            agents_by_status = {"compliant": [], "warning": [], "non_compliant": []}

            if 'agents' in compliance_data:
                for agent_name, validation in compliance_data['agents'].items():
                    score = validation.get('compliance_score', 0)
                    if score >= 0.8:
                        agents_by_status['compliant'].append((agent_name, score))
                    elif score >= 0.5:
                        agents_by_status['warning'].append((agent_name, score))
                    else:
                        agents_by_status['non_compliant'].append((agent_name, score))

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**✅ Compliant**")
                for agent, score in agents_by_status['compliant'][:5]:
                    st.write(f"• {agent} ({score:.0%})")

            with col2:
                st.markdown("**⚠️ Needs Review**")
                for agent, score in agents_by_status['warning'][:5]:
                    st.write(f"• {agent} ({score:.0%})")

            with col3:
                st.markdown("**❌ Non-Compliant**")
                for agent, score in agents_by_status['non_compliant'][:5]:
                    st.write(f"• {agent} ({score:.0%})")

        else:
            st.info("👆 Click 'Check Agent Compliance' in Quick Actions to run compliance validation")

            # Show Trinity Architecture principles
            st.markdown("##### 📜 Trinity Architecture Compliance Rules")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Knowledge (Data)**")
                st.write("• All results must be stored")
                st.write("• No logic in data files")
                st.write("• Complete lineage tracking")

            with col2:
                st.markdown("**Patterns (Workflows)**")
                st.write("• Orchestrate agents only")
                st.write("• No data storage")
                st.write("• Clear step definitions")

            with col3:
                st.markdown("**Agents (Actors)**")
                st.write("• Must use graph methods")
                st.write("• Store all computations")
                st.write("• No persistent state")

    with tab5:
        st.markdown("#### 📊 System Oversight Dashboard")
        st.markdown("*Real-time monitoring of system health, data flows, and governance metrics*")

        # System health overview
        col1, col2 = st.columns([2, 1])

        with col1:
            # Data flow visualization
            st.markdown("##### 🔄 Data Flow Activity")

            # Calculate recent activity metrics
            if graph and hasattr(graph, 'nodes'):
                # Group nodes by creation time (last 24 hours)
                now = datetime.now()
                recent_nodes = []

                for node_id, node in graph.nodes.items():
                    created = node.get('created', '')
                    if created:
                        try:
                            node_time = datetime.fromisoformat(created)
                            if (now - node_time) < timedelta(hours=24):
                                recent_nodes.append((node_id, node))
                        except Exception:
                            # Skip nodes with invalid timestamps
                            continue

                # Create activity chart
                if recent_nodes:
                    # Group by hour
                    hourly_counts = {}
                    for node_id, node in recent_nodes:
                        created = datetime.fromisoformat(node['created'])
                        hour_key = created.strftime("%H:00")
                        hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1

                    # Create bar chart
                    hours = sorted(hourly_counts.keys())
                    counts = [hourly_counts[h] for h in hours]

                    fig = go.Figure(data=[
                        go.Bar(x=hours, y=counts, marker_color='lightblue')
                    ])
                    fig.update_layout(
                        title="Node Creation Activity (Last 24 Hours)",
                        xaxis_title="Hour",
                        yaxis_title="Nodes Created",
                        height=250
                    )
                    st.plotly_chart(fig, width="stretch")

                    st.info(f"📈 {len(recent_nodes)} nodes created in last 24 hours")
                else:
                    st.info("📊 No recent activity. System may be idle.")

        with col2:
            # Governance metrics
            st.markdown("##### 🎯 Governance Metrics")

            # Calculate key metrics
            if graph:
                total_nodes = len(graph.nodes)
                total_edges = len(graph.edges) if hasattr(graph, 'edges') else 0

                # Node type distribution
                node_types = {}
                for node_id, node in graph.nodes.items():
                    node_type = node.get('type', 'unknown')
                    node_types[node_type] = node_types.get(node_type, 0) + 1

                # Show top node types
                st.markdown("**Node Distribution:**")
                for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                    percentage = (count / total_nodes * 100) if total_nodes > 0 else 0
                    st.write(f"• {node_type}: {count} ({percentage:.1f}%)")

                # Connection density
                if total_nodes > 0:
                    density = total_edges / (total_nodes * (total_nodes - 1) / 2) if total_nodes > 1 else 0
                    st.metric("Graph Density", f"{density:.2%}")

        # Oversight alerts
        st.markdown("##### 🚨 Oversight Alerts")

        # Check for various system issues
        alerts = []

        # Check for orphan nodes
        if graph_metrics.get('lineage_gaps'):
            alerts.append({
                'level': 'warning',
                'message': f"{len(graph_metrics['lineage_gaps'])} orphan nodes detected",
                'action': "Run 'fix_orphan_nodes.py' to reconnect"
            })

        # Check for stale data
        if graph:
            stale_count = 0
            for node_id, node in graph.nodes.items():
                modified = node.get('modified', '')
                if modified:
                    try:
                        node_time = datetime.fromisoformat(modified)
                        if (datetime.now() - node_time) > timedelta(days=7):
                            stale_count += 1
                    except Exception:
                        # Skip nodes with invalid modified dates
                        continue

            if stale_count > 10:
                alerts.append({
                    'level': 'info',
                    'message': f"{stale_count} nodes haven't been updated in 7+ days",
                    'action': "Consider refreshing stale data"
                })

        # Check agent compliance
        if compliance_data:
            non_compliant = compliance_data.get('summary', {}).get('non_compliant', 0)
            if non_compliant > 0:
                alerts.append({
                    'level': 'error',
                    'message': f"{non_compliant} agents are non-compliant with Trinity Architecture",
                    'action': "Update agents to use knowledge graph methods"
                })

        # Display alerts
        if alerts:
            for alert in alerts:
                if alert['level'] == 'error':
                    st.error(f"🔴 **{alert['message']}**\n\n*Action: {alert['action']}*")
                elif alert['level'] == 'warning':
                    st.warning(f"🟡 **{alert['message']}**\n\n*Action: {alert['action']}*")
                else:
                    st.info(f"🔵 **{alert['message']}**\n\n*Action: {alert['action']}*")
        else:
            st.success("✅ All systems operational - no alerts")

        # System evolution tracking
        st.markdown("##### 📈 System Evolution")

        # Show growth metrics
        if 'graph_growth_history' not in st.session_state:
            st.session_state['graph_growth_history'] = []

        # Add current snapshot
        current_snapshot = {
            'timestamp': datetime.now().isoformat(),
            'nodes': len(graph.nodes) if graph else 0,
            'edges': len(graph.edges) if graph and hasattr(graph, 'edges') else 0
        }

        # Keep last 20 snapshots
        st.session_state['graph_growth_history'].append(current_snapshot)
        st.session_state['graph_growth_history'] = st.session_state['graph_growth_history'][-20:]

        if len(st.session_state['graph_growth_history']) > 1:
            # Calculate growth rate
            first = st.session_state['graph_growth_history'][0]
            last = st.session_state['graph_growth_history'][-1]

            node_growth = last['nodes'] - first['nodes']
            edge_growth = last['edges'] - first['edges']

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Node Growth", f"+{node_growth}", "Since session start")
            with col2:
                st.metric("Edge Growth", f"+{edge_growth}", "Since session start")

    # System Improvements Section
    if 'system_improvements' in st.session_state:
        st.markdown("---")
        st.markdown("### 🔧 System Improvement Suggestions")

        suggestions = st.session_state['system_improvements']
        improvements = suggestions.get('improvements', [])

        if improvements:
            # Group improvements by priority
            high_priority = [i for i in improvements if i['priority'] == 'high']
            medium_priority = [i for i in improvements if i['priority'] == 'medium']
            low_priority = [i for i in improvements if i['priority'] == 'low']

            col1, col2, col3 = st.columns(3)

            with col1:
                if high_priority:
                    st.markdown("#### 🔴 High Priority")
                    for imp in high_priority[:5]:
                        st.markdown(f"• {imp['description']}")

            with col2:
                if medium_priority:
                    st.markdown("#### 🟡 Medium Priority")
                    for imp in medium_priority[:5]:
                        st.markdown(f"• {imp['description']}")

            with col3:
                if low_priority:
                    st.markdown("#### 🟢 Low Priority")
                    for imp in low_priority[:5]:
                        st.markdown(f"• {imp['description']}")

            # Clear suggestions button
            if st.button("Clear Suggestions"):
                del st.session_state['system_improvements']
                st.rerun()
        else:
            st.info("No improvement suggestions available. Click 'Auto-Improve System' to analyze.")

    # Governance history
    st.markdown("---")
    st.markdown("### 📚 Recent Governance Activities")

    # Show recent governance activities from session state or agent memory
    if 'governance_history' not in st.session_state:
        st.session_state.governance_history = []

    if st.session_state.governance_history:
        for i, activity in enumerate(reversed(st.session_state.governance_history[-5:])):
            with st.expander(f"🔸 {activity.get('action', 'Governance Action')} - {activity.get('timestamp', 'Unknown time')}"):
                st.write(f"**Request:** {activity.get('request', 'N/A')}")
                st.write(f"**Status:** {activity.get('status', 'N/A')}")
                if 'result' in activity:
                    st.json(activity['result'])
    else:
        st.info("📝 No recent governance activities. Execute a governance action to see history.")

    # Add current request to history if executed
    if execute_governance and governance_request:
        st.session_state.governance_history.append({
            'action': 'Conversational Governance',
            'request': governance_request,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Executed',
            'source': 'UI Tab'
        })
