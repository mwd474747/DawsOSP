'use client';

import dynamicImport from 'next/dynamic';
import { useEffect, useState } from 'react';

// Dynamically import PortfolioOverview to avoid SSR issues
const PortfolioOverview = dynamicImport(() => import('@/components/PortfolioOverview').then(mod => ({ default: mod.PortfolioOverview })), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-64">
      <div className="text-slate-500">Loading portfolio overview...</div>
    </div>
  )
});

// Force dynamic rendering
export const dynamic = 'force-dynamic'

export default function PortfolioPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              Portfolio Overview
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              Comprehensive portfolio analysis and performance metrics
            </p>
          </div>
          <div className="flex items-center justify-center h-64">
            <div className="text-slate-500">Loading...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
            Portfolio Overview
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Comprehensive portfolio analysis and performance metrics
          </p>
        </div>
        
        <PortfolioOverview portfolioId="main-portfolio" />
      </div>
    </div>
  );
}
