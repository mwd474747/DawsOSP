# Metrics Architect Agent

**Role**: Performance metrics, currency attribution, factor analysis
**Reports to**: [ORCHESTRATOR](../ORCHESTRATOR.md)
**Status**: Sprint 2 - Core Analytics Phase
**Priority**: P0

---

## Mission

Build the **performance analytics engine** that delivers:
1. **Time-weighted return (TWR)** - Pure investment performance
2. **Money-weighted return (MWR)** - Investor-specific returns
3. **Currency attribution** - Local vs FX vs interaction decomposition
4. **Factor exposures** - Beta decomposition (real rate, inflation, credit, FX)
5. **Risk metrics** - Volatility, Sharpe, max drawdown, beta to benchmark
6. **Position-level risk** - Marginal contribution to portfolio vol

All metrics must:
- Reference `pricing_pack_id` for reproducibility
- Reconcile to Beancount ledger ±1 basis point
- Support multi-currency portfolios correctly

---

## Sub-Agents

### PERFORMANCE_CALCULATOR
**Responsibilities**:
- TWR calculation (geometric linking of daily returns)
- MWR calculation (IRR accounting for cash flows)
- Sharpe ratio, Sortino ratio
- Maximum drawdown
- Beta to benchmark (hedged/unhedged)
- Rolling volatility (30/90/252 day)

**Deliverables**:

**TWR Calculation**:
```python
# services/metrics.py
from decimal import Decimal
import pandas as pd
import numpy as np
from datetime import date, timedelta

class PerformanceCalculator:
    def __init__(self, db):
        self.db = db

    async def compute_twr(self, portfolio_id: str, pack_id: str, lookback_days: int = 252) -> dict:
        """
        Compute time-weighted return over lookback period.

        TWR formula:
        R = [(1+r1)(1+r2)...(1+rn)] - 1

        Where r_i = (V_i - V_{i-1} - CF_i) / (V_{i-1} + CF_i)
        CF = cash flows (contributions/withdrawals)
        """
        # Get daily valuations from pricing pack history
        end_date = await self._get_pack_date(pack_id)
        start_date = end_date - timedelta(days=lookback_days)

        # Query daily values (from portfolio_metrics hypertable)
        values = await self.db.fetch("""
            SELECT asof_date, total_value, cash_flows
            FROM portfolio_daily_values
            WHERE portfolio_id = $1 AND asof_date BETWEEN $2 AND $3
            ORDER BY asof_date
        """, portfolio_id, start_date, end_date)

        if len(values) < 2:
            return {"twr": 0.0, "error": "Insufficient data"}

        # Compute daily returns
        returns = []
        for i in range(1, len(values)):
            v_prev = Decimal(str(values[i-1]["total_value"]))
            v_curr = Decimal(str(values[i]["total_value"]))
            cf = Decimal(str(values[i].get("cash_flows", 0)))

            # r = (V_i - V_{i-1} - CF) / (V_{i-1} + CF)
            if v_prev + cf > 0:
                r = (v_curr - v_prev - cf) / (v_prev + cf)
                returns.append(float(r))

        # Geometric linking
        twr = float(np.prod([1 + r for r in returns]) - 1)

        # Annualized metrics
        days = (end_date - start_date).days
        ann_factor = 365 / days if days > 0 else 1
        ann_twr = (1 + twr) ** ann_factor - 1

        # Volatility (annualized std dev of daily returns)
        vol = float(np.std(returns) * np.sqrt(252)) if len(returns) > 1 else 0.0

        # Sharpe (assume 4% risk-free rate)
        rf_rate = 0.04
        sharpe = (ann_twr - rf_rate) / vol if vol > 0 else 0.0

        return {
            "twr": twr,
            "ann_twr": ann_twr,
            "vol": vol,
            "sharpe": sharpe,
            "days": days,
            "data_points": len(values)
        }

    async def compute_mwr(self, portfolio_id: str, pack_id: str) -> dict:
        """
        Compute money-weighted return (IRR).

        Solves: 0 = V_0 - sum(CF_i / (1+IRR)^t_i) + V_n / (1+IRR)^t_n
        """
        # Get all cash flows and terminal value
        end_date = await self._get_pack_date(pack_id)
        start_date = end_date - timedelta(days=365)

        cash_flows = await self.db.fetch("""
            SELECT trade_date, amount
            FROM portfolio_cash_flows
            WHERE portfolio_id = $1 AND trade_date BETWEEN $2 AND $3
            ORDER BY trade_date
        """, portfolio_id, start_date, end_date)

        if not cash_flows:
            return {"mwr": 0.0, "error": "No cash flows"}

        # Build cash flow series for IRR calculation
        cf_series = []
        for cf in cash_flows:
            days_from_start = (cf["trade_date"] - start_date).days
            cf_series.append((days_from_start, float(cf["amount"])))

        # Terminal value
        terminal_value = await self._get_portfolio_value(portfolio_id, pack_id)
        total_days = (end_date - start_date).days
        cf_series.append((total_days, -float(terminal_value)))  # Negative = ending value

        # Solve for IRR using Newton-Raphson
        irr = self._calculate_irr(cf_series)

        return {
            "mwr": irr,
            "ann_mwr": (1 + irr) ** (365 / total_days) - 1 if total_days > 0 else 0.0
        }

    def _calculate_irr(self, cash_flows: list[tuple[int, float]], guess: float = 0.1) -> float:
        """Newton-Raphson IRR solver"""
        max_iter = 100
        tolerance = 1e-6

        r = guess
        for _ in range(max_iter):
            npv = sum(cf / (1 + r) ** (t / 365) for t, cf in cash_flows)
            npv_prime = sum(-t * cf / (365 * (1 + r) ** (t / 365 + 1)) for t, cf in cash_flows)

            if abs(npv) < tolerance:
                return r

            if abs(npv_prime) < 1e-10:
                break

            r = r - npv / npv_prime

        return r  # May not converge; caller should check

    async def compute_max_drawdown(self, portfolio_id: str, pack_id: str, lookback_days: int = 252) -> dict:
        """
        Maximum drawdown: largest peak-to-trough decline.
        """
        end_date = await self._get_pack_date(pack_id)
        start_date = end_date - timedelta(days=lookback_days)

        values = await self.db.fetch("""
            SELECT asof_date, total_value
            FROM portfolio_daily_values
            WHERE portfolio_id = $1 AND asof_date BETWEEN $2 AND $3
            ORDER BY asof_date
        """, portfolio_id, start_date, end_date)

        if len(values) < 2:
            return {"max_dd": 0.0}

        values_arr = np.array([float(v["total_value"]) for v in values])

        # Compute running max and drawdown
        running_max = np.maximum.accumulate(values_arr)
        drawdowns = (values_arr - running_max) / running_max

        max_dd = float(np.min(drawdowns))
        max_dd_idx = int(np.argmin(drawdowns))

        return {
            "max_dd": max_dd,
            "max_dd_date": values[max_dd_idx]["asof_date"].isoformat(),
            "recovery_days": self._compute_recovery_days(values, max_dd_idx)
        }

    def _compute_recovery_days(self, values: list, dd_idx: int) -> int:
        """Days from max drawdown to recovery"""
        peak_value = max(float(v["total_value"]) for v in values[:dd_idx+1])
        for i in range(dd_idx, len(values)):
            if float(values[i]["total_value"]) >= peak_value:
                return (values[i]["asof_date"] - values[dd_idx]["asof_date"]).days
        return -1  # Not yet recovered

    async def _get_pack_date(self, pack_id: str) -> date:
        row = await self.db.fetchrow("SELECT asof_date FROM pricing_pack WHERE id = $1", pack_id)
        return row["asof_date"]

    async def _get_portfolio_value(self, portfolio_id: str, pack_id: str) -> Decimal:
        # Sum valued positions
        positions = await self.db.fetch("""
            SELECT l.qty_open, p.close, fx.rate
            FROM lots l
            JOIN prices p ON l.security_id = p.security_id AND p.pricing_pack_id = $2
            JOIN fx_rates fx ON p.currency = fx.base_ccy AND fx.pricing_pack_id = $2
            WHERE l.portfolio_id = $1 AND l.qty_open > 0
        """, portfolio_id, pack_id)

        total = sum(
            Decimal(str(pos["qty_open"])) * Decimal(str(pos["close"])) * Decimal(str(pos["rate"]))
            for pos in positions
        )
        return total
```

---

### CURRENCY_ATTRIBUTOR
**Responsibilities**:
- Decompose returns into local + FX + interaction
- Per-position currency contribution
- Hedged vs unhedged benchmark attribution

**Deliverables**:

**Currency Attribution Formula**:
```
r_base = (1 + r_local)(1 + r_fx) - 1
       = r_local + r_fx + r_local * r_fx

where:
- r_base = total return in base currency
- r_local = return in local currency (price change only)
- r_fx = FX rate change (quote_ccy/base_ccy)
- r_local * r_fx = interaction term
```

**Implementation**:
```python
# services/currency_attribution.py
from decimal import Decimal
import pandas as pd

class CurrencyAttributor:
    def __init__(self, db):
        self.db = db

    async def compute_attribution(self, portfolio_id: str, pack_id: str, lookback_days: int = 30) -> dict:
        """
        Decompose portfolio return into local + FX + interaction.
        """
        end_date = await self._get_pack_date(pack_id)
        start_date = end_date - timedelta(days=lookback_days)

        # Get start and end packs
        start_pack = await self.db.fetchrow("""
            SELECT id FROM pricing_pack WHERE asof_date = $1
        """, start_date)

        if not start_pack:
            return {"error": "No starting pack"}

        # Get positions at start and end
        start_positions = await self._get_valued_positions(portfolio_id, start_pack["id"])
        end_positions = await self._get_valued_positions(portfolio_id, pack_id)

        # Compute local and FX returns per position
        attribution = {
            "local_return": 0.0,
            "fx_return": 0.0,
            "interaction": 0.0,
            "total_return": 0.0,
            "by_currency": {}
        }

        for sym in set(p["symbol"] for p in start_positions + end_positions):
            start_pos = next((p for p in start_positions if p["symbol"] == sym), None)
            end_pos = next((p for p in end_positions if p["symbol"] == sym), None)

            if not (start_pos and end_pos):
                continue

            # Local return (price change in local currency)
            r_local = (end_pos["price"] / start_pos["price"] - 1) if start_pos["price"] > 0 else 0.0

            # FX return (FX rate change)
            r_fx = (end_pos["fx_rate"] / start_pos["fx_rate"] - 1) if start_pos["fx_rate"] > 0 else 0.0

            # Interaction
            r_interaction = r_local * r_fx

            # Total base return
            r_base = (1 + r_local) * (1 + r_fx) - 1

            # Weight by starting value
            weight = start_pos["value_base"] / sum(p["value_base"] for p in start_positions)

            # Accumulate
            attribution["local_return"] += weight * r_local
            attribution["fx_return"] += weight * r_fx
            attribution["interaction"] += weight * r_interaction
            attribution["total_return"] += weight * r_base

            # By currency
            ccy = start_pos["currency"]
            if ccy not in attribution["by_currency"]:
                attribution["by_currency"][ccy] = {
                    "local": 0.0, "fx": 0.0, "interaction": 0.0, "weight": 0.0
                }

            attribution["by_currency"][ccy]["local"] += weight * r_local
            attribution["by_currency"][ccy]["fx"] += weight * r_fx
            attribution["by_currency"][ccy]["interaction"] += weight * r_interaction
            attribution["by_currency"][ccy]["weight"] += weight

        return attribution

    async def _get_valued_positions(self, portfolio_id: str, pack_id: str) -> list[dict]:
        """Get positions with price and FX rate from pack"""
        rows = await self.db.fetch("""
            SELECT s.symbol, s.trading_currency as currency, l.qty_open,
                   p.close as price, fx.rate as fx_rate,
                   l.qty_open * p.close * fx.rate as value_base
            FROM lots l
            JOIN securities s ON l.security_id = s.id
            JOIN prices p ON s.id = p.security_id AND p.pricing_pack_id = $2
            LEFT JOIN fx_rates fx ON p.currency = fx.base_ccy AND fx.pricing_pack_id = $2
            WHERE l.portfolio_id = $1 AND l.qty_open > 0
        """, portfolio_id, pack_id)

        return [
            {
                "symbol": r["symbol"],
                "currency": r["currency"],
                "qty": Decimal(str(r["qty_open"])),
                "price": Decimal(str(r["price"])),
                "fx_rate": Decimal(str(r["fx_rate"] or 1.0)),
                "value_base": Decimal(str(r["value_base"]))
            }
            for r in rows
        ]
```

---

### FACTOR_ANALYZER
**Responsibilities**:
- Factor loading estimation (real rate, inflation, credit, FX, equity risk premium)
- Beta decomposition per holding
- Factor variance contribution
- Pre-warm factor models after pack build

**Deliverables**:

**Factor Regression**:
```python
# services/factor_analysis.py
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

class FactorAnalyzer:
    def __init__(self, db, fred_service):
        self.db = db
        self.fred = fred_service

    async def compute_exposures(self, portfolio_id: str, pack_id: str, lookback_days: int = 252) -> dict:
        """
        Regress portfolio returns on factor returns to get betas.

        Factors:
        - Real rates: T10Y - inflation expectations
        - Inflation surprise: CPI YoY change
        - Credit spread: BAA10Y
        - USD index: DXY
        - Equity risk premium: SPY excess return
        """
        end_date = await self._get_pack_date(pack_id)
        start_date = end_date - timedelta(days=lookback_days)

        # Get portfolio daily returns
        port_returns = await self._get_portfolio_returns(portfolio_id, start_date, end_date)

        # Get factor returns
        factor_data = await self._get_factor_returns(start_date, end_date)

        # Align dates
        df = pd.DataFrame({
            "portfolio": port_returns,
            **factor_data
        }).dropna()

        if len(df) < 60:
            return {"error": "Insufficient data for regression"}

        # Fit regression
        X = df[["real_rate", "inflation", "credit", "usd", "equity_risk_premium"]].values
        y = df["portfolio"].values

        model = LinearRegression()
        model.fit(X, y)

        betas = {
            "real_rate": float(model.coef_[0]),
            "inflation": float(model.coef_[1]),
            "credit": float(model.coef_[2]),
            "usd": float(model.coef_[3]),
            "equity_risk_premium": float(model.coef_[4]),
            "alpha": float(model.intercept_)
        }

        # Variance decomposition
        var_explained = model.score(X, y)  # R^2

        # Factor variance contribution
        residuals = y - model.predict(X)
        total_var = np.var(y)
        residual_var = np.var(residuals)

        var_share = {
            "systematic": (total_var - residual_var) / total_var,
            "idiosyncratic": residual_var / total_var,
            "r_squared": var_explained
        }

        return {
            "betas": betas,
            "var_share": var_share,
            "lookback_days": lookback_days
        }

    async def _get_portfolio_returns(self, portfolio_id: str, start: date, end: date) -> pd.Series:
        """Daily portfolio returns from portfolio_metrics"""
        rows = await self.db.fetch("""
            SELECT asof_date, twr
            FROM portfolio_daily_values
            WHERE portfolio_id = $1 AND asof_date BETWEEN $2 AND $3
            ORDER BY asof_date
        """, portfolio_id, start, end)

        return pd.Series({r["asof_date"]: float(r["twr"]) for r in rows})

    async def _get_factor_returns(self, start: date, end: date) -> dict[str, pd.Series]:
        """Fetch and compute factor returns"""
        # Real rate = T10Y - T5YIFR (5Y inflation expectations)
        t10y = await self.fred.get_series("DGS10", start, end)
        t5yifr = await self.fred.get_series("T5YIFR", start, end)
        real_rate = (t10y - t5yifr).diff()

        # Inflation surprise = CPI YoY change
        cpi = await self.fred.get_series("CPIAUCSL", start, end)
        inflation = cpi.pct_change(periods=12)  # YoY

        # Credit spread = BAA10Y
        credit = await self.fred.get_series("BAA10Y", start, end)
        credit = credit.diff()

        # USD index (DXY) returns
        dxy = await self.fred.get_series("DTWEXBGS", start, end)
        usd = dxy.pct_change()

        # Equity risk premium = SPY return - T-bill
        spy = await self._get_spy_returns(start, end)
        tbill = await self.fred.get_series("DTB3", start, end) / 252  # Daily risk-free
        equity_risk_premium = spy - tbill

        return {
            "real_rate": real_rate,
            "inflation": inflation,
            "credit": credit,
            "usd": usd,
            "equity_risk_premium": equity_risk_premium
        }

    async def _get_spy_returns(self, start: date, end: date) -> pd.Series:
        """Get SPY daily returns from pricing pack history"""
        spy_id = await self.db.fetchval("SELECT id FROM securities WHERE symbol = 'SPY'")
        rows = await self.db.fetch("""
            SELECT pp.asof_date, p.close
            FROM prices p
            JOIN pricing_pack pp ON p.pricing_pack_id = pp.id
            WHERE p.security_id = $1 AND pp.asof_date BETWEEN $2 AND $3
            ORDER BY pp.asof_date
        """, spy_id, start, end)

        prices = pd.Series({r["asof_date"]: float(r["close"]) for r in rows})
        return prices.pct_change()

    async def prewarm_factors(self, pack_id: str):
        """
        Pre-compute factor exposures for all portfolios after pack build.
        Store in cache for fast retrieval.
        """
        portfolios = await self.db.fetch("SELECT id FROM portfolios")

        for p in portfolios:
            try:
                exposures = await self.compute_exposures(p["id"], pack_id)
                # Cache in Redis
                cache_key = f"factor_exposures:{p['id']}:{pack_id}"
                await self.redis.setex(cache_key, 86400, json.dumps(exposures))
            except Exception as e:
                logger.error(f"Factor prewarm failed for {p['id']}: {e}")
```

---

## Position-Level Risk

**Marginal Contribution to Portfolio Volatility**:
```python
# services/risk_metrics.py
import numpy as np

class RiskMetrics:
    async def position_risk_contribution(self, portfolio_id: str, pack_id: str) -> list[dict]:
        """
        Compute each position's marginal contribution to portfolio volatility.

        MCTR = (beta_i * weight_i * portfolio_vol) / sum(all MCTRs)
        """
        # Get covariance matrix of holdings
        positions = await self._get_valued_positions(portfolio_id, pack_id)
        returns = await self._get_returns_matrix(portfolio_id, pack_id, lookback=90)

        cov_matrix = np.cov(returns.T)
        weights = np.array([p["weight"] for p in positions])

        # Portfolio variance = w' Cov w
        port_var = weights @ cov_matrix @ weights
        port_vol = np.sqrt(port_var)

        # Marginal contribution = Cov w
        marginal_contrib = cov_matrix @ weights

        # Risk contribution = weight * marginal / port_vol
        risk_contrib = (weights * marginal_contrib) / port_vol

        return [
            {
                "symbol": positions[i]["symbol"],
                "weight": float(weights[i]),
                "risk_contrib": float(risk_contrib[i]),
                "risk_contrib_pct": float(risk_contrib[i] / port_vol * 100)
            }
            for i in range(len(positions))
        ]
```

---

## Acceptance Criteria (Sprint 2 Gate)

- [ ] TWR calculated correctly (geometric linking of daily returns)
- [ ] MWR (IRR) converges for realistic cash flow patterns
- [ ] Currency attribution sums: local + FX + interaction = total (±0.1bp)
- [ ] Factor exposures regress with R^2 > 0.5 on diversified portfolios
- [ ] Max drawdown identifies correct peak-to-trough
- [ ] Position risk contributions sum to portfolio volatility (±0.1%)
- [ ] Pre-warm completes for 100 portfolios < 60s

---

## Handoff

Upon completion, deliver:
1. **Metrics calculation guide**: Formulas, edge cases, reconciliation procedures
2. **Currency attribution explainer**: Visual breakdown for UI display
3. **Factor model documentation**: Factors used, regression methodology, interpretation
4. **Performance optimization notes**: Pre-warm strategy, caching, hypertable aggregates
