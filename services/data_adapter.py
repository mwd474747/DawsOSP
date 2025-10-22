"""
Trinity Data Adapter - Unified Data Interface
Per Integration Specialist recommendations

Provides clean abstraction over data sources with built-in fallback:
OpenBBService (real data) → MockDataService (fallback)
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DataAdapter:
    """
    Unified data interface with automatic fallback logic.
    
    Architecture:
    - Primary: OpenBBService (real-time market data)
    - Fallback: MockDataService (reliable mock data)
    - Mode tracking: "real" vs "mock"
    """
    
    def __init__(self):
        """Initialize data adapter with primary and fallback sources"""
        try:
            from services.openbb_service import OpenBBService
            from services.mock_data_service import MockDataService
            
            self.primary = OpenBBService()
            self.fallback = MockDataService()
            self.mode = "real"
            logger.info("DataAdapter initialized with OpenBB (real data) + MockData (fallback)")
        except Exception as e:
            logger.warning(f"OpenBB initialization failed: {e}, using MockData only")
            from services.mock_data_service import MockDataService
            self.primary = MockDataService()
            self.fallback = MockDataService()
            self.mode = "mock"
    
    def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get stock data with automatic fallback.
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL')
        
        Returns:
            Dictionary with stock data (price, volume, etc.)
        """
        try:
            data = self.primary.get_stock_data(symbol)
            if data:
                return data
            raise ValueError("No data returned")
        except Exception as e:
            logger.warning(f"Primary data source failed for {symbol}: {e}, using fallback")
            return self.fallback.get_stock_data(symbol)
    
    def get_market_data(self, symbols: Optional[list] = None) -> Dict[str, Any]:
        """
        Get market overview data.
        
        Args:
            symbols: List of symbols (defaults to major indices)
        
        Returns:
            Dictionary with market data
        """
        try:
            data = self.primary.get_market_data(symbols)
            if data:
                return data
            raise ValueError("No data returned")
        except Exception as e:
            logger.warning(f"Primary data source failed for market data: {e}, using fallback")
            return self.fallback.get_market_data(symbols)
    
    def get_economic_data(self, indicator: str) -> Dict[str, Any]:
        """
        Get economic indicator data (GDP, CPI, etc.).
        
        Args:
            indicator: Economic indicator code (e.g., 'GDP', 'CPI')
        
        Returns:
            Dictionary with economic data
        """
        try:
            data = self.primary.get_economic_data(indicator)
            if data:
                return data
            raise ValueError("No data returned")
        except Exception as e:
            logger.warning(f"Primary data source failed for {indicator}: {e}, using fallback")
            return self.fallback.get_economic_data(indicator)
    
    def get_financials(self, symbol: str) -> Dict[str, Any]:
        """
        Get company financials.
        
        Args:
            symbol: Stock ticker
        
        Returns:
            Dictionary with financial statements
        """
        try:
            data = self.primary.get_financials(symbol)
            if data:
                return data
            raise ValueError("No data returned")
        except Exception as e:
            logger.warning(f"Primary data source failed for {symbol} financials: {e}, using fallback")
            return self.fallback.get_financials(symbol)
    
    def get_current_mode(self) -> str:
        """Get current data source mode"""
        return self.mode
    
    def is_real_data(self) -> bool:
        """Check if using real data"""
        return self.mode == "real"
