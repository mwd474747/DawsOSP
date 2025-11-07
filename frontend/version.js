/**
 * DawsOS Version Management
 * Provides version information for cache-busting and debugging
 */

(function(global) {
    'use strict';
    
    // Version information
    const VERSION = {
        major: 2025,
        minor: 1,
        patch: 15,
        build: Date.now(), // Use timestamp for development
        toString: function() {
            return `${this.major}${String(this.minor).padStart(2, '0')}${String(this.patch).padStart(2, '0')}`;
        },
        getQueryString: function() {
            // Use build timestamp for development, version string for production
            return process.env.NODE_ENV === 'production' ? this.toString() : this.build;
        }
    };
    
    // Export to global DawsOS namespace
    if (!global.DawsOS) {
        global.DawsOS = {};
    }
    
    global.DawsOS.Version = VERSION;
    
    // Log version for debugging
    console.log(`✅ DawsOS Version: ${VERSION.toString()} (build: ${VERSION.build})`);
    
})(window);

