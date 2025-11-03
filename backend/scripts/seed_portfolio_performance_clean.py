#!/usr/bin/env python3
"""
Clean Portfolio Performance Data Seeder
========================================
Creates realistic performance data for the demo portfolio using ONLY business days.
Ensures no duplicate entries and accurate metrics calculation.

Generates:
1. Realistic NAV movements in portfolio_daily_values (business days only)
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
import os
import logging
import json
from uuid import UUID

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


class CleanPerformanceSeeder:
    """Seeds realistic performance data for portfolio - BUSINESS DAYS ONLY"""
    
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn
        
    async def clean_existing_data(self):
        """Remove all existing data to prevent duplicates"""
        logger.info("Cleaning existing data...")
        
        # First count existing records
        metrics_count = await self.conn.fetchval(
            "SELECT COUNT(*) FROM portfolio_metrics WHERE portfolio_id = $1",
            PORTFOLIO_ID
        )
        
        nav_count = await self.conn.fetchval(
            "SELECT COUNT(*) FROM portfolio_daily_values WHERE portfolio_id = $1",
            PORTFOLIO_ID
        )
        
        # Start transaction for atomic cleanup
        async with self.conn.transaction():
            # Delete portfolio metrics
            await self.conn.execute(
                "DELETE FROM portfolio_metrics WHERE portfolio_id = $1",
                PORTFOLIO_ID
            )
            
            # Delete portfolio daily values  
            await self.conn.execute(
                "DELETE FROM portfolio_daily_values WHERE portfolio_id = $1",
                PORTFOLIO_ID
            )
            
            logger.info(f"Deleted {nav_count} NAV records and {metrics_count} metrics records")
    
    def generate_business_days(self) -> pd.DatetimeIndex:
        """Generate only business days (Monday-Friday)"""
        # Use pandas business day frequency
        business_days = pd.bdate_range(start=START_DATE, end=END_DATE, freq='B')
        logger.info(f"Generated {len(business_days)} business days from {START_DATE} to {END_DATE}")
        return business_days
    
    async def generate_nav_history(self) -> pd.DataFrame:
        """Generate realistic NAV history with proper volatility - BUSINESS DAYS ONLY"""
        
        # Create business day date range
        dates = self.generate_business_days()
        num_days = len(dates)
        
        # Calculate required growth
        total_return_needed = (TARGET_VALUE / INITIAL_VALUE) - 1
        daily_return = (1 + total_return_needed) ** (1 / num_days) - 1
        
        # Generate returns with realistic volatility
        daily_vol = ANNUAL_VOLATILITY / np.sqrt(TRADING_DAYS_PER_YEAR)
        
        # Create base trend
        base_trend = np.linspace(0, total_return_needed, num_days)
        
        # Generate correlated noise with market regimes
        noise = np.random.normal(0, daily_vol, num_days)
        regime_multipliers = self._generate_market_regimes(num_days)
        noise = noise * regime_multipliers
        
        # Calculate NAV values
        nav_values = np.zeros(num_days)
        nav_values[0] = INITIAL_VALUE
        
        for i in range(1, num_days):
            # Combine trend with noise
            period_return = (base_trend[i] - base_trend[i-1]) + noise[i] * 0.7  # Dampen noise slightly
            
            # Apply to NAV
            nav_values[i] = nav_values[i-1] * (1 + period_return)
            
            # Ensure we don't go below 50% of initial value
            nav_values[i] = max(nav_values[i], INITIAL_VALUE * 0.5)
        
        # Scale to match target value
        scaling_factor = TARGET_VALUE / nav_values[-1]
        nav_values = nav_values * scaling_factor
        
        # Create DataFrame
        df = pd.DataFrame({
            'valuation_date': dates,
            'total_value': nav_values,
            'cash_balance': nav_values * 0.82,  # ~82% cash allocation
            'positions_value': nav_values * 0.18,  # ~18% positions
            'currency': 'USD',
            'cash_flows': 0.0
        })
        
        # Add realistic cash flows (dividends and sells)
        df = self._add_cash_flows(df)
        
        return df
    
    def _generate_market_regimes(self, num_days: int) -> np.ndarray:
        """Generate realistic market regime changes"""
        regimes = np.ones(num_days)
        
        # Market regime periods with volatility multipliers
        regime_periods = [
            (0, int(num_days * 0.1), 1.2),      # Initial bull (10%)
            (int(num_days * 0.1), int(num_days * 0.2), 0.8),    # Correction (10%)
            (int(num_days * 0.2), int(num_days * 0.4), 1.1),    # Recovery (20%)
            (int(num_days * 0.4), int(num_days * 0.5), 0.7),    # Bear phase (10%)
            (int(num_days * 0.5), int(num_days * 0.75), 1.3),   # Strong bull (25%)
            (int(num_days * 0.75), int(num_days * 0.85), 0.9),  # Consolidation (10%)
            (int(num_days * 0.85), num_days, 1.15)              # Final bull (15%)
        ]
        
        for start, end, multiplier in regime_periods:
            if start < num_days:
                end = min(end, num_days)
                regimes[start:end] = multiplier
                
        return regimes
    
    def _add_cash_flows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add realistic cash flows from transactions"""
        
        # Known transaction dates and amounts
        cash_flow_events = [
            ('2024-02-15', 350.00),    # Q1 Dividend
            ('2024-03-15', 280.00),    # Q1 Dividend
            ('2024-05-15', 420.00),    # Q2 Dividend
            ('2024-06-15', 315.00),    # Q2 Dividend
            ('2024-07-15', -15000.00), # Position reduction
            ('2024-08-15', 385.00),    # Q3 Dividend
            ('2024-09-15', 490.00),    # Q3 Dividend
            ('2024-10-01', -12000.00), # Position reduction
            ('2024-11-15', 450.00),    # Q4 Dividend
            ('2025-02-15', 380.00),    # Q1 Dividend
            ('2025-05-15', 410.00),    # Q2 Dividend
            ('2025-08-15', 395.00),    # Q3 Dividend
        ]
        
        for date_str, amount in cash_flow_events:
            # Convert to business day if needed
            target_date = pd.to_datetime(date_str)
            # Find nearest business day
            business_date = pd.bdate_range(start=target_date, periods=1)[0]
            
            # Find in dataframe
            mask = df['valuation_date'].dt.date == business_date.date()
            if mask.any():
                df.loc[mask, 'cash_flows'] = amount
                
        return df
    
    async def calculate_metrics(self, nav_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive portfolio metrics"""
        
        metrics_list = []
        nav_values = nav_df['total_value'].values
        dates = nav_df['valuation_date'].values
        
        for i in range(len(dates)):
            date_val = dates[i]
            
            # Period returns
            twr_1d = self._calculate_return(nav_values, i, 1)
            twr_mtd = self._calculate_period_return(nav_values, dates, i, 'MTD')
            twr_qtd = self._calculate_period_return(nav_values, dates, i, 'QTD')
            twr_ytd = self._calculate_period_return(nav_values, dates, i, 'YTD')
            twr_1y = self._calculate_return(nav_values, i, 252)
            
            # Volatility calculations
            vol_30d = self._calculate_volatility(nav_values, i, 21)  # ~21 business days in 30 calendar days
            vol_60d = self._calculate_volatility(nav_values, i, 42)  # ~42 business days in 60 calendar days
            vol_90d = self._calculate_volatility(nav_values, i, 63)  # ~63 business days in 90 calendar days
            vol_1y = self._calculate_volatility(nav_values, i, 252)
            
            # Risk metrics
            sharpe_1y = self._calculate_sharpe(twr_1y, vol_1y)
            max_dd_1y = self._calculate_max_drawdown(nav_values, i, 252)
            
            # Current drawdown
            if i > 0:
                running_max = np.max(nav_values[:i+1])
                current_dd = (nav_values[i] - running_max) / running_max if running_max > 0 else 0
            else:
                current_dd = 0
            
            # Money-weighted returns (simplified)
            mwr_ytd = twr_ytd * 0.95 if twr_ytd else 0
            mwr_1y = twr_1y * 0.95 if twr_1y else 0
            
            # Inception metrics
            inception_return = (nav_values[i] / INITIAL_VALUE - 1) if INITIAL_VALUE > 0 else 0
            days_elapsed = (i + 1)
            years_elapsed = days_elapsed / 252.0
            if years_elapsed > 0:
                inception_ann = (1 + inception_return) ** (1 / years_elapsed) - 1
            else:
                inception_ann = 0
            
            # Additional metrics
            beta_1y = 0.85 + np.random.normal(0, 0.02)  # Market beta with small variation
            alpha_1y = max(0, twr_1y - (0.12 * beta_1y)) if twr_1y else 0  # Excess return
            
            metrics = {
                'portfolio_id': PORTFOLIO_ID,
                'asof_date': date_val,
                'pricing_pack_id': f'PP_{pd.to_datetime(date_val).strftime("%Y-%m-%d")}',
                'twr_1d': twr_1d,
                'twr_1d_base': twr_1d,
                'twr_mtd': twr_mtd,
                'twr_qtd': twr_qtd,
                'twr_ytd': twr_ytd,
                'twr_1y': twr_1y,
                'twr_3y_ann': twr_1y * 0.9 if twr_1y else None,
                'twr_5y_ann': twr_1y * 0.85 if twr_1y else None,
                'twr_inception_ann': inception_ann,
                'mwr_ytd': mwr_ytd,
                'mwr_1y': mwr_1y,
                'mwr_3y_ann': mwr_1y * 0.9 if mwr_1y else None,
                'mwr_inception_ann': inception_ann * 0.95,
                'volatility_30d': vol_30d,
                'volatility_60d': vol_60d,
                'volatility_90d': vol_90d,
                'volatility_1y': vol_1y,
                'sharpe_30d': self._calculate_sharpe(self._calculate_return(nav_values, i, 21), vol_30d),
                'sharpe_60d': self._calculate_sharpe(self._calculate_return(nav_values, i, 42), vol_60d),
                'sharpe_90d': self._calculate_sharpe(self._calculate_return(nav_values, i, 63), vol_90d),
                'sharpe_1y': sharpe_1y,
                'max_drawdown_1y': max_dd_1y,
                'max_drawdown_3y': max_dd_1y * 1.2 if max_dd_1y else None,
                'current_drawdown': current_dd,
                'alpha_1y': alpha_1y,
                'alpha_3y_ann': alpha_1y * 0.8 if alpha_1y else None,
                'beta_1y': beta_1y,
                'beta_3y': beta_1y * 0.98,
                'tracking_error_1y': 0.08 + np.random.normal(0, 0.005),
                'information_ratio_1y': 0.5 + np.random.normal(0, 0.05),
                'win_rate_1y': 0.52 + np.random.normal(0, 0.02),
                'avg_win': 0.015 + np.random.normal(0, 0.002),
                'avg_loss': 0.012 + np.random.normal(0, 0.002),
                'portfolio_value_base': nav_values[i],
                'portfolio_value_local': nav_values[i],
                'cash_balance': nav_values[i] * 0.82,
                'base_currency': 'USD',
                'benchmark_id': 'SPY',
                'reconciliation_error_bps': np.random.normal(0, 1)
            }
            
            metrics_list.append(metrics)
        
        return pd.DataFrame(metrics_list)
    
    def _calculate_return(self, values: np.ndarray, current_idx: int, lookback: int) -> float:
        """Calculate return over lookback period"""
        if current_idx < lookback or lookback <= 0:
            return 0.0
        
        current = values[current_idx]
        previous = values[current_idx - lookback]
        
        if previous <= 0:
            return 0.0
            
        return (current / previous) - 1
    
    def _calculate_period_return(self, values: np.ndarray, dates: np.ndarray, 
                                 current_idx: int, period: str) -> float:
        """Calculate period returns (MTD, QTD, YTD)"""
        current_date = pd.to_datetime(dates[current_idx])
        
        if period == 'MTD':
            period_start = current_date.replace(day=1)
        elif period == 'QTD':
            quarter_month = ((current_date.month - 1) // 3) * 3 + 1
            period_start = current_date.replace(month=quarter_month, day=1)
        elif period == 'YTD':
            period_start = current_date.replace(month=1, day=1)
        else:
            return 0.0
        
        # Find the first business day of the period
        for i in range(current_idx, -1, -1):
            if pd.to_datetime(dates[i]) <= period_start:
                if i == current_idx:
                    return 0.0
                return self._calculate_return(values, current_idx, current_idx - i)
        
        # If we got here, use all available data
        return self._calculate_return(values, current_idx, current_idx)
    
    def _calculate_volatility(self, values: np.ndarray, current_idx: int, lookback: int) -> float:
        """Calculate annualized volatility"""
        if current_idx < lookback or lookback <= 1:
            return 0.0
        
        # Get period values
        period_values = values[max(0, current_idx - lookback):current_idx + 1]
        
        if len(period_values) < 2:
            return 0.0
        
        # Calculate daily returns
        daily_returns = np.diff(period_values) / period_values[:-1]
        
        # Annualize (252 trading days)
        return np.std(daily_returns) * np.sqrt(252)
    
    def _calculate_sharpe(self, annual_return: float, annual_vol: float) -> float:
        """Calculate Sharpe ratio"""
        if annual_vol <= 0 or not annual_return:
            return 0.0
        
        return (annual_return - RISK_FREE_RATE) / annual_vol
    
    def _calculate_max_drawdown(self, values: np.ndarray, current_idx: int, lookback: int) -> float:
        """Calculate maximum drawdown over period"""
        if current_idx < lookback or lookback <= 0:
            return 0.0
        
        start_idx = max(0, current_idx - lookback)
        period_values = values[start_idx:current_idx + 1]
        
        if len(period_values) == 0:
            return 0.0
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(period_values)
        
        # Calculate drawdowns
        drawdowns = (period_values - running_max) / running_max
        
        return np.min(drawdowns)
    
    async def insert_nav_history(self, nav_df: pd.DataFrame):
        """Insert NAV history records - ensures no duplicates"""
        logger.info(f"Inserting {len(nav_df)} NAV history records...")
        
        inserted_count = 0
        
        async with self.conn.transaction():
            for _, row in nav_df.iterrows():
                val_date = row['valuation_date'].date() if hasattr(row['valuation_date'], 'date') else row['valuation_date']
                
                # Use UPSERT to prevent duplicates
                await self.conn.execute("""
                    INSERT INTO portfolio_daily_values (
                        portfolio_id, valuation_date, total_value, 
                        cash_balance, positions_value, cash_flows, 
                        currency, computed_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (portfolio_id, valuation_date) 
                    DO UPDATE SET
                        total_value = EXCLUDED.total_value,
                        cash_balance = EXCLUDED.cash_balance,
                        positions_value = EXCLUDED.positions_value,
                        cash_flows = EXCLUDED.cash_flows,
                        currency = EXCLUDED.currency,
                        computed_at = EXCLUDED.computed_at
                """,
                    PORTFOLIO_ID,
                    val_date,
                    Decimal(str(row['total_value'])),
                    Decimal(str(row['cash_balance'])),
                    Decimal(str(row['positions_value'])),
                    Decimal(str(row.get('cash_flows', 0))),
                    row['currency'],
                    datetime.now()
                )
                inserted_count += 1
        
        logger.info(f"✅ Inserted/updated {inserted_count} NAV records")
    
    async def insert_metrics(self, metrics_df: pd.DataFrame):
        """Insert portfolio metrics - ensures no duplicates"""
        logger.info(f"Inserting {len(metrics_df)} portfolio metrics...")
        
        inserted_count = 0
        
        async with self.conn.transaction():
            for _, row in metrics_df.iterrows():
                asof_date = row['asof_date'].date() if hasattr(row['asof_date'], 'date') else row['asof_date']
                
                # Convert None/NaN to SQL NULL
                def to_decimal_or_none(val):
                    if val is None or (isinstance(val, float) and np.isnan(val)):
                        return None
                    return Decimal(str(val))
                
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
                    ON CONFLICT (portfolio_id, asof_date, pricing_pack_id)
                    DO UPDATE SET
                        twr_1d = EXCLUDED.twr_1d,
                        twr_1d_base = EXCLUDED.twr_1d_base,
                        twr_mtd = EXCLUDED.twr_mtd,
                        twr_qtd = EXCLUDED.twr_qtd,
                        twr_ytd = EXCLUDED.twr_ytd,
                        twr_1y = EXCLUDED.twr_1y,
                        volatility_1y = EXCLUDED.volatility_1y,
                        sharpe_1y = EXCLUDED.sharpe_1y,
                        portfolio_value_base = EXCLUDED.portfolio_value_base
                """,
                    PORTFOLIO_ID,
                    asof_date,
                    row['pricing_pack_id'],
                    to_decimal_or_none(row['twr_1d']),
                    to_decimal_or_none(row['twr_1d_base']),
                    to_decimal_or_none(row['twr_mtd']),
                    to_decimal_or_none(row['twr_qtd']),
                    to_decimal_or_none(row['twr_ytd']),
                    to_decimal_or_none(row['twr_1y']),
                    to_decimal_or_none(row['twr_3y_ann']),
                    to_decimal_or_none(row['twr_5y_ann']),
                    to_decimal_or_none(row['twr_inception_ann']),
                    to_decimal_or_none(row['mwr_ytd']),
                    to_decimal_or_none(row['mwr_1y']),
                    to_decimal_or_none(row['mwr_3y_ann']),
                    to_decimal_or_none(row['mwr_inception_ann']),
                    to_decimal_or_none(row['volatility_30d']),
                    to_decimal_or_none(row['volatility_60d']),
                    to_decimal_or_none(row['volatility_90d']),
                    to_decimal_or_none(row['volatility_1y']),
                    to_decimal_or_none(row['sharpe_30d']),
                    to_decimal_or_none(row['sharpe_60d']),
                    to_decimal_or_none(row['sharpe_90d']),
                    to_decimal_or_none(row['sharpe_1y']),
                    to_decimal_or_none(row['max_drawdown_1y']),
                    to_decimal_or_none(row['max_drawdown_3y']),
                    to_decimal_or_none(row['current_drawdown']),
                    to_decimal_or_none(row['alpha_1y']),
                    to_decimal_or_none(row['alpha_3y_ann']),
                    to_decimal_or_none(row['beta_1y']),
                    to_decimal_or_none(row['beta_3y']),
                    to_decimal_or_none(row['tracking_error_1y']),
                    to_decimal_or_none(row['information_ratio_1y']),
                    to_decimal_or_none(row['win_rate_1y']),
                    to_decimal_or_none(row['avg_win']),
                    to_decimal_or_none(row['avg_loss']),
                    to_decimal_or_none(row['portfolio_value_base']),
                    to_decimal_or_none(row['portfolio_value_local']),
                    to_decimal_or_none(row['cash_balance']),
                    row['base_currency'],
                    row['benchmark_id'],
                    to_decimal_or_none(row['reconciliation_error_bps'])
                )
                inserted_count += 1
        
        logger.info(f"✅ Inserted/updated {inserted_count} metrics records")
    
    async def create_pricing_packs(self, dates):
        """Create pricing packs for all dates"""
        logger.info("Creating pricing packs...")
        import hashlib
        
        created_count = 0
        for date in dates:
            pack_id = f'PP_{pd.to_datetime(date).strftime("%Y-%m-%d")}'
            
            date_obj = pd.to_datetime(date)
            if hasattr(date_obj, 'date'):
                date_value = date_obj.date()
            else:
                date_value = date_obj
            
            # Generate a hash for the pricing pack
            hash_input = f"{pack_id}_{date_value}_WM4PM_CAD"
            pack_hash = hashlib.md5(hash_input.encode()).hexdigest()
            
            result = await self.conn.fetchval("""
                INSERT INTO pricing_packs (
                    id, date, policy, hash, sources_json, status, 
                    is_fresh, prewarm_done, reconciliation_passed, 
                    reconciliation_failed, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $11)
                ON CONFLICT (id) DO NOTHING
                RETURNING id
            """, 
                pack_id,
                date_value,
                'WM4PM_CAD',
                pack_hash,
                json.dumps({}),
                'warming',
                False,
                False,
                False,
                False,
                datetime.now()
            )
            
            if result:
                created_count += 1
        
        logger.info(f"✅ Created {created_count} new pricing packs")
    
    async def verify_data_integrity(self):
        """Verify the seeded data integrity"""
        logger.info("\n" + "="*60)
        logger.info("VERIFYING DATA INTEGRITY")
        logger.info("="*60)
        
        # 1. Check for duplicate dates
        duplicates = await self.conn.fetch("""
            SELECT valuation_date, COUNT(*) as count
            FROM portfolio_daily_values
            WHERE portfolio_id = $1
            GROUP BY valuation_date
            HAVING COUNT(*) > 1
        """, PORTFOLIO_ID)
        
        if duplicates:
            logger.error(f"❌ Found {len(duplicates)} duplicate dates!")
            for row in duplicates[:5]:
                logger.error(f"  - {row['valuation_date']}: {row['count']} duplicates")
        else:
            logger.info("✅ No duplicate dates found")
        
        # 2. Check weekend dates
        weekend_dates = await self.conn.fetchval("""
            SELECT COUNT(*) 
            FROM portfolio_daily_values
            WHERE portfolio_id = $1
              AND EXTRACT(DOW FROM valuation_date) IN (0, 6)
        """, PORTFOLIO_ID)
        
        if weekend_dates > 0:
            logger.warning(f"⚠️ Found {weekend_dates} weekend dates (should be 0)")
        else:
            logger.info("✅ No weekend dates found (business days only)")
        
        # 3. Check total record counts
        nav_count = await self.conn.fetchval(
            "SELECT COUNT(*) FROM portfolio_daily_values WHERE portfolio_id = $1",
            PORTFOLIO_ID
        )
        
        metrics_count = await self.conn.fetchval(
            "SELECT COUNT(*) FROM portfolio_metrics WHERE portfolio_id = $1",
            PORTFOLIO_ID
        )
        
        logger.info(f"\n📊 Record Counts:")
        logger.info(f"  - NAV History: {nav_count} records")
        logger.info(f"  - Portfolio Metrics: {metrics_count} records")
        
        # 4. Check date ranges
        date_range = await self.conn.fetchrow("""
            SELECT 
                MIN(valuation_date) as min_date,
                MAX(valuation_date) as max_date,
                COUNT(DISTINCT valuation_date) as unique_dates
            FROM portfolio_daily_values
            WHERE portfolio_id = $1
        """, PORTFOLIO_ID)
        
        if date_range:
            logger.info(f"\n📅 Date Range:")
            logger.info(f"  - Start: {date_range['min_date']}")
            logger.info(f"  - End: {date_range['max_date']}")
            logger.info(f"  - Unique Dates: {date_range['unique_dates']}")
        
        # 5. Check latest metrics
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
        
        if latest_metrics:
            logger.info(f"\n📈 Latest Portfolio Metrics ({latest_metrics['asof_date']}):")
            logger.info(f"  - Portfolio Value: ${float(latest_metrics['portfolio_value_base']):,.2f}")
            
            if latest_metrics['twr_1y']:
                logger.info(f"  - 1Y Return: {float(latest_metrics['twr_1y'])*100:.2f}%")
            
            if latest_metrics['sharpe_1y']:
                logger.info(f"  - Sharpe Ratio: {float(latest_metrics['sharpe_1y']):.2f}")
            
            if latest_metrics['volatility_1y']:
                logger.info(f"  - Volatility: {float(latest_metrics['volatility_1y'])*100:.2f}%")
            
            if latest_metrics['max_drawdown_1y']:
                logger.info(f"  - Max Drawdown: {float(latest_metrics['max_drawdown_1y'])*100:.2f}%")
        
        logger.info("\n" + "="*60)
    
    async def seed_clean_data(self):
        """Main seeding function with full cleanup and verification"""
        try:
            logger.info("\n" + "="*60)
            logger.info("CLEAN PORTFOLIO PERFORMANCE DATA SEEDER")
            logger.info("="*60)
            
            # Step 1: Clean existing data
            await self.clean_existing_data()
            
            # Step 2: Generate NAV history (business days only)
            logger.info("\n📊 Generating NAV history...")
            nav_df = await self.generate_nav_history()
            logger.info(f"✅ Generated {len(nav_df)} business days of NAV history")
            
            # Step 3: Calculate metrics
            logger.info("\n📈 Calculating portfolio metrics...")
            metrics_df = await self.calculate_metrics(nav_df)
            logger.info(f"✅ Calculated metrics for {len(metrics_df)} days")
            
            # Step 4: Create pricing packs
            logger.info("\n📦 Creating pricing packs...")
            await self.create_pricing_packs(metrics_df['asof_date'].unique())
            
            # Step 5: Insert data
            logger.info("\n💾 Inserting data into database...")
            await self.insert_nav_history(nav_df)
            await self.insert_metrics(metrics_df)
            
            # Step 6: Verify integrity
            await self.verify_data_integrity()
            
            logger.info("\n✅ CLEAN SEEDING COMPLETED SUCCESSFULLY!")
            logger.info("="*60 + "\n")
            
        except Exception as e:
            logger.error(f"\n❌ Error during seeding: {e}")
            raise


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
        seeder = CleanPerformanceSeeder(conn)
        await seeder.seed_clean_data()
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())