"""
Trinity 3.0 - Integrated Market Overview Module
Provides real-time market data with proper error handling and data flow
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional, Any
from datetime import datetime
import traceback

from ui.professional_theme import ProfessionalTheme


class MarketDataProvider:
    """Centralized market data provider with consistent error handling"""
    
    def __init__(self):
        """Initialize with session state services"""
        self.openbb_service = st.session_state.get('openbb_service')
        self.real_data = st.session_state.get('real_data')
        self.cache = {}
    
    def get_equity_data(self, symbol: str) -> Tuple[Optional[float], Optional[float], str]:
        """
        Get equity price and change with proper error handling
        Returns: (price, change_percent, status)
        """
        try:
            price = None
            change = None
            status = "no_data"
            
            # Try real data service first
            if self.real_data:
                try:
                    real_price = self.real_data.get_realtime_price(symbol)
                    if real_price is not None:
                        price = real_price
                        status = "live"
                except Exception as e:
                    print(f"Error getting real-time price for {symbol}: {e}")
            
            # Try OpenBB service for full quote data
            if self.openbb_service:
                try:
                    quote = self.openbb_service.get_equity_quote(symbol)
                    if quote and 'results' in quote and len(quote['results']) > 0:
                        result = quote['results'][0]
                        if 'price' in result and result['price']:
                            price = float(result['price'])
                            status = "live"
                        if 'changesPercentage' in result:
                            change = float(result['changesPercentage'])
                except Exception as e:
                    print(f"Error getting OpenBB quote for {symbol}: {e}")
            
            return price, change, status
            
        except Exception as e:
            print(f"Critical error in get_equity_data for {symbol}: {e}")
            return None, None, "error"
    
    def get_market_internals(self) -> Dict[str, Any]:
        """Get market internals data - only real data, no placeholders"""
        internals = {
            'vix': {'value': None, 'change': None, 'status': 'no_data'},
            'breadth': {'value': None, 'change': None, 'status': 'no_data'},
            'put_call': {'value': None, 'change': None, 'status': 'no_data'}
        }
        
        try:
            # Try to get real VIX data
            if self.real_data:
                try:
                    vix_value = self.real_data.get_vix_data()
                    vix_change = self.real_data.get_vix_change()
                    internals['vix'] = {
                        'value': vix_value,
                        'change': vix_change,
                        'status': 'live'
                    }
                except:
                    pass
            
            # Try to get market breadth
            if self.openbb_service:
                try:
                    breadth_data = self.openbb_service.get_market_breadth()
                    if breadth_data and 'market_internals' in breadth_data:
                        breadth_value = breadth_data['market_internals']['advance_decline_ratio']
                        internals['breadth'] = {
                            'value': breadth_value,
                            'change': (breadth_value - 1) * 100,
                            'status': 'live'
                        }
                except:
                    pass
            
            # Try to get put/call ratio
            if self.real_data:
                try:
                    pc_ratio = self.real_data.get_real_put_call_ratio()
                    internals['put_call'] = {
                        'value': pc_ratio,
                        'change': (pc_ratio - 1) * 100,
                        'status': 'live'
                    }
                except:
                    pass
                    
        except Exception:
            pass  # Use fallback values
        
        return internals
    
    def get_market_regime(self, vix: float, breadth: float, pc_ratio: float) -> Tuple[str, str]:
        """
        Determine market regime based on indicators
        Returns: (regime_name, color)
        """
        try:
            if vix < 15 and breadth > 1.2 and pc_ratio < 0.8:
                return "RISK ON", ProfessionalTheme.COLORS['accent_success']
            elif vix > 25 or breadth < 0.7 or pc_ratio > 1.2:
                return "RISK OFF", ProfessionalTheme.COLORS['accent_danger']
            else:
                return "NEUTRAL", ProfessionalTheme.COLORS['accent_warning']
        except:
            return "NEUTRAL", ProfessionalTheme.COLORS['accent_warning']
    
    def get_sector_data(self) -> List[Tuple[str, str, Optional[float], Optional[float]]]:
        """Get sector performance data - only real data"""
        sectors = [
            ("Technology", "XLK"),
            ("Healthcare", "XLV"),
            ("Financials", "XLF"),
            ("Consumer Disc", "XLY"),
            ("Energy", "XLE"),
            ("Utilities", "XLU"),
            ("Real Estate", "XLRE"),
            ("Materials", "XLB"),
            ("Industrials", "XLI"),
            ("Cons Staples", "XLP"),
            ("Communications", "XLC")
        ]
        
        result = []
        for name, symbol in sectors:
            try:
                price, change, _ = self.get_equity_data(symbol)
                result.append((f"{name} ({symbol})", symbol, price, change))
            except Exception as e:
                print(f"Error getting sector data for {symbol}: {e}")
                result.append((f"{name} ({symbol})", symbol, None, None))
        
        return result[:8]  # Return top 8 for grid display
    
    def get_market_news(self) -> List[Dict]:
        """Get market news - only real news from API"""
        news_items = []
        
        try:
            if self.openbb_service:
                news_data = self.openbb_service.get_market_news(limit=5)
                if news_data and 'articles' in news_data:
                    news_items = []
                    for article in news_data['articles'][:5]:
                        news_items.append({
                            'time': article.get('publishedAt', '')[:10],
                            'title': article.get('title', 'No title'),
                            'source': article.get('source', {}).get('name', 'Unknown')
                        })
                    return news_items if news_items else []
        except Exception as e:
            print(f"Error getting market news: {e}")
            return []
        
        return []


def render_market_overview_integrated():
    """
    Render Market Overview with fully integrated data flow and error handling
    Following Trinity 3.0 architecture patterns
    """
    
    # Initialize data provider
    data_provider = MarketDataProvider()
    
    # Add loading state management
    with st.container():
        # Section: Major Indices
        st.subheader("Major Indices")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Define indices with defaults
        indices = [
            ("S&P 500 (SPY)", "SPY", 452.75, 1.25),
            ("Nasdaq 100 (QQQ)", "QQQ", 378.42, 1.58),
            ("Dow Jones (DIA)", "DIA", 342.18, 0.82),
            ("Russell 2000 (IWM)", "IWM", 198.65, -0.48)
        ]
        
        for col, (name, symbol, default_price, default_change) in zip([col1, col2, col3, col4], indices):
            with col:
                try:
                    price, change, status = data_provider.get_equity_data(symbol)
                    
                    # Only display if we have real data
                    if price is not None:
                        # Display metric with status indicator
                        st.metric(
                            label=name,
                            value=f"${price:.2f}",
                            delta=f"{change:.2f}%" if change is not None else None,
                            help=f"Data: {status}"
                        )
                        
                        # Add mini status indicator
                        if status == "live":
                            st.caption("Live")
                        else:
                            st.caption(status.capitalize())
                    else:
                        # Show loading state when no data available
                        st.metric(
                            label=name,
                            value="Loading...",
                            delta=None,
                            help="Fetching real-time data"
                        )
                        st.caption("No data available")
                        
                except Exception as e:
                    st.metric(name, "Error", help=f"Error: {str(e)}")
    
    # Section: Market Internals & Sentiment
    with st.container():
        st.subheader("Market Internals & Sentiment")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # Get market internals data
        internals = data_provider.get_market_internals()
        
        with col1:
            vix_data = internals['vix']
            if vix_data['value'] is not None:
                st.metric(
                    "VIX",
                    f"{vix_data['value']:.2f}",
                    f"{vix_data['change']:.2f}%" if vix_data['change'] is not None else None,
                    help=f"Volatility Index - Data: {vix_data['status']}"
                )
            else:
                st.metric("VIX", "Loading...", None, help="Fetching VIX data")
        
        with col2:
            breadth_data = internals['breadth']
            if breadth_data['value'] is not None:
                st.metric(
                    "A/D Ratio",
                    f"{breadth_data['value']:.2f}",
                    f"{breadth_data['change']:.1f}%" if breadth_data['change'] is not None else None,
                    help=f"Advance/Decline Ratio - Data: {breadth_data['status']}"
                )
            else:
                st.metric("A/D Ratio", "Loading...", None, help="Fetching market breadth")
        
        with col3:
            pc_data = internals['put_call']
            if pc_data['value'] is not None:
                st.metric(
                    "Put/Call Ratio",
                    f"{pc_data['value']:.2f}",
                    f"{pc_data['change']:.1f}%" if pc_data['change'] is not None else None,
                    help=f"Options Sentiment - Data: {pc_data['status']}"
                )
            else:
                st.metric("Put/Call Ratio", "Loading...", None, help="Fetching options data")
        
        with col4:
            # Market Regime Indicator
            regime, regime_color = data_provider.get_market_regime(
                internals['vix']['value'],
                internals['breadth']['value'],
                internals['put_call']['value']
            )
            
            st.markdown(f"""
            <div style="background: {regime_color}20; border: 2px solid {regime_color}; 
                        border-radius: 8px; padding: 0.75rem; text-align: center; height: 100%;">
                <div style="font-size: 0.7rem; color: {ProfessionalTheme.COLORS['text_secondary']}; margin-bottom: 0.25rem;">
                    MARKET REGIME
                </div>
                <div style="font-size: 1.2rem; font-weight: bold; color: {regime_color};">
                    {regime}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Section: Commodities & Bonds
    with st.container():
        st.subheader("Commodities & Bonds")
        
        col1, col2, col3, col4 = st.columns(4)
        
        commodities = [
            ("Gold (GLD)", "GLD", 185.50, 0.35),
            ("Oil (USO)", "USO", 72.15, -1.25),
            ("20Y Treasury (TLT)", "TLT", 92.80, 0.15),
            ("US Dollar (UUP)", "UUP", 28.50, -0.10)
        ]
        
        for col, (name, symbol, default_price, default_change) in zip([col1, col2, col3, col4], commodities):
            with col:
                try:
                    price, change, status = data_provider.get_equity_data(symbol, default_price, default_change)
                    st.metric(
                        label=name,
                        value=f"${price:.2f}",
                        delta=f"{change:.2f}%",
                        help=f"Data: {status}"
                    )
                except Exception as e:
                    st.metric(name, "N/A", help=f"Error: {str(e)}")
    
    # Section: Sector Performance
    with st.container():
        st.subheader("Sector Performance")
        
        try:
            sectors = data_provider.get_sector_data()
            
            for row in range(2):
                cols = st.columns(4)
                for i in range(4):
                    idx = row * 4 + i
                    if idx < len(sectors):
                        name, symbol, price, change = sectors[idx]
                        with cols[i]:
                            if price is not None:
                                st.metric(
                                    label=name,
                                    value=f"${price:.2f}",
                                    delta=f"{change:.2f}%" if change is not None else None
                                )
                            else:
                                st.metric(
                                    label=name,
                                    value="Loading...",
                                    delta=None,
                                    help="Fetching sector data"
                                )
        except Exception as e:
            st.error(f"Sector data temporarily unavailable: {str(e)}")
    
    # Section: Market News
    with st.container():
        st.subheader("Market News & Events")
        
        try:
            news_items = data_provider.get_market_news()
            
            if news_items:
                for item in news_items:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{item['title']}**")
                        with col2:
                            st.caption(f"{item['source']} • {item['time']}")
                        st.markdown("---")
            else:
                st.info("No news data available. News will appear when market data feed is connected.")
        except Exception as e:
            st.error(f"News feed temporarily unavailable: {str(e)}")
    
    # Add data refresh timestamp
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Add refresh button
    if st.button("Refresh Data", key="refresh_market_overview"):
        st.rerun()


# Testing function
def test_market_overview():
    """Test the integrated market overview"""
    try:
        st.write("## Market Overview Test Suite")
        
        # Test data provider
        provider = MarketDataProvider()
        
        # Test equity data retrieval
        st.write("### Testing Equity Data Retrieval")
        test_symbols = ["SPY", "QQQ", "INVALID_SYMBOL"]
        for symbol in test_symbols:
            price, change, status = provider.get_equity_data(symbol)
            if price is not None:
                st.write(f"{symbol}: Price=${price:.2f}, Change={change:.2f if change else 0}%, Status={status}")
            else:
                st.write(f"{symbol}: No data available, Status={status}")
        
        # Test market internals
        st.write("### Testing Market Internals")
        internals = provider.get_market_internals()
        for key, data in internals.items():
            if data['value'] is not None:
                st.write(f"{key}: Value={data['value']:.2f}, Change={data['change']:.2f if data['change'] else 0}%, Status={data['status']}")
            else:
                st.write(f"{key}: No data available, Status={data['status']}")
        
        # Test market regime
        st.write("### Testing Market Regime")
        regime, color = provider.get_market_regime(20, 1.1, 0.9)
        st.write(f"Regime: {regime}, Color: {color}")
        
        st.success("✅ All tests completed")
        
    except Exception as e:
        st.error(f"❌ Test failed: {str(e)}")
        st.code(traceback.format_exc())