'use client'

import React from 'react';
import { MetricCard } from './MetricCard'
import { PerformanceChart } from './PerformanceChart'
import { HoldingsTable } from './HoldingsTable'
import { usePortfolioOverview } from '@/lib/queries'
import { demoPortfolioData } from '@/lib/seed-data'

interface PortfolioOverviewProps {
  portfolioId?: string;
}

export function PortfolioOverview({ portfolioId = 'main-portfolio' }: PortfolioOverviewProps) {
  // Fetch portfolio data using React Query
  const { 
    data: portfolioData, 
    isLoading, 
    error, 
    refetch 
  } = usePortfolioOverview(portfolioId);

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-fib8 py-fib6">
        <div className="mb-fib8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-fib2">Portfolio Overview</h1>
          <p className="text-slate-600 dark:text-slate-400">Loading portfolio data...</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-fib5 mb-fib8">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="metric-card animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-3/4 mb-2"></div>
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
      <div className="max-w-7xl mx-auto px-fib8 py-fib6">
        <div className="mb-fib8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-fib2">Portfolio Overview</h1>
          <div className="bg-red-50 border border-red-200 rounded-fib3 p-fib5">
            <p className="text-red-800 font-medium">Error loading portfolio data</p>
            <p className="text-red-600 text-sm mt-fib2">{error.message}</p>
            <button 
              onClick={() => refetch()}
              className="mt-fib3 px-fib4 py-fib2 bg-red-600 text-white rounded-fib2 text-sm hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Extract data from API response
  const result = portfolioData?.result || {};
  const state = portfolioData?.state || {};
  
  // Build metrics from API data - no mock fallbacks
  const metrics = [
    {
      title: 'Total Value',
      value: state.total_value ? `$${state.total_value.toLocaleString()}` : 'No data available',
      change: state.today_change ? `${(state.today_change * 100).toFixed(2)}%` : 'N/A',
      changeType: (state.today_change || 0) >= 0 ? 'profit' as const : 'loss' as const,
      subtitle: 'Today',
    },
    {
      title: 'TWR (1Y)',
      value: state.twr_1y ? `${(state.twr_1y * 100).toFixed(2)}%` : 'No data available',
      change: state.twr_1y_benchmark ? `${(state.twr_1y_benchmark * 100).toFixed(1)}%` : 'N/A',
      changeType: 'profit' as const,
      subtitle: 'vs S&P 500',
    },
    {
      title: 'Sharpe Ratio',
      value: state.sharpe_ratio ? state.sharpe_ratio.toFixed(2) : 'No data available',
      change: state.sharpe_ratio_benchmark ? `${state.sharpe_ratio_benchmark.toFixed(2)}` : 'N/A',
      changeType: 'profit' as const,
      subtitle: 'Risk-adjusted',
    },
    {
      title: 'Max Drawdown',
      value: state.max_drawdown ? `-${(state.max_drawdown * 100).toFixed(2)}%` : 'No data available',
      change: state.max_drawdown_benchmark ? `-${(state.max_drawdown_benchmark * 100).toFixed(1)}%` : 'N/A',
      changeType: 'loss' as const,
      subtitle: 'Peak to trough',
    },
  ];

  // Build holdings from API data - no mock fallbacks
  const holdings = state.holdings || [];

  // Build performance data for chart - no mock fallbacks
  const performanceData = state.performance_data || [];

  return (
    <div className="max-w-7xl mx-auto px-fib8 py-fib6">
      {/* Page Header */}
      <div className="mb-fib8">
        <h1 className="text-3xl font-bold text-slate-900 mb-fib2">Portfolio Overview</h1>
        <p className="text-slate-600">Real-time portfolio analytics and performance metrics</p>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-fib5 mb-fib8">
        {metrics.map((metric, index) => (
          <MetricCard key={index} {...metric} />
        ))}
      </div>

      {/* Charts and Tables Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-fib8 mb-fib8">
        {/* Performance Chart */}
        <div className="metric-card">
          <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Performance</h3>
          <PerformanceChart data={performanceData} />
        </div>

        {/* Allocation Chart */}
        <div className="metric-card">
          <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Asset Allocation</h3>
          <div className="h-64 flex items-center justify-center bg-slate-50 rounded-fib3">
            <p className="text-slate-500">Allocation Chart (Recharts)</p>
          </div>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="metric-card">
        <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Holdings</h3>
        <HoldingsTable holdings={holdings} />
      </div>
    </div>
  )
}
