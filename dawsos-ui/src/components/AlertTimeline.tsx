interface Alert {
  id: string
  condition: string
  threshold: number
  current_value: number
  status: 'active' | 'triggered' | 'disabled'
  created_at: string
  last_triggered: string | null
}

interface AlertTimelineProps {
  alerts: Alert[]
}

export function AlertTimeline({ alerts }: AlertTimelineProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-accent-500'
      case 'triggered': return 'bg-red-500'
      case 'disabled': return 'bg-slate-400'
      default: return 'bg-slate-400'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active': return 'Active'
      case 'triggered': return 'Triggered'
      case 'disabled': return 'Disabled'
      default: return 'Unknown'
    }
  }

  return (
    <div className="metric-card">
      <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Alert Timeline</h3>
      
      <div className="space-y-fib4">
        {alerts.map((alert, index) => (
          <div key={alert.id} className="flex items-start space-x-fib4">
            <div className="flex flex-col items-center">
              <div className={`w-fib3 h-fib3 ${getStatusColor(alert.status)} rounded-full`}></div>
              {index < alerts.length - 1 && (
                <div className="w-px h-fib8 bg-slate-200 mt-fib2"></div>
              )}
            </div>
            
            <div className="flex-1 pb-fib4">
              <div className="flex items-center justify-between mb-fib1">
                <h4 className="text-sm font-medium text-slate-900">{alert.condition}</h4>
                <span className={`text-xs px-fib2 py-fib1 rounded-fib1 ${
                  alert.status === 'active' ? 'bg-accent-100 text-accent-800' :
                  alert.status === 'triggered' ? 'bg-red-100 text-red-800' :
                  'bg-slate-100 text-slate-800'
                }`}>
                  {getStatusText(alert.status)}
                </span>
              </div>
              
              <div className="text-xs text-slate-600 mb-fib2">
                Threshold: {alert.threshold} | Current: {alert.current_value}
              </div>
              
              <div className="text-xs text-slate-500">
                Created: {new Date(alert.created_at).toLocaleString()}
                {alert.last_triggered && (
                  <span className="ml-fib3">
                    | Triggered: {new Date(alert.last_triggered).toLocaleString()}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
