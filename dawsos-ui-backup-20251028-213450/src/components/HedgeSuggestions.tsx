interface HedgeSuggestion {
  instrument: string
  strike?: number
  expiry?: string
  allocation?: number
  cost_bps: number
  protection: number
  description: string
}

interface HedgeSuggestionsProps {
  suggestions: HedgeSuggestion[]
}

export function HedgeSuggestions({ suggestions }: HedgeSuggestionsProps) {
  const getProtectionColor = (protection: number) => {
    if (protection >= 0.8) return 'bg-accent-100 text-accent-800 border-accent-200'
    if (protection >= 0.6) return 'bg-primary-100 text-primary-800 border-primary-200'
    if (protection >= 0.4) return 'bg-warning-100 text-warning-800 border-warning-200'
    return 'bg-red-100 text-red-800 border-red-200'
  }

  const getCostColor = (cost_bps: number) => {
    if (cost_bps <= 50) return 'profit'
    if (cost_bps <= 100) return 'neutral'
    return 'loss'
  }

  return (
    <div className="metric-card">
      <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Hedge Suggestions</h3>
      
      <div className="space-y-fib4">
        {suggestions.map((hedge, index) => (
          <div key={index} className="border border-slate-200 rounded-fib3 p-fib4">
            <div className="flex items-start justify-between mb-fib3">
              <div className="flex-1">
                <h4 className="text-sm font-medium text-slate-900 mb-fib1">{hedge.instrument}</h4>
                <p className="text-xs text-slate-600">{hedge.description}</p>
              </div>
              <div className={`rating-badge ${getProtectionColor(hedge.protection)}`}>
                {(hedge.protection * 100).toFixed(0)}% Protection
              </div>
            </div>

            {/* Hedge Details */}
            <div className="grid grid-cols-2 gap-fib3 mb-fib3">
              {hedge.strike && (
                <div>
                  <div className="text-xs text-slate-600">Strike</div>
                  <div className="text-sm font-medium text-slate-900">{hedge.strike}</div>
                </div>
              )}
              {hedge.expiry && (
                <div>
                  <div className="text-xs text-slate-600">Expiry</div>
                  <div className="text-sm font-medium text-slate-900">{hedge.expiry}</div>
                </div>
              )}
              {hedge.allocation && (
                <div>
                  <div className="text-xs text-slate-600">Allocation</div>
                  <div className="text-sm font-medium text-slate-900">{(hedge.allocation * 100).toFixed(0)}%</div>
                </div>
              )}
              <div>
                <div className="text-xs text-slate-600">Cost</div>
                <div className={`text-sm font-medium ${getCostColor(hedge.cost_bps)}`}>
                  {hedge.cost_bps} bps
                </div>
              </div>
            </div>

            {/* Cost vs Protection Bar */}
            <div className="space-y-fib1">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-600">Cost vs Protection</span>
                <span className="text-xs text-slate-600">
                  {hedge.cost_bps} bps / {(hedge.protection * 100).toFixed(0)}%
                </span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-fib1">
                <div 
                  className="h-fib1 rounded-full bg-primary-500"
                  style={{ width: `${(hedge.protection * 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="mt-fib5 pt-fib4 border-t border-slate-200">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-900">Total Hedge Cost</span>
          <span className="text-sm font-medium text-slate-900">
            {suggestions.reduce((sum, hedge) => sum + hedge.cost_bps, 0)} bps
          </span>
        </div>
        <div className="flex items-center justify-between mt-fib1">
          <span className="text-sm font-medium text-slate-900">Average Protection</span>
          <span className="text-sm font-medium text-slate-900">
            {((suggestions.reduce((sum, hedge) => sum + hedge.protection, 0) / suggestions.length) * 100).toFixed(0)}%
          </span>
        </div>
      </div>
    </div>
  )
}
