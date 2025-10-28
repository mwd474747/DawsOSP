interface CycleData {
  phase: string
  confidence: number
  duration: string
}

interface CycleAnalysisProps {
  stdc: CycleData
  ltdc: CycleData
  empire: CycleData
}

export function CycleAnalysis({ stdc, ltdc, empire }: CycleAnalysisProps) {
  const cycles = [
    { name: 'STDC', label: 'Short-Term Debt Cycle', data: stdc, color: 'bg-primary-500' },
    { name: 'LTDC', label: 'Long-Term Debt Cycle', data: ltdc, color: 'bg-secondary-500' },
    { name: 'Empire', label: 'Empire Cycle', data: empire, color: 'bg-accent-500' },
  ]

  return (
    <div className="metric-card">
      <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Cycle Analysis</h3>
      
      <div className="space-y-fib5">
        {cycles.map((cycle) => (
          <div key={cycle.name} className="border border-slate-200 rounded-fib3 p-fib4">
            <div className="flex items-center justify-between mb-fib3">
              <div className="flex items-center space-x-fib3">
                <div className={`w-fib3 h-fib3 ${cycle.color} rounded-fib1`}></div>
                <div>
                  <h4 className="text-sm font-medium text-slate-900">{cycle.name}</h4>
                  <p className="text-xs text-slate-600">{cycle.label}</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-slate-900">{cycle.data.phase}</div>
                <div className="text-xs text-slate-600">{cycle.data.duration}</div>
              </div>
            </div>
            
            {/* Confidence Bar */}
            <div className="space-y-fib1">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-600">Confidence</span>
                <span className="text-xs font-medium text-slate-900">
                  {(cycle.data.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-fib1">
                <div 
                  className={`h-fib1 rounded-full ${cycle.color}`}
                  style={{ width: `${cycle.data.confidence * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Cycle Phase Legend */}
      <div className="mt-fib5 pt-fib4 border-t border-slate-200">
        <h5 className="text-xs font-medium text-slate-600 mb-fib2">Cycle Phases</h5>
        <div className="grid grid-cols-2 gap-fib2 text-xs">
          <div className="flex items-center space-x-fib1">
            <div className="w-fib1 h-fib1 bg-accent-500 rounded-full"></div>
            <span className="text-slate-600">Expansion</span>
          </div>
          <div className="flex items-center space-x-fib1">
            <div className="w-fib1 h-fib1 bg-warning-500 rounded-full"></div>
            <span className="text-slate-600">Late Cycle</span>
          </div>
          <div className="flex items-center space-x-fib1">
            <div className="w-fib1 h-fib1 bg-red-500 rounded-full"></div>
            <span className="text-slate-600">Recession</span>
          </div>
          <div className="flex items-center space-x-fib1">
            <div className="w-fib1 h-fib1 bg-primary-500 rounded-full"></div>
            <span className="text-slate-600">Recovery</span>
          </div>
        </div>
      </div>
    </div>
  )
}
