/**
 * DawsOS Frontend Panel Components
 *
 * EXTRACTED FROM: /Users/mdawson/Documents/GitHub/DawsOSP/full_ui.html
 * EXTRACTION DATE: 2025-11-07
 * SOURCE LINES: 3992-4789
 *
 * This file contains all panel component definitions extracted from the full_ui.html file.
 * All components are preserved exactly as they appeared in the source.
 *
 * DEPENDENCIES:
 * - React 16.8+ (useState, useEffect, useRef hooks)
 * - React.createElement (aliased as 'e')
 * - Chart.js (for chart rendering)
 * - DawsOS.Utils (formatValue, getColorClass, formatPercentage, formatCurrency, formatNumber)
 * - window.selectedSecurity (global state for navigation)
 * - CustomEvent 'navigate' (for page navigation)
 *
 * PANEL COMPONENTS INCLUDED:
 * 1. MetricsGridPanel - Grid layout for metrics display
 * 2. TablePanel - Data table with sorting and formatting
 * 3. LineChartPanel - Line chart with Chart.js
 * 4. NewsListPanel (advanced) - News feed with filtering (lines 4261-4435)
 * 5. PieChartPanel - Pie chart visualization
 * 6. DonutChartPanel - Donut chart (wrapper around PieChartPanel)
 * 7. ActionCardsPanel - Action cards grid layout
 * 8. CycleCardPanel - Business cycle display card
 * 9. ScorecardPanel - Scorecard with components
 * 10. DualListPanel - Winners/Losers dual list
 * 11. NewsListPanel (simple) - Simple news list (lines 4738-4761)
 * 12. ReportViewerPanel - Embedded iframe viewer
 * 13. BarChartPanel - Bar chart (delegates to LineChartPanel)
 *
 * HELPER FUNCTIONS INCLUDED:
 * - formatValue - Format values by type
 * - getColorClass - Get CSS class based on value
 */

(function(global) {
    'use strict';

    // Initialize DawsOS namespace if not exists
    if (!global.DawsOS) {
        global.DawsOS = {};
    }

    // Create Panels namespace
    const Panels = {};

    // React shortcuts
    const { useState, useEffect, useRef } = React;
    const e = React.createElement;

    // Import utility functions from DawsOS.Utils
    // These are referenced but defined in utils.js or globally
    const formatPercentage = global.DawsOS.Utils?.formatPercentage || ((v) => v + '%');
    const formatCurrency = global.DawsOS.Utils?.formatCurrency || ((v) => '$' + v);
    const formatNumber = global.DawsOS.Utils?.formatNumber || ((v) => v.toFixed(2));

    /**
     * Helper functions for formatting values
     * Lines 4637-4666
     */
    function formatValue(value, format) {
        if (value === null || value === undefined || value === '') return '-';

        // Convert string values to numbers for numeric formats
        let numValue = value;
        if (typeof value === 'string' && (format === 'percentage' || format === 'currency' || format === 'number' || format === 'bps')) {
            numValue = parseFloat(value);
            if (isNaN(numValue)) return '-';
        }

        switch (format) {
            case 'percentage':
                return formatPercentage(numValue);
            case 'currency':
                return formatCurrency(numValue);
            case 'number':
                return formatNumber(numValue, 2);
            case 'bps':
                return `${formatNumber(numValue, 0)} bps`;
            default:
                return typeof value === 'number' ? formatNumber(value, 2) : String(value);
        }
    }

    function getColorClass(value, format) {
        if (format === 'percentage' || format === 'currency') {
            return value > 0 ? 'positive' : value < 0 ? 'negative' : 'neutral';
        }
        return '';
    }

    /**
     * Metrics Grid Panel Component
     * Lines 3992-4022
     */
    function MetricsGridPanel({ title, data, config = {} }) {
        if (!data) return null;

        const metrics = config.metrics || [];
        const columns = config.columns || 4;

        return e('div', { className: 'card' },
            title && e('div', { className: 'card-header' },
                e('h3', { className: 'card-title' }, title)
            ),
            e('div', {
                className: 'stats-grid',
                style: { gridTemplateColumns: `repeat(${columns}, 1fr)` }
            },
                metrics.map(metric => {
                    const value = data[metric.key];
                    const formattedValue = formatValue(value, metric.format);
                    const colorClass = getColorClass(value, metric.format);

                    return e('div', { key: metric.key, className: 'stat-card' },
                        e('div', { className: 'stat-label' }, metric.label),
                        e('div', { className: `stat-value ${colorClass}` }, formattedValue),
                        metric.description && e('div', { className: 'stat-description' }, metric.description)
                    );
                })
            )
        );
    }

    /**
     * Table Panel Component
     * Lines 4024-4123
     */
    function TablePanel({ title, data, config = {} }) {
        const columns = config.columns || [];
        const maxRows = config.maxRows || 20;

        // Show empty state message for corporate actions or other patterns
        if (!data || !Array.isArray(data) || data.length === 0) {
            const emptyMessage = config.emptyMessage ||
                (title?.includes('Corporate Actions')
                    ? 'No upcoming corporate actions found for your portfolio holdings. This could mean no events are scheduled in the selected time range, or your portfolio has no holdings.'
                    : 'No data available');

            return e('div', { className: 'card' },
                title && e('div', { className: 'card-header' },
                    e('h3', { className: 'card-title' }, title)
                ),
                e('div', { style: { padding: '2rem', textAlign: 'center', color: '#94a3b8' } },
                    e('p', { style: { fontSize: '0.95rem', marginBottom: '1rem' } }, emptyMessage),
                    title?.includes('Corporate Actions') && e('div', { style: { fontSize: '0.875rem', color: '#64748b' } },
                        e('p', null, '💡 Corporate actions include:'),
                        e('ul', { style: { listStyle: 'none', padding: 0, marginTop: '0.5rem' } },
                            e('li', null, '• Dividends - Cash or stock distributions'),
                            e('li', null, '• Stock Splits - Share quantity adjustments'),
                            e('li', null, '• Earnings Announcements - Quarterly results')
                        )
                    )
                )
            );
        }

        const displayData = data.slice(0, maxRows);

        return e('div', { className: 'card' },
            title && e('div', { className: 'card-header' },
                e('h3', { className: 'card-title' }, title)
            ),
            e('div', { className: 'table-container' },
                e('table', { className: 'data-table' },
                    columns.length > 0 && e('thead', null,
                        e('tr', null,
                            columns.map(col =>
                                e('th', { key: col.field }, col.header || col.field)
                            )
                        )
                    ),
                    e('tbody', null,
                        displayData.map((row, idx) =>
                            e('tr', { key: idx },
                                columns.length > 0 ?
                                    columns.map(col => {
                                        const value = row[col.field];
                                        const formattedValue = formatValue(value, col.format);
                                        const colorClass = col.color_condition ? getColorClass(value, col.format) : '';

                                        // Make symbol field clickable in holdings table
                                        if (col.field === 'symbol' && title?.includes('Holdings')) {
                                            return e('td', {
                                                key: col.field,
                                                style: { cursor: 'pointer', color: '#00d9ff', textDecoration: 'underline' },
                                                onClick: () => {
                                                    // Store security info globally
                                                    window.selectedSecurity = {
                                                        symbol: value,
                                                        security_id: row.security_id
                                                    };
                                                    // Navigate to security detail
                                                    const event = new CustomEvent('navigate', {
                                                        detail: { page: 'security-detail' }
                                                    });
                                                    window.dispatchEvent(event);
                                                }
                                            }, formattedValue);
                                        }

                                        return e('td', {
                                            key: col.field,
                                            className: colorClass
                                        }, formattedValue);
                                    }) :
                                    Object.entries(row).map(([key, value]) =>
                                        e('td', { key }, formatValue(value))
                                    )
                            )
                        )
                    )
                ),
                data.length > maxRows && e('div', {
                    style: {
                        padding: '0.5rem',
                        textAlign: 'center',
                        fontSize: '0.875rem',
                        color: '#64748b',
                        borderTop: '1px solid rgba(255,255,255,0.1)'
                    }
                }, `Showing ${maxRows} of ${data.length} items`)
            )
        );
    }

    /**
     * Line Chart Panel Component
     * Lines 4125-4256
     */
    function LineChartPanel({ title, data, config = {} }) {
        const chartRef = useRef(null);
        const chartInstance = useRef(null);

        useEffect(() => {
            if (!data || !chartRef.current) return;

            // Destroy existing chart
            if (chartInstance.current) {
                chartInstance.current.destroy();
            }

            const ctx = chartRef.current.getContext('2d');

            // Handle nested agent return structures (defensive handling for all cases)
            // Supports: flat arrays, nested objects, double-nested structures
            let chartLabels = [];
            let chartValues = [];

            // Try multiple extraction strategies in order of preference
            if (data.labels && data.values && Array.isArray(data.labels) && Array.isArray(data.values)) {
                // Strategy 1: Flat structure with labels and values
                chartLabels = data.labels;
                chartValues = data.values;
            } else if (data.data && Array.isArray(data.data)) {
                // Strategy 2: Array of {date, nav_value} or {date, value} or {x, y}
                chartLabels = data.data.map(d => d.date || d.x);
                chartValues = data.data.map(d => d.nav_value || d.value || d.y);
            } else if (Array.isArray(data)) {
                // Strategy 3: Direct array of {date, nav_value} or {date, value}
                chartLabels = data.map(d => d.date || d.x);
                chartValues = data.map(d => d.nav_value || d.value || d.y);
            } else if (data.historical_nav) {
                // Strategy 4: Handle nested historical_nav (single or double nesting)
                const navData = Array.isArray(data.historical_nav)
                    ? data.historical_nav
                    : (data.historical_nav.historical_nav || data.historical_nav.data || []);
                if (Array.isArray(navData)) {
                    chartLabels = navData.map(d => d.date || d.x);
                    chartValues = navData.map(d => d.nav_value || d.value || d.y);
                }
            } else if (data.values && Array.isArray(data.values)) {
                // Strategy 5: Try to extract from common nested patterns
                // Check for nested data structures
                const nestedKeys = Object.keys(data).filter(k =>
                    k !== 'labels' && k !== 'values' && k !== 'data' &&
                    Array.isArray(data[k]) && data[k].length > 0
                );
                if (nestedKeys.length > 0) {
                    // Use first array found
                    const arrayData = data[nestedKeys[0]];
                    chartLabels = arrayData.map(d => d.date || d.x || d.label);
                    chartValues = arrayData.map(d => d.nav_value || d.value || d.y || d.value);
                }
            }

            // Prepare chart data
            const chartData = {
                labels: chartLabels,
                datasets: [{
                    label: config.label || 'Value',
                    data: chartValues,
                    borderColor: config.color || 'rgb(59, 130, 246)',
                    backgroundColor: config.backgroundColor || 'rgba(59, 130, 246, 0.1)',
                    tension: 0.1,
                    fill: config.fill !== false
                }]
            };

            // Create new chart
            chartInstance.current = new Chart(ctx, {
                type: 'line',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: config.showLegend !== false,
                            labels: {
                                color: '#94a3b8'
                            }
                        },
                        title: {
                            display: false
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            },
                            ticks: {
                                color: '#94a3b8'
                            }
                        },
                        y: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.05)'
                            },
                            ticks: {
                                color: '#94a3b8',
                                callback: function(value) {
                                    return formatValue(value, config.format);
                                }
                            }
                        }
                    }
                }
            });

            return () => {
                if (chartInstance.current) {
                    chartInstance.current.destroy();
                }
            };
        }, [data]);

        if (!data) return null;

        return e('div', { className: 'card' },
            title && e('div', { className: 'card-header' },
                e('h3', { className: 'card-title' }, title)
            ),
            e('div', { className: 'chart-container', style: { height: '400px' } },
                e('canvas', { ref: chartRef })
            )
        );
    }

    /**
     * News List Panel Component (Advanced with Filtering)
     * Lines 4258-4435
     */
    function NewsListPanel({ title, data, config = {} }) {
        // Initialize filters from config if provided, otherwise use defaults
        const [filterSymbol, setFilterSymbol] = useState(config.filterSymbol || '');
        const [sentimentFilter, setSentimentFilter] = useState(config.sentimentFilter || 'all');

        const formatSentiment = (sentiment) => {
            const sentimentMap = {
                'POSITIVE': { text: 'Positive', className: 'positive' },
                'NEGATIVE': { text: 'Negative', className: 'negative' },
                'NEUTRAL': { text: 'Neutral', className: 'neutral' },
                'MIXED': { text: 'Mixed', className: 'neutral' }
            };
            return sentimentMap[sentiment] || sentimentMap['NEUTRAL'];
        };

        const formatImpactScore = (score) => {
            if (score >= 0.2) return { text: 'High Impact', className: 'negative' };
            if (score >= 0.1) return { text: 'Medium Impact', className: 'neutral' };
            return { text: 'Low Impact', className: 'positive' };
        };

        const formatTimeAgo = (dateStr) => {
            const date = new Date(dateStr);
            const now = new Date();
            const diff = now - date;
            const hours = Math.floor(diff / (1000 * 60 * 60));

            if (hours < 1) return 'Just now';
            if (hours === 1) return '1 hour ago';
            if (hours < 24) return `${hours} hours ago`;
            const days = Math.floor(hours / 24);
            if (days === 1) return '1 day ago';
            return `${days} days ago`;
        };

        if (!data || !data.news_with_impact) return null;

        const filteredNews = data.news_with_impact.filter(item => {
            const symbolMatch = !filterSymbol ||
                item.entities.some(e => e.toLowerCase().includes(filterSymbol.toLowerCase()));
            const sentimentMatch = sentimentFilter === 'all' ||
                item.sentiment.toLowerCase() === sentimentFilter.toLowerCase();
            return symbolMatch && sentimentMatch;
        });

        return e('div', { className: 'card' },
            e('div', { className: 'card-header' },
                e('h3', { className: 'card-title' }, title || 'News Feed'),
                e('div', { style: { display: 'flex', gap: '1rem', marginTop: '1rem' } },
                    e('input', {
                        type: 'text',
                        className: 'form-input',
                        placeholder: 'Filter by symbol...',
                        value: filterSymbol,
                        onChange: (e) => setFilterSymbol(e.target.value),
                        style: { maxWidth: '200px' }
                    }),
                    e('select', {
                        className: 'form-input',
                        value: sentimentFilter,
                        onChange: (e) => setSentimentFilter(e.target.value),
                        style: { maxWidth: '150px' }
                    },
                        e('option', { value: 'all' }, 'All Sentiment'),
                        e('option', { value: 'positive' }, 'Positive'),
                        e('option', { value: 'negative' }, 'Negative'),
                        e('option', { value: 'neutral' }, 'Neutral')
                    ),
                    filterSymbol && e('button', {
                        onClick: () => setFilterSymbol(''),
                        style: {
                            background: 'transparent',
                            border: '1px solid var(--border-primary)',
                            padding: '0.5rem 1rem',
                            borderRadius: '6px',
                            color: 'var(--text-secondary)',
                            cursor: 'pointer'
                        }
                    }, 'Clear Filter')
                )
            ),
            e('div', { style: { padding: '1rem 0' } },
                filteredNews.length > 0 ?
                    filteredNews.map((item, idx) =>
                        e('div', {
                            key: idx,
                            style: {
                                padding: '1.5rem',
                                borderBottom: idx < filteredNews.length - 1 ?
                                    '1px solid var(--border-secondary)' : 'none',
                                transition: 'background 0.2s',
                                cursor: 'pointer'
                            },
                            onMouseEnter: (e) => e.target.style.background = 'rgba(255, 255, 255, 0.02)',
                            onMouseLeave: (e) => e.target.style.background = 'transparent'
                        },
                            e('div', { style: { display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' } },
                                e('div', { style: { flex: 1 } },
                                    e('h4', { style: { fontSize: '1rem', fontWeight: '600', marginBottom: '0.5rem' } },
                                        item.headline
                                    ),
                                    e('div', {
                                        style: {
                                            display: 'flex',
                                            gap: '1rem',
                                            fontSize: '0.875rem',
                                            color: 'var(--text-secondary)',
                                            marginBottom: '0.5rem'
                                        }
                                    },
                                        e('span', null, item.source),
                                        e('span', null, '•'),
                                        e('span', null, formatTimeAgo(item.published_at)),
                                        item.entities.length > 0 && e('span', null, '•'),
                                        item.entities.length > 0 && e('span', {
                                            style: { color: 'var(--color-info)' }
                                        }, item.entities.join(', '))
                                    )
                                ),
                                e('div', { style: { display: 'flex', flexDirection: 'column', gap: '0.5rem', minWidth: '150px', alignItems: 'flex-end' } },
                                    e('span', {
                                        className: formatSentiment(item.sentiment).className,
                                        style: {
                                            padding: '0.25rem 0.75rem',
                                            borderRadius: '12px',
                                            fontSize: '0.75rem',
                                            fontWeight: '600',
                                            background: item.sentiment === 'POSITIVE' ? 'rgba(16, 185, 129, 0.2)' :
                                                      item.sentiment === 'NEGATIVE' ? 'rgba(239, 68, 68, 0.2)' :
                                                      'rgba(148, 163, 184, 0.2)'
                                        }
                                    }, formatSentiment(item.sentiment).text),
                                    e('span', {
                                        className: formatImpactScore(item.impact_score).className,
                                        style: {
                                            fontSize: '0.75rem',
                                            fontWeight: '500'
                                        }
                                    }, formatImpactScore(item.impact_score).text)
                                )
                            ),
                            e('p', { style: { color: 'var(--text-secondary)', marginTop: '0.75rem' } },
                                item.summary
                            ),
                            e('div', {
                                style: {
                                    display: 'flex',
                                    gap: '2rem',
                                    marginTop: '0.75rem',
                                    fontSize: '0.875rem',
                                    color: 'var(--text-muted)'
                                }
                            },
                                e('span', null,
                                    `Sentiment Score: ${item.sentiment_score > 0 ? '+' : ''}${(item.sentiment_score * 100).toFixed(0)}%`
                                ),
                                e('span', null,
                                    `Impact Score: ${(item.impact_score * 100).toFixed(1)}%`
                                ),
                                e('span', null,
                                    `Portfolio Weight: ${formatPercentage(item.weight_affected)}`
                                )
                            )
                        )
                    ) :
                    e('div', {
                        style: {
                            textAlign: 'center',
                            padding: '3rem',
                            color: 'var(--text-secondary)'
                        }
                    }, 'No news items match your filters')
            )
        );
    }

    /**
     * Pie Chart Panel Component
     * Lines 4437-4546
     */
    function PieChartPanel({ title, data, config = {} }) {
        const chartRef = useRef(null);
        const chartInstance = useRef(null);

        useEffect(() => {
            if (!data || !chartRef.current) return;

            if (chartInstance.current) {
                chartInstance.current.destroy();
            }

            const ctx = chartRef.current.getContext('2d');

            // Handle nested agent return structures (defensive handling for all cases)
            // Supports: flat objects, nested objects, double-nested structures
            let chartDataObj = data;

            // Try multiple extraction strategies
            if (data.sector_allocation) {
                // Strategy 1: Handle nested sector_allocation (single or double nesting)
                if (typeof data.sector_allocation === 'object' && !Array.isArray(data.sector_allocation)) {
                    // Check for double nesting: {sector_allocation: {sector_allocation: {...}}}
                    chartDataObj = data.sector_allocation.sector_allocation || data.sector_allocation;
                }
            } else if (typeof data === 'object' && !Array.isArray(data)) {
                // Strategy 2: Check if data itself is a flat object (already correct)
                // Filter out metadata fields
                const metadataKeys = ['_provenance', '__metadata__', 'total_sectors', 'total_value', 'currency', 'lookback_days', 'data_points'];
                const hasMetadata = metadataKeys.some(k => k in data);
                if (!hasMetadata) {
                    // Likely already a flat object
                    chartDataObj = data;
                } else {
                    // Try to find nested object
                    const nestedKeys = Object.keys(data).filter(k =>
                        !metadataKeys.includes(k) &&
                        typeof data[k] === 'object' &&
                        !Array.isArray(data[k])
                    );
                    if (nestedKeys.length > 0) {
                        chartDataObj = data[nestedKeys[0]];
                    }
                }
            }

            // Prepare chart data
            const labels = Object.keys(chartDataObj);
            const values = Object.values(chartDataObj);

            chartInstance.current = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: config.colors || [
                            '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
                            '#9b59b6', '#e67e22', '#1abc9c', '#34495e'
                        ],
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                color: '#94a3b8',
                                padding: 15
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ${formatValue(value, config.format)} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });

            return () => {
                if (chartInstance.current) {
                    chartInstance.current.destroy();
                }
            };
        }, [data]);

        if (!data) return null;

        return e('div', { className: 'card' },
            title && e('div', { className: 'card-header' },
                e('h3', { className: 'card-title' }, title)
            ),
            e('div', { className: 'chart-container', style: { height: '400px' } },
                e('canvas', { ref: chartRef })
            )
        );
    }

    /**
     * Donut Chart Panel Component (similar to pie but with cutout)
     * Lines 4548-4554
     */
    function DonutChartPanel({ title, data, config = {} }) {
        const modifiedConfig = { ...config, cutout: '50%' };
        return e(PieChartPanel, { title, data, config: modifiedConfig });
    }

    /**
     * Action Cards Panel Component
     * Lines 4556-4588
     */
    function ActionCardsPanel({ title, data, config = {} }) {
        if (!data || !Array.isArray(data)) return null;

        return e('div', { className: 'card' },
            title && e('div', { className: 'card-header' },
                e('h3', { className: 'card-title' }, title)
            ),
            e('div', { className: 'action-cards-grid' },
                data.map((item, idx) =>
                    e('div', { key: idx, className: 'action-card' },
                        e('h4', { className: 'action-title' }, item.title || item.instrument),
                        e('p', { className: 'action-subtitle' }, item.subtitle || item.strategy),
                        item.metrics && e('div', { className: 'action-metrics' },
                            item.metrics.map((metric, midx) =>
                                e('div', { key: midx, className: 'metric-row' },
                                    e('span', { className: 'metric-label' }, metric.label),
                                    e('span', { className: 'metric-value' },
                                        formatValue(metric.value, metric.format))
                                )
                            )
                        ),
                        item.action && e('button', {
                            className: 'btn btn-primary',
                            onClick: () => item.action()
                        }, item.actionLabel || 'Execute')
                    )
                )
            )
        );
    }

    /**
     * Cycle Card Panel Component
     * Lines 4590-4632
     */
    function CycleCardPanel({ title, data, config = {} }) {
        if (!data) return null;

        const getCycleClass = (phase) => {
            if (phase?.toLowerCase().includes('late')) return 'warning';
            if (phase?.toLowerCase().includes('early')) return 'success';
            if (phase?.toLowerCase().includes('crisis')) return 'error';
            return '';
        };

        return e('div', { className: `cycle-card ${config.cycleType || ''}` },
            e('div', { className: 'cycle-header' },
                e('div', { className: 'cycle-title' }, title),
                data.phase_label && e('span', {
                    className: `badge ${getCycleClass(data.phase_label)}`
                }, data.phase_label)
            ),
            data.description && e('p', { className: 'cycle-description' }, data.description),
            e('div', { className: 'cycle-metrics' },
                data.score !== undefined && e('div', { className: 'metric-row' },
                    e('span', { className: 'metric-label' }, 'Score:'),
                    e('span', { className: 'metric-value' }, formatValue(data.score, 'number'))
                ),
                data.confidence !== undefined && e('div', { className: 'metric-row' },
                    e('span', { className: 'metric-label' }, 'Confidence:'),
                    e('span', { className: 'metric-value' }, formatValue(data.confidence, 'percentage'))
                ),
                Object.entries(data).filter(([key]) =>
                    !['phase_label', 'description', 'score', 'confidence'].includes(key)
                ).slice(0, 4).map(([key, value]) =>
                    e('div', { key, className: 'metric-row' },
                        e('span', { className: 'metric-label' },
                            key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) + ':'),
                        e('span', { className: 'metric-value' },
                            formatValue(value))
                    )
                )
            )
        );
    }

    /**
     * Scorecard Panel Component
     * Lines 4668-4701
     */
    function ScorecardPanel({ title, data, config = {} }) {
        if (!data) return null;

        return e('div', { className: 'card' },
            title && e('div', { className: 'card-header' },
                e('h3', { className: 'card-title' }, title)
            ),
            e('div', { className: 'scorecard-content' },
                data.overall_score !== undefined && e('div', { className: 'overall-score' },
                    e('div', { className: 'score-value' },
                        `${formatNumber(data.overall_score, 1)}/${data.max_score || 10}`),
                    e('div', { className: 'score-label' }, 'Overall Score')
                ),
                data.components && e('div', { className: 'score-components' },
                    data.components.map((comp, idx) =>
                        e('div', { key: idx, className: 'score-component' },
                            e('div', { className: 'component-header' },
                                e('span', { className: 'component-label' }, comp.label),
                                e('span', { className: 'component-score' },
                                    formatValue(comp.score, 'number'))
                            ),
                            comp.value !== undefined && e('div', { className: 'component-value' },
                                formatValue(comp.value, comp.format)),
                            comp.explanation && e('div', { className: 'component-explanation' },
                                comp.explanation)
                        )
                    )
                )
            )
        );
    }

    /**
     * Dual List Panel Component
     * Lines 4703-4736
     */
    function DualListPanel({ title, data, config = {} }) {
        if (!data) return null;

        const winners = data.winners || [];
        const losers = data.losers || [];

        return e('div', { className: 'card' },
            title && e('div', { className: 'card-header' },
                e('h3', { className: 'card-title' }, title)
            ),
            e('div', { className: 'dual-list-container' },
                e('div', { className: 'list-section winners' },
                    e('h4', null, 'Top Winners'),
                    winners.map((item, idx) =>
                        e('div', { key: idx, className: 'list-item' },
                            e('span', { className: 'item-label' }, item.symbol || item.name),
                            e('span', { className: 'item-value positive' },
                                formatValue(item.delta_value || item.value, 'currency'))
                        )
                    )
                ),
                e('div', { className: 'list-section losers' },
                    e('h4', null, 'Top Losers'),
                    losers.map((item, idx) =>
                        e('div', { key: idx, className: 'list-item' },
                            e('span', { className: 'item-label' }, item.symbol || item.name),
                            e('span', { className: 'item-value negative' },
                                formatValue(item.delta_value || item.value, 'currency'))
                        )
                    )
                )
            )
        );
    }

    /**
     * News List Panel Component (Simple Version)
     * Lines 4738-4761
     * Note: This is a simpler version compared to the advanced NewsListPanel above
     */
    function NewsListPanelSimple({ title, data, config = {} }) {
        if (!data || !Array.isArray(data)) return null;

        return e('div', { className: 'card' },
            title && e('div', { className: 'card-header' },
                e('h3', { className: 'card-title' }, title)
            ),
            e('div', { className: 'news-list' },
                data.slice(0, config.maxItems || 10).map((item, idx) =>
                    e('div', { key: idx, className: 'news-item' },
                        e('div', { className: 'news-header' },
                            e('h4', { className: 'news-title' }, item.title),
                            e('span', { className: 'news-date' },
                                new Date(item.date || item.published_at).toLocaleDateString())
                        ),
                        item.summary && e('p', { className: 'news-summary' }, item.summary),
                        item.sentiment && e('span', {
                            className: `sentiment-badge ${item.sentiment.toLowerCase()}`
                        }, item.sentiment)
                    )
                )
            )
        );
    }

    /**
     * Report Viewer Panel Component
     * Lines 4763-4779
     */
    function ReportViewerPanel({ title, data, config = {} }) {
        if (!data) return null;

        return e('div', { className: 'card' },
            title && e('div', { className: 'card-header' },
                e('h3', { className: 'card-title' }, title)
            ),
            e('div', { className: 'report-viewer' },
                e('iframe', {
                    src: data.url || data,
                    width: '100%',
                    height: config.height || '800px',
                    frameBorder: '0'
                })
            )
        );
    }

    /**
     * Bar Chart Panel Component
     * Lines 4781-4789
     */
    function BarChartPanel({ title, data, config = {} }) {
        // Implementation similar to LineChartPanel but with bar chart
        // For brevity, delegating to LineChartPanel with modified config
        return e(LineChartPanel, {
            title,
            data,
            config: { ...config, chartType: 'bar' }
        });
    }

    // Expose all panel components via DawsOS.Panels namespace
    Panels.MetricsGridPanel = MetricsGridPanel;
    Panels.TablePanel = TablePanel;
    Panels.LineChartPanel = LineChartPanel;
    Panels.NewsListPanel = NewsListPanel;
    Panels.NewsListPanelSimple = NewsListPanelSimple;
    Panels.PieChartPanel = PieChartPanel;
    Panels.DonutChartPanel = DonutChartPanel;
    Panels.ActionCardsPanel = ActionCardsPanel;
    Panels.CycleCardPanel = CycleCardPanel;
    Panels.ScorecardPanel = ScorecardPanel;
    Panels.DualListPanel = DualListPanel;
    Panels.ReportViewerPanel = ReportViewerPanel;
    Panels.BarChartPanel = BarChartPanel;

    // Also expose helper functions
    Panels.formatValue = formatValue;
    Panels.getColorClass = getColorClass;

    global.DawsOS.Panels = Panels;

})(typeof window !== 'undefined' ? window : global);
