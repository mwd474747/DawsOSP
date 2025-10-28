interface Scenario {
  name: string
  probability: number
  impact: number
}

interface DaRVisualizationProps {
  dar: number
  benchmark_dar: number
  confidence: number
  horizon_days: number
  scenarios: Scenario[]
}

export function DaRVisualization({ dar, benchmark_dar, confidence, horizon_days, scenarios }: DaRVisualizationProps) {
  const darPercentage = (dar * 100).toFixed(1)
  const benchmarkPercentage = (benchmark_dar * 100).toFixed(1)
  const outperformance = ((dar - benchmark_dar) / benchmark_dar * 100).toFixed(1)

  return (
    <div className="metric-card">
      <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Drawdown at Risk (DaR)</h3>
      
      {/* DaR Summary */}
      <div className="grid grid-cols-2 gap-fib4 mb-fib6">
        <div className="text-center p-fib4 bg-slate-50 rounded-fib3">
          <div className="text-2xl font-bold text-slate-900">{darPercentage}%</div>
          <div className="text-xs text-slate-600">Portfolio DaR</div>
        </div>
        <div className="text-center p-fib4 bg-slate-50 rounded-fib3">
          <div className="text-2xl font-bold text-slate-900">{benchmarkPercentage}%</div>
          <div className="text-xs text-slate-600">Benchmark DaR</div>
        </div>
      </div>

      {/* Performance vs Benchmark */}
      <div className="mb-fib6">
        <div className="flex items-center justify-between mb-fib2">
          <span className="text-sm text-slate-600">vs Benchmark</span>
          <span className={`text-sm font-medium ${
            parseFloat(outperformance) > 0 ? 'loss' : 'profit'
          }`}>
            {outperformance > 0 ? '+' : ''}{outperformance}%
          </span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-fib2">
          <div 
            className={`h-fib2 rounded-full ${
              parseFloat(outperformance) > 0 ? 'bg-red-500' : 'bg-accent-500'
            }`}
            style={{ width: `${Math.min(Math.abs(parseFloat(outperformance)) * 10, 100)}%` }}
          ></div>
        </div>
      </div>

      {/* Scenario Analysis */}
      <div>
        <div className="flex items-center justify-between mb-fib4">
          <h4 className="text-sm font-medium text-slate-900">Scenario Analysis</h4>
          <span className="text-xs text-slate-600">{horizon_days} days</span>
        </div>
        
        <div className="space-y-fib3">
          {scenarios.map((scenario, index) => (
            <div key={index} className="flex items-center justify-between p-fib3 bg-slate-50 rounded-fib2">
              <div className="flex-1">
                <div className="text-sm font-medium text-slate-900">{scenario.name}</div>
                <div className="text-xs text-slate-600">
                  {(scenario.probability * 100).toFixed(0)}% probability
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-slate-900">
                  {(scenario.impact * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-slate-600">impact</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Confidence Indicator */}
      <div className="mt-fib5 pt-fib4 border-t border-slate-200">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-600">Model Confidence</span>
          <span className="text-xs font-medium text-slate-900">
            {(confidence * 100).toFixed(0)}%
          </span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-fib1 mt-fib1">
          <div 
            className="h-fib1 rounded-full bg-primary-500"
            style={{ width: `${confidence * 100}%` }}
          ></div>
        </div>
      </div>
    </div>
  )
}
