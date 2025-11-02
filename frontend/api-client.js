/**
 * DawsOS API Client Module
 * Extracted from full_ui.html for better modularity
 * This module handles all API communication, authentication, and error handling
 */

(function(global) {
    'use strict';
    
    // ============================================
    // API Configuration and Authentication
    // ============================================
    
    const API_BASE = '';
    
    // Helper function to get current portfolio ID
    const getCurrentPortfolioId = () => {
        // First try to get from user context
        const user = TokenManager.getUser();
        if (user && user.default_portfolio_id) {
            return user.default_portfolio_id;
        }
        // Fallback to hardcoded ID for now
        // This should eventually be replaced with proper user portfolio selection
        return '64ff3be6-0ed1-4990-a32b-4ded17f0320c';
    };
    
    // JWT Token Management with Enhanced Features
    const TokenManager = {
        getToken: () => localStorage.getItem('access_token'),
        setToken: (token) => localStorage.setItem('access_token', token),
        removeToken: () => localStorage.removeItem('access_token'),
        getUser: () => {
            const userStr = localStorage.getItem('user');
            return userStr ? JSON.parse(userStr) : null;
        },
        setUser: (user) => localStorage.setItem('user', JSON.stringify(user)),
        removeUser: () => localStorage.removeItem('user'),
        
        // Token refresh promise to prevent multiple simultaneous refresh attempts
        refreshPromise: null,
        
        // Perform token refresh
        async performTokenRefresh() {
            try {
                const response = await axios.post(`${API_BASE}/api/auth/refresh`, {}, {
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    // Don't use interceptors for refresh request
                    transformRequest: [(data, headers) => {
                        delete headers.Authorization;
                        return JSON.stringify(data);
                    }]
                });
                
                const { access_token } = response.data;
                this.setToken(access_token);
                return access_token;
            } catch (error) {
                console.error('Token refresh failed:', error);
                return null;
            }
        },
        
        // Refresh token with singleton pattern to prevent race conditions
        async refreshToken() {
            // If already refreshing, wait for the existing refresh to complete
            if (this.refreshPromise) {
                return this.refreshPromise;
            }
            
            // Start a new refresh and store the promise
            this.refreshPromise = this.performTokenRefresh();
            
            try {
                const token = await this.refreshPromise;
                return token;
            } finally {
                // Clear the promise after completion
                this.refreshPromise = null;
            }
        }
    };
    
    // Enhanced error handler that distinguishes between error types
    const handleApiError = (error) => {
        if (error.response) {
            // Server responded with error status
            return {
                type: 'server',
                message: error.response.data?.detail || error.response.data?.message || 'Server error',
                code: error.response.status,
                details: error.response.data,
            };
        } else if (error.request) {
            // Request was made but no response received (network error)
            return {
                type: 'network',
                message: 'Network error - please check your connection',
                code: 'NETWORK_ERROR',
            };
        } else {
            // Something else happened (e.g., configuration error)
            return {
                type: 'unknown',
                message: error.message || 'An unexpected error occurred',
                code: 'UNKNOWN_ERROR',
            };
        }
    };
    
    // Retry configuration with exponential backoff
    const retryConfig = {
        maxRetries: 3,
        shouldRetry: (error, attemptNumber) => {
            // Don't retry on 4xx client errors (except 401 which is handled separately)
            if (error.response?.status >= 400 && error.response?.status < 500 && error.response?.status !== 401) {
                return false;
            }
            // Retry for network errors and 5xx server errors
            return attemptNumber < retryConfig.maxRetries;
        },
        getRetryDelay: (attemptNumber) => {
            // Exponential backoff: 1s, 2s, 4s, max 30s
            return Math.min(1000 * Math.pow(2, attemptNumber - 1), 30000);
        }
    };
    
    // Enhanced request interceptor with retry support
    axios.interceptors.request.use(
        config => {
            // Add auth token to all requests
            const token = TokenManager.getToken();
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            
            // Initialize retry metadata if not present
            if (!config._retryCount) {
                config._retryCount = 0;
            }
            
            return config;
        },
        error => Promise.reject(error)
    );
    
    // Enhanced response interceptor with automatic token refresh and retry logic
    axios.interceptors.response.use(
        response => response,
        async error => {
            const originalRequest = error.config;
            
            // Handle 401 Unauthorized errors (token expired)
            if (error.response?.status === 401 && !originalRequest._retry) {
                originalRequest._retry = true;
                
                try {
                    // Attempt to refresh the token
                    const newToken = await TokenManager.refreshToken();
                    
                    if (newToken) {
                        // Update the authorization header with the new token
                        originalRequest.headers.Authorization = `Bearer ${newToken}`;
                        
                        // Retry the original request with the new token
                        return axios(originalRequest);
                    }
                } catch (refreshError) {
                    // Token refresh failed, redirect to login
                    console.error('Token refresh failed, redirecting to login');
                    TokenManager.removeToken();
                    TokenManager.removeUser();
                    window.location.href = '/login';
                    return Promise.reject(refreshError);
                }
            }
            
            // Handle other errors with retry logic (excluding 401 which was handled above)
            if (error.response?.status !== 401 && originalRequest._retryCount < retryConfig.maxRetries) {
                if (retryConfig.shouldRetry(error, originalRequest._retryCount + 1)) {
                    originalRequest._retryCount++;
                    
                    // Calculate delay for exponential backoff
                    const delay = retryConfig.getRetryDelay(originalRequest._retryCount);
                    
                    console.log(`Retrying request (attempt ${originalRequest._retryCount}/${retryConfig.maxRetries}) after ${delay}ms`);
                    
                    // Wait for the delay before retrying
                    await new Promise(resolve => setTimeout(resolve, delay));
                    
                    // Retry the request
                    return axios(originalRequest);
                }
            }
            
            // If we've exhausted retries or shouldn't retry, return the enhanced error
            const enhancedError = handleApiError(error);
            error.enhancedError = enhancedError;
            
            return Promise.reject(error);
        }
    );
    
    // API Client with enhanced error handling and retry support
    const apiClient = {
        // Helper method to handle API errors consistently
        handleApiCallError: (operation, error) => {
            const enhancedError = error.enhancedError || handleApiError(error);
            console.error(`${operation} failed:`, {
                type: enhancedError.type,
                message: enhancedError.message,
                code: enhancedError.code,
                details: enhancedError.details
            });
            
            // Throw the enhanced error for better error handling in UI components
            const errorWithContext = new Error(enhancedError.message);
            errorWithContext.type = enhancedError.type;
            errorWithContext.code = enhancedError.code;
            errorWithContext.details = enhancedError.details;
            errorWithContext.originalError = error;
            throw errorWithContext;
        },
        
        // Execute pattern through orchestrator with automatic retry
        executePattern: async (patternName, inputs = {}, options = {}) => {
            try {
                // Allow custom retry configuration per request
                const config = {
                    ...options,
                    _customRetryConfig: options.retryConfig
                };
                
                const response = await axios.post(`${API_BASE}/api/patterns/execute`, {
                    pattern: patternName,
                    inputs: inputs, // Using 'inputs' to maintain backward compatibility
                    require_fresh: options.requireFresh
                }, config);
                
                return response.data;
            } catch (error) {
                return apiClient.handleApiCallError(`Pattern execution '${patternName}'`, error);
            }
        },
        
        // Get portfolio data with enhanced error handling
        getPortfolio: async () => {
            try {
                const response = await axios.get(`${API_BASE}/api/portfolio`);
                return response.data;
            } catch (error) {
                return apiClient.handleApiCallError('Fetch portfolio', error);
            }
        },
        
        // Get holdings with enhanced error handling
        getHoldings: async () => {
            try {
                const response = await axios.get(`${API_BASE}/api/holdings`);
                return response.data;
            } catch (error) {
                return apiClient.handleApiCallError('Fetch holdings', error);
            }
        },
        
        // Get metrics with enhanced error handling
        getMetrics: async (portfolioId = getCurrentPortfolioId()) => {
            try {
                const response = await axios.get(`${API_BASE}/api/metrics/${portfolioId}`);
                return response.data;
            } catch (error) {
                return apiClient.handleApiCallError('Fetch metrics', error);
            }
        },
        
        // Get macro data with enhanced error handling
        getMacro: async () => {
            try {
                const response = await axios.get(`${API_BASE}/api/macro`);
                return response.data;
            } catch (error) {
                return apiClient.handleApiCallError('Fetch macro data', error);
            }
        },
        
        // Get transactions with enhanced error handling
        getTransactions: async (portfolioId = getCurrentPortfolioId(), page = 1, pageSize = 100) => {
            try {
                const response = await axios.get(`${API_BASE}/api/transactions`, {
                    params: {
                        portfolio_id: portfolioId,
                        page: page,
                        page_size: pageSize
                    }
                });
                return response.data;
            } catch (error) {
                return apiClient.handleApiCallError('Fetch transactions', error);
            }
        },
        
        // Authentication methods with token management
        login: async (email, password) => {
            try {
                const response = await axios.post(`${API_BASE}/api/auth/login`, {
                    email,
                    password
                });
                
                const { access_token, user } = response.data;
                
                // Store token and user info
                TokenManager.setToken(access_token);
                TokenManager.setUser(user);
                
                return response.data;
            } catch (error) {
                return apiClient.handleApiCallError('Login', error);
            }
        },
        
        logout: async () => {
            try {
                await axios.post(`${API_BASE}/api/auth/logout`);
            } catch (error) {
                console.error('Logout error:', error);
            } finally {
                // Always clear local storage on logout attempt
                TokenManager.removeToken();
                TokenManager.removeUser();
            }
        },
        
        // Health check with enhanced error handling
        healthCheck: async () => {
            try {
                const response = await axios.get(`${API_BASE}/health`);
                return response.data;
            } catch (error) {
                return apiClient.handleApiCallError('Health check', error);
            }
        }
    };
    
    // ============================================
    // Export to global scope for browser usage
    // ============================================
    
    // Export the API client and utilities to the global window object
    // This maintains backward compatibility with the existing code
    global.API_BASE = API_BASE;
    global.getCurrentPortfolioId = getCurrentPortfolioId;
    global.TokenManager = TokenManager;
    global.handleApiError = handleApiError;
    global.retryConfig = retryConfig;
    global.apiClient = apiClient;
    
    // For debugging purposes
    console.log('API Client module loaded successfully');
    
})(window);