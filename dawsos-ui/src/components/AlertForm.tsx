'use client'

import { useState } from 'react'

export function AlertForm() {
  const [formData, setFormData] = useState({
    condition: '',
    threshold: '',
    portfolio_id: 'main',
  })

  const conditions = [
    'Portfolio Value Drop',
    'DaR Breach',
    'Volatility Spike',
    'Single Position Loss',
    'Correlation Spike',
    'Macro Regime Change',
  ]

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Creating alert:', formData)
    // TODO: Implement alert creation
  }

  return (
    <div className="metric-card">
      <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Create Alert</h3>
      
      <form onSubmit={handleSubmit} className="space-y-fib5">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-fib2">
            Condition
          </label>
          <select
            value={formData.condition}
            onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
            className="w-full px-fib3 py-fib2 border border-slate-300 rounded-fib2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Select condition...</option>
            {conditions.map((condition) => (
              <option key={condition} value={condition}>
                {condition}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-fib2">
            Threshold
          </label>
          <input
            type="number"
            step="0.1"
            value={formData.threshold}
            onChange={(e) => setFormData({ ...formData, threshold: e.target.value })}
            className="w-full px-fib3 py-fib2 border border-slate-300 rounded-fib2 focus:outline-none focus:ring-2 focus:ring-primary-500"
            placeholder="Enter threshold value..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-fib2">
            Portfolio
          </label>
          <select
            value={formData.portfolio_id}
            onChange={(e) => setFormData({ ...formData, portfolio_id: e.target.value })}
            className="w-full px-fib3 py-fib2 border border-slate-300 rounded-fib2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="main">Main Portfolio</option>
            <option value="growth">Growth Portfolio</option>
            <option value="income">Income Portfolio</option>
          </select>
        </div>

        <button
          type="submit"
          className="w-full bg-primary-500 text-white py-fib3 px-fib4 rounded-fib2 hover:bg-primary-600 transition-colors duration-fib2"
        >
          Create Alert
        </button>
      </form>
    </div>
  )
}
