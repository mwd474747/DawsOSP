'use client'

import { useState, useEffect } from 'react'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { apiClient } from '@/lib/api-client'
import Link from 'next/link'

export default function DashboardPage() {
  const [portfolioData, setPortfolioData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const [portfolio, macro, alerts] = await Promise.all([
        fetch('/api/portfolio').then(res => res.json()),
        fetch('/api/macro').then(res => res.json()),
        fetch('/api/alerts').then(res => res.json()).catch(() => ({ active: 0 }))
      ])
      setPortfolioData({ portfolio, macro, alerts })
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  // Sample data for visualizations
  const performanceData = Array.from({ length: 30 }, (_, i) => ({
    day: `D${i + 1}`,
    portfolio: 100 + Math.random() * 10 + i * 0.3,
    benchmark: 100 + Math.random() * 8 + i * 0.25
  }))

  const allocationData = [
    { name: 'US Equities', value: 45, color: '#3b82f6' },
    { name: 'Int\'l Equities', value: 20, color: '#10b981' },
    { name: 'Fixed Income', value: 25, color: '#f59e0b' },
    { name: 'Alternatives', value: 7, color: '#8b5cf6' },
    { name: 'Cash', value: 3, color: '#64748b' }
  ]

  const riskMetrics = [
    { metric: 'Portfolio Beta', value: 0.85, status: 'normal' },
    { metric: 'Sharpe Ratio', value: 1.85, status: 'good' },
    { metric: 'Max Drawdown', value: -8.2, status: 'warning' },
    { metric: 'VaR (95%)', value: -125430, status: 'normal' },
    { metric: 'Sortino Ratio', value: 2.15, status: 'good' }
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-blue-400">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="glass-card-dark">
        <h1 className="text-2xl font-bold text-blue-400">PORTFOLIO DASHBOARD</h1>
        <p className="text-slate-400 mt-2">
          Real-time portfolio analytics and performance monitoring
        </p>
      </header>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-5 gap-4">
        <div className="data-cell">
          <div className="data-label">Total Value</div>
          <div className="data-value profit">$12.5M</div>
          <div className="text-xs profit mt-1">+12.5%</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Today's P&L</div>
          <div className="data-value profit">+$125.4K</div>
          <div className="text-xs profit mt-1">+1.02%</div>
        </div>
        <div className="data-cell">
          <div className="data-label">YTD Return</div>
          <div className="data-value profit">+18.5%</div>
          <div className="text-xs neutral mt-1">vs 15.2% benchmark</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Active Alerts</div>
          <div className="data-value text-yellow-400">8</div>
          <div className="text-xs text-yellow-400 mt-1">3 critical</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Risk Score</div>
          <div className="data-value text-blue-400">6.5/10</div>
          <div className="text-xs neutral mt-1">MODERATE</div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-2 gap-6">
        {/* Performance Chart */}
        <div className="glass-card-dark">
          <div className="terminal-header">
            <h2 className="terminal-title">30-Day Performance</h2>
            <span className="badge badge-success">OUTPERFORMING</span>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="day" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                  border: '1px solid rgba(255, 255, 255, 0.1)' 
                }} 
              />
              <Line type="monotone" dataKey="portfolio" stroke="#10b981" strokeWidth={2} dot={false} name="Portfolio" />
              <Line type="monotone" dataKey="benchmark" stroke="#64748b" strokeWidth={2} dot={false} strokeDasharray="5 5" name="Benchmark" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Asset Allocation */}
        <div className="glass-card-dark">
          <div className="terminal-header">
            <h2 className="terminal-title">Asset Allocation</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={allocationData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {allocationData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Risk Metrics Table */}
      <div className="glass-card-dark">
        <div className="terminal-header">
          <h2 className="terminal-title">Risk Metrics Overview</h2>
        </div>
        <table className="terminal-table">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Value</th>
              <th>Status</th>
              <th>30D Change</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {riskMetrics.map((item) => (
              <tr key={item.metric}>
                <td className="font-semibold">{item.metric}</td>
                <td className={item.value < 0 ? 'loss' : 'profit'}>
                  {typeof item.value === 'number' && item.value < 0 
                    ? item.value < -1000 
                      ? `$${(item.value / 1000).toFixed(1)}K`
                      : `${item.value.toFixed(1)}%`
                    : item.value}
                </td>
                <td>
                  <span className={`badge ${
                    item.status === 'good' ? 'badge-success' : 
                    item.status === 'warning' ? 'badge-warning' : 
                    'badge-info'
                  }`}>
                    {item.status.toUpperCase()}
                  </span>
                </td>
                <td className="neutral">--</td>
                <td>
                  <Link href={item.metric.includes('VaR') ? '/risk' : '/optimizer'}>
                    <button className="text-blue-400 hover:text-blue-300 text-xs uppercase">
                      Analyze
                    </button>
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-4 gap-4">
        <Link href="/macro-cycles">
          <button className="btn-terminal w-full">View Macro Cycles</button>
        </Link>
        <Link href="/scenarios">
          <button className="btn-terminal w-full">Run Scenarios</button>
        </Link>
        <Link href="/optimizer">
          <button className="btn-terminal w-full">Optimize Portfolio</button>
        </Link>
        <Link href="/reports">
          <button className="btn-terminal-success w-full">Generate Report</button>
        </Link>
      </div>

      {/* Market Regime Indicator */}
      <div className="glass-card-dark">
        <div className="terminal-header">
          <h2 className="terminal-title">Current Market Regime</h2>
        </div>
        <div className="grid grid-cols-4 gap-4">
          <div className="p-4 border-l-4 border-yellow-500">
            <div className="data-label">Economic Cycle</div>
            <div className="data-value text-yellow-400">LATE CYCLE</div>
          </div>
          <div className="p-4 border-l-4 border-blue-500">
            <div className="data-label">Credit Conditions</div>
            <div className="data-value text-blue-400">TIGHTENING</div>
          </div>
          <div className="p-4 border-l-4 border-green-500">
            <div className="data-label">Liquidity</div>
            <div className="data-value profit">ADEQUATE</div>
          </div>
          <div className="p-4 border-l-4 border-red-500">
            <div className="data-label">Volatility</div>
            <div className="data-value loss">ELEVATED</div>
          </div>
        </div>
      </div>
    </div>
  )
}