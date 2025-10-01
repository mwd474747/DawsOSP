#!/usr/bin/env python3
"""
Seed DawsOS with Buffett-Ackman-Dalio Investment Framework
This creates the hierarchical knowledge structure without changing any code
"""
import os
import json
from datetime import datetime

# Load environment
from load_env import load_env
load_env()

# Import components
from core.knowledge_graph import KnowledgeGraph
from core.agent_runtime import AgentRuntime
from agents.claude import Claude
from agents.graph_mind import GraphMind
from agents.data_harvester import DataHarvester
from agents.relationship_hunter import RelationshipHunter
from capabilities.fred import FREDCapability
from capabilities.market_data import MarketDataCapability

print("=" * 80)
print("SEEDING DawsOS WITH INVESTMENT MASTER FRAMEWORK")
print("Philosophy: Dalio (Regime) → Buffett (Quality) → Ackman (Opportunity)")
print("=" * 80)

# Initialize
graph = KnowledgeGraph()
runtime = AgentRuntime()
fred = FREDCapability()
market = MarketDataCapability()

# Register agents
runtime.register_agent('claude', Claude(graph))
runtime.register_agent('graph_mind', GraphMind(graph))
runtime.register_agent('data_harvester', DataHarvester(graph, {'fred': fred, 'market': market}))
runtime.register_agent('relationship_hunter', RelationshipHunter(graph))

print("\n📊 LEVEL 1: ECONOMIC MACHINE (Dalio Framework)")
print("-" * 80)

# Create master regime node
regime = graph.add_node('regime', {
    'name': 'ECONOMIC_REGIME',
    'description': 'Master node - current economic conditions',
    'importance': 'PRIMARY'
}, 'ECONOMIC_REGIME')
print(f"✅ Created master node: ECONOMIC_REGIME")

# Add current economic indicators
indicators = {
    'GDP': fred.get_latest('GDP'),
    'CPI': fred.get_latest('CPIAUCSL'),
    'UNEMPLOYMENT': fred.get_latest('UNRATE'),
    'FED_RATE': fred.get_latest('DFF'),
    'TREASURY_10Y': fred.get_latest('DGS10')
}

for name, data in indicators.items():
    if data and 'value' in data:
        node = graph.add_node('indicator', {
            'value': data['value'],
            'date': data['date'],
            'series': name
        }, name)

        # Connect to regime
        if name == 'GDP':
            graph.connect(name, 'ECONOMIC_REGIME', 'indicates_growth', 0.9)
        elif name == 'CPI':
            graph.connect(name, 'ECONOMIC_REGIME', 'indicates_inflation', 0.85)
        elif name == 'FED_RATE':
            graph.connect(name, 'ECONOMIC_REGIME', 'determines_liquidity', 0.9)

        print(f"✅ Added {name}: {data['value']} [{data['date']}]")

# Determine current regime
gdp_growth = indicators['GDP']['value'] if indicators['GDP'] else 0
inflation = indicators['CPI']['value'] if indicators['CPI'] else 0
fed_rate = indicators['FED_RATE']['value'] if indicators['FED_RATE'] else 0

# Simple regime classification
if gdp_growth > 28000 and inflation < 350 and fed_rate > 3:
    current_regime = "GOLDILOCKS"
    regime_description = "Moderate growth, controlled inflation, normalized rates"
elif gdp_growth > 28000 and inflation > 350:
    current_regime = "OVERHEATING"
    regime_description = "Strong growth, high inflation, tightening likely"
elif gdp_growth < 28000 and fed_rate < 2:
    current_regime = "RECESSION_RISK"
    regime_description = "Slow growth, accommodative policy"
else:
    current_regime = "TRANSITIONAL"
    regime_description = "Mixed signals, regime uncertain"

# Update regime node
regime_node = graph.nodes.get('ECONOMIC_REGIME')
if regime_node:
    regime_node['data']['current_state'] = current_regime
    regime_node['data']['description'] = regime_description
    print(f"\n📍 Current Regime: {current_regime}")
    print(f"   {regime_description}")

print("\n📈 LEVEL 2: RISK FRAMEWORK")
print("-" * 80)

# Create risk sentiment node
risk_node = graph.add_node('sentiment', {
    'name': 'RISK_SENTIMENT',
    'current': 'RISK_ON' if fed_rate < 5 else 'RISK_OFF'
}, 'RISK_SENTIMENT')

# Add VIX if available (using SPY volatility as proxy)
spy = market.get_quote('SPY')
if spy:
    spy_node = graph.add_node('index', {
        'symbol': 'SPY',
        'price': spy.get('price'),
        'change': spy.get('change_percent')
    }, 'SPY')

    graph.connect('RISK_SENTIMENT', 'SPY', 'drives', 0.8)
    print(f"✅ Added SPY (S&P 500): ${spy.get('price')}")

print("\n🏢 LEVEL 3: SECTOR ROTATION (Buffett Framework)")
print("-" * 80)

# Define sectors with current regime preferences
sectors = {
    'TECHNOLOGY': {'symbols': ['AAPL', 'MSFT', 'NVDA'], 'regime_fit': 'GOLDILOCKS'},
    'FINANCIALS': {'symbols': ['JPM', 'BAC', 'BRK.B'], 'regime_fit': 'GOLDILOCKS'},
    'HEALTHCARE': {'symbols': ['JNJ', 'UNH', 'PFE'], 'regime_fit': 'DEFENSIVE'},
    'CONSUMER_STAPLES': {'symbols': ['PG', 'KO', 'WMT'], 'regime_fit': 'DEFENSIVE'},
    'ENERGY': {'symbols': ['XOM', 'CVX'], 'regime_fit': 'INFLATION'},
}

for sector_name, sector_data in sectors.items():
    # Create sector node
    sector_node = graph.add_node('sector', {
        'name': sector_name,
        'regime_fit': sector_data['regime_fit'],
        'symbols': sector_data['symbols']
    }, sector_name)

    # Connect to regime
    strength = 0.8 if sector_data['regime_fit'] in current_regime else 0.4
    graph.connect('ECONOMIC_REGIME', sector_name, 'favors', strength)

    print(f"✅ Added sector: {sector_name} (Regime fit: {sector_data['regime_fit']})")

    # Add 1-2 stocks per sector for depth
    for symbol in sector_data['symbols'][:1]:  # Just first stock to avoid API limits
        quote = market.get_quote(symbol)
        if quote and 'price' in quote:
            stock_node = graph.add_node('stock', {
                'symbol': symbol,
                'price': quote.get('price'),
                'pe': quote.get('pe', 0),
                'market_cap': quote.get('market_cap', 0)
            }, symbol)

            # Connect to sector
            graph.connect(sector_name, symbol, 'contains', 0.9)

            # Buffett quality check
            if quote.get('pe') and quote.get('pe') < 20:
                graph.add_node('signal', {
                    'type': 'VALUE',
                    'target': symbol,
                    'reason': f"P/E {quote.get('pe')} < 20"
                }, f"{symbol}_VALUE")
                graph.connect(f"{symbol}_VALUE", symbol, 'signals', 0.7)
                print(f"   📍 {symbol}: ${quote.get('price')} (P/E: {quote.get('pe')}) - VALUE SIGNAL")
            else:
                print(f"   • {symbol}: ${quote.get('price')} (P/E: {quote.get('pe', 'N/A')})")

print("\n🔄 ESTABLISHING KEY RELATIONSHIPS")
print("-" * 80)

# Create critical market relationships
relationships = [
    ('GDP', 'CORPORATE_EARNINGS', 'drives', 0.85),
    ('CPI', 'VALUATIONS', 'pressures', -0.7),
    ('FED_RATE', 'RISK_SENTIMENT', 'influences', -0.6),
    ('RISK_SENTIMENT', 'TECHNOLOGY', 'favors', 0.8),
    ('UNEMPLOYMENT', 'FED_RATE', 'influences', -0.7)
]

created = 0
for from_node, to_node, rel_type, strength in relationships:
    if from_node in graph.nodes and to_node in graph.nodes:
        graph.connect(from_node, to_node, rel_type, strength)
        created += 1
        print(f"✅ {from_node} → {rel_type}({strength}) → {to_node}")

print(f"\nCreated {created} relationships")

print("\n📊 GRAPH STATISTICS")
print("-" * 80)

stats = graph.get_stats()
print(f"Total Nodes: {stats['total_nodes']}")
print(f"Total Edges: {stats['total_edges']}")
print(f"Node Types: {stats['node_types']}")

# Save the seeded graph
graph.save('storage/seeded_graph.json')
print(f"\n💾 Seeded graph saved to storage/seeded_graph.json")

print("\n🎯 ACTIONABLE INSIGHTS")
print("-" * 80)

# Run a forecast on SPY based on regime
if 'SPY' in graph.nodes:
    forecast = graph.forecast('SPY')
    print(f"\nSPY Forecast based on regime:")
    print(f"  Direction: {forecast.get('forecast', 'Unknown')}")
    print(f"  Confidence: {forecast.get('confidence', 0):.1%}")
    print(f"  Key Drivers: {forecast.get('influences', 0)} influences detected")

# Find value opportunities
value_signals = [node for node_id, node in graph.nodes.items()
                if node['type'] == 'signal' and node['data'].get('type') == 'VALUE']

if value_signals:
    print(f"\n💎 Value Opportunities Found:")
    for signal in value_signals:
        print(f"  • {signal['data'].get('target')}: {signal['data'].get('reason')}")

print("\n" + "=" * 80)
print("SEEDING COMPLETE")
print("=" * 80)
print("""
Next steps to build knowledge:
1. "What's the current regime?" - Analyzes economic conditions
2. "Show me value stocks" - Finds P/E < 20 with quality
3. "Which sectors for this regime?" - Returns favored sectors
4. "Add Warren Buffett's portfolio" - Expands quality universe
5. "Find activist opportunities" - Triggers Ackman-style analysis
""")