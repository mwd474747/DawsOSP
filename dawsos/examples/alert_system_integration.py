#!/usr/bin/env python3
"""
Alert System Integration Example
Demonstrates how to integrate the Alert Manager into DawsOS Trinity
"""

import streamlit as st
from core.alert_manager import AlertManager
from ui.alert_panel import AlertPanel
from core.agent_runtime import AgentRuntime


def integrate_alerts_into_dashboard():
    """
    Example: Integrate alerts into the main Trinity dashboard

    Add this to your main.py or trinity_ui_components.py
    """

    # Initialize Alert Manager (do this once at startup)
    if 'alert_manager' not in st.session_state:
        st.session_state.alert_manager = AlertManager(storage_dir='storage/alerts')

    alert_manager = st.session_state.alert_manager

    # Initialize Alert Panel
    runtime = st.session_state.get('runtime')  # Your AgentRuntime instance
    alert_panel = AlertPanel(alert_manager, runtime)

    # Option 1: Add as a new tab in your dashboard
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Markets", "Alerts", "Settings"])

    with tab3:
        alert_panel.render_alert_panel()

    # Option 2: Add notification widget to sidebar
    with st.sidebar:
        alert_panel.render_alert_notifications()


def setup_automatic_alert_checking():
    """
    Example: Set up automatic alert checking on dashboard refresh

    Add this to your main rendering function
    """

    alert_manager = st.session_state.get('alert_manager')
    runtime = st.session_state.get('runtime')

    if alert_manager and runtime:
        # Check alerts on every dashboard refresh
        triggered_events = alert_manager.check_alerts(runtime)

        # Display notifications for new triggers
        for event in triggered_events:
            if event.severity.value == 'critical':
                st.error(f"🚨 CRITICAL ALERT: {event.message}")
            elif event.severity.value == 'warning':
                st.warning(f"⚠️ WARNING: {event.message}")
            else:
                st.info(f"ℹ️ INFO: {event.message}")


def create_default_alerts(alert_manager: AlertManager):
    """
    Example: Create default alerts for a new system
    """

    # 1. System Health Alert - Pattern execution success rate
    alert_manager.create_template_alert(
        'pattern_failure',
        threshold=0.8  # Alert if success rate drops below 80%
    )

    # 2. Data Freshness Alert - FRED economic data
    alert_manager.create_template_alert(
        'data_freshness',
        dataset='FRED',
        max_age_hours=24  # Alert if data is older than 24 hours
    )

    # 3. Trinity Compliance Alert - Bypass warnings
    alert_manager.create_template_alert(
        'compliance_violation',
        threshold=0  # Alert on any bypass warning
    )

    # 4. Response Time Alert - System performance
    alert_manager.create_template_alert(
        'response_time',
        threshold=5.0  # Alert if response time > 5 seconds
    )

    # 5. Knowledge Graph Anomaly
    alert_manager.create_template_alert(
        'graph_anomaly',
        threshold=100  # Alert if more than 100 nodes added in short time
    )

    print("✅ Created 5 default system alerts")


def create_custom_stock_alerts(alert_manager: AlertManager):
    """
    Example: Create custom stock price alerts
    """

    # Alert when Apple stock goes above $200
    alert_manager.create_template_alert(
        'stock_price_above',
        symbol='AAPL',
        threshold=200.0
    )

    # Alert when Tesla stock drops below $150
    alert_manager.create_template_alert(
        'stock_price_below',
        symbol='TSLA',
        threshold=150.0
    )

    # Custom alert using create_alert for more control
    alert_manager.create_alert(
        name="NVDA Significant Move",
        alert_type="pattern",
        condition={
            'field': 'NVDA.change_percent',
            'operator': '>',
            'value': 5.0  # Alert if NVDA moves more than 5% in a day
        },
        severity="warning",
        metadata={
            'description': "Alert when NVIDIA has a significant daily move",
            'symbol': 'NVDA'
        }
    )

    print("✅ Created stock price alerts for AAPL, TSLA, and NVDA")


def setup_alert_callbacks(alert_manager: AlertManager):
    """
    Example: Register callbacks for alert types
    """

    def on_critical_alert(event):
        """Called when any critical alert is triggered"""
        print(f"🚨 CRITICAL ALERT TRIGGERED: {event.alert_name}")
        print(f"   Message: {event.message}")
        print(f"   Time: {event.timestamp}")

        # Could send email, SMS, or other notification here
        # send_email(to="admin@example.com", subject=event.alert_name, body=event.message)

    def on_compliance_alert(event):
        """Called when Trinity compliance alert is triggered"""
        print(f"⚠️ COMPLIANCE VIOLATION: {event.message}")

        # Log to compliance monitoring system
        # compliance_logger.log(event.to_dict())

    def on_data_quality_alert(event):
        """Called when data quality alert is triggered"""
        print(f"📊 DATA QUALITY ISSUE: {event.message}")

        # Trigger data refresh
        # data_harvester.refresh_stale_data(event.details)

    # Register callbacks
    alert_manager.register_callback('trinity_compliance', on_compliance_alert)
    alert_manager.register_callback('data_quality', on_data_quality_alert)

    # Register callback for all critical alerts
    for alert in alert_manager.alerts.values():
        if alert.severity.value == 'critical':
            alert_manager.register_callback(alert.alert_type.value, on_critical_alert)


def periodic_alert_check(alert_manager: AlertManager, runtime: AgentRuntime):
    """
    Example: Run periodic alert checks (e.g., every minute)

    Could be called from a background thread or scheduled task
    """

    import time
    from datetime import datetime

    while True:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking alerts...")

        # Check all alerts
        triggered_events = alert_manager.check_alerts(runtime)

        if triggered_events:
            print(f"  ⚠️ {len(triggered_events)} alert(s) triggered")
            for event in triggered_events:
                print(f"     - {event.alert_name}: {event.message}")
        else:
            print("  ✅ All alerts normal")

        # Wait 60 seconds before next check
        time.sleep(60)


def display_alert_summary_widget(alert_manager: AlertManager):
    """
    Example: Add a compact alert summary widget to any page
    """

    summary = alert_manager.get_alert_summary()

    st.markdown("### 🔔 Alert Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        triggered = summary['triggered_alerts']
        if triggered > 0:
            st.error(f"🔴 {triggered} Triggered")
        else:
            st.success("✅ All Clear")

    with col2:
        unack = summary['unacknowledged_events']
        if unack > 0:
            st.warning(f"⏳ {unack} Pending")
        else:
            st.info("📭 No Pending")

    with col3:
        critical = summary['severity_counts']['critical']
        if critical > 0:
            st.error(f"🚨 {critical} Critical")
        else:
            st.success("✅ No Critical")


# Complete integration example
def main():
    """
    Complete example showing full integration
    """

    st.set_page_config(page_title="DawsOS Trinity with Alerts", layout="wide")

    # Initialize system
    if 'alert_manager' not in st.session_state:
        st.session_state.alert_manager = AlertManager()

        # Create default alerts on first run
        if len(st.session_state.alert_manager.alerts) == 0:
            create_default_alerts(st.session_state.alert_manager)
            create_custom_stock_alerts(st.session_state.alert_manager)
            setup_alert_callbacks(st.session_state.alert_manager)

    if 'runtime' not in st.session_state:
        st.session_state.runtime = AgentRuntime()
        # ... initialize runtime with agents ...

    alert_manager = st.session_state.alert_manager
    runtime = st.session_state.runtime

    # Create Alert Panel
    alert_panel = AlertPanel(alert_manager, runtime)

    # Main UI
    st.title("🤖 DawsOS Trinity - Alert-Enhanced Dashboard")

    # Sidebar with notifications
    with st.sidebar:
        st.markdown("## Navigation")
        page = st.radio("Go to", ["Dashboard", "Alerts", "Markets", "Analysis"])

        st.markdown("---")

        # Alert notifications in sidebar
        alert_panel.render_alert_notifications()

    # Main content area
    if page == "Dashboard":
        st.markdown("## 📊 Dashboard")

        # Alert summary widget
        display_alert_summary_widget(alert_manager)

        st.markdown("---")

        # Your dashboard content here
        st.info("Dashboard content goes here...")

    elif page == "Alerts":
        # Full alert panel
        alert_panel.render_alert_panel()

    elif page == "Markets":
        st.markdown("## 📈 Markets")
        # Your markets content here

    elif page == "Analysis":
        st.markdown("## 🔍 Analysis")
        # Your analysis content here

    # Check alerts on every page refresh
    setup_automatic_alert_checking()


if __name__ == "__main__":
    main()
