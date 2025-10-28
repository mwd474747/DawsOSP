'use client';

import { HoldingsDetail } from '@/components/HoldingsDetail';

// Force dynamic rendering
export const dynamic = 'force-dynamic'

export default function HoldingsPage() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
            Holdings Detail
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Detailed analysis of individual holdings and positions
          </p>
        </div>
        
        <HoldingsDetail portfolioId="main-portfolio" />
      </div>
    </div>
  );
}
