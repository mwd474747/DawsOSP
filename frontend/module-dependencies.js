/**
 * Module Dependency Graph and Validation
 * Defines module dependencies and validates load order
 */

(function(global) {
    'use strict';
    
    // Module dependency graph
    const MODULE_DEPENDENCIES = {
        'api-client.js': {
            dependencies: [],
            namespace: 'DawsOS.APIClient',
            description: 'API client and token management'
        },
        'utils.js': {
            dependencies: [],
            namespace: 'DawsOS.Utils',
            description: 'Utility functions'
        },
        'panels.js': {
            dependencies: ['utils.js'],
            namespace: 'DawsOS.Panels',
            description: 'Panel components'
        },
        'context.js': {
            dependencies: ['api-client.js', 'utils.js'],
            namespace: 'DawsOS.Context',
            description: 'Portfolio context management'
        },
        'pattern-system.js': {
            dependencies: ['context.js', 'panels.js', 'utils.js'],
            namespace: 'DawsOS.PatternSystem',
            description: 'Pattern orchestration system'
        },
        'pages.js': {
            dependencies: ['context.js', 'pattern-system.js', 'panels.js', 'utils.js'],
            namespace: 'DawsOS.Pages',
            description: 'Page components'
        }
    };
    
    // Track loaded modules
    const loadedModules = new Set();
    const moduleErrors = [];
    const moduleWarnings = [];
    
    // Validate module after load
    function validateModule(filename) {
        // Extract filename from path
        const cleanFilename = filename.split('/').pop().split('?')[0];
        const module = MODULE_DEPENDENCIES[cleanFilename];
        
        if (!module) {
            // Not a tracked module, skip validation
            return;
        }
        
        // Check dependencies
        const missingDeps = module.dependencies.filter(dep => !loadedModules.has(dep));
        if (missingDeps.length > 0) {
            const error = `[ModuleValidation] ${cleanFilename} loaded before dependencies: ${missingDeps.join(', ')}`;
            console.error(error);
            moduleErrors.push({
                module: cleanFilename,
                type: 'dependency',
                message: error,
                missing: missingDeps
            });
        }
        
        // Check namespace
        const namespacePath = module.namespace.split('.');
        let namespace = global;
        for (const part of namespacePath) {
            namespace = namespace?.[part];
        }
        
        if (!namespace) {
            const error = `[ModuleValidation] ${cleanFilename} namespace ${module.namespace} not found`;
            console.error(error);
            moduleErrors.push({
                module: cleanFilename,
                type: 'namespace',
                message: error,
                expected: module.namespace
            });
        }
        
        // Mark as loaded
        loadedModules.add(cleanFilename);
        
        if (missingDeps.length === 0 && namespace) {
            console.log(`✅ [ModuleValidation] ${cleanFilename} loaded successfully`);
        }
    }
    
    // Validate all modules after page load
    function validateAllModules() {
        // Check all expected modules are loaded
        const expectedModules = Object.keys(MODULE_DEPENDENCIES);
        const missingModules = expectedModules.filter(module => !loadedModules.has(module));
        
        if (missingModules.length > 0) {
            const error = `[ModuleValidation] Missing modules: ${missingModules.join(', ')}`;
            console.error(error);
            moduleErrors.push({
                type: 'missing',
                message: error,
                missing: missingModules
            });
        }
        
        // Report results
        if (moduleErrors.length > 0) {
            console.error('[ModuleValidation] Module loading errors:', moduleErrors);
            
            // Show error banner if in development
            if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                const errorDiv = document.createElement('div');
                errorDiv.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; background: #ff0000; color: white; padding: 1rem; z-index: 10000; font-family: monospace; font-size: 12px;';
                errorDiv.innerHTML = `
                    <strong>Module Loading Errors Detected</strong><br>
                    Check console for details. Errors: ${moduleErrors.length}
                `;
                document.body.appendChild(errorDiv);
                
                // Auto-remove after 10 seconds
                setTimeout(() => errorDiv.remove(), 10000);
            }
        } else if (moduleWarnings.length > 0) {
            console.warn('[ModuleValidation] Module loading warnings:', moduleWarnings);
        } else {
            console.log('✅ [ModuleValidation] All modules loaded successfully');
        }
    }
    
    // Override script loading to validate
    const originalCreateElement = document.createElement;
    document.createElement = function(tagName) {
        const element = originalCreateElement.call(document, tagName);
        
        if (tagName === 'script' && element.src) {
            element.addEventListener('load', function() {
                validateModule(this.src);
            });
            element.addEventListener('error', function() {
                const filename = this.src.split('/').pop().split('?')[0];
                const error = `[ModuleValidation] Failed to load module: ${filename}`;
                console.error(error);
                moduleErrors.push({
                    module: filename,
                    type: 'load',
                    message: error
                });
            });
        }
        
        return element;
    };
    
    // Validate after all modules loaded
    window.addEventListener('load', function() {
        // Wait a bit for all scripts to execute
        setTimeout(validateAllModules, 100);
    });
    
    // Export validator
    if (!global.DawsOS) {
        global.DawsOS = {};
    }
    
    global.DawsOS.ModuleValidator = {
        dependencies: MODULE_DEPENDENCIES,
        validate: validateModule,
        validateAll: validateAllModules,
        getErrors: () => moduleErrors,
        getWarnings: () => moduleWarnings,
        getLoadedModules: () => Array.from(loadedModules)
    };
    
})(window);

