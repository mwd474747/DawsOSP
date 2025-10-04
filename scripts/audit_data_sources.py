#!/usr/bin/env python3
"""
Audit Data Sources - Check Real vs Mock Data

This script audits the DawsOS system to identify:
- Which APIs are configured and working
- How much real vs placeholder data exists
- Data quality metrics
- Recommendations for improvement
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dawsos.load_env import load_env
load_env()

from dawsos.core.knowledge_graph import KnowledgeGraph
from dawsos.capabilities.market_data import MarketDataCapability
from dawsos.capabilities.fred_data import FredDataCapability
from dawsos.capabilities.news import NewsCapability
from datetime import datetime
import json

def check_api_status():
    """Check API connectivity and configuration"""
    print("\n" + "="*60)
    print("🔑 API Configuration & Connectivity")
    print("="*60)

    market = MarketDataCapability()
    fred = FredDataCapability()
    news = NewsCapability()

    results = {
        'apis': {},
        'all_configured': True
    }

    # FMP API
    print("\n📈 FMP API (Financial Modeling Prep):")
    if market.api_key:
        print(f"  ✓ API Key Configured: {market.api_key[:8]}...{market.api_key[-4:]}")
        try:
            quote = market.get_quote('SPY')
            if 'error' not in quote and 'price' in quote:
                print(f"  ✓ API Call Success: SPY = ${quote['price']}")
                results['apis']['fmp'] = {'status': 'working', 'test_result': 'success'}
            else:
                print(f"  ✗ API Call Failed: {quote.get('error', 'Unknown error')}")
                results['apis']['fmp'] = {'status': 'configured', 'test_result': 'failed'}
        except Exception as e:
            print(f"  ✗ API Call Error: {e}")
            results['apis']['fmp'] = {'status': 'error', 'test_result': str(e)}
    else:
        print("  ✗ API Key Missing - Set FMP_API_KEY in dawsos/.env")
        results['apis']['fmp'] = {'status': 'missing'}
        results['all_configured'] = False

    # FRED API
    print("\n📊 FRED API (Federal Reserve Economic Data):")
    if fred.api_key:
        print(f"  ✓ API Key Configured: {fred.api_key[:8]}...{fred.api_key[-4:]}")
        try:
            gdp = fred.get_latest('GDP')
            if gdp.get('value'):
                print(f"  ✓ API Call Success: GDP = {gdp['value']} (latest)")
                results['apis']['fred'] = {'status': 'working', 'test_result': 'success'}
            else:
                print(f"  ✗ API Call Failed: No data returned")
                results['apis']['fred'] = {'status': 'configured', 'test_result': 'failed'}
        except Exception as e:
            print(f"  ✗ API Call Error: {e}")
            results['apis']['fred'] = {'status': 'error', 'test_result': str(e)}
    else:
        print("  ✗ API Key Missing - Set FRED_API_KEY in dawsos/.env")
        results['apis']['fred'] = {'status': 'missing'}
        results['all_configured'] = False

    # NewsAPI
    print("\n📰 NewsAPI:")
    if news.api_key:
        print(f"  ✓ API Key Configured: {news.api_key[:8]}...{news.api_key[-4:]}")
        try:
            headlines = news.get_headlines(category='business')
            if 'error' not in headlines and headlines.get('articles'):
                print(f"  ✓ API Call Success: {len(headlines['articles'])} articles")
                results['apis']['news'] = {'status': 'working', 'test_result': 'success'}
            else:
                print(f"  ✗ API Call Failed: {headlines.get('error', 'No articles')}")
                results['apis']['news'] = {'status': 'configured', 'test_result': 'failed'}
        except Exception as e:
            print(f"  ✗ API Call Error: {e}")
            results['apis']['news'] = {'status': 'error', 'test_result': str(e)}
    else:
        print("  ✗ API Key Missing - Set NEWSAPI_KEY in dawsos/.env")
        results['apis']['news'] = {'status': 'missing'}
        results['all_configured'] = False

    return results

def audit_knowledge_graph():
    """Audit knowledge graph for data quality"""
    print("\n" + "="*60)
    print("🕸️  Knowledge Graph Data Quality Audit")
    print("="*60)

    graph = KnowledgeGraph()

    # Try to load existing graph
    if os.path.exists('dawsos/storage/graph.json'):
        try:
            graph.load('dawsos/storage/graph.json')
            print(f"\n✓ Loaded graph from: dawsos/storage/graph.json")
        except Exception as e:
            print(f"\n✗ Error loading graph: {e}")
            return None
    else:
        print("\n⚠️  No saved graph found at dawsos/storage/graph.json")
        return None

    stats = graph.get_stats()

    print(f"\n📊 Graph Statistics:")
    print(f"  Total Nodes: {stats['total_nodes']:,}")
    print(f"  Total Edges: {stats['total_edges']:,}")
    print(f"  Node Types: {len(stats['node_types'])}")

    print(f"\n📋 Node Types Breakdown:")
    for node_type, count in sorted(stats['node_types'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {node_type:20} {count:>6,} nodes")

    # Check for placeholder/mock data
    print(f"\n🔍 Data Quality Analysis:")

    placeholder_indicators = [
        'unavailable',
        'Data Pending',
        'placeholder',
        'Analysis Required',
        'FRED API required',
        'mock',
        'fake',
        'sample'
    ]

    placeholder_nodes = []
    real_data_nodes = []
    api_sourced_nodes = []

    for node_id, node_data in graph.nodes.items():
        props = node_data.get('properties', {})
        node_text = json.dumps(props).lower()

        # Check for placeholder indicators
        has_placeholder = any(indicator.lower() in node_text for indicator in placeholder_indicators)

        if has_placeholder:
            placeholder_nodes.append({
                'id': node_id,
                'type': node_data.get('type'),
                'issue': 'Contains placeholder data'
            })
        else:
            real_data_nodes.append(node_id)

        # Check for API-sourced data
        if any(source in node_text for source in ['fmp', 'fred', 'newsapi', 'api']):
            api_sourced_nodes.append(node_id)

    total_nodes = len(graph.nodes)
    placeholder_count = len(placeholder_nodes)
    real_count = len(real_data_nodes)
    api_count = len(api_sourced_nodes)

    print(f"  Real Data Nodes:        {real_count:>6,} ({real_count/total_nodes*100:.1f}%)")
    print(f"  Placeholder Data Nodes: {placeholder_count:>6,} ({placeholder_count/total_nodes*100:.1f}%)")
    print(f"  API-Sourced Nodes:      {api_count:>6,} ({api_count/total_nodes*100:.1f}%)")

    if placeholder_count > 0:
        print(f"\n⚠️  Found {placeholder_count} nodes with placeholder data:")
        for node in placeholder_nodes[:10]:  # Show first 10
            print(f"    - {node['id']} ({node['type']}): {node['issue']}")
        if placeholder_count > 10:
            print(f"    ... and {placeholder_count - 10} more")

    # Data freshness check
    print(f"\n📅 Data Freshness:")
    recent_nodes = 0
    stale_nodes = 0
    no_timestamp_nodes = 0
    now = datetime.now()

    for node_id, node_data in graph.nodes.items():
        props = node_data.get('properties', {})
        timestamp = props.get('last_updated') or props.get('date') or props.get('timestamp')

        if timestamp:
            try:
                node_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                age_days = (now - node_date).days

                if age_days <= 7:
                    recent_nodes += 1
                else:
                    stale_nodes += 1
            except:
                no_timestamp_nodes += 1
        else:
            no_timestamp_nodes += 1

    print(f"  Recent (<7 days):       {recent_nodes:>6,} ({recent_nodes/total_nodes*100:.1f}%)")
    print(f"  Stale (>7 days):        {stale_nodes:>6,} ({stale_nodes/total_nodes*100:.1f}%)")
    print(f"  No Timestamp:           {no_timestamp_nodes:>6,} ({no_timestamp_nodes/total_nodes*100:.1f}%)")

    return {
        'total_nodes': total_nodes,
        'real_data_pct': real_count/total_nodes*100 if total_nodes > 0 else 0,
        'placeholder_count': placeholder_count,
        'api_sourced_count': api_count,
        'recent_nodes': recent_nodes
    }

def generate_recommendations(api_results, graph_results):
    """Generate recommendations for improving data quality"""
    print("\n" + "="*60)
    print("💡 Recommendations")
    print("="*60)

    recommendations = []

    # API recommendations
    if not api_results['all_configured']:
        print("\n🔧 API Configuration:")
        for api_name, api_info in api_results['apis'].items():
            if api_info['status'] == 'missing':
                print(f"  ⚠️  Configure {api_name.upper()} API key in dawsos/.env")
                recommendations.append(f"configure_{api_name}_api")

    # Data loading recommendations
    if graph_results:
        print("\n📦 Data Loading:")
        if graph_results['total_nodes'] < 1000:
            print(f"  📈 Load historical market data")
            print(f"     Run: python scripts/load_historical_data.py")
            recommendations.append("load_historical_data")

        if graph_results['api_sourced_count'] < 100:
            print(f"  📊 Load more API-sourced data")
            print(f"     Current: {graph_results['api_sourced_count']} nodes")
            print(f"     Target: >1000 nodes for robust analysis")
            recommendations.append("increase_api_data")

        if graph_results['placeholder_count'] > 10:
            print(f"  🧹 Clean up placeholder data")
            print(f"     Found: {graph_results['placeholder_count']} placeholder nodes")
            print(f"     Action: Replace with real data or remove")
            recommendations.append("cleanup_placeholders")

        if graph_results['recent_nodes'] < graph_results['total_nodes'] * 0.5:
            print(f"  🔄 Refresh stale data")
            print(f"     Recent data: {graph_results['recent_nodes']} nodes")
            print(f"     Action: Re-fetch from APIs")
            recommendations.append("refresh_stale_data")

    # Architecture recommendations
    print("\n🏗️  Architecture:")
    print(f"  ✓ Enable strict mode in UniversalExecutor")
    print(f"     Location: dawsos/main.py")
    print(f"     Change: strict_mode=True (fail on missing data)")

    print(f"\n  ✓ Add data quality monitoring")
    print(f"     Add telemetry to track real vs placeholder data usage")

    return recommendations

def main():
    """Main audit execution"""
    print("\n" + "="*70)
    print("🔍 DawsOS Data Source Audit")
    print("="*70)
    print("\nThis audit will check:")
    print("  1. API configuration and connectivity")
    print("  2. Knowledge graph data quality")
    print("  3. Real vs placeholder/mock data")
    print("  4. Recommendations for improvement")

    # Run audits
    api_results = check_api_status()
    graph_results = audit_knowledge_graph()

    # Generate summary
    print("\n" + "="*70)
    print("📋 Summary")
    print("="*70)

    # API summary
    working_apis = sum(1 for api in api_results['apis'].values() if api.get('test_result') == 'success')
    total_apis = len(api_results['apis'])

    print(f"\n✅ APIs Working: {working_apis}/{total_apis}")
    if working_apis == total_apis:
        print("   All APIs configured and operational!")
    elif working_apis > 0:
        print(f"   {total_apis - working_apis} API(s) need attention")
    else:
        print("   ⚠️  No APIs working - configure API keys in dawsos/.env")

    # Graph summary
    if graph_results:
        quality_score = graph_results['real_data_pct']
        print(f"\n📊 Data Quality Score: {quality_score:.1f}%")

        if quality_score >= 90:
            print("   ✅ Excellent - mostly real data")
        elif quality_score >= 70:
            print("   ⚠️  Good - some placeholder data present")
        elif quality_score >= 50:
            print("   ⚠️  Fair - significant placeholder data")
        else:
            print("   ❌ Poor - mostly placeholder data")

    # Recommendations
    recommendations = generate_recommendations(api_results, graph_results)

    print("\n" + "="*70)
    print("🎯 Next Steps")
    print("="*70)

    if not recommendations:
        print("\n✨ System is in good shape!")
        print("   Consider loading more historical data for deeper analysis.")
    else:
        print(f"\nComplete {len(recommendations)} action items to improve data quality:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec.replace('_', ' ').title()}")

    print("\n" + "="*70)
    print("📚 For more information, see:")
    print("   DATA_FLOW_AND_SEEDING_GUIDE.md")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()
