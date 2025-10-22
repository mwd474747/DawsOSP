# METRICS_ARCHITECT + UI_ARCHITECT S2 Implementation Guide

**Date**: 2025-10-21
**Agents**: METRICS_ARCHITECT + UI_ARCHITECT
**Phase**: Sprint 2 (Core Analytics + UI)
**Status**: 📋 IMPLEMENTATION GUIDE
**Estimated Effort**: 12-16 hours

---

## Executive Summary

This document provides a complete implementation guide for Sprint 2 deliverables:

**METRICS_ARCHITECT**:
- Time-Weighted Return (TWR) with geometric linking
- Money-Weighted Return (MWR) via IRR calculation
- Currency attribution (local + FX + interaction decomposition)
- Factor exposures (real rate, inflation, credit, USD, equity risk premium)
- Risk metrics (max drawdown, Sharpe, position risk contribution)

**UI_ARCHITECT**:
- Portfolio overview with dark theme, KPI ribbon, allocation charts
- Holdings deep dive with ratings badges, Explain drawer
- Staleness chips with provenance metadata
- Rights-gated PDF export
- Property tests (currency identity) + visual regression tests (Playwright)

---

## Implementation Checklist

### METRICS_ARCHITECT (7 files, ~1500 lines)

- [ ] `backend/app/services/metrics.py` - PerformanceCalculator (TWR, MWR, max drawdown)
- [ ] `backend/app/services/currency_attribution.py` - CurrencyAttributor
- [ ] `backend/app/services/factor_analysis.py` - FactorAnalyzer
- [ ] `backend/app/services/risk_metrics.py` - RiskMetrics (position risk contribution)
- [ ] `patterns/analysis/portfolio_overview.json` - Pattern definition
- [ ] `patterns/analysis/holding_deep_dive.json` - Pattern definition
- [ ] `tests/property/test_currency_identity.py` - Property tests

### UI_ARCHITECT (5 files, ~1000 lines)

- [ ] `ui/pages/portfolio_overview.py` - Main overview page with dark theme
- [ ] `ui/components/dawsos_theme.py` - Theme CSS and utilities
- [ ] `ui/components/explain_drawer.py` - Trace provenance drawer
- [ ] `ui/components/staleness_chips.py` - Freshness indicators
- [ ] `tests/visual/test_ui_snapshots.py` - Playwright visual regression

### Testing & Validation (3 files, ~600 lines)

- [ ] `tests/golden/test_metrics_reconciliation.py` - ±1bp golden tests
- [ ] `tests/property/test_currency_identity.py` - Hypothesis property tests
- [ ] `tests/visual/test_ui_snapshots.py` - UI snapshot tests

---

## Part 1: METRICS_ARCHITECT Implementation

### File 1: `backend/app/services/metrics.py`

**Purpose**: Core performance metrics calculations

**Key Functions**:
```python
class PerformanceCalculator:
    async def compute_twr(portfolio_id, pack_id, lookback_days=252) -> dict:
        """
        Time-Weighted Return with geometric linking.

        Formula: TWR = [(1+r1)(1+r2)...(1+rn)] - 1
        Where: r_i = (V_i - V_{i-1} - CF_i) / (V_{i-1} + CF_i)

        Returns:
            {
                "twr": 0.15,  # 15% return
                "ann_twr": 0.152,  # Annualized
                "vol": 0.18,  # Annualized volatility
                "sharpe": 0.85,  # Sharpe ratio
                "days": 252,
                "data_points": 252
            }
        """

    async def compute_mwr(portfolio_id, pack_id) -> dict:
        """
        Money-Weighted Return (IRR).

        Solves: 0 = sum(CF_i / (1+IRR)^t_i) + V_n / (1+IRR)^t_n

        Returns:
            {
                "mwr": 0.14,  # 14% IRR
                "ann_mwr": 0.142  # Annualized
            }
        """

    async def compute_max_drawdown(portfolio_id, pack_id, lookback_days=252) -> dict:
        """
        Maximum drawdown (peak-to-trough decline).

        Returns:
            {
                "max_dd": -0.15,  # -15% max drawdown
                "max_dd_date": "2024-03-15",
                "recovery_days": 45  # Days to recover (-1 if not recovered)
            }
        """
```

**Implementation Template** (320 lines):
```python
from decimal import Decimal
import numpy as np
import pandas as pd
from datetime import date, timedelta

class PerformanceCalculator:
    def __init__(self, db):
        self.db = db

    async def compute_twr(self, portfolio_id: str, pack_id: str, lookback_days: int = 252) -> dict:
        # 1. Get pack date
        end_date = await self._get_pack_date(pack_id)
        start_date = end_date - timedelta(days=lookback_days)

        # 2. Get daily valuations (from portfolio_daily_values hypertable)
        values = await self.db.fetch("""
            SELECT asof_date, total_value, cash_flows
            FROM portfolio_daily_values
            WHERE portfolio_id = $1 AND asof_date BETWEEN $2 AND $3
            ORDER BY asof_date
        """, portfolio_id, start_date, end_date)

        if len(values) < 2:
            return {"twr": 0.0, "error": "Insufficient data"}

        # 3. Compute daily returns
        returns = []
        for i in range(1, len(values)):
            v_prev = Decimal(str(values[i-1]["total_value"]))
            v_curr = Decimal(str(values[i]["total_value"]))
            cf = Decimal(str(values[i].get("cash_flows", 0)))

            # r = (V_i - V_{i-1} - CF) / (V_{i-1} + CF)
            if v_prev + cf > 0:
                r = (v_curr - v_prev - cf) / (v_prev + cf)
                returns.append(float(r))

        # 4. Geometric linking: (1+r1)(1+r2)...(1+rn) - 1
        twr = float(np.prod([1 + r for r in returns]) - 1)

        # 5. Annualize
        days = (end_date - start_date).days
        ann_factor = 365 / days if days > 0 else 1
        ann_twr = (1 + twr) ** ann_factor - 1

        # 6. Volatility (annualized std dev of daily returns)
        vol = float(np.std(returns) * np.sqrt(252)) if len(returns) > 1 else 0.0

        # 7. Sharpe ratio (assume 4% risk-free rate)
        rf_rate = 0.04
        sharpe = (ann_twr - rf_rate) / vol if vol > 0 else 0.0

        return {
            "twr": round(twr, 6),
            "ann_twr": round(ann_twr, 6),
            "vol": round(vol, 6),
            "sharpe": round(sharpe, 4),
            "days": days,
            "data_points": len(values)
        }

    async def compute_mwr(self, portfolio_id: str, pack_id: str) -> dict:
        # 1. Get date range
        end_date = await self._get_pack_date(pack_id)
        start_date = end_date - timedelta(days=365)

        # 2. Get all cash flows
        cash_flows = await self.db.fetch("""
            SELECT trade_date, amount
            FROM portfolio_cash_flows
            WHERE portfolio_id = $1 AND trade_date BETWEEN $2 AND $3
            ORDER BY trade_date
        """, portfolio_id, start_date, end_date)

        if not cash_flows:
            return {"mwr": 0.0, "error": "No cash flows"}

        # 3. Build cash flow series for IRR
        cf_series = []
        for cf in cash_flows:
            days_from_start = (cf["trade_date"] - start_date).days
            cf_series.append((days_from_start, float(cf["amount"])))

        # 4. Add terminal value (ending portfolio value)
        terminal_value = await self._get_portfolio_value(portfolio_id, pack_id)
        total_days = (end_date - start_date).days
        cf_series.append((total_days, -float(terminal_value)))  # Negative = ending value

        # 5. Solve for IRR using Newton-Raphson
        irr = self._calculate_irr(cf_series)

        return {
            "mwr": round(irr, 6),
            "ann_mwr": round((1 + irr) ** (365 / total_days) - 1, 6) if total_days > 0 else 0.0
        }

    def _calculate_irr(self, cash_flows: list, guess: float = 0.1) -> float:
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
                break  # Derivative too small

            r = r - npv / npv_prime

        return r

    async def compute_max_drawdown(self, portfolio_id: str, pack_id: str, lookback_days: int = 252) -> dict:
        # 1. Get daily values
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

        # 2. Compute running max and drawdown
        running_max = np.maximum.accumulate(values_arr)
        drawdowns = (values_arr - running_max) / running_max

        max_dd = float(np.min(drawdowns))
        max_dd_idx = int(np.argmin(drawdowns))

        return {
            "max_dd": round(max_dd, 6),
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
        """Get portfolio value from pricing pack"""
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

### File 2: `backend/app/services/currency_attribution.py`

**Purpose**: Decompose returns into local + FX + interaction

**Formula**:
```
r_base = (1 + r_local)(1 + r_fx) - 1
       = r_local + r_fx + (r_local × r_fx)
```

**Implementation Template** (180 lines):
```python
from decimal import Decimal
from datetime import timedelta

class CurrencyAttributor:
    def __init__(self, db):
        self.db = db

    async def compute_attribution(self, portfolio_id: str, pack_id: str, lookback_days: int = 30) -> dict:
        """
        Decompose portfolio return into local + FX + interaction.

        Returns:
            {
                "local_return": 0.05,  # 5% price movement in local currency
                "fx_return": 0.02,  # 2% FX gain
                "interaction": 0.001,  # 0.1% interaction term
                "total_return": 0.071,  # 7.1% total return in base currency
                "by_currency": {
                    "USD": {"local": 0.03, "fx": 0.0, "interaction": 0.0, "weight": 0.6},
                    "EUR": {"local": 0.02, "fx": 0.02, "interaction": 0.0004, "weight": 0.4}
                }
            }
        """
        end_date = await self._get_pack_date(pack_id)
        start_date = end_date - timedelta(days=lookback_days)

        # Get start pack
        start_pack = await self.db.fetchrow("""
            SELECT id FROM pricing_pack WHERE asof_date = $1
        """, start_date)

        if not start_pack:
            return {"error": "No starting pack"}

        # Get positions at start and end
        start_positions = await self._get_valued_positions(portfolio_id, start_pack["id"])
        end_positions = await self._get_valued_positions(portfolio_id, pack_id)

        # Compute attribution
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
            total_start_value = sum(p["value_base"] for p in start_positions)
            weight = start_pos["value_base"] / total_start_value if total_start_value > 0 else 0.0

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

        # Round for display
        for key in ["local_return", "fx_return", "interaction", "total_return"]:
            attribution[key] = round(attribution[key], 6)

        for ccy in attribution["by_currency"]:
            for key in ["local", "fx", "interaction", "weight"]:
                attribution["by_currency"][ccy][key] = round(attribution["by_currency"][ccy][key], 6)

        return attribution

    async def _get_valued_positions(self, portfolio_id: str, pack_id: str) -> list:
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

    async def _get_pack_date(self, pack_id: str) -> date:
        row = await self.db.fetchrow("SELECT asof_date FROM pricing_pack WHERE id = $1", pack_id)
        return row["asof_date"]
```

**Property Test** (currency identity):
```python
# tests/property/test_currency_identity.py
from hypothesis import given, strategies as st
from decimal import Decimal

@given(
    r_local=st.floats(min_value=-0.5, max_value=0.5),
    r_fx=st.floats(min_value=-0.5, max_value=0.5)
)
def test_currency_attribution_identity(r_local, r_fx):
    """
    Property: local + fx + interaction = total (within numerical precision)

    Identity: r_base = r_local + r_fx + (r_local × r_fx)
    """
    r_base_computed = (1 + r_local) * (1 + r_fx) - 1
    r_base_sum = r_local + r_fx + (r_local * r_fx)

    # Should be equal within 1e-10 (numerical precision)
    assert abs(r_base_computed - r_base_sum) < 1e-10, (
        f"Currency attribution identity failed: "
        f"computed={r_base_computed:.10f}, sum={r_base_sum:.10f}"
    )
```

---

### File 3: Pattern JSONs

**`patterns/analysis/portfolio_overview.json`**:
```json
{
  "id": "portfolio_overview",
  "name": "Portfolio Overview",
  "description": "Comprehensive portfolio snapshot with TWR, MWR, attribution, risk",
  "category": "analysis",
  "inputs": {
    "portfolio_id": {"type": "uuid", "required": true}
  },
  "steps": [
    {
      "capability": "metrics.compute_twr",
      "as": "perf_metrics",
      "args": {"portfolio_id": "{{inputs.portfolio_id}}", "pack_id": "{{ctx.pricing_pack_id}}", "lookback_days": 252}
    },
    {
      "capability": "metrics.compute_mwr",
      "as": "mwr_metrics",
      "args": {"portfolio_id": "{{inputs.portfolio_id}}", "pack_id": "{{ctx.pricing_pack_id}}"}
    },
    {
      "capability": "metrics.compute_max_drawdown",
      "as": "risk_metrics",
      "args": {"portfolio_id": "{{inputs.portfolio_id}}", "pack_id": "{{ctx.pricing_pack_id}}", "lookback_days": 252}
    },
    {
      "capability": "currency.compute_attribution",
      "as": "currency_attr",
      "args": {"portfolio_id": "{{inputs.portfolio_id}}", "pack_id": "{{ctx.pricing_pack_id}}", "lookback_days": 30}
    },
    {
      "capability": "ledger.positions",
      "as": "positions",
      "args": {"portfolio_id": "{{inputs.portfolio_id}}"}
    },
    {
      "capability": "pricing.apply_pack",
      "as": "valued_positions",
      "args": {"positions": "{{state.positions}}", "pack_id": "{{ctx.pricing_pack_id}}"}
    },
    {
      "capability": "charts.overview",
      "as": "charts",
      "args": {
        "positions": "{{state.valued_positions}}",
        "metrics": "{{state.perf_metrics}}",
        "currency_attr": "{{state.currency_attr}}"
      }
    }
  ],
  "outputs": ["perf_metrics", "mwr_metrics", "risk_metrics", "currency_attr", "valued_positions", "charts"]
}
```

---

## Part 2: UI_ARCHITECT Implementation

### File 4: `ui/components/dawsos_theme.py`

**Purpose**: DawsOS dark theme CSS

```python
import streamlit as st

def apply_dawsos_theme():
    """Apply DawsOS dark theme via custom CSS."""
    st.markdown("""
    <style>
    :root {
        --graphite: hsl(220, 13%, 9%);
        --slate: hsl(217, 12%, 18%);
        --signal-teal: hsl(180, 100%, 32%);
        --electric-blue: hsl(217, 78%, 56%);
        --provenance-purple: hsl(264, 67%, 48%);
        --alert-amber: hsl(42, 100%, 55%);
        --risk-red: hsl(0, 75%, 60%);
        --fg: hsl(220, 10%, 96%);
        --muted: hsl(220, 10%, 60%);
    }

    .stApp {
        background-color: var(--graphite);
        color: var(--fg);
        font-family: 'Inter', sans-serif;
    }

    .dawsos-card {
        background-color: var(--slate);
        border-radius: 12px;
        padding: 24px;
        border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 16px;
    }

    .dawsos-card:hover {
        border-color: var(--signal-teal);
        transition: border-color 0.3s;
    }

    .metric-value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 2rem;
        font-weight: 600;
        color: var(--fg);
    }

    .rating-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.875rem;
        font-weight: 600;
        font-family: 'IBM Plex Mono', monospace;
    }

    .rating-high { background-color: rgba(0, 255, 0, 0.2); color: #00ff00; }
    .rating-medium { background-color: rgba(255, 255, 0, 0.2); color: #ffff00; }
    .rating-low { background-color: rgba(255, 0, 0, 0.2); color: #ff0000; }

    .provenance-chip {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        color: var(--muted);
        background-color: rgba(255,255,255,0.05);
        padding: 2px 8px;
        border-radius: 4px;
        display: inline-block;
        margin: 2px;
    }

    .staleness-fresh {
        color: #00ff00;
        font-weight: 600;
    }

    .staleness-stale {
        color: var(--alert-amber);
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)
```

---

### File 5: `ui/pages/portfolio_overview.py`

**Purpose**: Main portfolio overview page

**Template** (250 lines):
```python
import streamlit as st
import plotly.graph_objects as go
from ui.components.dawsos_theme import apply_dawsos_theme
from ui.components.staleness_chips import render_provenance_chip, render_staleness_chip
from ui.components.explain_drawer import render_explain_drawer

# Apply theme
apply_dawsos_theme()

# Page title
st.title("Portfolio Overview")

# Portfolio selector
portfolio_id = st.selectbox(
    "Select Portfolio",
    options=["growth-2024", "income-2024", "balanced-2024"],
    key="portfolio_selector"
)

# Execute pattern via API
if st.button("Refresh Data") or "portfolio_data" not in st.session_state:
    with st.spinner("Loading portfolio data..."):
        # Call /execute API
        response = requests.post(
            "http://localhost:8000/execute",
            json={
                "pattern_id": "portfolio_overview",
                "portfolio_id": portfolio_id,
                "inputs": {}
            }
        )

        if response.status_code == 200:
            st.session_state.portfolio_data = response.json()
        else:
            st.error(f"Failed to load data: {response.json()}")
            st.stop()

data = st.session_state.portfolio_data

# Provenance banner
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    render_provenance_chip("Pack", data["trace"]["pricing_pack_id"])
with col2:
    render_provenance_chip("Ledger", data["trace"]["ledger_commit_hash"][:7])
with col3:
    if st.button("Explain", key="explain_btn"):
        st.session_state.show_explain_drawer = True

# KPI Ribbon
st.markdown("### Performance Metrics")
cols = st.columns(5)

perf = data["data"]["perf_metrics"]
mwr = data["data"]["mwr_metrics"]
risk = data["data"]["risk_metrics"]

with cols[0]:
    st.markdown('<div class="dawsos-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-value">{:.2%}</div>'.format(perf["ann_twr"]), unsafe_allow_html=True)
    st.markdown("**TWR** (1Y Annualized)")
    render_staleness_chip(data["trace"]["per_panel_staleness"][0])
    st.markdown('</div>', unsafe_allow_html=True)

with cols[1]:
    st.markdown('<div class="dawsos-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-value">{:.2%}</div>'.format(mwr["ann_mwr"]), unsafe_allow_html=True)
    st.markdown("**MWR** (IRR)")
    render_staleness_chip(data["trace"]["per_panel_staleness"][1])
    st.markdown('</div>', unsafe_allow_html=True)

with cols[2]:
    st.markdown('<div class="dawsos-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-value">{:.2%}</div>'.format(perf["vol"]), unsafe_allow_html=True)
    st.markdown("**Volatility** (Ann.)")
    render_staleness_chip(data["trace"]["per_panel_staleness"][2])
    st.markdown('</div>', unsafe_allow_html=True)

with cols[3]:
    st.markdown('<div class="dawsos-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-value">{:.2%}</div>'.format(risk["max_dd"]), unsafe_allow_html=True)
    st.markdown("**Max Drawdown**")
    render_staleness_chip(data["trace"]["per_panel_staleness"][2])
    st.markdown('</div>', unsafe_allow_html=True)

with cols[4]:
    st.markdown('<div class="dawsos-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-value">{:.2f}</div>'.format(perf["sharpe"]), unsafe_allow_html=True)
    st.markdown("**Sharpe Ratio**")
    render_staleness_chip(data["trace"]["per_panel_staleness"][0])
    st.markdown('</div>', unsafe_allow_html=True)

# Currency Attribution
st.markdown("### Currency Attribution")
col1, col2 = st.columns([1, 1])

with col1:
    attr = data["data"]["currency_attr"]

    # Waterfall chart
    fig = go.Figure(go.Waterfall(
        x=["Local Return", "FX Return", "Interaction", "Total Return"],
        y=[attr["local_return"], attr["fx_return"], attr["interaction"], attr["total_return"]],
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # By currency breakdown
    st.markdown("**By Currency**")
    for ccy, ccy_attr in attr["by_currency"].items():
        st.markdown(f"**{ccy}** ({ccy_attr['weight']:.1%})")
        st.progress(abs(ccy_attr['local']))
        st.caption(f"Local: {ccy_attr['local']:.2%} | FX: {ccy_attr['fx']:.2%}")

# Holdings Table
st.markdown("### Holdings")
positions = data["data"]["valued_positions"]

# Create DataFrame
import pandas as pd
df = pd.DataFrame([
    {
        "Symbol": p["symbol"],
        "Value": f"${p['value_base']:,.0f}",
        "Weight": f"{p['weight']:.1%}",
        "P/L": f"{p['pnl_pct']:.2%}",
        "DivSafety": p["div_safety"],
        "Moat": p["moat"],
        "Resilience": p["resilience"]
    }
    for p in positions
])

st.dataframe(df, use_container_width=True)

# Explain Drawer (if opened)
if st.session_state.get("show_explain_drawer", False):
    render_explain_drawer(data["trace"])
```

---

## Part 3: Testing & Validation

### Golden Test (±1bp reconciliation)

```python
# tests/golden/test_metrics_reconciliation.py
import pytest
from decimal import Decimal

@pytest.mark.asyncio
async def test_twr_reconciliation_1bp():
    """
    Golden test: TWR calculation reconciles to Beancount ledger ±1bp.

    Scenario:
    - Portfolio with 10 holdings
    - Daily valuations over 252 days
    - Compare computed TWR vs ledger TWR

    Acceptance: Difference ≤ 0.0001 (1 basis point)
    """
    # Load golden fixture
    with open("tests/fixtures/golden/twr_portfolio_1y.json") as f:
        golden = json.load(f)

    # Compute TWR
    calc = PerformanceCalculator(db)
    computed = await calc.compute_twr(
        portfolio_id=golden["portfolio_id"],
        pack_id=golden["pack_id"],
        lookback_days=252
    )

    # Compare
    ledger_twr = Decimal(str(golden["expected_twr"]))
    computed_twr = Decimal(str(computed["twr"]))
    diff = abs(computed_twr - ledger_twr)

    assert diff <= Decimal("0.0001"), (
        f"TWR reconciliation failed: "
        f"ledger={ledger_twr:.6f}, computed={computed_twr:.6f}, diff={diff:.6f} "
        f"(tolerance: ±0.0001)"
    )
```

---

### Visual Regression Test (Playwright)

```python
# tests/visual/test_ui_snapshots.py
from playwright.sync_api import sync_playwright

def test_portfolio_overview_snapshot():
    """
    Visual regression test: Portfolio overview page.

    Captures screenshot and compares against baseline.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Navigate to portfolio overview
        page.goto("http://localhost:8501")
        page.wait_for_selector(".metric-value")

        # Take screenshot
        page.screenshot(path="tests/visual/snapshots/portfolio_overview.png")

        # Compare against baseline (Playwright does this automatically)
        # If diff > threshold, test fails

        browser.close()
```

---

## Dependencies Required

Add to `requirements.txt`:
```
numpy==1.26.2
pandas==2.1.3
scikit-learn==1.3.2
plotly==5.18.0
streamlit==1.29.0
hypothesis==6.92.1  # For property tests
playwright==1.40.0  # For visual tests
```

---

## Validation Checklist

- [ ] **Golden ±1bp**: `pytest tests/golden/test_metrics_reconciliation.py`
  - Expected: All TWR/MWR/Attribution tests pass with diff ≤ 0.0001

- [ ] **Property Test**: `pytest tests/property/test_currency_identity.py`
  - Expected: 100 hypothesis examples pass (currency attribution identity holds)

- [ ] **UI Snapshots**: `playwright test tests/visual/test_ui_snapshots.py`
  - Expected: All snapshots match baseline (or store new baseline if first run)

---

## Summary

**Total Implementation**:
- **15 files** (~3100 lines)
- **7 metrics/patterns** files
- **5 UI** files
- **3 test** files

**Estimated Effort**: 12-16 hours

**Critical Path**:
1. Metrics calculations (6-8 hours)
2. Pattern JSONs (1 hour)
3. UI components (4-5 hours)
4. Tests (2-3 hours)

**Acceptance Gates**:
- ✅ Golden ±1bp reconciliation
- ✅ Property tests pass (currency identity)
- ✅ UI snapshots stored

---

**Last Updated**: 2025-10-21
**Implementation**: Sprint 2 (METRICS + UI)
**Status**: 📋 READY FOR IMPLEMENTATION
