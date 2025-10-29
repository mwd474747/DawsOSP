'use client';

import React from 'react';
import { useBuffettChecklist } from '@/lib/queries';

interface BuffettChecklistProps {
  portfolioId?: string;
}

export function BuffettChecklist({ portfolioId = 'main-portfolio' }: BuffettChecklistProps) {
  // Fetch Buffett checklist data using React Query
  const { 
    data: checklistData, 
    isLoading, 
    error, 
    refetch 
  } = useBuffettChecklist(portfolioId);

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Buffett Quality Checklist</h1>
          <p className="text-slate-600 dark:text-slate-400">Loading checklist analysis...</p>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-slate-500">Loading checklist data...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Buffett Quality Checklist</h1>
          <p className="text-slate-600 dark:text-slate-400">Error loading checklist analysis</p>
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
                Error loading checklist
              </h3>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                {error.message || 'Failed to load Buffett checklist data'}
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
  const checklist = checklistData?.result?.checklist || [];
  const overallScore = checklistData?.result?.overall_score || 0;
  const recommendations = checklistData?.result?.recommendations || [];

  return (
    <div className="max-w-7xl mx-auto px-8 py-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">Buffett Quality Checklist</h1>
        <p className="text-slate-600 dark:text-slate-400">Warren Buffett's investment criteria analysis</p>
      </div>

      {/* Overall Score */}
      <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700 mb-8">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Overall Quality Score</h2>
        <div className="flex items-center">
          <div className="text-4xl font-bold text-slate-900 dark:text-white mr-4">
            {overallScore.toFixed(1)}/10
          </div>
          <div className="flex-1">
            <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-3">
              <div 
                className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                style={{ width: `${(overallScore / 10) * 100}%` }}
              ></div>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
              Based on Warren Buffett's investment criteria
            </p>
          </div>
        </div>
      </div>

      {/* Checklist Items */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {checklist.map((item: any, index: number) => (
          <div key={index} className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                {item.criteria}
              </h3>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                item.score >= 8 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                  : item.score >= 6
                  ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                  : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
              }`}>
                {item.score.toFixed(1)}/10
              </div>
            </div>
            <p className="text-slate-600 dark:text-slate-400 mb-4">
              {item.description}
            </p>
            <div className="space-y-2">
              {item.details?.map((detail: any, detailIndex: number) => (
                <div key={detailIndex} className="flex items-center text-sm">
                  <div className={`w-2 h-2 rounded-full mr-3 ${
                    detail.passed 
                      ? 'bg-green-500' 
                      : 'bg-red-500'
                  }`}></div>
                  <span className={detail.passed ? 'text-slate-700 dark:text-slate-300' : 'text-slate-500 dark:text-slate-400'}>
                    {detail.description}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="bg-white dark:bg-slate-800 rounded-lg p-6 shadow-sm border border-slate-200 dark:border-slate-700">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">Recommendations</h2>
          <div className="space-y-4">
            {recommendations.map((rec: any, index: number) => (
              <div key={index} className="flex items-start">
                <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-sm font-medium mr-3 mt-0.5">
                  {index + 1}
                </div>
                <div>
                  <h3 className="font-medium text-slate-900 dark:text-white mb-1">
                    {rec.title}
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400">
                    {rec.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Data State */}
      {checklist.length === 0 && (
        <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-8 text-center">
          <p className="text-slate-500 dark:text-slate-400">No checklist data available</p>
        </div>
      )}
    </div>
  );
}
