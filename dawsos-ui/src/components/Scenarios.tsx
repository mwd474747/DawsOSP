'use client'

import { ScenarioCard } from './ScenarioCard'
import { ImpactAnalysis } from './ImpactAnalysis'
import { HedgeSuggestions } from './HedgeSuggestions'

export function Scenarios() {
  const scenarios = [
    {
      id: 'recession',
      name: 'Recession Scenario',
      description: 'Economic contraction with rising unemployment and falling GDP',
      probability: 0.15,
      impact: 0.25,
      regime: 'RECESSION',
      factors: ['GDP Growth', 'Unemployment', 'Consumer Spending'],
      portfolio_impact: -0.18,
      duration_months: 12,
    },
    {
      id: 'stagflation',
      name: 'Stagflation Scenario',
      description: 'High inflation with stagnant economic growth',
      probability: 0.25,
      impact: 0.18,
      regime: 'STAGFLATION',
      factors: ['Inflation', 'GDP Growth', 'Interest Rates'],
      portfolio_impact: -0.12,
      duration_months: 18,
    },
    {
      id: 'soft_landing',
      name: 'Soft Landing Scenario',
      description: 'Gradual economic slowdown without recession',
      probability: 0.45,
      impact: 0.08,
      regime: 'MID_EXPANSION',
      factors: ['Interest Rates', 'Employment', 'Consumer Confidence'],
      portfolio_impact: -0.05,
      duration_months: 6,
    },
    {
      id: 'goldilocks',
      name: 'Goldilocks Scenario',
      description: 'Optimal economic conditions with moderate growth and low inflation',
      probability: 0.15,
      impact: 0.05,
      regime: 'EARLY_EXPANSION',
      factors: ['GDP Growth', 'Inflation', 'Employment'],
      portfolio_impact: 0.08,
      duration_months: 24,
    },
  ]

  const impactAnalysis = {
    total_portfolio_value: 1247832.45,
    worst_case_loss: -224610.84,
    best_case_gain: 99826.60,
    expected_value: -18717.49,
    var_95: -0.15,
    cvar_95: -0.22,
  }

  const hedgeSuggestions = [
    {
      instrument: 'SPY Put Options',
      strike: 420,
      expiry: '2025-12-19',
      cost_bps: 150,
      protection: 0.85,
      description: 'Protects against market decline below 420',
    },
    {
      instrument: 'VIX Calls',
      strike: 25,
      expiry: '2025-12-19',
      cost_bps: 80,
      protection: 0.60,
      description: 'Hedges against volatility spike',
    },
    {
      instrument: 'TLT (Treasury Bonds)',
      allocation: 0.15,
      cost_bps: 20,
      protection: 0.40,
      description: 'Flight to quality hedge',
    },
  ]

  return (
    <div className="max-w-7xl mx-auto px-fib8 py-fib6">
      {/* Page Header */}
      <div className="mb-fib8">
        <h1 className="text-3xl font-bold text-slate-900 mb-fib2">Scenario Analysis</h1>
        <p className="text-slate-600">Stress testing, impact analysis, and hedge suggestions</p>
      </div>

      {/* Scenario Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-fib8 mb-fib8">
        {scenarios.map((scenario) => (
          <ScenarioCard key={scenario.id} scenario={scenario} />
        ))}
      </div>

      {/* Impact Analysis and Hedge Suggestions Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-fib8 mb-fib8">
        <ImpactAnalysis analysis={impactAnalysis} />
        <HedgeSuggestions suggestions={hedgeSuggestions} />
      </div>

      {/* Additional Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-fib8">
        <div className="metric-card">
          <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Risk Metrics</h3>
          <div className="space-y-fib4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">VaR (95%)</span>
              <span className="text-sm font-medium loss">{(impactAnalysis.var_95 * 100).toFixed(1)}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">CVaR (95%)</span>
              <span className="text-sm font-medium loss">{(impactAnalysis.cvar_95 * 100).toFixed(1)}%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Max Drawdown</span>
              <span className="text-sm font-medium loss">-18.0%</span>
            </div>
          </div>
        </div>
        
        <div className="metric-card">
          <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Scenario Weights</h3>
          <div className="space-y-fib3">
            {scenarios.map((scenario) => (
              <div key={scenario.id} className="flex items-center justify-between">
                <span className="text-sm text-slate-600">{scenario.name}</span>
                <span className="text-sm font-medium text-slate-900">
                  {(scenario.probability * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="metric-card">
          <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Regime Distribution</h3>
          <div className="space-y-fib3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Expansion</span>
              <span className="text-sm font-medium text-slate-900">60%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Stagflation</span>
              <span className="text-sm font-medium text-slate-900">25%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Recession</span>
              <span className="text-sm font-medium text-slate-900">15%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
