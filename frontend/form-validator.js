/**
 * DawsOS Form Validator Module
 *
 * Form validation utilities for user input.
 * Extracted from full_ui.html (lines 1720-1760)
 *
 * Features:
 * - Email validation
 * - Password strength validation
 * - Required field validation
 * - Number range validation
 *
 * Dependencies: None (standalone module)
 * Exports: DawsOS.FormValidator
 */

(function(global) {
    'use strict';

    const FormValidator = {
        /**
         * Validate email format
         */
        validateEmail: (email) => {
            const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!email) return { valid: false, message: 'Email is required' };
            if (!re.test(email)) return { valid: false, message: 'Please enter a valid email address' };
            return { valid: true };
        },

        /**
         * Validate password strength
         */
        validatePassword: (password) => {
            if (!password) return { valid: false, message: 'Password is required' };
            if (password.length < 8) return { valid: false, message: 'Password must be at least 8 characters' };
            return { valid: true };
        },

        /**
         * Validate required field
         */
        validateRequired: (value, fieldName) => {
            if (!value || value.toString().trim() === '') {
                return { valid: false, message: `${fieldName} is required` };
            }
            return { valid: true };
        },

        /**
         * Validate number range
         */
        validateRange: (value, min, max, fieldName) => {
            const num = parseFloat(value);
            if (isNaN(num)) return { valid: false, message: `${fieldName} must be a number` };
            if (num < min) return { valid: false, message: `${fieldName} must be at least ${min}` };
            if (num > max) return { valid: false, message: `${fieldName} must be at most ${max}` };
            return { valid: true };
        }
    };

    // Expose via DawsOS namespace
    global.DawsOS = global.DawsOS || {};
    global.DawsOS.FormValidator = FormValidator;

    console.log('[FormValidator] Module loaded successfully');

})(window);
