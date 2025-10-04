#!/usr/bin/env python3
"""
Pattern Browser UI Component - Comprehensive Pattern Discovery and Execution Interface
Provides a rich UI for browsing, searching, filtering, and executing all 45 patterns in the DawsOS system
"""

import streamlit as st
from typing import Dict, Any, List
from datetime import datetime


class PatternBrowser:
    """Comprehensive pattern browser UI component for DawsOS Trinity system"""

    # Category icons and colors
    CATEGORY_CONFIG = {
        'queries': {'icon': '🔍', 'color': '#3498db', 'description': 'Data queries and lookups'},
        'analysis': {'icon': '📊', 'color': '#2ecc71', 'description': 'Analytical patterns'},
        'financial': {'icon': '💰', 'color': '#f39c12', 'description': 'Financial analysis'},
        'sector': {'icon': '🏢', 'color': '#9b59b6', 'description': 'Sector analysis'},
        'cycles': {'icon': '🔄', 'color': '#e74c3c', 'description': 'Economic cycles'},
        'workflows': {'icon': '⚡', 'color': '#1abc9c', 'description': 'Multi-step workflows'},
        'governance': {'icon': '🛡️', 'color': '#34495e', 'description': 'Data governance'},
        'templates': {'icon': '📋', 'color': '#95a5a6', 'description': 'Template patterns'},
        'actions': {'icon': '🎯', 'color': '#e67e22', 'description': 'Action patterns'},
        'ui': {'icon': '🎨', 'color': '#16a085', 'description': 'UI generation'},
        'system': {'icon': '⚙️', 'color': '#7f8c8d', 'description': 'System patterns'},
        'other': {'icon': '📦', 'color': '#95a5a6', 'description': 'Other patterns'}
    }

    def __init__(self, runtime):
        """
        Initialize Pattern Browser

        Args:
            runtime: AgentRuntime instance with pattern_engine
        """
        self.runtime = runtime
        self.pattern_engine = runtime.pattern_engine if hasattr(runtime, 'pattern_engine') else None

    def render_pattern_browser(self) -> None:
        """Main entry point for pattern browser tab"""
        st.markdown("### 🔮 Pattern Browser - Discover and Execute Patterns")
        st.markdown("*Browse all 45 patterns in the DawsOS Trinity system*")

        if not self.pattern_engine:
            st.error("Pattern Engine not available")
            return

        # Get all patterns
        all_patterns = self._get_all_patterns()

        # Top-level metrics
        self._render_pattern_metrics(all_patterns)

        st.markdown("---")

        # Search and filter controls
        search_term, category_filter, priority_filter = self._render_search_controls()

        # Filter patterns
        filtered_patterns = self._filter_patterns(all_patterns, search_term, category_filter, priority_filter)

        st.markdown(f"**Showing {len(filtered_patterns)} of {len(all_patterns)} patterns**")

        # Display mode toggle
        display_mode = st.radio(
            "Display Mode:",
            ["Grid View", "List View", "Category Groups"],
            horizontal=True,
            key="pattern_display_mode"
        )

        st.markdown("---")

        # Render patterns based on display mode
        if display_mode == "Grid View":
            self._render_grid_view(filtered_patterns)
        elif display_mode == "List View":
            self._render_list_view(filtered_patterns)
        else:
            self._render_category_view(filtered_patterns)

    def _get_all_patterns(self) -> List[Dict[str, Any]]:
        """Get all patterns from pattern engine"""
        patterns = []

        for pattern_id, pattern in self.pattern_engine.patterns.items():
            if pattern_id == 'schema':
                continue

            # Extract pattern metadata
            pattern_info = {
                'id': pattern_id,
                'name': pattern.get('name', pattern_id.replace('_', ' ').title()),
                'description': pattern.get('description', 'No description available'),
                'category': self._determine_category(pattern_id, pattern),
                'triggers': pattern.get('triggers', pattern.get('trigger_phrases', [])),
                'priority': pattern.get('priority', 5),
                'steps': pattern.get('steps', pattern.get('workflow', [])),
                'last_updated': pattern.get('last_updated', 'Unknown'),
                'version': pattern.get('version', '1.0'),
                'response_type': pattern.get('response_type', 'generic'),
                'entities': pattern.get('entities', []),
                'raw_pattern': pattern
            }

            patterns.append(pattern_info)

        # Sort by priority (descending) then name
        patterns.sort(key=lambda p: (-p['priority'], p['name']))

        return patterns

    def _determine_category(self, pattern_id: str, pattern: Dict) -> str:
        """Determine pattern category from ID and metadata"""
        # Check explicit category
        if 'category' in pattern:
            return pattern['category'].lower()

        # Infer from ID
        if '/' in pattern_id or pattern_id.startswith('queries'):
            parts = pattern_id.split('/')
            if len(parts) > 1:
                return parts[0].lower()

        # Infer from pattern ID keywords
        id_lower = pattern_id.lower()
        if any(keyword in id_lower for keyword in ['query', 'stock', 'market', 'macro', 'company', 'sector', 'correlation']):
            return 'queries'
        elif any(keyword in id_lower for keyword in ['analysis', 'analyze', 'buffett', 'moat', 'dcf', 'earnings', 'technical', 'risk']):
            return 'analysis'
        elif any(keyword in id_lower for keyword in ['workflow', 'briefing', 'review', 'scan', 'dive']):
            return 'workflows'
        elif any(keyword in id_lower for keyword in ['governance', 'audit', 'compliance', 'quality', 'policy']):
            return 'governance'
        elif any(keyword in id_lower for keyword in ['ui', 'dashboard', 'alert', 'watchlist', 'help']):
            return 'ui'
        elif any(keyword in id_lower for keyword in ['add', 'create', 'export', 'generate']):
            return 'actions'
        elif any(keyword in id_lower for keyword in ['cycle', 'dalio', 'rotation']):
            return 'cycles'
        elif any(keyword in id_lower for keyword in ['system', 'meta', 'architecture', 'executor']):
            return 'system'

        return 'other'

    def _render_pattern_metrics(self, patterns: List[Dict]) -> None:
        """Render top-level pattern metrics"""
        col1, col2, col3, col4, col5 = st.columns(5)

        # Count by category
        categories = {}
        total_steps = 0
        high_priority = 0

        for pattern in patterns:
            cat = pattern['category']
            categories[cat] = categories.get(cat, 0) + 1
            total_steps += len(pattern['steps'])
            if pattern['priority'] >= 8:
                high_priority += 1

        with col1:
            st.metric("Total Patterns", len(patterns), delta="Active")

        with col2:
            st.metric("Categories", len(categories))

        with col3:
            st.metric("High Priority", high_priority)

        with col4:
            avg_steps = total_steps / len(patterns) if patterns else 0
            st.metric("Avg Steps", f"{avg_steps:.1f}")

        with col5:
            # Count patterns with entities (parameterized)
            parameterized = sum(1 for p in patterns if p['entities'])
            st.metric("Parameterized", parameterized)

    def _render_search_controls(self) -> tuple:
        """Render search and filter controls"""
        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            search_term = st.text_input(
                "🔍 Search patterns",
                placeholder="Search by name, description, or trigger phrase...",
                key="pattern_search"
            )

        with col2:
            categories = sorted(set(self.CATEGORY_CONFIG.keys()))
            category_filter = st.selectbox(
                "Category Filter",
                ["All Categories"] + [cat.title() for cat in categories],
                key="category_filter"
            )

        with col3:
            priority_filter = st.selectbox(
                "Priority Filter",
                ["All Priorities", "High (8+)", "Medium (5-7)", "Low (<5)"],
                key="priority_filter"
            )

        return search_term, category_filter, priority_filter

    def _filter_patterns(self, patterns: List[Dict], search_term: str,
                         category_filter: str, priority_filter: str) -> List[Dict]:
        """Filter patterns based on search and filter criteria"""
        filtered = patterns

        # Apply search filter
        if search_term:
            search_lower = search_term.lower()
            filtered = [
                p for p in filtered
                if search_lower in p['name'].lower()
                or search_lower in p['description'].lower()
                or any(search_lower in str(t).lower() for t in p['triggers'])
            ]

        # Apply category filter
        if category_filter != "All Categories":
            filtered = [
                p for p in filtered
                if p['category'] == category_filter.lower()
            ]

        # Apply priority filter
        if priority_filter == "High (8+)":
            filtered = [p for p in filtered if p['priority'] >= 8]
        elif priority_filter == "Medium (5-7)":
            filtered = [p for p in filtered if 5 <= p['priority'] < 8]
        elif priority_filter == "Low (<5)":
            filtered = [p for p in filtered if p['priority'] < 5]

        return filtered

    def _render_grid_view(self, patterns: List[Dict]) -> None:
        """Render patterns in grid view"""
        # Create 3-column grid
        for i in range(0, len(patterns), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(patterns):
                    with col:
                        self._render_pattern_card(patterns[i + j])

    def _render_list_view(self, patterns: List[Dict]) -> None:
        """Render patterns in list view"""
        for pattern in patterns:
            self._render_pattern_list_item(pattern)

    def _render_category_view(self, patterns: List[Dict]) -> None:
        """Render patterns grouped by category"""
        # Group patterns by category
        by_category = {}
        for pattern in patterns:
            cat = pattern['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(pattern)

        # Render each category
        for category in sorted(by_category.keys()):
            cat_patterns = by_category[category]
            config = self.CATEGORY_CONFIG.get(category, self.CATEGORY_CONFIG['other'])

            with st.expander(
                f"{config['icon']} **{category.title()}** ({len(cat_patterns)} patterns) - {config['description']}",
                expanded=True
            ):
                for pattern in cat_patterns:
                    self._render_pattern_list_item(pattern, show_category=False)

    def _render_pattern_card(self, pattern: Dict) -> None:
        """Render individual pattern as a card"""
        config = self.CATEGORY_CONFIG.get(pattern['category'], self.CATEGORY_CONFIG['other'])

        # Card container with custom styling
        with st.container():
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, {config['color']}15 0%, {config['color']}05 100%);
                            border-left: 4px solid {config['color']};
                            padding: 15px;
                            border-radius: 8px;
                            margin-bottom: 15px;">
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 24px; margin-right: 10px;">{config['icon']}</span>
                        <strong style="font-size: 16px;">{pattern['name']}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Description
            st.caption(pattern['description'][:100] + ('...' if len(pattern['description']) > 100 else ''))

            # Metadata
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"⭐ Priority: {pattern['priority']}")
            with col2:
                st.caption(f"🔧 Steps: {len(pattern['steps'])}")

            # Triggers (show first 2)
            if pattern['triggers']:
                triggers_display = pattern['triggers'][:2]
                st.caption(f"🎯 Triggers: {', '.join(str(t) for t in triggers_display)}")

            # Execute button
            if st.button(
                "▶️ Execute",
                key=f"exec_card_{pattern['id']}",
                width="stretch"
            ):
                st.session_state['selected_pattern'] = pattern['id']
                st.session_state['show_execution_form'] = True
                st.rerun()

            # Details expander
            with st.expander("📋 View Details"):
                self._render_pattern_details(pattern)

    def _render_pattern_list_item(self, pattern: Dict, show_category: bool = True) -> None:
        """Render pattern as a list item"""
        config = self.CATEGORY_CONFIG.get(pattern['category'], self.CATEGORY_CONFIG['other'])

        with st.container():
            col1, col2, col3 = st.columns([6, 4, 2])

            with col1:
                st.markdown(f"**{config['icon']} {pattern['name']}**")
                st.caption(pattern['description'][:80] + ('...' if len(pattern['description']) > 80 else ''))

            with col2:
                if show_category:
                    st.caption(f"📁 {pattern['category'].title()}")
                st.caption(f"⭐ Priority: {pattern['priority']} | 🔧 {len(pattern['steps'])} steps")

            with col3:
                if st.button("Execute", key=f"exec_list_{pattern['id']}", width="stretch"):
                    st.session_state['selected_pattern'] = pattern['id']
                    st.session_state['show_execution_form'] = True
                    st.rerun()

            st.markdown("---")

    def _render_pattern_details(self, pattern: Dict) -> None:
        """Render detailed pattern information"""
        # Basic info
        st.markdown(f"**Pattern ID:** `{pattern['id']}`")
        st.markdown(f"**Version:** {pattern['version']}")
        st.markdown(f"**Last Updated:** {pattern['last_updated']}")
        st.markdown(f"**Response Type:** {pattern['response_type']}")

        # All triggers
        if pattern['triggers']:
            st.markdown("**All Triggers:**")
            for trigger in pattern['triggers']:
                st.caption(f"  • {trigger}")

        # Entities (parameters)
        if pattern['entities']:
            st.markdown("**Required Parameters:**")
            for entity in pattern['entities']:
                st.caption(f"  • {entity}")

        # Steps breakdown
        st.markdown(f"**Execution Steps ({len(pattern['steps'])}):**")
        for i, step in enumerate(pattern['steps'], 1):
            action = step.get('action', step.get('agent', 'unknown'))
            outputs = step.get('outputs', step.get('save_as', []))
            if isinstance(outputs, str):
                outputs = [outputs]

            st.caption(f"  {i}. **{action}**")
            if outputs:
                st.caption(f"     → Outputs: {', '.join(outputs)}")

        # Show raw JSON
        with st.expander("🔍 View Raw JSON"):
            st.json(pattern['raw_pattern'])

    def render_pattern_execution_form(self, pattern: Dict) -> None:
        """Show input form for pattern parameters"""
        st.markdown(f"### Execute: {pattern['name']}")
        st.markdown(f"*{pattern['description']}*")

        params = {}

        # Check if pattern requires parameters
        entities = pattern.get('entities', [])

        if entities:
            st.markdown("**Required Parameters:**")

            with st.form(key=f"execution_form_{pattern['id']}"):
                for entity in entities:
                    if entity == 'SYMBOL':
                        params['symbol'] = st.text_input(
                            "Stock Symbol",
                            placeholder="e.g., AAPL, MSFT, GOOGL",
                            help="Enter a valid stock ticker symbol"
                        )
                    elif entity == 'SECTOR':
                        params['sector'] = st.selectbox(
                            "Sector",
                            ["Technology", "Healthcare", "Financial", "Consumer", "Energy", "Industrial"]
                        )
                    else:
                        params[entity.lower()] = st.text_input(
                            entity.replace('_', ' ').title(),
                            placeholder=f"Enter {entity.lower()}..."
                        )

                # Additional context
                additional_context = st.text_area(
                    "Additional Context (Optional)",
                    placeholder="Add any additional context or instructions...",
                    help="This will be passed to the pattern execution"
                )

                col1, col2 = st.columns([1, 1])
                with col1:
                    submit = st.form_submit_button("▶️ Execute Pattern", width="stretch")
                with col2:
                    cancel = st.form_submit_button("❌ Cancel", width="stretch")

                if cancel:
                    st.session_state['show_execution_form'] = False
                    st.session_state['selected_pattern'] = None
                    st.rerun()

                if submit:
                    # Build execution context
                    context = {
                        'user_input': f"Execute {pattern['name']} with params: {params}",
                        **params
                    }

                    if additional_context:
                        context['additional_context'] = additional_context

                    self.execute_pattern_ui(pattern, context)
        else:
            # No parameters required
            st.info("This pattern doesn't require any parameters.")

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("▶️ Execute Pattern", width="stretch"):
                    context = {
                        'user_input': f"Execute {pattern['name']}",
                        'timestamp': datetime.now().isoformat()
                    }
                    self.execute_pattern_ui(pattern, context)

            with col2:
                if st.button("❌ Cancel", width="stretch"):
                    st.session_state['show_execution_form'] = False
                    st.session_state['selected_pattern'] = None
                    st.rerun()

    def execute_pattern_ui(self, pattern: Dict, context: Dict) -> None:
        """Execute pattern and display results"""
        try:
            with st.spinner(f"Executing {pattern['name']}..."):
                # Execute via pattern engine
                result = self.pattern_engine.execute_pattern(pattern['raw_pattern'], context)

                # Store execution in history
                if 'pattern_execution_history' not in st.session_state:
                    st.session_state.pattern_execution_history = []

                execution_record = {
                    'pattern_id': pattern['id'],
                    'pattern_name': pattern['name'],
                    'timestamp': datetime.now().isoformat(),
                    'context': context,
                    'result': result,
                    'success': 'error' not in result
                }

                st.session_state.pattern_execution_history.append(execution_record)

                # Display results
                if 'error' in result:
                    st.error(f"❌ Execution Failed: {result['error']}")
                else:
                    st.success("✅ Pattern executed successfully!")

                    # Display formatted response if available
                    if 'formatted_response' in result:
                        st.markdown("### 📊 Results")
                        st.markdown(result['formatted_response'])

                    # Display confidence if available
                    if 'confidence' in result:
                        confidence = result['confidence']
                        if isinstance(confidence, (int, float)):
                            confidence_pct = confidence * 100 if confidence <= 1 else confidence
                            color = "green" if confidence_pct > 80 else "orange" if confidence_pct > 60 else "red"
                            st.metric("Confidence Score", f"{confidence_pct:.1f}%")

                    # Show step results
                    if 'results' in result and result['results']:
                        with st.expander("🔍 View Step-by-Step Results", expanded=False):
                            for step_result in result['results']:
                                step_num = step_result.get('step', '?')
                                step_action = step_result.get('action', step_result.get('agent', 'unknown'))

                                st.markdown(f"**Step {step_num}: {step_action}**")

                                if 'error' in step_result:
                                    st.error(f"Error: {step_result['error']}")
                                else:
                                    st.json(step_result.get('result', {}))

                                st.markdown("---")

                    # Show raw result
                    with st.expander("🔍 View Raw Result"):
                        st.json(result)

                # Reset form state
                st.session_state['show_execution_form'] = False
                st.session_state['selected_pattern'] = None

        except Exception as e:
            st.error(f"❌ Execution Error: {str(e)}")
            import traceback
            with st.expander("🐛 View Error Details"):
                st.code(traceback.format_exc())


def render_pattern_browser(runtime) -> None:
    """
    Main entry point for pattern browser tab

    Args:
        runtime: AgentRuntime instance with pattern_engine
    """
    # Initialize browser
    browser = PatternBrowser(runtime)

    # Check if we're showing execution form
    if st.session_state.get('show_execution_form') and st.session_state.get('selected_pattern'):
        pattern_id = st.session_state['selected_pattern']

        # Find the pattern
        all_patterns = browser._get_all_patterns()
        selected = next((p for p in all_patterns if p['id'] == pattern_id), None)

        if selected:
            browser.render_pattern_execution_form(selected)
        else:
            st.error("Pattern not found")
            st.session_state['show_execution_form'] = False
            st.session_state['selected_pattern'] = None
    else:
        # Show main browser
        browser.render_pattern_browser()

    # Show execution history in sidebar
    if st.session_state.get('pattern_execution_history'):
        st.sidebar.markdown("### 📜 Recent Executions")

        history = st.session_state['pattern_execution_history'][-5:]  # Last 5
        history.reverse()  # Most recent first

        for i, record in enumerate(history):
            timestamp = datetime.fromisoformat(record['timestamp']).strftime('%H:%M:%S')
            status_icon = "✅" if record['success'] else "❌"

            with st.sidebar.expander(f"{status_icon} {record['pattern_name']} - {timestamp}"):
                st.caption(f"**Pattern ID:** {record['pattern_id']}")
                st.caption(f"**Success:** {record['success']}")

                if st.button("View Full Result", key=f"history_view_{i}"):
                    st.session_state['view_history_result'] = record
