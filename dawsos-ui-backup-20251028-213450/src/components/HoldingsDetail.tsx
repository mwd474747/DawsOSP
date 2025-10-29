'use client'

import { BuffettRatingCard } from './BuffettRatingCard'
import { PositionDetails } from './PositionDetails'
import { FundamentalsTable } from './FundamentalsTable'
import { useHoldingsDetail } from '@/lib/queries'

interface HoldingsDetailProps {
  portfolioId?: string;
}

export function HoldingsDetail({ portfolioId = 'main-portfolio' }: HoldingsDetailProps) {
  // Fetch holdings data using React Query
  const { 
    data: holdingsData, 
    isLoading, 
    error, 
    refetch 
  } = useHoldingsDetail(portfolioId);

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Holdings Detail</h1>
          <p className="text-slate-600 dark:text-slate-400">Loading holdings data...</p>
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
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Holdings Detail</h1>
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <p className="text-red-800 dark:text-red-200 font-medium">Error loading holdings data</p>
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

  // Extract data from API response - no mock fallbacks
  const selectedHolding = holdingsData?.result?.selected_holding || null;
  const buffettRating = holdingsData?.result?.buffett_rating || null;
  const fundamentals = holdingsData?.result?.fundamentals || [];
  const positionHistory = holdingsData?.result?.position_history || [];

  // Show no data state if no holding selected
  if (!selectedHolding) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Holdings Detail</h1>
          <p className="text-slate-600 dark:text-slate-400">No holding selected for analysis</p>
        </div>
        <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-8 text-center">
          <p className="text-slate-500 dark:text-slate-400">Select a holding from the portfolio overview to view detailed analysis</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-8 py-6">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Holdings Detail</h1>
            <p className="text-slate-600 dark:text-slate-400">Buffett quality ratings, position details, and fundamental analysis</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-slate-600 dark:text-slate-400">Selected Holding</div>
            <div className="text-xl font-bold text-slate-900 dark:text-white">{selectedHolding.symbol}</div>
          </div>
        </div>
      </div>

      {/* Buffett Rating Card */}
      {buffettRating && (
        <div className="mb-8">
          <BuffettRatingCard rating={buffettRating} />
        </div>
      )}

      {/* Position Details and Fundamentals Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <PositionDetails 
          holding={selectedHolding}
          history={positionHistory}
        />
        <FundamentalsTable 
          fundamentals={fundamentals}
          symbol={selectedHolding.symbol}
        />
      </div>

      {/* Additional Analysis Placeholders */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-fib8">
        <div className="metric-card">
          <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Technical Analysis</h3>
          <div className="h-48 flex items-center justify-center bg-slate-50 rounded-fib3">
            <p className="text-slate-500">Price Chart (Coming Soon)</p>
          </div>
        </div>
        
        <div className="metric-card">
          <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Peer Comparison</h3>
          <div className="h-48 flex items-center justify-center bg-slate-50 rounded-fib3">
            <p className="text-slate-500">Peer Metrics (Coming Soon)</p>
          </div>
        </div>
        
        <div className="metric-card">
          <h3 className="text-lg font-semibold text-slate-900 mb-fib5">Risk Metrics</h3>
          <div className="h-48 flex items-center justify-center bg-slate-50 rounded-fib3">
            <p className="text-slate-500">Risk Analysis (Coming Soon)</p>
          </div>
        </div>
      </div>
    </div>
  )
}
