#!/usr/bin/env python3
"""
Load Historical Market Data into Knowledge Graph

This script demonstrates how to bulk load historical data from APIs
and store it in the knowledge graph for future analysis.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dawsos.load_env import load_env
load_env()

from dawsos.core.knowledge_graph import KnowledgeGraph
from dawsos.capabilities.market_data import MarketDataCapability
from dawsos.capabilities.fred_data import FredDataCapability
from datetime import datetime, timedelta
import time
import json

def load_market_history(graph, market_capability, tickers, years=5):
    """Load historical price data for given tickers"""
    print(f"\n📈 Loading {years} years of market data for {len(tickers)} tickers...")

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365*years)).strftime('%Y-%m-%d')

    loaded_count = 0
    error_count = 0

    for ticker in tickers:
        try:
            print(f"  Fetching {ticker}...", end=' ')

            # Get historical data from FMP API
            historical = market_capability.get_historical_prices(
                ticker,
                start_date=start_date,
                end_date=end_date
            )

            if 'error' in historical:
                print(f"✗ Error: {historical['error']}")
                error_count += 1
                continue

            # Create company node if doesn't exist
            company_id = f"{ticker}_company"
            if company_id not in graph.nodes:
                graph.add_node('company', {
                    'ticker': ticker,
                    'name': ticker,
                    'data_source': 'FMP'
                }, node_id=company_id)

            # Store each historical data point
            data_points = historical.get('historical', [])
            for idx, point in enumerate(data_points):
                node_id = f"{ticker}_price_{point['date']}"

                graph.add_node('price_history', {
                    'ticker': ticker,
                    'date': point['date'],
                    'open': point['open'],
                    'high': point['high'],
                    'low': point['low'],
                    'close': point['close'],
                    'volume': point['volume'],
                    'change_percent': point.get('change_percent', 0)
                }, node_id=node_id)

                # Link to company
                graph.connect(company_id, node_id, 'has_price_data')

            loaded_count += 1
            print(f"✓ Loaded {len(data_points)} data points")

            # Rate limiting
            time.sleep(0.2)

        except Exception as e:
            print(f"✗ Error: {e}")
            error_count += 1

    print(f"\n✅ Loaded {loaded_count} tickers successfully, {error_count} errors")
    return loaded_count

def load_economic_history(graph, fred_capability, indicators, years=10):
    """Load historical economic indicators from FRED"""
    print(f"\n📊 Loading {years} years of economic data for {len(indicators)} indicators...")

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365*years)).strftime('%Y-%m-%d')

    loaded_count = 0

    for indicator_name, series_id in indicators.items():
        try:
            print(f"  Fetching {indicator_name} ({series_id})...", end=' ')

            # Get series data
            series_data = fred_capability.get_series(series_id, start_date, end_date)

            if 'error' in series_data:
                print(f"✗ Error: {series_data['error']}")
                continue

            observations = series_data.get('observations', [])

            if not observations:
                print(f"✗ No data available")
                continue

            # Create indicator node
            indicator_id = f"indicator_{series_id}"
            graph.add_node('economic_indicator', {
                'name': indicator_name,
                'series_id': series_id,
                'source': 'FRED',
                'frequency': series_data.get('frequency', 'unknown'),
                'units': series_data.get('units', 'unknown')
            }, node_id=indicator_id)

            # Store observations
            for obs in observations:
                obs_id = f"{series_id}_{obs['date']}"
                graph.add_node('indicator_observation', {
                    'series_id': series_id,
                    'indicator_name': indicator_name,
                    'date': obs['date'],
                    'value': obs['value']
                }, node_id=obs_id)

                graph.connect(indicator_id, obs_id, 'has_observation')

            loaded_count += 1
            print(f"✓ Loaded {len(observations)} observations")

            # Rate limiting
            time.sleep(0.1)

        except Exception as e:
            print(f"✗ Error: {e}")

    print(f"\n✅ Loaded {loaded_count} indicators successfully")
    return loaded_count

def load_company_fundamentals(graph, market_capability, tickers):
    """Load company fundamental data"""
    print(f"\n💼 Loading fundamental data for {len(tickers)} companies...")

    loaded_count = 0

    for ticker in tickers:
        try:
            print(f"  Fetching {ticker} fundamentals...", end=' ')

            # Get key metrics
            metrics = market_capability.get_key_metrics(ticker, period='annual')

            if 'error' in metrics or not metrics:
                print(f"✗ No data")
                continue

            # Store latest metrics
            latest_metrics = metrics[0] if isinstance(metrics, list) and metrics else metrics

            # Create/update company node
            company_id = f"{ticker}_company"
            if company_id in graph.nodes:
                # Update existing
                graph.nodes[company_id]['properties'].update({
                    'market_cap': latest_metrics.get('marketCap'),
                    'pe_ratio': latest_metrics.get('peRatio'),
                    'revenue': latest_metrics.get('revenue'),
                    'net_income': latest_metrics.get('netIncome'),
                    'roic': latest_metrics.get('roic'),
                    'roe': latest_metrics.get('roe'),
                    'debt_to_equity': latest_metrics.get('debtToEquity'),
                    'last_updated': datetime.now().isoformat()
                })
            else:
                graph.add_node('company', {
                    'ticker': ticker,
                    'market_cap': latest_metrics.get('marketCap'),
                    'pe_ratio': latest_metrics.get('peRatio'),
                    'revenue': latest_metrics.get('revenue'),
                    'net_income': latest_metrics.get('netIncome'),
                    'roic': latest_metrics.get('roic'),
                    'roe': latest_metrics.get('roe'),
                    'debt_to_equity': latest_metrics.get('debtToEquity'),
                    'last_updated': datetime.now().isoformat()
                }, node_id=company_id)

            loaded_count += 1
            print(f"✓ Loaded")

            time.sleep(0.2)

        except Exception as e:
            print(f"✗ Error: {e}")

    print(f"\n✅ Loaded {loaded_count} company fundamentals")
    return loaded_count

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("📦 DawsOS Historical Data Loader")
    print("="*60)

    # Initialize
    graph = KnowledgeGraph()
    market = MarketDataCapability()
    fred = FredDataCapability()

    # Check API keys
    print("\n🔑 API Status:")
    print(f"  FMP API: {'✓ Configured' if market.api_key else '✗ Missing - set FMP_API_KEY in .env'}")
    print(f"  FRED API: {'✓ Configured' if fred.api_key else '✗ Missing - set FRED_API_KEY in .env'}")

    if not market.api_key or not fred.api_key:
        print("\n⚠️  Missing API keys. Configure them in dawsos/.env to proceed.")
        return

    # Try to load existing graph
    if os.path.exists('dawsos/storage/graph.json'):
        try:
            graph.load('dawsos/storage/graph.json')
            print(f"\n📂 Loaded existing graph: {graph.get_stats()['total_nodes']} nodes")
        except Exception as e:
            print(f"\n⚠️  Could not load existing graph: {e}")

    # Define what to load
    tickers = [
        # Major ETFs
        'SPY', 'QQQ', 'DIA', 'IWM',
        # Tech
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA',
        # Finance
        'JPM', 'BAC', 'WFC', 'GS',
        # Healthcare
        'JNJ', 'UNH', 'PFE', 'ABBV',
        # Consumer
        'WMT', 'HD', 'MCD', 'NKE', 'SBUX',
        # Energy
        'XOM', 'CVX',
        # Industrial
        'BA', 'CAT', 'GE'
    ]

    economic_indicators = {
        'GDP': 'GDP',
        'CPI': 'CPIAUCSL',
        'Unemployment': 'UNRATE',
        'Fed Funds Rate': 'FEDFUNDS',
        '10Y Treasury': 'DGS10',
        '2Y Treasury': 'DGS2',
        'VIX': 'VIXCLS',
        'M2 Money Supply': 'M2SL',
        'Industrial Production': 'INDPRO',
        'Retail Sales': 'RSXFS'
    }

    # Load data
    total_loaded = 0

    # 1. Load market history
    if input("\n📈 Load 5 years of price history? (y/n): ").lower() == 'y':
        total_loaded += load_market_history(graph, market, tickers, years=5)

    # 2. Load economic data
    if input("\n📊 Load 10 years of economic indicators? (y/n): ").lower() == 'y':
        total_loaded += load_economic_history(graph, fred, economic_indicators, years=10)

    # 3. Load fundamentals
    if input("\n💼 Load company fundamentals? (y/n): ").lower() == 'y':
        total_loaded += load_company_fundamentals(graph, market, tickers)

    # Save graph
    if total_loaded > 0:
        print("\n💾 Saving knowledge graph...")
        try:
            graph.save('dawsos/storage/graph_with_historical.json')
            print(f"✅ Saved graph with {graph.get_stats()['total_nodes']} nodes")
            print(f"   Location: dawsos/storage/graph_with_historical.json")

            # Also save to default location
            if input("\n📝 Replace default graph.json? (y/n): ").lower() == 'y':
                graph.save('dawsos/storage/graph.json')
                print("✅ Updated default graph.json")
        except Exception as e:
            print(f"✗ Error saving graph: {e}")

    print("\n" + "="*60)
    print("✨ Data loading complete!")
    print("="*60)
    print(f"\nFinal graph statistics:")
    stats = graph.get_stats()
    print(f"  Total Nodes: {stats['total_nodes']}")
    print(f"  Total Edges: {stats['total_edges']}")
    print(f"  Node Types: {len(stats['node_types'])}")
    print("\n🚀 Your knowledge graph is ready for analysis!")

if __name__ == '__main__':
    main()
