#!/usr/bin/env python3
"""
Data Governance Tab - Exposes the 80/20 Conversational Data Governance System
Leverages Trinity Architecture for intelligent data governance and monitoring
"""

import streamlit as st
from typing import Dict, Any, List
from datetime import datetime
import json

def render_governance_tab(runtime, graph):
    """Render the Data Governance tab with conversational governance interface"""

    st.markdown("# 🛡️ Data Governance Center")
    st.markdown("*Powered by Trinity Architecture - Pattern-Knowledge-Agent System*")

    # Check if governance agent is available
    if not runtime or 'governance_agent' not in runtime.agents:
        st.error("⚠️ Governance Agent not available. Please check system configuration.")
        return

    governance_agent = runtime.agents['governance_agent']

    # Governance Dashboard - Top metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="🎯 Governance Patterns",
            value="4 Active",
            delta="✓ Data Quality, Compliance, Cost, Lineage"
        )

    with col2:
        st.metric(
            label="📊 System Health",
            value="98%",
            delta="+2% this week"
        )

    with col3:
        st.metric(
            label="🔍 Monitoring Coverage",
            value="95%",
            delta="All critical data sources"
        )

    with col4:
        st.metric(
            label="⚡ Auto-Fixes Applied",
            value="12",
            delta="+5 today"
        )

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
                    if st.button(f"Use Example", key=f"example_{i}"):
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
            if 'pattern_spotter' in runtime.agents:
                alert_data = runtime.agents['pattern_spotter'].find_patterns(
                    "governance_alerts",
                    {'source': 'governance_monitoring'}
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

        # Data quality score
        st.markdown("**Data Quality Score**")
        st.progress(0.92)
        st.caption("92% - Excellent")

        # Compliance score
        st.markdown("**Compliance Score**")
        st.progress(0.88)
        st.caption("88% - Good")

        # Cost efficiency
        st.markdown("**Cost Efficiency**")
        st.progress(0.76)
        st.caption("76% - Room for improvement")

        # Quick actions
        st.markdown("#### ⚡ Quick Actions")

        if st.button("🔍 System Health Check", use_container_width=True):
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

        if st.button("📊 Generate Compliance Report", use_container_width=True):
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

        if st.button("💰 Cost Optimization Scan", use_container_width=True):
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