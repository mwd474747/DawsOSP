'use client'

import { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { apiClient } from '@/lib/api-client'
import { TrendingUp, TrendingDown, Clock, AlertCircle } from 'lucide-react'

export default function MarketDataPage() {
  const [marketData, setMarketData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [activeView, setActiveView] = useState('quotes')
  const [selectedAsset, setSelectedAsset] = useState('SPY')

  useEffect(() => {
    fetchMarketData()
    const interval = setInterval(fetchMarketData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchMarketData = async () => {
    try {
      // Fetch market data from backend
      const response = await apiClient.executePattern({
        pattern: 'news_impact_analysis',
        inputs: { symbol: selectedAsset }
      })
      setMarketData(response.result)
    } catch (error) {
      console.error('Failed to fetch market data:', error)
    } finally {
      setLoading(false)
    }
  }

  // Real-time quotes data
  const quotes = [
    { symbol: 'SPY', name: 'S&P 500 ETF', price: 452.38, change: 5.82, pctChange: 1.30, volume: '82.5M', bid: 452.35, ask: 452.40 },
    { symbol: 'QQQ', name: 'Nasdaq ETF', price: 385.62, change: 8.45, pctChange: 2.24, volume: '45.2M', bid: 385.60, ask: 385.65 },
    { symbol: 'DIA', name: 'Dow ETF', price: 358.94, change: 2.15, pctChange: 0.60, volume: '12.8M', bid: 358.92, ask: 358.96 },
    { symbol: 'IWM', name: 'Russell 2000', price: 198.75, change: -1.23, pctChange: -0.62, volume: '28.3M', bid: 198.73, ask: 198.77 },
    { symbol: 'VIX', name: 'Volatility Index', price: 18.52, change: -0.85, pctChange: -4.39, volume: 'N/A', bid: 18.50, ask: 18.54 },
    { symbol: 'GLD', name: 'Gold ETF', price: 185.42, change: 2.18, pctChange: 1.19, volume: '8.2M', bid: 185.40, ask: 185.44 },
    { symbol: 'TLT', name: '20Y Treasury', price: 92.85, change: -0.42, pctChange: -0.45, volume: '15.6M', bid: 92.83, ask: 92.87 },
    { symbol: 'DXY', name: 'Dollar Index', price: 105.28, change: 0.35, pctChange: 0.33, volume: 'N/A', bid: 105.26, ask: 105.30 }
  ]

  // News impact data
  const newsImpact = [
    { 
      time: '09:30', 
      headline: 'Fed Minutes Suggest Pause in Rate Hikes',
      impact: 'HIGH',
      sentiment: 'POSITIVE',
      assets: ['SPY', 'TLT'],
      priceMove: '+0.8%'
    },
    { 
      time: '10:15', 
      headline: 'Tech Earnings Beat Expectations',
      impact: 'MEDIUM',
      sentiment: 'POSITIVE',
      assets: ['QQQ', 'AAPL'],
      priceMove: '+1.2%'
    },
    { 
      time: '11:00', 
      headline: 'China Trade Data Disappoints',
      impact: 'MEDIUM',
      sentiment: 'NEGATIVE',
      assets: ['EEM', 'FXI'],
      priceMove: '-0.5%'
    },
    { 
      time: '13:45', 
      headline: 'Oil Inventories Rise More Than Expected',
      impact: 'LOW',
      sentiment: 'NEGATIVE',
      assets: ['XLE', 'USO'],
      priceMove: '-1.8%'
    },
    { 
      time: '14:30', 
      headline: 'GDP Growth Revised Higher',
      impact: 'HIGH',
      sentiment: 'POSITIVE',
      assets: ['SPY', 'DIA'],
      priceMove: '+0.6%'
    }
  ]

  // Fundamental data
  const fundamentals = {
    'SPY': {
      pe: 18.5,
      pb: 4.2,
      divYield: 1.45,
      eps: 24.50,
      marketCap: '38.2T',
      avgVolume: '85M',
      beta: 1.0,
      high52w: 468.25,
      low52w: 385.50
    }
  }

  // Intraday price data
  const intradayData = Array.from({ length: 78 }, (_, i) => {
    const hour = Math.floor(i / 6) + 9
    const minute = (i % 6) * 10
    return {
      time: `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`,
      price: 452 + Math.sin(i * 0.1) * 3 + Math.random() * 2,
      volume: 1000000 + Math.random() * 500000
    }
  })

  // Economic calendar
  const economicCalendar = [
    { time: '08:30', event: 'Initial Jobless Claims', actual: '215K', forecast: '220K', prior: '218K', impact: 'MEDIUM' },
    { time: '10:00', event: 'Consumer Confidence', actual: '108.5', forecast: '106.0', prior: '105.2', impact: 'HIGH' },
    { time: '10:30', event: 'EIA Crude Oil Inventories', actual: '+2.8M', forecast: '+1.5M', prior: '-1.2M', impact: 'MEDIUM' },
    { time: '14:00', event: 'Fed Beige Book', actual: 'Released', forecast: 'N/A', prior: 'N/A', impact: 'HIGH' }
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-blue-400">Loading market data...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header className="glass-card-dark">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-blue-400">MARKET DATA & NEWS</h1>
            <p className="text-slate-400 mt-2">
              Real-time quotes, news impact analysis, and fundamental data
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Clock size={16} className="text-slate-400" />
            <span className="text-sm text-slate-400">
              Last Update: {new Date().toLocaleTimeString()}
            </span>
          </div>
        </div>
      </header>

      {/* View Tabs */}
      <div className="flex gap-2 p-1 glass-card-dark w-fit rounded-lg">
        {['quotes', 'news', 'fundamentals', 'intraday', 'calendar'].map((view) => (
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

      {/* Real-time Quotes */}
      {activeView === 'quotes' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Live Market Quotes</h2>
              <span className="badge badge-success">MARKET OPEN</span>
            </div>
            <table className="terminal-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Name</th>
                  <th>Price</th>
                  <th>Change</th>
                  <th>% Change</th>
                  <th>Volume</th>
                  <th>Bid</th>
                  <th>Ask</th>
                  <th>Trend</th>
                </tr>
              </thead>
              <tbody>
                {quotes.map((quote) => (
                  <tr key={quote.symbol}>
                    <td className="font-bold text-blue-400">{quote.symbol}</td>
                    <td className="text-xs">{quote.name}</td>
                    <td className="font-mono">${quote.price.toFixed(2)}</td>
                    <td className={quote.change > 0 ? 'profit' : 'loss'}>
                      {quote.change > 0 ? '+' : ''}{quote.change.toFixed(2)}
                    </td>
                    <td className={quote.pctChange > 0 ? 'profit' : 'loss'}>
                      {quote.pctChange > 0 ? '+' : ''}{quote.pctChange.toFixed(2)}%
                    </td>
                    <td>{quote.volume}</td>
                    <td className="font-mono text-xs">${quote.bid.toFixed(2)}</td>
                    <td className="font-mono text-xs">${quote.ask.toFixed(2)}</td>
                    <td>
                      {quote.change > 0 ? (
                        <TrendingUp size={16} className="text-green-400" />
                      ) : (
                        <TrendingDown size={16} className="text-red-400" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="data-cell">
              <div className="data-label">Advancers</div>
              <div className="data-value profit">2,854</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Decliners</div>
              <div className="data-value loss">1,246</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Unchanged</div>
              <div className="data-value">385</div>
            </div>
            <div className="data-cell">
              <div className="data-label">A/D Ratio</div>
              <div className="data-value profit">2.29</div>
            </div>
          </div>
        </div>
      )}

      {/* News Impact Analysis */}
      {activeView === 'news' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">News Impact Analysis</h2>
              <span className="badge badge-warning">5 HIGH IMPACT</span>
            </div>
            <div className="space-y-3">
              {newsImpact.map((news, index) => (
                <div key={index} className="p-4 bg-slate-800/30 rounded-lg border-l-4 border-l-blue-500">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-xs text-slate-500">{news.time}</span>
                        <span className={`badge ${
                          news.impact === 'HIGH' ? 'badge-danger' : 
                          news.impact === 'MEDIUM' ? 'badge-warning' : 
                          'badge-info'
                        }`}>
                          {news.impact}
                        </span>
                        <span className={`badge ${
                          news.sentiment === 'POSITIVE' ? 'badge-success' : 
                          news.sentiment === 'NEGATIVE' ? 'badge-danger' : 
                          'badge-info'
                        }`}>
                          {news.sentiment}
                        </span>
                      </div>
                      <h3 className="font-semibold text-slate-200 mb-2">{news.headline}</h3>
                      <div className="flex items-center gap-4 text-xs">
                        <span className="text-slate-400">Affected:</span>
                        {news.assets.map(asset => (
                          <span key={asset} className="text-blue-400">{asset}</span>
                        ))}
                        <span className="text-slate-400">Impact:</span>
                        <span className={news.priceMove.startsWith('+') ? 'profit' : 'loss'}>
                          {news.priceMove}
                        </span>
                      </div>
                    </div>
                    <AlertCircle size={16} className="text-yellow-400" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="data-cell">
              <div className="data-label">Positive News</div>
              <div className="data-value profit">12</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Negative News</div>
              <div className="data-value loss">8</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Sentiment Score</div>
              <div className="data-value profit">+0.65</div>
            </div>
          </div>
        </div>
      )}

      {/* Fundamental Data */}
      {activeView === 'fundamentals' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="flex items-center gap-4 mb-6">
              <select
                value={selectedAsset}
                onChange={(e) => setSelectedAsset(e.target.value)}
                className="terminal-input"
              >
                {quotes.map(q => (
                  <option key={q.symbol} value={q.symbol}>{q.symbol} - {q.name}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-3 gap-6">
              <div>
                <h3 className="terminal-title mb-4">Valuation Metrics</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">P/E Ratio</span>
                    <span>18.5</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">P/B Ratio</span>
                    <span>4.2</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">P/S Ratio</span>
                    <span>2.8</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">PEG Ratio</span>
                    <span>1.65</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">EV/EBITDA</span>
                    <span>14.2</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="terminal-title mb-4">Performance Metrics</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">1D Return</span>
                    <span className="profit">+1.30%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">1W Return</span>
                    <span className="profit">+2.85%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">1M Return</span>
                    <span className="loss">-1.25%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">YTD Return</span>
                    <span className="profit">+18.5%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">1Y Return</span>
                    <span className="profit">+22.3%</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="terminal-title mb-4">Risk Metrics</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Beta</span>
                    <span>1.0</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Volatility (30D)</span>
                    <span>15.8%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Sharpe Ratio</span>
                    <span>1.42</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Max Drawdown</span>
                    <span className="loss">-8.5%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">RSI (14)</span>
                    <span className="text-yellow-400">65.2</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-700">
              <div className="data-cell">
                <div className="data-label">Market Cap</div>
                <div className="data-value">$38.2T</div>
              </div>
              <div className="data-cell">
                <div className="data-label">52W High</div>
                <div className="data-value">$468.25</div>
              </div>
              <div className="data-cell">
                <div className="data-label">52W Low</div>
                <div className="data-value">$385.50</div>
              </div>
              <div className="data-cell">
                <div className="data-label">Avg Volume</div>
                <div className="data-value">85M</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Intraday Chart */}
      {activeView === 'intraday' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Intraday Price & Volume - {selectedAsset}</h2>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={intradayData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis 
                  dataKey="time" 
                  stroke="#64748b"
                  interval={12}
                />
                <YAxis yAxisId="left" stroke="#64748b" />
                <YAxis yAxisId="right" orientation="right" stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Legend />
                <Line 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="price" 
                  stroke="#10b981" 
                  strokeWidth={2} 
                  dot={false} 
                  name="Price"
                />
                <Bar yAxisId="right" dataKey="volume" fill="#3b82f6" opacity={0.3} name="Volume" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-5 gap-4">
            <div className="data-cell">
              <div className="data-label">Open</div>
              <div className="data-value">$450.25</div>
            </div>
            <div className="data-cell">
              <div className="data-label">High</div>
              <div className="data-value profit">$455.80</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Low</div>
              <div className="data-value loss">$449.50</div>
            </div>
            <div className="data-cell">
              <div className="data-label">VWAP</div>
              <div className="data-value">$452.65</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Volume</div>
              <div className="data-value">82.5M</div>
            </div>
          </div>
        </div>
      )}

      {/* Economic Calendar */}
      {activeView === 'calendar' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Economic Calendar - Today</h2>
            </div>
            <table className="terminal-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Event</th>
                  <th>Actual</th>
                  <th>Forecast</th>
                  <th>Prior</th>
                  <th>Impact</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {economicCalendar.map((event, index) => (
                  <tr key={index}>
                    <td>{event.time}</td>
                    <td className="font-semibold">{event.event}</td>
                    <td className={
                      event.actual > event.forecast ? 'profit' : 
                      event.actual < event.forecast ? 'loss' : 
                      'neutral'
                    }>
                      {event.actual}
                    </td>
                    <td>{event.forecast}</td>
                    <td>{event.prior}</td>
                    <td>
                      <span className={`badge ${
                        event.impact === 'HIGH' ? 'badge-danger' : 
                        event.impact === 'MEDIUM' ? 'badge-warning' : 
                        'badge-info'
                      }`}>
                        {event.impact}
                      </span>
                    </td>
                    <td>
                      {new Date().getHours() > parseInt(event.time.split(':')[0]) ? (
                        <span className="text-green-400">Released</span>
                      ) : (
                        <span className="text-slate-400">Pending</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="data-cell">
              <div className="data-label">Events Today</div>
              <div className="data-value">12</div>
            </div>
            <div className="data-cell">
              <div className="data-label">High Impact</div>
              <div className="data-value text-yellow-400">4</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Next Event</div>
              <div className="data-value">14:00</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}