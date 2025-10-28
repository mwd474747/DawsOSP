'use client'

import { RegimeCard } from './RegimeCard'
import { CycleAnalysis } from './CycleAnalysis'
import { DaRVisualization } from './DaRVisualization'
import { MacroIndicators } from './MacroIndicators'

export function MacroDashboard() {
  const regimeData = {
    current: 'MID_EXPANSION',
    confidence: 0.87,
    duration: '8 months',
    indicators: ['GDP Growth', 'Unemployment', 'Inflation', 'Yield Curve'],
  }

  const cycleData = {
    stdc: { phase: 'Expansion', confidence: 0.82, duration: '6 months' },
    ltdc: { phase: 'Late Cycle', confidence: 0.75, duration: '18 months' },
    empire: { phase: 'Rising', confidence: 0.68, duration: '12 months' },
  }

  const darData = {
    portfolio_dar: 0.12,
    benchmark_dar: 0.08,
    confidence: 0.95,
    horizon_days: 30,
    scenarios: [
      { name: 'Recession', probability: 0.15, impact: 0.25 },
      { name: 'Stagflation', probability: 0.25, impact: 0.18 },
      { name: 'Soft Landing', probability: 0.45, impact: 0.08 },
      { name: 'Goldilocks', probability: 0.15, impact: 0.05 },
    ],
  }

  const indicators = [
    { name: 'GDP Growth', value: 2.4, change: 0.2, trend: 'up' as const, significance: 'high' as const },
    { name: 'Unemployment', value: 3.8, change: -0.1, trend: 'down' as const, significance: 'high' as const },
    { name: 'Inflation (CPI)', value: 3.2, change: -0.3, trend: 'down' as const, significance: 'high' as const },
    { name: '10Y-2Y Spread', value: 0.15, change: 0.05, trend: 'up' as const, significance: 'medium' as const },
    { name: 'VIX', value: 18.5, change: -2.1, trend: 'down' as const, significance: 'medium' as const },
    { name: 'Dollar Index', value: 103.2, change: 0.8, trend: 'up' as const, significance: 'medium' as const },
  ]

  return (
    <div className="max-w-7xl mx-auto px-fib8 py-fib6">
      {/* Page Header */}
      <div className="mb-fib8">
        <h1 className="text-3xl font-bold text-slate-900 mb-fib2">Macro Dashboard</h1>
        <p className="text-slate-600">Regime detection, cycle analysis, and scenario risk assessment</p>
      </div>

      {/* Regime Cards Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-fib8 mb-fib8">
        <RegimeCard 
          title="Current Regime" 
          regime={regimeData.current}
          confidence={regimeData.confidence}
          duration={regimeData.duration}
          indicators={regimeData.indicators}
        />
        <RegimeCard 
          title="STDC Cycle" 
          regime={cycleData.stdc.phase}
          confidence={cycleData.stdc.confidence}
          duration={cycleData.stdc.duration}
          indicators={['Employment', 'Consumer Spending', 'Business Investment']}
        />
        <RegimeCard 
          title="LTDC Cycle" 
          regime={cycleData.ltdc.phase}
          confidence={cycleData.ltdc.confidence}
          duration={cycleData.ltdc.duration}
          indicators={['Debt Levels', 'Credit Growth', 'Asset Valuations']}
        />
      </div>

      {/* DaR and Cycle Analysis Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-fib8 mb-fib8">
        <DaRVisualization 
          dar={darData.portfolio_dar}
          benchmark_dar={darData.benchmark_dar}
          confidence={darData.confidence}
          horizon_days={darData.horizon_days}
          scenarios={darData.scenarios}
        />
        <CycleAnalysis 
          stdc={cycleData.stdc}
          ltdc={cycleData.ltdc}
          empire={cycleData.empire}
        />
      </div>

      {/* Macro Indicators */}
      <div className="metric-card">
        <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Macro Indicators</h3>
        <MacroIndicators indicators={indicators} />
      </div>
    </div>
  )
}
