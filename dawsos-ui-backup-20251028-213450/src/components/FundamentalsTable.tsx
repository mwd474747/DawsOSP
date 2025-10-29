interface Fundamental {
  metric: string
  value: number
  benchmark: number
  status: 'above' | 'below' | 'equal'
}

interface FundamentalsTableProps {
  fundamentals: Fundamental[]
  symbol: string
}

export function FundamentalsTable({ fundamentals, symbol }: FundamentalsTableProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'above': return 'bg-accent-100 text-accent-800 border-accent-200'
      case 'below': return 'bg-red-100 text-red-800 border-red-200'
      case 'equal': return 'bg-slate-100 text-slate-800 border-slate-200'
      default: return 'bg-slate-100 text-slate-800 border-slate-200'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'above': return '↗'
      case 'below': return '↘'
      case 'equal': return '→'
      default: return '→'
    }
  }

  const formatValue = (metric: string, value: number) => {
    if (metric.includes('Ratio') || metric.includes('Growth')) {
      return value.toFixed(1)
    }
    return value.toFixed(2)
  }

  return (
    <div className="metric-card">
      <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Fundamental Metrics</h3>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-200">
              <th className="text-left py-fib3 px-fib4 text-sm font-medium text-slate-600">Metric</th>
              <th className="text-right py-fib3 px-fib4 text-sm font-medium text-slate-600">{symbol}</th>
              <th className="text-right py-fib3 px-fib4 text-sm font-medium text-slate-600">Benchmark</th>
              <th className="text-center py-fib3 px-fib4 text-sm font-medium text-slate-600">Status</th>
            </tr>
          </thead>
          <tbody>
            {fundamentals.map((fundamental, index) => (
              <tr key={index} className="border-b border-slate-100 hover:bg-slate-50">
                <td className="py-fib4 px-fib4">
                  <div className="font-medium text-slate-900">{fundamental.metric}</div>
                </td>
                <td className="py-fib4 px-fib4 text-right">
                  <div className="text-sm font-medium text-slate-900">
                    {formatValue(fundamental.metric, fundamental.value)}
                    {fundamental.metric.includes('Growth') || fundamental.metric.includes('Yield') ? '%' : ''}
                  </div>
                </td>
                <td className="py-fib4 px-fib4 text-right">
                  <div className="text-sm text-slate-600">
                    {formatValue(fundamental.metric, fundamental.benchmark)}
                    {fundamental.metric.includes('Growth') || fundamental.metric.includes('Yield') ? '%' : ''}
                  </div>
                </td>
                <td className="py-fib4 px-fib4 text-center">
                  <div className="flex items-center justify-center space-x-fib1">
                    <span className="text-lg">
                      {getStatusIcon(fundamental.status)}
                    </span>
                    <div className={`rating-badge ${getStatusColor(fundamental.status)}`}>
                      {fundamental.status}
                    </div>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-fib5 pt-fib4 border-t border-slate-200">
        <h5 className="text-xs font-medium text-slate-600 mb-fib2">Status Legend</h5>
        <div className="grid grid-cols-3 gap-fib2 text-xs">
          <div className="flex items-center space-x-fib1">
            <div className="w-fib1 h-fib1 bg-accent-500 rounded-full"></div>
            <span className="text-slate-600">Above Benchmark</span>
          </div>
          <div className="flex items-center space-x-fib1">
            <div className="w-fib1 h-fib1 bg-red-500 rounded-full"></div>
            <span className="text-slate-600">Below Benchmark</span>
          </div>
          <div className="flex items-center space-x-fib1">
            <div className="w-fib1 h-fib1 bg-slate-500 rounded-full"></div>
            <span className="text-slate-600">Equal to Benchmark</span>
          </div>
        </div>
      </div>
    </div>
  )
}
