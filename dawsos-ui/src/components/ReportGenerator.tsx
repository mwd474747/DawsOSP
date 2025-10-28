'use client'

import { useState } from 'react'

export function ReportGenerator() {
  const [formData, setFormData] = useState({
    template: 'portfolio_summary',
    portfolio_id: 'main',
    include_charts: true,
    include_attributions: true,
    watermark: true,
  })

  const templates = [
    { value: 'portfolio_summary', label: 'Portfolio Summary' },
    { value: 'buffett_analysis', label: 'Buffett Analysis' },
    { value: 'macro_overview', label: 'Macro Overview' },
    { value: 'scenario_analysis', label: 'Scenario Analysis' },
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Generating report:', formData)
    // TODO: Implement report generation
  }

  return (
    <div className="metric-card">
      <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Generate Report</h3>
      
      <form onSubmit={handleSubmit} className="space-y-fib5">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-fib2">
            Template
          </label>
          <select
            value={formData.template}
            onChange={(e) => setFormData({ ...formData, template: e.target.value })}
            className="w-full px-fib3 py-fib2 border border-slate-300 rounded-fib2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {templates.map((template) => (
              <option key={template.value} value={template.value}>
                {template.label}
              </option>
            ))}
          </select>
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

        <div className="space-y-fib3">
          <label className="flex items-center space-x-fib3">
            <input
              type="checkbox"
              checked={formData.include_charts}
              onChange={(e) => setFormData({ ...formData, include_charts: e.target.checked })}
              className="rounded border-slate-300 text-primary-500 focus:ring-primary-500"
            />
            <span className="text-sm text-slate-700">Include Charts</span>
          </label>
          
          <label className="flex items-center space-x-fib3">
            <input
              type="checkbox"
              checked={formData.include_attributions}
              onChange={(e) => setFormData({ ...formData, include_attributions: e.target.checked })}
              className="rounded border-slate-300 text-primary-500 focus:ring-primary-500"
            />
            <span className="text-sm text-slate-700">Include Attributions</span>
          </label>
          
          <label className="flex items-center space-x-fib3">
            <input
              type="checkbox"
              checked={formData.watermark}
              onChange={(e) => setFormData({ ...formData, watermark: e.target.checked })}
              className="rounded border-slate-300 text-primary-500 focus:ring-primary-500"
            />
            <span className="text-sm text-slate-700">Add Watermark</span>
          </label>
        </div>

        <button
          type="submit"
          className="w-full bg-primary-500 text-white py-fib3 px-fib4 rounded-fib2 hover:bg-primary-600 transition-colors duration-fib2"
        >
          Generate PDF Report
        </button>
      </form>
    </div>
  )
}
