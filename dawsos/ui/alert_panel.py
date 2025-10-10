#!/usr/bin/env python3
"""
Alert Panel - Streamlit UI components for the DawsOS Alert System
Provides user interface for creating, managing, and viewing alerts

Phase 3.1: Comprehensive type hints added
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.typing_compat import TypeAlias

# Plotly imports with error handling
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None
    px = None

# Import alert manager components
import sys
from pathlib import Path
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.alert_manager import AlertManager, AlertType, AlertSeverity, AlertStatus, Alert, AlertEvent

# Type aliases for clarity
ComponentDict: TypeAlias = Dict[str, Any]
SummaryDict: TypeAlias = Dict[str, Any]
EventList: TypeAlias = List[AlertEvent]


class AlertPanel:
    """Alert panel UI components for DawsOS Trinity"""

    def __init__(self, alert_manager: AlertManager, runtime: Optional[Any] = None) -> None:
        """Initialize alert panel.

        Args:
            alert_manager: AlertManager instance for alert operations
            runtime: Optional runtime instance for alert checking
        """
        self.alert_manager: AlertManager = alert_manager
        self.runtime: Optional[Any] = runtime

        # Initialize session state for notifications
        if 'alert_notifications' not in st.session_state:
            st.session_state.alert_notifications = []
        if 'dismissed_notifications' not in st.session_state:
            st.session_state.dismissed_notifications = set()

    def render_alert_panel(self) -> None:
        """Main alert panel UI."""
        st.markdown("### 🔔 Alert & Notification Center")

        # Alert summary at the top
        self._render_alert_summary()

        st.markdown("---")

        # Tab layout for different sections
        tabs = st.tabs(["📊 Dashboard", "➕ Create Alert", "📋 Active Alerts", "📜 History", "🔧 Templates"])

        with tabs[0]:
            self._render_alert_dashboard()

        with tabs[1]:
            self._render_alert_creation_form()

        with tabs[2]:
            self._render_active_alerts()

        with tabs[3]:
            self._render_alert_history()

        with tabs[4]:
            self._render_alert_templates()

        # Check for alerts and show notifications
        self._check_and_show_notifications()

    def _render_alert_summary(self) -> None:
        """Render alert summary metrics."""
        summary = self.alert_manager.get_alert_summary()

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Alerts", summary['total_alerts'])

        with col2:
            st.metric("Active", summary['active_alerts'],
                     delta=f"{summary['active_alerts']} enabled")

        with col3:
            triggered = summary['triggered_alerts']
            st.metric("Triggered", triggered,
                     delta="Needs attention" if triggered > 0 else "All clear",
                     delta_color="inverse")

        with col4:
            unack = summary['unacknowledged_events']
            st.metric("Unacknowledged", unack,
                     delta="Check history" if unack > 0 else None,
                     delta_color="inverse")

        with col5:
            critical_count = summary['severity_counts']['critical']
            st.metric("Critical", critical_count,
                     delta="High priority" if critical_count > 0 else None,
                     delta_color="inverse")

    def _render_severity_distribution(self, severity_data: Dict[str, int]) -> None:
        """Render severity distribution chart or metrics."""
        if sum(severity_data.values()) > 0:
            if PLOTLY_AVAILABLE and go is not None:
                fig = go.Figure(data=[go.Pie(
                    labels=['Info', 'Warning', 'Critical'],
                    values=[severity_data['info'], severity_data['warning'], severity_data['critical']],
                    marker=dict(colors=['#3498db', '#f39c12', '#e74c3c']),
                    hole=0.4
                )])
                fig.update_layout(height=300)
                st.plotly_chart(fig, width="stretch")
            else:
                st.metric("Info", severity_data['info'])
                st.metric("Warning", severity_data['warning'])
                st.metric("Critical", severity_data['critical'])
        else:
            st.info("No alerts configured yet")

    def _render_alert_type_breakdown(self) -> None:
        """Render breakdown of alert types."""
        alert_types = {}
        for alert in self.alert_manager.alerts.values():
            alert_type = alert.alert_type.value
            alert_types[alert_type] = alert_types.get(alert_type, 0) + 1

        if alert_types:
            for alert_type, count in sorted(alert_types.items(), key=lambda x: x[1], reverse=True):
                st.metric(alert_type.replace('_', ' ').title(), count)
        else:
            st.info("No alerts yet")

    def _render_activity_timeline(self, recent_events: EventList) -> None:
        """Render recent alert activity timeline."""
        if recent_events:
            timeline_data = []
            for event in recent_events:
                timeline_data.append({
                    'timestamp': event['timestamp'],
                    'alert': event['alert_name'],
                    'severity': event['severity'],
                    'acknowledged': event['acknowledged']
                })

            df = pd.DataFrame(timeline_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            if PLOTLY_AVAILABLE and px is not None:
                fig = px.scatter(df, x='timestamp', y='alert',
                               color='severity',
                               color_discrete_map={
                                   'info': '#3498db',
                                   'warning': '#f39c12',
                                   'critical': '#e74c3c'
                               },
                               title="Alert Timeline (Last 10 Events)")
                fig.update_traces(marker=dict(size=12))
                st.plotly_chart(fig, width="stretch")
            else:
                st.dataframe(df)
        else:
            st.info("No recent alert activity")

    def _calculate_effectiveness_metrics(self, recent_events: EventList) -> Dict[str, Any]:
        """Calculate alert effectiveness metrics."""
        # Calculate average acknowledgment time
        ack_times = []
        for event in recent_events:
            if event['acknowledged'] and event.get('acknowledged_at'):
                trigger_time = datetime.fromisoformat(event['timestamp'])
                ack_time = datetime.fromisoformat(event['acknowledged_at'])
                ack_times.append((ack_time - trigger_time).total_seconds() / 60)

        avg_ack_time = sum(ack_times) / len(ack_times) if ack_times else 0

        # Find most triggered alert
        trigger_counts = {}
        for event in recent_events:
            alert_name = event['alert_name']
            trigger_counts[alert_name] = trigger_counts.get(alert_name, 0) + 1

        most_triggered = max(trigger_counts, key=trigger_counts.get) if trigger_counts else "N/A"
        if most_triggered != "N/A" and len(most_triggered) > 20:
            most_triggered = most_triggered[:20] + "..."

        # Calculate response rate
        total_events = len(recent_events)
        ack_events = sum(1 for e in recent_events if e['acknowledged'])
        response_rate = (ack_events / total_events * 100) if total_events > 0 else 0

        return {
            'avg_ack_time': avg_ack_time,
            'most_triggered': most_triggered,
            'response_rate': response_rate
        }

    def _render_effectiveness_metrics(self, recent_events: EventList) -> None:
        """Render alert effectiveness metrics."""
        metrics = self._calculate_effectiveness_metrics(recent_events)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Avg Acknowledgment Time", f"{metrics['avg_ack_time']:.1f} min")

        with col2:
            st.metric("Most Triggered", metrics['most_triggered'])

        with col3:
            st.metric("Response Rate", f"{metrics['response_rate']:.1f}%")

    def _render_alert_dashboard(self) -> None:
        """Render alert dashboard with visualizations."""
        st.markdown("#### 📊 Alert Analytics Dashboard")

        summary = self.alert_manager.get_alert_summary()

        # Severity distribution
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("**Alert Distribution by Severity**")
            self._render_severity_distribution(summary['severity_counts'])

        with col2:
            st.markdown("**Alert Type Breakdown**")
            self._render_alert_type_breakdown()

        # Recent activity timeline
        st.markdown("**Recent Alert Activity**")
        self._render_activity_timeline(summary['recent_events'])

        # Alert effectiveness metrics
        st.markdown("**Alert Effectiveness**")
        self._render_effectiveness_metrics(summary['recent_events'])

    def _render_alert_creation_form(self) -> None:
        """Render alert creation form."""
        st.markdown("#### ➕ Create New Alert")

        with st.form("create_alert_form"):
            col1, col2 = st.columns(2)

            with col1:
                alert_name = st.text_input("Alert Name*", placeholder="e.g., AAPL Price Alert")

                alert_type = st.selectbox(
                    "Alert Type*",
                    options=[t.value for t in AlertType],
                    format_func=lambda x: x.replace('_', ' ').title()
                )

                severity = st.selectbox(
                    "Severity*",
                    options=[s.value for s in AlertSeverity],
                    format_func=lambda x: x.upper()
                )

            with col2:
                # Condition configuration
                st.markdown("**Condition**")

                field = st.text_input("Field Path*", placeholder="e.g., AAPL.price or system.success_rate")

                operator = st.selectbox(
                    "Operator*",
                    options=['>', '<', '>=', '<=', '==', '!=', 'contains', 'missing'],
                    format_func=lambda x: {
                        '>': 'Greater than (>)',
                        '<': 'Less than (<)',
                        '>=': 'Greater than or equal (>=)',
                        '<=': 'Less than or equal (<=)',
                        '==': 'Equals (==)',
                        '!=': 'Not equal (!=)',
                        'contains': 'Contains',
                        'missing': 'Is missing'
                    }.get(x, x)
                )

                if operator != 'missing':
                    value = st.text_input("Value*", placeholder="e.g., 150 or 0.8")
                else:
                    value = None

            # Additional metadata
            st.markdown("**Additional Settings**")
            col3, col4 = st.columns(2)

            with col3:
                enabled = st.checkbox("Enabled", value=True)

            with col4:
                description = st.text_area("Description (optional)", placeholder="Alert description...")

            submit = st.form_submit_button("Create Alert", type="primary")

            if submit:
                if not alert_name or not field:
                    st.error("Please fill in all required fields (marked with *)")
                elif operator != 'missing' and not value:
                    st.error("Please provide a value for the condition")
                else:
                    try:
                        # Parse value to appropriate type
                        parsed_value = value
                        if operator != 'missing' and operator not in ['contains', '==', '!=']:
                            try:
                                parsed_value = float(value)
                            except ValueError:
                                parsed_value = value

                        metadata = {'description': description} if description else {}

                        alert = self.alert_manager.create_alert(
                            name=alert_name,
                            alert_type=alert_type,
                            condition={
                                'field': field,
                                'operator': operator,
                                'value': parsed_value
                            },
                            severity=severity,
                            metadata=metadata
                        )

                        if not enabled:
                            self.alert_manager.update_alert(alert.alert_id, enabled=False)

                        st.success(f"✅ Alert '{alert_name}' created successfully!")
                        st.balloons()

                    except Exception as e:
                        st.error(f"Error creating alert: {str(e)}")

    def _render_active_alerts(self) -> None:
        """Render active alerts list."""
        st.markdown("#### 📋 Active Alerts")

        active_alerts = self.alert_manager.get_active_alerts()
        all_alerts = list(self.alert_manager.alerts.values())

        # Filter options
        col1, col2, col3 = st.columns(3)

        with col1:
            show_filter = st.selectbox("Show", ["All Alerts", "Active Only", "Triggered Only", "Disabled"])

        with col2:
            severity_filter = st.selectbox("Severity", ["All", "Critical", "Warning", "Info"])

        with col3:
            type_filter = st.selectbox("Type", ["All"] + [t.value.replace('_', ' ').title() for t in AlertType])

        # Apply filters
        filtered_alerts = all_alerts

        if show_filter == "Active Only":
            filtered_alerts = [a for a in filtered_alerts if a.enabled and a.status == AlertStatus.ACTIVE]
        elif show_filter == "Triggered Only":
            filtered_alerts = [a for a in filtered_alerts if a.status == AlertStatus.TRIGGERED]
        elif show_filter == "Disabled":
            filtered_alerts = [a for a in filtered_alerts if not a.enabled]

        if severity_filter != "All":
            filtered_alerts = [a for a in filtered_alerts if a.severity.value == severity_filter.lower()]

        if type_filter != "All":
            filtered_alerts = [a for a in filtered_alerts if a.alert_type.value.replace('_', ' ').title() == type_filter]

        # Display alerts
        if filtered_alerts:
            for alert in filtered_alerts:
                self._render_alert_card(alert)
        else:
            st.info("No alerts match the current filters")

    def _render_alert_card(self, alert: Alert) -> None:
        """Render individual alert card.

        Args:
            alert: Alert instance to render
        """
        # Status indicator
        status_colors = {
            'active': '🟢',
            'triggered': '🔴',
            'acknowledged': '🟡',
            'resolved': '✅'
        }

        severity_colors = {
            'info': 'blue',
            'warning': 'orange',
            'critical': 'red'
        }

        with st.expander(
            f"{status_colors.get(alert.status.value, '⚪')} {alert.name} "
            f"[{alert.severity.value.upper()}]",
            expanded=(alert.status == AlertStatus.TRIGGERED)
        ):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Type:** {alert.alert_type.value.replace('_', ' ').title()}")
                st.markdown(f"**Condition:** `{alert.condition.field} {alert.condition.operator} {alert.condition.value}`")

                if alert.metadata.get('description'):
                    st.markdown(f"**Description:** {alert.metadata['description']}")

                st.markdown(f"**Status:** {alert.status.value.title()}")

                if alert.last_triggered:
                    trigger_time = datetime.fromisoformat(alert.last_triggered)
                    st.markdown(f"**Last Triggered:** {trigger_time.strftime('%Y-%m-%d %H:%M:%S')}")

                st.markdown(f"**Trigger Count:** {alert.trigger_count}")

            with col2:
                # Action buttons
                if alert.enabled:
                    if st.button("Disable", key=f"disable_{alert.alert_id}"):
                        self.alert_manager.update_alert(alert.alert_id, enabled=False)
                        st.success("Alert disabled")
                        st.rerun()
                else:
                    if st.button("Enable", key=f"enable_{alert.alert_id}"):
                        self.alert_manager.update_alert(alert.alert_id, enabled=True)
                        st.success("Alert enabled")
                        st.rerun()

                if alert.status == AlertStatus.TRIGGERED:
                    if st.button("Resolve", key=f"resolve_{alert.alert_id}"):
                        self.alert_manager.resolve_alert(alert.alert_id)
                        st.success("Alert resolved")
                        st.rerun()

                if st.button("Delete", key=f"delete_{alert.alert_id}"):
                    if st.button("Confirm Delete", key=f"confirm_delete_{alert.alert_id}"):
                        self.alert_manager.delete_alert(alert.alert_id)
                        st.success("Alert deleted")
                        st.rerun()

    def _render_alert_history(self) -> None:
        """Render alert history."""
        st.markdown("#### 📜 Alert History")

        # History filters
        col1, col2, col3 = st.columns(3)

        with col1:
            limit = st.slider("Show last N events", 10, 100, 50)

        with col2:
            severity_filter = st.selectbox("Filter by severity", ["All", "Critical", "Warning", "Info"], key="history_severity")

        with col3:
            ack_filter = st.selectbox("Filter by status", ["All", "Acknowledged", "Unacknowledged"])

        # Get history
        severity_val = severity_filter.lower() if severity_filter != "All" else None
        history = self.alert_manager.get_alert_history(limit=limit, severity=severity_val)

        # Apply acknowledgment filter
        if ack_filter == "Acknowledged":
            history = [e for e in history if e.acknowledged]
        elif ack_filter == "Unacknowledged":
            history = [e for e in history if not e.acknowledged]

        # Display history
        if history:
            for event in history:
                self._render_event_card(event)
        else:
            st.info("No alert events in history")

    def _render_event_card(self, event: AlertEvent) -> None:
        """Render individual event card.

        Args:
            event: AlertEvent instance to render
        """
        severity_colors = {
            'info': '🔵',
            'warning': '🟠',
            'critical': '🔴'
        }

        ack_status = "✅ Acknowledged" if event.acknowledged else "⏳ Pending"

        with st.expander(
            f"{severity_colors.get(event.severity.value, '⚪')} {event.alert_name} - "
            f"{datetime.fromisoformat(event.timestamp).strftime('%Y-%m-%d %H:%M:%S')} [{ack_status}]"
        ):
            st.markdown(f"**Message:** {event.message}")

            if event.details:
                st.markdown("**Details:**")
                st.json(event.details)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Severity:** {event.severity.value.upper()}")
                st.markdown(f"**Triggered:** {datetime.fromisoformat(event.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")

            with col2:
                if event.acknowledged:
                    ack_time = datetime.fromisoformat(event.acknowledged_at)
                    st.markdown(f"**Acknowledged:** {ack_time.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    if st.button("Acknowledge", key=f"ack_{event.event_id}"):
                        self.alert_manager.acknowledge_alert(event.event_id)
                        st.success("Event acknowledged")
                        st.rerun()

    def _render_stock_price_template(self) -> None:
        """Render stock price alert template form."""
        with st.form("stock_price_template"):
            st.markdown("**Stock Price Alert**")
            symbol = st.text_input("Symbol", value="AAPL", key="template_symbol")
            direction = st.radio("Alert when price is", ["Above", "Below"], key="template_direction")
            threshold = st.number_input("Threshold ($)", value=150.0, key="template_threshold")

            if st.form_submit_button("Create Stock Price Alert"):
                template_name = 'stock_price_above' if direction == "Above" else 'stock_price_below'
                try:
                    alert = self.alert_manager.create_template_alert(
                        template_name,
                        symbol=symbol,
                        threshold=threshold
                    )
                    st.success(f"✅ Created alert: {alert.name}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    def _render_system_health_template(self) -> None:
        """Render system health alert template form."""
        with st.form("system_health_template"):
            st.markdown("**Response Time Alert**")
            response_threshold = st.number_input("Max Response Time (seconds)", value=5.0, key="response_threshold")

            if st.form_submit_button("Create Response Time Alert"):
                try:
                    alert = self.alert_manager.create_template_alert(
                        'response_time',
                        threshold=response_threshold
                    )
                    st.success(f"✅ Created alert: {alert.name}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    def _render_data_freshness_template(self) -> None:
        """Render data freshness alert template form."""
        with st.form("data_freshness_template"):
            st.markdown("**Data Freshness Alert**")
            dataset = st.selectbox("Dataset", ["FRED", "Market Sectors", "Economic Cycles"], key="dataset_select")
            max_age = st.number_input("Max Age (hours)", value=24, key="max_age")

            if st.form_submit_button("Create Data Freshness Alert"):
                try:
                    alert = self.alert_manager.create_template_alert(
                        'data_freshness',
                        dataset=dataset,
                        max_age_hours=max_age
                    )
                    st.success(f"✅ Created alert: {alert.name}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    def _render_compliance_template(self) -> None:
        """Render compliance alert template form."""
        with st.form("compliance_template"):
            st.markdown("**Trinity Compliance Alert**")
            bypass_threshold = st.number_input("Max Bypass Warnings", value=0, key="bypass_threshold")

            if st.form_submit_button("Create Compliance Alert"):
                try:
                    alert = self.alert_manager.create_template_alert(
                        'compliance_violation',
                        threshold=bypass_threshold
                    )
                    st.success(f"✅ Created alert: {alert.name}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    def _render_quick_templates(self) -> None:
        """Render one-click quick template buttons."""
        st.markdown("**⚡ Quick Templates (One-Click)**")

        quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)

        with quick_col1:
            if st.button("Pattern Failure Alert"):
                try:
                    alert = self.alert_manager.create_template_alert('pattern_failure', threshold=0.8)
                    st.success(f"✅ Created: {alert.name}")
                except Exception as e:
                    st.error(str(e))

        with quick_col2:
            if st.button("Graph Anomaly Alert"):
                try:
                    alert = self.alert_manager.create_template_alert('graph_anomaly', threshold=100)
                    st.success(f"✅ Created: {alert.name}")
                except Exception as e:
                    st.error(str(e))

        with quick_col3:
            if st.button("FRED Data Alert"):
                try:
                    alert = self.alert_manager.create_template_alert('data_freshness', dataset='FRED', max_age_hours=24)
                    st.success(f"✅ Created: {alert.name}")
                except Exception as e:
                    st.error(str(e))

        with quick_col4:
            if st.button("Compliance Monitor"):
                try:
                    alert = self.alert_manager.create_template_alert('compliance_violation', threshold=0)
                    st.success(f"✅ Created: {alert.name}")
                except Exception as e:
                    st.error(str(e))

    def _render_alert_templates(self) -> None:
        """Render alert templates for quick creation."""
        st.markdown("#### 🔧 Alert Templates")
        st.markdown("Quickly create alerts from common templates")

        # Template categories
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📈 Stock & Market Alerts**")
            self._render_stock_price_template()

        with col2:
            st.markdown("**🔧 System Health Alerts**")
            self._render_system_health_template()

        st.markdown("---")

        col3, col4 = st.columns(2)

        with col3:
            st.markdown("**📊 Data Quality Alerts**")
            self._render_data_freshness_template()

        with col4:
            st.markdown("**🛡️ Compliance Alerts**")
            self._render_compliance_template()

        # One-click common templates
        st.markdown("---")
        self._render_quick_templates()

    def _check_and_show_notifications(self) -> None:
        """Check alerts and show real-time notifications."""
        if self.runtime:
            # Check all alerts
            triggered_events = self.alert_manager.check_alerts(self.runtime)

            # Show notifications for new triggers
            for event in triggered_events:
                if event.event_id not in st.session_state.dismissed_notifications:
                    # Add to notification queue
                    st.session_state.alert_notifications.append(event)

        # Display notifications
        self._render_notifications()

    def _render_notifications(self) -> None:
        """Render real-time toast notifications."""
        if st.session_state.alert_notifications:
            for event in st.session_state.alert_notifications[:3]:  # Show max 3 at a time
                if event.event_id not in st.session_state.dismissed_notifications:
                    # Show toast notification
                    if event.severity == AlertSeverity.CRITICAL:
                        st.toast(f"🔴 CRITICAL: {event.message}", icon="🚨")
                    elif event.severity == AlertSeverity.WARNING:
                        st.toast(f"🟠 WARNING: {event.message}", icon="⚠️")
                    else:
                        st.toast(f"🔵 INFO: {event.message}", icon="ℹ️")

                    # Mark as shown
                    st.session_state.dismissed_notifications.add(event.event_id)

            # Clean up old notifications
            st.session_state.alert_notifications = [
                e for e in st.session_state.alert_notifications
                if e.event_id not in st.session_state.dismissed_notifications
            ]

    def render_alert_notifications(self) -> None:
        """Render alert notifications sidebar widget."""
        with st.sidebar:
            st.markdown("### 🔔 Notifications")

            # Get unacknowledged events
            unack_events = [e for e in self.alert_manager.history if not e.acknowledged][-5:]

            if unack_events:
                for event in unack_events:
                    severity_icon = {
                        'critical': '🔴',
                        'warning': '🟠',
                        'info': '🔵'
                    }.get(event.severity.value, '⚪')

                    with st.expander(f"{severity_icon} {event.alert_name[:25]}..."):
                        st.caption(datetime.fromisoformat(event.timestamp).strftime('%H:%M:%S'))
                        st.markdown(f"_{event.message}_")

                        if st.button("Acknowledge", key=f"sidebar_ack_{event.event_id}"):
                            self.alert_manager.acknowledge_alert(event.event_id)
                            st.rerun()
            else:
                st.success("All clear! No pending alerts.")


def get_alert_panel(alert_manager: AlertManager, runtime: Optional[Any] = None) -> AlertPanel:
    """Factory function to create alert panel.

    Args:
        alert_manager: AlertManager instance
        runtime: Optional runtime instance

    Returns:
        AlertPanel instance
    """
    return AlertPanel(alert_manager, runtime)
