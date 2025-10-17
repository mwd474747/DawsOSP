# Consolidated Refactoring Implementation Plan

**Date**: October 16, 2025
**Status**: 📋 Ready for Implementation
**Scope**: DawsOS codebase-wide + prediction features
**Total Impact**: 15-20% codebase reduction + improved maintainability

---

## Executive Summary

This plan consolidates two refactoring analyses:
1. **Codebase-wide refactoring** (REFACTORING_OPPORTUNITIES.md) - 571 opportunities
2. **Prediction-specific refactoring** (PREDICTION_CODE_REFACTORING.md) - 200+ line reduction

**Combined Benefits**:
- **Reduce codebase by 15-20%** (800-1,000 lines)
- **Eliminate 90% of code duplication** in predictions
- **Improve function complexity** (174 → 95 branches in critical functions)
- **Better maintainability** through reusable components
- **Zero breaking changes** - all functionality preserved

**Estimated Total Effort**: 15-20 hours (can be done incrementally over 2-3 weeks)

---

## Priority Matrix

| Priority | Category | Impact | Risk | Effort | Lines Saved |
|----------|----------|--------|------|--------|-------------|
| **P0** | Quick Wins | Medium | None | 30 min | 50-100 |
| **P1** | Prediction Refactoring | High | Low | 2-3 hrs | 200-250 |
| **P2** | Function Decomposition | High | Medium | 4-6 hrs | 400-500 |
| **P3** | Dead Code Removal | Medium | High | 2-3 hrs | 200-300 |
| **P4** | Structural Improvements | Medium | Low | 6-8 hrs | 100-150 |

---

## Phase 1: Quick Wins (Week 1, Day 1 - 30 minutes)

### ✅ P0.1: Move Utility Scripts to scripts/

**Impact**: Organization, reduce root clutter
**Risk**: None (just file moves)
**Time**: 5 minutes

```bash
# Move 6 utility scripts from dawsos/ to scripts/
mv dawsos/data_integrity_cli.py scripts/
mv dawsos/fix_orphan_nodes.py scripts/
mv dawsos/manage_knowledge.py scripts/
mv dawsos/seed_knowledge.py scripts/
mv dawsos/seed_knowledge_graph.py scripts/
mv dawsos/verify_apis.py scripts/

# Update any imports (if necessary)
git grep -l "from dawsos.data_integrity_cli" | xargs sed -i '' 's/from dawsos\.data_integrity_cli/from scripts.data_integrity_cli/g'
```

**Validation**: Run `./start.sh` and ensure app loads correctly

### ✅ P0.2: Fix Legacy String Module Pattern

**Impact**: Python 3 compatibility
**Risk**: Low
**Time**: 5 minutes

**File**: [dawsos/agents/code_monkey.py](dawsos/agents/code_monkey.py)

```python
# BEFORE
import string
result = string.upper(text)

# AFTER
result = text.upper()
```

**Validation**: Run `pytest dawsos/tests/validation/`

### ✅ P0.3: Remove Unused Imports (after validation)

**Impact**: Reduce dependencies, faster imports
**Risk**: None (linter-verified)
**Time**: 10 minutes

**Files to clean** (18 unused imports):
- [dawsos/ui/alert_panel.py](dawsos/ui/alert_panel.py)
- [dawsos/ui/data_integrity_tab.py](dawsos/ui/data_integrity_tab.py)
- [dawsos/ui/governance_tab.py](dawsos/ui/governance_tab.py)
- [dawsos/ui/trinity_dashboard_tabs.py](dawsos/ui/trinity_dashboard_tabs.py)

**Validation**: For each import, verify not used via `eval()` or dynamic imports before removing

### ✅ P0.4: Create Refactoring Branch

```bash
git checkout -b refactoring-consolidation
git add -A
git commit -m "chore: Quick wins - move scripts, fix legacy patterns, clean imports"
```

**Lines Saved**: ~50-100 lines

---

## Phase 2: Prediction Code Refactoring (Week 1, Days 2-3 - 2-3 hours)

### 🔥 P1.1: Create Unified Forecast Engine

**Impact**: Eliminates 150+ lines of duplication
**Risk**: Low (requires thorough testing)
**Time**: 1.5 hours

**Step 1**: Create new file [dawsos/forecasting/forecast_engine.py](dawsos/forecasting/forecast_engine.py)

```python
"""
Unified forecasting engine for all prediction types.

This module consolidates duplicate forecasting logic from sector rotation
and macro indicators into a single, reusable engine.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Any, Optional
from core.knowledge_loader import get_knowledge_loader

@dataclass
class ForecastScenario:
    """Single forecast scenario (bull/base/bear)"""
    value: float
    confidence: float
    assumptions: List[str]

@dataclass
class Forecast:
    """Complete forecast for one horizon"""
    horizon: str  # '1y', '2y', '5y'
    bull: ForecastScenario
    base: ForecastScenario
    bear: ForecastScenario
    confidence: float
    metadata: Dict[str, Any]

class ForecastEngine:
    """
    Unified forecasting engine for all prediction types.

    Provides common infrastructure for:
    - Economic cycle context
    - Multi-scenario generation (bull/base/bear)
    - Confidence scoring
    - Assumptions/risks generation

    Usage:
        engine = ForecastEngine()
        forecasts = engine.generate_forecast(
            'unemployment',
            current_value=4.3,
            forecast_fn=self._forecast_unemployment,
            horizons=[1, 2, 5]
        )
    """

    def __init__(self):
        self._knowledge_loader = None
        self._cycle_cache = None
        self._logger = None

    @property
    def knowledge_loader(self):
        """Lazy-loaded knowledge loader"""
        if self._knowledge_loader is None:
            self._knowledge_loader = get_knowledge_loader()
        return self._knowledge_loader

    @property
    def logger(self):
        """Lazy-loaded logger"""
        if self._logger is None:
            import logging
            self._logger = logging.getLogger(__name__)
        return self._logger

    def get_cycle_context(self) -> Dict[str, Any]:
        """
        Get current economic cycle context (cached).

        Returns:
            Dict with:
                - phase: str ('expansion', 'peak', 'contraction', 'trough')
                - phase_start: datetime
                - phase_month: int (months since phase start)
                - phase_progress: float (0.0 to 1.0)
                - typical_length: int (months)
        """
        if self._cycle_cache is None:
            try:
                cycles_data = self.knowledge_loader.get_dataset('economic_cycles')

                # Current cycle: expansion since Oct 2023
                phase_start = datetime(2023, 10, 1)
                phase_month = int((datetime.now() - phase_start).days / 30)
                typical_expansion_length = 72  # months
                phase_progress = min(phase_month / typical_expansion_length, 1.0)

                self._cycle_cache = {
                    'phase': 'expansion',
                    'phase_start': phase_start,
                    'phase_month': phase_month,
                    'phase_progress': phase_progress,
                    'typical_length': typical_expansion_length,
                    'cycles_data': cycles_data
                }
            except Exception as e:
                self.logger.warning(f"Could not load cycle context: {e}")
                # Fallback to default
                self._cycle_cache = {
                    'phase': 'expansion',
                    'phase_start': datetime(2023, 10, 1),
                    'phase_month': 24,
                    'phase_progress': 0.33,
                    'typical_length': 72,
                    'cycles_data': None
                }

        return self._cycle_cache

    def generate_forecast(
        self,
        indicator_name: str,
        current_value: float,
        forecast_fn: Callable[[Dict, float, int], ForecastScenario],
        horizons: List[int] = [1, 2, 5]
    ) -> Dict[str, Forecast]:
        """
        Generate forecasts for multiple horizons.

        Args:
            indicator_name: Name of indicator (e.g., 'unemployment')
            current_value: Current value of indicator
            forecast_fn: Function that generates base scenario for one horizon
                Signature: (cycle_context, current_value, years) -> ForecastScenario
            horizons: List of years to forecast (default: [1, 2, 5])

        Returns:
            Dict mapping horizon ('1y', '2y', '5y') to Forecast objects
        """
        cycle_context = self.get_cycle_context()
        forecasts = {}

        for years in horizons:
            horizon_key = f'{years}y'

            try:
                # Generate base scenario using provided function
                base_scenario = forecast_fn(cycle_context, current_value, years)

                # Generate bull/bear variants
                bull_scenario = self._generate_bull_scenario(base_scenario, years, indicator_name)
                bear_scenario = self._generate_bear_scenario(base_scenario, years, indicator_name)

                forecasts[horizon_key] = Forecast(
                    horizon=horizon_key,
                    bull=bull_scenario,
                    base=base_scenario,
                    bear=bear_scenario,
                    confidence=base_scenario.confidence,
                    metadata={
                        'generated_at': datetime.now(),
                        'cycle_phase': cycle_context['phase'],
                        'phase_progress': cycle_context['phase_progress'],
                        'indicator_name': indicator_name,
                        'current_value': current_value
                    }
                )
            except Exception as e:
                self.logger.error(f"Error generating {horizon_key} forecast for {indicator_name}: {e}")
                # Create fallback forecast
                forecasts[horizon_key] = self._create_fallback_forecast(
                    horizon_key, current_value, indicator_name
                )

        return forecasts

    def _generate_bull_scenario(
        self,
        base: ForecastScenario,
        years: int,
        indicator_name: str
    ) -> ForecastScenario:
        """Generate optimistic scenario (better than base by 10-20%)"""
        improvement_factor = 0.85 if years <= 2 else 0.80

        # For unemployment/CPI, lower is better
        if 'unemployment' in indicator_name.lower() or 'cpi' in indicator_name.lower():
            bull_value = base.value * improvement_factor
        else:
            # For GDP/Fed funds/returns, higher is better (contextual)
            if 'gdp' in indicator_name.lower() or 'return' in indicator_name.lower():
                bull_value = base.value * 1.15
            else:
                bull_value = base.value * 0.90  # Fed funds lower in bull case

        return ForecastScenario(
            value=bull_value,
            confidence=base.confidence * 0.75,  # Lower confidence for optimistic
            assumptions=base.assumptions + [
                "Strong productivity gains from AI/technology",
                "No major geopolitical disruptions"
            ]
        )

    def _generate_bear_scenario(
        self,
        base: ForecastScenario,
        years: int,
        indicator_name: str
    ) -> ForecastScenario:
        """Generate pessimistic scenario (worse than base by 15-30%)"""
        deterioration_factor = 1.15 if years <= 2 else 1.25

        # For unemployment/CPI, higher is worse
        if 'unemployment' in indicator_name.lower() or 'cpi' in indicator_name.lower():
            bear_value = base.value * deterioration_factor
        else:
            # For GDP, lower is worse
            if 'gdp' in indicator_name.lower() or 'return' in indicator_name.lower():
                bear_value = base.value * 0.70
            else:
                bear_value = base.value * 1.20  # Fed funds higher in bear case

        return ForecastScenario(
            value=bear_value,
            confidence=base.confidence * 0.70,  # Lower confidence for pessimistic
            assumptions=base.assumptions + [
                "Recession triggers within forecast horizon",
                "Elevated geopolitical or financial risks"
            ]
        )

    def _create_fallback_forecast(
        self,
        horizon: str,
        current_value: float,
        indicator_name: str
    ) -> Forecast:
        """Create fallback forecast when generation fails"""
        base_scenario = ForecastScenario(
            value=current_value,
            confidence=0.3,
            assumptions=["Fallback forecast - insufficient data"]
        )

        return Forecast(
            horizon=horizon,
            bull=base_scenario,
            base=base_scenario,
            bear=base_scenario,
            confidence=0.3,
            metadata={
                'generated_at': datetime.now(),
                'error': True,
                'indicator_name': indicator_name
            }
        )

    def get_assumptions(self, cycle_ctx: Optional[Dict] = None) -> List[str]:
        """
        Generate standard assumptions based on cycle context.

        Returns:
            List of assumption strings for forecast disclosure
        """
        cycle_ctx = cycle_ctx or self.get_cycle_context()

        months_remaining = max(0, cycle_ctx['typical_length'] - cycle_ctx['phase_month'])
        end_date = cycle_ctx['phase_start'] + timedelta(days=cycle_ctx['typical_length']*30)

        return [
            f"Current {cycle_ctx['phase']} continues for ~{months_remaining} months (until {end_date.strftime('%b %Y')})",
            "No major black swan events (pandemic, war, financial crisis)",
            "Fed maintains 2% inflation target credibility",
            "Historical cycle patterns (2007-2025) continue to hold",
            f"Typical {cycle_ctx['phase']} length: 48-96 months (using {cycle_ctx['typical_length']}-month baseline)"
        ]

    def get_risks(
        self,
        recession_prob_2y: float,
        recession_prob_5y: float,
        cycle_ctx: Optional[Dict] = None
    ) -> List[str]:
        """
        Generate standard risk disclosures.

        Args:
            recession_prob_2y: Probability of recession in 2 years (0.0-1.0)
            recession_prob_5y: Probability of recession in 5 years (0.0-1.0)
            cycle_ctx: Optional cycle context (uses current if not provided)

        Returns:
            List of risk disclosure strings
        """
        cycle_ctx = cycle_ctx or self.get_cycle_context()
        phase_progress = cycle_ctx['phase_progress']

        risks = [
            f"Recession probability: {int(recession_prob_2y*100)}% in 2 years, {int(recession_prob_5y*100)}% in 5 years",
            "Inflation could resurge if wage-price spiral or supply shocks",
            "Geopolitical shocks (wars, trade wars) not modeled",
            "Structural changes (AI revolution, demographics) may alter patterns",
            "Debt crisis (government or corporate) could trigger financial instability"
        ]

        # Add cycle-specific risks
        if phase_progress > 0.7:
            risks.append(f"Late-cycle risks elevated (expansion {int(phase_progress*100)}% complete)")

        return risks
```

**Step 2**: Create [dawsos/forecasting/__init__.py](dawsos/forecasting/__init__.py)

```python
"""
DawsOS Forecasting Module

Unified forecasting infrastructure for predictions across:
- Sector rotation
- Macro indicators (unemployment, Fed funds, CPI, GDP)
- Stock prices (future)
- Earnings (future)
"""

from dawsos.forecasting.forecast_engine import (
    ForecastEngine,
    Forecast,
    ForecastScenario
)

__all__ = [
    'ForecastEngine',
    'Forecast',
    'ForecastScenario'
]
```

**Step 3**: Update [dawsos/ui/trinity_dashboard_tabs.py](dawsos/ui/trinity_dashboard_tabs.py) to use ForecastEngine

Replace `_generate_macro_forecasts()` method (Lines 1918-2201):

```python
def _generate_macro_forecasts(self, current_data: dict) -> dict:
    """Generate forward macro indicator forecasts using unified engine"""
    try:
        from dawsos.forecasting import ForecastEngine, ForecastScenario

        engine = ForecastEngine()
        cycle_ctx = engine.get_cycle_context()

        # Generate forecasts for each indicator
        forecasts = {
            'unemployment': engine.generate_forecast(
                'unemployment',
                current_data.get('unemployment', 4.3),
                self._forecast_unemployment
            ),
            'fed_funds': engine.generate_forecast(
                'fed_funds',
                current_data.get('fed_funds', 4.22),
                self._forecast_fed_funds
            ),
            'cpi_change': engine.generate_forecast(
                'cpi_change',
                current_data.get('cpi_yoy', 3.5),
                self._forecast_cpi
            ),
            'gdp_growth': engine.generate_forecast(
                'gdp_growth',
                current_data.get('gdp_growth', 2.5),
                self._forecast_gdp
            )
        }

        # Calculate recession probabilities
        phase_progress = cycle_ctx['phase_progress']
        recession_prob_2y = min((phase_progress + 0.3) * 0.4, 0.5)
        recession_prob_5y = min((phase_progress + 0.5) * 0.6, 0.8)

        return {
            **forecasts,
            'assumptions': engine.get_assumptions(cycle_ctx),
            'risks': engine.get_risks(recession_prob_2y, recession_prob_5y, cycle_ctx),
            'last_updated': datetime.now(),
            'metadata': {
                'cycle_phase': cycle_ctx['phase'],
                'phase_progress': phase_progress,
                'phase_month': cycle_ctx['phase_month']
            }
        }

    except Exception as e:
        self.logger.error(f"Error generating macro forecasts: {e}")
        return {'error': str(e)}

# Add individual forecast methods (extract from original logic)
def _forecast_unemployment(self, cycle_ctx: dict, current: float, years: int) -> ForecastScenario:
    """Forecast unemployment for given horizon"""
    from dawsos.forecasting import ForecastScenario

    phase_progress = cycle_ctx['phase_progress']

    if years == 1:
        if phase_progress < 0.5:
            value = max(3.5, current - 0.1)
        else:
            value = current
        confidence = 0.70
    elif years == 2:
        recession_prob = min((phase_progress + 0.3) * 0.4, 0.5)
        expansion_val = max(3.5, current - 0.2)
        recession_val = 5.5
        value = expansion_val * (1 - recession_prob) + recession_val * recession_prob
        confidence = 0.55
    else:  # 5 years
        value = 4.8
        confidence = 0.35

    return ForecastScenario(
        value=value,
        confidence=confidence,
        assumptions=[
            f"Cycle-based forecast: {cycle_ctx['phase']} phase",
            "Labor market follows historical patterns"
        ]
    )

def _forecast_fed_funds(self, cycle_ctx: dict, current: float, years: int) -> ForecastScenario:
    """Forecast Fed funds using Taylor Rule"""
    from dawsos.forecasting import ForecastScenario

    neutral_rate = 2.5
    inflation_target = 2.0

    # Simple Taylor Rule implementation
    if years == 1:
        inflation = 2.4
        unemployment = 4.2
    elif years == 2:
        inflation = 2.2
        unemployment = 4.5
    else:
        inflation = 2.0
        unemployment = 4.8

    inflation_gap = inflation - inflation_target
    unemployment_gap = unemployment - 4.0

    value = neutral_rate + 1.5 * inflation_gap - 0.5 * unemployment_gap
    value = max(0.25, min(value, 4.5))

    confidence = 0.65 if years == 1 else (0.55 if years == 2 else 0.40)

    return ForecastScenario(
        value=value,
        confidence=confidence,
        assumptions=[
            "Taylor Rule: r = neutral + 1.5×(π-target) - 0.5×(u gap)",
            f"Neutral rate: {neutral_rate}%"
        ]
    )

def _forecast_cpi(self, cycle_ctx: dict, current: float, years: int) -> ForecastScenario:
    """Forecast CPI using mean reversion"""
    from dawsos.forecasting import ForecastScenario

    target = 2.0
    reversion_speed = 0.35

    # Mean reversion to 2% target
    if years == 1:
        value = current - (current - target) * reversion_speed
    elif years == 2:
        value = current - (current - target) * reversion_speed * 1.5
    else:
        value = target + 0.2  # Slight overshoot

    confidence = 0.60 if years == 1 else (0.50 if years == 2 else 0.35)

    return ForecastScenario(
        value=value,
        confidence=confidence,
        assumptions=[
            "Mean reversion to 2% Fed target",
            f"Reversion speed: {int(reversion_speed*100)}% per year"
        ]
    )

def _forecast_gdp(self, cycle_ctx: dict, current: float, years: int) -> ForecastScenario:
    """Forecast GDP growth"""
    from dawsos.forecasting import ForecastScenario

    phase_progress = cycle_ctx['phase_progress']
    potential_growth = 2.0

    if years == 1:
        value = 2.3 if phase_progress < 0.5 else 2.0
        confidence = 0.65
    elif years == 2:
        value = 1.8
        confidence = 0.50
    else:
        value = 2.0
        confidence = 0.30

    return ForecastScenario(
        value=value,
        confidence=confidence,
        assumptions=[
            f"Long-run potential growth: {potential_growth}%",
            "Productivity growth steady"
        ]
    )
```

**Validation**:
```bash
# Test forecasting engine
pytest dawsos/tests/validation/ -k forecast

# Manual test in Streamlit
./start.sh
# Navigate to Economy tab → Macro Forecasts
```

**Lines Saved**: ~150 lines

### 🔥 P1.2: Create Unified Prediction UI Component

**Impact**: Eliminates 100+ lines
**Risk**: Low
**Time**: 1 hour

**Step 1**: Create [dawsos/ui/utils/cache_helper.py](dawsos/ui/utils/cache_helper.py)

```python
"""
Session state caching utilities for Streamlit.

Provides TTL-based caching with automatic expiration and refresh.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Tuple, Callable, Any, Optional

class CacheManager:
    """Unified session state caching for predictions"""

    @staticmethod
    def get_cached_data(
        cache_key: str,
        ttl_seconds: int,
        fetch_fn: Callable[[], Any],
        force_refresh: bool = False,
        spinner_msg: str = "Loading..."
    ) -> Tuple[Any, Optional[datetime]]:
        """
        Get data from cache or fetch if expired.

        Args:
            cache_key: Unique key for this cached data
            ttl_seconds: Time-to-live in seconds
            fetch_fn: Function to call if cache miss/expired
            force_refresh: If True, bypass cache
            spinner_msg: Message to show during fetch

        Returns:
            Tuple of (data, timestamp)
        """
        data_key = f'{cache_key}_data'
        timestamp_key = f'{cache_key}_timestamp'

        # Initialize if not exists
        if data_key not in st.session_state:
            st.session_state[data_key] = None
            st.session_state[timestamp_key] = None

        # Check if refresh needed
        needs_refresh = (
            st.session_state[data_key] is None or
            force_refresh or
            (st.session_state[timestamp_key] and
             (datetime.now() - st.session_state[timestamp_key]).total_seconds() > ttl_seconds)
        )

        if needs_refresh:
            with st.spinner(spinner_msg):
                st.session_state[data_key] = fetch_fn()
                st.session_state[timestamp_key] = datetime.now()

        return st.session_state[data_key], st.session_state[timestamp_key]
```

**Step 2**: Create [dawsos/forecasting/prediction_ui.py](dawsos/forecasting/prediction_ui.py)

```python
"""
Unified UI components for predictions.

Provides reusable UI patterns for:
- Prediction panels with caching and refresh
- Forecast comparison tables
- Confidence-based styling
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Callable, List, Optional

class PredictionUI:
    """Unified UI for all prediction types"""

    @staticmethod
    def render_prediction_panel(
        title: str,
        subtitle: str,
        cache_key: str,
        ttl_seconds: int,
        generate_fn: Callable[[], Dict],
        tabs_config: Dict[str, Callable],
        icon: str = "🔮"
    ):
        """
        Render complete prediction panel with caching, tabs, and refresh.

        Args:
            title: Main title (e.g., "Sector Rotation Predictions")
            subtitle: Subtitle/description
            cache_key: Key for session state cache
            ttl_seconds: Time-to-live for cache
            generate_fn: Function to generate predictions
            tabs_config: Dict mapping tab name to render function
            icon: Emoji icon for title
        """
        st.markdown(f"### {icon} {title}")
        st.caption(subtitle)

        # Caching with refresh button
        from ui.utils.cache_helper import CacheManager

        col1, col2 = st.columns([6, 1])
        with col2:
            refresh = st.button("🔄", key=f"refresh_{cache_key}", help="Refresh predictions")

        predictions, timestamp = CacheManager.get_cached_data(
            cache_key=cache_key,
            ttl_seconds=ttl_seconds,
            fetch_fn=generate_fn,
            force_refresh=refresh,
            spinner_msg=f"Generating {title.lower()}..."
        )

        # Status indicator
        PredictionUI._render_cache_status(timestamp, ttl_seconds)

        # Tabbed interface
        if predictions and 'error' not in predictions:
            tabs = st.tabs(list(tabs_config.keys()))
            for tab, (tab_name, render_fn) in zip(tabs, tabs_config.items()):
                with tab:
                    render_fn(predictions)
        else:
            st.error(f"❌ Error generating predictions: {predictions.get('error', 'Unknown error')}")

    @staticmethod
    def _render_cache_status(timestamp: Optional[datetime], ttl_seconds: int):
        """Render cache age indicator"""
        if timestamp:
            age = datetime.now() - timestamp
            age_minutes = int(age.total_seconds() / 60)
            ttl_minutes = int(ttl_seconds / 60)

            if age_minutes < ttl_minutes / 2:
                status = f"🟢 Fresh ({age_minutes}m old)"
            elif age_minutes < ttl_minutes:
                status = f"🟡 Aging ({age_minutes}m old)"
            else:
                status = f"🔴 Stale ({age_minutes}m old)"

            st.caption(f"{status} • Updates every {ttl_minutes} minutes")

class ForecastTableGenerator:
    """Generate comparison tables for forecasts"""

    @staticmethod
    def generate_comparison_table(
        forecasts: Dict[str, Dict],
        horizons: List[str] = ['1y', '2y', '5y'],
        include_confidence: bool = True
    ) -> pd.DataFrame:
        """
        Generate formatted comparison table for multiple forecasts.

        Args:
            forecasts: Dict mapping indicator name to forecast data
            horizons: List of horizons to include
            include_confidence: Whether to show confidence indicators

        Returns:
            Formatted pandas DataFrame ready for display
        """
        from ui.utils.display_helpers import ConfidenceFormatter

        rows = []
        for name, forecast_data in forecasts.items():
            row = {'Indicator': name}

            for horizon in horizons:
                h_data = forecast_data.get(horizon, {})
                base = h_data.get('base', 0)
                conf = h_data.get('confidence', 0)

                if include_confidence:
                    conf_display = ConfidenceFormatter.get_display(conf)
                    row[horizon.upper()] = f"{base:.1f} {conf_display.icon}"
                else:
                    row[horizon.upper()] = f"{base:.1f}"

            rows.append(row)

        return pd.DataFrame(rows)

    @staticmethod
    def render_comparison_table(
        forecasts: Dict[str, Dict],
        title: str = "Forecast Summary",
        **kwargs
    ):
        """Generate and render comparison table with title"""
        st.markdown(f"##### {title}")
        df = ForecastTableGenerator.generate_comparison_table(forecasts, **kwargs)
        st.dataframe(df, use_container_width=True, hide_index=True)

        if kwargs.get('include_confidence', True):
            st.caption("🟢 = High confidence (>65%) | 🟡 = Medium (45-65%) | 🔴 = Low (<45%)")
```

**Step 3**: Update [dawsos/ui/trinity_dashboard_tabs.py](dawsos/ui/trinity_dashboard_tabs.py) to use PredictionUI

Replace `_render_macro_forecasts()` method (Lines 2203-2405):

```python
def _render_macro_forecasts(self) -> None:
    """Render auto-loading macro indicator forecasts"""
    from dawsos.forecasting.prediction_ui import PredictionUI, ForecastTableGenerator

    PredictionUI.render_prediction_panel(
        title="Forward Macro Projections",
        subtitle="AI-powered forecasts for unemployment, Fed funds, inflation, and GDP growth",
        cache_key='macro_forecasts',
        ttl_seconds=21600,  # 6 hours
        generate_fn=lambda: self._generate_macro_forecasts({
            'unemployment': 4.3,
            'fed_funds': 4.22,
            'cpi_yoy': 3.5,
            'gdp_growth': 2.5
        }),
        tabs_config={
            "📊 Overview": self._render_macro_overview,
            "👥 Unemployment": lambda p: self._render_macro_detail(p, 'unemployment', 'Unemployment Rate', '%'),
            "💰 Fed Funds": lambda p: self._render_macro_detail(p, 'fed_funds', 'Fed Funds Rate', '%'),
            "📈 Inflation": lambda p: self._render_macro_detail(p, 'cpi_change', 'CPI Change', '%'),
            "🏭 GDP Growth": lambda p: self._render_macro_detail(p, 'gdp_growth', 'GDP Growth', '%')
        },
        icon="🔮"
    )

def _render_macro_overview(self, predictions: dict) -> None:
    """Render macro forecast overview tab"""
    from dawsos.forecasting.prediction_ui import ForecastTableGenerator

    # Comparison table
    ForecastTableGenerator.render_comparison_table(
        {
            'Unemployment Rate (%)': predictions.get('unemployment', {}),
            'Fed Funds Rate (%)': predictions.get('fed_funds', {}),
            'CPI Change (%)': predictions.get('cpi_change', {}),
            'GDP Growth (%)': predictions.get('gdp_growth', {})
        },
        title="All Indicators Summary"
    )

    # Assumptions and risks
    st.markdown("---")
    with st.expander("📋 Key Assumptions", expanded=False):
        for assumption in predictions.get('assumptions', []):
            st.markdown(f"- {assumption}")

    with st.expander("⚠️ Key Risks", expanded=False):
        for risk in predictions.get('risks', []):
            st.markdown(f"- {risk}")

def _render_macro_detail(self, predictions: dict, key: str, title: str, unit: str) -> None:
    """Render detail tab for single indicator"""
    import plotly.graph_objects as go

    indicator_data = predictions.get(key, {})

    # Metrics for each horizon
    col1, col2, col3 = st.columns(3)

    for col, horizon in zip([col1, col2, col3], ['1y', '2y', '5y']):
        h_data = indicator_data.get(horizon, {})
        base = h_data.get('base', 0)
        conf = h_data.get('confidence', 0)

        with col:
            st.metric(
                label=f"{horizon.upper()} Forecast",
                value=f"{base:.1f}{unit}",
                delta=None,
                help=f"Confidence: {int(conf*100)}%"
            )

    # Chart with bull/base/bear scenarios
    st.markdown("##### Scenario Analysis")

    horizons = []
    bull_vals = []
    base_vals = []
    bear_vals = []

    for horizon in ['1y', '2y', '5y']:
        h_data = indicator_data.get(horizon, {})
        horizons.append(horizon)
        bull_vals.append(h_data.get('bull', 0))
        base_vals.append(h_data.get('base', 0))
        bear_vals.append(h_data.get('bear', 0))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=horizons, y=bull_vals, mode='lines+markers', name='Bull', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=horizons, y=base_vals, mode='lines+markers', name='Base', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=horizons, y=bear_vals, mode='lines+markers', name='Bear', line=dict(color='red')))

    fig.update_layout(
        title=f"{title} Forecast Scenarios",
        xaxis_title="Horizon",
        yaxis_title=unit,
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)
```

**Validation**:
```bash
# Test UI components
./start.sh
# Navigate to Economy tab → Macro Forecasts
# Verify refresh button, caching, tabs all work
```

**Lines Saved**: ~100 lines

### 🔥 P1.3: Update Sector Predictions to Use Unified Components

**Time**: 30 minutes

Update [dawsos/ui/trinity_dashboard_tabs.py](dawsos/ui/trinity_dashboard_tabs.py):

```python
def _render_sector_rotation_predictions(self) -> None:
    """Render sector rotation predictions using unified UI"""
    from dawsos.forecasting.prediction_ui import PredictionUI

    PredictionUI.render_prediction_panel(
        title="Sector Rotation Predictions",
        subtitle="AI-powered sector forecasts based on economic cycle analysis",
        cache_key='sector_predictions',
        ttl_seconds=3600,  # 1 hour
        generate_fn=lambda: self._generate_sector_rotation_predictions({}),
        tabs_config={
            "📊 Overview": self._render_sector_overview,
            "📈 Top Picks": lambda p: self._render_sector_top_picks(p),
            "⚠️ Avoid": lambda p: self._render_sector_avoid(p)
        },
        icon="🔮"
    )

# Keep existing detail render methods (_render_sector_overview, etc.)
```

**Lines Saved**: ~50 lines

**Total Phase 2 Lines Saved**: ~200-250 lines

---

## Phase 3: Function Decomposition (Week 2, Days 1-2 - 4-6 hours)

### 🛠️ P2.1: Split `render_governance_tab()` (HIGHEST PRIORITY)

**Impact**: Massive maintainability improvement
**Risk**: Medium (requires careful testing)
**Time**: 2-3 hours

**File**: [dawsos/ui/governance_tab.py](dawsos/ui/governance_tab.py) (Lines 14-1025)

**Current**: 1,011 lines, complexity 123 branches

**Target**: 8-10 functions, <150 lines each, <15 branches each

**Refactoring Plan**:

```python
# AFTER: Composed from smaller functions
def render_governance_tab(runtime, capabilities: dict):
    """Main governance tab - composed from modular sections"""
    _render_dashboard_header()

    st.markdown("---")
    _render_governance_metrics(runtime)

    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Policy Management",
        "📊 Audit Log",
        "✅ Compliance Checks",
        "🔍 Data Quality"
    ])

    with tab1:
        _render_policy_management(runtime)
    with tab2:
        _render_audit_log(runtime)
    with tab3:
        _render_compliance_checks(runtime)
    with tab4:
        _render_data_quality(runtime)

def _render_dashboard_header():
    """Render governance dashboard header"""
    # ~30 lines

def _render_governance_metrics(runtime):
    """Render key governance metrics"""
    # ~50 lines

def _render_policy_management(runtime):
    """Render policy management section"""
    # ~150 lines

def _render_audit_log(runtime):
    """Render audit log section"""
    # ~120 lines

def _render_compliance_checks(runtime):
    """Render compliance checks section"""
    # ~100 lines

def _render_data_quality(runtime):
    """Render data quality section"""
    # ~80 lines
```

**Validation**:
```bash
pytest dawsos/tests/validation/
./start.sh  # Manual test
```

**Lines Saved**: No reduction, but massive complexity reduction (123 → <15 branches per function)

### 🛠️ P2.2: Split `main()` in main.py

**Time**: 1 hour

**File**: [dawsos/main.py](dawsos/main.py) (Lines 630-993)

**Current**: 363 lines, complexity 34 branches

**Target**: 5 functions, <100 lines each

```python
def main():
    """Main Streamlit app entry point - composed from modules"""
    _initialize_app()

    sidebar_state = _render_sidebar()

    _render_main_tabs(sidebar_state)

def _initialize_app():
    """Initialize session state and configuration"""
    # Lines 630-720 (90 lines)

def _render_sidebar():
    """Render sidebar with settings and agent selector"""
    # Lines 721-850 (130 lines)
    return {'selected_agent': agent, 'api_keys': keys}

def _render_main_tabs(sidebar_state):
    """Render main tabbed interface"""
    # Lines 851-993 (143 lines)
```

**Lines Saved**: None, but improves testability and maintainability

### 🛠️ P2.3: Split `render_api_health_tab()`

**Time**: 1 hour

**File**: [dawsos/ui/api_health_tab.py](dawsos/ui/api_health_tab.py) (Lines 17-381)

**Current**: 364 lines, complexity 17 branches

**Target**: 6 functions for each API + overview

```python
def render_api_health_tab(runtime, capabilities: dict):
    """Main API health tab"""
    _render_api_overview()

    st.markdown("---")

    apis = ['FMP', 'FRED', 'OpenAI', 'Anthropic']
    tabs = st.tabs([f"🔌 {api}" for api in apis])

    for tab, api in zip(tabs, apis):
        with tab:
            _render_api_health(api, runtime)

def _render_api_overview():
    """Overview of all APIs"""
    # ~50 lines

def _render_api_health(api_name: str, runtime):
    """Render health check for specific API"""
    # ~60 lines per API
```

**Lines Saved**: ~50 lines through consolidation

### 🛠️ P2.4: Split Other Long Functions

**Time**: 1-2 hours

Apply similar patterns to remaining long functions:
- `render_trinity_dashboard()` - 231 lines → 4 functions
- `init_session_state()` - 179 lines → dataclass-based approach
- Others in list from REFACTORING_OPPORTUNITIES.md

**Total Phase 3 Lines Saved**: ~400-500 lines through consolidation + massive complexity reduction

---

## Phase 4: Dead Code Removal (Week 2, Days 3-4 - 2-3 hours)

### ⚠️ P3.1: Validate and Remove Unused Files

**Impact**: Medium
**Risk**: High (needs careful validation)
**Time**: 1-2 hours

**Process**:
1. For each potentially unused file:
   ```bash
   # Check if imported anywhere
   git grep -l "from.*<module_name> import"
   git grep -l "import <module_name>"

   # Check git history
   git log --oneline --follow -- <file> | head -20
   ```

2. If truly unused:
   ```bash
   git rm <file>
   ```

3. Run full test suite:
   ```bash
   pytest dawsos/tests/validation/
   ```

**High-confidence removals** (likely one-time scripts):
- ✅ `dawsos/fix_orphan_nodes.py` (already moved to scripts/)
- ✅ `dawsos/seed_knowledge.py` (already moved to scripts/)
- ✅ `dawsos/seed_knowledge_graph.py` (already moved to scripts/)

**Lines Saved**: ~200-300 lines

### ⚠️ P3.2: Remove Unused Functions

**Time**: 1 hour

Similar validation process for functions marked as unused.

**IMPORTANT**: Many functions may be used via:
- Dynamic imports
- Pattern engine actions
- Streamlit callbacks
- String-based dispatch

**Only remove if 100% certain unused.**

**Lines Saved**: ~100-200 lines (after careful validation)

**Total Phase 4 Lines Saved**: ~200-300 lines

---

## Phase 5: Structural Improvements (Week 3 - 6-8 hours)

### 🏗️ P4.1: Extract UI Components into Submodules

**Impact**: Organization, parallel development
**Risk**: Low
**Time**: 3-4 hours

**Current**:
```
dawsos/ui/
  - governance_tab.py (1,011 lines)
  - api_health_tab.py (364 lines)
  - trinity_dashboard_tabs.py (4,200+ lines)
```

**Proposed**:
```
dawsos/ui/
  governance/
    - __init__.py
    - dashboard.py (200 lines)
    - policy_management.py (150 lines)
    - audit_log.py (120 lines)
    - compliance_checks.py (100 lines)
    - data_quality.py (80 lines)

  api_health/
    - __init__.py
    - overview.py (50 lines)
    - component_health.py (60 lines per API × 4)

  trinity_dashboard/
    - __init__.py
    - overview.py
    - markets.py
    - economy.py
    - predictions.py
```

**Lines Saved**: ~100-150 lines through consolidation

### 🏗️ P4.2: Consolidate Duplicate Functions

**Time**: 2-3 hours

Review 82 duplicate function names and:
1. Keep both if different functionality
2. Consolidate into shared module if identical
3. Rename for clarity if similar but different

**Example**: `calculate_confidence()` duplicated 2 times → move to `dawsos/ui/utils/display_helpers.py`

**Lines Saved**: ~50-100 lines

### 🏗️ P4.3: Simplify Pattern Engine (ADVANCED)

**Time**: 2-3 hours
**Risk**: High

Convert `_execute_action_legacy()` (118 branches) to action registry pattern.

**Note**: Partially exists in `dawsos/core/actions/` but legacy method still used.

**Recommendation**: Defer to Phase 6 (future work) unless critical.

**Total Phase 5 Lines Saved**: ~100-150 lines

---

## Implementation Schedule

### Week 1: Quick Wins + Predictions
| Day | Phase | Hours | Focus |
|-----|-------|-------|-------|
| Mon | P0 | 0.5 | Quick wins (scripts, imports, legacy) |
| Tue | P1.1 | 1.5 | Forecast engine |
| Wed | P1.2 | 1.0 | Prediction UI |
| Thu | P1.3 | 0.5 | Sector predictions update |
| Fri | - | 1.0 | Testing + documentation |

**Week 1 Total**: 4.5 hours, ~250-350 lines saved

### Week 2: Function Decomposition + Dead Code
| Day | Phase | Hours | Focus |
|-----|-------|-------|-------|
| Mon | P2.1 | 2.0 | Split governance_tab |
| Tue | P2.2-2.4 | 2.0 | Split main, api_health, others |
| Wed | P3.1 | 1.5 | Validate/remove dead files |
| Thu | P3.2 | 1.0 | Remove unused functions |
| Fri | - | 1.0 | Testing + documentation |

**Week 2 Total**: 7.5 hours, ~600-800 lines saved

### Week 3: Structural Improvements (Optional)
| Day | Phase | Hours | Focus |
|-----|-------|-------|-------|
| Mon | P4.1 | 3.0 | Extract UI submodules |
| Tue | P4.2 | 2.0 | Consolidate duplicates |
| Wed | - | 1.0 | Testing + documentation |

**Week 3 Total**: 6 hours, ~100-150 lines saved

**Grand Total**: 18 hours, ~950-1,300 lines saved (18-24% reduction)

---

## Risk Mitigation Strategy

### Before Starting
1. ✅ Create git branch: `git checkout -b refactoring-consolidation`
2. ✅ Run full test suite: `pytest dawsos/tests/validation/`
3. ✅ Backup patterns: `cp -r dawsos/patterns dawsos/patterns.backup`
4. ✅ Document current state: `git log --oneline --graph --all -20 > git-state-backup.txt`

### During Each Phase
1. ✅ Work on one refactoring at a time
2. ✅ Run tests after each change: `pytest dawsos/tests/validation/`
3. ✅ Manual smoke test: `./start.sh` → test affected UI
4. ✅ Commit frequently with descriptive messages:
   ```bash
   git add -A
   git commit -m "refactor(predictions): Add unified forecast engine [P1.1]"
   ```

### Rollback Plan
```bash
# View recent changes
git log --oneline -10

# Revert last commit (safe)
git revert HEAD

# Revert to specific commit
git revert <commit-hash>

# Nuclear option (use with caution)
git reset --hard HEAD~1
```

### Testing Checklist

After each phase:
- [ ] All unit tests passing: `pytest dawsos/tests/validation/`
- [ ] Streamlit app launches: `./start.sh`
- [ ] All tabs load without errors
- [ ] Predictions generate correctly
- [ ] No console errors
- [ ] Performance not degraded

---

## Success Metrics

### Code Metrics
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Total Lines** | ~12,000 | ~10,000-10,500 | 12-17% reduction |
| **Prediction Code** | 1,400 | 1,100-1,200 | 14-21% reduction |
| **Avg Function Length** | 50 lines | 30 lines | 40% reduction |
| **Max Function Complexity** | 123 branches | <20 branches | 84% reduction |
| **Code Duplication** | 300+ lines | <50 lines | 83% reduction |

### Maintainability Metrics
- ✅ All functions <150 lines
- ✅ All functions <20 branches
- ✅ Unified forecasting infrastructure
- ✅ Reusable UI components
- ✅ Better test coverage (smaller functions = easier to test)

### Developer Experience
- ✅ Faster onboarding (clearer code structure)
- ✅ Easier to add new predictions (unified engine)
- ✅ Parallel development enabled (submodules)
- ✅ Reduced merge conflicts

---

## Post-Refactoring Tasks

### Documentation Updates
1. Update [CLAUDE.md](CLAUDE.md):
   - Add forecasting module documentation
   - Update metrics (lines, functions, etc.)
   - Document new UI component patterns

2. Update [docs/AgentDevelopmentGuide.md](docs/AgentDevelopmentGuide.md):
   - Add section on prediction development
   - Document ForecastEngine usage

3. Create new guide: `docs/PredictionDevelopmentGuide.md`
   - How to add new prediction types
   - ForecastEngine API reference
   - UI component patterns

### Code Quality
1. Run linters:
   ```bash
   python scripts/lint_patterns.py
   flake8 dawsos/ --max-line-length=120
   mypy dawsos/forecasting/
   ```

2. Add type hints to new modules:
   - `forecast_engine.py` - 100% coverage
   - `prediction_ui.py` - 100% coverage

3. Add unit tests:
   - `test_forecast_engine.py` - test all scenarios
   - `test_prediction_ui.py` - test caching, rendering

### Performance Validation
1. Benchmark before/after:
   ```bash
   # App startup time
   time ./start.sh

   # Prediction generation time
   # (measure in UI with timestamp logging)
   ```

2. Profile if needed:
   ```bash
   python -m cProfile -o profile.stats dawsos/main.py
   ```

---

## Future Enhancements (Post-Refactoring)

### Short-term (1-2 months)
1. **Stock Price Forecasts** - Use ForecastEngine for individual stocks
2. **Earnings Predictions** - Integrate with earnings_analysis pattern
3. **VIX Forecasts** - Options market volatility predictions
4. **Correlation Forecasts** - Predict sector correlation shifts

### Medium-term (3-6 months)
1. **Machine Learning Integration** - Train models on historical data
2. **Ensemble Forecasting** - Combine multiple models
3. **Backtesting Framework** - Validate forecast accuracy
4. **Confidence Calibration** - Adjust confidence based on historical performance

### Long-term (6-12 months)
1. **Real-time Forecast Updates** - As new data arrives
2. **Explainable AI** - Show why forecasts changed
3. **User Feedback Loop** - Learn from user corrections
4. **Multi-asset Forecasts** - Stocks, bonds, commodities, FX

---

## Conclusion

This consolidated refactoring plan provides a clear, incremental path to:

1. **Reduce codebase by 15-20%** (800-1,000 lines)
2. **Eliminate 90% of code duplication**
3. **Improve maintainability** through unified components
4. **Preserve all functionality** - zero breaking changes
5. **Enable rapid feature development** with reusable infrastructure

**Recommended Approach**:
- **Week 1**: Quick wins + prediction refactoring (highest ROI)
- **Week 2**: Function decomposition + dead code removal (highest risk)
- **Week 3**: Structural improvements (optional, long-term benefit)

**Total Effort**: 18 hours over 3 weeks (6 hours/week)
**Total Impact**: ~1,000 lines saved + massive complexity reduction

Ready to proceed with **Phase 1 (Quick Wins)** when approved.

---

**Document Version**: 1.0
**Status**: ✅ Ready for Implementation
**Next Step**: Approve plan → Execute Phase 1
