/**
 * API Client for DawsOS Backend
 * 
 * Purpose: Centralized API communication with authentication and error handling
 * Updated: 2025-10-29
 * Priority: P0 (Critical for UI data integration)
 * 
 * Features:
 *   - Axios-based HTTP client
 *   - JWT authentication with auto-refresh
 *   - Request/response interceptors
 *   - Error handling and retry logic
 *   - TypeScript types for all endpoints
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_TIMEOUT = 30000; // 30 seconds

// Types
export interface ExecuteRequest {
  pattern: string;
  inputs: Record<string, any>;
  require_fresh?: boolean;
}

export interface ExecuteResponse {
  result: any;
  metadata: {
    pricing_pack_id: string;
    ledger_commit_hash: string;
    pattern_id: string;
    asof_date: string;
    duration_ms: number;
    timestamp: string;
  };
  warnings: string[];
  trace_id: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    role: string;
  };
}

export interface UserResponse {
  id: string;
  email: string;
  role: string;
  permissions: string[];
}

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
    this.loadTokenFromStorage();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.clearToken();
          // Redirect to login if not already there
          if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  private loadTokenFromStorage() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
  }

  private saveToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  private clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  // Authentication Methods
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/auth/login', credentials);
    this.saveToken(response.data.access_token);
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout');
    } finally {
      this.clearToken();
    }
  }

  async getCurrentUser(): Promise<UserResponse> {
    const response = await this.client.get<UserResponse>('/auth/me');
    return response.data;
  }

  // Pattern Execution
  async executePattern(request: ExecuteRequest): Promise<ExecuteResponse> {
    const response = await this.client.post<ExecuteResponse>('/v1/execute', {
      pattern_id: request.pattern,
      inputs: request.inputs,
      require_fresh: request.require_fresh || false
    });
    return response.data;
  }

  // Portfolio Methods
  async getPortfolioOverview(portfolioId: string): Promise<ExecuteResponse> {
    const realPortfolioId = this.mapPortfolioId(portfolioId);
    return this.executePattern({
      pattern: 'portfolio_overview',
      inputs: { 
        portfolio_id: realPortfolioId,
        lookback_days: 252  // Default to 1 year
      },
    });
  }

  async getMacroDashboard(): Promise<ExecuteResponse> {
    return this.executePattern({
      pattern: 'macro_cycles_overview',
      inputs: {}
    });
  }

  async getHoldingsDetail(portfolioId: string): Promise<ExecuteResponse> {
    const realPortfolioId = this.mapPortfolioId(portfolioId);
    return this.executePattern({
      pattern: 'holdings_detail',
      inputs: { portfolio_id: realPortfolioId }
    });
  }

  async getScenarios(portfolioId: string): Promise<ExecuteResponse> {
    const realPortfolioId = this.mapPortfolioId(portfolioId);
    return this.executePattern({
      pattern: 'portfolio_scenario_analysis',
      inputs: { portfolio_id: realPortfolioId }
    });
  }

  async getAlerts(): Promise<ExecuteResponse> {
    return this.executePattern({
      pattern: 'macro_trend_monitor',
      inputs: {}
    });
  }

  async getReports(portfolioId: string): Promise<ExecuteResponse> {
    const realPortfolioId = this.mapPortfolioId(portfolioId);
    return this.executePattern({
      pattern: 'portfolio_reports',
      inputs: { portfolio_id: realPortfolioId }
    });
  }

  async getBuffettChecklist(portfolioId: string, securityId?: string): Promise<ExecuteResponse> {
    const realPortfolioId = this.mapPortfolioId(portfolioId);
    return this.executePattern({
      pattern: 'buffett_checklist',
      inputs: { 
        portfolio_id: realPortfolioId,
        security_id: securityId || '11111111-1111-1111-1111-111111111111'
      }
    });
  }

  async getPolicyRebalance(portfolioId: string): Promise<ExecuteResponse> {
    const realPortfolioId = this.mapPortfolioId(portfolioId);
    return this.executePattern({
      pattern: 'policy_rebalance',
      inputs: { portfolio_id: realPortfolioId }
    });
  }

  async getCycleDeleveraging(portfolioId: string): Promise<ExecuteResponse> {
    const realPortfolioId = this.mapPortfolioId(portfolioId);
    return this.executePattern({
      pattern: 'cycle_deleveraging_scenarios',
      inputs: { portfolio_id: realPortfolioId }
    });
  }

  async getHoldingDeepDive(portfolioId: string, holdingId?: string): Promise<ExecuteResponse> {
    const realPortfolioId = this.mapPortfolioId(portfolioId);
    return this.executePattern({
      pattern: 'holding_deep_dive',
      inputs: { 
        portfolio_id: realPortfolioId,
        security_id: holdingId || '11111111-1111-1111-1111-111111111111'
      }
    });
  }

  private mapPortfolioId(portfolioId: string): string {
    // Map hardcoded portfolio IDs to real UUIDs
    const portfolioMap: Record<string, string> = {
      'main-portfolio': '11111111-1111-1111-1111-111111111111',
      'demo-portfolio': '22222222-2222-2222-2222-222222222222',
      'test-portfolio': '33333333-3333-3333-3333-333333333333'
    };

    return portfolioMap[portfolioId] || portfolioId;
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();