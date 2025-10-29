interface RegimeCardProps {
  title: string
  regime: string
  confidence: number
  duration: string
  indicators: string[]
}

export function RegimeCard({ title, regime, confidence, duration, indicators }: RegimeCardProps) {
  const getRegimeColor = (regime: string) => {
    const regimeLower = regime.toLowerCase()
    if (regimeLower.includes('expansion') || regimeLower.includes('rising')) {
      return 'bg-accent-100 text-accent-800 border-accent-200'
    } else if (regimeLower.includes('late') || regimeLower.includes('peak')) {
      return 'bg-warning-100 text-warning-800 border-warning-200'
    } else if (regimeLower.includes('recession') || regimeLower.includes('declining')) {
      return 'bg-red-100 text-red-800 border-red-200'
    } else {
      return 'bg-primary-100 text-primary-800 border-primary-200'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-accent-600'
    if (confidence >= 0.6) return 'text-warning-600'
    return 'text-red-600'
  }

  return (
    <div className="metric-card">
      <div className="flex items-start justify-between mb-fib4">
        <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
        <div className={`rating-badge ${getRegimeColor(regime)}`}>
          {regime.replace('_', ' ')}
        </div>
      </div>

      <div className="space-y-fib4">
        {/* Confidence Score */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-600">Confidence</span>
          <span className={`text-sm font-medium ${getConfidenceColor(confidence)}`}>
            {(confidence * 100).toFixed(0)}%
          </span>
        </div>

        {/* Duration */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-600">Duration</span>
          <span className="text-sm font-medium text-slate-900">{duration}</span>
        </div>

        {/* Indicators */}
        <div>
          <span className="text-sm text-slate-600 mb-fib2 block">Key Indicators</span>
          <div className="space-y-fib1">
            {indicators.map((indicator, index) => (
              <div key={index} className="flex items-center space-x-fib2">
                <div className="w-fib1 h-fib1 bg-primary-500 rounded-full"></div>
                <span className="text-xs text-slate-600">{indicator}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
