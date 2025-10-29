'use client';

import dynamicImport from 'next/dynamic';
import { useEffect, useState } from 'react';

// Dynamically import MacroDashboard to avoid SSR issues
const MacroDashboard = dynamicImport(() => import('@/components/MacroDashboard').then(mod => ({ default: mod.MacroDashboard })), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-64">
      <div className="text-slate-500">Loading macro dashboard...</div>
    </div>
  )
});

// Force dynamic rendering
export const dynamic = 'force-dynamic'

export default function MacroPage() {
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
              Macro Dashboard
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              Market regime analysis and economic cycle monitoring
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
            Macro Dashboard
          </h1>
          <p className="text-slate-600 dark:text-slate-400">
            Market regime analysis and economic cycle monitoring
          </p>
        </div>
        
        <MacroDashboard />
      </div>
    </div>
  );
}
