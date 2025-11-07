/**
 * DawsOS Context Management Module
 * Extracted from full_ui.html on 2025-11-07
 *
 * This module provides portfolio context management including:
 * - Portfolio ID retrieval and persistence
 * - User context with portfolio state management
 * - Portfolio switching and selection UI
 *
 * Dependencies:
 * - React (useState, useEffect, useCallback, useContext, createContext, useRef)
 * - DawsOS.APIClient.TokenManager (for user and token management)
 * - DawsOS.APIClient.apiClient (for portfolio data fetching)
 * - CacheManager (global, defined in full_ui.html)
 *
 * Exports:
 * - getCurrentPortfolioId: Function to get current portfolio ID with fallback
 * - UserContext: React context for user and portfolio state
 * - UserContextProvider: React component provider for UserContext
 * - useUserContext: Custom React hook to access UserContext
 * - PortfolioSelector: React component for portfolio selection UI
 */

(function(global) {
    'use strict';

    // Ensure DawsOS namespace exists
    if (!global.DawsOS) {
        global.DawsOS = {};
    }

    // Get dependencies
    // TokenManager and apiClient are exported directly to global scope by api-client.js
    const TokenManager = global.TokenManager || {};
    const apiClient = global.apiClient || {};
    const { useState, useEffect, useCallback, useContext, createContext, useRef } = global.React || {};

    // React.createElement shorthand (used throughout this module)
    const e = global.React ? global.React.createElement : null;

    if (!e) {
        console.error('[Context] React.createElement not available!');
        throw new Error('[Context] React is required but not loaded');
    }

    // ===== UNIFIED PATTERN INTEGRATION SYSTEM =====

    /**
     * Get the current portfolio ID with fallback
     * This ensures we always have a valid portfolio ID
     */
    function getCurrentPortfolioId() {
        // 1. Check localStorage first for persisted selection
        const savedPortfolioId = localStorage.getItem('selectedPortfolioId');
        if (savedPortfolioId) {
            console.log('Using saved portfolio ID from localStorage:', savedPortfolioId);
            return savedPortfolioId;
        }

        // 2. Check if user has a portfolio ID in token storage
        const storedUser = TokenManager.getUser();
        if (storedUser && storedUser.default_portfolio_id) {
            console.log('Using user portfolio ID:', storedUser.default_portfolio_id);
            return storedUser.default_portfolio_id;
        }

        // 3. Use hardcoded fallback portfolio ID
        const fallbackPortfolioId = '64ff3be6-0ed1-4990-a32b-4ded17f0320c';
        console.log('Using fallback portfolio ID:', fallbackPortfolioId);
        return fallbackPortfolioId;
    }

    /**
     * Enhanced Portfolio Context Manager for centralized portfolio management
     */
    const UserContext = createContext();

    // Portfolio Context Manager Provider
    function UserContextProvider({ children }) {
        const [portfolioId, setPortfolioIdState] = useState(null);
        const [user, setUser] = useState(null);
        const [portfolios, setPortfolios] = useState([]);
        const [currentPortfolioData, setCurrentPortfolioData] = useState(null);
        const [loadingPortfolios, setLoadingPortfolios] = useState(false);

        // Enhanced setPortfolioId that persists to localStorage and broadcasts changes
        const setPortfolioId = useCallback((newPortfolioId) => {
            if (newPortfolioId && newPortfolioId !== portfolioId) {
                // Save to localStorage
                localStorage.setItem('selectedPortfolioId', newPortfolioId);

                // Update state
                setPortfolioIdState(newPortfolioId);

                // Broadcast portfolio change event for components that need to react
                window.dispatchEvent(new CustomEvent('portfolioChanged', {
                    detail: { portfolioId: newPortfolioId }
                }));

                console.log('Portfolio changed to:', newPortfolioId);
            }
        }, [portfolioId]);

        // Load user portfolios
        const loadPortfolios = useCallback(async () => {
            if (!user) return;

            setLoadingPortfolios(true);
            try {
                // For now, we'll use a single portfolio structure
                // In the future, this can be expanded to fetch multiple portfolios
                const portfolio = await apiClient.getPortfolio();
                const metrics = await apiClient.getMetrics(portfolioId);

                // Create portfolio array from available data
                const portfolioData = {
                    id: portfolioId,
                    name: user.email ? `${user.email.split('@')[0]}'s Portfolio` : 'Main Portfolio',
                    value: metrics?.current_value || portfolio?.total_value || 0,
                    performance: {
                        ytd: metrics?.ytd_return || 0,
                        oneYear: metrics?.one_year_return || 0
                    }
                };

                setPortfolios([portfolioData]);
                console.log('Loaded portfolio:', portfolioData);
            } catch (error) {
                console.error('Failed to load portfolios:', error);
                // Set a default portfolio structure if API fails
                setPortfolios([{
                    id: portfolioId,
                    name: 'Default Portfolio',
                    value: 0
                }]);
            } finally {
                setLoadingPortfolios(false);
            }
        }, [user, portfolioId]);

        // Load current portfolio data
        const loadCurrentPortfolioData = useCallback(async () => {
            if (!portfolioId) return;

            try {
                // Fetch current portfolio details using available API methods
                const [portfolio, metrics] = await Promise.all([
                    apiClient.getPortfolio(),
                    apiClient.getMetrics(portfolioId)
                ]);

                if (portfolio || metrics) {
                    setCurrentPortfolioData({
                        id: portfolioId,
                        name: user?.email ? `${user.email.split('@')[0]}'s Portfolio` : 'Main Portfolio',
                        value: metrics?.current_value || portfolio?.total_value || 0,
                        performance: {
                            ytd: metrics?.ytd_return || 0,
                            oneYear: metrics?.one_year_return || 0
                        }
                    });
                }
            } catch (error) {
                console.error('Failed to load portfolio data:', error);
            }
        }, [portfolioId, user]);

        // Initialize on mount
        useEffect(() => {
            // Get user from token manager
            const storedUser = TokenManager.getUser();
            if (storedUser) {
                setUser(storedUser);
            }

            // Initialize portfolio ID using enhanced function
            const initialPortfolioId = getCurrentPortfolioId();
            setPortfolioIdState(initialPortfolioId);
        }, []);

        // Load portfolios when user changes
        useEffect(() => {
            if (user) {
                loadPortfolios();
            }
        }, [user, loadPortfolios]);

        // Load portfolio data when portfolio changes
        useEffect(() => {
            if (portfolioId) {
                loadCurrentPortfolioData();
            }
        }, [portfolioId, loadCurrentPortfolioData]);

        // Method to switch portfolios
        const switchPortfolio = useCallback((newPortfolioId) => {
            setPortfolioId(newPortfolioId);
        }, [setPortfolioId]);

        // Clear portfolio selection (useful for logout)
        const clearPortfolioSelection = useCallback(() => {
            localStorage.removeItem('selectedPortfolioId');
            setPortfolioIdState(null);
            setCurrentPortfolioData(null);
        }, []);

        const contextValue = {
            portfolioId,
            setPortfolioId,
            user,
            portfolios,
            currentPortfolioData,
            loadingPortfolios,
            switchPortfolio,
            clearPortfolioSelection,
            refreshPortfolios: loadPortfolios,
            refreshCurrentPortfolio: loadCurrentPortfolioData
        };

        return e(UserContext.Provider, { value: contextValue }, children);
    }

    // Custom hook to use user context
    function useUserContext() {
        const context = useContext(UserContext);
        if (!context) {
            throw new Error('useUserContext must be used within UserContextProvider');
        }
        return context;
    }

    /**
     * Portfolio Selector Component
     * Allows users to switch between portfolios with a dropdown interface
     */
    function PortfolioSelector() {
        const {
            portfolioId,
            portfolios,
            currentPortfolioData,
            loadingPortfolios,
            switchPortfolio,
            refreshPortfolios
        } = useUserContext();

        const [isOpen, setIsOpen] = useState(false);
        const dropdownRef = useRef(null);

        // Close dropdown when clicking outside
        useEffect(() => {
            function handleClickOutside(event) {
                if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                    setIsOpen(false);
                }
            }

            document.addEventListener('mousedown', handleClickOutside);
            return () => {
                document.removeEventListener('mousedown', handleClickOutside);
            };
        }, []);

        // Refresh portfolios on mount
        useEffect(() => {
            if (!portfolios || portfolios.length === 0) {
                refreshPortfolios();
            }
        }, []);

        const handlePortfolioSelect = (portfolio) => {
            if (portfolio.id !== portfolioId) {
                switchPortfolio(portfolio.id);
                setIsOpen(false);
            }
        };

        const formatValue = (value) => {
            if (!value) return '$0';
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(value);
        };

        const formatPerformance = (performance) => {
            if (!performance || !performance.ytd) return null;
            const ytd = performance.ytd;
            const sign = ytd >= 0 ? '+' : '';
            return `${sign}${(ytd * 100).toFixed(2)}%`;
        };

        // Determine current portfolio display info
        const currentDisplay = currentPortfolioData || {
            name: portfolios?.find(p => p.id === portfolioId)?.name || 'Portfolio',
            value: portfolios?.find(p => p.id === portfolioId)?.value || 0
        };

        return e('div', { className: 'portfolio-selector', ref: dropdownRef },
            e('div', {
                className: `portfolio-selector-trigger ${isOpen ? 'open' : ''}`,
                onClick: () => setIsOpen(!isOpen)
            },
                e('div', { className: 'portfolio-info' },
                    e('div', { className: 'portfolio-name' }, currentDisplay.name),
                    e('div', { className: 'portfolio-value' }, formatValue(currentDisplay.value))
                ),
                e('span', { className: `portfolio-arrow ${isOpen ? 'open' : ''}` }, '▼')
            ),

            isOpen && e('div', { className: 'portfolio-dropdown' },
                e('div', { className: 'portfolio-dropdown-header' }, 'Select Portfolio'),

                loadingPortfolios
                    ? e('div', { className: 'portfolio-loading' },
                        e('div', { className: 'spinner-small' })
                    )
                    : portfolios && portfolios.length > 0
                        ? e('div', { className: 'portfolio-list' },
                            portfolios.map(portfolio =>
                                e('div', {
                                    key: portfolio.id,
                                    className: `portfolio-item ${portfolio.id === portfolioId ? 'active' : ''}`,
                                    onClick: () => handlePortfolioSelect(portfolio)
                                },
                                    e('div', { className: 'portfolio-item-info' },
                                        e('div', { className: 'portfolio-item-name' }, portfolio.name),
                                        e('div', { className: 'portfolio-item-value' },
                                            formatValue(portfolio.value || portfolio.total_value)
                                        )
                                    ),
                                    portfolio.performance && formatPerformance(portfolio.performance) &&
                                        e('div', {
                                            className: `portfolio-item-performance ${
                                                portfolio.performance.ytd >= 0 ? 'positive' : 'negative'
                                            }`
                                        }, formatPerformance(portfolio.performance)),
                                    portfolio.id === portfolioId &&
                                        e('span', { className: 'portfolio-item-check' }, '✓')
                                )
                            )
                        )
                        : e('div', { className: 'portfolio-empty' },
                            'No portfolios available'
                        )
            )
        );
    }

    // Export to global DawsOS namespace
    global.DawsOS.Context = {
        UserContext,
        UserContextProvider,
        useUserContext,
        PortfolioSelector
    };


})(window);
