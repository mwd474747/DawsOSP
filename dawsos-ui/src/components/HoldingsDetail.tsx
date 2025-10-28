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

  // Extract data from API response or use defaults
  const selectedHolding = holdingsData?.result?.selected_holding || {
    symbol: 'AAPL',
    name: 'Apple Inc.',
    quantity: 150,
    market_value: 23450.00,
    cost_basis: 21000.00,
    unrealized_pnl: 2450.00,
    weight: 18.8,
    currency: 'USD',
  };

  const buffettRating = holdingsData?.result?.buffett_rating || {
    security_id: 'AAPL',
    symbol: 'AAPL',
    dividend_safety: 8.5,
    moat_strength: 9.2,
    resilience: 7.8,
    overall_score: 8.5,
    recommendation: 'buy' as const,
    rationale: 'Exceptional moat strength with strong brand loyalty and ecosystem lock-in. Dividend safety is excellent with consistent growth. Resilience score reflects cyclical exposure to consumer spending.',
  };

  const fundamentals = holdingsData?.result?.fundamentals || [
    { metric: 'P/E Ratio', value: 28.5, benchmark: 22.3, status: 'above' as const },
    { metric: 'P/B Ratio', value: 8.2, benchmark: 3.1, status: 'above' as const },
    { metric: 'ROE', value: 28.9, benchmark: 15.2, status: 'above' as const },
    { metric: 'ROA', value: 12.4, benchmark: 8.7, status: 'above' as const },
    { metric: 'Debt/Equity', value: 0.15, benchmark: 0.35, status: 'below' as const },
    { metric: 'Current Ratio', value: 1.8, benchmark: 1.5, status: 'above' as const },
    { metric: 'Dividend Yield', value: 0.5, benchmark: 2.1, status: 'below' as const },
    { metric: 'EPS Growth (5Y)', value: 12.3, benchmark: 8.9, status: 'above' as const },
  ];

  const positionHistory = holdingsData?.result?.position_history || [
    { date: '2024-01-15', action: 'Buy', quantity: 50, price: 185.50, total: 9275.00 },
    { date: '2024-03-22', action: 'Buy', quantity: 50, price: 168.20, total: 8410.00 },
    { date: '2024-06-10', action: 'Buy', quantity: 50, price: 192.30, total: 9615.00 },
  ];

  return (
    <div className="max-w-7xl mx-auto px-fib8 py-fib6">
      {/* Page Header */}
      <div className="mb-fib8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 mb-fib2">Holdings Detail</h1>
            <p className="text-slate-600">Buffett quality ratings, position details, and fundamental analysis</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-slate-600">Selected Holding</div>
            <div className="text-xl font-bold text-slate-900">{selectedHolding.symbol}</div>
          </div>
        </div>
      </div>

      {/* Buffett Rating Card */}
      <div className="mb-fib8">
        <BuffettRatingCard rating={buffettRating} />
      </div>

      {/* Position Details and Fundamentals Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-fib8 mb-fib8">
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
