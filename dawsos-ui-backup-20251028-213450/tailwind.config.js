/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      // Divine Proportions Design System
      spacing: {
        // Fibonacci sequence spacing (px)
        'fib1': '2px',   // 2
        'fib2': '3px',   // 3  
        'fib3': '5px',   // 5
        'fib4': '8px',   // 8
        'fib5': '13px',  // 13
        'fib6': '21px',  // 21
        'fib7': '34px',  // 34
        'fib8': '55px',  // 55
        'fib9': '89px',  // 89
        'fib10': '144px', // 144
        'fib11': '233px', // 233
        'fib12': '377px', // 377
      },
      colors: {
        // Golden angle color distribution
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe', 
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9', // Primary blue (180°)
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        secondary: {
          50: '#fef7ff',
          100: '#fceeff',
          200: '#f8d9ff',
          300: '#f2b5ff',
          400: '#e882ff',
          500: '#dc4fff', // Secondary purple (252°)
          600: '#c026d3',
          700: '#a21caf',
          800: '#86198f',
          900: '#701a75',
        },
        accent: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e', // Accent green (137.5°)
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b', // Warning amber (36°)
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        // Financial data colors
        profit: '#22c55e',
        loss: '#ef4444',
        neutral: '#6b7280',
      },
      boxShadow: {
        // φ-based shadow opacity
        'fib1': '0 1px 2px 0 rgba(0, 0, 0, 0.21)', // 21%
        'fib2': '0 1px 3px 0 rgba(0, 0, 0, 0.13)', // 13%
        'fib3': '0 4px 6px -1px rgba(0, 0, 0, 0.08)', // 8%
        'fib4': '0 10px 15px -3px rgba(0, 0, 0, 0.05)', // 5%
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
      },
      animation: {
        // Fibonacci animation timing
        'fib1': '89ms ease-in-out',
        'fib2': '144ms ease-in-out', 
        'fib3': '233ms ease-in-out',
        'fib4': '377ms ease-in-out',
      },
      backdropBlur: {
        'glass': '16px',
      },
      borderRadius: {
        'fib1': '2px',
        'fib2': '3px',
        'fib3': '5px',
        'fib4': '8px',
        'fib5': '13px',
      },
    },
  },
  plugins: [],
}
