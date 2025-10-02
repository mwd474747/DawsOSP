import os
import urllib.request
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class FredDataCapability:
    """Federal Reserve Economic Data (FRED) API integration"""

    def __init__(self):
        # Get FRED API key from environment
        self.api_key = os.getenv('FRED_API_KEY')
        self.base_url = 'https://api.stlouisfed.org/fred'
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour for economic data

        # Common economic indicators
        self.indicators = {
            'GDP': 'GDP',  # Gross Domestic Product
            'CPI': 'CPIAUCSL',  # Consumer Price Index
            'UNEMPLOYMENT': 'UNRATE',  # Unemployment Rate
            'FED_FUNDS': 'DFF',  # Federal Funds Rate
            'TREASURY_10Y': 'DGS10',  # 10-Year Treasury Rate
            'TREASURY_2Y': 'DGS2',  # 2-Year Treasury Rate
            'VIX': 'VIXCLS',  # CBOE Volatility Index
            'DOLLAR_INDEX': 'DTWEXBGS',  # Trade Weighted Dollar Index
            'RETAIL_SALES': 'RSXFS',  # Retail Sales
            'INDUSTRIAL_PRODUCTION': 'INDPRO',  # Industrial Production Index
            'HOUSING_STARTS': 'HOUST',  # Housing Starts
            'CONSUMER_SENTIMENT': 'UMCSENT',  # Consumer Sentiment
            'M2': 'M2SL',  # M2 Money Supply
            'INFLATION_EXPECTATIONS': 'T5YIE',  # 5-Year Inflation Expectations
            'CREDIT_SPREADS': 'BAMLH0A0HYM2',  # High Yield Credit Spreads
            'DEBT_TO_GDP': 'GFDEGDQ188S',  # Federal Debt to GDP
            'SAVINGS_RATE': 'PSAVERT',  # Personal Savings Rate
            'JOBLESS_CLAIMS': 'ICSA',  # Initial Jobless Claims
            'NFIB_OPTIMISM': 'NFIB',  # Small Business Optimism Index
            'PMI_MANUFACTURING': 'MANEMP',  # Manufacturing Employment
        }

    def get_series(self, series_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """Get time series data for a specific indicator"""

        # Check cache
        cache_key = f"{series_id}:{start_date}:{end_date}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached['time'] < timedelta(seconds=self.cache_ttl):
                return cached['data']

        # Default date range
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')

        # Build URL
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'observation_start': start_date,
            'observation_end': end_date
        }

        url = f"{self.base_url}/series/observations?"
        url += '&'.join([f"{k}={v}" for k, v in params.items()])

        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())

                # Parse observations
                observations = []
                for obs in data.get('observations', []):
                    try:
                        # Skip entries with "." which means no data
                        if obs.get('value') == '.':
                            continue
                        value = float(obs['value'])
                        observations.append({
                            'date': obs['date'],
                            'value': value
                        })
                    except (ValueError, KeyError, TypeError):
                        continue

                result = {
                    'series_id': series_id,
                    'name': self._get_series_name(series_id),
                    'units': data.get('units', 'Index'),
                    'frequency': data.get('frequency', 'Monthly'),
                    'observations': observations,
                    'latest_value': observations[-1]['value'] if observations else None,
                    'latest_date': observations[-1]['date'] if observations else None
                }

                # Update cache
                self.cache[cache_key] = {
                    'data': result,
                    'time': datetime.now()
                }

                return result

        except Exception as e:
            return {'error': str(e), 'series_id': series_id}

    def get_latest(self, indicator: str) -> Dict:
        """Get latest value for an indicator"""

        # Map indicator name to series ID
        series_id = self.indicators.get(indicator.upper(), indicator)

        # Get last 30 days of data
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        data = self.get_series(series_id, start_date, end_date)

        if 'error' in data:
            return data

        # Calculate change
        observations = data.get('observations', [])
        if len(observations) >= 2:
            latest = observations[-1]['value']
            previous = observations[-2]['value']
            change = latest - previous
            change_pct = ((latest - previous) / previous * 100) if previous != 0 else 0

            # Determine trend
            if len(observations) >= 5:
                recent_avg = sum(o['value'] for o in observations[-5:]) / 5
                older_avg = sum(o['value'] for o in observations[-10:-5]) / min(5, len(observations)-5) if len(observations) > 5 else recent_avg
                if recent_avg > older_avg * 1.01:
                    trend = 'rising'
                elif recent_avg < older_avg * 0.99:
                    trend = 'falling'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'

            return {
                'indicator': indicator,
                'series_id': series_id,
                'name': data.get('name'),
                'value': latest,
                'previous': previous,
                'change': round(change, 2),
                'change_percent': round(change_pct, 2),
                'trend': trend,
                'date': observations[-1]['date'],
                'units': data.get('units')
            }

        return {
            'indicator': indicator,
            'series_id': series_id,
            'value': data.get('latest_value'),
            'date': data.get('latest_date')
        }

    def get_all_indicators(self) -> Dict:
        """Get latest values for all common indicators"""

        results = {}

        # Key indicators to fetch
        key_indicators = [
            'GDP', 'CPI', 'UNEMPLOYMENT', 'FED_FUNDS',
            'TREASURY_10Y', 'TREASURY_2Y', 'VIX', 'M2',
            'RETAIL_SALES', 'HOUSING_STARTS', 'JOBLESS_CLAIMS'
        ]

        for indicator in key_indicators:
            data = self.get_latest(indicator)
            if 'error' not in data:
                results[indicator] = data

        # Calculate yield curve (10Y - 2Y)
        if 'TREASURY_10Y' in results and 'TREASURY_2Y' in results:
            yield_curve = results['TREASURY_10Y']['value'] - results['TREASURY_2Y']['value']
            results['YIELD_CURVE'] = {
                'indicator': 'YIELD_CURVE',
                'name': '10Y-2Y Treasury Spread',
                'value': round(yield_curve, 2),
                'inverted': yield_curve < 0,
                'units': 'Percentage Points'
            }

        return results

    def get_recession_indicators(self) -> Dict:
        """Get recession probability indicators"""

        indicators = {}

        # Sahm Rule (unemployment rate)
        unemployment = self.get_latest('UNEMPLOYMENT')
        if 'error' not in unemployment:
            # Simplified Sahm rule calculation
            sahm_triggered = unemployment.get('change', 0) > 0.5
            indicators['sahm_rule'] = {
                'triggered': sahm_triggered,
                'unemployment_rate': unemployment.get('value'),
                'change': unemployment.get('change')
            }

        # Yield curve inversion
        treasury_10y = self.get_latest('TREASURY_10Y')
        treasury_2y = self.get_latest('TREASURY_2Y')
        if 'error' not in treasury_10y and 'error' not in treasury_2y:
            spread = treasury_10y['value'] - treasury_2y['value']
            indicators['yield_curve'] = {
                'spread': round(spread, 2),
                'inverted': spread < 0,
                '10y_rate': treasury_10y['value'],
                '2y_rate': treasury_2y['value']
            }

        # Credit spreads
        credit = self.get_latest('CREDIT_SPREADS')
        if 'error' not in credit:
            indicators['credit_spreads'] = {
                'value': credit.get('value'),
                'elevated': credit.get('value', 0) > 5,
                'trend': credit.get('trend')
            }

        # Leading indicators composite
        jobless = self.get_latest('JOBLESS_CLAIMS')
        housing = self.get_latest('HOUSING_STARTS')

        recession_score = 0
        if indicators.get('sahm_rule', {}).get('triggered'):
            recession_score += 30
        if indicators.get('yield_curve', {}).get('inverted'):
            recession_score += 25
        if indicators.get('credit_spreads', {}).get('elevated'):
            recession_score += 20
        if jobless and jobless.get('trend') == 'rising':
            recession_score += 15
        if housing and housing.get('trend') == 'falling':
            recession_score += 10

        indicators['recession_probability'] = {
            'score': recession_score,
            'risk_level': 'High' if recession_score > 60 else 'Medium' if recession_score > 30 else 'Low',
            'description': self._get_recession_description(recession_score)
        }

        return indicators

    def get_inflation_data(self) -> Dict:
        """Get comprehensive inflation metrics"""

        metrics = {}

        # Core CPI
        cpi = self.get_latest('CPI')
        if 'error' not in cpi:
            metrics['cpi'] = {
                'value': cpi.get('value'),
                'yoy_change': cpi.get('change_percent'),
                'trend': cpi.get('trend'),
                'date': cpi.get('date')
            }

        # Inflation expectations
        expectations = self.get_latest('INFLATION_EXPECTATIONS')
        if 'error' not in expectations:
            metrics['expectations_5y'] = {
                'value': expectations.get('value'),
                'trend': expectations.get('trend')
            }

        # M2 money supply growth
        m2 = self.get_latest('M2')
        if 'error' not in m2:
            metrics['m2_growth'] = {
                'value': m2.get('change_percent'),
                'trend': m2.get('trend')
            }

        # Determine inflation regime
        cpi_value = cpi.get('value') if cpi else None
        if cpi_value is not None:
            if cpi_value > 4:
                regime = 'High Inflation'
            elif cpi_value > 2.5:
                regime = 'Above Target'
            elif cpi_value > 1.5:
                regime = 'On Target'
            else:
                regime = 'Below Target/Deflation Risk'

            metrics['regime'] = regime
            metrics['fed_action_likely'] = 'Hawkish' if cpi_value > 3 else 'Neutral' if cpi_value > 2 else 'Dovish'
        else:
            metrics['regime'] = 'Unknown'
            metrics['fed_action_likely'] = 'Unknown'

        return metrics

    def _get_series_name(self, series_id: str) -> str:
        """Get human-readable name for series"""

        # Reverse lookup in indicators dict
        for name, sid in self.indicators.items():
            if sid == series_id:
                return name.replace('_', ' ').title()

        return series_id

    def _get_recession_description(self, score: int) -> str:
        """Get description based on recession score"""

        if score >= 70:
            return "Very high recession risk. Multiple indicators flashing red."
        elif score >= 50:
            return "Elevated recession risk. Several concerning indicators."
        elif score >= 30:
            return "Moderate recession risk. Some warning signs present."
        elif score >= 15:
            return "Low recession risk. Few concerns at this time."
        else:
            return "Minimal recession risk. Economic indicators generally positive."