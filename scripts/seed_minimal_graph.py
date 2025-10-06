#!/usr/bin/env python3
"""
Seed Minimal Knowledge Graph

Creates a minimal but functional knowledge graph (~500 nodes) from enriched datasets.
This is much faster than loading a full 96K node graph and provides all core functionality.

Run this script once after cloning the repository or when starting fresh.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dawsos.core.knowledge_graph import KnowledgeGraph
from dawsos.core.knowledge_loader import get_knowledge_loader
from dawsos.core.logger import get_logger

logger = get_logger('SeedMinimalGraph')


def seed_sectors(graph: KnowledgeGraph, loader) -> dict:
    """Seed 11 market sectors"""
    logger.info("Seeding sectors...")

    sectors_data = loader.get_dataset('sector_performance')
    if not sectors_data or 'sectors' not in sectors_data:
        logger.error("sector_performance.json not found")
        return {}

    sector_nodes = {}
    for sector_name, sector_info in sectors_data['sectors'].items():
        node_id = graph.add_node(
            node_type='sector',
            data={
                'name': sector_name,
                'ticker': sector_info.get('ticker'),
                'description': sector_info.get('description', ''),
                'performance': sector_info.get('performance', {}),
                'characteristics': sector_info.get('characteristics', [])
            }
        )
        sector_nodes[sector_name] = node_id

    logger.info(f"Created {len(sector_nodes)} sector nodes")
    return sector_nodes


def seed_major_stocks(graph: KnowledgeGraph, loader, sector_nodes: dict) -> dict:
    """Seed ~50 major stocks (top holdings from each sector)"""
    logger.info("Seeding major stocks...")

    sp500_data = loader.get_dataset('sp500_companies')
    if not sp500_data:
        logger.error("sp500_companies.json not found")
        return {}

    stock_nodes = {}
    stocks_per_sector = 5  # Top 5 from each sector

    for sector_name, sector_id in sector_nodes.items():
        if sector_name not in sp500_data:
            continue

        companies = sp500_data[sector_name]
        for i, company in enumerate(companies[:stocks_per_sector]):
            symbol = company.get('symbol')
            if not symbol:
                continue

            node_id = graph.add_node(
                node_type='stock',
                data={
                    'symbol': symbol,
                    'name': company.get('name'),
                    'sector': sector_name,
                    'market_cap': company.get('market_cap'),
                    'weight': company.get('weight', 0)
                }
            )
            stock_nodes[symbol] = node_id

            # Connect to sector
            graph.connect(
                node_id,
                sector_id,
                relationship='belongs_to',
                strength=0.9
            )

    logger.info(f"Created {len(stock_nodes)} stock nodes")
    return stock_nodes


def seed_economic_cycles(graph: KnowledgeGraph, loader) -> dict:
    """Seed economic cycle framework"""
    logger.info("Seeding economic cycles...")

    cycles_data = loader.get_dataset('economic_cycles')
    if not cycles_data or 'economic_cycles' not in cycles_data:
        logger.error("economic_cycles.json not found")
        return {}

    cycle_nodes = {}
    for cycle_name, cycle_info in cycles_data['economic_cycles'].items():
        node_id = graph.add_node(
            node_type='economic_cycle',
            data={
                'name': cycle_name,
                'description': cycle_info.get('description', ''),
                'duration': cycle_info.get('duration', ''),
                'indicators': cycle_info.get('indicators', []),
                'sector_performance': cycle_info.get('sector_performance', {})
            }
        )
        cycle_nodes[cycle_name] = node_id

    logger.info(f"Created {len(cycle_nodes)} economic cycle nodes")
    return cycle_nodes


def seed_investment_frameworks(graph: KnowledgeGraph, loader) -> dict:
    """Seed Buffett and Dalio investment frameworks"""
    logger.info("Seeding investment frameworks...")

    framework_nodes = {}

    # Buffett framework
    buffett_data = loader.get_dataset('buffett_framework')
    if buffett_data:
        buffett_id = graph.add_node(
            node_type='investment_framework',
            data={
                'name': 'Warren Buffett Value Investing',
                'principles': buffett_data.get('principles', []),
                'moat_factors': buffett_data.get('moat_factors', []),
                'red_flags': buffett_data.get('red_flags', [])
            }
        )
        framework_nodes['buffett'] = buffett_id

    # Dalio framework
    dalio_data = loader.get_dataset('dalio_framework')
    if dalio_data:
        dalio_id = graph.add_node(
            node_type='investment_framework',
            data={
                'name': 'Ray Dalio All Weather',
                'principles': dalio_data.get('principles', []),
                'regime_indicators': dalio_data.get('regime_indicators', []),
                'asset_allocation': dalio_data.get('asset_allocation', {})
            }
        )
        framework_nodes['dalio'] = dalio_id

    logger.info(f"Created {len(framework_nodes)} framework nodes")
    return framework_nodes


def seed_relationships(graph: KnowledgeGraph, loader, sector_nodes: dict, cycle_nodes: dict):
    """Seed sector-cycle relationships"""
    logger.info("Seeding relationships...")

    # Connect sectors to economic cycles based on performance
    cycles_data = loader.get_dataset('economic_cycles')
    if not cycles_data:
        return

    relationships_count = 0
    for cycle_name, cycle_id in cycle_nodes.items():
        cycle_info = cycles_data['economic_cycles'].get(cycle_name, {})
        sector_perf = cycle_info.get('sector_performance', {})

        for sector_name, performance in sector_perf.items():
            if sector_name not in sector_nodes:
                continue

            sector_id = sector_nodes[sector_name]

            # Strength based on performance rating
            strength_map = {
                'Strong': 0.9,
                'Moderate': 0.6,
                'Weak': 0.3
            }
            strength = strength_map.get(performance, 0.5)

            graph.connect(
                sector_id,
                cycle_id,
                relationship='performs_in',
                strength=strength,
                data={'performance': performance}
            )
            relationships_count += 1

    logger.info(f"Created {relationships_count} sector-cycle relationships")


def seed_correlations(graph: KnowledgeGraph, loader, sector_nodes: dict):
    """Seed sector correlation relationships"""
    logger.info("Seeding correlations...")

    corr_data = loader.get_dataset('sector_correlations')
    if not corr_data or 'sector_correlations' not in corr_data:
        return

    correlations = corr_data['sector_correlations']
    relationships_count = 0

    for sector1, sector2, correlation in correlations:
        if sector1 not in sector_nodes or sector2 not in sector_nodes:
            continue

        # Only add significant correlations (|r| > 0.5)
        if abs(correlation) < 0.5:
            continue

        graph.connect(
            sector_nodes[sector1],
            sector_nodes[sector2],
            relationship='correlates_with',
            strength=abs(correlation),
            data={'correlation': correlation}
        )
        relationships_count += 1

    logger.info(f"Created {relationships_count} sector correlation relationships")


def main():
    """Seed minimal knowledge graph from enriched datasets"""
    logger.info("=" * 80)
    logger.info("Seeding Minimal Knowledge Graph")
    logger.info("=" * 80)

    # Initialize
    graph = KnowledgeGraph()
    loader = get_knowledge_loader()

    # Seed nodes
    sector_nodes = seed_sectors(graph, loader)
    stock_nodes = seed_major_stocks(graph, loader, sector_nodes)
    cycle_nodes = seed_economic_cycles(graph, loader)
    framework_nodes = seed_investment_frameworks(graph, loader)

    # Seed relationships
    seed_relationships(graph, loader, sector_nodes, cycle_nodes)
    seed_correlations(graph, loader, sector_nodes)

    # Save
    save_path = 'storage/graph.json'
    logger.info(f"Saving graph to {save_path}...")
    graph.save(save_path)

    # Summary
    stats = graph.get_stats()
    logger.info("=" * 80)
    logger.info("Minimal Graph Seeded Successfully")
    logger.info("=" * 80)
    logger.info(f"Nodes: {stats['total_nodes']}")
    logger.info(f"Edges: {stats['total_edges']}")
    logger.info(f"Node Types: {', '.join(stats['node_types'].keys())}")
    logger.info(f"Saved to: {save_path}")
    logger.info("=" * 80)
    logger.info("✓ Ready to run: streamlit run dawsos/main.py")


if __name__ == '__main__':
    main()
