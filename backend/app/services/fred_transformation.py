"""
FRED Data Transformation Service

Purpose: Transform raw FRED API values to standardized decimal/percentage formats
Updated: 2025-11-02

This service handles the scaling and transformation of raw FRED data values
based on their series-specific units to produce consistent decimal/percentage
values for macro economic analysis.
"""

import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Optional, Any

logger = logging.getLogger("DawsOS.FREDTransformation")


class FREDTransformationService:
    """
    Transform raw FRED data to normalized values for macro indicators.
    
    Each FRED series has different units and needs specific transformations:
    - Index values (CPI, INDPRO) → YoY percentage change
    - Debt values → Ratio to GDP
    - Percentages → Decimal format (0.05 = 5%)
    - PMI values → Keep as-is or scale appropriately
    """
    
    # FRED series mapping with transformation details
    SERIES_TRANSFORMATIONS = {
        # GDP and Growth
        'A191RL1Q225SBEA': {
            'name': 'gdp_growth',
            'transform': 'percent_to_decimal',
            'description': 'Real GDP % change (already in percent)'
        },
        'GDP': {
            'name': 'gdp_nominal',
            'transform': 'billions_to_value',
            'description': 'Nominal GDP in billions'
        },
        
        # Inflation (CPI)
        'CPIAUCSL': {
            'name': 'inflation',
            'transform': 'index_to_yoy_change',
            'description': 'CPI index (1982-84=100) to YoY %'
        },
        'CPILFESL': {
            'name': 'core_inflation',
            'transform': 'index_to_yoy_change',
            'description': 'Core CPI to YoY %'
        },
        
        # Employment
        'UNRATE': {
            'name': 'unemployment',
            'transform': 'percent_to_decimal',
            'description': 'Unemployment rate as decimal'
        },
        'PAYEMS': {
            'name': 'payroll_growth',
            'transform': 'level_to_yoy_change',
            'description': 'Nonfarm payrolls to YoY %'
        },
        
        # Interest Rates
        'DGS10': {
            'name': 'treasury_10y',
            'transform': 'percent_to_decimal',
            'description': '10-Year Treasury yield'
        },
        'DGS2': {
            'name': 'treasury_2y',
            'transform': 'percent_to_decimal',
            'description': '2-Year Treasury yield'
        },
        'T10Y2Y': {
            'name': 'yield_curve',
            'transform': 'percent_to_decimal',
            'description': '10Y-2Y Treasury spread'
        },
        'DFF': {
            'name': 'interest_rate',
            'transform': 'percent_to_decimal',
            'description': 'Federal Funds Rate'
        },
        'FEDFUNDS': {
            'name': 'fed_funds_rate',
            'transform': 'percent_to_decimal',
            'description': 'Federal Funds Effective Rate'
        },
        
        # Debt and Credit
        'GFDEBTN': {
            'name': 'federal_debt',
            'transform': 'millions_to_gdp_ratio',
            'description': 'Federal debt in millions to GDP ratio'
        },
        'GFDEGDQ188S': {
            'name': 'debt_to_gdp',
            'transform': 'percent_to_decimal',
            'description': 'Federal debt to GDP ratio (already %)'
        },
        'TDSP': {
            'name': 'debt_service_ratio',
            'transform': 'percent_to_decimal',
            'description': 'Household debt service ratio'
        },
        'TOTBKCR': {
            'name': 'credit_growth',
            'transform': 'level_to_yoy_change',
            'description': 'Total bank credit to YoY %'
        },
        'BAA10Y': {
            'name': 'credit_spreads',
            'transform': 'percent_to_decimal',
            'description': 'BAA-10Y Treasury spread'
        },
        
        # Fiscal
        'FYFSGDA188S': {
            'name': 'fiscal_deficit',
            'transform': 'percent_to_decimal_signed',
            'description': 'Federal deficit as % of GDP (negative)'
        },
        'FYFSD': {
            'name': 'fiscal_deficit_dollars',
            'transform': 'billions_to_value',
            'description': 'Federal deficit in billions'
        },
        
        # Production
        'INDPRO': {
            'name': 'industrial_production',
            'transform': 'index_to_yoy_change',
            'description': 'Industrial Production Index to YoY %'
        },
        'CAPUTL': {
            'name': 'capacity_utilization',
            'transform': 'percent_to_decimal',
            'description': 'Capacity utilization rate'
        },
        
        # PMI and Business
        'MANEMP': {
            'name': 'manufacturing_employment',
            'transform': 'index_keep',
            'description': 'ISM Manufacturing Employment Index'
        },
        'NAPM': {
            'name': 'manufacturing_pmi',
            'transform': 'index_keep',
            'description': 'ISM Manufacturing PMI (keep as-is)'
        },
        'NAPMNOI': {
            'name': 'manufacturing_new_orders',
            'transform': 'index_keep',
            'description': 'ISM Manufacturing New Orders'
        },
        
        # Trade
        'NETEXP': {
            'name': 'trade_balance',
            'transform': 'billions_to_gdp_ratio_signed',
            'description': 'Net exports to GDP ratio'
        },
        
        # Money Supply
        'M2SL': {
            'name': 'm2_money_supply',
            'transform': 'level_to_yoy_change',
            'description': 'M2 Money Supply to YoY %'
        },
        
        # Consumer
        'RSXFS': {
            'name': 'retail_sales',
            'transform': 'level_to_yoy_change',
            'description': 'Retail sales to YoY %'
        },
        'UMCSENT': {
            'name': 'consumer_confidence',
            'transform': 'index_keep',
            'description': 'UMich Consumer Sentiment (keep as-is)'
        },
        
        # Housing
        'HOUST': {
            'name': 'housing_starts',
            'transform': 'thousands_keep',
            'description': 'Housing starts in thousands'
        },
        
        # Markets
        'VIXCLS': {
            'name': 'vix',
            'transform': 'index_keep',
            'description': 'VIX volatility index'
        },
        'SP500': {
            'name': 'sp500',
            'transform': 'index_to_yoy_change',
            'description': 'S&P 500 to YoY %'
        }
    }
    
    def __init__(self):
        """Initialize transformation service"""
        self.gdp_cache = {}  # Cache GDP values for ratio calculations
        self.historical_data = {}  # Cache for YoY calculations
        
    def transform_fred_value(
        self,
        series_id: str,
        value: float,
        date_str: str,
        historical_values: Optional[List[Dict]] = None,
        gdp_value: Optional[float] = None
    ) -> Optional[float]:
        """
        Transform a raw FRED value based on the series type.
        
        Args:
            series_id: FRED series identifier
            value: Raw value from FRED
            date_str: Date string (YYYY-MM-DD)
            historical_values: Historical values for YoY calculations
            gdp_value: Current GDP value for ratio calculations
            
        Returns:
            Transformed value or None if transformation fails
        """
        if series_id not in self.SERIES_TRANSFORMATIONS:
            logger.warning(f"No transformation defined for series {series_id}")
            return value
            
        transform_info = self.SERIES_TRANSFORMATIONS[series_id]
        transform_type = transform_info['transform']
        
        try:
            if transform_type == 'percent_to_decimal':
                # Convert percentage to decimal (5% → 0.05)
                return value / 100.0
                
            elif transform_type == 'percent_to_decimal_signed':
                # Convert percentage to decimal, preserving sign
                return value / 100.0
                
            elif transform_type == 'index_to_yoy_change':
                # Calculate year-over-year percentage change
                if not historical_values:
                    logger.warning(f"No historical data for YoY calculation: {series_id}")
                    return None
                    
                # Find value from 1 year ago
                current_date = datetime.strptime(date_str, "%Y-%m-%d")
                year_ago = current_date - timedelta(days=365)
                
                for hist in historical_values:
                    hist_date = datetime.strptime(hist['date'], "%Y-%m-%d")
                    if abs((hist_date - year_ago).days) <= 7:  # Within a week
                        year_ago_value = float(hist['value'])
                        if year_ago_value > 0:
                            yoy_change = (value - year_ago_value) / year_ago_value
                            return yoy_change
                            
                logger.warning(f"Could not find year-ago value for {series_id}")
                return None
                
            elif transform_type == 'level_to_yoy_change':
                # Similar to index_to_yoy_change but for level data
                if not historical_values:
                    return None
                    
                current_date = datetime.strptime(date_str, "%Y-%m-%d")
                year_ago = current_date - timedelta(days=365)
                
                for hist in historical_values:
                    hist_date = datetime.strptime(hist['date'], "%Y-%m-%d")
                    if abs((hist_date - year_ago).days) <= 7:
                        year_ago_value = float(hist['value'])
                        if year_ago_value > 0:
                            yoy_change = (value - year_ago_value) / year_ago_value
                            return yoy_change
                            
                return None
                
            elif transform_type == 'millions_to_gdp_ratio':
                # Convert millions to ratio of GDP
                if not gdp_value or gdp_value <= 0:
                    logger.warning(f"No GDP value for ratio calculation: {series_id}")
                    # Use approximate US GDP of $27 trillion
                    gdp_value = 27000000  # In millions
                    
                # GFDEBTN is in millions, GDP should be in millions too
                ratio = value / gdp_value
                return ratio
                
            elif transform_type == 'billions_to_gdp_ratio_signed':
                # Convert billions to ratio of GDP (for trade balance)
                if not gdp_value or gdp_value <= 0:
                    gdp_value = 27000  # In billions
                    
                ratio = value / gdp_value
                return ratio
                
            elif transform_type == 'billions_to_value':
                # Keep in billions but ensure it's a reasonable value
                return value
                
            elif transform_type == 'thousands_keep':
                # Keep in thousands (for housing starts)
                return value
                
            elif transform_type == 'index_keep':
                # Keep index value as-is (for PMI, sentiment)
                return value
                
            else:
                logger.warning(f"Unknown transformation type: {transform_type}")
                return value
                
        except Exception as e:
            logger.error(f"Error transforming {series_id}: {e}")
            return None
            
    def get_indicator_name(self, series_id: str) -> str:
        """Get the standardized indicator name for a FRED series"""
        if series_id in self.SERIES_TRANSFORMATIONS:
            return self.SERIES_TRANSFORMATIONS[series_id]['name']
        return series_id.lower()
        
    def needs_historical_data(self, series_id: str) -> bool:
        """Check if a series needs historical data for transformation"""
        if series_id not in self.SERIES_TRANSFORMATIONS:
            return False
            
        transform_type = self.SERIES_TRANSFORMATIONS[series_id]['transform']
        return transform_type in ['index_to_yoy_change', 'level_to_yoy_change']
        
    def needs_gdp_data(self, series_id: str) -> bool:
        """Check if a series needs GDP data for transformation"""
        if series_id not in self.SERIES_TRANSFORMATIONS:
            return False
            
        transform_type = self.SERIES_TRANSFORMATIONS[series_id]['transform']
        return 'gdp_ratio' in transform_type
        
    def batch_transform(
        self,
        observations: List[Dict[str, Any]],
        series_id: str,
        gdp_value: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Transform a batch of FRED observations.
        
        Args:
            observations: List of FRED observations
            series_id: FRED series identifier
            gdp_value: Current GDP value for ratio calculations
            
        Returns:
            List of transformed observations
        """
        transformed = []
        
        # Sort observations by date for YoY calculations
        sorted_obs = sorted(observations, key=lambda x: x['date'])
        
        for i, obs in enumerate(sorted_obs):
            try:
                raw_value = float(obs['value'])
                date_str = obs['date']
                
                # Get historical values if needed
                historical_values = None
                if self.needs_historical_data(series_id) and i > 0:
                    historical_values = sorted_obs[:i]
                
                # Transform the value
                transformed_value = self.transform_fred_value(
                    series_id=series_id,
                    value=raw_value,
                    date_str=date_str,
                    historical_values=historical_values,
                    gdp_value=gdp_value
                )
                
                if transformed_value is not None:
                    transformed.append({
                        'date': date_str,
                        'value': transformed_value,
                        'raw_value': raw_value,
                        'indicator_name': self.get_indicator_name(series_id),
                        'series_id': series_id
                    })
                    
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid observation: {e}")
                continue
                
        return transformed


# Singleton instance
_transformation_service = None


def get_transformation_service() -> FREDTransformationService:
    """Get or create singleton transformation service"""
    global _transformation_service
    if _transformation_service is None:
        _transformation_service = FREDTransformationService()
        logger.info("FRED Transformation Service initialized")
    return _transformation_service