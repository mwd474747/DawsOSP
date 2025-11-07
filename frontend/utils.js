/**
 * DawsOS Frontend Utility Functions
 *
 * EXTRACTED FROM: /Users/mdawson/Documents/GitHub/DawsOSP/full_ui.html
 * EXTRACTION DATE: 2025-11-07
 *
 * This file contains utility functions extracted from the full_ui.html file.
 * All functions are preserved exactly as they appeared in the source.
 *
 * NOTE: These include React components that require React/JSX dependencies.
 * Use with React 16.8+ (hooks support required).
 *
 * DEPENDENCIES:
 * - React (useState, useEffect hooks)
 * - ErrorHandler (from error handling utilities)
 * - CacheManager (for useCachedQuery/useCachedMutation)
 * - 'e' function (React.createElement shorthand)
 */

(function(global) {
    'use strict';

    // Initialize DawsOS namespace if not exists
    if (!global.DawsOS) {
        global.DawsOS = {};
    }

    // Import CacheManager from module (required for useCachedQuery/useCachedMutation)
    const CacheManager = global.DawsOS.CacheManager;
    if (!CacheManager) {
        console.error('[Utils] CacheManager not loaded! Ensure cache-manager.js loads before utils.js');
        throw new Error('[Utils] CacheManager module not available. Check script load order.');
    }

    console.log('[Utils] CacheManager loaded successfully');

    // Create Utils namespace
    const Utils = {};

    /**
     * formatCurrency - Format number as currency
     */
    Utils.formatCurrency = function(value, decimals = 2) {
        if (value === null || value === undefined || isNaN(value)) return '-';
        const absValue = Math.abs(value);
        const sign = value < 0 ? '-' : '';

        if (absValue >= 1e9) {
            return sign + '$' + (absValue / 1e9).toFixed(1) + 'B';
        } else if (absValue >= 1e6) {
            return sign + '$' + (absValue / 1e6).toFixed(1) + 'M';
        } else if (absValue >= 1e3) {
            return sign + '$' + (absValue / 1e3).toFixed(1) + 'K';
        }
        return sign + '$' + absValue.toFixed(decimals);
    };

    /**
     * formatPercentage - Format number as percentage
     */
    Utils.formatPercentage = function(value, decimals = 2) {
        if (value === null || value === undefined || isNaN(value)) return '-';
        return (value * 100).toFixed(decimals) + '%';
    };

    /**
     * formatNumber - Format number with specified decimals
     */
    Utils.formatNumber = function(value, decimals = 2) {
        if (value === null || value === undefined || isNaN(value)) return '-';
        return value.toLocaleString('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    };

    /**
     * formatDate - Format date string
     */
    Utils.formatDate = function(dateString) {
        if (!dateString) return '-';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (e) {
            return dateString;
        }
    };

    /**
     * formatValue - Format values according to specified format type
     * Lines 4637-4659
     */
    Utils.formatValue = function(value, format) {
        if (value === null || value === undefined || value === '') return '-';

        // Convert string values to numbers for numeric formats
        let numValue = value;
        if (typeof value === 'string' && (format === 'percentage' || format === 'currency' || format === 'number' || format === 'bps')) {
            numValue = parseFloat(value);
            if (isNaN(numValue)) return '-';
        }

        switch (format) {
            case 'percentage':
                return Utils.formatPercentage(numValue);
            case 'currency':
                return Utils.formatCurrency(numValue);
            case 'number':
                return Utils.formatNumber(numValue, 2);
            case 'bps':
                return Utils.formatNumber(numValue, 0) + ' bps';
            default:
                return typeof value === 'number' ? Utils.formatNumber(value, 2) : String(value);
        }
    };

    /**
     * getColorClass - Get color class based on value and format
     * Lines 4661-4666
     */
    Utils.getColorClass = function(value, format) {
        if (format === 'percentage' || format === 'currency') {
            return value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral';
        }
        return '';
    };

    /**
     * useCachedQuery - React Hook for cached queries with automatic invalidation
     * Lines 6379-6451
     */
    Utils.useCachedQuery = function(queryKey, queryFn, options = {}) {
        const [state, setState] = React.useState({
            data: null,
            error: null,
            isLoading: true,
            isStale: false,
            isFetching: false
        });

        React.useEffect(() => {
            let mounted = true;

            // Subscribe to cache updates
            const unsubscribe = CacheManager.subscribe(queryKey, (update) => {
                if (mounted) {
                    if (update.invalidated) {
                        // Refetch on invalidation
                        fetchData();
                    } else {
                        setState(prev => ({
                            ...prev,
                            data: update.data,
                            error: update.error,
                            isStale: update.isStale || false
                        }));
                    }
                }
            });

            // Fetch data
            const fetchData = async () => {
                setState(prev => ({ ...prev, isFetching: true }));

                try {
                    const result = await CacheManager.get(queryKey, queryFn, options);

                    if (mounted) {
                        setState({
                            data: result.data,
                            error: result.error,
                            isLoading: false,
                            isStale: result.isStale,
                            isFetching: result.isFetching || false
                        });
                    }
                } catch (error) {
                    if (mounted) {
                        setState({
                            data: null,
                            error,
                            isLoading: false,
                            isStale: false,
                            isFetching: false
                        });
                    }
                }
            };

            fetchData();

            // Cleanup
            return () => {
                mounted = false;
                unsubscribe();
            };
        }, [JSON.stringify(queryKey)]);

        return state;
    };

    /**
     * useCachedMutation - React Hook for mutations with cache invalidation
     * Lines 6452-6551
     */
    Utils.useCachedMutation = function(mutationFn, options = {}) {
        const [state, setState] = React.useState({
            isLoading: false,
            error: null,
            data: null
        });

        const mutate = async (variables) => {
            setState({ isLoading: true, error: null, data: null });

            try {
                const result = await mutationFn(variables);

                // Invalidate related queries
                if (options.onSuccess) {
                    options.onSuccess(result, variables);
                }

                setState({ isLoading: false, error: null, data: result });
                return result;
            } catch (error) {
                if (options.onError) {
                    options.onError(error, variables);
                }

                setState({ isLoading: false, error, data: null });
                throw error;
            }
        };

        return { mutate, ...state };
    };

    /**
     * ProvenanceWarningBanner - Component that displays warnings for stub data
     * Lines 6872-6938
     */
    Utils.ProvenanceWarningBanner = function({ warnings = [] }) {
        if (!warnings || warnings.length === 0) return null;

        const allWarnings = warnings.flatMap(w => w.warnings || []);
        const uniqueWarnings = [...new Set(allWarnings)];

        if (uniqueWarnings.length === 0) return null;

        return React.createElement('div', {
            className: 'provenance-warning-banner',
            style: {
                backgroundColor: '#fff3cd',
                borderLeft: '4px solid #ffc107',
                padding: '12px 16px',
                marginBottom: '16px',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px'
            }
        },
            React.createElement('span', {
                style: {
                    fontSize: '20px',
                    lineHeight: '1'
                }
            }, '⚠️'),
            React.createElement('div', {
                style: {
                    flex: 1
                }
            },
                React.createElement('div', {
                    style: {
                        fontWeight: '600',
                        marginBottom: '8px',
                        color: '#856404'
                    }
                }, 'Data Quality Warning'),
                React.createElement('ul', {
                    style: {
                        margin: 0,
                        paddingLeft: '20px',
                        color: '#856404'
                    }
                },
                    ...uniqueWarnings.map(warning =>
                        React.createElement('li', { key: warning }, warning)
                    )
                ),
                React.createElement('div', {
                    style: {
                        marginTop: '8px',
                        fontSize: '0.875rem',
                        fontStyle: 'italic',
                        color: '#856404'
                    }
                }, '⚠️ This data is not suitable for investment decisions')
            )
        );
    };

    /**
     * DataBadge - Component that shows data source provenance
     * Lines 6939-7009
     */
    Utils.DataBadge = function({ source = 'demo', position = 'top-right', style = {} }) {
        const getBadgeConfig = () => {
            switch(source.toLowerCase()) {
                case 'live':
                    return {
                        text: 'Live Data',
                        color: '#10b981', // green
                        bgColor: 'rgba(16, 185, 129, 0.1)',
                        borderColor: 'rgba(16, 185, 129, 0.3)'
                    };
                case 'cached':
                    return {
                        text: 'Cached',
                        color: '#f59e0b', // yellow
                        bgColor: 'rgba(245, 158, 11, 0.1)',
                        borderColor: 'rgba(245, 158, 11, 0.3)'
                    };
                case 'demo':
                default:
                    return {
                        text: 'Demo Data',
                        color: '#ef4444', // red
                        bgColor: 'rgba(239, 68, 68, 0.1)',
                        borderColor: 'rgba(239, 68, 68, 0.3)'
                    };
            }
        };

        const getPositionStyle = () => {
            const positions = {
                'top-right': { top: '0.5rem', right: '0.5rem' },
                'top-left': { top: '0.5rem', left: '0.5rem' },
                'bottom-right': { bottom: '0.5rem', right: '0.5rem' },
                'bottom-left': { bottom: '0.5rem', left: '0.5rem' }
            };
            return positions[position] || positions['top-right'];
        };

        const config = getBadgeConfig();

        // Log when badge is rendered
        React.useEffect(() => {
            console.log(`[DataBadge] Showing ${config.text} badge at ${position}`);
        }, [source]);

        return React.createElement('div', {
            className: 'data-provenance-badge',
            style: {
                position: 'absolute',
                ...getPositionStyle(),
                padding: '0.25rem 0.5rem',
                fontSize: '0.625rem',
                fontWeight: '600',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                color: config.color,
                backgroundColor: config.bgColor,
                border: `1px solid ${config.borderColor}`,
                borderRadius: '4px',
                zIndex: 10,
                pointerEvents: 'none',
                ...style
            }
        }, config.text);
    };

    /**
     * withDataProvenance - Higher-Order Component that adds data provenance badge
     * Lines 7010-7037
     */
    Utils.withDataProvenance = function(Component, getDataSource = () => 'demo') {
        return function WrappedComponent(props) {
            const [dataSource, setDataSource] = React.useState('demo');

            React.useEffect(() => {
                // Determine data source based on props
                const source = getDataSource(props);
                setDataSource(source);
                console.log(`[withDataProvenance] Data source determined: ${source}`, props);
            }, [props]);

            return React.createElement('div', {
                style: {
                    position: 'relative',
                    display: 'inline-block',
                    width: '100%'
                }
            },
                React.createElement(Component, props),
                React.createElement(Utils.DataBadge, { source: dataSource })
            );
        };
    };

    /**
     * getDataSourceFromResponse - Helper function to determine data source from API responses
     * Lines 7037-7072
     */
    Utils.getDataSourceFromResponse = function(data) {
        if (!data) return 'demo';

        // Phase 1: Metadata removed from results (moved to trace only)
        // Metadata no longer available in results, use default 'demo'
        // TODO: Read from trace if data source display is needed

        // Check for error states that indicate demo data
        if (data.error || data.fallback) {
            return 'demo';
        }

        // Check for timestamps to determine if cached
        if (data.cached_at || data._cached) {
            const cacheAge = Date.now() - new Date(data.cached_at || data._cached).getTime();
            // If cached data is less than 5 minutes old, consider it "live enough"
            return cacheAge < 5 * 60 * 1000 ? 'live' : 'cached';
        }

        // Check for real-time indicators
        if (data.realtime || data.live || data.timestamp) {
            const dataAge = data.timestamp ? Date.now() - new Date(data.timestamp).getTime() : 0;
            return dataAge < 60 * 1000 ? 'live' : 'cached';
        }

        // Default to demo if we can't determine
        return 'demo';
    };

    /**
     * ErrorMessage - Component that displays error messages with appropriate styling
     * Lines 7073-7130
     */
    Utils.ErrorMessage = function({ error, onRetry, canDismiss = true }) {
        const [dismissed, setDismissed] = React.useState(false);

        if (dismissed) return null;

        const errorInfo = ErrorHandler.classifyError(error);
        const suggestions = ErrorHandler.getSuggestions(errorInfo);

        const getSeverityClass = () => {
            switch (errorInfo.severity) {
                case 'warning': return 'error-message-warning';
                case 'info': return 'error-message-info';
                default: return 'error-message-error';
            }
        };

        const getIcon = () => {
            switch (errorInfo.severity) {
                case 'warning': return '⚠️';
                case 'info': return 'ℹ️';
                default: return '❌';
            }
        };

        return React.createElement('div', { className: `error-message ${getSeverityClass()}` },
            React.createElement('div', { className: 'error-message-content' },
                React.createElement('div', { className: 'error-message-header' },
                    React.createElement('span', { className: 'error-message-icon' }, getIcon()),
                    React.createElement('span', { className: 'error-message-text' }, errorInfo.message),
                    canDismiss && React.createElement('button', {
                        className: 'error-message-close',
                        onClick: () => setDismissed(true),
                        'aria-label': 'Dismiss'
                    }, '×')
                ),

                suggestions.length > 0 && React.createElement('div', { className: 'error-message-suggestions' },
                    React.createElement('div', { className: 'suggestions-title' }, 'Suggestions:'),
                    React.createElement('ul', { className: 'suggestions-list' },
                        suggestions.map((suggestion, index) =>
                            React.createElement('li', { key: index }, suggestion)
                        )
                    )
                ),

                errorInfo.canRetry && onRetry && React.createElement('div', { className: 'error-message-actions' },
                    React.createElement('button', {
                        className: 'btn-retry',
                        onClick: onRetry
                    }, 'Try Again')
                )
            )
        );
    };

    /**
     * LoadingSpinner - Component that displays a consistent loading indicator
     * Lines 7131-7142
     */
    Utils.LoadingSpinner = function({ size = 'medium', message }) {
        const sizeClass = `spinner-${size}`;

        return React.createElement('div', { className: 'loading-container' },
            React.createElement('div', { className: `spinner ${sizeClass}` }),
            message && React.createElement('div', { className: 'loading-message' }, message)
        );
    };

    /**
     * EmptyState - Component that displays when no data is available
     * Lines 7143-7156
     */
    Utils.EmptyState = function({ title, message, icon, action }) {
        return React.createElement('div', { className: 'empty-state' },
            icon && React.createElement('div', { className: 'empty-state-icon' }, icon),
            React.createElement('h3', { className: 'empty-state-title' }, title || 'No data available'),
            React.createElement('p', { className: 'empty-state-message' },
                message || 'There is no data to display at this time.'
            ),
            action && React.createElement('div', { className: 'empty-state-action' }, action)
        );
    };

    /**
     * FormField - Component for form fields with validation error display
     * Lines 7157-7172
     */
    Utils.FormField = function({ label, error, required, children }) {
        const hasError = Boolean(error);

        return React.createElement('div', { className: `form-group ${hasError ? 'has-error' : ''}` },
            label && React.createElement('label', { className: 'form-label' },
                label,
                required && React.createElement('span', { className: 'required-marker' }, ' *')
            ),
            children,
            hasError && React.createElement('div', { className: 'form-error' }, error)
        );
    };

    /**
     * NetworkStatusIndicator - Component that shows current network status
     * Lines 7173-7199
     */
    Utils.NetworkStatusIndicator = function() {
        const [isOnline, setIsOnline] = React.useState(window.navigator.onLine);

        React.useEffect(() => {
            const handleOnline = () => setIsOnline(true);
            const handleOffline = () => setIsOnline(false);

            window.addEventListener('online', handleOnline);
            window.addEventListener('offline', handleOffline);

            return () => {
                window.removeEventListener('online', handleOnline);
                window.removeEventListener('offline', handleOffline);
            };
        }, []);

        if (isOnline) return null;

        return React.createElement('div', { className: 'network-status-indicator' },
            React.createElement('span', { className: 'network-status-icon' }, '🔌'),
            React.createElement('span', { className: 'network-status-text' }, 'No internet connection')
        );
    };

    /**
     * RetryableError - Component with exponential backoff retry logic
     * Lines 7200-7246
     */
    Utils.RetryableError = function({ error, onRetry, maxRetries = 3 }) {
        const [retryCount, setRetryCount] = React.useState(0);
        const [isRetrying, setIsRetrying] = React.useState(false);

        const handleRetry = async () => {
            if (retryCount >= maxRetries) {
                return;
            }

            setIsRetrying(true);

            // Exponential backoff
            const delay = Math.pow(2, retryCount) * 1000;
            await new Promise(resolve => setTimeout(resolve, delay));

            setRetryCount(prev => prev + 1);
            setIsRetrying(false);

            if (onRetry) {
                onRetry();
            }
        };

        const errorInfo = ErrorHandler.classifyError(error);

        return React.createElement('div', { className: 'retryable-error' },
            React.createElement('div', { className: 'error-content' },
                React.createElement('h3', null, 'Unable to load data'),
                React.createElement('p', null, errorInfo.message),
                retryCount > 0 && React.createElement('p', { className: 'retry-count' },
                    `Retry attempt ${retryCount} of ${maxRetries}`
                ),

                React.createElement('div', { className: 'error-actions' },
                    isRetrying ?
                        React.createElement(Utils.LoadingSpinner, { size: 'small', message: 'Retrying...' }) :
                        retryCount < maxRetries && React.createElement('button', {
                            className: 'btn btn-primary',
                            onClick: handleRetry,
                            disabled: isRetrying
                        }, 'Retry'),

                    retryCount >= maxRetries && React.createElement('div', { className: 'max-retries-reached' },
                        React.createElement('p', null, 'Maximum retry attempts reached.'),
                        React.createElement('button', {
                            className: 'btn',
                            onClick: () => window.location.reload()
                        }, 'Reload Page')
                    )
                )
            )
        );
    };

    // Expose Utils via global DawsOS namespace
    global.DawsOS.Utils = Utils;

})(typeof window !== 'undefined' ? window : global);
