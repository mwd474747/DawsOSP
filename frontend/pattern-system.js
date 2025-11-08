/**
 * DawsOS Pattern System
 *
 * Extracted from: full_ui.html
 * Extraction Date: 2025-11-07
 *
 * This module contains the pattern orchestration and registry system for DawsOS.
 * It provides pattern rendering, panel dispatching, and pattern metadata.
 *
 * Dependencies:
 * - React (useState, useEffect) - Required for component state management
 * - DawsOS.Utils - Utility functions (formatValue, LoadingSpinner, ErrorMessage)
 * - DawsOS.Panels - All panel components (MetricsGridPanel, TablePanel, ChartPanels, etc.)
 * - DawsOS.Context - Context hooks (useUserContext, getCurrentPortfolioId)
 * - DawsOS.APIClient - API client for pattern execution
 * - ErrorHandler - Global error handler (remains in full_ui.html)
 * - CacheManager - Global cache manager (remains in full_ui.html)
 * - TokenManager - Global token manager (remains in full_ui.html)
 * - ProvenanceWarningBanner - Phase 1 stub data warning component
 *
 * Components Exposed:
 * - getDataByPath - Extract data from nested object paths
 * - PatternRenderer - Main pattern orchestration component
 * - PanelRenderer - Panel rendering dispatcher
 * - patternRegistry - Pattern metadata and configuration
 * - queryKeys - Query key generation for caching
 * - queryHelpers - Data fetching helpers with caching
 *
 * @module DawsOS.PatternSystem
 */

(function(global) {
    'use strict';

    // Ensure DawsOS namespace exists
    if (!global.DawsOS) {
        global.DawsOS = {};
    }

    // Initialize placeholder namespace immediately with safe defaults
    global.DawsOS.PatternSystem = {
        PatternPanel: function PlaceholderPatternPanel() {
            if (global.React && global.React.createElement) {
                return global.React.createElement('div', null, 'Loading Pattern Panel...');
            }
            return null;
        },
        PatternComposerPanel: function PlaceholderComposerPanel() {
            if (global.React && global.React.createElement) {
                return global.React.createElement('div', null, 'Loading Pattern Composer...');
            }
            return null;
        },
        isInitialized: false
    };

    // Define initialization function that can be called multiple times
    function initializePatternSystem() {
        const Logger = global.DawsOS?.Logger;
        
        // Check if React is available
        if (!global.React) {
            if (Logger) {
                Logger.debug('[PatternSystem] React not available, will retry...');
            } else {
                (global.DawsOS?.Logger || console).debug('[PatternSystem] React not available, will retry...');
            }
            setTimeout(initializePatternSystem, 100);
            return;
        }
        
        // Check if APIClient is available
        if (!global.DawsOS?.APIClient) {
            if (Logger) {
                Logger.debug('[PatternSystem] APIClient not ready, will retry...');
            } else {
                (global.DawsOS?.Logger || console).debug('[PatternSystem] APIClient not ready, will retry...');
            }
            setTimeout(initializePatternSystem, 100);
            return;
        }
        
        // Check if Panels are available
        if (!global.DawsOS?.Panels) {
            if (Logger) {
                Logger.debug('[PatternSystem] Panels not ready, will retry...');
            } else {
                (global.DawsOS?.Logger || console).debug('[PatternSystem] Panels not ready, will retry...');
            }
            setTimeout(initializePatternSystem, 100);
            return;
        }
        
        // Don't re-initialize if already done
        if (global.DawsOS.PatternSystem?.isInitialized) {
            return;
        }
        
        // Validate that panel components are available before marking as initialized
        // This prevents race conditions where pattern-system.js loads before panels.js
        const PanelsNamespace = global.DawsOS?.Panels || {};
        const requiredPanels = ['MetricsGridPanel', 'TablePanel', 'LineChartPanel', 'PieChartPanel', 'DonutChartPanel', 'BarChartPanel', 'ActionCardsPanel', 'CycleCardPanel', 'ScorecardPanel', 'DualListPanel', 'NewsListPanel', 'ReportViewerPanel'];
        const missingPanels = requiredPanels.filter(name => !PanelsNamespace[name]);
        
        if (missingPanels.length > 0) {
            if (Logger) {
                Logger.warn(`[PatternSystem] Missing panel components: ${missingPanels.join(', ')}. Retrying in 100ms...`);
            } else {
                console.warn(`[PatternSystem] Missing panel components: ${missingPanels.join(', ')}. Retrying in 100ms...`);
            }
            // Retry initialization after a short delay
            setTimeout(initializePatternSystem, 100);
            return;
        }
        
        if (Logger) {
            Logger.checkpoint('[PatternSystem] All dependencies ready, initializing...');
        } else {
            console.log('[PatternSystem] All dependencies ready, initializing...');
        }

    // Import React hooks (now we know React is available)
    const { createElement: e, useState, useEffect } = global.React;

    // Import from DawsOS modules (with correct namespaces)
    const { useUserContext, getCurrentPortfolioId } = global.DawsOS?.Context || {};
    // Note: apiClient methods are directly on DawsOS.APIClient, not nested
    const apiClient = global.DawsOS.APIClient;
    const TokenManagerFromAPI = apiClient.TokenManager;

    // DO NOT destructure panel components during initialization
    // This causes race conditions - components may be undefined if panels.js hasn't loaded yet
    // Instead, PanelRenderer will dynamically lookup components at render time
    // This ensures components are always fresh, even if they load after pattern-system.js

    // Import global utilities (these remain in full_ui.html)
    // NOTE: DO NOT destructure these components during initialization - they may not be loaded yet
    // Instead, use dynamic lookup at usage time: global.ErrorHandler, global.CacheManager, etc.
    // This prevents the same race condition that affected panel components
    const TokenManager = TokenManagerFromAPI || global.TokenManager;
    
    // Validate TokenManager
    if (!TokenManager) {
        if (Logger) {
            Logger.error('[PatternSystem] TokenManager not available from DawsOS.APIClient or global');
        } else {
            console.error('[PatternSystem] TokenManager not available from DawsOS.APIClient or global');
        }
        throw new Error('[PatternSystem] TokenManager is required but not found');
    }

    // ============================================
    // PATTERN REGISTRY
    // ============================================

    /**
     * Pattern Registry with metadata for all patterns
     * Contains pattern definitions, display configurations, and panel layouts
     */
    const patternRegistry = {
        portfolio_overview: {
            category: 'portfolio',
            name: 'Portfolio Overview',
            description: 'Comprehensive portfolio snapshot',
            icon: '📊',
            display: {
                panels: [
                    {
                        id: 'performance_strip',
                        title: 'Performance Metrics',
                        type: 'metrics_grid',
                        dataPath: 'perf_metrics',
                        config: {
                            columns: 5,
                            metrics: [
                                { key: 'twr_1y', label: 'TWR (1Y)', format: 'percentage' },
                                { key: 'twr_ytd', label: 'YTD Return', format: 'percentage' },
                                { key: 'mwr_1y', label: 'MWR (1Y)', format: 'percentage' },
                                { key: 'volatility', label: 'Volatility', format: 'percentage' },
                                { key: 'sharpe_ratio', label: 'Sharpe Ratio', format: 'number' },
                                { key: 'max_drawdown', label: 'Max Drawdown', format: 'percentage' },
                                { key: 'twr_1d', label: '1 Day', format: 'percentage' },
                                { key: 'twr_mtd', label: 'MTD', format: 'percentage' },
                                { key: 'current_drawdown', label: 'Current DD', format: 'percentage' },
                                { key: 'sortino_ratio', label: 'Sortino Ratio', format: 'number' }
                            ]
                        }
                    },
                    {
                        id: 'nav_chart',
                        title: 'Portfolio Value Over Time',
                        type: 'line_chart',
                        dataPath: 'historical_nav'
                    },
                    {
                        id: 'currency_attr',
                        title: 'Currency Attribution',
                        type: 'donut_chart',
                        dataPath: 'currency_attr'
                    },
                    {
                        id: 'sector_alloc',
                        title: 'Sector Allocation',
                        type: 'pie_chart',
                        dataPath: 'sector_allocation'
                    },
                    {
                        id: 'holdings_table',
                        title: 'Holdings',
                        type: 'table',
                        dataPath: 'valued_positions.positions',
                        config: {
                            columns: [
                                { field: 'symbol', header: 'Symbol', format: 'text' },
                                { field: 'quantity', header: 'Shares', format: 'number' },
                                { field: 'market_value', header: 'Market Value', format: 'currency' },
                                { field: 'cost_basis', header: 'Cost Basis', format: 'currency' },
                                { field: 'price', header: 'Price', format: 'currency' },
                                { field: 'weight', header: 'Weight (%)', format: 'percentage' },
                                { field: 'currency', header: 'Currency', format: 'text' }
                            ],
                            maxRows: 50
                        }
                    }
                ]
            }
        },

        portfolio_scenario_analysis: {
            category: 'risk',
            name: 'Scenario Analysis',
            description: 'Stress test portfolio with macro scenarios',
            icon: '⚡',
            display: {
                panels: [
                    {
                        id: 'scenario_impact',
                        title: 'Scenario Impact',
                        type: 'metrics_grid',
                        dataPath: 'scenario_result'
                    },
                    {
                        id: 'position_deltas',
                        title: 'Position Deltas',
                        type: 'table',
                        dataPath: 'scenario_result.position_deltas'
                    },
                    {
                        id: 'winners_losers',
                        title: 'Winners & Losers',
                        type: 'dual_list',
                        dataPath: 'scenario_result'
                    },
                    {
                        id: 'hedge_cards',
                        title: 'Hedge Suggestions',
                        type: 'action_cards',
                        dataPath: 'hedge_suggestions.suggestions'
                    }
                ]
            }
        },

        portfolio_cycle_risk: {
            category: 'risk',
            name: 'Cycle Risk Analysis',
            description: 'Analyze portfolio risk across economic cycles',
            icon: '🔄',
            display: {
                panels: [
                    {
                        id: 'cycle_risk_summary',
                        title: 'Cycle Risk Summary',
                        type: 'metrics_grid',
                        dataPath: 'cycle_risk_map'
                    },
                    {
                        id: 'vulnerabilities',
                        title: 'Vulnerabilities',
                        type: 'table',
                        dataPath: 'cycle_risk_map.amplified_factors'
                    }
                ]
            }
        },

        macro_cycles_overview: {
            category: 'macro',
            name: 'Macro Cycles Overview',
            description: 'Dalio framework: Debt, Empire, Civil cycles',
            icon: '🌍',
            display: {
                panels: [
                    {
                        id: 'stdc_panel',
                        title: 'Short-Term Debt Cycle',
                        type: 'cycle_card',
                        dataPath: 'stdc'
                    },
                    {
                        id: 'ltdc_panel',
                        title: 'Long-Term Debt Cycle',
                        type: 'cycle_card',
                        dataPath: 'ltdc'
                    },
                    {
                        id: 'empire_panel',
                        title: 'Empire Cycle',
                        type: 'cycle_card',
                        dataPath: 'empire'
                    },
                    {
                        id: 'civil_panel',
                        title: 'Civil/Internal Order Cycle',
                        type: 'cycle_card',
                        dataPath: 'civil'
                    }
                ]
            }
        },

        macro_trend_monitor: {
            category: 'macro',
            name: 'Macro Trend Monitor',
            description: 'Track key economic indicators and trends with alert suggestions',
            icon: '📈',
            display: {
                panels: [
                    {
                        id: 'trends_grid',
                        title: 'Economic Trends',
                        type: 'metrics_grid',
                        dataPath: 'trend_analysis'
                    },
                    {
                        id: 'indicators_chart',
                        title: 'Key Indicators',
                        type: 'line_chart',
                        dataPath: 'factor_history'
                    },
                    {
                        id: 'alert_suggestions',
                        title: 'Suggested Alerts',
                        type: 'action_cards',
                        dataPath: 'alert_suggestions.suggestions'
                    }
                ]
            }
        },

        buffett_checklist: {
            category: 'analysis',
            name: 'Buffett Quality Checklist',
            description: 'Buffett-style quality and moat scorecard',
            icon: '✅',
            display: {
                panels: [
                    {
                        id: 'quality_score',
                        title: 'Quality Scorecard',
                        type: 'scorecard',
                        dataPath: 'moat_strength'
                    },
                    {
                        id: 'moat_analysis',
                        title: 'Moat Strength',
                        type: 'scorecard',
                        dataPath: 'moat_strength'
                    },
                    {
                        id: 'dividend_safety',
                        title: 'Dividend Safety',
                        type: 'scorecard',
                        dataPath: 'dividend_safety'
                    },
                    {
                        id: 'resilience',
                        title: 'Balance Sheet Resilience',
                        type: 'metrics_grid',
                        dataPath: 'resilience'
                    }
                ]
            }
        },

        news_impact_analysis: {
            category: 'analysis',
            name: 'News Impact Analysis',
            description: 'Analyze news impact on portfolio with optional alerting',
            icon: '📰',
            display: {
                panels: [
                    {
                        id: 'news_summary',
                        title: 'Impact Summary',
                        type: 'metrics_grid',
                        dataPath: 'impact_analysis',
                        config: {
                            metrics: [
                                { key: 'total_items', label: 'News Analyzed', format: 'integer' },
                                { key: 'high_impact_count', label: 'High Impact', format: 'integer' },
                                { key: 'exposed_portfolio_pct', label: 'Portfolio Exposure', format: 'percentage' },
                                { key: 'overall_sentiment', label: 'Overall Sentiment', format: 'sentiment' }
                            ],
                            columns: 4
                        }
                    },
                    {
                        id: 'news_items',
                        title: 'Relevant News',
                        type: 'news_list',
                        dataPath: 'impact_analysis.news_with_impact'
                    },
                    {
                        id: 'entity_mentions',
                        title: 'Entity Mentions',
                        type: 'bar_chart',
                        dataPath: 'impact_analysis.entity_mentions'
                    },
                    {
                        id: 'alert_result',
                        title: 'Alert Status',
                        type: 'metrics_grid',
                        dataPath: 'alert_result',
                        config: {
                            metrics: [
                                { key: 'status', label: 'Alert Status', format: 'text' },
                                { key: 'alert_id', label: 'Alert ID', format: 'text' },
                                { key: 'created_at', label: 'Created At', format: 'datetime' }
                            ],
                            columns: 3
                        }
                    }
                ]
            }
        },

        holding_deep_dive: {
            category: 'portfolio',
            name: 'Holding Deep Dive',
            description: 'Detailed analysis of individual holdings',
            icon: '🔍',
            display: {
                panels: [
                    {
                        id: 'holding_metrics',
                        title: 'Holding Metrics',
                        type: 'metrics_grid',
                        dataPath: 'position'
                    },
                    {
                        id: 'fundamentals',
                        title: 'Fundamentals',
                        type: 'table',
                        dataPath: 'fundamentals'
                    }
                ]
            }
        },

        policy_rebalance: {
            category: 'action',
            name: 'Policy Rebalance',
            description: 'Generate rebalancing recommendations',
            icon: '⚖️',
            display: {
                panels: [
                    {
                        id: 'rebalance_summary',
                        title: 'Rebalance Summary',
                        type: 'metrics_grid',
                        dataPath: 'rebalance_result'
                    },
                    {
                        id: 'trade_proposals',
                        title: 'Trade Proposals',
                        type: 'table',
                        dataPath: 'rebalance_result.trades'
                    }
                ]
            }
        },

        cycle_deleveraging_scenarios: {
            category: 'action',
            name: 'Cycle Deleveraging Scenarios',
            description: 'Deleveraging strategies based on cycles',
            icon: '📉',
            display: {
                panels: [
                    {
                        id: 'deleveraging_options',
                        title: 'Deleveraging Options',
                        type: 'action_cards',
                        dataPath: 'options'
                    },
                    {
                        id: 'impact_analysis',
                        title: 'Impact Analysis',
                        type: 'table',
                        dataPath: 'impact'
                    }
                ]
            }
        },

        export_portfolio_report: {
            category: 'reports',
            name: 'Export Portfolio Report',
            description: 'Generate comprehensive portfolio PDF report',
            icon: '📄',
            display: {
                panels: [
                    {
                        id: 'report_status',
                        title: 'Export Status',
                        type: 'metrics_grid',
                        dataPath: 'pdf_result',
                        config: {
                            metrics: [
                                { key: 'status', label: 'Status', format: 'text' },
                                { key: 'file_size', label: 'File Size', format: 'bytes' },
                                { key: 'download_url', label: 'Download URL', format: 'url' },
                                { key: 'generated_at', label: 'Generated At', format: 'datetime' }
                            ],
                            columns: 4
                        }
                    },
                    {
                        id: 'report_preview',
                        title: 'Report Preview',
                        type: 'report_viewer',
                        dataPath: 'pdf_result.download_url'
                    }
                ]
            }
        },

        corporate_actions_upcoming: {
            category: 'corporate_actions',
            name: 'Upcoming Corporate Actions',
            description: 'Track dividends, splits, and earnings for portfolio holdings',
            icon: '📅',
            display: {
                panels: [
                    {
                        id: 'actions_table',
                        title: 'Upcoming Corporate Actions',
                        type: 'table',
                        dataPath: 'actions_with_impact.actions',
                        config: {
                            columns: [
                                { field: 'date', header: 'Date', width: 120 },
                                { field: 'symbol', header: 'Symbol', width: 100 },
                                { field: 'type', header: 'Type', width: 100 },
                                { field: 'amount', header: 'Amount', format: 'currency', width: 120 },
                                { field: 'portfolio_quantity', header: 'Shares', format: 'number', width: 100 },
                                { field: 'portfolio_impact', header: 'Impact', format: 'currency', width: 120 }
                            ],
                            sort_by: 'date',
                            sort_order: 'asc'
                        }
                    },
                    {
                        id: 'summary_metrics',
                        title: 'Summary',
                        type: 'metrics_grid',
                        dataPath: 'actions_with_impact.summary',
                        config: {
                            columns: 4,
                            metrics: [
                                { key: 'total_actions', label: 'Total Actions', format: 'number' },
                                { key: 'dividends_expected', label: 'Dividends Expected', format: 'currency' },
                                { key: 'splits_pending', label: 'Splits Pending', format: 'number' },
                                { key: 'earnings_releases', label: 'Earnings Releases', format: 'number' }
                            ]
                        }
                    },
                    {
                        id: 'notifications_list',
                        title: 'Notifications',
                        type: 'dual_list',
                        dataPath: 'actions_with_impact.notifications',
                        config: {
                            urgent_title: 'Urgent (Next 7 Days)',
                            informational_title: 'Upcoming'
                        }
                    }
                ]
            }
        },

        portfolio_macro_overview: {
            category: 'reports',
            name: 'Portfolio Macro Overview',
            description: 'Portfolio analysis with macro context',
            icon: '🌐',
            display: {
                panels: [
                    {
                        id: 'macro_context',
                        title: 'Macro Context',
                        type: 'metrics_grid',
                        dataPath: 'macro_context'
                    },
                    {
                        id: 'portfolio_positioning',
                        title: 'Portfolio Positioning',
                        type: 'table',
                        dataPath: 'positioning'
                    }
                ]
            }
        }
    };

    // ============================================
    // HELPER FUNCTIONS
    // ============================================

    /**
     * Helper function to extract data from nested path
     * @param {object} data - The data object to extract from
     * @param {string} path - Dot-separated path (e.g., 'user.profile.name')
     * @returns {*} The extracted data or null if not found
     */
    function getDataByPath(data, path) {
        if (!path || !data) return data;

        const parts = path.split('.');
        let current = data;

        for (const part of parts) {
            if (current && typeof current === 'object') {
                current = current[part];
            } else {
                return null;
            }
        }

        return current;
    }

    // ============================================
    // PATTERN RENDERER COMPONENT
    // ============================================

    /**
     * Generic Pattern Renderer Component
     * Handles pattern execution, loading states, error handling, and panel orchestration
     *
     * @param {object} props - Component props
     * @param {string} props.pattern - Pattern name from patternRegistry
     * @param {object} props.inputs - Pattern input parameters
     * @param {object} props.config - Rendering configuration
     * @param {function} props.onDataLoaded - Callback when data is loaded
     */
    function PatternRenderer({ pattern, inputs = {}, config = {}, onDataLoaded }) {
        const [loading, setLoading] = useState(true);
        const [error, setError] = useState(null);
        const [data, setData] = useState(null);
        const [panels, setPanels] = useState([]);
        const [provenanceWarnings, setProvenanceWarnings] = useState([]);
        const { portfolioId } = useUserContext();

        useEffect(() => {
            loadPattern();
        }, [pattern, portfolioId, JSON.stringify(inputs)]);

        // Listen for portfolio changes from the portfolio selector
        useEffect(() => {
            const handlePortfolioChange = (event) => {
                if (Logger) {
                    Logger.debug('Portfolio changed, reloading pattern:', pattern);
                } else {
                    console.log('Portfolio changed, reloading pattern:', pattern);
                }
                loadPattern();
            };

            window.addEventListener('portfolioChanged', handlePortfolioChange);

            return () => {
                window.removeEventListener('portfolioChanged', handlePortfolioChange);
            };
        }, [pattern, inputs]);

        const loadPattern = async () => {
            try {
                setLoading(true);
                setError(null);

                // Don't block execution - let backend handle authentication
                // Backend will return appropriate error if authentication required
                const token = TokenManager.getToken();
                if (!token) {
                    if (Logger) {
                        Logger.warn(`No authentication token for pattern ${pattern}`);
                    } else {
                        console.warn(`No authentication token for pattern ${pattern}`);
                    }
                    // Don't block - let backend handle auth
                    // Some patterns might not require auth
                }

                // Patterns that don't require portfolio_id
                const nonPortfolioPatterns = ['macro_cycles_overview', 'macro_trend_monitor'];
                const needsPortfolioId = !nonPortfolioPatterns.includes(pattern);

                // Build final inputs - only add portfolio_id if pattern needs it
                const finalInputs = { ...inputs };

                if (needsPortfolioId) {
                    // Ensure we always have a valid portfolio ID for portfolio patterns
                    let validPortfolioId = portfolioId || inputs.portfolio_id;

                    // If still no portfolio ID, use the fallback
                    if (!validPortfolioId) {
                        validPortfolioId = getCurrentPortfolioId();
                        if (Logger) {
                            Logger.warn('No portfolio ID in context or inputs, using fallback:', validPortfolioId);
                        } else {
                            console.warn('No portfolio ID in context or inputs, using fallback:', validPortfolioId);
                        }
                    }

                    // Add portfolio ID to inputs, ensuring it's always present
                    finalInputs.portfolio_id = validPortfolioId;
                }

                if (Logger) {
                    Logger.debug(`Executing pattern ${pattern} with inputs:`, finalInputs);
                } else {
                    console.log(`Executing pattern ${pattern} with inputs:`, finalInputs);
                }

                // Execute pattern
                const result = await apiClient.executePattern(pattern, finalInputs);

                if (Logger) {
                    Logger.debug(`Pattern ${pattern} execution result:`, result);
                } else {
                    console.log(`Pattern ${pattern} execution result:`, result);
                }

                // Get pattern metadata
                const metadata = patternRegistry[pattern];
                if (!metadata) {
                    throw new Error(`Pattern ${pattern} not found in registry`);
                }

                // PHASE 1 FIX: Check for provenance warnings in data
                const dataResult = result.data || result;
                const provenanceWarnings = [];

                // Recursively check for _provenance fields in data
                function checkProvenance(obj, path = '') {
                    if (!obj || typeof obj !== 'object') return;

                    if (obj._provenance && obj._provenance.type === 'stub') {
                        provenanceWarnings.push({
                            path: path || 'root',
                            warnings: obj._provenance.warnings || [],
                            recommendation: obj._provenance.recommendation || 'Do not use for investment decisions'
                        });
                    }

                    // Recursively check nested objects
                    for (const key in obj) {
                        if (key !== '_provenance' && obj.hasOwnProperty(key)) {
                            checkProvenance(obj[key], path ? `${path}.${key}` : key);
                        }
                    }
                }

                checkProvenance(dataResult);

                // Set data and panels
                setData(dataResult);
                setPanels(metadata.display.panels || []);
                setProvenanceWarnings(provenanceWarnings);
                setLoading(false);

                // Display warnings if found
                if (provenanceWarnings.length > 0) {
                    if (Logger) {
                        Logger.warn('Provenance warnings detected:', provenanceWarnings);
                    } else {
                        console.warn('Provenance warnings detected:', provenanceWarnings);
                    }
                }

                // Callback for parent components
                if (onDataLoaded) {
                    onDataLoaded(dataResult);
                }
            } catch (err) {
                if (Logger) {
                    Logger.error(`Error loading pattern ${pattern}:`, err);
                } else {
                    console.error(`Error loading pattern ${pattern}:`, err);
                }
                const errorMessage = err.message || 'Failed to load pattern';
                setError(errorMessage);
                setLoading(false);
                // Call onDataLoaded with error data if callback exists
                if (onDataLoaded) {
                    onDataLoaded({ error: errorMessage });
                }
            }
        };

        // If hidden (via config.hidden), return null to avoid blocking
        // The parent component will handle loading/error states
        const isHidden = config.hidden || (config.showPanels && config.showPanels.length === 0);

        if (loading && !isHidden) {
            return e('div', { className: 'loading-container' },
                e('div', { className: 'loading-spinner' }),
                e('p', null, `Loading ${patternRegistry[pattern]?.name || pattern.replace(/_/g, ' ')}...`)
            );
        }

        if (error && !isHidden) {
            // Provide more helpful error messages based on pattern type
            let errorMessage = String(error);
            let helpfulTip = '';

            if (pattern.includes('corporate_actions')) {
                if (errorMessage.includes('FMP') || errorMessage.includes('API')) {
                    helpfulTip = 'The corporate actions data provider may be temporarily unavailable. Please try again in a few moments.';
                } else if (errorMessage.includes('portfolio')) {
                    helpfulTip = 'Please ensure you have selected a valid portfolio with holdings.';
                } else {
                    helpfulTip = 'Corporate actions data is fetched from external providers. If your portfolio has no holdings, no actions will be shown.';
                }
            } else if (errorMessage.includes('401') || errorMessage.includes('authentication')) {
                helpfulTip = 'Your session may have expired. Please refresh the page and log in again.';
            } else if (errorMessage.includes('404')) {
                helpfulTip = 'The requested data could not be found. Please verify your portfolio selection.';
            }

            return e('div', { className: 'error-container' },
                e('h3', null, '⚠️ Unable to Load Data'),
                e('p', { style: { marginBottom: '1rem' } }, errorMessage),
                helpfulTip && e('p', { style: { fontSize: '0.9rem', opacity: 0.8 } }, `💡 ${helpfulTip}`),
                e('button', {
                    className: 'btn btn-primary',
                    onClick: loadPattern,
                    style: { marginTop: '1rem' }
                }, '🔄 Retry')
            );
        }

        // If hidden, return null to avoid rendering anything
        if (isHidden) {
            return null;
        }

        // Filter panels if config.showPanels is provided
        const filteredPanels = config.showPanels
            ? panels.filter(panel => config.showPanels.includes(panel.id))
            : panels;

        // DYNAMIC LOOKUP: Get ProvenanceWarningBanner at render time, not initialization time
        // This fixes the race condition where the component may not be loaded yet during initialization
        const ProvenanceWarningBanner = global.ProvenanceWarningBanner;
        
        // Defensive check - if component is not available, just skip rendering it
        // This prevents React Error #130 when the component is undefined
        const provenanceBannerElement = ProvenanceWarningBanner 
            ? e(ProvenanceWarningBanner, { warnings: provenanceWarnings })
            : null;
        
        return e('div', { className: 'pattern-content' },
            // PHASE 1 FIX: Display provenance warnings (only if component is available)
            provenanceBannerElement,
            filteredPanels.map(panel =>
                e(PanelRenderer, {
                    key: panel.id,
                    panel: panel,
                    data: getDataByPath(data, panel.dataPath),
                    fullData: data
                })
            )
        );
    }

    // ============================================
    // PANEL RENDERER COMPONENT
    // ============================================

    /**
     * Generic Panel Renderer that delegates to specific panel types
     *
     * @param {object} props - Component props
     * @param {object} props.panel - Panel configuration
     * @param {*} props.data - Panel data
     * @param {object} props.fullData - Full pattern data for context
     */
    function PanelRenderer({ panel, data, fullData }) {
        const { type, title, config } = panel;
        const Logger = global.DawsOS?.Logger;

        // DYNAMIC LOOKUP: Get panel component at render time, not initialization time
        // This fixes the race condition where panels.js may not be loaded yet during initialization
        const PanelsNamespace = global.DawsOS?.Panels || {};
        
        // Map panel type to component name
        const typeToComponentMap = {
            'metrics_grid': 'MetricsGridPanel',
            'table': 'TablePanel',
            'line_chart': 'LineChartPanel',
            'pie_chart': 'PieChartPanel',
            'donut_chart': 'DonutChartPanel',
            'bar_chart': 'BarChartPanel',
            'action_cards': 'ActionCardsPanel',
            'cycle_card': 'CycleCardPanel',
            'scorecard': 'ScorecardPanel',
            'dual_list': 'DualListPanel',
            'news_list': 'NewsListPanel',
            'report_viewer': 'ReportViewerPanel'
        };
        
        // Dynamically lookup component from Panels namespace
        const componentName = typeToComponentMap[type];
        let PanelComponent = componentName ? PanelsNamespace[componentName] : null;
        
        // If component not found, try to wait and retry (for race conditions)
        if (!PanelComponent && componentName) {
            // Log warning but don't block - component may load later
            if (Logger) {
                Logger.warn(`[PanelRenderer] Panel component "${componentName}" not yet available for type "${type}". Panels namespace may not be loaded yet.`);
            } else {
                console.warn(`[PanelRenderer] Panel component "${componentName}" not yet available for type "${type}". Panels namespace may not be loaded yet.`);
            }
            
            // Return loading state instead of error - component may load on next render
            return e('div', { className: 'card' },
                e('div', { className: 'card-header' },
                    e('h3', { className: 'card-title' }, title || 'Panel')
                ),
                e('div', { className: 'card-body', style: { padding: '2rem', textAlign: 'center', color: '#94a3b8' } },
                    e('div', { className: 'loading-spinner', style: { margin: '0 auto 1rem' } }),
                    e('p', null, `Loading panel component "${componentName}"...`)
                )
            );
        }
        
        // Validate component exists before rendering
        if (!PanelComponent) {
            if (Logger) {
                Logger.error(`[PanelRenderer] Panel component not available for type: ${type}. Available components: ${Object.keys(PanelsNamespace).join(', ')}`);
            } else {
                console.error(`[PanelRenderer] Panel component not available for type: ${type}. Available components: ${Object.keys(PanelsNamespace).join(', ')}`);
            }
            return e('div', { className: 'card' },
                e('div', { className: 'card-header' },
                    e('h3', { className: 'card-title' }, title || 'Panel')
                ),
                e('div', { className: 'card-body', style: { padding: '2rem', textAlign: 'center', color: '#94a3b8' } },
                    e('p', null, `Panel type "${type}" is not available. Please check that all panel components are loaded.`),
                    e('p', { style: { fontSize: '0.875rem', marginTop: '0.5rem', color: '#64748b' } }, 
                        `Available components: ${Object.keys(PanelsNamespace).length > 0 ? Object.keys(PanelsNamespace).join(', ') : 'None loaded'}`
                    )
                )
            );
        }

        // Wrap in error boundary to catch rendering errors
        try {
            return e(PanelComponent, { title, data, config, fullData });
        } catch (error) {
            if (Logger) {
                Logger.error(`[PanelRenderer] Error rendering panel ${type}:`, error, { stack: error.stack });
            } else {
                console.error(`[PanelRenderer] Error rendering panel ${type}:`, error);
            }
            return e('div', { className: 'card' },
                e('div', { className: 'card-header' },
                    e('h3', { className: 'card-title' }, title || 'Panel')
                ),
                e('div', { className: 'card-body', style: { padding: '2rem', textAlign: 'center', color: '#ef4444' } },
                    e('p', { style: { fontWeight: '600', marginBottom: '0.5rem' } }, 'Error rendering panel'),
                    e('p', { style: { fontSize: '0.875rem', color: '#94a3b8' } }, error.message || 'Unknown error'),
                    e('p', { style: { fontSize: '0.75rem', marginTop: '1rem', color: '#64748b' } }, 'Please refresh the page or contact support if the issue persists.')
                )
            );
        }
    }

    // ============================================
    // QUERY KEYS AND HELPERS
    // ============================================

    /**
     * Query Key Generator - Helper for consistent query keys
     * Follows React Query patterns for cache key generation
     */
    const queryKeys = {
        portfolio: (id) => ['portfolio', id],
        macro: () => ['macro'],
        holdings: (id) => ['holdings', id],
        scenarios: (id) => ['scenarios', id],
        alerts: (id) => ['alerts', id],
        reports: (id) => ['reports', id],
        user: () => ['user'],
        health: () => ['health'],
        pattern: (pattern, params) => ['pattern', pattern, params]
    };

    /**
     * Enhanced API Client with Caching (Query Helpers)
     * Wraps the existing apiClient with caching layer
     */
    const queryHelpers = {
        ...apiClient,

        /**
         * Execute pattern with caching
         * @param {string} pattern - Pattern name
         * @param {object} inputs - Pattern inputs (must be named 'inputs' for backend compatibility)
         * @param {object} options - Cache options
         */
        executePattern: async (pattern, inputs = {}, options = {}) => {
            // DYNAMIC LOOKUP: Get CacheManager at usage time, not initialization time
            const CacheManager = global.CacheManager;
            if (!CacheManager) {
                const Logger = global.DawsOS?.Logger;
                if (Logger) {
                    Logger.warn('[PatternSystem] CacheManager not available, executing pattern without cache');
                } else {
                    console.warn('[PatternSystem] CacheManager not available, executing pattern without cache');
                }
                return apiClient.executePattern(pattern, inputs);
            }

            const queryKey = queryKeys.pattern(pattern, inputs);

            // Different cache times for different patterns
            const cacheConfig = {
                staleTime: pattern.includes('overview') ? 2 * 60 * 1000 : 5 * 60 * 1000,
                ...options
            };

            return CacheManager.get(
                queryKey,
                () => apiClient.executePattern(pattern, inputs),
                cacheConfig
            );
        },

        /**
         * Get portfolio overview with caching
         * @param {string} portfolioId - Portfolio ID
         * @param {object} options - Cache options
         */
        getPortfolioOverview: async (portfolioId, options = {}) => {
            // DYNAMIC LOOKUP: Get CacheManager at usage time
            const CacheManager = global.CacheManager;
            if (!CacheManager) {
                const Logger = global.DawsOS?.Logger;
                if (Logger) {
                    Logger.warn('[PatternSystem] CacheManager not available, executing without cache');
                } else {
                    console.warn('[PatternSystem] CacheManager not available, executing without cache');
                }
                return apiClient.executePattern('portfolio_overview', {
                    portfolio_id: portfolioId,
                    lookback_days: 252
                });
            }

            const queryKey = queryKeys.portfolio(portfolioId);

            return CacheManager.get(
                queryKey,
                () => apiClient.executePattern('portfolio_overview', {
                    portfolio_id: portfolioId,
                    lookback_days: 252
                }),
                { staleTime: 2 * 60 * 1000, ...options }
            );
        },

        /**
         * Get macro dashboard with caching
         * @param {object} options - Cache options
         */
        getMacroDashboard: async (options = {}) => {
            // DYNAMIC LOOKUP: Get CacheManager at usage time
            const CacheManager = global.CacheManager;
            if (!CacheManager) {
                const Logger = global.DawsOS?.Logger;
                if (Logger) {
                    Logger.warn('[PatternSystem] CacheManager not available, executing without cache');
                } else {
                    console.warn('[PatternSystem] CacheManager not available, executing without cache');
                }
                return apiClient.executePattern('macro_cycles_overview', {});
            }

            const queryKey = queryKeys.macro();

            return CacheManager.get(
                queryKey,
                () => apiClient.executePattern('macro_cycles_overview', {}),
                { staleTime: 10 * 60 * 1000, ...options }
            );
        },

        /**
         * Get holdings with caching
         * @param {string} portfolioId - Portfolio ID
         * @param {object} options - Cache options
         */
        getHoldings: async (portfolioId, options = {}) => {
            // DYNAMIC LOOKUP: Get CacheManager at usage time
            const CacheManager = global.CacheManager;
            if (!CacheManager) {
                const Logger = global.DawsOS?.Logger;
                if (Logger) {
                    Logger.warn('[PatternSystem] CacheManager not available, executing without cache');
                } else {
                    console.warn('[PatternSystem] CacheManager not available, executing without cache');
                }
                return apiClient.getHoldings(portfolioId);
            }

            const queryKey = queryKeys.holdings(portfolioId);

            return CacheManager.get(
                queryKey,
                () => apiClient.getHoldings(portfolioId),
                { staleTime: 5 * 60 * 1000, ...options }
            );
        },

        /**
         * Get alerts with caching
         * @param {string} portfolioId - Portfolio ID
         * @param {object} options - Cache options
         */
        getAlerts: async (portfolioId, options = {}) => {
            // DYNAMIC LOOKUP: Get CacheManager at usage time
            const CacheManager = global.CacheManager;
            if (!CacheManager) {
                const Logger = global.DawsOS?.Logger;
                if (Logger) {
                    Logger.warn('[PatternSystem] CacheManager not available, executing without cache');
                } else {
                    console.warn('[PatternSystem] CacheManager not available, executing without cache');
                }
                return apiClient.executePattern('macro_trend_monitor', {
                    portfolio_id: portfolioId
                });
            }

            const queryKey = queryKeys.alerts(portfolioId);

            return CacheManager.get(
                queryKey,
                () => apiClient.executePattern('macro_trend_monitor', {
                    portfolio_id: portfolioId
                }),
                { staleTime: 1 * 60 * 1000, ...options }
            );
        },

        /**
         * Invalidate portfolio-related caches
         * @param {string} portfolioId - Portfolio ID
         */
        invalidatePortfolio: (portfolioId) => {
            // DYNAMIC LOOKUP: Get CacheManager at usage time
            const CacheManager = global.CacheManager;
            if (!CacheManager) {
                const Logger = global.DawsOS?.Logger;
                if (Logger) {
                    Logger.warn('[PatternSystem] CacheManager not available, skipping cache invalidation');
                } else {
                    console.warn('[PatternSystem] CacheManager not available, skipping cache invalidation');
                }
                return;
            }

            CacheManager.invalidate(queryKeys.portfolio(portfolioId));
            CacheManager.invalidate(queryKeys.holdings(portfolioId));
            CacheManager.invalidate(queryKeys.scenarios(portfolioId));
            CacheManager.invalidate(queryKeys.alerts(portfolioId));
            CacheManager.invalidate(queryKeys.reports(portfolioId));
        },

        /**
         * Invalidate all caches
         */
        invalidateAll: () => {
            // DYNAMIC LOOKUP: Get CacheManager at usage time
            const CacheManager = global.CacheManager;
            if (!CacheManager) {
                const Logger = global.DawsOS?.Logger;
                if (Logger) {
                    Logger.warn('[PatternSystem] CacheManager not available, skipping cache clear');
                } else {
                    console.warn('[PatternSystem] CacheManager not available, skipping cache clear');
                }
                return;
            }

            CacheManager.clear();
        },

        /**
         * Prefetch portfolio data
         * @param {string} portfolioId - Portfolio ID
         */
        prefetchPortfolio: async (portfolioId) => {
            // DYNAMIC LOOKUP: Get CacheManager at usage time
            const CacheManager = global.CacheManager;
            if (!CacheManager) {
                const Logger = global.DawsOS?.Logger;
                if (Logger) {
                    Logger.warn('[PatternSystem] CacheManager not available, skipping prefetch');
                } else {
                    console.warn('[PatternSystem] CacheManager not available, skipping prefetch');
                }
                return;
            }

            await CacheManager.prefetch(
                queryKeys.portfolio(portfolioId),
                () => apiClient.executePattern('portfolio_overview', {
                    portfolio_id: portfolioId,
                    lookback_days: 252
                }),
                { staleTime: 2 * 60 * 1000 }
            );

            await CacheManager.prefetch(
                queryKeys.holdings(portfolioId),
                () => apiClient.getHoldings(portfolioId),
                { staleTime: 5 * 60 * 1000 }
            );
        }
    };

    // ============================================
    // PUBLIC API EXPORT
    // ============================================

        /**
         * Export Pattern System to global DawsOS namespace
         */
        global.DawsOS.PatternSystem = {
            getDataByPath,
            PatternRenderer,
            PanelRenderer,
            patternRegistry,
            queryKeys,
            queryHelpers,
            isInitialized: true
    };

        if (Logger) {
            Logger.checkpoint('[PatternSystem] Module fully initialized');
        } else {
            console.log('[PatternSystem] Module fully initialized');
        }
        
        // Register module with validator when ready (with retry logic)
        function registerPatternSystemModule() {
            if (!global.DawsOS?.ModuleValidator) {
                return false;
            }
            try {
                global.DawsOS.ModuleValidator.validate('pattern-system.js');
                if (Logger) {
                    Logger.checkpoint('[PatternSystem] Module validated');
                } else {
                    console.log('[PatternSystem] Module validated');
                }
                return true;
            } catch (e) {
                return false;
            }
        }
        
        // Retry validation until successful
        let validationAttempts = 0;
        const maxValidationAttempts = 20;
        function tryRegisterPatternSystemModule() {
            if (registerPatternSystemModule()) {
                return; // Success
            }
            validationAttempts++;
            if (validationAttempts < maxValidationAttempts) {
                setTimeout(tryRegisterPatternSystemModule, 50);
            } else {
                if (Logger) {
                    Logger.warn('[PatternSystem] Failed to validate after', maxValidationAttempts, 'attempts');
                } else {
                    console.warn('[PatternSystem] Failed to validate after', maxValidationAttempts, 'attempts');
                }
            }
        }
        tryRegisterPatternSystemModule();
    }
    
    // Start initialization process
    initializePatternSystem();

})(window);
