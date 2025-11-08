/**
 * Namespace Validation
 * Validates namespace structure and checks for namespace pollution
 */

(function(global) {
    'use strict';
    
    // Get Logger if available
    const Logger = global.DawsOS?.Logger;
    
    // Expected namespaces
    const EXPECTED_NAMESPACES = [
        'DawsOS.APIClient',
        'DawsOS.Utils',
        'DawsOS.Panels',
        'DawsOS.Context',
        'DawsOS.PatternSystem',
        'DawsOS.Pages'
    ];
    
    // Deprecated namespaces (still work but should migrate)
    const DEPRECATED_NAMESPACES = [
        {
            path: 'global.TokenManager',
            replacement: 'DawsOS.APIClient.TokenManager',
            description: 'Use DawsOS.APIClient.TokenManager instead'
        },
        {
            path: 'global.apiClient',
            replacement: 'DawsOS.APIClient',
            description: 'Use DawsOS.APIClient instead'
        }
    ];
    
    // Expected global objects (not considered pollution)
    const EXPECTED_GLOBALS = [
        'React',
        'ReactDOM',
        'axios',
        'Chart',
        'DawsOS',
        'window',
        'document',
        'console',
        'localStorage',
        'sessionStorage',
        'navigator',
        'location',
        'history',
        'fetch',
        'Promise',
        'Date',
        'Math',
        'JSON',
        'Array',
        'Object',
        'String',
        'Number',
        'Boolean',
        'Function',
        'Error',
        'RegExp',
        'Map',
        'Set',
        'WeakMap',
        'WeakSet'
    ];
    
    const errors = [];
    const warnings = [];
    
    // Helper to get nested property
    function getNested(obj, path) {
        const parts = path.split('.');
        let current = obj;
        for (const part of parts) {
            if (current == null) return null;
            current = current[part];
        }
        return current;
    }
    
    // Validate namespaces
    function validateNamespaces() {
        errors.length = 0;
        warnings.length = 0;
        
        // Check expected namespaces
        for (const namespacePath of EXPECTED_NAMESPACES) {
            const namespace = getNested(global, namespacePath);
            
            if (!namespace) {
                errors.push({
                    type: 'missing',
                    namespace: namespacePath,
                    message: `Missing expected namespace: ${namespacePath}`
                });
            } else if (typeof namespace !== 'object' || namespace === null) {
                errors.push({
                    type: 'invalid',
                    namespace: namespacePath,
                    message: `Namespace ${namespacePath} exists but is not an object`
                });
            }
        }
        
        // Check for deprecated namespaces
        for (const deprecated of DEPRECATED_NAMESPACES) {
            const namespace = getNested(global, deprecated.path);
            
            if (namespace) {
                warnings.push({
                    type: 'deprecated',
                    namespace: deprecated.path,
                    replacement: deprecated.replacement,
                    message: `Deprecated namespace still exists: ${deprecated.path}. ${deprecated.description}`
                });
            }
        }
        
        // Check for namespace pollution (unexpected global exports)
        const actualGlobals = Object.keys(global).filter(key => {
            // Skip expected globals
            if (EXPECTED_GLOBALS.includes(key)) return false;
            
            // Skip private/internal properties
            if (key.startsWith('_')) return false;
            
            // Only check objects
            const value = global[key];
            return typeof value === 'object' && value !== null && !Array.isArray(value);
        });
        
        if (actualGlobals.length > 0) {
            warnings.push({
                type: 'pollution',
                namespaces: actualGlobals,
                message: `Potential namespace pollution detected: ${actualGlobals.join(', ')}`
            });
        }
        
        // Report results
        if (errors.length > 0) {
            if (Logger) {
                Logger.error('[NamespaceValidation] Errors:', errors);
            } else {
                console.error('[NamespaceValidation] Errors:', errors);
            }
        }
        if (warnings.length > 0) {
            if (Logger) {
                Logger.warn('[NamespaceValidation] Warnings:', warnings);
            } else {
                console.warn('[NamespaceValidation] Warnings:', warnings);
            }
        }
        
        if (errors.length === 0 && warnings.length === 0) {
            if (Logger) {
                Logger.checkpoint('[NamespaceValidation] All namespaces valid');
            } else {
                console.log('✅ [NamespaceValidation] All namespaces valid');
            }
        }
        
        return {
            valid: errors.length === 0,
            errors: errors,
            warnings: warnings
        };
    }
    
    // Validate after all modules loaded
    window.addEventListener('load', function() {
        // Wait a bit for all scripts to execute
        setTimeout(validateNamespaces, 200);
    });
    
    // Export validator
    if (!global.DawsOS) {
        global.DawsOS = {};
    }
    
    global.DawsOS.NamespaceValidator = {
        validate: validateNamespaces,
        getErrors: () => errors,
        getWarnings: () => warnings,
        expectedNamespaces: EXPECTED_NAMESPACES,
        deprecatedNamespaces: DEPRECATED_NAMESPACES
    };
    
})(window);

