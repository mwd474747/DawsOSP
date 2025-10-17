"""
Backtest Agent - Runs historical backtests of investment strategies

This agent coordinates backtesting activities:
- Executes strategy backtests
- Validates prediction accuracy
- Generates performance reports
- Tracks historical results
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from agents.base_agent import BaseAgent


class BacktestAgent(BaseAgent):
    """Agent specialized in running strategy backtests and validating predictions"""

    def __init__(self, runtime, market_data_capability, knowledge_loader, graph):
        """
        Initialize Backtest Agent

        Args:
            runtime: AgentRuntime instance
            market_data_capability: MarketDataCapability for historical data
            knowledge_loader: KnowledgeLoader for datasets
            graph: KnowledgeGraph for storing results
        """
        super().__init__(name="backtest_agent", role="Backtesting Specialist", runtime=runtime)

        # Import here to avoid circular dependency
        from capabilities.backtesting import BacktestEngine

        self.backtest_engine = BacktestEngine(
            market_data=market_data_capability,
            knowledge_loader=knowledge_loader,
            graph=graph
        )
        self.logger = logging.getLogger(__name__)

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process backtest requests

        Args:
            context: Request context with backtest parameters

        Returns:
            Backtest results and analysis
        """
        request_type = context.get('request_type', 'run_backtest')

        if request_type == 'run_backtest':
            return self._run_backtest(context)
        elif request_type == 'get_history':
            return self._get_backtest_history(context)
        elif request_type == 'list_strategies':
            return self._list_available_strategies()
        else:
            return {
                'error': f"Unknown request type: {request_type}",
                'available_types': ['run_backtest', 'get_history', 'list_strategies']
            }

    def _run_backtest(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a backtest

        Args:
            context: Must include strategy_name, start_date, end_date, universe

        Returns:
            Backtest results with metrics and analysis
        """
        # Extract parameters
        strategy_name = context.get('strategy_name', '')
        start_date = context.get('start_date', '')
        end_date = context.get('end_date', '')
        universe = context.get('universe', [])
        rebalance_frequency = context.get('rebalance_frequency', 'monthly')
        initial_capital = context.get('initial_capital', 100000.0)

        # Validate inputs
        if not all([strategy_name, start_date, end_date]):
            return {
                'error': 'Missing required parameters: strategy_name, start_date, end_date',
                'received': context
            }

        self.logger.info(f"Running backtest: {strategy_name} ({start_date} to {end_date})")

        # Run backtest
        result = self.backtest_engine.run_backtest(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            universe=universe,
            rebalance_frequency=rebalance_frequency,
            initial_capital=initial_capital,
            **context  # Pass through any additional parameters
        )

        # Add metadata
        result['agent'] = self.name
        result['timestamp'] = datetime.now().isoformat()

        return result

    def _get_backtest_history(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve historical backtest results

        Args:
            context: Optional strategy_name filter

        Returns:
            List of historical backtest results
        """
        strategy_name = context.get('strategy_name')

        history = self.backtest_engine.get_backtest_history(strategy_name)

        return {
            'history': history,
            'count': len(history),
            'filter': strategy_name if strategy_name else 'all'
        }

    def _list_available_strategies(self) -> Dict[str, Any]:
        """
        List available backtest strategies

        Returns:
            List of strategy names and descriptions
        """
        strategies = [
            {
                'name': 'dcf_accuracy',
                'description': 'DCF Valuation Accuracy - Compare intrinsic value predictions vs actual prices',
                'type': 'validation',
                'data_required': ['historical DCF analyses in graph', 'stock prices']
            },
            {
                'name': 'buffett_checklist',
                'description': 'Buffett Checklist Strategy - Screen stocks using quality criteria, track returns',
                'type': 'strategy',
                'data_required': ['fundamental data', 'stock prices']
            },
            {
                'name': 'dalio_regime',
                'description': 'Economic Regime Prediction - Validate regime predictions vs actual outcomes',
                'type': 'validation',
                'data_required': ['economic indicators', 'economic_cycles dataset']
            },
            {
                'name': 'earnings_surprise',
                'description': 'Earnings Surprise Prediction - Test beat/miss predictions vs actual earnings',
                'type': 'validation',
                'data_required': ['analyst estimates', 'actual earnings']
            },
            {
                'name': 'sector_rotation',
                'description': 'Sector Rotation Strategy - Allocate based on economic regime, track performance',
                'type': 'strategy',
                'data_required': ['economic regime', 'sector prices']
            },
            {
                'name': 'insider_signal',
                'description': 'Insider Trading Signal - Track returns following insider buying activity',
                'type': 'signal',
                'data_required': ['insider transactions', 'stock prices']
            }
        ]

        return {
            'strategies': strategies,
            'count': len(strategies),
            'agent': self.name
        }

    def think(self, context: Dict[str, Any]) -> str:
        """
        Provide strategic insights about backtesting

        Args:
            context: Context for analysis

        Returns:
            Analysis and recommendations
        """
        strategy = context.get('strategy_name', 'unknown')

        insights = f"""
        Backtesting Strategy: {strategy}

        Key Considerations:
        1. Look-ahead bias: Ensure we only use data available at prediction time
        2. Survivorship bias: Include delisted stocks in historical universe
        3. Transaction costs: Account for commissions and slippage
        4. Data quality: Verify historical data accuracy
        5. Sample size: Ensure sufficient data points for statistical significance

        Best Practices:
        - Use walk-forward optimization to avoid overfitting
        - Compare against relevant benchmark
        - Test across multiple market regimes
        - Calculate risk-adjusted returns (Sharpe, Sortino)
        - Track drawdowns and recovery periods
        """

        return insights.strip()

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze backtest results

        Args:
            data: Backtest results to analyze

        Returns:
            Analysis with strengths, weaknesses, recommendations
        """
        metrics = data.get('metrics', {})

        # Extract key metrics
        total_return = metrics.get('total_return_pct', 0)
        sharpe = metrics.get('sharpe_ratio', 0)
        max_dd = metrics.get('max_drawdown_pct', 0)
        alpha = metrics.get('alpha_pct', 0)

        # Analyze performance
        strengths = []
        weaknesses = []

        if total_return > 10:
            strengths.append(f"Strong total return of {total_return:.1f}%")
        elif total_return < 0:
            weaknesses.append(f"Negative total return of {total_return:.1f}%")

        if sharpe > 1.0:
            strengths.append(f"Excellent risk-adjusted returns (Sharpe: {sharpe:.2f})")
        elif sharpe < 0:
            weaknesses.append(f"Poor risk-adjusted returns (Sharpe: {sharpe:.2f})")

        if max_dd < 15:
            strengths.append(f"Limited downside risk (Max DD: {max_dd:.1f}%)")
        elif max_dd > 30:
            weaknesses.append(f"Significant drawdown risk (Max DD: {max_dd:.1f}%)")

        if alpha > 0:
            strengths.append(f"Outperformed benchmark by {alpha:.1f}%")
        elif alpha < -5:
            weaknesses.append(f"Underperformed benchmark by {abs(alpha):.1f}%")

        # Generate recommendations
        recommendations = []

        if max_dd > 20:
            recommendations.append("Consider adding stop-loss rules to limit drawdowns")

        if sharpe < 0.5:
            recommendations.append("Review position sizing and rebalancing frequency")

        if alpha < 0:
            recommendations.append("Compare strategy vs passive index - may not justify active management")

        return {
            'strengths': strengths if strengths else ['No clear strengths identified'],
            'weaknesses': weaknesses if weaknesses else ['No major weaknesses identified'],
            'recommendations': recommendations if recommendations else ['Strategy appears sound'],
            'overall_assessment': self._get_overall_assessment(total_return, sharpe, max_dd, alpha)
        }

    def _get_overall_assessment(
        self,
        total_return: float,
        sharpe: float,
        max_dd: float,
        alpha: float
    ) -> str:
        """Generate overall assessment of strategy"""

        if total_return > 15 and sharpe > 1.0 and max_dd < 20:
            return "Excellent - Strong performance with good risk management"
        elif total_return > 10 and sharpe > 0.5:
            return "Good - Positive returns with acceptable risk"
        elif total_return > 0:
            return "Adequate - Modest positive returns"
        elif total_return > -5:
            return "Weak - Minimal or negative returns"
        else:
            return "Poor - Significant losses, strategy needs revision"

    def get_capabilities(self) -> list:
        """Return list of capabilities this agent provides"""
        return [
            'can_run_backtest',
            'can_validate_predictions',
            'can_analyze_strategy_performance',
            'can_calculate_performance_metrics'
        ]
