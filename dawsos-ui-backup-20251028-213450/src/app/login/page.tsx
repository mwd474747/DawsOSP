'use client';

import dynamicImport from 'next/dynamic';
import { useEffect, useState } from 'react';

// Dynamically import LoginForm to avoid SSR issues
const LoginForm = dynamicImport(() => import('@/components/LoginForm').then(mod => ({ default: mod.LoginForm })), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-64">
      <div className="text-slate-500">Loading login form...</div>
    </div>
  )
});

// Force dynamic rendering
export const dynamic = 'force-dynamic'

export default function LoginPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-slate-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-slate-900 dark:text-white">
            Sign in to DawsOS
          </h2>
          <p className="mt-2 text-center text-sm text-slate-600 dark:text-slate-400">
            Portfolio Intelligence Platform
          </p>
        </div>
        <LoginForm />
      </div>
    </div>
  );
}
