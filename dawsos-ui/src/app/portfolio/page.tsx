'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { usePortfolioOverview } from '@/lib/queries';

export default function PortfolioPage() {
  const { data, isLoading, error } = usePortfolioOverview('main-portfolio');

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-slate-600">Loading portfolio data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Error Loading Portfolio</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-slate-600">
              {error.message || 'Failed to load portfolio data. Please try again.'}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
            Portfolio Overview
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Comprehensive portfolio analysis and performance metrics
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Portfolio Performance */}
          <Card>
            <CardHeader>
              <CardTitle>Portfolio Performance</CardTitle>
              <CardDescription>
                Real-time performance metrics from backend API
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {data?.result?.currency_attr?.total_return ? 
                        `${(data.result.currency_attr.total_return * 100).toFixed(2)}%` : 
                        '0.00%'
                      }
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">Total Return</div>
                  </div>
                  <div className="text-center p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {data?.result?.currency_attr?.local_return ? 
                        `${(data.result.currency_attr.local_return * 100).toFixed(2)}%` : 
                        '0.00%'
                      }
                    </div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">Local Return</div>
                  </div>
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400">
                  <p><strong>Portfolio ID:</strong> {data?.result?.currency_attr?.portfolio_id || 'N/A'}</p>
                  <p><strong>Base Currency:</strong> {data?.result?.currency_attr?.base_currency || 'N/A'}</p>
                  <p><strong>As of Date:</strong> {data?.result?.currency_attr?.asof_date || 'N/A'}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Status */}
          <Card>
            <CardHeader>
              <CardTitle>API Status</CardTitle>
              <CardDescription>
                Backend connection and data flow status
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Backend API:</span>
                  <span className="text-green-600">✓ Connected</span>
                </div>
                <div className="flex justify-between">
                  <span>Pattern Execution:</span>
                  <span className="text-green-600">✓ Working</span>
                </div>
                <div className="flex justify-between">
                  <span>Data Freshness:</span>
                  <span className="text-blue-600">
                    {data?.metadata?.timestamp ? 
                      new Date(data.metadata.timestamp).toLocaleTimeString() : 
                      'Unknown'
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Execution Time:</span>
                  <span className="text-blue-600">
                    {data?.metadata?.duration_ms ? 
                      `${data.metadata.duration_ms}ms` : 
                      'Unknown'
                    }
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
