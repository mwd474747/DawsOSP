#!/usr/bin/env python3
"""
Options Analyzer - Handles all options analysis calculations

Follows DCFAnalyzer pattern for consistency.
Focuses on options-specific analysis: Greeks, IV, flow sentiment, unusual activity.

Key Methods:
- analyze_greeks: Calculate aggregated Greeks and market positioning
- analyze_flow_sentiment: Analyze put/call ratios for market sentiment
- detect_unusual_activity: Identify smart money signals
- calculate_iv_rank: IV percentile and strategy suggestions
- suggest_hedges: Generate hedge recommendations

Integrates with PolygonOptionsCapability for data fetching.
"""

from typing import Dict, List, Any, Optional
from core.typing_compat import TypeAlias
from datetime import datetime
import logging

# Type aliases
OptionChainData: TypeAlias = Dict[str, Any]
GreeksResult: TypeAlias = Dict[str, Any]
FlowResult: TypeAlias = Dict[str, Any]
UnusualActivityResult: TypeAlias = Dict[str, Any]
IVRankResult: TypeAlias = Dict[str, Any]
HedgeResult: TypeAlias = Dict[str, Any]


class OptionsAnalyzer:
    """
    Performs options analysis: Greeks, flow, unusual activity, IV rank.

    Uses polygon_options capability for data fetching.
    Provides actionable insights for options trading.

    Example:
        analyzer = OptionsAnalyzer(polygon_capability, logger)
        greeks = analyzer.analyze_greeks("SPY")
        print(f"Net Delta: {greeks['net_delta']}")
    """

    def __init__(self, polygon_capability: Any, logger: logging.Logger):
        """Initialize Options Analyzer.

        Args:
            polygon_capability: Polygon options data provider
            logger: Logger instance for tracking calculations
        """
        self.polygon = polygon_capability
        self.logger = logger

    def analyze_greeks(
        self,
        ticker: str,
        expiration: Optional[str] = None
    ) -> GreeksResult:
        """Calculate aggregated Greeks and market positioning.

        Args:
            ticker: Stock symbol (e.g., 'SPY')
            expiration: Optional expiration date filter (YYYY-MM-DD)

        Returns:
            Dictionary containing:
                - net_delta: Aggregated delta (calls + puts)
                - total_gamma: Total gamma exposure
                - max_pain_strike: Strike with highest OI
                - gamma_flip_point: Price where gamma exposure reverses
                - positioning: 'bullish', 'bearish', or 'neutral'
                - confidence: Confidence score (0-1)
        """
        try:
            # Fetch option chain
            chain = self.polygon.get_option_chain(ticker, expiration=expiration)

            if 'error' in chain:
                self.logger.error(f"Failed to fetch chain for {ticker}: {chain['error']}")
                return {
                    'error': chain['error'],
                    'ticker': ticker,
                    'net_delta': 0.0,
                    'positioning': 'unknown'
                }

            calls = chain.get('calls', [])
            puts = chain.get('puts', [])

            # Calculate max pain (strike with highest OI)
            max_pain_strike = self._calculate_max_pain(calls, puts)

            # Calculate net delta and gamma (placeholder - requires contract details)
            net_delta = self._aggregate_delta(calls, puts)
            total_gamma = self._aggregate_gamma(calls, puts)

            # Determine positioning
            positioning = self._determine_positioning(net_delta)

            # Calculate confidence based on data quality
            confidence = self._calculate_confidence(calls, puts)

            return {
                'ticker': ticker,
                'net_delta': net_delta,
                'total_gamma': total_gamma,
                'max_pain_strike': max_pain_strike,
                'gamma_flip_point': 0.0,  # Placeholder
                'positioning': positioning,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error analyzing Greeks for {ticker}: {e}")
            return {
                'error': str(e),
                'ticker': ticker,
                'net_delta': 0.0,
                'positioning': 'unknown'
            }

    def analyze_flow_sentiment(
        self,
        tickers: List[str]
    ) -> FlowResult:
        """Analyze put/call flow for market sentiment.

        Args:
            tickers: List of tickers to analyze (e.g., ['SPY', 'QQQ', 'IWM'])

        Returns:
            Dictionary containing:
                - put_call_ratio: Aggregated P/C ratio
                - sentiment: 'bullish', 'bearish', or 'neutral'
                - confidence: Confidence score (0-1)
                - direction: Directional bias
                - flow_data: Per-ticker flow data
        """
        try:
            flow_data = {}
            total_call_volume = 0
            total_put_volume = 0

            for ticker in tickers:
                chain = self.polygon.get_option_chain(ticker)

                if 'error' in chain:
                    self.logger.warning(f"Skipping {ticker}: {chain['error']}")
                    continue

                calls = chain.get('calls', [])
                puts = chain.get('puts', [])

                # Calculate volume (placeholder - requires detailed contract data)
                call_volume = len(calls) * 100  # Placeholder
                put_volume = len(puts) * 100   # Placeholder

                total_call_volume += call_volume
                total_put_volume += put_volume

                flow_data[ticker] = {
                    'call_volume': call_volume,
                    'put_volume': put_volume,
                    'ratio': put_volume / call_volume if call_volume > 0 else 0
                }

            # Calculate aggregated P/C ratio
            put_call_ratio = total_put_volume / total_call_volume if total_call_volume > 0 else 0

            # Determine sentiment (typical P/C ratio is ~0.7)
            # P/C < 0.7: Bullish (more calls)
            # P/C > 1.2: Bearish (more puts)
            if put_call_ratio < 0.7:
                sentiment = 'bullish'
                direction = 'Upward bias'
            elif put_call_ratio > 1.2:
                sentiment = 'bearish'
                direction = 'Downward bias'
            else:
                sentiment = 'neutral'
                direction = 'No clear bias'

            # Confidence based on volume
            confidence = min(total_call_volume + total_put_volume, 100000) / 100000

            return {
                'put_call_ratio': round(put_call_ratio, 2),
                'sentiment': sentiment,
                'confidence': round(confidence, 2),
                'direction': direction,
                'flow_data': flow_data,
                'tickers': tickers,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error analyzing flow sentiment: {e}")
            return {
                'error': str(e),
                'put_call_ratio': 0.0,
                'sentiment': 'unknown'
            }

    def detect_unusual_activity(
        self,
        min_premium: float = 10000,
        volume_oi_ratio: float = 3.0
    ) -> UnusualActivityResult:
        """Detect unusual options activity (smart money signals).

        Args:
            min_premium: Minimum premium threshold (default: $10k)
            volume_oi_ratio: Minimum volume/OI ratio (default: 3.0)

        Returns:
            Dictionary containing:
                - unusual_activities: List of unusual trades
                - top_tickers: Most active tickers
                - sentiment_score: Bullish/bearish score (-1 to 1)
                - smart_money_signals: High-confidence signals
        """
        try:
            # Fetch unusual activity from Polygon
            unusual = self.polygon.detect_unusual_activity(
                min_premium=min_premium,
                volume_oi_ratio=volume_oi_ratio
            )

            # For now, placeholder since this requires higher-tier API access
            self.logger.info(f"Scanning for unusual activity (min_premium: ${min_premium})")

            return {
                'unusual_activities': unusual,
                'top_tickers': [],
                'sentiment_score': 0.0,
                'smart_money_signals': [],
                'filters': {
                    'min_premium': min_premium,
                    'volume_oi_ratio': volume_oi_ratio
                },
                'note': 'Full implementation requires Polygon Starter+ tier',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error detecting unusual activity: {e}")
            return {
                'error': str(e),
                'unusual_activities': []
            }

    def calculate_iv_rank(
        self,
        ticker: str,
        lookback_days: int = 252
    ) -> IVRankResult:
        """Calculate IV rank and suggest strategies.

        Args:
            ticker: Stock symbol
            lookback_days: Days to look back (default: 252 = 1 year)

        Returns:
            Dictionary containing:
                - iv_rank: IV rank (0-100)
                - iv_percentile: IV percentile (0-100)
                - regime: 'high', 'medium', or 'low'
                - suggested_strategies: List of appropriate strategies
        """
        try:
            # Fetch IV rank from Polygon
            iv_data = self.polygon.calculate_iv_rank(ticker, lookback_days)

            # Determine regime and suggest strategies
            iv_rank = iv_data.get('iv_rank', 0)

            if iv_rank > 80:
                regime = 'high'
                strategies = [
                    'Sell premium (iron condors, covered calls)',
                    'Short straddles/strangles',
                    'Calendar spreads'
                ]
            elif iv_rank < 20:
                regime = 'low'
                strategies = [
                    'Buy options (long calls/puts)',
                    'Debit spreads',
                    'Backspreads'
                ]
            else:
                regime = 'medium'
                strategies = [
                    'Neutral strategies (butterflies, iron condors)',
                    'Diagonal spreads',
                    'Ratio spreads'
                ]

            return {
                'ticker': ticker,
                'iv_rank': iv_rank,
                'iv_percentile': iv_data.get('iv_percentile', 0),
                'current_iv': iv_data.get('current_iv', 0),
                'high_52w': iv_data.get('high_52w', 0),
                'low_52w': iv_data.get('low_52w', 0),
                'regime': regime,
                'suggested_strategies': strategies,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error calculating IV rank for {ticker}: {e}")
            return {
                'error': str(e),
                'ticker': ticker,
                'iv_rank': 0.0
            }

    def suggest_hedges(
        self,
        ticker: str,
        portfolio_value: float
    ) -> HedgeResult:
        """Generate hedge recommendations.

        Args:
            ticker: Stock symbol to hedge
            portfolio_value: Portfolio value to hedge

        Returns:
            Dictionary containing:
                - protective_puts: OTM put recommendations
                - collar_strategy: Collar (buy put, sell call) details
                - vix_hedge: VIX hedge for SPY positions
                - cost_analysis: Monthly and annual cost
        """
        try:
            # Fetch option chain
            chain = self.polygon.get_option_chain(ticker)

            if 'error' in chain:
                return {'error': chain['error']}

            # Placeholder for hedge calculations
            # Full implementation requires current stock price and option pricing

            return {
                'ticker': ticker,
                'portfolio_value': portfolio_value,
                'protective_puts': [],
                'collar_strategy': {},
                'vix_hedge': {},
                'cost_analysis': {
                    'monthly': 0.0,
                    'annual': 0.0
                },
                'note': 'Placeholder - requires option pricing data',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error suggesting hedges for {ticker}: {e}")
            return {
                'error': str(e),
                'protective_puts': []
            }

    # Helper methods

    def _calculate_max_pain(
        self,
        calls: List[Dict],
        puts: List[Dict]
    ) -> float:
        """Find strike with highest open interest (max pain)."""
        # Placeholder - requires OI data from contract details
        return 0.0

    def _aggregate_delta(
        self,
        calls: List[Dict],
        puts: List[Dict]
    ) -> float:
        """Calculate net delta across all contracts."""
        # Placeholder - requires delta from contract details
        return 0.0

    def _aggregate_gamma(
        self,
        calls: List[Dict],
        puts: List[Dict]
    ) -> float:
        """Calculate total gamma exposure."""
        # Placeholder - requires gamma from contract details
        return 0.0

    def _determine_positioning(self, net_delta: float) -> str:
        """Determine market positioning from net delta."""
        if net_delta > 0.2:
            return 'bullish'
        elif net_delta < -0.2:
            return 'bearish'
        else:
            return 'neutral'

    def _calculate_confidence(
        self,
        calls: List[Dict],
        puts: List[Dict]
    ) -> float:
        """Calculate confidence score based on data quality."""
        # More contracts = higher confidence
        total_contracts = len(calls) + len(puts)
        return min(total_contracts / 100, 1.0)  # Cap at 1.0
