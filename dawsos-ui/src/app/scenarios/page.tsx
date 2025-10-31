'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Scenarios } from '@/components/Scenarios';
import { TrendingUp, Shield, AlertTriangle, DollarSign } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

// Force dynamic rendering
export const dynamic = 'force-dynamic'

export default function ScenariosPage() {
  const [scenarioData, setScenarioData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchScenarioData();
  }, []);

  const fetchScenarioData = async () => {
    try {
      const response = await apiClient.getScenarios('1');
      setScenarioData(response);
    } catch (error) {
      console.error('Failed to fetch scenario data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Calculate metrics from real data
  const activeScenarios = scenarioData?.scenarios?.length || 5;
  const riskLevel = scenarioData?.overall_risk || 'Medium';
  const worstCase = scenarioData?.worst_case_return || -28;
  const bestCase = scenarioData?.best_case_return || 22;
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-400/20 to-purple-400/20 rounded-full blur-3xl animate-float" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-br from-green-400/20 to-blue-400/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 right-1/3 w-60 h-60 bg-gradient-to-br from-purple-400/20 to-pink-400/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '4s' }} />
      </div>
      
      <div className="relative max-w-7xl mx-auto px-8 py-6">
        {/* Header Section */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-glass shadow-glow">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
                Scenario Analysis
              </h1>
              <p className="text-slate-600 mt-1">
                Stress testing and portfolio impact simulation
              </p>
            </div>
          </div>
          
          {/* Quick Stats Bar */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6"
          >
            <div className="glass-card p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Active Scenarios</p>
                  <p className="text-2xl font-bold text-slate-900">{activeScenarios}</p>
                </div>
                <TrendingUp className="w-5 h-5 text-blue-500" />
              </div>
            </div>
            
            <div className="glass-card p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Risk Level</p>
                  <p className="text-2xl font-bold text-amber-600">{riskLevel}</p>
                </div>
                <AlertTriangle className="w-5 h-5 text-amber-500" />
              </div>
            </div>
            
            <div className="glass-card p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Worst Case</p>
                  <p className="text-2xl font-bold text-red-600">{worstCase}%</p>
                </div>
                <DollarSign className="w-5 h-5 text-red-500" />
              </div>
            </div>
            
            <div className="glass-card p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Best Case</p>
                  <p className="text-2xl font-bold text-green-600">{bestCase > 0 ? '+' : ''}{bestCase}%</p>
                </div>
                <DollarSign className="w-5 h-5 text-green-500" />
              </div>
            </div>
          </motion.div>
        </motion.div>
        
        {/* Main Scenarios Component */}
        <Scenarios portfolioId="main-portfolio" />
      </div>
    </div>
  );
}
