'use client'

import { useState, useEffect } from 'react'
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { apiClient } from '@/lib/api-client'

export default function RatingsPage() {
  const [ratingsData, setRatingsData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [selectedStock, setSelectedStock] = useState('AAPL')
  const [activeView, setActiveView] = useState('buffett')

  useEffect(() => {
    fetchRatingsData()
  }, [selectedStock])

  const fetchRatingsData = async () => {
    try {
      const response = await apiClient.executePattern({
        pattern: 'buffett_checklist',
        inputs: { symbol: selectedStock }
      })
      setRatingsData(response.result)
    } catch (error) {
      console.error('Failed to fetch ratings data:', error)
    } finally {
      setLoading(false)
    }
  }

  // Buffett Checklist data
  const buffettCriteria = [
    { criteria: 'Simple Business', score: 85, weight: 'High' },
    { criteria: 'Consistent Operating History', score: 92, weight: 'High' },
    { criteria: 'Favorable Long-term Prospects', score: 78, weight: 'High' },
    { criteria: 'Rational Management', score: 88, weight: 'Medium' },
    { criteria: 'Attractive Price', score: 65, weight: 'High' },
    { criteria: 'High ROE', score: 95, weight: 'High' },
    { criteria: 'Low Debt', score: 82, weight: 'Medium' },
    { criteria: 'High Profit Margins', score: 90, weight: 'High' },
    { criteria: 'Moat/Competitive Advantage', score: 94, weight: 'High' },
    { criteria: 'Owner Earnings Growth', score: 87, weight: 'Medium' }
  ]

  // Dividend Safety scores
  const dividendSafety = {
    overall: 82,
    factors: [
      { factor: 'Payout Ratio', score: 88 },
      { factor: 'Free Cash Flow', score: 85 },
      { factor: 'Debt/Equity', score: 75 },
      { factor: 'Earnings Stability', score: 90 },
      { factor: 'Revenue Growth', score: 78 },
      { factor: 'Dividend History', score: 95 }
    ]
  }

  // Moat Strength analysis
  const moatStrength = [
    { aspect: 'Brand Value', current: 95, industry: 65 },
    { aspect: 'Switching Costs', current: 88, industry: 45 },
    { aspect: 'Network Effects', current: 78, industry: 55 },
    { aspect: 'Cost Advantage', current: 72, industry: 60 },
    { aspect: 'Intangible Assets', current: 92, industry: 50 },
    { aspect: 'Efficient Scale', current: 85, industry: 70 }
  ]

  // Resilience Rating
  const resilienceFactors = [
    { factor: 'Financial Strength', score: 88, status: 'Strong' },
    { factor: 'Market Position', score: 92, status: 'Dominant' },
    { factor: 'Adaptability', score: 78, status: 'Good' },
    { factor: 'Management Quality', score: 85, status: 'Excellent' },
    { factor: 'Diversification', score: 72, status: 'Moderate' },
    { factor: 'Innovation', score: 95, status: 'Leader' }
  ]

  // Stock watchlist
  const watchlist = [
    { symbol: 'AAPL', name: 'Apple Inc.', buffett: 88, dividend: 82, moat: 92, resilience: 87 },
    { symbol: 'MSFT', name: 'Microsoft', buffett: 92, dividend: 85, moat: 95, resilience: 93 },
    { symbol: 'BRK.B', name: 'Berkshire', buffett: 98, dividend: 0, moat: 88, resilience: 95 },
    { symbol: 'JNJ', name: 'Johnson & Johnson', buffett: 85, dividend: 95, moat: 82, resilience: 88 },
    { symbol: 'KO', name: 'Coca-Cola', buffett: 90, dividend: 92, moat: 94, resilience: 85 }
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-blue-400">Loading ratings analysis...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header className="glass-card-dark">
        <h1 className="text-2xl font-bold text-blue-400">COMPANY RATINGS & ANALYSIS</h1>
        <p className="text-slate-400 mt-2">
          Buffett checklist, dividend safety, moat strength, and resilience ratings
        </p>
      </header>

      {/* Stock Selector */}
      <div className="glass-card-dark">
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            {watchlist.map((stock) => (
              <button
                key={stock.symbol}
                onClick={() => setSelectedStock(stock.symbol)}
                className={`px-4 py-2 rounded-lg text-sm transition-all ${
                  selectedStock === stock.symbol
                    ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                {stock.symbol}
              </button>
            ))}
          </div>
          <input
            type="text"
            placeholder="Enter symbol..."
            className="terminal-input w-32"
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                setSelectedStock((e.target as HTMLInputElement).value.toUpperCase())
              }
            }}
          />
        </div>
      </div>

      {/* Rating Tabs */}
      <div className="flex gap-2 p-1 glass-card-dark w-fit rounded-lg">
        {['buffett', 'dividend', 'moat', 'resilience'].map((view) => (
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

      {/* Buffett Checklist */}
      {activeView === 'buffett' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Buffett Investment Checklist - {selectedStock}</h2>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold text-blue-400">88/100</span>
                <span className="badge badge-success">STRONG BUY</span>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <table className="terminal-table">
                  <thead>
                    <tr>
                      <th>Criteria</th>
                      <th>Score</th>
                      <th>Weight</th>
                    </tr>
                  </thead>
                  <tbody>
                    {buffettCriteria.map((item) => (
                      <tr key={item.criteria}>
                        <td className="text-xs">{item.criteria}</td>
                        <td>
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-slate-700 rounded">
                              <div 
                                className={`h-2 rounded ${
                                  item.score > 80 ? 'bg-green-500' : 
                                  item.score > 60 ? 'bg-yellow-500' : 
                                  'bg-red-500'
                                }`}
                                style={{ width: `${item.score}%` }}
                              />
                            </div>
                            <span className="text-xs">{item.score}</span>
                          </div>
                        </td>
                        <td>
                          <span className={`badge badge-sm ${
                            item.weight === 'High' ? 'badge-danger' : 
                            item.weight === 'Medium' ? 'badge-warning' : 
                            'badge-info'
                          }`}>
                            {item.weight}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={buffettCriteria.slice(0, 6)}>
                    <PolarGrid stroke="#1e293b" />
                    <PolarAngleAxis dataKey="criteria" stroke="#64748b" tick={{ fontSize: 10 }} />
                    <PolarRadiusAxis stroke="#64748b" domain={[0, 100]} />
                    <Radar name="Score" dataKey="score" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="data-cell">
              <div className="data-label">Overall Score</div>
              <div className="data-value text-blue-400">88/100</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Strengths</div>
              <div className="data-value profit">7/10</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Weaknesses</div>
              <div className="data-value text-yellow-400">2/10</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Recommendation</div>
              <div className="data-value profit">BUY</div>
            </div>
          </div>
        </div>
      )}

      {/* Dividend Safety */}
      {activeView === 'dividend' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Dividend Safety Analysis - {selectedStock}</h2>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold text-green-400">{dividendSafety.overall}/100</span>
                <span className="badge badge-success">SAFE</span>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={dividendSafety.factors}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="factor" stroke="#64748b" angle={-45} textAnchor="end" height={80} />
                <YAxis stroke="#64748b" domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Bar dataKey="score" fill={(entry: any) => 
                  entry.score > 80 ? '#10b981' : 
                  entry.score > 60 ? '#f59e0b' : 
                  '#ef4444'
                } />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-5 gap-4">
            <div className="data-cell">
              <div className="data-label">Current Yield</div>
              <div className="data-value">2.8%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">5Y Growth</div>
              <div className="data-value profit">+8.5%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Payout Ratio</div>
              <div className="data-value text-yellow-400">45%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Years Paid</div>
              <div className="data-value">38</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Cut Risk</div>
              <div className="data-value profit">LOW</div>
            </div>
          </div>
        </div>
      )}

      {/* Moat Strength */}
      {activeView === 'moat' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Competitive Moat Analysis - {selectedStock}</h2>
              <span className="badge badge-info">WIDE MOAT</span>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={moatStrength}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="aspect" stroke="#64748b" angle={-45} textAnchor="end" height={100} />
                <YAxis stroke="#64748b" domain={[0, 100]} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Legend />
                <Bar dataKey="current" fill="#3b82f6" name={selectedStock} />
                <Bar dataKey="industry" fill="#64748b" name="Industry Avg" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="data-cell">
              <div className="data-label">Overall Moat</div>
              <div className="data-value text-blue-400">WIDE</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Moat Trend</div>
              <div className="data-value profit">STRENGTHENING</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Disruption Risk</div>
              <div className="data-value profit">LOW</div>
            </div>
          </div>
        </div>
      )}

      {/* Resilience Rating */}
      {activeView === 'resilience' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Company Resilience Rating - {selectedStock}</h2>
              <div className="text-2xl font-bold text-blue-400">87/100</div>
            </div>
            <table className="terminal-table">
              <thead>
                <tr>
                  <th>Factor</th>
                  <th>Score</th>
                  <th>Status</th>
                  <th>Trend</th>
                </tr>
              </thead>
              <tbody>
                {resilienceFactors.map((factor) => (
                  <tr key={factor.factor}>
                    <td>{factor.factor}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-2 bg-slate-700 rounded">
                          <div 
                            className={`h-2 rounded ${
                              factor.score > 80 ? 'bg-green-500' : 
                              factor.score > 60 ? 'bg-yellow-500' : 
                              'bg-red-500'
                            }`}
                            style={{ width: `${factor.score}%` }}
                          />
                        </div>
                        <span className="text-xs">{factor.score}</span>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${
                        factor.score > 80 ? 'badge-success' : 
                        factor.score > 60 ? 'badge-warning' : 
                        'badge-danger'
                      }`}>
                        {factor.status}
                      </span>
                    </td>
                    <td className="profit">↑</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="glass-card-dark">
            <h3 className="terminal-title mb-4">Crisis Resilience Scenarios</h3>
            <div className="grid grid-cols-4 gap-4">
              <div className="p-4 border-l-4 border-green-500">
                <div className="data-label">Recession</div>
                <div className="data-value profit">HIGH</div>
              </div>
              <div className="p-4 border-l-4 border-yellow-500">
                <div className="data-label">Tech Disruption</div>
                <div className="data-value text-yellow-400">MEDIUM</div>
              </div>
              <div className="p-4 border-l-4 border-green-500">
                <div className="data-label">Supply Chain</div>
                <div className="data-value profit">HIGH</div>
              </div>
              <div className="p-4 border-l-4 border-blue-500">
                <div className="data-label">Regulatory</div>
                <div className="data-value text-blue-400">MODERATE</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Watchlist Summary */}
      <div className="glass-card-dark">
        <div className="terminal-header">
          <h2 className="terminal-title">Ratings Watchlist</h2>
        </div>
        <table className="terminal-table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Company</th>
              <th>Buffett Score</th>
              <th>Dividend Safety</th>
              <th>Moat Strength</th>
              <th>Resilience</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {watchlist.map((stock) => (
              <tr key={stock.symbol}>
                <td className="font-bold text-blue-400">{stock.symbol}</td>
                <td className="text-xs">{stock.name}</td>
                <td>
                  <span className={stock.buffett > 85 ? 'profit' : stock.buffett > 70 ? 'text-yellow-400' : 'loss'}>
                    {stock.buffett}
                  </span>
                </td>
                <td>
                  <span className={stock.dividend > 80 ? 'profit' : stock.dividend > 60 ? 'text-yellow-400' : 'loss'}>
                    {stock.dividend || 'N/A'}
                  </span>
                </td>
                <td>
                  <span className={stock.moat > 85 ? 'profit' : stock.moat > 70 ? 'text-yellow-400' : 'loss'}>
                    {stock.moat}
                  </span>
                </td>
                <td>
                  <span className={stock.resilience > 85 ? 'profit' : stock.resilience > 70 ? 'text-yellow-400' : 'loss'}>
                    {stock.resilience}
                  </span>
                </td>
                <td>
                  <button
                    onClick={() => setSelectedStock(stock.symbol)}
                    className="text-blue-400 hover:text-blue-300 text-xs uppercase"
                  >
                    Analyze
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}