'use client';

import React from 'react';
import { useCycleDeleveraging } from '@/lib/queries';

interface CycleDeleveragingProps {
  portfolioId?: string;
}

export function CycleDeleveraging({ portfolioId = 'main-portfolio' }: CycleDeleveragingProps) {
  // Fetch cycle deleveraging data using React Query
  const { 
    data: deleveragingData, 
    isLoading, 
    error, 
    refetch 
  } = useCycleDeleveraging(portfolioId);

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Cycle Deleveraging Scenarios</h1>
          <p className="text-slate-600 dark:text-slate-400">Loading deleveraging analysis...</p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-slate-500">Loading deleveraging data...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Cycle Deleveraging Scenarios</h1>
          <p className="text-slate-600 dark:text-slate-400">Error loading deleveraging analysis</p>
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
                Error loading deleveraging
              </h3>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                {error.message || 'Failed to load cycle deleveraging data'}
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
  const scenarios = deleveragingData?.result?.scenarios || [];
  const currentCycle = deleveragingData?.result?.current_cycle || {};
  const deleveragingRisk = deleveragingData?.result?.deleveraging_risk || {};
  const portfolioImpact = deleveragingData?.result?.portfolio_impact || {};

  return (
    <div className="max-w-7xl mx-auto px-8 py-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Cycle Deleveraging Scenarios</h1>
        <p className="text-slate-600 dark:text-slate-400">Economic cycle deleveraging scenario analysis</p>
      </div>

      {/* Current Cycle Status */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 mb-8">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Current Cycle Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {currentCycle.phase || 'Unknown'}
            </div>
            <div className="text-sm text-slate-600 dark:text-slate-400">Current Phase</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {currentCycle.confidence ? `${(currentCycle.confidence * 100).toFixed(1)}%` : 'N/A'}
            </div>
            <div className="text-sm text-slate-600 dark:text-slate-400">Confidence</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {currentCycle.duration || 'N/A'}
            </div>
            <div className="text-sm text-slate-600 dark:text-slate-400">Duration</div>
          </div>
        </div>
      </div>

      {/* Deleveraging Risk Assessment */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 mb-8">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Deleveraging Risk Assessment</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">Risk Level</h3>
            <div className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
              deleveragingRisk.level === 'High' 
                ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                : deleveragingRisk.level === 'Medium'
                ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                : 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
            }`}>
              {deleveragingRisk.level || 'Unknown'}
            </div>
          </div>
          <div>
            <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">Risk Score</h3>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {deleveragingRisk.score ? deleveragingRisk.score.toFixed(1) : 'N/A'}/10
            </div>
          </div>
        </div>
        {deleveragingRisk.factors && (
          <div className="mt-4">
            <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Key Risk Factors:</h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-slate-600 dark:text-slate-400">
              {deleveragingRisk.factors.map((factor: string, index: number) => (
                <li key={index}>{factor}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Scenarios */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 mb-8">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Deleveraging Scenarios</h2>
        <div className="space-y-4">
          {scenarios.map((scenario: any, index: number) => (
            <div key={index} className="border border-slate-200 dark:border-slate-600 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-slate-900 dark:text-white">{scenario.name}</h3>
                <div className="flex items-center space-x-4">
                  <div className="text-sm text-slate-600 dark:text-slate-400">
                    Probability: {scenario.probability ? `${(scenario.probability * 100).toFixed(1)}%` : 'N/A'}
                  </div>
                  <div className={`px-2 py-1 rounded text-sm font-medium ${
                    scenario.severity === 'High' 
                      ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                      : scenario.severity === 'Medium'
                      ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                      : 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                  }`}>
                    {scenario.severity || 'Unknown'}
                  </div>
                </div>
              </div>
              <p className="text-slate-600 dark:text-slate-400 mb-3">
                {scenario.description}
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-slate-600 dark:text-slate-400">Duration:</span>
                  <span className="ml-2 font-medium text-slate-900 dark:text-white">
                    {scenario.duration || 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-600 dark:text-slate-400">Portfolio Impact:</span>
                  <span className="ml-2 font-medium text-slate-900 dark:text-white">
                    {scenario.portfolio_impact ? `${(scenario.portfolio_impact * 100).toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-600 dark:text-slate-400">Market Impact:</span>
                  <span className="ml-2 font-medium text-slate-900 dark:text-white">
                    {scenario.market_impact ? `${(scenario.market_impact * 100).toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-600 dark:text-slate-400">Recovery Time:</span>
                  <span className="ml-2 font-medium text-slate-900 dark:text-white">
                    {scenario.recovery_time || 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Portfolio Impact Analysis */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Portfolio Impact Analysis</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {portfolioImpact.expected_loss ? `${(portfolioImpact.expected_loss * 100).toFixed(1)}%` : 'N/A'}
            </div>
            <div className="text-sm text-slate-600 dark:text-slate-400">Expected Loss</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {portfolioImpact.worst_case ? `${(portfolioImpact.worst_case * 100).toFixed(1)}%` : 'N/A'}
            </div>
            <div className="text-sm text-slate-600 dark:text-slate-400">Worst Case</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {portfolioImpact.var_95 ? `${(portfolioImpact.var_95 * 100).toFixed(1)}%` : 'N/A'}
            </div>
            <div className="text-sm text-slate-600 dark:text-slate-400">VaR 95%</div>
          </div>
        </div>
      </div>

      {/* No Data State */}
      {scenarios.length === 0 && (
        <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-8 text-center">
          <p className="text-slate-500 dark:text-slate-400">No deleveraging scenarios available</p>
        </div>
      )}
    </div>
  );
}
