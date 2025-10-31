'use client'

import { useState, useEffect } from 'react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, AreaChart, Area } from 'recharts'
import { apiClient } from '@/lib/api-client'

export default function AttributionPage() {
  const [attributionData, setAttributionData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [activeView, setActiveView] = useState('currency')
  const [dateRange, setDateRange] = useState('3M')

  useEffect(() => {
    fetchAttributionData()
  }, [dateRange])

  const fetchAttributionData = async () => {
    try {
      const response = await apiClient.getAttribution('1')
      setAttributionData(response)
    } catch (error) {
      console.error('Failed to fetch attribution data:', error)
    } finally {
      setLoading(false)
    }
  }

  // Currency attribution data
  const currencyAttr = [
    { period: 'Jan', local: 2.5, fx: -0.8, cross: 0.2, total: 1.9 },
    { period: 'Feb', local: 1.8, fx: 0.5, cross: 0.1, total: 2.4 },
    { period: 'Mar', local: -1.2, fx: 0.3, cross: -0.1, total: -1.0 },
    { period: 'Apr', local: 3.2, fx: -0.2, cross: 0.3, total: 3.3 },
    { period: 'May', local: 2.1, fx: 0.6, cross: 0.2, total: 2.9 },
    { period: 'Jun', local: 1.5, fx: -0.4, cross: 0.0, total: 1.1 }
  ]

  // Factor attribution
  const factorAttr = [
    { factor: 'Selection', contribution: 2.85, percentage: 35 },
    { factor: 'Allocation', contribution: 1.65, percentage: 20 },
    { factor: 'Interaction', contribution: 0.45, percentage: 6 },
    { factor: 'Currency', contribution: -0.85, percentage: -10 },
    { factor: 'Trading', contribution: 0.35, percentage: 4 },
    { factor: 'Residual', contribution: 0.15, percentage: 2 }
  ]

  // Sector attribution
  const sectorAttr = [
    { sector: 'Technology', weight: 35.2, return: 12.5, contribution: 4.38, active: 5.2 },
    { sector: 'Healthcare', weight: 18.5, return: 8.2, contribution: 1.52, active: -2.5 },
    { sector: 'Financials', weight: 15.2, return: 6.8, contribution: 1.03, active: 0.2 },
    { sector: 'Consumer', weight: 12.8, return: 5.2, contribution: 0.67, active: -1.2 },
    { sector: 'Energy', weight: 8.5, return: -2.5, contribution: -0.21, active: 1.5 },
    { sector: 'Other', weight: 9.8, return: 3.2, contribution: 0.31, active: -3.2 }
  ]

  // Performance comparison
  const performanceComparison = Array.from({ length: 12 }, (_, i) => ({
    month: `M${i + 1}`,
    portfolio: 100 * (1 + 0.08) ** (i / 12) + Math.random() * 5,
    benchmark: 100 * (1 + 0.06) ** (i / 12) + Math.random() * 3,
    excess: (Math.random() - 0.3) * 2
  }))

  // TWR vs MWR data
  const twrMwr = [
    { period: 'Q1 2024', twr: 3.2, mwr: 2.8, flows: -500000 },
    { period: 'Q2 2024', twr: 4.5, mwr: 4.8, flows: 1200000 },
    { period: 'Q3 2024', twr: -1.2, mwr: -1.5, flows: -200000 },
    { period: 'Q4 2024', twr: 5.8, mwr: 5.2, flows: 800000 }
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-blue-400">Loading attribution analysis...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header className="glass-card-dark">
        <h1 className="text-2xl font-bold text-blue-400">PERFORMANCE ATTRIBUTION</h1>
        <p className="text-slate-400 mt-2">
          Detailed breakdown of portfolio performance drivers and return attribution
        </p>
      </header>

      {/* Date Range Selector */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2 p-1 glass-card-dark w-fit rounded-lg">
          {['1M', '3M', '6M', 'YTD', '1Y', '3Y'].map((range) => (
            <button
              key={range}
              onClick={() => setDateRange(range)}
              className={`px-4 py-2 rounded-lg text-sm uppercase tracking-wider transition-all ${
                dateRange === range
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
        <div className="text-sm text-slate-400">
          Period: {dateRange === 'YTD' ? 'Jan 1 - Oct 31, 2025' : `Last ${dateRange}`}
        </div>
      </div>

      {/* Attribution Summary */}
      <div className="grid grid-cols-5 gap-4">
        <div className="data-cell">
          <div className="data-label">Total Return</div>
          <div className="data-value profit">+8.65%</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Benchmark Return</div>
          <div className="data-value">+6.20%</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Active Return</div>
          <div className="data-value profit">+2.45%</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Tracking Error</div>
          <div className="data-value text-yellow-400">3.8%</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Information Ratio</div>
          <div className="data-value profit">0.64</div>
        </div>
      </div>

      {/* View Tabs */}
      <div className="flex gap-2 p-1 glass-card-dark w-fit rounded-lg">
        {['currency', 'factor', 'sector', 'benchmark', 'twr-mwr'].map((view) => (
          <button
            key={view}
            onClick={() => setActiveView(view)}
            className={`px-4 py-2 rounded-lg text-sm uppercase tracking-wider transition-all ${
              activeView === view
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            {view.replace('-', ' / ')}
          </button>
        ))}
      </div>

      {/* Currency Attribution */}
      {activeView === 'currency' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Currency Attribution Analysis</h2>
              <span className="badge badge-warning">FX IMPACT: -0.85%</span>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={currencyAttr}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="period" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Legend />
                <Bar dataKey="local" stackId="a" fill="#3b82f6" name="Local Return" />
                <Bar dataKey="fx" stackId="a" fill="#f59e0b" name="FX Impact" />
                <Bar dataKey="cross" stackId="a" fill="#8b5cf6" name="Cross Effects" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="data-cell">
              <div className="data-label">Local Returns</div>
              <div className="data-value profit">+9.50%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">FX Impact</div>
              <div className="data-value loss">-0.85%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Cross Effects</div>
              <div className="data-value neutral">+0.20%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Total Return</div>
              <div className="data-value profit">+8.85%</div>
            </div>
          </div>

          <div className="glass-card-dark">
            <h3 className="terminal-title mb-4">Currency Exposure Breakdown</h3>
            <table className="terminal-table">
              <thead>
                <tr>
                  <th>Currency</th>
                  <th>Exposure</th>
                  <th>Spot Return</th>
                  <th>Local Return</th>
                  <th>Total Contribution</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="font-bold">USD</td>
                  <td>65.0%</td>
                  <td className="neutral">0.0%</td>
                  <td className="profit">+8.2%</td>
                  <td className="profit">+5.33%</td>
                </tr>
                <tr>
                  <td className="font-bold">EUR</td>
                  <td>15.0%</td>
                  <td className="loss">-2.5%</td>
                  <td className="profit">+6.8%</td>
                  <td className="profit">+0.64%</td>
                </tr>
                <tr>
                  <td className="font-bold">GBP</td>
                  <td>10.0%</td>
                  <td className="loss">-1.8%</td>
                  <td className="profit">+5.2%</td>
                  <td className="profit">+0.34%</td>
                </tr>
                <tr>
                  <td className="font-bold">JPY</td>
                  <td>5.0%</td>
                  <td className="loss">-3.2%</td>
                  <td className="profit">+4.5%</td>
                  <td className="neutral">+0.07%</td>
                </tr>
                <tr>
                  <td className="font-bold">Other</td>
                  <td>5.0%</td>
                  <td className="profit">+1.2%</td>
                  <td className="profit">+7.5%</td>
                  <td className="profit">+0.44%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Factor Attribution */}
      {activeView === 'factor' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Factor Attribution Analysis</h2>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={factorAttr} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" stroke="#64748b" />
                <YAxis type="category" dataKey="factor" stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Bar 
                  dataKey="contribution" 
                  fill={(entry: any) => entry.contribution > 0 ? '#10b981' : '#ef4444'}
                  name="Contribution (%)"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="data-cell">
              <div className="data-label">Selection Effect</div>
              <div className="data-value profit">+2.85%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Allocation Effect</div>
              <div className="data-value profit">+1.65%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Total Active</div>
              <div className="data-value profit">+4.50%</div>
            </div>
          </div>
        </div>
      )}

      {/* Sector Attribution */}
      {activeView === 'sector' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Sector Attribution Breakdown</h2>
            </div>
            <table className="terminal-table">
              <thead>
                <tr>
                  <th>Sector</th>
                  <th>Portfolio Weight</th>
                  <th>Benchmark Weight</th>
                  <th>Active Weight</th>
                  <th>Return</th>
                  <th>Contribution</th>
                  <th>Active Contribution</th>
                </tr>
              </thead>
              <tbody>
                {sectorAttr.map((sector) => (
                  <tr key={sector.sector}>
                    <td className="font-bold">{sector.sector}</td>
                    <td>{sector.weight}%</td>
                    <td>{(sector.weight - sector.active).toFixed(1)}%</td>
                    <td className={sector.active > 0 ? 'profit' : 'loss'}>
                      {sector.active > 0 ? '+' : ''}{sector.active.toFixed(1)}%
                    </td>
                    <td className={sector.return > 0 ? 'profit' : 'loss'}>
                      {sector.return > 0 ? '+' : ''}{sector.return}%
                    </td>
                    <td className={sector.contribution > 0 ? 'profit' : 'loss'}>
                      {sector.contribution > 0 ? '+' : ''}{sector.contribution.toFixed(2)}%
                    </td>
                    <td className={sector.active * sector.return / 100 > 0 ? 'profit' : 'loss'}>
                      {((sector.active * sector.return) / 100).toFixed(3)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="glass-card-dark">
              <h3 className="terminal-title mb-4">Top Contributors</h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Technology Overweight</span>
                  <span className="profit">+0.65%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Healthcare Selection</span>
                  <span className="profit">+0.42%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Energy Underweight</span>
                  <span className="profit">+0.28%</span>
                </div>
              </div>
            </div>

            <div className="glass-card-dark">
              <h3 className="terminal-title mb-4">Top Detractors</h3>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Consumer Underweight</span>
                  <span className="loss">-0.22%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Financials Selection</span>
                  <span className="loss">-0.18%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Cash Drag</span>
                  <span className="loss">-0.15%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Benchmark Comparison */}
      {activeView === 'benchmark' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Portfolio vs Benchmark Performance</h2>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={performanceComparison}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="month" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Legend />
                <Line type="monotone" dataKey="portfolio" stroke="#10b981" strokeWidth={2} dot={false} name="Portfolio" />
                <Line type="monotone" dataKey="benchmark" stroke="#64748b" strokeWidth={2} dot={false} strokeDasharray="5 5" name="Benchmark" />
                <Line type="monotone" dataKey="excess" stroke="#3b82f6" strokeWidth={2} dot={false} name="Excess Return" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="data-cell">
              <div className="data-label">Active Return</div>
              <div className="data-value profit">+2.45%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Tracking Error</div>
              <div className="data-value">3.8%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Information Ratio</div>
              <div className="data-value profit">0.64</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Hit Rate</div>
              <div className="data-value profit">62%</div>
            </div>
          </div>
        </div>
      )}

      {/* TWR vs MWR */}
      {activeView === 'twr-mwr' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Time-Weighted vs Money-Weighted Returns</h2>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={twrMwr}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="period" stroke="#64748b" />
                <YAxis yAxisId="left" stroke="#64748b" />
                <YAxis yAxisId="right" orientation="right" stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="twr" stroke="#10b981" strokeWidth={2} name="TWR (%)" />
                <Line yAxisId="left" type="monotone" dataKey="mwr" stroke="#3b82f6" strokeWidth={2} name="MWR (%)" />
                <Bar yAxisId="right" dataKey="flows" fill="#f59e0b" opacity={0.3} name="Cash Flows ($)" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="glass-card-dark">
            <table className="terminal-table">
              <thead>
                <tr>
                  <th>Period</th>
                  <th>TWR</th>
                  <th>MWR</th>
                  <th>Difference</th>
                  <th>Cash Flows</th>
                  <th>Timing Impact</th>
                </tr>
              </thead>
              <tbody>
                {twrMwr.map((period) => (
                  <tr key={period.period}>
                    <td className="font-bold">{period.period}</td>
                    <td className={period.twr > 0 ? 'profit' : 'loss'}>
                      {period.twr > 0 ? '+' : ''}{period.twr}%
                    </td>
                    <td className={period.mwr > 0 ? 'profit' : 'loss'}>
                      {period.mwr > 0 ? '+' : ''}{period.mwr}%
                    </td>
                    <td className={period.mwr - period.twr > 0 ? 'profit' : 'loss'}>
                      {(period.mwr - period.twr).toFixed(1)}%
                    </td>
                    <td className={period.flows > 0 ? 'profit' : 'loss'}>
                      ${(Math.abs(period.flows) / 1000).toFixed(0)}K
                    </td>
                    <td>
                      <span className={`badge ${
                        Math.abs(period.mwr - period.twr) > 0.5 
                          ? period.mwr > period.twr ? 'badge-success' : 'badge-danger'
                          : 'badge-info'
                      }`}>
                        {period.mwr > period.twr ? 'GOOD' : period.mwr < period.twr ? 'POOR' : 'NEUTRAL'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="data-cell">
              <div className="data-label">YTD TWR</div>
              <div className="data-value profit">+12.3%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">YTD MWR</div>
              <div className="data-value profit">+11.3%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Timing Effect</div>
              <div className="data-value loss">-1.0%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Net Flows YTD</div>
              <div className="data-value profit">+$1.3M</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}