interface Scenario {
  id: string
  name: string
  description: string
  probability: number
  impact: number
  regime: string
  factors: string[]
  portfolio_impact: number
  duration_months: number
}

interface ScenarioCardProps {
  scenario: Scenario
}

export function ScenarioCard({ scenario }: ScenarioCardProps) {
  const getRegimeColor = (regime: string) => {
    switch (regime) {
      case 'RECESSION': return 'bg-red-100 text-red-800 border-red-200'
      case 'STAGFLATION': return 'bg-warning-100 text-warning-800 border-warning-200'
      case 'MID_EXPANSION': return 'bg-primary-100 text-primary-800 border-primary-200'
      case 'EARLY_EXPANSION': return 'bg-accent-100 text-accent-800 border-accent-200'
      default: return 'bg-slate-100 text-slate-800 border-slate-200'
    }
  }

  const getImpactColor = (impact: number) => {
    if (impact >= 0.15) return 'loss'
    if (impact >= 0.05) return 'neutral'
    return 'profit'
  }

  return (
    <div className="metric-card">
      <div className="flex items-start justify-between mb-fib4">
        <h3 className="text-lg font-semibold text-slate-900">{scenario.name}</h3>
        <div className={`rating-badge ${getRegimeColor(scenario.regime)}`}>
          {scenario.regime.replace('_', ' ')}
        </div>
      </div>

      <p className="text-sm text-slate-600 mb-fib5">{scenario.description}</p>

      {/* Probability and Impact */}
      <div className="grid grid-cols-2 gap-fib4 mb-fib5">
        <div className="text-center p-fib3 bg-slate-50 rounded-fib2">
          <div className="text-lg font-bold text-slate-900">
            {(scenario.probability * 100).toFixed(0)}%
          </div>
          <div className="text-xs text-slate-600">Probability</div>
        </div>
        <div className="text-center p-fib3 bg-slate-50 rounded-fib2">
          <div className={`text-lg font-bold ${
            getImpactColor(scenario.impact)
          }`}>
            {(scenario.impact * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-slate-600">Impact</div>
        </div>
      </div>

      {/* Portfolio Impact */}
      <div className="mb-fib5">
        <div className="flex items-center justify-between mb-fib2">
          <span className="text-sm text-slate-600">Portfolio Impact</span>
          <span className={`text-sm font-medium ${
            scenario.portfolio_impact >= 0 ? 'profit' : 'loss'
          }`}>
            {(scenario.portfolio_impact * 100).toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-fib2">
          <div 
            className={`h-fib2 rounded-full ${
              scenario.portfolio_impact >= 0 ? 'bg-accent-500' : 'bg-red-500'
            }`}
            style={{ width: `${Math.min(Math.abs(scenario.portfolio_impact) * 500, 100)}%` }}
          ></div>
        </div>
      </div>

      {/* Duration */}
      <div className="flex items-center justify-between mb-fib5">
        <span className="text-sm text-slate-600">Expected Duration</span>
        <span className="text-sm font-medium text-slate-900">
          {scenario.duration_months} months
        </span>
      </div>

      {/* Key Factors */}
      <div>
        <h4 className="text-sm font-medium text-slate-900 mb-fib3">Key Factors</h4>
        <div className="space-y-fib1">
          {scenario.factors.map((factor, index) => (
            <div key={index} className="flex items-center space-x-fib2">
              <div className="w-fib1 h-fib1 bg-primary-500 rounded-full"></div>
              <span className="text-xs text-slate-600">{factor}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
