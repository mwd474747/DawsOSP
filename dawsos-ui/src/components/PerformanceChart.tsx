'use client';

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  ReferenceLine,
} from 'recharts';

interface PerformanceChartProps {
  data?: Array<{
    date: string;
    value: number;
    benchmark?: number;
  }>;
  height?: number;
  showBenchmark?: boolean;
  className?: string;
}

export function PerformanceChart({ 
  data = [], 
  height = 300, 
  showBenchmark = true,
  className = ''
}: PerformanceChartProps) {
  // Sample data if none provided
  const chartData = data.length > 0 ? data : [
    { date: '2024-01-01', value: 1000000, benchmark: 1000000 },
    { date: '2024-02-01', value: 1020000, benchmark: 1005000 },
    { date: '2024-03-01', value: 1050000, benchmark: 1010000 },
    { date: '2024-04-01', value: 1030000, benchmark: 1015000 },
    { date: '2024-05-01', value: 1080000, benchmark: 1020000 },
    { date: '2024-06-01', value: 1120000, benchmark: 1025000 },
    { date: '2024-07-01', value: 1100000, benchmark: 1030000 },
    { date: '2024-08-01', value: 1150000, benchmark: 1035000 },
    { date: '2024-09-01', value: 1180000, benchmark: 1040000 },
    { date: '2024-10-01', value: 1200000, benchmark: 1045000 },
  ];

  const formatValue = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`;
    }
    return `$${value.toFixed(0)}`;
  };

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', { 
      month: 'short', 
      year: '2-digit' 
    });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 rounded-fib2 shadow-fib2 border border-slate-200">
          <p className="text-sm font-medium text-slate-900">
            {formatDate(label)}
          </p>
          <p className="text-sm text-blue-600">
            Portfolio: {formatValue(payload[0].value)}
          </p>
          {showBenchmark && payload[1] && (
            <p className="text-sm text-slate-500">
              Benchmark: {formatValue(payload[1].value)}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`w-full ${className}`}>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <defs>
            <linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.05}/>
            </linearGradient>
            <linearGradient id="benchmarkGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#64748b" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#64748b" stopOpacity={0.05}/>
            </linearGradient>
          </defs>
          
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          
          <XAxis 
            dataKey="date" 
            tickFormatter={formatDate}
            tick={{ fontSize: 12, fill: '#64748b' }}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          
          <YAxis 
            tickFormatter={formatValue}
            tick={{ fontSize: 12, fill: '#64748b' }}
            axisLine={{ stroke: '#e2e8f0' }}
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          {/* Portfolio Area */}
          <Area
            type="monotone"
            dataKey="value"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="url(#portfolioGradient)"
            name="Portfolio"
          />
          
          {/* Benchmark Line */}
          {showBenchmark && (
            <Line
              type="monotone"
              dataKey="benchmark"
              stroke="#64748b"
              strokeWidth={1.5}
              strokeDasharray="5 5"
              dot={false}
              name="Benchmark"
            />
          )}
          
          {/* Reference line at starting value */}
          <ReferenceLine 
            y={chartData[0]?.value} 
            stroke="#94a3b8" 
            strokeDasharray="2 2"
            label={{ value: "Start", position: "top" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
