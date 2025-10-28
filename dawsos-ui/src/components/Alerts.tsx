'use client'

import { AlertForm } from './AlertForm'
import { AlertTimeline } from './AlertTimeline'
import { useAlerts } from '@/lib/queries'

interface AlertsProps {
  portfolioId?: string;
}

export function Alerts({ portfolioId = 'main-portfolio' }: AlertsProps) {
  // Fetch alerts data using React Query
  const { 
    data: alertsData, 
    isLoading, 
    error, 
    refetch 
  } = useAlerts(portfolioId);

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Alerts</h1>
          <p className="text-slate-600 dark:text-slate-400">Loading alerts data...</p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-3/4 mb-4"></div>
              <div className="h-8 bg-slate-200 rounded w-1/2 mb-2"></div>
              <div className="h-3 bg-slate-200 rounded w-1/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Alerts</h1>
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <p className="text-red-800 dark:text-red-200 font-medium">Error loading alerts data</p>
            <p className="text-red-600 dark:text-red-300 text-sm mt-2">
              {error instanceof Error ? error.message : 'Unknown error occurred'}
            </p>
            <button 
              onClick={() => refetch()}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Extract data from API response or use defaults
  const alerts: Array<{
    id: string;
    condition: string;
    threshold: number;
    current_value: number;
    status: 'active' | 'triggered' | 'disabled';
    created_at: string;
    last_triggered: string | null;
  }> = alertsData?.result?.alerts || [
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
