'use client'

import { ReportGenerator } from './ReportGenerator'
import { ReportHistory } from './ReportHistory'
import { useReports } from '@/lib/queries'

interface ReportsProps {
  portfolioId?: string;
}

export function Reports({ portfolioId = 'main-portfolio' }: ReportsProps) {
  // Fetch reports data using React Query
  const { 
    data: reportsData, 
    isLoading, 
    error, 
    refetch 
  } = useReports(portfolioId);

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Reports</h1>
          <p className="text-slate-600 dark:text-slate-400">Loading reports data...</p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-3/4 mb-4"></div>
              <div className="h-8 bg-slate-200 rounded w-1/2 mb-2"></div>
              <div className="h-3 bg-slate-200 rounded w-1/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Reports</h1>
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <p className="text-red-800 dark:text-red-200 font-medium">Error loading reports data</p>
            <p className="text-red-600 dark:text-red-300 text-sm mt-2">
              {error instanceof Error ? error.message : 'Unknown error occurred'}
            </p>
            <button 
              onClick={() => refetch()}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Extract data from API response or use defaults
  const reports = reportsData?.result?.reports || [
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
