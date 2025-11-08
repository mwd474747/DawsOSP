/**
 * Frontend Logger
 * 
 * Purpose: Environment-based logging for frontend code
 * Updated: 2025-01-15
 * Priority: P2 (Medium - Phase 5)
 * 
 * Features:
 *     - Environment-based logging (dev vs production)
 *     - Log levels (debug, info, warn, error)
 *     - Strategic checkpoint support
 *     - No-op in production for debug/info
 * 
 * Usage:
 *     import Logger from './logger.js';
 *     
 *     Logger.debug('Debug message', data);
 *     Logger.info('Info message', data);
 *     Logger.warn('Warning message', data);
 *     Logger.error('Error message', error);
 *     Logger.checkpoint('Checkpoint name', data);
 */

(function() {
    'use strict';

    // Detect environment (development vs production)
    const isDevelopment = window.location.hostname === 'localhost' || 
                         window.location.hostname === '127.0.0.1' ||
                         window.location.hostname.includes('dev') ||
                         window.location.search.includes('debug=true');

    /**
     * Frontend Logger
     */
    const Logger = {
        /**
         * Debug logging (only in development)
         */
        debug: function(message, ...args) {
            if (isDevelopment) {
                console.log(`[DEBUG] ${message}`, ...args);
            }
        },

        /**
         * Info logging (only in development)
         */
        info: function(message, ...args) {
            if (isDevelopment) {
                console.info(`[INFO] ${message}`, ...args);
            }
        },

        /**
         * Warning logging (always logged)
         */
        warn: function(message, ...args) {
            console.warn(`[WARN] ${message}`, ...args);
        },

        /**
         * Error logging (always logged)
         */
        error: function(message, ...args) {
            console.error(`[ERROR] ${message}`, ...args);
        },

        /**
         * Strategic checkpoint (always logged for debugging)
         * Use for critical debugging points
         */
        checkpoint: function(name, data) {
            console.log(`[CHECKPOINT] ${name}`, data);
        }
    };

    // Export Logger
    if (typeof global !== 'undefined' && global.DawsOS) {
        global.DawsOS.Logger = Logger;
    } else {
        // Fallback if DawsOS namespace not available
        window.Logger = Logger;
    }

    // Also export as module if using ES6 modules
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = Logger;
    }
})();

