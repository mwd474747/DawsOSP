'use client'

import { AlertForm } from './AlertForm'
import { AlertTimeline } from './AlertTimeline'

export function Alerts() {
  const alerts = [
    {
      id: '1',
      condition: 'Portfolio Value Drop',
      threshold: -5.0,
      current_value: -2.3,
      status: 'active' as const,
      created_at: '2025-10-25T10:30:00Z',
      last_triggered: null,
    },
    {
      id: '2',
      condition: 'DaR Breach',
      threshold: 0.15,
      current_value: 0.12,
      status: 'active' as const,
      created_at: '2025-10-24T14:15:00Z',
      last_triggered: null,
    },
    {
      id: '3',
      condition: 'Volatility Spike',
      threshold: 25.0,
      current_value: 18.5,
      status: 'triggered' as const,
      created_at: '2025-10-23T09:45:00Z',
      last_triggered: '2025-10-27T11:20:00Z',
    },
  ]

  return (
    <div className="max-w-7xl mx-auto px-fib8 py-fib6">
      {/* Page Header */}
      <div className="mb-fib8">
        <h1 className="text-3xl font-bold text-slate-900 mb-fib2">Alerts</h1>
        <p className="text-slate-600">Create and manage portfolio alerts and notifications</p>
      </div>

      {/* Alert Form and Timeline Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-fib8 mb-fib8">
        <AlertForm />
        <AlertTimeline alerts={alerts} />
      </div>

      {/* Active Alerts */}
      <div className="metric-card">
        <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Active Alerts</h3>
        <div className="space-y-fib4">
          {alerts.map((alert) => (
            <div key={alert.id} className="flex items-center justify-between p-fib4 bg-slate-50 rounded-fib3">
              <div className="flex items-center space-x-fib4">
                <div className={`w-fib2 h-fib2 rounded-full ${
                  alert.status === 'active' ? 'bg-accent-500' : 
                  alert.status === 'triggered' ? 'bg-red-500' : 
                  'bg-slate-400'
                }`}></div>
                <div>
                  <div className="text-sm font-medium text-slate-900">{alert.condition}</div>
                  <div className="text-xs text-slate-600">
                    Created: {new Date(alert.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium text-slate-900">
                  {alert.current_value} / {alert.threshold}
                </div>
                <div className={`text-xs font-medium ${
                  alert.status === 'active' ? 'text-accent-600' : 
                  alert.status === 'triggered' ? 'text-red-600' : 
                  'text-slate-600'
                }`}>
                  {alert.status.toUpperCase()}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
