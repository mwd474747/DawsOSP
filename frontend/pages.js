/**
 * DawsOS Frontend Page Components
 *
 * EXTRACTED FROM: /Users/mdawson/Documents/GitHub/DawsOSP/full_ui.html
 * EXTRACTION DATE: 2025-11-07
 * SOURCE LINES: 7593-12021 (approximately 4,429 lines)
 *
 * This file contains all page component definitions extracted from the full_ui.html file.
 * All components are preserved exactly as they appeared in the source.
 *
 * DEPENDENCIES:
 * - React 16.8+ (useState, useEffect, useRef hooks)
 * - React.createElement (aliased as 'e')
 * - Chart.js (for chart rendering in MacroCyclesPage)
 * - DawsOS.APIClient (apiClient)
 * - DawsOS.Utils (all utility functions and hooks)
 * - DawsOS.Panels (all panel components)
 * - PatternRenderer (for pattern-based data loading)
 * - ErrorHandler, TokenManager, CacheManager
 * - Various UI components: LoadingSpinner, ErrorMessage, RetryableError, EmptyState, 
 *   NetworkStatusIndicator, FormField, DataBadge, etc.
 *
 * PAGE COMPONENTS INCLUDED (20 total):
 * 1. LoginPage - User authentication page
 * 2. MacroCyclesPage - Macro economic cycles visualization (ALL 4 cycles)
 * 3. DashboardPage - Main dashboard with portfolio overview
 * 4. DashboardPageLegacy - Legacy dashboard implementation (kept for reference)
 * 5. HoldingsPage - Portfolio holdings view
 * 6. TransactionsPage - Transaction history
 * 7. PerformancePage - Performance analytics
 * 8. ScenariosPage - Scenario analysis
 * 9. ScenariosPageLegacy - Legacy scenario page
 * 10. RiskPage - Risk metrics and analysis
 * 11. AttributionPage - Performance attribution
 * 12. OptimizerPage - Portfolio optimization
 * 13. RatingsPage - Security ratings and analysis
 * 14. AIInsightsPage - AI-generated insights
 * 15. AIAssistantPage - AI chat assistant
 * 16. AlertsPage - Portfolio alerts and notifications
 * 17. ReportsPage - Report generation and viewing
 * 18. CorporateActionsPage - Corporate actions tracking
 * 19. MarketDataPage - Market data and quotes
 * 20. SettingsPage - User settings and preferences
 *
 * SUPPORTING COMPONENTS INCLUDED:
 * - PortfolioOverview - Portfolio summary cards
 * - HoldingsTable - Holdings data table
 */

(function(global) {
    'use strict';

    // Initialize DawsOS namespace if not exists
    if (!global.DawsOS) {
        global.DawsOS = {};
    }

    // Create Pages namespace
    const Pages = {};

    // React shortcuts
    const { useState, useEffect, useRef } = React;
    const e = React.createElement;

    // Import dependencies from DawsOS namespace
    const APIClient = global.DawsOS?.APIClient;
    const apiClient = APIClient; // For backward compatibility
    const Utils = global.DawsOS?.Utils || {};
    const Panels = global.DawsOS?.Panels || {};
    const Context = global.DawsOS?.Context || {};
    const PatternSystem = global.DawsOS?.PatternSystem || {};
    
    // Validate critical dependencies
    const Logger = global.DawsOS?.Logger;
    if (!APIClient) {
        if (Logger) {
            Logger.error('[Pages] DawsOS.APIClient not loaded');
            Logger.error('[Pages] Available namespaces:', Object.keys(global.DawsOS || {}));
        } else {
            (global.DawsOS?.Logger || console).error('[Pages] DawsOS.APIClient not loaded');
            (global.DawsOS?.Logger || console).error('[Pages] Available namespaces:', Object.keys(global.DawsOS || {}));
        }
        throw new Error('[Pages] Required dependency DawsOS.APIClient not found. Check script load order.');
    }

    // Import utility functions
    const formatPercentage = Utils.formatPercentage || ((v) => v + '%');
    const formatCurrency = Utils.formatCurrency || ((v) => '$' + v);
    const formatNumber = Utils.formatNumber || ((v) => v.toFixed(2));

    // Import context functions (from DawsOS.Context, NOT Utils)
    const useUserContext = Context.useUserContext || (() => ({ portfolioId: null }));
    const getCurrentPortfolioId = Context.getCurrentPortfolioId || (() => null);

    // Import cached API client (queryHelpers) from pattern-system
    const cachedApiClient = PatternSystem.queryHelpers || apiClient;

    // Import UI components from DawsOS namespaces
    const LoadingSpinner = Utils.LoadingSpinner || global.LoadingSpinner;
    const ErrorMessage = Utils.ErrorMessage || global.ErrorMessage;
    const RetryableError = Utils.RetryableError || global.RetryableError;
    const EmptyState = Utils.EmptyState || global.EmptyState;
    // These are in UI.Primitives namespace (exported from utils.js)
    const NetworkStatusIndicator = global.DawsOS?.UI?.Primitives?.NetworkStatusIndicator || Utils.NetworkStatusIndicator;
    const FormField = global.DawsOS?.UI?.Primitives?.FormField || Utils.FormField;
    const DataBadge = global.DawsOS?.UI?.Primitives?.DataBadge || global.DataBadge;
    const PatternRenderer = PatternSystem.PatternRenderer;
    // These should be in DawsOS namespace if loaded correctly
    const FormValidator = global.DawsOS?.FormValidator || global.FormValidator;
    const ErrorHandler = global.DawsOS?.ErrorHandler || global.ErrorHandler;
    // Use TokenManager from DawsOS.APIClient if available, otherwise fallback to global
    const TokenManager = APIClient?.TokenManager || global.TokenManager;
    const getDataSourceFromResponse = global.getDataSourceFromResponse;
    
    // Validate TokenManager
    if (!TokenManager) {
        if (Logger) {
            Logger.error('[Pages] TokenManager not available from DawsOS.APIClient or global');
        } else {
            (global.DawsOS?.Logger || console).error('[Pages] TokenManager not available from DawsOS.APIClient or global');
        }
        throw new Error('[Pages] TokenManager is required but not found');
    }

    // ============================================
    // PAGE COMPONENTS
    // ============================================

            function LoginPage({ onLogin }) {
                const [email, setEmail] = useState('michael@dawsos.com');
                const [password, setPassword] = useState('password123');
                const [loading, setLoading] = useState(false);
                const [error, setError] = useState(null);
                const [fieldErrors, setFieldErrors] = useState({});
                const [touched, setTouched] = useState({});
                
                const validateField = (field, value) => {
                    switch (field) {
                        case 'email':
                            return FormValidator.validateEmail(value);
                        case 'password':
                            return FormValidator.validatePassword(value);
                        default:
                            return { valid: true };
                    }
                };
                
                const handleFieldChange = (field, value) => {
                    // Update value
                    if (field === 'email') setEmail(value);
                    if (field === 'password') setPassword(value);
                    
                    // Validate if touched
                    if (touched[field]) {
                        const validation = validateField(field, value);
                        setFieldErrors(prev => ({
                            ...prev,
                            [field]: validation.valid ? null : validation.message
                        }));
                    }
                };
                
                const handleFieldBlur = (field) => {
                    setTouched(prev => ({ ...prev, [field]: true }));
                    const value = field === 'email' ? email : password;
                    const validation = validateField(field, value);
                    setFieldErrors(prev => ({
                        ...prev,
                        [field]: validation.valid ? null : validation.message
                    }));
                };
                
                const handleSubmit = async (e) => {
                    e.preventDefault();
                    
                    // Validate all fields
                    const emailValidation = FormValidator.validateEmail(email);
                    const passwordValidation = FormValidator.validatePassword(password);
                    
                    if (!emailValidation.valid || !passwordValidation.valid) {
                        setFieldErrors({
                            email: emailValidation.valid ? null : emailValidation.message,
                            password: passwordValidation.valid ? null : passwordValidation.message
                        });
                        setTouched({ email: true, password: true });
                        return;
                    }
                    
                    setLoading(true);
                    setError(null);
                    
                    try {
                        const response = await apiClient.login(email, password);
                        
                        if (response.access_token) {
                            onLogin(response.user);
                        }
                    } catch (error) {
                        if (Logger) {
                            Logger.error('Login failed:', error);
                        } else {
                            (global.DawsOS?.Logger || console).error('Login failed:', error);
                        }
                        // Use ErrorHandler for better error classification
                        const errorInfo = ErrorHandler.classifyError(error);
                        setError(error);
                    } finally {
                        setLoading(false);
                    }
                };
                
                return e('div', { className: 'login-container' },
                    e(NetworkStatusIndicator, null),
                    e('div', { className: 'login-box' },
                        e('div', { className: 'login-header' },
                            e('h1', null, 'DawsOS'),
                            e('p', null, 'Portfolio Intelligence Platform')
                        ),
                        error && e(ErrorMessage, { 
                            error, 
                            onRetry: () => handleSubmit({ preventDefault: () => {} }),
                            canDismiss: true 
                        }),
                        e('form', { onSubmit: handleSubmit },
                            e(FormField, {
                                label: 'Email',
                                error: fieldErrors.email,
                                required: true
                            },
                                e('input', {
                                    type: 'email',
                                    className: `form-input ${fieldErrors.email ? 'error' : ''}`,
                                    value: email,
                                    onChange: (e) => handleFieldChange('email', e.target.value),
                                    onBlur: () => handleFieldBlur('email'),
                                    placeholder: 'Enter your email',
                                    disabled: loading
                                })
                            ),
                            e(FormField, {
                                label: 'Password',
                                error: fieldErrors.password,
                                required: true
                            },
                                e('input', {
                                    type: 'password',
                                    className: `form-input ${fieldErrors.password ? 'error' : ''}`,
                                    value: password,
                                    onChange: (e) => handleFieldChange('password', e.target.value),
                                    onBlur: () => handleFieldBlur('password'),
                                    placeholder: 'Enter your password',
                                    disabled: loading
                                })
                            ),
                            e('button', { 
                                type: 'submit', 
                                className: 'btn', 
                                disabled: loading || Object.values(fieldErrors).some(e => e)
                            },
                                loading ? e('span', null,
                                    e('span', { className: 'spinner-small' }),
                                    ' Signing in...'
                                ) : 'Sign In'
                            )
                        )
                    )
                );
            }
            
            // ============================================
            // Component: Portfolio Overview
            // ============================================
            
            function PortfolioOverview({ data, isLoading, error, onRetry }) {
                // Enhanced with proper loading and error states
                if (isLoading) {
                    return e(LoadingSpinner, { 
                        size: 'medium', 
                        message: 'Loading portfolio data...' 
                    });
                }
                
                if (error) {
                    return e(RetryableError, { 
                        error, 
                        onRetry,
                        maxRetries: 3
                    });
                }
                
                if (!data) {
                    return e(EmptyState, {
                        title: 'No Portfolio Data',
                        message: 'Portfolio data is not available at this time.',
                        icon: '📊',
                        action: onRetry && e('button', { 
                            className: 'btn btn-primary', 
                            onClick: onRetry 
                        }, 'Reload Data')
                    });
                }
                
                // Determine data source for provenance badge
                const dataSource = getDataSourceFromResponse(data);
                if (Logger) {
                    Logger.debug('[PortfolioOverview] Data source:', dataSource, data);
                } else {
                    (global.DawsOS?.Logger || console).debug('[PortfolioOverview] Data source:', dataSource, data);
                }
                
                return e('div', { className: 'stats-grid', style: { position: 'relative' } },
                    e(DataBadge, { source: dataSource, position: 'top-right' }),
                    e('div', { className: 'stat-card' },
                        e('div', { className: 'stat-label' }, 'Total Value'),
                        e('div', { className: 'stat-value' }, formatCurrency(data.total_value || 0)),
                        e('div', { className: `stat-change ${data.change_pct >= 0 ? 'positive' : 'negative'}` }, 
                            formatPercentage((data.change_pct || 0.0235) / 100))
                    ),
                    e('div', { className: 'stat-card' },
                        e('div', { className: 'stat-label' }, 'Holdings'),
                        e('div', { className: 'stat-value' }, data.holdings_count || 0),
                        e('div', { className: 'stat-change neutral' }, 'Securities')
                    ),
                    e('div', { className: 'stat-card' },
                        e('div', { className: 'stat-label' }, 'YTD Return'),
                        e('div', { className: 'stat-value' }, formatPercentage((data.ytd_return || 0.145) / 100)),
                        e('div', { className: `stat-change ${data.ytd_return >= 0 ? 'positive' : 'negative'}` },
                            'Year to Date')
                    ),
                    e('div', { className: 'stat-card' },
                        e('div', { className: 'stat-label' }, 'Sharpe Ratio'),
                        e('div', { className: 'stat-value' }, formatNumber(data.sharpe_ratio || 0)),
                        e('div', { className: 'stat-change neutral' }, 'Risk-Adjusted')
                    )
                );
            }
            
            // ============================================
            // Component: Holdings Table
            // ============================================
            
            function HoldingsTable({ holdings, showAll = false, isLoading, error }) {
                if (isLoading) {
                    return e(LoadingSpinner, { 
                        size: 'medium', 
                        message: 'Loading holdings...' 
                    });
                }
                
                if (error) {
                    return e(ErrorMessage, { 
                        error, 
                        canDismiss: false 
                    });
                }
                
                if (!holdings || holdings.length === 0) {
                    return e(EmptyState, {
                        title: 'No Holdings',
                        message: 'No holdings data available in your portfolio.',
                        icon: '📈'
                    });
                }
                
                const displayHoldings = showAll ? holdings : holdings.slice(0, 5);
                
                // Phase 1: Metadata removed from results (moved to trace only)
                // Use default 'cached' if holdings exist, 'demo' if empty
                const dataSource = holdings.length > 0 ? 'cached' : 'demo';
                if (Logger) {
                    Logger.debug('[HoldingsTable] Data source:', dataSource, holdings);
                } else {
                    (global.DawsOS?.Logger || console).debug('[HoldingsTable] Data source:', dataSource, holdings);
                }
                
                return e('div', { className: 'card', style: { position: 'relative' } },
                    e(DataBadge, { source: dataSource, position: 'top-right' }),
                    e('div', { className: 'card-header' },
                        e('h3', { className: 'card-title' }, 'Holdings'),
                        !showAll && holdings.length > 5 && e('div', { className: 'card-actions' },
                            e('span', { style: { fontSize: '0.875rem', color: 'var(--text-secondary)' } }, 
                                `Showing 5 of ${holdings.length}`)
                        )
                    ),
                    e('div', { className: 'table-container' },
                        e('table', { className: 'table' },
                            e('thead', null,
                                e('tr', null,
                                    e('th', null, 'Symbol'),
                                    e('th', null, 'Name'),
                                    e('th', null, 'Quantity'),
                                    e('th', null, 'Value'),
                                    e('th', null, 'Weight'),
                                    e('th', null, 'Unrealized Gain/Loss')
                                )
                            ),
                            e('tbody', null,
                                displayHoldings.map((holding, index) =>
                                    e('tr', { key: index },
                                        e('td', { className: 'symbol' }, holding.symbol),
                                        e('td', null, holding.name || holding.symbol),
                                        e('td', null, formatNumber(holding.quantity, 0)),
                                        e('td', null, formatCurrency(holding.market_value)),
                                        e('td', null, formatPercentage((holding.weight || 0) / 100)),
                                        e('td', { className: holding.return_pct >= 0 ? 'positive' : 'negative' },
                                            formatPercentage((holding.return_pct || 0) / 100))
                                    )
                                )
                            )
                        )
                    )
                );
            }
            
            // ============================================
            // Component: Macro Cycles Page (ALL 4 CYCLES)
            // ============================================
            
            function MacroCyclesPage() {
                const [loading, setLoading] = useState(true);
                const [error, setError] = useState(null);
                const [macroData, setMacroData] = useState(null);
                const [activeTab, setActiveTab] = useState('short-term');
                
                // Chart references for each cycle
                const chartRefs = {
                    shortTerm: useRef(null),
                    longTerm: useRef(null),
                    empire: useRef(null),
                    dar: useRef(null),
                    overview: useRef(null)
                };
                const chartInstances = useRef({});
                
                // Clean up chart instances on unmount
                useEffect(() => {
                    return () => {
                        // Clean up all chart instances
                        Object.values(chartInstances.current).forEach(chart => {
                            if (chart) chart.destroy();
                        });
                    };
                }, []);
                
                // Timeout protection - prevent stuck loading state
                useEffect(() => {
                    if (loading) {
                        const timeout = setTimeout(() => {
                            if (Logger) {
                                Logger.warn('MacroCyclesPage: Pattern loading timeout');
                            } else {
                                (global.DawsOS?.Logger || console).warn('MacroCyclesPage: Pattern loading timeout');
                            }
                            setLoading(false);
                            setError('Data loading timed out. Please try refreshing the page.');
                        }, 30000); // 30 second timeout
                        
                        return () => clearTimeout(timeout);
                    }
                }, [loading]);
                
                // Re-render charts when data or tab changes
                useEffect(() => {
                    if (macroData && !loading) {
                        renderActiveChart();
                    }
                }, [macroData, activeTab, loading]);
                
                // Handle pattern data from PatternRenderer
                const handlePatternData = (data) => {
                    if (Logger) {
                        Logger.debug('MacroCyclesPage received pattern data:', data);
                    } else {
                        (global.DawsOS?.Logger || console).debug('MacroCyclesPage received pattern data:', data);
                    }
                    try {
                        // Check for error first
                        if (data?.error) {
                            if (Logger) {
                                Logger.error('MacroCyclesPage: Pattern execution failed:', data.error);
                            } else {
                                (global.DawsOS?.Logger || console).error('MacroCyclesPage: Pattern execution failed:', data.error);
                            }
                            setError(data.error || 'Failed to load macro cycle data. Please try refreshing the page.');
                            setLoading(false);
                            return;
                        }
                        
                        // Handle multiple nested structures
                        let result = data;
                        if (data?.data) {
                            result = data.data;
                        } else if (data?.result) {
                            result = data.result;
                        } else if (data?.result?.data) {
                            result = data.result.data;
                        }
                        
                        // More flexible validation - check for any cycle data
                        const hasCycleData = result && (
                            result.stdc || result.ltdc || result.empire || result.civil ||
                            result.short_term_cycle || result.long_term_cycle || 
                            result.empire_cycle || result.internal_order_cycle
                        );
                        
                        if (hasCycleData) {
                            // Normalize data structure to ensure consistent format
                            const normalizedData = {
                                stdc: result.stdc || result.short_term_cycle || {},
                                ltdc: result.ltdc || result.long_term_cycle || {},
                                empire: result.empire || result.empire_cycle || {},
                                civil: result.civil || result.internal_order_cycle || {},
                                dar: result.dar || {},
                                regime_detection: result.regime_detection || {}
                            };
                            
                            if (Logger) {
                                Logger.debug('MacroCyclesPage: Valid macro cycles data received:', normalizedData);
                            } else {
                                console.log('MacroCyclesPage: Valid macro cycles data received:', normalizedData);
                            }
                            setMacroData(normalizedData);
                            setError(null);
                            setLoading(false);
                        } else {
                            // Unexpected data structure - show error
                            if (Logger) {
                                Logger.warn('MacroCyclesPage: Unexpected data structure. Received:', result);
                            } else {
                                console.warn('MacroCyclesPage: Unexpected data structure. Received:', result);
                            }
                            setError('Unexpected data format. Please try refreshing the page.');
                            setLoading(false);
                        }
                    } catch (err) {
                        if (Logger) {
                            Logger.error('MacroCyclesPage: Error processing pattern data:', err);
                        } else {
                            console.error('MacroCyclesPage: Error processing pattern data:', err);
                        }
                        setError(err.message || 'Failed to process macro cycle data. Please try refreshing the page.');
                        setLoading(false);
                    }
                };
                
                const renderActiveChart = () => {
                    // Clean up existing chart for active tab
                    if (chartInstances.current[activeTab]) {
                        chartInstances.current[activeTab].destroy();
                    }
                    
                    switch(activeTab) {
                        case 'short-term':
                            renderShortTermChart();
                            break;
                        case 'long-term':
                            renderLongTermChart();
                            break;
                        case 'empire':
                            renderEmpireChart();
                            break;
                        case 'dar':
                            renderDarChart();
                            break;
                        case 'overview':
                            renderOverviewChart();
                            break;
                    }
                };
                
                const renderShortTermChart = () => {
                    if (!chartRefs.shortTerm.current) return;
                    if (!macroData?.short_term_history) return; // Don't render if no data
                    
                    const ctx = chartRefs.shortTerm.current.getContext('2d');
                    const data = macroData.short_term_history;
                    
                    chartInstances.current['short-term'] = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: data.map(d => d.month),
                            datasets: [
                                {
                                    label: 'Debt Level',
                                    data: data.map(d => d.debt),
                                    borderColor: '#ef4444',
                                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                    borderWidth: 2,
                                    tension: 0.4
                                },
                                {
                                    label: 'GDP Growth',
                                    data: data.map(d => d.gdp),
                                    borderColor: '#10b981',
                                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                                    borderWidth: 2,
                                    tension: 0.4
                                },
                                {
                                    label: 'Credit Growth',
                                    data: data.map(d => d.credit),
                                    borderColor: '#3b82f6',
                                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                                    borderWidth: 2,
                                    tension: 0.4
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {
                                mode: 'index',
                                intersect: false
                            },
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'Short-Term Debt Cycle (5-8 Years)',
                                    color: '#f1f5f9',
                                    font: { size: 16, weight: 'bold' }
                                },
                                legend: {
                                    display: true,
                                    labels: { color: '#94a3b8' }
                                },
                                tooltip: {
                                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                    borderColor: 'rgba(255, 255, 255, 0.1)',
                                    borderWidth: 1
                                }
                            },
                            scales: {
                                x: {
                                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                                    ticks: { color: '#64748b', maxRotation: 45 }
                                },
                                y: {
                                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                                    ticks: { color: '#64748b' }
                                }
                            }
                        }
                    });
                };
                
                const renderLongTermChart = () => {
                    if (!chartRefs.longTerm.current) return;
                    
                    const ctx = chartRefs.longTerm.current.getContext('2d');
                    const data = macroData?.long_term_history || generateLongTermHistory();
                    
                    chartInstances.current['long-term'] = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: data.map(d => d.year),
                            datasets: [
                                {
                                    label: 'Debt/GDP %',
                                    data: data.map(d => d.debtToGDP),
                                    borderColor: '#ef4444',
                                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                                    borderWidth: 2,
                                    fill: true,
                                    tension: 0.4
                                },
                                {
                                    label: 'Productivity',
                                    data: data.map(d => d.productivity),
                                    borderColor: '#10b981',
                                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                                    borderWidth: 2,
                                    fill: true,
                                    tension: 0.4
                                },
                                {
                                    label: 'Inequality',
                                    data: data.map(d => d.inequality),
                                    borderColor: '#f59e0b',
                                    backgroundColor: 'rgba(245, 158, 11, 0.2)',
                                    borderWidth: 2,
                                    fill: true,
                                    tension: 0.4
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {
                                mode: 'index',
                                intersect: false
                            },
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'Long-Term Debt Cycle (75-100 Years)',
                                    color: '#f1f5f9',
                                    font: { size: 16, weight: 'bold' }
                                },
                                legend: {
                                    display: true,
                                    labels: { color: '#94a3b8' }
                                },
                                tooltip: {
                                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                    borderColor: 'rgba(255, 255, 255, 0.1)',
                                    borderWidth: 1
                                }
                            },
                            scales: {
                                x: {
                                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                                    ticks: { color: '#64748b' }
                                },
                                y: {
                                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                                    ticks: { color: '#64748b' }
                                }
                            }
                        }
                    });
                };
                
                const renderEmpireChart = () => {
                    if (!chartRefs.empire.current) return;
                    
                    const ctx = chartRefs.empire.current.getContext('2d');
                    const data = macroData?.empire_history || generateEmpireHistory();
                    
                    chartInstances.current['empire'] = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: data.map(d => d.year),
                            datasets: [
                                {
                                    label: 'Global Power',
                                    data: data.map(d => d.power),
                                    borderColor: '#3b82f6',
                                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                                    borderWidth: 2,
                                    fill: true,
                                    tension: 0.4
                                },
                                {
                                    label: 'Education',
                                    data: data.map(d => d.education),
                                    borderColor: '#10b981',
                                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                                    borderWidth: 2,
                                    fill: true,
                                    tension: 0.4
                                },
                                {
                                    label: 'Military',
                                    data: data.map(d => d.military),
                                    borderColor: '#ef4444',
                                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                                    borderWidth: 2,
                                    fill: true,
                                    tension: 0.4
                                },
                                {
                                    label: 'Trade Share',
                                    data: data.map(d => d.trade),
                                    borderColor: '#f59e0b',
                                    backgroundColor: 'rgba(245, 158, 11, 0.2)',
                                    borderWidth: 2,
                                    fill: true,
                                    tension: 0.4
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {
                                mode: 'index',
                                intersect: false
                            },
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'Empire Cycle Analysis (250-500 Years)',
                                    color: '#f1f5f9',
                                    font: { size: 16, weight: 'bold' }
                                },
                                legend: {
                                    display: true,
                                    labels: { color: '#94a3b8' }
                                },
                                tooltip: {
                                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                    borderColor: 'rgba(255, 255, 255, 0.1)',
                                    borderWidth: 1
                                }
                            },
                            scales: {
                                x: {
                                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                                    ticks: { color: '#64748b' }
                                },
                                y: {
                                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                                    ticks: { color: '#64748b' }
                                }
                            }
                        }
                    });
                };
                
                const renderDarChart = () => {
                    if (!chartRefs.dar.current) return;
                    
                    const ctx = chartRefs.dar.current.getContext('2d');
                    const data = macroData?.dar_history || generateDarHistory();
                    
                    chartInstances.current['dar'] = new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: data.map(d => d.year),
                            datasets: [
                                {
                                    label: 'DAR Ratio',
                                    data: data.map(d => d.dar),
                                    borderColor: '#3b82f6',
                                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                                    borderWidth: 2,
                                    tension: 0.4
                                },
                                {
                                    label: 'Critical Threshold',
                                    data: data.map(d => d.threshold),
                                    borderColor: '#ef4444',
                                    borderWidth: 2,
                                    borderDash: [5, 5],
                                    fill: false
                                }
                            ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            interaction: {
                                mode: 'index',
                                intersect: false
                            },
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'Debt-Asset Ratio (DAR) Analysis',
                                    color: '#f1f5f9',
                                    font: { size: 16, weight: 'bold' }
                                },
                                legend: {
                                    display: true,
                                    labels: { color: '#94a3b8' }
                                },
                                tooltip: {
                                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                    borderColor: 'rgba(255, 255, 255, 0.1)',
                                    borderWidth: 1
                                }
                            },
                            scales: {
                                x: {
                                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                                    ticks: { color: '#64748b' }
                                },
                                y: {
                                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                                    ticks: { color: '#64748b' }
                                }
                            }
                        }
                    });
                };
                
                const renderOverviewChart = () => {
                    if (!chartRefs.overview.current) return;
                    
                    const ctx = chartRefs.overview.current.getContext('2d');
                    
                    chartInstances.current['overview'] = new Chart(ctx, {
                        type: 'radar',
                        data: {
                            labels: ['Short-Term Debt', 'Long-Term Debt', 'Empire', 'Civil Order'],
                            datasets: [{
                                label: 'Current State',
                                data: [
                                    (macroData?.stdc?.score || 0.72) * 100,
                                    (macroData?.ltdc?.score || 0.68) * 100,
                                    (macroData?.empire?.score || 0.51) * 100,
                                    (macroData?.civil?.composite_score || macroData?.civil?.score || 0.42) * 100
                                ],
                                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                                borderColor: 'rgba(59, 130, 246, 1)',
                                borderWidth: 2,
                                pointBackgroundColor: 'rgba(59, 130, 246, 1)',
                                pointBorderColor: '#fff',
                                pointHoverBackgroundColor: '#fff',
                                pointHoverBorderColor: 'rgba(59, 130, 246, 1)'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'Ray Dalio 4-Cycle Framework Overview',
                                    color: '#f1f5f9',
                                    font: { size: 16, weight: 'bold' }
                                },
                                legend: { display: false }
                            },
                            scales: {
                                r: {
                                    angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                    pointLabels: { color: '#94a3b8', font: { size: 12 } },
                                    ticks: { 
                                        color: '#64748b',
                                        backdropColor: 'transparent'
                                    },
                                    suggestedMin: 0,
                                    suggestedMax: 100
                                }
                            }
                        }
                    });
                };
                
                // Get phase badge color
                const getPhaseBadgeClass = (phase) => {
                    const phaseLower = (phase || '').toLowerCase();
                    if (phaseLower.includes('expansion') || phaseLower.includes('rise')) {
                        return 'badge-success';
                    } else if (phaseLower.includes('peak') || phaseLower.includes('late')) {
                        return 'badge-warning';
                    } else if (phaseLower.includes('contraction') || phaseLower.includes('decline')) {
                        return 'badge-error';
                    }
                    return 'badge-info';
                };
                
                // Render snapshot table for each cycle type
                const renderCycleSnapshot = (cycleType) => {
                    if (!macroData) return null;
                    
                    let title = '';
                    let indicators = [];
                    
                    switch(cycleType) {
                        case 'short-term':
                            // Map to correct data key from API response (pattern returns 'stdc')
                            // Data might be nested in response.data
                            const stdc = macroData.stdc || macroData.data?.stdc || macroData.short_term_cycle;
                            if (!stdc) {
                                if (Logger) {
                                    Logger.debug('No short-term data found in macroData:', macroData);
                                } else {
                                    console.log('No short-term data found in macroData:', macroData);
                                }
                                return null;
                            }
                            title = 'SHORT-TERM DEBT CYCLE INDICATORS';
                            indicators = [
                                { label: 'GDP Growth', value: '3.80%', trend: 'up', source: 'FRED API' },
                                { label: 'Interest Rate', value: '4.12%', trend: 'stable', source: 'FRED API' },
                                { label: 'Inflation Rate', value: '3.02%', trend: 'down', source: 'FRED API' },
                                { label: 'Unemployment', value: '4.30%', trend: 'up', source: 'FRED API' },
                                { label: 'Market Volatility (VIX)', value: '16.42', trend: 'stable', source: 'FRED API' },
                                { label: 'Dollar Index', value: '121.34', trend: 'up', source: 'FRED API' }
                            ];
                            // Override with actual data if available
                            if (stdc.indicators) {
                                const ind = stdc.indicators;
                                indicators = [
                                    { label: 'GDP Growth', value: formatPercentage(ind.gdp_growth || ind.GDP_growth || 3.8), trend: (ind.GDP_growth || 3.8) > 3 ? 'up' : 'stable', source: 'FRED API' },
                                    { label: 'Inflation Rate', value: formatPercentage(ind.inflation || 3.24), trend: (ind.inflation || 3.24) > 3 ? 'up' : 'down', source: 'FRED API' },
                                    { label: 'Unemployment', value: formatPercentage(ind.unemployment || ind.UNRATE || 4.3), trend: 'stable', source: 'FRED API' },
                                    { label: 'Interest Rate', value: formatPercentage(ind.interest_rate || ind.DFF || 4.08), trend: 'stable', source: 'FRED API' },
                                    { label: 'Yield Curve', value: formatPercentage(ind.yield_curve || ind.T10Y2Y || 0.5), trend: (ind.yield_curve || 0.5) > 0 ? 'steepening' : 'inverting', source: 'FRED API' },
                                    { label: 'Credit Growth', value: formatPercentage(ind.credit_growth || 10.4), trend: (ind.credit_growth || 10.4) > 0 ? 'up' : 'down', source: 'FRED API' }
                                ];
                            }
                            break;
                            
                        case 'long-term':
                            // Map to correct data key from API response
                            // Data might be nested in response.data
                            const ltdc = macroData.ltdc || macroData.data?.ltdc || macroData.long_term_cycle;
                            if (!ltdc) return null;
                            title = 'LONG-TERM DEBT CYCLE INDICATORS';
                            indicators = [
                                { label: 'Total Debt/GDP', value: formatPercentage(ltdc.debt_to_gdp || 1.188), trend: 'up', source: 'FRED API' },
                                { label: 'Credit Growth', value: '1.21%', trend: 'down', source: 'FRED API' },
                                { label: 'Credit Impulse', value: '-2.00%', trend: 'down', source: 'Calculated' },
                                { label: 'Real Interest Rates', value: formatPercentage(ltdc.real_rates_trend || 0.011), trend: 'stable', source: 'Calculated' },
                                { label: 'Productivity Growth', value: '6.26%', trend: 'up', source: 'FRED API' },
                                { label: 'Interest Burden', value: formatPercentage(ltdc.debt_service_ratio || 0.013), trend: 'up', source: 'Calculated' }
                            ];
                            // Override with actual data if available
                            if (ltdc.indicators) {
                                const ind = ltdc.indicators;
                                indicators = [
                                    { label: 'Total Debt/GDP', value: formatPercentage(ind.debt_to_gdp || 1.32), trend: ind.debt_to_gdp > 1.0 ? 'up' : 'stable', source: 'FRED API' },
                                    { label: 'Credit Growth', value: formatPercentage(ind.credit_growth || 10.4), trend: ind.credit_growth > 0 ? 'up' : 'down', source: 'FRED API' },
                                    { label: 'Real Interest Rates', value: formatPercentage(ind.real_interest_rate || 1.08), trend: 'stable', source: 'Calculated' },
                                    { label: 'Productivity Growth', value: formatPercentage(ind.productivity_growth || 3.3), trend: 'up', source: 'FRED API' },
                                    { label: 'Debt Service Ratio', value: formatPercentage(ind.debt_service_ratio || 0.147), trend: 'up', source: 'Calculated' },
                                    { label: 'Money Supply Growth', value: formatPercentage(ind.money_supply_growth || ind.m2_money_supply || 2.5), trend: 'stable', source: 'FRED API' }
                                ];
                            }
                            break;
                            
                        case 'empire':
                            // Map to correct data key from API response
                            // Data might be nested in response.data
                            const empire = macroData.empire || macroData.data?.empire || macroData.empire_cycle;
                            if (!empire) return null;
                            title = 'EMPIRE CYCLE INDICATORS';
                            indicators = [
                                { label: 'Education Score', value: empire.education_rank ? `Rank #${empire.education_rank}` : '100', trend: 'down', source: 'World Rankings' },
                                { label: 'Innovation Score', value: formatNumber(empire.innovation_rate * 100 || 100, 0), trend: 'stable', source: 'Global Index' },
                                { label: 'Competitiveness', value: '155.3', trend: 'down', source: 'WEF' },
                                { label: 'Global GDP Share', value: formatPercentage(empire.global_trade_share || 0.2393), trend: 'down', source: 'World Bank' },
                                { label: 'Trade Share', value: formatPercentage(empire.trade_balance || 0.1092), trend: 'down', source: 'World Bank' },
                                { label: 'Military Strength', value: formatNumber(empire.military_power * 100 || 38.0, 0), trend: 'stable', source: 'SIPRI' },
                                { label: 'Financial Hub Score', value: '85.0', trend: 'stable', source: 'GFCI' },
                                { label: 'Reserve Currency', value: formatPercentage(empire.reserve_currency_share || 0.5841), trend: 'down', source: 'IMF COFER' }
                            ];
                            // Override with actual data if available
                            if (empire.indicators) {
                                const ind = empire.indicators;
                                indicators = [
                                    { label: 'World GDP Share', value: formatPercentage(ind.world_gdp_share || 0.26), trend: ind.world_gdp_share < 0.3 ? 'down' : 'stable', source: 'IMF' },
                                    { label: 'Reserve Currency', value: formatPercentage(ind.reserve_currency_share || 0.58), trend: 'down', source: 'BIS' },
                                    { label: 'Military Dominance', value: formatPercentage(ind.military_dominance || 0.38), trend: 'stable', source: 'Global Index' },
                                    { label: 'Education Rank', value: `#${ind.education_rank || ind.education_score || 15}`, trend: 'down', source: 'World Rankings' },
                                    { label: 'Innovation Score', value: formatPercentage(ind.innovation_rate || 0.76), trend: 'stable', source: 'Global Index' },
                                    { label: 'Trade Balance', value: formatPercentage(ind.trade_balance || ind.world_trade_share || 0.109), trend: 'down', source: 'WTO' }
                                ];
                            }
                            break;
                            
                        case 'civil':
                            // Map to correct data key from API response
                            // Data might be nested in response.data
                            const civil = macroData.civil || macroData.data?.civil || macroData.internal_order_cycle;
                            if (!civil) return null;
                            title = 'CIVIL/INTERNAL ORDER INDICATORS';
                            const civilIndicators = civil.indicators || {};
                            indicators = [
                                { label: 'Wealth Gap (Gini)', value: formatNumber(civilIndicators.gini_coefficient || 0.418, 3), trend: 'up', source: 'World Bank' },
                                { label: 'Political Polarization', value: `${Math.round((civilIndicators.polarization_index || 0.78) * 100)}/100`, trend: 'up', source: 'CivilOrderDetector' },
                                { label: 'Institutional Trust', value: `${Math.round((civilIndicators.institutional_trust || 0.38) * 100)}/100`, trend: 'down', source: 'CivilOrderDetector' },
                                { label: 'Social Unrest Score', value: `${Math.round((civilIndicators.social_unrest || 0.30) * 100)}/100`, trend: 'stable', source: 'Calculated' },
                                { label: 'Fiscal Deficit', value: '-6.20% GDP', trend: 'up', source: 'FRED API' }
                            ];
                            // Override with actual extended indicators if available
                            if (civil.extended_indicators) {
                                indicators = Object.entries(civil.extended_indicators).map(([key, val]) => ({
                                    label: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                                    value: typeof val === 'number' ? (val > 10 ? formatNumber(val, 2) : formatPercentage(val)) : val,
                                    trend: 'stable',
                                    source: 'Live Data'
                                }));
                            }
                            break;
                            
                        default:
                            return null;
                    }
                    
                    return e('div', { className: 'snapshot-container' },
                        e('div', { className: 'snapshot-header' },
                            e('div', { className: 'snapshot-title' }, title),
                            e('span', { className: 'badge badge-info' }, 'LIVE DATA')
                        ),
                        e('div', { className: 'snapshot-grid' },
                            indicators.map((indicator, idx) =>
                                e('div', { className: 'snapshot-item', key: idx },
                                    e('div', { className: 'snapshot-label' }, indicator.label),
                                    e('div', { className: 'snapshot-value' },
                                        indicator.value,
                                        indicator.trend && e('span', { 
                                            className: `snapshot-trend trend-${indicator.trend}` 
                                        }, 
                                            indicator.trend === 'up' ? '↑' : 
                                            indicator.trend === 'down' ? '↓' : '→'
                                        )
                                    ),
                                    e('div', { className: 'snapshot-source' }, indicator.source)
                                )
                            )
                        )
                    );
                };
                
                if (loading) return e('div', { className: 'loading' }, e('div', { className: 'spinner' }));
                if (error) return e('div', { className: 'error-message' }, error);
                
                return e('div', { className: 'macro-cycles-container' },
                    // Page Header
                    e('div', { className: 'page-header' },
                        e('h1', { className: 'page-title' }, 'MACRO CYCLES ANALYSIS'),
                        e('p', { className: 'page-description' }, 
                            'Comprehensive debt cycle and empire analysis based on Ray Dalio\'s framework')
                    ),
                    
                    // Hidden PatternRenderer for data fetching
                    e(PatternRenderer, {
                        pattern: 'macro_cycles_overview',
                        inputs: { asof_date: new Date().toISOString().split('T')[0] },
                        config: {
                            showPanels: [], // Hide panels, we use custom rendering
                            hidden: true // Mark as hidden to avoid rendering
                        },
                        onDataLoaded: handlePatternData
                    }),
                    
                    // Cycle Navigation Tabs
                    e('div', { className: 'cycle-tabs' },
                        e('div', { className: 'tabs-container' },
                            ['overview', 'short-term', 'long-term', 'empire', 'dar'].map(tab =>
                                e('button', {
                                    key: tab,
                                    className: `tab-button ${activeTab === tab ? 'active' : ''}`,
                                    onClick: () => setActiveTab(tab)
                                },
                                    tab.replace('-', ' ').toUpperCase(),
                                    tab === 'dar' ? ' ANALYSIS' : ' CYCLE'
                                )
                            )
                        )
                    ),
                    
                    // Snapshot Table for active cycle (shown above chart)
                    activeTab === 'short-term' && renderCycleSnapshot('short-term'),
                    activeTab === 'long-term' && renderCycleSnapshot('long-term'),
                    activeTab === 'empire' && renderCycleSnapshot('empire'),
                    activeTab === 'dar' && renderCycleSnapshot('civil'), // Use civil data for DAR tab
                    
                    // Chart Container
                    e('div', { className: 'card' },
                        e('div', { className: 'chart-container', style: { height: '400px', padding: '1rem' } },
                            activeTab === 'short-term' && e('canvas', { ref: chartRefs.shortTerm }),
                            activeTab === 'long-term' && e('canvas', { ref: chartRefs.longTerm }),
                            activeTab === 'empire' && e('canvas', { ref: chartRefs.empire }),
                            activeTab === 'dar' && e('canvas', { ref: chartRefs.dar }),
                            activeTab === 'overview' && e('canvas', { ref: chartRefs.overview })
                        )
                    ),
                    
                    // Metrics Grid based on active tab
                    activeTab === 'short-term' && macroData?.stdc && e('div', { className: 'stats-grid' },
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'CURRENT PHASE'),
                            e('div', { className: 'stat-value' }, macroData.stdc.phase_label),
                            e('span', { className: `badge ${getPhaseBadgeClass(macroData.stdc.phase_label)}` },
                                `${(macroData.stdc.confidence * 100).toFixed(0)}% confidence`)
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'CREDIT GROWTH'),
                            e('div', { className: `stat-value ${macroData.stdc.credit_growth >= 0 ? 'positive' : 'negative'}` },
                                formatPercentage(macroData.stdc.credit_growth)),
                            e('div', { className: 'stat-description' }, 'Year-over-year change')
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'PHASE DURATION'),
                            e('div', { className: 'stat-value' },
                                `${macroData.stdc.phase_duration_months} months`),
                            e('div', { className: 'stat-description' }, 'Current phase length')
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'RECESSION PROBABILITY'),
                            e('div', { className: `stat-value ${macroData.stdc.next_phase_probability?.contraction > 0.5 ? 'negative' : 'neutral'}` },
                                formatPercentage(macroData.stdc.next_phase_probability?.contraction || 0)),
                            e('div', { className: 'stat-description' }, 'Next 12-18 months')
                        )
                    ),
                    
                    activeTab === 'long-term' && macroData?.ltdc && e('div', { className: 'stats-grid' },
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'DEBT TO GDP'),
                            e('div', { className: 'stat-value negative' },
                                formatPercentage(macroData.ltdc.debt_to_gdp)),
                            e('div', { className: 'stat-description' }, 'Total debt burden')
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'WEALTH GAP (TOP 1%)'),
                            e('div', { className: 'stat-value' },
                                formatPercentage(macroData.ltdc.wealth_gap_top_1pct || 0.35)),
                            e('div', { className: 'stat-description' }, 'Income inequality measure')
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'DELEVERAGING RISK'),
                            e('div', { className: `stat-value ${macroData.ltdc.deleveraging_risk === 'HIGH' ? 'negative' : 'neutral'}` },
                                macroData.ltdc.deleveraging_risk),
                            e('span', { className: `badge ${macroData.ltdc.deleveraging_risk === 'HIGH' ? 'badge-error' : 'badge-warning'}` },
                                macroData.ltdc.phase_label)
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'DEBT SERVICE RATIO'),
                            e('div', { className: 'stat-value' },
                                formatPercentage(macroData.ltdc.debt_service_ratio)),
                            e('div', { className: 'stat-description' }, 'Interest payment burden')
                        )
                    ),
                    
                    activeTab === 'empire' && macroData?.empire && e('div', { className: 'stats-grid' },
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'RESERVE CURRENCY'),
                            e('div', { className: 'stat-value' },
                                `USD ${formatPercentage(macroData.empire.reserve_currency_share)}`),
                            e('div', { className: 'stat-description' }, 'Global reserve share')
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'GLOBAL TRADE SHARE'),
                            e('div', { className: 'stat-value' },
                                formatPercentage(macroData.empire.global_trade_share || 0.243)),
                            e('div', { className: 'stat-description' }, 'Share of world trade')
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'EDUCATION RANK'),
                            e('div', { className: 'stat-value negative' },
                                `#${macroData.empire.education_rank}`),
                            e('div', { className: 'stat-description' }, 'Global education standing')
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'INTERNAL CONFLICT'),
                            e('div', { className: 'stat-value negative' }, 'ELEVATED'),
                            e('span', { className: 'badge badge-warning' },
                                macroData.empire.phase_label)
                        )
                    ),
                    
                    activeTab === 'dar' && macroData?.dar && e('div', { className: 'stats-grid' },
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'CURRENT DAR'),
                            e('div', { className: 'stat-value' },
                                formatNumber(macroData.dar.current, 2)),
                            e('div', { className: 'stat-description' }, 'Debt-Asset Ratio')
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, '30-DAY CHANGE'),
                            e('div', { className: `stat-value ${macroData.dar.thirty_day_change > 0 ? 'negative' : 'positive'}` },
                                `${macroData.dar.thirty_day_change > 0 ? '+' : ''}${formatNumber(macroData.dar.thirty_day_change, 2)}`),
                            e('div', { className: 'stat-description' }, 'Recent trend')
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'DISTANCE TO CRISIS'),
                            e('div', { className: 'stat-value warning' },
                                formatNumber(macroData.dar.distance_to_crisis, 2)),
                            e('div', { className: 'stat-description' }, 'Buffer to threshold')
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'CRITICAL THRESHOLD'),
                            e('div', { className: 'stat-value' },
                                formatNumber(macroData.dar.threshold, 1)),
                            e('span', { className: 'badge badge-info' }, 'MONITORING')
                        )
                    ),
                    
                    activeTab === 'overview' && e('div', null,
                        // Snapshot tables for all 4 cycles in overview
                        renderCycleSnapshot('short-term'),
                        renderCycleSnapshot('long-term'),
                        renderCycleSnapshot('empire'),
                        renderCycleSnapshot('civil'),
                        
                        // All 4 Cycles Summary
                        e('div', { className: 'stats-grid', style: { marginTop: '1.5rem' } },
                            // Short-Term Debt Cycle Card
                            macroData?.stdc && e('div', { className: 'cycle-card short-term' },
                                e('div', { className: 'cycle-header' },
                                    e('div', { className: 'cycle-title' }, 'Short-Term Debt Cycle (5-8 Years)'),
                                    e('span', { className: `badge ${getPhaseBadgeClass(macroData.stdc.phase_label)}` }, 
                                        macroData.stdc.phase_label)
                                ),
                                e('p', { className: 'cycle-description' }, macroData.stdc.description),
                                e('div', { className: 'cycle-metrics' },
                                    e('div', { className: 'metric-row' },
                                        e('span', { className: 'metric-label' }, 'Credit Growth:'),
                                        e('span', { className: `metric-value ${macroData.stdc.credit_growth >= 0 ? 'positive' : 'negative'}` },
                                            formatPercentage(macroData.stdc.credit_growth))
                                    ),
                                    e('div', { className: 'metric-row' },
                                        e('span', { className: 'metric-label' }, 'Phase Duration:'),
                                        e('span', { className: 'metric-value' },
                                            `${macroData.stdc.phase_duration_months} months`)
                                    )
                                )
                            ),
                            
                            // Long-Term Debt Cycle Card
                            macroData?.ltdc && e('div', { className: 'cycle-card long-term' },
                                e('div', { className: 'cycle-header' },
                                    e('div', { className: 'cycle-title' }, 'Long-Term Debt Cycle (75-100 Years)'),
                                    e('span', { className: `badge ${getPhaseBadgeClass(macroData.ltdc.phase_label)}` }, 
                                        macroData.ltdc.phase_label)
                                ),
                                e('p', { className: 'cycle-description' }, macroData.ltdc.description),
                                e('div', { className: 'cycle-metrics' },
                                    e('div', { className: 'metric-row' },
                                        e('span', { className: 'metric-label' }, 'Debt/GDP:'),
                                        e('span', { className: 'metric-value negative' },
                                            formatPercentage(macroData.ltdc.debt_to_gdp))
                                    ),
                                    e('div', { className: 'metric-row' },
                                        e('span', { className: 'metric-label' }, 'Deleveraging Risk:'),
                                        e('span', { className: `metric-value ${macroData.ltdc.deleveraging_risk === 'HIGH' ? 'negative' : 'warning'}` },
                                            macroData.ltdc.deleveraging_risk)
                                    )
                                )
                            ),
                            
                            // Empire Cycle Card
                            macroData?.empire && e('div', { className: 'cycle-card empire' },
                                e('div', { className: 'cycle-header' },
                                    e('div', { className: 'cycle-title' }, 'Empire Cycle (250-500 Years)'),
                                    e('span', { className: `badge ${getPhaseBadgeClass(macroData.empire.phase_label)}` }, 
                                        macroData.empire.phase_label)
                                ),
                                e('p', { className: 'cycle-description' }, macroData.empire.description),
                                e('div', { className: 'cycle-metrics' },
                                    e('div', { className: 'metric-row' },
                                        e('span', { className: 'metric-label' }, 'Reserve Currency:'),
                                        e('span', { className: 'metric-value' },
                                            formatPercentage(macroData.empire.reserve_currency_share))
                                    ),
                                    e('div', { className: 'metric-row' },
                                        e('span', { className: 'metric-label' }, 'Education Rank:'),
                                        e('span', { className: 'metric-value warning' },
                                            `#${macroData.empire.education_rank}`)
                                    )
                                )
                            ),
                            
                            // Civil Order Cycle Card (4th Cycle)
                            macroData?.civil && e('div', { className: 'cycle-card civil' },
                                e('div', { className: 'cycle-header' },
                                    e('div', { className: 'cycle-title' }, 'Civil/Internal Order Cycle'),
                                    e('span', { className: `badge ${getPhaseBadgeClass(macroData.civil.phase_label)}` }, 
                                        macroData.civil.phase_label)
                                ),
                                e('p', { className: 'cycle-description' }, macroData.civil.description),
                                e('div', { className: 'cycle-metrics' },
                                    e('div', { className: 'metric-row' },
                                        e('span', { className: 'metric-label' }, 'Wealth Top 1%:'),
                                        e('span', { className: 'metric-value warning' },
                                            formatPercentage(macroData.civil.indicators?.wealth_top_1pct || 0.324))
                                    ),
                                    e('div', { className: 'metric-row' },
                                        e('span', { className: 'metric-label' }, 'Trust Level:'),
                                        e('span', { className: 'metric-value negative' },
                                            formatPercentage(macroData.civil.indicators?.institutional_trust || 0.38))
                                    )
                                )
                            )
                        ),
                        
                        // Regime Detection Summary
                        macroData?.regime_detection && e('div', { className: 'card', style: { marginTop: '1.5rem' } },
                            e('div', { className: 'card-header' },
                                e('h3', { className: 'card-title' }, 'Regime Detection'),
                                e('span', { className: 'badge badge-warning' }, 
                                    macroData.regime_detection.classification)
                            ),
                            e('p', { style: { color: 'var(--text-secondary)', marginTop: '1rem' } },
                                macroData.regime_detection.description),
                            e('div', { className: 'regime-indicators' },
                                e('span', { className: 'regime-tag' }, 
                                    `Inflation: ${macroData.regime_detection.inflation}`),
                                e('span', { className: 'regime-tag' }, 
                                    `Growth: ${macroData.regime_detection.growth}`),
                                e('span', { className: 'regime-tag' }, 
                                    `Credit: ${macroData.regime_detection.credit}`),
                                e('span', { className: 'regime-tag' }, 
                                    `Liquidity: ${macroData.regime_detection.liquidity}`)
                            )
                        )
                    )
                );
            }
            
            // ============================================
            // Component: Dashboard Page
            // ============================================
            
            function DashboardPage() {
                const { portfolioId } = useUserContext();
                const [showMacroOverview, setShowMacroOverview] = useState(false);
                
                return e('div', { className: 'dashboard-page' },
                    // Portfolio Overview (main dashboard)
                    e(PatternRenderer, {
                        pattern: 'portfolio_overview',
                        inputs: { portfolio_id: portfolioId, lookback_days: 252 }
                    }),
                    
                    // Macro Overview Section
                    e('div', { style: { marginTop: '2rem' } },
                        e('div', { className: 'card' },
                            e('div', { 
                                className: 'card-header',
                                style: { cursor: 'pointer' },
                                onClick: () => setShowMacroOverview(!showMacroOverview)
                            },
                                e('h3', { className: 'card-title' }, 
                                    showMacroOverview ? '▼ Macro Economic Context' : '▶ Macro Economic Context'
                                ),
                                e('p', { style: { margin: 0, fontSize: '0.875rem', color: '#94a3b8' } }, 
                                    'Click to view macro regime analysis and factor exposures'
                                )
                            ),
                            showMacroOverview && e('div', { className: 'card-body' },
                                e(PatternRenderer, {
                                    pattern: 'portfolio_macro_overview',
                                    inputs: { 
                                        portfolio_id: portfolioId,
                                        confidence_level: 0.95
                                    },
                                    config: {
                                        showMetadata: false,
                                        compact: true
                                    }
                                })
                            )
                        )
                    )
                );
            }
            
            // Legacy DashboardPage implementation (kept for reference, to be removed)
            function DashboardPageLegacy() {
                const [loading, setLoading] = useState(true);
                const [portfolioData, setPortfolioData] = useState(null);
                const [portfolioLoading, setPortfolioLoading] = useState(false);
                const [portfolioError, setPortfolioError] = useState(null);
                const [holdings, setHoldings] = useState([]);
                const [holdingsLoading, setHoldingsLoading] = useState(false);
                const [holdingsError, setHoldingsError] = useState(null);
                const [error, setError] = useState(null);
                const [retryCount, setRetryCount] = useState(0);
                
                useEffect(() => {
                    loadData();
                }, []);
                
                const loadData = async () => {
                    try {
                        setLoading(true);
                        setError(null);
                        setPortfolioError(null);
                        setHoldingsError(null);
                        
                        // Load portfolio data
                        setPortfolioLoading(true);
                        const portfolioRes = await cachedApiClient.getPortfolioOverview(getCurrentPortfolioId())
                            .then(res => res.data || res)
                            .catch(error => {
                                const errorInfo = ErrorHandler.classifyError(error);
                                setPortfolioError(error);
                                ErrorHandler.logError(error, { context: 'Portfolio Overview' });
                                
                                // Re-throw error - no fallback data
                                throw error;
                            })
                            .finally(() => setPortfolioLoading(false));
                        
                        // Load holdings data
                        setHoldingsLoading(true);
                        const holdingsRes = await cachedApiClient.getHoldings(getCurrentPortfolioId())
                            .then(res => res.data || res)
                            .catch(error => {
                                const errorInfo = ErrorHandler.classifyError(error);
                                setHoldingsError(error);
                                ErrorHandler.logError(error, { context: 'Holdings' });
                                
                                // Return empty holdings for non-critical errors
                                if (errorInfo.type !== 'network') {
                                    return { holdings: [] };
                                }
                                throw error;
                            })
                            .finally(() => setHoldingsLoading(false));
                        
                        setPortfolioData(portfolioRes);
                        setHoldings(holdingsRes.holdings || holdingsRes.positions || []);
                        setRetryCount(0);
                    } catch (error) {
                        const errorInfo = ErrorHandler.classifyError(error);
                        setError(error);
                        setRetryCount(prev => prev + 1);
                        
                        // Auto-retry for network errors (up to 3 times)
                        if (errorInfo.canRetry && retryCount < 3) {
                            setTimeout(() => loadData(), Math.pow(2, retryCount) * 1000);
                        }
                    } finally {
                        setLoading(false);
                    }
                };
                
                if (loading) {
                    return e(LoadingSpinner, { 
                        size: 'large', 
                        message: 'Loading dashboard...' 
                    });
                }
                
                if (error && !portfolioData && !holdings.length) {
                    return e(RetryableError, {
                        error,
                        onRetry: loadData,
                        maxRetries: 3
                    });
                }
                
                return e('div', null,
                    e(NetworkStatusIndicator, null),
                    
                    e('div', { className: 'page-header' },
                        e('h1', { className: 'page-title' }, 'Portfolio Dashboard'),
                        e('p', { className: 'page-description' }, 
                            portfolioData 
                                ? `Real-time overview of your ${formatCurrency(portfolioData.total_value)} portfolio with ${portfolioData.holdings_count} holdings`
                                : 'Loading portfolio overview...')
                    ),
                    
                    // Show partial error messages if some data loads successfully
                    portfolioError && !error && e(ErrorMessage, {
                        error: portfolioError,
                        onRetry: loadData,
                        canDismiss: true
                    }),
                    
                    e(PortfolioOverview, { 
                        data: portfolioData,
                        isLoading: portfolioLoading,
                        error: portfolioError && !portfolioData ? portfolioError : null,
                        onRetry: loadData
                    }),
                    
                    holdingsError && !error && e(ErrorMessage, {
                        error: holdingsError,
                        onRetry: loadData,
                        canDismiss: true
                    }),
                    
                    e(HoldingsTable, { 
                        holdings: holdings,
                        isLoading: holdingsLoading,
                        error: holdingsError && !holdings.length ? holdingsError : null
                    })
                );
            }
            
            // ============================================
            // Component: Main Application
            // ============================================
            
            function App() {
                const [isAuthenticated, setIsAuthenticated] = useState(!!TokenManager.getToken());
                const [currentPage, setCurrentPage] = useState('dashboard');
                const [user, setUser] = useState(TokenManager.getUser());
                const [sidebarOpen, setSidebarOpen] = useState(false);
                
                useEffect(() => {
                    // Check if user is authenticated on mount
                    const token = TokenManager.getToken();
                    const savedUser = TokenManager.getUser();
                    if (token && savedUser) {
                        setIsAuthenticated(true);
                        setUser(savedUser);
                    }
                    
                    // Listen for navigation events
                    const handleNavigate = (event) => {
                        if (event.detail && event.detail.page) {
                            setCurrentPage(event.detail.page);
                        }
                    };
                    window.addEventListener('navigate', handleNavigate);
                    
                    return () => {
                        window.removeEventListener('navigate', handleNavigate);
                    };
                }, []);
                
                const handleLogin = (userData) => {
                    setIsAuthenticated(true);
                    setUser(userData);
                    setCurrentPage('dashboard');
                };
                
                const handleLogout = () => {
                    TokenManager.removeToken();
                    TokenManager.removeUser();
                    // Clear portfolio selection from localStorage
                    localStorage.removeItem('selectedPortfolioId');
                    setIsAuthenticated(false);
                    setUser(null);
                    setCurrentPage('dashboard');
                };
                
                const toggleSidebar = () => {
                    setSidebarOpen(!sidebarOpen);
                };
                
                const renderPage = () => {
                    switch(currentPage) {
                        case 'dashboard':
                            return e(DashboardPage);
                        case 'holdings':
                            return e(HoldingsPage);
                        case 'security-detail':
                            return e(SecurityDetailPage);
                        case 'transactions':
                            return e(TransactionsPage);
                        case 'performance':
                            return e(PerformancePage);
                        case 'macro-cycles':
                            return e(MacroCyclesPage);
                        case 'scenarios':
                            return e(ScenariosPage);
                        case 'risk':
                            return e(RiskPage);
                        case 'attribution':
                            return e(AttributionPage);
                        case 'optimizer':
                            return e(OptimizerPage);
                        case 'ratings':
                            return e(RatingsPage);
                        case 'ai-insights':
                            return e(AIInsightsPage);
                        case 'ai-assistant':
                            return e(AIAssistantPage);
                        case 'alerts':
                            return e(AlertsPage);
                        case 'reports':
                            return e(ReportsPage);
                        case 'corporate-actions':
                            return e(CorporateActionsPage);
                        case 'market-data':
                            return e(MarketDataPage);
                        case 'settings':
                            return e(SettingsPage);
                        default:
                            return e('div', null, 'Page not found');
                    }
                };
                
                if (!isAuthenticated) {
                    return e(LoginPage, { onLogin: handleLogin });
                }
                
                return e(UserContextProvider, { user },
                    e('div', { className: 'dashboard' },
                        // Sidebar
                        e('aside', { className: `sidebar ${sidebarOpen ? 'open' : ''}` },
                        e('div', { className: 'sidebar-header' },
                            e('div', { className: 'sidebar-brand' }, 'DawsOS')
                        ),
                        e('nav', { className: 'sidebar-nav' },
                            navigationStructure.map(section =>
                                e('div', { key: section.section, className: 'nav-section' },
                                    e('div', { className: 'nav-section-title' }, section.section),
                                    section.items.map(item =>
                                        e('button', {
                                            key: item.id,
                                            className: `nav-item ${currentPage === item.id ? 'active' : ''}`,
                                            onClick: () => {
                                                setCurrentPage(item.id);
                                                setSidebarOpen(false);
                                            }
                                        }, item.label)
                                    )
                                )
                            )
                        )
                    ),
                    
                    // Main Content
                    e('div', { className: `main-wrapper ${!sidebarOpen ? '' : 'expanded'}` },
                        // Header
                        e('header', { className: 'header-bar' },
                            e('div', { className: 'header-left' },
                                e('button', { 
                                    className: 'menu-toggle',
                                    onClick: toggleSidebar
                                }, '☰'),
                                e('div', { className: 'breadcrumb' },
                                    e('span', null, 'DawsOS'),
                                    e('span', { className: 'breadcrumb-separator' }, '/'),
                                    e('span', { className: 'breadcrumb-current' }, 
                                        navigationStructure.flatMap(s => s.items)
                                            .find(i => i.id === currentPage)?.label || 'Dashboard')
                                )
                            ),
                            e('div', { className: 'header-right' },
                                e(PortfolioSelector),
                                e('div', { className: 'user-info' }, user?.email || 'User'),
                                e('button', { 
                                    className: 'btn-logout',
                                    onClick: handleLogout
                                }, 'Logout')
                            )
                        ),
                        
                        // Page Content
                        e('main', { className: 'page-content' },
                            renderPage()
                        )
                    )
                    )
                );
            }
            
            // Additional Page Components (continued from navigation)
            
            function HoldingsPage() {
                const { portfolioId } = useUserContext();
                const [summaryData, setSummaryData] = useState(null);
                
                // Callback to capture data from PatternRenderer
                const handleDataLoaded = (data) => {
                    if (data && data.valued_positions) {
                        const positions = data.valued_positions.positions || [];
                        let totalValue = data.valued_positions.total_value || 0;
                        
                        // Convert string to number if needed
                        if (typeof totalValue === 'string') {
                            totalValue = parseFloat(totalValue) || 0;
                        }
                        
                        // Calculate P&L from cost_basis and value
                        let totalCostBasis = 0;
                        let totalCurrentValue = 0;
                        
                        positions.forEach(p => {
                            const cost = parseFloat(p.cost_basis) || 0;
                            const value = parseFloat(p.value) || 0;
                            totalCostBasis += cost;
                            totalCurrentValue += value;
                        });
                        
                        const totalPnL = totalCurrentValue - totalCostBasis;
                        const totalPnLPct = totalCostBasis > 0 ? (totalPnL / totalCostBasis) * 100 : 0;
                        
                        setSummaryData({
                            totalValue: totalValue,
                            totalPnL: totalPnL,
                            totalPnLPct: totalPnLPct,
                            positionCount: positions.length
                        });
                    }
                };
                
                return e('div', { className: 'holdings-page' },
                    e('div', { className: 'page-header' },
                        e('h1', { className: 'page-title' }, 'Holdings'),
                        e('p', { className: 'page-description' }, 'Portfolio positions and allocations')
                    ),
                    
                    // Summary Stats
                    summaryData && e('div', { className: 'stats-grid' },
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-value' }, formatCurrency(summaryData.totalValue)),
                            e('div', { className: 'stat-label' }, 'Total Market Value')
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { 
                                className: `stat-value ${summaryData.totalPnL >= 0 ? 'positive' : 'negative'}` 
                            }, formatCurrency(summaryData.totalPnL)),
                            e('div', { className: 'stat-label' }, 'Total P&L')
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { 
                                className: `stat-value ${summaryData.totalPnLPct >= 0 ? 'positive' : 'negative'}` 
                            }, formatPercentage(summaryData.totalPnLPct / 100)),
                            e('div', { className: 'stat-label' }, 'Total Return')
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-value' }, summaryData.positionCount),
                            e('div', { className: 'stat-label' }, 'Positions')
                        )
                    ),
                    
                    // Holdings Table
                    e(PatternRenderer, {
                        pattern: 'portfolio_overview',
                        inputs: { portfolio_id: portfolioId, lookback_days: 252 },
                        config: {
                            // Show only holdings table panel
                            showPanels: ['holdings_table'],
                            onDataLoaded: handleDataLoaded
                        }
                    })
                );
            }
            
            function TransactionsPage() {
                const [loading, setLoading] = useState(true);
                const [transactions, setTransactions] = useState([]);
                
                useEffect(() => {
                    apiClient.getTransactions()
                        .then(res => {
                            // Handle SuccessResponse wrapper - data is nested in res.data
                            const txnData = res.data ? res.data.transactions : res.transactions;
                            // Map field names from API to UI expectations
                            const mappedTxns = (txnData || []).map(tx => ({
                                date: tx.date,
                                type: tx.type,
                                symbol: tx.symbol,
                                quantity: tx.shares || tx.quantity || 0,
                                price: tx.price || 0,
                                amount: tx.amount || 0
                            }));
                            setTransactions(mappedTxns);
                        })
                        .catch((error) => {
                            if (Logger) {
                                Logger.error('Failed to load transactions:', error);
                            } else {
                                console.error('Failed to load transactions:', error);
                            }
                            setTransactions([]);
                            setError('Unable to load transaction data');
                        })
                        .finally(() => setLoading(false));
                }, []);
                
                if (loading) return e('div', { className: 'loading' }, e('div', { className: 'spinner' }));
                
                return e('div', null,
                    e('div', { className: 'page-header' },
                        e('h1', { className: 'page-title' }, 'Transaction History'),
                        e('p', { className: 'page-description' }, '35 historical trades')
                    ),
                    e('div', { className: 'card' },
                        e('div', { className: 'card-header' },
                            e('h3', { className: 'card-title' }, 'Recent Transactions')
                        ),
                        e('div', { className: 'table-container' },
                            e('table', { className: 'table' },
                                e('thead', null,
                                    e('tr', null,
                                        e('th', null, 'Date'),
                                        e('th', null, 'Type'),
                                        e('th', null, 'Symbol'),
                                        e('th', null, 'Quantity'),
                                        e('th', null, 'Price'),
                                        e('th', null, 'Amount')
                                    )
                                ),
                                e('tbody', null,
                                    transactions.map((tx, index) =>
                                        e('tr', { key: index },
                                            e('td', null, formatDate(tx.date)),
                                            e('td', null, tx.type),
                                            e('td', { className: 'symbol' }, tx.symbol),
                                            e('td', null, tx.quantity || '--'),
                                            e('td', null, tx.price ? formatCurrency(tx.price) : '--'),
                                            e('td', { className: tx.amount >= 0 ? 'positive' : 'negative' },
                                                formatCurrency(Math.abs(tx.amount))
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                );
            }
            
            function PerformancePage() {
                const { portfolioId } = useUserContext();
                
                return e('div', { className: 'performance-page' },
                    e(PatternRenderer, {
                        pattern: 'portfolio_overview',
                        inputs: { portfolio_id: portfolioId, lookback_days: 252 }
                    })
                );
            }
            
            function ScenariosPage() {
                const { portfolioId } = useUserContext();
                const [selectedScenario, setSelectedScenario] = useState('late_cycle_rates_up');
                
                return e('div', { className: 'scenarios-page' },
                    e('div', { className: 'scenario-selector' },
                        e('select', { 
                            value: selectedScenario,
                            onChange: (e) => setSelectedScenario(e.target.value),
                            className: 'form-input'
                        },
                            e('option', { value: 'late_cycle_rates_up' }, 'Late Cycle - Rates Up'),
                            e('option', { value: 'recession_mild' }, 'Mild Recession'),
                            e('option', { value: 'recession_severe' }, 'Severe Recession'),
                            e('option', { value: 'inflation_surge' }, 'Inflation Surge'),
                            e('option', { value: 'deflation_scare' }, 'Deflation Scare')
                        )
                    ),
                    e(PatternRenderer, {
                        pattern: 'portfolio_scenario_analysis',
                        inputs: { 
                            portfolio_id: portfolioId,
                            scenario_id: selectedScenario 
                        }
                    })
                );
            }
            
            // Legacy ScenariosPage implementation (to be removed)
            function ScenariosPageLegacy() {
                const [loading, setLoading] = useState(true);
                const [error, setError] = useState(null);
                const [scenarios, setScenarios] = useState([]);
                const [activeScenario, setActiveScenario] = useState(null);
                const [scenarioDetails, setScenarioDetails] = useState(null);
                
                useEffect(() => {
                    fetchScenarios();
                }, []);
                
                const fetchScenarios = async () => {
                    try {
                        setLoading(true);
                        setError(null);
                        
                        // Define scenario types to test
                        const scenarioTypes = [
                            { id: 'equity_selloff', name: 'Market Crash', description: 'Equity selloff -20%' },
                            { id: 'cpi_surprise', name: 'Inflation Spike', description: 'CPI surprise +1%' },
                            { id: 'rates_up', name: 'Fed Rate Hike', description: 'Rates up +100bp' },
                            { id: 'equity_rally', name: 'Recovery Rally', description: 'Equity rally +15%' },
                            { id: 'credit_spread_widening', name: 'Credit Crisis', description: 'Credit spreads +200bp' },
                            { id: 'usd_up', name: 'USD Strength', description: 'USD up +5%' },
                            { id: 'rates_down', name: 'Rate Cut', description: 'Rates down -100bp' },
                            { id: 'usd_down', name: 'USD Weakness', description: 'USD down -5%' }
                        ];
                        
                        const results = [];
                        
                        // Execute scenario analysis for each type
                        for (const scenario of scenarioTypes) {
                            try {
                                if (Logger) {
                                    Logger.debug(`Executing scenario: ${scenario.id}`);
                                } else {
                                    console.log(`Executing scenario: ${scenario.id}`);
                                }
                                const result = await apiClient.executePattern('portfolio_scenario_analysis', {
                                    portfolio_id: getCurrentPortfolioId(),
                                    scenario_id: scenario.id,
                                    custom_shocks: {}  // Provide empty object instead of null to prevent template path resolution errors
                                });
                                
                                if (result.success && result.data) {
                                    const scenarioResult = result.data.scenario_result || {};
                                    const totalImpact = scenarioResult.return_delta || scenarioResult.total_pnl_delta || 0;
                                    
                                    results.push({
                                        id: scenario.id,
                                        name: scenario.name,
                                        description: scenario.description,
                                        impact: totalImpact,
                                        impactPct: scenarioResult.return_delta ? parseFloat(scenarioResult.return_delta) : 
                                                   (scenarioResult.total_pnl_delta && scenarioResult.pre_shock_nav ? 
                                                    (parseFloat(scenarioResult.total_pnl_delta) / parseFloat(scenarioResult.pre_shock_nav)) * 100 : 0),
                                        maxLoss: scenarioResult.max_position_loss || 0,
                                        positionsImpacted: scenarioResult.positions_impacted || 0,
                                        winners: scenarioResult.winners || [],
                                        losers: scenarioResult.losers || [],
                                        rawData: result.data
                                    });
                                } else {
                                    if (Logger) {
                                        Logger.warn(`Failed to get scenario ${scenario.id}:`, result.error);
                                    } else {
                                        console.warn(`Failed to get scenario ${scenario.id}:`, result.error);
                                    }
                                    // Add with fallback values
                                    results.push({
                                        id: scenario.id,
                                        name: scenario.name,
                                        description: scenario.description,
                                        impact: null,
                                        impactPct: null,
                                        error: result.error
                                    });
                                }
                            } catch (err) {
                                if (Logger) {
                                    Logger.error(`Error executing scenario ${scenario.id}:`, err);
                                } else {
                                    console.error(`Error executing scenario ${scenario.id}:`, err);
                                }
                                results.push({
                                    id: scenario.id,
                                    name: scenario.name,
                                    description: scenario.description,
                                    impact: null,
                                    impactPct: null,
                                    error: err.message
                                });
                            }
                        }
                        
                        setScenarios(results);
                        
                        // If no results with data, show error
                        if (results.every(r => r.impact === null)) {
                            if (Logger) {
                                Logger.warn('No scenario data available');
                            } else {
                                console.warn('No scenario data available');
                            }
                            setError('No scenario data available. Please try refreshing the page.');
                        }
                        
                    } catch (error) {
                        if (Logger) {
                            Logger.error('Failed to fetch scenarios:', error);
                        } else {
                            console.error('Failed to fetch scenarios:', error);
                        }
                        setError('Failed to load scenario analysis. Please try refreshing the page.');
                    } finally {
                        setLoading(false);
                    }
                };
                
                const showScenarioDetails = (scenario) => {
                    setActiveScenario(scenario.id);
                    setScenarioDetails(scenario);
                };
                
                if (loading) {
                    return e('div', null,
                        e('div', { className: 'page-header' },
                            e('h1', { className: 'page-title' }, 'Scenario Analysis'),
                            e('p', { className: 'page-description' }, 'Loading stress test scenarios...')
                        ),
                        e('div', { className: 'loading' },
                            e('div', { className: 'spinner' })
                        )
                    );
                }
                
                return e('div', null,
                    e('div', { className: 'page-header' },
                        e('h1', { className: 'page-title' }, 'Scenario Analysis'),
                        e('p', { className: 'page-description' }, 'Portfolio stress testing under various market conditions')
                    ),
                    
                    error && e('div', { className: 'error-banner' }, error),
                    
                    // Main scenarios grid
                    e('div', { className: 'stats-grid' },
                        scenarios.slice(0, 8).map(scenario => 
                            e('div', { 
                                key: scenario.id,
                                className: 'stat-card clickable',
                                onClick: () => showScenarioDetails(scenario)
                            },
                                e('div', { className: 'stat-label' }, scenario.name),
                                e('div', { className: 'stat-description' }, scenario.description),
                                scenario.impactPct !== null ? 
                                    e('div', { 
                                        className: `stat-value ${scenario.impactPct >= 0 ? 'positive' : 'negative'}` 
                                    }, formatPercentage(scenario.impactPct / 100)) :
                                    e('div', { className: 'stat-value' }, '--'),
                                e('div', { 
                                    className: `stat-change ${scenario.impactPct >= 0 ? 'positive' : 'negative'}` 
                                }, 'Portfolio Impact')
                            )
                        )
                    ),
                    
                    // Scenario details modal/panel
                    scenarioDetails && e('div', { className: 'scenario-details' },
                        e('div', { className: 'section-header' },
                            e('h3', null, `${scenarioDetails.name} - Detailed Analysis`),
                            e('button', { 
                                className: 'btn-close',
                                onClick: () => { setActiveScenario(null); setScenarioDetails(null); }
                            }, '×')
                        ),
                        
                        scenarioDetails.winners && scenarioDetails.winners.length > 0 &&
                            e('div', { className: 'subsection' },
                                e('h4', null, 'Top Winners'),
                                e('div', { className: 'winners-losers-grid' },
                                    scenarioDetails.winners.slice(0, 5).map(position =>
                                        e('div', { key: position.symbol, className: 'position-item' },
                                            e('span', { className: 'symbol' }, position.symbol),
                                            e('span', { className: 'impact positive' }, 
                                                formatCurrency(position.delta_value || 0))
                                        )
                                    )
                                )
                            ),
                        
                        scenarioDetails.losers && scenarioDetails.losers.length > 0 &&
                            e('div', { className: 'subsection' },
                                e('h4', null, 'Top Losers'),
                                e('div', { className: 'winners-losers-grid' },
                                    scenarioDetails.losers.slice(0, 5).map(position =>
                                        e('div', { key: position.symbol, className: 'position-item' },
                                            e('span', { className: 'symbol' }, position.symbol),
                                            e('span', { className: 'impact negative' }, 
                                                formatCurrency(position.delta_value || 0))
                                        )
                                    )
                                )
                            )
                    ),
                    
                    // Add refresh button
                    e('div', { className: 'actions' },
                        e('button', { 
                            className: 'btn btn-secondary',
                            onClick: fetchScenarios,
                            disabled: loading
                        }, 'Refresh Scenarios')
                    )
                );
            }
            
            function RiskPage() {
                const { portfolioId } = useUserContext();
                
                return e('div', { className: 'risk-page' },
                    e(PatternRenderer, {
                        pattern: 'portfolio_cycle_risk',
                        inputs: { portfolio_id: portfolioId }
                    })
                );
            }
            
            function AttributionPage() {
                const { portfolioId } = useUserContext();
                
                return e('div', { className: 'attribution-page' },
                    e('div', { className: 'page-header' },
                        e('h1', { className: 'page-title' }, 'Performance Attribution'),
                        e('p', { className: 'page-description' }, 'Sources of portfolio returns')
                    ),
                    e(PatternRenderer, {
                        pattern: 'portfolio_overview',
                        inputs: { portfolio_id: portfolioId, lookback_days: 252 },
                        config: {
                            // Show only currency attribution panel
                            showPanels: ['currency_attr']
                        }
                    })
                );
            }
            
            function OptimizerPage() {
                const [optimizationData, setOptimizationData] = useState(null);
                const [isConfigOpen, setIsConfigOpen] = useState(true);
                const [refreshKey, setRefreshKey] = useState(0);
                const [refreshing, setRefreshing] = useState(false);
                const portfolioId = getCurrentPortfolioId();
                
                // Policy configuration state
                const [policyConfig, setPolicyConfig] = useState({
                    risk: 30,
                    growth: 30,
                    dividend: 20,
                    defensive: 20,
                    minQualityScore: 7.0,
                    maxSinglePosition: 25.0,
                    maxSector: 35.0,
                    maxTurnoverPct: 10.0,
                    minLotValue: 500
                });
                
                // Computed inputs for PatternRenderer
                const patternInputs = React.useMemo(() => {
                    // Create policies array based on configuration
                    const policies = [];
                    
                    // Add allocation targets based on weights
                    if (policyConfig.risk > 0) {
                        policies.push({ type: 'target_allocation', category: 'risk', value: policyConfig.risk / 100 });
                    }
                    if (policyConfig.growth > 0) {
                        policies.push({ type: 'target_allocation', category: 'growth', value: policyConfig.growth / 100 });
                    }
                    if (policyConfig.dividend > 0) {
                        policies.push({ type: 'target_allocation', category: 'dividend', value: policyConfig.dividend / 100 });
                    }
                    if (policyConfig.defensive > 0) {
                        policies.push({ type: 'target_allocation', category: 'defensive', value: policyConfig.defensive / 100 });
                    }
                    
                    // Add quality and position constraints
                    policies.push({ type: 'min_quality_score', value: policyConfig.minQualityScore });
                    policies.push({ type: 'max_single_position', value: policyConfig.maxSinglePosition });
                    policies.push({ type: 'max_sector', value: policyConfig.maxSector });
                    
                    return {
                        portfolio_id: portfolioId,
                        policies: policies,
                        constraints: {
                            max_te_pct: 2.0,
                            max_turnover_pct: policyConfig.maxTurnoverPct,
                            min_lot_value: policyConfig.minLotValue
                        }
                    };
                }, [portfolioId, policyConfig, refreshKey]);
                
                // Callback when pattern data loads
                const handleDataLoaded = (data) => {
                    if (Logger) {
                        Logger.debug('Optimizer data loaded:', data);
                    } else {
                        console.log('Optimizer data loaded:', data);
                    }
                    if (data) {
                        setOptimizationData(processOptimizationData(data));
                    }
                };
                
                const handlePolicySubmit = (e) => {
                    e.preventDefault();
                    // Trigger refresh by changing key
                    setRefreshKey(prev => prev + 1);
                    setIsConfigOpen(false);
                };
                
                const handleSliderChange = (field, value) => {
                    const newValue = parseInt(value);
                    
                    // For allocation weights, ensure they sum to 100
                    if (['risk', 'growth', 'dividend', 'defensive'].includes(field)) {
                        const currentTotal = policyConfig.risk + policyConfig.growth + 
                                           policyConfig.dividend + policyConfig.defensive;
                        const otherFields = ['risk', 'growth', 'dividend', 'defensive'].filter(f => f !== field);
                        const otherTotal = otherFields.reduce((sum, f) => sum + policyConfig[f], 0);
                        
                        // Adjust the value if it would exceed 100
                        const maxValue = 100 - otherTotal;
                        const finalValue = Math.min(newValue, maxValue);
                        
                        setPolicyConfig(prev => ({ ...prev, [field]: finalValue }));
                    } else {
                        setPolicyConfig(prev => ({ ...prev, [field]: parseFloat(value) }));
                    }
                };
                
                const getTotalWeight = () => {
                    return policyConfig.risk + policyConfig.growth + policyConfig.dividend + policyConfig.defensive;
                };
                
                const fetchOptimizationRecommendations = async () => {
                    setRefreshing(true);
                    setRefreshKey(prev => prev + 1);
                    // The actual data loading is handled by PatternRenderer
                    // Set refreshing to false after a short delay to show the state change
                    setTimeout(() => setRefreshing(false), 1000);
                };
                
                const processOptimizationData = (data) => {
                    // Extract data from the pattern response
                    const rebalanceSummary = data.rebalance_summary || {};
                    const proposedTrades = data.proposed_trades || [];
                    const impactAnalysis = data.impact_analysis || {};
                    const rebalanceResult = data.rebalance_result || {};
                    
                    return {
                        summary: {
                            totalTrades: rebalanceResult.trade_count || rebalanceSummary.trade_count || 0,
                            totalTurnover: rebalanceResult.total_turnover || rebalanceSummary.total_turnover || 0,
                            turnoverPct: rebalanceResult.turnover_pct || rebalanceSummary.turnover_pct || 0,
                            estimatedCosts: rebalanceResult.estimated_costs || rebalanceSummary.estimated_costs || 0,
                            costBps: rebalanceResult.cost_bps || rebalanceSummary.cost_bps || 0,
                            teImpact: impactAnalysis.te_delta || 0
                        },
                        trades: Array.isArray(proposedTrades) ? proposedTrades : 
                                (rebalanceResult.trades || []),
                        impact: {
                            currentValue: impactAnalysis.current_value || 291290,
                            postValue: impactAnalysis.post_rebalance_value || 291290,
                            valueDelta: impactAnalysis.value_delta || 0,
                            currentDivSafety: impactAnalysis.current_div_safety || 0,
                            postDivSafety: impactAnalysis.post_div_safety || 0,
                            divSafetyDelta: impactAnalysis.div_safety_delta || 0,
                            currentMoat: impactAnalysis.current_moat || 0,
                            postMoat: impactAnalysis.post_moat || 0,
                            moatDelta: impactAnalysis.moat_delta || 0,
                            currentConcentration: impactAnalysis.current_concentration || 0,
                            postConcentration: impactAnalysis.post_concentration || 0,
                            concentrationDelta: impactAnalysis.concentration_delta || 0
                        }
                    };
                };
                
                const getActionStyle = (action) => {
                    switch (action?.toUpperCase()) {
                        case 'BUY':
                            return { color: 'var(--color-success)' };
                        case 'SELL':
                        case 'REDUCE':
                            return { color: 'var(--color-error)' };
                        case 'HOLD':
                            return { color: 'var(--color-warning)' };
                        default:
                            return {};
                    }
                };
                
                return e('div', { className: 'optimizer-page' },
                    e('div', { className: 'page-header' },
                        e('h1', { className: 'page-title' }, 'Portfolio Optimizer'),
                        e('p', { className: 'page-description' }, 'AI-powered optimization with policy-based rebalancing')
                    ),
                    
                    // Policy Configuration Form
                    e('div', { className: 'card', style: { marginBottom: '2rem' } },
                        e('div', { className: 'card-header' },
                            e('h3', { className: 'card-title' }, 'Policy Configuration'),
                            e('button', { 
                                className: 'btn btn-sm',
                                onClick: () => setIsConfigOpen(!isConfigOpen)
                            }, isConfigOpen ? 'Hide Config' : 'Show Config')
                        ),
                        isConfigOpen && e('form', { 
                            className: 'policy-form', 
                            onSubmit: handlePolicySubmit,
                            style: { padding: '1.5rem' }
                        },
                            // Target Allocations Section
                            e('div', { style: { marginBottom: '2rem' } },
                                e('h4', { style: { marginBottom: '1rem', color: 'var(--text-secondary)' } }, 
                                    'Target Allocations (must sum to 100%)'),
                                
                                // Risk Weight
                                e('div', { className: 'form-group', style: { marginBottom: '1rem' } },
                                    e('label', { className: 'form-label' }, 
                                        `Risk Assets: ${policyConfig.risk}%`),
                                    e('input', {
                                        type: 'range',
                                        className: 'form-range',
                                        min: 0,
                                        max: 100,
                                        value: policyConfig.risk,
                                        onChange: (e) => handleSliderChange('risk', e.target.value),
                                        style: { width: '100%' }
                                    })
                                ),
                                
                                // Growth Weight
                                e('div', { className: 'form-group', style: { marginBottom: '1rem' } },
                                    e('label', { className: 'form-label' }, 
                                        `Growth Assets: ${policyConfig.growth}%`),
                                    e('input', {
                                        type: 'range',
                                        className: 'form-range',
                                        min: 0,
                                        max: 100,
                                        value: policyConfig.growth,
                                        onChange: (e) => handleSliderChange('growth', e.target.value),
                                        style: { width: '100%' }
                                    })
                                ),
                                
                                // Dividend Weight
                                e('div', { className: 'form-group', style: { marginBottom: '1rem' } },
                                    e('label', { className: 'form-label' }, 
                                        `Dividend Assets: ${policyConfig.dividend}%`),
                                    e('input', {
                                        type: 'range',
                                        className: 'form-range',
                                        min: 0,
                                        max: 100,
                                        value: policyConfig.dividend,
                                        onChange: (e) => handleSliderChange('dividend', e.target.value),
                                        style: { width: '100%' }
                                    })
                                ),
                                
                                // Defensive Weight
                                e('div', { className: 'form-group', style: { marginBottom: '1rem' } },
                                    e('label', { className: 'form-label' }, 
                                        `Defensive Assets: ${policyConfig.defensive}%`),
                                    e('input', {
                                        type: 'range',
                                        className: 'form-range',
                                        min: 0,
                                        max: 100,
                                        value: policyConfig.defensive,
                                        onChange: (e) => handleSliderChange('defensive', e.target.value),
                                        style: { width: '100%' }
                                    })
                                ),
                                
                                // Total Weight Display
                                e('div', { 
                                    style: { 
                                        padding: '0.75rem',
                                        background: getTotalWeight() === 100 ? 
                                            'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                                        border: getTotalWeight() === 100 ? 
                                            '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(245, 158, 11, 0.3)',
                                        borderRadius: '8px',
                                        color: getTotalWeight() === 100 ? 
                                            'var(--color-success)' : 'var(--color-warning)',
                                        marginBottom: '1rem'
                                    }
                                }, `Total Weight: ${getTotalWeight()}%`)
                            ),
                            
                            // Constraints Section
                            e('div', { style: { marginBottom: '2rem' } },
                                e('h4', { style: { marginBottom: '1rem', color: 'var(--text-secondary)' } }, 
                                    'Constraints'),
                                
                                // Min Quality Score
                                e('div', { className: 'form-group', style: { marginBottom: '1rem' } },
                                    e('label', { className: 'form-label' }, 
                                        `Min Quality Score: ${policyConfig.minQualityScore.toFixed(1)}`),
                                    e('input', {
                                        type: 'range',
                                        className: 'form-range',
                                        min: 5,
                                        max: 10,
                                        step: 0.5,
                                        value: policyConfig.minQualityScore,
                                        onChange: (e) => handleSliderChange('minQualityScore', e.target.value),
                                        style: { width: '100%' }
                                    })
                                ),
                                
                                // Max Single Position
                                e('div', { className: 'form-group', style: { marginBottom: '1rem' } },
                                    e('label', { className: 'form-label' }, 
                                        `Max Single Position: ${policyConfig.maxSinglePosition.toFixed(1)}%`),
                                    e('input', {
                                        type: 'range',
                                        className: 'form-range',
                                        min: 5,
                                        max: 50,
                                        step: 5,
                                        value: policyConfig.maxSinglePosition,
                                        onChange: (e) => handleSliderChange('maxSinglePosition', e.target.value),
                                        style: { width: '100%' }
                                    })
                                ),
                                
                                // Max Sector
                                e('div', { className: 'form-group', style: { marginBottom: '1rem' } },
                                    e('label', { className: 'form-label' }, 
                                        `Max Sector Concentration: ${policyConfig.maxSector.toFixed(1)}%`),
                                    e('input', {
                                        type: 'range',
                                        className: 'form-range',
                                        min: 20,
                                        max: 50,
                                        step: 5,
                                        value: policyConfig.maxSector,
                                        onChange: (e) => handleSliderChange('maxSector', e.target.value),
                                        style: { width: '100%' }
                                    })
                                ),
                                
                                // Max Turnover
                                e('div', { className: 'form-group', style: { marginBottom: '1rem' } },
                                    e('label', { className: 'form-label' }, 
                                        `Max Turnover: ${policyConfig.maxTurnoverPct.toFixed(1)}%`),
                                    e('input', {
                                        type: 'range',
                                        className: 'form-range',
                                        min: 5,
                                        max: 30,
                                        step: 5,
                                        value: policyConfig.maxTurnoverPct,
                                        onChange: (e) => handleSliderChange('maxTurnoverPct', e.target.value),
                                        style: { width: '100%' }
                                    })
                                )
                            ),
                            
                            // Submit Button
                            e('button', { 
                                type: 'submit',
                                className: 'btn btn-primary',
                                disabled: getTotalWeight() !== 100,
                                style: { marginRight: '1rem' }
                            }, 'Apply Configuration'),
                            
                            e('button', {
                                type: 'button',
                                className: 'btn btn-secondary',
                                onClick: () => {
                                    setPolicyConfig({
                                        risk: 30,
                                        growth: 30,
                                        dividend: 20,
                                        defensive: 20,
                                        minQualityScore: 7.0,
                                        maxSinglePosition: 25.0,
                                        maxSector: 35.0,
                                        maxTurnoverPct: 10.0,
                                        minLotValue: 500
                                    });
                                }
                            }, 'Reset to Defaults')
                        )
                    ),
                    
                    // PatternRenderer to load optimization data (hidden)
                    e('div', { style: { display: 'none' } },
                        e(PatternRenderer, {
                            key: refreshKey,
                            pattern: 'policy_rebalance',
                            inputs: patternInputs,
                            onDataLoaded: handleDataLoaded
                        })
                    ),
                    
                    // Summary Statistics
                    optimizationData && optimizationData.summary && e('div', { className: 'stats-grid', style: { marginBottom: '2rem' } },
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'Total Trades'),
                            e('div', { className: 'stat-value' }, optimizationData.summary.totalTrades || 0)
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'Turnover'),
                            e('div', { className: 'stat-value' }, 
                                formatCurrency(optimizationData.summary.totalTurnover || 0))
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'Turnover %'),
                            e('div', { className: 'stat-value' }, 
                                formatPercentage((optimizationData.summary.turnoverPct || 0) / 100))
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'Est. Costs'),
                            e('div', { className: 'stat-value' }, 
                                formatCurrency(optimizationData.summary.estimatedCosts || 0))
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'Cost (bps)'),
                            e('div', { className: 'stat-value' }, 
                                formatNumber(optimizationData.summary.costBps || 0))
                        ),
                        e('div', { className: 'stat-card' },
                            e('div', { className: 'stat-label' }, 'TE Impact'),
                            e('div', { className: 'stat-value' }, 
                                formatPercentage((optimizationData.summary.teImpact || 0) / 100))
                        )
                    ),
                    
                    // Proposed Trades
                    e('div', { className: 'card' },
                        e('div', { className: 'card-header' },
                            e('h3', { className: 'card-title' }, 'Proposed Trades'),
                            e('button', {
                                className: 'btn btn-sm',
                                onClick: fetchOptimizationRecommendations,
                                disabled: refreshing
                            }, refreshing ? 'Refreshing...' : 'Refresh')
                        ),
                        e('div', { className: 'table-container' },
                            optimizationData && optimizationData.trades && optimizationData.trades.length > 0 ?
                                e('table', { className: 'table' },
                                    e('thead', null,
                                        e('tr', null,
                                            e('th', null, 'Action'),
                                            e('th', null, 'Symbol'),
                                            e('th', null, 'Quantity'),
                                            e('th', null, 'Price'),
                                            e('th', null, 'Value'),
                                            e('th', null, 'Reason'),
                                            e('th', null, 'Est. Cost')
                                        )
                                    ),
                                    e('tbody', null,
                                        optimizationData.trades.map((trade, index) =>
                                            e('tr', { key: index },
                                                e('td', { style: getActionStyle(trade.action) }, 
                                                    trade.action || 'N/A'),
                                                e('td', { className: 'symbol' }, trade.symbol || 'N/A'),
                                                e('td', null, formatNumber(trade.quantity || 0)),
                                                e('td', null, formatCurrency(trade.price || 0)),
                                                e('td', { 
                                                    className: trade.value >= 0 ? 'positive' : 'negative' 
                                                }, formatCurrency(Math.abs(trade.value || 0))),
                                                e('td', null, trade.reason || 'Optimization target'),
                                                e('td', null, formatCurrency(trade.estimated_cost || 0))
                                            )
                                        )
                                    )
                                ) :
                                e('div', { className: 'empty-state' }, 
                                    'No trades recommended - portfolio is optimally balanced')
                        )
                    ),
                    
                    // Impact Analysis
                    optimizationData && optimizationData.impact && e('div', { className: 'card' },
                        e('div', { className: 'card-header' },
                            e('h3', { className: 'card-title' }, 'Impact Analysis')
                        ),
                        e('div', { className: 'table-container' },
                            e('table', { className: 'table' },
                                e('thead', null,
                                    e('tr', null,
                                        e('th', null, 'Metric'),
                                        e('th', null, 'Current'),
                                        e('th', null, 'Post-Rebalance'),
                                        e('th', null, 'Change')
                                    )
                                ),
                                e('tbody', null,
                                    e('tr', null,
                                        e('td', null, 'Portfolio Value'),
                                        e('td', null, formatCurrency(optimizationData.impact.currentValue)),
                                        e('td', null, formatCurrency(optimizationData.impact.postValue)),
                                        e('td', { 
                                            className: optimizationData.impact.valueDelta >= 0 ? 'positive' : 'negative' 
                                        }, formatCurrency(optimizationData.impact.valueDelta))
                                    ),
                                    e('tr', null,
                                        e('td', null, 'Avg Dividend Safety'),
                                        e('td', null, formatNumber(optimizationData.impact.currentDivSafety)),
                                        e('td', null, formatNumber(optimizationData.impact.postDivSafety)),
                                        e('td', { 
                                            className: optimizationData.impact.divSafetyDelta >= 0 ? 'positive' : 'negative' 
                                        }, formatNumber(optimizationData.impact.divSafetyDelta, true))
                                    ),
                                    e('tr', null,
                                        e('td', null, 'Avg Moat Strength'),
                                        e('td', null, formatNumber(optimizationData.impact.currentMoat)),
                                        e('td', null, formatNumber(optimizationData.impact.postMoat)),
                                        e('td', { 
                                            className: optimizationData.impact.moatDelta >= 0 ? 'positive' : 'negative' 
                                        }, formatNumber(optimizationData.impact.moatDelta, true))
                                    ),
                                    e('tr', null,
                                        e('td', null, 'Concentration (Top 10)'),
                                        e('td', null, formatPercentage(optimizationData.impact.currentConcentration / 100)),
                                        e('td', null, formatPercentage(optimizationData.impact.postConcentration / 100)),
                                        e('td', { 
                                            className: optimizationData.impact.concentrationDelta <= 0 ? 'positive' : 'negative' 
                                        }, formatPercentage(optimizationData.impact.concentrationDelta / 100))
                                    )
                                )
                            )
                        )
                    )
                );
            }
            
            function RatingsPage() {
                const [loading, setLoading] = useState(true);
                const [error, setError] = useState(null);
                const [holdings, setHoldings] = useState([]);
                const [ratings, setRatings] = useState({});
                const [selectedSymbol, setSelectedSymbol] = useState(null);
                const [detailedRating, setDetailedRating] = useState(null);
                const [loadingDetail, setLoadingDetail] = useState(false);
                const [showDetailView, setShowDetailView] = useState(false);
                const [selectedSecurityId, setSelectedSecurityId] = useState(null);
                
                // Security ID mapping for common symbols (corrected from database)
                const symbolToSecurityId = {
                    'AAPL': '048a0b1e-5fa7-507a-9854-af6a9d7360e9',
                    'GOOGL': '33333333-3333-3333-3333-333333333302',
                    'MSFT': '33333333-3333-3333-3333-333333333303',
                    'BRK.B': '0b225e3f-5c2c-4dc6-8d3c-2bcf9700c32c',  // Fixed
                    'BAM': 'fc31a905-53b4-44fe-9f77-56ce5e9ecda4',     // Fixed
                    'CNR': '3406c701-34b0-4ba5-ad9a-ef54df4e37e2',    // Fixed
                    'BBUC': '40f59d8f-c3ca-4b95-9c17-1fadbef1c213',    // Fixed
                    'BTI': 'e778134c-818b-4dbd-b5ba-31bf211a1841',     // Fixed
                    'EVO': 'c9520fc4-b809-44a4-9f1c-53d9c3159382',     // Fixed
                    'NKE': '3a11ade4-5b85-4d3d-89dc-aaeed10dd8bc',     // Fixed
                    'PYPL': 'db4b10cc-3d43-4ec2-b9fe-2cae36d9d106',    // Fixed
                    'HHC': '89d7721e-9115-4806-ac41-a83c963feeee'      // Fixed
                };
                
                useEffect(() => {
                    fetchHoldingsAndRatings();
                }, []);
                
                const fetchHoldingsAndRatings = async () => {
                    try {
                        setLoading(true);
                        setError(null);
                        
                        // First get the holdings
                        const holdingsData = await apiClient.getHoldings();
                        const holdingsList = holdingsData.holdings || [];
                        
                        // Aggregate holdings by security_id to get unique securities
                        const aggregatedHoldings = {};
                        
                        holdingsList.forEach(lot => {
                            const securityId = lot.security_id || symbolToSecurityId[lot.symbol];
                            const symbol = lot.symbol;
                            
                            if (!aggregatedHoldings[securityId]) {
                                // Initialize with first lot's data
                                aggregatedHoldings[securityId] = {
                                    symbol: symbol,
                                    security_id: securityId,
                                    quantity: 0,
                                    value: 0,
                                    cost_basis: 0,
                                    lots: []
                                };
                            }
                            
                            // Aggregate quantities and values
                            aggregatedHoldings[securityId].quantity += lot.quantity || 0;
                            aggregatedHoldings[securityId].value += lot.value || 0;
                            aggregatedHoldings[securityId].cost_basis += lot.cost_basis || 0;
                            aggregatedHoldings[securityId].lots.push(lot);
                        });
                        
                        // Convert to array of unique securities
                        const uniqueSecurities = Object.values(aggregatedHoldings);
                        if (Logger) {
                            Logger.debug(`Aggregated ${holdingsList.length} lots into ${uniqueSecurities.length} unique securities`);
                        } else {
                            console.log(`Aggregated ${holdingsList.length} lots into ${uniqueSecurities.length} unique securities`);
                        }
                        setHoldings(uniqueSecurities);
                        
                        // Now fetch ratings for each unique security in parallel for better performance
                        const ratingsData = {};
                        
                        // Create array of rating promises for parallel processing
                        const ratingPromises = uniqueSecurities.map(async (security) => {
                            const symbol = security.symbol;
                            const securityId = security.security_id;
                            
                            if (securityId) {
                                try {
                                    if (Logger) {
                                        Logger.debug(`Fetching rating for ${symbol} with security_id: ${securityId}`);
                                    } else {
                                        console.log(`Fetching rating for ${symbol} with security_id: ${securityId}`);
                                    }
                                    const result = await apiClient.executePattern('buffett_checklist', {
                                        security_id: securityId
                                    });
                                    
                                    if (result.status === 'success' && result.data) {
                                        return { symbol, rating: parseBuffettResults(result.data, symbol) };
                                    } else {
                                        if (Logger) {
                                            Logger.warn(`Failed to get rating for ${symbol}:`, result.error || result);
                                        } else {
                                            console.warn(`Failed to get rating for ${symbol}:`, result.error || result);
                                        }
                                        return { symbol, rating: null, error: result.error || 'Failed to fetch rating' };
                                    }
                                } catch (err) {
                                    if (Logger) {
                                        Logger.error(`Error fetching rating for ${symbol}:`, err);
                                    } else {
                                        console.error(`Error fetching rating for ${symbol}:`, err);
                                    }
                                    return { symbol, rating: null, error: err.message };
                                }
                            } else {
                                return { symbol, rating: null, error: 'No security_id available' };
                            }
                        });
                        
                        // Wait for all ratings to complete
                        const ratingResults = await Promise.all(ratingPromises);
                        
                        // Build ratings data object from results
                        for (const result of ratingResults) {
                            // Include security_id in rating data for PatternRenderer
                            const security = uniqueSecurities.find(s => s.symbol === result.symbol);
                            ratingsData[result.symbol] = {
                                ...result.rating,
                                security_id: security?.security_id
                            };
                        }
                        
                        if (Object.keys(ratingsData).length === 0) {
                            setError('No ratings data available. Please try refreshing the page.');
                        } else {
                            setRatings(ratingsData);
                        }
                    } catch (err) {
                        if (Logger) {
                            Logger.error('Failed to fetch ratings:', err);
                        } else {
                            console.error('Failed to fetch ratings:', err);
                        }
                        setError('Failed to load ratings data. Please try refreshing the page.');
                    } finally {
                        setLoading(false);
                    }
                };
                
                const parseBuffettResults = (data, symbol) => {
                    // Parse the pattern result into rating format
                    // The API returns data in an 'aggregate' object with the following structure:
                    // aggregate: { overall_rating, overall_grade, moat: {overall}, resilience: {overall}, dividend: {overall} }
                    
                    // Check if aggregate exists in the response
                    const aggregate = data.aggregate || data.state?.aggregate || {};
                    
                    // Parse the overall rating and grade from aggregate
                    const overallRating = parseFloat(aggregate.overall_rating) || 0;
                    const overallGrade = aggregate.overall_grade || 'N/A';
                    
                    // Parse component scores from the aggregate nested structure
                    const moatScore = parseFloat(aggregate.moat?.overall) || 0;
                    const dividendScore = parseFloat(aggregate.dividend?.overall) || 0;
                    const resilienceScore = parseFloat(aggregate.resilience?.overall) || 0;
                    
                    // Use the overall_rating from API if available, otherwise calculate
                    const overallScore = overallRating > 0 ? (overallRating / 10) : 
                        (() => {
                            const scores = [moatScore];
                            if (dividendScore > 0) scores.push(dividendScore);
                            if (resilienceScore > 0) scores.push(resilienceScore);
                            return scores.reduce((a, b) => a + b, 0) / scores.length;
                        })();
                    
                    // Use the overall_grade from API if available, otherwise calculate
                    const letterGrade = overallGrade !== 'N/A' ? overallGrade :
                        (() => {
                            if (overallScore >= 9) return 'A+';
                            else if (overallScore >= 8) return 'A';
                            else if (overallScore >= 7) return 'B+';
                            else if (overallScore >= 6) return 'B';
                            else if (overallScore >= 5) return 'C+';
                            else return 'C';
                        })();
                    
                    // Parse detailed component data if available
                    const moatDetails = data.moat_strength || aggregate.moat || {};
                    const dividendDetails = data.dividend_safety || aggregate.dividend || {};
                    const resilienceDetails = data.resilience || aggregate.resilience || {};
                    
                    return {
                        symbol: symbol,
                        moatScore: moatScore,
                        dividendScore: dividendScore > 0 ? dividendScore : null,
                        resilienceScore: resilienceScore,
                        overallScore: overallScore,
                        letterGrade: letterGrade,
                        details: {
                            // Moat components
                            roe: moatDetails.components?.roe || moatDetails.roe_score || 0,
                            margins: moatDetails.components?.margins || moatDetails.margin_score || 0,
                            fcf: moatDetails.components?.fcf || moatDetails.fcf_score || 0,
                            growthStability: moatDetails.components?.growth_stability || moatDetails.growth_stability_score || 0,
                            brandPower: moatDetails.components?.brand_power || moatDetails.brand_score || 0,
                            networkEffects: moatDetails.components?.network_effects || moatDetails.network_score || 0,
                            costAdvantage: moatDetails.components?.cost_advantage || moatDetails.cost_score || 0,
                            switchingCosts: moatDetails.components?.switching_costs || moatDetails.switching_score || 0
                        },
                        rawData: data
                    };
                };
                
                const showDetailedRating = (symbol) => {
                    // Find security_id from ratings or symbolToSecurityId mapping
                    const securityId = ratings[symbol]?.security_id || 
                        symbolToSecurityId[symbol] ||
                        Object.values(holdings).find(h => h.symbol === symbol)?.security_id;
                    
                    if (securityId) {
                        setSelectedSymbol(symbol);
                        setSelectedSecurityId(securityId);
                        setShowDetailView(true);
                    } else {
                        if (Logger) {
                            Logger.warn(`No security_id found for symbol: ${symbol}`);
                        } else {
                            console.warn(`No security_id found for symbol: ${symbol}`);
                        }
                        // Fallback to showing cached rating if available
                        if (ratings[symbol]) {
                            setSelectedSymbol(symbol);
                            setDetailedRating(ratings[symbol]);
                        }
                    }
                };
                
                const getGradeColor = (grade) => {
                    // Handle null/undefined/empty values
                    if (!grade || grade === 'N/A') return 'neutral';
                    
                    // Convert to string for safe checking
                    const gradeStr = String(grade);
                    
                    // Check if it's a letter grade (using indexOf to avoid startsWith errors)
                    if (gradeStr[0] === 'A' || parseFloat(gradeStr) >= 8) return 'positive';
                    if (gradeStr[0] === 'B' || parseFloat(gradeStr) >= 6) return 'warning';
                    if (gradeStr[0] === 'C' || parseFloat(gradeStr) >= 4) return 'neutral';
                    
                    return 'negative';
                };
                
                if (loading) {
                    return e('div', null,
                        e('div', { className: 'page-header' },
                            e('h1', { className: 'page-title' }, 'Investment Ratings'),
                            e('p', { className: 'page-description' }, 'Loading Buffett-style quality assessments...')
                        ),
                        e('div', { className: 'loading' },
                            e('div', { className: 'spinner' })
                        )
                    );
                }
                
                return e('div', null,
                    e('div', { className: 'page-header' },
                        e('h1', { className: 'page-title' }, 'Investment Ratings'),
                        e('p', { className: 'page-description' }, 'Buffett-style quality assessment based on moat, dividends, and resilience')
                    ),
                    
                    error && e('div', { className: 'error-banner' }, error),
                    
                    // Main ratings table
                    e('div', { className: 'card' },
                        e('div', { className: 'card-header' },
                            e('h3', { className: 'card-title' }, 'Quality Ratings'),
                            e('div', { className: 'card-actions' },
                                e('button', { 
                                    className: 'btn btn-sm',
                                    onClick: fetchHoldingsAndRatings
                                }, 'Refresh Ratings')
                            )
                        ),
                        e('div', { className: 'table-container' },
                            e('table', { className: 'table' },
                                e('thead', null,
                                    e('tr', null,
                                        e('th', null, 'Symbol'),
                                        e('th', null, 'Grade'),
                                        e('th', null, 'Overall Score'),
                                        e('th', null, 'Moat'),
                                        e('th', null, 'Dividend Safety'),
                                        e('th', null, 'Resilience'),
                                        e('th', null, 'Action')
                                    )
                                ),
                                e('tbody', null,
                                    Object.values(ratings).map(rating => 
                                        e('tr', { key: rating.symbol },
                                            e('td', { className: 'symbol' }, rating.symbol),
                                            e('td', { 
                                                className: getGradeColor(rating.letterGrade),
                                                style: { fontWeight: 'bold' }
                                            }, rating.letterGrade),
                                            e('td', { 
                                                className: getGradeColor(rating.overallScore)
                                            }, `${rating.overallScore.toFixed(1)}/10`),
                                            e('td', null, `${rating.moatScore.toFixed(1)}/10`),
                                            e('td', null, rating.dividendScore ? `${rating.dividendScore.toFixed(1)}/10` : 'N/A'),
                                            e('td', null, `${rating.resilienceScore.toFixed(1)}/10`),
                                            e('td', null,
                                                e('button', {
                                                    className: 'btn btn-sm',
                                                    onClick: () => showDetailedRating(rating.symbol)
                                                }, 'Details')
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    ),
                    
                    // Detailed rating view using PatternRenderer
                    showDetailView && selectedSecurityId && selectedSymbol && e('div', { className: 'card', style: { marginTop: '1rem' } },
                        e('div', { className: 'card-header' },
                            e('h3', { className: 'card-title' }, 
                                `${selectedSymbol} - Detailed Buffett Analysis`),
                            e('button', { 
                                className: 'btn-close',
                                onClick: () => { 
                                    setShowDetailView(false);
                                    setSelectedSymbol(null);
                                    setSelectedSecurityId(null);
                                    setDetailedRating(null);
                                }
                            }, '×')
                        ),
                        e('div', { className: 'card-body' },
                            e(PatternRenderer, {
                                pattern: 'buffett_checklist',
                                inputs: { security_id: selectedSecurityId },
                                config: {
                                    showPanels: ['quality_score', 'moat_analysis', 'dividend_safety', 'resilience']
                                }
                            })
                        )
                    ),
                    
                    // Fallback: Show cached detailed rating if PatternRenderer not available
                    selectedSymbol && detailedRating && !showDetailView && e('div', { className: 'card', style: { marginTop: '1rem' } },
                        e('div', { className: 'card-header' },
                            e('h3', { className: 'card-title' }, 
                                `${selectedSymbol} - Detailed Buffett Analysis`),
                            e('button', { 
                                className: 'btn-close',
                                onClick: () => { setSelectedSymbol(null); setDetailedRating(null); }
                            }, '×')
                        ),
                        loadingDetail ? e('div', { className: 'loading' }, e('div', { className: 'spinner' })) :
                        e('div', { className: 'card-body' },
                            // Overall summary
                            e('div', { className: 'stats-grid', style: { marginBottom: '1rem' } },
                                e('div', { className: 'stat-card' },
                                    e('div', { className: 'stat-label' }, 'Overall Grade'),
                                    e('div', { 
                                        className: `stat-value ${getGradeColor(detailedRating.letterGrade)}`,
                                        style: { fontSize: '2rem' }
                                    }, detailedRating.letterGrade)
                                ),
                                e('div', { className: 'stat-card' },
                                    e('div', { className: 'stat-label' }, 'Buffett Score'),
                                    e('div', { 
                                        className: `stat-value ${getGradeColor(detailedRating.overallScore)}`
                                    }, `${(detailedRating.overallScore * 10).toFixed(0)}/100`)
                                )
                            ),
                            
                            // Detailed criteria
                            detailedRating.details && e('div', null,
                                e('h4', { style: { marginBottom: '1rem' } }, 'Individual Criteria Scores'),
                                e('div', { className: 'stats-grid' },
                                    e('div', { className: 'stat-card' },
                                        e('div', { className: 'stat-label' }, 'Return on Equity (ROE)'),
                                        e('div', { className: 'stat-value' }, 
                                            `${(detailedRating.details.roe || 0).toFixed(1)}/10`),
                                        e('div', { className: 'stat-description' }, 
                                            'Consistent ROE > 15% indicates strong advantage')
                                    ),
                                    e('div', { className: 'stat-card' },
                                        e('div', { className: 'stat-label' }, 'Operating Margins'),
                                        e('div', { className: 'stat-value' }, 
                                            `${(detailedRating.details.margins || 0).toFixed(1)}/10`),
                                        e('div', { className: 'stat-description' }, 
                                            'High margins suggest pricing power')
                                    ),
                                    e('div', { className: 'stat-card' },
                                        e('div', { className: 'stat-label' }, 'Free Cash Flow'),
                                        e('div', { className: 'stat-value' }, 
                                            `${(detailedRating.details.fcf || 0).toFixed(1)}/10`),
                                        e('div', { className: 'stat-description' }, 
                                            'Strong FCF indicates capital efficiency')
                                    ),
                                    e('div', { className: 'stat-card' },
                                        e('div', { className: 'stat-label' }, 'Growth Stability'),
                                        e('div', { className: 'stat-value' }, 
                                            `${(detailedRating.details.growthStability || 0).toFixed(1)}/10`),
                                        e('div', { className: 'stat-description' }, 
                                            'Low volatility indicates predictable revenue')
                                    )
                                ),
                                
                                e('h4', { style: { margin: '1.5rem 0 1rem' } }, 'Competitive Moat Analysis'),
                                e('div', { className: 'stats-grid' },
                                    e('div', { className: 'stat-card' },
                                        e('div', { className: 'stat-label' }, 'Brand Power'),
                                        e('div', { className: 'stat-value' }, 
                                            `${(detailedRating.details.brandPower || 0).toFixed(1)}/10`)
                                    ),
                                    e('div', { className: 'stat-card' },
                                        e('div', { className: 'stat-label' }, 'Network Effects'),
                                        e('div', { className: 'stat-value' }, 
                                            `${(detailedRating.details.networkEffects || 0).toFixed(1)}/10`)
                                    ),
                                    e('div', { className: 'stat-card' },
                                        e('div', { className: 'stat-label' }, 'Cost Advantage'),
                                        e('div', { className: 'stat-value' }, 
                                            `${(detailedRating.details.costAdvantage || 0).toFixed(1)}/10`)
                                    ),
                                    e('div', { className: 'stat-card' },
                                        e('div', { className: 'stat-label' }, 'Switching Costs'),
                                        e('div', { className: 'stat-value' }, 
                                            `${(detailedRating.details.switchingCosts || 0).toFixed(1)}/10`)
                                    )
                                )
                            )
                        )
                    )
                );
            }
            
            function AIInsightsPage() {
                const [explanations, setExplanations] = useState({});
                const [loadingExplanations, setLoadingExplanations] = useState({});
                const [refreshKey, setRefreshKey] = useState(0);
                const { portfolioId } = useUserContext();
                
                // Key patterns to display in AI Insights
                const keyPatterns = [
                    { id: 'portfolio_overview', name: 'Portfolio Overview', icon: '📊' },
                    { id: 'portfolio_scenario_analysis', name: 'Risk Analysis', icon: '⚠️' },
                    { id: 'tax_harvesting_opportunities', name: 'Tax Harvesting', icon: '💰' },
                    { id: 'portfolio_cycle_risk', name: 'Cycle Positioning', icon: '🔄' }
                ];
                
                // Generate AI explanation when pattern data is loaded
                const handlePatternDataLoaded = async (patternId, patternName, data) => {
                    if (!data || data.error) return;
                    
                    // Skip if explanation already exists or is loading
                    if (explanations[patternId] || loadingExplanations[patternId]) return;
                    
                    setLoadingExplanations(prev => ({ ...prev, [patternId]: true }));
                    
                    try {
                        // Get AI explanation of the results
                        const explanationPrompt = `Analyze these ${patternName} results and provide 2-3 key insights in simple, non-technical terms for an investor: ${JSON.stringify(data).substring(0, 1000)}`;
                        
                        const explanation = await apiClient.aiChat(explanationPrompt, {
                            portfolioId,
                            source: 'insights',
                            pattern: patternId
                        });
                        
                        setExplanations(prev => ({
                            ...prev,
                            [patternId]: explanation.data?.response || explanation.response || 'Analysis in progress...'
                        }));
                    } catch (err) {
                        if (Logger) {
                            Logger.error(`Failed to get AI explanation for ${patternName}:`, err);
                        } else {
                            console.error(`Failed to get AI explanation for ${patternName}:`, err);
                        }
                        setExplanations(prev => ({
                            ...prev,
                            [patternId]: 'Unable to generate AI explanation. Please try refreshing.'
                        }));
                    } finally {
                        setLoadingExplanations(prev => {
                            const updated = { ...prev };
                            delete updated[patternId];
                            return updated;
                        });
                    }
                };
                
                const handleRefresh = () => {
                    setRefreshKey(prev => prev + 1);
                    setExplanations({});
                    setLoadingExplanations({});
                };
                
                return e('div', null,
                    e('div', { className: 'page-header' },
                        e('h1', { className: 'page-title' }, 'AI Insights'),
                        e('p', { className: 'page-description' }, 'Pattern-driven portfolio intelligence with AI-powered explanations')
                    ),
                    
                    // Header with refresh button
                    e('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' } },
                        e('h2', { style: { margin: 0 } }, 'Portfolio Analysis Dashboard'),
                        e('button', {
                            className: 'btn btn-primary',
                            onClick: handleRefresh,
                            disabled: Object.keys(loadingExplanations).length > 0
                        }, Object.keys(loadingExplanations).length > 0 ? 'Generating Insights...' : 'Refresh Insights')
                    ),
                    
                    // Display insights using PatternRenderer directly
                    e('div', { className: 'insights-grid' },
                        keyPatterns.map(pattern => 
                            e('div', { 
                                key: pattern.id, 
                                className: 'card',
                                style: { marginBottom: '2rem' }
                            },
                                // Card header with pattern name and icon
                                e('div', { className: 'card-header' },
                                    e('h3', { className: 'card-title' },
                                        e('span', { style: { marginRight: '0.5rem' } }, pattern.icon),
                                        pattern.name
                                    )
                                ),
                                
                                // AI Explanation section (generated when pattern loads)
                                (explanations[pattern.id] || loadingExplanations[pattern.id]) && e('div', { 
                                    style: { padding: '1rem', borderBottom: '1px solid var(--border-color)' } 
                                },
                                    e('h4', { style: { marginBottom: '0.75rem', color: 'var(--color-info)' } }, 
                                        '🤖 AI Analysis'
                                    ),
                                    e('div', { 
                                        style: { 
                                            padding: '1rem',
                                            backgroundColor: 'rgba(59, 130, 246, 0.05)',
                                            borderRadius: '8px',
                                            border: '1px solid rgba(59, 130, 246, 0.2)'
                                        } 
                                    }, 
                                        loadingExplanations[pattern.id] ? 
                                            e('p', null, 'Generating AI insights...') :
                                            explanations[pattern.id] ? explanations[pattern.id].split('\n').map((line, i) => 
                                                e('p', { 
                                                    key: i, 
                                                    style: { marginBottom: i < explanations[pattern.id].split('\n').length - 1 ? '0.5rem' : 0 }
                                                }, line)
                                            ) : null
                                    )
                                ),
                                
                                // Pattern data using PatternRenderer (single execution)
                                e('div', { style: { padding: '1rem' } },
                                    e(PatternRenderer, {
                                        key: `${pattern.id}-${refreshKey}`,
                                        pattern: pattern.id,
                                        inputs: { 
                                            portfolio_id: portfolioId
                                        },
                                        config: { 
                                            compact: true,
                                            hideHeader: true 
                                        },
                                        onDataLoaded: (data) => {
                                            if (data && !data.error) {
                                                handlePatternDataLoaded(pattern.id, pattern.name, data);
                                            }
                                        }
                                    })
                                )
                            )
                        )
                    )
                );
            }
            
            function AIAssistantPage() {
                const [messages, setMessages] = useState([]);
                const [inputValue, setInputValue] = useState('');
                const [loading, setLoading] = useState(false);
                const [error, setError] = useState(null);
                const [executingPattern, setExecutingPattern] = useState(null);
                const { portfolioId } = useUserContext();
                const messagesEndRef = React.useRef(null);
                
                // Auto-scroll to bottom when new messages arrive
                useEffect(() => {
                    if (messagesEndRef.current) {
                        messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
                    }
                }, [messages]);
                
                // Show welcome message on first load
                useEffect(() => {
                    const welcomeMessage = {
                        role: 'assistant',
                        content: 'Hello! I\'m your AI Assistant powered by pattern analysis. I can help you with:\n\n• Portfolio performance analysis (ask about returns, metrics)\n• Risk scenarios (ask about market drops, volatility)\n• Tax insights (ask about tax harvesting, realized gains)\n• Holdings analysis (ask about positions, concentration)\n• Macro cycles (ask about economic cycles, trends)\n\nI\'ll automatically run relevant analysis patterns to provide data-driven answers. How can I help you today?',
                        timestamp: new Date().toISOString()
                    };
                    setMessages([welcomeMessage]);
                }, []);
                
                // Pattern mapping function - detects which pattern to execute based on query
                const getPatternForQuery = (query) => {
                    const q = query.toLowerCase();
                    
                    // Portfolio overview patterns
                    if (q.includes('performance') || q.includes('return') || q.includes('how is') || 
                        q.includes('portfolio doing') || q.includes('ytd') || q.includes('year to date')) {
                        return { id: 'portfolio_overview', name: 'Portfolio Overview' };
                    }
                    
                    // Risk analysis patterns  
                    if (q.includes('risk') || q.includes('scenario') || q.includes('what if') || 
                        q.includes('market drop') || q.includes('crash') || q.includes('volatility')) {
                        return { id: 'portfolio_scenario_analysis', name: 'Risk Analysis' };
                    }
                    
                    // Tax patterns
                    if (q.includes('tax') || q.includes('harvest') || q.includes('realized') || 
                        q.includes('capital gains') || q.includes('losses')) {
                        return q.includes('harvest') 
                            ? { id: 'tax_harvesting_opportunities', name: 'Tax Harvesting' }
                            : { id: 'portfolio_tax_report', name: 'Tax Report' };
                    }
                    
                    // Holdings patterns
                    if (q.includes('holding') || q.includes('position') || q.includes('stock') || 
                        q.includes('concentration') || q.includes('allocation')) {
                        return { id: 'holding_deep_dive', name: 'Holdings Analysis' };
                    }
                    
                    // Macro/cycle patterns
                    if (q.includes('cycle') || q.includes('macro') || q.includes('economic') || 
                        q.includes('regime') || q.includes('trend')) {
                        return { id: 'portfolio_cycle_risk', name: 'Cycle Analysis' };
                    }
                    
                    // News patterns
                    if (q.includes('news') || q.includes('event') || q.includes('happening')) {
                        return { id: 'news_impact_analysis', name: 'News Impact' };
                    }
                    
                    // Buffett checklist
                    if (q.includes('buffett') || q.includes('quality') || q.includes('moat')) {
                        return { id: 'buffett_checklist', name: 'Quality Analysis' };
                    }
                    
                    return null; // No pattern matched
                };
                
                const sendMessage = async () => {
                    if (!inputValue.trim() || loading) return;
                    
                    const userMessage = { 
                        role: 'user', 
                        content: inputValue,
                        timestamp: new Date().toISOString()
                    };
                    
                    setMessages(prev => [...prev, userMessage]);
                    setInputValue('');
                    setLoading(true);
                    setError(null);
                    
                    try {
                        // Check if query maps to a pattern
                        const pattern = getPatternForQuery(inputValue);
                        
                        if (pattern) {
                            // Pattern was detected - execute it
                            setExecutingPattern(pattern.name);
                            
                            // Add a status message
                            const statusMessage = {
                                role: 'assistant',
                                content: `I detected you're asking about ${pattern.name.toLowerCase()}. Let me run that analysis for you...`,
                                timestamp: new Date().toISOString(),
                                isStatus: true
                            };
                            setMessages(prev => [...prev, statusMessage]);
                            
                            // Execute the pattern
                            const patternInputs = {
                                portfolio_id: portfolioId,
                                tax_year: pattern.id === 'portfolio_tax_report' ? new Date().getFullYear() : undefined,
                                symbol: undefined // User must specify symbol
                            };
                            
                            const result = await apiClient.executePattern(pattern.id, patternInputs);
                            
                            // Get AI explanation of the pattern results
                            const explanationPrompt = `User asked: "${inputValue}". Based on this ${pattern.name} analysis, provide a clear, helpful answer: ${JSON.stringify(result.data || result).substring(0, 1500)}`;
                            
                            const explanation = await apiClient.aiChat(explanationPrompt, {
                                portfolioId,
                                source: 'assistant',
                                pattern: pattern.id
                            });
                            
                            // Create message with pattern results
                            const aiMessage = {
                                role: 'assistant',
                                content: explanation.data?.response || explanation.response || `Here's your ${pattern.name} analysis...`,
                                pattern: pattern.id,
                                patternName: pattern.name,
                                patternData: result.data || result,
                                timestamp: new Date().toISOString()
                            };
                            
                            setMessages(prev => [...prev, aiMessage]);
                            setExecutingPattern(null);
                        } else {
                            // No pattern detected - regular AI chat
                            const response = await apiClient.aiChat(inputValue, {
                                portfolioId,
                                source: 'assistant'
                            });
                            
                            const aiMessage = {
                                role: 'assistant',
                                content: response.data?.response || response.response || 'Let me help you with that.',
                                timestamp: new Date().toISOString()
                            };
                            
                            setMessages(prev => [...prev, aiMessage]);
                        }
                    } catch (error) {
                        if (Logger) {
                            Logger.error('AI Assistant error:', error);
                        } else {
                            console.error('AI Assistant error:', error);
                        }
                        setError('Unable to complete analysis. Please try again.');
                        
                        const errorResponse = { 
                            role: 'assistant', 
                            content: 'I had trouble completing that analysis. Please try rephrasing your question or try again later.',
                            timestamp: new Date().toISOString(),
                            isError: true
                        };
                        setMessages(prev => [...prev, errorResponse]);
                    } finally {
                        setLoading(false);
                        setExecutingPattern(null);
                    }
                };
                
                const clearChat = () => {
                    const welcomeMessage = {
                        role: 'assistant',
                        content: 'Chat cleared. How can I help you today?',
                        timestamp: new Date().toISOString()
                    };
                    setMessages([welcomeMessage]);
                    setError(null);
                };
                
                const formatMessage = (content) => {
                    if (!content) return '';
                    // Split content by newlines and format
                    return content.split('\n').map((line, idx) => {
                        if (line.startsWith('•')) {
                            return e('li', { key: idx }, line.substring(1).trim());
                        }
                        if (line.trim() === '') {
                            return e('br', { key: idx });
                        }
                        return e('span', { key: idx }, [line, idx < content.split('\n').length - 1 ? e('br') : null]);
                    });
                };
                
                // Suggested questions to help users
                const suggestedQuestions = [
                    'How is my portfolio performing year to date?',
                    'What are my biggest risks right now?',
                    'Do I have any tax harvesting opportunities?',
                    'What happens if the market drops 20%?',
                    'Show me my holdings analysis',
                    'What\'s the current economic cycle?'
                ];
                
                const askSuggestion = (question) => {
                    setInputValue(question);
                    // Focus the input for better UX
                    const textarea = document.querySelector('.chat-input');
                    if (textarea) {
                        textarea.focus();
                    }
                };
                
                const handleKeyPress = (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                    }
                };
                
                return e('div', { className: 'page-container ai-assistant-page' },
                    e('div', { className: 'page-header' },
                        e('h1', null, 'AI Assistant'),
                        e('p', { className: 'page-subtitle' }, 
                            'Get personalized insights and recommendations powered by advanced AI'
                        )
                    ),
                    
                    // Error notification
                    error && e('div', { className: 'alert alert-error mb-4' },
                        e('div', { className: 'alert-content' },
                            e('strong', null, 'Connection Issue'),
                            e('p', null, error)
                        )
                    ),
                    
                    // Chat container
                    e('div', { className: 'chat-container' },
                        // Chat header with actions
                        e('div', { className: 'chat-header' },
                            e('div', { className: 'chat-title' },
                                e('span', { className: 'status-dot online' }),
                                'AI Assistant - Online'
                            ),
                            e('button', {
                                className: 'btn btn-secondary btn-sm',
                                onClick: clearChat
                            }, 'Clear Chat')
                        ),
                        
                        // Messages area
                        e('div', { className: 'chat-messages' },
                            // Suggested questions for new chat
                            messages.length === 1 && e('div', { className: 'suggested-questions', style: { marginBottom: '1.5rem' } },
                                e('h4', { className: 'suggestions-title' }, 'Try asking about:'),
                                e('div', { className: 'suggestions-grid', style: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '0.5rem' } },
                                    suggestedQuestions.map(question => 
                                        e('button', {
                                            key: question,
                                            className: 'suggestion-chip',
                                            style: { 
                                                padding: '0.5rem 1rem', 
                                                fontSize: '0.875rem',
                                                textAlign: 'left',
                                                background: 'var(--bg-secondary)',
                                                border: '1px solid var(--border-color)',
                                                borderRadius: '8px',
                                                cursor: 'pointer'
                                            },
                                            onClick: () => askSuggestion(question)
                                        }, question)
                                    )
                                )
                            ),
                            
                            messages.map((msg, index) =>
                                e('div', { 
                                    key: index, 
                                    className: `chat-message ${msg.role} ${msg.isError ? 'error' : ''} ${msg.isStatus ? 'status' : ''}` 
                                },
                                    e('div', { className: 'message-header' },
                                        e('span', { className: 'message-role' }, 
                                            msg.role === 'user' ? 'You' : msg.isStatus ? '🔍 Pattern Detection' : '🤖 AI Assistant'),
                                        msg.timestamp && e('span', { className: 'message-time' }, 
                                            new Date(msg.timestamp).toLocaleTimeString([], { 
                                                hour: '2-digit', 
                                                minute: '2-digit' 
                                            })
                                        )
                                    ),
                                    e('div', { className: 'message-content' }, 
                                        msg.content.startsWith('•') 
                                            ? e('ul', { className: 'message-list' }, formatMessage(msg.content))
                                            : formatMessage(msg.content)
                                    ),
                                    
                                    // Display pattern results if available
                                    msg.patternData && msg.pattern && e('div', { 
                                        className: 'pattern-results',
                                        style: { 
                                            marginTop: '1rem',
                                            padding: '1rem',
                                            background: 'var(--bg-secondary)',
                                            borderRadius: '8px',
                                            border: '1px solid var(--border-color)'
                                        }
                                    },
                                        e('div', { style: { marginBottom: '0.75rem', fontWeight: '600', color: 'var(--color-info)' } },
                                            `📊 ${msg.patternName} Results:`
                                        ),
                                        // Use PatternRenderer to display the pattern results
                                        e(PatternRenderer, {
                                            pattern: msg.pattern,
                                            inputs: {
                                                portfolio_id: portfolioId,
                                                tax_year: msg.pattern === 'portfolio_tax_report' ? new Date().getFullYear() : undefined,
                                                symbol: undefined // User must specify symbol
                                            },
                                            config: {
                                                compact: true,
                                                hideHeader: true,
                                                maxHeight: '400px' // Limit height in chat
                                            }
                                        })
                                    )
                                )
                            ),
                            
                            // Pattern execution indicator
                            executingPattern && e('div', { className: 'chat-message assistant status' },
                                e('div', { className: 'message-content' },
                                    e('span', null, `🔄 Running ${executingPattern} analysis...`)
                                )
                            ),
                            loading && e('div', { className: 'chat-message assistant typing' },
                                e('div', { className: 'typing-dots' },
                                    e('span', { className: 'dot' }),
                                    e('span', { className: 'dot' }),
                                    e('span', { className: 'dot' })
                                )
                            ),
                            e('div', { ref: messagesEndRef })
                        ),
                        
                        // Input area
                        e('div', { className: 'chat-input-container' },
                            e('textarea', {
                                className: 'chat-input',
                                value: inputValue,
                                onChange: (e) => setInputValue(e.target.value),
                                onKeyPress: handleKeyPress,
                                placeholder: 'Type your question here... (Press Enter to send, Shift+Enter for new line)',
                                disabled: loading,
                                rows: 3
                            }),
                            e('div', { className: 'chat-actions' },
                                e('div', { className: 'chat-info' },
                                    e('span', { className: 'input-hint' }, 
                                        loading ? 'AI is thinking...' : 'Press Enter to send')
                                ),
                                e('button', { 
                                    className: `btn ${loading ? 'btn-loading' : 'btn-primary'}`,
                                    onClick: sendMessage,
                                    disabled: loading || !inputValue.trim()
                                }, 
                                    loading ? e('span', null,
                                        e('span', { className: 'spinner-small' }),
                                        ' Processing...'
                                    ) : e('span', null,
                                        '✨ Send Message'
                                    )
                                )
                            )
                        )
                    )
                );
            }
            
            function AlertsPage() {
                const [loading, setLoading] = useState(true);
                const [alerts, setAlerts] = useState([]);
                const [showModal, setShowModal] = useState(false);
                const [editingAlert, setEditingAlert] = useState(null);
                const [error, setError] = useState(null);
                const [success, setSuccess] = useState(null);
                const [formData, setFormData] = useState({
                    type: 'price',
                    symbol: '',
                    threshold: '',
                    condition: 'below',
                    notification_channel: 'email'
                });
                
                useEffect(() => {
                    loadAlerts();
                }, []);
                
                const loadAlerts = async () => {
                    try {
                        setLoading(true);
                        setError(null);
                        const token = localStorage.getItem('access_token');
                        const response = await fetch('/api/alerts', {
                            headers: {
                                'Authorization': `Bearer ${token}`
                            }
                        });
                        
                        if (!response.ok) {
                            throw new Error('Failed to fetch alerts');
                        }
                        
                        const result = await response.json();
                        setAlerts(result.data?.alerts || []);
                    } catch (err) {
                        if (Logger) {
                            Logger.error('Error loading alerts:', err);
                        } else {
                            console.error('Error loading alerts:', err);
                        }
                        setError('Failed to load alerts. Please try refreshing the page.');
                    } finally {
                        setLoading(false);
                    }
                };
                
                const handleCreateOrUpdate = async () => {
                    try {
                        setError(null);
                        const token = localStorage.getItem('access_token');
                        
                        const url = editingAlert 
                            ? `/api/alerts/${editingAlert.id}`
                            : '/api/alerts';
                        
                        const method = editingAlert ? 'PATCH' : 'POST';
                        
                        const response = await fetch(url, {
                            method: method,
                            headers: {
                                'Authorization': `Bearer ${token}`,
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                type: formData.type,
                                symbol: formData.type === 'price' ? formData.symbol : null,
                                threshold: parseFloat(formData.threshold),
                                condition: formData.condition,
                                notification_channel: formData.notification_channel
                            })
                        });
                        
                        if (!response.ok) {
                            throw new Error(editingAlert ? 'Failed to update alert' : 'Failed to create alert');
                        }
                        
                        setSuccess(editingAlert ? 'Alert updated successfully!' : 'Alert created successfully!');
                        setShowModal(false);
                        setEditingAlert(null);
                        resetForm();
                        await loadAlerts();
                    } catch (err) {
                        if (Logger) {
                            Logger.error('Error saving alert:', err);
                        } else {
                            console.error('Error saving alert:', err);
                        }
                        setError(editingAlert ? 'Failed to update alert' : 'Failed to create alert');
                    }
                };
                
                const handleDelete = async (alertId) => {
                    if (!confirm('Are you sure you want to delete this alert?')) return;
                    
                    try {
                        setError(null);
                        const token = localStorage.getItem('access_token');
                        
                        const response = await fetch(`/api/alerts/${alertId}`, {
                            method: 'DELETE',
                            headers: {
                                'Authorization': `Bearer ${token}`
                            }
                        });
                        
                        if (!response.ok) {
                            throw new Error('Failed to delete alert');
                        }
                        
                        setSuccess('Alert deleted successfully!');
                        await loadAlerts();
                    } catch (err) {
                        if (Logger) {
                            Logger.error('Error deleting alert:', err);
                        } else {
                            console.error('Error deleting alert:', err);
                        }
                        setError('Failed to delete alert');
                    }
                };
                
                const handleEdit = (alert) => {
                    setEditingAlert(alert);
                    setFormData({
                        type: alert.type || 'price',
                        symbol: alert.symbol || '',
                        threshold: alert.threshold?.toString() || '',
                        condition: alert.condition || 'below',
                        notification_channel: alert.notification_channel || 'email'
                    });
                    setShowModal(true);
                };
                
                const resetForm = () => {
                    setFormData({
                        type: 'price',
                        symbol: '',
                        threshold: '',
                        condition: 'below',
                        notification_channel: 'email'
                    });
                };
                
                const openCreateModal = () => {
                    setEditingAlert(null);
                    resetForm();
                    setShowModal(true);
                };
                
                const getAlertIcon = (type) => {
                    switch (type) {
                        case 'price': return '💰';
                        case 'portfolio': return '📊';
                        case 'risk': return '⚠️';
                        case 'news': return '📰';
                        default: return '🔔';
                    }
                };
                
                const getAlertTypeLabel = (type) => {
                    switch (type) {
                        case 'price': return 'Price Alert';
                        case 'portfolio': return 'Portfolio Alert';
                        case 'risk': return 'Risk Alert';
                        case 'news': return 'News Alert';
                        default: return 'Alert';
                    }
                };
                
                const formatAlertMessage = (alert) => {
                    if (alert.message) return alert.message;
                    
                    switch (alert.type) {
                        case 'price':
                            return `${alert.symbol} ${alert.condition} $${alert.threshold}`;
                        case 'portfolio':
                            return `Portfolio value ${alert.condition} ${alert.threshold}%`;
                        case 'risk':
                            return `Risk level ${alert.condition} ${alert.threshold}`;
                        case 'news':
                            return `News sentiment ${alert.condition} ${alert.threshold}`;
                        default:
                            return 'Custom alert';
                    }
                };
                
                // Clear messages after 5 seconds
                useEffect(() => {
                    if (error || success) {
                        const timer = setTimeout(() => {
                            setError(null);
                            setSuccess(null);
                        }, 5000);
                        return () => clearTimeout(timer);
                    }
                }, [error, success]);
                
                if (loading) return e('div', { className: 'loading' }, e('div', { className: 'spinner' }));
                
                return e('div', null,
                    e('div', { className: 'page-header' },
                        e('h1', { className: 'page-title' }, 'Alert Management'),
                        e('p', { className: 'page-description' }, 'Configure and manage portfolio alerts'),
                        e('button', { 
                            className: 'btn btn-primary',
                            onClick: openCreateModal,
                            style: { float: 'right', marginTop: '-3rem' }
                        }, '+ Create Alert')
                    ),
                    
                    // Success/Error Messages
                    success && e('div', { className: 'alert-success' }, success),
                    error && e('div', { className: 'alert-error' }, error),
                    
                    // Alert Presets from Macro Trend Monitor
                    e('div', { className: 'card', style: { marginBottom: '2rem' } },
                        e('div', { className: 'card-header' },
                            e('h3', { className: 'card-title' }, 'Suggested Alerts'),
                            e('p', { className: 'card-subtitle' }, 'AI-recommended alerts based on macro trends')
                        ),
                        e(PatternRenderer, {
                            pattern: 'macro_trend_monitor',
                            inputs: { portfolio_id: getCurrentPortfolioId() },
                            config: {
                                // Show only alert suggestions panel
                                showPanels: ['alert_suggestions']
                            }
                        })
                    ),
                    
                    // Alert List
                    e('div', { className: 'card' },
                        e('div', { className: 'card-header' },
                            e('h3', { className: 'card-title' }, `Active Alerts (${alerts.length})`),
                            e('p', { className: 'card-subtitle' }, 'Monitor price changes, portfolio performance, and risk levels')
                        ),
                        
                        alerts.length === 0 ? (
                            e('div', { className: 'empty-state' },
                                e('div', { className: 'empty-state-title' }, 'No Active Alerts'),
                                e('div', { className: 'empty-state-message' }, 
                                    'Create alerts to monitor price changes, portfolio events, and risk thresholds'),
                                e('button', { 
                                    className: 'btn btn-primary',
                                    onClick: openCreateModal
                                }, 'Create Your First Alert')
                            )
                        ) : (
                            e('div', { className: 'alerts-list' },
                                alerts.map(alert =>
                                    e('div', { key: alert.id, className: 'alert-item' },
                                        e('div', { className: 'alert-item-left' },
                                            e('span', { className: 'alert-icon' }, getAlertIcon(alert.type)),
                                            e('div', { className: 'alert-details' },
                                                e('div', { className: 'alert-type' }, getAlertTypeLabel(alert.type)),
                                                e('div', { className: 'alert-message' }, formatAlertMessage(alert)),
                                                e('div', { className: 'alert-meta' },
                                                    e('span', { className: 'alert-status' }, 
                                                        alert.active ? '🟢 Active' : '🔴 Inactive'),
                                                    ' | ',
                                                    e('span', { className: 'alert-date' }, 
                                                        'Created: ' + new Date(alert.created_at).toLocaleDateString())
                                                )
                                            )
                                        ),
                                        e('div', { className: 'alert-item-actions' },
                                            e('button', { 
                                                className: 'btn-icon',
                                                onClick: () => handleEdit(alert),
                                                title: 'Edit Alert'
                                            }, '✏️'),
                                            e('button', { 
                                                className: 'btn-icon btn-danger',
                                                onClick: () => handleDelete(alert.id),
                                                title: 'Delete Alert'
                                            }, '🗑️')
                                        )
                                    )
                                )
                            )
                        )
                    ),
                    
                    // Create/Edit Modal
                    showModal && e('div', { className: 'modal-overlay', onClick: () => setShowModal(false) },
                        e('div', { className: 'modal-content', onClick: (e) => e.stopPropagation() },
                            e('div', { className: 'modal-header' },
                                e('h2', { className: 'modal-title' }, 
                                    editingAlert ? 'Edit Alert' : 'Create New Alert'),
                                e('button', { 
                                    className: 'modal-close',
                                    onClick: () => setShowModal(false)
                                }, '×')
                            ),
                            e('div', { className: 'modal-body' },
                                e('div', { className: 'form-group' },
                                    e('label', { className: 'form-label' }, 'Alert Type'),
                                    e('select', {
                                        className: 'form-input',
                                        value: formData.type,
                                        onChange: (e) => setFormData({...formData, type: e.target.value})
                                    },
                                        e('option', { value: 'price' }, 'Price Alert'),
                                        e('option', { value: 'portfolio' }, 'Portfolio Performance'),
                                        e('option', { value: 'risk' }, 'Risk Level'),
                                        e('option', { value: 'news' }, 'News Sentiment')
                                    )
                                ),
                                
                                formData.type === 'price' && e('div', { className: 'form-group' },
                                    e('label', { className: 'form-label' }, 'Symbol'),
                                    e('input', {
                                        type: 'text',
                                        className: 'form-input',
                                        value: formData.symbol,
                                        onChange: (e) => setFormData({...formData, symbol: e.target.value.toUpperCase()}),
                                        placeholder: 'e.g., AAPL, GOOGL'
                                    })
                                ),
                                
                                e('div', { className: 'form-group' },
                                    e('label', { className: 'form-label' }, 'Condition'),
                                    e('select', {
                                        className: 'form-input',
                                        value: formData.condition,
                                        onChange: (e) => setFormData({...formData, condition: e.target.value})
                                    },
                                        e('option', { value: 'above' }, 'Above'),
                                        e('option', { value: 'below' }, 'Below'),
                                        e('option', { value: 'change' }, 'Change By')
                                    )
                                ),
                                
                                e('div', { className: 'form-group' },
                                    e('label', { className: 'form-label' }, 
                                        formData.type === 'price' ? 'Price Threshold ($)' :
                                        formData.type === 'portfolio' ? 'Performance Threshold (%)' :
                                        formData.type === 'risk' ? 'Risk Score' :
                                        'Sentiment Score'),
                                    e('input', {
                                        type: 'number',
                                        className: 'form-input',
                                        value: formData.threshold,
                                        onChange: (e) => setFormData({...formData, threshold: e.target.value}),
                                        placeholder: formData.type === 'price' ? '150.00' : '10',
                                        step: formData.type === 'price' ? '0.01' : '1'
                                    })
                                ),
                                
                                e('div', { className: 'form-group' },
                                    e('label', { className: 'form-label' }, 'Notification Channel'),
                                    e('select', {
                                        className: 'form-input',
                                        value: formData.notification_channel,
                                        onChange: (e) => setFormData({...formData, notification_channel: e.target.value})
                                    },
                                        e('option', { value: 'email' }, 'Email'),
                                        e('option', { value: 'in-app' }, 'In-App Notification'),
                                        e('option', { value: 'both' }, 'Both')
                                    )
                                )
                            ),
                            e('div', { className: 'modal-footer' },
                                e('button', { 
                                    className: 'btn btn-secondary',
                                    onClick: () => setShowModal(false)
                                }, 'Cancel'),
                                e('button', { 
                                    className: 'btn btn-primary',
                                    onClick: handleCreateOrUpdate,
                                    disabled: !formData.threshold || (formData.type === 'price' && !formData.symbol)
                                }, editingAlert ? 'Update Alert' : 'Create Alert')
                            )
                        )
                    )
                );
            }
            
            function ReportsPage() {
                const [error, setError] = useState(null);
                const [success, setSuccess] = useState(null);
                const [generatingType, setGeneratingType] = useState(null);
                const [reportHistory, setReportHistory] = useState([
                    { id: 1, name: 'Q3 2024 Report', date: '2024-09-30', type: 'quarterly', size: '2.3 MB' },
                    { id: 2, name: 'Mid-Year Summary', date: '2024-06-30', type: 'ytd', size: '3.1 MB' },
                    { id: 3, name: 'Q2 2024 Report', date: '2024-06-30', type: 'quarterly', size: '2.1 MB' }
                ]);
                
                // Timeout protection: reset generatingType if pattern execution takes too long
                useEffect(() => {
                    if (generatingType) {
                        const timeout = setTimeout(() => {
                            setGeneratingType(null);
                            setError('Report generation timed out. Please try again.');
                        }, 90000); // 90 second timeout (PDF generation can take time)
                        return () => clearTimeout(timeout);
                    }
                }, [generatingType]);
                
                const handleReportData = (reportType, data) => {
                    try {
                        // Extract PDF result from pattern response
                        const pdfResult = data?.pdf_result || data;
                        if (!pdfResult || !pdfResult.pdf_base64) {
                            throw new Error('No PDF data in response');
                        }
                        
                        // Convert base64 to blob
                        const base64Data = pdfResult.pdf_base64;
                        const byteCharacters = atob(base64Data);
                        const byteNumbers = new Array(byteCharacters.length);
                        for (let i = 0; i < byteCharacters.length; i++) {
                            byteNumbers[i] = byteCharacters.charCodeAt(i);
                        }
                        const byteArray = new Uint8Array(byteNumbers);
                        const blob = new Blob([byteArray], { type: 'application/pdf' });
                        
                        // Create download link
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.style.display = 'none';
                        a.href = url;
                        a.download = pdfResult.download_filename || `${reportType}_report_${new Date().toISOString().split('T')[0]}.pdf`;
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                        
                        // Show success message
                        setSuccess(`${reportType === 'quarterly' ? 'Quarterly' : 'Year-to-Date'} report generated successfully!`);
                        
                        // Calculate file size from bytes
                        const sizeBytes = pdfResult.size_bytes || byteArray.length;
                        const sizeMB = (sizeBytes / (1024 * 1024)).toFixed(1);
                        
                        // Add to history
                        const newReport = {
                            id: reportHistory.length + 1,
                            name: `${reportType === 'quarterly' ? 'Q4 2024' : 'YTD 2024'} Report`,
                            date: new Date().toISOString().split('T')[0],
                            type: reportType,
                            size: `${sizeMB} MB`
                        };
                        setReportHistory([newReport, ...reportHistory.slice(0, 4)]);
                        
                    } catch (error) {
                        if (Logger) {
                            Logger.error('Error processing report:', error);
                        } else {
                            console.error('Error processing report:', error);
                        }
                        setError(`Failed to process report: ${error.message}`);
                    } finally {
                        setGeneratingType(null);
                        // Clear messages after 5 seconds
                        setTimeout(() => {
                            setError(null);
                            setSuccess(null);
                        }, 5000);
                    }
                };
                
                const handleReportError = (error) => {
                    if (Logger) {
                        Logger.error('Error generating report:', error);
                    } else {
                        console.error('Error generating report:', error);
                    }
                    setError(`Failed to generate report: ${error.message || 'Unknown error'}`);
                    setGeneratingType(null);
                    setTimeout(() => {
                        setError(null);
                    }, 5000);
                };
                
                const generateReport = (reportType) => {
                    setGeneratingType(reportType);
                    setError(null);
                    setSuccess(null);
                };
                
                return e('div', null,
                    e('div', { className: 'page-header' },
                        e('h1', { className: 'page-title' }, 'Portfolio Reports'),
                        e('p', { className: 'page-description' }, 'Generate and download professional PDF portfolio reports')
                    ),
                    
                    // Alert Messages
                    error && e('div', { className: 'alert alert-error', style: { marginBottom: '1.5rem' } },
                        e('div', { className: 'alert-content' },
                            e('span', { className: 'alert-icon' }, '⚠️'),
                            e('span', null, error)
                        )
                    ),
                    
                    success && e('div', { className: 'alert alert-success', style: { marginBottom: '1.5rem' } },
                        e('div', { className: 'alert-content' },
                            e('span', { className: 'alert-icon' }, '✅'),
                            e('span', null, success)
                        )
                    ),
                    
                    // Report Generation Cards
                    e('div', { className: 'stats-grid', style: { marginBottom: '2rem' } },
                        // Quarterly Report Card
                        e('div', { className: 'card' },
                            e('div', { style: { padding: '1.5rem' } },
                                e('h3', { style: { marginBottom: '0.5rem', color: 'var(--text-primary)' } }, 'Quarterly Report'),
                                e('p', { style: { color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.9rem' } }, 
                                    'Q4 2024 performance metrics including holdings, returns, and risk analysis'),
                                e('div', { style: { marginBottom: '1rem' } },
                                    e('div', { style: { fontSize: '0.85rem', color: 'var(--text-muted)' } }, 'Includes:'),
                                    e('ul', { style: { fontSize: '0.85rem', color: 'var(--text-secondary)', marginLeft: '1.5rem', marginTop: '0.5rem' } },
                                        e('li', null, 'Portfolio holdings and allocation'),
                                        e('li', null, 'Quarterly performance metrics'),
                                        e('li', null, 'Risk analytics and attribution'),
                                        e('li', null, 'Market commentary')
                                    )
                                ),
                                generatingType === 'quarterly' ? 
                                    e('div', { style: { textAlign: 'center', padding: '1rem' } },
                                        e('div', { className: 'spinner-small', style: { margin: '0 auto 0.5rem' } }),
                                        e('div', { style: { fontSize: '0.9rem', color: 'var(--text-secondary)' } }, 'Generating report...'),
                                        e('div', { style: { display: 'none' } },
                                            e(PatternRenderer, {
                                                pattern: 'export_portfolio_report',
                                                inputs: {
                                                    portfolio_id: getCurrentPortfolioId(),
                                                    include_holdings: true,
                                                    include_performance: true,
                                                    include_macro: false
                                                },
                                                onDataLoaded: (data) => {
                                                    try {
                                                        if (data && data.pdf_result && data.pdf_result.pdf_base64) {
                                                            handleReportData('quarterly', data);
                                                        } else if (data && data.error) {
                                                            handleReportError(new Error(data.error));
                                                        } else {
                                                            handleReportError(new Error('Invalid response from pattern'));
                                                        }
                                                    } catch (error) {
                                                        handleReportError(error);
                                                    }
                                                }
                                            })
                                        )
                                    ) :
                                    e('button', { 
                                        className: 'btn btn-primary',
                                        onClick: () => generateReport('quarterly'),
                                        disabled: !!generatingType,
                                        style: { width: '100%' }
                                    }, 'Generate Quarterly Report')
                            )
                        ),
                        
                        // YTD Summary Card
                        e('div', { className: 'card' },
                            e('div', { style: { padding: '1.5rem' } },
                                e('h3', { style: { marginBottom: '0.5rem', color: 'var(--text-primary)' } }, 'YTD Summary'),
                                e('p', { style: { color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.9rem' } }, 
                                    'Year-to-Date 2024 comprehensive performance analysis'),
                                e('div', { style: { marginBottom: '1rem' } },
                                    e('div', { style: { fontSize: '0.85rem', color: 'var(--text-muted)' } }, 'Includes:'),
                                    e('ul', { style: { fontSize: '0.85rem', color: 'var(--text-secondary)', marginLeft: '1.5rem', marginTop: '0.5rem' } },
                                        e('li', null, 'Full year portfolio overview'),
                                        e('li', null, 'YTD returns and benchmarks'),
                                        e('li', null, 'Sector performance breakdown'),
                                        e('li', null, 'Annual risk metrics')
                                    )
                                ),
                                generatingType === 'ytd' ? 
                                    e('div', { style: { textAlign: 'center', padding: '1rem' } },
                                        e('div', { className: 'spinner-small', style: { margin: '0 auto 0.5rem' } }),
                                        e('div', { style: { fontSize: '0.9rem', color: 'var(--text-secondary)' } }, 'Generating report...'),
                                        e('div', { style: { display: 'none' } },
                                            e(PatternRenderer, {
                                                pattern: 'export_portfolio_report',
                                                inputs: {
                                                    portfolio_id: getCurrentPortfolioId(),
                                                    include_holdings: true,
                                                    include_performance: true,
                                                    include_macro: true
                                                },
                                                onDataLoaded: (data) => {
                                                    try {
                                                        if (data && data.pdf_result && data.pdf_result.pdf_base64) {
                                                            handleReportData('ytd', data);
                                                        } else if (data && data.error) {
                                                            handleReportError(new Error(data.error));
                                                        } else {
                                                            handleReportError(new Error('Invalid response from pattern'));
                                                        }
                                                    } catch (error) {
                                                        handleReportError(error);
                                                    }
                                                }
                                            })
                                        )
                                    ) :
                                    e('button', { 
                                        className: 'btn btn-primary',
                                        onClick: () => generateReport('ytd'),
                                        disabled: !!generatingType,
                                        style: { width: '100%' }
                                    }, 'Generate YTD Summary')
                            )
                        )
                    ),
                    
                    // Report History
                    e('div', { className: 'card' },
                        e('div', { className: 'card-header' },
                            e('h3', { className: 'card-title' }, 'Recent Reports'),
                            e('div', { style: { fontSize: '0.85rem', color: 'var(--text-secondary)' } }, 
                                `${reportHistory.length} reports generated`)
                        ),
                        reportHistory.length > 0 ? 
                            e('div', { className: 'table-container' },
                                e('table', { className: 'table' },
                                    e('thead', null,
                                        e('tr', null,
                                            e('th', null, 'Report Name'),
                                            e('th', null, 'Type'),
                                            e('th', null, 'Date Generated'),
                                            e('th', null, 'Size')
                                        )
                                    ),
                                    e('tbody', null,
                                        reportHistory.map(report =>
                                            e('tr', { key: report.id },
                                                e('td', { style: { fontWeight: '500' } }, report.name),
                                                e('td', null, 
                                                    e('span', { 
                                                        className: 'badge',
                                                        style: { 
                                                            backgroundColor: report.type === 'quarterly' ? 
                                                                'rgba(59, 130, 246, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                                                            color: report.type === 'quarterly' ? 
                                                                'var(--color-info)' : 'var(--color-success)'
                                                        }
                                                    }, report.type.toUpperCase())
                                                ),
                                                e('td', null, formatDate(report.date)),
                                                e('td', { style: { color: 'var(--text-secondary)' } }, report.size)
                                            )
                                        )
                                    )
                                )
                            ) :
                            e('div', { className: 'empty-state' },
                                e('div', { className: 'empty-state-title' }, 'No Recent Reports'),
                                e('div', { className: 'empty-state-message' }, 'Generate your first report using the options above')
                            )
                    )
                );
            }
            
            function CorporateActionsPage() {
                const [filterType, setFilterType] = useState('all');
                const [filterDays, setFilterDays] = useState(90);
                const [patternData, setPatternData] = useState(null);
                
                // Pattern inputs
                const patternInputs = {
                    portfolio_id: getCurrentPortfolioId(),
                    days_ahead: filterDays
                };
                
                // Handle pattern data
                const handlePatternData = (data) => {
                    setPatternData(data);
                };
                
                // Get filtered actions from pattern data (client-side filtering)
                const filteredActions = React.useMemo(() => {
                    if (!patternData?.actions_with_impact?.actions) return [];
                    
                    let actions = patternData.actions_with_impact.actions;
                    
                    // Apply type filter (client-side)
                    if (filterType !== 'all') {
                        actions = actions.filter(a => a.type?.toLowerCase() === filterType);
                    }
                    
                    return actions;
                }, [patternData, filterType]);
                
                return e('div', null,
                    e('div', { className: 'page-header' },
                        e('h1', { className: 'page-title' }, 'Corporate Actions'),
                        e('p', { className: 'page-description' }, 
                            'Track dividends, splits, and other corporate events')
                    ),
                    
                    // Filtering Controls (keep existing filter UI)
                    e('div', { className: 'card', style: { marginBottom: '1.5rem' } },
                        e('div', { className: 'card-header' },
                            e('h3', { className: 'card-title' }, 'Filter Corporate Actions')
                        ),
                        e('div', { style: { padding: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' } },
                            // Action Type Filter
                            e('div', { style: { flex: '1 1 200px', minWidth: '150px' } },
                                e('label', { className: 'form-label' }, 'Action Type'),
                                e('select', {
                                    className: 'form-input',
                                    value: filterType,
                                    onChange: (e) => setFilterType(e.target.value)
                                },
                                    e('option', { value: 'all' }, 'All Types'),
                                    e('option', { value: 'dividend' }, 'Dividends'),
                                    e('option', { value: 'split' }, 'Stock Splits'),
                                    e('option', { value: 'earnings' }, 'Earnings')
                                )
                            ),
                            
                            // Date Range Filter
                            e('div', { style: { flex: '1 1 200px', minWidth: '150px' } },
                                e('label', { className: 'form-label' }, 'Date Range'),
                                e('select', {
                                    className: 'form-input',
                                    value: filterDays,
                                    onChange: (e) => setFilterDays(Number(e.target.value))
                                },
                                    e('option', { value: 30 }, 'Next 30 days'),
                                    e('option', { value: 90 }, 'Next 90 days'),
                                    e('option', { value: 180 }, 'Next 180 days'),
                                    e('option', { value: 365 }, 'Next year')
                                )
                            )
                        )
                    ),
                    
                    // PatternRenderer for main content
                    e(PatternRenderer, {
                        pattern: 'corporate_actions_upcoming',
                        inputs: patternInputs,
                        onDataLoaded: handlePatternData
                    })
                );
            }
            
            function MarketDataPage() {
                const [portfolioData, setPortfolioData] = useState(null);
                const [refreshKey, setRefreshKey] = useState(0);
                const [refreshing, setRefreshing] = useState(false);
                const { portfolioId } = useUserContext();
                
                // News filtering state
                const [filterSymbol, setFilterSymbol] = useState('');
                const [sentimentFilter, setSentimentFilter] = useState('all');
                const [lookbackHours, setLookbackHours] = useState(72);
                const [minImpactThreshold, setMinImpactThreshold] = useState(0.02);
                
                // Callback to capture portfolio data from PatternRenderer
                const handlePortfolioDataLoaded = (data) => {
                    if (data && data.valued_positions) {
                        setPortfolioData(data);
                    }
                };
                
                const handleRefresh = () => {
                    setRefreshing(true);
                    setRefreshKey(prev => prev + 1);
                    // Reset refreshing after a short delay to allow PatternRenderer to update
                    setTimeout(() => setRefreshing(false), 500);
                };
                
                // Build inputs for PatternRenderer
                const patternInputs = {
                    portfolio_id: portfolioId || getCurrentPortfolioId(),
                    lookback_days: 1  // Just need current prices
                };
                
                // Extract market data from portfolio overview pattern results
                const marketData = portfolioData?.valued_positions?.positions?.reduce((acc, pos) => {
                    if (pos.symbol && pos.price) {
                        acc[pos.symbol] = {
                            price: pos.price,
                            change: pos.unrealized_pnl_pct ? (pos.unrealized_pnl_pct * pos.price / 100) : 0,
                            changePercent: pos.unrealized_pnl_pct || 0
                        };
                    }
                    return acc;
                }, {}) || {};
                
                const portfolioSecurities = portfolioData?.valued_positions?.positions || [];
                
                return e('div', null,
                    e('div', { className: 'page-header', style: { marginBottom: '1.5rem' } },
                        e('div', { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' } },
                            e('div', null,
                                e('h1', { className: 'page-title' }, 'Market Data & News Analysis'),
                                e('p', { className: 'page-description' }, 
                                    'Real-time prices and sentiment analysis for your portfolio')
                            ),
                            e('button', {
                                className: 'btn',
                                onClick: handleRefresh,
                                disabled: refreshing,
                                style: { 
                                    padding: '0.5rem 1rem',
                                    fontSize: '0.875rem',
                                    minWidth: '100px'
                                }
                            }, refreshing ? 'Refreshing...' : '↻ Refresh')
                        )
                    ),
                    
                    // News Filtering Controls
                    e('div', { className: 'card', style: { marginBottom: '1.5rem' } },
                        e('div', { className: 'card-header' },
                            e('h3', { className: 'card-title' }, 'News Filter Controls')
                        ),
                        e('div', { style: { padding: '1rem', display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'flex-end' } },
                            // Symbol filter
                            e('div', { style: { flex: '1 1 200px', minWidth: '150px' } },
                                e('label', { 
                                    className: 'form-label', 
                                    style: { fontSize: '0.75rem', marginBottom: '0.25rem' } 
                                }, 'Filter by Symbol'),
                                e('input', {
                                    type: 'text',
                                    className: 'form-input',
                                    placeholder: 'e.g., AAPL, MSFT',
                                    value: filterSymbol,
                                    onChange: (e) => setFilterSymbol(e.target.value),
                                    style: { fontSize: '0.875rem' }
                                })
                            ),
                            
                            // Sentiment filter
                            e('div', { style: { flex: '1 1 150px', minWidth: '130px' } },
                                e('label', { 
                                    className: 'form-label', 
                                    style: { fontSize: '0.75rem', marginBottom: '0.25rem' } 
                                }, 'Sentiment'),
                                e('select', {
                                    className: 'form-input',
                                    value: sentimentFilter,
                                    onChange: (e) => setSentimentFilter(e.target.value),
                                    style: { fontSize: '0.875rem' }
                                },
                                    e('option', { value: 'all' }, 'All Sentiment'),
                                    e('option', { value: 'positive' }, 'Positive'),
                                    e('option', { value: 'negative' }, 'Negative'),
                                    e('option', { value: 'neutral' }, 'Neutral')
                                )
                            ),
                            
                            // Lookback period
                            e('div', { style: { flex: '1 1 150px', minWidth: '130px' } },
                                e('label', { 
                                    className: 'form-label', 
                                    style: { fontSize: '0.75rem', marginBottom: '0.25rem' } 
                                }, 'Lookback Period'),
                                e('select', {
                                    className: 'form-input',
                                    value: lookbackHours,
                                    onChange: (e) => setLookbackHours(Number(e.target.value)),
                                    style: { fontSize: '0.875rem' }
                                },
                                    e('option', { value: 24 }, '24 hours'),
                                    e('option', { value: 48 }, '48 hours'),
                                    e('option', { value: 72 }, '72 hours'),
                                    e('option', { value: 168 }, '1 week')
                                )
                            ),
                            
                            // Impact threshold
                            e('div', { style: { flex: '1 1 150px', minWidth: '130px' } },
                                e('label', { 
                                    className: 'form-label', 
                                    style: { fontSize: '0.75rem', marginBottom: '0.25rem' } 
                                }, 'Min Impact'),
                                e('select', {
                                    className: 'form-input',
                                    value: minImpactThreshold,
                                    onChange: (e) => setMinImpactThreshold(Number(e.target.value)),
                                    style: { fontSize: '0.875rem' }
                                },
                                    e('option', { value: 0.01 }, 'Low (1%)'),
                                    e('option', { value: 0.02 }, 'Medium (2%)'),
                                    e('option', { value: 0.05 }, 'High (5%)'),
                                    e('option', { value: 0.10 }, 'Very High (10%)')
                                )
                            ),
                            
                            // Clear filters button
                            (filterSymbol || sentimentFilter !== 'all') && e('button', {
                                onClick: () => {
                                    setFilterSymbol('');
                                    setSentimentFilter('all');
                                },
                                style: { 
                                    background: 'transparent',
                                    border: '1px solid var(--border-primary)',
                                    padding: '0.5rem 1rem',
                                    borderRadius: '6px',
                                    color: 'var(--text-secondary)',
                                    cursor: 'pointer',
                                    fontSize: '0.875rem',
                                    alignSelf: 'flex-end'
                                }
                            }, 'Clear Filters')
                        )
                    ),
                    
                    // Portfolio Securities Prices using PatternRenderer
                    e('div', { className: 'card', style: { marginBottom: '1.5rem' } },
                        e('div', { className: 'card-header' },
                            e('h3', { className: 'card-title' }, 'Portfolio Security Prices')
                        ),
                        e(PatternRenderer, {
                            key: `portfolio-prices-${refreshKey}`,
                            pattern: 'portfolio_overview',
                            inputs: patternInputs,
                            config: {
                                showPanels: ['holdings'],  // Only show holdings panel with prices
                                compact: true
                            },
                            onDataLoaded: handlePortfolioDataLoaded
                        })
                    ),
                    
                    // News Impact Analysis using PatternRenderer with dynamic inputs
                    // Pass filters as config to be used by NewsListPanel for client-side filtering
                    e(PatternRenderer, {
                        key: `${refreshKey}-${filterSymbol}-${sentimentFilter}-${lookbackHours}-${minImpactThreshold}`,
                        pattern: 'news_impact_analysis',
                        inputs: {
                            portfolio_id: portfolioId || getCurrentPortfolioId(),
                            lookback_hours: lookbackHours,
                            min_impact_threshold: minImpactThreshold
                        },
                        config: {
                            filterSymbol: filterSymbol,
                            sentimentFilter: sentimentFilter
                        }
                    })
                );
            }
            
            // Security Detail Page - Shows deep analysis for individual holdings
            function SecurityDetailPage() {
                const { portfolioId } = useUserContext();
                const [currentSymbol, setCurrentSymbol] = useState(null);
                const [currentSecurityId, setCurrentSecurityId] = useState(null);
                const [loading, setLoading] = useState(false);
                const [error, setError] = useState(null);
                
                // Get security info from global state (set by Holdings page)
                useEffect(() => {
                    const securityInfo = window.selectedSecurity;
                    if (securityInfo) {
                        setCurrentSymbol(securityInfo.symbol);
                        setCurrentSecurityId(securityInfo.security_id);
                    }
                }, []);
                
                const goBackToHoldings = () => {
                    // Clear selected security
                    window.selectedSecurity = null;
                    // Navigate back to holdings
                    const event = new CustomEvent('navigate', { detail: { page: 'holdings' } });
                    window.dispatchEvent(event);
                };
                
                if (!currentSecurityId) {
                    return e('div', { className: 'security-detail-page' },
                        e('div', { className: 'page-header' },
                            e('button', { 
                                className: 'button button-secondary',
                                onClick: goBackToHoldings
                            }, '← Back to Holdings')
                        ),
                        e('div', { className: 'message' }, 'Select a security from Holdings to view details')
                    );
                }
                
                return e('div', { className: 'security-detail-page' },
                    e('div', { className: 'page-header' },
                        e('button', { 
                            className: 'button button-secondary',
                            onClick: goBackToHoldings,
                            style: { marginBottom: '1rem' }
                        }, '← Back to Holdings'),
                        e('h1', { className: 'page-title' }, `Security Analysis: ${currentSymbol || 'Loading...'}`),
                        e('p', { className: 'page-description' }, 'Detailed analysis of position, performance, risk, and contribution')
                    ),
                    
                    // PatternRenderer for holding deep dive
                    e(PatternRenderer, {
                        pattern: 'holding_deep_dive',
                        inputs: {
                            portfolio_id: portfolioId,
                            security_id: currentSecurityId,
                            lookback_days: 252
                        },
                        config: {
                            showMetadata: true
                        }
                    })
                );
            }
            
            function SettingsPage() {
                return e('div', null,
                    e('div', { className: 'page-header' },
                        e('h1', { className: 'page-title' }, 'Settings'),
                        e('p', { className: 'page-description' }, 'Configure your account and preferences')
                    ),
                    e('div', { className: 'card' },
                        e('div', { className: 'card-header' },
                            e('h3', { className: 'card-title' }, 'Account Settings')
                        ),
                        e('div', { style: { padding: '1rem' } },
                            e('div', { style: { marginBottom: '1rem' } },
                                e('label', { className: 'form-label' }, 'Email'),
                                e('input', { 
                                    className: 'form-input', 
                                    value: 'michael@dawsos.com',
                                    disabled: true 
                                })
                            ),
                            e('div', { style: { marginBottom: '1rem' } },
                                e('label', { className: 'form-label' }, 'Base Currency'),
                                e('select', { className: 'form-input' },
                                    e('option', null, 'USD'),
                                    e('option', null, 'EUR'),
                                    e('option', null, 'GBP')
                                )
                            )
                        )
                    )
                );
            }

    // ============================================
    // Expose Page Components
    // ============================================

    // Assign all page components to Pages namespace
    Pages.LoginPage = LoginPage;
    Pages.MacroCyclesPage = MacroCyclesPage;
    Pages.DashboardPage = DashboardPage;
    Pages.DashboardPageLegacy = DashboardPageLegacy;
    Pages.HoldingsPage = HoldingsPage;
    Pages.TransactionsPage = TransactionsPage;
    Pages.PerformancePage = PerformancePage;
    Pages.ScenariosPage = ScenariosPage;
    Pages.ScenariosPageLegacy = ScenariosPageLegacy;
    Pages.RiskPage = RiskPage;
    Pages.AttributionPage = AttributionPage;
    Pages.OptimizerPage = OptimizerPage;
    Pages.RatingsPage = RatingsPage;
    Pages.AIInsightsPage = AIInsightsPage;
    Pages.AIAssistantPage = AIAssistantPage;
    Pages.AlertsPage = AlertsPage;
    Pages.ReportsPage = ReportsPage;
    Pages.CorporateActionsPage = CorporateActionsPage;
    Pages.MarketDataPage = MarketDataPage;
    Pages.SecurityDetailPage = SecurityDetailPage;
    Pages.SettingsPage = SettingsPage;

    // Also expose supporting components
    Pages.PortfolioOverview = PortfolioOverview;
    Pages.HoldingsTable = HoldingsTable;

    // Expose to global DawsOS namespace
    global.DawsOS.Pages = Pages;

    // Log successful initialization
    if (Logger) {
        Logger.checkpoint('DawsOS Pages module loaded successfully');
        Logger.debug('Available pages:', Object.keys(Pages));
    } else {
        console.log('DawsOS Pages module loaded successfully');
        console.log('Available pages:', Object.keys(Pages));
    }
    
    // Register module with validator when ready (with retry logic)
    function registerModule() {
        if (!global.DawsOS?.ModuleValidator) {
            return false;
        }
        try {
            global.DawsOS.ModuleValidator.validate('pages.js');
            if (Logger) {
                Logger.debug('[pages] Module validated');
            } else {
                console.log('[pages] Module validated');
            }
            return true;
        } catch (e) {
            return false;
        }
    }
    
    // Retry validation until successful
    let validationAttempts = 0;
    const maxValidationAttempts = 20;
    function tryRegisterModule() {
        if (registerModule()) {
            return; // Success
        }
        validationAttempts++;
        if (validationAttempts < maxValidationAttempts) {
            setTimeout(tryRegisterModule, 50);
            } else {
                if (Logger) {
                    Logger.warn('[pages] Failed to validate after', maxValidationAttempts, 'attempts');
                } else {
                    console.warn('[pages] Failed to validate after', maxValidationAttempts, 'attempts');
                }
            }
    }
    tryRegisterModule();

})(window);
