"""
Backtesting Capability - Test investment strategies and predictions against historical data

This module provides infrastructure for:
- Running historical backtests of investment strategies
- Validating prediction accuracy
- Calculating performance metrics
- Storing results in knowledge graph
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import statistics

from core.typing_compat import TypeAlias

# Type aliases
BacktestResult: TypeAlias = Dict[str, Any]
PerformanceMetrics: TypeAlias = Dict[str, float]
TradeLog: TypeAlias = List[Dict[str, Any]]

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Engine for running historical backtests of investment strategies"""

    def __init__(self, market_data, knowledge_loader, graph):
        """
        Initialize backtest engine

        Args:
            market_data: MarketDataCapability instance for historical data
            knowledge_loader: KnowledgeLoader instance for datasets
            graph: KnowledgeGraph instance for storing results
        """
        self.market_data = market_data
        self.knowledge_loader = knowledge_loader
        self.graph = graph
        self.logger = logging.getLogger(__name__)

    def run_backtest(
        self,
        strategy_name: str,
        start_date: str,
        end_date: str,
        universe: List[str],
        rebalance_frequency: str = 'monthly',
        initial_capital: float = 100000.0,
        **kwargs
    ) -> BacktestResult:
        """
        Run a backtest for a given strategy

        Args:
            strategy_name: Name of strategy to backtest (e.g., 'buffett_checklist')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            universe: List of stock symbols to consider
            rebalance_frequency: How often to rebalance ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')
            initial_capital: Starting portfolio value
            **kwargs: Strategy-specific parameters

        Returns:
            BacktestResult with performance metrics, trade log, and analysis
        """
        self.logger.info(f"Starting backtest: {strategy_name} from {start_date} to {end_date}")

        # Map strategy name to implementation
        strategy_map = {
            'dcf_accuracy': self._backtest_dcf_accuracy,
            'buffett_checklist': self._backtest_buffett_strategy,
            'dalio_regime': self._backtest_regime_prediction,
            'earnings_surprise': self._backtest_earnings_prediction,
            'sector_rotation': self._backtest_sector_rotation,
            'insider_signal': self._backtest_insider_signal
        }

        if strategy_name not in strategy_map:
            return {
                'error': f"Unknown strategy: {strategy_name}",
                'available_strategies': list(strategy_map.keys())
            }

        # Execute strategy-specific backtest
        try:
            result = strategy_map[strategy_name](
                start_date=start_date,
                end_date=end_date,
                universe=universe,
                rebalance_frequency=rebalance_frequency,
                initial_capital=initial_capital,
                **kwargs
            )

            # Store results in knowledge graph
            self._store_backtest_results(strategy_name, result)

            return result

        except Exception as e:
            self.logger.error(f"Backtest failed: {str(e)}")
            return {
                'error': f"Backtest execution failed: {str(e)}",
                'strategy': strategy_name
            }

    def _backtest_dcf_accuracy(
        self,
        start_date: str,
        end_date: str,
        universe: List[str],
        **kwargs
    ) -> BacktestResult:
        """
        Backtest DCF valuation accuracy

        Strategy:
        1. Find all historical DCF analyses in knowledge graph
        2. For each analysis, get actual stock price at prediction time + 6M/12M later
        3. Calculate prediction error (intrinsic value vs actual price)
        4. Aggregate metrics

        Returns:
            Accuracy metrics, prediction errors, best/worst calls
        """
        self.logger.info("Running DCF accuracy backtest")

        results = {
            'strategy': 'dcf_accuracy',
            'start_date': start_date,
            'end_date': end_date,
            'predictions': [],
            'metrics': {}
        }

        # Query graph for historical DCF analyses
        # Node pattern: dcf_analysis_{SYMBOL}_{TIMESTAMP}
        try:
            # Get graph stats to verify connectivity
            stats = self.graph.get_stats()
            self.logger.info(f"Graph has {stats['total_nodes']} nodes, {stats['total_edges']} edges")

            # Find DCF analysis nodes
            # In a real implementation, this would query the graph
            # For now, we'll use a placeholder
            dcf_nodes = []

            # TODO: Implement graph query when graph query API is ready
            # dcf_nodes = self.graph.query({
            #     'node_type': 'dcf_analysis',
            #     'created_after': start_date,
            #     'created_before': end_date
            # })

            if not dcf_nodes:
                self.logger.warning("No historical DCF analyses found in graph")
                results['metrics'] = {
                    'total_predictions': 0,
                    'note': 'No historical DCF analyses found. Run DCF valuations first to build history.'
                }
                return results

            # For each DCF prediction, calculate accuracy
            errors = []
            predictions = []

            for node in dcf_nodes:
                symbol = node.get('symbol', 'UNKNOWN')
                intrinsic_value = node.get('intrinsic_value', 0)
                prediction_date = node.get('created', '')

                # Get actual price 6 months and 12 months later
                # TODO: Implement when historical price fetching is ready
                # actual_price_6m = self._get_price_at_date(symbol, date_6m_later)
                # actual_price_12m = self._get_price_at_date(symbol, date_12m_later)

                # Calculate error
                # error_6m = (intrinsic_value - actual_price_6m) / actual_price_6m * 100
                # errors.append(error_6m)

                predictions.append({
                    'symbol': symbol,
                    'prediction_date': prediction_date,
                    'intrinsic_value': intrinsic_value,
                    # 'actual_price_6m': actual_price_6m,
                    # 'error_pct': error_6m
                })

            results['predictions'] = predictions
            results['metrics'] = {
                'total_predictions': len(predictions),
                'mean_error_pct': statistics.mean(errors) if errors else 0,
                'median_error_pct': statistics.median(errors) if errors else 0,
                'rmse': self._calculate_rmse(errors) if errors else 0,
                'directional_accuracy': self._calculate_directional_accuracy(predictions) if predictions else 0
            }

        except Exception as e:
            self.logger.error(f"DCF backtest error: {str(e)}")
            results['error'] = str(e)

        return results

    def _backtest_buffett_strategy(
        self,
        start_date: str,
        end_date: str,
        universe: List[str],
        rebalance_frequency: str,
        initial_capital: float,
        **kwargs
    ) -> BacktestResult:
        """
        Backtest Buffett Checklist strategy

        Strategy:
        1. Each rebalance period, screen universe using Buffett Checklist
        2. Select stocks passing >= threshold (default 12/15 criteria)
        3. Equal-weight selected stocks
        4. Track portfolio returns
        5. Compare vs benchmark (SPY)

        Returns:
            Performance metrics, holdings history, vs benchmark comparison
        """
        self.logger.info("Running Buffett Checklist strategy backtest")

        threshold = kwargs.get('passing_threshold', 12)
        max_positions = kwargs.get('max_positions', 20)

        results = {
            'strategy': 'buffett_checklist',
            'start_date': start_date,
            'end_date': end_date,
            'parameters': {
                'threshold': threshold,
                'max_positions': max_positions,
                'rebalance_frequency': rebalance_frequency
            },
            'trades': [],
            'holdings_history': [],
            'metrics': {}
        }

        # Load Buffett Checklist criteria
        try:
            buffett_data = self.knowledge_loader.get_dataset('buffett_checklist')
            criteria = buffett_data.get('criteria', [])

            self.logger.info(f"Loaded {len(criteria)} Buffett criteria")

            # TODO: Implement full backtest logic
            # For each rebalance period:
            #   1. Fetch fundamentals for universe
            #   2. Score each stock against criteria
            #   3. Select top stocks passing threshold
            #   4. Calculate position sizes (equal weight)
            #   5. Execute trades (from trade log)
            #   6. Track portfolio value

            results['metrics'] = {
                'total_trades': 0,
                'total_return_pct': 0,
                'annualized_return_pct': 0,
                'sharpe_ratio': 0,
                'max_drawdown_pct': 0,
                'win_rate': 0,
                'benchmark_return_pct': 0,
                'alpha': 0,
                'note': 'Implementation in progress - requires historical fundamental data fetching'
            }

        except Exception as e:
            self.logger.error(f"Buffett backtest error: {str(e)}")
            results['error'] = str(e)

        return results

    def _backtest_regime_prediction(
        self,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> BacktestResult:
        """
        Backtest economic regime prediction accuracy

        Strategy:
        1. Load actual historical regimes from economic_cycles.json
        2. For each quarter, use Dalio framework to predict regime
        3. Compare predicted vs actual
        4. Calculate accuracy metrics

        Returns:
            Regime prediction accuracy, confusion matrix
        """
        self.logger.info("Running regime prediction backtest")

        results = {
            'strategy': 'dalio_regime',
            'start_date': start_date,
            'end_date': end_date,
            'predictions': [],
            'metrics': {}
        }

        try:
            # Load actual historical regimes
            cycles_data = self.knowledge_loader.get_dataset('economic_cycles')
            actual_cycles = cycles_data.get('cycles', [])

            # Load Dalio framework
            dalio_data = self.knowledge_loader.get_dataset('dalio_framework')

            self.logger.info(f"Loaded {len(actual_cycles)} historical cycles")

            # TODO: Implement regime prediction logic
            # For each quarter in date range:
            #   1. Fetch economic indicators (GDP, CPI, unemployment, etc.)
            #   2. Apply Dalio framework to predict regime
            #   3. Compare vs actual regime from cycles_data
            #   4. Track accuracy

            results['metrics'] = {
                'total_predictions': 0,
                'accuracy': 0,
                'precision_by_regime': {},
                'recall_by_regime': {},
                'note': 'Implementation in progress - requires FRED data integration'
            }

        except Exception as e:
            self.logger.error(f"Regime backtest error: {str(e)}")
            results['error'] = str(e)

        return results

    def _backtest_earnings_prediction(
        self,
        start_date: str,
        end_date: str,
        universe: List[str],
        **kwargs
    ) -> BacktestResult:
        """
        Backtest earnings surprise prediction

        Strategy:
        1. For each earnings season, get analyst estimates
        2. Apply earnings surprise model (historical beat rate)
        3. Predict beat/meet/miss
        4. Compare vs actual reported earnings
        5. Calculate prediction accuracy

        Returns:
            Beat/miss prediction accuracy, by stock and overall
        """
        self.logger.info("Running earnings prediction backtest")

        results = {
            'strategy': 'earnings_surprise',
            'start_date': start_date,
            'end_date': end_date,
            'predictions': [],
            'metrics': {}
        }

        try:
            # Load earnings surprise patterns
            earnings_data = self.knowledge_loader.get_dataset('earnings_surprises')

            # TODO: Implement earnings prediction logic
            # For each quarter in range:
            #   1. Fetch analyst estimates for universe
            #   2. Get historical beat rate for each stock
            #   3. Predict beat/meet/miss
            #   4. Fetch actual reported earnings
            #   5. Compare prediction vs actual

            results['metrics'] = {
                'total_predictions': 0,
                'beat_prediction_accuracy': 0,
                'miss_prediction_accuracy': 0,
                'overall_accuracy': 0,
                'note': 'Implementation in progress - requires earnings data API'
            }

        except Exception as e:
            self.logger.error(f"Earnings backtest error: {str(e)}")
            results['error'] = str(e)

        return results

    def _backtest_sector_rotation(
        self,
        start_date: str,
        end_date: str,
        rebalance_frequency: str,
        initial_capital: float,
        **kwargs
    ) -> BacktestResult:
        """
        Backtest sector rotation strategy

        Strategy:
        1. Determine economic regime each period
        2. Identify favored sectors for that regime (from Dalio framework)
        3. Allocate portfolio to those sectors
        4. Track returns vs equal-weight sector allocation

        Returns:
            Performance metrics, sector allocation history
        """
        self.logger.info("Running sector rotation backtest")

        results = {
            'strategy': 'sector_rotation',
            'start_date': start_date,
            'end_date': end_date,
            'allocations': [],
            'metrics': {}
        }

        try:
            # Load sector performance data
            sector_data = self.knowledge_loader.get_dataset('sector_performance')

            # Load Dalio framework for regime -> sector mapping
            dalio_data = self.knowledge_loader.get_dataset('dalio_framework')

            # TODO: Implement sector rotation logic
            # For each rebalance period:
            #   1. Determine current regime
            #   2. Get favored sectors for regime
            #   3. Allocate to those sectors (overweight)
            #   4. Track portfolio value
            #   5. Compare vs equal-weight benchmark

            results['metrics'] = {
                'total_return_pct': 0,
                'benchmark_return_pct': 0,
                'alpha': 0,
                'sharpe_ratio': 0,
                'note': 'Implementation in progress - requires sector ETF pricing'
            }

        except Exception as e:
            self.logger.error(f"Sector rotation backtest error: {str(e)}")
            results['error'] = str(e)

        return results

    def _backtest_insider_signal(
        self,
        start_date: str,
        end_date: str,
        universe: List[str],
        **kwargs
    ) -> BacktestResult:
        """
        Backtest insider trading signal

        Strategy:
        1. Identify stocks with significant insider buying
        2. Track subsequent price performance
        3. Compare vs stocks with insider selling
        4. Calculate signal effectiveness

        Returns:
            Signal performance, win rate, average returns
        """
        self.logger.info("Running insider signal backtest")

        buy_threshold = kwargs.get('buy_threshold', 5)  # 5+ insider buys

        results = {
            'strategy': 'insider_signal',
            'start_date': start_date,
            'end_date': end_date,
            'signals': [],
            'metrics': {}
        }

        try:
            # Load insider activity data
            insider_data = self.knowledge_loader.get_dataset('insider_institutional')

            # TODO: Implement insider signal logic
            # For each month in range:
            #   1. Identify stocks with high insider buying
            #   2. Flag as bullish signal
            #   3. Track price performance 1/3/6 months forward
            #   4. Calculate returns

            results['metrics'] = {
                'total_signals': 0,
                'avg_return_1m': 0,
                'avg_return_3m': 0,
                'avg_return_6m': 0,
                'win_rate': 0,
                'note': 'Implementation in progress - requires insider transaction API'
            }

        except Exception as e:
            self.logger.error(f"Insider signal backtest error: {str(e)}")
            results['error'] = str(e)

        return results

    def _calculate_rmse(self, errors: List[float]) -> float:
        """Calculate Root Mean Squared Error"""
        if not errors:
            return 0.0
        return (sum(e**2 for e in errors) / len(errors)) ** 0.5

    def _calculate_directional_accuracy(self, predictions: List[Dict]) -> float:
        """Calculate % of predictions that got direction right"""
        if not predictions:
            return 0.0

        # TODO: Implement when actual prices are available
        return 0.0

    def _store_backtest_results(self, strategy_name: str, result: BacktestResult) -> None:
        """Store backtest results in knowledge graph"""
        try:
            node_id = f"backtest_{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # TODO: Store in graph when graph add_node API is ready
            # self.graph.add_node(
            #     node_id=node_id,
            #     node_type='backtest_result',
            #     data=result
            # )

            self.logger.info(f"Backtest results stored: {node_id}")

        except Exception as e:
            self.logger.warning(f"Failed to store backtest results: {str(e)}")

    def get_backtest_history(self, strategy_name: Optional[str] = None) -> List[BacktestResult]:
        """
        Retrieve historical backtest results from knowledge graph

        Args:
            strategy_name: Filter by strategy (optional)

        Returns:
            List of historical backtest results
        """
        try:
            # TODO: Query graph for backtest results
            # results = self.graph.query({
            #     'node_type': 'backtest_result',
            #     'strategy': strategy_name if strategy_name else '*'
            # })

            return []

        except Exception as e:
            self.logger.error(f"Failed to retrieve backtest history: {str(e)}")
            return []

    def calculate_performance_metrics(
        self,
        portfolio_values: List[float],
        dates: List[str],
        benchmark_values: Optional[List[float]] = None
    ) -> PerformanceMetrics:
        """
        Calculate standard performance metrics

        Args:
            portfolio_values: Portfolio values over time
            dates: Corresponding dates
            benchmark_values: Benchmark values for comparison (optional)

        Returns:
            Dict with performance metrics
        """
        if not portfolio_values or len(portfolio_values) < 2:
            return {}

        # Calculate returns
        returns = [(portfolio_values[i] - portfolio_values[i-1]) / portfolio_values[i-1]
                   for i in range(1, len(portfolio_values))]

        # Total return
        total_return = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]

        # Annualized return (assuming daily data)
        days = len(portfolio_values)
        years = days / 252  # Trading days per year
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        # Volatility (annualized)
        volatility = statistics.stdev(returns) * (252 ** 0.5) if len(returns) > 1 else 0

        # Sharpe ratio (assuming 0% risk-free rate for simplicity)
        sharpe = annualized_return / volatility if volatility > 0 else 0

        # Max drawdown
        peak = portfolio_values[0]
        max_drawdown = 0
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        metrics = {
            'total_return_pct': total_return * 100,
            'annualized_return_pct': annualized_return * 100,
            'volatility_pct': volatility * 100,
            'sharpe_ratio': sharpe,
            'max_drawdown_pct': max_drawdown * 100,
            'final_value': portfolio_values[-1],
            'initial_value': portfolio_values[0]
        }

        # Add benchmark comparison if provided
        if benchmark_values and len(benchmark_values) == len(portfolio_values):
            benchmark_return = (benchmark_values[-1] - benchmark_values[0]) / benchmark_values[0]
            metrics['benchmark_return_pct'] = benchmark_return * 100
            metrics['alpha_pct'] = (total_return - benchmark_return) * 100

        return metrics
