interface MacroIndicator {
  name: string
  value: number
  change: number
  trend: 'up' | 'down' | 'flat'
  significance: 'high' | 'medium' | 'low'
}

interface MacroIndicatorsProps {
  indicators: MacroIndicator[]
}

export function MacroIndicators({ indicators }: MacroIndicatorsProps) {
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return '↗'
      case 'down': return '↘'
      case 'flat': return '→'
      default: return '→'
    }
  }

  const getTrendColor = (trend: string, change: number) => {
    if (trend === 'up') return change > 0 ? 'profit' : 'loss'
    if (trend === 'down') return change < 0 ? 'profit' : 'loss'
    return 'neutral'
  }

  const getSignificanceColor = (significance: string) => {
    switch (significance) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200'
      case 'medium': return 'bg-warning-100 text-warning-800 border-warning-200'
      case 'low': return 'bg-slate-100 text-slate-800 border-slate-200'
      default: return 'bg-slate-100 text-slate-800 border-slate-200'
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-200">
            <th className="text-left py-fib3 px-fib4 text-sm font-medium text-slate-600">Indicator</th>
            <th className="text-right py-fib3 px-fib4 text-sm font-medium text-slate-600">Value</th>
            <th className="text-right py-fib3 px-fib4 text-sm font-medium text-slate-600">Change</th>
            <th className="text-center py-fib3 px-fib4 text-sm font-medium text-slate-600">Trend</th>
            <th className="text-center py-fib3 px-fib4 text-sm font-medium text-slate-600">Significance</th>
          </tr>
        </thead>
        <tbody>
          {indicators.map((indicator, index) => (
            <tr key={index} className="border-b border-slate-100 hover:bg-slate-50">
              <td className="py-fib4 px-fib4">
                <div className="font-medium text-slate-900">{indicator.name}</div>
              </td>
              <td className="py-fib4 px-fib4 text-right">
                <div className="text-sm font-medium text-slate-900">
                  {indicator.value.toFixed(1)}
                  {indicator.name.includes('VIX') ? '' : '%'}
                </div>
              </td>
              <td className="py-fib4 px-fib4 text-right">
                <div className={`text-sm font-medium ${
                  getTrendColor(indicator.trend, indicator.change)
                }`}>
                  {indicator.change > 0 ? '+' : ''}{indicator.change.toFixed(1)}
                  {indicator.name.includes('VIX') ? '' : '%'}
                </div>
              </td>
              <td className="py-fib4 px-fib4 text-center">
                <div className={`text-lg ${
                  getTrendColor(indicator.trend, indicator.change)
                }`}>
                  {getTrendIcon(indicator.trend)}
                </div>
              </td>
              <td className="py-fib4 px-fib4 text-center">
                <div className={`rating-badge ${getSignificanceColor(indicator.significance)}`}>
                  {indicator.significance}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
