'use client'

import { useState, useEffect } from 'react'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { apiClient } from '@/lib/api-client'

export default function MacroCyclesPage() {
  const [macroData, setMacroData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('short-term')

  useEffect(() => {
    fetchMacroData()
  }, [])

  const fetchMacroData = async () => {
    try {
      const response = await apiClient.executePattern({
        pattern: 'macro_cycles_overview',
        inputs: {}
      })
      setMacroData(response.result)
    } catch (error) {
      console.error('Failed to fetch macro data:', error)
    } finally {
      setLoading(false)
    }
  }

  // Generate sample data for visualizations
  const shortTermDebtCycle = Array.from({ length: 96 }, (_, i) => ({
    month: `M${i + 1}`,
    debt: 100 + 20 * Math.sin(i * 0.13) + Math.random() * 10,
    gdp: 100 + 15 * Math.sin(i * 0.13 + 1) + Math.random() * 5,
    credit: 100 + 25 * Math.sin(i * 0.13 - 0.5) + Math.random() * 8
  }))

  const longTermDebtCycle = Array.from({ length: 100 }, (_, i) => ({
    year: 1920 + i,
    debtToGDP: 30 + 40 * Math.sin(i * 0.063) + i * 0.3,
    productivity: 100 + i * 0.5 + Math.random() * 10,
    inequality: 20 + 30 * Math.sin(i * 0.063 + 2) + i * 0.2
  }))

  const empireCycle = Array.from({ length: 500 }, (_, i) => ({
    year: 1500 + i,
    power: 50 + 40 * Math.exp(-((i - 250) ** 2) / 20000),
    education: 30 + 35 * Math.exp(-((i - 220) ** 2) / 18000),
    military: 40 + 45 * Math.exp(-((i - 270) ** 2) / 22000),
    trade: 35 + 40 * Math.exp(-((i - 240) ** 2) / 19000)
  }))

  const darData = Array.from({ length: 30 }, (_, i) => ({
    year: 1994 + i,
    dar: 1.2 + 0.8 * Math.sin(i * 0.3) + Math.random() * 0.2,
    threshold: 2.0
  }))

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-blue-400">Loading macro cycles data...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header className="glass-card-dark">
        <h1 className="text-2xl font-bold text-blue-400">MACRO CYCLES ANALYSIS</h1>
        <p className="text-slate-400 mt-2">
          Comprehensive debt cycle and empire analysis based on Ray Dalio's framework
        </p>
      </header>

      {/* Cycle Tabs */}
      <div className="flex gap-2 p-1 glass-card-dark w-fit rounded-lg">
        {['short-term', 'long-term', 'empire', 'dar'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg text-sm uppercase tracking-wider transition-all ${
              activeTab === tab
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            {tab.replace('-', ' ')} Cycle
          </button>
        ))}
      </div>

      {/* Short-term Debt Cycle */}
      {activeTab === 'short-term' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Short-Term Debt Cycle (2-8 Years)</h2>
              <span className="badge badge-info">EXPANSION PHASE</span>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={shortTermDebtCycle}>
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
                <Line type="monotone" dataKey="debt" stroke="#ef4444" strokeWidth={2} dot={false} name="Debt Level" />
                <Line type="monotone" dataKey="gdp" stroke="#10b981" strokeWidth={2} dot={false} name="GDP Growth" />
                <Line type="monotone" dataKey="credit" stroke="#3b82f6" strokeWidth={2} dot={false} name="Credit Growth" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="data-cell">
              <div className="data-label">Current Phase</div>
              <div className="data-value text-blue-400">EXPANSION</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Cycle Duration</div>
              <div className="data-value">5.3 Years</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Credit Growth</div>
              <div className="data-value profit">+8.2%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Next Recession</div>
              <div className="data-value text-yellow-400">18-24 Months</div>
            </div>
          </div>
        </div>
      )}

      {/* Long-term Debt Cycle */}
      {activeTab === 'long-term' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Long-Term Debt Cycle (50-100 Years)</h2>
              <span className="badge badge-warning">LATE CYCLE</span>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={longTermDebtCycle}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="year" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Legend />
                <Area type="monotone" dataKey="debtToGDP" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} name="Debt/GDP %" />
                <Area type="monotone" dataKey="productivity" stackId="2" stroke="#10b981" fill="#10b981" fillOpacity={0.3} name="Productivity" />
                <Area type="monotone" dataKey="inequality" stackId="3" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.3} name="Inequality" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="data-cell">
              <div className="data-label">Total Debt/GDP</div>
              <div className="data-value loss">280%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Wealth Gap (Top 1%)</div>
              <div className="data-value text-yellow-400">35%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Deleveraging Risk</div>
              <div className="data-value loss">HIGH</div>
            </div>
          </div>
        </div>
      )}

      {/* Empire Cycle */}
      {activeTab === 'empire' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Empire Cycle Analysis (500+ Years)</h2>
              <span className="badge badge-danger">DECLINING PHASE</span>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={empireCycle}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="year" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Legend />
                <Area type="monotone" dataKey="power" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} name="Global Power" />
                <Area type="monotone" dataKey="education" stroke="#10b981" fill="#10b981" fillOpacity={0.3} name="Education" />
                <Area type="monotone" dataKey="military" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} name="Military" />
                <Area type="monotone" dataKey="trade" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.3} name="Trade Share" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="data-cell">
              <div className="data-label">Reserve Currency</div>
              <div className="data-value text-blue-400">USD (62%)</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Global Trade Share</div>
              <div className="data-value">24.3%</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Education Rank</div>
              <div className="data-value text-yellow-400">#15</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Internal Conflict</div>
              <div className="data-value loss">ELEVATED</div>
            </div>
          </div>
        </div>
      )}

      {/* DAR Analysis */}
      {activeTab === 'dar' && (
        <div className="space-y-6">
          <div className="glass-card-dark">
            <div className="terminal-header">
              <h2 className="terminal-title">Debt-Asset Ratio (DAR) Analysis</h2>
              <span className="badge badge-info">MONITORING</span>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={darData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="year" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                    border: '1px solid rgba(255, 255, 255, 0.1)' 
                  }} 
                />
                <Legend />
                <Line type="monotone" dataKey="dar" stroke="#3b82f6" strokeWidth={2} dot={false} name="DAR Ratio" />
                <Line type="monotone" dataKey="threshold" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 5" dot={false} name="Critical Threshold" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="data-cell">
              <div className="data-label">Current DAR</div>
              <div className="data-value">1.85</div>
            </div>
            <div className="data-cell">
              <div className="data-label">30-Day Change</div>
              <div className="data-value loss">+0.12</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Distance to Crisis</div>
              <div className="data-value text-yellow-400">0.15</div>
            </div>
            <div className="data-cell">
              <div className="data-label">Risk Level</div>
              <div className="data-value text-yellow-400">MODERATE</div>
            </div>
          </div>
        </div>
      )}

      {/* Regime Detection Panel */}
      <div className="glass-card-dark">
        <div className="terminal-header">
          <h2 className="terminal-title">Current Regime Detection</h2>
        </div>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <h3 className="text-sm font-semibold text-slate-400 mb-4">ECONOMIC INDICATORS</h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Inflation</span>
                <span className="profit">DECLINING</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Growth</span>
                <span className="text-yellow-400">SLOWING</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Credit</span>
                <span className="loss">TIGHTENING</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Liquidity</span>
                <span className="text-yellow-400">MODERATE</span>
              </div>
            </div>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-400 mb-4">REGIME CLASSIFICATION</h3>
            <div className="p-4 border-2 border-yellow-500/30 rounded-lg bg-yellow-500/10">
              <div className="text-yellow-400 font-bold text-lg mb-2">LATE CYCLE SLOWDOWN</div>
              <p className="text-sm text-slate-400">
                Characterized by slowing growth, tightening credit conditions, and elevated debt levels.
                Risk of recession in next 12-18 months.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}