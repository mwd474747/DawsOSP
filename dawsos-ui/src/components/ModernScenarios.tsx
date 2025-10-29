'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, Cell, Legend, PieChart, Pie
} from 'recharts'
import { 
  TrendingDown, TrendingUp, Activity, AlertCircle, 
  Shield, DollarSign, Zap, Cloud, Sun, CloudRain,
  ChevronRight, Plus, Minus, Settings, PlayCircle
} from 'lucide-react'
import { useScenarios } from '@/lib/queries'
import { cn } from '@/lib/utils'

interface ScenariosProps {
  portfolioId?: string;
}

interface Scenario {
  id: string;
  name: string;
  description: string;
  probability: number;
  impact: number;
  regime: string;
  factors: string[];
  portfolio_impact: number;
  duration_months: number;
}

const scenarioIcons: Record<string, any> = {
  'market_crash': CloudRain,
  'interest_rate_spike': Zap,
  'inflation_surge': TrendingUp,
  'soft_landing': Cloud,
  'economic_boom': Sun
}

const scenarioColors: Record<string, string> = {
  'market_crash': 'from-red-500 to-red-600',
  'interest_rate_spike': 'from-orange-500 to-orange-600',
  'inflation_surge': 'from-amber-500 to-amber-600',
  'soft_landing': 'from-blue-500 to-blue-600',
  'economic_boom': 'from-green-500 to-green-600'
}

export function ModernScenarios({ portfolioId = 'main-portfolio' }: ScenariosProps) {
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null)
  const [isSimulating, setIsSimulating] = useState(false)
  const { data: scenariosData, isLoading, error, refetch } = useScenarios(portfolioId)

  // Loading state with beautiful skeleton
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(4)].map((_, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="glass-card p-6"
            >
              <div className="skeleton h-6 w-3/4 mb-4" />
              <div className="skeleton h-12 w-1/2 mb-4" />
              <div className="space-y-2">
                <div className="skeleton h-4 w-full" />
                <div className="skeleton h-4 w-5/6" />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    )
  }

  // Error state with retry
  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-card p-8 text-center"
      >
        <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-slate-900 mb-2">Error Loading Scenarios</h3>
        <p className="text-slate-600 mb-6">
          {error instanceof Error ? error.message : 'Failed to load scenario data'}
        </p>
        <button onClick={() => refetch()} className="btn-primary">
          Retry
        </button>
      </motion.div>
    )
  }

  const scenarios = scenariosData?.result?.scenarios || []
  const metrics = scenariosData?.result?.portfolio_metrics || {}
  const hedges = scenariosData?.result?.hedge_suggestions || []

  // Prepare chart data
  const impactData = scenarios.map((s: Scenario) => ({
    name: s.name.replace(' Scenario', ''),
    probability: s.probability * 100,
    impact: Math.abs(s.portfolio_impact * 100),
    expected: s.probability * s.portfolio_impact * 100
  }))

  const radarData = scenarios.map((s: Scenario) => ({
    scenario: s.name.split(' ')[0],
    probability: s.probability * 100,
    impact: Math.abs(s.impact * 100),
    duration: (s.duration_months / 36) * 100
  }))

  const runSimulation = () => {
    setIsSimulating(true)
    setTimeout(() => {
      setIsSimulating(false)
    }, 3000)
  }

  return (
    <div className="space-y-6">
      {/* Scenario Cards Grid */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6"
      >
        {scenarios.map((scenario: Scenario, index: number) => {
          const Icon = scenarioIcons[scenario.id] || Activity
          const gradientClass = scenarioColors[scenario.id] || 'from-gray-500 to-gray-600'
          
          return (
            <motion.div
              key={scenario.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
              onClick={() => setSelectedScenario(scenario)}
              className="glass-card-hover p-6 cursor-pointer relative overflow-hidden group"
            >
              {/* Background Gradient */}
              <div className={cn(
                "absolute inset-0 bg-gradient-to-br opacity-5 group-hover:opacity-10 transition-opacity",
                gradientClass
              )} />
              
              {/* Content */}
              <div className="relative">
                <div className="flex items-start justify-between mb-4">
                  <div className={cn(
                    "p-3 rounded-glass bg-gradient-to-br text-white shadow-lg",
                    gradientClass
                  )}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className={cn(
                    "px-3 py-1 rounded-full text-xs font-medium",
                    scenario.portfolio_impact < 0 ? 'badge-danger' : 'badge-success'
                  )}>
                    {(scenario.portfolio_impact * 100).toFixed(1)}%
                  </span>
                </div>
                
                <h3 className="text-lg font-semibold text-slate-900 mb-2">{scenario.name}</h3>
                <p className="text-sm text-slate-600 mb-4">{scenario.description}</p>
                
                {/* Metrics */}
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-500">Probability</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${scenario.probability * 100}%` }}
                          transition={{ duration: 1, delay: index * 0.1 }}
                          className="h-full bg-gradient-to-r from-blue-400 to-blue-600"
                        />
                      </div>
                      <span className="text-xs font-medium">{(scenario.probability * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-500">Impact</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.abs(scenario.impact) * 100}%` }}
                          transition={{ duration: 1, delay: index * 0.1 + 0.2 }}
                          className={cn(
                            "h-full",
                            scenario.impact < 0 
                              ? "bg-gradient-to-r from-red-400 to-red-600"
                              : "bg-gradient-to-r from-green-400 to-green-600"
                          )}
                        />
                      </div>
                      <span className="text-xs font-medium">{(Math.abs(scenario.impact) * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-500">Duration</span>
                    <span className="text-xs font-medium">{scenario.duration_months} months</span>
                  </div>
                </div>
                
                {/* Factors */}
                <div className="mt-4 flex flex-wrap gap-2">
                  {scenario.factors.slice(0, 3).map((factor, i) => (
                    <span key={i} className="px-2 py-1 bg-slate-100 text-slate-700 text-xs rounded-full">
                      {factor}
                    </span>
                  ))}
                </div>
              </div>
            </motion.div>
          )
        })}
      </motion.div>

      {/* Interactive Charts Section */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Impact vs Probability Chart */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="chart-container"
        >
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Impact vs Probability</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={impactData}>
              <defs>
                <linearGradient id="colorProbability" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorImpact" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '12px',
                  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Area 
                type="monotone" 
                dataKey="probability" 
                stroke="#3b82f6" 
                fillOpacity={1} 
                fill="url(#colorProbability)" 
                strokeWidth={2}
              />
              <Area 
                type="monotone" 
                dataKey="impact" 
                stroke="#ef4444" 
                fillOpacity={1} 
                fill="url(#colorImpact)" 
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Scenario Radar Chart */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="chart-container"
        >
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Scenario Analysis Radar</h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="scenario" tick={{ fontSize: 12 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
              <Radar name="Probability" dataKey="probability" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} strokeWidth={2} />
              <Radar name="Impact" dataKey="impact" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} strokeWidth={2} />
              <Radar name="Duration" dataKey="duration" stroke="#10b981" fill="#10b981" fillOpacity={0.3} strokeWidth={2} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '12px'
                }}
              />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Portfolio Impact Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-6"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-semibold text-slate-900">Portfolio Impact Summary</h3>
          <button
            onClick={runSimulation}
            disabled={isSimulating}
            className="btn-primary flex items-center gap-2"
          >
            <PlayCircle className="w-4 h-4" />
            {isSimulating ? 'Simulating...' : 'Run Simulation'}
          </button>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <p className="text-sm text-slate-600 mb-1">Portfolio Value</p>
            <p className="text-2xl font-bold text-slate-900">
              ${(metrics.total_portfolio_value / 1000000).toFixed(2)}M
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-600 mb-1">Worst Case</p>
            <p className="text-2xl font-bold text-red-600">
              ${(metrics.worst_case_loss / 1000).toFixed(0)}K
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-600 mb-1">Best Case</p>
            <p className="text-2xl font-bold text-green-600">
              +${(metrics.best_case_gain / 1000).toFixed(0)}K
            </p>
          </div>
          <div>
            <p className="text-sm text-slate-600 mb-1">VaR (95%)</p>
            <p className="text-2xl font-bold text-amber-600">
              {(metrics.var_95 * 100).toFixed(1)}%
            </p>
          </div>
        </div>

        {/* Animated Progress Bars */}
        {isSimulating && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-6 space-y-3"
          >
            {scenarios.map((scenario: Scenario, i: number) => (
              <div key={scenario.id} className="flex items-center gap-4">
                <span className="text-sm text-slate-600 w-32">{scenario.name}</span>
                <div className="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: '100%' }}
                    transition={{ duration: 2, delay: i * 0.2 }}
                    className={cn(
                      "h-full",
                      scenario.portfolio_impact < 0 
                        ? "bg-gradient-to-r from-red-400 to-red-600"
                        : "bg-gradient-to-r from-green-400 to-green-600"
                    )}
                  />
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </motion.div>

      {/* Hedge Suggestions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-6"
      >
        <h3 className="text-xl font-semibold text-slate-900 mb-6">Recommended Hedges</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {hedges.map((hedge: any, i: number) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.1 }}
              whileHover={{ scale: 1.05 }}
              className="neumorphic-card p-4"
            >
              <div className="flex items-center gap-3 mb-3">
                <Shield className="w-5 h-5 text-blue-600" />
                <h4 className="font-medium text-slate-900">{hedge.instrument}</h4>
              </div>
              <p className="text-xs text-slate-600 mb-3">{hedge.description}</p>
              <div className="flex justify-between items-center">
                <span className="text-xs text-slate-500">Protection</span>
                <span className="text-sm font-semibold text-green-600">
                  {(hedge.protection * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between items-center mt-2">
                <span className="text-xs text-slate-500">Cost</span>
                <span className="text-sm font-semibold text-slate-900">
                  {hedge.cost_bps} bps
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Selected Scenario Modal */}
      <AnimatePresence>
        {selectedScenario && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedScenario(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-slate-900">{selectedScenario.name}</h2>
                <button
                  onClick={() => setSelectedScenario(null)}
                  className="p-2 hover:bg-slate-100 rounded-full transition-colors"
                >
                  <Plus className="w-5 h-5 rotate-45" />
                </button>
              </div>
              
              <p className="text-slate-600 mb-6">{selectedScenario.description}</p>
              
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-slate-500 mb-2">Key Factors</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedScenario.factors.map((factor, i) => (
                      <span key={i} className="px-3 py-1 bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800 rounded-full text-sm">
                        {factor}
                      </span>
                    ))}
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4">
                  <div className="metric-card p-4">
                    <p className="text-xs text-slate-500 mb-1">Probability</p>
                    <p className="text-xl font-bold text-slate-900">{(selectedScenario.probability * 100).toFixed(0)}%</p>
                  </div>
                  <div className="metric-card p-4">
                    <p className="text-xs text-slate-500 mb-1">Portfolio Impact</p>
                    <p className={cn(
                      "text-xl font-bold",
                      selectedScenario.portfolio_impact < 0 ? "text-red-600" : "text-green-600"
                    )}>
                      {(selectedScenario.portfolio_impact * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="metric-card p-4">
                    <p className="text-xs text-slate-500 mb-1">Duration</p>
                    <p className="text-xl font-bold text-slate-900">{selectedScenario.duration_months}mo</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}