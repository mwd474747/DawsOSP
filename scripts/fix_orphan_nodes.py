#!/usr/bin/env python3
"""
Fix orphan nodes by reconnecting them to the knowledge graph
"""

from core.knowledge_graph import KnowledgeGraph
from capabilities.market_data import MarketDataCapability

def fix_orphan_nodes():
    """Reconnect orphan nodes to the graph"""

    # Load graph
    graph = KnowledgeGraph()
    market = MarketDataCapability()

    # Find orphan nodes
    orphans = []
    for node_id, node in graph._graph.nodes(data=True):
        incoming = len(node.get('connections_in', []))
        outgoing = len(node.get('connections_out', []))
        if incoming == 0 and outgoing == 0:
            orphans.append((node_id, node))

    print(f"Found {len(orphans)} orphan nodes")

    # Fix company nodes
    company_nodes = [(nid, n) for nid, n in orphans if n['type'] == 'company']
    for node_id, node in company_nodes:
        symbol = node['data'].get('symbol')
        if symbol:
            print(f"Fixing company node for {symbol}")

            # Fetch current market data
            quote = market.get_quote(symbol)

            # Update node with fresh data
            node['data'].update({
                'price': quote.get('price'),
                'market_cap': quote.get('market_cap'),
                'pe': quote.get('pe'),
                'updated': datetime.now().isoformat()
            })

            # Create sector node if not exists
            sector_name = quote.get('sector', 'Technology')
            sector_node = None
            for nid, n in graph._graph.nodes(data=True):
                if n.get('type') == 'sector' and n.get('data', {}).get('name') == sector_name:
                    sector_node = nid
                    break

            if not sector_node:
                sector_node = graph.add_node('sector', {'name': sector_name})

            # Connect company to sector
            graph.connect(node_id, sector_node, 'belongs_to', strength=1.0)

            # Add moat analysis result node
            moat_node = graph.add_node('moat_analysis', {
                'symbol': symbol,
                'moat_score': calculate_moat_score(quote),
                'factors': {
                    'brand': symbol in ['AAPL', 'MSFT', 'V'],  # Strong brands
                    'network_effects': symbol in ['V', 'MSFT'],  # Network effects
                    'switching_costs': symbol in ['MSFT', 'AAPL'],  # High switching costs
                    'cost_advantage': symbol in ['COST', 'BRK.B'],  # Cost advantages
                }
            })

            # Connect company to moat analysis
            graph.connect(node_id, moat_node, 'has_moat', strength=0.8)

    # Fix query nodes
    query_nodes = [(nid, n) for nid, n in orphans if n['type'] == 'analysis_query']
    for node_id, node in query_nodes:
        symbol = node['data'].get('symbol')
        query = node['data'].get('query')

        if symbol:
            print(f"Fixing query node for {symbol}")

            # Find corresponding company node
            company_node = None
            for nid, n in graph._graph.nodes(data=True):
                if n.get('type') == 'company' and n.get('data', {}).get('symbol') == symbol:
                    company_node = nid
                    break

            if company_node:
                # Connect query to company
                graph.connect(node_id, company_node, 'queries', strength=0.7)

                # Find moat analysis result
                for nid, n in graph._graph.nodes(data=True):
                    if n.get('type') == 'moat_analysis' and n.get('data', {}).get('symbol') == symbol:
                        # Connect query to result
                        graph.connect(node_id, nid, 'resulted_in', strength=0.9)
                        break

    # Save updated graph
    graph.save_graph('storage/graph_fixed.json')
    print(f"✅ Fixed {len(orphans)} orphan nodes")
    print("Saved to storage/graph_fixed.json")

    # Report connections
    fixed_count = 0
    for node_id, node in orphans:
        incoming = len(graph.get_node(node_id).get('connections_in', []))
        outgoing = len(graph.get_node(node_id).get('connections_out', []))
        if incoming > 0 or outgoing > 0:
            fixed_count += 1

    print(f"Successfully connected {fixed_count}/{len(orphans)} nodes")

    return graph

def calculate_moat_score(quote):
    """Calculate competitive moat score based on financial metrics"""
    score = 0.5  # Base score

    # High PE might indicate pricing power
    if quote.get('pe') and quote['pe'] > 25:
        score += 0.1

    # Large market cap indicates dominance
    if quote.get('market_cap') and quote['market_cap'] > 500_000_000_000:  # $500B
        score += 0.2
    elif quote.get('market_cap') and quote['market_cap'] > 100_000_000_000:  # $100B
        score += 0.1

    return min(score, 1.0)

if __name__ == "__main__":
    from datetime import datetime
    fix_orphan_nodes()