#!/usr/bin/env python3
"""
Seed Portfolio Performance Data
================================
Creates realistic performance data for the existing demo portfolio
to enable dashboard and performance features.

Generates:
1. Realistic NAV movements in portfolio_daily_values
2. Daily portfolio metrics (TWR, MWR, Sharpe, volatility)
3. Proper performance calculations

Author: DawsOS
Date: November 2025
"""

import asyncio
import asyncpg
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
import os
import logging
from uuid import UUID
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Portfolio configuration
PORTFOLIO_ID = UUID('64ff3be6-0ed1-4990-a32b-4ded17f0320c')
INITIAL_VALUE = 280870.00  # Initial portfolio value from lots cost basis
TARGET_VALUE = 1638500.00  # Current portfolio value
START_DATE = date(2023, 12, 1)
END_DATE = date(2025, 10, 31)

# Market parameters for realistic simulation
ANNUAL_RETURN = 0.145  # 14.5% annual return (to reach target)
ANNUAL_VOLATILITY = 0.182  # 18.2% annual volatility
RISK_FREE_RATE = 0.035  # 3.5% risk-free rate
TRADING_DAYS_PER_YEAR = 252

# Seed for reproducibility
np.random.seed(42)


class PerformanceSeeder:
    """Seeds realistic performance data for portfolio"""
    
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
        
    async def generate_nav_history(self) -> pd.DataFrame:
        """Generate realistic NAV history with proper volatility"""
        
        # Create date range
        dates = pd.date_range(start=START_DATE, end=END_DATE, freq='D')
        num_days = len(dates)
        
        # Calculate required growth
        total_return_needed = (TARGET_VALUE / INITIAL_VALUE) - 1
        daily_return = (1 + total_return_needed) ** (1 / num_days) - 1
        
        # Generate returns with realistic volatility
        daily_vol = ANNUAL_VOLATILITY / np.sqrt(TRADING_DAYS_PER_YEAR)
        
        # Create correlated returns (trending with noise)
        trend = np.linspace(0, total_return_needed, num_days)
        noise = np.random.normal(0, daily_vol, num_days)
        
        # Add market regime changes (bull/bear periods)
        regime_changes = self._generate_market_regimes(num_days)
        noise = noise * regime_changes
        
        # Calculate cumulative returns
        cumulative_returns = np.zeros(num_days)
        nav_values = np.zeros(num_days)
        nav_values[0] = INITIAL_VALUE
        
        for i in range(1, num_days):
            # Combine trend with noise
            period_return = trend[i] - trend[i-1] + noise[i]
            
            # Apply to NAV
            nav_values[i] = nav_values[i-1] * (1 + period_return)
            
            # Ensure we don't go negative
            nav_values[i] = max(nav_values[i], INITIAL_VALUE * 0.5)
        
        # Adjust final value to match target
        scaling_factor = TARGET_VALUE / nav_values[-1]
        nav_values = nav_values * scaling_factor
        
        # Create DataFrame
        df = pd.DataFrame({
            'valuation_date': dates,
            'total_value': nav_values,
            'cash_balance': nav_values * 0.82,  # ~82% cash based on current data
            'positions_value': nav_values * 0.18,  # ~18% positions
            'currency': 'USD'
        })
        
        # Add some cash flows based on transactions
        df = self._add_cash_flows(df)
        
        return df
    
    def _generate_market_regimes(self, num_days: int) -> np.ndarray:
        """Generate market regime changes (bull/bear cycles)"""
        regimes = np.ones(num_days)
        
        # Define regime periods
        regime_periods = [
            (0, 90, 1.2),      # Initial bull
            (90, 150, 0.8),    # Correction
            (150, 300, 1.1),   # Recovery
            (300, 400, 0.7),   # Bear phase
            (400, 550, 1.3),   # Strong bull
            (550, 600, 0.9),   # Consolidation
            (600, num_days, 1.1)  # Final bull
        ]
        
        for start, end, multiplier in regime_periods:
            if end > num_days:
                end = num_days
            regimes[start:end] = multiplier
            
        return regimes
    
    def _add_cash_flows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add cash flows from transactions"""
        
        # Transaction dates from database
        transaction_dates = [
            ('2024-02-15', 350.00),   # Dividend
            ('2024-03-15', 280.00),   # Dividend
            ('2024-05-15', 420.00),   # Dividend
            ('2024-06-15', 315.00),   # Dividend
            ('2024-07-15', -15000.00), # Sell
            ('2024-08-15', 385.00),   # Dividend
            ('2024-09-15', 490.00),   # Dividend
            ('2024-10-01', -12000.00), # Sell
        ]
        
        for date_str, amount in transaction_dates:
            date_obj = pd.to_datetime(date_str).date()
            if date_obj in df['valuation_date'].dt.date.values:
                idx = df[df['valuation_date'].dt.date == date_obj].index[0]
                df.loc[idx, 'cash_flows'] = amount
            
        df['cash_flows'] = df['cash_flows'].fillna(0)
        
        return df
    
    async def calculate_metrics(self, nav_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate daily portfolio metrics"""
        
        metrics_list = []
        nav_values = nav_df['total_value'].values
        dates = nav_df['valuation_date'].values
        
        # Calculate total return for inception calculation
        total_return_needed = (TARGET_VALUE / INITIAL_VALUE) - 1
        
        for i in range(len(dates)):
            date = dates[i]
            
            # Calculate returns for different periods
            twr_1d = self._calculate_return(nav_values, i, 1)
            twr_mtd = self._calculate_mtd_return(nav_values, dates, i)
            twr_qtd = self._calculate_qtd_return(nav_values, dates, i)
            twr_ytd = self._calculate_ytd_return(nav_values, dates, i)
            twr_1y = self._calculate_return(nav_values, i, 252)
            
            # Calculate volatility for different periods
            vol_30d = self._calculate_volatility(nav_values, i, 30)
            vol_60d = self._calculate_volatility(nav_values, i, 60)
            vol_90d = self._calculate_volatility(nav_values, i, 90)
            vol_1y = self._calculate_volatility(nav_values, i, 252)
            
            # Calculate Sharpe ratio
            sharpe_1y = self._calculate_sharpe(twr_1y, vol_1y)
            
            # Calculate max drawdown
            max_dd_1y = self._calculate_max_drawdown(nav_values, i, 252)
            
            # Money-weighted returns (simplified - would need cash flows)
            mwr_ytd = twr_ytd * 0.95  # Slightly lower due to cash flows
            mwr_1y = twr_1y * 0.95
            
            # Calculate inception return
            inception_return = (nav_values[i] / INITIAL_VALUE) - 1 if INITIAL_VALUE > 0 else 0
            days_since_inception = max(1, i + 1)  # Avoid division by zero
            inception_ann = ((1 + inception_return) ** (365 / days_since_inception)) - 1 if days_since_inception > 0 else 0
            
            # Calculate additional Sharpe ratios for different periods
            sharpe_30d = self._calculate_sharpe(self._calculate_return(nav_values, i, 30), vol_30d)
            sharpe_60d = self._calculate_sharpe(self._calculate_return(nav_values, i, 60), vol_60d)
            sharpe_90d = self._calculate_sharpe(self._calculate_return(nav_values, i, 90), vol_90d)
            
            # Calculate current drawdown
            if i > 0:
                running_max = np.max(nav_values[:i+1])
                current_dd = (nav_values[i] - running_max) / running_max if running_max > 0 else 0
            else:
                current_dd = 0
            
            # Calculate alpha and beta (simplified for demo)
            market_return = 0.12  # Assume 12% market return
            alpha_1y = max(0, twr_1y - (market_return * 0.85))  # Excess return over beta-adjusted market
            
            # Win rate calculation (simplified - based on daily returns)
            if i > 252:
                period_returns = np.diff(nav_values[i-252:i+1]) / nav_values[i-252:i]
                win_rate = np.sum(period_returns > 0) / len(period_returns) if len(period_returns) > 0 else 0.5
                avg_win = np.mean(period_returns[period_returns > 0]) if np.sum(period_returns > 0) > 0 else 0
                avg_loss = np.mean(np.abs(period_returns[period_returns < 0])) if np.sum(period_returns < 0) > 0 else 0
            else:
                win_rate = 0.52  # Default to slightly positive
                avg_win = 0.015
                avg_loss = 0.012
            
            metrics = {
                'portfolio_id': PORTFOLIO_ID,
                'asof_date': date,
                'pricing_pack_id': f'PP_{pd.to_datetime(date).strftime("%Y-%m-%d")}',
                'twr_1d': twr_1d,
                'twr_1d_base': twr_1d,
                'twr_mtd': twr_mtd,
                'twr_qtd': twr_qtd,
                'twr_ytd': twr_ytd,
                'twr_1y': twr_1y,
                'twr_3y_ann': twr_1y * 0.9,  # Simplified
                'twr_5y_ann': twr_1y * 0.85,  # Simplified
                'twr_inception_ann': inception_ann,
                'mwr_ytd': mwr_ytd,
                'mwr_1y': mwr_1y,
                'mwr_3y_ann': mwr_1y * 0.9,
                'mwr_inception_ann': inception_ann * 0.95,  # Slightly lower for MWR
                'volatility_30d': vol_30d,
                'volatility_60d': vol_60d,
                'volatility_90d': vol_90d,
                'volatility_1y': vol_1y,
                'sharpe_30d': sharpe_30d,
                'sharpe_60d': sharpe_60d,
                'sharpe_90d': sharpe_90d,
                'sharpe_1y': sharpe_1y,
                'max_drawdown_1y': max_dd_1y,
                'max_drawdown_3y': max_dd_1y * 1.2,  # Assume slightly worse over 3y
                'current_drawdown': current_dd,
                'alpha_1y': alpha_1y,
                'alpha_3y_ann': alpha_1y * 0.8,  # Conservative for 3y
                'beta_1y': 0.85 + np.random.normal(0, 0.05),  # Market beta
                'beta_3y': 0.82 + np.random.normal(0, 0.03),
                'tracking_error_1y': 0.08 + np.random.normal(0, 0.01),
                'information_ratio_1y': 0.5 + np.random.normal(0, 0.1),
                'win_rate_1y': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'portfolio_value_base': nav_values[i],
                'portfolio_value_local': nav_values[i],
                'cash_balance': nav_values[i] * 0.82,  # ~82% cash based on current data
                'base_currency': 'USD',
                'benchmark_id': 'SPY',
                'reconciliation_error_bps': np.random.normal(0, 2)  # Small reconciliation errors
            }
            
            metrics_list.append(metrics)
        
        return pd.DataFrame(metrics_list)
    
    def _calculate_return(self, values: np.ndarray, current_idx: int, lookback: int) -> float:
        """Calculate return over lookback period"""
        if current_idx < lookback:
            return 0.0
        
        current = values[current_idx]
        previous = values[current_idx - lookback]
        
        if previous == 0:
            return 0.0
            
        return (current / previous) - 1
    
    def _calculate_mtd_return(self, values: np.ndarray, dates: np.ndarray, current_idx: int) -> float:
        """Calculate month-to-date return"""
        current_date = pd.to_datetime(dates[current_idx])
        month_start = current_date.replace(day=1)
        
        # Find month start index
        for i in range(current_idx, -1, -1):
            if pd.to_datetime(dates[i]) < month_start:
                if i < len(dates) - 1:
                    return self._calculate_return(values, current_idx, current_idx - i - 1)
                break
        
        return 0.0
    
    def _calculate_qtd_return(self, values: np.ndarray, dates: np.ndarray, current_idx: int) -> float:
        """Calculate quarter-to-date return"""
        current_date = pd.to_datetime(dates[current_idx])
        quarter_start = current_date.replace(month=((current_date.month-1)//3)*3+1, day=1)
        
        # Find quarter start index
        for i in range(current_idx, -1, -1):
            if pd.to_datetime(dates[i]) < quarter_start:
                if i < len(dates) - 1:
                    return self._calculate_return(values, current_idx, current_idx - i - 1)
                break
        
        return 0.0
    
    def _calculate_ytd_return(self, values: np.ndarray, dates: np.ndarray, current_idx: int) -> float:
        """Calculate year-to-date return"""
        current_date = pd.to_datetime(dates[current_idx])
        year_start = current_date.replace(month=1, day=1)
        
        # Find year start index
        for i in range(current_idx, -1, -1):
            if pd.to_datetime(dates[i]) < year_start:
                if i < len(dates) - 1:
                    return self._calculate_return(values, current_idx, current_idx - i - 1)
                break
        
        return 0.0
    
    def _calculate_volatility(self, values: np.ndarray, current_idx: int, lookback: int) -> float:
        """Calculate annualized volatility"""
        if current_idx < lookback:
            return 0.0
        
        # Get daily returns
        period_values = values[current_idx - lookback:current_idx + 1]
        daily_returns = np.diff(period_values) / period_values[:-1]
        
        if len(daily_returns) == 0:
            return 0.0
        
        # Annualize
        return np.std(daily_returns) * np.sqrt(TRADING_DAYS_PER_YEAR)
    
    def _calculate_sharpe(self, return_1y: float, vol_1y: float) -> float:
        """Calculate Sharpe ratio"""
        if vol_1y == 0:
            return 0.0
        
        return (return_1y - RISK_FREE_RATE) / vol_1y
    
    def _calculate_max_drawdown(self, values: np.ndarray, current_idx: int, lookback: int) -> float:
        """Calculate maximum drawdown"""
        if current_idx < lookback:
            return 0.0
        
        period_values = values[current_idx - lookback:current_idx + 1]
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(period_values)
        
        # Calculate drawdown
        drawdown = (period_values - running_max) / running_max
        
        return np.min(drawdown)
    
    async def update_nav_history(self, nav_df: pd.DataFrame):
        """Update portfolio_daily_values table"""
        
        logger.info(f"Updating {len(nav_df)} NAV history records...")
        
        # Delete existing records
        await self.conn.execute(
            "DELETE FROM portfolio_daily_values WHERE portfolio_id = $1",
            PORTFOLIO_ID
        )
        
        # Insert new records
        for _, row in nav_df.iterrows():
            await self.conn.execute("""
                INSERT INTO portfolio_daily_values (
                    portfolio_id, valuation_date, total_value, 
                    cash_balance, positions_value, cash_flows, 
                    currency, computed_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                PORTFOLIO_ID,
                row['valuation_date'].date() if hasattr(row['valuation_date'], 'date') else row['valuation_date'],
                Decimal(str(row['total_value'])),
                Decimal(str(row['cash_balance'])),
                Decimal(str(row['positions_value'])),
                Decimal(str(row.get('cash_flows', 0))),
                row['currency'],
                datetime.now()
            )
        
        logger.info("NAV history updated successfully")
    
    async def insert_metrics(self, metrics_df: pd.DataFrame):
        """Insert portfolio metrics"""
        
        logger.info(f"Inserting {len(metrics_df)} portfolio metrics...")
        
        # Delete existing metrics
        await self.conn.execute(
            "DELETE FROM portfolio_metrics WHERE portfolio_id = $1",
            PORTFOLIO_ID
        )
        
        # Insert new metrics
        for _, row in metrics_df.iterrows():
            # Convert pandas Timestamp to date if needed
            asof_date = row['asof_date']
            if hasattr(asof_date, 'date'):
                asof_date = asof_date.date()
            
            await self.conn.execute("""
                INSERT INTO portfolio_metrics (
                    portfolio_id, asof_date, pricing_pack_id,
                    twr_1d, twr_1d_base, twr_mtd, twr_qtd, twr_ytd, twr_1y,
                    twr_3y_ann, twr_5y_ann, twr_inception_ann,
                    mwr_ytd, mwr_1y, mwr_3y_ann, mwr_inception_ann,
                    volatility_30d, volatility_60d, volatility_90d, volatility_1y,
                    sharpe_30d, sharpe_60d, sharpe_90d, sharpe_1y,
                    max_drawdown_1y, max_drawdown_3y, current_drawdown,
                    alpha_1y, alpha_3y_ann, beta_1y, beta_3y,
                    tracking_error_1y, information_ratio_1y,
                    win_rate_1y, avg_win, avg_loss,
                    portfolio_value_base, portfolio_value_local, cash_balance,
                    base_currency, benchmark_id, reconciliation_error_bps
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                    $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24,
                    $25, $26, $27, $28, $29, $30, $31, $32, $33, $34, $35, $36,
                    $37, $38, $39, $40, $41, $42
                )
            """,
                PORTFOLIO_ID,
                asof_date,
                row['pricing_pack_id'],
                Decimal(str(row['twr_1d'])),
                Decimal(str(row['twr_1d_base'])),
                Decimal(str(row['twr_mtd'])) if not pd.isna(row['twr_mtd']) else None,
                Decimal(str(row['twr_qtd'])) if not pd.isna(row['twr_qtd']) else None,
                Decimal(str(row['twr_ytd'])),
                Decimal(str(row['twr_1y'])),
                Decimal(str(row['twr_3y_ann'])) if not pd.isna(row['twr_3y_ann']) else None,
                Decimal(str(row['twr_5y_ann'])) if not pd.isna(row['twr_5y_ann']) else None,
                Decimal(str(row['twr_inception_ann'])) if not pd.isna(row['twr_inception_ann']) else None,
                Decimal(str(row['mwr_ytd'])) if not pd.isna(row['mwr_ytd']) else None,
                Decimal(str(row['mwr_1y'])) if not pd.isna(row['mwr_1y']) else None,
                Decimal(str(row['mwr_3y_ann'])) if not pd.isna(row['mwr_3y_ann']) else None,
                Decimal(str(row['mwr_inception_ann'])) if not pd.isna(row['mwr_inception_ann']) else None,
                Decimal(str(row['volatility_30d'])) if not pd.isna(row['volatility_30d']) else None,
                Decimal(str(row['volatility_60d'])) if not pd.isna(row['volatility_60d']) else None,
                Decimal(str(row['volatility_90d'])) if not pd.isna(row['volatility_90d']) else None,
                Decimal(str(row['volatility_1y'])),
                Decimal(str(row['sharpe_30d'])) if not pd.isna(row['sharpe_30d']) else None,
                Decimal(str(row['sharpe_60d'])) if not pd.isna(row['sharpe_60d']) else None,
                Decimal(str(row['sharpe_90d'])) if not pd.isna(row['sharpe_90d']) else None,
                Decimal(str(row['sharpe_1y'])),
                Decimal(str(row['max_drawdown_1y'])),
                Decimal(str(row['max_drawdown_3y'])) if not pd.isna(row['max_drawdown_3y']) else None,
                Decimal(str(row['current_drawdown'])),
                Decimal(str(row['alpha_1y'])) if not pd.isna(row['alpha_1y']) else None,
                Decimal(str(row['alpha_3y_ann'])) if not pd.isna(row['alpha_3y_ann']) else None,
                Decimal(str(row['beta_1y'])) if not pd.isna(row['beta_1y']) else None,
                Decimal(str(row['beta_3y'])) if not pd.isna(row['beta_3y']) else None,
                Decimal(str(row['tracking_error_1y'])) if not pd.isna(row['tracking_error_1y']) else None,
                Decimal(str(row['information_ratio_1y'])) if not pd.isna(row['information_ratio_1y']) else None,
                Decimal(str(row['win_rate_1y'])) if not pd.isna(row['win_rate_1y']) else None,
                Decimal(str(row['avg_win'])) if not pd.isna(row['avg_win']) else None,
                Decimal(str(row['avg_loss'])) if not pd.isna(row['avg_loss']) else None,
                Decimal(str(row['portfolio_value_base'])),
                Decimal(str(row['portfolio_value_local'])),
                Decimal(str(row['cash_balance'])),
                row['base_currency'],
                row['benchmark_id'],
                Decimal(str(row['reconciliation_error_bps'])) if not pd.isna(row['reconciliation_error_bps']) else None
            )
        
        logger.info("Portfolio metrics inserted successfully")
    
    async def create_pricing_packs(self, dates):
        """Create pricing packs for all dates"""
        logger.info("Creating pricing packs...")
        
        for date in dates:
            pack_id = f'PP_{pd.to_datetime(date).strftime("%Y-%m-%d")}'
            
            # Check if pricing pack exists
            exists = await self.conn.fetchval(
                "SELECT 1 FROM pricing_packs WHERE id = $1",
                pack_id
            )
            
            if not exists:
                # Create pricing pack with all required columns
                # Convert pandas Timestamp to Python date
                date_obj = pd.to_datetime(date)
                if hasattr(date_obj, 'date'):
                    date_value = date_obj.date()
                else:
                    date_value = date_obj
                
                await self.conn.execute("""
                    INSERT INTO pricing_packs (
                        id, date, policy, sources_json, status, 
                        is_fresh, prewarm_done, reconciliation_passed, 
                        reconciliation_failed, created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $10)
                    ON CONFLICT (id) DO NOTHING
                """, 
                    pack_id,
                    date_value,
                    'WM4PM_CAD',  # Default policy
                    json.dumps({}),  # Empty sources as JSON string
                    'warming',  # Status
                    False,  # is_fresh
                    False,  # prewarm_done
                    False,  # reconciliation_passed
                    False,  # reconciliation_failed
                    datetime.now()  # created_at and updated_at
                )
        
        logger.info(f"Created pricing packs for {len(dates)} dates")
    
    async def seed_performance_data(self):
        """Main seeding function"""
        try:
            logger.info("Starting portfolio performance data seeding...")
            
            # Generate NAV history
            nav_df = await self.generate_nav_history()
            logger.info(f"Generated {len(nav_df)} days of NAV history")
            
            # Calculate metrics
            metrics_df = await self.calculate_metrics(nav_df)
            logger.info(f"Calculated {len(metrics_df)} days of portfolio metrics")
            
            # Create pricing packs for all dates
            await self.create_pricing_packs(metrics_df['asof_date'].unique())
            
            # Update database
            await self.update_nav_history(nav_df)
            await self.insert_metrics(metrics_df)
            
            # Verify the data
            await self.verify_seeded_data()
            
            logger.info("✅ Portfolio performance data seeding completed successfully!")
            
        except Exception as e:
            logger.error(f"Error seeding performance data: {e}")
            raise
    
    async def verify_seeded_data(self):
        """Verify that seeded data is correct"""
        
        # Check NAV history
        nav_count = await self.conn.fetchval(
            "SELECT COUNT(*) FROM portfolio_daily_values WHERE portfolio_id = $1",
            PORTFOLIO_ID
        )
        
        # Check metrics
        metrics_count = await self.conn.fetchval(
            "SELECT COUNT(*) FROM portfolio_metrics WHERE portfolio_id = $1",
            PORTFOLIO_ID
        )
        
        # Get latest metrics
        latest_metrics = await self.conn.fetchrow("""
            SELECT 
                asof_date,
                portfolio_value_base,
                twr_1y,
                sharpe_1y,
                volatility_1y,
                max_drawdown_1y
            FROM portfolio_metrics
            WHERE portfolio_id = $1
            ORDER BY asof_date DESC
            LIMIT 1
        """, PORTFOLIO_ID)
        
        logger.info(f"Verification Results:")
        logger.info(f"  - NAV History Records: {nav_count}")
        logger.info(f"  - Portfolio Metrics Records: {metrics_count}")
        
        if latest_metrics:
            logger.info(f"  - Latest Date: {latest_metrics['asof_date']}")
            logger.info(f"  - Latest Portfolio Value: ${latest_metrics['portfolio_value_base']:,.2f}")
            logger.info(f"  - 1Y Return: {latest_metrics['twr_1y']*100:.2f}%")
            logger.info(f"  - Sharpe Ratio: {latest_metrics['sharpe_1y']:.2f}")
            logger.info(f"  - Volatility: {latest_metrics['volatility_1y']*100:.2f}%")
            logger.info(f"  - Max Drawdown: {latest_metrics['max_drawdown_1y']*100:.2f}%")


async def main():
    """Main execution function"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return
    
    # Connect to database
    conn = await asyncpg.connect(database_url)
    
    try:
        # Create seeder and run
        seeder = PerformanceSeeder(conn)
        await seeder.seed_performance_data()
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())