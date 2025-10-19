"""
Prediction Service - Store, track, and backtest predictions
Handles prediction persistence, accuracy tracking, and simulation
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid

class PredictionService:
    """Manages predictions, backtesting, and simulations"""
    
    def __init__(self):
        """Initialize prediction service with database connection"""
        self.db_config = {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': os.getenv('PGPORT', '5432'),
            'database': os.getenv('PGDATABASE', 'trinity'),
            'user': os.getenv('PGUSER', 'postgres'),
            'password': os.getenv('PGPASSWORD', '')
        }
        self._init_database()
        
    def _init_database(self):
        """Initialize database tables for predictions"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        # Enable pgcrypto extension for UUID generation
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        
        # Predictions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                prediction_type VARCHAR(50),
                symbol VARCHAR(20),
                target_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                prediction_data JSONB,
                confidence FLOAT,
                status VARCHAR(20) DEFAULT 'pending',
                actual_outcome JSONB,
                accuracy_score FLOAT,
                agent VARCHAR(50),
                model_version VARCHAR(20)
            )
        """)
        
        # Backtests table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS backtests (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                strategy_name VARCHAR(100),
                start_date DATE,
                end_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                parameters JSONB,
                results JSONB,
                performance_metrics JSONB,
                trades JSONB[]
            )
        """)
        
        # Simulations table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS simulations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                simulation_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                parameters JSONB,
                scenarios JSONB[],
                results JSONB,
                probability_distribution JSONB
            )
        """)
        
        # Create indexes for better query performance
        cur.execute("CREATE INDEX IF NOT EXISTS idx_predictions_symbol ON predictions(symbol)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictions(target_date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_predictions_type ON predictions(prediction_type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_backtests_strategy ON backtests(strategy_name)")
        
        conn.commit()
        cur.close()
        conn.close()
        
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def store_prediction(
        self,
        prediction_type: str,
        prediction_data: Dict[str, Any],
        confidence: float,
        target_date: str,
        symbol: Optional[str] = None,
        agent: str = "unknown"
    ) -> str:
        """
        Store a new prediction in the database
        
        Args:
            prediction_type: Type of prediction (price, recession, sector_rotation, etc.)
            prediction_data: The actual prediction details
            confidence: Confidence score (0-100)
            target_date: When the prediction should be evaluated
            symbol: Stock symbol if applicable
            agent: Which agent made the prediction
        
        Returns:
            Prediction ID
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        prediction_id = str(uuid.uuid4())
        
        cur.execute("""
            INSERT INTO predictions 
            (id, prediction_type, symbol, target_date, prediction_data, confidence, agent, model_version)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            prediction_id,
            prediction_type,
            symbol,
            target_date,
            json.dumps(prediction_data),
            confidence,
            agent,
            "3.0.0"
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return prediction_id
    
    def update_prediction_outcome(
        self,
        prediction_id: str,
        actual_outcome: Dict[str, Any],
        accuracy_score: float
    ):
        """Update a prediction with its actual outcome"""
        conn = self._get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE predictions 
            SET actual_outcome = %s, 
                accuracy_score = %s,
                status = 'evaluated'
            WHERE id = %s
        """, (json.dumps(actual_outcome), accuracy_score, prediction_id))
        
        conn.commit()
        cur.close()
        conn.close()
    
    def get_predictions(
        self,
        symbol: Optional[str] = None,
        prediction_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Retrieve predictions with optional filters"""
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = "SELECT * FROM predictions WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = %s"
            params.append(symbol)
        
        if prediction_type:
            query += " AND prediction_type = %s"
            params.append(prediction_type)
            
        if status:
            query += " AND status = %s"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        cur.execute(query, params)
        predictions = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return predictions
    
    def calculate_prediction_accuracy(self, agent: Optional[str] = None) -> Dict[str, float]:
        """Calculate accuracy metrics for predictions"""
        conn = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                prediction_type,
                COUNT(*) as total,
                AVG(accuracy_score) as avg_accuracy,
                STDDEV(accuracy_score) as std_dev,
                MAX(accuracy_score) as best,
                MIN(accuracy_score) as worst
            FROM predictions 
            WHERE status = 'evaluated'
        """
        
        if agent:
            query += " AND agent = %s GROUP BY prediction_type"
            cur.execute(query, (agent,))
        else:
            query += " GROUP BY prediction_type"
            cur.execute(query)
        
        results = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return results
    
    def backtest_strategy(
        self,
        strategy_name: str,
        strategy_logic: callable,
        data: pd.DataFrame,
        initial_capital: float = 100000,
        commission: float = 0.001,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a backtest on historical data
        
        Args:
            strategy_name: Name of the strategy
            strategy_logic: Function that returns signals based on data
            data: Historical price data
            initial_capital: Starting capital
            commission: Transaction cost as percentage
            start_date: Backtest start date
            end_date: Backtest end date
        
        Returns:
            Backtest results with performance metrics
        """
        # Filter data by date range if specified
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
        
        # Run strategy logic
        signals = strategy_logic(data)
        
        # Initialize portfolio
        portfolio = {
            'cash': initial_capital,
            'positions': 0,
            'value': initial_capital,
            'trades': [],
            'equity_curve': []
        }
        
        # Execute trades based on signals
        for i, (date, signal) in enumerate(signals.items()):
            price = data.loc[date, 'close'] if 'close' in data.columns else data.loc[date, 'price']
            
            if signal == 'buy' and portfolio['cash'] > 0:
                # Buy signal
                shares = (portfolio['cash'] * (1 - commission)) / price
                portfolio['positions'] += shares
                portfolio['cash'] = 0
                portfolio['trades'].append({
                    'date': str(date),
                    'action': 'buy',
                    'price': price,
                    'shares': shares,
                    'value': shares * price
                })
                
            elif signal == 'sell' and portfolio['positions'] > 0:
                # Sell signal
                value = portfolio['positions'] * price * (1 - commission)
                portfolio['cash'] += value
                portfolio['trades'].append({
                    'date': str(date),
                    'action': 'sell',
                    'price': price,
                    'shares': portfolio['positions'],
                    'value': value
                })
                portfolio['positions'] = 0
            
            # Calculate portfolio value
            portfolio_value = portfolio['cash'] + (portfolio['positions'] * price if portfolio['positions'] > 0 else 0)
            portfolio['equity_curve'].append({
                'date': str(date),
                'value': portfolio_value
            })
        
        # Calculate performance metrics
        equity_curve = pd.DataFrame(portfolio['equity_curve'])
        if not equity_curve.empty:
            equity_curve['returns'] = equity_curve['value'].pct_change()
            
            metrics = {
                'total_return': (portfolio_value / initial_capital - 1) * 100,
                'sharpe_ratio': self._calculate_sharpe_ratio(equity_curve['returns'].dropna()),
                'max_drawdown': self._calculate_max_drawdown(equity_curve['value']),
                'win_rate': self._calculate_win_rate(portfolio['trades']),
                'total_trades': len(portfolio['trades']),
                'final_value': portfolio_value
            }
        else:
            metrics = {'error': 'No trades executed'}
        
        # Store backtest results
        conn = self._get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO backtests 
            (strategy_name, start_date, end_date, parameters, results, performance_metrics, trades)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            strategy_name,
            start_date or data.index[0].strftime('%Y-%m-%d'),
            end_date or data.index[-1].strftime('%Y-%m-%d'),
            json.dumps({'initial_capital': initial_capital, 'commission': commission}),
            json.dumps({'equity_curve': portfolio['equity_curve']}),
            json.dumps(metrics),
            json.dumps(portfolio['trades'])
        ))
        
        backtest_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            'id': backtest_id,
            'metrics': metrics,
            'trades': portfolio['trades'],
            'equity_curve': portfolio['equity_curve']
        }
    
    def simulate_scenarios(
        self,
        simulation_type: str,
        base_data: Dict[str, Any],
        scenarios: List[Dict[str, Any]],
        monte_carlo_runs: int = 1000
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulations for different scenarios
        
        Args:
            simulation_type: Type of simulation (price, portfolio, economic)
            base_data: Current/base case data
            scenarios: List of scenario parameters
            monte_carlo_runs: Number of simulation runs
        
        Returns:
            Simulation results with probability distributions
        """
        results = []
        
        for scenario in scenarios:
            scenario_results = []
            
            for _ in range(monte_carlo_runs):
                # Add random variation based on scenario parameters
                volatility = scenario.get('volatility', 0.2)
                drift = scenario.get('drift', 0.05)
                time_horizon = scenario.get('days', 252)
                
                # Generate random walk
                daily_returns = np.random.normal(
                    drift / 252,
                    volatility / np.sqrt(252),
                    time_horizon
                )
                
                # Calculate price path
                if 'initial_value' in base_data:
                    price_path = base_data['initial_value'] * np.exp(np.cumsum(daily_returns))
                    final_value = price_path[-1]
                else:
                    final_value = np.exp(np.sum(daily_returns))
                
                scenario_results.append(final_value)
            
            # Calculate statistics for this scenario
            scenario_stats = {
                'scenario': scenario['name'],
                'mean': np.mean(scenario_results),
                'median': np.median(scenario_results),
                'std': np.std(scenario_results),
                'percentile_5': np.percentile(scenario_results, 5),
                'percentile_95': np.percentile(scenario_results, 95),
                'probability_positive': np.sum(np.array(scenario_results) > base_data.get('initial_value', 1)) / monte_carlo_runs
            }
            
            results.append(scenario_stats)
        
        # Store simulation results
        conn = self._get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO simulations 
            (simulation_type, parameters, scenarios, results, probability_distribution)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            simulation_type,
            json.dumps(base_data),
            json.dumps(scenarios),
            json.dumps(results),
            json.dumps({'monte_carlo_runs': monte_carlo_runs})
        ))
        
        simulation_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            'id': simulation_id,
            'results': results,
            'base_case': base_data,
            'scenarios_tested': len(scenarios),
            'simulations_per_scenario': monte_carlo_runs
        }
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) == 0:
            return 0
        excess_returns = returns - risk_free_rate / 252
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std() if excess_returns.std() > 0 else 0
    
    def _calculate_max_drawdown(self, values: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + values.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min() * 100
    
    def _calculate_win_rate(self, trades: List[Dict]) -> float:
        """Calculate win rate from trades"""
        if len(trades) < 2:
            return 0
        
        wins = 0
        for i in range(0, len(trades) - 1, 2):
            if i + 1 < len(trades):
                buy_price = trades[i]['price']
                sell_price = trades[i + 1]['price']
                if sell_price > buy_price:
                    wins += 1
        
        total_pairs = len(trades) // 2
        return (wins / total_pairs * 100) if total_pairs > 0 else 0
    
    def get_recent_predictions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent predictions for display"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, prediction_type, symbol, target_date, 
                       prediction_data, confidence, agent, status,
                       actual_outcome, accuracy_score, created_at
                FROM predictions 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (limit,))
            
            rows = cur.fetchall()
            cur.close()
            conn.close()
            
            predictions = []
            for row in rows:
                predictions.append({
                    'id': row[0],
                    'type': row[1],
                    'symbol': row[2],
                    'target_date': row[3].strftime('%Y-%m-%d') if row[3] else None,
                    'prediction': row[4] if isinstance(row[4], dict) else json.loads(row[4]) if row[4] else {},
                    'confidence': row[5],
                    'agent': row[6],
                    'status': row[7],
                    'outcome': row[8] if isinstance(row[8], dict) else json.loads(row[8]) if row[8] else None,
                    'accuracy': row[9],
                    'created_at': row[10].strftime('%Y-%m-%d %H:%M') if row[10] else None
                })
            
            return predictions
            
        except Exception as e:
            print(f"Error getting recent predictions: {e}")
            # Return empty list if database not available
            return []