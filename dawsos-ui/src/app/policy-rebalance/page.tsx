'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { usePolicyRebalance } from '@/lib/queries';

export default function PolicyRebalancePage() {
  const { data, isLoading, error } = usePolicyRebalance('main-portfolio');

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-slate-600">Loading policy rebalance data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle className="text-red-600">Error Loading Policy Rebalance</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-slate-600">
              {error.message || 'Failed to load policy rebalance data. Please try again.'}
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
            Policy Rebalance
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Portfolio rebalancing recommendations and execution strategies
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Rebalance Analysis</CardTitle>
              <CardDescription>
                Real-time rebalance data from backend API
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {data?.result ? (
                  <div className="space-y-2">
                    <div className="text-sm text-slate-600 dark:text-slate-400">
                      <p><strong>Pattern:</strong> {data.metadata?.pattern_id || 'N/A'}</p>
                      <p><strong>Execution Time:</strong> {data.metadata?.duration_ms ? `${data.metadata.duration_ms}ms` : 'N/A'}</p>
                      <p><strong>Timestamp:</strong> {data.metadata?.timestamp ? new Date(data.metadata.timestamp).toLocaleTimeString() : 'N/A'}</p>
                    </div>
                    <div className="mt-4 p-4 bg-slate-100 dark:bg-slate-800 rounded-lg">
                      <h4 className="font-semibold mb-2">Raw Data:</h4>
                      <pre className="text-xs overflow-auto">
                        {JSON.stringify(data.result, null, 2)}
                      </pre>
                    </div>
                  </div>
                ) : (
                  <p className="text-slate-500">No rebalance data available</p>
                )}
              </div>
            </CardContent>
          </Card>

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
