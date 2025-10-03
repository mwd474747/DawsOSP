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

def init_session_state():
    """Initialize session state variables"""
    if 'graph' not in st.session_state:
        st.session_state.graph = KnowledgeGraph()

        # First, try to load existing graph
        loaded_from_file = False
        if os.path.exists('storage/graph.json'):
            try:
                st.session_state.graph.load('storage/graph.json')
                loaded_from_file = True
                print(f"Loaded graph with {st.session_state.graph.get_stats()['total_nodes']} nodes from file")
            except Exception as e:
                print(f"Error loading graph: {e}")

        # Then seed with fundamental analysis knowledge if not enough nodes
        # This ensures we always have the base knowledge
        if st.session_state.graph.get_stats()['total_nodes'] < 40:
            try:
                import seed_knowledge_graph
                seed_knowledge_graph.seed_buffett_framework(st.session_state.graph)
                seed_knowledge_graph.seed_dalio_framework(st.session_state.graph)
                seed_knowledge_graph.seed_financial_calculations(st.session_state.graph)
                seed_knowledge_graph.seed_investment_examples(st.session_state.graph)
                print(f"Seeded knowledge graph to {st.session_state.graph.get_stats()['total_nodes']} nodes")

                # Save the seeded graph for next time
                st.session_state.graph.save('storage/graph.json')
            except Exception as e:
                print(f"Note: Knowledge seeding skipped: {e}")

    # Initialize capabilities FIRST (before agent_runtime that uses it)
    if 'capabilities' not in st.session_state:
        st.session_state.capabilities = {
            'fred': FredDataCapability(),  # Use our improved FRED capability
            'market': MarketDataCapability(),
            'news': NewsCapability(),
            'crypto': CryptoCapability(),
            'fundamentals': FundamentalsCapability()
        }

    if 'agent_runtime' not in st.session_state:
        # Initialize agent runtime
        st.session_state.agent_runtime = AgentRuntime()

        # Now capabilities exists and can be used
        caps = st.session_state.capabilities

        # Register agents with explicit capabilities
        runtime = st.session_state.agent_runtime
        runtime.register_agent(
            'graph_mind',
            GraphMind(st.session_state.graph),
            capabilities=AGENT_CAPABILITIES['graph_mind']
        )
        runtime.register_agent(
            'claude',
            Claude(st.session_state.graph),
            capabilities=AGENT_CAPABILITIES['claude']
        )
        runtime.register_agent(
            'data_harvester',
            DataHarvester(st.session_state.graph, caps),
            capabilities=AGENT_CAPABILITIES['data_harvester']
        )
        runtime.register_agent(
            'data_digester',
            DataDigester(st.session_state.graph),
            capabilities=AGENT_CAPABILITIES['data_digester']
        )
        runtime.register_agent(
            'relationship_hunter',
            RelationshipHunter(st.session_state.graph, capabilities=caps),
            capabilities=AGENT_CAPABILITIES['relationship_hunter']
        )
        runtime.register_agent(
            'pattern_spotter',
            PatternSpotter(st.session_state.graph),
            capabilities=AGENT_CAPABILITIES['pattern_spotter']
        )
        runtime.register_agent(
            'forecast_dreamer',
            ForecastDreamer(st.session_state.graph),
            capabilities=AGENT_CAPABILITIES['forecast_dreamer']
        )
        runtime.register_agent(
            'code_monkey',
            CodeMonkey(st.session_state.graph),
            capabilities=AGENT_CAPABILITIES['code_monkey']
        )
        runtime.register_agent(
            'structure_bot',
            StructureBot(st.session_state.graph),
            capabilities=AGENT_CAPABILITIES['structure_bot']
        )
        runtime.register_agent(
            'refactor_elf',
            RefactorElf(st.session_state.graph),
            capabilities=AGENT_CAPABILITIES['refactor_elf']
        )
        runtime.register_agent(
            'workflow_recorder',
            WorkflowRecorder(st.session_state.graph),
            capabilities=AGENT_CAPABILITIES['workflow_recorder']
        )
        runtime.register_agent(
            'workflow_player',
            WorkflowPlayer(st.session_state.graph),
            capabilities=AGENT_CAPABILITIES['workflow_player']
        )
        runtime.register_agent(
            'ui_generator',
            UIGeneratorAgent(st.session_state.graph),
            capabilities=AGENT_CAPABILITIES['ui_generator']
        )
        runtime.register_agent(
            'financial_analyst',
            FinancialAnalyst(st.session_state.graph),
            capabilities=AGENT_CAPABILITIES['financial_analyst']
        )
        runtime.register_agent(
            'governance_agent',
            GovernanceAgent(st.session_state.graph),
            capabilities=AGENT_CAPABILITIES['governance_agent']
        )

        # Initialize PatternEngine after agents are registered
        runtime.pattern_engine = PatternEngine(
            'dawsos/patterns',
            runtime=runtime,
            graph=st.session_state.graph
        )
        print(f"PatternEngine initialized with {len(runtime.pattern_engine.patterns)} patterns")

    # Initialize Universal Executor AFTER agent_runtime
    if 'executor' not in st.session_state:
        st.session_state.executor = UniversalExecutor(
            st.session_state.graph,
            st.session_state.agent_runtime.agent_registry,
            runtime=st.session_state.agent_runtime
        )
        print("Universal Executor initialized - ALL execution now routes through Trinity path")
        # Share executor with runtime for centralized orchestration
        st.session_state.agent_runtime.executor = st.session_state.executor

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'workflows' not in st.session_state:
        st.session_state.workflows = InvestmentWorkflows(
            st.session_state.agent_runtime,
            st.session_state.graph
        )
        
    if 'persistence' not in st.session_state:
        st.session_state.persistence = PersistenceManager()

    # Initialize alert manager
    if 'alert_manager' not in st.session_state:
        st.session_state.alert_manager = AlertManager()
        # Create default alerts
        st.session_state.alert_manager.create_template_alert(
            'compliance_violation',
            threshold=0
        )

def visualize_graph():
    """Create interactive graph visualization"""
    graph = st.session_state.graph
    
    # Create NetworkX graph
    G = nx.DiGraph()
    
    # Add nodes
    for node_id, node_data in graph.nodes.items():
        G.add_node(node_id, **node_data)
    
    # Add edges
    for edge in graph.edges:
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
        edge_data = graph.edges[0]  # Get actual edge data
        
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
        node_data = graph.nodes[node]
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

def display_chat_interface():
    """Main chat interface with Claude"""
    st.markdown("### Chat with DawsOS")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["content"])
            else:
                if isinstance(message["content"], dict):
                    # Display pattern-based responses
                    if 'pattern' in message["content"]:
                        st.caption(f"🔮 Pattern: {message['content'].get('pattern', 'Unknown')}")

                    if 'formatted_response' in message["content"]:
                        st.write(message["content"]['formatted_response'])
                    elif 'response' in message["content"]:
                        st.write(message["content"]['response'])
                    elif 'results' in message["content"]:
                        for result in message["content"]['results']:
                            if isinstance(result, dict):
                                if result.get('action') == 'explain':
                                    st.write(result.get('text', ''))
                                elif result.get('action') == 'forecast':
                                    forecast = result.get('result', {})
                                    col1, col2, col3 = st.columns(3)
                                    col1.metric("Forecast", forecast.get('forecast', 'Unknown'))
                                    col2.metric("Confidence", f"{forecast.get('confidence', 0)*100:.1f}%")
                                    col3.metric("Signal", f"{forecast.get('signal_strength', 0):.2f}")
                                elif result.get('action') == 'add_node':
                                    st.success(f"Added node: {result.get('node_id')}")
                                elif result.get('action') == 'connect':
                                    st.info(f"Connected: {result.get('from')} to {result.get('to')}")
                                elif 'error' in result:
                                    st.error(f"Error: {result['error']}")
                                elif 'response' in result:
                                    st.write(result['response'])
                    elif 'friendly_response' in message["content"]:
                        st.write(message["content"]['friendly_response'])
                    else:
                        st.json(message["content"])
                else:
                    st.write(message["content"])
    
    # Chat input
    user_input = st.chat_input("Ask anything about markets, economics, or stocks...")
    
    if user_input:
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Get response from agent system
        with st.chat_message("assistant"):
            with st.spinner("DawsOS is thinking..."):
                response = st.session_state.agent_runtime.orchestrate(user_input)
                
                # Display response
                if 'error' in response:
                    st.error(f"Error: {response['error']}")
                else:
                    # Display pattern-based response
                    if 'pattern' in response:
                        st.caption(f"🔮 Pattern: {response.get('pattern', 'Unknown')}")

                    if 'formatted_response' in response:
                        st.write(response['formatted_response'])
                    elif 'response' in response:
                        st.write(response['response'])
                    elif 'results' in response and response['results']:
                        # Display results from pattern execution
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

                    st.session_state.chat_history.append({"role": "assistant", "content": response})

                    # Save graph after changes
                    st.session_state.graph.save('storage/graph.json')

                    # Force rerun to update graph
                    st.rerun()

def display_intelligence_dashboard():
    """Display key metrics and insights"""
    graph = st.session_state.graph
    stats = graph.get_stats()

    # Display real market data at top
    st.markdown("### 📊 Market Overview")

    market = st.session_state.capabilities.get('market')
    if market:
        # Get major indices
        indices = ['SPY', 'QQQ', 'DIA', 'IWM']
        cols = st.columns(len(indices))

        for i, symbol in enumerate(indices):
            quote = market.get_quote(symbol)
            if 'error' not in quote:
                with cols[i]:
                    change = quote.get('change_percent', 0)
                    color = "green" if change >= 0 else "red"
                    st.metric(
                        symbol,
                        f"${quote.get('price', 0):.2f}",
                        f"{change:.2f}%",
                        delta_color="normal" if change >= 0 else "inverse"
                    )

    st.markdown("### 🧠 Knowledge Graph Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Nodes", stats['total_nodes'])
        st.caption("Knowledge entities")

    with col2:
        st.metric("Total Edges", stats['total_edges'])
        st.caption("Relationships")

    with col3:
        st.metric("Patterns", len(graph.patterns))
        st.caption("Discovered patterns")

    with col4:
        avg_conn = stats.get('avg_connections', 0)
        st.metric("Avg Connections", f"{avg_conn:.2f}")
        st.caption("Network density")
    
    # Node type distribution
    st.markdown("#### Node Distribution")
    if stats['node_types']:
        df_nodes = pd.DataFrame(
            list(stats['node_types'].items()),
            columns=['Type', 'Count']
        )
        st.bar_chart(df_nodes.set_index('Type'))
    
    # Recent patterns
    st.markdown("#### Recent Patterns")
    if graph.patterns:
        for pattern_id, pattern in list(graph.patterns.items())[:5]:
            with st.expander(f"{pattern.get('name', pattern_id)}"):
                st.write(f"Type: {pattern.get('type')}")
                st.write(f"Strength: {pattern.get('strength', 'N/A')}")
                st.write(f"Discovered: {pattern.get('discovered', 'Unknown')}")

def display_market_data():
    """Display live market data"""
    st.markdown("### Market Data")
    
    market = st.session_state.capabilities['market']
    
    # Quick quote lookup
    col1, col2 = st.columns([3, 1])
    with col1:
        symbol = st.text_input("Enter symbol:", value="AAPL")
    with col2:
        if st.button("Get Quote"):
            quote = market.get_quote(symbol)
            if 'error' not in quote:
                st.success(f"Added {symbol} to graph")
                # Add to graph
                node_id = st.session_state.graph.add_node(
                    'stock',
                    {'ticker': symbol, 'price': quote['price']},
                    node_id=symbol
                )
    
    # Market movers
    tab1, tab2, tab3 = st.tabs(["Gainers", "Losers", "Most Active"])
    
    with tab1:
        gainers = market.get_market_movers('gainers')
        if gainers and not any('error' in g for g in gainers):
            df_gainers = pd.DataFrame(gainers[:10])
            st.dataframe(df_gainers, hide_index=True)
    
    with tab2:
        losers = market.get_market_movers('losers')
        if losers and not any('error' in l for l in losers):
            df_losers = pd.DataFrame(losers[:10])
            st.dataframe(df_losers, hide_index=True)
    
    with tab3:
        actives = market.get_market_movers('actives')
        if actives and not any('error' in a for a in actives):
            df_actives = pd.DataFrame(actives[:10])
            st.dataframe(df_actives, hide_index=True)

def display_economic_indicators():
    """Display economic indicators with real FRED data"""
    st.markdown("### 📊 Economic Dashboard")

    fred = st.session_state.capabilities.get('fred')
    if not fred:
        st.warning("Economic data not available - set FRED_API_KEY")
        return

    # Main economic indicators
    st.markdown("#### Key Economic Indicators")

    indicators = ['GDP', 'CPI', 'UNEMPLOYMENT', 'FED_FUNDS']
    cols = st.columns(len(indicators))

    for i, indicator in enumerate(indicators):
        with cols[i]:
            data = fred.get_latest(indicator)
            if data and 'error' not in data:
                value = data.get('value', 0)
                change = data.get('change', 0)
                trend = data.get('trend', 'stable')
                date = data.get('date', 'N/A')

                # Format values appropriately
                if value is not None:
                    if indicator in ['GDP', 'CPI', 'UNEMPLOYMENT']:
                        display_value = f"{value:.1f}%"
                    else:
                        display_value = f"{value:.2f}%"
                else:
                    display_value = "N/A"

                # Determine delta color
                if indicator == 'UNEMPLOYMENT':
                    delta_color = "inverse"  # Lower is better
                elif indicator == 'GDP':
                    delta_color = "normal"   # Higher is better
                else:
                    delta_color = "off"      # Neutral

                st.metric(
                    indicator.replace('_', ' '),
                    display_value,
                    f"{change:+.2f}",
                    delta_color=delta_color
                )
                st.caption(f"{trend.capitalize()} • {date}")

def main():
    """Main application"""
    # Initialize
    init_session_state()
    
    # Header
    st.markdown("# DawsOS - Living Knowledge Graph Intelligence")
    st.markdown("*Every interaction makes me smarter*")
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
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
        "Alerts"
    ])
    
    # Initialize Trinity dashboard tabs
    try:
        trinity_tabs = get_trinity_dashboard_tabs(
            st.session_state.agent_runtime.pattern_engine,
            st.session_state.agent_runtime,
            st.session_state.graph
        )
    except Exception as e:
        st.error(f"Failed to initialize Trinity tabs: {str(e)}")
        trinity_tabs = None

    with tab1:
        if trinity_tabs:
            trinity_tabs.render_trinity_chat_interface()
        else:
            display_chat_interface()

    with tab2:
        if trinity_tabs:
            trinity_tabs.render_trinity_knowledge_graph()
        else:
            # Fallback to original implementation
            st.markdown("### Living Knowledge Graph")
            if st.session_state.graph.nodes:
                fig = visualize_graph()
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Start chatting to build the knowledge graph!")
            stats = st.session_state.graph.get_stats()
            st.json(stats)

    with tab3:
        if trinity_tabs:
            trinity_tabs.render_trinity_dashboard()
        else:
            display_intelligence_dashboard()

    with tab4:
        if trinity_tabs:
            trinity_tabs.render_trinity_markets()
        else:
            display_market_data()

    with tab5:
        if trinity_tabs:
            trinity_tabs.render_trinity_economy()
        else:
            display_economic_indicators()

    with tab6:
        if trinity_tabs:
            trinity_tabs.render_trinity_workflows()
        else:
            render_workflows_tab(
                st.session_state.workflows,
                st.session_state.graph,
                st.session_state.agent_runtime
            )

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
            st.markdown("- 🔧 Quick template-based alert creation")

    # Sidebar
    with st.sidebar:
        st.markdown("### Quick Actions")

        # Alert notifications in sidebar
        try:
            alert_panel = AlertPanel(
                st.session_state.alert_manager,
                st.session_state.agent_runtime
            )
            alert_panel.render_alert_notifications()
        except Exception:
            pass  # Silent fail for sidebar notifications
        
        if st.button("Analyze Macro Environment"):
            # Add user message to chat
            user_msg = "Show me macro analysis"
            st.session_state.chat_history.append({"role": "user", "content": user_msg})

            # Get response
            response = st.session_state.agent_runtime.orchestrate(user_msg)

            # Add assistant response to chat
            st.session_state.chat_history.append({"role": "assistant", "content": response})

            # Show brief feedback
            st.success("Analysis complete! Check the chat tab.")
            st.rerun()

        if st.button("Detect Market Regime"):
            # Add user message to chat
            user_msg = "Detect the market regime"
            st.session_state.chat_history.append({"role": "user", "content": user_msg})

            # Get response
            response = st.session_state.agent_runtime.orchestrate(user_msg)

            # Add assistant response to chat
            st.session_state.chat_history.append({"role": "assistant", "content": response})

            # Show brief feedback
            st.success("Regime detected! Check the chat tab.")
            st.rerun()

        if st.button("Find Patterns"):
            # Add user message to chat
            user_msg = "Show sector performance"
            st.session_state.chat_history.append({"role": "user", "content": user_msg})

            # Get response
            response = st.session_state.agent_runtime.orchestrate(user_msg)

            # Add assistant response to chat
            st.session_state.chat_history.append({"role": "assistant", "content": response})

            # Show brief feedback
            st.success("Patterns discovered! Check the chat tab.")
            st.rerun()

        if st.button("Hunt Relationships"):
            # Add user message to chat
            user_msg = "Find correlations for SPY"
            st.session_state.chat_history.append({"role": "user", "content": user_msg})

            # Get response
            response = st.session_state.agent_runtime.orchestrate(user_msg)

            # Add assistant response to chat
            st.session_state.chat_history.append({"role": "assistant", "content": response})

            # Show brief feedback
            st.success("Relationships found! Check the chat tab.")
            st.rerun()
        
        st.markdown("---")

        # Fundamental Analysis section
        st.markdown("### Fundamental Analysis")

        if st.button("🏰 Analyze Moat"):
            user_msg = "Analyze economic moat for AAPL"
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            response = st.session_state.agent_runtime.orchestrate(user_msg)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.success("Moat analysis complete!")
            st.rerun()

        if st.button("✅ Buffett Checklist"):
            user_msg = "Run Buffett checklist for MSFT"
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            response = st.session_state.agent_runtime.orchestrate(user_msg)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.success("Checklist complete!")
            st.rerun()

        if st.button("💰 Owner Earnings"):
            user_msg = "Calculate owner earnings"
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            response = st.session_state.agent_runtime.orchestrate(user_msg)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.success("Calculation complete!")
            st.rerun()

        if st.button("🔄 Debt Cycle"):
            user_msg = "Where are we in the debt cycle?"
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            response = st.session_state.agent_runtime.orchestrate(user_msg)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.success("Cycle analysis complete!")
            st.rerun()

        st.markdown("---")

        # Pattern Browser
        st.markdown("### Available Patterns")
        if hasattr(st.session_state.agent_runtime, 'pattern_engine'):
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

        st.markdown("---")

        # Graph controls
        st.markdown("### Graph Controls")
        
        if st.button("Save Graph"):
            st.session_state.graph.save('storage/graph.json')
            st.success("Graph saved!")
            
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
        
        # API Status
        st.markdown("---")
        st.markdown("### API Status")
        
        # Check API keys
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

if __name__ == "__main__":
    main()
