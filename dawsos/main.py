import streamlit as st
import os
import plotly.graph_objects as go
import networkx as nx
import pandas as pd

# Load environment variables
from load_env import load_env
load_env()

# Core imports
from core.knowledge_graph import KnowledgeGraph
from core.agent_runtime import AgentRuntime
from core.persistence import PersistenceManager
from core.pattern_engine import PatternEngine
from core.universal_executor import UniversalExecutor
from core.agent_capabilities import AGENT_CAPABILITIES
from core.llm_client import LLMClient

# Agent imports
from agents.graph_mind import GraphMind
from agents.claude import Claude
from agents.data_harvester import DataHarvester
from agents.data_digester import DataDigester
from agents.relationship_hunter import RelationshipHunter
from agents.pattern_spotter import PatternSpotter
from agents.forecast_dreamer import ForecastDreamer
from agents.code_monkey import CodeMonkey
from agents.structure_bot import StructureBot
from agents.refactor_elf import RefactorElf
from agents.workflow_recorder import WorkflowRecorder
from agents.workflow_player import WorkflowPlayer
from agents.ui_generator import UIGeneratorAgent
from agents.financial_analyst import FinancialAnalyst
from agents.governance_agent import GovernanceAgent

# Capability imports
from capabilities.market_data import MarketDataCapability
from capabilities.fred_data import FredDataCapability
from capabilities.news import NewsCapability
from capabilities.crypto import CryptoCapability
from capabilities.fundamentals import FundamentalsCapability
from capabilities.polygon_options import PolygonOptionsCapability

# Workflow imports
from workflows.investment_workflows import InvestmentWorkflows
from ui.workflows_tab import render_workflows_tab

# New UI imports
from ui.pattern_browser import render_pattern_browser
from ui.alert_panel import AlertPanel
from core.alert_manager import AlertManager

# Trinity UI imports
from ui.trinity_ui_components import get_trinity_ui
from ui.data_integrity_tab import render_data_integrity_tab
from ui.trinity_dashboard_tabs import get_trinity_dashboard_tabs
from ui.api_health_tab import render_api_health_tab
from ui.economic_dashboard import render_economic_dashboard

# Page config
st.set_page_config(
    page_title="DawsOS - Knowledge Graph Intelligence",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main {padding-top: 2rem;}
    .stChatInput > div > div > input {font-size: 16px;}
    .graph-container {background: #0e1117; border-radius: 10px; padding: 20px;}
    .metric-card {background: #262730; border-radius: 8px; padding: 15px; margin: 10px 0;}
    .pattern-badge {background: #00cc88; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;}
    .risk-badge {background: #ff4444; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;}
    </style>
""", unsafe_allow_html=True)

def _init_knowledge_graph():
    """Initialize knowledge graph with loading and seeding logic."""
    st.session_state.graph = KnowledgeGraph()

    # Try to load existing graph
    if os.path.exists('storage/graph.json'):
        try:
            st.session_state.graph.load('storage/graph.json')
            print(f"Loaded graph with {st.session_state.graph.get_stats()['total_nodes']} nodes from file")
            return
        except Exception as e:
            print(f"Error loading graph: {e}")

    # Seed with fundamental analysis knowledge if not enough nodes
    if st.session_state.graph.get_stats()['total_nodes'] < 40:
        try:
            import seed_knowledge_graph
            seed_knowledge_graph.seed_buffett_framework(st.session_state.graph)
            seed_knowledge_graph.seed_dalio_framework(st.session_state.graph)
            seed_knowledge_graph.seed_financial_calculations(st.session_state.graph)
            seed_knowledge_graph.seed_investment_examples(st.session_state.graph)
            print(f"Seeded knowledge graph to {st.session_state.graph.get_stats()['total_nodes']} nodes")

            # Save the seeded graph with backup
            if 'persistence' in st.session_state:
                st.session_state.persistence.save_graph_with_backup(st.session_state.graph)
            else:
                st.session_state.graph.save('storage/graph.json')
        except Exception as e:
            print(f"Note: Knowledge seeding skipped: {e}")


def _init_capabilities():
    """Initialize external capabilities for agents."""
    st.session_state.capabilities = {
        'fred': FredDataCapability(),
        'market': MarketDataCapability(),
        'news': NewsCapability(),
        'crypto': CryptoCapability(),
        'fundamentals': FundamentalsCapability(),
        'polygon': PolygonOptionsCapability()
    }


def _init_llm_client():
    """Initialize LLM client (optional - system works without it)."""
    try:
        st.session_state.llm_client = LLMClient()
        print("✅ LLM Client initialized successfully")
    except Exception as e:
        st.session_state.llm_client = None
        print(f"⚠️ LLM Client not available: {e}")


def _register_all_agents(runtime, caps):
    """Register all agents with their capabilities."""
    runtime.graph = st.session_state.graph

    # Core agents
    runtime.register_agent('graph_mind', GraphMind(st.session_state.graph),
                          capabilities=AGENT_CAPABILITIES['graph_mind'])
    runtime.register_agent('claude', Claude(st.session_state.graph, llm_client=st.session_state.llm_client),
                          capabilities=AGENT_CAPABILITIES['claude'])

    # Data agents
    runtime.register_agent('data_harvester', DataHarvester(st.session_state.graph, caps),
                          capabilities=AGENT_CAPABILITIES['data_harvester'])
    runtime.register_agent('data_digester', DataDigester(st.session_state.graph),
                          capabilities=AGENT_CAPABILITIES['data_digester'])

    # Analysis agents
    runtime.register_agent('relationship_hunter', RelationshipHunter(st.session_state.graph, capabilities=caps),
                          capabilities=AGENT_CAPABILITIES['relationship_hunter'])
    runtime.register_agent('pattern_spotter', PatternSpotter(st.session_state.graph),
                          capabilities=AGENT_CAPABILITIES['pattern_spotter'])
    runtime.register_agent('forecast_dreamer', ForecastDreamer(st.session_state.graph),
                          capabilities=AGENT_CAPABILITIES['forecast_dreamer'])

    # Development agents
    runtime.register_agent('code_monkey', CodeMonkey(st.session_state.graph),
                          capabilities=AGENT_CAPABILITIES['code_monkey'])
    runtime.register_agent('structure_bot', StructureBot(st.session_state.graph),
                          capabilities=AGENT_CAPABILITIES['structure_bot'])
    runtime.register_agent('refactor_elf', RefactorElf(st.session_state.graph),
                          capabilities=AGENT_CAPABILITIES['refactor_elf'])

    # Workflow agents
    runtime.register_agent('workflow_recorder', WorkflowRecorder(st.session_state.graph),
                          capabilities=AGENT_CAPABILITIES['workflow_recorder'])
    runtime.register_agent('workflow_player', WorkflowPlayer(st.session_state.graph),
                          capabilities=AGENT_CAPABILITIES['workflow_player'])

    # UI and business agents
    runtime.register_agent('ui_generator', UIGeneratorAgent(st.session_state.graph),
                          capabilities=AGENT_CAPABILITIES['ui_generator'])
    runtime.register_agent('financial_analyst', FinancialAnalyst(st.session_state.graph),
                          capabilities=AGENT_CAPABILITIES['financial_analyst'])
    runtime.register_agent('governance_agent', GovernanceAgent(st.session_state.graph),
                          capabilities=AGENT_CAPABILITIES['governance_agent'])


def _init_agent_runtime():
    """Initialize agent runtime with all agents and pattern engine."""
    st.session_state.agent_runtime = AgentRuntime()

    # Register all agents
    _register_all_agents(st.session_state.agent_runtime, st.session_state.capabilities)

    # Initialize PatternEngine after agents are registered
    st.session_state.agent_runtime.pattern_engine = PatternEngine(
        'dawsos/patterns',
        runtime=st.session_state.agent_runtime,
        graph=st.session_state.graph
    )
    print(f"PatternEngine initialized with {len(st.session_state.agent_runtime.pattern_engine.patterns)} patterns")


def _init_executor():
    """Initialize Universal Executor for Trinity execution flow."""
    st.session_state.executor = UniversalExecutor(
        st.session_state.graph,
        st.session_state.agent_runtime.agent_registry,
        runtime=st.session_state.agent_runtime
    )
    print("Universal Executor initialized - ALL execution now routes through Trinity path")
    st.session_state.agent_runtime.executor = st.session_state.executor


def _init_workflows():
    """Initialize investment workflows."""
    st.session_state.workflows = InvestmentWorkflows(
        st.session_state.agent_runtime,
        st.session_state.graph
    )


def _init_persistence():
    """Initialize persistence manager."""
    st.session_state.persistence = PersistenceManager()


def _init_alert_manager():
    """Initialize alert manager with default alerts."""
    st.session_state.alert_manager = AlertManager()
    st.session_state.alert_manager.create_template_alert('compliance_violation', threshold=0)


def init_session_state():
    """Initialize session state variables.

    Orchestrates initialization of all core components in correct order:
    1. Knowledge graph (load or seed)
    2. Capabilities (external APIs)
    3. LLM client (optional)
    4. Agent runtime (with all agents)
    5. Universal executor (Trinity flow)
    6. Supporting systems (workflows, persistence, alerts, chat)
    """
    if 'graph' not in st.session_state:
        _init_knowledge_graph()

    if 'capabilities' not in st.session_state:
        _init_capabilities()

    if 'llm_client' not in st.session_state:
        _init_llm_client()

    if 'agent_runtime' not in st.session_state:
        _init_agent_runtime()

    if 'executor' not in st.session_state:
        _init_executor()

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'workflows' not in st.session_state:
        _init_workflows()

    if 'persistence' not in st.session_state:
        _init_persistence()

    if 'alert_manager' not in st.session_state:
        _init_alert_manager()

def visualize_graph():
    """Create interactive graph visualization"""
    graph = st.session_state.graph
    
    # Create NetworkX graph
    G = nx.DiGraph()
    
    # Add nodes
    for node_id, node_data in graph._graph.nodes(data=True):
        G.add_node(node_id, **node_data)
    
    # Add edges
    for edge in graph.get_all_edges():
        G.add_edge(
            edge['from'], 
            edge['to'], 
            weight=edge['strength'],
            type=edge['type']
        )
    
    # Generate layout
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Create Plotly figure
    edge_trace = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_data = G.edges[edge]  # Get actual edge data for current edge

        # Color based on relationship type
        edge_color = '#666'
        if edge_data['type'] in ['causes', 'supports']:
            edge_color = '#00cc88'
        elif edge_data['type'] in ['pressures', 'weakens']:
            edge_color = '#ff4444'

        edge_trace.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(width=edge_data.get('strength', 0.5) * 3, color=edge_color),
            hoverinfo='none'
        ))
    
    # Node trace
    node_trace = go.Scatter(
        x=[],
        y=[],
        mode='markers+text',
        hoverinfo='text',
        marker=dict(
            size=[],
            color=[],
            colorscale='Viridis',
            line_width=2
        ),
        text=[],
        textposition="top center"
    )
    
    for node in G.nodes():
        x, y = pos[node]
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])
        node_trace['text'] += tuple([node])
        
        # Color by node type
        node_data = graph.get_node(node)
        if node_data['type'] == 'indicator':
            color = '#3498db'
        elif node_data['type'] == 'sector':
            color = '#e74c3c'
        elif node_data['type'] == 'stock':
            color = '#f39c12'
        else:
            color = '#95a5a6'
            
        node_trace['marker']['color'] += tuple([color])
        node_trace['marker']['size'] += tuple([20 + len(list(G.neighbors(node))) * 5])
        
        # Hover text
        hover_text = f"{node}<br>Type: {node_data['type']}<br>Connections: {len(list(G.neighbors(node)))}"
        node_trace['hoverinfo'] = 'text'
    
    # Create figure
    fig = go.Figure(data=edge_trace + [node_trace])
    
    fig.update_layout(
        showlegend=False,
        hovermode='closest',
        margin=dict(b=0,l=0,r=0,t=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=500
    )
    
    return fig

def _display_user_message(content):
    """Display user message in chat."""
    st.write(content)


def _display_forecast_result(result):
    """Display forecast result with metrics."""
    forecast = result.get('result', {})
    col1, col2, col3 = st.columns(3)
    col1.metric("Forecast", forecast.get('forecast', 'Unknown'))
    col2.metric("Confidence", f"{forecast.get('confidence', 0)*100:.1f}%")
    col3.metric("Signal", f"{forecast.get('signal_strength', 0):.2f}")


def _display_action_result(result):
    """Display action results (add_node, connect, etc)."""
    if result.get('action') == 'explain':
        st.write(result.get('text', ''))
    elif result.get('action') == 'forecast':
        _display_forecast_result(result)
    elif result.get('action') == 'add_node':
        st.success(f"Added node: {result.get('node_id')}")
    elif result.get('action') == 'connect':
        st.info(f"Connected: {result.get('from')} to {result.get('to')}")
    elif 'error' in result:
        st.error(f"Error: {result['error']}")
    elif 'response' in result:
        st.write(result['response'])


def _display_assistant_message(content):
    """Display assistant message with pattern info."""
    if isinstance(content, dict):
        # Show pattern badge if available
        if 'pattern' in content:
            st.caption(f"🔮 Pattern: {content.get('pattern', 'Unknown')}")

        # Display response content
        if 'formatted_response' in content:
            st.write(content['formatted_response'])
        elif 'response' in content:
            st.write(content['response'])
        elif 'results' in content:
            for result in content['results']:
                if isinstance(result, dict):
                    _display_action_result(result)
        elif 'friendly_response' in content:
            st.write(content['friendly_response'])
        else:
            st.json(content)
    else:
        st.write(content)


def _display_chat_history():
    """Display complete chat history."""
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                _display_user_message(message["content"])
            else:
                _display_assistant_message(message["content"])


def _show_fallback_warning(response):
    """Show fallback/cached data warning if applicable."""
    if response.get('source') == 'fallback':
        ui_message = response.get('ui_message', '⚠️ Using cached data')
        st.warning(ui_message)

        with st.expander("ℹ️ Why am I seeing cached data?"):
            reason = response.get('fallback_reason', 'Unknown')
            st.markdown(f"""
**Reason**: {reason}

**To enable live AI responses**:
1. Add `ANTHROPIC_API_KEY` to your `.env` file
2. Restart the application

**Note**: Cached responses are still useful for analysis and are updated regularly.
            """)


def _display_response_content(response):
    """Display main response content."""
    if 'error' in response:
        st.error(f"Error: {response['error']}")
        return

    # Show pattern info
    if 'pattern' in response:
        st.caption(f"🔮 Pattern: {response.get('pattern', 'Unknown')}")

    # Display main content
    if 'formatted_response' in response:
        st.write(response['formatted_response'])
    elif 'response' in response:
        st.write(response['response'])
    elif 'results' in response and response['results']:
        for i, result in enumerate(response['results']):
            if isinstance(result, dict):
                if 'error' in result:
                    st.error(f"Step {i+1} error: {result['error']}")
                elif 'response' in result:
                    st.write(result['response'])
                elif 'data' in result:
                    st.json(result['data'])
    elif 'friendly_response' in response:
        st.write(response['friendly_response'])
    else:
        st.json(response)


def _process_user_input(user_input):
    """Process user input and generate response."""
    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Get response from agent system
    with st.chat_message("assistant"):
        with st.spinner("DawsOS is thinking..."):
            response = st.session_state.agent_runtime.orchestrate(user_input)

            # Show fallback warning if needed
            _show_fallback_warning(response)

            # Display response
            _display_response_content(response)

            # Add to history if successful
            if 'error' not in response:
                st.session_state.chat_history.append({"role": "assistant", "content": response})

                # Save graph with backup after changes
                st.session_state.persistence.save_graph_with_backup(st.session_state.graph)

                # Force rerun to update graph
                st.rerun()


# Legacy display_* functions removed - now using Trinity dashboard tabs directly



def _render_main_tabs():
    """Render all main application tabs using Trinity architecture."""
    # Initialize Trinity tabs for tabs that use it
    trinity_tabs = get_trinity_dashboard_tabs(
        st.session_state.agent_runtime.pattern_engine,
        st.session_state.agent_runtime,
        st.session_state.graph
    )

    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12 = st.tabs([
        "Chat",
        "Knowledge Graph",
        "Dashboard",
        "Markets",
        "Economy",
        "Workflows",
        "Trinity UI",
        "Data Integrity",
        "Data Governance",
        "Pattern Browser",
        "Alerts",
        "API Health"
    ])

    with tab1:
        trinity_tabs.render_trinity_chat_interface()

    with tab2:
        trinity_tabs.render_trinity_knowledge_graph()

    with tab3:
        trinity_tabs.render_trinity_dashboard()

    with tab4:
        trinity_tabs.render_trinity_markets()

    with tab5:
        # Trinity 3.0 GDP Refresh Flow dashboard with FRED data
        render_economic_dashboard(
            st.session_state.agent_runtime,
            st.session_state.capabilities
        )

    with tab6:
        trinity_tabs.render_trinity_workflows()

    with tab7:
        # Trinity UI Tab - Pattern-Knowledge-Agent powered interface
        try:
            trinity_ui = get_trinity_ui(
                pattern_engine=st.session_state.agent_runtime.pattern_engine,
                runtime=st.session_state.agent_runtime
            )
            trinity_ui.render_trinity_dashboard()
        except Exception as e:
            st.error(f"Trinity UI Error: {str(e)}")
            st.info("This is the new Trinity-powered UI system leveraging the Pattern-Knowledge-Agent architecture.")
            st.markdown("### Features")
            st.markdown("- Pattern-driven UI generation")
            st.markdown("- Knowledge-based content")
            st.markdown("- Agent-orchestrated components")
            st.markdown("- Real-time intelligence dashboard")

    with tab8:
        # Data Integrity Tab - Real-time data monitoring and management
        render_data_integrity_tab()

    with tab9:
        # Data Governance Tab
        from ui.governance_tab import render_governance_tab
        try:
            render_governance_tab(st.session_state.agent_runtime, st.session_state.graph)
        except Exception as e:
            st.error(f"Data Governance tab error: {str(e)}")
            st.info("The Data Governance system provides conversational governance capabilities.")
            st.markdown("### Features")
            st.markdown("- 🛡️ Conversational governance interface")
            st.markdown("- 📊 Real-time governance monitoring")
            st.markdown("- 🎯 Data quality, compliance, and cost governance patterns")
            st.markdown("- ⚡ Quick governance actions")
            st.markdown("- 📚 Governance activity history")

    with tab10:
        # Pattern Browser Tab - Browse and Execute All Patterns
        try:
            render_pattern_browser(st.session_state.agent_runtime)
        except Exception as e:
            st.error(f"Pattern Browser Error: {str(e)}")
            st.info("The Pattern Browser provides comprehensive access to all patterns in the system.")
            st.markdown("### Features")
            st.markdown("- 🔍 Search and filter patterns by name, description, triggers")
            st.markdown("- 📁 Browse by category (queries, analysis, workflows, etc.)")
            st.markdown("- ⭐ Filter by priority level")
            st.markdown("- 📊 View detailed pattern information and steps")
            st.markdown("- ▶️ Execute patterns with parameter input forms")
            st.markdown("- 📈 View execution results with confidence scores")
            st.markdown("- 📜 Track execution history")

    with tab11:
        # Alerts Tab - Alert Management and Notifications
        try:
            alert_panel = AlertPanel(
                st.session_state.alert_manager,
                st.session_state.agent_runtime
            )
            alert_panel.render_alert_panel()
        except Exception as e:
            st.error(f"Alerts Tab Error: {str(e)}")
            st.info("The Alert System monitors patterns, data quality, and system health.")
            st.markdown("### Features")
            st.markdown("- 📊 Alert analytics dashboard")
            st.markdown("- ➕ Create custom alerts with templates")
            st.markdown("- 📋 Manage active alerts with filters")
            st.markdown("- 📜 View alert history and acknowledge events")

    with tab12:
        # API Health Tab - Fallback monitoring and API status
        try:
            render_api_health_tab()
        except Exception as e:
            st.error(f"API Health Tab Error: {str(e)}")
            st.info("The API Health Monitor tracks fallback events and API configuration.")
            st.markdown("### Features")
            st.markdown("- 📊 Fallback event statistics (LLM, APIs, cache)")
            st.markdown("- 🕐 Recent fallback events with explanations")
            st.markdown("- 🔑 API configuration status checker")
            st.markdown("- 📡 FRED API health metrics")
            st.markdown("- 📅 Data freshness guidelines")
            st.markdown("- 🔧 Quick template-based alert creation")


def _execute_chat_action(user_msg: str, success_msg: str) -> None:
    """Execute a chat action and display feedback.

    Args:
        user_msg: User message to send to agent runtime
        success_msg: Success message to display to user
    """
    st.session_state.chat_history.append({"role": "user", "content": user_msg})
    response = st.session_state.agent_runtime.orchestrate(user_msg)
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    st.success(success_msg)
    st.rerun()


def _render_quick_actions():
    """Render quick action buttons in sidebar."""
    st.markdown("### Quick Actions")

    if st.button("Analyze Macro Environment"):
        _execute_chat_action("Show me macro analysis", "Analysis complete! Check the chat tab.")

    if st.button("Detect Market Regime"):
        _execute_chat_action("Detect the market regime", "Regime detected! Check the chat tab.")

    if st.button("Find Patterns"):
        _execute_chat_action("Show sector performance", "Patterns discovered! Check the chat tab.")

    if st.button("Hunt Relationships"):
        _execute_chat_action("Find correlations for SPY", "Relationships found! Check the chat tab.")


def _render_fundamental_analysis():
    """Render fundamental analysis buttons in sidebar."""
    st.markdown("### Fundamental Analysis")

    if st.button("🏰 Analyze Moat"):
        _execute_chat_action("Analyze economic moat for AAPL", "Moat analysis complete!")

    if st.button("✅ Buffett Checklist"):
        _execute_chat_action("Run Buffett checklist for MSFT", "Checklist complete!")

    if st.button("💰 Owner Earnings"):
        _execute_chat_action("Calculate owner earnings", "Calculation complete!")

    if st.button("🔄 Debt Cycle"):
        _execute_chat_action("Where are we in the debt cycle?", "Cycle analysis complete!")


def _render_pattern_library():
    """Render available patterns browser in sidebar."""
    st.markdown("### Available Patterns")

    if not hasattr(st.session_state.agent_runtime, 'pattern_engine'):
        return

    pattern_engine = st.session_state.agent_runtime.pattern_engine
    pattern_categories = {
        'Queries': [],
        'Analysis': [],
        'Actions': [],
        'Workflows': [],
        'UI': []
    }

    for pattern_id, pattern in pattern_engine.patterns.items():
        if pattern_id == 'schema':
            continue

        # Categorize patterns
        if pattern_id in ['stock_price', 'market_regime', 'macro_analysis', 'company_analysis', 'sector_performance', 'correlation_finder']:
            pattern_categories['Queries'].append(pattern['name'])
        elif pattern_id in ['technical_analysis', 'portfolio_analysis', 'earnings_analysis', 'risk_assessment', 'sentiment_analysis']:
            pattern_categories['Analysis'].append(pattern['name'])
        elif pattern_id in ['add_to_graph', 'create_alert', 'generate_forecast', 'add_to_portfolio', 'export_data']:
            pattern_categories['Actions'].append(pattern['name'])
        elif pattern_id in ['morning_briefing', 'deep_dive', 'opportunity_scan', 'portfolio_review']:
            pattern_categories['Workflows'].append(pattern['name'])
        elif pattern_id in ['dashboard_update', 'watchlist_update', 'help_guide']:
            pattern_categories['UI'].append(pattern['name'])

    with st.expander("📚 Pattern Library", expanded=False):
        for category, patterns in pattern_categories.items():
            if patterns:
                st.caption(f"**{category}** ({len(patterns)})")
                for pattern_name in patterns:
                    st.text(f"  • {pattern_name}")


def _render_graph_controls():
    """Render graph control buttons in sidebar."""
    st.markdown("### Graph Controls")

    if st.button("Save Graph"):
        save_result = st.session_state.persistence.save_graph_with_backup(st.session_state.graph)
        st.success(f"Graph saved with backup! Checksum: {save_result['checksum'][:16]}...")

    if st.button("Load Graph"):
        if st.session_state.graph.load('storage/graph.json'):
            st.success("Graph loaded!")
            st.rerun()

    if st.button("Clear Graph"):
        if st.checkbox("Confirm clear"):
            st.session_state.graph = KnowledgeGraph()
            st.session_state.chat_history = []
            st.success("Graph cleared!")
            st.rerun()


def _render_api_status():
    """Render API status indicators in sidebar."""
    st.markdown("### API Status")

    api_status = {
        "Claude": "Active" if os.getenv('ANTHROPIC_API_KEY') else "Missing",
        "FMP": "Active" if os.getenv('FMP_API_KEY') else "Missing",
        "FRED": "Active",  # Free API
        "News": "Warning",  # Needs key
    }

    for api, status in api_status.items():
        if status == "Active":
            st.write(f"[Active] {api}")
        elif status == "Missing":
            st.write(f"[Missing] {api}")
        else:
            st.write(f"[Warning] {api}")


def _render_sidebar():
    """Render complete sidebar with all sections."""
    with st.sidebar:
        _render_quick_actions()

        # API Health Status
        st.markdown("---")
        try:
            trinity_ui = get_trinity_ui(
                pattern_engine=st.session_state.agent_runtime.pattern_engine,
                runtime=st.session_state.agent_runtime
            )
            trinity_ui.render_api_health_status()
        except Exception as e:
            st.warning(f"API health status unavailable: {str(e)}")
        st.markdown("---")

        # Alert notifications in sidebar
        try:
            alert_panel = AlertPanel(
                st.session_state.alert_manager,
                st.session_state.agent_runtime
            )
            alert_panel.render_alert_notifications()
        except Exception:
            pass  # Silent fail for sidebar notifications

        st.markdown("---")
        _render_fundamental_analysis()

        st.markdown("---")
        _render_pattern_library()

        st.markdown("---")
        _render_graph_controls()

        st.markdown("---")
        _render_api_status()


def main():
    """Main Streamlit application entry point."""
    # Initialize system
    init_session_state()

    # Render header
    st.markdown("# DawsOS - Living Knowledge Graph Intelligence")
    st.markdown("*Every interaction makes me smarter*")

    # Render main tabs
    _render_main_tabs()

    # Render sidebar
    _render_sidebar()

if __name__ == "__main__":
    main()
