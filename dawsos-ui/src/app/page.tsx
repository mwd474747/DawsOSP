'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useCurrentUser } from '@/lib/queries';

export default function HomePage() {
  const { data: user, isLoading } = useCurrentUser();

  const features = [
    {
      name: 'Portfolio Overview',
      description: 'Comprehensive portfolio snapshot with performance metrics and attribution analysis',
      href: '/portfolio',
      icon: '📊',
      color: 'bg-blue-500'
    },
    {
      name: 'Macro Dashboard',
      description: 'Economic cycle detection and regime analysis with market indicators',
      href: '/macro',
      icon: '🌍',
      color: 'bg-green-500'
    },
    {
      name: 'Holdings Detail',
      description: 'Detailed analysis of individual holdings with fundamentals and technicals',
      href: '/holdings',
      icon: '📈',
      color: 'bg-purple-500'
    },
    {
      name: 'Scenarios',
      description: 'Portfolio stress testing and scenario analysis with risk assessment',
      href: '/scenarios',
      icon: '🎯',
      color: 'bg-orange-500'
    },
    {
      name: 'Alerts',
      description: 'Real-time market alerts and portfolio monitoring with notifications',
      href: '/alerts',
      icon: '🔔',
      color: 'bg-red-500'
    },
    {
      name: 'Reports',
      description: 'Comprehensive portfolio reports with PDF generation and export',
      href: '/reports',
      icon: '📄',
      color: 'bg-indigo-500'
    },
    {
      name: 'Buffett Checklist',
      description: 'Warren Buffett investment criteria analysis and quality assessment',
      href: '/buffett-checklist',
      icon: '📋',
      color: 'bg-yellow-500'
    },
    {
      name: 'Policy Rebalance',
      description: 'Portfolio rebalancing recommendations and execution strategies',
      href: '/policy-rebalance',
      icon: '⚖️',
      color: 'bg-teal-500'
    },
    {
      name: 'Cycle Deleveraging',
      description: 'Economic cycle deleveraging scenario analysis and risk assessment',
      href: '/cycle-deleveraging',
      icon: '🔄',
      color: 'bg-cyan-500'
    },
    {
      name: 'Holding Deep Dive',
      description: 'Detailed analysis of individual holdings with fundamentals and technicals',
      href: '/holding-deep-dive',
      icon: '🔍',
      color: 'bg-pink-500'
    }
  ];

  // Don't show loading for user query since it's disabled by default

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
            Welcome to DawsOS
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 mb-2">
            Professional Portfolio Intelligence Platform
          </p>
          {user && (
            <p className="text-lg text-slate-500 dark:text-slate-500">
              Hello, {user.email} ({user.role})
            </p>
          )}
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <Link key={feature.name} href={feature.href} className="group">
              <Card className="h-full hover:shadow-lg transition-shadow duration-200">
                <CardHeader>
                  <div className="flex items-center mb-4">
                    <div className={`w-12 h-12 ${feature.color} rounded-lg flex items-center justify-center mr-4`}>
                      <span className="text-white text-xl">{feature.icon}</span>
                    </div>
                    <CardTitle className="text-xl">{feature.name}</CardTitle>
                  </div>
                  <CardDescription className="text-slate-600 dark:text-slate-400">
                    {feature.description}
                  </CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>

        {/* Status */}
        <div className="mt-12 text-center">
          <Card className="max-w-2xl mx-auto">
            <CardHeader>
              <CardTitle>System Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="flex items-center justify-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                  Backend API: Online
                </div>
                <div className="flex items-center justify-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                  Database: Connected
                </div>
                <div className="flex items-center justify-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                  Authentication: Active
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}