/**
 * DawsOS Error Handler Module
 *
 * Error classification and user-friendly messaging system.
 * Extracted from full_ui.html (lines 1574-1715)
 *
 * Features:
 * - Error classification (network, server, client, timeout)
 * - User-friendly error messages
 * - Actionable suggestions
 * - Development-mode error logging
 *
 * Dependencies: None (standalone module)
 * Exports: DawsOS.ErrorHandler
 */

(function(global) {
    'use strict';

    const ErrorHandler = {
        /**
         * Map error codes to user-friendly messages
         */
        errorMessages: {
            400: "There was an issue with your request. Please check your input and try again.",
            401: "Your session has expired. Please log in again to continue.",
            403: "You don't have permission to access this resource.",
            404: "The requested data could not be found. It may have been moved or deleted.",
            408: "The request took too long. Please check your connection and try again.",
            429: "Too many requests. Please wait a moment and try again.",
            500: "We're experiencing a server issue. Please try again in a few moments.",
            502: "Unable to connect to the server. Please check your connection.",
            503: "The service is temporarily unavailable. Please try again later.",
            504: "The server took too long to respond. Please try again.",

            // Network errors
            'NETWORK_ERROR': "Unable to connect to the server. Please check your internet connection.",
            'TIMEOUT': "The request timed out. Please try again.",
            'UNKNOWN_ERROR': "An unexpected error occurred. Please try again.",

            // Application-specific errors
            'INVALID_PORTFOLIO': "The selected portfolio could not be found.",
            'INSUFFICIENT_DATA': "Not enough data available for this analysis.",
            'CALCULATION_ERROR': "Unable to complete the calculation. Please try again.",
            'AUTH_EXPIRED': "Your authentication has expired. Please log in again.",
            'RATE_LIMIT': "You've made too many requests. Please wait a moment.",
            'VALIDATION_ERROR': "Please check your input and try again.",
            'CONNECTION_LOST': "Connection to the server was lost. Attempting to reconnect..."
        },

        /**
         * Classify error type for appropriate handling
         */
        classifyError: (error) => {
            // Check if it's a network error
            if (!window.navigator.onLine) {
                return {
                    type: 'network',
                    severity: 'warning',
                    message: ErrorHandler.errorMessages['NETWORK_ERROR'],
                    canRetry: true
                };
            }

            // Check for response status codes
            if (error.response) {
                const status = error.response.status;
                const message = ErrorHandler.errorMessages[status] ||
                               error.response.data?.detail ||
                               error.response.data?.message ||
                               'An error occurred. Please try again.';

                return {
                    type: status >= 500 ? 'server' : 'client',
                    severity: status >= 500 ? 'error' : 'warning',
                    status,
                    message,
                    canRetry: status >= 500 || status === 408 || status === 429,
                    details: error.response.data
                };
            }

            // Check for request errors (no response received)
            if (error.request) {
                return {
                    type: 'network',
                    severity: 'error',
                    message: ErrorHandler.errorMessages['NETWORK_ERROR'],
                    canRetry: true
                };
            }

            // Check for timeout errors
            if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
                return {
                    type: 'timeout',
                    severity: 'warning',
                    message: ErrorHandler.errorMessages['TIMEOUT'],
                    canRetry: true
                };
            }

            // Default to unknown error
            return {
                type: 'unknown',
                severity: 'error',
                message: error.message || ErrorHandler.errorMessages['UNKNOWN_ERROR'],
                canRetry: true
            };
        },

        /**
         * Get actionable suggestions based on error type
         */
        getSuggestions: (errorInfo) => {
            const suggestions = [];

            switch (errorInfo.type) {
                case 'network':
                    suggestions.push('Check your internet connection');
                    suggestions.push('Try refreshing the page');
                    suggestions.push('Check if you are behind a firewall or VPN');
                    break;
                case 'server':
                    suggestions.push('Wait a few moments and try again');
                    suggestions.push('If the problem persists, contact support');
                    break;
                case 'client':
                    if (errorInfo.status === 401) {
                        suggestions.push('Click here to log in again');
                    } else if (errorInfo.status === 403) {
                        suggestions.push('Contact your administrator for access');
                    } else if (errorInfo.status === 429) {
                        suggestions.push('Wait a few seconds before retrying');
                    }
                    break;
                case 'timeout':
                    suggestions.push('Check your internet connection speed');
                    suggestions.push('Try again with a smaller data range');
                    break;
            }

            return suggestions;
        },

        /**
         * Log error for debugging (in development mode)
         */
        logError: (error, context = {}) => {
            if (console.group) {
                console.group('%c🔴 Error Details', 'color: #ef4444; font-weight: bold');
                console.error('Error:', error);
                console.log('Context:', context);
                console.log('Stack:', error.stack);
                console.log('Timestamp:', new Date().toISOString());
                console.groupEnd();
            } else {
                console.error('Error occurred:', error, context);
            }
        }
    };

    // Expose via DawsOS namespace
    global.DawsOS = global.DawsOS || {};
    global.DawsOS.ErrorHandler = ErrorHandler;

    console.log('[ErrorHandler] Module loaded successfully');

})(window);
