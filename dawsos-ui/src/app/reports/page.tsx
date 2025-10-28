'use client';

import { Reports } from '@/components/Reports';

// Force dynamic rendering
export const dynamic = 'force-dynamic'

export default function ReportsPage() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
            Reports
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Generate comprehensive PDF reports and export portfolio data
          </p>
        </div>
        
        <Reports portfolioId="main-portfolio" />
      </div>
    </div>
  );
}
