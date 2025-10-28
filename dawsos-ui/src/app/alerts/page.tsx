'use client';

import { Alerts } from '@/components/Alerts';

// Force dynamic rendering
export const dynamic = 'force-dynamic'

export default function AlertsPage() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto px-8 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
            Alerts
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Real-time alert management and risk monitoring
          </p>
        </div>
        
        <Alerts portfolioId="main-portfolio" />
      </div>
    </div>
  );
}
