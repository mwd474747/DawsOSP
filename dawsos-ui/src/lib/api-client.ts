/**
 * API Client for DawsOS Backend
 * 
 * Purpose: Centralized API communication with authentication and error handling
 * Updated: 2025-10-28
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
  state: Record<string, any>;
  status: 'success' | 'error';
  error?: string;
  metadata?: {
    execution_time_ms: number;
    pattern_name: string;
    agents_used: string[];
  };
}

export interface LoginRequest {
  email: string;
  password: string;
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

export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}

// API Client Class
class ApiClient {
  private client: AxiosInstance;
  private refreshPromise: Promise<string | null> | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor - Add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor - Handle auth errors and retries
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 errors (token expired)
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const newToken = await this.refreshToken();
            if (newToken) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            this.clearAuthToken();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(this.handleError(error));
      }
    );
  }

  private getAuthToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('auth_token');
  }

  private setAuthToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem('auth_token', token);
  }

  private clearAuthToken(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('auth_token');
  }

  private async refreshToken(): Promise<string | null> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.performTokenRefresh();
    try {
      const token = await this.refreshPromise;
      return token;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async performTokenRefresh(): Promise<string | null> {
    try {
      const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {}, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const { access_token } = response.data;
      this.setAuthToken(access_token);
      return access_token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return null;
    }
  }

  private handleError(error: any): ApiError {
    if (error.response) {
      // Server responded with error status
      return {
        message: error.response.data?.detail || error.response.data?.message || 'Server error',
        code: error.response.data?.code,
        details: error.response.data,
      };
    } else if (error.request) {
      // Request was made but no response received
      return {
        message: 'Network error - please check your connection',
        code: 'NETWORK_ERROR',
      };
    } else {
      // Something else happened
      return {
        message: error.message || 'An unexpected error occurred',
        code: 'UNKNOWN_ERROR',
      };
    }
  }

  // Authentication Methods
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/auth/login', credentials);
    const { access_token } = response.data;
    this.setAuthToken(access_token);
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.clearAuthToken();
    }
  }

  async getCurrentUser(): Promise<any> {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  // Pattern Execution Methods
  async executePattern(request: ExecuteRequest): Promise<ExecuteResponse> {
    const response = await this.client.post<ExecuteResponse>('/execute', request);
    return response.data;
  }

  // Portfolio Methods
  async getPortfolioOverview(portfolioId: string): Promise<any> {
    return this.executePattern({
      pattern: 'portfolio_overview',
      inputs: { portfolio_id: portfolioId },
    });
  }

  async getMacroDashboard(): Promise<any> {
    return this.executePattern({
      pattern: 'macro_cycles_overview',
      inputs: {},
    });
  }

  async getHoldingsDetail(portfolioId: string): Promise<any> {
    return this.executePattern({
      pattern: 'holding_deep_dive',
      inputs: { portfolio_id: portfolioId },
    });
  }

  async getScenarios(portfolioId: string): Promise<any> {
    return this.executePattern({
      pattern: 'portfolio_scenario_analysis',
      inputs: { portfolio_id: portfolioId },
    });
  }

  async getAlerts(portfolioId: string): Promise<any> {
    return this.executePattern({
      pattern: 'macro_trend_monitor',
      inputs: { portfolio_id: portfolioId },
    });
  }

  async getReports(portfolioId: string): Promise<any> {
    return this.executePattern({
      pattern: 'export_portfolio_report',
      inputs: { portfolio_id: portfolioId },
    });
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; message: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
