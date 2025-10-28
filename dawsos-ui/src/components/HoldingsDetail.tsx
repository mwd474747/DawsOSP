'use client'

import { BuffettRatingCard } from './BuffettRatingCard'
import { PositionDetails } from './PositionDetails'
import { FundamentalsTable } from './FundamentalsTable'

export function HoldingsDetail() {
  const selectedHolding = {
    symbol: 'AAPL',
    name: 'Apple Inc.',
    quantity: 150,
    market_value: 23450.00,
    cost_basis: 21000.00,
    unrealized_pnl: 2450.00,
    weight: 18.8,
    currency: 'USD',
  }

  const buffettRating = {
    security_id: 'AAPL',
    symbol: 'AAPL',
    dividend_safety: 8.5,
    moat_strength: 9.2,
    resilience: 7.8,
    overall_score: 8.5,
    recommendation: 'buy' as const,
    rationale: 'Exceptional moat strength with strong brand loyalty and ecosystem lock-in. Dividend safety is excellent with consistent growth. Resilience score reflects cyclical exposure to consumer spending.',
  }

  const fundamentals = [
    { metric: 'P/E Ratio', value: 28.5, benchmark: 22.3, status: 'above' },
    { metric: 'P/B Ratio', value: 8.2, benchmark: 3.1, status: 'above' },
    { metric: 'ROE', value: 28.9, benchmark: 15.2, status: 'above' },
    { metric: 'ROA', value: 12.4, benchmark: 8.7, status: 'above' },
    { metric: 'Debt/Equity', value: 0.15, benchmark: 0.35, status: 'below' },
    { metric: 'Current Ratio', value: 1.8, benchmark: 1.5, status: 'above' },
    { metric: 'Dividend Yield', value: 0.5, benchmark: 2.1, status: 'below' },
    { metric: 'EPS Growth (5Y)', value: 12.3, benchmark: 8.9, status: 'above' },
  ]

  const positionHistory = [
    { date: '2024-01-15', action: 'Buy', quantity: 50, price: 185.50, total: 9275.00 },
    { date: '2024-03-22', action: 'Buy', quantity: 50, price: 168.20, total: 8410.00 },
    { date: '2024-06-10', action: 'Buy', quantity: 50, price: 192.30, total: 9615.00 },
  ]

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
