'use client';

import React from 'react';
import { usePolicyRebalance } from '@/lib/queries';

interface PolicyRebalanceProps {
  portfolioId?: string;
}

export function PolicyRebalance({ portfolioId = 'main-portfolio' }: PolicyRebalanceProps) {
  // Fetch policy rebalance data using React Query
  const { 
    data: rebalanceData, 
    isLoading, 
    error, 
    refetch 
  } = usePolicyRebalance(portfolioId);

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Policy Rebalance</h1>
          <p className="text-slate-600 dark:text-slate-400">Loading rebalancing analysis...</p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-slate-500">Loading rebalance data...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Policy Rebalance</h1>
          <p className="text-slate-600 dark:text-slate-400">Error loading rebalancing analysis</p>
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
                Error loading rebalance
              </h3>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                {error.message || 'Failed to load policy rebalance data'}
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
  const rebalanceRecommendations = rebalanceData?.result?.recommendations || [];
  const currentAllocation = rebalanceData?.result?.current_allocation || {};
  const targetAllocation = rebalanceData?.result?.target_allocation || {};
  const driftAnalysis = rebalanceData?.result?.drift_analysis || {};
  const executionPlan = rebalanceData?.result?.execution_plan || {};

  return (
    <div className="max-w-7xl mx-auto px-8 py-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Policy Rebalance</h1>
        <p className="text-slate-600 dark:text-slate-400">Portfolio rebalancing recommendations and execution</p>
      </div>

      {/* Drift Analysis */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 mb-8">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Portfolio Drift Analysis</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {driftAnalysis.total_drift ? `${(driftAnalysis.total_drift * 100).toFixed(1)}%` : 'N/A'}
            </div>
            <div className="text-sm text-slate-600 dark:text-slate-400">Total Drift</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {driftAnalysis.max_drift ? `${(driftAnalysis.max_drift * 100).toFixed(1)}%` : 'N/A'}
            </div>
            <div className="text-sm text-slate-600 dark:text-slate-400">Max Single Drift</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {driftAnalysis.rebalance_threshold ? `${(driftAnalysis.rebalance_threshold * 100).toFixed(1)}%` : 'N/A'}
            </div>
            <div className="text-sm text-slate-600 dark:text-slate-400">Rebalance Threshold</div>
          </div>
        </div>
      </div>

      {/* Allocation Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Current Allocation</h3>
          <div className="space-y-3">
            {Object.entries(currentAllocation).map(([asset, allocation]) => (
              <div key={asset} className="flex justify-between items-center">
                <span className="text-slate-700 dark:text-slate-300">{asset}</span>
                <span className="font-medium text-slate-900 dark:text-white">
                  {typeof allocation === 'number' ? `${(allocation * 100).toFixed(1)}%` : 'N/A'}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Target Allocation</h3>
          <div className="space-y-3">
            {Object.entries(targetAllocation).map(([asset, allocation]) => (
              <div key={asset} className="flex justify-between items-center">
                <span className="text-slate-700 dark:text-slate-300">{asset}</span>
                <span className="font-medium text-slate-900 dark:text-white">
                  {typeof allocation === 'number' ? `${(allocation * 100).toFixed(1)}%` : 'N/A'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Rebalance Recommendations */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 mb-8">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Rebalance Recommendations</h2>
        <div className="space-y-4">
          {rebalanceRecommendations.map((rec: any, index: number) => (
            <div key={index} className="border border-slate-200 dark:border-slate-600 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-slate-900 dark:text-white">{rec.security}</h3>
                <div className={`px-2 py-1 rounded text-sm font-medium ${
                  rec.action === 'BUY' 
                    ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                    : rec.action === 'SELL'
                    ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                    : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                }`}>
                  {rec.action}
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-slate-600 dark:text-slate-400">Current:</span>
                  <span className="ml-2 font-medium text-slate-900 dark:text-white">
                    {rec.current_weight ? `${(rec.current_weight * 100).toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-600 dark:text-slate-400">Target:</span>
                  <span className="ml-2 font-medium text-slate-900 dark:text-white">
                    {rec.target_weight ? `${(rec.target_weight * 100).toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-600 dark:text-slate-400">Amount:</span>
                  <span className="ml-2 font-medium text-slate-900 dark:text-white">
                    {rec.amount ? `$${rec.amount.toLocaleString()}` : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-600 dark:text-slate-400">Shares:</span>
                  <span className="ml-2 font-medium text-slate-900 dark:text-white">
                    {rec.shares ? rec.shares.toLocaleString() : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Execution Plan */}
      {executionPlan.steps && executionPlan.steps.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Execution Plan</h2>
          <div className="space-y-4">
            {executionPlan.steps.map((step: any, index: number) => (
              <div key={index} className="flex items-start">
                <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-sm font-medium mr-3 mt-0.5">
                  {index + 1}
                </div>
                <div>
                  <h3 className="font-medium text-slate-900 dark:text-white mb-1">
                    {step.action}
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400">
                    {step.description}
                  </p>
                  {step.estimated_cost && (
                    <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                      Estimated cost: ${step.estimated_cost.toLocaleString()}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Data State */}
      {rebalanceRecommendations.length === 0 && (
        <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-8 text-center">
          <p className="text-slate-500 dark:text-slate-400">No rebalance recommendations available</p>
        </div>
      )}
    </div>
  );
}
