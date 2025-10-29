'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { 
  TrendingUp, Shield, BarChart3, Briefcase, 
  Bell, FileText, ArrowUpRight, DollarSign,
  Activity, Zap, Globe2, ChartBar
} from 'lucide-react';

// Force dynamic rendering
export const dynamic = 'force-dynamic'

const stats = [
  { label: 'Total Value', value: '$1,234,567', change: '+12.5%', trend: 'up' },
  { label: "Today's P&L", value: '+$12,345', change: '+2.3%', trend: 'up' },
  { label: 'YTD Return', value: '+15.2%', change: '+0.8%', trend: 'up' },
  { label: 'Sharpe Ratio', value: '1.85', change: '+0.12', trend: 'up' },
];

const cards = [
  {
    href: '/portfolio',
    icon: BarChart3,
    title: 'Portfolio Overview',
    description: 'Comprehensive portfolio analysis with KPIs and performance metrics',
    color: 'from-blue-500 to-indigo-600',
    delay: 0.1
  },
  {
    href: '/macro',
    icon: Globe2,
    title: 'Macro Dashboard',
    description: 'Market regime analysis, economic cycles, and factor monitoring',
    color: 'from-green-500 to-emerald-600',
    delay: 0.2
  },
  {
    href: '/holdings',
    icon: Briefcase,
    title: 'Holdings Detail',
    description: 'Detailed holdings analysis with risk metrics and attribution',
    color: 'from-purple-500 to-pink-600',
    delay: 0.3
  },
  {
    href: '/scenarios',
    icon: Shield,
    title: 'Scenarios',
    description: 'Stress testing and what-if analysis for portfolio assessment',
    color: 'from-orange-500 to-red-600',
    delay: 0.4
  },
  {
    href: '/alerts',
    icon: Bell,
    title: 'Alerts',
    description: 'Real-time alert management and risk monitoring system',
    color: 'from-red-500 to-rose-600',
    delay: 0.5
  },
  {
    href: '/reports',
    icon: FileText,
    title: 'Reports',
    description: 'Generate comprehensive PDF reports and export portfolio data',
    color: 'from-indigo-500 to-purple-600',
    delay: 0.6
  }
];

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-full blur-3xl animate-float" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-br from-green-500/10 to-blue-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 right-1/3 w-72 h-72 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '4s' }} />
      </div>

      {/* Main content */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8 py-8">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12"
        >
          <div className="flex justify-center items-center gap-4 mb-4">
            <div className="p-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl shadow-glow">
              <ChartBar className="w-10 h-10 text-white" />
            </div>
          </div>
          <h1 className="text-5xl lg:text-6xl font-bold mb-4">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              DawsOS Portfolio
            </span>
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
              Intelligence
            </span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Advanced portfolio analysis and risk management platform with real-time insights
          </p>
        </motion.div>

        {/* Stats Grid */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-12"
        >
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.1 * index }}
              whileHover={{ scale: 1.02 }}
              className="glass-card-dark p-6 group"
            >
              <div className="flex justify-between items-start mb-2">
                <p className="text-sm text-slate-400">{stat.label}</p>
                {stat.trend === 'up' ? (
                  <TrendingUp className="w-4 h-4 text-green-400" />
                ) : (
                  <Activity className="w-4 h-4 text-blue-400" />
                )}
              </div>
              <p className="text-3xl font-bold text-white mb-1">{stat.value}</p>
              <div className="flex items-center gap-2">
                <span className={`text-sm ${stat.trend === 'up' ? 'text-green-400' : 'text-blue-400'}`}>
                  {stat.change}
                </span>
                <span className="text-xs text-slate-500">24h</span>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Navigation Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cards.map((card) => {
            const Icon = card.icon;
            return (
              <motion.div
                key={card.href}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: card.delay }}
                whileHover={{ scale: 1.03, y: -5 }}
              >
                <Link href={card.href}>
                  <div className="glass-card-dark p-6 h-full group hover:shadow-glow transition-all duration-300">
                    <div className="flex items-start justify-between mb-4">
                      <div className={`p-3 rounded-xl bg-gradient-to-br ${card.color} shadow-lg group-hover:shadow-glow-sm transition-all`}>
                        <Icon className="w-6 h-6 text-white" />
                      </div>
                      <ArrowUpRight className="w-5 h-5 text-slate-500 group-hover:text-white transition-colors" />
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-2 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-blue-400 group-hover:to-purple-400 transition-all">
                      {card.title}
                    </h3>
                    <p className="text-slate-400 group-hover:text-slate-300 transition-colors">
                      {card.description}
                    </p>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </div>

        {/* Quick Actions */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
          className="mt-12 text-center"
        >
          <div className="inline-flex gap-4">
            <button className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full font-semibold hover:shadow-glow-sm transition-all duration-300 hover:scale-105">
              <Zap className="inline-block w-5 h-5 mr-2" />
              Quick Analysis
            </button>
            <button className="px-8 py-3 glass-card-dark text-white rounded-full font-semibold hover:shadow-glow-sm transition-all duration-300 hover:scale-105">
              <DollarSign className="inline-block w-5 h-5 mr-2" />
              Market Overview
            </button>
          </div>
        </motion.div>
      </div>
    </main>
  );
}