'use client'

import { ReportGenerator } from './ReportGenerator'
import { ReportHistory } from './ReportHistory'

export function Reports() {
  const reports = [
    {
      id: '1',
      portfolio_id: 'main',
      template_name: 'portfolio_summary',
      generated_at: '2025-10-27T14:30:00Z',
      file_size: 2048576,
      download_url: '/reports/portfolio_summary_2025-10-27.pdf',
      attributions: ['Data provided by FMP', 'Analysis by DawsOS'],
      watermark: 'DawsOS Internal Use Only',
    },
    {
      id: '2',
      portfolio_id: 'main',
      template_name: 'buffett_analysis',
      generated_at: '2025-10-26T10:15:00Z',
      file_size: 1536000,
      download_url: '/reports/buffett_analysis_2025-10-26.pdf',
      attributions: ['Data provided by FMP', 'Analysis by DawsOS'],
      watermark: 'DawsOS Internal Use Only',
    },
    {
      id: '3',
      portfolio_id: 'main',
      template_name: 'macro_overview',
      generated_at: '2025-10-25T16:45:00Z',
      file_size: 1024000,
      download_url: '/reports/macro_overview_2025-10-25.pdf',
      attributions: ['Data provided by FRED', 'Analysis by DawsOS'],
      watermark: 'DawsOS Internal Use Only',
    },
  ]

  return (
    <div className="max-w-7xl mx-auto px-fib8 py-fib6">
      {/* Page Header */}
      <div className="mb-fib8">
        <h1 className="text-3xl font-bold text-slate-900 mb-fib2">Reports</h1>
        <p className="text-slate-600">Generate and manage PDF reports with rights enforcement</p>
      </div>

      {/* Report Generator and History Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-fib8 mb-fib8">
        <ReportGenerator />
        <ReportHistory reports={reports} />
      </div>

      {/* Report Templates */}
      <div className="metric-card">
        <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Available Templates</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-fib5">
          <div className="p-fib4 bg-slate-50 rounded-fib3">
            <h4 className="text-sm font-medium text-slate-900 mb-fib2">Portfolio Summary</h4>
            <p className="text-xs text-slate-600 mb-fib3">
              Comprehensive portfolio overview with performance metrics and holdings
            </p>
            <div className="text-xs text-slate-500">
              Includes: KPIs, charts, holdings table, attribution
            </div>
          </div>
          
          <div className="p-fib4 bg-slate-50 rounded-fib3">
            <h4 className="text-sm font-medium text-slate-900 mb-fib2">Buffett Analysis</h4>
            <p className="text-xs text-slate-600 mb-fib3">
              Quality ratings and fundamental analysis for each holding
            </p>
            <div className="text-xs text-slate-500">
              Includes: Ratings, fundamentals, recommendations
            </div>
          </div>
          
          <div className="p-fib4 bg-slate-50 rounded-fib3">
            <h4 className="text-sm font-medium text-slate-900 mb-fib2">Macro Overview</h4>
            <p className="text-xs text-slate-600 mb-fib3">
              Macro regime analysis and scenario impact assessment
            </p>
            <div className="text-xs text-slate-500">
              Includes: Regime, cycles, DaR, scenarios
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
