'use client'

import { useState, useEffect } from 'react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ScatterChart, Scatter } from 'recharts'
import { apiClient } from '@/lib/api-client'

export default function OptimizerPage() {
  const [optimizerData, setOptimizerData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [activeView, setActiveView] = useState('proposals')

  useEffect(() => {
    fetchOptimizerData()
  }, [])

  const fetchOptimizerData = async () => {
    try {
      const response = await apiClient.executePattern({
        pattern: 'policy_rebalance',
        inputs: { portfolio_id: 'default' }
      })
      setOptimizerData(response.result)
    } catch (error) {
      console.error('Failed to fetch optimizer data:', error)
    } finally {
      setLoading(false)
    }
  }

  // Trade proposals data
  const tradeProposals = [
    { 
      id: 1, 
      action: 'BUY', 
      symbol: 'VTI', 
      shares: 150, 
      price: 218.50, 
      impact: '+0.8%',
      reason: 'Increase US equity exposure',
      confidence: 85
    },
    { 
      id: 2, 
      action: 'SELL', 
      symbol: 'AAPL', 
      shares: 50, 
      price: 178.25, 
      impact: '-0.3%',
      reason: 'Reduce concentration risk',
      confidence: 92
    },
    { 
      id: 3, 
      action: 'BUY', 
      symbol: 'GLD', 
      shares: 100, 
      price: 185.60, 
      impact: '+0.5%',
      reason: 'Add inflation hedge',
      confidence: 78
    },
    { 
      id: 4, 
      action: 'SELL', 
      symbol: 'TSLA', 
      shares: 25, 
      price: 245.80, 
      impact: '-0.2%',
      reason: 'Reduce volatility',
      confidence: 88
    },
    { 
      id: 5, 
      action: 'BUY', 
      symbol: 'BND', 
      shares: 200, 
      price: 72.40, 
      impact: '+1.2%',
      reason: 'Increase bond allocation',
      confidence: 95
    }
  ]

  // Impact analysis data
  const impactData = [
    { metric: 'Expected Return', current: 8.5, optimized: 9.8, change: '+1.3%' },
    { metric: 'Volatility', current: 15.2, optimized: 12.8, change: '-2.4%' },
    { metric: 'Sharpe Ratio', current: 0.85, optimized: 1.15, change: '+0.30' },
    { metric: 'Max Drawdown', current: -18.5, optimized: -14.2, change: '+4.3%' },
    { metric: 'Beta', current: 1.12, optimized: 0.95, change: '-0.17' }
  ]

  // Efficient frontier data
  const efficientFrontier = Array.from({ length: 20 }, (_, i) => ({
    risk: 5 + i * 0.8,
    return: 4 + i * 0.5 + Math.random() * 2,
    current: i === 12
  }))

  // Hedge recommendations
  const hedgeRecommendations = [
    { 
      type: 'PUT Options',
      underlying: 'SPY',
      strike: '420',
      expiry: '3 months',
      cost: '$8,500',
      protection: '15% downside',
      effectiveness: 85
    },
    { 
      type: 'VIX Calls',
      underlying: 'VIX',
      strike: '25',
      expiry: '2 months',
      cost: '$3,200',
      protection: 'Volatility spike',
      effectiveness: 72
    },
    { 
      type: 'Gold ETF',
      underlying: 'GLD',
      allocation: '5%',
      cost: '$62,500',
      protection: 'Inflation/Crisis',
      effectiveness: 68
    },
    { 
      type: 'Currency Hedge',
      underlying: 'EUR/USD',
      size: '$250K',
      cost: '$1,850',
      protection: 'FX exposure',
      effectiveness: 90
    }
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-blue-400">Loading optimizer...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header className="glass-card-dark">
        <h1 className="text-2xl font-bold text-blue-400">PORTFOLIO OPTIMIZER CONSOLE</h1>
        <p className="text-slate-400 mt-2">
          Trade proposals, impact analysis, and hedge recommendations
        </p>
      </header>

      {/* Optimization Summary */}
      <div className="grid grid-cols-5 gap-4">
        <div className="data-cell">
          <div className="data-label">Optimization Score</div>
          <div className="data-value text-blue-400">8.5/10</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Proposed Trades</div>
          <div className="data-value">5</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Expected Improvement</div>
          <div className="data-value profit">+15.3%</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Risk Reduction</div>
          <div className="data-value profit">-18.5%</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Total Cost</div>
          <div className="data-value">$2,450</div>
        </div>
      </div>

      {/* View Tabs */}
      <div className="flex gap-2 p-1 glass-card-dark w-fit rounded-lg">
        {['proposals', 'impact', 'hedging', 'frontier'].map((view) => (
          <button
            key={view}
            onClick={() => setActiveView(view)}
            className={`px-4 py-2 rounded-lg text-sm uppercase tracking-wider transition-all ${
              activeView === view
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            {view}
          </button>
        ))}
      </div>

      {/* Trade Proposals */}
      {activeView === 'proposals' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Recommended Trades</h2>
              <button className="btn-terminal">Execute All</button>
            </div>
            <table className="terminal-table">
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Symbol</th>
                  <th>Shares</th>
                  <th>Price</th>
                  <th>Value</th>
                  <th>Impact</th>
                  <th>Reason</th>
                  <th>Confidence</th>
                  <th>Execute</th>
                </tr>
              </thead>
              <tbody>
                {tradeProposals.map((trade) => (
                  <tr key={trade.id}>
                    <td>
                      <span className={`badge ${trade.action === 'BUY' ? 'badge-success' : 'badge-danger'}`}>
                        {trade.action}
                      </span>
                    </td>
                    <td className="font-bold text-blue-400">{trade.symbol}</td>
                    <td>{trade.shares}</td>
                    <td>${trade.price}</td>
                    <td>${(trade.shares * trade.price).toLocaleString()}</td>
                    <td className={trade.impact.startsWith('+') ? 'profit' : 'loss'}>
                      {trade.impact}
                    </td>
                    <td className="text-xs">{trade.reason}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-slate-700 rounded">
                          <div 
                            className="h-2 bg-blue-500 rounded" 
                            style={{ width: `${trade.confidence}%` }}
                          />
                        </div>
                        <span className="text-xs">{trade.confidence}%</span>
                      </div>
                    </td>
                    <td>
                      <button className="text-blue-400 hover:text-blue-300 text-xs uppercase">
                        Execute
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="data-cell">
              <div className="data-label">Total Buy Value</div>
              <div className="data-value profit">$95,820</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Total Sell Value</div>
              <div className="data-value loss">$38,450</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Net Cash Impact</div>
              <div className="data-value loss">-$57,370</div>
            </div>
          </div>
        </div>
      )}

      {/* Impact Analysis */}
      {activeView === 'impact' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Portfolio Impact Analysis</h2>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={impactData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" stroke="#64748b" />
                <YAxis type="category" dataKey="metric" stroke="#64748b" width={120} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Legend />
                <Bar dataKey="current" fill="#64748b" name="Current" />
                <Bar dataKey="optimized" fill="#3b82f6" name="Optimized" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="glass-card-dark">
              <h3 className="terminal-title mb-4">Risk Metrics</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Portfolio Beta</span>
                  <div className="flex items-center gap-4">
                    <span className="text-slate-500">1.12</span>
                    <span className="text-slate-300">→</span>
                    <span className="profit">0.95</span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Tracking Error</span>
                  <div className="flex items-center gap-4">
                    <span className="text-slate-500">4.8%</span>
                    <span className="text-slate-300">→</span>
                    <span className="profit">3.2%</span>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Information Ratio</span>
                  <div className="flex items-center gap-4">
                    <span className="text-slate-500">0.65</span>
                    <span className="text-slate-300">→</span>
                    <span className="profit">0.92</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="glass-card-dark">
              <h3 className="terminal-title mb-4">Sector Allocation Changes</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Technology</span>
                  <span className="loss">35% → 28%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Healthcare</span>
                  <span className="profit">12% → 18%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Financials</span>
                  <span className="neutral">15% → 15%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Energy</span>
                  <span className="profit">5% → 8%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Hedge Recommendations */}
      {activeView === 'hedging' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Recommended Hedges</h2>
              <span className="badge badge-warning">HIGH PRIORITY</span>
            </div>
            <div className="overflow-x-auto">
              <table className="terminal-table">
                <thead>
                  <tr>
                    <th>Hedge Type</th>
                    <th>Underlying</th>
                    <th>Details</th>
                    <th>Cost</th>
                    <th>Protection</th>
                    <th>Effectiveness</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {hedgeRecommendations.map((hedge) => (
                    <tr key={hedge.type}>
                      <td className="font-semibold">{hedge.type}</td>
                      <td className="text-blue-400">{hedge.underlying}</td>
                      <td className="text-xs">
                        {hedge.strike && `Strike: ${hedge.strike}, `}
                        {hedge.expiry && `Expiry: ${hedge.expiry}`}
                        {hedge.allocation && `Allocation: ${hedge.allocation}`}
                        {hedge.size && `Size: ${hedge.size}`}
                      </td>
                      <td>{hedge.cost}</td>
                      <td className="text-yellow-400">{hedge.protection}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-slate-700 rounded">
                            <div 
                              className={`h-2 rounded ${
                                hedge.effectiveness > 80 ? 'bg-green-500' : 
                                hedge.effectiveness > 60 ? 'bg-yellow-500' : 
                                'bg-red-500'
                              }`}
                              style={{ width: `${hedge.effectiveness}%` }}
                            />
                          </div>
                          <span className="text-xs">{hedge.effectiveness}%</span>
                        </div>
                      </td>
                      <td>
                        <button className="btn-terminal text-xs">Implement</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="data-cell">
              <div className="data-label">Total Hedge Cost</div>
              <div className="data-value">$76,050</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Downside Protection</div>
              <div className="data-value profit">85%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Break-even Move</div>
              <div className="data-value text-yellow-400">-3.2%</div>
            </div>
          </div>

          <div className="glass-card-dark">
            <h3 className="terminal-title mb-4">Deleveraging Hedges</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="p-4 border-l-4 border-green-500 bg-green-500/10">
                <h4 className="text-sm font-semibold text-green-400 mb-2">Money Printing Scenario</h4>
                <ul className="space-y-1 text-sm text-slate-400">
                  <li>• Increase TIPS allocation to 15%</li>
                  <li>• Add commodity exposure (5%)</li>
                  <li>• Reduce nominal bonds</li>
                </ul>
              </div>
              <div className="p-4 border-l-4 border-yellow-500 bg-yellow-500/10">
                <h4 className="text-sm font-semibold text-yellow-400 mb-2">Austerity Scenario</h4>
                <ul className="space-y-1 text-sm text-slate-400">
                  <li>• Increase cash to 20%</li>
                  <li>• Buy long-duration treasuries</li>
                  <li>• Reduce cyclical stocks</li>
                </ul>
              </div>
              <div className="p-4 border-l-4 border-red-500 bg-red-500/10">
                <h4 className="text-sm font-semibold text-red-400 mb-2">Default Scenario</h4>
                <ul className="space-y-1 text-sm text-slate-400">
                  <li>• Maximize gold allocation</li>
                  <li>• Hold foreign currency</li>
                  <li>• Short financial sector</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Efficient Frontier */}
      {activeView === 'frontier' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Efficient Frontier Analysis</h2>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="risk" stroke="#64748b" label={{ value: 'Risk (Volatility %)', position: 'insideBottom', offset: -5 }} />
                <YAxis dataKey="return" stroke="#64748b" label={{ value: 'Return (%)', angle: -90, position: 'insideLeft' }} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Scatter 
                  name="Portfolios" 
                  data={efficientFrontier} 
                  fill={(entry: any) => entry.current ? '#ef4444' : '#3b82f6'}
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="data-cell">
              <div className="data-label">Current Position</div>
              <div className="data-value text-yellow-400">SUB-OPTIMAL</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Optimal Risk</div>
              <div className="data-value">12.5%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Optimal Return</div>
              <div className="data-value profit">9.8%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Efficiency Gain</div>
              <div className="data-value profit">+22%</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}