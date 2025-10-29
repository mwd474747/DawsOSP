interface MetricCardProps {
  title: string
  value: string
  change: string
  changeType: 'profit' | 'loss' | 'neutral'
  subtitle: string
}

export function MetricCard({ title, value, change, changeType, subtitle }: MetricCardProps) {
  return (
    <div className="metric-card">
      <div className="flex items-start justify-between mb-fib3">
        <h3 className="text-sm font-medium text-slate-600">{title}</h3>
        <div className={`text-xs font-medium px-fib2 py-fib1 rounded-fib1 ${
          changeType === 'profit' ? 'profit bg-accent-50' :
          changeType === 'loss' ? 'loss bg-red-50' :
          'neutral bg-slate-50'
        }`}>
          {change}
        </div>
      </div>
      
      <div className="space-y-fib1">
        <div className="text-2xl font-bold text-slate-900">{value}</div>
        <div className="text-xs text-slate-500">{subtitle}</div>
      </div>
    </div>
  )
}
