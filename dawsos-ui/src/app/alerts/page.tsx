'use client'

import { useState, useEffect } from 'react'
import { Bell, AlertTriangle, TrendingUp, TrendingDown, Clock, Check, X, AlertCircle } from 'lucide-react'

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('active')
  const [showCreateForm, setShowCreateForm] = useState(false)

  useEffect(() => {
    fetchAlerts()
    const interval = setInterval(fetchAlerts, 10000) // Refresh every 10 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchAlerts = async () => {
    try {
      const response = await fetch('/api/alerts')
      const data = await response.json()
      setAlerts(data.alerts || [])
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
      // Use sample data if API fails
      setAlerts(sampleAlerts)
    } finally {
      setLoading(false)
    }
  }

  const sampleAlerts = [
    {
      id: 1,
      type: 'PRICE',
      status: 'ACTIVE',
      severity: 'HIGH',
      symbol: 'AAPL',
      condition: 'Price > $180',
      currentValue: '$178.25',
      created: '2025-10-30 09:15:00',
      triggered: null,
      message: 'Apple price approaching threshold'
    },
    {
      id: 2,
      type: 'RISK',
      status: 'TRIGGERED',
      severity: 'CRITICAL',
      symbol: 'PORTFOLIO',
      condition: 'VaR > $150K',
      currentValue: '$165,430',
      created: '2025-10-29 14:22:00',
      triggered: '2025-10-31 10:35:00',
      message: 'Portfolio VaR exceeds risk limit'
    },
    {
      id: 3,
      type: 'VOLUME',
      status: 'ACTIVE',
      severity: 'MEDIUM',
      symbol: 'TSLA',
      condition: 'Volume > 50M',
      currentValue: '42.5M',
      created: '2025-10-31 08:00:00',
      triggered: null,
      message: 'Tesla volume spike alert'
    },
    {
      id: 4,
      type: 'MACRO',
      status: 'TRIGGERED',
      severity: 'HIGH',
      symbol: 'DXY',
      condition: 'Dollar Index > 106',
      currentValue: '106.28',
      created: '2025-10-28 16:45:00',
      triggered: '2025-10-31 11:15:00',
      message: 'Dollar strength impacting portfolio'
    },
    {
      id: 5,
      type: 'DRAWDOWN',
      status: 'ACTIVE',
      severity: 'MEDIUM',
      symbol: 'PORTFOLIO',
      condition: 'Drawdown > 10%',
      currentValue: '-8.2%',
      created: '2025-10-25 12:00:00',
      triggered: null,
      message: 'Portfolio drawdown monitoring'
    }
  ]

  const alertTypes = ['PRICE', 'RISK', 'VOLUME', 'MACRO', 'DRAWDOWN', 'CORRELATION', 'VOLATILITY']
  const severityLevels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

  const activeAlerts = alerts.filter(a => a.status === 'ACTIVE')
  const triggeredAlerts = alerts.filter(a => a.status === 'TRIGGERED')
  const historicalAlerts = alerts.filter(a => a.status === 'RESOLVED' || a.status === 'EXPIRED')

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-blue-400">Loading alerts...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header className="glass-card-dark">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-blue-400">ALERT MANAGEMENT SYSTEM</h1>
            <p className="text-slate-400 mt-2">
              Real-time monitoring and alert configuration for portfolio risk management
            </p>
          </div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="btn-terminal"
          >
            CREATE ALERT
          </button>
        </div>
      </header>

      {/* Alert Statistics */}
      <div className="grid grid-cols-5 gap-4">
        <div className="data-cell">
          <div className="data-label">Active Alerts</div>
          <div className="data-value text-blue-400">{activeAlerts.length}</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Triggered Today</div>
          <div className="data-value text-yellow-400">{triggeredAlerts.length}</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Critical</div>
          <div className="data-value loss">
            {alerts.filter(a => a.severity === 'CRITICAL').length}
          </div>
        </div>
        <div className="data-cell">
          <div className="data-label">Response Time</div>
          <div className="data-value profit">2.3s</div>
        </div>
        <div className="data-cell">
          <div className="data-label">Uptime</div>
          <div className="data-value profit">99.98%</div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 p-1 glass-card-dark w-fit rounded-lg">
        {['active', 'triggered', 'history', 'configure'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm uppercase tracking-wider transition-all ${
              activeTab === tab
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Active Alerts */}
      {activeTab === 'active' && (
        <div className="glass-card-dark">
          <div className="terminal-header">
            <h2 className="terminal-title">Active Alerts</h2>
            <span className="text-sm text-slate-400">{activeAlerts.length} alerts monitoring</span>
          </div>
          <table className="terminal-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Symbol</th>
                <th>Condition</th>
                <th>Current Value</th>
                <th>Severity</th>
                <th>Created</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {activeAlerts.map((alert) => (
                <tr key={alert.id}>
                  <td className="font-mono">#{alert.id.toString().padStart(4, '0')}</td>
                  <td>
                    <span className="badge badge-info">{alert.type}</span>
                  </td>
                  <td className="font-bold text-blue-400">{alert.symbol}</td>
                  <td className="text-xs">{alert.condition}</td>
                  <td className="font-mono">{alert.currentValue}</td>
                  <td>
                    <span className={`badge ${
                      alert.severity === 'CRITICAL' ? 'badge-danger' :
                      alert.severity === 'HIGH' ? 'badge-warning' :
                      alert.severity === 'MEDIUM' ? 'badge-info' :
                      'badge-success'
                    }`}>
                      {alert.severity}
                    </span>
                  </td>
                  <td className="text-xs">{alert.created}</td>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="text-green-400 text-xs">MONITORING</span>
                    </div>
                  </td>
                  <td>
                    <div className="flex gap-2">
                      <button className="text-blue-400 hover:text-blue-300 text-xs">EDIT</button>
                      <button className="text-red-400 hover:text-red-300 text-xs">DELETE</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Triggered Alerts */}
      {activeTab === 'triggered' && (
        <div className="glass-card-dark">
          <div className="terminal-header">
            <h2 className="terminal-title">Triggered Alerts</h2>
            <span className="badge badge-warning">{triggeredAlerts.length} REQUIRE ACTION</span>
          </div>
          <div className="space-y-4">
            {triggeredAlerts.map((alert) => (
              <div key={alert.id} className="p-4 bg-slate-800/50 rounded-lg border-l-4 border-l-yellow-500">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <AlertTriangle className="text-yellow-400" size={20} />
                      <span className="font-bold text-lg">{alert.symbol}</span>
                      <span className={`badge ${
                        alert.severity === 'CRITICAL' ? 'badge-danger' : 'badge-warning'
                      }`}>
                        {alert.severity}
                      </span>
                      <span className="badge badge-warning">TRIGGERED</span>
                    </div>
                    <p className="text-slate-200 mb-2">{alert.message}</p>
                    <div className="grid grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500">Type:</span>
                        <span className="ml-2">{alert.type}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Condition:</span>
                        <span className="ml-2">{alert.condition}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Current:</span>
                        <span className="ml-2 text-yellow-400">{alert.currentValue}</span>
                      </div>
                      <div>
                        <span className="text-slate-500">Triggered:</span>
                        <span className="ml-2">{alert.triggered}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col gap-2">
                    <button className="btn-terminal-success text-xs px-3 py-1">ACKNOWLEDGE</button>
                    <button className="btn-terminal-danger text-xs px-3 py-1">DISMISS</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Alert History */}
      {activeTab === 'history' && (
        <div className="glass-card-dark">
          <div className="terminal-header">
            <h2 className="terminal-title">Alert History</h2>
          </div>
          <div className="mb-4 flex gap-4">
            <input
              type="date"
              className="terminal-input"
              defaultValue="2025-10-01"
            />
            <input
              type="date"
              className="terminal-input"
              defaultValue="2025-10-31"
            />
            <select className="terminal-input">
              <option>All Types</option>
              {alertTypes.map(type => (
                <option key={type}>{type}</option>
              ))}
            </select>
          </div>
          <table className="terminal-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Symbol</th>
                <th>Condition</th>
                <th>Triggered Value</th>
                <th>Duration</th>
                <th>Resolution</th>
              </tr>
            </thead>
            <tbody>
              {[...Array(5)].map((_, i) => (
                <tr key={i}>
                  <td className="text-xs">2025-10-{25 - i} 14:30:00</td>
                  <td><span className="badge badge-info">PRICE</span></td>
                  <td className="font-bold">SPY</td>
                  <td className="text-xs">Price < $450</td>
                  <td className="loss">$448.50</td>
                  <td>2h 15m</td>
                  <td>
                    <span className="badge badge-success">AUTO-RESOLVED</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Configure Alerts */}
      {activeTab === 'configure' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Alert Configuration</h2>
            </div>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-semibold text-slate-400 mb-4">CREATE NEW ALERT</h3>
                <div className="space-y-4">
                  <div>
                    <label className="data-label">Alert Type</label>
                    <select className="terminal-input w-full">
                      {alertTypes.map(type => (
                        <option key={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="data-label">Symbol/Asset</label>
                    <input type="text" className="terminal-input w-full" placeholder="e.g., AAPL, SPY" />
                  </div>
                  <div>
                    <label className="data-label">Condition</label>
                    <div className="flex gap-2">
                      <select className="terminal-input">
                        <option>Greater than</option>
                        <option>Less than</option>
                        <option>Equals</option>
                        <option>Changes by</option>
                      </select>
                      <input type="text" className="terminal-input flex-1" placeholder="Value" />
                    </div>
                  </div>
                  <div>
                    <label className="data-label">Severity</label>
                    <select className="terminal-input w-full">
                      {severityLevels.map(level => (
                        <option key={level}>{level}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="data-label">Notification Method</label>
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2">
                        <input type="checkbox" defaultChecked />
                        <span className="text-sm">Dashboard</span>
                      </label>
                      <label className="flex items-center gap-2">
                        <input type="checkbox" />
                        <span className="text-sm">Email</span>
                      </label>
                      <label className="flex items-center gap-2">
                        <input type="checkbox" />
                        <span className="text-sm">SMS</span>
                      </label>
                    </div>
                  </div>
                  <button className="btn-terminal w-full">CREATE ALERT</button>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-slate-400 mb-4">ALERT TEMPLATES</h3>
                <div className="space-y-3">
                  <button className="w-full p-3 bg-slate-800/30 rounded-lg hover:bg-slate-800/50 text-left">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold">Portfolio Risk Alert</div>
                        <div className="text-xs text-slate-400">VaR > $100K or Drawdown > 10%</div>
                      </div>
                      <span className="text-blue-400">USE</span>
                    </div>
                  </button>
                  <button className="w-full p-3 bg-slate-800/30 rounded-lg hover:bg-slate-800/50 text-left">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold">Market Crash Alert</div>
                        <div className="text-xs text-slate-400">SPY drops > 3% in 1 day</div>
                      </div>
                      <span className="text-blue-400">USE</span>
                    </div>
                  </button>
                  <button className="w-full p-3 bg-slate-800/30 rounded-lg hover:bg-slate-800/50 text-left">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold">Volatility Spike</div>
                        <div className="text-xs text-slate-400">VIX > 25 or rises > 20%</div>
                      </div>
                      <span className="text-blue-400">USE</span>
                    </div>
                  </button>
                  <button className="w-full p-3 bg-slate-800/30 rounded-lg hover:bg-slate-800/50 text-left">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold">Position Concentration</div>
                        <div className="text-xs text-slate-400">Any position > 15% of portfolio</div>
                      </div>
                      <span className="text-blue-400">USE</span>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="glass-card-dark">
            <h3 className="terminal-title mb-4">Alert Performance Statistics</h3>
            <div className="grid grid-cols-4 gap-4">
              <div className="p-4 border-l-4 border-green-500">
                <div className="data-label">Alerts Triggered</div>
                <div className="data-value">285</div>
                <div className="text-xs text-slate-500 mt-1">Last 30 days</div>
              </div>
              <div className="p-4 border-l-4 border-blue-500">
                <div className="data-label">Avg Response Time</div>
                <div className="data-value">2.3s</div>
                <div className="text-xs text-slate-500 mt-1">99th percentile: 5.2s</div>
              </div>
              <div className="p-4 border-l-4 border-yellow-500">
                <div className="data-label">False Positives</div>
                <div className="data-value">3.2%</div>
                <div className="text-xs text-slate-500 mt-1">12 of 285</div>
              </div>
              <div className="p-4 border-l-4 border-purple-500">
                <div className="data-label">Coverage</div>
                <div className="data-value">92%</div>
                <div className="text-xs text-slate-500 mt-1">Assets monitored</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}