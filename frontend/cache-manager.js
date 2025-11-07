/**
 * DawsOS Cache Manager Module
 *
 * Advanced caching system with stale-while-revalidate pattern.
 * Extracted from full_ui.html (lines 1165-1564)
 *
 * Features:
 * - Query key-based caching
 * - Stale-while-revalidate pattern
 * - Automatic garbage collection
 * - Request deduplication
 * - Cache invalidation on mutations
 * - Background refetching
 *
 * Inspired by React Query patterns from the TypeScript implementation
 *
 * Dependencies: None (standalone module)
 * Exports: DawsOS.CacheManager
 */

(function(global) {
    'use strict';

    const CacheManager = (() => {
        // Cache storage
        const cache = new Map();
        const querySubscribers = new Map();
        const activeRequests = new Map();
        const cacheTimers = new Map();

        // Default configuration (matching React Query defaults)
        const defaultConfig = {
            staleTime: 5 * 60 * 1000,      // 5 minutes - how long data is fresh
            gcTime: 10 * 60 * 1000,         // 10 minutes - garbage collection time
            retryCount: 3,                   // Number of retry attempts
            retryDelay: 1000,                // Base retry delay
            refetchOnWindowFocus: true,     // Refetch when window gains focus
            refetchOnReconnect: true,        // Refetch on network reconnect
            backgroundRefetchInterval: null  // Background refetch interval (null = disabled)
        };

        /**
         * Generate cache key from query key array or string
         * @param {Array|string} queryKey - Query key
         * @returns {string} Serialized cache key
         */
        const getCacheKey = (queryKey) => {
            if (typeof queryKey === 'string') return queryKey;
            if (Array.isArray(queryKey)) return JSON.stringify(queryKey);
            return JSON.stringify([queryKey]);
        };

        /**
         * Check if cached data is stale
         * @param {object} entry - Cache entry
         * @param {number} staleTime - Stale time in ms
         * @returns {boolean} Whether data is stale
         */
        const isStale = (entry, staleTime = defaultConfig.staleTime) => {
            if (!entry) return true;
            const age = Date.now() - entry.timestamp;
            return age > staleTime;
        };

        /**
         * Check if cache should be garbage collected
         * @param {object} entry - Cache entry
         * @param {number} gcTime - Garbage collection time in ms
         * @returns {boolean} Whether to garbage collect
         */
        const shouldGarbageCollect = (entry, gcTime = defaultConfig.gcTime) => {
            if (!entry) return true;
            const age = Date.now() - entry.lastAccessed;
            return age > gcTime && entry.subscribers === 0;
        };

        /**
         * Get cached data with stale-while-revalidate pattern
         * @param {Array|string} queryKey - Query key
         * @param {Function} queryFn - Function to fetch data
         * @param {object} options - Query options
         * @returns {Promise} Cached or fresh data
         */
        const get = async (queryKey, queryFn, options = {}) => {
            const key = getCacheKey(queryKey);
            const config = { ...defaultConfig, ...options };

            // Check cache
            const cached = cache.get(key);

            // Update last accessed time
            if (cached) {
                cached.lastAccessed = Date.now();
            }

            // Return fresh cached data immediately
            if (cached && !isStale(cached, config.staleTime)) {
                return {
                    data: cached.data,
                    error: null,
                    isStale: false,
                    isFetching: false,
                    isFromCache: true
                };
            }

            // Check if there's already an active request (deduplication)
            if (activeRequests.has(key)) {
                const activePromise = activeRequests.get(key);
                return activePromise;
            }

            // Stale-while-revalidate: Return stale data immediately while fetching
            if (cached && isStale(cached, config.staleTime)) {
                // Start background refetch
                const refetchPromise = fetchWithRetry(queryFn, config)
                    .then(data => {
                        set(queryKey, data);
                        notifySubscribers(key, { data, error: null, isStale: false });
                        return { data, error: null, isStale: false, isFetching: false };
                    })
                    .catch(error => {
                        // Keep stale data on error
                        notifySubscribers(key, { data: cached.data, error, isStale: true });
                        return { data: cached.data, error, isStale: true, isFetching: false };
                    })
                    .finally(() => {
                        activeRequests.delete(key);
                    });

                activeRequests.set(key, refetchPromise);

                // Return stale data immediately
                return {
                    data: cached.data,
                    error: null,
                    isStale: true,
                    isFetching: true,
                    isFromCache: true
                };
            }

            // No cache or expired - fetch fresh data
            const fetchPromise = fetchWithRetry(queryFn, config)
                .then(data => {
                    set(queryKey, data);
                    notifySubscribers(key, { data, error: null, isStale: false });
                    return { data, error: null, isStale: false, isFetching: false };
                })
                .catch(error => {
                    notifySubscribers(key, { data: null, error, isStale: false });
                    throw error;
                })
                .finally(() => {
                    activeRequests.delete(key);
                });

            activeRequests.set(key, fetchPromise);
            return fetchPromise;
        };

        /**
         * Fetch with retry logic
         * @param {Function} queryFn - Query function
         * @param {object} config - Configuration
         * @returns {Promise} Query result
         */
        const fetchWithRetry = async (queryFn, config) => {
            let lastError;

            for (let attempt = 0; attempt <= config.retryCount; attempt++) {
                try {
                    const result = await queryFn();
                    return result;
                } catch (error) {
                    lastError = error;

                    // Don't retry on 4xx errors
                    if (error.response?.status >= 400 && error.response?.status < 500) {
                        throw error;
                    }

                    // Wait before retry with exponential backoff
                    if (attempt < config.retryCount) {
                        const delay = Math.min(
                            config.retryDelay * Math.pow(2, attempt),
                            30000
                        );
                        await new Promise(resolve => setTimeout(resolve, delay));
                    }
                }
            }

            throw lastError;
        };

        /**
         * Set data in cache
         * @param {Array|string} queryKey - Query key
         * @param {any} data - Data to cache
         * @param {object} options - Cache options
         */
        const set = (queryKey, data, options = {}) => {
            const key = getCacheKey(queryKey);
            const config = { ...defaultConfig, ...options };

            // Clear existing garbage collection timer
            if (cacheTimers.has(key)) {
                clearTimeout(cacheTimers.get(key));
            }

            // Store in cache
            cache.set(key, {
                data,
                timestamp: Date.now(),
                lastAccessed: Date.now(),
                subscribers: querySubscribers.get(key)?.size || 0
            });

            // Schedule garbage collection
            const gcTimer = setTimeout(() => {
                const entry = cache.get(key);
                if (entry && shouldGarbageCollect(entry, config.gcTime)) {
                    cache.delete(key);
                    cacheTimers.delete(key);
                }
            }, config.gcTime);

            cacheTimers.set(key, gcTimer);
        };

        /**
         * Invalidate cache entries
         * @param {Array|string|Function} queryKey - Query key or predicate
         */
        const invalidate = (queryKey) => {
            if (typeof queryKey === 'function') {
                // Invalidate by predicate
                for (const [key, entry] of cache.entries()) {
                    if (queryKey(key, entry.data)) {
                        cache.delete(key);
                        notifySubscribers(key, { invalidated: true });
                    }
                }
            } else {
                // Invalidate by key
                const key = getCacheKey(queryKey);

                // Support partial matching for array keys
                if (Array.isArray(queryKey)) {
                    const prefix = JSON.stringify(queryKey);
                    for (const cacheKey of cache.keys()) {
                        if (cacheKey.startsWith(prefix.slice(0, -1))) {
                            cache.delete(cacheKey);
                            notifySubscribers(cacheKey, { invalidated: true });
                        }
                    }
                } else {
                    cache.delete(key);
                    notifySubscribers(key, { invalidated: true });
                }
            }
        };

        /**
         * Clear entire cache
         */
        const clear = () => {
            cache.clear();
            activeRequests.clear();

            // Clear all timers
            for (const timer of cacheTimers.values()) {
                clearTimeout(timer);
            }
            cacheTimers.clear();

            // Notify all subscribers
            for (const key of querySubscribers.keys()) {
                notifySubscribers(key, { invalidated: true });
            }
        };

        /**
         * Subscribe to cache updates
         * @param {Array|string} queryKey - Query key
         * @param {Function} callback - Callback function
         * @returns {Function} Unsubscribe function
         */
        const subscribe = (queryKey, callback) => {
            const key = getCacheKey(queryKey);

            if (!querySubscribers.has(key)) {
                querySubscribers.set(key, new Set());
            }

            querySubscribers.get(key).add(callback);

            // Update subscriber count
            const entry = cache.get(key);
            if (entry) {
                entry.subscribers = querySubscribers.get(key).size;
            }

            // Return unsubscribe function
            return () => {
                const subscribers = querySubscribers.get(key);
                if (subscribers) {
                    subscribers.delete(callback);
                    if (subscribers.size === 0) {
                        querySubscribers.delete(key);
                    }

                    // Update subscriber count
                    const entry = cache.get(key);
                    if (entry) {
                        entry.subscribers = subscribers.size;
                    }
                }
            };
        };

        /**
         * Notify subscribers of cache updates
         * @param {string} key - Cache key
         * @param {object} update - Update data
         */
        const notifySubscribers = (key, update) => {
            const subscribers = querySubscribers.get(key);
            if (subscribers) {
                subscribers.forEach(callback => {
                    try {
                        callback(update);
                    } catch (error) {
                        console.error('Error in cache subscriber:', error);
                    }
                });
            }
        };

        /**
         * Prefetch data into cache
         * @param {Array|string} queryKey - Query key
         * @param {Function} queryFn - Query function
         * @param {object} options - Options
         */
        const prefetch = async (queryKey, queryFn, options = {}) => {
            const key = getCacheKey(queryKey);
            const cached = cache.get(key);

            // Only prefetch if not cached or stale
            if (!cached || isStale(cached, options.staleTime)) {
                try {
                    const data = await queryFn();
                    set(queryKey, data, options);
                } catch (error) {
                    console.error('Prefetch error:', error);
                }
            }
        };

        /**
         * Get cache statistics
         * @returns {object} Cache statistics
         */
        const getStats = () => {
            const entries = Array.from(cache.entries());
            const now = Date.now();

            return {
                size: cache.size,
                activeRequests: activeRequests.size,
                subscribers: querySubscribers.size,
                entries: entries.map(([key, entry]) => ({
                    key,
                    age: now - entry.timestamp,
                    lastAccessed: now - entry.lastAccessed,
                    isStale: isStale(entry),
                    subscribers: entry.subscribers
                }))
            };
        };

        // Setup window focus refetching
        if (typeof window !== 'undefined' && defaultConfig.refetchOnWindowFocus) {
            window.addEventListener('focus', () => {
                // Refetch all queries with subscribers
                for (const [key, subscribers] of querySubscribers.entries()) {
                    if (subscribers.size > 0) {
                        const cached = cache.get(key);
                        if (cached && isStale(cached)) {
                            // Mark for refetch
                            cached.timestamp = 0;
                        }
                    }
                }
            });
        }

        // Setup online/offline handling
        if (typeof window !== 'undefined' && defaultConfig.refetchOnReconnect) {
            window.addEventListener('online', () => {
                // Trigger refetch for stale queries
                for (const [key, entry] of cache.entries()) {
                    if (isStale(entry)) {
                        notifySubscribers(key, { refetch: true });
                    }
                }
            });
        }

        return {
            get,
            set,
            invalidate,
            clear,
            subscribe,
            prefetch,
            getStats,
            isStale,
            config: defaultConfig
        };
    })();

    // Expose via DawsOS namespace
    global.DawsOS = global.DawsOS || {};
    global.DawsOS.CacheManager = CacheManager;

    console.log('[CacheManager] Module loaded successfully');

})(window);
