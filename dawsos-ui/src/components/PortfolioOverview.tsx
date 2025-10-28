'use client'

import { MetricCard } from './MetricCard'
import { PerformanceChart } from './PerformanceChart'
import { HoldingsTable } from './HoldingsTable'

export function PortfolioOverview() {
  const metrics = [
    {
      title: 'Total Value',
      value: '$1,247,832.45',
      change: '+2.34%',
      changeType: 'profit' as const,
      subtitle: 'Today',
    },
    {
      title: 'TWR (1Y)',
      value: '+18.47%',
      change: '+2.1%',
      changeType: 'profit' as const,
      subtitle: 'vs S&P 500',
    },
    {
      title: 'Sharpe Ratio',
      value: '1.84',
      change: '+0.12',
      changeType: 'profit' as const,
      subtitle: 'Risk-adjusted',
    },
    {
      title: 'Max Drawdown',
      value: '-8.23%',
      change: '-1.2%',
      changeType: 'loss' as const,
      subtitle: 'Peak to trough',
    },
  ]

  const holdings = [
    { symbol: 'AAPL', name: 'Apple Inc.', quantity: 150, value: 23450.00, weight: 18.8, change: '+1.2%' },
    { symbol: 'MSFT', name: 'Microsoft Corp.', quantity: 100, value: 42100.00, weight: 33.7, change: '+2.1%' },
    { symbol: 'GOOGL', name: 'Alphabet Inc.', quantity: 50, value: 8750.00, weight: 7.0, change: '+0.8%' },
    { symbol: 'AMZN', name: 'Amazon.com Inc.', quantity: 30, value: 4890.00, weight: 3.9, change: '-0.5%' },
    { symbol: 'TSLA', name: 'Tesla Inc.', quantity: 25, value: 6250.00, weight: 5.0, change: '+3.2%' },
  ]

  return (
    <div className="max-w-7xl mx-auto px-fib8 py-fib6">
      {/* Page Header */}
      <div className="mb-fib8">
        <h1 className="text-3xl font-bold text-slate-900 mb-fib2">Portfolio Overview</h1>
        <p className="text-slate-600">Real-time portfolio analytics and performance metrics</p>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-fib5 mb-fib8">
        {metrics.map((metric, index) => (
          <MetricCard key={index} {...metric} />
        ))}
      </div>

      {/* Charts and Tables Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-fib8 mb-fib8">
        {/* Performance Chart */}
        <div className="metric-card">
          <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Performance</h3>
          <PerformanceChart />
        </div>

        {/* Allocation Chart */}
        <div className="metric-card">
          <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Asset Allocation</h3>
          <div className="h-64 flex items-center justify-center bg-slate-50 rounded-fib3">
            <p className="text-slate-500">Allocation Chart (Recharts)</p>
          </div>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="metric-card">
        <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Holdings</h3>
        <HoldingsTable holdings={holdings} />
      </div>
    </div>
  )
}
