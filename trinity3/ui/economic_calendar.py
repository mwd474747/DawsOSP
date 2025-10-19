"""Economic Calendar and Events Module for DawsOS 3.0"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class EconomicCalendar:
    """Display economic events and Fed meetings calendar"""
    
    # Event importance colors
    IMPORTANCE_COLORS = {
        'critical': '#EF4444',  # Red
        'high': '#F59E0B',      # Orange
        'medium': '#10B981',    # Green
        'low': '#6B7280'        # Gray
    }
    
    @classmethod
    def get_upcoming_events(cls, days_ahead: int = 30) -> List[Dict]:
        """Get upcoming economic events"""
        
        # Sample events data (in production, this would come from an API)
        events = [
            {
                'date': datetime.now() + timedelta(days=2),
                'event': 'FOMC Meeting Minutes',
                'importance': 'critical',
                'type': 'policy',
                'description': 'Federal Open Market Committee meeting minutes release',
                'expected_impact': 'High volatility expected in bond and equity markets',
                'time': '14:00 ET'
            },
            {
                'date': datetime.now() + timedelta(days=5),
                'event': 'Non-Farm Payrolls',
                'importance': 'high',
                'type': 'data_release',
                'description': 'Monthly employment report',
                'expected_impact': 'Key indicator for Fed policy decisions',
                'time': '08:30 ET',
                'forecast': '+180K',
                'previous': '+223K'
            },
            {
                'date': datetime.now() + timedelta(days=7),
                'event': 'CPI Data Release',
                'importance': 'critical',
                'type': 'data_release',
                'description': 'Consumer Price Index - inflation indicator',
                'expected_impact': 'Direct impact on rate expectations',
                'time': '08:30 ET',
                'forecast': '3.2% YoY',
                'previous': '3.7% YoY'
            },
            {
                'date': datetime.now() + timedelta(days=10),
                'event': 'Retail Sales',
                'importance': 'medium',
                'type': 'data_release',
                'description': 'Monthly retail sales data',
                'expected_impact': 'Consumer spending indicator',
                'time': '08:30 ET',
                'forecast': '+0.3% MoM',
                'previous': '+0.7% MoM'
            },
            {
                'date': datetime.now() + timedelta(days=14),
                'event': 'Fed Chair Speech',
                'importance': 'high',
                'type': 'policy',
                'description': 'Jerome Powell speaks at Jackson Hole',
                'expected_impact': 'Policy hints and forward guidance expected',
                'time': '10:00 ET'
            },
            {
                'date': datetime.now() + timedelta(days=21),
                'event': 'FOMC Rate Decision',
                'importance': 'critical',
                'type': 'policy',
                'description': 'Federal funds rate decision',
                'expected_impact': 'Market-moving event with press conference',
                'time': '14:00 ET',
                'forecast': 'Hold at 5.33%',
                'current': '5.33%'
            },
            {
                'date': datetime.now() + timedelta(days=25),
                'event': 'GDP Q4 Preliminary',
                'importance': 'high',
                'type': 'data_release',
                'description': 'Quarterly GDP growth rate',
                'expected_impact': 'Economic growth assessment',
                'time': '08:30 ET',
                'forecast': '2.1% QoQ',
                'previous': '2.8% QoQ'
            }
        ]
        
        # Filter by days ahead
        end_date = datetime.now() + timedelta(days=days_ahead)
        filtered_events = [e for e in events if e['date'] <= end_date]
        
        # Sort by date
        filtered_events.sort(key=lambda x: x['date'])
        
        return filtered_events
    
    @classmethod
    def render_calendar(cls):
        """Render the economic calendar interface"""
        
        st.markdown("### Economic Calendar")
        st.markdown("*Track market-moving events and data releases*")
        
        # Filter controls
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            days_ahead = st.selectbox(
                "Time Window",
                options=[7, 14, 30, 60],
                format_func=lambda x: f"Next {x} days",
                index=2,
                key="eco_cal_days"
            )
        
        with col2:
            importance_filter = st.multiselect(
                "Importance Level",
                options=['critical', 'high', 'medium', 'low'],
                default=['critical', 'high'],
                format_func=lambda x: x.title(),
                key="eco_cal_importance"
            )
        
        with col3:
            event_type = st.multiselect(
                "Event Type",
                options=['policy', 'data_release'],
                default=['policy', 'data_release'],
                format_func=lambda x: x.replace('_', ' ').title(),
                key="eco_cal_type"
            )
        
        # Get and filter events
        events = cls.get_upcoming_events(days_ahead)
        
        if importance_filter:
            events = [e for e in events if e['importance'] in importance_filter]
        
        if event_type:
            events = [e for e in events if e['type'] in event_type]
        
        # Display events
        if not events:
            st.info(f"No events matching your filters in the next {days_ahead} days")
            return
        
        st.markdown(f"**{len(events)} upcoming events**")
        st.markdown("---")
        
        # Group events by week
        current_week = None
        
        for event in events:
            event_date = event['date']
            week_start = event_date - timedelta(days=event_date.weekday())
            
            # Week header
            if current_week != week_start:
                current_week = week_start
                week_end = week_start + timedelta(days=6)
                st.markdown(f"#### Week of {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
            
            # Event card
            with st.container():
                col_date, col_event = st.columns([1, 4])
                
                with col_date:
                    st.markdown(f"**{event_date.strftime('%b %d')}**")
                    st.markdown(f"*{event_date.strftime('%A')}*")
                    if 'time' in event:
                        st.caption(event['time'])
                
                with col_event:
                    # Event header with importance badge
                    importance_color = cls.IMPORTANCE_COLORS[event['importance']]
                    
                    st.markdown(
                        f"**{event['event']}** "
                        f"<span style='color: {importance_color}; font-size: 0.8em;'>"
                        f"[{event['importance'].upper()}]</span>",
                        unsafe_allow_html=True
                    )
                    
                    st.caption(event['description'])
                    
                    # Show forecast vs previous if available
                    if 'forecast' in event and 'previous' in event:
                        col_fore, col_prev = st.columns(2)
                        with col_fore:
                            st.metric("Forecast", event['forecast'], label_visibility="visible")
                        with col_prev:
                            st.metric("Previous", event['previous'], label_visibility="visible")
                    elif 'forecast' in event and 'current' in event:
                        col_fore, col_curr = st.columns(2)
                        with col_fore:
                            st.metric("Expected", event['forecast'], label_visibility="visible")
                        with col_curr:
                            st.metric("Current", event['current'], label_visibility="visible")
                    
                    # Expected impact
                    if 'expected_impact' in event:
                        st.info(f"{event['expected_impact']}")
                
                st.markdown("---")
    
    @classmethod
    def render_fed_schedule(cls):
        """Render upcoming Fed meeting schedule"""
        
        st.markdown("### Federal Reserve Schedule")
        
        # FOMC meeting dates for 2024-2025
        meetings = [
            {
                'date': datetime(2024, 12, 18),
                'type': 'FOMC Meeting',
                'has_sep': True,  # Summary of Economic Projections
                'press_conf': True
            },
            {
                'date': datetime(2025, 1, 29),
                'type': 'FOMC Meeting',
                'has_sep': False,
                'press_conf': True
            },
            {
                'date': datetime(2025, 3, 19),
                'type': 'FOMC Meeting',
                'has_sep': True,
                'press_conf': True
            },
            {
                'date': datetime(2025, 5, 7),
                'type': 'FOMC Meeting',
                'has_sep': False,
                'press_conf': True
            },
            {
                'date': datetime(2025, 6, 18),
                'type': 'FOMC Meeting',
                'has_sep': True,
                'press_conf': True
            },
            {
                'date': datetime(2025, 7, 30),
                'type': 'FOMC Meeting',
                'has_sep': False,
                'press_conf': True
            }
        ]
        
        # Filter future meetings
        future_meetings = [m for m in meetings if m['date'] > datetime.now()][:4]
        
        if not future_meetings:
            st.info("No upcoming Fed meetings scheduled")
            return
        
        # Display in a grid
        cols = st.columns(2)
        
        for idx, meeting in enumerate(future_meetings):
            with cols[idx % 2]:
                days_until = (meeting['date'] - datetime.now()).days
                
                # Card-like display
                with st.container():
                    st.markdown(f"**{meeting['date'].strftime('%B %d, %Y')}**")
                    st.caption(f"In {days_until} days")
                    
                    # Meeting details
                    if meeting['has_sep']:
                        st.success("Includes Economic Projections (SEP)")
                    
                    if meeting['press_conf']:
                        st.info("Press Conference Scheduled")
                    
                    # Expected outcomes
                    if days_until < 30:
                        st.warning("Market volatility expected")
                    
                    st.markdown("---")