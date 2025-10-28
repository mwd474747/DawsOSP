'use client'

import { RegimeCard } from './RegimeCard'
import { CycleAnalysis } from './CycleAnalysis'
import { DaRVisualization } from './DaRVisualization'
import { MacroIndicators } from './MacroIndicators'
import { useMacroDashboard } from '@/lib/queries'

export function MacroDashboard() {
  // Fetch macro data using React Query
  const { 
    data: macroData, 
    isLoading, 
    error, 
    refetch 
  } = useMacroDashboard();

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Macro Dashboard</h1>
          <p className="text-slate-600 dark:text-slate-400">Loading macro data...</p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-3/4 mb-4"></div>
              <div className="h-8 bg-slate-200 rounded w-1/2 mb-2"></div>
              <div className="h-3 bg-slate-200 rounded w-1/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Macro Dashboard</h1>
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <p className="text-red-800 dark:text-red-200 font-medium">Error loading macro data</p>
            <p className="text-red-600 dark:text-red-300 text-sm mt-2">
              {error instanceof Error ? error.message : 'Unknown error occurred'}
            </p>
            <button 
              onClick={() => refetch()}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Extract data from API response or use defaults
  const regimeData = macroData?.result?.regime_data || {
    current: 'MID_EXPANSION',
    confidence: 0.87,
    duration: '8 months',
    indicators: ['GDP Growth', 'Unemployment', 'Inflation', 'Yield Curve'],
  };

  const cycleData = macroData?.result?.cycle_data || {
    stdc: { phase: 'Expansion', confidence: 0.82, duration: '6 months' },
    ltdc: { phase: 'Late Cycle', confidence: 0.75, duration: '18 months' },
    empire: { phase: 'Rising', confidence: 0.68, duration: '12 months' },
  };

  const darData = macroData?.result?.dar_data || {
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
  };

  const indicators = macroData?.result?.indicators || [
    { name: 'GDP Growth', value: 2.4, change: 0.2, trend: 'up' as const, significance: 'high' as const },
    { name: 'Unemployment', value: 3.8, change: -0.1, trend: 'down' as const, significance: 'high' as const },
    { name: 'Inflation (CPI)', value: 3.2, change: -0.3, trend: 'down' as const, significance: 'high' as const },
    { name: '10Y-2Y Spread', value: 0.15, change: 0.05, trend: 'up' as const, significance: 'medium' as const },
    { name: 'VIX', value: 18.5, change: -2.1, trend: 'down' as const, significance: 'medium' as const },
    { name: 'Dollar Index', value: 103.2, change: 0.8, trend: 'up' as const, significance: 'medium' as const },
  ];

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
