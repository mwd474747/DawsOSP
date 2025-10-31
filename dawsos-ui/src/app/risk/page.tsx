'use client'

import { useState, useEffect } from 'react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, HeatMapGrid } from 'recharts'
import { apiClient } from '@/lib/api-client'

export default function RiskAnalyticsPage() {
  const [riskData, setRiskData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [activeView, setActiveView] = useState('overview')

  useEffect(() => {
    fetchRiskData()
  }, [])

  const fetchRiskData = async () => {
    try {
      const [metricsResponse, attributionResponse] = await Promise.all([
        fetch('/api/metrics').then(res => res.json()),
        fetch('/api/attribution').then(res => res.json())
      ])
      setRiskData({ metrics: metricsResponse, attribution: attributionResponse })
    } catch (error) {
      console.error('Failed to fetch risk data:', error)
    } finally {
      setLoading(false)
    }
  }

  // Sample data for visualizations
  const varData = Array.from({ length: 30 }, (_, i) => ({
    day: `Day ${i + 1}`,
    var95: -2.5 - Math.random() * 1.5,
    var99: -3.5 - Math.random() * 2,
    actual: i % 7 === 0 ? -4 - Math.random() * 2 : -1 - Math.random() * 1.5
  }))

  const factorExposures = [
    { factor: 'Market Beta', exposure: 0.85, risk: 0.65 },
    { factor: 'Size', exposure: -0.25, risk: 0.15 },
    { factor: 'Value', exposure: 0.45, risk: 0.35 },
    { factor: 'Momentum', exposure: 0.15, risk: 0.12 },
    { factor: 'Quality', exposure: 0.55, risk: 0.42 },
    { factor: 'Low Vol', exposure: -0.35, risk: 0.28 }
  ]

  const concentrationData = [
    { asset: 'AAPL', weight: 15.2, risk: 18.5 },
    { asset: 'MSFT', weight: 12.8, risk: 14.2 },
    { asset: 'GOOGL', weight: 10.5, risk: 12.8 },
    { asset: 'AMZN', weight: 8.2, risk: 11.5 },
    { asset: 'NVDA', weight: 6.5, risk: 9.8 },
    { asset: 'Others', weight: 46.8, risk: 33.2 }
  ]

  const drawdownData = Array.from({ length: 252 }, (_, i) => {
    const baseValue = 100
    const trend = Math.sin(i * 0.05) * 10
    const noise = Math.random() * 5
    const value = baseValue + trend - noise
    const drawdown = Math.min(0, value - baseValue)
    return {
      day: i,
      value: value,
      drawdown: drawdown
    }
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-blue-400">Loading risk analytics...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header className="glass-card-dark">
        <h1 className="text-2xl font-bold text-blue-400">RISK ANALYTICS DASHBOARD</h1>
        <p className="text-slate-400 mt-2">
          Comprehensive risk metrics, factor exposures, and concentration analysis
        </p>
      </header>

      {/* Risk Metrics Overview */}
      <div className="grid grid-cols-5 gap-4">
        <div className="data-cell">
          <div className="data-label">VaR (95%)</div>
          <div className="data-value loss">-$125,430</div>
          <div className="text-xs text-slate-500 mt-1">1-Day</div>
        </div>
        <div className="data-cell">
          <div className="data-label">VaR (99%)</div>
          <div className="data-value loss">-$198,250</div>
          <div className="text-xs text-slate-500 mt-1">1-Day</div>
        </div>
        <div className="data-cell">
          <div className="data-label">CVaR</div>
          <div className="data-value loss">-$245,820</div>
          <div className="text-xs text-slate-500 mt-1">Tail Risk</div>
        </div>
        <div className="data-cell">
          <div className="data-label">DaR (95%)</div>
          <div className="data-value loss">-8.2%</div>
          <div className="text-xs text-slate-500 mt-1">Max DD</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Sharpe Ratio</div>
          <div className="data-value profit">1.85</div>
          <div className="text-xs text-slate-500 mt-1">Risk-Adjusted</div>
        </div>
      </div>

      {/* View Tabs */}
      <div className="flex gap-2 p-1 glass-card-dark w-fit rounded-lg">
        {['overview', 'var-analysis', 'factors', 'concentration', 'drawdown'].map((view) => (
          <button
            key={view}
            onClick={() => setActiveView(view)}
            className={`px-4 py-2 rounded-lg text-sm uppercase tracking-wider transition-all ${
              activeView === view
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            {view.replace('-', ' ')}
          </button>
        ))}
      </div>

      {/* Risk Overview */}
      {activeView === 'overview' && (
        <div className="grid grid-cols-2 gap-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Risk Distribution</h2>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={concentrationData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="asset" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Legend />
                <Bar dataKey="weight" fill="#3b82f6" name="Weight %" />
                <Bar dataKey="risk" fill="#ef4444" name="Risk Contribution %" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Factor Exposures</h2>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={factorExposures}>
                <PolarGrid stroke="#1e293b" />
                <PolarAngleAxis dataKey="factor" stroke="#64748b" />
                <PolarRadiusAxis stroke="#64748b" />
                <Radar name="Exposure" dataKey="exposure" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
                <Radar name="Risk" dataKey="risk" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* VaR Analysis */}
      {activeView === 'var-analysis' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Value at Risk (VaR) Analysis</h2>
              <span className="badge badge-warning">2 BREACHES</span>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={varData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="day" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Legend />
                <Line type="monotone" dataKey="var95" stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 5" dot={false} name="VaR 95%" />
                <Line type="monotone" dataKey="var99" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 5" dot={false} name="VaR 99%" />
                <Line type="monotone" dataKey="actual" stroke="#3b82f6" strokeWidth={2} dot={false} name="Actual P&L" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="data-cell">
              <div className="data-label">Breaches (95%)</div>
              <div className="data-value text-yellow-400">2 / 30</div>
              <div className="text-xs text-slate-500 mt-1">Expected: 1.5</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Breaches (99%)</div>
              <div className="data-value profit">0 / 30</div>
              <div className="text-xs text-slate-500 mt-1">Expected: 0.3</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Kupiec Test</div>
              <div className="data-value profit">PASS</div>
              <div className="text-xs text-slate-500 mt-1">p-value: 0.72</div>
            </div>
          </div>
        </div>
      )}

      {/* Factor Analysis */}
      {activeView === 'factors' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Factor Exposure Heatmap</h2>
            </div>
            <div className="p-6">
              <table className="terminal-table">
                <thead>
                  <tr>
                    <th>Factor</th>
                    <th>Exposure</th>
                    <th>Risk Contribution</th>
                    <th>P&L Attribution</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {factorExposures.map((factor) => (
                    <tr key={factor.factor}>
                      <td className="font-semibold">{factor.factor}</td>
                      <td className={factor.exposure > 0 ? 'profit' : 'loss'}>
                        {factor.exposure > 0 ? '+' : ''}{(factor.exposure * 100).toFixed(1)}%
                      </td>
                      <td>{(factor.risk * 100).toFixed(1)}%</td>
                      <td className={factor.exposure > 0 ? 'profit' : 'loss'}>
                        ${Math.abs(factor.exposure * 10000).toFixed(0)}
                      </td>
                      <td>
                        <span className={`badge ${factor.risk > 0.4 ? 'badge-warning' : 'badge-success'}`}>
                          {factor.risk > 0.4 ? 'HIGH' : 'NORMAL'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="data-cell">
              <div className="data-label">Total Factor Risk</div>
              <div className="data-value">68.5%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Idiosyncratic Risk</div>
              <div className="data-value">31.5%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Active Risk</div>
              <div className="data-value text-yellow-400">12.3%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Tracking Error</div>
              <div className="data-value">4.8%</div>
            </div>
          </div>
        </div>
      )}

      {/* Concentration Analysis */}
      {activeView === 'concentration' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Portfolio Concentration Analysis</h2>
              <span className="badge badge-warning">HIGH CONCENTRATION</span>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={concentrationData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" stroke="#64748b" />
                <YAxis type="category" dataKey="asset" stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Legend />
                <Bar dataKey="weight" fill="#3b82f6" name="Portfolio Weight %" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="data-cell">
              <div className="data-label">Top 5 Holdings</div>
              <div className="data-value text-yellow-400">53.2%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Herfindahl Index</div>
              <div className="data-value">0.082</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Effective N</div>
              <div className="data-value">12.2</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Max Position</div>
              <div className="data-value loss">15.2%</div>
            </div>
          </div>
        </div>
      )}

      {/* Drawdown Analysis */}
      {activeView === 'drawdown' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Maximum Drawdown Analysis</h2>
              <span className="badge badge-info">-8.2% CURRENT</span>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={drawdownData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="day" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Legend />
                <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} name="Portfolio Value" />
                <Line type="monotone" dataKey="drawdown" stroke="#ef4444" strokeWidth={2} dot={false} name="Drawdown %" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="data-cell">
              <div className="data-label">Current Drawdown</div>
              <div className="data-value loss">-8.2%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Max Drawdown</div>
              <div className="data-value loss">-15.8%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Recovery Days</div>
              <div className="data-value">45</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Underwater Days</div>
              <div className="data-value text-yellow-400">120</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}