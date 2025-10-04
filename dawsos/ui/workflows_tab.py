"""
Workflows Tab - Investment workflow management and execution
"""
import streamlit as st
from datetime import datetime
import pandas as pd

def render_workflows_tab(workflows, graph, runtime):
    """Render the workflows management tab"""

    st.markdown("## 🔄 Investment Workflows")
    st.markdown("Automated investment analysis patterns based on Buffett, Ackman, and Dalio frameworks")

    # Create three columns for workflow categories
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📊 Daily Workflows")
        workflows_daily = [w for w in workflows.workflows.items()
                          if w[1]['frequency'] == 'daily']
        for wf_name, wf_data in workflows_daily:
            with st.expander(wf_data['name']):
                st.markdown(f"**Description:** {wf_data['description']}")
                st.markdown(f"**Priority:** {wf_data['priority']}")
                st.markdown(f"**Steps:** {len(wf_data['steps'])}")

                if st.button(f"▶️ Run {wf_data['name']}", key=f"run_{wf_name}"):
                    with st.spinner(f"Running {wf_data['name']}..."):
                        result = workflows.execute_workflow(wf_name)
                        workflows.save_workflow_result(result)
                        st.success(f"✅ {wf_data['name']} completed!")

                        # Show results
                        st.json(result)

    with col2:
        st.markdown("### 📈 Weekly Workflows")
        workflows_weekly = [w for w in workflows.workflows.items()
                           if w[1]['frequency'] == 'weekly']
        for wf_name, wf_data in workflows_weekly:
            with st.expander(wf_data['name']):
                st.markdown(f"**Description:** {wf_data['description']}")
                st.markdown(f"**Priority:** {wf_data['priority']}")
                st.markdown(f"**Steps:** {len(wf_data['steps'])}")

                if st.button(f"▶️ Run {wf_data['name']}", key=f"run_{wf_name}"):
                    with st.spinner(f"Running {wf_data['name']}..."):
                        result = workflows.execute_workflow(wf_name)
                        workflows.save_workflow_result(result)
                        st.success(f"✅ {wf_data['name']} completed!")

                        # Show results
                        st.json(result)

    with col3:
        st.markdown("### 📆 Periodic Workflows")
        workflows_other = [w for w in workflows.workflows.items()
                          if w[1]['frequency'] not in ['daily', 'weekly']]
        for wf_name, wf_data in workflows_other:
            with st.expander(wf_data['name']):
                st.markdown(f"**Description:** {wf_data['description']}")
                st.markdown(f"**Frequency:** {wf_data['frequency']}")
                st.markdown(f"**Steps:** {len(wf_data['steps'])}")

                if st.button(f"▶️ Run {wf_data['name']}", key=f"run_{wf_name}"):
                    with st.spinner(f"Running {wf_data['name']}..."):
                        result = workflows.execute_workflow(wf_name)
                        workflows.save_workflow_result(result)
                        st.success(f"✅ {wf_data['name']} completed!")

                        # Show results
                        st.json(result)

    st.markdown("---")

    # Quick Actions Section
    st.markdown("### ⚡ Quick Actions")
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)

    with quick_col1:
        if st.button("🌅 Morning Briefing", width="stretch"):
            with st.spinner("Generating morning briefing..."):
                result = workflows.execute_workflow('morning_briefing')
                workflows.save_workflow_result(result)

                # Display formatted briefing
                st.markdown("### Today's Investment Briefing")

                # Get regime
                regime = graph.nodes.get('ECONOMIC_REGIME', {})
                regime_state = regime.get('data', {}).get('current_state', 'Unknown')
                st.info(f"**Current Regime:** {regime_state}")

                # Find value opportunities
                value_stocks = []
                for node_id, node in graph.nodes.items():
                    if node['type'] == 'stock':
                        pe = node['data'].get('pe', 999)
                        if 0 < pe < 20:
                            value_stocks.append(f"{node_id} (P/E: {pe:.1f})")

                if value_stocks:
                    st.success(f"**Value Opportunities:** {', '.join(value_stocks[:3])}")

                # Sector recommendations
                if regime_state == 'GOLDILOCKS':
                    st.markdown("**Favored Sectors:** Technology, Financials")
                elif regime_state == 'RISK_OFF':
                    st.markdown("**Favored Sectors:** Utilities, Consumer Staples")
                else:
                    st.markdown("**Favored Sectors:** Balanced allocation recommended")

    with quick_col2:
        if st.button("💎 Find Value", width="stretch"):
            with st.spinner("Scanning for value..."):
                result = workflows.execute_workflow('value_scan')
                workflows.save_workflow_result(result)
                st.success("Value scan complete!")

                # Display value opportunities
                for step in result.get('steps', []):
                    if step['action'] == 'fetch_fundamentals':
                        value_stocks = step['result'].get('value_stocks', [])
                        if value_stocks:
                            st.markdown("### Value Opportunities Found")
                            for stock in value_stocks[:5]:
                                st.markdown(f"- **{stock['symbol']}**: P/E {stock['pe']:.1f}, Price ${stock['price']:.2f}")

    with quick_col3:
        if st.button("🎯 Check Regime", width="stretch"):
            with st.spinner("Analyzing regime..."):
                result = workflows.execute_workflow('regime_check')
                workflows.save_workflow_result(result)

                # Display regime analysis
                for step in result.get('steps', []):
                    if step['action'] == 'summarize_regime':
                        regime_data = step['result']
                        st.markdown("### Economic Regime Analysis")
                        st.info(f"**Current Regime:** {regime_data.get('regime', 'Unknown')}")
                        st.markdown(f"**Description:** {regime_data.get('description', 'No description')}")

    with quick_col4:
        if st.button("⚠️ Risk Check", width="stretch"):
            with st.spinner("Assessing risks..."):
                result = workflows.execute_workflow('risk_assessment')
                workflows.save_workflow_result(result)
                st.success("Risk assessment complete!")
                st.info("Check the JSON output for detailed risk metrics")

    st.markdown("---")

    # Workflow History
    st.markdown("### 📜 Workflow History")

    history = workflows.get_workflow_history()
    if history:
        # Convert to DataFrame for better display
        history_df = pd.DataFrame(history)

        # Show last 10 executions
        st.markdown("**Recent Executions:**")
        for item in history[-10:][::-1]:  # Reverse to show most recent first
            timestamp = datetime.fromisoformat(item['timestamp']).strftime("%Y-%m-%d %H:%M")
            workflow_name = item['workflow']
            steps_count = len(item.get('steps', []))

            col1, col2, col3 = st.columns([2, 3, 1])
            with col1:
                st.text(timestamp)
            with col2:
                st.text(workflows.workflows.get(workflow_name, {}).get('name', workflow_name))
            with col3:
                st.text(f"{steps_count} steps")
    else:
        st.info("No workflow history yet. Run a workflow to start building history.")

    st.markdown("---")

    # Workflow Scheduling
    st.markdown("### ⏰ Workflow Scheduling")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Schedule a Workflow:**")
        workflow_to_schedule = st.selectbox(
            "Select workflow",
            options=list(workflows.workflows.keys()),
            format_func=lambda x: workflows.workflows[x]['name']
        )

        if st.button("📅 Schedule"):
            schedule_result = workflows.schedule_workflow(workflow_to_schedule)
            st.success(f"Scheduled {workflows.workflows[workflow_to_schedule]['name']}")
            st.info(f"Next run: {schedule_result['next_run']}")

    with col2:
        st.markdown("**Active Schedules:**")
        # In production, this would show actual scheduled workflows
        st.markdown("- Morning Briefing: Daily at 9:00 AM")
        st.markdown("- Regime Check: Daily at 4:00 PM")
        st.markdown("- Value Scan: Weekly on Mondays")
        st.markdown("- Sector Rotation: Weekly on Fridays")

    st.markdown("---")

    # Workflow Insights
    st.markdown("### 💡 Workflow Insights")

    insight_col1, insight_col2, insight_col3 = st.columns(3)

    with insight_col1:
        st.metric(
            "Workflows Available",
            len(workflows.workflows),
            "8 investment strategies"
        )

    with insight_col2:
        st.metric(
            "Executions Today",
            len([h for h in history if datetime.fromisoformat(h['timestamp']).date() == datetime.now().date()]),
            "Automated analysis"
        )

    with insight_col3:
        regime = graph.nodes.get('ECONOMIC_REGIME', {})
        regime_state = regime.get('data', {}).get('current_state', 'Unknown')
        st.metric(
            "Current Regime",
            regime_state,
            "Market positioning"
        )