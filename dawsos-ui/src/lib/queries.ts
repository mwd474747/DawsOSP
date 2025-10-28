/**
 * React Query Hooks for DawsOS
 * 
 * Purpose: Data fetching and caching with React Query
 * Updated: 2025-10-28
 * Priority: P0 (Critical for UI data integration)
 * 
 * Features:
 *   - React Query hooks for all API endpoints
 *   - Automatic caching and background refetching
 *   - Error handling and loading states
 *   - Optimistic updates where appropriate
 *   - TypeScript types for all queries
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, ExecuteRequest, ExecuteResponse, LoginRequest, LoginResponse } from './api-client';

// Query Keys
export const queryKeys = {
  portfolio: (id: string) => ['portfolio', id],
  macro: () => ['macro'],
  holdings: (id: string) => ['holdings', id],
  scenarios: (id: string) => ['scenarios', id],
  alerts: (id: string) => ['alerts', id],
  reports: (id: string) => ['reports', id],
  user: () => ['user'],
  health: () => ['health'],
} as const;

// Authentication Hooks
export const useLogin = () => {
  const queryClient = useQueryClient();
  
  return useMutation<LoginResponse, Error, LoginRequest>({
    mutationFn: apiClient.login,
    onSuccess: (data) => {
      // Invalidate user query to refetch user data
      queryClient.invalidateQueries({ queryKey: queryKeys.user() });
    },
  });
};

export const useLogout = () => {
  const queryClient = useQueryClient();
  
  return useMutation<void, Error, void>({
    mutationFn: apiClient.logout,
    onSuccess: () => {
      // Clear all cached data
      queryClient.clear();
    },
  });
};

export const useCurrentUser = () => {
  return useQuery({
    queryKey: queryKeys.user(),
    queryFn: apiClient.getCurrentUser,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

// Portfolio Hooks
export const usePortfolioOverview = (portfolioId: string) => {
  return useQuery({
    queryKey: queryKeys.portfolio(portfolioId),
    queryFn: () => apiClient.getPortfolioOverview(portfolioId),
    enabled: !!portfolioId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });
};

export const useMacroDashboard = () => {
  return useQuery({
    queryKey: queryKeys.macro(),
    queryFn: apiClient.getMacroDashboard,
    staleTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: 15 * 60 * 1000, // Refetch every 15 minutes
  });
};

export const useHoldingsDetail = (portfolioId: string) => {
  return useQuery({
    queryKey: queryKeys.holdings(portfolioId),
    queryFn: () => apiClient.getHoldingsDetail(portfolioId),
    enabled: !!portfolioId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useScenarios = (portfolioId: string) => {
  return useQuery({
    queryKey: queryKeys.scenarios(portfolioId),
    queryFn: () => apiClient.getScenarios(portfolioId),
    enabled: !!portfolioId,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useAlerts = (portfolioId: string) => {
  return useQuery({
    queryKey: queryKeys.alerts(portfolioId),
    queryFn: () => apiClient.getAlerts(portfolioId),
    enabled: !!portfolioId,
    staleTime: 1 * 60 * 1000, // 1 minute
    refetchInterval: 2 * 60 * 1000, // Refetch every 2 minutes
  });
};

export const useReports = (portfolioId: string) => {
  return useQuery({
    queryKey: queryKeys.reports(portfolioId),
    queryFn: () => apiClient.getReports(portfolioId),
    enabled: !!portfolioId,
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};

// Generic Pattern Execution Hook
export const usePatternExecution = () => {
  const queryClient = useQueryClient();
  
  return useMutation<ExecuteResponse, Error, ExecuteRequest>({
    mutationFn: apiClient.executePattern,
    onSuccess: (data, variables) => {
      // Invalidate related queries based on pattern
      const pattern = variables.pattern;
      const portfolioId = variables.inputs.portfolio_id;
      
      if (portfolioId) {
        switch (pattern) {
          case 'portfolio_overview':
            queryClient.invalidateQueries({ queryKey: queryKeys.portfolio(portfolioId) });
            break;
          case 'holding_deep_dive':
            queryClient.invalidateQueries({ queryKey: queryKeys.holdings(portfolioId) });
            break;
          case 'portfolio_scenario_analysis':
            queryClient.invalidateQueries({ queryKey: queryKeys.scenarios(portfolioId) });
            break;
          case 'macro_trend_monitor':
            queryClient.invalidateQueries({ queryKey: queryKeys.alerts(portfolioId) });
            break;
          case 'export_portfolio_report':
            queryClient.invalidateQueries({ queryKey: queryKeys.reports(portfolioId) });
            break;
        }
      }
      
      if (pattern === 'macro_cycles_overview') {
        queryClient.invalidateQueries({ queryKey: queryKeys.macro() });
      }
    },
  });
};

// Health Check Hook
export const useHealthCheck = () => {
  return useQuery({
    queryKey: queryKeys.health(),
    queryFn: apiClient.healthCheck,
    retry: 3,
    retryDelay: 5000, // 5 seconds
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
  });
};

// Utility Hooks
export const useInvalidatePortfolio = (portfolioId: string) => {
  const queryClient = useQueryClient();
  
  return () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.portfolio(portfolioId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.holdings(portfolioId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.scenarios(portfolioId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.alerts(portfolioId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.reports(portfolioId) });
  };
};

export const useInvalidateAll = () => {
  const queryClient = useQueryClient();
  
  return () => {
    queryClient.invalidateQueries();
  };
};
