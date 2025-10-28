interface ImpactAnalysisProps {
  analysis: {
    total_portfolio_value: number
    worst_case_loss: number
    best_case_gain: number
    expected_value: number
    var_95: number
    cvar_95: number
  }
}

export function ImpactAnalysis({ analysis }: ImpactAnalysisProps) {
  const worstCasePercentage = (analysis.worst_case_loss / analysis.total_portfolio_value) * 100
  const bestCasePercentage = (analysis.best_case_gain / analysis.total_portfolio_value) * 100
  const expectedPercentage = (analysis.expected_value / analysis.total_portfolio_value) * 100

  return (
    <div className="metric-card">
      <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Impact Analysis</h3>
      
      {/* Summary Metrics */}
      <div className="grid grid-cols-1 gap-fib4 mb-fib6">
        <div className="text-center p-fib4 bg-slate-50 rounded-fib3">
          <div className="text-2xl font-bold text-slate-900">
            ${analysis.total_portfolio_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </div>
          <div className="text-xs text-slate-600">Current Portfolio Value</div>
        </div>
      </div>

      {/* Scenario Outcomes */}
      <div className="space-y-fib4 mb-fib6">
        <div className="flex items-center justify-between p-fib3 bg-red-50 rounded-fib2">
          <div>
            <div className="text-sm font-medium text-slate-900">Worst Case</div>
            <div className="text-xs text-slate-600">Recession Scenario</div>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium loss">
              ${analysis.worst_case_loss.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-slate-600">
              ({worstCasePercentage.toFixed(1)}%)
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between p-fib3 bg-accent-50 rounded-fib2">
          <div>
            <div className="text-sm font-medium text-slate-900">Best Case</div>
            <div className="text-xs text-slate-600">Goldilocks Scenario</div>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium profit">
              +${analysis.best_case_gain.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-slate-600">
              (+{bestCasePercentage.toFixed(1)}%)
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between p-fib3 bg-slate-50 rounded-fib2">
          <div>
            <div className="text-sm font-medium text-slate-900">Expected Value</div>
            <div className="text-xs text-slate-600">Probability Weighted</div>
          </div>
          <div className="text-right">
            <div className={`text-sm font-medium ${
              analysis.expected_value >= 0 ? 'profit' : 'loss'
            }`}>
              {analysis.expected_value >= 0 ? '+' : ''}${analysis.expected_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </div>
            <div className="text-xs text-slate-600">
              ({expectedPercentage >= 0 ? '+' : ''}{expectedPercentage.toFixed(1)}%)
            </div>
          </div>
        </div>
      </div>

      {/* Risk Metrics */}
      <div className="border-t border-slate-200 pt-fib5">
        <h4 className="text-sm font-medium text-slate-900 mb-fib3">Risk Metrics</h4>
        <div className="space-y-fib3">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-600">Value at Risk (95%)</span>
            <span className="text-sm font-medium loss">
              {(analysis.var_95 * 100).toFixed(1)}%
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-600">Conditional VaR (95%)</span>
            <span className="text-sm font-medium loss">
              {(analysis.cvar_95 * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
