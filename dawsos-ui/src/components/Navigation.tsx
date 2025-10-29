'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { useLogout } from '@/lib/queries';
import { LogOutIcon, MenuIcon } from 'lucide-react';

export function Navigation() {
  const pathname = usePathname();
  const logoutMutation = useLogout();

  const navigationItems = [
    { name: 'Dashboard', href: '/', icon: '🏠' },
    { name: 'Portfolio', href: '/portfolio', icon: '📊' },
    { name: 'Macro', href: '/macro', icon: '🌍' },
    { name: 'Holdings', href: '/holdings', icon: '📈' },
    { name: 'Scenarios', href: '/scenarios', icon: '🎯' },
    { name: 'Alerts', href: '/alerts', icon: '🔔' },
    { name: 'Reports', href: '/reports', icon: '📄' },
    { name: 'Buffett Checklist', href: '/buffett-checklist', icon: '📋' },
    { name: 'Policy Rebalance', href: '/policy-rebalance', icon: '⚖️' },
    { name: 'Cycle Deleveraging', href: '/cycle-deleveraging', icon: '🔄' },
    { name: 'Holding Deep Dive', href: '/holding-deep-dive', icon: '🔍' },
  ];

  const handleLogout = async () => {
    try {
      await logoutMutation.mutateAsync();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <nav className="bg-white dark:bg-slate-800 shadow-sm border-b border-slate-200 dark:border-slate-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <Link href="/" className="flex-shrink-0 flex items-center">
              <span className="text-2xl font-bold text-slate-900 dark:text-white">
                DawsOS
              </span>
            </Link>
            <div className="hidden sm:-my-px sm:ml-6 sm:flex sm:space-x-8">
              {navigationItems.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                    pathname === item.href
                      ? 'border-blue-500 text-slate-900 dark:text-white'
                      : 'border-transparent text-slate-500 dark:text-slate-400 hover:border-slate-300 hover:text-slate-700 dark:hover:text-slate-300'
                  }`}
                >
                  <span className="mr-2">{item.icon}</span>
                  {item.name}
                </Link>
              ))}
            </div>
          </div>
          <div className="hidden sm:ml-6 sm:flex sm:items-center">
            <Button 
              onClick={handleLogout} 
              variant="ghost" 
              className="text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300"
              disabled={logoutMutation.isPending}
            >
              <LogOutIcon className="h-5 w-5 mr-2" />
              {logoutMutation.isPending ? 'Logging out...' : 'Logout'}
            </Button>
          </div>
          <div className="-mr-2 flex items-center sm:hidden">
            <Button variant="ghost" size="icon">
              <MenuIcon className="h-6 w-6" />
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
}
