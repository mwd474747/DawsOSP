/**
 * React Query Hooks for DawsOS
 * 
 * Purpose: Centralized data fetching with React Query
 * Updated: 2025-10-29
 * Priority: P0 (Critical for UI data integration)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, LoginRequest, ExecuteRequest } from './api-client';

// Query Keys
export const queryKeys = {
  // Authentication
  currentUser: ['auth', 'me'] as const,
  
  // Portfolio
  portfolio: (id: string) => ['portfolio', id] as const,
  portfolioOverview: (id: string) => ['portfolio', id, 'overview'] as const,
  holdings: (id: string) => ['portfolio', id, 'holdings'] as const,
  scenarios: (id: string) => ['portfolio', id, 'scenarios'] as const,
  reports: (id: string) => ['portfolio', id, 'reports'] as const,
  
  // Macro
  macro: () => ['macro'] as const,
  alerts: () => ['alerts'] as const,
  
  // Analysis
  buffettChecklist: (portfolioId: string, securityId?: string) => 
    ['analysis', 'buffett', portfolioId, securityId] as const,
  policyRebalance: (portfolioId: string) => 
    ['analysis', 'policy', portfolioId] as const,
  cycleDeleveraging: (portfolioId: string) => 
    ['analysis', 'cycle', portfolioId] as const,
  holdingDeepDive: (portfolioId: string, holdingId?: string) => 
    ['analysis', 'holding', portfolioId, holdingId] as const,
};

// Authentication Hooks
export const useCurrentUser = () => {
  return useQuery({
    queryKey: queryKeys.currentUser,
    queryFn: () => apiClient.getCurrentUser(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false, // Don't retry auth failures
    enabled: false, // Don't auto-fetch, only when explicitly called
  });
};

export const useLogin = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (credentials: LoginRequest) => apiClient.login(credentials),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.currentUser });
    },
  });
};

export const useLogout = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: apiClient.logout,
    onSuccess: () => {
      queryClient.clear();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    },
  });
};

// Portfolio Hooks
export const usePortfolioOverview = (portfolioId: string) => {
  return useQuery({
    queryKey: queryKeys.portfolioOverview(portfolioId),
    queryFn: () => apiClient.getPortfolioOverview(portfolioId),
    enabled: !!portfolioId,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
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

export const useReports = (portfolioId: string) => {
  return useQuery({
    queryKey: queryKeys.reports(portfolioId),
    queryFn: () => apiClient.getReports(portfolioId),
    enabled: !!portfolioId,
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
};

// Macro Hooks
export const useMacroDashboard = () => {
  return useQuery({
    queryKey: queryKeys.macro(),
    queryFn: () => apiClient.getMacroDashboard(),
    staleTime: 10 * 60 * 1000, // 10 minutes
    refetchInterval: 15 * 60 * 1000, // Refetch every 15 minutes
  });
};

export const useAlerts = () => {
  return useQuery({
    queryKey: queryKeys.alerts(),
    queryFn: () => apiClient.getAlerts(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 10 * 60 * 1000, // Refetch every 10 minutes
  });
};

// Analysis Hooks
export const useBuffettChecklist = (portfolioId: string, securityId?: string) => {
  return useQuery({
    queryKey: queryKeys.buffettChecklist(portfolioId, securityId),
    queryFn: () => apiClient.getBuffettChecklist(portfolioId, securityId),
    enabled: !!portfolioId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
};

export const usePolicyRebalance = (portfolioId: string) => {
  return useQuery({
    queryKey: queryKeys.policyRebalance(portfolioId),
    queryFn: () => apiClient.getPolicyRebalance(portfolioId),
    enabled: !!portfolioId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
};

export const useCycleDeleveraging = (portfolioId: string) => {
  return useQuery({
    queryKey: queryKeys.cycleDeleveraging(portfolioId),
    queryFn: () => apiClient.getCycleDeleveraging(portfolioId),
    enabled: !!portfolioId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
};

export const useHoldingDeepDive = (portfolioId: string, holdingId?: string) => {
  return useQuery({
    queryKey: queryKeys.holdingDeepDive(portfolioId, holdingId),
    queryFn: () => apiClient.getHoldingDeepDive(portfolioId, holdingId),
    enabled: !!portfolioId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
};

// Generic Pattern Execution Hook
export const useExecutePattern = () => {
  return useMutation({
    mutationFn: (request: ExecuteRequest) => apiClient.executePattern(request),
  });
};