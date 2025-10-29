'use client';

import React, { useState } from 'react';
import { useHoldingDeepDive } from '@/lib/queries';

interface HoldingDeepDiveProps {
  portfolioId?: string;
}

export function HoldingDeepDive({ portfolioId = 'main-portfolio' }: HoldingDeepDiveProps) {
  const [selectedHolding, setSelectedHolding] = useState<string | null>(null);
  
  // Fetch holding deep dive data using React Query
  const { 
    data: deepDiveData, 
    isLoading, 
    error, 
    refetch 
  } = useHoldingDeepDive(portfolioId, selectedHolding || undefined);

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Holding Deep Dive</h1>
          <p className="text-slate-600 dark:text-slate-400">Loading deep dive analysis...</p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-slate-500">Loading deep dive data...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Holding Deep Dive</h1>
          <p className="text-slate-600 dark:text-slate-400">Error loading deep dive analysis</p>
        </div>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
          <div className="flex items-center">
            <div className="text-red-600 dark:text-red-400">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                Error loading deep dive
              </h3>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                {error.message || 'Failed to load holding deep dive data'}
              </p>
              <button
                onClick={() => refetch()}
                className="mt-2 text-sm text-red-600 dark:text-red-400 hover:text-red-500"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Extract data from API response - no mock fallbacks
  const holdings = deepDiveData?.result?.holdings || [];
  const selectedHoldingData = deepDiveData?.result?.selected_holding || null;
  const fundamentals = deepDiveData?.result?.fundamentals || {};
  const technicalAnalysis = deepDiveData?.result?.technical_analysis || {};
  const riskMetrics = deepDiveData?.result?.risk_metrics || {};
  const comparableCompanies = deepDiveData?.result?.comparable_companies || [];

  return (
    <div className="max-w-7xl mx-auto px-8 py-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Holding Deep Dive</h1>
        <p className="text-slate-600 dark:text-slate-400">Detailed analysis of individual holdings</p>
      </div>

      {/* Holdings Selection */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 mb-8">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Select Holding for Analysis</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {holdings.map((holding: any) => (
            <button
              key={holding.security_id}
              onClick={() => setSelectedHolding(holding.security_id)}
              className={`p-4 rounded-lg border text-left transition-colors ${
                selectedHolding === holding.security_id
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-slate-200 dark:border-slate-600 hover:border-slate-300 dark:hover:border-slate-500'
              }`}
            >
              <div className="font-medium text-slate-900 dark:text-white">{holding.symbol}</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">{holding.name}</div>
              <div className="text-sm text-slate-500 dark:text-slate-500">
                {holding.weight ? `${(holding.weight * 100).toFixed(1)}%` : 'N/A'} of portfolio
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Selected Holding Analysis */}
      {selectedHoldingData ? (
        <div className="space-y-8">
          {/* Basic Information */}
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">
              {selectedHoldingData.symbol} - {selectedHoldingData.name}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Current Price</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  ${selectedHoldingData.current_price || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Market Cap</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  {selectedHoldingData.market_cap ? `$${selectedHoldingData.market_cap.toLocaleString()}` : 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Sector</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  {selectedHoldingData.sector || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Weight</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  {selectedHoldingData.weight ? `${(selectedHoldingData.weight * 100).toFixed(1)}%` : 'N/A'}
                </div>
              </div>
            </div>
          </div>

          {/* Fundamentals */}
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Fundamentals</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">P/E Ratio</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  {fundamentals.pe_ratio || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">P/B Ratio</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  {fundamentals.pb_ratio || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">ROE</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  {fundamentals.roe ? `${(fundamentals.roe * 100).toFixed(1)}%` : 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Debt/Equity</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  {fundamentals.debt_to_equity || 'N/A'}
                </div>
              </div>
            </div>
          </div>

          {/* Technical Analysis */}
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Technical Analysis</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">RSI</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  {technicalAnalysis.rsi || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">MACD</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  {technicalAnalysis.macd || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Moving Average</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  {technicalAnalysis.moving_average || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Support Level</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  ${technicalAnalysis.support_level || 'N/A'}
                </div>
              </div>
            </div>
          </div>

          {/* Risk Metrics */}
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Risk Metrics</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Beta</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  {riskMetrics.beta || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Volatility</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  {riskMetrics.volatility ? `${(riskMetrics.volatility * 100).toFixed(1)}%` : 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Sharpe Ratio</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  {riskMetrics.sharpe_ratio || 'N/A'}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-600 dark:text-slate-400">VaR 95%</div>
                <div className="text-lg font-semibold text-slate-900 dark:text-white">
                  {riskMetrics.var_95 ? `${(riskMetrics.var_95 * 100).toFixed(1)}%` : 'N/A'}
                </div>
              </div>
            </div>
          </div>

          {/* Comparable Companies */}
          {comparableCompanies.length > 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Comparable Companies</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-600">
                  <thead>
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Symbol</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">P/E</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Market Cap</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-slate-600">
                    {comparableCompanies.map((company: any, index: number) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900 dark:text-white">
                          {company.symbol}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                          {company.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                          {company.pe_ratio || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500 dark:text-slate-400">
                          {company.market_cap ? `$${company.market_cap.toLocaleString()}` : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-8 text-center">
          <p className="text-slate-500 dark:text-slate-400">Select a holding to view detailed analysis</p>
        </div>
      )}

      {/* No Data State */}
      {holdings.length === 0 && (
        <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-8 text-center">
          <p className="text-slate-500 dark:text-slate-400">No holdings available for analysis</p>
        </div>
      )}
    </div>
  );
}
