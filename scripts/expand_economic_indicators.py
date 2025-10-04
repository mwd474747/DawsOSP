#!/usr/bin/env python3
"""
Expand Economic Indicators from 22 to 200+ FRED Series
Systematically loads comprehensive economic data into knowledge graph
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dawsos.load_env import load_env
load_env()

from dawsos.core.knowledge_graph import KnowledgeGraph
from dawsos.capabilities.fred_data import FredDataCapability
from datetime import datetime, timedelta
import time
import json

# Define all 200+ economic indicators organized by category
ECONOMIC_INDICATORS = {
    'Labor Market': {
        'UNRATE': 'Unemployment Rate',
        'PAYEMS': 'Total Nonfarm Payrolls',
        'CIVPART': 'Labor Force Participation Rate',
        'EMRATIO': 'Employment-Population Ratio',
        'U6RATE': 'Total unemployed plus marginally attached',
        'ICSA': 'Initial Jobless Claims',
        'CCSA': 'Continued Jobless Claims',
        'JTSJOL': 'Job Openings',
        'JTSQUR': 'Quits Rate',
        'AWHI': 'Average Weekly Hours',
        'AHETPI': 'Average Hourly Earnings',
        'UNEMPLOY': 'Unemployed Persons',
        'LNS12032194': 'Employment Level - Part-Time',
        'LNS14000012': 'Unemployment Level - 16-19 years',
        'MEHOINUSA672N': 'Real Median Household Income',
        'LES1252881600Q': 'Employment Cost Index',
        'CES0500000003': 'Average Hourly Earnings of Production',
        'LREM64TTUSM156S': 'Employment Rate 25-54',
        'USSLIND': 'Leading Index for the United States',
        'USPHCI': 'Private Health Care Employment'
    },
    'Inflation & Prices': {
        'CPIAUCSL': 'Consumer Price Index',
        'CPILFESL': 'Core CPI (ex food & energy)',
        'PCEPI': 'PCE Price Index',
        'PCEPILFE': 'Core PCE',
        'PPIFIS': 'PPI - Finished Goods',
        'PPIACO': 'PPI - All Commodities',
        'PPITM': 'PPI - Intermediate Materials',
        'T5YIE': '5-Year Inflation Expectations',
        'T10YIE': '10-Year Inflation Expectations',
        'MICH': 'UMich Inflation Expectation',
        'DCOILWTICO': 'Crude Oil WTI',
        'DCOILBRENTEU': 'Crude Oil Brent',
        'GASREGW': 'US Regular Gas Price',
        'GOLDAMGBD228NLBM': 'Gold Fixing Price',
        'DEXCHUS': 'China/US Exchange Rate',
        'DEXJPUS': 'Japan/US Exchange Rate',
        'DEXUSEU': 'US/Euro Exchange Rate',
        'DEXUSUK': 'US/UK Exchange Rate',
        'DTWEXBGS': 'Trade Weighted US Dollar Index'
    },
    'GDP & Growth': {
        'GDP': 'Gross Domestic Product',
        'GDPC1': 'Real GDP',
        'GDPPOT': 'Potential Real GDP',
        'A191RL1Q225SBEA': 'Real GDP % change',
        'GDPDEF': 'GDP Deflator',
        'PCECC96': 'Real Personal Consumption',
        'PCEC96': 'Real PCE Goods',
        'PCESV96': 'Real PCE Services',
        'GPDI': 'Gross Private Domestic Investment',
        'GPDIC1': 'Real Gross Private Domestic Investment',
        'PNFI': 'Private Nonresidential Fixed Investment',
        'PRFI': 'Private Residential Fixed Investment',
        'NETEXP': 'Net Exports',
        'EXPGS': 'Exports of Goods and Services',
        'IMPGS': 'Imports of Goods and Services',
        'GCE': 'Government Consumption',
        'FGEXPND': 'Federal Government Expenditures',
        'SLEXPND': 'State/Local Government Expenditures',
        'PI': 'Personal Income'
    },
    'Interest Rates & Yield Curve': {
        'FEDFUNDS': 'Federal Funds Rate',
        'DFF': 'Federal Funds Effective Rate',
        'DFEDTARU': 'Fed Funds Target Range - Upper',
        'DFEDTARL': 'Fed Funds Target Range - Lower',
        'DGS1MO': '1-Month Treasury',
        'DGS3MO': '3-Month Treasury',
        'DGS6MO': '6-Month Treasury',
        'DGS1': '1-Year Treasury',
        'DGS2': '2-Year Treasury',
        'DGS3': '3-Year Treasury',
        'DGS5': '5-Year Treasury',
        'DGS7': '7-Year Treasury',
        'DGS10': '10-Year Treasury',
        'DGS20': '20-Year Treasury',
        'DGS30': '30-Year Treasury',
        'T10Y2Y': '10Y-2Y Treasury Spread',
        'T10Y3M': '10Y-3M Treasury Spread',
        'T10YFF': '10Y minus Fed Funds',
        'TEDRATE': 'TED Spread',
        'AAA': 'Moodys AAA Corporate Bond Yield',
        'BAA': 'Moodys BAA Corporate Bond Yield',
        'BAMLH0A0HYM2': 'ICE BofA High Yield Index',
        'MORTGAGE30US': '30-Year Fixed Rate Mortgage',
        'MORTGAGE15US': '15-Year Fixed Rate Mortgage',
        'DPRIME': 'Bank Prime Loan Rate'
    },
    'Money Supply & Credit': {
        'M1SL': 'M1 Money Stock',
        'M2SL': 'M2 Money Stock',
        'M2V': 'Velocity of M2',
        'BOGMBASE': 'Monetary Base',
        'WALCL': 'Fed Total Assets',
        'TOTRESNS': 'Total Reserves',
        'EXCSRESNS': 'Excess Reserves',
        'TOTALSL': 'Total Consumer Credit',
        'REVOLSL': 'Revolving Consumer Credit',
        'NONREVSL': 'Non-Revolving Consumer Credit',
        'DTCOLNVHFNM': 'Consumer Loans at Commercial Banks',
        'BUSLOANS': 'Commercial and Industrial Loans',
        'TOTBKCR': 'Bank Credit',
        'INVEST': 'Securities in Bank Credit'
    },
    'Housing Market': {
        'HOUST': 'Housing Starts',
        'PERMIT': 'Building Permits',
        'HOUST1F': 'Single-Family Housing Starts',
        'HOUST5F': '5-Unit+ Housing Starts',
        'COMPUTSA': 'New Housing Units Completed',
        'UNDCONTSA': 'Housing Units Under Construction',
        'MSACSR': 'Months Supply of Houses',
        'HSN1F': 'New One Family Houses Sold',
        'MSPUS': 'Median Sales Price of Houses',
        'ASPUS': 'Average Sales Price of Houses',
        'CSUSHPISA': 'S&P/Case-Shiller Home Price Index',
        'SPCS20RSA': 'S&P/Case-Shiller 20-City Index',
        'RHORUSQ156N': 'Homeownership Rate',
        'UMCSENT': 'Consumer Sentiment'
    },
    'Manufacturing & Business': {
        'INDPRO': 'Industrial Production Index',
        'IPG': 'Industrial Production: Manufacturing',
        'IPMANSICS': 'IP: Manufacturing (SIC)',
        'IPBUSEQ': 'IP: Business Equipment',
        'CAPUTL': 'Capacity Utilization',
        'TCU': 'Capacity Utilization: Total Industry',
        'NAPM': 'ISM Manufacturing PMI',
        'NAPMPI': 'ISM: Production Index',
        'NAPMNOI': 'ISM: New Orders',
        'NAPMII': 'ISM: Inventories',
        'NAPMPRI': 'ISM: Prices Paid',
        'NAPMEI': 'ISM: Employment',
        'NEWORDER': 'Manufacturers New Orders',
        'AMTMNO': 'Manufacturers New Orders: Durable',
        'DGORDER': 'Durable Goods New Orders',
        'BUSINV': 'Total Business Inventories',
        'ISRATIO': 'Business Inventories/Sales Ratio'
    },
    'Retail & Consumer': {
        'RSXFS': 'Retail Sales',
        'RRSFS': 'Real Retail Sales',
        'RSAFS': 'Retail Sales: Automotive',
        'RSGMS': 'Retail Sales: General Merchandise',
        'RSFHFS': 'Retail Sales: Food and Beverage',
        'UMCSENT': 'UMich Consumer Sentiment',
        'PCE': 'Personal Consumption Expenditures',
        'PSAVERT': 'Personal Saving Rate',
        'DPI': 'Disposable Personal Income',
        'DSPIC96': 'Real Disposable Personal Income',
        'PCEC96': 'Real PCE'
    },
    'Stock Market Indicators': {
        'SP500': 'S&P 500',
        'VIXCLS': 'CBOE Volatility Index',
        'WILL5000INDFC': 'Wilshire 5000',
        'DJIA': 'Dow Jones Industrial Average'
    },
    'Government & Fiscal': {
        'GFDEBTN': 'Federal Debt Total',
        'GFDEGDQ188S': 'Federal Debt to GDP Ratio',
        'FYFSD': 'Federal Surplus or Deficit',
        'FGRECPT': 'Federal Government Receipts',
        'FGEXPND': 'Federal Government Expenditures',
        'SLGSDODNS': 'State/Local Govt Debt',
        'WSHOMCB': 'Fed Mortgage-Backed Securities',
        'WTREGEN': 'Fed Treasury Securities Held'
    }
}

def load_economic_category(graph, fred, category_name, indicators, years=10):
    """Load all indicators for a specific category"""
    print(f"\n{'='*60}")
    print(f"📊 Loading Category: {category_name}")
    print(f"{'='*60}")

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365*years)).strftime('%Y-%m-%d')

    loaded_count = 0
    error_count = 0
    total = len(indicators)

    for idx, (series_id, indicator_name) in enumerate(indicators.items(), 1):
        try:
            print(f"  [{idx}/{total}] {series_id:20} {indicator_name[:40]:40}", end=' ')

            # Get series data
            series_data = fred.get_series(series_id, start_date, end_date)

            if 'error' in series_data:
                print(f"✗ {series_data['error']}")
                error_count += 1
                continue

            observations = series_data.get('observations', [])

            if not observations:
                print(f"✗ No data")
                error_count += 1
                continue

            # Create indicator node
            indicator_id = f"indicator_{series_id}"
            graph.add_node('economic_indicator', {
                'name': indicator_name,
                'series_id': series_id,
                'category': category_name,
                'source': 'FRED',
                'frequency': series_data.get('frequency', 'unknown'),
                'units': series_data.get('units', 'unknown'),
                'observation_count': len(observations),
                'last_updated': datetime.now().isoformat(),
                'data_start': observations[0]['date'] if observations else None,
                'data_end': observations[-1]['date'] if observations else None
            }, node_id=indicator_id)

            # Store observations
            obs_added = 0
            for obs in observations:
                if obs['value'] != '.':  # Skip missing values
                    obs_id = f"{series_id}_{obs['date']}"
                    graph.add_node('indicator_value', {
                        'series_id': series_id,
                        'indicator_name': indicator_name,
                        'category': category_name,
                        'date': obs['date'],
                        'value': float(obs['value']) if obs['value'] != '.' else None
                    }, node_id=obs_id)

                    # Link to indicator
                    graph.connect(indicator_id, obs_id, 'has_observation')
                    obs_added += 1

            loaded_count += 1
            print(f"✓ {obs_added} values")

            # Rate limiting (FRED allows 1000/min, use 0.1s = 600/min for safety)
            time.sleep(0.1)

        except Exception as e:
            print(f"✗ Error: {e}")
            error_count += 1

    print(f"\n✅ Category Complete: {loaded_count}/{total} loaded, {error_count} errors")
    return loaded_count, error_count

def main():
    """Main execution"""
    print("\n" + "="*70)
    print("📈 DawsOS Economic Indicator Expansion")
    print("="*70)
    print("\nExpanding from 22 to 200+ FRED economic indicators...")

    # Initialize
    graph = KnowledgeGraph()
    fred = FredDataCapability()

    # Check API
    if not fred.api_key:
        print("\n❌ FRED API key not configured!")
        print("Set FRED_API_KEY in dawsos/.env")
        return

    print(f"\n✓ FRED API Key: {fred.api_key[:8]}...{fred.api_key[-4:]}")

    # Load existing graph
    if os.path.exists('dawsos/storage/graph.json'):
        try:
            graph.load('dawsos/storage/graph.json')
            print(f"✓ Loaded existing graph: {graph.get_stats()['total_nodes']} nodes")
        except Exception as e:
            print(f"⚠️  Could not load existing graph: {e}")

    # Track progress
    total_loaded = 0
    total_errors = 0
    start_time = datetime.now()

    # Load each category
    for category_name, indicators in ECONOMIC_INDICATORS.items():
        loaded, errors = load_economic_category(graph, fred, category_name, indicators, years=10)
        total_loaded += loaded
        total_errors += errors

        # Save progress after each category
        checkpoint_file = f'dawsos/storage/graph_econ_{category_name.replace(" ", "_").lower()}.json'
        graph.save(checkpoint_file)
        print(f"💾 Saved checkpoint: {checkpoint_file}")

    # Final save
    print("\n" + "="*70)
    print("💾 Saving final graph...")
    graph.save('dawsos/storage/graph_economic_expanded.json')

    # Also update default graph
    graph.save('dawsos/storage/graph.json')
    print("✅ Updated default graph.json")

    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    stats = graph.get_stats()

    print("\n" + "="*70)
    print("📊 Economic Expansion Complete!")
    print("="*70)
    print(f"\n✨ Results:")
    print(f"  Indicators Loaded:  {total_loaded}")
    print(f"  Errors:             {total_errors}")
    print(f"  Total Graph Nodes:  {stats['total_nodes']:,}")
    print(f"  Total Edges:        {stats['total_edges']:,}")
    print(f"  Execution Time:     {elapsed/60:.1f} minutes")
    print(f"\n📁 Saved to:")
    print(f"  - dawsos/storage/graph_economic_expanded.json")
    print(f"  - dawsos/storage/graph.json (default)")
    print("\n🚀 Ready for analysis with comprehensive economic data!")

if __name__ == '__main__':
    main()
