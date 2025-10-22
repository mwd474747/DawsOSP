# Trinity 3.0 UI Specialist

**Your Role**: Build production-ready UI for Trinity 3.0 with Bloomberg Terminal aesthetic

**Timeline**: Week 7-8
**Deliverables**:
- Week 7: Enhanced chat interface with entity extraction display
- Week 8: All 5 feature views (equity, portfolio, macro, economic, market)

---

## Mission

Create professional Bloomberg-quality UI for Trinity 3.0:
- Enhanced chat with conversation memory visualization
- Entity extraction display
- 5 streamlined feature views
- Bloomberg aesthetic (purple-pink-blue gradient, glass morphism, dark theme)
- **NO EMOJIS** (professional only)
- Real-time data integration
- Performance metrics dashboard

---

## Week 7 Tasks

### Day 1: Design System Foundation

**Create Design System**:

```python
# trinity3/ui/design_system.py
"""
Trinity 3.0 Bloomberg-inspired design system.

Key Principles:
- NO EMOJIS OR ICONS (professional text-only)
- Dark background with gradient accents
- Glass morphism for cards/panels
- Purple-pink-blue color scheme
- Clean typography hierarchy
"""

# Color Palette
COLORS = {
    # Backgrounds
    'bg_primary': '#0a0e27',
    'bg_secondary': '#1a1e3f',
    'bg_tertiary': '#2a2e4f',

    # Gradients
    'gradient_primary': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'gradient_accent': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'gradient_success': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',

    # Text
    'text_primary': '#ffffff',
    'text_secondary': '#b8c1ec',
    'text_tertiary': '#8892b0',

    # Accents
    'accent_purple': '#667eea',
    'accent_pink': '#f093fb',
    'accent_blue': '#4facfe',

    # Status
    'success': '#00f2fe',
    'warning': '#f5576c',
    'error': '#ff4757',
    'info': '#667eea'
}

# Typography
FONTS = {
    'heading_xl': {'size': '32px', 'weight': '700', 'line_height': '1.2'},
    'heading_lg': {'size': '24px', 'weight': '600', 'line_height': '1.3'},
    'heading_md': {'size': '20px', 'weight': '600', 'line_height': '1.4'},
    'heading_sm': {'size': '16px', 'weight': '600', 'line_height': '1.5'},
    'body_lg': {'size': '16px', 'weight': '400', 'line_height': '1.6'},
    'body_md': {'size': '14px', 'weight': '400', 'line_height': '1.6'},
    'body_sm': {'size': '12px', 'weight': '400', 'line_height': '1.5'},
    'mono': {'family': 'Monaco, Consolas, monospace', 'size': '13px'}
}

# Glass Morphism
GLASS_STYLE = """
    background: rgba(26, 30, 63, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
"""

# Component Styles
def get_card_style(variant='default'):
    """Get card styling"""
    base = GLASS_STYLE

    if variant == 'primary':
        return base + f"""
            border: 1px solid {COLORS['accent_purple']};
            box-shadow: 0 8px 32px 0 rgba(102, 126, 234, 0.2);
        """
    elif variant == 'accent':
        return base + f"""
            border: 1px solid {COLORS['accent_pink']};
            box-shadow: 0 8px 32px 0 rgba(240, 147, 251, 0.2);
        """
    else:
        return base

def get_button_style(variant='primary'):
    """Get button styling"""
    if variant == 'primary':
        return f"""
            background: {COLORS['gradient_primary']};
            color: {COLORS['text_primary']};
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        """
    elif variant == 'secondary':
        return f"""
            background: transparent;
            color: {COLORS['accent_purple']};
            border: 1px solid {COLORS['accent_purple']};
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        """

def apply_global_styles():
    """Apply global CSS to Streamlit"""
    return f"""
    <style>
        /* Hide Streamlit branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        /* Global background */
        .stApp {{
            background: {COLORS['bg_primary']};
            color: {COLORS['text_primary']};
        }}

        /* Headers */
        h1 {{
            font-size: {FONTS['heading_xl']['size']};
            font-weight: {FONTS['heading_xl']['weight']};
            color: {COLORS['text_primary']};
            margin-bottom: 1.5rem;
        }}

        h2 {{
            font-size: {FONTS['heading_lg']['size']};
            font-weight: {FONTS['heading_lg']['weight']};
            color: {COLORS['text_secondary']};
            margin-bottom: 1rem;
        }}

        h3 {{
            font-size: {FONTS['heading_md']['size']};
            font-weight: {FONTS['heading_md']['weight']};
            color: {COLORS['text_secondary']};
        }}

        /* Inputs */
        .stTextInput input {{
            background: {COLORS['bg_secondary']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['accent_purple']};
            border-radius: 8px;
            padding: 12px;
        }}

        /* Selectbox */
        .stSelectbox select {{
            background: {COLORS['bg_secondary']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['accent_purple']};
            border-radius: 8px;
        }}

        /* Cards/Containers */
        .element-container {{
            margin-bottom: 1rem;
        }}
    </style>
    """
```

**Success Criteria**:
- Design system defined
- Color palette, fonts, styles documented
- Global styles apply to Streamlit
- NO emojis in any component

---

### Day 2-3: Enhanced Chat Interface

**Create Enhanced Chat UI**:

```python
# trinity3/ui/enhanced_chat.py
import streamlit as st
from typing import Dict, Any, List
from datetime import datetime

class EnhancedChatUI:
    """Professional chat interface with entity extraction and memory"""

    def __init__(self, chat_processor, design_system):
        self.chat_processor = chat_processor
        self.design = design_system

    def render(self):
        """Render complete chat interface"""
        st.markdown(self.design.apply_global_styles(), unsafe_allow_html=True)

        # Header
        self._render_header()

        # Main layout: 70% chat, 30% sidebar
        col_chat, col_sidebar = st.columns([7, 3])

        with col_chat:
            self._render_chat_area()

        with col_sidebar:
            self._render_memory_panel()
            self._render_entity_panel()

    def _render_header(self):
        """Render chat header"""
        st.markdown(f"""
        <div style="{self.design.get_card_style('primary')}; padding: 1.5rem; margin-bottom: 2rem;">
            <h1 style="margin: 0; background: {self.design.COLORS['gradient_primary']}; -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Trinity Intelligence
            </h1>
            <p style="margin: 0; color: {self.design.COLORS['text_secondary']};">
                Natural language financial analysis powered by pattern-driven AI
            </p>
        </div>
        """, unsafe_allow_html=True)

    def _render_chat_area(self):
        """Render main chat conversation"""
        st.subheader("Conversation")

        # Initialize chat history
        if 'messages' not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for message in st.session_state.messages:
            self._render_message(message)

        # Input area
        user_input = st.text_input(
            "Ask about markets, stocks, economy...",
            key="chat_input",
            label_visibility="collapsed"
        )

        col1, col2 = st.columns([8, 2])
        with col1:
            use_extraction = st.checkbox("Enable entity extraction", value=True)

        with col2:
            if st.button("Send", type="primary"):
                if user_input:
                    self._process_message(user_input, use_extraction)
                    st.rerun()

    def _render_message(self, message: Dict[str, Any]):
        """Render single message"""
        role = message['role']
        content = message['content']
        timestamp = message.get('timestamp', datetime.now())

        # User message
        if role == 'user':
            st.markdown(f"""
            <div style="{self.design.get_card_style()}; padding: 1rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span style="color: {self.design.COLORS['accent_blue']}; font-weight: 600;">You</span>
                    <span style="color: {self.design.COLORS['text_tertiary']}; font-size: 12px;">{timestamp.strftime('%H:%M')}</span>
                </div>
                <p style="margin: 0; color: {self.design.COLORS['text_primary']};">{content}</p>
            </div>
            """, unsafe_allow_html=True)

        # Assistant message
        else:
            st.markdown(f"""
            <div style="{self.design.get_card_style('accent')}; padding: 1rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span style="color: {self.design.COLORS['accent_purple']}; font-weight: 600;">Trinity</span>
                    <span style="color: {self.design.COLORS['text_tertiary']}; font-size: 12px;">{timestamp.strftime('%H:%M')}</span>
                </div>
                <div style="color: {self.design.COLORS['text_primary']};">{content}</div>
            </div>
            """, unsafe_allow_html=True)

            # Show metadata if available
            if 'metadata' in message:
                with st.expander("Analysis Details"):
                    self._render_metadata(message['metadata'])

    def _render_metadata(self, metadata: Dict[str, Any]):
        """Render message metadata (pattern used, entities, etc.)"""
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            **Pattern Used**
            {metadata.get('pattern', 'N/A')}
            """)

        with col2:
            st.markdown(f"""
            **Intent Confidence**
            {metadata.get('intent_confidence', 0):.0%}
            """)

        with col3:
            st.markdown(f"""
            **Execution Time**
            {metadata.get('execution_time', 0):.2f}s
            """)

    def _render_memory_panel(self):
        """Render conversation memory visualization"""
        st.markdown(f"""
        <div style="{self.design.get_card_style()}; padding: 1rem; margin-bottom: 1rem;">
            <h3 style="margin-top: 0;">Conversation Memory</h3>
        """, unsafe_allow_html=True)

        memory = self.chat_processor.memory.get_recent_entities()

        # Recent symbols
        if memory.get('symbols'):
            st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <p style="color: {self.design.COLORS['text_secondary']}; font-size: 12px; margin-bottom: 0.5rem;">Recent Symbols</p>
            """, unsafe_allow_html=True)

            for symbol in memory['symbols'][:5]:
                st.markdown(f"""
                <span style="background: {self.design.COLORS['accent_purple']}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 0.5rem;">
                    {symbol}
                </span>
                """, unsafe_allow_html=True)

        # Recent sectors
        if memory.get('sectors'):
            st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <p style="color: {self.design.COLORS['text_secondary']}; font-size: 12px; margin-bottom: 0.5rem;">Recent Sectors</p>
            """, unsafe_allow_html=True)

            for sector in memory['sectors'][:3]:
                st.markdown(f"""
                <span style="background: {self.design.COLORS['accent_pink']}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 0.5rem;">
                    {sector}
                </span>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_entity_panel(self):
        """Render extracted entities from last query"""
        st.markdown(f"""
        <div style="{self.design.get_card_style()}; padding: 1rem;">
            <h3 style="margin-top: 0;">Extracted Entities</h3>
        """, unsafe_allow_html=True)

        if st.session_state.get('last_entities'):
            entities = st.session_state.last_entities

            # Symbol
            if entities.get('symbol'):
                st.markdown(f"""
                **Symbol**
                `{entities['symbol']}`
                """)

            # Analysis Type
            if entities.get('analysis_type'):
                st.markdown(f"""
                **Analysis Type**
                {entities['analysis_type'].replace('_', ' ').title()}
                """)

            # Depth
            if entities.get('depth'):
                st.markdown(f"""
                **Depth**
                {entities['depth'].title()}
                """)

            # Timeframe
            if entities.get('timeframe'):
                st.markdown(f"""
                **Timeframe**
                {entities['timeframe'].replace('_', ' ').title()}
                """)

        st.markdown("</div>", unsafe_allow_html=True)

    def _process_message(self, user_input: str, use_extraction: bool):
        """Process user message through chat processor"""
        # Add user message to history
        st.session_state.messages.append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now()
        })

        # Process with chat processor
        result = self.chat_processor.process_query(user_input, use_entity_extraction=use_extraction)

        # Add assistant response
        st.session_state.messages.append({
            'role': 'assistant',
            'content': result['response'],
            'timestamp': datetime.now(),
            'metadata': {
                'pattern': result.get('pattern'),
                'intent_confidence': result.get('intent', {}).get('confidence', 0),
                'execution_time': result.get('execution_time', 0)
            }
        })

        # Store entities for panel
        if result.get('extracted_entities'):
            st.session_state.last_entities = result['extracted_entities']
```

**Success Criteria**:
- Chat interface renders with Bloomberg aesthetic
- Conversation history displays correctly
- Memory panel shows recent entities
- Entity extraction panel shows parsed data
- NO emojis anywhere

---

### Day 4-5: Chat Features & Polish

**Add Suggested Follow-Ups**:
```python
def _render_suggested_followups(self):
    """Render context-aware follow-up suggestions"""
    suggestions = self.chat_processor.memory.suggest_follow_up()

    if suggestions:
        st.markdown(f"""
        <div style="{self.design.get_card_style()}; padding: 1rem; margin-top: 1rem;">
            <p style="color: {self.design.COLORS['text_secondary']}; font-size: 12px; margin-bottom: 0.5rem;">Suggested Follow-Ups</p>
        """, unsafe_allow_html=True)

        for suggestion in suggestions[:3]:
            if st.button(suggestion, key=f"suggestion_{suggestion}"):
                self._process_message(suggestion, use_extraction=True)
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
```

**Add Export Conversation**:
```python
def _render_export_button(self):
    """Export conversation history"""
    if st.button("Export Conversation"):
        import json
        conversation = {
            'messages': st.session_state.messages,
            'memory': self.chat_processor.memory.get_recent_entities(),
            'timestamp': datetime.now().isoformat()
        }

        st.download_button(
            "Download JSON",
            data=json.dumps(conversation, indent=2),
            file_name=f"trinity_conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
```

**Success Criteria**:
- Follow-up suggestions work
- Export conversation works
- Chat performance < 2s response time
- Professional appearance (no emojis)

---

## Week 8 Tasks

### Day 1: Feature View Framework

**Create View System**:

```python
# trinity3/ui/views/base_view.py
from abc import ABC, abstractmethod
import streamlit as st

class BaseView(ABC):
    """Base class for all feature views"""

    def __init__(self, runtime, design_system):
        self.runtime = runtime
        self.design = design_system

    @abstractmethod
    def render(self):
        """Render the view"""
        pass

    def render_metric_card(self, title: str, value: str, delta: str = None, trend: str = None):
        """Render metric card (standard component)"""
        st.markdown(f"""
        <div style="{self.design.get_card_style()}; padding: 1.5rem;">
            <p style="color: {self.design.COLORS['text_tertiary']}; font-size: 12px; margin: 0 0 0.5rem 0; text-transform: uppercase; letter-spacing: 1px;">
                {title}
            </p>
            <h2 style="margin: 0; color: {self.design.COLORS['text_primary']};">
                {value}
            </h2>
            {f'<p style="color: {self.design.COLORS["success"] if trend == "up" else self.design.COLORS["error"]}; font-size: 14px; margin: 0.5rem 0 0 0;">{delta}</p>' if delta else ''}
        </div>
        """, unsafe_allow_html=True)
```

**Success Criteria**:
- Base view class created
- Standard components (metric card, table, chart)
- Design system integrated

---

### Day 2: Equity Analysis View

**Create Equity View**:

```python
# trinity3/ui/views/equity_view.py
from .base_view import BaseView
import streamlit as st

class EquityView(BaseView):
    """Equity analysis view"""

    def render(self):
        st.markdown("<h1>Equity Analysis</h1>", unsafe_allow_html=True)

        # Symbol input
        symbol = st.text_input("Enter Symbol", value="AAPL")

        # Analysis type selector
        analysis_type = st.selectbox(
            "Analysis Type",
            ["Fundamental", "Technical", "Valuation", "Comprehensive"]
        )

        if st.button("Analyze", type="primary"):
            self._run_analysis(symbol, analysis_type)

    def _run_analysis(self, symbol: str, analysis_type: str):
        """Run equity analysis"""
        # Route to appropriate pattern
        pattern_map = {
            'Fundamental': 'smart_stock_analysis',
            'Technical': 'technical_analysis',
            'Valuation': 'valuation_analysis',
            'Comprehensive': 'deep_dive'
        }

        pattern_id = pattern_map[analysis_type]

        # Execute via runtime
        result = self.runtime.execute_pattern(pattern_id, {
            'symbol': symbol,
            'analysis_type': analysis_type.lower(),
            'depth': 'standard'
        })

        # Display results
        self._display_results(result)

    def _display_results(self, result: Dict):
        """Display analysis results"""
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        data = result.get('data', {})

        with col1:
            self.render_metric_card(
                "P/E Ratio",
                f"{data.get('pe_ratio', 0):.2f}",
                delta="+12% vs sector"
            )

        with col2:
            self.render_metric_card(
                "Revenue Growth",
                f"{data.get('revenue_growth', 0):.1f}%",
                trend="up"
            )

        # ... add more metrics
        with col3:
            self.render_metric_card("Profit Margin", f"{data.get('profit_margin', 0):.1f}%")

        with col4:
            self.render_metric_card("Debt/Equity", f"{data.get('debt_to_equity', 0):.2f}")

        # Full response
        st.markdown(f"""
        <div style="{self.design.get_card_style()}; padding: 2rem; margin-top: 2rem;">
            {result.get('response', 'No analysis available')}
        </div>
        """, unsafe_allow_html=True)
```

**Success Criteria**:
- Equity view renders
- Analysis executes via patterns
- Results display professionally
- NO emojis

---

### Day 3-4: Portfolio, Macro, Economic Views

**Create Remaining Views** (same pattern as equity):

1. **Portfolio View** (`portfolio_view.py`):
   - Portfolio input (holdings table)
   - Risk metrics dashboard
   - Allocation visualization
   - Rebalancing recommendations

2. **Macro View** (`macro_view.py`):
   - Sector rotation heatmap
   - Economic regime indicator
   - Macro-aware allocation

3. **Economic View** (`economic_view.py`):
   - Key indicators dashboard (GDP, inflation, unemployment, fed rate)
   - Recession risk gauge
   - Economic calendar
   - FRED data charts

**Success Criteria**:
- All 4 views created
- Each view uses patterns
- Professional Bloomberg aesthetic
- NO emojis

---

### Day 5: Market Overview Dashboard

**Create Market View**:

```python
# trinity3/ui/views/market_view.py
class MarketView(BaseView):
    """Real-time market overview"""

    def render(self):
        st.markdown("<h1>Market Overview</h1>", unsafe_allow_html=True)

        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)

        # Fetch real-time data
        sp500 = self.runtime.openbb_adapter.fetch_stock_quote("SPY")
        nasdaq = self.runtime.openbb_adapter.fetch_stock_quote("QQQ")
        vix = self.runtime.openbb_adapter.fetch_stock_quote("VIX")
        tnx = self.runtime.openbb_adapter.fetch_stock_quote("TNX")

        with col1:
            self.render_metric_card(
                "S&P 500",
                f"${sp500['price']:.2f}",
                delta=f"{sp500['change_percent']:.2f}%",
                trend="up" if sp500['change'] > 0 else "down"
            )

        with col2:
            self.render_metric_card(
                "Nasdaq",
                f"${nasdaq['price']:.2f}",
                delta=f"{nasdaq['change_percent']:.2f}%",
                trend="up" if nasdaq['change'] > 0 else "down"
            )

        with col3:
            self.render_metric_card(
                "VIX",
                f"{vix['price']:.2f}",
                delta=f"{vix['change_percent']:.2f}%",
                trend="down" if vix['change'] > 0 else "up"  # Inverted (high VIX = bad)
            )

        with col4:
            self.render_metric_card(
                "10Y Treasury",
                f"{tnx['price']:.2f}%"
            )

        # Sector performance
        self._render_sector_performance()

        # Market breadth
        self._render_market_breadth()

    def _render_sector_performance(self):
        """Render sector performance heatmap"""
        st.subheader("Sector Performance")

        # Fetch sector ETFs
        sectors = ['XLK', 'XLF', 'XLV', 'XLE', 'XLI', 'XLP', 'XLY', 'XLC', 'XLU', 'XLRE', 'XLB']
        sector_data = []

        for sector_etf in sectors:
            data = self.runtime.openbb_adapter.fetch_stock_quote(sector_etf)
            sector_data.append({
                'sector': sector_etf,
                'change': data['change_percent']
            })

        # Render as heatmap (using Plotly or custom HTML)
        # ...

    def _render_market_breadth(self):
        """Render market breadth indicators"""
        # Fetch breadth data
        # Render advance/decline, new highs/lows, etc.
        pass
```

**Success Criteria**:
- Market view shows real-time data
- Sector performance visualized
- Market breadth indicators
- Professional appearance

---

## Common Issues & Solutions

### Issue 1: Emojis Appearing
**Symptom**: Emojis in UI despite design guidelines
**Solution**: Search codebase for emoji characters, replace with text

```bash
grep -r "[\u{1F600}-\u{1F64F}]" trinity3/ui/
```

### Issue 2: Slow UI Performance
**Symptom**: UI takes > 2s to render
**Solution**:
1. Use st.cache_data for expensive computations
2. Implement lazy loading for charts
3. Reduce real-time data fetches

### Issue 3: Responsive Layout Issues
**Symptom**: UI breaks on different screen sizes
**Solution**: Use Streamlit columns with relative widths, test on multiple screens

---

## Resources

- **Design Guide**: [trinity3/DESIGN_GUIDE.md](../trinity3/DESIGN_GUIDE.md)
- **Streamlit Docs**: https://docs.streamlit.io
- **Bloomberg Terminal** (for design inspiration)

**Report to**: Migration Lead
**Update**: MIGRATION_STATUS.md weekly
**Escalate**: Performance issues, design inconsistencies, emoji violations
